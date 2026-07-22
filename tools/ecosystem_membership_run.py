#!/usr/bin/env python3
"""ecosystem_membership_run.py -- iterate a consumer's ecosystem-membership
registry, run Preflight across its in_scope set, and aggregate the per-member
verdicts into one ecosystem-level result with a cross-repo consistency check.

This is the n-case iteration + aggregation (NIP-0002 Stage 3; NDEBT-031).
Where the shipped ecosystem tools take a single ``--repo-root``, this reads the
membership registry that sets ``n`` (registry/scope_definition_patterns.md;
schema/ecosystem_membership.schema.json) and runs the per-repository stage once
per ``in_scope`` member (feature 076), then rolls the per-member verdicts up
into ONE ecosystem-level result artifact at ``<output-dir>/membership_run.json``
(schema/ecosystem_membership_result.schema.json, feature 077).

The aggregate records the cross-repository CONSISTENCY the shipped single-repo
tools only guarded as a 'future extension': every in_scope member MUST have run
under the same framework pin (the ``resolved_sha`` recorded in each member's
``.nizam/provenance.json``). A divergent or missing pin is a first-class recorded
``consistency_finding``, not a silent mismatch, and a pin-inconsistent ecosystem
cannot be ``PASS``.

Full registry validation is ``tools/validate.sh --target <registry>`` (C12);
this tool does a lightweight structural read (enough to iterate safely) and
fails clearly on a malformed registry. The single-``--repo-root`` stage tool
(ecosystem_preflight.py) is invoked unchanged, once per member -- the count-1
case is a single-member registry.

Exit codes (mirroring ecosystem_preflight.py's table):
  0   ecosystem_verdict PASS: every in_scope member returned an ACCEPTABLE
      Preflight verdict (PASS / PASS_WITH_EXCEPTIONS) AND all members ran under
      the same framework pin.
  1   ecosystem_verdict FAIL: at least one member hard-FAILed / had a missing
      repo-root, or the members diverged on their framework pin.
  64  usage error (bad arguments, or an unreadable/structurally-invalid registry).
"""

import argparse
import json
import os
import subprocess
import sys

EXIT_CLEAN = 0
EXIT_NOT_CLEAN = 1
EXIT_USAGE_ERROR = 64

# The stage tool's verdict exit codes (ecosystem_preflight.py). PASS and both
# PASS_WITH_EXCEPTIONS variants are acceptable; a hard FAIL(1) or anything else
# leaves the ecosystem not clean.
ACCEPTABLE_STAGE_EXITS = {0, 2, 3}
STAGE_VERDICT = {0: "PASS", 1: "FAIL", 2: "PASS_WITH_EXCEPTIONS", 3: "PASS_WITH_EXCEPTIONS"}

SCOPE_LISTS = ("in_scope", "incubating", "reference_archive", "out_of_scope")


def die_usage(message):
    print(f"ecosystem_membership_run.py: usage error: {message}", file=sys.stderr)
    sys.exit(EXIT_USAGE_ERROR)


