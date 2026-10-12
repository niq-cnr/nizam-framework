#!/usr/bin/env python3
"""Phase-014 scope-budget measurement (spec 1.1.4, "Scope budget measurement";
rule row 4a added in spec 1.1.6).

Replayable from the repository root. For each feature commit range it
classifies every changed path into exactly one path class and prints two
totals:

* BUDGET_COUNTED_LINES -- product, contract, verdict, audit-deliverable and
  planning lines. This is the figure the Scope Budget Protocol's per-feature
  and cumulative checks use in phase 014.
* EVIDENCE_LINES -- raw evidence captures and verification helpers under
  ``.agent/evidence/``, plus (spec 1.1.6, row 4a) every file under
  ``.agent/validator/`` whose name does not end in ``.json`` (raw captures such
  as Mode B re-run captures; verdicts are JSON). Tracked separately and never
  gated. A ``.json`` file in a subdirectory of ``.agent/validator/`` still
  matches no rule and stays UNCLASSIFIED (fail closed).

``.agent/run_state.json`` is EXCLUDED (coordination churn: the Orchestrator's
own ledger, which grows with every gate event independent of feature scope,
and which records the measurement itself).

Lines are ``insertions + deletions`` from ``git diff --numstat --no-renames``
(binary files count 0 and are reported). When a range has no HEAD
(``LABEL=BASE..``), the working tree is compared with BASE and untracked,
non-ignored files are added at their line counts.

The classification is first-match-wins over an ordered rule list. A path that
matches no rule is UNCLASSIFIED: it is listed, and the script exits 3, so no
line is silently dropped or silently counted.

Usage:
    python3 .agent/evidence/scope-budget-014/measure.py \
        --range 099=483f016..88959c9 --range 103=88959c9..1c06720 [--files]

Exit codes: 0 = measured, every path classified; 2 = usage or git error;
3 = measured, but at least one path is unclassified.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

EXCLUDED = "excluded/run_state"
EVIDENCE = "evidence"
UNCLASSIFIED = "unclassified"

# Ordered (class, kind, pattern) rules; first match wins.
#   kind "exact"  -> path == pattern
#   kind "prefix" -> path.startswith(pattern)
#   kind "regex"  -> re.fullmatch(pattern, path)
RULES: List[Tuple[str, str, str]] = [
    (EXCLUDED, "exact", ".agent/run_state.json"),
    (EVIDENCE, "prefix", ".agent/evidence/"),
    ("budget/contract", "prefix", ".agent/contracts/"),
    ("budget/verdict", "regex", r"\.agent/(qa|validator)/[^/]+\.json"),
    # Spec 1.1.6 row 4a: non-JSON files at any depth under .agent/validator/
    # are raw evidence captures (verdicts are JSON). Disjoint from the verdict
    # rule above, so the order between the two does not matter.
    (EVIDENCE, "regex", r"\.agent/validator/.+(?<!\.json)"),
    ("budget/audit-deliverable", "prefix", ".agent/audits/"),
    ("budget/planning", "regex", r"\.agent/product_spec[^/]*\.md"),
    ("budget/planning", "regex", r"\.agent/feature_list[^/]*\.json"),
    ("budget/planning", "prefix", "docs/planning/"),
    ("budget/planning", "exact", "AGENTS.md"),
    ("budget/planning", "exact", "DEBT.md"),
    ("budget/product", "prefix", "tools/"),
    ("budget/product", "prefix", "ecosystem/"),
    ("budget/product", "prefix", "standard/"),
    ("budget/product", "prefix", "methodology/"),
    ("budget/product", "prefix", "schema/"),
    ("budget/product", "prefix", "templates/"),
    ("budget/product", "prefix", "docs/guide/"),
    ("budget/product", "exact", "NIZAM.json"),
    ("budget/product", "exact", "CHANGELOG.md"),
    # Planner extension: the rest of the tracked repository payload, so that
    # no product path is unclassified (104 edits .github/, 107 edits docs/nips/).
    ("budget/product-ext", "prefix", ".github/"),
    ("budget/product-ext", "prefix", "registry/"),
    ("budget/product-ext", "prefix", "docs/"),
    ("budget/product-ext", "exact", "README.md"),
    ("budget/product-ext", "exact", "CONTEXT.md"),
    ("budget/product-ext", "exact", "LICENSE"),
    ("budget/product-ext", "exact", "bootstrap.sh"),
    ("budget/product-ext", "exact", ".gitignore"),
]

CLASS_ORDER = [
    "budget/product",
    "budget/product-ext",
    "budget/contract",
    "budget/verdict",
    "budget/audit-deliverable",
    "budget/planning",
    EVIDENCE,
    EXCLUDED,
    UNCLASSIFIED,
]


class MeasureError(Exception):
    """Raised on a usage or git failure (exit 2)."""


def classify(path: str) -> str:
    """Return the path class of a repo-relative path (first matching rule).

    Args:
        path: Repository-relative POSIX path.

    Returns:
        The class name, or UNCLASSIFIED when no rule matches.
    """
    for class_name, kind, pattern in RULES:
        if kind == "exact" and path == pattern:
            return class_name
        if kind == "prefix" and path.startswith(pattern):
            return class_name
        if kind == "regex" and re.fullmatch(pattern, path):
            return class_name
    return UNCLASSIFIED


def run_git(arguments: List[str]) -> bytes:
    """Run a git command and return stdout, raising MeasureError on failure.

    Args:
        arguments: Arguments after ``git``.

    Returns:
        Raw stdout bytes.
    """
    completed = subprocess.run(["git", *arguments], capture_output=True)
    if completed.returncode != 0:
        raise MeasureError(
            "git " + " ".join(arguments) + " failed: "
            + completed.stderr.decode("utf-8", "replace").strip()
        )
    return completed.stdout


def resolve(revision: str) -> str:
    """Resolve a revision to a full commit SHA.

    Args:
        revision: Any commit-ish.

    Returns:
        The 40-hex SHA.
    """
    return run_git(["rev-parse", "--verify", revision + "^{commit}"]).decode().strip()


def numstat(base: str, head: Optional[str]) -> List[Tuple[str, int, bool]]:
    """Return (path, lines, is_binary) for every path changed in the range.

    Args:
        base: Base commit SHA.
        head: Head commit SHA, or None for the working tree plus untracked files.

    Returns:
        One tuple per path.
    """
    arguments = ["diff", "--numstat", "--no-renames", "-z", base]
    if head is not None:
        arguments.append(head)
    records: List[Tuple[str, int, bool]] = []
    for record in run_git(arguments).split(b"\0"):
        if not record:
            continue
        added, deleted, path = record.decode("utf-8", "surrogateescape").split("\t", 2)
        if added == "-" or deleted == "-":
            records.append((path, 0, True))
        else:
            records.append((path, int(added) + int(deleted), False))
    if head is None:
        untracked = run_git(["ls-files", "--others", "--exclude-standard", "-z"])
        for raw_path in untracked.split(b"\0"):
            if not raw_path:
                continue
            path = raw_path.decode("utf-8", "surrogateescape")
            with open(path, "rb") as handle:
                content = handle.read()
            if b"\0" in content:
                records.append((path, 0, True))
            else:
                records.append((path, len(content.splitlines()), False))
    return records


def evidence_group(path: str) -> str:
    """Group an evidence path by its first directory under .agent/evidence/.

    Args:
        path: A path in the evidence class.

    Returns:
        ``.agent/evidence/<first component>`` (a trailing ``/`` marks a directory).
    """
    parts = path.split("/")
    return "/".join(parts[:3]) + ("/" if len(parts) > 3 else "")


def measure(label: str, spec: str, list_files: bool) -> Tuple[Dict[str, int], int]:
    """Measure one LABEL=BASE..HEAD range, print its report, return totals.

    Args:
        label: Feature label, e.g. ``099``.
        spec: ``BASE..HEAD`` or ``BASE..`` (working tree).
        list_files: Print per-file classification for non-evidence paths.

    Returns:
        (lines per class, number of unclassified paths).
    """
    if ".." not in spec:
        raise MeasureError(f"range for {label!r} must be BASE..HEAD or BASE..: {spec!r}")
    base_revision, head_revision = spec.split("..", 1)
    base = resolve(base_revision)
    head = resolve(head_revision) if head_revision else None
    records = numstat(base, head)
    lines: Dict[str, int] = defaultdict(int)
    files: Dict[str, int] = defaultdict(int)
    binaries = 0
    evidence_groups: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    unclassified_paths: List[str] = []
    detail: List[Tuple[str, str, int]] = []
    for path, count, is_binary in records:
        class_name = classify(path)
        lines[class_name] += count
        files[class_name] += 1
        binaries += 1 if is_binary else 0
        if class_name == EVIDENCE:
            group = evidence_groups[evidence_group(path)]
            group[0] += 1
            group[1] += count
        else:
            detail.append((class_name, path, count))
        if class_name == UNCLASSIFIED:
            unclassified_paths.append(path)

    head_text = head if head is not None else "WORKTREE+untracked"
    print(f"== {label}: {base_revision}..{head_revision or 'WORKTREE'}")
    print(f"   resolved {base}..{head_text}")
    print(f"   paths={len(records)} binary_paths={binaries}")
    print(f"   {'class':<26}{'files':>7}{'lines':>8}")
    for class_name in CLASS_ORDER:
        print(f"   {class_name:<26}{files[class_name]:>7}{lines[class_name]:>8}")
    if list_files:
        print("   -- non-evidence paths (class, lines, path)")
        for class_name, path, count in sorted(detail, key=lambda d: (CLASS_ORDER.index(d[0]), d[1])):
            print(f"   {class_name:<26}{count:>8}  {path}")
        print("   -- evidence groups (files, lines, group)")
        for group_name in sorted(evidence_groups):
            group_files, group_lines = evidence_groups[group_name]
            print(f"   {'evidence':<26}{group_files:>7}{group_lines:>8}  {group_name}")
    budget = sum(v for k, v in lines.items() if k.startswith("budget/"))
    overhead = budget - lines["budget/product"] - lines["budget/product-ext"]
    all_paths = sum(count for _, count, _ in records)
    reconciled = budget + lines[EVIDENCE] + lines[EXCLUDED] + lines[UNCLASSIFIED]
    if reconciled != all_paths:
        raise MeasureError(f"{label}: class totals {reconciled} != all-paths total {all_paths}")
    product = lines["budget/product"] + lines["budget/product-ext"]
    print(f"   PRODUCT_LINES={product}")
    print(f"   PROCESS_OVERHEAD_LINES={overhead}  (contract + verdict + audit-deliverable + planning)")
    print(f"   BUDGET_COUNTED_LINES={budget}")
    print(f"   EVIDENCE_LINES={lines[EVIDENCE]}")
    print(f"   EXCLUDED_LINES={lines[EXCLUDED]}")
    print(f"   UNCLASSIFIED_LINES={lines[UNCLASSIFIED]}")
    print(f"   ALL_PATHS_LINES={all_paths}  (= budget {budget} + evidence {lines[EVIDENCE]}"
          f" + excluded {lines[EXCLUDED]} + unclassified {lines[UNCLASSIFIED]})")
    for path in unclassified_paths:
        print(f"   UNCLASSIFIED: {path}")
    totals = dict(lines)
    totals["_budget"] = budget
    totals["_all"] = all_paths
    return totals, len(unclassified_paths)


def main() -> int:
    """Parse arguments, measure every range, print the combined totals.

    Returns:
        Process exit code (0, 2 or 3).
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--range", dest="ranges", action="append", required=True,
                        metavar="LABEL=BASE..HEAD",
                        help="feature label and commit range; omit HEAD for the working tree")
    parser.add_argument("--files", action="store_true",
                        help="list every non-evidence path with its class")
    arguments = parser.parse_args()
    try:
        top_level = run_git(["rev-parse", "--show-toplevel"]).decode().strip()
        if os.path.realpath(os.getcwd()) != os.path.realpath(top_level):
            raise MeasureError(f"run from the repository root ({top_level})")
        grand: Dict[str, int] = defaultdict(int)
        unclassified = 0
        for item in arguments.ranges:
            if "=" not in item:
                raise MeasureError(f"--range must be LABEL=BASE..HEAD: {item!r}")
            label, spec = item.split("=", 1)
            totals, missing = measure(label, spec, arguments.files)
            unclassified += missing
            for key, value in totals.items():
                grand[key] += value
    except MeasureError as error:
        print(f"measure.py: {error}", file=sys.stderr)
        return 2
    if len(arguments.ranges) > 1:
        print("== combined")
        print(f"   BUDGET_COUNTED_LINES={grand['_budget']}")
        print(f"   EVIDENCE_LINES={grand[EVIDENCE]}")
        print(f"   EXCLUDED_LINES={grand[EXCLUDED]}")
        print(f"   UNCLASSIFIED_LINES={grand[UNCLASSIFIED]}")
        print(f"   ALL_PATHS_LINES={grand['_all']}")
    return 3 if unclassified else 0


if __name__ == "__main__":
    sys.exit(main())
