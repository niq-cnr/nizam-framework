#!/usr/bin/env python3
"""Observe one unchanged semantic selector with pinned Git2.55; no induced config."""
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
GIT = Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
EXPECTED_BLOBS = {
    'tools/workflow_assurance.py': 'a627b97cc00be278f22203b3928246e7d37929b0',
    'tools/test_workflow_assurance.py': '80d1d95991fb0db6f5fcc54341e17f0e50b51e5a',
    '.agent/contracts/122.json': 'ed83c7704868180f523329f204440076d33d93b3',
}


def emit(kind, **values):
    print(json.dumps(dict(kind=kind, **values), sort_keys=True), flush=True)


def main():
    version = subprocess.check_output(['git', '--version']).decode().strip()
    if version != 'git version 2.55.0':
        raise RuntimeError('Selected Git version mismatch: ' + version)
    emit('diagnostic_identity', classification='unchanged selector with Git2.55 and local Python3.12; not identical hosted environment',
         root=str(ROOT), python=platform.python_version(), argv=sys.argv,
         revision=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip(),
         git=version, selected_binary=str(GIT), binary_sha256=hashlib.sha256(GIT.read_bytes()).hexdigest(),
         exec_path=subprocess.check_output(['git', '--exec-path']).decode().strip(),
         environment={key: os.environ.get(key) for key in
                      ('PATH', 'GIT_EXEC_PATH', 'PYTHONDONTWRITEBYTECODE', 'GIT_TRACE2_EVENT', 'NIZAM_WA120_FIXTURE')})
    for path, expected in EXPECTED_BLOBS.items():
        entry = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', 'HEAD', '--', path]).decode().strip()
        current = subprocess.check_output(['git', '-C', str(ROOT), 'hash-object', '--', path]).decode().strip()
        if entry.split()[:3] != ['100644', 'blob', expected] or current != expected:
            raise RuntimeError('Protected immutable/current pin mismatch: ' + path)
        emit('protected_pin', path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), git_entry=entry)
    spec = importlib.util.spec_from_file_location('unchanged_acceptance', ROOT / 'tools/test_workflow_assurance.py')
    acceptance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acceptance)
    original_files = acceptance.FailureFixture.files
    prior = {}
    ordinal = 0

    def observed_files(fixture):
        nonlocal ordinal
        snapshot = original_files(fixture)
        ordinal += 1
        frame = inspect.currentframe().f_back
        caller = dict(function=frame.f_code.co_name, line=frame.f_lineno)
        label = None
        context = frame
        while context is not None:
            if context.f_code.co_name == 'failure_semantic':
                label = context.f_locals.get('label')
                break
            context = context.f_back
        inputs = repr((fixture.request, fixture.policy, fixture.state,
                       fixture.authority, fixture.capture, fixture.evidence))
        emit('snapshot', ordinal=ordinal, parent=str(fixture.parent), caller=caller, label=label,
             input_repr_sha256=hashlib.sha256(inputs.encode()).hexdigest(), count=len(snapshot))
        previous = prior.get(str(fixture.parent))
        if previous is not None:
            for path in sorted(set(previous) | set(snapshot)):
                if previous.get(path) != snapshot.get(path):
                    emit('snapshot_delta', ordinal=ordinal, caller=caller, label=label, path=path,
                         before=previous.get(path), after=snapshot.get(path))
        prior[str(fixture.parent)] = snapshot
        return snapshot

    acceptance.FailureFixture.files = observed_files
    acceptance.run_failure_case('semantic-failed', acceptance.load_api())
    print('PASS semantic-failed (Git2.55 diagnostic only)', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc(chain=True)
        raise SystemExit(1)
