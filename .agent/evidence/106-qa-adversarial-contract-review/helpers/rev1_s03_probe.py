#!/usr/bin/env python3
"""Execute contract 106 revision 1 S02 and S03 commands.

Git diff/status are substituted at the subprocess boundary. The real
run_state, the contract, and product files are not written. validate.sh
and fixtures_self_test.sh are not invoked.
"""

from __future__ import annotations

import ast
import difflib
import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
A = "2a22ecdfda6ff3895792a1d974489d091e11e696"
B_REV = "55c428a"
PHASE = "docs/planning/phase_014.yaml"
DEBT = "docs/planning/DEBT.md"
FEATURE_LIST = ".agent/feature_list_014.json"
RUN_STATE = ".agent/run_state.json"

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name if not detail else f"{name}: {detail}")
        if detail:
            print("    " + detail)


def heredoc_body(command: str) -> str:
    prefix = "python3 - <<'PY'\n"
    if not command.startswith(prefix):
        raise SystemExit("command is not the expected python heredoc")
    rest = command[len(prefix) :]
    if rest.endswith("\nPY\n"):
        return rest[: -len("\nPY\n")]
    if rest.endswith("\nPY"):
        return rest[: -len("\nPY")]
    raise SystemExit("heredoc closer missing")


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            out.update(flatten(value, path))
        return out
    if isinstance(obj, list):
        out = {}
        for index, value in enumerate(obj):
            out.update(flatten(value, f"{prefix}[{index}]"))
        return out
    return {prefix: obj}


class Completed:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def problems_of(output: str) -> list:
    lines = [line for line in output.splitlines() if "problems:" in line]
    if len(lines) != 1:
        raise AssertionError(f"expected one problems line, got {lines!r}")
    text = lines[0].split("problems:", 1)[1].strip()
    return ast.literal_eval(text)


def exec_body(body: str, fake_run, opener=None):
    namespace = {"__name__": "contract_command"}
    if opener is not None:
        namespace["open"] = opener
    real_run = subprocess.run
    subprocess.run = fake_run
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    rc = 0
    try:
        exec(compile(body, "<contract-command>", "exec"), namespace)  # noqa: S102
    except SystemExit as exc:
        code = exc.code
        if code is None:
            rc = 0
        elif isinstance(code, int):
            rc = code
        else:
            rc = 1
            print(f"non-int SystemExit: {code!r}", file=old_stdout)
    finally:
        sys.stdout = old_stdout
        subprocess.run = real_run
    return rc, buffer.getvalue()


def nul_payload(paths: list[str]) -> str:
    if not paths:
        return ""
    return "\0".join(paths) + "\0"


def make_fake(diff_by_commit: dict[str, list[str]], approved_text: str, full_b: str):
    def fake_run(args, capture_output=True, text=True, check=False):
        argv = list(args)
        stdout = ""
        rc = 0
        if argv[:4] == ["git", "diff", "--name-only", "-z"] and len(argv) == 5:
            commit = argv[4]
            if commit not in diff_by_commit:
                raise AssertionError(f"unexpected diff commit {commit}")
            stdout = nul_payload(diff_by_commit[commit])
        elif argv == ["git", "status", "--porcelain", "--untracked-files=all", "-z"]:
            stdout = ""
        elif argv == ["git", "cat-file", "-t", full_b]:
            stdout = "commit\n"
        elif argv[:3] == ["git", "merge-base", "--is-ancestor"] and len(argv) == 5:
            rc = 0
        elif argv == ["git", "rev-list", "--count", f"{full_b}..HEAD"]:
            stdout = "1\n"
        elif argv == ["git", "show", f"{full_b}:.agent/contracts/106.json"]:
            stdout = approved_text
        else:
            raise AssertionError(f"unexpected argv {argv}")
        if check and rc != 0:
            raise subprocess.CalledProcessError(rc, argv, stdout, "")
        return Completed(stdout, rc)

    return fake_run


