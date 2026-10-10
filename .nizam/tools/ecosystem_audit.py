#!/usr/bin/env python3
"""ecosystem_audit.py -- Deterministic Ecosystem Engineering Cycle audit assembler.

Implements the mechanizable slice of ``ecosystem/03_engineering_audit.md``:

- Sec 2 (When to Run) -- the evidence-first ENTRY CONDITION. An audit MUST NOT
  begin until a clean-state preflight returned ``PASS`` (or an operator-approved
  ``PASS_WITH_EXCEPTIONS``) and a baseline was captured for the SAME execution.
  This CLI refuses to assemble an audit whose entry conditions are unmet, so a
  speculative audit (Sec 2: "an audit that begins without both inputs is not
  evidence-first, it is speculative") cannot be produced by tooling.
- Sec 7 (Audit Artifact) -- the artifact PRODUCTION. Given auditor-authored
  finding records, this CLI validates each against
  ``schema/engineering_finding.schema.json``'s required shape and the
  no-promotion-beyond-evidence closure rule (Sec 3/5: a ``resolved`` finding
  MUST carry non-empty closure evidence), then emits the canonical, schema-valid
  ``findings.json`` (a top-level array) and a rendered human-readable
  ``report.md``, with raw evidence externalised by path (never inlined).

This CLI is deterministic and makes NO engineering judgement: it does not invent
findings, assign confidence, or assess maturity -- those are the auditor's
(agent's or human's) evidence-first work, supplied via ``--findings-input``. What
it mechanizes is the GATE (Sec 2) and the RULES (Sec 3/5/7) the protocol defines,
exactly as ``ecosystem_preflight.py`` mechanizes the preflight verdict's
clean-state rules rather than the operator's risk judgement. The schema remains
the authoritative contract; this CLI enforces the same rules in the standard
library so it carries no third-party dependency (jsonschema is used only by
``tools/validate.sh``, which independently re-validates the emitted artifact).

Commercial/GA readiness is out of scope here exactly as it is for the protocol
(Sec 6): this CLI scores nothing, it only assembles engineering findings.

Exit codes
----------
This CLI documents its exit codes both here and via ``--help``:

    0   OK -- entry conditions met and every supplied finding is valid.
        findings.json and report.md are written, schema-valid.
    1   FINDINGS_INVALID -- the entry conditions were met, but at least one
        supplied finding violates the engineering-finding schema shape or the
        no-promotion-beyond-evidence closure rule (a resolved finding with no
        closure evidence). No artifact is emitted -- a malformed audit is never
        half-written, exactly as a FAIL preflight never captures a baseline.
    2   ENTRY_CONDITION_UNMET -- the Sec 2 entry conditions are not satisfied:
        the preflight verdict is FAIL, or PASS_WITH_EXCEPTIONS without a
        recorded operator approval, or the baseline is missing/unreadable, or
        the preflight and baseline name different executions. The audit is
        refused; no findings are assembled.
    64  Usage error -- missing or invalid command-line arguments. Distinct from
        every domain exit code (0/1/2) above.

Example
-------
    python3 tools/ecosystem_audit.py \\
        --audit-id audit-2026-07-20-abc1234 \\
        --output-dir /tmp/audit-out \\
        --findings-input /tmp/findings-draft.json \\
        --preflight .agent/reconciliation/exec-1/preflight.json \\
        --baseline  .agent/reconciliation/exec-1/baseline.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Sequence

EXIT_OK = 0
EXIT_FINDINGS_INVALID = 1
EXIT_ENTRY_CONDITION_UNMET = 2
EXIT_USAGE_ERROR = 64

# The finding shape mirrored from schema/engineering_finding.schema.json. Kept in
# lock-step with that schema (the authoritative contract); tools/validate.sh C12
# independently re-validates every emitted finding via jsonschema, so a drift
# between this list and the schema is caught by the self-test, not silently.
REQUIRED_FINDING_KEYS: tuple[str, ...] = (
    "id",
    "severity",
    "confidence",
    "evidence",
    "impact",
    "owner",
    "status",
    "closure_criteria",
)
CONFIDENCE_VOCABULARY: tuple[str, ...] = ("Confirmed", "Probable", "Suspected")
MATURITY_LEVELS: tuple[str, ...] = (
    "Designed",
    "Authored",
    "Implemented",
    "Unit Tested",
    "Integrated",
    "Rendered",
    "Deployed",
    "Exercised",
    "Observable",
    "Production Proven",
)
STATUS_VALUES: tuple[str, ...] = ("open", "resolved")
EVIDENCE_PATH_PREFIX = ".agent/evidence/"

APPROVED_PREFLIGHT_VERDICTS: tuple[str, ...] = ("PASS", "PASS_WITH_EXCEPTIONS")


class AuditUsageError(Exception):
    """Raised for a malformed CLI invocation; the caller maps this to exit 64.

    A custom error class (per the house code-generation standard) rather than a
    bare ``SystemExit`` from argparse, so a usage error is never silently
    conflated with a domain exit code (0/1/2) above -- the same discipline
    ``ecosystem_preflight.py`` follows.
    """


class _UsageErrorArgumentParser(argparse.ArgumentParser):
    """An ``argparse.ArgumentParser`` whose ``error()`` raises, not exits.

    argparse's default ``error()`` calls ``sys.exit(2)`` directly, which would
    collide with this CLI's own domain exit code 2 (ENTRY_CONDITION_UNMET).
    Raising :class:`AuditUsageError` lets the entry point map every malformed
    invocation to the single documented exit code 64.
    """

    def error(self, message: str) -> None:  # noqa: D102 - argparse override
        raise AuditUsageError(message)


def read_utc_now() -> datetime.datetime:
    """Return the current time as a single, timezone-aware UTC clock read.

    Called exactly once per invocation (methodology/04_tool_driven_state.md's
    Clock-Read Timestamps rule) so every timestamp a single run emits is
    mutually consistent.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def format_iso8601(moment: datetime.datetime) -> str:
    """Format a timezone-aware UTC datetime as a ``YYYY-MM-DDTHH:MM:SSZ`` string."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json_document(path: str, flag: str) -> object:
    """Load and JSON-parse ``path``; raise :class:`AuditUsageError` on failure.

    A missing file or unparseable JSON on a caller-supplied input is a usage
    error (exit 64), never a silently fabricated or empty document.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as error:
        raise AuditUsageError(f"{flag} could not be read: {error}")
    except json.JSONDecodeError as error:
        raise AuditUsageError(f"{flag} is not valid JSON: {error}")


