#!/usr/bin/env python3
"""Unit 10: extract feature 102 AT7's pin table, verify against disk, run AT7 verbatim, add negative control."""
import hashlib, json, re, subprocess, sys
fl = json.load(open(".agent/feature_list_014.json"))
f102 = [f for f in fl["features"] if f["id"] == "102"][0]
at7 = f102["acceptance_tests"][6]
assert "frozen acceptance infrastructure" in at7, "AT7 index not the pin test"
pins = dict(re.findall(r"'(\.agent/evidence/phase-014-activation/[^']+)':'([0-9a-f]{64})'", at7))
print("pins extracted:", len(pins))
bad = 0
for path, want in sorted(pins.items()):
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    ok = got == want
    bad += not ok
    print(("MATCH   " if ok else "MISMATCH ") + path + " " + got)
# every file in the frozen dir (excluding eval/) is covered by a pin?
import os
disk = sorted(os.path.join(d, n) for d, _, ns in os.walk(".agent/evidence/phase-014-activation") if "/eval" not in d for n in ns)
print("files on disk outside eval/:", len(disk), "unpinned:", [p for p in disk if p not in pins])
# AT7 verbatim command
cmd = at7
rc = subprocess.run(["bash", "-c", cmd]).returncode
print("AT7 verbatim command rc=%d" % rc)
# negative control: same command with one wrong hash must fail
first = next(iter(pins.values()))
neg = cmd.replace(first, "0" * 64, 1)
rc_neg = subprocess.run(["bash", "-c", neg], capture_output=True).returncode
print("negative control (one pin zeroed) rc=%d (must be non-zero)" % rc_neg)
ok = bad == 0 and len(pins) == 7 and rc == 0 and rc_neg != 0
print("RESULT:", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
