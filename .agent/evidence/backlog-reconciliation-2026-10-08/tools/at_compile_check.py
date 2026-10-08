#!/usr/bin/env python3
"""Syntax-check every acceptance-test command in .agent/feature_list_014.json.

Run from the repository root:

    python3 .agent/evidence/backlog-reconciliation-2026-10-08/tools/at_compile_check.py

For every acceptance test: (1) `bash -n -c <command>` must accept the shell syntax;
(2) every embedded Python body -- `python3 -c "<code>"` and `--py-mutate "<code>"` -- must
compile with compile(). The test commands follow a quoting discipline that makes bash's
double-quote processing an identity on the embedded code (no `"`, `$`, backtick or
backslash-backslash inside a double-quoted Python body); that discipline is asserted too,
so the compiled text is exactly the text Python receives. The frozen gate scripts are
compiled in memory as well. Exit 0 only if everything compiles.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys

BODY = re.compile(r'(?:python3 -c|--py-mutate) "([^"]*)"')
bad = 0
total_bodies = 0
doc = json.load(open(".agent/feature_list_014.json", encoding="utf-8"))
for f in doc["features"]:
    for i, at in enumerate(f["acceptance_tests"], 1):
        label = f"{f['id']} AT{i}"
        sh = subprocess.run(["bash", "-n", "-c", at], capture_output=True, text=True)
        bodies = BODY.findall(at)
        problems = [] if sh.returncode == 0 else [f"bash -n: {sh.stderr.strip()}"]
        for n, code in enumerate(bodies, 1):
            total_bodies += 1
            if re.search(r"\$[A-Za-z_{(]|`|\\\\", code):
                problems.append(f"body {n}: violates the quoting discipline")
            try:
                compile(code, f"<{label} body {n}>", "exec")
            except SyntaxError as exc:
                problems.append(f"body {n}: SyntaxError {exc.msg} at {exc.lineno}:{exc.offset}")
        print(f"{'OK  ' if not problems else 'BAD '} {label:<9} bash-syntax ok={sh.returncode == 0} python-bodies={len(bodies)}"
              + ("" if not problems else " -- " + "; ".join(problems)))
        bad += bool(problems)
for path in sorted(glob.glob(".agent/evidence/phase-014-activation/gates/*.py")):
    try:
        compile(open(path, encoding="utf-8").read(), path, "exec")  # in memory: writes no .pyc
        print(f"OK   compile {path}")
    except SyntaxError as exc:
        print(f"BAD  compile {path} -- {exc.msg}")
        bad += 1
n_at = sum(len(f["acceptance_tests"]) for f in doc["features"])
print(f"COMPILE CHECK: {n_at} acceptance tests, {total_bodies} embedded Python bodies; {bad} problem(s)")
sys.exit(1 if bad else 0)