def _is_nonempty_str(value: object) -> bool:
    """Return True iff ``value`` is a non-empty string."""
    return isinstance(value, str) and bool(value)


def validate_evidence_item(item: object, label: str) -> list[str]:
    """Return schema violations for one evidence/closure-evidence item.

    Mirrors ``schema/engineering_finding.schema.json`` ``$defs/evidence_item``:
    a ``path`` (non-empty, beginning ``.agent/evidence/``) and a ``revision``
    (non-empty). Raw evidence is referenced by path, never inlined
    (methodology/04_tool_driven_state.md Sec 5).
    """
    problems: list[str] = []
    if not isinstance(item, dict):
        return [f"{label}: evidence item is not an object"]
    path = item.get("path")
    revision = item.get("revision")
    if not _is_nonempty_str(path):
        problems.append(f"{label}: evidence item 'path' missing or empty")
    elif not path.startswith(EVIDENCE_PATH_PREFIX):
        problems.append(
            f"{label}: evidence path '{path}' must begin with '{EVIDENCE_PATH_PREFIX}' "
            "(evidence is externalised by path, ecosystem/03_engineering_audit.md Sec 7)"
        )
    if not _is_nonempty_str(revision):
        problems.append(f"{label}: evidence item 'revision' missing or empty")
    return problems


