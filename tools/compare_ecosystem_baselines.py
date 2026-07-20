#!/usr/bin/env python3
"""compare_ecosystem_baselines.py -- Deterministic Compare-stage delta tool.

Implements the mechanizable slice of ``ecosystem/07_progress_comparison.md``:
given two already-approved audits (their ``findings.json`` arrays) and the two
baselines that anchor them, it classifies every finding into exactly one of the
five transition classes (Sec 3) and emits the schema-valid delta artifact
(``schema/audit_delta.schema.json``) at ``<output-dir>/delta.json``.

Deterministic classification (no judgement invented -- every class follows from
the two inputs plus the prior delta):

- ``new`` -- in the later audit, absent from the earlier one, not previously
  resolved.
- ``resolved`` -- open in the earlier audit and recorded ``resolved`` (with
  closure evidence) in the later one, within this window. The
  closure-only-with-evidence rule (Sec 4) is enforced: a finding merely ABSENT
  from the later audit is NOT auto-resolved -- absence alone is consistent with
  the scan simply not looking. Such a finding is reported as UNCLASSIFIABLE
  (exit 1), so the auditor must carry a resolved-with-evidence entry rather than
  let the tool guess.
- ``reopened`` -- previously classified ``resolved`` (via ``--prior-delta``),
  present and open again. Necessarily empty on a first comparison (Sec 3.2,
  when ``--prior-delta`` is omitted).
- ``persisting`` -- open on both sides with CURRENT evidence, freshly
  re-confirmed at or after the later anchor (delegated to
  ``validate_evidence_freshness.finding_is_fresh``).
- ``stale`` -- open on both sides but the backing evidence is no longer current
  (Sec 5): not silently carried forward as if re-confirmed.

Pre-window-resolved findings (Sec 3.1 -- resolved before the earlier anchor) are
recorded under ``pre_window_resolved`` with their closure evidence, excluded from
the five-class taxonomy and from the open-findings score. The open-findings
count (Sec 6.1) counts ``open`` findings only, and ``score_movement`` cites the
new/resolved/reopened/stale ids responsible (never ``persisting``, Sec 6).

Exit codes
----------
    0   OK -- delta.json was written, schema-valid.
    1   COMPARISON_INVALID -- the inputs cannot be validly classified: an
        earlier-open finding vanished from the later audit with no closure
        evidence (Sec 3/4), or a resolved finding carries no closure evidence,
        or a findings payload is not a top-level array. No delta is written.
    64  Usage error -- missing/invalid arguments, unreadable inputs, or a
        baseline from which no reference point can be derived.

Example
-------
    python3 tools/compare_ecosystem_baselines.py \\
        --audit-id audit-2026-07-20-abc1234 \\
        --output-dir /tmp/compare-out \\
        --earlier-findings .agent/audits/audit-A/findings.json \\
        --later-findings   .agent/audits/audit-B/findings.json \\
        --earlier-baseline .agent/reconciliation/exec-A/baseline.json \\
        --later-baseline   .agent/reconciliation/exec-B/baseline.json \\
        --prior-delta      .agent/audits/audit-A/delta.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Sequence

# The freshness rule lives in the sibling tool so it is defined once and shared.
# A script's own directory is sys.path[0], so this resolves when the tool is run
# as `python3 tools/compare_ecosystem_baselines.py`; the explicit insert makes it
# resolve under import/`-m` contexts and the injected bootstrap payload too
# (bootstrap injects the whole tools/ directory, so the two travel together).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_evidence_freshness import finding_is_fresh  # noqa: E402

EXIT_OK = 0
EXIT_COMPARISON_INVALID = 1
EXIT_USAGE_ERROR = 64


class CompareUsageError(Exception):
    """Raised for a malformed CLI invocation; the caller maps this to exit 64."""


class _UsageErrorArgumentParser(argparse.ArgumentParser):
    """An ``argparse.ArgumentParser`` whose ``error()`` raises, not exits."""

    def error(self, message: str) -> None:  # noqa: D102 - argparse override
        raise CompareUsageError(message)


def _is_nonempty_str(value: object) -> bool:
    """Return True iff ``value`` is a non-empty string."""
    return isinstance(value, str) and bool(value)


def load_json_document(path: str, flag: str) -> object:
    """Load and JSON-parse ``path``; raise :class:`CompareUsageError` on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as error:
        raise CompareUsageError(f"{flag} could not be read: {error}")
    except json.JSONDecodeError as error:
        raise CompareUsageError(f"{flag} is not valid JSON: {error}")


