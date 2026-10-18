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

    # 3. Full producer-to-consumer chain on ReceiptFixture: capture -> publish -> build-receipt -> verify-receipt -> resume (F2 + A2)
    import test_workflow_assurance as twa
    import workflow_assurance as wa

    with tempfile.TemporaryDirectory(prefix="nizam-receipt-chain-") as chain_dir:
        os.environ["NIZAM_WA120_FIXTURE"] = "observed"
        fixture = twa.ReceiptFixture(wa, Path(chain_dir))
        froot = fixture.root
        cand_sha = twa.sha(twa.canonical(fixture.candidate))
        counter_file = froot / "proof" / "chain-exec-count.txt"

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

        # Publish the raw capture into Git and project the closed 12-field receipt capture
        res_pub = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "publish",
                "--capture",
                raw_cap["capture_path"],
                "--root",
                str(froot),
            ],
            cwd=ROOT,
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

        # Build and verify receipt via build-receipt CLI
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

    print("start-path: bugfix, small-change, trivial, classify, amend-contract, preflight, capture, publish, build-receipt, and status gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

