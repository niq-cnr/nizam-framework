#!/usr/bin/env python3
"""validate_evidence_freshness.py -- Deterministic evidence-freshness check.

Implements the mechanizable core of ``ecosystem/07_progress_comparison.md``
Sec 5 (Stale-Evidence Non-Reuse Rule): evidence backing a finding still present
in the later execution MUST NOT be silently reused as CURRENT evidence once it
is genuinely stale relative to the later execution's own revision and timestamp
anchors (``ecosystem/02_evidence_baseline.md`` Sec 4). A finding whose only
backing evidence predates the later execution, with no fresh confirmation
captured at or after that execution, is stale.

The freshness rule this module defines is used two ways:

- as a library: ``evidence_is_fresh(...)`` and ``finding_is_fresh(...)`` are
  imported by ``tools/compare_ecosystem_baselines.py`` to split both-sides
  findings into ``persisting`` (fresh) vs ``stale`` (not fresh).
- as a CLI: run against an audit's ``findings.json`` and a later reference
  point to report which findings carry stale evidence.

FRESHNESS RULE (deterministic, no network, no git). One evidence item is
CURRENT iff it was demonstrably captured at or after the later reference point:
either it carries a ``timestamp`` at or after the anchor timestamp (ISO-8601
UTC ``...Z`` strings compare lexically), or its ``revision`` equals the anchor
revision (captured at the anchor commit). A finding's evidence is FRESH iff at
least one of its evidence items is current. When freshness cannot be confirmed
the finding is STALE, never optimistically carried forward: Sec 5 is explicit
that a comparison MUST NOT treat the absence of contrary evidence as
confirmation that prior evidence still holds -- the stale classification exists
precisely so that gap is reported, not papered over.

Exit codes
----------
    0   FRESH -- every inspected finding's evidence is current.
    1   STALE -- at least one inspected finding carries only stale evidence.
    64  Usage error -- missing or invalid command-line arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

EXIT_FRESH = 0
EXIT_STALE = 1
EXIT_USAGE_ERROR = 64


class FreshnessUsageError(Exception):
    """Raised for a malformed CLI invocation; the caller maps this to exit 64."""


class _UsageErrorArgumentParser(argparse.ArgumentParser):
    """An ``argparse.ArgumentParser`` whose ``error()`` raises, not exits."""

    def error(self, message: str) -> None:  # noqa: D102 - argparse override
        raise FreshnessUsageError(message)


def _is_nonempty_str(value: object) -> bool:
    """Return True iff ``value`` is a non-empty string."""
    return isinstance(value, str) and bool(value)


def evidence_is_fresh(
    evidence_items: object,
    anchor_revision: str,
    anchor_timestamp: str,
) -> bool:
    """Return True iff at least one evidence item is current at the later anchor.

    An item is current iff it carries a ``timestamp`` at or after
    ``anchor_timestamp`` (ISO-8601 ``...Z`` strings compare lexically), or its
    ``revision`` equals ``anchor_revision``. See the module docstring's FRESHNESS
    RULE. An empty or non-list ``evidence_items`` is not fresh (there is nothing
    current to cite).
    """
    if not isinstance(evidence_items, list):
        return False
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        timestamp = item.get("timestamp")
        if _is_nonempty_str(timestamp) and _is_nonempty_str(anchor_timestamp) and timestamp >= anchor_timestamp:
            return True
        revision = item.get("revision")
        if _is_nonempty_str(revision) and _is_nonempty_str(anchor_revision) and revision == anchor_revision:
            return True
    return False


def finding_is_fresh(finding: object, anchor_revision: str, anchor_timestamp: str) -> bool:
    """Return True iff ``finding``'s evidence is fresh at the later anchor."""
    if not isinstance(finding, dict):
        return False
    return evidence_is_fresh(finding.get("evidence"), anchor_revision, anchor_timestamp)


def load_json_document(path: str, flag: str) -> object:
    """Load and JSON-parse ``path``; raise :class:`FreshnessUsageError` on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as error:
        raise FreshnessUsageError(f"{flag} could not be read: {error}")
    except json.JSONDecodeError as error:
        raise FreshnessUsageError(f"{flag} is not valid JSON: {error}")


def build_argument_parser() -> _UsageErrorArgumentParser:
    """Construct this CLI's argument parser."""
    parser = _UsageErrorArgumentParser(
        prog="validate_evidence_freshness.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--findings",
        required=True,
        help="Path to an audit findings.json (a top-level JSON array of findings).",
    )
    parser.add_argument(
        "--anchor-revision",
        required=True,
        help="The later reference point's revision (evidence at this revision is current).",
    )
    parser.add_argument(
        "--anchor-timestamp",
        required=True,
        help="The later reference point's timestamp (ISO-8601 UTC, e.g. 2026-07-20T00:00:00Z).",
    )
    parser.add_argument(
        "--open-only",
        action="store_true",
        help="Inspect only findings whose status is 'open' (Sec 5 targets carried-forward findings).",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    """Run the CLI and return its process exit code (see the module docstring's table)."""
    parser = build_argument_parser()
    try:
        args = parser.parse_args(list(argv))
        findings = load_json_document(args.findings, "--findings")
    except FreshnessUsageError as usage_error:
        print(f"usage error: {usage_error}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if not isinstance(findings, list):
        print("usage error: --findings must be a top-level JSON array", file=sys.stderr)
        return EXIT_USAGE_ERROR

    stale_ids: list[str] = []
    inspected = 0
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if args.open_only and finding.get("status") != "open":
            continue
        inspected += 1
        if not finding_is_fresh(finding, args.anchor_revision, args.anchor_timestamp):
            stale_ids.append(str(finding.get("id")))

    if stale_ids:
        print(f"STALE: {len(stale_ids)} of {inspected} inspected finding(s) carry only stale evidence")
        for finding_id in stale_ids:
            print(f"  - {finding_id}", file=sys.stderr)
        return EXIT_STALE

    print(f"FRESH: all {inspected} inspected finding(s) carry current evidence")
    return EXIT_FRESH


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
