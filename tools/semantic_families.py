"""The seven decision families: question definitions, admission gates and state projection.

This module realizes the family layer on top of the typed contracts and the
catalog. It owns, for each family:

- the versioned question definition (full instructions, ordered options or
  rubric or polarity, dependencies, max_mode);
- the admission gate that refuses dispatch when mandatory state sources are
  missing (a missing source is ``missing_context``, never a coerced answer);
- the bounded state projection that renders substantive context into the
  question instructions rather than relying on opaque question ids.

DF-01 is implemented first and is the validation wave the other families learn
from. A model here is treated purely as data: its answer is validated by
``semantic_contract`` and composed by ``semantic_policy``; nothing in this
module grants authority or approves work.
"""

from __future__ import annotations

from typing import Any

from semantic_catalog import CatalogError, FAMILY_DEFINITIONS, validate_question_spec

# --------------------------------------------------------------------------- #
# Question definitions
# --------------------------------------------------------------------------- #

DF01_QUESTION = {
    "family": "DF-01",
    "question_id": "component_requirement.v1",
    "version": "component_requirement.v1",
    "primitive": "choice",
    "instructions": (
        "Classify the relationship of the proposed component to the approved requirements. "
        "Read the approved requirements, the explicit non-goals, the component proposal and "
        "the supplied source/dependency context, then select exactly one option:\n"
        "- direct_requirement: the component directly implements an approved requirement.\n"
        "- necessary_support: the component is necessary support for a requirement (security, "
        "validation, compatibility, migration, or another named concern) even though no feature "
        "sentence names it explicitly.\n"
        "- unsupported_extension: the component is speculative scope not grounded in an "
        "approved requirement.\n"
        "- insufficient_evidence: the supplied sources are not enough to decide.\n"
        "An author's assertion that a component is necessary is not independent evidence."
    ),
    "options": [
        "direct_requirement",
        "necessary_support",
        "unsupported_extension",
        "insufficient_evidence",
    ],
    "max_mode": "advisory",
    "depends_on": [],
}

# Mandatory state sources per family. A request missing any of these refuses
# dispatch with reason ``missing_context`` before any network activity.
MANDATORY_SOURCES: dict[str, tuple[str, ...]] = {
    "DF-01": ("approved_requirements", "component_proposal"),
    "DF-02": ("protected_path_facts", "candidate_delta"),
    "DF-03": ("immutable_evidence", "mandatory_findings"),
    "DF-04": ("risk_observations", "approved_profiles"),
    "DF-05": ("captured_failures", "task_contract"),
    "DF-06": ("claims", "citations"),
    "DF-07": ("user_goal", "accepted_deliverables"),
}

FAMILY_QUESTIONS: dict[str, list[dict[str, Any]]] = {
    "DF-01": [DF01_QUESTION],
}


class FamilyAdmissionError(ValueError):
    """A family request cannot be dispatched because mandatory context is missing."""


def validate_family_questions() -> None:
    """Ensure every family question satisfies the catalog's typed-question rules."""
    for family, questions in FAMILY_QUESTIONS.items():
        if family not in FAMILY_DEFINITIONS:
            raise CatalogError(f"questions registered for unknown family {family!r}")
        for question in questions:
            validate_question_spec(question)


def admit(family: str, state: dict[str, Any]) -> None:
    """Refuse dispatch when a mandatory state source is missing or unusable."""
    if family not in FAMILY_DEFINITIONS:
        raise FamilyAdmissionError(f"unknown family {family!r}")
    missing = [
        source
        for source in MANDATORY_SOURCES.get(family, ())
        if state.get(source) in (None, "", [], {})
    ]
    if missing:
        raise FamilyAdmissionError(
            "missing mandatory context: " + ", ".join(sorted(missing))
        )


def required_sources(family: str) -> tuple[str, ...]:
    return MANDATORY_SOURCES.get(family, ())


def build_projections(family: str, state: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    """Return a dispatch request with substantive context projected into the instructions.

    This is a deterministic bounded projection, never a model call. The full
    question definition is returned with its instructions rendered from the
    supplied state; mandatory sources that fall back to empty are surfaced by
    :func:`admit` before this is called.
    """
    admit(family, state)
    if question.get("family") != family:
        raise FamilyAdmissionError(
            f"question {question.get('question_id')!r} does not belong to family {family!r}"
        )
    validate_question_spec(question)
    rendered = {
        **question,
        "instructions": _render_instructions(family, question["instructions"], state),
    }
    return rendered


def _render_instructions(family: str, template: str, state: dict[str, Any]) -> str:
    """Substitute the family's state sources into the instruction template."""
    rendered = template
    for source in FAMILY_DEFINITIONS[family]["state_sources"]:
        value = state.get(source)
        placeholder = "{" + source + "}"
        if placeholder in rendered:
            rendered = rendered.replace(placeholder, _stringify(value))
        else:
            rendered += f"\n\n{source}:\n{_stringify(value)}"
    return rendered


def _stringify(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        if value and all(isinstance(item, dict) for item in value):
            from semantic_contract import _canonical_bytes  # deterministic, order-preserving

            return _canonical_bytes(value).decode("utf-8")
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        from semantic_contract import _canonical_bytes

        return _canonical_bytes(value).decode("utf-8")
    return str(value)
