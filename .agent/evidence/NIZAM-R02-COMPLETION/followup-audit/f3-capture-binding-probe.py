"""Read-only diagnostic, OUTSIDE F1/F2 implementation scope; not acceptance/QA.

This preserves the independently executed initial F3 reproduction. The capture
JSON is deliberately a synthetic contradictory input, not an official capture
or a claim that its named child process ran. A real temporary Git repository is
used. Only the unmodified upstream load_passing_qa validator is exercised.
"""
import copy
import json
import runpy
import subprocess
import tempfile
from pathlib import Path

api = runpy.run_path("tools/start_path.py", run_name="readonly_evaluator_probe")
with tempfile.TemporaryDirectory(prefix="nizam-r02-qa-readonly-") as temp:
    root = Path(temp)

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, text=True,
            capture_output=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "diagnostic@example.invalid")
    git("config", "user.name", "Read-only Diagnostic")
    (root / "source.txt").write_text("baseline\n")
    git("add", "source.txt")
    git("commit", "-qm", "disposable baseline")
    head = git("rev-parse", "HEAD")
    (root / ".agent/qa").mkdir(parents=True)
    (root / ".agent/evidence").mkdir()
    relative = ".agent/evidence/actual.capture.json"
    # Ordinary unsuccessful command metadata, not expected-negative semantics.
    (root / relative).write_text(json.dumps({
        "executed": True, "exit_code": 7, "outcome": "failed",
        "candidate_sha256": "a" * 64, "argv": ["ordinary-test-command"],
    }))
    base = {
        "feature_id": "probe", "qa_pass": True, "checks_run": 1,
        "checks_passed": 1, "adversarial": {"performed": True},
        "evidence_files": [relative], "issues": [],
        "unsupported_claims": [], "missing_acceptance_coverage": [],
        "required_fixes": [],
        "final_verdict": {
            "approved": True,
            "summary": "Synthetic diagnostic verdict; not QA approval",
        },
        "checks": [{
            "command": "ordinary-test-command", "executed": True,
            "exit_code": 0, "evidence": relative,
        }],
    }
    cases = [
        ("ordinary_failed_capture_with_current_head", dict(base, candidate=head)),
        ("ordinary_failed_capture_with_unchecked_sha256", dict(base, candidate_sha256="f" * 64)),
        ("stale_40hex_candidate_control", dict(base, candidate="f" * 40)),
    ]
    bad = copy.deepcopy(base)
    bad["checks"][0]["exit_code"] = 7
    cases.append(("declared_failed_check_control", bad))
    results = []
    for label, verdict in cases:
        (root / ".agent/qa/probe.json").write_text(json.dumps(verdict))
        try:
            api["load_passing_qa"](root, "probe")
            result = {"case": label, "accepted": True}
        except api["StartPathError"] as exc:
            result = {
                "case": label, "accepted": False, "exit_code": exc.exit_code,
                "diagnostic": str(exc),
            }
        results.append(result)
    print(json.dumps({
        "kind": "read-only diagnostic against unmodified source; disposable Git repository only",
        "scope": "OUTSIDE F1/F2 implementation scope; not acceptance or passing QA",
        "capture_fixture": "synthetic contradictory metadata, not an official executed capture",
        "source_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
        ).stdout.strip(),
        "results": results,
    }, indent=2))