def main() -> None:
    os_chdir = Path.cwd()
    try:
        import os

        os.chdir(REPO)
        print("cwd", Path.cwd())
        print("validate.sh invoked", False)
        print("fixtures_self_test.sh invoked", False)

        full_b = subprocess.check_output(["git", "rev-parse", B_REV], text=True).strip()
        full_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        print("A", A)
        print("B", full_b)
        print("HEAD", full_head)

        real_names = subprocess.check_output(
            ["git", "diff", "--name-only", A, full_b], text=True
        ).splitlines()
        print("real_diff_count", len(real_names))
        for path in real_names:
            print("real_diff", path)
        check(
            "real git diff --name-only A 55c428a contains .agent/run_state.json",
            RUN_STATE in real_names,
            repr(real_names),
        )

        numstat = subprocess.check_output(
            ["git", "diff", "--numstat", A, full_b, "--", RUN_STATE], text=True
        ).strip()
        print("run_state_numstat", numstat)
        run_state_diff = subprocess.check_output(
            ["git", "diff", A, full_b, "--", RUN_STATE], text=True
        )
        print("run_state_diff_begin")
        print(run_state_diff.rstrip("\n"))
        print("run_state_diff_end")
        check(
            "run_state diff is the contract_approved bookkeeping edit",
            "contract_approved" in run_state_diff and "active_contract_id" in run_state_diff,
        )

        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", A, full_b],
            capture_output=True,
            text=True,
        )
        print("real_ancestor_A_of_B", ancestor.returncode)
        past = subprocess.check_output(
            ["git", "rev-list", "--count", f"{full_b}..HEAD"], text=True
        ).strip()
        print("real_shared_tree_commits_past_B", past)
        print(
            "note: S02's rev-list count is simulated as 1, the attempt-root condition. "
            "The shared branch is not the attempt worktree."
        )

        work = json.loads(Path(".agent/contracts/106.json").read_text(encoding="utf-8"))
        old = json.loads(
            subprocess.check_output(
                ["git", "show", f"{full_b}:.agent/contracts/106.json"], text=True
            )
        )
        head_doc = json.loads(
            subprocess.check_output(
                ["git", "show", "HEAD:.agent/contracts/106.json"], text=True
            )
        )
        approved_text = subprocess.check_output(
            ["git", "show", f"{full_b}:.agent/contracts/106.json"], text=True
        )
        check("contract status is proposed", work["status"] == "proposed", work["status"])
        check(
            "approvals not yet set",
            work["approvals"]["validator_mode_a"] is False
            and work["approvals"]["evaluator_contract_review"] is False
            and work["approvals"]["revisions"] == 1,
            repr(work["approvals"]),
        )
        check(
            "revision 0 blob at 55c428a is approved",
            old["status"] == "approved" and json.loads(approved_text)["status"] == "approved",
        )

        changed_paths = sorted(set(flatten(old)) | set(flatten(work)))
        diff_paths = sorted(
            path for path in changed_paths if flatten(old).get(path) != flatten(work).get(path)
        )
        print("json_paths_changed", len(diff_paths))
        for path in diff_paths:
            print("json_path", path)
        expected_paths = [
            "approvals.approved_at",
            "approvals.evaluator_contract_review",
            "approvals.revisions",
            "approvals.validator_mode_a",
            "design_notes.retry_identity_note",
            "design_notes.revision",
            "design_notes.revision_history[0].at",
            "design_notes.revision_history[0].revision",
            "design_notes.revision_history[0].summary",
            "design_notes.revision_history[1].at",
            "design_notes.revision_history[1].revision",
            "design_notes.revision_history[1].summary",
            "status",
            "verification[10].acceptance_test",
            "verification[10].command",
            "verification[10].expected_outcome",
        ]
        check(
            "only the revision envelope and S03 text differ from 55c428a",
            diff_paths == expected_paths,
            repr(diff_paths),
        )

        def by_evidence(doc):
            return {item["evidence_file"]: item for item in doc["verification"]}

        work_v = by_evidence(work)
        old_v = by_evidence(old)
        head_v = by_evidence(head_doc)
        s02_key = ".agent/evidence/106/s02-attempt-root-delta.txt"
        s03_key = ".agent/evidence/106/s03-scope-boundary.txt"
        check(
            "S02 command byte-identical to 55c428a and HEAD",
            work_v[s02_key]["command"] == old_v[s02_key]["command"]
            and work_v[s02_key]["command"] == head_v[s02_key]["command"],
        )
        feature = next(
            item
            for item in json.loads(Path(".agent/feature_list_014.json").read_text(encoding="utf-8"))[
                "features"
            ]
            if item["id"] == "106"
        )
        print("feature_dependencies", feature["dependencies"])
        tests = [item for item in work["verification"] if not item.get("supplementary")]
        check(
            "eight acceptance commands byte-identical to feature_list_014.json",
            [item["command"] for item in tests] == feature["acceptance_tests"]
            and [item["acceptance_test"] for item in tests] == feature["acceptance_tests"],
        )

        new_s03 = work_v[s03_key]["command"]
        old_s03 = old_v[s03_key]["command"]
        print("S03 command unified diff against 55c428a")
        for line in difflib.unified_diff(
            old_s03.splitlines(),
            new_s03.splitlines(),
            fromfile="55c428a S03",
            tofile="worktree S03",
            lineterm="",
        ):
            print(line)
        print("S03 acceptance_test unified diff")
        for line in difflib.unified_diff(
            old_v[s03_key]["acceptance_test"].splitlines(),
            work_v[s03_key]["acceptance_test"].splitlines(),
            lineterm="",
        ):
            print(line)
        print("S03 expected_outcome unified diff")
        for line in difflib.unified_diff(
            old_v[s03_key]["expected_outcome"].splitlines(),
            work_v[s03_key]["expected_outcome"].splitlines(),
            lineterm="",
        ):
            print(line)
        removed = ' or ".agent/run_state.json" in changed'
        check("revision 0 hard-fail names run_state", removed in old_s03)
        check("revision 1 command omits the run_state hard-fail", removed not in new_s03)
        check(
            "revision 1 owned set still names run_state",
            '".agent/run_state.json"' in new_s03
            and 'owned = {".agent/contracts/106.json", ".agent/run_state.json", ".agent/feature_list_014.json"}'
            in new_s03,
        )
        check(
            "revision 1 hard-fail still names phase YAML and DEBT.md",
            'if "docs/planning/phase_014.yaml" in changed or "docs/planning/DEBT.md" in changed:'
            in new_s03,
        )
        check(
            "revision 1 still hard-fails a feature-list change",
            'if ".agent/feature_list_014.json" in changed:' in new_s03,
        )

        scope_paths = {
            item["path"]
            for key in ("files_create", "files_modify")
            for item in work["scope"][key]
        }
        modified = [item["path"] for item in work["scope"]["files_modify"]]
        print("files_modify", modified)
        check("run_state is not in S02 scope", RUN_STATE not in scope_paths)
        check("phase YAML is not in S02 scope", PHASE not in scope_paths)
        check(
            "S02 command computes scope from files_create and files_modify and subtracts it from delta",
            'scope = {item["path"] for key in ("files_create", "files_modify") for item in contract["scope"][key]}'
            in work_v[s02_key]["command"]
            and "extra = sorted(delta - scope)" in work_v[s02_key]["command"],
        )

        new_body = heredoc_body(new_s03)
        old_body = heredoc_body(old_s03)
        s02_body = heredoc_body(work_v[s02_key]["command"])
        compile(new_body, "<s03-rev1>", "exec")
        compile(old_body, "<s03-rev0>", "exec")
        compile(s02_body, "<s02>", "exec")

        faithful = sorted(set(real_names) | set(modified))
        print("faithful_changed_count", len(faithful))

        def run_s03(body: str, paths: list[str]):
            fake = make_fake({A: paths}, approved_text, full_b)
            return exec_body(body, fake)

        cases = [
            (
                "S03 real A..B paths only (run_state present, deliverables absent)",
                new_body,
                real_names,
                1,
                ["files_modify paths not changed: " + repr(sorted(modified))],
            ),
            (
                "S03 real A..B paths plus files_modify (run_state present)",
                new_body,
                faithful,
                0,
                [],
            ),
            (
                "S03 same set plus docs/planning/phase_014.yaml",
                new_body,
                sorted(set(faithful) | {PHASE}),
                1,
                [
                    "paths outside scope and allowlist: " + repr([PHASE]),
                    "orchestrator-owned file changed inside the attempt",
                ],
            ),
            (
                "S03 same set plus docs/planning/DEBT.md",
                new_body,
                sorted(set(faithful) | {DEBT}),
                1,
                [
                    "paths outside scope and allowlist: " + repr([DEBT]),
                    "orchestrator-owned file changed inside the attempt",
                ],
            ),
            (
                "S03 same set plus .agent/feature_list_014.json",
                new_body,
                sorted(set(faithful) | {FEATURE_LIST}),
                1,
                [
                    "feature list changed inside the attempt; status flips are Orchestrator-owned"
                ],
            ),
            (
                "revision 0 S03 on the faithful set still hard-fails run_state",
                old_body,
                faithful,
                1,
                ["orchestrator-owned file changed inside the attempt"],
            ),
        ]
        for name, body, paths, expect_rc, expect_problems in cases:
            print("CASE", name)
            print("injected_contains_run_state", RUN_STATE in paths)
            rc, output = run_s03(body, paths)
            print(output.rstrip("\n"))
            print("rc", rc)
            got = problems_of(output)
            check(name + " rc", rc == expect_rc, f"got {rc}")
            check(name + " problems", got == expect_problems, repr(got))

        def run_s02(delta_paths: list[str]):
            fake = make_fake({full_b: delta_paths}, approved_text, full_b)

            def opener(path, *args, **kwargs):
                if path == ".agent/evidence/106/attempt-base.txt":
                    return io.StringIO(f"git rev-parse HEAD\n{full_b}\nEXIT:0\n")
                return open(path, *args, **kwargs)

            return exec_body(s02_body, fake, opener)

        s02_cases = [
            (
                "S02 delta is only .agent/run_state.json",
                [RUN_STATE],
                1,
                ["paths changed since B outside scope: " + repr([RUN_STATE])],
            ),
            (
                "S02 delta is only NIZAM.json",
                ["NIZAM.json"],
                0,
                [],
            ),
        ]
        for name, delta_paths, expect_rc, expect_problems in s02_cases:
            print("CASE", name)
            rc, output = run_s02(delta_paths)
            print(output.rstrip("\n"))
            print("rc", rc)
            got = problems_of(output)
            check(name + " rc", rc == expect_rc, f"got {rc}")
            check(name + " problems", got == expect_problems, repr(got))

        print("failures", failures)
        sys.exit(1 if failures else 0)
    finally:
        import os

        os.chdir(os_chdir)


if __name__ == "__main__":
    main()
