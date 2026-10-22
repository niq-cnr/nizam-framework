"""Cohort economics and honest measurement labeling (JR-08).

Computes cost per independently accepted change from a preregistered cohort,
keeping the numerator and denominator honest:

- the numerator includes every attributed provider attempt, fallback, retry and
  rework, plus failed and abandoned work;
- the denominator deduplicates accepted identity and only counts distinct,
  independently accepted changes;
- a zero accepted-change denominator is ``undefined``, never zero cost and never
  a fabricated saving;
- absent usage is ``unknown`` and is reported separately from known totals.

It also encodes the corrected historical measurement labels so that supplied
cost units, seeded fixtures and local command timing can never be re-minted as
measured end-to-end LLM savings.
"""

from __future__ import annotations

from typing import Any

EVIDENCE_CLASSES = (
    "inspected_source",
    "pr_reported",
    "synthetic_fixture",
    "local_conformance",
    "actual_host_isolation",
    "actual_provider_observation",
    "exact_stored_replay",
    "independently_adjudicated_semantic_quality",
    "operational_comparison",
    "release_install_identity",
    "real_consumer_migration",
    "staged_operation",
)

COST_SOURCES = (
    "provider_measured",   # report the provider's own billing measurement
    "price_derived",       # derived from a dated token/price basis
    "reviewer_time",       # human/agent reviewer effort, reported separately
    "setup_maintenance",   # harness/setup/maintenance overhead, reported separately
    "shadow",              # shadow/counterfactual cost, never realized savings
    "realized",            # an observed operational cost
    "unknown",             # usage that is unavailable
)

# Historical corrections, preserved verbatim from the mandate measurement policy.
CORRECTED_HISTORICAL_CLAIMS = (
    "The 61.1% and 45.1% figures were supplied-unit / local-study results, not measured end-to-end LLM savings.",
    "Seeded blockers were not independent defect discoveries.",
    "Local shell timing was not provider latency.",
)


class EconomicsError(ValueError):
    """A cohort economics computation is asked to fabricate a number."""


def distinct_accepted_changes(accepted: list[str]) -> list[str]:
    """Deduplicate accepted identity; a superseding change is handled by the caller."""
    seen: list[str] = []
    for identity in accepted:
        if identity not in seen:
            seen.append(identity)
    return seen


def cost_per_accepted_change(attributed_cost: float, accepted: list[str]) -> dict[str, Any]:
    """Ratio of all attributed cost to distinct independently accepted changes.

    Returns ``ratio`` only when the denominator is non-empty; otherwise
    ``undefined`` is true and the ratio is explicitly not a number.
    """
    if attributed_cost < 0:
        raise EconomicsError("attributed cost cannot be negative")
    distinct = distinct_accepted_changes(accepted)
    if not distinct:
        return {"ratio": None, "undefined": True, "accepted_changes": 0}
    return {
        "ratio": attributed_cost / len(distinct),
        "undefined": False,
        "accepted_changes": len(distinct),
        "accepted_identities": distinct,
    }


def aggregate_cost_sources(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum known monetary sources and report unknown/shadow coverage separately.

    ``unknown`` costs are never folded into zero, and shadow costs are reported
    separately so they can never be presented as realized workflow savings.
    """
    known = 0.0
    unknown: list[str] = []
    shadow = 0.0
    for source in sources:
        kind = source.get("kind")
        amount = source.get("amount")
        if kind not in COST_SOURCES:
            raise EconomicsError(f"unknown cost source kind {kind!r}")
        if amount is None:
            if kind == "unknown":
                unknown.append(source.get("label", kind))
            continue
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0:
            raise EconomicsError("cost amount must be a non-negative number or absent/unknown")
        if kind == "shadow":
            shadow += amount
        else:
            known += amount
    return {
        "known_total": known,
        "unknown_labels": unknown,
        "unknown_coverage": bool(unknown),
        "shadow_total": shadow,
    }


def is_realized_saving(source_kind: str) -> bool:
    """Only an observed operational cost can support a realized-saving claim."""
    return source_kind == "realized"
