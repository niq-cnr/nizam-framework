"""Provider-attempt event accounting (JR-07).

Records the real boundary of every governed provider/model call with explicit
unknowns, and computes honest totals from the retained events. Rules enforced
here match the mandate (section 8):

- A batched request is charged once; per-question allocation is an estimate.
- Absent usage is ``unknown``, never zero.
- A replay reads a stored observation and incurs no provider request; a fresh
  inference is a new charged request.
- Partial billing reconciliation appends derived totals without deleting the
  original events or double-counting.
- Provider identity is never inferred from a role label; it is explicitly
  recorded or unknown.
"""

from __future__ import annotations

from typing import Any

EVENT_KINDS = ("pre_dispatch", "completion", "reconciliation")
OUTCOMES = ("success", "failed", "timeout", "cancelled", "unknown")

USAGE_FIELDS = ("input_tokens", "output_tokens", "cache_tokens")


class UsageError(ValueError):
    """A provider-attempt event is malformed or contradictory."""


def validate_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise UsageError("event must be an object")
    if event.get("schema_version") != 1:
        raise UsageError(f"unsupported event schema_version {event.get('schema_version')!r}")
    kind = event.get("kind")
    if kind not in EVENT_KINDS:
        raise UsageError(f"unsupported event kind {kind!r}")
    if not isinstance(event.get("operation_id"), str) or not event["operation_id"].strip():
        raise UsageError("event.operation_id must be a non-empty string")
    outcome = event.get("outcome")
    if kind == "completion" and outcome not in OUTCOMES:
        raise UsageError(f"completion event has unsupported outcome {outcome!r}")

    model = event.get("model")
    if not isinstance(model, dict):
        raise UsageError("event.model must be an object")
    if not isinstance(model.get("requested"), str) or not model["requested"].strip():
        raise UsageError("event.model.requested must be a non-empty exact model identity")
    if model.get("resolved") is not None and model.get("resolved") != model["requested"]:
        raise UsageError(
            f"resolved model {model.get('resolved')!r} does not match requested {model['requested']!r}"
        )
    # provider identity is explicit or unknown, never inferred from a role label
    provider = model.get("provider")
    if provider is not None and (not isinstance(provider, str) or not provider.strip()):
        raise UsageError("event.model.provider must be a non-empty string or absent/unknown")

    usage = event.get("usage")
    if usage is not None:
        if not isinstance(usage, dict):
            raise UsageError("event.usage must be an object")
        for field in USAGE_FIELDS:
            value = usage.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise UsageError(f"usage.{field} must be a non-negative integer or null/absent")
    return event


def _is_charged(event: dict[str, Any]) -> bool:
    """A request is charged when a transport call was actually attempted."""
    if event.get("kind") == "reconciliation":
        return False
    if event.get("replayed") is True:
        return False
    return bool(event.get("dispatched"))


def charged_request_count(events: list[dict[str, Any]]) -> int:
    """Number of distinct operations that incurred an actual provider request.

    Deduplicates by operation id: a pre_dispatch/completion pair for the same
    operation is one request. A batched request is one operation, charged once.
    """
    charged: set[str] = set()
    for event in events:
        validate_event(event)
        if _is_charged(event):
            charged.add(event["operation_id"])
    return len(charged)


def unknown_usage_fields(events: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Map operation id -> usage fields that are unknown (absent or null)."""
    unknown: dict[str, set[str]] = {}
    for event in events:
        if event.get("kind") == "reconciliation":
            continue
        usage = event.get("usage") or {}
        missing = {field for field in USAGE_FIELDS if usage.get(field) is None}
        if missing:
            unknown.setdefault(event["operation_id"], set()).update(missing)
    return unknown


def usage_totals(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum known usage and report which fields remain unknown.

    Unknown fields are reported explicitly and are never folded into zero.
    """
    totals = {field: 0 for field in USAGE_FIELDS}
    unknown: set[str] = set()
    for event in events:
        if event.get("kind") == "reconciliation":
            continue
        usage = event.get("usage") or {}
        for field in USAGE_FIELDS:
            value = usage.get(field)
            if value is None:
                unknown.add(field)
            else:
                totals[field] += value
    return {
        "known": totals,
        "unknown": sorted(unknown),
        "charged_requests": charged_request_count(events),
    }


def reconcile(events: list[dict[str, Any]], updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the original events plus reconciliation records, unchanged and unmutated.

    Reconciliation events carry the derived totals without touching the retained
    originals, so later billing updates can be appended without double-counting.
    """
    for update in updates:
        validate_event(update)
        if update.get("kind") != "reconciliation":
            raise UsageError("reconciliation updates must use kind 'reconciliation'")
    return list(events) + list(updates)
