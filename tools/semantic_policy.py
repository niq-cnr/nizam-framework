"""Mode-isolated deterministic semantic policy composition.

This module owns two concerns the mandate (NIZAM-JEV-OWNER-2026-10-22 section 6)
separates from the observation contract:

1. **Mode state** — the global and per-family mode with ``off`` as the immutable
   default. Widening influence requires an explicit authorized transition; a
   family can never enable itself or widen its own action set, and rollback to
   ``off`` is always permitted.

2. **Pure deterministic composition** — verified facts dominate semantic
   judgment. Hard vetoes are computed first and can never be averaged away. The
   remaining disposition is bounded by the active mode.

This layer never approves, suppresses, allocates attempts, or lowers an
assurance floor. It consumes the validated observations produced by
``tools/semantic_contract.py`` and emits a result shaped by
``schema/semantic_policy_result.schema.json``.
"""

from __future__ import annotations

from typing import Any, Callable, FrozenSet

SUPPORTED_MODES = ("off", "mock", "replay", "shadow", "advisory", "governed")
DEFAULT_MODE = "off"

# Partial order of influence. Widening (increasing influence) requires
# authorization; narrowing never does.
_MODE_RANK = {
    "off": 0,
    "mock": 1,
    "replay": 1,
    "shadow": 2,
    "advisory": 3,
    "governed": 4,
}

NO_EFFECT = "no_effect"
ADVISORY = "advisory"
CONSERVATIVE_ESCALATION = "conservative_escalation"
CLARIFY = "clarify"
ABSTAIN = "abstain"
VETO = "veto"

_DISPOSITIONS = (NO_EFFECT, ADVISORY, CONSERVATIVE_ESCALATION, CLARIFY, ABSTAIN, VETO)

# The dispositions each mode is permitted to emit. Off/mock/replay/shadow never
# influence the baseline actors; advisory may suggest (never bind); governed may
# act only inside its preapproved bounded action set.
_MODE_DISPOSITIONS: dict[str, FrozenSet[str]] = {
    "off": frozenset({NO_EFFECT}),
    "mock": frozenset({NO_EFFECT}),
    "replay": frozenset({NO_EFFECT}),
    "shadow": frozenset({NO_EFFECT}),
    "advisory": frozenset({NO_EFFECT, ADVISORY}),
    "governed": frozenset(
        {NO_EFFECT, ADVISORY, CONSERVATIVE_ESCALATION, CLARIFY, ABSTAIN}
    ),
}


class SemanticPolicyError(ValueError):
    """A policy transition or composition is invalid or unauthorized."""


class HardVeto:
    """A named deterministic predicate over verified facts.

    Vetoes read exact facts computed in code (exit codes, path membership,
    attempt counts, authority consumption, dates, budgets) and never semantic
    answers. A triggered veto forces the ``veto`` outcome regardless of mode.
    """

    __slots__ = ("id", "predicate", "reason")

    def __init__(self, veto_id: str, predicate: Callable[[dict[str, Any]], bool], reason: str):
        if not veto_id or not reason:
            raise SemanticPolicyError("a hard veto needs a non-empty id and reason")
        self.id = veto_id
        self.predicate = predicate
        self.reason = reason

    def applies(self, facts: dict[str, Any]) -> bool:
        try:
            return bool(self.predicate(facts))
        except Exception as exc:  # a broken veto must fail closed
            raise SemanticPolicyError(f"hard veto {self.id!r} raised during evaluation: {exc}") from exc


class ModeState:
    """An immutable global + per-family mode snapshot with ``off`` as default."""

    __slots__ = ("global_mode", "family_modes")

    def __init__(self, global_mode: str = DEFAULT_MODE, family_modes: dict[str, str] | None = None):
        if global_mode not in SUPPORTED_MODES:
            raise SemanticPolicyError(f"unsupported global mode {global_mode!r}")
        overrides: dict[str, str] = {}
        for family, mode in (family_modes or {}).items():
            if not isinstance(family, str) or not family.strip():
                raise SemanticPolicyError("family key must be a non-empty string")
            if mode not in SUPPORTED_MODES:
                raise SemanticPolicyError(f"unsupported mode {mode!r} for family {family!r}")
            overrides[family] = mode
        self.global_mode = global_mode
        self.family_modes = overrides

    def resolve(self, family: str) -> str:
        return self.family_modes.get(family, self.global_mode)


