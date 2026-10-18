#!/usr/bin/env python3
"""Drive tools/start_path.py against temporary project records and live repository state."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "start_path.py"
WA_TOOL = ROOT / "tools" / "workflow_assurance.py"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the shipped start-path command against one project root."""
    return subprocess.run(
        [sys.executable, str(TOOL), *args, "--root", str(root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_raw(*args: str) -> subprocess.CompletedProcess[str]:
    """Run start_path.py with exact arguments."""
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write(root: Path, relative: str, payload: dict) -> None:
    """Write one JSON record under the temporary project."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def cause(path_id: str) -> dict:
    return {
        "id": path_id,
        "path": "bugfix",
        "summary": "The public start path had no consumer.",
        "evidence": ["readme promised a file no tool read"],
    }


def scope(path_id: str, files: list[str], contract_id: str | None = None) -> dict:
    payload = {
        "id": path_id,
        "path": "bugfix",
        "files": files,
        "non_goals": ["no feature-loop change"],
    }
    if contract_id is not None:
        payload["contract_id"] = contract_id
    return payload


def contract(status: str, paths: list[str]) -> dict:
    return {
        "contract_id": "c1",
        "feature_id": "c1",
        "name": "repair",
        "status": status,
        "spec_ref": ".agent/product_spec.md",
        "scope": {
            "files_create": [],
            "files_modify": [{"path": path, "purpose": "repair"} for path in paths],
        },
        "non_goals": ["no new feature"],
        "verification": [
            {
                "acceptance_test": "start path done",
                "command": "python3 tools/start_path.py done bugfix --id demo",
            }
        ],
        "estimated_lines": 10,
        "evidence_dir": ".agent/evidence",
        "evidence_convention": "one JSON receipt per command",
    }


def qa(path_id: str, evidence: str) -> dict:
    return {
        "feature_id": path_id,
        "qa_pass": True,
        "checks_run": 1,
        "checks_passed": 1,
        "adversarial": {"performed": True},
        "evidence_files": [evidence],
        "issues": [],
        "unsupported_claims": [],
        "missing_acceptance_coverage": [],
        "required_fixes": [],
        "final_verdict": {"approved": True, "summary": "verification recorded"},
    }


def expect(result: subprocess.CompletedProcess[str], code: int, text: str) -> None:
    """Require an exit code and a phrase from the real command output."""
    combined = result.stdout + result.stderr
    if result.returncode != code or text not in combined:
        raise SystemExit(
            f"expected exit {code} and {text!r}\n"
            f"got exit {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def test_r5_classification_and_amendments(root: Path) -> None:
    """Verify semantic 5-route classification, trivial path, lightweight amendments, and verdict severity."""
    # 1. Trivial route classification
    res_trivial = run_raw("classify", "--files", "README.md", "--editorial")
    expect(res_trivial, 0, '"route": "trivial"')
    parsed_trivial = json.loads(res_trivial.stdout)
    assert parsed_trivial["stopping_conditions"]["max_attempts"] == 3
    assert parsed_trivial["stopping_conditions"]["comparator_subordinate"] is True

    # 2. Bugfix route classification
    res_bugfix = run_raw("classify", "--files", "tools/start_path.py", "--bugfix")
    expect(res_bugfix, 0, '"route": "bugfix"')

    # 3. Small-change route classification
    res_small = run_raw("classify", "--files", "tools/start_path.py")
    expect(res_small, 0, '"route": "small-change"')

    # 4. Standard-feature route classification (schema or needs_new_contract)
    res_feat = run_raw("classify", "--files", "schema/contract.schema.json")
    expect(res_feat, 0, '"route": "standard-feature"')

    # 5. High-risk route classification (security/isolation/workflow_assurance)
    res_hr = run_raw("classify", "--files", "tools/linux_trial_sandbox.sh")
    expect(res_hr, 0, '"route": "high-risk"')

    # 6. Reject .nizam/ edits in classify
    res_nizam = run_raw("classify", "--files", ".nizam/NIZAM.json")
    expect(res_nizam, 1, "installed .nizam/ payload is immutable")

    # 7. Trivial begin/done positive and negative
    write(
        root,
        ".agent/evidence/triv-intent.json",
        {
            "id": "triv",
            "path": "trivial",
            "summary": "Fix typo in README.",
            "needs_new_contract": False,
            "files": ["README.md"],
        },
    )
    expect(run(root, "begin", "trivial", "--id", "triv"), 0, "trivial triv: implementation may begin")
    triv_ev = ".agent/evidence/triv-out.txt"
    (root / triv_ev).write_text("exit 0\n", encoding="utf-8")
    write(root, ".agent/qa/triv.json", qa("triv", triv_ev))
    expect(run(root, "done", "trivial", "--id", "triv"), 0, "trivial triv: recorded verification result exists")

    write(
        root,
        ".agent/evidence/triv-bad-intent.json",
        {
            "id": "triv-bad",
            "path": "trivial",
            "summary": "Touch sandbox under trivial.",
            "needs_new_contract": False,
            "files": ["tools/linux_trial_sandbox.sh"],
        },
    )
    expect(run(root, "begin", "trivial", "--id", "triv-bad"), 1, "trivial path cannot modify schema or high-risk files")

    # 8. Lightweight contract amendment (positive + negative)
    write(root, ".agent/contracts/c1.json", contract("approved", ["README.md"]))
    amendment_ok = root / ".agent/evidence/c1-amend.json"
    write(
        root,
        ".agent/evidence/c1-amend.json",
        {
            "contract_id": "c1",
            "summary": "Add helper file and update verification command",
            "invariants_preserved": True,
            "files_modify_add": [{"path": "tools/start_path.py", "purpose": "helper"}],
            "verification_updates": [
                {
                    "acceptance_test": "start path done",
                    "command": "PYTHONDONTWRITEBYTECODE=1 python3 tools/start_path.py done bugfix --id demo",
                }
            ],
        },
    )
    res_amend = run(root, "amend-contract", "--contract", "c1", "--amendment", str(amendment_ok), "--apply")
    expect(res_amend, 0, '"applied": true')
    # Now bugfix scope including tools/start_path.py succeeds against amended c1!
    write(root, ".agent/evidence/bound-scope.json", scope("bound", ["README.md", "tools/start_path.py"], "c1"))
    expect(run(root, "begin", "bugfix", "--id", "bound"), 0, "implementation may begin")

    # Negative amendment: forbidden non_goals modification or high-risk sandbox path
    amendment_bad = root / ".agent/evidence/c1-amend-bad.json"
    write(
        root,
        ".agent/evidence/c1-amend-bad.json",
        {
            "contract_id": "c1",
            "summary": "Attempt to alter non_goals",
            "invariants_preserved": True,
            "non_goals": ["weakened"],
        },
    )
    expect(
        run(root, "amend-contract", "--contract", "c1", "--amendment", str(amendment_bad)),
        1,
        "lightweight amendment cannot modify non_goals",
    )

    # 9. Review verdict severity (advisory_minor non-blocking vs blocking issues)
    verdict_ok = root / ".agent/evidence/verdict-ok.json"
    write(
        root,
        ".agent/evidence/verdict-ok.json",
        {
            "final_verdict": {"approved": True},
            "issues": [],
            "missing_acceptance_coverage": [],
            "unsupported_claims": [],
            "advisory_minor": [{"title": "optional style note", "severity": "minor"}],
        },
    )
    expect(run_raw("check-verdict", "--verdict", str(verdict_ok)), 0, '"advisory_minor_count": 1')

    verdict_bad = root / ".agent/evidence/verdict-bad.json"
    write(
        root,
        ".agent/evidence/verdict-bad.json",
        {
            "final_verdict": {"approved": True},
            "issues": [{"title": "real defect", "description": "fails check"}],
            "missing_acceptance_coverage": [],
            "unsupported_claims": [],
        },
    )
    expect(
        run_raw("check-verdict", "--verdict", str(verdict_bad)),
        1,
        "final_verdict.approved cannot be true when blocking arrays are non-empty",
    )


def test_r6_r7_r8_preflight_capture_status_and_resume(root: Path) -> None:
    """Verify capability preflight, exclusive command capture, read-only status view, and receipt CLI."""
    # 1. Preflight on real repository root (R6 + R7 repository binding aligned)
    res_preflight = run(ROOT, "preflight")
    expect(res_preflight, 0, '"repository_binding_aligned": true')
    expect(res_preflight, 0, '"ok": true')

    # 2. Exclusive command capture: success, failure, and interrupted timeout (R6)
    res_cap_ok = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "1",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('capture-ok')",
    )
    expect(res_cap_ok, 0, '"outcome": "success"')
    cap_ok_doc = json.loads(res_cap_ok.stdout)
    assert cap_ok_doc["completion_state"] == "completed"
    assert cap_ok_doc["duration_ms"] >= 0
    assert (root / cap_ok_doc["stdout"]["path"]).read_text(encoding="utf-8").strip() == "capture-ok"

    res_cap_fail = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "2",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "import sys; sys.exit(3)",
    )
    expect(res_cap_fail, 1, '"outcome": "failed"')
    cap_fail_doc = json.loads(res_cap_fail.stdout)
    assert cap_fail_doc["exit_code"] == 3
    assert cap_fail_doc["capture_path"] != cap_ok_doc["capture_path"]
    # Earlier capture file still exists and was not overwritten
    assert (root / cap_ok_doc["capture_path"]).is_file()

    res_cap_timeout = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "3",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--timeout-sec",
        "0.05",
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "import time; time.sleep(2)",
    )
    expect(res_cap_timeout, 1, '"completion_state": "interrupted"')

    # Attempt 4 is rejected by the 3-attempt breaker cap
    res_cap_4 = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "4",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('forbidden')",
    )
    expect(res_cap_4, 2, "attempt must be an integer between 1 and 3")

    # 3. Concise status view on real repository root (R8)
    res_status = run(ROOT, "status", "--format", "json")
    expect(res_status, 0, '"repository": "https://github.com/niq-cnr/nizam-framework.git"')
    status_doc = json.loads(res_status.stdout)
    assert status_doc["repository_binding_aligned"] is True
    assert [p["id"] for p in status_doc["phase_019_profiles"]] == ["124", "125"]

    # 4. Operational CLI subcommands on workflow_assurance.py (R7)
    for subcmd in ("verify-receipt", "plan-transition", "route-failure"):
        wa_help = subprocess.run(
            [sys.executable, str(WA_TOOL), subcmd, "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert wa_help.returncode == 0, f"workflow_assurance.py {subcmd} --help failed"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nizam-start-path-") as name:
        root = Path(name)
        missing = run(root, "begin", "bugfix", "--id", "demo")
        expect(missing, 1, "required record does not exist")

        write(root, ".agent/evidence/demo-cause.json", cause("demo"))
        write(root, ".agent/evidence/demo-scope.json", scope("demo", ["README.md"]))
        began = run(root, "begin", "bugfix", "--id", "demo")
        expect(began, 0, "implementation may begin")
        undone = run(root, "done", "bugfix", "--id", "demo")
        expect(undone, 1, "required record does not exist")

        evidence = ".agent/evidence/demo-qa-out.txt"
        write(root, evidence, {"command": "true"})
        (root / evidence).write_text("exit 0\n", encoding="utf-8")
        write(root, ".agent/qa/demo.json", qa("demo", evidence))
        finished = run(root, "done", "bugfix", "--id", "demo")
        expect(finished, 0, "recorded verification result exists")

        write(root, ".agent/evidence/bound-cause.json", cause("bound"))
        write(
            root,
            ".agent/evidence/bound-scope.json",
            scope("bound", ["OTHER.md"], "c1"),
        )
        write(root, ".agent/contracts/c1.json", contract("approved", ["README.md"]))
        outside = run(root, "begin", "bugfix", "--id", "bound")
        expect(outside, 1, "not inside the named contract")

        write(
            root,
            ".agent/evidence/bound-scope.json",
            scope("bound", ["README.md"], "c1"),
        )
        write(root, ".agent/contracts/c1.json", contract("proposed", ["README.md"]))
        proposed = run(root, "begin", "bugfix", "--id", "bound")
        expect(proposed, 1, "not already approved")
        write(root, ".agent/contracts/c1.json", contract("approved", ["README.md"]))
        bound = run(root, "begin", "bugfix", "--id", "bound")
        expect(bound, 0, "implementation may begin")

        write(
            root,
            ".agent/evidence/tiny-intent.json",
            {
                "id": "tiny",
                "path": "small-change",
                "summary": "Fix one spelled word.",
                "needs_new_contract": True,
            },
        )
        refused = run(root, "begin", "small-change", "--id", "tiny")
        expect(refused, 1, "needs_new_contract")
        write(
            root,
            ".agent/evidence/tiny-intent.json",
            {
                "id": "tiny",
                "path": "small-change",
                "summary": "Fix one spelled word.",
                "needs_new_contract": False,
            },
        )
        small = run(root, "begin", "small-change", "--id", "tiny")
        expect(small, 0, "implementation may begin")
        small_evidence = ".agent/evidence/tiny-out.txt"
        (root / small_evidence).write_text("exit 0\n", encoding="utf-8")
        write(root, ".agent/qa/tiny.json", qa("tiny", small_evidence))
        small_done = run(root, "done", "small-change", "--id", "tiny")
        expect(small_done, 0, "recorded verification result exists")

        escaped = run(root, "begin", "bugfix", "--id", "../demo")
        expect(escaped, 2, "safe path token")

        test_r5_classification_and_amendments(root)
        test_r6_r7_r8_preflight_capture_status_and_resume(root)

    print("start-path: bugfix, small-change, trivial, classify, amend-contract, preflight, capture, and status gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
