#!/usr/bin/env python3
"""Drive tools/start_path.py against temporary project records and live repository state."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import stat
from contextlib import contextmanager
from unittest import mock
import shutil
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
    assert parsed_trivial["stopping_conditions"]["initial_strategy_ladder_attempts"] == 3
    assert parsed_trivial["stopping_conditions"]["hard_attempt_cap"] is None
    assert parsed_trivial["stopping_conditions"]["attempt_counter_role"] == "telemetry"
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
    expect(
        run(root, "begin", "trivial", "--id", "triv-bad"),
        1,
        "trivial path cannot modify schema, governance, tooling, or high-risk files",
    )

    # 8. Lightweight contract amendment (positive mechanical + negative semantic/unknown/vacuous)
    write(root, ".agent/contracts/c1.json", contract("approved", ["README.md", "tools/test_start_path.py"]))
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
    expect(res_amend, 0, '"amendment_class": "mechanical"')
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


def test_a1_f1_f5_scope_completion_and_amendments(root: Path) -> None:
    """Verify all F1 and F5 audit counterexamples fail closed and valid cases pass."""
    # F1.1: docs/authorization.py with --editorial must NOT be trivial
    res_doc_py = run_raw("classify", "--files", "docs/authorization.py", "--editorial")
    expect(res_doc_py, 0, '"route": "small-change"')

    # F1.2: AGENTS.md with --editorial must be standard-feature, not trivial
    res_agents = run_raw("classify", "--files", "AGENTS.md", "--editorial")
    expect(res_agents, 0, '"route": "standard-feature"')

    # F1.3: standard/AGF.md without flags must be standard-feature, not small-change
    res_agf = run_raw("classify", "--files", "standard/AGF.md")
    expect(res_agf, 0, '"route": "standard-feature"')

    # F1.4: Empty file list in classify must fail closed
    res_empty = run_raw("classify")
    expect(res_empty, 1, "files must be a non-empty list")

    # F1.5: begin trivial naming tools/start_path.py must fail closed
    write(
        root,
        ".agent/evidence/triv-tool-intent.json",
        {
            "id": "triv-tool",
            "path": "trivial",
            "summary": "Try to edit start_path under trivial.",
            "needs_new_contract": False,
            "files": ["tools/start_path.py"],
        },
    )
    expect(
        run(root, "begin", "trivial", "--id", "triv-tool"),
        1,
        "trivial path cannot modify schema, governance, tooling, or high-risk files",
    )

    # F1.6: begin small-change naming schema/contract.schema.json must fail closed
    write(
        root,
        ".agent/evidence/sc-schema-intent.json",
        {
            "id": "sc-schema",
            "path": "small-change",
            "summary": "Try to edit schema under small-change.",
            "needs_new_contract": False,
            "files": ["schema/contract.schema.json"],
        },
    )
    expect(
        run(root, "begin", "small-change", "--id", "sc-schema"),
        1,
        "small-change path cannot modify standard-feature files",
    )

    # F1.7: done trivial with unrelated feature_id, checks_run: 0, or empty evidence file must fail closed
    write(
        root,
        ".agent/evidence/triv-qa-probe-intent.json",
        {
            "id": "triv-qa-probe",
            "path": "trivial",
            "summary": "Probe QA completion checks.",
            "needs_new_contract": False,
            "files": ["README.md"],
        },
    )
    expect(run(root, "begin", "trivial", "--id", "triv-qa-probe"), 0, "implementation may begin")
    empty_ev = ".agent/evidence/triv-qa-empty.txt"
    (root / empty_ev).write_text("", encoding="utf-8")

    # Unrelated feature_id
    bad_qa_id = qa("unrelated-id", empty_ev)
    write(root, ".agent/qa/triv-qa-probe.json", bad_qa_id)
    expect(run(root, "done", "trivial", "--id", "triv-qa-probe"), 1, "does not match --id")

    # Zero executed checks
    bad_qa_zero = qa("triv-qa-probe", empty_ev)
    bad_qa_zero["checks_run"] = 0
    bad_qa_zero["checks_passed"] = 0
    write(root, ".agent/qa/triv-qa-probe.json", bad_qa_zero)
    expect(run(root, "done", "trivial", "--id", "triv-qa-probe"), 1, "does not pass")

    # Empty evidence file (0 bytes)
    bad_qa_empty = qa("triv-qa-probe", empty_ev)
    write(root, ".agent/qa/triv-qa-probe.json", bad_qa_empty)
    expect(run(root, "done", "trivial", "--id", "triv-qa-probe"), 1, "evidence file is empty")

    # Non-empty evidence file and matching id with checks_run=1 passes
    (root / empty_ev).write_text("verified README.md diff\n", encoding="utf-8")
    expect(run(root, "done", "trivial", "--id", "triv-qa-probe"), 0, "recorded verification result exists")

    # F1.8: Working-tree scope drift between begin and done in a Git repository must fail closed
    with tempfile.TemporaryDirectory(prefix="nizam-git-drift-") as git_dir_name:
        git_root = Path(git_dir_name).resolve()
        subprocess.run(["git", "-C", str(git_root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(git_root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(git_root), "config", "user.email", "test@example.invalid"], check=True)
        (git_root / "README.md").write_text("# Demo\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(git_root), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(git_root), "commit", "-qm", "init"], check=True)

        write(
            git_root,
            ".agent/evidence/drift-intent.json",
            {
                "id": "drift",
                "path": "trivial",
                "summary": "Update README only.",
                "needs_new_contract": False,
                "files": ["README.md"],
            },
        )
        expect(run(git_root, "begin", "trivial", "--id", "drift"), 0, "implementation may begin")
        (git_root / "README.md").write_text("# Demo updated\n", encoding="utf-8")
        (git_root / "UNDECLARED.py").write_text("print('drift')\n", encoding="utf-8")
        drift_ev = ".agent/evidence/drift-out.txt"
        (git_root / drift_ev).write_text("checked\n", encoding="utf-8")
        write(git_root, ".agent/qa/drift.json", qa("drift", drift_ev))
        expect(
            run(git_root, "done", "trivial", "--id", "drift"),
            1,
            "working tree contains undeclared changes outside scoped files: UNDECLARED.py",
        )
        (git_root / "UNDECLARED.py").unlink()
        expect(run(git_root, "done", "trivial", "--id", "drift"), 0, "recorded verification result exists")

    # F5.1: amend-contract rejects unknown fields
    write(root, ".agent/contracts/c-doc.json", contract("approved", ["README.md"]))
    amend_unknown = root / ".agent/evidence/c-doc-unknown.json"
    write(
        root,
        ".agent/evidence/c-doc-unknown.json",
        {
            "contract_id": "c-doc",
            "summary": "Unknown field probe",
            "invariants_preserved": True,
            "arbitrary_extra_field": "rejected",
        },
    )
    expect(
        run(root, "amend-contract", "--contract", "c-doc", "--amendment", str(amend_unknown)),
        1,
        "amendment contains unknown or unsupported field(s): arbitrary_extra_field",
    )

    # F5.2: amend-contract normalizes and rejects ./.nizam/tools/workflow_assurance.py
    amend_nizam = root / ".agent/evidence/c-doc-nizam.json"
    write(
        root,
        ".agent/evidence/c-doc-nizam.json",
        {
            "contract_id": "c-doc",
            "summary": "Dot-slash .nizam bypass probe",
            "invariants_preserved": True,
            "files_modify_add": [{"path": "./.nizam/tools/workflow_assurance.py", "purpose": "bypass"}],
        },
    )
    expect(
        run(root, "amend-contract", "--contract", "c-doc", "--amendment", str(amend_nizam)),
        1,
        "installed .nizam/ payload is immutable",
    )

    # F5.3: amend-contract rejects vacuous verification command "true"
    amend_vacuous = root / ".agent/evidence/c-doc-vacuous.json"
    write(
        root,
        ".agent/evidence/c-doc-vacuous.json",
        {
            "contract_id": "c-doc",
            "summary": "Vacuous command probe",
            "invariants_preserved": True,
            "verification_updates": [{"acceptance_test": "start path done", "command": "true"}],
        },
    )
    expect(
        run(root, "amend-contract", "--contract", "c-doc", "--amendment", str(amend_vacuous)),
        1,
        "verification command 'true' is vacuous (no-op)",
    )

    # F5.4: amend-contract adding tools/start_path.py to README.md-only contract is semantic (requires re-approval)
    amend_semantic = root / ".agent/evidence/c-doc-semantic.json"
    write(
        root,
        ".agent/evidence/c-doc-semantic.json",
        {
            "contract_id": "c-doc",
            "summary": "Expand prose contract to executable tooling",
            "invariants_preserved": True,
            "files_modify_add": [{"path": "tools/start_path.py", "purpose": "expand"}],
        },
    )
    res_sem_check = run(root, "amend-contract", "--contract", "c-doc", "--amendment", str(amend_semantic))
    expect(res_sem_check, 0, '"amendment_class": "semantic"')
    expect(res_sem_check, 0, '"re_approval_required": true')
    expect(
        run(root, "amend-contract", "--contract", "c-doc", "--amendment", str(amend_semantic), "--apply"),
        1,
        "semantic scope expansion requires re-approval",
    )


def test_r6_r7_r8_preflight_capture_status_and_resume(root: Path) -> None:
    """Verify capability preflight, exclusive command capture, producer-to-receipt chain, and status view."""
    import os
    import start_path as sp

    assert sp._repository_urls_match(
        "https://github.com/niq-cnr/nizam-framework.git",
        "https://github.com/niq-cnr/nizam-framework",
    ) is True
    assert sp._repository_urls_match(
        "https://github.com/niq-cnr/nizam-framework.git",
        "https://github.com/niq-cnr/other-repo",
    ) is False

    # 1. Preflight on real repository root (R6 + R7 + A2 operational sandbox probe)
    res_preflight = run(ROOT, "preflight", "--require-sandbox")
    expect(res_preflight, 0, '"repository_binding_aligned": true')
    expect(res_preflight, 0, '"sandbox_operational": true')
    expect(res_preflight, 0, '"ok": true')
    preflight_doc = json.loads(res_preflight.stdout)
    for required_cap in ("installed", "available", "operational", "qualified", "status"):
        assert required_cap in preflight_doc["capabilities"], f"missing {required_cap} in preflight capabilities"

    # F5.5: Fake broken bwrap first on PATH fails preflight --require-sandbox
    with tempfile.TemporaryDirectory(prefix="nizam-fake-bwrap-") as fake_bin_dir:
        fake_bwrap = Path(fake_bin_dir) / "bwrap"
        fake_bwrap.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake_bwrap.chmod(0o755)
        env_with_fake = dict(os.environ)
        env_with_fake["PATH"] = f"{fake_bin_dir}:{env_with_fake.get('PATH', '')}"
        res_bad_sb = subprocess.run(
            [sys.executable, str(TOOL), "preflight", "--require-sandbox", "--root", str(ROOT)],
            cwd=ROOT,
            env=env_with_fake,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_bad_sb, 1, '"sandbox_operational": false')
        expect(res_bad_sb, 1, '"ok": false')

    # 2. Exclusive command capture: unbound vs bound, success, failure, and interrupted timeout (R6 + F2)
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
    assert cap_ok_doc["binding_state"] == "unbound"
    assert cap_ok_doc["candidate_sha256"] is None
    assert cap_ok_doc["duration_ms"] >= 1
    assert (root / cap_ok_doc["stdout"]["path"]).read_text(encoding="utf-8").strip() == "capture-ok"

    # Unbound capture cannot be published for receipt consumption
    res_pub_unbound = run_raw(
        "publish",
        "--capture",
        str(root / cap_ok_doc["capture_path"]),
        "--root",
        str(root),
    )
    expect(res_pub_unbound, 1, "cannot publish unbound capture")

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

    # Attempt 4 without a qualifying continuation basis is rejected with exit 2
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
    expect(res_cap_4, 2, "attempt must be between 1 and 3")

    # C3 positive and negative stopping/continuation checks
    res_cap_4_decomp = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "4",
        "--continuation-basis",
        "verified-decomposition",
        "--decomposition-of",
        "verify-part-a",
        "--repair-summary",
        "Split verification into part A and part B after timeout",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('attempt-4-decomposed-ok')",
    )
    expect(res_cap_4_decomp, 0, '"continuation_basis": "verified-decomposition"')
    cap_4_doc = json.loads(res_cap_4_decomp.stdout)
    assert cap_4_doc["continuation_lineage"]["attempt"] == 4
    assert cap_4_doc["continuation_lineage"]["parent_attempt"] == 3
    assert cap_4_doc["continuation_lineage"]["decomposition_of"] == "verify-part-a"
    assert len(cap_4_doc["continuation_lineage"]["prior_attempts"]) >= 3

    # C3 positive: 4th attempt permitted by recorded contract amendment (amendments list in .agent/contracts/c1.json)
    res_cap_4_amend = run_raw(
        "capture",
        "--id",
        "c1",
        "--step",
        "verify",
        "--attempt",
        "4",
        "--repair-summary",
        "Continue after mechanical contract amendment on c1",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('attempt-4-amended-ok')",
    )
    expect(res_cap_4_amend, 0, '"continuation_basis": "bounded-amendment"')
    assert json.loads(res_cap_4_amend.stdout)["continuation_lineage"]["contract_amendment_present"] is True

    # C3 negative: invariant breach halts immediately
    res_cap_inv = run_raw(
        "capture",
        "--id",
        "demo",
        "--step",
        "verify",
        "--attempt",
        "2",
        "--invariant-breach",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('never')",
    )
    expect(res_cap_inv, 2, "stopping policy halt: invariant or authority boundary breached")

    # C3 negative: repeated identical unresolved defect signature across consecutive attempts without repair/amendment/decomposition halts
    for att_idx in (1, 2):
        rc_rep = run_raw(
            "capture",
            "--id",
            "rep-defect",
            "--step",
            "check",
            "--attempt",
            str(att_idx),
            "--defect-signature",
            "sig-identical-01",
            "--repair-summary" if att_idx == 2 else "--cause",
            "tried minor tweak" if att_idx == 2 else "implementation",
            "--output-dir",
            str(root / ".agent/evidence/captures"),
            "--root",
            str(root),
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(1)",
        )
        expect(rc_rep, 1, '"defect_signature": "sig-identical-01"')

    res_rep_halt = run_raw(
        "capture",
        "--id",
        "rep-defect",
        "--step",
        "check",
        "--attempt",
        "3",
        "--defect-signature",
        "sig-identical-01",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('should-halt')",
    )
    expect(res_rep_halt, 2, "stopping policy halt: repeated identical unresolved defect signature")

    # C3 negative: exceeding configured step limit in .agent/run_state.json halts
    write(
        root,
        ".agent/run_state.json",
        {
            "schema_version": "1.0.0",
            "repository": "https://github.com/niq-cnr/nizam-framework.git",
            "current_phase": "019",
            "current_feature": "lim-task",
            "status": "in_progress",
            "updated_at": "2026-10-19T00:00:00Z",
            "circuit_breaker": {
                "lim-task-check": {"attempts": 2, "limit": 2, "status": "open"}
            },
            "history": [],
        },
    )
    res_lim_halt = run_raw(
        "capture",
        "--id",
        "lim-task",
        "--step",
        "check",
        "--attempt",
        "3",
        "--output-dir",
        str(root / ".agent/evidence/captures"),
        "--root",
        str(root),
        "--",
        sys.executable,
        "-c",
        "print('exceeds-limit')",
    )
    expect(res_lim_halt, 2, "exceeds configured step limit (2)")
    (root / ".agent/run_state.json").unlink()

    # 3. Full producer-to-consumer chain on ReceiptFixture: capture -> publish -> build-receipt -> verify-receipt -> resume (F2 + A2 + C1)
    import test_workflow_assurance as twa
    import workflow_assurance as wa

    with tempfile.TemporaryDirectory(prefix="nizam-receipt-chain-") as chain_dir:
        os.environ["NIZAM_WA120_FIXTURE"] = "observed"
        fixture = twa.ReceiptFixture(wa, Path(chain_dir))
        froot = fixture.root
        cand_sha = twa.sha(twa.canonical(fixture.candidate))
        counter_file = froot / "proof" / "chain-exec-count.txt"

        # Create an authorized test mutation adapter script that commits exact literal_pathspec files via a temp GIT_INDEX_FILE
        adapter_script = Path(chain_dir) / "test_mutation_adapter.py"
        adapter_script.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, shutil, subprocess, sys, tempfile\n"
            "from pathlib import Path\n"
            "req = json.loads(sys.stdin.read())\n"
            "root = Path(req['repository_root']).resolve()\n"
            "head = subprocess.run(['git', '--no-optional-locks', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()\n"
            "if head != req['intended_base']:\n"
            "    print(json.dumps({'approved': False, 'status': 'denied', 'reason': 'base mismatch'}))\n"
            "    sys.exit(0)\n"
            "specs = [f['literal_pathspec'] for f in req['files']]\n"
            "with tempfile.TemporaryDirectory(prefix='nizam-adapter-idx-') as td:\n"
            "    tmp_idx = Path(td) / 'index'\n"
            "    env = {**os.environ, 'GIT_INDEX_FILE': str(tmp_idx)}\n"
            "    subprocess.run(['git', '-C', str(root), 'read-tree', head], env=env, check=True)\n"
            "    subprocess.run(['git', '-C', str(root), 'add', '--', *specs], env=env, check=True)\n"
            "    c = subprocess.run(['git', '-C', str(root), 'commit', '-q', '-m', req['commit_message'], '--', *specs], env=env, capture_output=True, text=True)\n"
            "    if c.returncode != 0:\n"
            "        sys.stderr.write(c.stderr or c.stdout)\n"
            "        sys.exit(c.returncode)\n"
            "    subprocess.run(['git', '-C', str(root), 'reset', '-q', 'HEAD', '--', *specs], check=True)\n"
            "new_head = subprocess.run(['git', '--no-optional-locks', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()\n"
            "if os.environ.get('NIZAM_TEST_FAIL_AFTER_S1') == '1' and req['stage'] == 'outputs_pending':\n"
            "    sys.exit(1)\n"
            "print(json.dumps({'approved': True, 'status': 'committed', 'committed': True, 'revision': new_head}))\n",
            encoding="utf-8",
        )
        adapter_script.chmod(0o755)
        adapter_env = {**os.environ, "NIZAM_MUTATION_ADAPTER": f"{sys.executable} {adapter_script}"}

        cmd_code = (
            "import os, pathlib; "
            "assert os.environ['NIZAM_WA120_FIXTURE'] == 'observed'; "
            f"pathlib.Path({str(counter_file)!r}).open('a').write('ran\\n'); "
            f"print({fixture.diagnostic!r})"
        )
        res_chain_cap = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "capture",
                "--id",
                "120",
                "--step",
                "feature-complete",
                "--attempt",
                "1",
                "--output-dir",
                "proof/captures",
                "--candidate",
                cand_sha,
                "--env-var",
                "NIZAM_WA120_FIXTURE=observed",
                "--agent-id",
                fixture.producer["agent_id"],
                "--session-id",
                fixture.producer["session_id"],
                "--root",
                str(froot),
                "--",
                sys.executable,
                "-c",
                cmd_code,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_chain_cap, 0, '"binding_state": "candidate-bound"')
        raw_cap = json.loads(res_chain_cap.stdout)
        assert len(counter_file.read_text(encoding="utf-8").splitlines()) == 1

        # Publish the raw capture into Git via --mode publish + NIZAM_MUTATION_ADAPTER and project the closed 12-field receipt capture
        res_pub = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "publish",
                "--mode",
                "publish",
                "--capture",
                raw_cap["capture_path"],
                "--root",
                str(froot),
            ],
            cwd=ROOT,
            env=adapter_env,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_pub, 0, '"receipt_capture_ref"')
        pub_doc = json.loads(res_pub.stdout)
        assert set(pub_doc["receipt_capture"].keys()) == {
            "schema_version",
            "argv",
            "cwd",
            "revision",
            "candidate_sha256",
            "environment",
            "producer",
            "executed",
            "outcome",
            "exit_code",
            "stdout",
            "stderr",
        }
        # Command was NOT re-executed during publish
        assert len(counter_file.read_text(encoding="utf-8").splitlines()) == 1

        # Prepare policy and state files on disk in fixture.root
        policy_doc = json.loads(json.dumps(fixture.policy))
        policy_doc["commands"] = [
            {
                "argv": [sys.executable, "-c", cmd_code],
                "expected_exit": 0,
                "proof_kind": "success",
                "diagnostic": fixture.diagnostic,
                "capture": pub_doc["receipt_capture_ref"],
            }
        ]
        policy_path = froot / "proof" / "chain-policy.json"
        policy_path.write_bytes(twa.canonical(policy_doc) + b"\n")
        state_path = froot / "record.json"
        state_path.write_text(json.dumps(fixture.state, indent=2) + "\n", encoding="utf-8")
        receipt_out_path = froot / "proof" / "chain-receipt.json"

        # Build and verify receipt via build-receipt CLI (--commit mediated by NIZAM_MUTATION_ADAPTER)
        res_build = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "build-receipt",
                "--policy",
                str(policy_path),
                "--published",
                pub_doc["published_path"],
                "--output",
                str(receipt_out_path),
                "--update-policy",
                "--commit",
                "--root",
                str(froot),
            ],
            cwd=ROOT,
            env=adapter_env,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_build, 0, '"verified": true')

        # Also verify directly via workflow_assurance.py verify-receipt CLI
        res_wa_verify = subprocess.run(
            [
                sys.executable,
                str(WA_TOOL),
                "verify-receipt",
                "--root",
                str(froot),
                "--policy",
                str(policy_path),
                "--receipt",
                str(receipt_out_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_wa_verify, 0, '"status":"passed"')

        # Advance state once via start_path.py resume --apply
        res_resume_1 = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "resume",
                "--root",
                str(froot),
                "--policy",
                str(policy_path),
                "--receipt",
                str(receipt_out_path),
                "--state",
                str(state_path),
                "--apply",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_resume_1, 0, '"action": "advance"')
        expect(res_resume_1, 0, '"applied": true')

        # Second resume is idempotent noop and never re-executes the command
        res_resume_2 = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "resume",
                "--root",
                str(froot),
                "--policy",
                str(policy_path),
                "--receipt",
                str(receipt_out_path),
                "--state",
                str(state_path),
                "--apply",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_resume_2, 0, '"action": "noop"')
        assert len(counter_file.read_text(encoding="utf-8").splitlines()) == 1

        # Route-bound receipt stage ('trivial-complete') positive and negative test
        triv_intent = {
            "id": "120",
            "path": "trivial",
            "summary": "Trivial README update.",
            "needs_new_contract": False,
            "files": ["README.md"],
        }
        triv_ev_ref = fixture.pin("proof/triv-ev.txt", b"verified trivial output\n")
        triv_intent_ref = fixture.pin("proof/triv-intent.json", triv_intent)
        triv_qa = qa("120", "proof/triv-ev.txt")
        triv_qa["reviewed_revision"] = triv_intent_ref["revision"]
        triv_qa["intent_sha256"] = triv_intent_ref["sha256"]
        triv_qa["reviewer"] = "fixture-route-qa"
        triv_qa_ref = fixture.pin("proof/triv-qa.json", triv_qa)

        route_policy = json.loads(json.dumps(policy_doc))
        route_policy["stage"] = "trivial-complete"
        route_policy["operation_id"] = "route-op-triv-120"
        route_policy["contract"] = triv_intent_ref
        route_policy["operator"] = triv_intent_ref
        route_policy["prerequisites"] = [
            {
                "kind": "route-intent",
                "artifact": triv_intent_ref,
                "feature_id": "120",
                "assessed_revision": triv_intent_ref["revision"],
                "contract_sha256": triv_intent_ref["sha256"],
            },
            {
                "kind": "route-qa",
                "artifact": triv_qa_ref,
                "feature_id": "120",
                "assessed_revision": triv_intent_ref["revision"],
                "contract_sha256": triv_intent_ref["sha256"],
            },
        ]
        route_policy_path = froot / "proof" / "route-policy.json"
        route_policy_path.write_bytes(twa.canonical(route_policy) + b"\n")
        route_receipt_path = froot / "proof" / "route-receipt.json"
        res_route_build = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "build-receipt",
                "--policy",
                str(route_policy_path),
                "--published",
                pub_doc["published_path"],
                "--output",
                str(route_receipt_path),
                "--root",
                str(froot),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_route_build, 0, '"verified": true')

        # Negative: route-bound receipt attempting to cover schema/contract.schema.json under trivial-complete is rejected
        bad_triv_intent = dict(triv_intent, files=["schema/contract.schema.json"])
        bad_triv_ref = fixture.pin("proof/bad-triv-intent.json", bad_triv_intent)
        route_policy["contract"] = bad_triv_ref
        route_policy["operator"] = bad_triv_ref
        route_policy["prerequisites"][0]["artifact"] = bad_triv_ref
        route_policy["prerequisites"][0]["assessed_revision"] = bad_triv_ref["revision"]
        route_policy["prerequisites"][0]["contract_sha256"] = bad_triv_ref["sha256"]
        route_policy["prerequisites"][1]["contract_sha256"] = bad_triv_ref["sha256"]
        route_policy_path.write_bytes(twa.canonical(route_policy) + b"\n")
        res_bad_route = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "build-receipt",
                "--policy",
                str(route_policy_path),
                "--published",
                pub_doc["published_path"],
                "--output",
                str(route_receipt_path),
                "--root",
                str(froot),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expect(res_bad_route, 1, "trivial path cannot modify")

        # --- B1 + C1 Discrimination Suite (Closing V1 and F1) ---
        def _git_head_and_index_sha(repo_root: Path) -> tuple[str, str]:
            h = subprocess.run(
                ["git", "--no-optional-locks", "-C", str(repo_root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            idx_rel = subprocess.run(
                ["git", "--no-optional-locks", "-C", str(repo_root), "rev-parse", "--git-path", "index"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            idx_p = Path(idx_rel) if Path(idx_rel).is_absolute() else (repo_root / idx_rel)
            idx_sha = twa.sha(idx_p.read_bytes()) if idx_p.is_file() else "none"
            return h, idx_sha

        # (B1.a + C1 P2 mtime check) Repeated identical publication and mtime-only touch preserve HEAD and .git/index bytes identically!
        head_before_noop, idx_before_noop = _git_head_and_index_sha(froot)
        cap_stdout_file = froot / raw_cap["stdout"]["path"]
        os.utime(cap_stdout_file, (1893456000, 1893456000))
        for noop_mode_args in ([], ["--mode", "prepare"], ["--mode", "finalize"], ["--mode", "publish"]):
            res_pub_noop = subprocess.run(
                [sys.executable, str(TOOL), "publish", *noop_mode_args, "--capture", raw_cap["capture_path"], "--root", str(froot)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            expect(res_pub_noop, 0, '"noop": true')
            assert _git_head_and_index_sha(froot) == (head_before_noop, idx_before_noop), (
                f"mtime-only replay in mode {noop_mode_args} mutated HEAD or .git/index!"
            )

        # (B1.b) Changed evidence attempting to overwrite prior accepted evidence is rejected
        orig_stdout_bytes = cap_stdout_file.read_bytes()
        raw_cap_file = froot / raw_cap["capture_path"]
        orig_raw_cap_bytes = raw_cap_file.read_bytes()
        tampered_stdout = orig_stdout_bytes + b"tampered-line\n"
        cap_stdout_file.write_bytes(tampered_stdout)
        tampered_raw = json.loads(orig_raw_cap_bytes.decode("utf-8"))
        tampered_raw["stdout"]["sha256"] = twa.sha(tampered_stdout)
        raw_cap_file.write_bytes(twa.canonical(tampered_raw) + b"\n")
        res_pub_overwrite = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--capture", raw_cap["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_pub_overwrite, 1, "cannot overwrite")
        cap_stdout_file.write_bytes(orig_stdout_bytes)
        raw_cap_file.write_bytes(orig_raw_cap_bytes)

        # (B1.c) Raw closed-capture input to build-receipt without commit authority:
        #   - Uncommitted raw closed capture fails closed WITHOUT mutating HEAD/.git/index
        #   - Committed raw closed capture succeeds read-only WITHOUT mutating HEAD/.git/index
        uncommitted_closed_path = froot / "proof" / "captures" / "uncommitted.receipt-capture.json"
        uncommitted_closed_path.write_bytes((froot / pub_doc["receipt_capture_ref"]["path"]).read_bytes())
        head_before_raw, idx_before_raw = _git_head_and_index_sha(froot)
        res_raw_uncommitted = subprocess.run(
            [
                sys.executable, str(TOOL), "build-receipt",
                "--policy", str(policy_path),
                "--published", "proof/captures/uncommitted.receipt-capture.json",
                "--output", str(froot / "proof" / "raw-uncommitted-receipt.json"),
                "--root", str(froot),
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_raw_uncommitted, 1, "raw closed capture is not committed in Git")
        assert _git_head_and_index_sha(froot) == (head_before_raw, idx_before_raw)
        uncommitted_closed_path.unlink()

        res_raw_committed = subprocess.run(
            [
                sys.executable, str(TOOL), "build-receipt",
                "--policy", str(policy_path),
                "--published", pub_doc["receipt_capture_ref"]["path"],
                "--output", str(froot / "proof" / "raw-committed-receipt.json"),
                "--root", str(froot),
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_raw_committed, 0, '"verified": true')
        assert _git_head_and_index_sha(froot) == (head_before_raw, idx_before_raw)

        # (B1.d + C1) Default noncommitting publish (prepare), strict adapter mediation (no/empty/{}/bool/invalid/denied),
        #             unknown_external_commit_outcome reconciliation, and base/branch/delta binding
        res_cap_b1 = subprocess.run(
            [
                sys.executable, str(TOOL), "capture",
                "--id", "120", "--step", "b1-noncommitting", "--attempt", "1",
                "--output-dir", "proof/captures", "--candidate", cand_sha,
                "--env-var", "NIZAM_WA120_FIXTURE=observed",
                "--agent-id", fixture.producer["agent_id"],
                "--session-id", fixture.producer["session_id"],
                "--root", str(froot),
                "--", sys.executable, "-c", cmd_code,
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_cap_b1, 0, '"binding_state": "candidate-bound"')
        cap_b1 = json.loads(res_cap_b1.stdout)
        assert _git_head_and_index_sha(froot) == (head_before_raw, idx_before_raw)

        # Stage an unrelated file and create an unrelated unstaged file to prove they are preserved
        unrelated_staged = froot / "proof" / "unrelated-staged.txt"
        unrelated_staged.write_text("unrelated staged content\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(froot), "add", "--", "proof/unrelated-staged.txt"], check=True)
        unrelated_unstaged = froot / "proof" / "unrelated-unstaged.txt"
        unrelated_unstaged.write_text("unrelated unstaged content\n", encoding="utf-8")
        head_with_staged, idx_with_staged = _git_head_and_index_sha(froot)

        # Default `publish` (without --mode) is noncommitting `prepare`!
        res_prep1 = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_prep1, 0, '"stage": "outputs_pending"')
        expect(res_prep1, 0, '"status": "pending_external_commit"')
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)
        prep1_doc = json.loads(res_prep1.stdout)
        req_b1_path = froot / prep1_doc["publish_request_path"]
        assert req_b1_path.is_file()
        assert prep1_doc["commit_request"]["intended_base"] == head_with_staged
        assert "intended_branch" in prep1_doc["commit_request"]

        # C1.1: `--mode publish` without NIZAM_MUTATION_ADAPTER fails closed without local commit fallback
        env_no_adapter = {k: v for k, v in os.environ.items() if k not in ("NIZAM_MUTATION_ADAPTER", "NIZAM_MUTATION_POLICY")}
        res_no_adapter = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=env_no_adapter, text=True, capture_output=True, check=False,
        )
        expect(res_no_adapter, 1, "external commit mediation required for --mode publish")
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # C1.2: Adapter returning empty stdout, `{}`, `true`, invalid JSON, `approved=false`, or `status=denied/pending/failed` all fail closed
        import shlex

        for probe_code, expected_msg in (
            ("", "returned empty stdout"),
            ("print('{}')", "missing required completion fields"),
            ("print('true')", "response must be a JSON object"),
            ("print('not-json')", "returned invalid JSON"),
            ('print(\'{"approved": false, "status": "denied"}\')', "git commit denied by runtime mutation adapter"),
            ('print(\'{"status": "pending"}\')', "git commit pending by runtime mutation adapter"),
            ('print(\'{"status": "failed"}\')', "git commit failed by runtime mutation adapter"),
        ):
            probe_env = {**env_no_adapter, "NIZAM_MUTATION_ADAPTER": f"{shlex.quote(sys.executable)} -c {shlex.quote(probe_code)}"}
            res_probe = subprocess.run(
                [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
                cwd=ROOT, env=probe_env, text=True, capture_output=True, check=False,
            )
            expect(res_probe, 1, expected_msg)
            assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # Simulated commit denial via NIZAM_MUTATION_ADAPTER=deny leaves HEAD, .git/index, and unrelated staged unchanged
        deny_env = {**os.environ, "NIZAM_MUTATION_ADAPTER": "deny"}
        res_deny = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=deny_env, text=True, capture_output=True, check=False,
        )
        expect(res_deny, 1, "denied by runtime mutation authority")
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # Real commit denial via failing .git/hooks/pre-commit inside adapter leaves HEAD and .git/index byte-for-byte unchanged!
        hooks_dir = froot / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_hook.write_text("#!/usr/bin/env bash\necho 'hook denied commit' >&2\nexit 1\n", encoding="utf-8")
        pre_commit_hook.chmod(0o755)
        res_hook_deny = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=adapter_env, text=True, capture_output=True, check=False,
        )
        expect(res_hook_deny, 1, "hook denied commit")
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)
        pre_commit_hook.unlink()

        # Same-path staged conflict in .git/index is rejected without clobbering existing staged content
        subprocess.run(["git", "-C", str(froot), "add", "--", cap_b1["stdout"]["path"]], check=True)
        _, idx_with_conflict = _git_head_and_index_sha(froot)
        res_conflict = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=adapter_env, text=True, capture_output=True, check=False,
        )
        expect(res_conflict, 1, "same-path staged conflict in .git/index")
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_conflict)
        subprocess.run(["git", "-C", str(froot), "reset", "-q", "HEAD", "--", cap_b1["stdout"]["path"]], check=True)
        _, idx_with_staged = _git_head_and_index_sha(froot)

        # Failed git diff --cached / git status exits non-zero and never returns HEAD as if committed
        with tempfile.TemporaryDirectory(prefix="nizam-fake-git-") as fake_git_dir:
            real_git = shutil.which("git")
            fake_git = Path(fake_git_dir) / "git"
            fake_git.write_text(
                f'#!/usr/bin/env bash\n'
                f'for arg in "$@"; do\n'
                f'  if [ "$arg" = "diff" ]; then echo "simulated git diff failure" >&2; exit 128; fi\n'
                f'done\n'
                f'exec "{real_git}" "$@"\n',
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            bad_git_env = {**adapter_env, "PATH": f"{fake_git_dir}:{os.environ.get('PATH', '')}"}
            res_bad_diff = subprocess.run(
                [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
                cwd=ROOT, env=bad_git_env, text=True, capture_output=True, check=False,
            )
            expect(res_bad_diff, 1, "git diff --cached failed")
            assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # C1.3: Interrupted adapter (signal / unknown_external_commit_outcome) before commit and after commit reconciles cleanly
        sig_env = {
            **env_no_adapter,
            "NIZAM_MUTATION_ADAPTER": f"{sys.executable} -c 'import os, signal; os.kill(os.getpid(), signal.SIGTERM)'",
        }
        res_sig = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=sig_env, text=True, capture_output=True, check=False,
        )
        expect(res_sig, 1, "status=unknown_external_commit_outcome")
        assert json.loads(req_b1_path.read_text(encoding="utf-8"))["status"] == "unknown_external_commit_outcome"
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # Re-running prepare reconciles from unknown_external_commit_outcome when HEAD is still at intended_base
        res_reconcile_prep = subprocess.run(
            [sys.executable, str(TOOL), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_reconcile_prep, 0, '"reconciled_from_status": "unknown_external_commit_outcome"')

        # Adapter commits Stage 1 and then exits non-zero before acknowledging -> records unknown_external_commit_outcome
        fail_after_s1_env = {**adapter_env, "NIZAM_TEST_FAIL_AFTER_S1": "1"}
        res_fail_after_s1 = subprocess.run(
            [sys.executable, str(TOOL), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=fail_after_s1_env, text=True, capture_output=True, check=False,
        )
        expect(res_fail_after_s1, 1, "after HEAD advanced (status=unknown_external_commit_outcome)")
        head_s1, idx_s1 = _git_head_and_index_sha(froot)
        assert head_s1 != head_with_staged
        assert json.loads(req_b1_path.read_text(encoding="utf-8"))["status"] == "unknown_external_commit_outcome"

        # C1.4: Base/branch/delta binding negative probes on Stage 1 before Stage 2 preparation
        orig_req_b1 = json.loads(req_b1_path.read_text(encoding="utf-8"))
        # Wrong intended_base in publish-request is rejected
        bad_base_req = dict(orig_req_b1, intended_base="0" * 40)
        req_b1_path.write_text(json.dumps(bad_base_req), encoding="utf-8")
        res_bad_base = subprocess.run(
            [sys.executable, str(TOOL), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_base, 1, "does not match publish-request intended_base")
        # Wrong intended_branch in publish-request is rejected
        bad_branch_req = dict(orig_req_b1, intended_branch="nonexistent-branch-name", detached_head=False)
        req_b1_path.write_text(json.dumps(bad_branch_req), encoding="utf-8")
        res_bad_branch = subprocess.run(
            [sys.executable, str(TOOL), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_branch, 1, "does not match publish-request intended_branch")
        # Unauthorized file delta mismatch in publish-request is rejected
        bad_delta_req = dict(orig_req_b1, files=orig_req_b1["files"][:1])
        req_b1_path.write_text(json.dumps(bad_delta_req), encoding="utf-8")
        res_bad_delta = subprocess.run(
            [sys.executable, str(TOOL), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_delta, 1, "delta mismatch against publish-request")
        # Restore valid Stage 1 publish-request
        req_b1_path.write_text(json.dumps(orig_req_b1), encoding="utf-8")

        # Re-running prepare-publish reconciles the already-committed Stage 1 outputs and advances to Stage 2 receipt_capture_pending!
        res_prep2 = subprocess.run(
            [sys.executable, str(TOOL), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_prep2, 0, '"stage": "receipt_capture_pending"')
        assert _git_head_and_index_sha(froot) == (head_s1, idx_s1)
        prep2_doc = json.loads(res_prep2.stdout)
        assert prep2_doc["output_revision"] == head_s1

        # Finalize before Stage 2 is committed fails closed without mutating Git
        res_fin_early = subprocess.run(
            [sys.executable, str(TOOL), "finalize-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_fin_early, 1, "is not committed in Git")
        assert _git_head_and_index_sha(froot) == (head_s1, idx_s1)

        s2_specs = [f["literal_pathspec"] for f in prep2_doc["commit_request"]["files"]]
        with tempfile.TemporaryDirectory(prefix="nizam-ext-s2-") as td2:
            t_env2 = {**os.environ, "GIT_INDEX_FILE": str(Path(td2) / "index")}
            subprocess.run(["git", "-C", str(froot), "read-tree", head_s1], env=t_env2, check=True)
            subprocess.run(["git", "-C", str(froot), "add", "--", *s2_specs], env=t_env2, check=True)
            subprocess.run(["git", "-C", str(froot), "commit", "-qm", "ext s2", "--", *s2_specs], env=t_env2, check=True)
            subprocess.run(["git", "-C", str(froot), "reset", "-q", "HEAD", "--", *s2_specs], check=True)
        head_s2, idx_s2 = _git_head_and_index_sha(froot)

        res_fin = subprocess.run(
            [sys.executable, str(TOOL), "finalize-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_fin, 0, '"receipt_capture_ref"')
        assert _git_head_and_index_sha(froot) == (head_s2, idx_s2)

        # (B1.e) Multi-capture batch publication & two-stage interruption recovery without re-execution
        exec_before_batch = len(counter_file.read_text(encoding="utf-8").splitlines())
        batch_caps = []
        for step_name in ("batch-check-1", "batch-check-2"):
            rc_b = subprocess.run(
                [
                    sys.executable, str(TOOL), "capture",
                    "--id", "120", "--step", step_name, "--attempt", "1",
                    "--output-dir", "proof/captures", "--candidate", cand_sha,
                    "--env-var", "NIZAM_WA120_FIXTURE=observed",
                    "--agent-id", fixture.producer["agent_id"],
                    "--session-id", fixture.producer["session_id"],
                    "--root", str(froot),
                    "--", sys.executable, "-c", cmd_code,
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            expect(rc_b, 0, '"binding_state": "candidate-bound"')
            batch_caps.append(json.loads(rc_b.stdout)["capture_path"])
        assert len(counter_file.read_text(encoding="utf-8").splitlines()) == exec_before_batch + 2

        # Stop after Stage 1 outputs (simulating interruption between Stage 1 and Stage 2)
        res_stop_s1 = subprocess.run(
            [
                sys.executable, str(TOOL), "publish", "--mode", "publish",
                "--capture", batch_caps[0], "--capture", batch_caps[1],
                "--stop-after-stage", "outputs",
                "--root", str(froot),
            ],
            cwd=ROOT, env=adapter_env, text=True, capture_output=True, check=False,
        )
        expect(res_stop_s1, 0, '"status": "stopped_after_outputs"')
        head_after_batch_s1, _ = _git_head_and_index_sha(froot)

        # Resume publication across both captures: recovers from Stage 1 and commits Stage 2 in 1 commit without re-executing commands!
        res_batch_resume = subprocess.run(
            [
                sys.executable, str(TOOL), "publish", "--mode", "publish",
                "--capture", batch_caps[0], "--capture", batch_caps[1],
                "--root", str(froot),
            ],
            cwd=ROOT, env=adapter_env, text=True, capture_output=True, check=False,
        )
        expect(res_batch_resume, 0, '"published"')
        batch_pub_doc = json.loads(res_batch_resume.stdout)
        assert len(batch_pub_doc["published"]) == 2
        assert batch_pub_doc["published"][0]["output_revision"] == head_after_batch_s1
        assert batch_pub_doc["published"][1]["output_revision"] == head_after_batch_s1
        assert batch_pub_doc["published"][0]["receipt_capture_ref"]["revision"] == batch_pub_doc["published"][1]["receipt_capture_ref"]["revision"]
        assert len(counter_file.read_text(encoding="utf-8").splitlines()) == exec_before_batch + 2

        # Verify unrelated staged and unstaged files were preserved untouched throughout!
        staged_now = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(froot), "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        assert staged_now == ["proof/unrelated-staged.txt"], f"expected unrelated staged file preserved, got {staged_now}"
        assert unrelated_unstaged.read_text(encoding="utf-8") == "unrelated unstaged content\n"

    # 4. Concise status view on real repository root and synthetic contradiction probe (R8 + A5)
    res_status = run(ROOT, "status", "--format", "json")
    expect(res_status, 0, '"repository": "https://github.com/niq-cnr/nizam-framework.git"')
    status_doc = json.loads(res_status.stdout)
    assert status_doc["repository_binding_aligned"] is True
    assert [p["id"] for p in status_doc["phase_019_profiles"]] == ["124", "125"]
    assert status_doc["reconciled"] is True, f"unexpected contradictions: {status_doc['contradictions']}"
    assert status_doc["contradictions"] == []
    assert len(status_doc["discovered_feature_lists"]) >= 22
    assert len(status_doc["discovered_phase_yamls"]) >= 11

    # Synthetic cross-surface contradiction in isolated root
    write(
        root,
        "docs/planning/manifest.json",
        {
            "schema_version": 1,
            "current_phase": "022-portable-review-sandbox-adapter",
            "phases": [
                {
                    "id": "022-portable-review-sandbox-adapter",
                    "title": "Portable Sandbox",
                    "feature_list": ".agent/feature_list_022.json",
                    "status": "complete",
                }
            ],
        },
    )
    write(
        root,
        ".agent/feature_list_022.json",
        {
            "phase": "022-portable-review-sandbox-adapter",
            "phase_status": "in_progress",
            "features": [
                {
                    "id": "134",
                    "name": "Sandbox adapter",
                    "status": "in_progress",
                    "passes": False,
                }
            ],
        },
    )
    res_bad_status = run(root, "status", "--format", "json")
    expect(res_bad_status, 0, '"reconciled": false')
    bad_status_doc = json.loads(res_bad_status.stdout)
    assert bad_status_doc["reconciled"] is False
    assert any("contradicts manifest status" in c for c in bad_status_doc["contradictions"])
    assert any("non-terminal features: 134" in c for c in bad_status_doc["contradictions"])


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def test_jev_readiness_controls() -> None:
    """Prove strict QA normalization, complete-delta scope binding and contract identity consistency."""
    with tempfile.TemporaryDirectory(prefix="nizam-jev-qa-") as qa_dir:
        root = Path(qa_dir).resolve()
        legacy_ok = {
            "feature_id": "gate",
            "verdict": "pass",
            "executed_at": "2026-10-22T00:00:00Z",
            "checks": [
                {"command": "true", "exit_code": 0, "evidence": ".agent/evidence/gate-out.txt"}
            ],
            "required_fixes": [],
        }
        legacy_failed = dict(legacy_ok)
        legacy_failed["checks"] = [
            {"command": "false", "exit_code": 1, "evidence": ".agent/evidence/gate-out.txt"}
        ]
        legacy_blocked = dict(legacy_ok)
        legacy_blocked["issues"] = [{"description": "real blocker"}]
        evolved_contradiction = qa("gate", ".agent/evidence/gate-out.txt")
        evolved_contradiction["final_verdict"] = {"approved": False, "summary": "rejected"}
        evolved_short_evidence = qa("gate", ".agent/evidence/gate-out.txt")
        evolved_short_evidence["checks_run"] = 2
        evolved_short_evidence["checks_passed"] = 2

        write(
            root,
            ".agent/evidence/gate-intent.json",
            {
                "id": "gate",
                "path": "trivial",
                "summary": "Probe the normalized QA predicate.",
                "needs_new_contract": False,
                "files": ["README.md"],
            },
        )
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (root / ".agent/evidence/gate-out.txt").write_text("captured output\n", encoding="utf-8")

        for payload, code, text in (
            (legacy_ok, 0, "recorded verification result exists"),
            (legacy_failed, 1, "does not pass"),
            (legacy_blocked, 1, "does not pass"),
            (evolved_contradiction, 1, "does not pass"),
            (evolved_short_evidence, 1, "does not pass"),
        ):
            write(root, ".agent/qa/gate.json", payload)
            expect(run(root, "begin", "trivial", "--id", "gate"), 0, "implementation may begin")
            expect(run(root, "done", "trivial", "--id", "gate"), code, text)
            (root / ".agent/evidence/gate-base.json").unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="nizam-jev-scope-") as git_dir:
        git_root = Path(git_dir).resolve()
        _git(git_root, "init", "-q")
        _git(git_root, "config", "user.name", "Test")
        _git(git_root, "config", "user.email", "test@example.invalid")
        (git_root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (git_root / "OLD.txt").write_text("old\n", encoding="utf-8")
        _git(git_root, "add", "-A")
        _git(git_root, "commit", "-qm", "init")
        write(
            git_root,
            ".agent/evidence/delta-intent.json",
            {
                "id": "delta",
                "path": "small-change",
                "summary": "Update README only.",
                "needs_new_contract": False,
                "files": ["README.md"],
            },
        )
        expect(run(git_root, "begin", "small-change", "--id", "delta"), 0, "implementation may begin")
        (git_root / "README.md").write_text("# Demo updated\n", encoding="utf-8")
        (git_root / ".agent/evidence/delta-out.txt").write_text("captured\n", encoding="utf-8")
        write(git_root, ".agent/qa/delta.json", qa("delta", ".agent/evidence/delta-out.txt"))

        (git_root / "UNDECLARED.py").write_text("print('x')\n", encoding="utf-8")
        expect(run(git_root, "done", "small-change", "--id", "delta"), 1, "UNDECLARED.py")
        (git_root / "UNDECLARED.py").unlink()

        expect(
            run(git_root, "done", "small-change", "--id", "delta"),
            0,
            "recorded verification result exists",
        )

        (git_root / "COMMITTED.py").write_text("print('c')\n", encoding="utf-8")
        _git(git_root, "add", "COMMITTED.py")
        _git(git_root, "commit", "-qm", "undeclared committed change")
        expect(run(git_root, "done", "small-change", "--id", "delta"), 1, "COMMITTED.py")

        _git(git_root, "rm", "-q", "COMMITTED.py")
        _git(git_root, "commit", "-qm", "remove committed")
        _git(git_root, "mv", "OLD.txt", "RENAMED.txt")
        _git(git_root, "commit", "-qm", "rename")
        expect(run(git_root, "done", "small-change", "--id", "delta"), 1, "RENAMED.txt")

        _git(git_root, "mv", "RENAMED.txt", "OLD.txt")
        _git(git_root, "commit", "-qm", "rename back")
        (git_root / ".agent/run_state.json").write_text("{}\n", encoding="utf-8")
        expect(run(git_root, "done", "small-change", "--id", "delta"), 1, ".agent/run_state.json")

    with tempfile.TemporaryDirectory(prefix="nizam-jev-contract-") as contract_dir:
        croot = Path(contract_dir).resolve()
        mismatched = contract("approved", ["README.md"])
        mismatched["feature_id"] = "different-task"
        write(croot, ".agent/contracts/c1.json", mismatched)
        write(croot, ".agent/evidence/bound-scope.json", scope("bound", ["README.md"], "c1"))
        write(croot, ".agent/evidence/bound-cause.json", cause("bound"))
        expect(run(croot, "begin", "bugfix", "--id", "bound"), 1, "disagree")

    print("jev-readiness: strict QA, complete-delta scope and contract identity controls pass")


def test_jev_readiness_attempts() -> None:
    """Prove authoritative monotonic attempt allocation (F06/JR-05)."""
    with tempfile.TemporaryDirectory(prefix="nizam-jev-attempt-") as attempt_dir:
        root = Path(attempt_dir).resolve()
        out = str(root / ".agent/evidence/captures")

        res1 = run_raw(
            "capture", "--id", "mono", "--step", "check", "--attempt", "1",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('one')",
        )
        expect(res1, 0, '"outcome": "success"')

        res_reuse = run_raw(
            "capture", "--id", "mono", "--step", "check", "--attempt", "1",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('reuse')",
        )
        expect(res_reuse, 2, "reuses already-consumed attempt history")

        out2 = str(root / ".agent/evidence/other")
        res_hidden = run_raw(
            "capture", "--id", "mono", "--step", "check", "--attempt", "1",
            "--output-dir", out2, "--root", str(root), "--",
            sys.executable, "-c", "print('hidden')",
        )
        expect(res_hidden, 2, "reuses already-consumed attempt history")

        res2 = run_raw(
            "capture", "--id", "mono", "--step", "check", "--attempt", "2",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('two')",
        )
        expect(res2, 0, '"outcome": "success"')

        assert (root / ".agent/evidence/mono-check-attempt1.reservation.json").is_file()
        assert (root / ".agent/evidence/mono-check-attempt2.reservation.json").is_file()

    print("jev-readiness: authoritative monotonic attempt allocation passes")


def test_jev_readiness_authority() -> None:
    """Prove narrative summaries cannot substitute for verified continuation authority (F07/JR-06)."""
    with tempfile.TemporaryDirectory(prefix="nizam-jev-auth-") as auth_dir:
        root = Path(auth_dir).resolve()
        (root / ".agent").mkdir(parents=True)
        out = str(root / ".agent/evidence/captures")

        res_op = run_raw(
            "capture", "--id", "op", "--step", "verify", "--attempt", "4",
            "--continuation-basis", "operator-reset",
            "--repair-summary", "operator said to continue",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('op')",
        )
        expect(res_op, 2, "requires recorded operator authorization")

        res_am = run_raw(
            "capture", "--id", "am", "--step", "verify", "--attempt", "4",
            "--continuation-basis", "bounded-amendment",
            "--repair-summary", "I amended the contract",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('am')",
        )
        expect(res_am, 2, "requires a recorded contract amendment")

        res_dc = run_raw(
            "capture", "--id", "dc", "--step", "verify", "--attempt", "4",
            "--continuation-basis", "verified-decomposition",
            "--repair-summary", "I decomposed the task",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('dc')",
        )
        expect(res_dc, 2, "requires --decomposition-of")

    print("jev-readiness: continuation authority cannot be granted by narrative summary")


def _r02_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # The older _git helper intentionally returns None; these controls inspect actual output.
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True,
                          env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})


@contextmanager
def _r02_fixture(*, bugfix: bool = False):
    """Real disposable Git state; no network, inherited hooks or global Git configuration."""
    with tempfile.TemporaryDirectory(prefix="nizam-r02-") as tmp:
        root = Path(tmp)
        _r02_git(root, "init", "-q")
        _r02_git(root, "config", "user.name", "R02 Fixture")
        _r02_git(root, "config", "user.email", "r02@example.invalid")
        _r02_git(root, "config", "core.hooksPath", "/dev/null")
        _r02_git(root, "config", "commit.gpgsign", "false")
        _r02_git(root, "config", "core.filemode", "true")
        (root / "in_scope.py").write_text("original scoped content\n")
        (root / "outside.py").write_text("original outside content\n" * 20)
        (root / "outside.py").chmod(0o644)
        write(root, ".agent/run_state.json", {"status": "preserve"})
        if bugfix:
            write(root, "schema/demo.schema.json", {"type": "object"})
            write(root, ".agent/contracts/c1.json", contract("approved", ["in_scope.py", "schema/demo.schema.json"]))
        _r02_git(root, "add", ".")
        _r02_git(root, "commit", "-qm", "fixture baseline")
        if bugfix:
            write(root, ".agent/evidence/r02-cause.json", cause("r02"))
            write(root, ".agent/evidence/r02-scope.json", scope("r02", ["in_scope.py", "schema/demo.schema.json"], "c1"))
        else:
            write(root, ".agent/evidence/r02-intent.json", {
                "id": "r02", "path": "small-change", "summary": "Bounded content change",
                "needs_new_contract": False, "files": ["in_scope.py"],
            })
        yield root


def _r02_command(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(TOOL), *args, "--root", str(root)],
                          cwd=ROOT, text=True, capture_output=True, check=False, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})


def _r02_begin(root: Path, route: str = "small-change") -> None:
    expect(_r02_command(root, "begin", route, "--id", "r02"), 0, "implementation may begin")
    (root / "in_scope.py").write_text("legitimate task edit\n")


def _r02_qa(root: Path) -> None:
    evidence = ".agent/evidence/r02-check.txt"
    (root / evidence).write_text("fixture acceptance evidence\n")
    write(root, ".agent/qa/r02.json", qa("r02", evidence))


def _r02_done(root: Path, code: int = 0, needle: str = "recorded verification result exists", *, route: str = "small-change") -> None:
    _r02_qa(root)
    result = _r02_command(root, "done", route, "--id", "r02")
    expect(result, code, needle)
    if code == 1 and needle.endswith((".py", ".txt", ".json")):
        assert "undeclared changes" in result.stderr, result.stderr


def _r02_marker(root: Path) -> Path:
    return root / ".agent/evidence/r02-base.json"


def _r02_porcelain(root: Path) -> str:
    return _r02_git(root, "--no-optional-locks", "status", "--porcelain", "-z", "--untracked-files=all").stdout


def test_r02_completion_ac01() -> None:
    with _r02_fixture(bugfix=True) as root:
        _r02_begin(root, "bugfix")
        write(root, "schema/demo.schema.json", {"type": "string"})
        _r02_done(root, route="bugfix")


def test_r02_completion_ac02() -> None:
    variants = {"missing": "required record", "no-id": "approved contract_id", "proposed": "not already approved",
                "identity": "identity", "scope": "not inside the named contract"}
    for variant, needle in variants.items():
        with _r02_fixture(bugfix=True) as root:
            doc = contract("approved", ["in_scope.py", "schema/demo.schema.json"])
            if variant == "missing":
                (root / ".agent/contracts/c1.json").unlink()
            elif variant == "no-id":
                write(root, ".agent/evidence/r02-scope.json", scope("r02", ["in_scope.py", "schema/demo.schema.json"]))
            else:
                if variant == "proposed": doc["status"] = "proposed"
                if variant == "identity": doc["contract_id"] = doc["feature_id"] = "other"
                if variant == "scope": doc["scope"]["files_modify"] = [{"path": "in_scope.py", "purpose": "repair"}]
                write(root, ".agent/contracts/c1.json", doc)
            expect(_r02_command(root, "begin", "bugfix", "--id", "r02"), 1, needle)
            assert not _r02_marker(root).exists()
    for status in ("approved", "implemented", "complete"):
        with _r02_fixture(bugfix=True) as root:
            write(root, ".agent/contracts/c1.json", contract(status, ["in_scope.py", "schema/demo.schema.json"]))
            _r02_begin(root, "bugfix")
            _r02_done(root, route="bugfix")
            write(root, ".agent/contracts/c1.json", contract("proposed", ["in_scope.py", "schema/demo.schema.json"]))
            _r02_done(root, 1, "not already approved", route="bugfix")
    with _r02_fixture(bugfix=True) as root:
        write(root, ".agent/evidence/r02-scope.json", scope("r02", [".nizam/payload.json"], "c1"))
        expect(_r02_command(root, "begin", "bugfix", "--id", "r02"), 1, "installed .nizam/ payload is immutable")


def test_r02_completion_ac03() -> None:
    for variant in ("tracked", "untracked", "staged"):
        with _r02_fixture() as root:
            path = root / ("new.txt" if variant == "untracked" else "outside.py")
            path.write_bytes(b"inherited dirty bytes\n")
            if variant == "staged": _r02_git(root, "add", "outside.py")
            _r02_begin(root)
            before = (path.read_bytes(), (root / ".git/index").read_bytes(), _r02_marker(root).read_bytes())
            _r02_done(root)
            assert before == (path.read_bytes(), (root / ".git/index").read_bytes(), _r02_marker(root).read_bytes())


def test_r02_completion_ac04() -> None:
    with _r02_fixture() as root:
        path = root / "outside.py"
        path.write_text("inherited modification\n")
        _r02_begin(root)
        before = next(row for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py"))
        path.write_text("new undeclared bytes\n")
        after = next(row for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py"))
        assert before == after == " M outside.py"
        _r02_done(root, 1, "outside.py")


def test_r02_completion_ac05() -> None:
    for variant in ("unchanged-empty", "changed", "deleted"):
        with _r02_fixture() as root:
            path = root / "new.txt"
            path.write_bytes(b"")
            _r02_begin(root)
            obs = json.loads(_r02_marker(root).read_text())["observations"]["new.txt"]
            assert obs["index"] == [] and obs["worktree"]["sha256"] == hashlib.sha256(b"").hexdigest()
            if variant == "changed": path.write_bytes(b"new bytes")
            if variant == "deleted": path.unlink()
            _r02_done(root, 0 if variant == "unchanged-empty" else 1,
                      "recorded verification result exists" if variant == "unchanged-empty" else "new.txt")


def test_r02_completion_ac06() -> None:
    for variant in ("unchanged", "new-index", "index-to-worktree", "removed", "recreated", "worktree-only"):
        with _r02_fixture() as root:
            path = root / "outside.py"
            path.write_text("inherited staged bytes\n")
            _r02_git(root, "add", "outside.py")
            _r02_begin(root)
            before_code = next(row[:2] for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py"))
            if variant == "new-index":
                path.write_text("different staged bytes\n")
                _r02_git(root, "add", "outside.py")
                assert next(row[:2] for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py")) == before_code
            if variant == "index-to-worktree": _r02_git(root, "reset", "-q", "HEAD", "--", "outside.py")
            if variant in ("removed", "recreated"):
                _r02_git(root, "rm", "--cached", "-q", "outside.py")
            if variant == "recreated":
                path.write_text("replacement staged bytes\n")
                _r02_git(root, "add", "outside.py")
                path.write_text("inherited staged bytes\n")
            if variant == "worktree-only": path.write_text("new unstaged bytes\n")
            _r02_done(root, 0 if variant == "unchanged" else 1,
                      "recorded verification result exists" if variant == "unchanged" else "outside.py")


def test_r02_completion_ac07() -> None:
    with _r02_fixture() as root:
        path = root / "outside.py"
        path.write_text("inherited dirty bytes\n")
        _r02_begin(root)
        _r02_done(root)
        before = next(row for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py"))
        path.chmod(0o640)
        assert next(row for row in _r02_porcelain(root).split("\x00") if row.endswith("outside.py")) == before
        _r02_done(root, 1, "outside.py")


def test_r02_completion_ac08() -> None:
    with tempfile.TemporaryDirectory(prefix="nizam-r02-external-") as external, _r02_fixture() as root:
        target = Path(external) / "unreadable-special-target"
        os.mkfifo(target)
        link = root / "outside-link"
        link.symlink_to(target)
        _r02_begin(root)
        _r02_done(root)
        assert stat.S_ISFIFO(target.lstat().st_mode)
        link.unlink()
        link.symlink_to(Path(external) / "dangling-target")
        _r02_done(root, 1, "outside-link")
    with _r02_fixture() as root, tempfile.TemporaryDirectory(prefix="nizam-r02-ancestor-") as external:
        nested = root / "nested"
        nested.mkdir()
        (nested / "child.txt").write_text("tracked\n")
        _r02_git(root, "add", "nested/child.txt")
        _r02_git(root, "commit", "-qm", "nested baseline")
        (nested / "child.txt").write_text("inherited dirty\n")
        _r02_begin(root)
        (nested / "child.txt").unlink()
        nested.rmdir()
        external_child = Path(external) / "child.txt"
        external_child.write_text("external bytes must stay untouched\n")
        nested.symlink_to(external, target_is_directory=True)
        _r02_done(root, 1, "symlink ancestor")
        assert external_child.read_text() == "external bytes must stay untouched\n"


def test_r02_completion_ac09() -> None:
    for kind in ("rename", "copy"):
        for variant in ("unchanged", "destination-worktree", "original-worktree", "destination-index", "original-index"):
            with _r02_fixture() as root:
                original, destination = root / "outside.py", root / "destination.py"
                old = original.read_bytes()
                if kind == "rename":
                    _r02_git(root, "mv", "outside.py", "destination.py")
                else:
                    _r02_git(root, "config", "status.renames", "copies")
                    destination.write_bytes(old)
                    original.write_text("modified copy original\n" * 20)
                    _r02_git(root, "add", "outside.py", "destination.py")
                actual = _r02_porcelain(root)
                expected = ("R" if kind == "rename" else "C") + "  destination.py\x00outside.py\x00"
                assert expected in actual, (kind, actual)
                _r02_begin(root)
                observations = json.loads(_r02_marker(root).read_text())["observations"]
                assert {"outside.py", "destination.py"} <= observations.keys()
                path = original if variant.startswith("original") else destination
                inherited = path.read_bytes() if path.exists() else None
                if variant != "unchanged":
                    path.write_text("new endpoint bytes\n")
                    if variant.endswith("index"):
                        _r02_git(root, "add", path.name)
                        if inherited is None: path.unlink()
                        else: path.write_bytes(inherited)
                _r02_done(root, 0 if variant == "unchanged" else 1,
                          "recorded verification result exists" if variant == "unchanged" else path.name)


def test_r02_completion_ac10() -> None:
    for variant in ("modified", "deleted"):
        with _r02_fixture() as root:
            path = root / "outside.py"
            if variant == "modified": path.write_text("inherited modification\n")
            else: path.unlink()
            _r02_begin(root)
            _r02_git(root, "checkout", "HEAD", "--", "outside.py")
            assert "outside.py" not in _r02_porcelain(root)
            _r02_done(root, 1, "outside.py")


def test_r02_completion_ac11() -> None:
    for variant in ("committed", "masked-commit", "staged", "unstaged", "untracked", "rename", "shared-state"):
        with _r02_fixture() as root:
            _r02_begin(root)
            base = _r02_git(root, "rev-parse", "HEAD").stdout.strip()
            expected = "outside.py"
            if variant == "untracked":
                expected = "new.txt"
                (root / expected).write_text("new undeclared\n")
            elif variant == "rename":
                _r02_git(root, "mv", "outside.py", "renamed.py")
            elif variant == "shared-state":
                expected = ".agent/run_state.json"
                write(root, expected, {"status": "undeclared"})
            else:
                (root / "outside.py").write_text("new undeclared\n")
                if variant in ("staged", "committed", "masked-commit"):
                    _r02_git(root, "add", "outside.py")
                if variant in ("committed", "masked-commit"):
                    _r02_git(root, "commit", "-qm", "undeclared commit")
                if variant == "masked-commit":
                    _r02_git(root, "checkout", base, "--", "outside.py")
                    assert not _r02_git(root, "diff", base, "--", "outside.py").stdout
                    assert _r02_git(root, "diff", base, "HEAD", "--", "outside.py").stdout
            _r02_done(root, 1, expected)


def test_r02_completion_ac12() -> None:
    for inherited_declared in (False, True):
        with _r02_fixture() as root:
            if inherited_declared: (root / "in_scope.py").write_text("inherited declared change\n")
            _r02_begin(root)
            doc = json.loads(_r02_marker(root).read_text())
            doc["schema_version"] = 1
            del doc["observations"]
            _r02_marker(root).write_text(json.dumps(doc))
            before = _r02_marker(root).read_bytes()
            _r02_begin(root)
            _r02_done(root)
            assert _r02_marker(root).read_bytes() == before


def test_r02_completion_ac13() -> None:
    for variant in ("legacy", "version", "identity", "digest", "coverage", "index", "shape", "commit", "json"):
        with _r02_fixture() as root:
            (root / "outside.py").write_text("inherited dirty bytes\n")
            _r02_begin(root)
            marker = _r02_marker(root)
            doc = json.loads(marker.read_text())
            needle = "recorded task base"
            if variant == "legacy":
                doc["schema_version"] = 1
                del doc["observations"]
                needle = "preserve this marker and work"
            if variant == "version": doc["schema_version"] = 99
            if variant == "identity": doc["id"] = "wrong-task"
            if variant == "digest": doc["observations"]["outside.py"]["worktree"]["sha256"] = "not-a-digest"
            if variant == "coverage": del doc["observations"]["outside.py"]
            if variant == "index": doc["observations"]["outside.py"]["index"][0]["stage"] = True
            if variant == "shape": doc["pre_existing_entries"] = None
            if variant == "commit":
                doc["base_revision"] = "0" * 40
                needle = "Git rev-parse scope observation failed"
            marker.write_text("{" if variant == "json" else json.dumps(doc))
            before = (marker.read_bytes(), (root / "outside.py").read_bytes(), (root / ".git/index").read_bytes())
            expect(_r02_command(root, "begin", "small-change", "--id", "r02"), 1, needle)
            _r02_done(root, 1, needle)
            assert before == (marker.read_bytes(), (root / "outside.py").read_bytes(), (root / ".git/index").read_bytes())


def test_r02_completion_ac14() -> None:
    with _r02_fixture() as root:
        (root / "outside.py").write_text("inherited dirty bytes\n")
        _r02_begin(root)
        marker_before = _r02_marker(root).read_bytes()
        _r02_git(root, "add", "in_scope.py")
        _r02_git(root, "commit", "-qm", "declared task commit")
        (root / "outside.py").write_text("new undeclared bytes\n")
        _r02_begin(root)
        assert _r02_marker(root).read_bytes() == marker_before
        assert json.loads(marker_before)["base_revision"] != _r02_git(root, "rev-parse", "HEAD").stdout.strip()
        _r02_done(root, 1, "outside.py")


def _r02_module():
    spec = importlib.util.spec_from_file_location("nizam_r02_start_path", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _r02_reject(module, call, needle: str) -> None:
    try:
        call()
    except module.StartPathError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"observation unexpectedly passed: {needle}")


def test_r02_completion_ac15() -> None:
    module = _r02_module()
    cases = [("rev-parse", "failure", None), ("status", "failure", None), ("ls-files", "failure", None),
             ("status", "malformed", b" M outside.py"), ("status", "malformed", b"M\x00"),
             ("status", "partial", b"R  renamed.py\x00"), ("ls-files", "malformed", b"broken\x00"),
             ("ls-files", "partial", b"100644 " + b"a" * 40 + b" 0\toutside.py"),
             ("rev-parse", "commit", "not-a-commit\n")]
    for decision in ("begin", "done"):
        for target, kind, output in cases:
            with _r02_fixture() as root:
                (root / "outside.py").write_text("inherited dirty bytes\n")
                if decision == "done": _r02_begin(root)
                _r02_qa(root)
                original = module._run_git_readonly
                def broken(where, args, *, text=False):
                    matches = args[0] == target and (kind != "commit" or "--verify" in args)
                    if matches:
                        value = output if output is not None else ("" if text else b"")
                        return subprocess.CompletedProcess(args, 1 if kind == "failure" else 0, value, "" if text else b"")
                    return original(where, args, text=text)
                marker_before = _r02_marker(root).read_bytes() if _r02_marker(root).exists() else None
                with mock.patch.object(module, "_run_git_readonly", side_effect=broken):
                    _r02_reject(module, lambda: module.decide(decision, "small-change", "r02", root),
                                "observation" if kind != "failure" else "failed")
                assert (_r02_marker(root).read_bytes() if _r02_marker(root).exists() else None) == marker_before
        with _r02_fixture() as root:
            (root / "outside.py").write_text("inherited dirty bytes\n")
            if decision == "done": _r02_begin(root)
            _r02_qa(root)
            original_open = module.os.open
            def unreadable(path, flags, *args, **kwargs):
                if Path(path) == root / "outside.py": raise PermissionError("injected required fingerprint read error")
                return original_open(path, flags, *args, **kwargs)
            with mock.patch.object(module.os, "open", side_effect=unreadable):
                _r02_reject(module, lambda: module.decide(decision, "small-change", "r02", root), "cannot read worktree scope identity")
    with _r02_fixture() as root:
        _r02_begin(root)
        _r02_qa(root)
        original = module._run_git_readonly
        def incomplete_diff(where, args, *, text=False):
            if args[0] == "diff": return subprocess.CompletedProcess(args, 0, b"R100\x00only-one\x00", b"")
            return original(where, args, text=text)
        with mock.patch.object(module, "_run_git_readonly", side_effect=incomplete_diff):
            _r02_reject(module, lambda: module.decide("done", "small-change", "r02", root), "partial Git diff")
    with tempfile.TemporaryDirectory(prefix="nizam-r02-local-") as tmp:
        root = Path(tmp)
        (root / "in_scope.py").write_text("local content\n")
        write(root, ".agent/evidence/r02-intent.json", {"id": "r02", "path": "small-change", "summary": "local",
                                                        "needs_new_contract": False, "files": ["in_scope.py"]})
        _r02_begin(root)
        assert not _r02_marker(root).exists()
        _r02_done(root)


def test_r02_completion_ac16() -> None:
    for kind in ("fifo", "socket", "submodule", "unmerged"):
        with _r02_fixture() as root:
            handle = None
            try:
                if kind in ("fifo", "socket"):
                    (root / "outside.py").unlink()
                    if kind == "fifo": os.mkfifo(root / "outside.py")
                    else:
                        handle = socket.socket(socket.AF_UNIX)
                        handle.bind(str(root / "outside.py"))
                elif kind == "submodule":
                    nested = root / "vendor"
                    nested.mkdir()
                    _r02_git(nested, "init", "-q")
                    _r02_git(nested, "config", "user.name", "Nested Fixture")
                    _r02_git(nested, "config", "user.email", "nested@example.invalid")
                    _r02_git(nested, "config", "commit.gpgsign", "false")
                    (nested / "file.txt").write_text("nested\n")
                    _r02_git(nested, "add", "file.txt")
                    _r02_git(nested, "commit", "-qm", "nested fixture")
                    commit = _r02_git(nested, "rev-parse", "HEAD").stdout.strip()
                    _r02_git(root, "update-index", "--add", "--cacheinfo", f"160000,{commit},vendor")
                else:
                    oid = _r02_git(root, "rev-parse", "HEAD:outside.py").stdout.strip()
                    payload = "0 " + "0" * 40 + "\toutside.py\n" + "".join(f"100644 {oid} {stage}\toutside.py\n" for stage in (1, 2, 3))
                    subprocess.run(["git", "-C", str(root), "update-index", "--index-info"], input=payload,
                                   text=True, capture_output=True, check=True)
                expect(_r02_command(root, "begin", "small-change", "--id", "r02"), 1, "unsupported")
                assert not _r02_marker(root).exists()
            finally:
                if handle is not None: handle.close()
    for unsafe in ("../escape", "/absolute", "nested/../escape", "nested//file"):
        with _r02_fixture() as root:
            (root / "outside.py").write_text("inherited dirty bytes\n")
            _r02_begin(root)
            doc = json.loads(_r02_marker(root).read_text())
            for entry in doc["pre_existing_entries"]:
                entry["paths"] = [unsafe if path == "outside.py" else path for path in entry["paths"]]
            doc["observations"][unsafe] = doc["observations"].pop("outside.py")
            _r02_marker(root).write_text(json.dumps(doc))
            before = _r02_marker(root).read_bytes()
            _r02_done(root, 1, "unsafe path")
            assert _r02_marker(root).read_bytes() == before


def test_r02_completion_ac17() -> None:
    with _r02_fixture() as root:
        foreign = root / ".agent/evidence/other-task/old.txt"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("preserved unrelated evidence\n")
        _r02_begin(root)
        (root / ".agent/evidence/r02-note.txt").write_text("owned output\n")
        owned = root / ".agent/evidence/r02/nested.txt"
        owned.parent.mkdir()
        owned.write_text("owned nested output\n")
        _r02_done(root)
        assert foreign.read_text() == "preserved unrelated evidence\n"
        foreign.write_text("unauthorized evidence rewrite\n")
        _r02_done(root, 1, ".agent/evidence/other-task/old.txt")
    with _r02_fixture() as root:
        _r02_begin(root)
        foreign = root / ".agent/evidence/other-task/new.txt"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("new unrelated evidence\n")
        _r02_done(root, 1, ".agent/evidence/other-task/new.txt")


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
                "files": ["README.md"],
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
                "files": ["README.md"],
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
        test_a1_f1_f5_scope_completion_and_amendments(root)
        test_r6_r7_r8_preflight_capture_status_and_resume(root)

    test_jev_readiness_controls()
    test_jev_readiness_attempts()
    test_jev_readiness_authority()
    for check in (
        test_r02_completion_ac01, test_r02_completion_ac02, test_r02_completion_ac03,
        test_r02_completion_ac04, test_r02_completion_ac05, test_r02_completion_ac06,
        test_r02_completion_ac07, test_r02_completion_ac08, test_r02_completion_ac09,
        test_r02_completion_ac10, test_r02_completion_ac11, test_r02_completion_ac12,
        test_r02_completion_ac13, test_r02_completion_ac14, test_r02_completion_ac15,
        test_r02_completion_ac16, test_r02_completion_ac17,
    ):
        check()
    print("start-path: bugfix, small-change, trivial, classify, amend-contract, preflight, capture, publish, build-receipt, and status gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

