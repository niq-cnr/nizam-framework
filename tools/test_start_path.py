#!/usr/bin/env python3
"""Drive tools/start_path.py against temporary project records and live repository state."""

from __future__ import annotations

import json
import os
import importlib.util
import hashlib
from datetime import datetime, timezone
import time
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "start_path.py"
WA_TOOL = ROOT / "tools" / "workflow_assurance.py"


CHECK = {"id": "ordinary", "argv": [sys.executable, "-c", "pass"], "expected_exit": 0, "proof_kind": "success", "diagnostic": None}


def proof_bootstrap(root: Path) -> None:
    """Install the actual assessed implementation into a disposable consumer."""
    if (root / "tools/start_path.py").exists() or (root / ".nizam/tools/start_path.py").exists():
        return
    root.mkdir(parents=True, exist_ok=True)
    for relative in ["tools/start_path.py", "tools/workflow_assurance.py"] + ["schema/" + n + ".schema.json" for n in ("qa_verdict", "contract", "bugfix_scope", "bugfix_cause", "small_change_intent")]:
        target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (root / ".r02-source.txt").write_text("selected ordinary input\n")
    (root / ".r02-test.py").write_text("# selected fixture test input\n")
    if not (root / ".git").exists():
        _git(root, "init", "-q"); _git(root, "config", "user.name", "QA Fixture"); _git(root, "config", "user.email", "fixture@example.invalid")
    if subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], capture_output=True).returncode:
        _git(root, "remote", "add", "origin", "https://example.invalid/qa-fixture.git")
    paths = ["tools/start_path.py", "tools/workflow_assurance.py", "schema/qa_verdict.schema.json", "schema/contract.schema.json", "schema/bugfix_scope.schema.json", "schema/bugfix_cause.schema.json", "schema/small_change_intent.schema.json", ".r02-source.txt", ".r02-test.py"]
    _git(root, "add", "--", *paths); _git(root, "commit", "--only", "-qm", "actual QA fixture implementation", "--", *paths)


