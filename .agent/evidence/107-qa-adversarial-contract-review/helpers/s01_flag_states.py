#!/usr/bin/env python3
"""Run contract 107's S01 command on temp flag states. Does not write the contract."""

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)

CONTRACT_PATH = Path(".agent/contracts/107.json")
B = "839c52aef6a7a1cb0c21de1101d570718ffb2136"
LOAD = 'json.load(open(".agent/contracts/107.json"))'
PREFIX = "python3 - <<'PY'\n"
SUFFIX = "\nPY"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff_paths(old, new, prefix=""):
    found = []

    def walk(left, right, name):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                child = f"{name}.{key}" if name else key
                if key not in left:
                    found.append(child + " ADDED")
                elif key not in right:
                    found.append(child + " REMOVED")
                else:
                    walk(left[key], right[key], child)
            return
        if isinstance(left, list) and isinstance(right, list):
            if len(left) != len(right):
                found.append(f"{name} LEN {len(left)} -> {len(right)}")
            for index, (item_left, item_right) in enumerate(zip(left, right)):
                walk(item_left, item_right, f"{name}[{index}]")
            return
        if left != right:
            found.append(name)

    walk(old, new, prefix)
    return found


def run(argv, env=None):
    return subprocess.run(
        argv,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def show(label, proc):
    print(f"--- {label} rc={proc.returncode}")
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print("--- stderr")
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")


def main():
    before = sha256(CONTRACT_PATH)
    raw = CONTRACT_PATH.read_bytes()
    contract = json.loads(raw)
    command = next(
        item["command"]
        for item in contract["verification"]
        if item.get("supplementary") and item["acceptance_test"].startswith("Supplementary S01")
    )
    acceptance = next(
        item["acceptance_test"]
        for item in contract["verification"]
        if item.get("supplementary") and item["acceptance_test"].startswith("Supplementary S01")
    )
    if not command.startswith(PREFIX) or not command.endswith(SUFFIX):
        print("HARNESS: S01 command is not a python3 heredoc")
        return 1
    if command.count(LOAD) != 1:
        print("HARNESS: contract load count", command.count(LOAD))
        return 1
    if 'if contract["status"] == "approved":' not in command:
        print("HARNESS: approved branch missing from S01 command")
        return 1
    inner = command[len(PREFIX) : -len(SUFFIX)]
    redirected = "import os\n" + inner.replace(
        LOAD, 'json.load(open(os.environ["S01_CONTRACT"]))', 1
    )
    approvals = contract["approvals"]
    print(
        "REAL status=%s revisions=%s validator_mode_a=%s evaluator_contract_review=%s approved_at=%s"
        % (
            contract["status"],
            approvals.get("revisions"),
            approvals.get("validator_mode_a"),
            approvals.get("evaluator_contract_review"),
            "approved_at" in approvals,
        )
    )
    print("ACCEPTANCE", acceptance)
    print("PREDICATE_HAS_APPROVED_BRANCH", True)
    print("PREDICATE_HAS_ELSE_FALSE_FLAGS", "approvals are not false at revision 0" in command)

    baseline_ok = (
        contract["status"] == "proposed"
        and approvals.get("revisions") == 0
        and approvals.get("validator_mode_a") is False
        and approvals.get("evaluator_contract_review") is False
        and "approved_at" not in approvals
    )
    if not baseline_ok:
        print("HARNESS: working tree is not proposed with both flags false")
        return 1

    problems = []
    unmodified = run(["bash", "-c", command])
    show("UNMODIFIED_S01 proposed_both_false", unmodified)
    if unmodified.returncode != 0 or "problems: []" not in unmodified.stdout:
        problems.append("unmodified proposed both false")

    with tempfile.TemporaryDirectory(prefix="107-s01-flags-") as tmp:
        tmp_path = Path(tmp)
        script_path = tmp_path / "s01_redirect.py"
        script_path.write_text(redirected)

        def one(name, status, validator, evaluator, revisions, expect_rc, expect_text):
            data = copy.deepcopy(contract)
            data["status"] = status
            data["approvals"]["revisions"] = revisions
            data["approvals"]["validator_mode_a"] = validator
            data["approvals"]["evaluator_contract_review"] = evaluator
            path = tmp_path / (name + ".json")
            path.write_text(json.dumps(data))
            env = os.environ.copy()
            env["S01_CONTRACT"] = str(path)
            proc = run([sys.executable, str(script_path)], env=env)
            show(
                "%s status=%s revisions=%s validator=%s evaluator=%s expect_rc=%s"
                % (name, status, revisions, validator, evaluator, expect_rc),
                proc,
            )
            if proc.returncode != expect_rc or expect_text not in proc.stdout or proc.stderr:
                problems.append(name)

        one(
            "REDIRECT_CONTROL",
            "proposed",
            False,
            False,
            0,
            0,
            "problems: []",
        )
        one("APPROVED_BOTH_TRUE", "approved", True, True, 0, 0, "problems: []")
        one("APPROVED_BOTH_FALSE", "approved", False, False, 0, 1, "approved revision 0 does not have both approval flags true")
        one("PROPOSED_BOTH_TRUE", "proposed", True, True, 0, 1, "approvals are not false at revision 0")
        one("APPROVED_VALIDATOR_ONLY", "approved", True, False, 0, 1, "approved revision 0 does not have both approval flags true")
        one("APPROVED_EVALUATOR_ONLY", "approved", False, True, 0, 1, "approved revision 0 does not have both approval flags true")
        one("PROPOSED_VALIDATOR_ONLY", "proposed", True, False, 0, 1, "approvals are not false at revision 0")
        one("PROPOSED_EVALUATOR_ONLY", "proposed", False, True, 0, 1, "approvals are not false at revision 0")
        one("APPROVED_REV1_BOTH_TRUE", "approved", True, True, 1, 1, "approved revision 0 does not have both approval flags true")
        one("PROPOSED_REV1_BOTH_FALSE", "proposed", False, False, 1, 1, "approvals are not false at revision 0")

        control_stdout = None
        # one() already checked REDIRECT_CONTROL. Compare its stdout to the unmodified command
        # by replaying the same temp file, which one() left in the directory.
        env = os.environ.copy()
        env["S01_CONTRACT"] = str(tmp_path / "REDIRECT_CONTROL.json")
        replay = run([sys.executable, str(script_path)], env=env)
        control_stdout = replay.stdout
        print("--- REDIRECT_EQUALS_UNMODIFIED", control_stdout == unmodified.stdout)
        if control_stdout != unmodified.stdout:
            problems.append("redirect control stdout differs from unmodified S01")

    shown = subprocess.run(
        ["git", "show", B + ":.agent/contracts/107.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    approved = json.loads(shown.stdout)
    paths = diff_paths(approved, contract)
    print("DIFF_PATHS_VS_B", len(paths))
    for path in paths:
        print("PATH", path)
    same_commands = []
    for index, (left, right) in enumerate(zip(approved["verification"], contract["verification"])):
        if left.get("command") == right.get("command") and left.get("acceptance_test") == right.get("acceptance_test"):
            same_commands.append(index)
        else:
            print(
                "VERIFICATION_CHANGED",
                index,
                "command",
                left.get("command") != right.get("command"),
                "acceptance_test",
                left.get("acceptance_test") != right.get("acceptance_test"),
                "expected_outcome",
                left.get("expected_outcome") != right.get("expected_outcome"),
            )
    print("VERIFICATION_UNCHANGED_INDEXES", same_commands)
    if len(approved["verification"]) != len(contract["verification"]):
        problems.append("verification length changed")
    changed_indexes = [
        index
        for index, (left, right) in enumerate(zip(approved["verification"], contract["verification"]))
        if left != right
    ]
    print("VERIFICATION_OBJECT_CHANGED_INDEXES", changed_indexes)
    if changed_indexes != [6]:
        problems.append("verification delta is not only index 6")

    after = sha256(CONTRACT_PATH)
    print("SHA256_BEFORE", before)
    print("SHA256_AFTER", after)
    print("BYTES_UNCHANGED", raw == CONTRACT_PATH.read_bytes())
    if before != after or raw != CONTRACT_PATH.read_bytes():
        problems.append("real contract bytes changed")
    print("PROBLEMS", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
