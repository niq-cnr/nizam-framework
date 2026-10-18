#!/usr/bin/env python3
"""Envelope entry point for shipped, self-contained sandbox boundary tests."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("maintenance_sandbox_tests", ROOT / "tools/test_convergent_review.py")
boundaries = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = boundaries
assert SPEC.loader is not None
SPEC.loader.exec_module(boundaries)
exercise_cross_files_network = boundaries.exercise_cross_files_network
exercise_generated_execution = boundaries.exercise_generated_execution
exercise_docker_guards = boundaries.exercise_docker_guards
configure_isolation_adapter = boundaries.configure_isolation_adapter

def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument("--adapter", default=None,
                        help="force a specific sandbox adapter (tools/linux_trial_sandbox.sh or "
                             "tools/docker_trial_sandbox.sh); auto-selects native-first when absent")
    arguments = parser.parse_args()
    adapter = configure_isolation_adapter(arguments.adapter)
    if adapter is None:
        print('UNSUPPORTED: namespace capability unavailable: ' + boundaries.adapter_unavailable_detail(), file=sys.stderr)
        return 64
    digest = __import__('hashlib').sha256(adapter.wrapper.read_bytes()).hexdigest()
    print(f"SELECTED ISOLATION ADAPTER: {adapter.wrapper.relative_to(ROOT)} sha256={digest}", file=sys.stderr)
    try:
        with tempfile.TemporaryDirectory(prefix='nizam-sandbox-boundaries-') as name:
            scratch=Path(name)
            exercise_cross_files_network(scratch, adapter)
            exercise_generated_execution(scratch, adapter)
            if adapter.kind == 'docker':
                exercise_docker_guards(scratch, adapter)
        print('SANDBOX BOUNDARIES PASS: intact 0; isolated omission controls 40/41/42; unexpected execution errors rejected')
        return 0
    except (OSError,RuntimeError,subprocess.SubprocessError) as error:
        print('SANDBOX SETUP/BOUNDARY FAIL: '+str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
