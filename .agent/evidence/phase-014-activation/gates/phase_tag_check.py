#!/usr/bin/env python3
"""Phase-014 acceptance helper: assert no tag was created during the phase.

Frozen at phase-014 activation (Planner-authored acceptance infrastructure). No
phase-014 feature contract may modify anything under
.agent/evidence/phase-014-activation/.

Run from the repository root:

    python3 .agent/evidence/phase-014-activation/gates/phase_tag_check.py

It replaces the fixed-version tag-absence test (`git rev-parse -q --verify
refs/tags/v1.5.0; test $? -eq 1`), which broke as soon as an out-of-phase release
cut the named version and said nothing about any other tag. This check reads the
tag set recorded at activation (.agent/evidence/phase-014-activation/tag-baseline.txt,
a 04 Section 5 capture of `git tag -l`) and requires the current tag set to add
nothing to it. Phase 014 prepares no release, and the pipeline never self-tags.

PRECONDITION: the local tag set must be current. A tag cut on the remote but never fetched
is invisible to `git tag -l`, so the acceptance test runs `git fetch --tags --quiet origin`
first (feature 102 AT4: `git fetch --tags --quiet origin && python3 <this script>`); an
offline fetch failure fails the test rather than passing it blind.

The single exemption is the documented ephemeral namespace `e2e-*`: tools/e2e_bootstrap_test.sh
creates an annotated tag of that shape on the working checkout and deletes it on
exit, so a concurrent or interrupted harness run is not a release act.

Exit codes: 0 no new tag; 1 at least one tag was created since activation; 2 usage
or unreadable baseline. --baseline and --current-tags exist only for the probe script.
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

BASELINE = Path(".agent/evidence/phase-014-activation/tag-baseline.txt")
EPHEMERAL = "e2e-*"


def read_baseline(path: Path) -> set[str]:
    """Return the tag names recorded in a Section-5-shaped `git tag -l` capture."""
    if not path.is_file():
        raise SystemExit(f"phase_tag_check: baseline not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or lines[0] != "git tag -l" or lines[-1] != "EXIT:0":
        raise SystemExit(f"phase_tag_check: baseline is not a passing `git tag -l` capture: {path}")
    tags = {ln.strip() for ln in lines[1:-1] if ln.strip()}
    if "v1.4.0" not in tags:
        raise SystemExit("phase_tag_check: baseline lacks v1.4.0, the latest release at activation")
    return tags


def main() -> int:
    """Compare the current tag set with the activation baseline."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", default=str(BASELINE), help="probe-only override")
    parser.add_argument("--current-tags", help="probe-only: comma-separated substitute tag set")
    args = parser.parse_args()
    try:
        base = read_baseline(Path(args.baseline))
    except SystemExit as exc:
        print(exc)
        return 2
    if args.current_tags is not None:
        current = {t for t in args.current_tags.split(",") if t}
    else:
        proc = subprocess.run(["git", "tag", "-l"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"phase_tag_check: git tag -l failed: {proc.stderr.strip()}")
            return 2
        current = set(proc.stdout.split())
    new = sorted(t for t in current - base if not fnmatch.fnmatch(t, EPHEMERAL))
    print(f"phase_tag_check: baseline {len(base)} tags; current {len(current)}; new since activation: {new}")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
