#!/usr/bin/env python3
"""ecosystem_membership_run.py -- iterate a consumer's ecosystem-membership
registry and run the per-repository Preflight stage across its in_scope set.

This is the n-case iteration (NIP-0002 Stage 3; NDEBT-031). Where the shipped
ecosystem tools take a single ``--repo-root``, this reads the membership
registry that sets ``n`` (registry/scope_definition_patterns.md;
schema/ecosystem_membership.schema.json) and runs the per-repository stage once
per ``in_scope`` member, collecting a per-member result index at
``<output-dir>/membership_run.json``.

Cross-repository AGGREGATION into one schema-valid ecosystem-level result, and
the common-framework-pin CONSISTENCY check, are feature 077 -- this feature is
the iteration seam only. Full registry validation is ``tools/validate.sh
--target <registry>`` (C12); this tool does a lightweight structural read
(enough to iterate safely) and fails clearly on a malformed registry.

The single-``--repo-root`` stage tool (ecosystem_preflight.py) is invoked
unchanged, once per member -- the count-1 case is a single-member registry.

Exit codes (mirroring ecosystem_preflight.py's table):
  0   every in_scope member ran and returned an ACCEPTABLE Preflight verdict
      (PASS, or PASS_WITH_EXCEPTIONS pending/approved).
  1   at least one member's Preflight hard-FAILed, or a member's repo-root was
      missing/unrunnable -- the iteration completed but the ecosystem is not clean.
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
    not_clean = False
    for entry in members:
        if not isinstance(entry, dict):
            die_usage("an in_scope entry is not an object")
        name, repo_root = resolve_repo_root(entry, args.repo_roots_base)
        if not os.path.isdir(repo_root):
            print(f"  {name}: MISSING repo-root '{repo_root}'")
            results.append({"name": name, "repo_root": repo_root, "preflight_exit": None, "status": "missing_repo_root"})
            not_clean = True
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
        print(f"  {name}: Preflight {verdict} (exit {rc}) [{repo_root}]")
        results.append({
            "name": name, "repo_root": repo_root, "preflight_exit": rc,
            "verdict": verdict, "status": "acceptable" if acceptable else "fail",
        })
        if not acceptable:
            not_clean = True

    index = {
        "membership_registry": args.membership_registry,
        "member_count": len(members),
        "members": results,
    }
    index_path = os.path.join(args.output_dir, "membership_run.json")
    with open(index_path, "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2)
        handle.write("\n")

    acceptable_count = sum(1 for item in results if item.get("status") == "acceptable")
    print(
        f"ecosystem_membership_run.py: {acceptable_count}/{len(members)} in_scope member(s) "
        f"returned an acceptable Preflight verdict; run index at {index_path}."
    )
    return EXIT_NOT_CLEAN if not_clean else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
