"""Provider-neutral typed semantic observation contracts: Choice, Noul, Score.

This module defines the versioned discriminated union for the three supported
semantic primitives and the pure validation functions that gate every
observation. It is deliberately authority-free: no field here approves,
suppresses, allocates attempts or lowers an assurance floor. Semantic answers,
execution status and policy disposition are three distinct concerns; this module
owns only the first two and never the third.

Design invariants (mandate NIZAM-JEV-OWNER-2026-10-22 section 6):

- A primitive is identified by an explicit ``kind`` discriminator; malformed,
  missing or unknown kinds are unusable observations, never a cheap fallback.
- Option order participates in identity and is never silently sorted.
- A Noul probability is the probability of the declared ``yes`` proposition;
  a missing value is ``unknown``, never ``false``.
- A Score has an ordered rubric, a level distribution and an expected level
  position; the expected value is validated against the rubric. An average can
  never erase a hard veto (that is policy, not this contract).
"""

from __future__ import annotations

import json
import math
from typing import Any

# --------------------------------------------------------------------------- #
# Version and vocabulary
# --------------------------------------------------------------------------- #

OBSERVATION_SCHEMA_VERSION = 1

SUPPORTED_PRIMITIVES = ("choice", "noul", "score")

EXECUTION_STATUSES = (
    "disabled",
    "ineligible",
    "succeeded",
    "unavailable",
    "invalid_response",
    "cancelled",
)

REASON_CODES = (
    "missing_context",
    "missing_evidence",
    "denied_egress",
    "budget_exhausted",
    "timeout",
    "unsupported_capability",
    "invalid_response",
    "cancelled_before_dispatch",
)

PROBABILITY_SUM_TOLERANCE = 1e-6


class SemanticContractError(ValueError):
    """A semantic record is malformed or unusable; never coercible to a pass."""


def _canonical_bytes(value: Any) -> bytes:
    """Serialize a value into deterministic UTF-8 bytes preserving array order."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


# --------------------------------------------------------------------------- #
# Pure per-primitive validation
# --------------------------------------------------------------------------- #

def validate_probability(value: Any) -> float:
    """Return a finite probability in [0, 1]; reject anything else.

    NaN and infinities are not representable probabilities and are rejected so
    that a malformed distribution can never become a false risk signal.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SemanticContractError(f"probability must be a finite number, got {value!r}")
    number = float(value)
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        raise SemanticContractError(f"probability out of range or non-finite: {value!r}")
    return number


def validate_polarity(value: Any) -> str:
    """Return a stable documented polarity; only ``yes``/``no`` are supported."""
    if value not in ("yes", "no"):
        raise SemanticContractError(f"polarity must be 'yes' or 'no', got {value!r}")
    return value


def validate_choice_definition(options: Any) -> list[str]:
    """Validate an ordered list of mutually distinct, complete option labels.

    Order is semantic identity: the caller must preserve it, and this function
    never sorts or renormalizes it.
    """
    if not isinstance(options, list) or len(options) < 1:
        raise SemanticContractError("Choice options must be a non-empty ordered list")
    if len(options) < 2:
        raise SemanticContractError("Choice requires at least two mutually exclusive options")
    labels: list[str] = []
    for item in options:
        if not isinstance(item, str) or not item.strip():
            raise SemanticContractError(f"Choice option must be a non-empty string, got {item!r}")
        labels.append(item)
    if len(set(labels)) != len(labels):
        raise SemanticContractError("Choice options must be distinct; duplicates are ambiguous")
    return labels


def validate_distribution(
    distribution: Any,
    *,
    labels: list[str],
    tolerance: float = PROBABILITY_SUM_TOLERANCE,
) -> dict[str, float]:
    """Validate a distribution over exactly the declared labels.

    Every label must be present with a finite in-range probability, no extra
    labels are allowed, and the sum must be within the declared tolerance of 1.
    A missing or materially invalid sum is unusable, never silently renormalized.
    """
    if not isinstance(distribution, dict):
        raise SemanticContractError("distribution must be an object mapping label -> probability")
    expected = set(labels)
    if set(distribution) != expected:
        missing = sorted(expected - set(distribution))
        extra = sorted(set(distribution) - expected)
        raise SemanticContractError(
            "distribution labels do not match the declared options"
            + (f"; missing {missing}" if missing else "")
            + (f"; unknown {extra}" if extra else "")
        )
    values = {}
    for label in labels:
        values[label] = validate_probability(distribution[label])
    total = sum(values.values())
    if abs(total - 1.0) > tolerance:
        raise SemanticContractError(f"distribution sums to {total}, outside tolerance {tolerance}")
    return values


