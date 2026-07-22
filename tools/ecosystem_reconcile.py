#!/usr/bin/env python3
"""ecosystem_reconcile.py -- the Plan stage: turn approved audit findings into a
dependency-ordered, schema-valid cross-repository reconciliation plan.

This mechanizes ecosystem/04_dependency_reconciliation.md (NIP-0002 Stage 4;
NDEBT-035). It reads the ecosystem-level membership-run aggregate that
tools/ecosystem_membership_run.py emits (schema/ecosystem_membership_result.schema.json)
for the authoritative in_scope member set, and a packets-input file naming the
work packets (each targeting one in_scope repo, closing one or more approved
findings, and declaring typed cross-repo depends_on edges). It computes the
topological order of the packet dependency graph and emits a schema-valid
reconciliation plan at <output-dir>/plan.json (schema/reconciliation_plan.schema.json).

The topological-order invariant is the plan's core guarantee (ecosystem/04
Section 4): a cyclic dependency set has no valid order, so it is a first-class
recorded finding (cycle_findings) forcing plan_verdict FAIL -- never a silent
mis-order. The produced plan is the hand-aggregation made a produced artifact.

Full plan validation is tools/validate.sh --target <plan> (C12); this tool
produces a plan that validates and does a lightweight structural read of its
inputs, failing clearly on a malformed aggregate or packets input.

Exit codes (mirroring ecosystem_membership_run.py's table):
  0   plan_verdict PASS: every packet closes >=1 finding and targets an in_scope
      repo, and the dependency set is acyclic (a valid topological order exists).
  1   plan_verdict FAIL: the dependency set contains at least one cycle (recorded
      in cycle_findings); no valid order exists.
  64  usage error (bad arguments, an unreadable/structurally-invalid aggregate or
      packets input, an unknown target repo, or a dangling dependency edge).
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
    unreadable/structurally-invalid aggregate or packets input, an unknown target
    repo, a dangling edge), mirroring the sibling tools' usage exit so a caller can
    distinguish a caller mistake (64) from a FAIL plan (1).
    """
    print(f"ecosystem_reconcile.py: usage error: {message}", file=sys.stderr)
    sys.exit(EXIT_USAGE_ERROR)


def load_json_object(path, label):
    """Read a JSON object from path, or die_usage on an unreadable/non-object file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        die_usage(f"could not read {label} '{path}': {exc}")
    if not isinstance(data, dict):
        die_usage(f"{label} '{path}' is not a JSON object")
    return data


def load_in_scope_members(aggregate):
    """Extract the authoritative in_scope member names from the membership-run
    aggregate (schema/ecosystem_membership_result.schema.json's members[].name).
    The aggregate is the enumerated set the plan's packets must target."""
    members = aggregate.get("members")
    if not isinstance(members, list):
        die_usage("aggregate has no 'members' array -- validate it with "
                  "'tools/validate.sh --target <aggregate>' (C12, membership_result)")
    names = set()
    for item in members:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.add(item["name"])
    return names


def load_packets(packets_doc, member_names):
    """Structurally read + validate the packets input against the member set.

    Every packet needs a unique id, an in_scope repo, and >=1 closed finding
    (ecosystem/04 Section 3: a packet that closes no finding is not recorded).
    Returns the ordered list of packet dicts (id/repo/closes_findings/depends_on).
    """
    packets = packets_doc.get("packets")
    if not isinstance(packets, list) or not packets:
        die_usage("packets input has no non-empty 'packets' array")
    seen = set()
    normalised = []
    for item in packets:
        if not isinstance(item, dict):
            die_usage("a packet is not an object")
        pid = item.get("id")
        if not isinstance(pid, str) or not pid:
            die_usage("a packet has no identifying 'id'")
        if pid in seen:
            die_usage(f"packet id '{pid}' appears more than once (ids must be unique)")
        seen.add(pid)
        repo = item.get("repo")
        if not isinstance(repo, str) or not repo:
            die_usage(f"packet '{pid}' has no 'repo'")
        if repo not in member_names:
            die_usage(f"packet '{pid}' targets repo '{repo}', which is not an in_scope "
                      f"member of the aggregate ({sorted(member_names)})")
        closes = item.get("closes_findings")
        if not isinstance(closes, list) or not closes:
            die_usage(f"packet '{pid}' closes no findings (ecosystem/04 Section 3: a "
                      "packet that closes no approved finding is not recorded)")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list):
            die_usage(f"packet '{pid}' has a non-array 'depends_on'")
        normalised.append({"id": pid, "repo": repo,
                           "closes_findings": list(closes), "depends_on": list(deps)})
    # A dependency edge must reference a declared packet id (a dangling edge is a
    # malformed input, not a cycle).
    ids = {p["id"] for p in normalised}
    for p in normalised:
        for dep in p["depends_on"]:
            if dep not in ids:
                die_usage(f"packet '{p['id']}' depends_on '{dep}', which is not a declared packet id")
    return normalised


