#!/usr/bin/env python3
"""Verify the installed governance against its immutable released Git tree."""

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

TAG = "v1.5.0"
SHA = "f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852"
SOURCE = "https://github.com/niq-cnr/nizam-framework.git"
MODULES = ("standard", "templates", "schema", "tools", "methodology", "ecosystem")
REPO = Path(__file__).resolve().parents[2]


class GovernanceDrift(Exception):
    """An installed file or provenance record differs from the trusted pin."""


def git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True)
    if result.returncode:
        raise GovernanceDrift(f"git {' '.join(args)}: {result.stderr.decode().strip()}")
    return result.stdout


def verify(payload: Path) -> int:
    if payload.is_symlink() or not payload.is_dir():
        raise GovernanceDrift("payload root must be a real directory")
    if git("rev-parse", f"refs/tags/{TAG}^{{commit}}").decode().strip() != SHA:
        raise GovernanceDrift(f"local {TAG} does not resolve to the trusted commit")
    expected: dict[str, tuple[str, str]] = {}
    for entry in git("ls-tree", "-r", "-z", SHA, "--", *MODULES, "NIZAM.json").split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise GovernanceDrift(f"unsupported pinned file type: {path!r}")
        expected[path.decode()] = (mode, oid)
    if len(expected) != 238 or "NIZAM.json" not in expected:
        raise GovernanceDrift("trusted payload tree is missing its expected inventory")
    actual: set[str] = set()
    for directory, dirs, files in os.walk(payload, followlinks=False):
        for name in dirs:
            item = Path(directory) / name
            if item.is_symlink() or not stat.S_ISDIR(item.lstat().st_mode):
                raise GovernanceDrift(f"non-directory or symlink in payload: {item}")
        for name in files:
            item = Path(directory) / name
            if not stat.S_ISREG(item.lstat().st_mode):
                raise GovernanceDrift(f"non-regular file in payload: {item}")
            actual.add(item.relative_to(payload).as_posix())
    wanted = set(expected) | {"provenance.json"}
    if actual != wanted:
        raise GovernanceDrift(f"file inventory drift: missing={sorted(wanted - actual)}, extra={sorted(actual - wanted)}")
    try:
        provenance = json.loads((payload / "provenance.json").read_text())
    except (OSError, ValueError) as error:
        raise GovernanceDrift(f"unreadable provenance: {error}") from error
    keys = {"framework_version", "tag", "resolved_sha", "source_url", "installed_at"}
    if not isinstance(provenance, dict) or set(provenance) != keys:
        raise GovernanceDrift("provenance must contain exactly the bootstrap-generated fields")
    for key, value in {"framework_version": "1.5.0", "tag": TAG, "resolved_sha": SHA, "source_url": SOURCE}.items():
        if provenance[key] != value:
            raise GovernanceDrift(f"provenance {key} disagrees with trusted pin")
    timestamp = provenance["installed_at"]
    if not isinstance(timestamp, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp):
        raise GovernanceDrift("provenance installed_at is not a bootstrap UTC timestamp")
    try:
        datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise GovernanceDrift("provenance installed_at is not a valid date") from error
    for path, (mode, oid) in expected.items():
        item = payload / path
        # Git records the owner executable bit, not group-write/umask permissions.
        actual_mode = "100755" if item.stat().st_mode & stat.S_IXUSR else "100644"
        if actual_mode != mode:
            raise GovernanceDrift(f"Git executable-mode drift: {path}")
        if item.read_bytes() != git("cat-file", "blob", oid):
            raise GovernanceDrift(f"content drift: {path}")
    return len(expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-dir", type=Path, default=REPO / ".nizam")
    args = parser.parse_args()
    try:
        count = verify(args.payload_dir.absolute())
    except (GovernanceDrift, OSError) as error:
        print(f"SELF-GOVERNANCE FAIL: {error}", file=sys.stderr)
        return 1
    print(f"SELF-GOVERNANCE PASS: {count} released files + genuine provenance; {TAG} at {SHA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
