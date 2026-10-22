"""Adversarial tests for mode-isolated deterministic semantic policy composition.

Pure offline tests: no provider, network or credential is involved. They prove
the six JR-13 acceptance criteria using only ``tools/semantic_policy.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import semantic_policy as sp  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except sp.SemanticPolicyError:
        return True
    return False


def _obs(status="succeeded", operation="op-1"):
    return {
        "schema_version": 1,
        "task": {"task_id": "t", "operation_id": operation, "attempt": 1},
        "binding": {"base_revision": "0" * 40, "candidate": "1" * 40, "requirement_refs": [], "contract_refs": []},
        "question": {"family": "DF-01", "version": "v1", "primitive": "choice",
                     "instructions": "ctx", "options": ["a", "b"]},
        "model": {"requested": "jev-1", "resolved": "jev-1", "provider_request_id": None},
        "transport": {"transmitted_body_sha256": "a" * 64, "raw_response_sha256": "b" * 64},
        "execution": {"status": status, "reason_code": None},
        "answer": {"distribution": {"a": 0.7, "b": 0.3}, "selection": 0} if status == "succeeded" else None,
    }


def _veto():
    return [sp.HardVeto("protected-path", lambda f: f.get("path") == "schema/", "protected path must not change")]


def test_off_is_default_and_imports_no_provider():
    # AC-13-01: default is off; nothing in this module imports a provider package
    state = sp.off_state()
    assert state.global_mode == "off"
    assert state.resolve("DF-01") == "off"
    for provider in ("openai", "requests", "httpx", "jev", "urllib3", "anthropic"):
        assert provider not in sys.modules, f"off layer pulled in provider module {provider!r}"


def test_off_mock_replay_shadow_never_influence():
    # AC-13-03: shadow (and off/mock/replay) never changes the baseline outcome
    for mode in ("off", "mock", "replay", "shadow"):
        result = sp.compose_policy(family="DF-01", mode=mode, facts={"path": "src/x.py"},
                                   observations=[_obs()], vetoes=_veto())
        assert result["disposition"]["outcome"] == "no_effect", mode
        assert result["vetoes"] == []


def test_governed_bounded_and_veto_first():
    # A valid succeeded observation yields a bounded action within the governed set
    result = sp.compose_policy(family="DF-01", mode="governed", facts={"path": "src/x.py"},
                               observations=[_obs()], vetoes=_veto())
    assert result["disposition"]["outcome"] in ("advisory", "conservative_escalation", "clarify", "abstain", "no_effect")
    # A hard veto over facts dominates a favorable observation in any mode
    vetoed = sp.compose_policy(family="DF-01", mode="governed", facts={"path": "schema/"},
                               observations=[_obs()], vetoes=_veto())
    assert vetoed["disposition"]["outcome"] == "veto"
    assert vetoed["vetoes"][0]["id"] == "protected-path"
    assert vetoed["vetoes"][0]["triggered"] is True


def test_execution_status_fallback():
    # AC-13-02: non-succeeded states are invisible and produce a safe fallback
    for status in ("disabled", "ineligible", "unavailable", "invalid_response", "cancelled"):
        result = sp.compose_policy(family="DF-01", mode="advisory", facts={"path": "src"},
                                   observations=[_obs(status)], vetoes=_veto())
        assert result["disposition"]["outcome"] == "no_effect", status


def test_pure_and_deterministic():
    # AC-13-04: identical inputs yield byte-identical results (replay-safe)
    args = dict(family="DF-01", mode="advisory", facts={"path": "src"}, observations=[_obs()], vetoes=_veto())
    assert sp.compose_policy(**args) == sp.compose_policy(**args)


def test_family_cannot_self_enable():
    # AC-13-06: widening requires authorization; narrowing never does; disable always works
    state = sp.off_state()
    assert _raises(sp.authorize_transition, state, family="DF-01", new_mode="advisory", authorization="")
    assert _raises(sp.authorize_transition, state, family="DF-01", new_mode="advisory", authorization=None)
    widened = sp.authorize_transition(state, family="DF-01", new_mode="advisory", authorization="authorized-record")
    assert widened.resolve("DF-01") == "advisory"
    # an unauthorized sibling family stays off
    assert widened.resolve("DF-02") == "off"
    # rollback to off requires no authorization and always succeeds
    back = sp.disable(widened, family="DF-01")
    assert back.resolve("DF-01") == "off"
    # a broken hard veto fails closed
    broken = sp.HardVeto("broken", lambda f: 1 / 0, "should raise")
    assert _raises(sp.compose_policy, family="DF-01", mode="advisory", facts={}, observations=[_obs()], vetoes=[broken])


def main() -> int:
    test_off_is_default_and_imports_no_provider()
    test_off_mock_replay_shadow_never_influence()
    test_governed_bounded_and_veto_first()
    test_execution_status_fallback()
    test_pure_and_deterministic()
    test_family_cannot_self_enable()
    print("semantic-policy: off-default modes, veto-first composition and authorized transitions pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
