#!/usr/bin/env python3
"""External diagnostic probe; does not modify framework product or installed payload."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def observation(path):
    if path.is_symlink():
        raw = os.fsencode(os.readlink(path))
        return {"kind": "symlink", "target_sha256": digest(raw)}
    if not path.exists():
        return {"kind": "missing"}
    return {"kind": "file", "sha256": digest(path.read_bytes()),
            "executable": bool(path.stat().st_mode & 0o111)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    framework = args.framework.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source_paths = ["tools/start_path.py", "tools/test_start_path.py"]
    before_hashes = {p: digest((framework / p).read_bytes()) for p in source_paths}
    spec = importlib.util.spec_from_file_location("existing_start_path_test_helpers",
                                                framework / "tools/test_start_path.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    records = []

    def setup_git(root, *argv):
        subprocess.run(["git", "-C", str(root), *argv], env=env,
                       check=True, capture_output=True)

    for name in ("F1-approved-schema", "F1-proposed-guard", "F2-tracked-unchanged",
                 "F2-tracked-mutated", "F2-untracked-mutated", "F2-index-mutated",
                 "F2-mode-mutated", "F2-symlink-mutated", "F2-rename-mutated"):
        case_dir = output / name
        case_dir.mkdir()
        events = []

        def run_record(root, label, argv):
            started = stamp()
            result = subprocess.run(argv, cwd=root, env=env, check=False,
                                    capture_output=True)
            ended = stamp()
            out = case_dir / (label + ".stdout.txt")
            err = case_dir / (label + ".stderr.txt")
            with out.open("xb") as stream:
                stream.write(result.stdout)
            with err.open("xb") as stream:
                stream.write(result.stderr)
            events.append({"label": label, "argv": argv, "cwd": str(root),
                           "started_at": started, "completed_at": ended,
                           "exit_code": result.returncode,
                           "stdout": {"path": out.name, "sha256": digest(result.stdout)},
                           "stderr": {"path": err.name, "sha256": digest(result.stderr)}})
            return result

        with tempfile.TemporaryDirectory(prefix="nizam-f1f2-probe-") as temp:
            root = Path(temp).resolve()
            task_id = "probe"
            (root / "README.md").write_text("baseline\n", encoding="utf-8")
            outside = root / "outside.py"
            outside.write_text("".join("line %d\n" % n for n in range(30)), encoding="utf-8")
            schema = root / "schema" / "example.schema.json"
            schema.parent.mkdir()
            schema.write_text("{}\n", encoding="utf-8")
            if name == "F2-symlink-mutated":
                outside.unlink()
                outside.symlink_to("target-0")
            setup_git(root, "init", "-q")
            setup_git(root, "config", "user.name", "Nizam Diagnostic Fixture")
            setup_git(root, "config", "user.email", "fixture@example.invalid")
            setup_git(root, "config", "core.filemode", "true")
            setup_git(root, "config", "commit.gpgsign", "false")
            setup_git(root, "config", "core.hooksPath", os.devnull)
            setup_git(root, "add", "--", "README.md", "outside.py", "schema/example.schema.json")
            setup_git(root, "commit", "-qm", "fixture baseline")
            if name.startswith("F1"):
                helpers.write(root, ".agent/contracts/c1.json",
                              helpers.contract("approved" if name == "F1-approved-schema" else "proposed",
                                               ["schema/example.schema.json"]))
                helpers.write(root, ".agent/evidence/probe-cause.json", helpers.cause(task_id))
                helpers.write(root, ".agent/evidence/probe-scope.json",
                              helpers.scope(task_id, ["schema/example.schema.json"], "c1"))
                route = "bugfix"
            else:
                if name == "F2-untracked-mutated":
                    outside = root / "untracked.py"
                    outside.write_text("pre-existing\n", encoding="utf-8")
                elif name == "F2-symlink-mutated":
                    outside.unlink()
                    outside.symlink_to("target-1")
                elif name == "F2-rename-mutated":
                    setup_git(root, "mv", "outside.py", "renamed.py")
                    outside = root / "renamed.py"
                else:
                    outside.write_text("pre-existing\n", encoding="utf-8")
                    if name == "F2-index-mutated":
                        setup_git(root, "add", "--", "outside.py")
                helpers.write(root, ".agent/evidence/probe-intent.json",
                              {"id": task_id, "path": "small-change", "summary": "Update README only",
                               "needs_new_contract": False, "files": ["README.md"]})
                route = "small-change"
            observed_before = observation(outside)
            status_before = run_record(root, "status-before", ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"])
            begin = run_record(root, "begin", [sys.executable, str(framework / "tools/start_path.py"),
                                               "begin", route, "--id", task_id, "--root", str(root)])
            if name == "F1-proposed-guard":
                requirement_met = begin.returncode == 1 and b"not already approved" in begin.stderr
                observed_exit = begin.returncode
                expected_exit = 1
            else:
                if begin.returncode != 0:
                    raise RuntimeError("fixture begin failed unexpectedly: " + name)
                marker = root / ".agent/evidence/probe-base.json"
                with (case_dir / "observed-task-base.json").open("xb") as stream:
                    stream.write(marker.read_bytes())
                if name == "F1-approved-schema":
                    schema.write_text('{"type":"object"}\n', encoding="utf-8")
                else:
                    (root / "README.md").write_text("task change\n", encoding="utf-8")
                    if name == "F2-mode-mutated":
                        outside.chmod(stat.S_IMODE(outside.stat().st_mode) | 0o100)
                    elif name == "F2-symlink-mutated":
                        outside.unlink()
                        outside.symlink_to("target-2")
                    elif name == "F2-rename-mutated":
                        outside.write_text(outside.read_text().replace("line 10\n", "new 10\n"), encoding="utf-8")
                        setup_git(root, "add", "--", "renamed.py")
                    elif name != "F2-tracked-unchanged":
                        outside.write_text("new undeclared task change\n", encoding="utf-8")
                        if name == "F2-index-mutated":
                            setup_git(root, "add", "--", "outside.py")
                evidence = ".agent/evidence/probe-qa.txt"
                (root / evidence).write_text("fixture QA output, no production acceptance claim\n", encoding="utf-8")
                helpers.write(root, ".agent/qa/probe.json", helpers.qa(task_id, evidence))
                status_after = run_record(root, "status-after", ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"])
                done = run_record(root, "done", [sys.executable, str(framework / "tools/start_path.py"),
                                                 "done", route, "--id", task_id, "--root", str(root)])
                expected_exit = 0 if name in ("F1-approved-schema", "F2-tracked-unchanged") else 1
                observed_exit = done.returncode
                requirement_met = observed_exit == expected_exit
            record = {"case": name, "expected_exit": expected_exit, "actual_exit": observed_exit,
                      "requirement_met": requirement_met, "before": observed_before,
                      "after": observation(outside), "events": events}
            save_json(case_dir / "execution.json", record)
            records.append({k: record[k] for k in ("case", "expected_exit", "actual_exit", "requirement_met")})
            print(json.dumps(records[-1], sort_keys=True), flush=True)
    after_hashes = {p: digest((framework / p).read_bytes()) for p in source_paths}
    if before_hashes != after_hashes:
        raise RuntimeError("framework product source changed during diagnostic")
    failures = sum(not row["requirement_met"] for row in records)
    save_json(output / "summary.json", {"source_revision": "00e0bcb1bd16ba2ddaf5774153bbf2c1e05244a6",
              "framework": str(framework), "source_before_sha256": before_hashes,
              "source_after_sha256": after_hashes, "cases": records,
              "requirements_failed": failures, "role": "Planner diagnostic; not acceptance",
              "scope": "F1/F2 only", "completed_at": stamp()})
    print("F1F2_BASELINE cases=%d requirements_failed=%d" % (len(records), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
