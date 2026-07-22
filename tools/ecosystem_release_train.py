#!/usr/bin/env python3
"""ecosystem_release_train.py -- the Promote stage: admit an authorized
reconciliation plan's work packets into a cross-repository release train.

This mechanizes ecosystem/05_release_train_coordination.md (NIP-0002 Stage 4;
NDEBT-035). It reads a reconciliation plan that tools/ecosystem_reconcile.py
produced (schema/reconciliation_plan.schema.json), admits its packets into a
train (all of them, or a --admit subset), and emits a schema-valid release-train
manifest at <output-dir>/manifest.json (schema/release_train_manifest.schema.json).

The gate H-TRAIN-ENTRY is record-but-never-self-execute (ecosystem/05 Section 5):
this tool NEVER promotes or departs the train, and it MUST NOT emit a PASS train
without the operator's admission decision recorded -- the caller passes
--entry-gate-recorded to assert that decision was taken (and recorded in
run_state per NDEBT-018) before the tool runs. Without it, the manifest is
written for the record but its verdict is FAIL.

The trace-to-plan invariant is the manifest's core guarantee (ecosystem/05
Section 4): every admitted packet MUST trace to a plan packet. An admitted id
with no plan origin (only reachable via --admit) is an orphan -- a first-class
recorded finding forcing train_verdict FAIL.

Full manifest validation is tools/validate.sh --target <manifest> (C12); this
tool produces a manifest that validates and fails clearly on a malformed or
non-PASS input plan.

Exit codes (mirroring ecosystem_reconcile.py's table):
  0   train_verdict PASS: every admitted packet traces to a plan packet AND the
      H-TRAIN-ENTRY admission decision is recorded.
  1   train_verdict FAIL: at least one admitted packet is an orphan, or the
      admission decision is not recorded (--entry-gate-recorded absent).
  64  usage error (bad arguments, an unreadable/structurally-invalid plan, or a
      source plan whose own plan_verdict is not PASS).
"""

import argparse
import json
import os
import sys

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE_ERROR = 64


def die_usage(message):
    """Print a usage-error diagnostic to stderr and exit EXIT_USAGE_ERROR (64).

    The single exit point for every unrecoverable input problem (bad arguments, an
    unreadable/structurally-invalid plan, a non-PASS source plan), mirroring the
    sibling tools' usage exit so a caller can distinguish a caller mistake (64)
    from a FAIL train (1).
    """
    print(f"ecosystem_release_train.py: usage error: {message}", file=sys.stderr)
    sys.exit(EXIT_USAGE_ERROR)


def load_plan(path):
    """Read + structurally validate the reconciliation plan. A train is only built
    from a PASS plan (ecosystem/05 Section 2: never from a FAIL/cyclic plan).
    Returns (plan_packet_ids, packets_by_id)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        die_usage(f"could not read reconciliation plan '{path}': {exc}")
    if not isinstance(data, dict):
        die_usage(f"reconciliation plan '{path}' is not a JSON object")
    if data.get("plan_verdict") != "PASS":
        die_usage(
            f"reconciliation plan '{path}' has plan_verdict "
            f"{data.get('plan_verdict')!r}, not PASS -- a train is only built from a "
            "PASS plan (ecosystem/05 Section 2). Resolve the plan's cycle first."
        )
    packets = data.get("packets")
    if not isinstance(packets, list) or not packets:
        die_usage(f"reconciliation plan '{path}' has no non-empty 'packets' array")
    by_id = {}
    for item in packets:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            by_id[item["id"]] = item
    if not by_id:
        die_usage(f"reconciliation plan '{path}' has no packets with an 'id'")
    return list(by_id.keys()), by_id


def main(argv=None):
    """Read the plan, admit its packets into a train, write the manifest, return the exit code.

    Produces a schema-valid release-train manifest at <output-dir>/manifest.json.
    Returns EXIT_PASS (0) when every admitted packet traces to a plan packet AND the
    admission decision is recorded; EXIT_FAIL (1) on an orphan or an ungated admission;
    usage errors exit EXIT_USAGE_ERROR (64) via die_usage.
    """
    parser = argparse.ArgumentParser(
        description="Admit an authorized reconciliation plan's packets into a cross-repository release train (NIP-0002 Stage 4)."
    )
    parser.add_argument("--plan", required=True,
                        help="Path to the reconciliation plan (schema/reconciliation_plan.schema.json) produced by ecosystem_reconcile.py.")
    parser.add_argument("--output-dir", required=True,
                        help="Directory for the produced release-train manifest (manifest.json).")
    parser.add_argument("--admit", action="append", default=None,
                        help="A packet id to admit into the train (repeatable). Default: every plan packet. An id not in the plan is a recorded orphan.")
    parser.add_argument("--entry-gate-recorded", action="store_true",
                        help="Assert the operator's H-TRAIN-ENTRY admission decision was taken and recorded (run_state, per NDEBT-018) before this run. Without it, a PASS train is never emitted.")
    args = parser.parse_args(argv)

    plan_packet_ids, packets_by_id = load_plan(args.plan)
    admitted_ids = args.admit if args.admit is not None else list(plan_packet_ids)

    plan_id_set = set(plan_packet_ids)
    admitted_packets = []
    orphan_findings = []
    train_member_set = set()
    for pid in admitted_ids:
        if pid in plan_id_set:
            repo = packets_by_id[pid].get("repo", "")
            admitted_packets.append({"id": pid, "repo": repo})
            if repo:
                train_member_set.add(repo)
        else:
            orphan_findings.append(f"admitted packet '{pid}' traces to no plan packet (orphan)")

    entry_gate_recorded = bool(args.entry_gate_recorded)
    train_pass = (not orphan_findings) and entry_gate_recorded

    # plan_packets carries the plan's (id, repo) mapping as provenance, so the
    # trace-to-plan invariant can be checked on BOTH fields (ecosystem/05 Section 4)
    # -- an admission that reuses a real id under the wrong repo is caught, not just
    # a wholly-unknown id.
    plan_packets_out = [{"id": pid, "repo": packets_by_id[pid].get("repo", "")} for pid in plan_packet_ids]

    manifest = {
        "schema_version": "1.0.0",
        "source_plan": args.plan,
        "plan_packets": plan_packets_out,
        "train_verdict": "PASS" if train_pass else "FAIL",
        "entry_gate_recorded": entry_gate_recorded,
        "admitted_packets": admitted_packets,
        "train_members": sorted(train_member_set),
        "orphan_findings": orphan_findings,
    }
    os.makedirs(args.output_dir, exist_ok=True)
    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    if train_pass:
        print(f"ecosystem_release_train.py: train_verdict=PASS -- {len(admitted_packets)} packet(s) "
              f"admitted across {len(train_member_set)} repo(s), H-TRAIN-ENTRY recorded. Manifest at {manifest_path}.")
        return EXIT_PASS
    if not entry_gate_recorded:
        reason = "H-TRAIN-ENTRY admission decision NOT recorded (--entry-gate-recorded absent)"
    else:
        reason = f"{len(orphan_findings)} orphan admission(s): {orphan_findings}"
    print(f"ecosystem_release_train.py: train_verdict=FAIL -- {reason}. Manifest at {manifest_path}.")
    return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
