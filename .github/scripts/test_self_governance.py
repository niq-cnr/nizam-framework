#!/usr/bin/env python3
"""Exercise drift failures on private payload copies; keep the real install intact."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
VERIFIER = REPO / ".github/scripts/verify_self_governance.py"
ORIGINAL = REPO / ".nizam"


def check(payload: Path, expected_success: bool, name: str) -> None:
    result = subprocess.run([sys.executable, str(VERIFIER), "--payload-dir", str(payload)], text=True, capture_output=True)
    if (result.returncode == 0) != expected_success:
        raise AssertionError(f"{name}: unexpected exit {result.returncode}\n{result.stdout}{result.stderr}")
    print(f"PASS {name} (exit {result.returncode})")


def mutate(payload: Path, kind: str) -> None:
    target = payload / "standard/NDS.md"
    if kind == "bytes":
        target.write_bytes(target.read_bytes() + b"\nunauthorized change\n")
    elif kind == "missing":
        target.unlink()
    elif kind == "extra":
        (payload / "unexpected.txt").write_text("unexpected file\n")
    elif kind == "mode":
        target.chmod(target.stat().st_mode ^ stat.S_IXUSR)
    elif kind == "symlink":
        target.unlink()
        target.symlink_to(ORIGINAL / "standard/NDS.md")
    elif kind == "missing_provenance":
        (payload / "provenance.json").unlink()
    else:
        path = payload / "provenance.json"
        data = json.loads(path.read_text())
        key = {"tag": "tag", "sha": "resolved_sha", "source": "source_url", "time": "installed_at"}[kind]
        data[key] = "invalid"
        path.write_text(json.dumps(data))


def main() -> int:
    check(ORIGINAL, True, "original installation")
    with tempfile.TemporaryDirectory(prefix="self-governance-negatives-") as root:
        for kind in ("bytes", "missing", "extra", "mode", "symlink", "missing_provenance", "tag", "sha", "source", "time"):
            payload = Path(root) / kind
            shutil.copytree(ORIGINAL, payload)
            mutate(payload, kind)
            check(payload, False, kind)
        # A group-write permission difference is harmless under Git's mode model.
        payload = Path(root) / "umask"
        shutil.copytree(ORIGINAL, payload)
        target = payload / "standard/NDS.md"
        target.chmod(target.stat().st_mode ^ stat.S_IWGRP)
        check(payload, True, "umask-compatible permissions")
    check(ORIGINAL, True, "original still unchanged")
    print("SELF-GOVERNANCE TESTS PASS: 10 drift negatives; real installation preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
