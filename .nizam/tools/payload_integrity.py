#!/usr/bin/env python3
"""Verify an installed .nizam/ payload against a trusted release commit tree or source root."""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

MODULES = ("standard", "templates", "schema", "tools", "methodology", "ecosystem")
PROVENANCE_KEYS = {"framework_version", "tag", "resolved_sha", "source_url", "installed_at"}
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class GovernanceDrift(Exception):
    """An installed file, directory, mode, or provenance record differs from the trusted pin."""


class ReferenceTreeUnavailable(Exception):
    """No trusted release commit tree or source root is reachable for content comparison."""


def _run_git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise GovernanceDrift(f"git {' '.join(args)}: {err}")
    return result.stdout


def _repo_has_commit(repo: Path, sha: str) -> bool:
    if not repo.is_dir():
        return False
    res = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    return res.returncode == 0


def _is_subpath_or_equal(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def _resolve_candidate_git_repo(
    *,
    payload: Path,
    git_repo: Path | None,
) -> Path | None:
    if git_repo is None:
        return None
    if git_repo.is_symlink() or not git_repo.is_dir():
        raise GovernanceDrift(f"git repository must be a real directory: {git_repo}")
    resolved_repo = git_repo.resolve()
    resolved_payload = payload.resolve()
    if _is_subpath_or_equal(resolved_repo, resolved_payload):
        raise GovernanceDrift(f"git repository reference must be outside payload directory: {resolved_repo}")
    return resolved_repo


def load_and_validate_provenance(
    payload: Path,
    *,
    expected_tag: str | None = None,
    expected_sha: str | None = None,
    expected_source_url: str | None = None,
    expected_framework_version: str | None = None,
) -> dict[str, str]:
    prov_path = payload / "provenance.json"
    try:
        st = prov_path.lstat()
    except OSError as exc:
        raise GovernanceDrift(f"unreadable provenance: {exc}") from exc
    if not stat.S_ISREG(st.st_mode):
        raise GovernanceDrift("provenance.json must be a regular file")
    try:
        provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GovernanceDrift(f"unreadable provenance: {exc}") from exc
    if not isinstance(provenance, dict) or set(provenance.keys()) != PROVENANCE_KEYS:
        raise GovernanceDrift("provenance must contain exactly the bootstrap-generated fields")
    for key in PROVENANCE_KEYS:
        val = provenance.get(key)
        if not isinstance(val, str) or not val:
            raise GovernanceDrift(f"provenance {key} must be a non-empty string")
    if not SHA40_RE.fullmatch(provenance["resolved_sha"]):
        raise GovernanceDrift(
            f"provenance resolved_sha is not a 40-character lowercase hex SHA: {provenance['resolved_sha']!r}"
        )
    timestamp = provenance["installed_at"]
    if not TIMESTAMP_RE.fullmatch(timestamp):
        raise GovernanceDrift("provenance installed_at is not a bootstrap UTC timestamp")
    try:
        datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise GovernanceDrift("provenance installed_at is not a valid date") from exc

    checks = {
        "framework_version": expected_framework_version,
        "tag": expected_tag,
        "resolved_sha": expected_sha,
        "source_url": expected_source_url,
    }
    for key, expected_val in checks.items():
        if expected_val is not None and provenance[key] != expected_val:
            raise GovernanceDrift(
                f"provenance {key} ({provenance[key]!r}) disagrees with trusted pin ({expected_val!r})"
            )

    nizam_path = payload / "NIZAM.json"
    try:
        nizam_doc = json.loads(nizam_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GovernanceDrift(f"unreadable NIZAM.json: {exc}") from exc
    fw_ver = nizam_doc.get("framework", {}).get("version") if isinstance(nizam_doc, dict) else None
    if not isinstance(fw_ver, str) or fw_ver != provenance["framework_version"]:
        raise GovernanceDrift(
            f"provenance framework_version ({provenance['framework_version']!r}) disagrees with NIZAM.json framework.version ({fw_ver!r})"
        )
    return provenance


def _walk_directory_inventory(root: Path, *, subpaths: tuple[str, ...] | None = None) -> dict[str, tuple[str, bytes]]:
    inventory: dict[str, tuple[str, bytes]] = {}
    targets: list[Path] = []
    if subpaths is None:
        targets.append(root)
    else:
        for rel in subpaths:
            p = root / rel
            if not p.exists() and not p.is_symlink():
                raise GovernanceDrift(f"reference source root is missing required entry: {rel}")
            targets.append(p)

    for target in targets:
        if target.is_symlink():
            raise GovernanceDrift(f"non-directory or symlink in payload: {target}")
        st = target.lstat()
        if stat.S_ISREG(st.st_mode):
            rel_posix = target.relative_to(root).as_posix()
            mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
            inventory[rel_posix] = (mode, target.read_bytes())
            continue
        if not stat.S_ISDIR(st.st_mode):
            raise GovernanceDrift(f"non-regular file in payload: {target}")
        for directory, dirs, files in os.walk(target, followlinks=False):
            dir_path = Path(directory)
            with os.scandir(dir_path) as it:
                for entry in it:
                    est = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(est.st_mode):
                        raise GovernanceDrift(f"non-directory or symlink in payload: {Path(entry.path)}")
                    if not stat.S_ISDIR(est.st_mode) and not stat.S_ISREG(est.st_mode):
                        raise GovernanceDrift(f"non-regular file in payload: {Path(entry.path)}")
            for name in dirs:
                item = dir_path / name
                if item.is_symlink() or not stat.S_ISDIR(item.lstat().st_mode):
                    raise GovernanceDrift(f"non-directory or symlink in payload: {item}")
            for name in files:
                item = dir_path / name
                lst = item.lstat()
                if not stat.S_ISREG(lst.st_mode):
                    raise GovernanceDrift(f"non-regular file in payload: {item}")
                rel_posix = item.relative_to(root).as_posix()
                mode = "100755" if lst.st_mode & stat.S_IXUSR else "100644"
                inventory[rel_posix] = (mode, item.read_bytes())
    return inventory


class _PayloadArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        print(f"PAYLOAD-INTEGRITY FAIL: argument error: {message}", file=sys.stderr)
        raise SystemExit(1)


def verify_payload_integrity(
    payload: Path,
    *,
    git_repo: Path | None = None,
    source_root: Path | None = None,
    expected_tag: str | None = None,
    expected_sha: str | None = None,
    expected_source_url: str | None = None,
    expected_framework_version: str | None = None,
    expected_file_count: int | None = None,
    require_tag_ref: bool = False,
    require_reference_tree: bool = False,
) -> dict[str, Any]:
    if payload.is_symlink() or not payload.is_dir():
        raise GovernanceDrift("payload root must be a real directory")
    resolved_payload = payload.resolve()

    if git_repo is not None and source_root is not None:
        raise GovernanceDrift("cannot combine --git-repo and --source-root")

    if expected_sha is not None and not SHA40_RE.fullmatch(expected_sha):
        raise GovernanceDrift(
            f"--expected-sha must be a 40-character lowercase hexadecimal commit SHA: {expected_sha!r}"
        )

    provenance = load_and_validate_provenance(
        payload,
        expected_tag=expected_tag,
        expected_sha=expected_sha,
        expected_source_url=expected_source_url,
        expected_framework_version=expected_framework_version,
    )

    tag = expected_tag or provenance["tag"]

    expected_git: dict[str, tuple[str, str]] = {}
    expected_fs: dict[str, tuple[str, bytes]] = {}
    ref_source = ""
    resolved_repo: Path | None = None
    content_integrity = ""

    if source_root is not None:
        if expected_sha is not None or require_reference_tree or require_tag_ref:
            raise GovernanceDrift(
                "--source-root performs an unbound directory comparison (directory_match_unbound) and cannot satisfy "
                "--expected-sha, --require-reference-tree, or --require-tag-ref; supply --git-repo with --expected-sha "
                "for commit-bound content-integrity verification"
            )
        if source_root.is_symlink() or not source_root.is_dir():
            raise GovernanceDrift(f"source root must be a real directory: {source_root}")
        resolved_source_root = source_root.resolve()
        if _is_subpath_or_equal(resolved_source_root, resolved_payload):
            raise GovernanceDrift(f"source root must be outside payload directory: {resolved_source_root}")
        expected_fs = _walk_directory_inventory(source_root, subpaths=(*MODULES, "NIZAM.json"))
        ref_source = f"source_root:{resolved_source_root}"
        expected_paths = set(expected_fs.keys())
        content_integrity = "directory_match_unbound"
    else:
        resolved_repo = _resolve_candidate_git_repo(
            payload=payload,
            git_repo=git_repo,
        )
        if resolved_repo is None:
            _walk_directory_inventory(payload)
            if expected_sha is not None or require_reference_tree or require_tag_ref:
                raise GovernanceDrift(
                    "commit-bound content-integrity verification requires an explicit --git-repo and 40-hex --expected-sha"
                )
            raise ReferenceTreeUnavailable(
                "no --git-repo or --source-root supplied for content comparison"
            )
        if not expected_sha:
            raise GovernanceDrift(
                "--git-repo verification requires an explicit 40-character lowercase hex --expected-sha "
                "(never derived solely from mutable provenance.json)"
            )
        sha = expected_sha
        tag_ref_check = subprocess.run(
            ["git", "-C", str(resolved_repo), "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if tag_ref_check.returncode == 0:
            tag_commit = tag_ref_check.stdout.strip()
            if tag_commit != sha:
                raise GovernanceDrift(f"local {tag} ({tag_commit}) does not resolve to the trusted commit ({sha})")
        elif require_tag_ref:
            raise GovernanceDrift(f"local {tag} does not resolve to the trusted commit")

        if not _repo_has_commit(resolved_repo, sha):
            raise GovernanceDrift(f"commit {sha} is not present in {resolved_repo}")

        for entry in _run_git(resolved_repo, "ls-tree", "-r", "-z", sha, "--", *MODULES, "NIZAM.json").split(b"\0"):
            if not entry:
                continue
            meta, path_bytes = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode("utf-8").split()
            if kind != "blob" or mode not in ("100644", "100755"):
                raise GovernanceDrift(f"unsupported pinned file type: {path_bytes!r}")
            expected_git[path_bytes.decode("utf-8")] = (mode, oid)
        ref_source = f"git:{resolved_repo}@{sha}"
        expected_paths = set(expected_git.keys())
        content_integrity = "verified"

    if "NIZAM.json" not in expected_paths:
        raise GovernanceDrift("trusted payload tree is missing its expected inventory")
    if expected_file_count is not None and len(expected_paths) != expected_file_count:
        raise GovernanceDrift("trusted payload tree is missing its expected inventory")

    actual_inventory = _walk_directory_inventory(payload)
    actual_paths = set(actual_inventory.keys())
    wanted_paths = expected_paths | {"provenance.json"}
    if actual_paths != wanted_paths:
        raise GovernanceDrift(
            f"file inventory drift: missing={sorted(wanted_paths - actual_paths)}, extra={sorted(actual_paths - wanted_paths)}"
        )

    if source_root is not None:
        for path, (expected_mode, expected_bytes) in sorted(expected_fs.items()):
            actual_mode, actual_bytes = actual_inventory[path]
            if actual_mode != expected_mode:
                raise GovernanceDrift(f"Git executable-mode drift: {path}")
            if actual_bytes != expected_bytes:
                raise GovernanceDrift(f"content drift: {path}")
    else:
        assert resolved_repo is not None
        for path, (expected_mode, oid) in sorted(expected_git.items()):
            actual_mode, actual_bytes = actual_inventory[path]
            if actual_mode != expected_mode:
                raise GovernanceDrift(f"Git executable-mode drift: {path}")
            if actual_bytes != _run_git(resolved_repo, "cat-file", "blob", oid):
                raise GovernanceDrift(f"content drift: {path}")

    return {
        "verified_files": len(expected_paths),
        "tag": provenance["tag"],
        "resolved_sha": provenance["resolved_sha"],
        "framework_version": provenance["framework_version"],
        "source_url": provenance["source_url"],
        "reference_source": ref_source,
        "content_integrity": content_integrity,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _PayloadArgumentParser(description=__doc__)
    parser.add_argument("--payload-dir", type=Path, required=True, help="Installed .nizam/ payload directory.")
    parser.add_argument("--git-repo", type=Path, default=None, help="Git repository containing the pinned commit/tag.")
    parser.add_argument("--source-root", type=Path, default=None, help="Unpacked framework release source root (unbound directory match only).")
    parser.add_argument("--expected-tag", default=None, help="Expected release tag in provenance.json.")
    parser.add_argument("--expected-sha", default=None, help="Expected 40-hex commit SHA in provenance.json and --git-repo.")
    parser.add_argument("--expected-source-url", default=None, help="Expected source_url in provenance.json.")
    parser.add_argument("--expected-framework-version", default=None, help="Expected framework_version in provenance.json.")
    parser.add_argument("--expected-file-count", type=int, default=None, help="Expected count of released files (excluding provenance.json).")
    parser.add_argument("--require-tag-ref", action="store_true", help="Require refs/tags/<tag>^{commit} in --git-repo.")
    parser.add_argument("--require-reference-tree", action="store_true", help="Exit 1 unless commit-bound reference verification succeeds.")
    args = parser.parse_args(argv)

    try:
        result = verify_payload_integrity(
            args.payload_dir.resolve(),
            git_repo=args.git_repo,
            source_root=args.source_root,
            expected_tag=args.expected_tag,
            expected_sha=args.expected_sha,
            expected_source_url=args.expected_source_url,
            expected_framework_version=args.expected_framework_version,
            expected_file_count=args.expected_file_count,
            require_tag_ref=args.require_tag_ref,
            require_reference_tree=args.require_reference_tree,
        )
    except ReferenceTreeUnavailable as exc:
        if args.require_reference_tree:
            print(f"PAYLOAD-INTEGRITY FAIL: {exc}", file=sys.stderr)
            return 1
        print(f"PAYLOAD-INTEGRITY UNCHECKED: {exc}")
        return 2
    except (GovernanceDrift, OSError) as exc:
        print(f"PAYLOAD-INTEGRITY FAIL: {exc}", file=sys.stderr)
        return 1

    if result["content_integrity"] == "directory_match_unbound":
        print(
            f"PAYLOAD-INTEGRITY DIRECTORY-MATCH (content_integrity=directory_match_unbound): "
            f"{result['verified_files']} files match unbound source root ({result['reference_source']}); "
            f"commit tree not verified"
        )
        return 0

    print(
        f"PAYLOAD-INTEGRITY PASS (content_integrity=verified): {result['verified_files']} released files + genuine provenance; "
        f"{result['tag']} at {result['resolved_sha']} ({result['reference_source']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
