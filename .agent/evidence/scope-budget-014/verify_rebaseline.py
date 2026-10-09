#!/usr/bin/env python3
"""Verify the spec 1.1.4 scope-budget re-baseline artifacts (phase 014).

Run from the repository root. Checks, each printed as PASS/FAIL:
  1. .agent/feature_list_014.json validates against schema/feature_list.schema.json;
  2. the spec frontmatter parses, validates against schema/frontmatter.schema.json,
     and carries the spec-versioning fields (spec_version == version == newest
     change_log entry, ISO-8601 Z timestamps, updated_at == newest entry date);
  3. spec_version lockstep between the spec and the feature list;
  4. the feature DAG: every dependency exists, no cycle, list order topological;
  5. the estimate arithmetic: pending estimated_lines sum, each estimate inside
     its range, original_estimate_lines == ceil100(1481 + 300 + pending sum), and the
     ceiling covers the range's high end;
  6. the frozen acceptance infrastructure (.agent/evidence/phase-014-activation/)
     is unchanged against HEAD.
Exit 0 when every check passes, else 1.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from typing import Dict, List

import jsonschema
import yaml

SPEC = ".agent/product_spec_014.md"
FEATURES = ".agent/feature_list_014.json"
MEASURED_BUDGET_099_103 = 1481
REBASELINE_PLANNING_ALLOWANCE = 300
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def report(results: List[bool], name: str, ok: bool, detail: str) -> None:
    """Print one check result and record it.

    Args:
        results: Accumulator of pass/fail booleans.
        name: Check name.
        ok: Whether the check passed.
        detail: One-line evidence for the result.
    """
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")


def main() -> int:
    """Run every check and return the exit code.

    Returns:
        0 if all checks pass, otherwise 1.
    """
    results: List[bool] = []
    features_doc = json.load(open(FEATURES, encoding="utf-8"))
    schema = json.load(open("schema/feature_list.schema.json", encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(features_doc), key=str)
    report(results, "feature-list-schema", not errors,
           f"{len(errors)} error(s) against schema/feature_list.schema.json")

    text = open(SPEC, encoding="utf-8").read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    front = yaml.safe_load(match.group(1)) if match else {}
    fm_schema = json.load(open("schema/frontmatter.schema.json", encoding="utf-8"))
    fm_errors = sorted(jsonschema.Draft202012Validator(fm_schema).iter_errors(front), key=str)
    report(results, "spec-frontmatter-schema", bool(match) and not fm_errors,
           f"{len(fm_errors)} error(s) against schema/frontmatter.schema.json")
    newest = (front.get("change_log") or [{}])[0]
    versioning_ok = (
        front.get("spec_version") == str(front.get("version")) == newest.get("version")
        and all(TIMESTAMP.match(str(front.get(key, ""))) for key in ("created_at", "updated_at"))
        and TIMESTAMP.match(str(newest.get("date", "")))
        and front.get("updated_at") == newest.get("date")
        and all({"version", "date", "summary"} <= set(entry) for entry in front["change_log"])
    )
    report(results, "spec-versioning-fields", bool(versioning_ok),
           f"spec_version={front.get('spec_version')} version={front.get('version')} "
           f"newest={newest.get('version')}@{newest.get('date')} updated_at={front.get('updated_at')}")
    report(results, "spec-version-lockstep",
           features_doc["spec_version"] == front.get("spec_version"),
           f"feature_list={features_doc['spec_version']} spec={front.get('spec_version')}")

    features = features_doc["features"]
    ids = [feature["id"] for feature in features]
    position: Dict[str, int] = {fid: index for index, fid in enumerate(ids)}
    missing = [(f["id"], d) for f in features for d in f["dependencies"] if d not in position]
    out_of_order = [(f["id"], d) for f in features for d in f["dependencies"]
                    if d in position and position[d] >= position[f["id"]]]
    report(results, "dag", not missing and not out_of_order and len(set(ids)) == len(ids),
           f"missing={missing} out_of_order={out_of_order} (list order topological => acyclic)")

    pending = [f for f in features if f["status"] == "pending"]
    pending_sum = sum(f["estimated_lines"] for f in pending)
    low = sum(f["estimated_lines_range"][0] for f in pending)
    high = sum(f["estimated_lines_range"][1] for f in pending)
    inside = all(f["estimated_lines_range"][0] <= f["estimated_lines"] <= f["estimated_lines_range"][1]
                 for f in pending)
    known = MEASURED_BUDGET_099_103 + REBASELINE_PLANNING_ALLOWANCE
    expected = math.ceil((known + pending_sum) / 100) * 100
    ceiling = round(features_doc["original_estimate_lines"] * 1.3)
    arithmetic_ok = (inside and features_doc["original_estimate_lines"] == expected
                     and known + high <= ceiling)
    report(results, "estimate-arithmetic", arithmetic_ok,
           f"pending_sum={pending_sum} range={low}-{high} "
           f"original={features_doc['original_estimate_lines']} expected=ceil100({MEASURED_BUDGET_099_103}+"
           f"{REBASELINE_PLANNING_ALLOWANCE}+{pending_sum})={expected} ceiling={ceiling} high_end={known + high}")

    frozen = subprocess.run(["git", "status", "--porcelain", "--", ".agent/evidence/phase-014-activation/"],
                            capture_output=True, text=True)
    report(results, "frozen-activation-infrastructure-unchanged",
           frozen.returncode == 0 and frozen.stdout == "",
           f"git status --porcelain entries: {len(frozen.stdout.splitlines())}")

    print(f"SUMMARY: {sum(results)} passed, {len(results) - sum(results)} failed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
