"""Independent real-Git behavioral fixtures; outputs here are parser test data.

Actual commissioning receipts are captured separately by baseline-driver.py.
No function in this file implements the product acceptance validator.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

CASES = ('reject-self-review', 'reject-seal-change', 'reject-missing-red',
         'reject-setup-as-red', 'independent-handoff')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok: raise AssertionError('POLICY_ASSERTION: ' + message)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def load(path):
    spec = importlib.util.spec_from_file_location('independent_fixture_module', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def environment():
    return {'runtime': {'implementation': platform.python_implementation(),
                        'version': platform.python_version(), 'system': platform.system(),
                        'machine': platform.machine()}, 'variables': {}}


def seal(bundle):
    bundle['seal_sha256'] = sha(canonical({k: v for k, v in bundle.items() if k != 'seal_sha256'}))


def review(bundle):
    person = bundle['roles']['acceptance_reviewer']
    return {'review': 'validator-test-bundle-review', 'feature': bundle['feature_id'],
            'actor': person['agent_id'], 'reviewer_session_id': person['session_id'],
            'seal_sha256': bundle['seal_sha256'], 'issues': [],
            'missing_acceptance_coverage': [], 'unsupported_claims': [],
            'final_verdict': {'approved': True, 'summary': 'Independent parser-fixture review.'}}


class BundleFixture:
    def __init__(self, parent):
        self.root = Path(parent) / 'repo'; self.root.mkdir()
        git(self.root, 'init', '-q'); git(self.root, 'config', 'user.name', 'Independent Bundle Fixture')
        git(self.root, 'config', 'user.email', 'bundle@example.invalid')
        self.items = [('test', 'tests.py', b'# independent test bytes\n'),
                      ('obligation', 'obligation.json', b'{"feature":"116"}\n'),
                      ('interface', 'interface.json', b'{"version":1}\n'),
                      ('baseline_control', 'control.py', b'def verify_acceptance_bundle(*args): return True\n')]
        for _, path, data in self.items: self.write(path, data)
        self.write('record.json', canonical({'status': 'in_progress', 'history': []}))
        git(self.root, 'add', '.'); git(self.root, 'commit', '-qm', 'independent immutable bundle inputs')
        commit = git(self.root, 'rev-parse', 'HEAD')
        self.bundle = {'schema_version': 1, 'feature_id': '116',
                       'baseline': {'commit': commit, 'tree': git(self.root, 'rev-parse', commit + '^{tree}')},
                       'inputs': sorted([{'kind': kind, 'path': path, 'sha256': sha(data),
                                          'executable': False} for kind, path, data in self.items], key=lambda x: x['path']),
                       'environment': environment(),
                       'roles': {kind: {'agent_id': kind + '-actor', 'session_id': kind + '-session'}
                                 for kind in ('test_author', 'developer', 'acceptance_reviewer')},
                       'required_cases': sorted(CASES), 'baseline_evidence': []}
        for name in sorted(CASES):
            positive = name + '-positive-input.json'; case = name + '-case-input.json'
            self.write(positive, canonical({'case': name, 'mutation': 'none'}))
            self.write(case, canonical({'case': name, 'mutation': 'specific-invariant'}))
            operation = {'target': 'verify_acceptance_bundle',
                         'positive_input': self.ref(positive), 'case_input': self.ref(case),
                         'mutation': name + ' independently differentiated policy operation',
                         'expected_result': 'accept' if name == 'independent-handoff' else 'reject'}
            row = {'case': name, 'operation': operation}
            for stage in ('setup', 'positive', 'red'):
                diagnostic = ('TARGET_CALLABLE: verify_acceptance_bundle PASS' if stage == 'setup' else
                              'POSITIVE_CONTROL: ' + name + ' PASS' if stage == 'positive' else
                              'POLICY_ASSERTION: ' + name + ' wrong baseline policy outcome')
                command = 'independent-fixture ' + name + ' ' + stage
                text = 'COMMAND: ' + command + '\nREVISION: ' + commit + '\nEXIT: ' + ('1' if stage == 'red' else '0') + '\nSTDOUT:\n'
                if stage != 'setup':
                    ref = operation['positive_input' if stage == 'positive' else 'case_input']
                    text += 'INPUT_SHA256: ' + ref['sha256'] + '\nOPERATION_SHA256: ' + sha(canonical(operation)) + '\n'
                if stage == 'red': text += 'OBSERVED_RESULT: ' + ('reject' if name == 'independent-handoff' else 'accept') + '\n'
                text += diagnostic + '\nSTDERR:\n'
                path = name + '-' + stage + '.txt'; self.write(path, text.encode())
                row[stage] = {**self.ref(path), 'command': command, 'revision': commit, 'diagnostic': diagnostic}
            self.bundle['baseline_evidence'].append(row)
        self.refresh()

    def write(self, path, data):
        target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)

    def ref(self, path):
        return {'path': path, 'sha256': sha((self.root / path).read_bytes())}

    def refresh(self):
        seal(self.bundle); self.review = review(self.bundle)

    def row(self, name):
        return next(x for x in self.bundle['baseline_evidence'] if x['case'] == name)

    def transition(self):
        self.write('record.json', canonical({'status': 'complete', 'history': [{'kind': 'captured'}]}))
        git(self.root, 'add', 'record.json'); git(self.root, 'commit', '-qm', 'actual record-only handoff')
        require(git(self.root, 'rev-parse', 'HEAD') != self.bundle['baseline']['commit'], 'real record-only HEAD transition')


