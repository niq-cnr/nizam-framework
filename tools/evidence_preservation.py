#!/usr/bin/env python3
"""Bounded, content-addressed preservation inventories for new evidence.

Historical captures sometimes copied an entire working tree per run, which
multiplied identical bytes across evidence files. This tool replaces that
pattern with one deterministic inventory per protected input set:

  * the inventory is derived from an explicit list of repository-relative
    paths, never a recursive whole-tree walk;
  * committed content is bound by commit, tree, blob id, mode, byte length and
    raw-byte SHA-256;
  * inventory content is stored once under its SHA-256 digest
    (``objects/<sha256>.json``); unchanged reruns reuse the same object;
  * every run keeps its own receipt (run id, command, producer, timestamps,
    exit status, inventory reference) under ``runs/<run-id>.json``;
  * writes are exclusive/atomic, so an interrupted or concurrent writer can
    never silently overwrite immutable content.

This tool does not execute restored content, does not copy worktrees, and does
not replace the existing command-capture contract. It is an additive producer
helper for captures that genuinely need input-integrity evidence.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import secrets
import subprocess
import sys
from typing import Any, Iterable

DEFAULT_ROOT = Path(".")
INVENTORY_SCHEMA_VERSION = 1


class PreservationError(Exception):
    """An invalid path, a conflicting digest, or an unsafe concurrent write."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PreservationError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _normalize(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise PreservationError("protected path must be a non-empty string")
    if "\x00" in path or "\\" in path:
        raise PreservationError(f"protected path contains an illegal character: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in ("..", "") for part in pure.parts):
        raise PreservationError(f"protected path is not normalized and relative: {path!r}")
    normalized = pure.as_posix()
    if normalized != path:
        raise PreservationError(f"protected path is not canonical: {path!r} -> {normalized!r}")
    if "/.git/" in normalized or normalized.endswith("/.git"):
        raise PreservationError(f"nested repository metadata is not preservable: {path!r}")
    return normalized


def _atomic_exclusive(path: Path, raw: bytes) -> bool:
    """Publish content atomically. Return False when identical content already exists.

    The payload is written to a unique temporary sibling, fsynced, then linked
    into place. An interrupted writer leaves only an orphan temporary file; the
    immutable destination is either absent or complete. A concurrent writer
    with different bytes fails closed instead of overwriting.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}.{secrets.token_hex(4)}")
    with temporary.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
        return True
    except FileExistsError:
        existing = path.read_bytes()
        if existing != raw:
            raise PreservationError(
                f"content-addressed preservation path already exists with different bytes: {path}"
            )
        return False
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _tracked_blob(root: Path, commit: str, rel: str) -> tuple[str, str, int, str] | None:
    listing = _git(root, "ls-tree", "-z", commit, "--", f":(literal){rel}")
    if not listing.strip(b"\0"):
        return None
    entries = [entry for entry in listing.split(b"\0") if entry]
    if len(entries) != 1:
        raise PreservationError(f"protected path is ambiguous in the tree: {rel}")
    meta, path = entries[0].split(b"\t", 1)
    mode, kind, oid = meta.decode("utf-8").split()
    if path.decode("utf-8") != rel:
        raise PreservationError(f"protected path resolved differently: {rel}")
    if kind != "blob" or mode not in ("100644", "100755"):
        raise PreservationError(f"protected path is not a regular file: {rel}")
    raw = _git(root, "cat-file", "blob", oid)
    return mode, oid, len(raw), _sha256(raw)


def build_inventory(root: Path, paths: Iterable[str], *, commit: str = "HEAD") -> dict[str, Any]:
    root = root.resolve()
    resolved_commit = _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    tree = _git(root, "rev-parse", "--verify", f"{resolved_commit}^{{tree}}").decode().strip()
    normalized: list[str] = sorted({_normalize(path) for path in paths})
    if not normalized:
        raise PreservationError("at least one protected path is required")
    entries: list[list[Any]] = []
    untracked: list[list[Any]] = []
    for rel in normalized:
        tracked = _tracked_blob(root, resolved_commit, rel)
        if tracked is not None:
            mode, oid, size, digest = tracked
            entries.append([rel, mode, oid, size, digest])
            continue
        target = root / rel
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise PreservationError(f"protected untracked path is not a regular file: {rel}")
        if not target.is_file():
            raise PreservationError(f"protected path is neither tracked nor present: {rel}")
        raw = target.read_bytes()
        untracked.append([rel, "untracked", len(raw), _sha256(raw)])
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "repository": {
            "origin": _git(root, "remote", "get-url", "origin").decode().strip(),
            "commit": resolved_commit,
            "tree": tree,
        },
        "tracked": entries,
        "untracked": untracked,
    }


def capture(
    root: Path,
    paths: Iterable[str],
    *,
    output_dir: Path,
    label: str,
    argv: list[str] | None = None,
    agent_id: str = "nizam-local-agent",
    session_id: str = "local-session",
    exit_status: int = 0,
    baseline: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not label or "/" in label or "\x00" in label:
        raise PreservationError("label must be a single safe token")
    inventory = build_inventory(root, paths)
    raw = canonical_bytes(inventory)
    digest = _sha256(raw)
    if baseline is not None and baseline != digest:
        raise PreservationError(
            f"protected inputs changed: expected inventory {baseline}, observed {digest}"
        )

    object_dir = output_dir / "objects"
    object_dir.mkdir(parents=True, exist_ok=True)
    _atomic_exclusive(object_dir / f"{digest}.json", raw)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{label}-{stamp}-{secrets.token_hex(4)}"
    receipt = {
        "schema_version": 1,
        "run_id": run_id,
        "label": label,
        "producer": {"agent_id": agent_id, "session_id": session_id},
        "argv": argv or [],
        "runtime": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "exit_status": exit_status,
        "inventory": {
            "path": (object_dir / f"{digest}.json").relative_to(output_dir).as_posix(),
            "sha256": digest,
            "tracked": len(inventory["tracked"]),
            "untracked": len(inventory["untracked"]),
        },
    }
    run_dir = output_dir / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    _atomic_exclusive(run_dir / f"{run_id}.json", canonical_bytes(receipt))
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture", help="Record a bounded preservation inventory and run receipt.")
    cap.add_argument("--path", action="append", required=True, help="Protected repository-relative path (repeatable).")
    cap.add_argument("--output-dir", type=Path, required=True)
    cap.add_argument("--label", required=True)
    cap.add_argument("--argv", nargs=argparse.REMAINDER, default=[])
    cap.add_argument("--agent-id", default="nizam-local-agent")
    cap.add_argument("--session-id", default="local-session")
    cap.add_argument("--exit-status", type=int, default=0)
    cap.add_argument("--baseline", default=None, help="Fail when the inventory digest differs from this baseline.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "capture":
            receipt = capture(
                args.root,
                args.path,
                output_dir=args.output_dir,
                label=args.label,
                argv=args.argv,
                agent_id=args.agent_id,
                session_id=args.session_id,
                exit_status=args.exit_status,
                baseline=args.baseline,
            )
            print(
                f"PRESERVATION OK: {receipt['inventory']['tracked']} tracked + "
                f"{receipt['inventory']['untracked']} untracked input(s), "
                f"inventory {receipt['inventory']['sha256']}"
            )
        else:  # pragma: no cover
            raise PreservationError(f"unknown command: {args.command}")
    except PreservationError as exc:
        print(f"PRESERVATION FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
