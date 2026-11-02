#!/usr/bin/env python3
"""Checker for NIP-0005 authoring acceptance tests AT1-AT5.

Usage: check_nip0005.py [--at1|--at2|--at3|--at4|--at5]   (default: all)
Exits 0 only if every selected assertion holds; otherwise exits 1 and names
each failed assertion. Assertions are not weakened to pass.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
NIP = REPO / "docs/nips/NIP-0005-executable-claim-binding.md"
BASE = "1dfa47f2f006d92e661aa2ec52b4dd0e1dd0bcdd"
FAILS = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def text():
    return NIP.read_text(encoding="utf-8")


def frontmatter():
    t = text()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1)) if m else None


def at1():
    print("AT1 frontmatter")
    try:
        fm = frontmatter()
    except yaml.YAMLError as e:
        check(False, f"AT1 frontmatter parses as YAML ({e.__class__.__name__})")
        return
    check(isinstance(fm, dict), "AT1 frontmatter parses as YAML mapping")
    fm = fm or {}
    check(fm.get("id") == "nip-0005-executable-claim-binding",
          f"AT1 id == nip-0005-executable-claim-binding (got {fm.get('id')!r})")
    check(fm.get("status") == "proposed", f"AT1 status == proposed (got {fm.get('status')!r})")


def at2():
    print("AT2 amendment headings")
    t = text()
    for h in ("A1", "A2", "A3", "A4"):
        check(re.search(rf"^### {h}\b", t, re.M) is not None, f"AT2 heading '### {h}' present")


def status_section():
    t = text()
    m = re.search(r"^## Status\n(.*?)(?=^## )", t, re.S | re.M)
    return m.group(1) if m else ""


# Affirmative assertions that a gate/proposal is active, adopted or accepted.
ASSERT_RE = re.compile(r"\b(is|are|was|been|now|becomes?)\s+(now\s+)?(active|adopted|accepted|in force|in effect)\b", re.I)
NEG_RE = re.compile(r"\b(not|no|never|awaiting|pending|until|requires?|requiring|cannot|does not|do not|nothing)\b", re.I)


def at3():
    print("AT3 status and no affirmative activation claims")
    check("awaiting H-NIP acceptance" in status_section(),
          "AT3 Status section contains 'awaiting H-NIP acceptance'")
    bad = []
    for n, line in enumerate(text().splitlines(), 1):
        for m in ASSERT_RE.finditer(line):
            # Look at the sentence containing the match for a negation or pending qualifier.
            start = max(line.rfind(".", 0, m.start()), 0)
            sentence = line[start:m.end() + 40]
            if not NEG_RE.search(sentence):
                bad.append(f"line {n}: {line.strip()[:110]}")
    check(not bad, "AT3 no unqualified affirmative claim that a gate is active/adopted/accepted"
          + ("" if not bad else " -- offending: " + " | ".join(bad)))


def at4():
    print("AT4 observations table")
    t = text()
    m = re.search(r"^### 1\.1.*?\n\| Observation.*?\n\| ---.*?\n((?:\|.*\n)+)", t, re.S | re.M)
    if not m:
        check(False, "AT4 observations table located under 1.1")
        return
    rows = [r for r in m.group(1).splitlines() if r.startswith("|")]
    check(len(rows) == 4, f"AT4 table has 4 data rows (got {len(rows)})")
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        ok = len(cells) == 2 and cells[1] != ""
        check(ok, f"AT4 result cell non-empty: {cells[0][:50]!r}")
        if not ok:
            continue
    table = m.group(1)
    for n in ("5", "8", "4", "23", "56", "33"):
        check(re.search(rf"(?<![\d.])\b{n}\b(?![\d.])", table) is not None,
              f"AT4 integer {n} appears as a standalone integer in the table")
    for placeholder in ("TODO", "TBD", "XXX", "<fill", "PLACEHOLDER"):
        check(placeholder.lower() not in table.lower(), f"AT4 no placeholder '{placeholder}'")


def at5():
    print(f"AT5 changed paths {BASE}..HEAD and worktree")
    out = subprocess.run(["git", "diff", "--name-only", f"{BASE}..HEAD"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    wt = subprocess.run(["git", "diff", "--name-only"], cwd=REPO,
                        capture_output=True, text=True, check=True).stdout
    paths = [p for p in (out + wt).splitlines() if p]
    print("  changed:", ", ".join(sorted(set(paths))) or "(none)")
    bad = [p for p in paths if p.startswith(".nizam/")]
    check(not bad, "AT5 no path beginning .nizam/" + ("" if not bad else f" -- {bad}"))


def main(argv):
    picks = {a.lstrip("-") for a in argv} or {"at1", "at2", "at3", "at4", "at5"}
    for name, fn in (("at1", at1), ("at2", at2), ("at3", at3), ("at4", at4), ("at5", at5)):
        if name in picks:
            fn()
    if FAILS:
        print(f"RESULT: FAIL ({len(FAILS)} assertion(s) failed)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
