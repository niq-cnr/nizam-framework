#!/usr/bin/env python3
"""Read-only pin, byte-identity, regex, and S01 checks. Does not run validate.sh."""

from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

os.chdir(lib.REPO)
bad: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + label + ((" " + detail) if detail else ""))
    if not ok:
        bad.append(label)


document = lib.contract()
pin = document["design_notes"]["pinned_interface"]
feature = next(
    item for item in __import__("json").load(open(".agent/feature_list_014.json"))["features"] if item["id"] == "106"
)
tests = [item for item in document["verification"] if not item.get("supplementary")]
check(
    "acceptance tests byte-identical and in order",
    [item["acceptance_test"] for item in tests] == feature["acceptance_tests"]
    and [item["command"] for item in tests] == feature["acceptance_tests"],
)
check("estimated_lines 750", document["estimated_lines"] == 750 == feature["estimated_lines"])
check("revision field 0", document["design_notes"]["revision"].startswith("Revision 0"))
check("status proposed", document["status"] == "proposed")
check("approvals still false", document["approvals"] == {
    "revisions": 0,
    "validator_mode_a": False,
    "evaluator_contract_review": False,
})

base_validate = lib.git_show(lib.REPO, lib.A + ":tools/validate.sh")
check("help anchor once", base_validate.count(pin["help_anchor"]) == 1)
check("problem anchor once", base_validate.count(pin["problem_anchor"]) == 1)
check("fail echo once", base_validate.count(pin["fail_echo"]) == 1)
check("fragment absent from help addition", pin["failure_fragment"] not in pin["help_addition"])
check("fragment once in subset block", pin["subset_block"].count(pin["failure_fragment"]) == 1)
problems_line = next(line for line in pin["subset_block"].splitlines() if pin["failure_fragment"] in line)
check("subset failure line is problems.append", problems_line.lstrip().startswith("problems.append("))
check("ablation indent is eight spaces", problems_line.startswith("        problems.append("), repr(problems_line[:20]))

base_nizam = lib.git_show(lib.REPO, lib.A + ":NIZAM.json")
old = '"authoritative_source": "methodology/00_planning.md"'
check("planning authoritative_source once", base_nizam.count(old) == 1)
check("preflight needle once", base_nizam.count(pin["nizam_needle"]) == 1)

moved = "methodology/00_planning_moved.md"
plain = "methodology/00_planning.md"
check(
    "planning.md regex does not match the moved path",
    re.search(r"methodology/00_planning\.md", moved) is None,
)
check(
    "planning.md regex matches the real module",
    re.search(r"methodology/00_planning\.md", plain) is not None,
)
check(
    "moved regex does not match the real module",
    re.search(r"methodology/00_planning_moved\.md", plain) is None,
)
sample = (
    "capabilities[3] (planning) -> methodology/00_planning.md "
    "is not the authoritative_source of any NIZAM.json capability"
)
check("sample detail matches fragment and module", pin["failure_fragment"] in sample and re.search(r"methodology/00_planning\.md", sample) is not None)
check("sample detail does not match the moved regex", re.search(r"methodology/00_planning_moved\.md", sample) is None)

s01 = lib.verification("s01-contract-valid.txt")["command"]
proc = lib.run(s01, lib.REPO, timeout=120)
print(lib.format_result("S01", proc))
check("S01 exit 0", proc.returncode == 0)

print("problems:", bad)
sys.exit(1 if bad else 0)
