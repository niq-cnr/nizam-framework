#!/usr/bin/env python3
"""Regression tests for framework-integrity findings SQA-integrity-003 and -004
(audit c905615d; findings sha256 82d4df0b34fc4235...). Standard library only; writes only
mktemp fixtures. Run:

  PYTHONDONTWRITEBYTECODE=1 python3 tools/test_framework_integrity_s003004.py

Each negative case here fails against the pre-fix tree (fe1d158d) and passes after.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
BASELINE_CATEGORIES = (
    "framework_references",
    "repository_references",
    "dependency_references",
    "ci_references",
    "planning_references",
    "evidence_references",
)


def full_baseline(execution_id: str = "e1") -> dict:
    doc: dict = {"execution_id": execution_id, "captured_at": "t"}
    for category in BASELINE_CATEGORIES:
        doc[category] = [{"revision": "abc123", "timestamp": "t"}]
    return doc


FINDINGS = [
    {
        "id": "F1",
        "severity": "low",
        "confidence": "Confirmed",
        "evidence": [{"path": ".agent/evidence/e1/x.txt", "revision": "abc123"}],
        "impact": "i",
        "owner": "o",
        "status": "open",
        "closure_criteria": "c",
    }
]


class AuditEntryGate(unittest.TestCase):
    """SQA-integrity-004: the audit CLI refuses an invalid baseline or contradictory preflight."""

    def setUp(self) -> None:
        self.d = Path(tempfile.mkdtemp(prefix="s004-audit-"))
        (self.d / "findings.json").write_text(json.dumps(FINDINGS))
        (self.d / "baseline.json").write_text(json.dumps(full_baseline()))

    def tearDown(self) -> None:
        shutil.rmtree(self.d, ignore_errors=True)

    def run_audit(self, preflight: dict | str, baseline: dict | str | None = None) -> tuple[int, Path]:
        pf = self.d / "preflight.json"
        pf.write_text(preflight if isinstance(preflight, str) else json.dumps(preflight))
        bl = self.d / "bl.json"
        if baseline is None:
            bl = self.d / "baseline.json"
        else:
            bl.write_text(baseline if isinstance(baseline, str) else json.dumps(baseline))
        out = self.d / "out"
        r = subprocess.run(
            ["python3", str(TOOLS / "ecosystem_audit.py"), "--audit-id", "a",
             "--output-dir", str(out), "--findings-input", str(self.d / "findings.json"),
             "--preflight", str(pf), "--baseline", str(bl)],
            capture_output=True, text=True, env=ENV,
        )
        return r.returncode, out

    def clean_preflight(self, **extra) -> dict:
        doc = {"verdict": "PASS", "execution_id": "e1", "generated_at": "t"}
        doc.update(extra)
        return doc

    def test_positive_full_baseline_and_clean_preflight_is_assembled(self) -> None:
        rc, out = self.run_audit(self.clean_preflight())
        self.assertEqual(rc, 0)
        self.assertTrue((out / "findings.json").is_file())

    def test_minimal_baseline_execution_id_only_is_refused(self) -> None:
        rc, out = self.run_audit(self.clean_preflight(), {"execution_id": "e1"})
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_each_missing_mandatory_baseline_category_is_refused(self) -> None:
        for category in BASELINE_CATEGORIES:
            with self.subTest(category=category):
                doc = full_baseline()
                del doc[category]
                rc, out = self.run_audit(self.clean_preflight(), doc)
                self.assertEqual(rc, 2)
                self.assertFalse(out.exists())

    def test_baseline_item_without_revision_or_timestamp_is_refused(self) -> None:
        doc = full_baseline()
        doc["ci_references"] = [{"timestamp": "t"}]
        rc, out = self.run_audit(self.clean_preflight(), doc)
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_pass_with_blocking_findings_is_refused(self) -> None:
        rc, out = self.run_audit(self.clean_preflight(blocking_findings=["unresolved"]))
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_missing_preflight_execution_id_is_refused(self) -> None:
        doc = {"verdict": "PASS", "generated_at": "t"}
        rc, out = self.run_audit(doc)
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_mismatched_execution_id_is_refused(self) -> None:
        rc, out = self.run_audit(self.clean_preflight(execution_id="e2"))
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_pass_with_exceptions_requires_complete_operator_approval(self) -> None:
        doc = self.clean_preflight(
            verdict="PASS_WITH_EXCEPTIONS",
            exceptions=[{"id": "x"}],
            operator_approval={"approver": "op", "authorization": "ok"},
        )
        rc, out = self.run_audit(doc)
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())

    def test_pass_with_exceptions_with_complete_approval_is_accepted(self) -> None:
        doc = self.clean_preflight(
            verdict="PASS_WITH_EXCEPTIONS",
            exceptions=[{"id": "x"}],
            operator_approval={"approver": "op", "approved_at": "t", "authorization": "ok"},
        )
        rc, _ = self.run_audit(doc)
        self.assertEqual(rc, 0)


class QaCompletionGate(unittest.TestCase):
    """SQA-integrity-003: C11 schema and C16 completion reject contradictory QA records."""

    def setUp(self) -> None:
        self.d = Path(tempfile.mkdtemp(prefix="s003-qa-"))
        for sub in ("contracts", "qa", "evidence/900"):
            (self.d / ".agent" / sub).mkdir(parents=True, exist_ok=True)
        (self.d / "schema").mkdir()
        for name in ("feature_list.schema.json", "qa_verdict.schema.json"):
            shutil.copy(REPO / "schema" / name, self.d / "schema" / name)
        (self.d / ".agent/evidence/900/proof.txt").write_text("proof\n")
        (self.d / ".agent/contracts/900.json").write_text(json.dumps({"contract_id": "900", "status": "complete"}))
        (self.d / ".agent/feature_list_900.json").write_text(json.dumps({
            "phase": "900-scratch", "spec_version": "1.0.0", "original_estimate_lines": 10,
            "features": [{"id": "900", "name": "S", "description": "S", "status": "complete",
                          "dependencies": [], "acceptance_tests": ["a"], "estimated_lines": 10,
                          "passes": True}],
        }))

    def tearDown(self) -> None:
        shutil.rmtree(self.d, ignore_errors=True)

    def qa(self, **overrides) -> None:
        doc = {
            "feature_id": "900", "qa_pass": True, "checks_run": 2, "checks_passed": 2,
            "adversarial": {"performed": True}, "evidence_files": [".agent/evidence/900/proof.txt"],
            "issues": [], "unsupported_claims": [], "missing_acceptance_coverage": [],
            "required_fixes": [], "final_verdict": {"approved": True, "summary": "s"},
        }
        doc.update(overrides)
        (self.d / ".agent/qa/900.json").write_text(json.dumps(doc))

    def schema_rc(self) -> int:
        code = ("import json,jsonschema;jsonschema.validate(instance=json.load(open('.agent/qa/900.json')),"
                "schema=json.load(open('schema/qa_verdict.schema.json')))")
        return subprocess.run(["python3", "-c", code], cwd=self.d, capture_output=True, env=ENV).returncode

    def completion_rc(self) -> int:
        cmd = f"source '{REPO}/tools/verify_lib.sh' && vlib_feature_list_lifecycle"
        return subprocess.run(["bash", "-c", cmd], cwd=self.d, capture_output=True, env=ENV).returncode

    def assert_refused(self, **overrides) -> None:
        self.qa(**overrides)
        self.assertNotEqual(self.schema_rc(), 0, f"C11 accepted {overrides}")
        self.assertNotEqual(self.completion_rc(), 0, f"C16 accepted {overrides}")

    def assert_completion_refused(self, **overrides) -> None:
        # Cross-field total agreement is not expressible in JSON Schema 2020-12, so C16
        # (the completion check) is the enforcing layer for these contradictions.
        self.qa(**overrides)
        self.assertNotEqual(self.completion_rc(), 0, f"C16 accepted {overrides}")

    def test_clean_passing_record_is_accepted_by_both(self) -> None:
        self.qa()
        self.assertEqual(self.schema_rc(), 0)
        self.assertEqual(self.completion_rc(), 0)

    def test_rejected_but_approved_record_is_refused(self) -> None:
        # The audit's exact contradiction: qa_pass=false yet final_verdict.approved=true.
        self.assert_refused(qa_pass=False, checks_run=2, checks_passed=0,
                            issues=["blocking defect"], required_fixes=["fix"])

    def test_nonempty_issues_on_passing_record_are_refused(self) -> None:
        self.assert_refused(issues=["unresolved defect"])

    def test_nonempty_unsupported_claims_on_passing_record_are_refused(self) -> None:
        self.assert_refused(unsupported_claims=["claimed but unproven"])

    def test_nonempty_missing_coverage_on_passing_record_is_refused(self) -> None:
        self.assert_refused(missing_acceptance_coverage=["AC-2 not covered"])

    def test_nonempty_required_fixes_on_passing_record_is_refused(self) -> None:
        self.assert_refused(required_fixes=["fix x"])

    def test_check_totals_mismatch_on_passing_record_is_refused(self) -> None:
        self.assert_completion_refused(checks_run=2, checks_passed=1)

    def test_check_passed_exceeding_run_is_refused(self) -> None:
        self.assert_completion_refused(checks_run=2, checks_passed=3)

    def test_pass_without_approval_is_refused(self) -> None:
        self.assert_refused(final_verdict={"approved": False, "summary": "s"})

    def test_fully_passing_check_total_on_rejected_record_is_refused(self) -> None:
        self.assert_completion_refused(qa_pass=False, checks_run=2, checks_passed=2,
                            final_verdict={"approved": False, "summary": "s"},
                            issues=["x"])


if __name__ == "__main__":
    unittest.main()