def _validate_selected_index(selection: Any, labels: list[str]) -> int:
    if isinstance(selection, bool) or not isinstance(selection, int):
        raise SemanticContractError(f"selected option index must be an integer, got {selection!r}")
    if selection < 0 or selection >= len(labels):
        raise SemanticContractError(f"selected option index {selection} out of range")
    return selection


def validate_choice_answer(answer: Any, *, options: list[str]) -> dict[str, Any]:
    """Validate a Choice answer against its ordered options.

    The selected option must be consistent with the returned distribution, or the
    answer must declare an explicit tie or ``insufficient_evidence``. A provider
    answer that omits any of these is unusable.
    """
    if not isinstance(answer, dict):
        raise SemanticContractError("Choice answer must be an object")
    labels = validate_choice_definition(options)
    distribution = validate_distribution(answer.get("distribution"), labels=labels)

    selection = answer.get("selection")
    tie = answer.get("tie")
    insufficient = answer.get("insufficient_evidence")

    explicit_modes = sum(1 for value in (selection, tie, insufficient) if value is not None)
    if explicit_modes != 1:
        raise SemanticContractError(
            "Choice answer must declare exactly one of selection, tie, or insufficient_evidence"
        )

    if insufficient is not None:
        if insufficient is not True:
            raise SemanticContractError("insufficient_evidence must be true when declared")
        return answer

    if tie is not None:
        if not isinstance(tie, list) or len(tie) < 2:
            raise SemanticContractError("a tie must name at least two options")
        indices = [_validate_selected_index(i, labels) for i in tie]
        if len(set(indices)) != len(indices):
            raise SemanticContractError("a tie must name distinct options")
        return answer

    index = _validate_selected_index(selection, labels)
    selected = labels[index]
    competitors = [v for l, v in distribution.items() if l != selected]
    if distribution[selected] <= max(competitors, default=1.0):
        raise SemanticContractError(
            "selected option is not the unique modal option; a genuine tie must be declared explicitly"
        )
    return answer


def validate_noul_answer(answer: Any, *, polarity: str = "yes") -> dict[str, Any]:
    """Validate a Noul answer: a probability of the declared yes proposition.

    A missing probability is ``unknown`` and handled by the caller, never
    coerced to false. No correctness confidence is accepted or invented.
    """
    if not isinstance(answer, dict):
        raise SemanticContractError("Noul answer must be an object")
    polarity = validate_polarity(polarity)
    if "probability" not in answer or answer["probability"] is None:
        raise SemanticContractError("Noul answer is missing its probability")
    probability = validate_probability(answer["probability"])
    if "confidence" in answer:
        raise SemanticContractError(
            "Noul answer must not carry a confidence field; probability is not confidence in correctness"
        )
    return answer


def validate_score_rubric(rubric: Any) -> list[dict[str, str]]:
    """Validate an ordered descriptive rubric of at least two levels."""
    if not isinstance(rubric, list) or len(rubric) < 2:
        raise SemanticContractError("Score rubric must be an ordered list of at least two levels")
    levels: list[dict[str, str]] = []
    for item in rubric:
        if not isinstance(item, dict):
            raise SemanticContractError(f"rubric level must be an object, got {item!r}")
        level = item.get("level")
        description = item.get("description")
        if not isinstance(level, str) or not level.strip() or not isinstance(description, str):
            raise SemanticContractError("every rubric level needs a non-empty 'level' and 'description'")
        levels.append({"level": level, "description": description})
    names = [l["level"] for l in levels]
    if len(set(names)) != len(names):
        raise SemanticContractError("rubric level names must be distinct")
    return levels


def validate_score_answer(answer: Any, *, rubric: list[dict[str, str]], tolerance: float = PROBABILITY_SUM_TOLERANCE) -> dict[str, Any]:
    """Validate a Score answer: level distribution and expected level position.

    The expected level position is validated against the declared rubric and
    must be an integer index. It is a distributional expectation, not an exact
    measurement of anything; a hard disqualifier is a policy veto handled
    outside this contract.
    """
    if not isinstance(answer, dict):
        raise SemanticContractError("Score answer must be an object")
    levels = validate_score_rubric(rubric)
    raw_dist = answer.get("distribution")
    if not isinstance(raw_dist, list) or len(raw_dist) != len(levels):
        raise SemanticContractError("Score distribution must be a list over every rubric level")
    probs = [validate_probability(v) for v in raw_dist]
    total = sum(probs)
    if abs(total - 1.0) > tolerance:
        raise SemanticContractError(f"Score distribution sums to {total}, outside tolerance {tolerance}")
    expected = answer.get("expected_level")
    _validate_selected_index(expected, [l["level"] for l in levels])
    return answer