def validate_finding(finding: object, index: int) -> list[str]:
    """Return a list of schema/protocol violations for one finding (empty == valid).

    Enforces the required shape of ``schema/engineering_finding.schema.json`` and
    the no-promotion-beyond-evidence closure rule (ecosystem/03_engineering_audit.md
    Sec 3/5): a ``resolved`` finding MUST carry a non-empty ``closure_evidence``;
    an ``open`` finding MUST NOT. severity is a free string (Sec 1: consumers
    extend severity), while confidence is the protocol's closed vocabulary.
    """
    label = f"finding[{index}]"
    if not isinstance(finding, dict):
        return [f"{label}: not a JSON object"]

    finding_id = finding.get("id")
    if _is_nonempty_str(finding_id):
        label = f"finding '{finding_id}'"

    problems: list[str] = []
    for key in REQUIRED_FINDING_KEYS:
        if key not in finding:
            problems.append(f"{label}: missing required key '{key}'")

    for key in ("id", "severity", "impact", "owner", "closure_criteria"):
        if key in finding and not _is_nonempty_str(finding.get(key)):
            problems.append(f"{label}: '{key}' must be a non-empty string")

    confidence = finding.get("confidence")
    if "confidence" in finding and confidence not in CONFIDENCE_VOCABULARY:
        problems.append(
            f"{label}: confidence '{confidence}' is not one of "
            f"{list(CONFIDENCE_VOCABULARY)} (ecosystem/03_engineering_audit.md Sec 5)"
        )

    maturity = finding.get("maturity")
    if "maturity" in finding and maturity not in MATURITY_LEVELS:
        problems.append(
            f"{label}: maturity '{maturity}' is not one of the ten levels "
            f"{list(MATURITY_LEVELS)} (ecosystem/03_engineering_audit.md Sec 4)"
        )

    status = finding.get("status")
    if "status" in finding and status not in STATUS_VALUES:
        problems.append(f"{label}: status '{status}' is not one of {list(STATUS_VALUES)}")

    evidence = finding.get("evidence")
    if "evidence" in finding:
        if not isinstance(evidence, list) or not evidence:
            problems.append(f"{label}: 'evidence' must be a non-empty array")
        else:
            for item in evidence:
                problems.extend(validate_evidence_item(item, f"{label} evidence"))

    # No-promotion-beyond-evidence closure rule (schema allOf; protocol Sec 3/5).
    closure_evidence = finding.get("closure_evidence")
    if status == "resolved":
        if not isinstance(closure_evidence, list) or not closure_evidence:
            problems.append(
                f"{label}: status 'resolved' requires a non-empty 'closure_evidence' "
                "(closure-only-with-evidence, ecosystem/03_engineering_audit.md Sec 3/5)"
            )
        else:
            for item in closure_evidence:
                problems.extend(validate_evidence_item(item, f"{label} closure_evidence"))
    elif closure_evidence is not None:
        # An open finding carrying closure_evidence contradicts its own status.
        problems.append(
            f"{label}: an 'open' finding must not carry 'closure_evidence' "
            "(closure evidence is recorded only when a finding is resolved)"
        )

    return problems


def validate_findings(findings: object) -> tuple[list[dict], list[str]]:
    """Validate the auditor-supplied findings payload.

    Returns ``(findings_list, problems)``. The payload MUST be a top-level JSON
    array (the shape ecosystem/03_engineering_audit.md Sec 7 and the shipped
    dogfood ``findings.json`` use). ``id`` values MUST be unique so findings can
    be matched across executions by the Compare step
    (ecosystem/07_progress_comparison.md).
    """
    if not isinstance(findings, list):
        return [], ["--findings-input must be a top-level JSON array of finding objects"]
    if not findings:
        return [], ["--findings-input array is empty; an audit records at least one finding"]

    problems: list[str] = []
    seen_ids: dict[str, int] = {}
    for index, finding in enumerate(findings):
        problems.extend(validate_finding(finding, index))
        if isinstance(finding, dict) and _is_nonempty_str(finding.get("id")):
            finding_id = finding["id"]
            if finding_id in seen_ids:
                problems.append(
                    f"finding '{finding_id}': duplicate id (also finding[{seen_ids[finding_id]}]); "
                    "finding ids must be unique within an audit"
                )
            else:
                seen_ids[finding_id] = index
    return [f for f in findings if isinstance(f, dict)], problems


