"""Versioned question/policy catalog: the seven semantic families and their questions.

This module owns the static, versioned definitions the mandate
(NIZAM-JEV-OWNER-2026-10-22) requires before any family can be dispatched or
operated: each family's purpose, required primitives, consumers, permitted
effects, state sources and consequential error, plus the typed questions those
families ask. It also validates the catalog so that cycles, dangling question
dependencies, ambiguous polarity, contradictory criteria, out-of-family
primitives and unauthorized actions fail closed.

Catalog and activation rules (AC-27-05): task text or a model-generated
configuration can never activate or expand a policy. A catalog change is a
reviewed, versioned record; this module only validates, never self-activates.
"""

from __future__ import annotations

from typing import Any

from semantic_contract import (
    SUPPORTED_PRIMITIVES,
    SemanticContractError,
    validate_choice_definition,
    validate_polarity,
    validate_score_rubric,
)
from semantic_policy import DISPOSITIONS, SUPPORTED_MODES

# --------------------------------------------------------------------------- #
# The seven decision families (Appendix C family-to-primitive map)
# --------------------------------------------------------------------------- #

FAMILY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "DF-01": {
        "name": "Component, dependency and requirement traceability",
        "primitives": ["choice", "noul"],
        "consumers": ["planner", "implementer", "completion-preparation"],
        "permitted_effects": ["no_effect", "advisory"],
        "state_sources": ["approved_requirements", "non_goals", "component_proposal", "source_context"],
        "consequential_error": "rejecting necessary supporting work or missing speculative scope",
        "core_package": "JR-15",
    },
    "DF-02": {
        "name": "Semantic scope and risk",
        "primitives": ["choice", "noul"],
        "consumers": ["orchestrator", "planner", "completion-preparation"],
        "permitted_effects": ["no_effect", "advisory", "conservative_escalation"],
        "state_sources": ["protected_path_facts", "risk_facts", "candidate_delta"],
        "consequential_error": "underclassifying consequential work or accepting unknown as low risk",
        "core_package": "JR-28",
    },
    "DF-03": {
        "name": "Context relevance and selection",
        "primitives": ["noul", "score", "choice"],
        "consumers": ["planner", "implementer", "context-preparation"],
        "permitted_effects": ["no_effect", "advisory"],
        "state_sources": ["immutable_evidence", "mandatory_findings", "context_budget"],
        "consequential_error": "omitting material evidence or contaminating independent review",
        "core_package": "JR-29",
    },
    "DF-04": {
        "name": "Reasoning depth and escalation",
        "primitives": ["choice", "score"],
        "consumers": ["authorized-orchestrator", "implementer"],
        "permitted_effects": ["no_effect", "advisory", "conservative_escalation"],
        "state_sources": ["risk_observations", "evidence_observations", "approved_profiles"],
        "consequential_error": "under-escalation or expensive escalation that cannot fix missing evidence or authority",
        "core_package": "JR-30",
    },
    "DF-05": {
        "name": "Failure and continuation diagnosis",
        "primitives": ["choice", "noul"],
        "consumers": ["failure-router", "implementer", "operator"],
        "permitted_effects": ["no_effect", "advisory"],
        "state_sources": ["captured_failures", "task_contract", "continuation_policy"],
        "consequential_error": "unproductive or unauthorized retry, or relabeling a valid rejection",
        "core_package": "JR-31",
    },
    "DF-06": {
        "name": "Evidence, claims and citations",
        "primitives": ["choice", "noul", "score"],
        "consumers": ["completion-preparation", "verifier", "operator"],
        "permitted_effects": ["no_effect", "advisory"],
        "state_sources": ["claims", "citations", "immutable_sources", "capture_receipts"],
        "consequential_error": "false support, missing contradiction, or overclaimed coverage",
        "core_package": "JR-32",
    },
    "DF-07": {
        "name": "Outcome quality and scope value",
        "primitives": ["choice", "noul", "score"],
        "consumers": ["post-run-evaluation", "operator"],
        "permitted_effects": ["no_effect", "advisory"],
        "state_sources": ["user_goal", "accepted_deliverables", "actual_feedback"],
        "consequential_error": "inflated success or satisfaction, or an inflated economic denominator",
        "core_package": "JR-33",
    },
}

CONSUMER_VOCABULARY = (
    "planner",
    "implementer",
    "completion-preparation",
    "orchestrator",
    "context-preparation",
    "authorized-orchestrator",
    "failure-router",
    "verifier",
    "operator",
    "post-run-evaluation",
)