def resolve_reference_point(baseline: object, flag: str) -> dict[str, str]:
    """Derive an audit_delta reference point ``{id, revision, timestamp}`` from a baseline.

    Maps ``execution_id`` -> id and ``captured_at`` -> timestamp, and takes the
    revision from the first ``repository_references`` entry (falling back to
    ``framework_references``). A baseline from which no revision, id, or timestamp
    can be derived is a usage error -- the reference point must be unambiguously
    anchored (ecosystem/02_evidence_baseline.md Sec 4), never fabricated.
    """
    if not isinstance(baseline, dict):
        raise CompareUsageError(f"{flag} is not a JSON object (a baseline artifact)")
    execution_id = baseline.get("execution_id")
    captured_at = baseline.get("captured_at")
    if not _is_nonempty_str(execution_id):
        raise CompareUsageError(f"{flag} has no non-empty 'execution_id'")
    if not _is_nonempty_str(captured_at):
        raise CompareUsageError(f"{flag} has no non-empty 'captured_at' timestamp")

    revision = None
    for category in ("repository_references", "framework_references"):
        references = baseline.get(category)
        if isinstance(references, list):
            for item in references:
                if isinstance(item, dict) and _is_nonempty_str(item.get("revision")):
                    revision = item["revision"]
                    break
        if revision is not None:
            break
    if revision is None:
        raise CompareUsageError(
            f"{flag} carries no revision in repository_references or "
            "framework_references -- a reference point cannot be anchored"
        )
    return {"id": execution_id, "revision": revision, "timestamp": captured_at}


def index_findings(findings: object, flag: str) -> dict[str, dict]:
    """Return an ``{id: finding}`` index; raise on a non-array or duplicate/blank id."""
    if not isinstance(findings, list):
        raise CompareUsageError(f"{flag} must be a top-level JSON array of findings")
    index: dict[str, dict] = {}
    for entry in findings:
        if not isinstance(entry, dict):
            raise CompareUsageError(f"{flag} contains a non-object finding entry")
        finding_id = entry.get("id")
        if not _is_nonempty_str(finding_id):
            raise CompareUsageError(f"{flag} contains a finding with no non-empty 'id'")
        if finding_id in index:
            raise CompareUsageError(f"{flag} contains a duplicate finding id '{finding_id}'")
        index[finding_id] = entry
    return index


def prior_resolved_ids(prior_delta: object) -> set[str]:
    """Return the set of finding ids a prior delta classified resolved (or pre-window).

    ``reopened`` requires a prior comparison's ``resolved`` classification to
    reopen against (Sec 3, Sec 3.2). Both the in-window ``resolved`` bucket and
    the ``pre_window_resolved`` list count as prior resolutions.
    """
    resolved: set[str] = set()
    if not isinstance(prior_delta, dict):
        return resolved
    transitions = prior_delta.get("transitions")
    if isinstance(transitions, dict):
        for item in transitions.get("resolved", []) or []:
            if isinstance(item, dict) and _is_nonempty_str(item.get("id")):
                resolved.add(item["id"])
    for item in prior_delta.get("pre_window_resolved", []) or []:
        if isinstance(item, dict) and _is_nonempty_str(item.get("id")):
            resolved.add(item["id"])
    return resolved


def _nonempty_closure(finding: dict) -> list | None:
    """Return a finding's closure_evidence iff it is a non-empty list, else None."""
    closure = finding.get("closure_evidence")
    if isinstance(closure, list) and closure:
        return closure
    return None


