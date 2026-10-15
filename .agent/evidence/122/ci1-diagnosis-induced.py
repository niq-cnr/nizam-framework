#!/usr/bin/env python3
"""Induced, synthetic-fixture-only Git housekeeping diagnosis; assertions unchanged."""
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / '.agent/evidence/122'


def emit(kind, **values):
    print(json.dumps(dict(kind=kind, **values), sort_keys=True), flush=True)


def main():
    emit('diagnostic_identity', classification='induced diagnostic, not identical hosted reproduction',
         root=str(ROOT), python=platform.python_version(), argv=sys.argv,
         revision=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip(),
         git=subprocess.check_output(['git', '--version']).decode().strip(),
         environment={key: os.environ.get(key) for key in
                      ('PYTHONDONTWRITEBYTECODE', 'GIT_TRACE2_EVENT', 'NIZAM_WA120_FIXTURE')})
    for path in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/122.json'):
        emit('protected_pin', path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
             git_entry=subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', 'HEAD', '--', path]).decode().strip())
    spec = importlib.util.spec_from_file_location('unchanged_acceptance', ROOT / 'tools/test_workflow_assurance.py')
    acceptance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acceptance)
    original_git = acceptance.git

    def fixture_git(root, *args):
        result = original_git(root, *args)
        if args == ('init', '-q'):
            # Called only for temporary synthetic repositories created by this selector.
            original_git(root, 'config', '--local', 'gc.auto', '1')
            original_git(root, 'config', '--local', 'gc.autoDetach', 'true')
            emit('induced_fixture_configuration', root=str(root), gc_auto='1', gc_autoDetach='true')
        return result

    acceptance.git = fixture_git
    original_files = acceptance.FailureFixture.files
    prior = {}
    ordinal = 0

    def observed_files(fixture):
        nonlocal ordinal
        snapshot = original_files(fixture)
        ordinal += 1
        frame = inspect.currentframe().f_back
        caller = dict(function=frame.f_code.co_name, line=frame.f_lineno)
        inputs = repr((fixture.request, fixture.policy, fixture.state,
                       fixture.authority, fixture.capture, fixture.evidence))
        emit('snapshot', ordinal=ordinal, parent=str(fixture.parent), caller=caller,
             input_repr_sha256=hashlib.sha256(inputs.encode()).hexdigest(), count=len(snapshot))
        previous = prior.get(str(fixture.parent))
        if previous is not None:
            for path in sorted(set(previous) | set(snapshot)):
                if previous.get(path) != snapshot.get(path):
                    emit('snapshot_delta', ordinal=ordinal, caller=caller, path=path,
                         before=previous.get(path), after=snapshot.get(path))
        prior[str(fixture.parent)] = snapshot
        return snapshot

    acceptance.FailureFixture.files = observed_files
    acceptance.run_failure_case('semantic-failed', acceptance.load_api())
    print('PASS semantic-failed (induced diagnostic only)', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr, flush=True)
        raise SystemExit(1)