def record_proof(root: Path, path_id: str, extra_contract_inputs: list[str] | None = None) -> dict:
    """Execute a real check and bind its exact output to a pinned route candidate."""
    proof_bootstrap(root)
    prefix = ".nizam/" if (root / ".nizam/tools/workflow_assurance.py").exists() else ""
    spec = importlib.util.spec_from_file_location("proof_wa_" + path_id, root / (prefix + "tools/workflow_assurance.py"))
    wa = importlib.util.module_from_spec(spec); spec.loader.exec_module(wa)
    base = json.loads((root / f".agent/evidence/{path_id}-base.json").read_text())
    paths = wa.qa_authorization_paths(root, path_id)
    checks = wa.qa_required_checks(json.loads((root / next(p for p in paths if p.endswith(("-scope.json", "-intent.json")))).read_text())["verification"])
    selected = {"source": [".r02-source.txt"], "tests": [".r02-test.py"], "tools": ["tools/start_path.py", "tools/workflow_assurance.py", "schema/qa_verdict.schema.json", "schema/contract.schema.json", "schema/bugfix_scope.schema.json", "schema/bugfix_cause.schema.json", "schema/small_change_intent.schema.json"], "contracts": paths, "unknown_dependencies": []}
    selected["tools"] = [prefix + p for p in selected["tools"]]
    selected["contracts"] = sorted(set(paths + (extra_contract_inputs or [])))
    scope_files = base["authorization"]["files"]
    existing = [p for p in paths + scope_files if os.path.lexists(root / p)]
    _git(root, "add", "--", *existing)
    if subprocess.check_output(["git", "-C", str(root), "diff", "--cached", "--name-only"]):
        _git(root, "commit", "--only", "-qm", "assessed task and immutable authorization", "--", *existing)
    context = wa.qa_context_sha256(root, path_id, paths, checks)
    os.environ[wa.QA_CONTEXT_VARIABLE] = context
    os.environ[wa.QA_EXECUTION_ROOT_VARIABLE] = str(root.resolve())
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    candidate = wa.assess_route_candidate(root, path_id, revision, selected, [wa.QA_CONTEXT_VARIABLE, wa.QA_EXECUTION_ROOT_VARIABLE])
    folder = root / ".agent/evidence" / path_id; folder.mkdir(exist_ok=True)
    def ref(path):
        return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = folder / "candidate.json"; manifest.write_bytes(wa.canonical(candidate))
    proof_checks = []
    for check in checks:
        started = datetime.now(timezone.utc).isoformat(); tick = time.monotonic()
        process = subprocess.run(check["argv"], cwd=root, capture_output=True, env=os.environ)
        completed = datetime.now(timezone.utc).isoformat()
        duration_ms = int((time.monotonic() - tick) * 1000)
        stdout = folder / (check["id"] + ".stdout"); stdout.write_bytes(process.stdout)
        stderr = folder / (check["id"] + ".stderr"); stderr.write_bytes(process.stderr)
        capture = {"schema_version": 1, "id": path_id, "argv": check["argv"], "cwd": str(root), "revision": revision, "candidate_sha256": wa.sha(wa.canonical(candidate)), "environment": candidate["environment"], "producer": {"agent_id": "actual-fixture", "session_id": "fixture-session"}, "executed": True, "completion_state": "completed", "proof_kind": check["proof_kind"], "outcome": check["proof_kind"] if process.returncode == 0 else "failed", "exit_code": process.returncode, "signal": None, "stdout": ref(stdout), "stderr": ref(stderr)}
        path = folder / (check["id"] + ".capture.json")
        capture.update(step=check["id"], attempt=1, binding_state="candidate-bound", started_at=started, completed_at=completed,
            duration_ms=duration_ms, cause_class=None, defect_signature=None, continuation_lineage={}, capture_path=path.relative_to(root).as_posix())
        path.write_bytes(wa.canonical(capture)); proof_checks.append({"id": check["id"], "capture": ref(path)})
    verdict = qa(path_id, str(folder.relative_to(root) / "ordinary.capture.json"))
    verdict.update(proof_version=2, candidate_ref=ref(manifest), checks=proof_checks, checks_run=len(checks), checks_passed=len(checks))
    write(root, f".agent/qa/{path_id}.json", verdict)
    return verdict


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the shipped start-path command against one project root."""
    proof_bootstrap(root)
    if args and args[0] == "begin" and "--id" in args:
        task = args[args.index("--id") + 1]
        if "/" not in task and not (root / f".agent/evidence/{task}-base.json").exists():
            authority = [p for p in (root / ".agent/evidence").glob(task + "-*.json") if p.is_file()] if (root / ".agent/evidence").exists() else []
            authority += list((root / ".agent/contracts").glob("*.json")) if (root / ".agent/contracts").exists() else []
            if authority:
                _git(root, "add", "--", *[str(p.relative_to(root)) for p in authority])
                if subprocess.check_output(["git", "-C", str(root), "diff", "--cached", "--name-only", "--", *[str(p.relative_to(root)) for p in authority]]): _git(root, "commit", "--only", "-qm", "task authorization before begin", "--", *[str(p.relative_to(root)) for p in authority])
    rooted_args = list(args)
    at = rooted_args.index("--") if "--" in rooted_args else len(rooted_args)
    rooted_args[at:at] = ["--root", str(root)]
    return subprocess.run(
        [sys.executable, str(root / (".nizam/tools/start_path.py" if (root / ".nizam/tools/start_path.py").exists() else "tools/start_path.py")), *rooted_args],
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
    if relative.endswith(("-scope.json", "-intent.json")) and isinstance(payload, dict) and "files" in payload and "verification" not in payload:
        payload = {**payload, "verification": [CHECK]}
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
            f"got exit {result.returncode} for {result.args!r}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def test_r5_classification_and_amendments(root: Path) -> None:
    """Verify semantic 5-route classification, trivial path, lightweight amendments, and verdict severity."""
    # 1. Trivial route classification
    res_trivial = run_raw("classify", "--files", "README.md", "--editorial")
    expect(res_trivial, 0, '"route": "trivial"')
    parsed_trivial = json.loads(res_trivial.stdout)
    assert parsed_trivial["stopping_conditions"]["initial_strategy_ladder_attempts"] == 3
    assert parsed_trivial["stopping_conditions"]["hard_attempt_cap"] == 6
    assert "finite task-wide" in parsed_trivial["stopping_conditions"]["attempt_counter_role"]
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
    record_proof(root, "triv")
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
    write(root, ".agent/evidence/bound-extended-cause.json", cause("bound-extended"))
    write(root, ".agent/evidence/bound-extended-scope.json", scope("bound-extended", ["README.md", "tools/start_path.py"], "c1"))
    expect(run(root, "begin", "bugfix", "--id", "bound-extended"), 0, "implementation may begin")

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
    empty_ev = ".agent/evidence/triv-qa-probe-empty.txt"
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
    expect(run(root, "done", "trivial", "--id", "triv-qa-probe"), 1, "structured QA proof")

    # Non-empty evidence file and matching id with checks_run=1 passes
    (root / empty_ev).write_text("verified README.md diff\n", encoding="utf-8")
    record_proof(root, "triv-qa-probe")
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
        record_proof(git_root, "drift")
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
    res_preflight = run(ROOT, "preflight")
    expect(res_preflight, 0, '"repository_binding_aligned": true')
    expect(res_preflight, 0, '"ok": true')
    preflight_doc = json.loads(res_preflight.stdout)
    for required_cap in ("installed", "available", "operational", "qualified", "status"):
        assert required_cap in preflight_doc["capabilities"], f"missing {required_cap} in preflight capabilities"
    res_preflight_sb = run(ROOT, "preflight", "--require-sandbox")
    if sp._probe_sandbox_operational(ROOT)[1]:
        expect(res_preflight_sb, 0, '"sandbox_operational": true')
        expect(res_preflight_sb, 0, '"ok": true')
    else:
        expect(res_preflight_sb, 1, '"sandbox_operational": false')
        expect(res_preflight_sb, 1, '"ok": false')

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
    expect(res_cap_4, 2, "finite configured step limit")

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
    expect(res_cap_4_decomp, 2, "real distinct failed parent")

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
    expect(res_cap_4_amend, 2, "finite configured step limit")

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
    for att_idx in (1, 2, 3):
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
        "4",
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
    expect(res_rep_halt, 2, "three failures of the same task-wide defect signature")

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
    expect(res_lim_halt, 2, "finite configured step limit (2)")
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
                str(froot / "tools/start_path.py"),
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
                "proof/qa-candidate.json",
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
                str(froot / "tools/start_path.py"),
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
                str(froot / "tools/start_path.py"),
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
                str(froot / "tools/workflow_assurance.py"),
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
                str(froot / "tools/start_path.py"),
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
                str(froot / "tools/start_path.py"),
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

        # Historical aggregate-only route receipt is now an explicit refusal control.
        # Full actual-capture route positives run in test_r02_structured_proof.
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
                str(froot / "tools/start_path.py"),
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
        expect(res_route_build, 1, 'immutable task base')

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
                str(froot / "tools/start_path.py"),
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
                [sys.executable, str(froot / "tools/start_path.py"), "publish", *noop_mode_args, "--capture", raw_cap["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--capture", raw_cap["capture_path"], "--root", str(froot)],
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
                sys.executable, str(froot / "tools/start_path.py"), "build-receipt",
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
                sys.executable, str(froot / "tools/start_path.py"), "build-receipt",
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
                sys.executable, str(froot / "tools/start_path.py"), "capture",
                "--id", "120", "--step", "b1-noncommitting", "--attempt", "1",
                "--output-dir", "proof/captures", "--candidate", "proof/qa-candidate.json",
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
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
                [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
                cwd=ROOT, env=probe_env, text=True, capture_output=True, check=False,
            )
            expect(res_probe, 1, expected_msg)
            assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # Simulated commit denial via NIZAM_MUTATION_ADAPTER=deny leaves HEAD, .git/index, and unrelated staged unchanged
        deny_env = {**os.environ, "NIZAM_MUTATION_ADAPTER": "deny"}
        res_deny = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=adapter_env, text=True, capture_output=True, check=False,
        )
        expect(res_hook_deny, 1, "hook denied commit")
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)
        pre_commit_hook.unlink()

        # Same-path staged conflict in .git/index is rejected without clobbering existing staged content
        subprocess.run(["git", "-C", str(froot), "add", "--", cap_b1["stdout"]["path"]], check=True)
        _, idx_with_conflict = _git_head_and_index_sha(froot)
        res_conflict = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
                [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, env=sig_env, text=True, capture_output=True, check=False,
        )
        expect(res_sig, 1, "status=unknown_external_commit_outcome")
        assert json.loads(req_b1_path.read_text(encoding="utf-8"))["status"] == "unknown_external_commit_outcome"
        assert _git_head_and_index_sha(froot) == (head_with_staged, idx_with_staged)

        # Re-running prepare reconciles from unknown_external_commit_outcome when HEAD is still at intended_base
        res_reconcile_prep = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_reconcile_prep, 0, '"reconciled_from_status": "unknown_external_commit_outcome"')

        # Adapter commits Stage 1 and then exits non-zero before acknowledging -> records unknown_external_commit_outcome
        fail_after_s1_env = {**adapter_env, "NIZAM_TEST_FAIL_AFTER_S1": "1"}
        res_fail_after_s1 = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_base, 1, "does not match publish-request intended_base")
        # Wrong intended_branch in publish-request is rejected
        bad_branch_req = dict(orig_req_b1, intended_branch="nonexistent-branch-name", detached_head=False)
        req_b1_path.write_text(json.dumps(bad_branch_req), encoding="utf-8")
        res_bad_branch = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_branch, 1, "does not match publish-request intended_branch")
        # Unauthorized file delta mismatch in publish-request is rejected
        bad_delta_req = dict(orig_req_b1, files=orig_req_b1["files"][:1])
        req_b1_path.write_text(json.dumps(bad_delta_req), encoding="utf-8")
        res_bad_delta = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_bad_delta, 1, "delta mismatch against publish-request")
        # Restore valid Stage 1 publish-request
        req_b1_path.write_text(json.dumps(orig_req_b1), encoding="utf-8")

        # Re-running prepare-publish reconciles the already-committed Stage 1 outputs and advances to Stage 2 receipt_capture_pending!
        res_prep2 = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "prepare-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        expect(res_prep2, 0, '"stage": "receipt_capture_pending"')
        assert _git_head_and_index_sha(froot) == (head_s1, idx_s1)
        prep2_doc = json.loads(res_prep2.stdout)
        assert prep2_doc["output_revision"] == head_s1

        # Finalize before Stage 2 is committed fails closed without mutating Git
        res_fin_early = subprocess.run(
            [sys.executable, str(froot / "tools/start_path.py"), "finalize-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
            [sys.executable, str(froot / "tools/start_path.py"), "finalize-publish", "--capture", cap_b1["capture_path"], "--root", str(froot)],
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
                    sys.executable, str(froot / "tools/start_path.py"), "capture",
                    "--id", "120", "--step", step_name, "--attempt", "1",
                    "--output-dir", "proof/captures", "--candidate", "proof/qa-candidate.json",
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
                sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish",
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
                sys.executable, str(froot / "tools/start_path.py"), "publish", "--mode", "publish",
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
            (legacy_ok, 1, "does not pass"),
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

        record_proof(git_root, "delta")
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
        expect(res_op, 2, "finite configured step limit")

        res_am = run_raw(
            "capture", "--id", "am", "--step", "verify", "--attempt", "4",
            "--continuation-basis", "bounded-amendment",
            "--repair-summary", "I amended the contract",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('am')",
        )
        expect(res_am, 2, "finite configured step limit")

        res_dc = run_raw(
            "capture", "--id", "dc", "--step", "verify", "--attempt", "4",
            "--continuation-basis", "verified-decomposition",
            "--repair-summary", "I decomposed the task",
            "--output-dir", out, "--root", str(root), "--",
            sys.executable, "-c", "print('dc')",
        )
        expect(res_dc, 2, "requires --decomposition-of")

    print("jev-readiness: continuation authority cannot be granted by narrative summary")


def test_r02_completion() -> None:
    """Real Git cases distinguish task authorization from inherited endpoint proof."""
    failures = []
    cases = ['schema-approved', 'schema-proposed', 'contract-revoked', 'contract-substituted',
             'tracked', 'untracked', 'index', 'mode', 'symlink', 'rename', 'restored',
             'unchanged', 'committed-cancel', 'staged-cancel', 'rename-source', 'legacy', 'legacy-clean',
             'malformed', 'repeat-begin', 'scope-substituted', 'unchanged-link', 'unchanged-rename']
    for case in cases:
        with tempfile.TemporaryDirectory(prefix='nizam-r02-') as name:
            root = Path(name)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args])
            git('init', '-q'); git('config', 'user.name', 'Test'); git('config', 'user.email', 'test@example.invalid')
            (root / 'README.md').write_text('base\n')
            (root / 'notes.txt').write_text('original\n')
            (root / 'link').symlink_to('notes.txt')
            git('add', '.'); git('commit', '-qm', 'initial')
            files = ['schema/demo.json'] if case.startswith('schema') else ['README.md']
            cid = 'c1' if case.startswith('schema') or case.startswith('contract') else None
            if cid:
                write(root, '.agent/contracts/c1.json', contract('proposed' if case == 'schema-proposed' else 'approved', files))
                write(root, '.agent/contracts/c2.json', {**contract('approved', files), 'contract_id': 'c2', 'feature_id': 'c2'})
            write(root, '.agent/evidence/r02-cause.json', cause('r02'))
            write(root, '.agent/evidence/r02-scope.json', scope('r02', files, cid))
            git('add', '.agent'); git('commit', '-qm', 'authority')
            if case in ('tracked', 'index', 'mode', 'restored', 'unchanged', 'legacy', 'malformed'):
                (root / 'notes.txt').write_text('inherited\n')
            if case == 'untracked': (root / 'new.txt').write_text('inherited\n')
            if case == 'index':
                git('add', 'notes.txt'); (root / 'notes.txt').write_text('original\n')
            if case in ('symlink', 'unchanged-link'):
                (root / 'link').unlink(); (root / 'link').symlink_to('README.md')
            if case in ('rename', 'unchanged-rename'): git('mv', 'notes.txt', 'renamed.txt')
            began = run(root, 'begin', 'bugfix', '--id', 'r02')
            if case == 'schema-proposed':
                if began.returncode == 0: failures.append(case)
                continue
            if began.returncode: failures.append(case + ':begin:' + began.stderr); continue
            if case in ('tracked', 'untracked', 'index'):
                target = root / ('new.txt' if case == 'untracked' else 'notes.txt')
                target.write_text('mutated\n')
                if case == 'index':
                    git('add', 'notes.txt'); target.write_text('original\n')
            if case == 'mode': (root / 'notes.txt').chmod(0o755)
            if case == 'symlink':
                (root / 'link').unlink(); (root / 'link').symlink_to('elsewhere')
            if case == 'rename': (root / 'renamed.txt').write_text('mutated\n')
            if case == 'restored': git('restore', 'notes.txt')
            if case == 'committed-cancel':
                (root / 'notes.txt').write_text('committed drift\n'); git('add', 'notes.txt'); git('commit', '-qm', 'drift')
                (root / 'notes.txt').write_text('original\n')
            if case == 'staged-cancel':
                (root / 'notes.txt').write_text('staged drift\n'); git('add', 'notes.txt')
                (root / 'notes.txt').write_text('original\n')
            if case == 'rename-source':
                git('mv', '-f', 'notes.txt', 'README.md')
            if case == 'contract-revoked': write(root, '.agent/contracts/c1.json', contract('proposed', files))
            if case == 'contract-substituted': write(root, '.agent/evidence/r02-scope.json', scope('r02', files, 'c2'))
            if case in ('legacy', 'legacy-clean', 'malformed'):
                base = json.loads((root / '.agent/evidence/r02-base.json').read_text())
                if case in ('legacy', 'legacy-clean'): base['schema_version'] = 1; base.pop('inherited_observations', None)
                else: base['inherited_observations'] = {'notes.txt': {}}
                write(root, '.agent/evidence/r02-base.json', base)
            if case in ('repeat-begin', 'scope-substituted'):
                marker = root / '.agent/evidence/r02-base.json'
                before = marker.read_bytes()
                write(root, '.agent/evidence/r02-scope.json', scope('r02', ['README.md', 'notes.txt']))
                if case == 'repeat-begin':
                    repeated = run(root, 'begin', 'bugfix', '--id', 'r02')
                    if repeated.returncode != 1 or marker.read_bytes() != before: failures.append(case)
                    continue
            if files[0].startswith('schema/'):
                (root / 'schema').mkdir(exist_ok=True); (root / files[0]).write_text('{}\n')
            else: (root / 'README.md').write_text('task change\n')
            ev = '.agent/evidence/r02-output.txt'; (root / ev).write_text('verified\n')
            write(root, '.agent/qa/r02.json', qa('r02', ev))
            positive = case in ('schema-approved', 'unchanged', 'unchanged-link', 'unchanged-rename')
            if positive: record_proof(root, 'r02')
            done = run(root, 'done', 'bugfix', '--id', 'r02')
            expected = 0 if positive else 1
            if done.returncode != expected: failures.append(case + ': expected ' + str(expected) + ', observed ' + str(done.returncode) + ': ' + done.stderr)
    assert not failures, '\n'.join(failures)


def route_receipt(root: Path, path_id: str, verdict: dict):
    """A complete route receipt with its own separately executed command."""
    prefix = '.nizam/' if (root / '.nizam/tools/workflow_assurance.py').exists() else ''
    spec = importlib.util.spec_from_file_location('route_receipt_api_' + path_id, root / (prefix + 'tools/workflow_assurance.py'))
    wa = importlib.util.module_from_spec(spec); spec.loader.exec_module(wa)
    candidate = json.loads((root / verdict['candidate_ref']['path']).read_text())
    base = json.loads((root / f'.agent/evidence/{path_id}-base.json').read_text())
    route = base['authorization']['route']
    intent_path = f'.agent/evidence/{path_id}-' + ('scope.json' if route == 'bugfix' else 'intent.json')
    def ref(path, revision):
        data = subprocess.check_output(['git', '-C', str(root), 'show', revision + ':' + path])
        return dict(path=path, sha256=hashlib.sha256(data).hexdigest(), revision=revision)
    intent = ref(intent_path, candidate['source_commit'])
    value = {**verdict, 'reviewed_revision': intent['revision'], 'intent_sha256': intent['sha256'], 'reviewer': 'actual-route-evaluator'}
    write(root, f'.agent/qa/{path_id}.json', value)
    folder = root / '.agent/evidence' / path_id; folder.mkdir(exist_ok=True)
    argv = [sys.executable, '-c', "print('ROUTE_RECEIPT_OK')"]
    process = subprocess.run(argv, cwd=root, capture_output=True, env=os.environ)
    stdout = folder / 'receipt.stdout'; stdout.write_bytes(process.stdout)
    stderr = folder / 'receipt.stderr'; stderr.write_bytes(process.stderr)
    selected = [str(p.relative_to(root)) for p in folder.iterdir() if p.is_file()] + [f'.agent/qa/{path_id}.json']
    _git(root, 'add', '--', *selected); _git(root, 'commit', '--only', '-qm', 'real route receipt proof', '--', *selected)
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    capture = dict(schema_version=1, argv=argv, cwd=str(root), revision=revision, candidate_sha256=wa.sha(wa.canonical(candidate)),
        environment=candidate['environment'], producer={'agent_id':'receipt-fixture','session_id':'receipt-session'},
        executed=True,outcome='success',exit_code=process.returncode,
        stdout=ref(str(stdout.relative_to(root)),revision),stderr=ref(str(stderr.relative_to(root)),revision))
    capture_path = f'.agent/evidence/{path_id}/receipt.capture.json'; write(root,capture_path,capture)
    _git(root,'add','--',capture_path);_git(root,'commit','--only','-qm','route receipt command capture','--',capture_path)
    capture_ref=ref(capture_path,subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip())
    qa_ref=ref(f'.agent/qa/{path_id}.json',revision)
    entries=[dict(kind=kind,artifact=reference,feature_id=path_id,assessed_revision=intent['revision'],contract_sha256=intent['sha256']) for kind,reference in [('route-intent',intent),('route-qa',qa_ref)]]
    policy=dict(schema_version=1,repository=candidate['repository'],feature_id=path_id,stage=route+'-complete',operation_id='route-proof-'+path_id,
        candidate=candidate,contract=intent,operator=intent,producer=capture['producer'],prerequisites=entries,
        commands=[dict(argv=argv,expected_exit=0,proof_kind='success',diagnostic='ROUTE_RECEIPT_OK',capture=capture_ref)],from_status='in_progress',to_status='complete',at='2026-10-24T00:00:00Z',recovery=None)
    gate=dict(final_verdict={'approved':True},issues=[],unsupported_claims=[],missing_acceptance_coverage=[])
    receipt={k:policy[k] for k in ('schema_version','repository','feature_id','stage','operation_id','candidate','producer','prerequisites')}
    receipt.update(status='passed',contract_ref=intent,operator_ref=intent,verdict=gate,
        checks=[dict(argv=argv,executed=True,outcome='success',exit_code=0,stdout=capture['stdout'],stderr=capture['stderr'],capture=capture_ref)])
    return wa, policy, receipt


def test_r02_structured_proof() -> None:
    """Full completion and full route receipt share real candidate-bound checks."""
    old_env = dict(os.environ)
    try:
        for layout in ('source','installed'):
            for inherited in ('tracked','untracked','symlink'):
                for mode in ('success','negative','wrapper'):
                    with tempfile.TemporaryDirectory(prefix='r02-proof-route-') as name:
                        root=Path(name);proof_bootstrap(root)
                        if layout=='installed':
                            (root/'.nizam').mkdir();_git(root,'mv','tools','.nizam/tools');_git(root,'mv','schema','.nizam/schema');_git(root,'commit','-qm','installed consumer layout')
                        (root/'README.md').write_text('task source\n');(root/'notes.txt').write_text('unrelated initial\n')
                        _git(root,'add','README.md','notes.txt');_git(root,'commit','-qm','initial task and unrelated input')
                        check=dict(CHECK)
                        if mode!='success':check.update(argv=[sys.executable,'-c',"print('EXPECTED_REFUSAL'); raise SystemExit(%s)"%(7 if mode=='negative' else 0)],expected_exit=7 if mode=='negative' else 0,proof_kind='semantic-negative',diagnostic='EXPECTED_REFUSAL')
                        write(root,'.agent/evidence/proof-cause.json',cause('proof'));write(root,'.agent/evidence/proof-scope.json',{**scope('proof',['README.md']),'verification':[check]})
                        # The inherited observation must precede begin, including an untracked symlink.
                        target=root/('notes.txt' if inherited=='tracked' else 'unrelated.txt')
                        if inherited=='symlink':target.symlink_to('notes.txt')
                        else:target.write_text('unchanged inherited work\n')
                        expect(run(root,'begin','bugfix','--id','proof'),0,'implementation may begin')
                        (root/'README.md').write_text('declared task edit\n')
                        verdict=record_proof(root,'proof')
                        expect(run(root,'done','bugfix','--id','proof'),0,'recorded verification result exists')
                        equivalent=dict(verdict);equivalent.pop('proof_version');write(root,'.agent/qa/proof.json',equivalent)
                        expect(run(root,'done','bugfix','--id','proof'),0,'recorded verification result exists')
                        write(root,'.agent/qa/proof.json',verdict)
                        wa,policy,receipt=route_receipt(root,'proof',verdict)
                        wa.verify_stage_receipt(root,receipt,policy=policy)
                        # Transfer exact proof to another filesystem root without pretending its command ran again.
                        with tempfile.TemporaryDirectory(prefix='r02-portable-') as clone_parent:
                            clone=Path(clone_parent)/'consumer'
                            subprocess.run(['git','clone','-q','--local',str(root),str(clone)],check=True,capture_output=True)
                            _git(clone,'remote','set-url','origin',policy['repository'])
                            inherited_clone=clone/target.relative_to(root)
                            if target.is_symlink():inherited_clone.symlink_to(os.readlink(target))
                            else:shutil.copyfile(target,inherited_clone)
                            expect(run(clone,'done','bugfix','--id','proof'),0,'recorded verification result exists')
                            prefix='.nizam/' if layout=='installed' else ''
                            spec=importlib.util.spec_from_file_location('clone_proof_api',clone/(prefix+'tools/workflow_assurance.py'))
                            clone_api=importlib.util.module_from_spec(spec);spec.loader.exec_module(clone_api)
                            clone_api.verify_stage_receipt(clone,receipt,policy=policy)
                            marker=clone/'.agent/evidence/proof/should-not-execute.txt'
                            refused=run(clone,'capture','--id','proof','--step','relocated-producer','--attempt','1','--candidate','.agent/evidence/proof/candidate.json','--output-dir','.agent/evidence/proof','--',sys.executable,'-c',f'from pathlib import Path;Path({str(marker)!r}).write_text("unexpected")')
                            expect(refused,1,'execution root must match');assert not marker.exists()
                            if layout=='installed':
                                (clone/'schema').mkdir();(clone/'schema/qa_verdict.schema.json').write_text('{}')
                                malformed=dict(verdict,checks=[])
                                try:clone_api.validate_qa_proof(clone,malformed,feature_id='proof',candidate=policy['candidate'],required_checks=[check])
                                except clone_api.AssuranceError as exc:assert 'schema' in str(exc),str(exc)
                                else:raise AssertionError('unassessed shadow schema replaced installed schema')
                        wa.verify_stage_receipt(root,receipt,policy=policy)
                        original=(root/'.agent/qa/proof.json').read_bytes()
                        qa_capture_path = root / verdict['checks'][0]['capture']['path']
                        original_capture = qa_capture_path.read_bytes()
                        def alter_capture(value, change):
                            capture = json.loads(original_capture);change(capture)
                            qa_capture_path.write_bytes(wa.canonical(capture))
                            value['checks'][0]['capture']['sha256'] = hashlib.sha256(qa_capture_path.read_bytes()).hexdigest()
                        changes=[('failed-summary',lambda v:v.update(qa_pass=False)),('missing',lambda v:v.update(checks=[])),('arbitrary-digest',lambda v:(v.pop('candidate_ref'),v.update(candidate_sha256='a'*64))),
                            ('wrong-command',lambda v:alter_capture(v,lambda c:c.update(argv=['false']))),
                            ('wrong-candidate',lambda v:alter_capture(v,lambda c:c.update(candidate_sha256='a'*64))),
                            ('wrong-cwd',lambda v:alter_capture(v,lambda c:c.update(cwd='/unrelated/producer'))),
                            ('adversarial-not-performed',lambda v:v.update(adversarial={'performed':False})),
                            ('missing-stream',lambda v:alter_capture(v,lambda c:c['stdout'].update(path='.agent/evidence/proof/missing.stdout'))),
                            ('tampered-stream',lambda v:alter_capture(v,lambda c:c['stderr'].update(sha256='a'*64)))]
                        if mode=='success':changes.append(('failed-capture',lambda v:alter_capture(v,lambda c:c.update(exit_code=7,outcome='failed'))))
                        else:changes.append(('ordinary-producer',lambda v:alter_capture(v,lambda c:c.update(proof_kind='success'))))
                        for label,change in changes:
                            bad=json.loads(original);change(bad);write(root,'.agent/qa/proof.json',bad)
                            expect(run(root,'done','bugfix','--id','proof'),1,'')
                            _git(root,'add','.agent/qa/proof.json');_git(root,'commit','--only','-qm','contradictory QA fixture '+label,'--','.agent/qa/proof.json')
                            revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
                            bad_policy=json.loads(json.dumps(policy));bad_receipt=json.loads(json.dumps(receipt))
                            reference=dict(path='.agent/qa/proof.json',sha256=hashlib.sha256((root/'.agent/qa/proof.json').read_bytes()).hexdigest(),revision=revision)
                            bad_policy['prerequisites'][1]['artifact']=reference;bad_receipt['prerequisites']=bad_policy['prerequisites']
                            try:wa.verify_stage_receipt(root,bad_receipt,policy=bad_policy)
                            except wa.AssuranceError:pass
                            else:raise AssertionError('route accepted '+label)
                            (root/'.agent/qa/proof.json').write_bytes(original)
                            qa_capture_path.write_bytes(original_capture)
                        # Consumer-time mutation after successful producer observation cannot disappear behind its manifest.
                        if inherited=='symlink':target.unlink();target.symlink_to('README.md')
                        else:target.write_text('mutated after capture\n')
                        expect(run(root,'done','bugfix','--id','proof'),1,'undeclared changes')
                        try:wa.verify_stage_receipt(root,receipt,policy=policy)
                        except wa.AssuranceError:pass
                        else:raise AssertionError('route receipt ignored inherited mutation')
        print('r02 structured proof: real direct/route success, negative, wrapper, empty streams, both layouts, inherited preservation and mutation refusal')
    finally:
        os.environ.clear();os.environ.update(old_env)


def test_r02_context_and_material() -> None:
    """Identical commands in one candidate still have different task authority."""
    old_env=dict(os.environ)
    try:
        with tempfile.TemporaryDirectory(prefix='r02-context-') as name:
            root=Path(name);proof_bootstrap(root)
            (root/'README.md').write_text('initial\n');_git(root,'add','README.md');_git(root,'commit','-qm','initial source')
            a_outputs=['.agent/evidence/task-a/'+f for f in ('candidate.json','ordinary.stdout','ordinary.stderr','ordinary.capture.json')]+['.agent/qa/task-a.json']
            for task,files in [('task-a',['README.md','.agent/evidence/task-b-base.json']),('task-b',['README.md','.agent/evidence/task-a-base.json']+a_outputs)]:
                write(root,f'.agent/evidence/{task}-cause.json',cause(task));write(root,f'.agent/evidence/{task}-scope.json',scope(task,files))
            _git(root,'add','.agent');_git(root,'commit','-qm','two independent authorized task policies')
            expect(run(root,'begin','bugfix','--id','task-a'),0,'implementation may begin')
            _git(root,'add','.agent/evidence/task-a-base.json');_git(root,'commit','-qm','first task observation')
            expect(run(root,'begin','bugfix','--id','task-b'),0,'implementation may begin')
            _git(root,'add','.agent/evidence/task-b-base.json');_git(root,'commit','-qm','second task observation')
            (root/'README.md').write_text('permitted edit shared by both tasks\n')
            extra=[f'.agent/evidence/task-b-{suffix}.json' for suffix in ('base','scope','cause')]
            verdict=record_proof(root,'task-a',extra)
            expect(run(root,'done','bugfix','--id','task-a'),0,'recorded verification result exists')
            reused={**verdict,'feature_id':'task-b'};write(root,'.agent/qa/task-b.json',reused)
            expect(run(root,'done','bugfix','--id','task-b'),1,'context environment mismatch')
            wa,policy,receipt=route_receipt(root,'task-b',reused)
            try:wa.verify_stage_receipt(root,receipt,policy=policy)
            except wa.AssuranceError as exc:assert 'context environment mismatch' in str(exc),str(exc)
            else:raise AssertionError('same candidate/command accepted wrong task context')
        for material in ('current','index'):
            with tempfile.TemporaryDirectory(prefix='r02-selected-') as name:
                root=Path(name);proof_bootstrap(root)
                write(root,'.agent/evidence/material-cause.json',cause('material'));write(root,'.agent/evidence/material-scope.json',scope('material',['README.md']))
                (root/'.r02-source.txt').write_text('inherited selected dependency drift\n')
                if material=='index':
                    _git(root,'add','.r02-source.txt');(root/'.r02-source.txt').write_text('selected ordinary input\n')
                expect(run(root,'begin','bugfix','--id','material'),0,'implementation may begin')
                try:record_proof(root,'material')
                except ValueError as exc:assert 'selected' in str(exc),str(exc)
                else:raise AssertionError('selected inherited dependency was exempted')
        print('r02 context/material: same-candidate cross-task capture reuse and inherited selected dependency drift refused')
    finally:
        os.environ.clear();os.environ.update(old_env)


def test_r02_loop_prevention() -> None:
    """Bounded retries cannot reset failure history or rerun identical assessed QA."""
    failures = []
    with tempfile.TemporaryDirectory(prefix='r02-loop-budget-') as tmp:
        root = Path(tmp); evidence = root / '.agent/evidence'; evidence.mkdir(parents=True)
        cmd = [sys.executable, '-c', 'raise SystemExit(7)']
        def capture(step, attempt=1, *extra):
            return run_raw('capture', '--id', 'loop', '--step', step, '--attempt', str(attempt),
                '--repair-summary', 'new narrative each time', '--output-dir', str(evidence / step),
                '--root', str(root), *extra, '--', *cmd)
        for step in ('one', 'two', 'three'):
            result = capture(step, 1, '--defect-signature', 'same-defect')
            expect(result, 1, '"outcome": "failed"')
        write(root, '.agent/contracts/loop.json', {**contract('approved', ['README.md']), 'amendments': ['old amendment']})
        result = capture('four', 1, '--defect-signature', 'same-defect', '--decomposition-of', 'one')
        if result.returncode != 2: failures.append('taskwide signature bypass')
        # Only exact task-scoped finite operator recovery can reopen the budget.
        previous = sorted(evidence.rglob('*.capture.json'))[-1].relative_to(root).as_posix()
        recovery = {'task_id': 'loop', 'approved': True, 'max_task_attempts': 4,
                    'after_capture': previous, 'authority_ref': '.agent/evidence/operator.json'}
        write(root, '.agent/evidence/operator.json', {'role': 'operator', **recovery})
        write(root, '.agent/run_state.json', {'circuit_breaker': {'loop': {'operator_recovery': recovery}}})
        if result.returncode == 2:
            expect(capture('recovery', 1, '--defect-signature', 'same-defect'), 1, '"outcome": "failed"')
            expect(capture('expired', 1, '--defect-signature', 'same-defect'), 2, 'finite')
    with tempfile.TemporaryDirectory(prefix='r02-loop-rotating-') as tmp:
        root = Path(tmp)
        for index in range(6):
            result = run_raw('capture', '--id', 'rotating', '--step', 'step' + str(index), '--attempt', '1', '--defect-signature', 'different' + str(index), '--output-dir', str(root / '.agent/evidence' / str(index)), '--root', str(root), '--', sys.executable, '-c', 'raise SystemExit(7)')
            expect(result, 1, '"outcome": "failed"')
        result = run_raw('capture', '--id', 'rotating', '--step', 'seventh', '--attempt', '1', '--output-dir', str(root / '.agent/evidence/seventh'), '--root', str(root), '--', sys.executable, '-c', 'pass')
        if result.returncode != 2 or 'budget' not in result.stderr: failures.append('rotating-signature ceiling bypass')
    with tempfile.TemporaryDirectory(prefix='r02-loop-cap-') as tmp:
        root = Path(tmp)
        write(root, '.agent/run_state.json', {'circuit_breaker': {'finite': {'limit': 1}}})
        write(root, '.agent/contracts/finite.json', {**contract('approved', ['README.md']), 'amendments': ['old']})
        result = run_raw('capture', '--id', 'finite', '--step', 'check', '--attempt', '2', '--continuation-basis', 'bounded-amendment', '--output-dir', str(root / '.agent/evidence'), '--root', str(root), '--', sys.executable, '-c', 'pass')
        expect(result, 2, 'finite configured step limit')
        write(root, '.agent/run_state.json', {'circuit_breaker': {'finite': {'operator_recovery': {'task_id': 'finite', 'approved': True, 'max_task_attempts': True, 'after_capture': 'missing', 'authority_ref': 'missing'}}}})
        result = run_raw('capture', '--id', 'finite', '--step', 'other', '--attempt', '1', '--output-dir', str(root / '.agent/evidence'), '--root', str(root), '--', sys.executable, '-c', 'pass')
        expect(result, 2, 'finite task operator recovery')
    with tempfile.TemporaryDirectory(prefix='r02-loop-corrupt-') as tmp:
        root = Path(tmp); (root / '.agent/evidence').mkdir(parents=True)
        (root / '.agent/evidence/corrupt-check-attempt1-bad.capture.json').write_text('{')
        result = run_raw('capture', '--id', 'corrupt', '--step', 'other', '--attempt', '1', '--output-dir', str(root / '.agent/evidence'), '--root', str(root), '--', sys.executable, '-c', 'pass')
        expect(result, 2, 'corrupt task capture history')
    for parent in ('nonexistent', 'self'):
        with tempfile.TemporaryDirectory(prefix='r02-loop-parent-') as tmp:
            root = Path(tmp)
            result = run_raw('capture', '--id', 'parent', '--step', 'self', '--attempt', '4',
                '--decomposition-of', parent, '--output-dir', str(root / '.agent/evidence'), '--root', str(root), '--', sys.executable, '-c', 'pass')
            if result.returncode != 2: failures.append(parent + ' decomposition accepted')
    with tempfile.TemporaryDirectory(prefix='r02-loop-amend-') as tmp:
        root = Path(tmp); write(root, '.agent/contracts/c1.json', contract('approved', ['README.md']))
        amendment = root / 'amendment.json'
        write(root, 'amendment.json', {'contract_id': 'c1', 'summary': 'metadata-only retry credit', 'invariants_preserved': True})
        result = run_raw('amend-contract', '--contract', 'c1', '--amendment', str(amendment), '--root', str(root))
        if result.returncode != 1: failures.append('no-op amendment accepted')
    with tempfile.TemporaryDirectory(prefix='r02-loop-proof-') as tmp:
        root = Path(tmp); task = 'proof'
        write(root, '.agent/evidence/proof-intent.json', {'id': task, 'path': 'trivial', 'summary': 'bounded proof', 'needs_new_contract': False, 'files': ['README.md']})
        (root / 'README.md').write_text('task\n')
        expect(run(root, 'begin', 'trivial', '--id', task), 0, 'implementation may begin')
        qa = record_proof(root, task)
        manifest = root / qa['candidate_ref']['path']
        args = ['capture', '--id', task, '--step', 'duplicate', '--attempt', '2', '--candidate', str(manifest),
                '--output-dir', str(root / '.agent/evidence/proof'), '--root', str(root), '--', *CHECK['argv']]
        result = subprocess.run([sys.executable, str(root / "tools/start_path.py"), *args], text=True, capture_output=True)
        if result.returncode != 2 or 'reuse' not in result.stderr: failures.append('identical successful proof rerun accepted')
        (root / '.r02-source.txt').write_text('stale material input\n')
        args[args.index('duplicate')] = 'stale'
        result = subprocess.run([sys.executable, str(root / "tools/start_path.py"), *args], text=True, capture_output=True)
        if result.returncode != 2 or 'before execution' not in result.stderr: failures.append('stale assessed input dispatched')
    with tempfile.TemporaryDirectory(prefix='r02-loop-negative-') as tmp:
        root = Path(tmp); task = 'negative'
        check = dict(CHECK, id='refusal', argv=[sys.executable, '-c', "print('EXPECTED_REFUSAL');raise SystemExit(7)"], expected_exit=7, proof_kind='semantic-negative', diagnostic='EXPECTED_REFUSAL')
        write(root, '.agent/evidence/negative-intent.json', {'id': task, 'path': 'small-change', 'summary': 'pinned negative proof', 'needs_new_contract': False, 'files': ['README.md', '.r02-source.txt'], 'verification': [check]})
        (root / 'README.md').write_text('task\n')
        expect(run(root, 'begin', 'small-change', '--id', task), 0, 'implementation may begin')
        qa = record_proof(root, task)
        # Existing independently pinned negative proof is success for reuse too.
        args = ['capture', '--id', task, '--step', 'repeat', '--attempt', '2', '--proof-kind', 'semantic-negative', '--candidate', str(root / qa['candidate_ref']['path']), '--output-dir', str(root / '.agent/evidence/negative'), '--root', str(root), '--', *check['argv']]
        result = subprocess.run([sys.executable, str(root / 'tools/start_path.py'), *args], text=True, capture_output=True)
        expect(result, 2, 'reuse')
        # Dispatch a distinct diagnostic under the same assessed candidate: it is
        # permitted, but an unpinned semantic-negative label grants no success.
        args[args.index('repeat')] = 'diagnostic'
        args[args.index('--') + 1:] = [sys.executable, '-c', "print('UNPINNED');raise SystemExit(7)"]
        result = subprocess.run([sys.executable, str(root / 'tools/start_path.py'), *args], text=True, capture_output=True)
        expect(result, 1, '"outcome": "failed"')
        captured = json.loads(result.stdout)
        assert 'qa_expected_predicate' not in captured['continuation_lineage']
        (root / '.r02-source.txt').write_text('next assessed candidate\n')
        _git(root, 'add', '.r02-source.txt'); _git(root, 'commit', '-qm', 'new bounded candidate')
        spec = importlib.util.spec_from_file_location('loop_negative_wa', root / 'tools/workflow_assurance.py')
        wa = importlib.util.module_from_spec(spec); spec.loader.exec_module(wa)
        old_candidate = json.loads((root / qa['candidate_ref']['path']).read_text())
        inputs = {key: [entry['path'] for entry in entries] for key, entries in old_candidate['assessed_inputs'].items()}
        inputs['unknown_dependencies'] = []
        next_candidate = wa.assess_route_candidate(root, task, subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(), inputs, list(old_candidate['environment']['variables']))
        manifest = root / '.agent/evidence/negative/next-candidate.json'; manifest.write_bytes(wa.canonical(next_candidate))
        args[args.index('diagnostic')] = 'qualified'
        args[args.index('--candidate') + 1] = str(manifest)
        args[args.index('--attempt') + 1] = '1'
        args[args.index('--') + 1:] = check['argv']
        result = subprocess.run([sys.executable, str(root / 'tools/start_path.py'), *args], text=True, capture_output=True)
        expect(result, 1, '"outcome": "failed"')
        qualified = json.loads(result.stdout)
        assert qualified['continuation_lineage']['qa_expected_predicate']['check'] == check
        args[args.index('--attempt') + 1] = '2'
        result = subprocess.run([sys.executable, str(root / 'tools/start_path.py'), *args], text=True, capture_output=True)
        expect(result, 2, 'reuse')
    assert not failures, '\n'.join(failures)
    print('PASS r02 finite taskwide loop prevention, decomposition, no-op and proof reuse controls')


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
        record_proof(root, "demo")
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
        record_proof(root, "tiny")
        small_done = run(root, "done", "small-change", "--id", "tiny")
        expect(small_done, 0, "recorded verification result exists")

        escaped = run(root, "begin", "bugfix", "--id", "../demo")
        expect(escaped, 2, "safe path token")

        test_r5_classification_and_amendments(root)
        test_a1_f1_f5_scope_completion_and_amendments(root)
        test_r6_r7_r8_preflight_capture_status_and_resume(root)

    test_r02_completion()
    test_r02_structured_proof()
    test_r02_context_and_material()
    test_r02_loop_prevention()
    test_jev_readiness_controls()
    test_jev_readiness_attempts()
    test_jev_readiness_authority()
    print("start-path: bugfix, small-change, trivial, classify, amend-contract, preflight, capture, publish, build-receipt, and status gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

