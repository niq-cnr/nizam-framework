"""Adversarial tests for cohort economics (JR-08)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cohort_economics as ce  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ce.EconomicsError:
        return True
    return False


def test_zero_denominator_is_undefined_not_zero():
    # AC-08-05: no accepted change -> undefined, never zero cost or a saving
    result = ce.cost_per_accepted_change(42.0, [])
    assert result["undefined"] is True
    assert result["ratio"] is None


def test_duplicate_acceptance_does_not_inflate_denominator():
    # AC-08-02: duplicate reports deduplicate; denominator is distinct identity
    result = ce.cost_per_accepted_change(10.0, ["change-a", "change-a", "change-b"])
    assert result["accepted_changes"] == 2
    assert result["ratio"] == 5.0


def test_unknown_cost_is_not_zero():
    # AC-08-03: unknown charges are reported separately, never folded into zero
    result = ce.aggregate_cost_sources([
        {"kind": "provider_measured", "amount": 1.5, "label": "billing"},
        {"kind": "unknown", "amount": None, "label": "timeout-cost"},
        {"kind": "shadow", "amount": 2.0, "label": "counterfactual"},
    ])
    assert result["known_total"] == 1.5
    assert result["unknown_coverage"] is True
    assert "timeout-cost" in result["unknown_labels"]
    assert result["shadow_total"] == 2.0


def test_shadow_is_not_realized_saving():
    # AC-08-04: shadow/counterfactual cost can never back a realized-saving claim
    assert ce.is_realized_saving("shadow") is False
    assert ce.is_realized_saving("realized") is True


def test_validation_rejects_bad_amounts():
    assert _raises(ce.aggregate_cost_sources, [{"kind": "provider_measured", "amount": -1}])
    assert _raises(ce.aggregate_cost_sources, [{"kind": "made_up", "amount": 1}])
    assert _raises(ce.cost_per_accepted_change, -5.0, ["a"])


def test_corrected_historical_claims_present():
    # AC-08-01: the historical figures are labeled supplied-unit / local-study
    assert any("61.1%" in c and "not measured end-to-end" in c for c in ce.CORRECTED_HISTORICAL_CLAIMS)
    assert any("Seeded blockers were not independent" in c for c in ce.CORRECTED_HISTORICAL_CLAIMS)
    assert any("Local shell timing was not provider latency" in c for c in ce.CORRECTED_HISTORICAL_CLAIMS)


def main() -> int:
    test_zero_denominator_is_undefined_not_zero()
    test_duplicate_acceptance_does_not_inflate_denominator()
    test_unknown_cost_is_not_zero()
    test_shadow_is_not_realized_saving()
    test_validation_rejects_bad_amounts()
    test_corrected_historical_claims_present()
    print("cohort-economics: undefined-zero-demoninator, dedup, unknown-and-shadow separation pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
