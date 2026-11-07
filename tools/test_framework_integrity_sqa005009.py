#!/usr/bin/env python3
"""Regression tests for framework-integrity findings SQA-integrity-005, -006, -007, -008,
-009 and -011 (audit c905615d; findings sha256 82d4df0b34fc4235...). Standard library only;
writes only mktemp fixtures. Run:

  PYTHONDONTWRITEBYTECODE=1 python3 tools/test_framework_integrity_sqa005009.py

Negative cases here fail against the pre-fix tree (0a0a4d24) and pass after this change.
The accounting (008) and preregistration (009) cases import their module directly; the
preflight (007) and C8 (006) cases run the real CLI or the real check function.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

import evaluation_harness as eh  # noqa: E402
import test_evaluation as te  # noqa: E402
import test_suite_coverage as cov  # noqa: E402
import usage_accounting as ua  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.email=t@example.invalid", "-c", "user.name=tester", *args],
        check=True, capture_output=True, text=True,
    ).stdout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CiReachability(unittest.TestCase):
    """SQA-integrity-005: every dedicated suite is run by CI or excluded with a reason."""

    def test_checker_passes_on_the_checked_in_manifest(self) -> None:
        self.assertEqual(cov.check(), [], "every tools/test_*.py must be listed or excluded")

    def test_unlisted_suite_is_refused(self) -> None:
        # A suite added with no CI invocation must be reported, not silently tolerated.
        d = Path(tempfile.mkdtemp(prefix="s005-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(TOOLS, d / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        (d / "tools" / "test_unwired_new_suite.py").write_text("import unittest\n")
        saved = cov.ROOT, cov.TOOLS, cov.LISTED, cov.EXCLUDED
        try:
            cov.ROOT, cov.TOOLS = d, d / "tools"
            cov.LISTED, cov.EXCLUDED = d / "tools/ci_suites.txt", d / "tools/ci_suite_exclusions.txt"
            problems = cov.check()
        finally:
            cov.ROOT, cov.TOOLS, cov.LISTED, cov.EXCLUDED = saved
        self.assertTrue(any("test_unwired_new_suite.py" in p for p in problems), problems)

    def test_exclusion_without_reason_is_refused(self) -> None:
        d = Path(tempfile.mkdtemp(prefix="s005-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        f = d / "ex.txt"
        f.write_text("tools/test_x.py|\n")
        saved = cov.EXCLUDED
        try:
            cov.EXCLUDED = f
            with self.assertRaises(ValueError):
                cov.load_excluded()
        finally:
            cov.EXCLUDED = saved

    def test_suite_both_run_and_excluded_is_refused(self) -> None:
        d = Path(tempfile.mkdtemp(prefix="s005-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "tools").mkdir()
        (d / "tools" / "test_x.py").write_text("")
        (d / "tools" / "ci_suites.txt").write_text("tools/test_x.py\n")
        (d / "tools" / "ci_suite_exclusions.txt").write_text("tools/test_x.py|reason\n")
        saved = cov.ROOT, cov.TOOLS, cov.LISTED, cov.EXCLUDED
        try:
            cov.ROOT, cov.TOOLS = d, d / "tools"
            cov.LISTED, cov.EXCLUDED = d / "tools/ci_suites.txt", d / "tools/ci_suite_exclusions.txt"
            problems = cov.check()
        finally:
            cov.ROOT, cov.TOOLS, cov.LISTED, cov.EXCLUDED = saved
        self.assertTrue(any("both run by CI and excluded" in p for p in problems), problems)

    def test_workflow_runs_the_manifest_loop(self) -> None:
        wf = (REPO / ".github/workflows/compliance.yml").read_text(encoding="utf-8")
        self.assertIn("tools/ci_suites.txt", wf)
        self.assertIn("tools/test_suite_coverage.py", wf)


class C8CommittedBump(unittest.TestCase):
    """SQA-integrity-006: C8 with an explicit comparison base sees a committed bump."""

    @classmethod
    def setUpClass(cls) -> None:
        text = (TOOLS / "validate.sh").read_text(encoding="utf-8")
        start = text.index("check_c8_version_changelog() {")
        # The function's closing brace is the first column-0 "}" after its final "  return 1".
        final_return = text.index("\n  return 1\n}\n", start) + len("\n  return 1\n")
        end = text.index("\n}\n", final_return) + len("\n}\n")
        cls.fn_text = text[start:end]

    def _c8(self, repo: Path, base: str | None, doc: str) -> subprocess.CompletedProcess:
        fn = repo.parent / (repo.name + "-c8.sh")
        fn.write_text(self.fn_text)
        self.addCleanup(lambda: fn.unlink(missing_ok=True))
        env = {**ENV}
        if base is None:
            env.pop("NIZAM_C8_BASE", None)
        else:
            env["NIZAM_C8_BASE"] = base
        return subprocess.run(
            ["bash", "-c", f"source '{fn}'; check_c8_version_changelog '{doc}'"],
            cwd=repo, env=env, capture_output=True, text=True,
        )

    def _two_revision_repo(self, bump_to: str, with_change_record: bool) -> Path:
        repo = Path(tempfile.mkdtemp(prefix="s006-"))
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        _git(repo, "init", "-q")
        (repo / "docs").mkdir()
        head = (
            '---\nid: x\ntitle: "x"\ndescription: "x"\nversion: 0.1.0\nstatus: active\n'
            'change_log:\n  - version: "0.1.0"\n    date: "2026-01-01"\n    summary: "init"\n---\n# X\n'
        )
        (repo / "docs" / "x.md").write_text(head)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "base")
        entry = ""
        if with_change_record:
            entry = (
                f'  - version: "{bump_to}"\n    date: "2026-02-01"\n    summary: "bump"\n'
            )
        bumped = head.replace("version: 0.1.0", f"version: {bump_to}").replace(
            "change_log:\n", "change_log:\n" + entry
        )
        (repo / "docs" / "x.md").write_text(bumped)
        _git(repo, "commit", "-qam", "committed bump")
        return repo

    def test_committed_bump_without_change_record_is_refused_with_explicit_base(self) -> None:
        repo = self._two_revision_repo("0.2.0", with_change_record=False)
        result = self._c8(repo, "HEAD~1", "docs/x.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("version bumped 0.1.0 -> 0.2.0", result.stdout)

    def test_committed_bump_with_change_record_is_accepted_with_explicit_base(self) -> None:
        repo = self._two_revision_repo("0.2.0", with_change_record=True)
        result = self._c8(repo, "HEAD~1", "docs/x.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[C8] PASS", result.stdout)

    def test_unresolvable_base_fails_closed(self) -> None:
        repo = self._two_revision_repo("0.2.0", with_change_record=True)
        result = self._c8(repo, "0000000000000000000000000000000000000000", "docs/x.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("is not a commit in this checkout", result.stdout)

    def test_local_default_still_detects_uncommitted_bump(self) -> None:
        repo = self._two_revision_repo("0.2.0", with_change_record=True)
        (repo / "docs" / "x.md").write_text(
            (repo / "docs" / "x.md").read_text().replace("version: 0.2.0", "version: 0.3.0")
        )
        result = self._c8(repo, None, "docs/x.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("0.2.0 -> 0.3.0", result.stdout)


class PreflightBaselineImmutable(unittest.TestCase):
    """SQA-integrity-007: a completed baseline is never deleted or replaced by a rerun."""

    def setUp(self) -> None:
        self.work = Path(tempfile.mkdtemp(prefix="s007-"))
        self.addCleanup(shutil.rmtree, self.work, ignore_errors=True)
        self.repo = self.work / "repo"
        self.repo.mkdir()
        shutil.copytree(REPO / "schema", self.repo / "schema")
        _git(self.repo, "init", "-q")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "init")
        self.out = self.work / "out"

    def _preflight(self, execution_id: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOLS / "ecosystem_preflight.py"), "--execution-id", execution_id,
             "--output-dir", str(self.out), "--repo-root", str(self.repo), "--self-fixture"],
            capture_output=True, text=True, env=ENV,
        )

    def test_passing_rerun_does_not_replace_baseline(self) -> None:
        first = self._preflight("E1")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        digest = _sha256(self.out / "baseline.json")
        second = self._preflight("E2")
        self.assertEqual(second.returncode, 64, "rerun into a completed baseline must be refused")
        self.assertEqual(_sha256(self.out / "baseline.json"), digest)
        self.assertIn('"execution_id": "E1"', (self.out / "baseline.json").read_text())

    def test_failing_rerun_does_not_delete_baseline(self) -> None:
        self.assertEqual(self._preflight("E1").returncode, 0)
        digest = _sha256(self.out / "baseline.json")
        (self.repo / "dirty.txt").write_text("x")
        second = self._preflight("E3")
        self.assertNotEqual(second.returncode, 0)
        self.assertTrue((self.out / "baseline.json").is_file(), "failing rerun deleted the baseline")
        self.assertEqual(_sha256(self.out / "baseline.json"), digest)

    def test_fresh_namespace_still_produces_a_baseline(self) -> None:
        self.assertEqual(self._preflight("E1").returncode, 0)
        fresh = self.work / "fresh"
        result = subprocess.run(
            [sys.executable, str(TOOLS / "ecosystem_preflight.py"), "--execution-id", "E2",
             "--output-dir", str(fresh), "--repo-root", str(self.repo), "--self-fixture"],
            capture_output=True, text=True, env=ENV,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((fresh / "baseline.json").is_file())


class UsageUniqueProviderUsage(unittest.TestCase):
    """SQA-integrity-008: usage totals count one operation's usage once."""

    def _event(self, **overrides):
        event = {
            "schema_version": 1, "event_id": "e-1", "kind": "completion", "operation_id": "op-1",
            "dispatched": True, "outcome": "success",
            "model": {"requested": "jev-1", "resolved": "jev-1", "provider": "typesafe"},
            "usage": {"input_tokens": 120, "output_tokens": 30, "cache_tokens": None},
        }
        event.update(overrides)
        return event

    def test_pre_post_pair_totals_are_not_doubled(self) -> None:
        pre = self._event(kind="pre_dispatch", event_id="p", outcome=None)
        total = ua.usage_totals([pre, self._event()])
        self.assertEqual(total["known"]["input_tokens"], 120)
        self.assertEqual(total["known"]["output_tokens"], 30)
        self.assertEqual(total["charged_requests"], 1)

    def test_completion_resolves_pre_dispatch_absent_fields(self) -> None:
        pre = self._event(kind="pre_dispatch", event_id="p", outcome=None, usage=None)
        total = ua.usage_totals([pre, self._event()])
        self.assertNotIn("input_tokens", total["unknown"])
        self.assertIn("cache_tokens", total["unknown"], "genuinely unreported usage stays unknown")

    def test_distinct_operations_sum_and_unreported_stays_unknown(self) -> None:
        a = self._event(operation_id="op-a")
        b = self._event(operation_id="op-b", event_id="b", usage={"input_tokens": 5, "output_tokens": None})
        total = ua.usage_totals([a, b])
        self.assertEqual(total["known"]["input_tokens"], 125)
        self.assertEqual(total["known"]["output_tokens"], 30)
        self.assertIn("output_tokens", total["unknown"])
        self.assertEqual(total["charged_requests"], 2)


