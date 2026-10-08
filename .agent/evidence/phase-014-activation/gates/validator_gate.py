#!/usr/bin/env python3
"""Phase-014 acceptance gate: run tools/validate.sh with its exit status captured.

Frozen at phase-014 activation (Planner-authored acceptance infrastructure, the
.agent/evidence/098/verify_release_prep.py precedent). No phase-014 feature contract
may modify anything under .agent/evidence/phase-014-activation/.

Run from the repository root:

    python3 .agent/evidence/phase-014-activation/gates/validator_gate.py [--payload]

The gate PASSES (exit 0) only when every condition holds:

  G1  the validator's own exit status is 0 -- read from the process, never inferred
      from printed text (a `validate.sh | grep SUMMARY` pipeline reports grep's
      status and loses the validator's);
  G2  exactly one SUMMARY line is printed, and it reports 0 failed;
  G3  the SUMMARY passed-count equals the number of `[Cn] PASS` lines;
  G4  no `[Cn] FAIL` line is printed;
  G5  every check id that PASSED in the activation-time baseline still PASSES, so a
      silently dropped or renamed check fails the gate while an authorized added
      check does not.

The check count is deliberately not hard-coded: a phase-014 feature may legitimately
change it (none is planned to -- C17 is earmarked by NIP-0003).

Exit codes: 0 pass; 1 gate failure; 2 usage or unreadable baseline.
The --command option substitutes the validator invocation; it exists only so the
probe script can drive synthetic validators, and no acceptance test uses it.
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(".agent/evidence/phase-014-activation")
BASELINES = {
    "default": (BASE_DIR / "validate.txt", re.compile(r"^SUMMARY: (\d+) passed, (\d+) failed$", re.M)),
    "payload": (BASE_DIR / "validate_payload.txt",
                re.compile(r"^SUMMARY \(payload mode\): (\d+) passed, (\d+) failed$", re.M)),
}
PASS_RE = re.compile(r"^\[(C\d+)\] PASS\b", re.M)
FAIL_RE = re.compile(r"^\[(C\d+)\] FAIL\b", re.M)


class GateUsageError(Exception):
    """Raised when the gate cannot evaluate (missing or malformed baseline)."""


def baseline_pass_ids(path: Path) -> set[str]:
    """Return the check ids that passed in a Section-5-shaped baseline capture."""
    if not path.is_file():
        raise GateUsageError(f"baseline not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or not lines[0].startswith("bash tools/validate.sh") or lines[-1] != "EXIT:0":
        raise GateUsageError(f"baseline is not a passing 04 Section 5 capture: {path}")
    ids = set(PASS_RE.findall("\n".join(lines[1:-1])))
    if not ids:
        raise GateUsageError(f"baseline records no passing checks: {path}")
    return ids


def main() -> int:
    """Evaluate gate conditions G1-G5 and print one line per condition."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--payload", action="store_true", help="gate tools/validate.sh --payload")
    parser.add_argument("--command", help="probe-only: substitute validator command line")
    args = parser.parse_args()
    mode = "payload" if args.payload else "default"
    baseline_path, summary_re = BASELINES[mode]
    try:
        base_ids = baseline_pass_ids(baseline_path)
    except GateUsageError as exc:
        print(f"GATE USAGE: {exc}")
        return 2

    if args.command:
        argv = shlex.split(args.command)
    else:
        argv = ["bash", "tools/validate.sh"] + (["--payload"] if args.payload else [])
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    out = proc.stdout + proc.stderr
    summaries = summary_re.findall(out)
    passed = set(PASS_RE.findall(out))
    pass_lines = len(PASS_RE.findall(out))
    failed = FAIL_RE.findall(out)

    results = [
        ("G1 validator exit status is 0", proc.returncode == 0, f"exit {proc.returncode}"),
        ("G2 exactly one SUMMARY line reporting 0 failed",
         len(summaries) == 1 and summaries[0][1] == "0", f"summaries={summaries}"),
        ("G3 SUMMARY passed-count equals [Cn] PASS lines",
         len(summaries) == 1 and int(summaries[0][0]) == pass_lines,
         f"summary={summaries} pass_lines={pass_lines}"),
        ("G4 no [Cn] FAIL line", not failed, f"failed={failed}"),
        ("G5 every baseline-passing check still passes", base_ids <= passed,
         f"missing={sorted(base_ids - passed)}"),
    ]
    ok = True
    print(f"validator_gate ({mode} mode): {' '.join(argv)}")
    for label, cond, detail in results:
        print(("PASS " if cond else "FAIL ") + label + ("" if cond else f" -- {detail}"))
        ok = ok and cond
    print(f"GATE: {'PASS' if ok else 'FAIL'} ({len(passed)} checks passing; baseline {len(base_ids)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
