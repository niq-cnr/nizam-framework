#!/usr/bin/env python3
"""implement.py TREE : minimal positive-control implementation of contract 103 (scratch clone only; never run in the repo).
Follows design_notes.implementation_shape, output_contract, mode_switch and pinned_texts verbatim."""
import json, re, sys, pathlib
tree = pathlib.Path(sys.argv[1])
contract = json.load(open(tree / '.agent/contracts/103.json'))
P = contract['design_notes']['pinned_texts']
L = contract['design_notes']['output_contract']['lines']

# ---- tools/test_convergent_review.py
path = tree / 'tools/test_convergent_review.py'
src = path.read_text()
src = src.replace('import copy\nimport hashlib\n', 'import argparse\nimport copy\nimport dataclasses\nimport functools\nimport hashlib\n', 1)
src = src.replace('import subprocess\nimport tempfile\nimport unittest\n', 'import subprocess\nimport sys\nimport tempfile\nimport unittest\n', 1)
block = '''

UNSUPPORTED_REASON_PREFIX = "UNSUPPORTED: user-namespace isolation unavailable"
ISOLATION_PROBE_COMMAND = ("unshare", "--user", "--map-root-user", "true")
ISOLATION_PROBE_TIMEOUT_SECONDS = 20
ISOLATION_DEPENDENT_TESTS: list[str] = []
_PROBE_CACHE: list["IsolationProbeResult"] = []


@dataclasses.dataclass(frozen=True)
class IsolationProbeResult:
    """Outcome of the host user-namespace capability probe."""

    available: bool
    detail: str


def probe_user_namespace_isolation() -> IsolationProbeResult:
    """Ask the host whether `unshare --user --map-root-user true` works; never raises."""
    try:
        completed = subprocess.run(
            list(ISOLATION_PROBE_COMMAND), stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=ISOLATION_PROBE_TIMEOUT_SECONDS, check=False,
        )
    except FileNotFoundError:
        return IsolationProbeResult(False, "unshare executable not found on PATH")
    except subprocess.TimeoutExpired:
        return IsolationProbeResult(False, f"probe timed out after {ISOLATION_PROBE_TIMEOUT_SECONDS}s")
    except OSError as exc:
        return IsolationProbeResult(False, f"probe could not run: {exc}")
    if completed.returncode == 0:
        return IsolationProbeResult(True, "")
    lines = completed.stderr.strip().splitlines()
    return IsolationProbeResult(False, lines[0] if lines else f"probe exited {completed.returncode}")


def requires_user_namespace_isolation(test_function):
    """Report the test UNSUPPORTED (a skip) when the host cannot prove isolation."""
    ISOLATION_DEPENDENT_TESTS.append(test_function.__name__)

    @functools.wraps(test_function)
    def wrapper(self, *args, **kwargs):
        if not _PROBE_CACHE:
            _PROBE_CACHE.append(probe_user_namespace_isolation())
        if not _PROBE_CACHE[0].available:
            self.skipTest(f"{UNSUPPORTED_REASON_PREFIX} ({_PROBE_CACHE[0].detail})")
        return test_function(self, *args, **kwargs)

    return wrapper
'''
anchor = '''def run_case(case: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command_for(case, output), cwd=ROOT, text=True, capture_output=True, check=False)
'''
assert src.count(anchor) == 1
src = src.replace(anchor, anchor + block, 1)
for name in contract['design_notes']['implementation_shape']['module_level_names_in_tools/test_convergent_review.py']['requires_user_namespace_isolation(test_function)'].split('Applied to exactly the five tests: ')[1].rstrip('.').split(', '):
    needle = '    def %s(self) -> None:' % name
    assert src.count(needle) == 1, name
    src = src.replace(needle, '    @requires_user_namespace_isolation\n' + needle, 1)
main = '''def main(argv: list[str] | None = None) -> int:
    """Run the suite in required-conformance mode; --allow-unsupported-isolation is local development only."""
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__, epilog="All other arguments are passed to unittest.")
    parser.add_argument("--allow-unsupported-isolation", action="store_true",
                        help="local development only, CI never passes it: do not fail the run for UNSUPPORTED isolation-dependent tests")
    arguments, remaining = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    program = unittest.main(argv=[sys.argv[0], *remaining], verbosity=2, exit=False)
    result = program.result
    unsupported = sum(1 for _, reason in result.skipped if reason.startswith(UNSUPPORTED_REASON_PREFIX))
    successful = result.wasSuccessful()
    if successful and not unsupported:
        line = "CONFORMANCE: FULL"
    elif unsupported and successful:
        line = f"CONFORMANCE: NOT FULL (UNSUPPORTED isolation-dependent tests: {unsupported})"
    elif unsupported:
        line = f"CONFORMANCE: NOT FULL (UNSUPPORTED isolation-dependent tests: {unsupported}; run unsuccessful)"
    else:
        line = "CONFORMANCE: NOT FULL (run unsuccessful)"
    print(line, file=sys.stderr)
    if unsupported and not arguments.allow_unsupported_isolation:
        print("REQUIRED CONFORMANCE NOT MET: user-namespace isolation is unavailable on this host; exiting non-zero. Local development may pass --allow-unsupported-isolation (CI must not).", file=sys.stderr)
    elif unsupported:
        print("--allow-unsupported-isolation given: the UNSUPPORTED outcome does not fail this run (local development only; CI must not pass this flag).", file=sys.stderr)
    return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation) else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
old_tail = '\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n'
assert src.endswith(old_tail)
src = src[:-len(old_tail)] + '\n\n' + main
path.write_text(src)
# the pinned note lines must equal the contract's output_contract lines
assert L['required_note'] in src and L['allow_note'] in src and L['full'] in src

# ---- tools/README.md
path = tree / 'tools/README.md'
t = path.read_text()
t = t.replace('version: 0.11.0\n', 'version: 0.12.0\n', 1)
t = t.replace('change_log:\n', 'change_log:\n  - version: "0.12.0"\n    date: "2026-10-09"\n    summary: "%s"\n' % P['readme_change_log_summary'], 1)
anchor = 'not durable.\n\n## Compliance Coverage'
assert t.count(anchor) == 1
t = t.replace(anchor, 'not durable.\n\n' + P['readme_paragraph'] + '\n\n## Compliance Coverage', 1)
path.write_text(t)

# ---- CHANGELOG.md
path = tree / 'CHANGELOG.md'
t = path.read_text()
anchor = 'recorded for either, and GA is not declared.\n\n## [1.4.0] - 2026-10-08'
assert t.count(anchor) == 1
t = t.replace(anchor, 'recorded for either, and GA is not declared.\n' + P['changelog_bullet'] + '\n\n## [1.4.0] - 2026-10-08', 1)
path.write_text(t)

# ---- docs/planning/phase_014.yaml
path = tree / 'docs/planning/phase_014.yaml'
t = path.read_text()
anchor = '    description: Sandbox prerequisite handling — explicit, non-passing UNSUPPORTED outcome when user-namespace isolation is unavailable (NDEBT-043).\n    status: PENDING\n'
assert t.count(anchor) == 1
t = t.replace(anchor, anchor + '    docs_updated: tools/README.md\n    changelog_entry: "%s"\n    evidence: .agent/evidence/103/at1-required-mode.txt\n' % P['phase_yaml_changelog_entry'], 1)
path.write_text(t)
print('implemented in', tree)
