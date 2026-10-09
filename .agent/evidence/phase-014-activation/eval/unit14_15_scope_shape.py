#!/usr/bin/env python3
"""Units 14 and 15: scope guard and evidence shape."""
import os, re, subprocess, sys
print("== UNIT 14 scope guard ==")
st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
paths = [l[3:] for l in st.splitlines() if l.strip()]
ALLOWED = (".agent/", "docs/planning/", "CHANGELOG.md")
FORBIDDEN = ("tools/", "standard/", "ecosystem/", "methodology/", "registry/", "schema/", ".github/", "NIZAM.json", "README", "CONTEXT", "docs/guide", "docs/nips", "bootstrap.sh")
out = [p for p in paths if not (p == "CHANGELOG.md" or p.startswith(ALLOWED[:2]))]
forb = [p for p in paths if p.startswith(FORBIDDEN)]
print("changed/untracked path count:", len(paths))
print("status prefix summary:", {k: sum(p.startswith(k) for p in paths) for k in (".agent/", "docs/planning/")}, "CHANGELOG.md" in paths)
print("paths outside .agent/, docs/planning/, CHANGELOG.md:", out)
print("paths under forbidden prefixes:", forb)
deleted = [l for l in st.splitlines() if l[:2].strip() in ("D", "R")]
print("deleted/renamed entries:", deleted)
# also check staged state and that no tracked file outside allowlist differs from HEAD
diff = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True).stdout.split()
print("tracked files differing from HEAD:", diff)
staged = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True).stdout.split()
print("staged files:", staged)
ok14 = not out and not forb and not deleted and not staged
print("UNIT 14:", "OK" if ok14 else "FAIL")

print("== UNIT 15 evidence shape ==")
roots = [".agent/evidence/backlog-reconciliation-2026-10-08", ".agent/evidence/phase-014-activation"]
exc = []; n = 0
for r in roots:
    for d, _, fs in os.walk(r):
        for f in sorted(fs):
            if not f.endswith(".txt"): continue
            p = os.path.join(d, f)
            if p.endswith(("eval/unit14_15_scope_shape.txt", "eval/unit14_15_rerun.txt")):
                print("   (skipping the in-flight capture of this very script; checked after the run by the Evaluator)"); continue
            n += 1
            lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            first = lines[0] if lines else ""
            nonempty = [l for l in lines if l.strip()]
            last = nonempty[-1] if nonempty else ""
            why = []
            if not lines: why.append("empty")
            if re.search(r"/home|\.tmp|scratchpad|/tmp/|/Users/", first): why.append("first line has non-repo-relative path")
            if first.startswith("/"): why.append("first line absolute")
            if not re.fullmatch(r"EXIT:\d+", last): why.append("last line is not EXIT:<code>: %r" % last[:60])
            if why: exc.append((p, why))
print("*.txt files inspected:", n)
print("exceptions:", len(exc))
for p, w in exc: print("   EXC", p, w)
# control: the checker flags a synthetic bad first line
print("control flags '/home/x' first line:", bool(re.search(r"/home|\.tmp|scratchpad", "python3 /home/x/y.py")))
print("UNIT 15:", "OK" if not exc else "EXCEPTIONS LISTED")
sys.exit(0 if ok14 and not exc else 1)