def check_entry_conditions(preflight: object, baseline: object) -> list[str]:
    """Return the reasons the Sec 2 evidence-first entry conditions are unmet.

    An audit may proceed only from a ``PASS`` (or operator-approved
    ``PASS_WITH_EXCEPTIONS``) preflight verdict AND a baseline captured for the
    SAME execution (ecosystem/03_engineering_audit.md Sec 2;
    ecosystem/01_clean_state_preflight.md Sec 3/5). An empty return means the
    conditions are satisfied.
    """
    problems: list[str] = []

    if not isinstance(preflight, dict):
        problems.append("--preflight is not a JSON object (a preflight verdict artifact)")
        preflight = {}
    if not isinstance(baseline, dict):
        problems.append("--baseline is not a JSON object (a baseline artifact)")
        baseline = {}

    verdict = preflight.get("verdict")
    if verdict not in APPROVED_PREFLIGHT_VERDICTS:
        problems.append(
            f"preflight verdict is '{verdict}', not PASS or an approved "
            "PASS_WITH_EXCEPTIONS -- an audit is never run from a FAIL or an "
            "unresolved PASS_WITH_EXCEPTIONS (ecosystem/01_clean_state_preflight.md Sec 3)"
        )
    elif verdict == "PASS_WITH_EXCEPTIONS":
        approval = preflight.get("operator_approval")
        approver = approval.get("approver") if isinstance(approval, dict) else None
        authorization = approval.get("authorization") if isinstance(approval, dict) else None
        if not (_is_nonempty_str(approver) and _is_nonempty_str(authorization)):
            problems.append(
                "preflight verdict is PASS_WITH_EXCEPTIONS with no recorded "
                "operator_approval (approver + authorization) -- an unapproved "
                "PASS_WITH_EXCEPTIONS does not authorize an audit "
                "(ecosystem/01_clean_state_preflight.md Sec 5)"
            )

    preflight_execution = preflight.get("execution_id")
    baseline_execution = baseline.get("execution_id")
    if not _is_nonempty_str(baseline_execution):
        problems.append("--baseline has no 'execution_id' -- it is not a captured baseline")
    if (
        _is_nonempty_str(preflight_execution)
        and _is_nonempty_str(baseline_execution)
        and preflight_execution != baseline_execution
    ):
        problems.append(
            f"preflight execution_id '{preflight_execution}' != baseline execution_id "
            f"'{baseline_execution}' -- both inputs must belong to the SAME execution "
            "(ecosystem/03_engineering_audit.md Sec 2)"
        )
    return problems