class PreregistrationCompleteness(unittest.TestCase):
    """SQA-integrity-009: every declared design field is required, or explicitly not applicable."""

    def test_each_newly_required_field_refuses_when_unset(self) -> None:
        for field in te.NEWLY_REQUIRED:
            doc = te._complete_preregistration()
            doc[field] = None
            with self.subTest(field=field), self.assertRaises(eh.HarnessError):
                eh.validate_preregistration(doc)

    def test_template_fields_are_all_required_or_declared(self) -> None:
        template = eh.preregistration_template()
        unrequired = [
            k for k in template
            if k not in eh.REQUIRED_PREREGISTRATION and k not in ("schema_version", "thresholds_set_after_holdout")
        ]
        self.assertEqual(unrequired, [], "a template field must be required or declared non-design")

    def test_partial_six_field_record_refused(self) -> None:
        doc = eh.preregistration_template()
        doc.update({
            "corpus_version": "v1", "assignment": "matched", "sample_size_rationale": "power",
            "quality_criteria": "critical-miss <= 1", "coverage_abstention_criteria": ">= 90%",
            "stopping_rule": "stop at budget or 3 misses",
        })
        with self.assertRaises(eh.HarnessError):
            eh.validate_preregistration(doc)

    def test_complete_record_accepted(self) -> None:
        self.assertTrue(eh.validate_preregistration(te._complete_preregistration()))


class SelfGovernanceCurrentInstallation(unittest.TestCase):
    """SQA-integrity-011: the current-installation heading names the structured pin."""

    def test_current_heading_names_the_structured_tag(self) -> None:
        text = (REPO / "docs/planning/SELF_GOVERNANCE.md").read_text(encoding="utf-8")
        tag = re.search(r"^  tag: (\S+)$", text, re.M).group(1)
        resolved = re.search(r"^  resolved_sha: (\S+)$", text, re.M).group(1)
        heading = re.search(r"^# Current installation .*$", text, re.M).group(0)
        self.assertIn(f"`{tag}`", heading)
        self.assertNotIn("v3.0.0", heading)
        # The current section body must name the same commit as the structured record.
        section = text.split(heading, 1)[1].split("\n# ", 1)[0]
        self.assertIn(resolved, section)

    def test_superseded_release_is_labeled_historical(self) -> None:
        text = (REPO / "docs/planning/SELF_GOVERNANCE.md").read_text(encoding="utf-8")
        heading = "# Historical installation \u2014 `v3.0.0`"
        self.assertTrue(
            any(line.startswith(heading) for line in text.splitlines()),
            "the superseded v3.0.0 record must carry an explicit historical heading",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
