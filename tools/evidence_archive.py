#!/usr/bin/env python3
"""Historical evidence archive over the existing Git repository.

The active checkout keeps current acceptance evidence. Completed historical
tranches may be removed from the working tree after this tool records a compact,
deterministic index that binds every removed path to its Git blob (type, object
id, mode, byte length) and raw-byte SHA-256. The blobs themselves stay reachable
through ordinary Git history; this tool never rewrites history, moves refs, or
fetches the network.

Commands (all read-only unless noted):

  generate --feature ID [--feature ID ...] [--source REV] [--output PATH]
      Build/merge an index for completed features from the verified Git tree.

  verify [--tranche ID]
      Validate index relations and every bound object offline.

  resolve-for-feature --feature ID --path PATH
      Exit 0 only when PATH is archived under an eligible, unchanged completed
      feature. Used by validator check C16 to resolve historical evidence
      without treating it as fresh acceptance.

  restore --tranche ID --output DIR
      Materialize a tranche into a fresh directory outside the active checkout.
      Never overwrites non-matching content, never executes restored files.

  check-growth --base REV [--limit-bytes N]
      Fail on newly added generated evidence blobs above the bounded limit and
      on nested repository metadata under .agent/evidence/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Iterable

INDEX_REL = ".agent/evidence-archive/index.json"
SCHEMA_VERSION = 1
GENERATOR_VERSION = "1"
DEFAULT_GROWTH_LIMIT = 1 << 20
EVIDENCE_PREFIX = ".agent/evidence/"


class ArchiveError(Exception):
    """A malformed index, an ineligible tranche, or an object/digest mismatch."""


def _run_git(root: Path, *args: str, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ArchiveError(f"git {' '.join(args)} failed: {detail}")
    if text:
        return result.stdout.decode("utf-8", errors="strict")
    return result.stdout


def _git_ok(root: Path, *args: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize_rel(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise ArchiveError("archived path must be a non-empty string")
    if "\x00" in path or "\\" in path:
        raise ArchiveError(f"archived path contains an illegal character: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in ("..", "") for part in pure.parts):
        raise ArchiveError(f"archived path is not a normalized relative path: {path!r}")
    normalized = pure.as_posix()
    if normalized != path:
        raise ArchiveError(f"archived path is not in canonical form: {path!r} -> {normalized!r}")
    if not normalized.startswith(EVIDENCE_PREFIX):
        raise ArchiveError(f"archived path is outside {EVIDENCE_PREFIX}: {path!r}")
    if "/.git/" in normalized or normalized.endswith("/.git"):
        raise ArchiveError(f"nested repository metadata is not eligible for archiving: {path!r}")
    return normalized


def _load_index(root: Path) -> dict[str, Any]:
    path = root / INDEX_REL
    if not path.is_file():
        raise ArchiveError(f"archive index not present: {INDEX_REL}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ArchiveError(f"archive index is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise ArchiveError("archive index must be a JSON object")
    return doc


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with tmp.open("xb") as handle:
        handle.write(raw)
    os.replace(tmp, path)


def _feature_state(root: Path) -> dict[str, dict[str, Any]]:
    """Return feature id -> {complete, lists, statuses} across every feature list."""
    state: dict[str, dict[str, Any]] = {}
    for list_path in sorted(root.glob(".agent/feature_list*.json")):
        try:
            doc = json.loads(list_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        features = doc.get("features") if isinstance(doc, dict) else None
        if not isinstance(features, list):
            continue
        rel = list_path.relative_to(root).as_posix()
        for feature in features:
            if not isinstance(feature, dict):
                continue
            fid = feature.get("id")
            if not isinstance(fid, str) or not fid:
                continue
            row = state.setdefault(fid, {"complete": False, "lists": [], "statuses": []})
            status = feature.get("status")
            row["lists"].append(rel)
            row["statuses"].append(status)
            if status == "complete":
                row["complete"] = True
    return state


def _require_complete(root: Path, feature_id: str) -> list[str]:
    state = _feature_state(root).get(feature_id)
    if state is None:
        raise ArchiveError(f"feature {feature_id!r} is not present in any feature list")
    if not state["complete"]:
        raise ArchiveError(
            f"feature {feature_id!r} is not complete (statuses: {state['statuses']}); "
            "active or reopened features require current evidence"
        )
    return list(state["lists"])


def _file_digest(path: Path) -> str:
    try:
        return _sha256(path.read_bytes())
    except OSError as exc:
        raise ArchiveError(f"cannot read required record {path}: {exc}") from exc


def _collect_tranche_paths(root: Path, feature_id: str, source: str) -> list[tuple[str, str, str]]:
    """Return (path, mode, object_id) rows for a feature tranche from the Git tree."""
    prefix = f"{EVIDENCE_PREFIX}{feature_id}/"
    sibling_prefix = f"{EVIDENCE_PREFIX}{feature_id}-"
    listing = _run_git(root, "ls-tree", "-r", "-z", source, "--", EVIDENCE_PREFIX)
    rows: list[tuple[str, str, str]] = []
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        meta, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode("utf-8").split()
        path = raw_path.decode("utf-8")
        if not (path.startswith(prefix) or path.startswith(sibling_prefix)):
            continue
        _normalize_rel(path)
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ArchiveError(f"unsupported object for {path}: {kind} mode {mode}")
        rows.append((path, mode, oid))
    rows.sort(key=lambda row: row[0])
    return rows


def _resolve_commit(root: Path, rev: str) -> tuple[str, str]:
    commit = str(_run_git(root, "rev-parse", "--verify", f"{rev}^{{commit}}", text=True)).strip()
    tree = str(_run_git(root, "rev-parse", "--verify", f"{commit}^{{tree}}", text=True)).strip()
    return commit, tree


def _read_object(root: Path, oid: str) -> tuple[int, str]:
    size = int(str(_run_git(root, "cat-file", "-s", oid, text=True)).strip())
    raw = _run_git(root, "cat-file", "blob", oid)
    assert isinstance(raw, bytes)
    if len(raw) != size:
        raise ArchiveError(f"object {oid} length disagrees with cat-file size")
    return size, _sha256(raw)


def _batch_objects(root: Path, oids: Iterable[str]) -> dict[str, tuple[str, bytes]]:
    """Read many objects through one git process; reports missing objects explicitly."""
    unique = list(dict.fromkeys(oids))
    if not unique:
        return {}
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=("\n".join(unique) + "\n").encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ArchiveError(f"git cat-file --batch failed: {detail}")
    data = result.stdout
    position = 0
    out: dict[str, tuple[str, bytes]] = {}
    for oid in unique:
        newline = data.find(b"\n", position)
        if newline < 0:
            raise ArchiveError("truncated git cat-file --batch output")
        header = data[position:newline].decode("utf-8", errors="strict")
        position = newline + 1
        parts = header.split()
        if len(parts) == 2 and parts[1] == "missing":
            out[oid] = ("missing", b"")
            continue
        if len(parts) != 3:
            raise ArchiveError(f"unexpected git cat-file header: {header!r}")
        kind, size_text = parts[1], parts[2]
        size = int(size_text)
        raw = data[position:position + size]
        position += size
        if data[position:position + 1] != b"\n":
            raise ArchiveError("truncated git cat-file --batch object payload")
        position += 1
        out[oid] = (kind, raw)
    return out


def generate(
    root: Path,
    feature_ids: Iterable[str],
    *,
    source: str = "HEAD",
    output: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    commit, tree = _resolve_commit(root, source)
    origin = str(_run_git(root, "remote", "get-url", "origin", text=True)).strip()
    output_path = output or (root / INDEX_REL)

    existing: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "repository": {}, "objects": {}, "tranches": []}
    if output_path.is_file():
        try:
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (OSError, ValueError) as exc:
            raise ArchiveError(f"cannot merge existing archive index: {exc}") from exc

    objects: dict[str, list[Any]] = dict(existing.get("objects") or {})
    oid_to_digest = {value[0]: digest for digest, value in objects.items()}
    tranches: dict[str, dict[str, Any]] = {
        row.get("feature_id"): row for row in existing.get("tranches", []) if isinstance(row, dict)
    }
    seen_paths: dict[str, str] = {}
    for tranche in tranches.values():
        for entry in tranche.get("entries", []):
            seen_paths[entry[0]] = str(tranche.get("feature_id"))

    for feature_id in sorted(set(feature_ids)):
        lists = _require_complete(root, feature_id)
        contract_rel = f".agent/contracts/{feature_id}.json"
        qa_rel = f".agent/qa/{feature_id}.json"
        if not (root / contract_rel).is_file() or not (root / qa_rel).is_file():
            raise ArchiveError(
                f"feature {feature_id!r} has no current contract/QA records; "
                "historical binding requires both"
            )

        rows = _collect_tranche_paths(root, feature_id, commit)
        if not rows:
            raise ArchiveError(f"feature {feature_id!r} has no tracked evidence at {commit}")
        entries: list[list[str]] = []
        for path, mode, oid in rows:
            owner = seen_paths.get(path)
            if owner is not None and owner != feature_id:
                raise ArchiveError(f"ambiguous archived path {path!r}: claimed by {owner!r} and {feature_id!r}")
            if owner == feature_id:
                prior = next(e for e in tranches[feature_id]["entries"] if e[0] == path)
                if prior[1] != mode:
                    raise ArchiveError(f"conflicting mode for {path!r}: {prior[1]!r} vs {mode!r}")
                entries.append(prior)
                continue
            digest = oid_to_digest.get(oid)
            if digest is None:
                size, digest = _read_object(root, oid)
                objects.setdefault(digest, [oid, size])
                oid_to_digest[oid] = digest
            entries.append([path, mode, digest])
            seen_paths[path] = feature_id

        tranches[feature_id] = {
            "id": f"feature-{feature_id}",
            "feature_id": feature_id,
            "feature_lists": lists,
            "archive_commit": commit,
            "archive_tree": tree,
            "proved_source_commit": commit,
            "contract": {"path": contract_rel, "sha256": _file_digest(root / contract_rel)},
            "qa": {"path": qa_rel, "sha256": _file_digest(root / qa_rel)},
            "object_type": "blob",
            "entries": sorted(entries, key=lambda row: row[0]),
        }

    # Drop object rows no longer referenced (deterministic merge on regeneration).
    referenced = {entry[2] for tranche in tranches.values() for entry in tranche.get("entries", [])}
    objects = {digest: value for digest, value in objects.items() if digest in referenced}

    doc = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "repository": {
            "origin": origin,
            "archive_commit": commit,
            "archive_tree": tree,
        },
        "objects": objects,
        "tranches": [tranches[fid] for fid in sorted(tranches)],
    }
    _atomic_write(output_path, canonical_bytes(doc))
    return doc


def _verify_structure(doc: dict[str, Any], root: Path) -> None:
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise ArchiveError(f"unsupported archive schema_version: {doc.get('schema_version')!r}")
    objects = doc.get("objects")
    tranches = doc.get("tranches")
    if not isinstance(objects, dict) or not isinstance(tranches, list):
        raise ArchiveError("archive index must carry objects and tranches")
    seen: dict[str, str] = {}
    tranche_ids: set[str] = set()
    for tranche in tranches:
        if not isinstance(tranche, dict):
            raise ArchiveError("tranche must be an object")
        tid = tranche.get("id")
        fid = tranche.get("feature_id")
        if not isinstance(tid, str) or not isinstance(fid, str):
            raise ArchiveError("tranche id/feature_id must be strings")
        if tid in tranche_ids:
            raise ArchiveError(f"duplicate tranche id: {tid}")
        tranche_ids.add(tid)
        if tranche.get("object_type") != "blob":
            raise ArchiveError(f"{tid}: unsupported object_type")
        for key in ("contract", "qa"):
            record = tranche.get(key)
            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                raise ArchiveError(f"{tid}: {key} binding is malformed")
        entries = tranche.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ArchiveError(f"{tid}: entries must be a non-empty list")
        for entry in entries:
            if not isinstance(entry, list) or len(entry) != 3:
                raise ArchiveError(f"{tid}: entry must be [path, mode, sha256]")
            path, mode, digest = entry
            _normalize_rel(path)
            if mode not in ("100644", "100755"):
                raise ArchiveError(f"{tid}: unsupported mode {mode!r} for {path!r}")
            if not isinstance(digest, str) or digest not in objects:
                raise ArchiveError(f"{tid}: object digest not declared for {path!r}")
            if path in seen:
                raise ArchiveError(f"duplicate archived path {path!r} in {seen[path]!r} and {tid!r}")
            seen[path] = tid
            obj = objects[digest]
            if not isinstance(obj, list) or len(obj) != 2:
                raise ArchiveError(f"object {digest} must be [git_oid, size]")
            oid, size = obj
            if not isinstance(oid, str) or not isinstance(size, int) or size < 0:
                raise ArchiveError(f"object {digest} has an invalid binding")


def verify(root: Path, *, tranche_id: str | None = None, check_records: bool = True) -> dict[str, Any]:
    root = root.resolve()
    doc = _load_index(root)
    _verify_structure(doc, root)
    objects = doc["objects"]
    selected = [t for t in doc["tranches"] if tranche_id is None or t["id"] == tranche_id]
    if tranche_id is not None and not selected:
        raise ArchiveError(f"tranche not found: {tranche_id}")
    verified = 0
    features: set[str] = set()
    needed: list[str] = []
    for tranche in selected:
        for _path, _mode, digest in tranche["entries"]:
            needed.append(objects[digest][0])
    observed = _batch_objects(root, needed)
    for tranche in selected:
        fid = tranche["feature_id"]
        features.add(fid)
        if check_records:
            _require_complete(root, fid)
            for key in ("contract", "qa"):
                record = tranche[key]
                path = root / record["path"]
                if not path.is_file():
                    raise ArchiveError(f"{tranche['id']}: current {key} record is missing: {record['path']}")
                if _file_digest(path) != record.get("sha256"):
                    raise ArchiveError(
                        f"{tranche['id']}: current {key} record changed since archiving; "
                        "historical evidence is no longer eligible"
                    )
        for path, mode, digest in tranche["entries"]:
            oid, expected_size = objects[digest]
            kind, raw = observed.get(oid, ("missing", b""))
            if kind == "missing":
                raise ArchiveError(f"{tranche['id']}: missing Git object {oid} for {path}")
            if kind != "blob":
                raise ArchiveError(f"{tranche['id']}: object {oid} for {path} is {kind}, expected blob")
            if len(raw) != int(expected_size):
                raise ArchiveError(f"{tranche['id']}: size mismatch for {path}")
            if _sha256(raw) != digest:
                raise ArchiveError(f"{tranche['id']}: SHA-256 mismatch for {path}")
            verified += 1
    return {"tranches": len(selected), "files": verified, "features": sorted(features)}


def _find_tranche_for_path(doc: dict[str, Any], path: str) -> dict[str, Any] | None:
    for tranche in doc["tranches"]:
        for entry in tranche["entries"]:
            if entry[0] == path:
                return tranche
    return None


def resolve_for_feature(root: Path, feature_id: str, path: str) -> dict[str, Any]:
    root = root.resolve()
    normalized = _normalize_rel(path)
    _require_complete(root, feature_id)
    doc = _load_index(root)
    _verify_structure(doc, root)
    tranche = _find_tranche_for_path(doc, normalized)
    if tranche is None:
        raise ArchiveError(f"{normalized}: not present in the historical archive")
    owner = tranche["feature_id"]
    _require_complete(root, owner)
    for key in ("contract", "qa"):
        record = tranche[key]
        record_path = root / record["path"]
        if not record_path.is_file() or _file_digest(record_path) != record.get("sha256"):
            raise ArchiveError(
                f"{normalized}: owning feature {owner} has changed {key} records; "
                "current evidence is required"
            )
    entry = next(row for row in tranche["entries"] if row[0] == normalized)
    oid, expected_size = doc["objects"][entry[2]][0], doc["objects"][entry[2]][1]
    kind, raw = _batch_objects(root, [oid]).get(oid, ("missing", b""))
    if kind == "missing":
        raise ArchiveError(f"{normalized}: archived Git object {oid} is missing")
    if kind != "blob":
        raise ArchiveError(f"{normalized}: archived object is not a blob")
    if len(raw) != int(expected_size) or _sha256(raw) != entry[2]:
        raise ArchiveError(f"{normalized}: archived object failed integrity verification")
    return {"feature_id": feature_id, "owner_feature_id": owner, "tranche": tranche["id"], "path": normalized}


def restore(root: Path, tranche_id: str, destination: Path) -> dict[str, Any]:
    root = root.resolve()
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ArchiveError("restore destination must be outside the active checkout")
    doc = _load_index(root)
    _verify_structure(doc, root)
    tranche = next((t for t in doc["tranches"] if t["id"] == tranche_id), None)
    if tranche is None:
        raise ArchiveError(f"tranche not found: {tranche_id}")
    observed = _batch_objects(root, [doc["objects"][entry[2]][0] for entry in tranche["entries"]])
    for path, mode, digest in tranche["entries"]:
        oid, expected_size = doc["objects"][digest]
        kind, raw = observed.get(oid, ("missing", b""))
        if kind != "blob" or len(raw) != int(expected_size) or _sha256(raw) != digest:
            raise ArchiveError(f"{tranche_id}: object {oid} failed integrity verification")
        target = destination.joinpath(*PurePosixPath(path).parts)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file() or target.read_bytes() != raw:
                raise ArchiveError(f"refusing to overwrite non-matching content: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
            with tmp.open("xb") as handle:
                handle.write(raw)
            os.chmod(tmp, 0o755 if mode == "100755" else 0o644)
            os.replace(tmp, target)
    return {"tranche": tranche_id, "restored": len(tranche["entries"]), "destination": str(destination)}


def check_growth(root: Path, *, base: str, limit: int) -> dict[str, Any]:
    root = root.resolve()
    listing = _run_git(root, "diff", "--name-only", "--diff-filter=A", "-z", base, "--", EVIDENCE_PREFIX)
    added = [p.decode("utf-8") for p in listing.split(b"\0") if p]
    failures: list[str] = []
    max_seen = 0
    for path in added:
        if "/.git/" in path or path.endswith("/.git"):
            failures.append(f"nested repository metadata added: {path}")
            continue
        if not _git_ok(root, "cat-file", "-e", f"HEAD:{path}"):
            continue
        size = int(str(_run_git(root, "cat-file", "-s", f"HEAD:{path}", text=True)).strip())
        max_seen = max(max_seen, size)
        if size > limit:
            failures.append(f"new evidence blob exceeds {limit} bytes: {path} ({size} bytes)")
    tracked = _run_git(root, "ls-files", "-z", "--", EVIDENCE_PREFIX)
    for raw in tracked.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if "/.git/" in path or path.endswith("/.git"):
            failures.append(f"nested repository metadata is tracked: {path}")
    evidence_root = root / ".agent/evidence"
    if evidence_root.is_dir():
        for directory, dirs, _files in os.walk(evidence_root, followlinks=False):
            for name in dirs:
                if name == ".git":
                    failures.append(
                        f"nested repository metadata present: "
                        f"{Path(directory, name).relative_to(root).as_posix()}"
                    )
    if failures:
        raise ArchiveError("; ".join(failures))
    return {"added": len(added), "max_bytes": max_seen, "limit": limit}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root (default: cwd).")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate or merge the archive index.")
    gen.add_argument("--feature", action="append", required=True, help="Completed feature id (repeatable).")
    gen.add_argument("--source", default="HEAD", help="Source revision whose tree holds the evidence.")
    gen.add_argument("--output", type=Path, default=None, help=f"Index path (default: {INDEX_REL}).")

    ver = sub.add_parser("verify", help="Verify index relations and bound Git objects.")
    ver.add_argument("--tranche", default=None)

    res = sub.add_parser("resolve-for-feature", help="Resolve one historical path for a completed feature.")
    res.add_argument("--feature", required=True)
    res.add_argument("--path", required=True)

    rst = sub.add_parser("restore", help="Restore one tranche outside the active checkout.")
    rst.add_argument("--tranche", required=True)
    rst.add_argument("--output", type=Path, required=True)

    gro = sub.add_parser("check-growth", help="Enforce bounded new evidence growth.")
    gro.add_argument("--base", required=True)
    gro.add_argument("--limit-bytes", type=int, default=DEFAULT_GROWTH_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.root
    try:
        if args.command == "generate":
            doc = generate(root, args.feature, source=args.source, output=args.output)
            print(
                f"ARCHIVE OK: {len(doc['tranches'])} tranche(s), "
                f"{sum(len(t['entries']) for t in doc['tranches'])} file(s), "
                f"{len(doc['objects'])} unique object(s)"
            )
        elif args.command == "verify":
            result = verify(root, tranche_id=args.tranche)
            print(
                f"ARCHIVE VERIFY OK: {result['tranches']} tranche(s), "
                f"{result['files']} file(s), features {','.join(result['features'])}"
            )
        elif args.command == "resolve-for-feature":
            result = resolve_for_feature(root, args.feature, args.path)
            print(
                f"ARCHIVE HISTORICAL OK: {result['path']} (tranche {result['tranche']}, "
                f"owner feature {result['owner_feature_id']}, integrity verified)"
            )
        elif args.command == "restore":
            result = restore(root, args.tranche, args.output)
            print(f"ARCHIVE RESTORE OK: {result['restored']} file(s) into {result['destination']}")
        elif args.command == "check-growth":
            result = check_growth(root, base=args.base, limit=args.limit_bytes)
            print(
                f"ARCHIVE GROWTH OK: {result['added']} added evidence file(s), "
                f"max {result['max_bytes']} bytes (limit {result['limit']})"
            )
        else:  # pragma: no cover - argparse enforces the set
            raise ArchiveError(f"unknown command: {args.command}")
    except ArchiveError as exc:
        print(f"ARCHIVE FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
