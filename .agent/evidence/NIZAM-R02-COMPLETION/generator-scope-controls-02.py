#!/usr/bin/env python3
"""Exercise a proposed contract's SCOPE predicate in disposable real Git repos.

This checks the verification plan. It does not implement or qualify the product.
Only the command's pinned base literal is replaced by each fixture's real base.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


TASK = "NIZAM-R02-COMPLETION"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def save_json(path, data):
    save(path, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    framework = args.framework.resolve()
    contract_path = args.contract.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw_contract = contract_path.read_bytes()
    contract = json.loads(raw_contract)
    assert contract["contract_id"] == TASK
    command = shlex.split(next(v["command"] for v in contract["verification"] if v["id"] == "SCOPE"))
    assert command[:3] == ["PYTHONDONTWRITEBYTECODE=1", "python3", "-c"]
    assert len(command) == 4
    source = command[3]
    assert source.count(contract["source_revision"]) == 1
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    product_paths = ("tools/start_path.py", "tools/test_start_path.py")
    source_before = {p: sha((framework / p).read_bytes()) for p in product_paths}
    cases = [
        ("clean", 0, []),
        ("allowed-worktree", 0, []),
        ("allowed-staged", 0, []),
        ("versioned-review", 0, []),
        ("versioned-qa", 0, []),
        ("official-capture-reservation", 0, []),
        ("rename-outside-into-metadata", 1, ["README.md"]),
        ("masked-committed-path", 1, ["outside.txt"]),
        ("masked-staged-path", 1, ["outside.txt"]),
        ("outside-worktree", 1, ["outside.txt"]),
        ("untracked-outside", 1, ["new-outside.txt"]),
        ("unrelated-review", 1, [".agent/qa/OTHER-contract-review-01.json"]),
        ("unrelated-reservation", 1, [".agent/evidence/NIZAM-R02-COMPLETIONX-scope-attempt1.reservation.json"]),
        ("shared-state", 1, [".agent/run_state.json"]),
    ]
    results = []
    for case, expected_exit, expected_paths in cases:
        case_dir = output / case
        case_dir.mkdir()
        with tempfile.TemporaryDirectory(prefix="nizam-contract-scope-02-") as name:
            fixture = Path(name)

            def git(*argv):
                return subprocess.check_output([
                    "git", "-c", "user.name=Nizam contract fixture",
                    "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
                    *argv], cwd=fixture, env=env, stderr=subprocess.PIPE)

            def write(relative, content="fixture\n"):
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)

            git("init", "-q")
            write("README.md", "readme base\n")
            write("outside.txt", "outside base\n")
            write("tools/start_path.py", "product base\n")
            git("add", ".")
            git("commit", "-qm", "fixture base")
            base = git("rev-parse", "HEAD").decode().strip()
            if case in ("allowed-worktree", "allowed-staged"):
                write("tools/start_path.py", "allowed product edit\n")
                if case == "allowed-staged":
                    git("add", "tools/start_path.py")
            elif case == "versioned-review":
                write(".agent/qa/" + TASK + "-contract-review-01.json", "{}\n")
            elif case == "versioned-qa":
                write(".agent/qa/" + TASK + "-02.json", "{}\n")
            elif case == "official-capture-reservation":
                capture_argv = [sys.executable, str(framework / ".nizam/tools/start_path.py"),
                                "capture", "--id", TASK, "--step", "scope", "--attempt", "1",
                                "--output-dir", ".agent/evidence/" + TASK + "/scope-control-capture",
                                "--root", str(fixture), "--", sys.executable, "-c", "print('scope capture fixture')"]
                cap = subprocess.run(capture_argv, cwd=fixture, env=env, capture_output=True)
                save(case_dir / "capture.stdout.txt", cap.stdout)
                save(case_dir / "capture.stderr.txt", cap.stderr)
                save_json(case_dir / "capture.execution.json", {"argv": capture_argv, "cwd": str(fixture), "exit_code": cap.returncode})
                assert cap.returncode == 0, "official capture fixture setup failed"
                marker = fixture / (".agent/evidence/" + TASK + "-scope-attempt1.reservation.json")
                assert marker.is_file(), "official capture did not create its reservation"
                save(case_dir / "observed.reservation.json", marker.read_bytes())
            elif case == "rename-outside-into-metadata":
                dest = ".agent/evidence/" + TASK + "/borrowed-readme.md"
                (fixture / dest).parent.mkdir(parents=True)
                git("mv", "README.md", dest)
            elif case == "masked-committed-path":
                write("outside.txt", "undeclared committed edit\n")
                git("add", "outside.txt")
                git("commit", "-qm", "undeclared edit")
                git("restore", "--source", base, "--staged", "--worktree", "--", "outside.txt")
                assert git("diff", "--name-only", base, "HEAD", "--").decode().splitlines() == ["outside.txt"]
                assert git("diff", "--name-only", base, "--") == b""
                assert git("diff", "--cached", "--name-only", base, "--") == b""
            elif case == "masked-staged-path":
                write("outside.txt", "undeclared staged edit\n")
                git("add", "outside.txt")
                write("outside.txt", "outside base\n")
                assert git("diff", "--name-only", base, "--") == b""
                assert git("diff", "--cached", "--name-only", base, "--").decode().splitlines() == ["outside.txt"]
            elif case == "outside-worktree":
                write("outside.txt", "undeclared worktree edit\n")
            elif case == "untracked-outside":
                write("new-outside.txt")
            elif case in ("unrelated-review", "unrelated-reservation", "shared-state"):
                write(expected_paths[0], "{}\n")

            fixture_source = source.replace(contract["source_revision"], base, 1)
            argv = [sys.executable, "-c", fixture_source]
            started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            proc = subprocess.run(argv, cwd=fixture, env=env, capture_output=True)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            save(case_dir / "stdout.txt", proc.stdout)
            save(case_dir / "stderr.txt", proc.stderr)
            observed = json.loads(proc.stdout)
            ok = proc.returncode == expected_exit and observed["unexpected"] == expected_paths
            record = {"case": case, "argv": argv, "cwd": str(fixture), "started_at": started_at,
                      "completed_at": completed_at, "fixture_base": base,
                      "expected_exit": expected_exit, "exit_code": proc.returncode,
                      "expected_unexpected_paths": expected_paths, "observed": observed,
                      "stdout_sha256": sha(proc.stdout), "stderr_sha256": sha(proc.stderr),
                      "stdout_path": "stdout.txt", "stderr_path": "stderr.txt", "passed": ok,
                      "command_substitution": "Only the pinned baseline literal was replaced by the fixture base; projections, path policy and assertion are unchanged."}
            save_json(case_dir / "execution.json", record)
            results.append({"case": case, "passed": ok, "exit_code": proc.returncode,
                            "execution": case + "/execution.json"})
    after = {p: sha((framework / p).read_bytes()) for p in product_paths}
    assert source_before == after and contract_path.read_bytes() == raw_contract
    summary = {"purpose": "Pre-code verification-plan controls only; no product implementation or qualification",
               "contract_sha256": sha(raw_contract), "cases": results,
               "passed": all(r["passed"] for r in results), "source_before_sha256": source_before,
               "source_after_sha256": after, "contract_unchanged": True}
    save_json(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
