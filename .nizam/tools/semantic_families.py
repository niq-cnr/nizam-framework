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

DF02_RISK_CLASS = {
    "family": "DF-02",
    "question_id": "risk_class.v1",
    "version": "risk_class.v1",
    "primitive": "choice",
    "instructions": (
        "Classify the behavioral risk of the change beyond its filename and author label, using the "
        "verified protected-path and risk facts plus the candidate delta. Verified facts dominate any "
        "favorable impression. Select exactly one:\n"
        "- low_risk: no behavioral, security, authorization, schema or blast-radius consequence.\n"
        "- bounded_risk: a contained behavioral consequence inside declared scope.\n"
        "- consequential_risk: a security, authorization, contract, irreversibility or cross-component "
        "consequence a filename would miss.\n"
        "- unknown_risk: the facts are insufficient or conflicting. Unknown must never read as low."
    ),
    "options": ["low_risk", "bounded_risk", "consequential_risk", "unknown_risk"],
    "max_mode": "advisory",
    "depends_on": [],
}

DF02_ESCALATE = {
    "family": "DF-02",
    "question_id": "risk_escalate.v1",
    "version": "risk_escalate.v1",
    "primitive": "noul",
    "polarity": "yes",
    "instructions": (
        "Probability that this change genuinely requires conservative escalation to a higher assurance "
        "review, given the verified protected-path and risk facts. Absence of a clear answer is unknown, "
        "never a low probability."
    ),
    "max_mode": "advisory",
    "depends_on": ["risk_class.v1"],
}

DF03_RELEVANCE = {
    "family": "DF-03",
    "question_id": "evidence_relevance.v1",
    "version": "evidence_relevance.v1",
    "primitive": "score",
    "instructions": (
        "Score the relevance of this optional evidence excerpt for the downstream decision. Mandatory "
        "contracts, findings and audit scope are retained deterministically and are never filtered; only "
        "optional excerpt ranking is scored. Levels: irrelevant, marginal, material, critical."
    ),
    "rubric": [
        {"level": "irrelevant", "description": "No bearing on the decision."},
        {"level": "marginal", "description": "Weakly related context."},
        {"level": "material", "description": "Directly affects the decision."},
        {"level": "critical", "description": "Decision-determinative; omission is unsafe."},
    ],
    "max_mode": "advisory",
    "depends_on": [],
}

DF04_PROFILE = {
    "family": "DF-04",
    "question_id": "reasoning_profile.v1",
    "version": "reasoning_profile.v1",
    "primitive": "choice",
    "instructions": (
        "Select the reasoning/effort profile for the named deficit. Only configured approved profiles may "
        "be selected; more reasoning cannot repair missing evidence or authority. Select exactly one:\n"
        "- routine: bounded judgment with an existing short answer.\n"
        "- standard: normal implementation reasoning.\n"
        "- extended: multi-step investigation with a bounded stopping condition.\n"
        "- specialist: a specialist domain analysis.\n"
        "A stated deficit that is missing evidence or authority must resolve to routine, not extended."
    ),
    "options": ["routine", "standard", "extended", "specialist"],
    "max_mode": "advisory",
    "depends_on": [],
}

DF05_DIAGNOSIS = {
    "family": "DF-05",
    "question_id": "failure_class.v1",
    "version": "failure_class.v1",
    "primitive": "choice",
    "instructions": (
        "Classify the observed failure from the captured logs and signatures. Select exactly one:\n"
        "- infrastructure: transport, host or provider infrastructure failure.\n"
        "- environment: missing capability or dependency in the environment.\n"
        "- evidence: missing or insufficient evidence.\n"
        "- scope_conflict: a contract or scope conflict.\n"
        "- defect: a deterministic implementation defect.\n"
        "- decomposition_needed: the task must be decomposed.\n"
        "- unknown: insufficient information to classify.\n"
        "Diagnosis is not authority: it can never authorize an attempt or relabel a valid rejection as a "
        "transient failure."
    ),
    "options": [
        "infrastructure",
        "environment",
        "evidence",
        "scope_conflict",
        "defect",
        "decomposition_needed",
        "unknown",
    ],
    "max_mode": "advisory",
    "depends_on": [],
}

DF06_SUPPORT = {
    "family": "DF-06",
    "question_id": "claim_support.v1",
    "version": "claim_support.v1",
    "primitive": "choice",
    "instructions": (
        "Assess whether a claim is supported by its cited source. Existence, digest, freshness and anchor "
        "are verified exactly in code before this question runs; this question assesses semantic support "
        "only. Select exactly one:\n"
        "- supported: the source entails the claim.\n"
        "- partial: the source partly supports the claim.\n"
        "- contradicted: the source contradicts the claim.\n"
        "- unrelated: the valid link does not bear on the claim.\n"
        "- insufficient_evidence: the citations are insufficient. A positive result can never replace a "
        "missing capture."
    ),
    "options": ["supported", "partial", "contradicted", "unrelated", "insufficient_evidence"],
    "max_mode": "advisory",
    "depends_on": [],
}

DF07_VALUE = {
    "family": "DF-07",
    "question_id": "outcome_value.v1",
    "version": "outcome_value.v1",
    "primitive": "score",
    "instructions": (
        "Score the realized value of the accepted change against the original user goal and approved "
        "requirements, separating execution, passing checks, coverage, independent acceptance and observed "
        "user outcome. Missing user feedback is unknown. Levels: unsatisfactory, partial, satisfactory, "
        "excellent."
    ),
    "rubric": [
        {"level": "unsatisfactory", "description": "Goal not met; required failures remain."},
        {"level": "partial", "description": "Goal partly met; material residual work."},
        {"level": "satisfactory", "description": "Goal met within accepted scope."},
        {"level": "excellent", "description": "Goal met with measured user outcome."},
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
    "DF-02": [DF02_RISK_CLASS, DF02_ESCALATE],
    "DF-03": [DF03_RELEVANCE],
    "DF-04": [DF04_PROFILE],
    "DF-05": [DF05_DIAGNOSIS],
    "DF-06": [DF06_SUPPORT],
    "DF-07": [DF07_VALUE],
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