def write_json_document(path: str, document: object) -> None:
    """Write ``document`` to ``path`` as indented JSON with a trailing newline."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")


def _distribution(values: Sequence[str], vocabulary: Sequence[str]) -> list[tuple[str, int]]:
    """Return ``(label, count)`` pairs for ``values`` over ``vocabulary`` order."""
    counts = {label: 0 for label in vocabulary}
    for value in values:
        if value in counts:
            counts[value] += 1
    return [(label, counts[label]) for label in vocabulary if counts[label]]


def render_report(
    audit_id: str,
    generated_at: str,
    findings: Sequence[dict],
    baseline: dict,
    preflight: dict,
) -> str:
    """Render the human-readable ``report.md`` for this audit.

    Mirrors the structure of the shipped dogfood report
    (.agent/audits/<id>/report.md): a preamble naming the audit and its inputs,
    a findings summary that DEFERS to findings.json, deterministic maturity /
    confidence / status distributions, and a forward-prioritisation section that
    lists open findings strongest-evidence-first. Raw evidence is never
    re-pasted here (methodology/04_tool_driven_state.md Sec 5); findings.json is
    the machine-readable companion.
    """
    execution_id = baseline.get("execution_id", "unknown")
    verdict = preflight.get("verdict", "unknown")
    open_findings = [f for f in findings if f.get("status") == "open"]
    resolved_findings = [f for f in findings if f.get("status") == "resolved"]

    lines: list[str] = []
    lines.append(f"# Engineering Audit Report -- {audit_id}")
    lines.append("")
    lines.append(
        f"Assembled by `tools/ecosystem_audit.py` at {generated_at} for execution "
        f"`{execution_id}` (preflight verdict `{verdict}`), per "
        "`ecosystem/03_engineering_audit.md`. Raw evidence is externalised by path "
        "under `.agent/evidence/` and is not re-pasted here; the machine-readable "
        "companion is `findings.json` alongside this report."
    )
    lines.append("")
    lines.append(
        f"Totals: {len(findings)} finding(s) -- {len(open_findings)} open, "
        f"{len(resolved_findings)} resolved."
    )
    lines.append("")

    lines.append("## Findings Summary (see findings.json)")
    lines.append("")
    for finding in findings:
        maturity = finding.get("maturity")
        maturity_note = f", maturity {maturity}" if maturity else ""
        lines.append(
            f"- `{finding.get('id')}` [{finding.get('severity')}] "
            f"{finding.get('confidence')}{maturity_note}, {finding.get('status')} "
            f"(owner: {finding.get('owner')}) -- {finding.get('impact')}"
        )
    lines.append("")

    confidence_dist = _distribution([f.get("confidence", "") for f in findings], CONFIDENCE_VOCABULARY)
    maturity_dist = _distribution([f.get("maturity", "") for f in findings], MATURITY_LEVELS)
    lines.append("## Distributions")
    lines.append("")
    lines.append(
        "- Confidence: "
        + (", ".join(f"{label} {count}" for label, count in confidence_dist) or "none")
    )
    lines.append(
        "- Maturity: "
        + (", ".join(f"{label} {count}" for label, count in maturity_dist) or "none asserted")
    )
    lines.append(f"- Status: open {len(open_findings)}, resolved {len(resolved_findings)}")
    lines.append("")

    lines.append("## Forward Prioritization")
    lines.append("")
    if not open_findings:
        lines.append("- No open findings.")
    else:
        by_confidence = {label: [] for label in CONFIDENCE_VOCABULARY}
        for finding in open_findings:
            by_confidence.get(finding.get("confidence"), by_confidence["Suspected"]).append(finding)
        for label in CONFIDENCE_VOCABULARY:
            for finding in by_confidence[label]:
                lines.append(
                    f"- `{finding.get('id')}` ({label}) -- closure criteria: "
                    f"{finding.get('closure_criteria')}"
                )
    lines.append("")
    return "\n".join(lines)


def write_assembly_log(
    output_dir: str,
    audit_id: str,
    generated_at: str,
    findings: Sequence[dict],
    baseline: dict,
) -> None:
    """Write the run's plain-text evidence log to ``output_dir/assembly-log.txt``."""
    lines = [
        f"ecosystem_audit.py assembly log -- audit_id={audit_id}",
        f"generated_at={generated_at}",
        f"execution_id={baseline.get('execution_id', 'unknown')}",
        f"finding_count={len(findings)}",
        f"finding_ids={[f.get('id') for f in findings]}",
    ]
    with open(os.path.join(output_dir, "assembly-log.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def build_argument_parser() -> _UsageErrorArgumentParser:
    """Construct this CLI's argument parser."""
    parser = _UsageErrorArgumentParser(
        prog="ecosystem_audit.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--audit-id",
        required=True,
        help="The ecosystem-cycle audit identifier this run produces artifacts for.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help=(
            "Directory where findings.json / report.md / assembly-log.txt are "
            "written (created if absent). Conventionally .agent/audits/<audit-id>/."
        ),
    )
    parser.add_argument(
        "--findings-input",
        required=True,
        help=(
            "Path to the auditor-authored findings payload: a top-level JSON array "
            "of finding objects (schema/engineering_finding.schema.json). This CLI "
            "validates and assembles them; it does not invent findings."
        ),
    )
    parser.add_argument(
        "--preflight",
        required=True,
        help=(
            "Path to this execution's preflight verdict artifact (preflight.json). "
            "The audit's Sec 2 entry condition: verdict must be PASS or an "
            "operator-approved PASS_WITH_EXCEPTIONS."
        ),
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help=(
            "Path to this execution's baseline artifact (baseline.json), captured "
            "for the SAME execution as --preflight."
        ),
    )
    return parser


def main(argv: Sequence[str]) -> int:
    """Run the CLI and return its process exit code (see the module docstring's table)."""
    parser = build_argument_parser()
    try:
        args = parser.parse_args(list(argv))
        preflight = load_json_document(args.preflight, "--preflight")
        baseline = load_json_document(args.baseline, "--baseline")
        findings_payload = load_json_document(args.findings_input, "--findings-input")
    except AuditUsageError as usage_error:
        print(f"usage error: {usage_error}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    entry_problems = check_entry_conditions(preflight, baseline)
    if entry_problems:
        print("AUDIT REFUSED: entry conditions unmet (ecosystem/03_engineering_audit.md Sec 2)")
        for problem in entry_problems:
            print(f"  - {problem}", file=sys.stderr)
        return EXIT_ENTRY_CONDITION_UNMET

    findings, finding_problems = validate_findings(findings_payload)
    if finding_problems:
        print(f"AUDIT INVALID: {len(finding_problems)} finding problem(s); no artifact written")
        for problem in finding_problems:
            print(f"  - {problem}", file=sys.stderr)
        return EXIT_FINDINGS_INVALID

    os.makedirs(args.output_dir, exist_ok=True)
    generated_at = format_iso8601(read_utc_now())

    # findings.json: the validated findings as a top-level array, ordered by id
    # for deterministic output regardless of input ordering.
    ordered = sorted(findings, key=lambda f: f.get("id", ""))
    write_json_document(os.path.join(args.output_dir, "findings.json"), ordered)

    report = render_report(args.audit_id, generated_at, ordered, preflight=preflight, baseline=baseline)
    with open(os.path.join(args.output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write(report)

    write_assembly_log(args.output_dir, args.audit_id, generated_at, ordered, baseline)

    print(
        f"AUDIT ASSEMBLED: {len(ordered)} finding(s) -> "
        f"{os.path.join(args.output_dir, 'findings.json')} + report.md"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