def classify(
    earlier: dict[str, dict],
    later: dict[str, dict],
    later_ref: dict[str, str],
    prior_resolved: set[str],
) -> tuple[dict, list, list[str]]:
    """Classify every finding into the five-class taxonomy plus pre_window_resolved.

    Returns ``(transitions, pre_window_resolved, problems)``. ``problems`` is
    non-empty when the inputs cannot be validly classified (an earlier-open
    finding gone from the later audit with no closure evidence, Sec 3/4; or a
    resolved finding missing its closure evidence). Each bucket is sorted by id
    for deterministic output.
    """
    new_b: list[dict] = []
    resolved_b: list[dict] = []
    reopened_b: list[dict] = []
    persisting_b: list[dict] = []
    stale_b: list[dict] = []
    pre_window: list[dict] = []
    problems: list[str] = []

    for finding_id in sorted(set(earlier) | set(later)):
        e = earlier.get(finding_id)
        l = later.get(finding_id)
        e_status = e.get("status") if e else None

        if l is not None:
            if l.get("status") == "resolved":
                closure = _nonempty_closure(l)
                if closure is None:
                    problems.append(
                        f"finding '{finding_id}': recorded resolved in the later audit "
                        "with no closure_evidence (closure-only-with-evidence, Sec 4)"
                    )
                    continue
                item = {"id": finding_id, "closure_evidence": closure}
                if e is not None and e_status == "open":
                    resolved_b.append(item)          # in-window resolution (Sec 3)
                else:
                    pre_window.append(item)          # resolved outside the window (Sec 3.1)
            else:  # open in the later audit
                if e is not None:
                    if finding_is_fresh(l, later_ref["revision"], later_ref["timestamp"]):
                        persisting_b.append({"id": finding_id, "evidence": l.get("evidence", [])})
                    else:
                        stale_b.append({"id": finding_id})
                elif finding_id in prior_resolved:
                    reopened_b.append({"id": finding_id})
                else:
                    new_b.append({"id": finding_id})
        else:  # absent from the later audit
            if e_status == "resolved":
                closure = _nonempty_closure(e)
                if closure is None:
                    problems.append(
                        f"finding '{finding_id}': resolved in the earlier audit with no "
                        "closure_evidence (Sec 4)"
                    )
                    continue
                pre_window.append({"id": finding_id, "closure_evidence": closure})
            else:
                problems.append(
                    f"finding '{finding_id}': open in the earlier audit but absent from the "
                    "later one with no closure evidence -- absence alone does not resolve a "
                    "finding (Sec 4); carry a resolved-with-evidence entry or keep it open"
                )

    transitions = {
        "new": new_b,
        "resolved": resolved_b,
        "reopened": reopened_b,
        "persisting": persisting_b,
        "stale": stale_b,
    }
    return transitions, pre_window, problems


def count_open(index: dict[str, dict]) -> int:
    """Return the number of findings in ``open`` status (Sec 6.1: open only)."""
    return sum(1 for finding in index.values() if finding.get("status") == "open")


def build_delta(
    earlier_ref: dict[str, str],
    later_ref: dict[str, str],
    transitions: dict,
    pre_window: list,
    earlier: dict[str, dict],
    later: dict[str, dict],
) -> dict:
    """Assemble the audit_delta document (schema/audit_delta.schema.json shape)."""
    earlier_open = count_open(earlier)
    later_open = count_open(later)
    cited = sorted(
        item["id"]
        for bucket in ("new", "resolved", "reopened", "stale")
        for item in transitions[bucket]
    )
    delta: dict = {
        "earlier": earlier_ref,
        "later": later_ref,
        "transitions": transitions,
        "score_movement": {
            "earlier_open_score": earlier_open,
            "later_open_score": later_open,
            "cited_findings": cited,
            "note": "persisting findings are carried, never cited as score movement (Sec 6).",
        },
        "open_findings_count": {"earlier": earlier_open, "later": later_open},
    }
    if pre_window:
        delta["pre_window_resolved"] = sorted(pre_window, key=lambda item: item["id"])
    return delta


