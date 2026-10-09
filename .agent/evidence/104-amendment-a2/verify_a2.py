#!/usr/bin/env python3
"""Verify amendment A2 (spec 1.1.5): 104 AT5's branch literal, and nothing else.

Run from the repository root, on the branch that carries the uncommitted or
committed amendment, against the pre-amendment base given by --base (default
b8ea889, main at the start of feature 104). Each check prints PASS/FAIL:

  1. at5-single-literal: 104 AT5 differs from the base in exactly one literal,
     'phase/014-ga-track' -> 'phase/014-104-sandbox-ci' (printed diff region);
  2. other-acceptance-tests-unchanged: every other acceptance test of every
     feature is byte-identical to the base;
  3. feature-104-field-scope: in 104 only description, acceptance_tests and
     acceptance_provenance differ; the description changes only in the
     positive-run clause; the provenance only gains operator_approved_amendment_1_1_5;
  4. other-features-unchanged: every other feature is identical to the base;
  5. top-level-scope: only spec_version and planning_note differ at the top level,
     and the base planning_note is a prefix of the new one;
  6. feature-list-schema: valid against schema/feature_list.schema.json;
  7. spec-frontmatter-schema and spec-versioning-fields (1.1.5, newest change_log
     entry quotes the operator verbatim and names A2);
  8. spec-version-lockstep;
  9. dag: every dependency exists, the list order is topological;
 10. no-stale-branch-in-feature-list-tests-or-description: 'phase/014-ga-track' no longer
     occurs in any feature description or acceptance test (planning_note may cite it);
 11. frozen-activation-infrastructure-unchanged against HEAD;
 12. at5-simulation: in a scratch clone (tempfile, removed afterwards) with a
     simulated convergent job, the AMENDED AT5 passes a well-formed run on the
     feature branch and fails a run on phase/014-ga-track, on main, at a
     non-ancestor headSha, and with a failed conclusion; the BASE AT5 fails the
     well-formed feature-branch run (the amendment is effective).
Exit 0 when every check passes, else 1.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import jsonschema
import yaml

SPEC = ".agent/product_spec_014.md"
FEATURES = ".agent/feature_list_014.json"
OLD_LITERAL = "'phase/014-ga-track'"
NEW_LITERAL = "'phase/014-104-sandbox-ci'"
OLD_DESCRIPTION_CLAUSE = "(positive) on branch phase/014-ga-track at a commit"
NEW_DESCRIPTION_CLAUSE = ("(positive) on the feature branch phase/014-104-sandbox-ci "
                          "(a pull_request run; amendment A2, spec 1.1.5) at a commit")
OPERATOR_VERBATIM = "'B. Amend AT5'"
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
JOB_YAML = ("\n  convergent_review:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: python3 tools/test_convergent_review.py\n")


class VerificationSetupError(Exception):
    """Raised when the verification cannot be set up faithfully."""


def report(results: List[bool], name: str, ok: bool, detail: str) -> None:
    """Print one check result and record it.

    Args:
        results: Accumulator of pass/fail booleans.
        name: Check name.
        ok: Whether the check passed.
        detail: Evidence for the result.
    """
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")


def git_show_json(base: str, path: str) -> Dict[str, Any]:
    """Load a JSON file as it stands at a git revision.

    Args:
        base: Git revision.
        path: Repo-relative path.

    Returns:
        The parsed JSON document.

    Raises:
        VerificationSetupError: If git cannot show the file.
    """
    shown = subprocess.run(["git", "show", f"{base}:{path}"], capture_output=True, text=True)
    if shown.returncode != 0:
        raise VerificationSetupError(f"git show {base}:{path} failed: {shown.stderr.strip()}")
    return json.loads(shown.stdout)


def diff_region(old: str, new: str, context: int = 60) -> str:
    """Render the single differing span of two strings with surrounding context.

    Args:
        old: The base string.
        new: The amended string.
        context: Characters of shared context to show on each side.

    Returns:
        A two-line '-'/'+' rendering of the differing region.
    """
    prefix = 0
    while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(old), len(new)) - prefix
           and old[len(old) - 1 - suffix] == new[len(new) - 1 - suffix]):
        suffix += 1
    start = max(0, prefix - context)
    old_end = len(old) - suffix
    new_end = len(new) - suffix
    tail_old = old[old_end:old_end + context]
    tail_new = new[new_end:new_end + context]
    return (f"\n    differing span: base[{prefix}:{old_end}] -> new[{prefix}:{new_end}]"
            f"\n    - ...{old[start:prefix]}[{old[prefix:old_end]}]{tail_old}..."
            f"\n    + ...{new[start:prefix]}[{new[prefix:new_end]}]{tail_new}...")


def simulate_at5(at5_command: str, clone: Path, run: Dict[str, Any]) -> int:
    """Run one AT5 command inside the scratch clone against a simulated run record.

    Args:
        at5_command: The acceptance-test command line.
        clone: Scratch clone root.
        run: The simulated `gh run view --json` record.

    Returns:
        The command's exit status.
    """
    evidence = clone / ".agent/evidence/104"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "ci-positive-run.txt").write_text(
        "gh run view 4242 --json headSha,headBranch,conclusion,jobs\n"
        + json.dumps(run, indent=1) + "\nEXIT:0\n", encoding="utf-8")
    return subprocess.run(["bash", "-c", at5_command], cwd=clone, capture_output=True).returncode


def main() -> int:
    """Run every check and return the exit code.

    Returns:
        0 if all checks pass, otherwise 1.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="b8ea889", help="pre-amendment revision (default b8ea889)")
    args = parser.parse_args()
    results: List[bool] = []

    base_doc = git_show_json(args.base, FEATURES)
    new_doc = json.load(open(FEATURES, encoding="utf-8"))
    base_features = {f["id"]: f for f in base_doc["features"]}
    new_features = {f["id"]: f for f in new_doc["features"]}

    old_at5 = base_features["104"]["acceptance_tests"][4]
    new_at5 = new_features["104"]["acceptance_tests"][4]
    single = (old_at5.count(OLD_LITERAL) == 1 and new_at5.count(NEW_LITERAL) == 1
              and OLD_LITERAL not in new_at5
              and old_at5.replace(OLD_LITERAL, NEW_LITERAL) == new_at5)
    report(results, "at5-single-literal", single,
           f"base AT5 {len(old_at5)} chars, new AT5 {len(new_at5)} chars; "
           f"base.replace({OLD_LITERAL}, {NEW_LITERAL}) == new: "
           f"{old_at5.replace(OLD_LITERAL, NEW_LITERAL) == new_at5}" + diff_region(old_at5, new_at5))

    changed_tests = [(fid, index + 1)
                     for fid in base_features
                     for index, (a, b) in enumerate(zip(base_features[fid]["acceptance_tests"],
                                                        new_features[fid]["acceptance_tests"]))
                     if a != b]
    counts_equal = all(len(base_features[fid]["acceptance_tests"]) == len(new_features[fid]["acceptance_tests"])
                       for fid in base_features)
    report(results, "other-acceptance-tests-unchanged", changed_tests == [("104", 5)] and counts_equal,
           f"changed (feature, AT) = {changed_tests}; per-feature AT counts equal: {counts_equal}")

    base_104, new_104 = base_features["104"], new_features["104"]
    changed_keys = sorted(k for k in set(base_104) | set(new_104) if base_104.get(k) != new_104.get(k))
    description_ok = (base_104["description"].count(OLD_DESCRIPTION_CLAUSE) == 1
                      and base_104["description"].replace(OLD_DESCRIPTION_CLAUSE, NEW_DESCRIPTION_CLAUSE)
                      == new_104["description"])
    expected_provenance = dict(base_104["acceptance_provenance"], operator_approved_amendment_1_1_5=[5])
    provenance_ok = new_104["acceptance_provenance"] == expected_provenance
    report(results, "feature-104-field-scope",
           changed_keys == ["acceptance_provenance", "acceptance_tests", "description"]
           and description_ok and provenance_ok,
           f"changed keys = {changed_keys}; description only the positive-run clause: {description_ok}; "
           f"provenance only + operator_approved_amendment_1_1_5=[5]: {provenance_ok}"
           + diff_region(base_104["description"], new_104["description"], context=30))

    other_changed = [fid for fid in base_features if fid != "104" and base_features[fid] != new_features.get(fid)]
    report(results, "other-features-unchanged",
           not other_changed and list(base_features) == list(new_features),
           f"other features differing: {other_changed}; id order identical: {list(base_features) == list(new_features)}")

    top_changed = sorted(k for k in set(base_doc) | set(new_doc)
                         if k != "features" and base_doc.get(k) != new_doc.get(k))
    report(results, "top-level-scope",
           top_changed == ["planning_note", "spec_version"]
           and new_doc["planning_note"].startswith(base_doc["planning_note"])
           and base_doc["spec_version"] == "1.1.4" and new_doc["spec_version"] == "1.1.5",
           f"changed top-level keys = {top_changed}; spec_version {base_doc['spec_version']} -> "
           f"{new_doc['spec_version']}; planning_note append-only: "
           f"{new_doc['planning_note'].startswith(base_doc['planning_note'])}")

    schema = json.load(open("schema/feature_list.schema.json", encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(new_doc), key=str)
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
        front.get("spec_version") == str(front.get("version")) == newest.get("version") == "1.1.5"
        and all(TIMESTAMP.match(str(front.get(key, ""))) for key in ("created_at", "updated_at"))
        and TIMESTAMP.match(str(newest.get("date", "")))
        and front.get("updated_at") == newest.get("date")
        and front["change_log"][1].get("version") == "1.1.4"
        and OPERATOR_VERBATIM in newest.get("summary", "")
        and "AMENDMENT A2" in newest.get("summary", "")
        and all({"version", "date", "summary"} <= set(entry) for entry in front["change_log"])
    )
    report(results, "spec-versioning-fields", bool(versioning_ok),
           f"spec_version={front.get('spec_version')} version={front.get('version')} "
           f"newest={newest.get('version')}@{newest.get('date')} updated_at={front.get('updated_at')} "
           f"previous={front['change_log'][1].get('version')} quotes {OPERATOR_VERBATIM}: "
           f"{OPERATOR_VERBATIM in newest.get('summary', '')} names A2: {'AMENDMENT A2' in newest.get('summary', '')}")
    report(results, "spec-version-lockstep", new_doc["spec_version"] == front.get("spec_version"),
           f"feature_list={new_doc['spec_version']} spec={front.get('spec_version')}")

    features = new_doc["features"]
    ids = [feature["id"] for feature in features]
    position = {fid: index for index, fid in enumerate(ids)}
    missing = [(f["id"], d) for f in features for d in f["dependencies"] if d not in position]
    out_of_order = [(f["id"], d) for f in features for d in f["dependencies"]
                    if d in position and position[d] >= position[f["id"]]]
    report(results, "dag", not missing and not out_of_order and len(set(ids)) == len(ids),
           f"missing={missing} out_of_order={out_of_order} (list order topological => acyclic)")

    stale = sum(text_field.count("phase/014-ga-track")
                for feature in features
                for text_field in [feature["description"], *feature["acceptance_tests"]])
    report(results, "no-stale-branch-in-feature-list-tests-or-description", stale == 0,
           f"remaining AT/description occurrences of the old branch: {stale} "
           f"(planning_note mentions it once, as the amendment record: "
           f"{new_doc['planning_note'].count('phase/014-ga-track')} occurrence(s))")

    frozen_status = subprocess.run(["git", "status", "--porcelain", "--", ".agent/evidence/phase-014-activation/"],
                                   capture_output=True, text=True)
    frozen_diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", ".agent/evidence/phase-014-activation/"])
    report(results, "frozen-activation-infrastructure-unchanged",
           frozen_status.returncode == 0 and frozen_status.stdout == "" and frozen_diff.returncode == 0,
           f"git status --porcelain entries: {len(frozen_status.stdout.splitlines())}; "
           f"git diff --quiet HEAD rc={frozen_diff.returncode}")

    scratch = Path(tempfile.mkdtemp(prefix="a2-at5-sim-"))
    try:
        clone = scratch / "clone"
        cloned = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", ".", str(clone)],
                                capture_output=True, text=True)
        if cloned.returncode != 0:
            raise VerificationSetupError(f"git clone failed: {cloned.stderr.strip()}")
        workflow = clone / ".github/workflows/compliance.yml"
        workflow.write_text(workflow.read_text(encoding="utf-8") + JOB_YAML, encoding="utf-8")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=clone, capture_output=True,
                              text=True, check=True).stdout.strip()
        jobs_ok = [{"name": "validate", "databaseId": 1, "conclusion": "success"},
                   {"name": "convergent_review", "databaseId": 7, "conclusion": "success"}]
        good = {"headSha": head, "headBranch": "phase/014-104-sandbox-ci", "conclusion": "success", "jobs": jobs_ok}
        cases = [
            ("amended AT5, well-formed run on phase/014-104-sandbox-ci", new_at5, good, 0),
            ("amended AT5, run on phase/014-ga-track", new_at5, dict(good, headBranch="phase/014-ga-track"), 1),
            ("amended AT5, run on main", new_at5, dict(good, headBranch="main"), 1),
            ("amended AT5, headSha not an ancestor of HEAD", new_at5, dict(good, headSha="c" * 40), 1),
            ("amended AT5, run conclusion failure", new_at5, dict(good, conclusion="failure"), 1),
            ("base AT5, well-formed run on phase/014-104-sandbox-ci", old_at5, good, 1),
        ]
        rows = []
        for label, command, run, want in cases:
            rc = simulate_at5(command, clone, run)
            rows.append((label, rc, want))
        simulation_ok = all((rc == 0) == (want == 0) for _, rc, want in rows)
        detail = f"scratch clone at HEAD {head[:7]} + simulated convergent_review job" + "".join(
            f"\n    {'OK ' if (rc == 0) == (want == 0) else 'BAD'} {label}: rc={rc} want={'0' if want == 0 else 'nonzero'}"
            for label, rc, want in rows)
        report(results, "at5-simulation", simulation_ok, detail)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print(f"SUMMARY: {sum(results)} passed, {len(results) - sum(results)} failed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