# --------------------------------------------------------------------------- #
# The discriminated union
# --------------------------------------------------------------------------- #

def validate_observation(observation: Any) -> dict[str, Any]:
    """Validate a full semantic observation: binding, question, model, execution, answer.

    Returns the normalized observation when it is coherent and usable, and
    raises :class:`SemanticContractError` otherwise. The caller may therefore
    treat ``validate_observation`` returning normally as "a valid observation
    with a usable (or explicitly absent) semantic answer"; it must then apply
    its own policy to the answer. This function never renders a policy verdict.
    """
    if not isinstance(observation, dict):
        raise SemanticContractError("observation must be an object")

    if observation.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        raise SemanticContractError(
            f"unsupported observation schema_version {observation.get('schema_version')!r}"
        )

    question = observation.get("question")
    if not isinstance(question, dict):
        raise SemanticContractError("observation.question must be an object")
    primitive = question.get("primitive")
    if primitive not in SUPPORTED_PRIMITIVES:
        raise SemanticContractError(f"unsupported primitive {primitive!r}")
    if not isinstance(question.get("family"), str) or not question["family"].strip():
        raise SemanticContractError("question.family must be a non-empty string")
    if not isinstance(question.get("version"), str) or not question["version"].strip():
        raise SemanticContractError("question.version must be a non-empty string")

    model = observation.get("model")
    if not isinstance(model, dict):
        raise SemanticContractError("observation.model must be an object")
    requested = model.get("requested")
    resolved = model.get("resolved")
    if not isinstance(requested, str) or not requested.strip():
        raise SemanticContractError("model.requested must be a non-empty exact model identity")
    if resolved is not None and resolved != requested:
        raise SemanticContractError(
            f"resolved model {resolved!r} does not match requested model {requested!r}"
        )

    execution = observation.get("execution")
    if not isinstance(execution, dict):
        raise SemanticContractError("observation.execution must be an object")
    status = execution.get("status")
    if status not in EXECUTION_STATUSES:
        raise SemanticContractError(f"unsupported execution status {status!r}")
    reason = execution.get("reason_code")
    if reason is not None and reason not in REASON_CODES:
        raise SemanticContractError(f"unsupported reason code {reason!r}")

    answer = observation.get("answer")
    if status != "succeeded":
        if answer is not None:
            raise SemanticContractError("an observation without 'succeeded' status must not claim an answer")
        return observation

    if not isinstance(answer, dict):
        raise SemanticContractError("a succeeded observation must carry an answer object")

    if primitive == "choice":
        options = question.get("options")
        validate_choice_answer(answer, options=options)
    elif primitive == "noul":
        validate_noul_answer(answer, polarity=question.get("polarity", "yes"))
    elif primitive == "score":
        validate_score_answer(answer, rubric=question.get("rubric"))

    return observation


def observation_identity(observation: dict[str, Any]) -> str:
    """Return a lowercase SHA-256 digest of the canonical observation bytes.

    Array order (option order, rubric order) participates in the digest; object
    keys do not. This identity does not confer authority against a hostile
    writer and is not a trust proof.
    """
    return __import__("hashlib").sha256(_canonical_bytes(observation)).hexdigest()


def fresh_observation(
    *,
    task_id: str,
    operation_id: str,
    attempt: int,
    base_revision: str,
    candidate: str,
    requirement_refs: list[str],
    contract_refs: list[str],
    question: dict[str, Any],
    model: dict[str, Any],
    provider_request_id: str | None,
    transmitted_body_sha256: str,
    raw_response_sha256: str,
    execution_status: str,
    reason_code: str | None,
    answer: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble a versioned observation with its full binding.

    This is a constructor, not a policy. Callers still run
    :func:`validate_observation` before anything is persisted or dispatched.
    """
    observation = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "task": {
            "task_id": task_id,
            "operation_id": operation_id,
            "attempt": attempt,
        },
        "binding": {
            "base_revision": base_revision,
            "candidate": candidate,
            "requirement_refs": list(requirement_refs),
            "contract_refs": list(contract_refs),
        },
        "question": question,
        "model": {
            "requested": model["requested"],
            "resolved": model.get("resolved"),
            "provider_request_id": provider_request_id,
        },
        "transport": {
            "transmitted_body_sha256": transmitted_body_sha256,
            "raw_response_sha256": raw_response_sha256,
        },
        "execution": {
            "status": execution_status,
            "reason_code": reason_code,
        },
        "answer": answer,
    }
    validate_observation(observation)
    return observation