def load_registry(path):
    """Structurally read the registry -- enough to iterate safely. The
    authoritative shape + exactly-one-list validation is tools/validate.sh C12."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        die_usage(f"could not read membership registry '{path}': {exc}")
    if not isinstance(data, dict):
        die_usage(f"membership registry '{path}' is not a JSON object")
    for key in SCOPE_LISTS:
        value = data.get(key)
        if not isinstance(value, list):
            die_usage(
                f"membership registry '{path}' is missing the required list '{key}' "
                f"(or it is not an array) -- validate it with "
                f"'tools/validate.sh --target {path}' (C12)"
            )
    # Fail closed on the exactly-one-list invariant BEFORE iterating (the same
    # rule validate.sh C12 enforces): a name appearing more than once -- twice in
    # one list, or across lists -- would run twice into the same <output-dir>/<name>
    # (silently reusing it) and bypass the exactly-one-list contract. Refuse it
    # here rather than iterate a registry C12 would reject.
    counts = {}
    for key in SCOPE_LISTS:
        for item in data[key]:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                counts[item["name"]] = counts.get(item["name"], 0) + 1
    duplicates = sorted(name for name, n in counts.items() if n > 1)
    if duplicates:
        die_usage(
            f"membership registry '{path}' violates the exactly-one-list invariant -- "
            f"these names appear more than once across the scope lists: {duplicates}. "
            f"Validate it with 'tools/validate.sh --target {path}' (C12)."
        )
    return data


def resolve_repo_root(entry, base):
    """Resolve a member entry to (name, repo_root). An entry MAY carry an explicit
    'repo_root' (absolute, or relative to --repo-roots-base); otherwise the member
    is looked for at <base>/<name>."""
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        die_usage("an in_scope entry has no identifying 'name'")
    repo_root = entry.get("repo_root")
    if isinstance(repo_root, str) and repo_root:
        resolved = repo_root if os.path.isabs(repo_root) else os.path.join(base, repo_root)
    else:
        resolved = os.path.join(base, name)
    return name, resolved


def read_framework_pin(repo_root):
    """Best-effort read of a member's framework pin -- the resolved_sha recorded in
    <repo_root>/.nizam/provenance.json by bootstrap.sh (feature 067). Returns the
    SHA string, or None when no readable pin is present (an unbootstrapped or
    pre-067 member), which is itself a consistency finding."""
    provenance = os.path.join(repo_root, ".nizam", "provenance.json")
    try:
        with open(provenance, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    pin = data.get("resolved_sha")
    return pin if isinstance(pin, str) and pin else None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Iterate an ecosystem-membership registry, running the Preflight stage per in_scope member (NIP-0002 Stage 3)."
    )
    parser.add_argument("--membership-registry", required=True,
                        help="Path to the membership registry JSON (schema/ecosystem_membership.schema.json).")
    parser.add_argument("--output-dir", required=True,
                        help="Directory for per-member Preflight outputs and the run index (membership_run.json).")
    parser.add_argument("--repo-roots-base", default=".",
                        help="Base directory a member's repo-root is resolved against when its entry has no absolute repo_root (default: CWD).")
    parser.add_argument("--stage-tool",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecosystem_preflight.py"),
                        help="The per-repository stage tool to run (default: the sibling ecosystem_preflight.py).")
    args = parser.parse_args(argv)

    data = load_registry(args.membership_registry)
    members = data["in_scope"]
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    all_members_acceptable = True
    for entry in members:
        if not isinstance(entry, dict):
            die_usage("an in_scope entry is not an object")
        name, repo_root = resolve_repo_root(entry, args.repo_roots_base)
        if not os.path.isdir(repo_root):
            print(f"  {name}: MISSING repo-root '{repo_root}'")
            results.append({"name": name, "repo_root": repo_root, "preflight_exit": None,
                            "verdict": "missing", "status": "missing_repo_root", "framework_pin": None})
            all_members_acceptable = False
            continue
        member_out = os.path.join(args.output_dir, name)
        os.makedirs(member_out, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, args.stage_tool, "--repo-root", repo_root,
             "--output-dir", member_out, "--execution-id", f"membership-{name}"],
            capture_output=True, text=True,
        )
        rc = completed.returncode
        verdict = STAGE_VERDICT.get(rc, f"exit_{rc}")
        acceptable = rc in ACCEPTABLE_STAGE_EXITS
        pin = read_framework_pin(repo_root)
        print(f"  {name}: Preflight {verdict} (exit {rc}); pin {pin or '<none>'} [{repo_root}]")
        results.append({
            "name": name, "repo_root": repo_root, "preflight_exit": rc,
            "verdict": verdict, "status": "acceptable" if acceptable else "fail",
            "framework_pin": pin,
        })
        if not acceptable:
            all_members_acceptable = False

    # Cross-repo consistency: every in_scope member MUST have run under the same,
    # non-null framework pin. A divergent or missing pin is a recorded finding.
    pins = {item["framework_pin"] for item in results}
    distinct_non_null = sorted(p for p in pins if p)
    missing_pin_members = sorted(item["name"] for item in results if not item["framework_pin"])
    consistency_findings = []
    for member_name in missing_pin_members:
        consistency_findings.append(f"member '{member_name}' has no readable framework pin (unbootstrapped or pre-067 provenance)")
    if len(distinct_non_null) > 1:
        consistency_findings.append(f"members diverge on framework pin: {distinct_non_null}")
    framework_pin_consistent = (not missing_pin_members) and len(distinct_non_null) == 1
    common_pin = distinct_non_null[0] if framework_pin_consistent else None

    ecosystem_pass = all_members_acceptable and framework_pin_consistent
    result = {
        "schema_version": "1.0.0",
        "membership_registry": args.membership_registry,
        "ecosystem_verdict": "PASS" if ecosystem_pass else "FAIL",
        "framework_pin_consistent": framework_pin_consistent,
        "framework_pin": common_pin,
        "member_count": len(members),
        "members": results,
        "consistency_findings": consistency_findings,
    }
    result_path = os.path.join(args.output_dir, "membership_run.json")
    with open(result_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")

    acceptable_count = sum(1 for item in results if item.get("status") == "acceptable")
    pin_note = f"pin-consistent ({common_pin})" if framework_pin_consistent else f"pin-INCONSISTENT ({len(consistency_findings)} finding(s))"
    print(
        f"ecosystem_membership_run.py: ecosystem_verdict={result['ecosystem_verdict']} -- "
        f"{acceptable_count}/{len(members)} in_scope member(s) acceptable, {pin_note}; "
        f"result at {result_path}."
    )
    return EXIT_CLEAN if ecosystem_pass else EXIT_NOT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
