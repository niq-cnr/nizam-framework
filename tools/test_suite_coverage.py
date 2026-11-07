#!/usr/bin/env python3
"""Require every top-level tools/test_*.py suite to be run by CI or explicitly excluded.

SQA-integrity-005. CI reaches dedicated suites only through explicit invocations; a suite
added without one is silently never executed. This checker closes that gap:

- tools/ci_suites.txt lists the suites the fixtures_self_test CI job runs in one loop;
- tools/ci_suite_exclusions.txt lists each other suite with a stated reason.

It fails when a tools/test_*.py file is neither listed nor excluded, when a file is both,
when a listed or excluded path does not exist, or when an exclusion has no reason.
Suites already invoked by name in a workflow or harness are excluded with that reason.

Run: python3 tools/test_suite_coverage.py   (standard library only; reads, never writes)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
LISTED = TOOLS / "ci_suites.txt"
EXCLUDED = TOOLS / "ci_suite_exclusions.txt"


def _rows(path: Path) -> list[str]:
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def load_listed() -> list[str]:
    return _rows(LISTED)


def load_excluded() -> dict[str, str]:
    excluded: dict[str, str] = {}
    for row in _rows(EXCLUDED):
        if "|" not in row:
            raise ValueError(f"exclusion has no reason: {row!r}")
        path, reason = (part.strip() for part in row.split("|", 1))
        if not reason:
            raise ValueError(f"exclusion has an empty reason: {path}")
        if path in excluded:
            raise ValueError(f"exclusion listed twice: {path}")
        excluded[path] = reason
    return excluded


def check() -> list[str]:
    problems: list[str] = []
    listed = load_listed()
    excluded = load_excluded()
    if len(set(listed)) != len(listed):
        problems.append("ci_suites.txt names a suite twice")
    for path in set(listed) & set(excluded):
        problems.append(f"{path} is both run by CI and excluded")
    for path in listed + sorted(excluded):
        if not (ROOT / path).is_file():
            problems.append(f"{path} is named but does not exist")
    on_disk = sorted(
        p.relative_to(ROOT).as_posix() for p in TOOLS.glob("test_*.py") if p.is_file()
    )
    for path in on_disk:
        if path not in listed and path not in excluded:
            problems.append(f"{path} is neither run by CI nor excluded with a reason")
    return problems


def main() -> int:
    try:
        problems = check()
    except ValueError as error:
        print(f"FAIL suite-coverage: {error}")
        return 1
    if problems:
        print("FAIL suite-coverage:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(
        f"suite-coverage: {len(load_listed())} suites run by CI, "
        f"{len(load_excluded())} excluded with reasons, none unaccounted for"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
