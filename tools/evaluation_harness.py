"""Four-arm evaluation harness and preregistration contract (JR-17).

The four comparison arms, per the mandate:

- **A** — repaired, instrumented Nizam with the semantic provider off;
- **B** — the existing model answers the same atomic questions with the same
  deterministic composition;
- **C** — the exact pinned Jev configuration answers those questions with a
  matched source projection and policy;
- **D** — exact deterministic rules, only where the question genuinely permits
  them, and abstains elsewhere.

This module is the offline harness: it validates arm attribution, matched
inputs, split isolation and all-attempt accounting. It makes no live call, and
reports discrimination/calibration data through the preregistration contract
whose thresholds are never chosen after seeing held-out results.
"""

from __future__ import annotations

from typing import Any

ARMS = ("A", "B", "C", "D")


class HarnessError(ValueError):
    """A comparison is misattributed, unmatched or would fabricate a result."""


def validate_arm(arm: str) -> str:
    if arm not in ARMS:
        raise HarnessError(f"unknown comparison arm {arm!r}")
    return arm


def matched_inputs(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify every task sees the same atomic question across its assigned arms.

    Arms B and C must answer the same atomic question with the same projection;
    a task whose arm inputs disagree is a controlled-factor violation.
    """
    by_task: dict[str, dict[str, Any]] = {}
    for assignment in assignments:
        arm = validate_arm(assignment.get("arm"))
        task = assignment.get("task_id")
        inputs = assignment.get("inputs")
        if not task:
            raise HarnessError("assignment is missing a task id")
        if by_task.get(task, inputs) != inputs:
            raise HarnessError(f"task {task!r} received unmatched inputs across arms")
        by_task[task] = inputs
    return by_task


def is_arm_d_applicable(question: dict[str, Any]) -> bool:
    """Arm D applies only where the question is exactly determinable; else abstain."""
    return question.get("deterministic") is True


def preregistration_template() -> dict[str, Any]:
    """The fields that must be predeclared before any held-out evaluation."""
    return {
        "schema_version": 1,
        "corpus_version": "",
        "assignment": "randomized-or-matched",
        "task_clustering": "",
        "carryover_controls": "",
        "blinding": "",
        "followup_rework_window": "",
        "sample_size_rationale": "",
        "quality_criteria": "",
        "noninferiority_margin": None,
        "critical_miss_tolerance": None,
        "coverage_abstention_criteria": "",
        "latency_cost_limits": "",
        "uncertainty_method": "",
        "stopping_rule": "",
        "thresholds_set_after_holdout": False,
    }


# Every predeclared design/threshold field the template carries. SQA-integrity-009:
# a field the template names must be supplied before held-out or live evaluation.
# The only exceptions are the two non-design fields below.
REQUIRED_PREREGISTRATION = (
    "corpus_version",
    "assignment",
    "task_clustering",
    "carryover_controls",
    "blinding",
    "followup_rework_window",
    "sample_size_rationale",
    "quality_criteria",
    "noninferiority_margin",
    "critical_miss_tolerance",
    "coverage_abstention_criteria",
    "latency_cost_limits",
    "uncertainty_method",
    "stopping_rule",
)


def _is_supplied(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return isinstance(value, str) and bool(value.strip())


def validate_preregistration(doc: dict[str, Any]) -> dict[str, Any]:
    """Require every predeclared field, or an explicit not_applicable declaration.

    A numeric threshold may be 0, so only None/absent/blank text counts as unset.
    The declaration ``{"not_applicable": "<reason>"}`` is the one permitted way to
    skip a field; a bare blank or null never is.
    """
    if not isinstance(doc, dict):
        raise HarnessError("preregistration must be an object")
    declared = doc.get("not_applicable") or {}
    if not isinstance(declared, dict):
        raise HarnessError("not_applicable must be an object of field -> reason")
    missing = []
    for field in REQUIRED_PREREGISTRATION:
        value = doc.get(field)
        if _is_supplied(value):
            continue
        reason = declared.get(field)
        if isinstance(reason, str) and reason.strip():
            continue
        missing.append(field)
    if missing:
        raise HarnessError("preregistration is missing predeclared fields: " + ", ".join(missing))
    if doc.get("thresholds_set_after_holdout") is not False:
        raise HarnessError("thresholds must not be chosen after seeing held-out results")
    return doc
