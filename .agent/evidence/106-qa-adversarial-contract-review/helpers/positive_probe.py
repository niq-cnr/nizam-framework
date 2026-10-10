#!/usr/bin/env python3
"""Faithful pinned implementation in a private scratch. Real tree is not modified."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

os.chdir(lib.REPO)
bad: list[str] = []


def expect(name: str, proc: subprocess.CompletedProcess[str], code: int, scratch: Path) -> None:
    print(lib.format_result(name, proc, scratch))
    if proc.returncode != code:
        bad.append(f"{name} rc={proc.returncode} expected {code}")


def matching_lines(text: str, patterns: list[str]) -> str:
    lines = []
    for pattern in patterns:
        hits = [line for line in text.splitlines() if re.search(pattern, line)]
        lines.append(f"PATTERN {pattern!r} hits={len(hits)}")
        lines.extend("  " + hit for hit in hits[:8])
    return "\n".join(lines)


def main() -> int:
    scratch_parent = Path(tempfile.mkdtemp(prefix="nizam-106-positive-"))
    tree = scratch_parent / "repo"
    try:
        lib.copy_tree(tree)
        sha = lib.approve_and_commit_base(tree)
        print(f"scratch B={sha[:12]} status flipped to approved inside the scratch only")
        lib.apply_faithful(tree, subset=True)
        # Worktree add would not copy these untracked files. S02 does not allowlist them.
        for relative in (
            ".agent/validator/106-mode-a.json",
            ".agent/evidence/106-qa-adversarial-contract-review",
        ):
            target = tree / relative
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        print("removed untracked paths a git worktree add from B would not contain")

        syntax = lib.run(["bash", "-n", "tools/fixtures_self_test.sh"], tree, timeout=30)
        expect("bash -n fixtures_self_test.sh", syntax, 0, tree)
        validate_text = (tree / "tools" / "validate.sh").read_text(encoding="utf-8")
        try:
            compile(lib.c13_python(validate_text), "<c13>", "exec")
            print("PASS compiled pinned C13 python")
        except SyntaxError as exc:
            print(f"FAIL compiled pinned C13 python {exc}")
            bad.append("c13 syntax")

        definitions = lib.load_s05_definitions(tree)
        ablate = definitions["ablate"]
        inner_parent = Path(tempfile.mkdtemp(prefix="nizam-106-cause-"))
        inner = inner_parent / "repo"
        try:
            shutil.copytree(tree, inner, symlinks=True)
            old = '"authoritative_source": "methodology/00_planning.md"'
            new = '"authoritative_source": "methodology/00_planning_moved.md"'
            index = inner / "NIZAM.json"
            raw = index.read_text(encoding="utf-8")
            if raw.count(old) != 1:
                raise SystemExit(f"planning source count {raw.count(old)}")
            index.write_text(raw.replace(old, new, 1), encoding="utf-8")
            moved = lib.run(["bash", "tools/validate.sh"], inner, timeout=180)
            print("### causation AT4 mutation (faithful subset) matching lines")
            print(matching_lines(moved.stdout + moved.stderr, [
                r"^\[C13\] FAIL",
                r"^\[C13\] PASS",
                r"^\[C4\] FAIL",
                r"^\[C4\] PASS",
                definitions["fragment"],
                r"methodology/00_planning\.md",
                r"methodology/00_planning_moved\.md",
            ]))
            print(f"causation validate rc={moved.returncode}")
            if moved.returncode != 1:
                bad.append(f"causation validate rc={moved.returncode}")
            namespace = {"root": inner, "Path": Path}
            exec(compile(ablate, "<ablate>", "exec"), namespace)  # noqa: S102
            ablated_py = lib.c13_python((inner / "tools" / "validate.sh").read_text(encoding="utf-8"))
            try:
                compile(ablated_py, "<c13-ablated>", "exec")
                print("PASS compiled ablated C13 python")
            except SyntaxError as exc:
                print(f"FAIL compiled ablated C13 python {exc}")
                bad.append("ablated syntax")
            ablated = lib.run(["bash", "tools/validate.sh"], inner, timeout=180)
            print("### causation after ablating the one subset line")
            print(matching_lines(ablated.stdout + ablated.stderr, [
                r"^\[C13\] FAIL",
                r"^\[C13\] PASS",
                r"^\[C4\] FAIL",
                r"^\[C4\] PASS",
                definitions["fragment"],
                r"methodology/00_planning\.md",
                r"methodology/00_planning_moved\.md",
            ]))
            print(f"ablated validate rc={ablated.returncode}")
            blob = ablated.stdout + ablated.stderr
            if ablated.returncode != 1 or re.search(r"^\[C13\] FAIL", blob, re.M) or not re.search(r"^\[C4\] FAIL", blob, re.M):
                bad.append("ablation did not keep C4 and drop C13")
        finally:
            shutil.rmtree(inner_parent, ignore_errors=True)

        commands = [
            ("S01", "s01-contract-valid.txt", 0, 120),
            ("S04", "s04-pinned-structure.txt", 0, 60),
            ("AT1", "at1-readme-skill-row.txt", 0, 30),
            ("AT2", "at2-subset.txt", 0, 30),
            ("AT5", "at5-no-c17.txt", 0, 180),
            ("AT4", "at4-planning-moved.txt", 0, 180),
            ("AT6", "at6-validator-gate.txt", 0, 180),
            ("AT7", "at7-validator-gate-payload.txt", 0, 180),
            ("S02-before-commit", "s02-attempt-root-delta.txt", 0, 60),
            ("S03-before-commit", "s03-scope-boundary.txt", 0, 60),
            ("S05", "s05-discriminating.txt", 0, 900),
            ("AT3", "at3-c13-substitute.txt", 0, 300),
            ("AT8", "at8-fixtures-self-test.txt", 0, 300),
        ]
        for name, suffix, code, timeout in commands:
            if name.startswith("S02"):
                command = lib.verification("s02-attempt-root-delta.txt")["command"]
            elif name.startswith("S03"):
                command = lib.verification("s03-scope-boundary.txt")["command"]
            else:
                command = lib.verification(suffix)["command"]
            proc = lib.run(command, tree, timeout=timeout)
            expect(name, proc, code, tree)
            if proc.returncode != code and name in {"S04", "AT4"}:
                print("stopping early after a structural or AT4 failure")
                break

        if not bad:
            subprocess.run(["git", "add", "--",
                            "NIZAM.json",
                            "tools/validate.sh",
                            "tools/fixtures_self_test.sh",
                            "tools/README.md",
                            "CHANGELOG.md",
                            "tools/fixtures/skill_index_neg_unindexed_capability.json",
                            ".agent/evidence/106/attempt-base.txt"], cwd=tree, check=True)
            subprocess.run(
                ["git", "commit", "-m", "feature 106 implementation (scratch only)"],
                cwd=tree,
                check=True,
                capture_output=True,
                text=True,
            )
            expect("S02-after-commit", lib.run(lib.verification("s02-attempt-root-delta.txt")["command"], tree, 60), 0, tree)
            expect("S03-after-commit", lib.run(lib.verification("s03-scope-boundary.txt")["command"], tree, 60), 0, tree)

        print("PROBE PROBLEMS:", bad)
        return 1 if bad else 0
    finally:
        shutil.rmtree(scratch_parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
