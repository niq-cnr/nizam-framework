#!/usr/bin/env python3
"""Independent regression tests for tools/evidence_archive.py.

Synthetic repositories only. No historical feature evidence is required.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TOOL = Path(__file__).resolve().parent / "evidence_archive.py"
ROOT = TOOL.parent.parent


def run(*args: str, cwd: Path, expect: int = 0) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(cwd), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {proc.returncode}: {' '.join(args)}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return proc


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def make_repo(parent: Path) -> Path:
    root = parent / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Archive Test")
    git(root, "config", "user.email", "archive@example.invalid")
    git(root, "remote", "add", "origin", "https://example.invalid/nizam.git")
    (root / ".agent/evidence/900").mkdir(parents=True)
    (root / ".agent/evidence/900/hello.txt").write_text("hello\n", encoding="utf-8")
    script = root / ".agent/evidence/900/run.sh"
    script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    script.chmod(0o755)
    (root / ".agent/contracts").mkdir()
    (root / ".agent/contracts/900.json").write_text('{"feature_id":"900"}\n', encoding="utf-8")
    (root / ".agent/qa").mkdir()
    (root / ".agent/qa/900.json").write_text(
        json.dumps(
            {
                "qa_pass": True,
                "evidence_files": [".agent/evidence/900/hello.txt", ".agent/evidence/900/run.sh"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / ".agent/feature_list_900.json").write_text(
        json.dumps(
            {
                "phase": "900-test",
                "spec_version": "1.0.0",
                "original_estimate_lines": 1,
                "features": [
                    {
                        "id": "900",
                        "name": "archive fixture",
                        "description": "synthetic",
                        "status": "complete",
                        "dependencies": [],
                        "acceptance_tests": ["synthetic"],
                        "estimated_lines": 1,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    commit(root, "fixture")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nizam-archive-test-") as raw:
        parent = Path(raw)
        root = make_repo(parent)
        source = git(root, "rev-parse", "HEAD")
        out = root / ".agent/evidence-archive/index.json"

        run("generate", "--feature", "900", "--source", source, cwd=root)
        first = out.read_bytes()
        run("generate", "--feature", "900", "--source", source, cwd=root)
        assert out.read_bytes() == first, "generation is not deterministic"
        run("verify", cwd=root)
        run("resolve-for-feature", "--feature", "900", "--path", ".agent/evidence/900/hello.txt", cwd=root)

        shutil.rmtree(root / ".agent/evidence/900")
        commit(root, "remove working evidence")
        run("verify", cwd=root)
        run("resolve-for-feature", "--feature", "900", "--path", ".agent/evidence/900/hello.txt", cwd=root)

        restored = parent / "restored"
        run("restore", "--tranche", "feature-900", "--output", str(restored), cwd=root)
        assert (restored / ".agent/evidence/900/hello.txt").read_text() == "hello\n"
        assert os.stat(restored / ".agent/evidence/900/run.sh").st_mode & 0o111, "executable mode lost"
        again = run("restore", "--tranche", "feature-900", "--output", str(restored), cwd=root)
        assert "RESTORE OK" in again.stdout

        inside = run(
            "restore", "--tranche", "feature-900", "--output", str(root / "hydrate"), cwd=root, expect=1
        )
        assert "outside the active checkout" in inside.stderr

        (restored / ".agent/evidence/900/hello.txt").write_text("tampered\n", encoding="utf-8")
        overwrite = run("restore", "--tranche", "feature-900", "--output", str(restored), cwd=root, expect=1)
        assert "refusing to overwrite" in overwrite.stderr

        contract = root / ".agent/contracts/900.json"
        original = contract.read_bytes()
        contract.write_text('{"feature_id":"900","changed":true}\n', encoding="utf-8")
        changed = run(
            "resolve-for-feature", "--feature", "900", "--path", ".agent/evidence/900/hello.txt",
            cwd=root, expect=1,
        )
        assert "changed contract" in changed.stderr
        contract.write_bytes(original)

        doc = json.loads(out.read_text(encoding="utf-8"))
        digest = doc["tranches"][0]["entries"][0][2]
        doc["objects"][digest][0] = "0" * 40
        out.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        broken = run("verify", cwd=root, expect=1)
        assert "missing Git object" in broken.stderr

        doc = json.loads(first.decode("utf-8"))
        doc["tranches"][0]["entries"][0][0] = "../escape"
        out.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        traversal = run("verify", cwd=root, expect=1)
        assert "normalized relative path" in traversal.stderr

        out.write_bytes(first)
        base = git(root, "rev-parse", "HEAD")
        large = root / ".agent/evidence/901"
        large.mkdir(parents=True)
        (large / "big.bin").write_bytes(b"x" * 2048)
        commit(root, "large evidence")
        growth = run("check-growth", "--base", base, "--limit-bytes", "1024", cwd=root, expect=1)
        assert "exceeds" in growth.stderr
        ok = run("check-growth", "--base", base, "--limit-bytes", "4096", cwd=root)
        assert "GROWTH OK" in ok.stdout

        nested = root / ".agent/evidence/901/nested"
        nested.mkdir(parents=True)
        git(nested, "init", "-q")
        nested_fail = run("check-growth", "--base", base, cwd=root, expect=1)
        assert "nested repository metadata" in nested_fail.stderr

    print("PASS evidence archive generate/verify/resolve/restore/determinism/failure-modes/growth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