def topological_order(packets):
    """Kahn's algorithm over the packet depends_on graph. Returns
    (order, cycle_nodes): on success, order is a valid topological sequence of
    every packet id and cycle_nodes is []; on a cycle, order is the partial
    sequence and cycle_nodes is the sorted ids that never resolved (they form or
    feed the cycle). For every edge A depends_on B, B precedes A in the order."""
    ids = [p["id"] for p in packets]
    deps = {p["id"]: set(p["depends_on"]) for p in packets}
    # dependants[b] = packets that depend on b (so removing b relaxes them).
    dependants = {i: set() for i in ids}
    for pid, ds in deps.items():
        for d in ds:
            dependants[d].add(pid)
    indegree = {i: len(deps[i]) for i in ids}
    # Deterministic order: process ready nodes sorted by id.
    ready = sorted(i for i in ids if indegree[i] == 0)
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        newly_ready = []
        for dependant in sorted(dependants[node]):
            indegree[dependant] -= 1
            if indegree[dependant] == 0:
                newly_ready.append(dependant)
        ready = sorted(ready + newly_ready)
    if len(order) < len(ids):
        cycle_nodes = sorted(i for i in ids if i not in set(order))
        return order, cycle_nodes
    return order, []


def main(argv=None):
    """Read the aggregate + packets input, compute the plan, write it, return the exit code.

    Produces a schema-valid reconciliation plan at <output-dir>/plan.json. Returns
    EXIT_PASS (0) for an acyclic plan, EXIT_FAIL (1) for a cyclic one (plan_verdict
    FAIL, cycle_findings recorded); usage errors exit EXIT_USAGE_ERROR (64) via die_usage.
    """
    parser = argparse.ArgumentParser(
        description="Turn approved findings into a dependency-ordered cross-repository reconciliation plan (NIP-0002 Stage 4)."
    )
    parser.add_argument("--source-result", required=True,
                        help="Path to the membership-run aggregate (schema/ecosystem_membership_result.schema.json) -- the in_scope set.")
    parser.add_argument("--packets", required=True,
                        help="Path to the packets-input JSON: {\"packets\": [{id, repo, closes_findings, depends_on}]}.")
    parser.add_argument("--output-dir", required=True,
                        help="Directory for the produced reconciliation plan (plan.json).")
    parser.add_argument("--membership-registry", default=None,
                        help="Optional path to the membership registry the aggregate iterated, carried into the plan for traceability.")
    args = parser.parse_args(argv)

    aggregate = load_json_object(args.source_result, "membership-run aggregate")
    member_names = load_in_scope_members(aggregate)
    packets_doc = load_json_object(args.packets, "packets input")
    packets = load_packets(packets_doc, member_names)

    order, cycle_nodes = topological_order(packets)
    cyclic = bool(cycle_nodes)
    cycle_findings = []
    if cyclic:
        cycle_findings.append(
            "cyclic cross-repo dependency set -- no valid topological order exists; "
            f"unresolved packets (forming or feeding the cycle): {cycle_nodes}"
        )

    plan = {
        "schema_version": "1.0.0",
        "source_result": args.source_result,
        "plan_verdict": "FAIL" if cyclic else "PASS",
        "packets": packets,
        "order": [] if cyclic else order,
        "cycle_findings": cycle_findings,
    }
    if args.membership_registry:
        plan["membership_registry"] = args.membership_registry

    os.makedirs(args.output_dir, exist_ok=True)
    plan_path = os.path.join(args.output_dir, "plan.json")
    with open(plan_path, "w", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2)
        handle.write("\n")

    if cyclic:
        print(f"ecosystem_reconcile.py: plan_verdict=FAIL -- cyclic dependency set "
              f"({cycle_nodes}); no valid order. Plan at {plan_path}.")
        return EXIT_FAIL
    print(f"ecosystem_reconcile.py: plan_verdict=PASS -- {len(packets)} packet(s) "
          f"across {len(member_names)} in_scope member(s), topologically ordered. Plan at {plan_path}.")
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
