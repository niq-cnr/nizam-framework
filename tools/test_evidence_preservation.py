#!/usr/bin/env python3
"""Independent regression tests for tools/evidence_preservation.py."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TOOL = Path(__file__).resolve().parent / "evidence_preservation.py"


def run(*args: str, cwd: Path, expect: int = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(cwd), *args],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
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


def make_repo(parent: Path) -> Path:
    root = parent / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Preservation Test")
    git(root, "config", "user.email", "preserve@example.invalid")
    git(root, "remote", "add", "origin", "https://example.invalid/nizam.git")
    (root / "src").mkdir()
    (root / "src/input.txt").write_text("committed\n", encoding="utf-8")
    (root / "src/local.txt").write_text("untracked\n", encoding="utf-8")
    git(root, "add", "src/input.txt")
    git(root, "commit", "-q", "-m", "fixture")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nizam-preservation-test-") as raw:
        root = make_repo(Path(raw))
        out = root / ".agent/evidence/preservation"
        args = ("capture", "--path", "src/input.txt", "--path", "src/local.txt",
                "--output-dir", str(out), "--label", "check")

        first = run(*args, cwd=root)
        second = run(*args, cwd=root)
        objects = sorted((out / "objects").glob("*.json"))
        runs = sorted((out / "runs").glob("*.json"))
        assert len(objects) == 1, f"unchanged inputs created {len(objects)} inventory objects"
        assert len(runs) == 2, f"each run must keep its own receipt, found {len(runs)}"
        receipts = [json.loads(p.read_text(encoding="utf-8")) for p in runs]
        assert receipts[0]["run_id"] != receipts[1]["run_id"], "run identities collided"
        assert receipts[0]["inventory"] == receipts[1]["inventory"], "inventory reference drifted"

        digest = json.loads(objects[0].read_text(encoding="utf-8"))
        assert digest["tracked"][0][0] == "src/input.txt"
        assert digest["untracked"][0][0] == "src/local.txt"
        assert not any((out / name).exists() for name in ("repo", "worktree", "tree")), "worktree copy committed"

        # An uncommitted edit is not silently represented as committed content.
        (root / "src/input.txt").write_text("dirty\n", encoding="utf-8")
        run(*args, cwd=root)
        assert len(list((out / "objects").glob("*.json"))) == 1, "dirty worktree changed committed identity"

        git(root, "add", "src/input.txt")
        git(root, "commit", "-q", "-m", "change")
        changed = run(*args, cwd=root)
        assert len(list((out / "objects").glob("*.json"))) == 2, "committed change did not create a new inventory"
        new_digest = changed.stdout.rsplit(" ", 1)[-1].strip()

        mismatch = run(*args, "--baseline", "0" * 64, cwd=root, expect=1)
        assert "protected inputs changed" in mismatch.stderr
        run(*args, "--baseline", new_digest, cwd=root)

        # Interrupted writer leaves only an orphan temporary sibling; the next run succeeds.
        (out / "objects" / f"{new_digest}.json.tmp.orphan").write_text("partial", encoding="utf-8")
        run(*args, cwd=root)

        traversal = run(
            "capture", "--path", "../escape", "--output-dir", str(out), "--label", "bad",
            cwd=root, expect=1,
        )
        assert "normalized and relative" in traversal.stderr
        nested = run(
            "capture", "--path", ".agent/evidence/nested/.git/config", "--output-dir", str(out),
            "--label", "bad", cwd=root, expect=1,
        )
        assert "nested repository metadata" in nested.stderr

        conflict = out / "objects" / ("f" * 64 + ".json")
        conflict.write_text("different\n", encoding="utf-8")
        # A synthetic conflicting digest path is not reachable through a real
        # inventory, so assert the primitive directly through the module.
        import importlib.util

        spec = importlib.util.spec_from_file_location("preservation_under_test", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            module._atomic_exclusive(conflict, b"other\n")
        except module.PreservationError as exc:
            assert "already exists with different bytes" in str(exc)
        else:
            raise AssertionError("conflicting content-addressed write was accepted")
        module._atomic_exclusive(conflict, b"different\n")

    print("PASS preservation dedup/distinct-receipts/baseline/interruption/traversal/conflict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