def write_json_document(path: str, document: object) -> None:
    """Write ``document`` to ``path`` as indented JSON with a trailing newline."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")


def write_compare_log(output_dir: str, audit_id: str, delta: dict) -> None:
    """Write the run's plain-text evidence log to ``output_dir/compare-log.txt``."""
    transitions = delta["transitions"]
    lines = [
        f"compare_ecosystem_baselines.py compare log -- audit_id={audit_id}",
        f"earlier={delta['earlier']}",
        f"later={delta['later']}",
        *(f"{name}={[i['id'] for i in transitions[name]]}" for name in
          ("new", "resolved", "reopened", "persisting", "stale")),
        f"pre_window_resolved={[i['id'] for i in delta.get('pre_window_resolved', [])]}",
        f"open_findings_count={delta['open_findings_count']}",
    ]
    with open(os.path.join(output_dir, "compare-log.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def build_argument_parser() -> _UsageErrorArgumentParser:
    """Construct this CLI's argument parser."""
    parser = _UsageErrorArgumentParser(
        prog="compare_ecosystem_baselines.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--audit-id", required=True, help="Identifier for the comparison execution.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where delta.json / compare-log.txt are written (created if absent).",
    )
    parser.add_argument("--earlier-findings", required=True, help="Earlier audit findings.json (array).")
    parser.add_argument("--later-findings", required=True, help="Later audit findings.json (array).")
    parser.add_argument("--earlier-baseline", required=True, help="Earlier baseline.json (anchors the earlier reference point).")
    parser.add_argument("--later-baseline", required=True, help="Later baseline.json (anchors the later reference point + freshness).")
    parser.add_argument(
        "--prior-delta",
        default=None,
        help="Optional prior delta.json; supplies the previously-resolved set for reopened detection. "
        "Omit for a first comparison (reopened is then necessarily empty, Sec 3.2).",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    """Run the CLI and return its process exit code (see the module docstring's table)."""
    parser = build_argument_parser()
    try:
        args = parser.parse_args(list(argv))
        earlier_findings = load_json_document(args.earlier_findings, "--earlier-findings")
        later_findings = load_json_document(args.later_findings, "--later-findings")
        earlier_baseline = load_json_document(args.earlier_baseline, "--earlier-baseline")
        later_baseline = load_json_document(args.later_baseline, "--later-baseline")
        prior_delta = load_json_document(args.prior_delta, "--prior-delta") if args.prior_delta else None
        earlier_ref = resolve_reference_point(earlier_baseline, "--earlier-baseline")
        later_ref = resolve_reference_point(later_baseline, "--later-baseline")
        earlier = index_findings(earlier_findings, "--earlier-findings")
        later = index_findings(later_findings, "--later-findings")
    except CompareUsageError as usage_error:
        print(f"usage error: {usage_error}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    transitions, pre_window, problems = classify(
        earlier, later, later_ref, prior_resolved_ids(prior_delta)
    )
    if problems:
        print(f"COMPARISON INVALID: {len(problems)} unclassifiable finding(s); no delta written")
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return EXIT_COMPARISON_INVALID

    delta = build_delta(earlier_ref, later_ref, transitions, pre_window, earlier, later)
    os.makedirs(args.output_dir, exist_ok=True)
    write_json_document(os.path.join(args.output_dir, "delta.json"), delta)
    write_compare_log(args.output_dir, args.audit_id, delta)

    counts = {name: len(transitions[name]) for name in transitions}
    print(
        "DELTA WRITTEN: "
        + ", ".join(f"{name} {counts[name]}" for name in
                    ("new", "resolved", "reopened", "persisting", "stale"))
        + f", pre_window_resolved {len(pre_window)} -> "
        + os.path.join(args.output_dir, "delta.json")
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
