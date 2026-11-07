"""Adversarial tests for the evaluation corpus and four-arm harness (JR-16/JR-17)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import evaluation_corpus as ec  # noqa: E402
import evaluation_harness as eh  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except (ec.CorpusError, eh.HarnessError):
        return True
    return False


def _entry(entry_id, group="g1", label="direct", eligibility="internal"):
    return ec.CorpusEntry(
        entry_id=entry_id, family="DF-01", primitive="choice",
        lineage_group=group, label=label, adjudicator="human-a",
        eligibility=eligibility, input={"component": entry_id},
    )


def test_split_keeps_lineage_groups_together():
    # AC-16-02/16-06: variants and descendants stay in one split; no leakage
    entries = [_entry("a1", "g1"), _entry("a2", "g1"), _entry("b1", "g2")]
    calibration, holdout = ec.split_by_lineage(entries, holdout_group_ids={"g2"})
    assert {e.entry_id for e in calibration} == {"a1", "a2"}
    assert {e.entry_id for e in holdout} == {"b1"}
    ec.assert_no_lineage_leakage(calibration, holdout)


def test_split_unknown_group_rejected():
    assert _raises(ec.split_by_lineage, [_entry("a1", "g1")], holdout_group_ids={"nope"})


def test_freeze_requires_adjudication_and_unique_ids():
    # AC-16-01: immutable ids, an adjudicator and a rubric are mandatory
    corpus = ec.freeze_corpus([_entry("a1"), _entry("a2")], version="v1",
                              rubric={"direct", "support", "ext", "insufficient"}, adjudicator="human-a")
    assert corpus["frozen"] is True and corpus["entry_count"] == 2
    assert _raises(ec.freeze_corpus, [_entry("a1"), _entry("a1")], version="v1",
                   rubric={"direct"}, adjudicator="human-a")
    # an ambiguous/missing label is allowed as None (evaluated as ambiguity), never forced
    unlabeled = ec.CorpusEntry(entry_id="u1", family="DF-01", primitive="choice",
                               lineage_group="g1", label=None, adjudicator="human-a",
                               eligibility="internal", input={})
    ec.freeze_corpus([unlabeled], version="v1", rubric={"direct"}, adjudicator="human-a")


def test_arm_attribution_and_matched_inputs():
    # AC-17-01: arms are attributed and a task's inputs must match across arms
    assignments = [
        {"arm": "B", "task_id": "t1", "inputs": {"q": "same"}},
        {"arm": "C", "task_id": "t1", "inputs": {"q": "same"}},
    ]
    assert "t1" in eh.matched_inputs(assignments)
    mismatch = [
        {"arm": "B", "task_id": "t1", "inputs": {"q": "same"}},
        {"arm": "C", "task_id": "t1", "inputs": {"q": "different"}},
    ]
    assert _raises(eh.matched_inputs, mismatch)
    assert _raises(eh.validate_arm, "E")


def test_arm_d_applicability():
    # Arm D applies only to exactly-determinable questions and abstains otherwise
    assert eh.is_arm_d_applicable({"deterministic": True})
    assert eh.is_arm_d_applicable({"deterministic": False}) is False


def _complete_preregistration() -> dict:
    # Every field the template declares, fully specified (SQA-integrity-009).
    doc = eh.preregistration_template()
    doc.update({
        "corpus_version": "v1", "assignment": "matched",
        "task_clustering": "by source document", "carryover_controls": "fresh session per arm",
        "blinding": "single-blind grader", "followup_rework_window": "7 days",
        "sample_size_rationale": "power", "quality_criteria": "critical-miss <= 1",
        "noninferiority_margin": 0.05, "critical_miss_tolerance": 0,
        "coverage_abstention_criteria": ">= 90%", "latency_cost_limits": "p95 < 5s, budget cap",
        "uncertainty_method": "bootstrap 95% CI", "stopping_rule": "stop at budget or 3 misses",
    })
    return doc


def test_preregistration_required_fields():
    # AC-17 / SQA-integrity-009: every declared design field is required before evaluation
    assert _raises(eh.validate_preregistration, eh.preregistration_template())
    doc = _complete_preregistration()
    assert eh.validate_preregistration(doc)
    doc["thresholds_set_after_holdout"] = True
    assert _raises(eh.validate_preregistration, doc)


def test_preregistration_six_field_partial_record_rejected():
    # SQA-integrity-009: the six-field subset the validator used to check is no longer sufficient
    doc = eh.preregistration_template()
    doc.update({
        "corpus_version": "v1", "assignment": "matched", "sample_size_rationale": "power",
        "quality_criteria": "critical-miss <= 1", "coverage_abstention_criteria": ">= 90%",
        "stopping_rule": "stop at budget or 3 misses",
    })
    assert _raises(eh.validate_preregistration, doc)


# Fields the template declares as predeclared but the base validator never required.
NEWLY_REQUIRED = (
    "task_clustering", "carryover_controls", "blinding", "followup_rework_window",
    "noninferiority_margin", "critical_miss_tolerance", "latency_cost_limits", "uncertainty_method",
)


def test_preregistration_unset_claimed_mandatory_field_rejected():
    # SQA-integrity-009: each newly-required declared field, when unset, refuses the record
    assert set(NEWLY_REQUIRED) <= set(eh.REQUIRED_PREREGISTRATION)
    for field in NEWLY_REQUIRED:
        doc = _complete_preregistration()
        doc[field] = None
        assert _raises(eh.validate_preregistration, doc), field


def test_preregistration_zero_threshold_is_supplied():
    # a numeric threshold of 0 is a real, supplied value, not unset
    doc = _complete_preregistration()
    doc["critical_miss_tolerance"] = 0
    assert eh.validate_preregistration(doc)


def test_preregistration_explicit_not_applicable_is_declared():
    # the only sanctioned way to skip a field is an explicit, reasoned declaration
    doc = _complete_preregistration()
    doc["blinding"] = ""
    assert _raises(eh.validate_preregistration, doc)
    doc["not_applicable"] = {"blinding": "no human graders; deterministic scoring"}
    assert eh.validate_preregistration(doc)
    doc["not_applicable"] = {"blinding": "  "}
    assert _raises(eh.validate_preregistration, doc)


def test_design_defining_field_cannot_be_waived():
    # SQA-integrity-009: a reason cannot waive a field the study design depends on
    for field in ("stopping_rule", "assignment", "corpus_version", "quality_criteria"):
        doc = _complete_preregistration()
        doc[field] = ""
        doc["not_applicable"] = {field: "not needed"}
        assert _raises(eh.validate_preregistration, doc), field


def test_waivable_field_with_reason_is_accepted():
    # a field with no meaning in some designs may be waived, but only with its reason
    doc = _complete_preregistration()
    doc["blinding"] = ""
    doc["not_applicable"] = {"blinding": "deterministic scoring, no human graders"}
    assert eh.validate_preregistration(doc)


def test_numeric_thresholds_must_be_finite_nonnegative_numbers():
    for bad in (float("nan"), -0.1, True):
        doc = _complete_preregistration()
        doc["noninferiority_margin"] = bad
        assert _raises(eh.validate_preregistration, doc), bad


def main() -> int:
    test_split_keeps_lineage_groups_together()
    test_split_unknown_group_rejected()
    test_freeze_requires_adjudication_and_unique_ids()
    test_arm_attribution_and_matched_inputs()
    test_arm_d_applicability()
    test_preregistration_required_fields()
    test_preregistration_six_field_partial_record_rejected()
    test_preregistration_unset_claimed_mandatory_field_rejected()
    test_preregistration_zero_threshold_is_supplied()
    test_preregistration_explicit_not_applicable_is_declared()
    test_design_defining_field_cannot_be_waived()
    test_waivable_field_with_reason_is_accepted()
    test_numeric_thresholds_must_be_finite_nonnegative_numbers()
    print("evaluation: leakage-free split, matched arms and preregistration pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