class CatalogError(ValueError):
    """A family or question catalog record is malformed or contradictory."""


def validate_family_registry() -> dict[str, dict[str, Any]]:
    """Require all seven families, each with a valid primitive/effect/consumer declaration."""
    if set(FAMILY_DEFINITIONS) != {f"DF-0{i}" for i in range(1, 8)}:
        raise CatalogError("the family registry must define exactly DF-01 through DF-07")
    for fid, spec in FAMILY_DEFINITIONS.items():
        for primitive in spec["primitives"]:
            if primitive not in SUPPORTED_PRIMITIVES:
                raise CatalogError(f"family {fid} declares unsupported primitive {primitive!r}")
        for effect in spec["permitted_effects"]:
            if effect not in DISPOSITIONS:
                raise CatalogError(f"family {fid} declares unsupported effect {effect!r}")
        for consumer in spec["consumers"]:
            if consumer not in CONSUMER_VOCABULARY:
                raise CatalogError(f"family {fid} declares unknown consumer {consumer!r}")
        if not spec["consequential_error"] or not spec["state_sources"]:
            raise CatalogError(f"family {fid} is missing its consequential error or state sources")
    return FAMILY_DEFINITIONS


def validate_question_spec(spec: Any) -> dict[str, Any]:
    """Validate one typed question definition against its family and primitive.

    Rejects an ambiguous polarity (a Noul without a declared polarity), a
    Choice without ordered options, a Score without a rubric, a primitive the
    family does not use, and malformed dependency references (validated
    separately by :func:`validate_question_dependencies`).
    """
    if not isinstance(spec, dict):
        raise CatalogError("question spec must be an object")
    family = spec.get("family")
    if family not in FAMILY_DEFINITIONS:
        raise CatalogError(f"question references unknown family {family!r}")
    if not isinstance(spec.get("version"), str) or not spec["version"].strip():
        raise CatalogError("question.version must be a non-empty string")
    question_id = spec.get("question_id")
    if not isinstance(question_id, str) or not question_id.strip():
        raise CatalogError("question.question_id must be a non-empty string")

    primitive = spec.get("primitive")
    if primitive not in SUPPORTED_PRIMITIVES:
        raise CatalogError(f"question {question_id} uses unsupported primitive {primitive!r}")
    if primitive not in FAMILY_DEFINITIONS[family]["primitives"]:
        raise CatalogError(f"question {question_id} uses primitive {primitive!r} the family {family} does not declare")

    if primitive == "choice":
        try:
            validate_choice_definition(spec.get("options"))
        except SemanticContractError as exc:
            raise CatalogError(str(exc)) from exc
    elif primitive == "noul":
        polarity = spec.get("polarity")
        if polarity is None:
            raise CatalogError(f"noul question {question_id} must declare a stable polarity")
        try:
            validate_polarity(polarity)
        except SemanticContractError as exc:
            raise CatalogError(str(exc)) from exc
    elif primitive == "score":
        try:
            validate_score_rubric(spec.get("rubric"))
        except SemanticContractError as exc:
            raise CatalogError(str(exc)) from exc

    mode = spec.get("max_mode", "advisory")
    if mode not in SUPPORTED_MODES:
        raise CatalogError(f"question {question_id} declares unsupported max_mode {mode!r}")

    depends_on = spec.get("depends_on")
    if depends_on is not None and not isinstance(depends_on, list):
        raise CatalogError(f"question {question_id} depends_on must be a list")
    return spec


def validate_question_dependencies(questions: list[dict[str, Any]]) -> None:
    """Reject dangling question references and dependency cycles (AC-27-02)."""
    ids = {q["question_id"] for q in questions}
    if len(ids) != len(questions):
        raise CatalogError("question ids must be unique within a catalog")

    for q in questions:
        for dep in q.get("depends_on") or []:
            if dep not in ids:
                raise CatalogError(f"question {q['question_id']} depends on unknown question {dep!r}")

    # cycle detection via DFS
    adj = {q["question_id"]: (q.get("depends_on") or []) for q in questions}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in adj}
    visiting: list[str] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        visiting.append(node)
        for dep in adj[node]:
            if color[dep] == GRAY:
                cycle = visiting[visiting.index(dep):] + [dep]
                raise CatalogError("question dependency cycle: " + " -> ".join(cycle))
            if color[dep] == WHITE:
                visit(dep)
        visiting.pop()
        color[node] = BLACK

    for name in adj:
        if color[name] == WHITE:
            visit(name)
