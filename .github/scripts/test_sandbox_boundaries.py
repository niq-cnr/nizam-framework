#!/usr/bin/env python3
"""Envelope entry point for shipped, self-contained sandbox boundary tests."""
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
NAMESPACES = boundaries.NAMESPACES
exercise_cross_files_network = boundaries.exercise_cross_files_network
exercise_generated_execution = boundaries.exercise_generated_execution

def main():
    try:
        capability = subprocess.run(NAMESPACES+['true'],text=True,capture_output=True,timeout=20)
    except (OSError,subprocess.TimeoutExpired) as error:
        print('UNSUPPORTED: namespace capability unavailable: '+str(error),file=sys.stderr)
        return 64
    if capability.returncode:
        print('UNSUPPORTED: namespace capability unavailable: '+capability.stderr.strip(),file=sys.stderr)
        return 64
    try:
        with tempfile.TemporaryDirectory(prefix='nizam-sandbox-boundaries-') as name:
            scratch=Path(name)
            exercise_cross_files_network(scratch)
            exercise_generated_execution(scratch)
        print('SANDBOX BOUNDARIES PASS: intact 0; isolated omission controls 40/41/42; unexpected execution errors rejected')
        return 0
    except (OSError,RuntimeError,subprocess.SubprocessError) as error:
        print('SANDBOX SETUP/BOUNDARY FAIL: '+str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
