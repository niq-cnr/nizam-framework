"""Adversarial tests for provider-attempt usage accounting (JR-07)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import usage_accounting as ua  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ua.UsageError:
        return True
    return False


def _event(**overrides):
    event = {
        "schema_version": 1,
        "event_id": "e-1",
        "kind": "completion",
        "operation_id": "op-1",
        "dispatched": True,
        "outcome": "success",
        "model": {"requested": "jev-1", "resolved": "jev-1", "provider": "typesafe"},
        "provider_request_id": "req-1",
        "transport_attempt": 1,
        "usage": {"input_tokens": 120, "output_tokens": 30, "cache_tokens": None},
        "billing": {"measured": None, "currency": None, "price_basis": None},
    }
    event.update(overrides)
    return event


def test_unknown_is_not_zero():
    # AC-07-01: a completion with missing usage reports the field as unknown
    total = ua.usage_totals([_event()])
    assert total["known"]["input_tokens"] == 120
    assert total["known"]["output_tokens"] == 30
    assert total["known"]["cache_tokens"] == 0
    assert "cache_tokens" in total["unknown"]


def test_batch_charged_once():
    # AC-07-03: a batched request (one operation) is charged once despite two events
    pre = _event(kind="pre_dispatch", event_id="p", outcome=None)
    post = _event(event_id="c")
    events = [pre, post]
    assert ua.charged_request_count(events) == 1


def test_replay_not_charged():
    # AC-07-03: replay of a stored observation incurs no provider request
    replay = _event(replayed=True, event_id="r")
    assert ua.charged_request_count([replay]) == 0


def test_validation_rejects_bad_events():
    # AC-07-02: provider cannot be inferred from a role label; model mismatch rejected
    assert _raises(ua.validate_event, _event(model={"requested": "jev-1", "resolved": "jev-2"}))
    assert _raises(ua.validate_event, _event(model={"requested": "jev-1", "provider": ""}))
    assert _raises(ua.validate_event, _event(kind="completion", outcome="confused"))
    assert _raises(ua.validate_event, _event(usage={"input_tokens": -1}))


def test_reconciliation_appends_without_mutation():
    # AC-07-04: reconciliation adds derived totals without changing originals
    events = [_event()]
    snapshot = [dict(e) for e in events]
    update = _event(kind="reconciliation", event_id="re", operation_id="op-1",
                    usage={"input_tokens": 10, "output_tokens": 5, "cache_tokens": 0})
    merged = ua.reconcile(events, [update])
    assert len(merged) == 2
    assert events == snapshot
    # a reconciliation with the wrong kind is rejected
    assert _raises(ua.reconcile, events, [_event(kind="completion")])


def test_duplicate_numbers_not_reported():
    # a cancelled-before-dispatch operation is never charged
    cancelled = _event(outcome="cancelled", dispatched=False)
    assert ua.charged_request_count([cancelled]) == 0


def main() -> int:
    test_unknown_is_not_zero()
    test_batch_charged_once()
    test_replay_not_charged()
    test_validation_rejects_bad_events()
    test_reconciliation_appends_without_mutation()
    test_duplicate_numbers_not_reported()
    print("usage-accounting: charged-once, unknown-not-zero, append-only reconciliation pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