def off_state() -> ModeState:
    """Return the default all-off state."""
    return ModeState()


def authorize_transition(
    state: ModeState,
    *,
    family: str | None,
    new_mode: str,
    authorization: str,
) -> ModeState:
    """Return a new state with the requested mode, widening only when authorized.

    Narrowing (reducing influence) needs no authorization because rollback to a
    safer mode must always be available. Widening requires a non-empty
    authorization record; without it the transition is refused, so a family can
    never enable itself or widen its own action set.
    """
    if new_mode not in SUPPORTED_MODES:
        raise SemanticPolicyError(f"unsupported mode {new_mode!r}")

    current = state.global_mode if family is None else state.resolve(family)
    if _MODE_RANK[new_mode] > _MODE_RANK[current]:
        if not isinstance(authorization, str) or not authorization.strip():
            raise SemanticPolicyError(
                "widening influence requires a non-empty authorization record"
            )

    if family is None:
        return ModeState(global_mode=new_mode, family_modes=state.family_modes)
    overrides = dict(state.family_modes)
    overrides[family] = new_mode
    return ModeState(global_mode=state.global_mode, family_modes=overrides)


def disable(state: ModeState, family: str | None = None) -> ModeState:
    """Roll back the global or a family mode to ``off``; never requires authorization."""
    if family is None:
        return ModeState(global_mode="off", family_modes=state.family_modes)
    overrides = dict(state.family_modes)
    overrides[family] = "off"
    return ModeState(global_mode=state.global_mode, family_modes=overrides)


def _execution_influential(observation: dict[str, Any] | None) -> bool:
    """A semantic answer influences policy only when it is a valid succeeded observation."""
    if not isinstance(observation, dict):
        return False
    execution = observation.get("execution")
    return isinstance(execution, dict) and execution.get("status") == "succeeded"


def compose_policy(
    *,
    family: str,
    mode: str,
    facts: dict[str, Any],
    observations: list[dict[str, Any]] | None,
    vetoes: list[HardVeto] | None = None,
    question_version: str | None = None,
) -> dict[str, Any]:
    """Compose a pure disposition from verified facts and validated observations.

    Order is fixed and cannot be reversed:

    1. Hard vetoes over verified facts — any trigger forces ``veto``.
    2. Execution-status fallback — non-succeeded observations are invisible.
    3. Mode-bounded disposition — never outside ``_MODE_DISPOSITIONS[mode]``.

    The function is pure: identical inputs produce identical output, so replay
    of a stored observation yields the exact same policy result.
    """
    if mode not in SUPPORTED_MODES:
        raise SemanticPolicyError(f"unsupported mode {mode!r}")
    if not isinstance(facts, dict):
        raise SemanticPolicyError("facts must be an object")

    triggered = []
    for veto in vetoes or []:
        if veto.applies(facts):
            triggered.append({"id": veto.id, "triggered": True, "reason": veto.reason})
    if triggered:
        return {
            "schema_version": 1,
            "family": family,
            "question_version": question_version,
            "disposition": {"outcome": VETO, "reason": "hard veto triggered"},
            "vetoes": triggered,
            "basis": {"facts": list(facts), "observations": [o.get("task", {}).get("operation_id") for o in (observations or []) if isinstance(o, dict)]},
        }

    influential = [o for o in (observations or []) if _execution_influential(o)]

    allowed = _MODE_DISPOSITIONS[mode]
    if mode in ("off", "mock", "replay", "shadow"):
        outcome = NO_EFFECT
    elif mode == "advisory" and influential:
        outcome = ADVISORY
    elif mode == "advisory":
        outcome = NO_EFFECT
    elif mode == "governed" and influential:
        # The mildest bounded action is the safe default; family policies bound
        # this further (clarify / conservative escalation / abstain) in JR-27.
        outcome = ADVISORY
    else:
        outcome = NO_EFFECT

    if outcome not in allowed:
        raise SemanticPolicyError(f"computed outcome {outcome!r} outside allowed set for mode {mode!r}")

    return {
        "schema_version": 1,
        "family": family,
        "question_version": question_version,
        "disposition": {"outcome": outcome},
        "vetoes": [],
        "basis": {
            "facts": list(facts),
            "observations": [o.get("task", {}).get("operation_id") for o in influential if isinstance(o, dict)],
        },
    }
