#!/usr/bin/env python3
"""Evaluator-originated check: rejected same-owner transfer is atomic."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sealed_transport', ROOT / 'tools/test_runtime_session.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
calls = []

class TracedSession(t.Session):
    def call(self, action, request, expected=0):
        self.serial += 1
        path = self.home / f'adversarial-{self.serial}.json'
        path.write_text(json.dumps(request))
        argv = [sys.executable, str(self.candidate / 'tools/runtime_session.py'), action,
                '--root', str(self.state), '--request', str(path)]
        p = subprocess.run(argv, cwd=self.candidate, env=self.env, capture_output=True, text=True, timeout=12)
        row = {'argv': argv, 'cwd': str(self.candidate), 'request': request, 'exit_code': p.returncode,
               'stdout': p.stdout, 'stderr': p.stderr}
        calls.append(row)
        print(json.dumps(row), flush=True)
        response = json.loads(p.stdout)
        assert p.returncode == expected and response['ok'] is (expected == 0), row
        return response

def digest(data):
    return hashlib.sha256(data).hexdigest()

def snapshot(session):
    return {str(p.relative_to(session.directory)): digest(p.read_bytes())
            for p in sorted(session.directory.rglob('*')) if p.is_file()}

def main():
    observations = {'check': 'same-owner-transfer-refusal-atomicity',
        'designer': '/root/runtime_qa126', 'role': 'Evaluator',
        'external_anchor': '.agent/contracts/126.json interface.transfer requires same-owner rejection and a single lease increment only for an actual transfer.',
        'design': 'Exercise omitted same-owner idle transfer; preserve all private state bytes/receipts and existing lease; valid human handover and mutation/read prove continued service.',
        'helper_sha256': digest(Path(__file__).read_bytes()),
        'sealed_transport_sha256': digest((ROOT / 'tools/test_runtime_session.py').read_bytes()),
        'runtime_ref': '.agent/evidence/126/final-qa/runtime.json'}
    with tempfile.TemporaryDirectory(prefix='qa126-own-') as home:
        s = TracedSession(home)
        observations['scratch_root'] = home
        try:
            s.open()
            meta = s.remember()
            observations['initial_ownership_proof'] = {'supervisor_pid': s.supervisor, 'group': s.group,
                'tokens': s.processes.copy(), 'private_flock_owned': s.owns_lock(s.supervisor),
                'actual_stub': s.runs_stub(meta['child_pid']),
                'proof': 'Sealed remember checks private lock fd/inode, live child ancestry/group, committed sibling stub path and live /proc start tokens before registration.'}
            assert s.execute('set', 'before-refusal') == 'before-refusal'
            assert s.execute('get') == 'before-refusal'
            before = snapshot(s)
            receipts = s.receipts()
            initial = dict(s.record)
            state_bytes = s.runstate.read_bytes()
            response = s.call('transfer-session', {**s.identity(t.ORCH), 'new_owner': initial['owner']}, 1)
            assert response['error'] == 'same_owner', response
            after = snapshot(s)
            assert before == after and s.receipts() == receipts
            durable = t.load(s.directory / 'runtime_session.json')
            assert durable['owner'] == initial['owner'] and durable['lease_epoch'] == initial['lease_epoch']
            observations['negative'] = {'exit': 1, 'error': response['error'], 'before': before, 'after': after,
                'receipts_unchanged': True, 'owner_lease_unchanged': True}
            s.transfer(t.HUMAN)
            assert s.record['lease_epoch'] == initial['lease_epoch'] + 1
            assert s.execute('get') == 'before-refusal'
            assert s.execute('set', 'after-valid-transfer') == 'after-valid-transfer'
            assert s.execute('get') == 'after-valid-transfer'
            assert s.runstate.read_bytes() == state_bytes
            observations['positive'] = {'transport_set_get': True, 'valid_distinct_transfer': True,
                'exactly_one_lease_increment': True, 'new_owner_read_mutate_read': True, 'attempt_state_unchanged': True}
            s.close()
            observations['owned_processes_stopped'] = all(t.process_token(pid) != token for pid, token in s.processes.items())
            assert observations['owned_processes_stopped']
            print('PASS evaluator same-owner transfer refused atomically; valid transfer and new-owner operations succeed')
            observations['passed'] = True
        finally:
            s.cleanup()
            observations['cleanup_live_registered_pids'] = [pid for pid, token in s.processes.items() if t.process_token(pid) == token]
            observations['calls'] = calls
            (OUT / 'adversarial-observations.json').write_text(json.dumps(observations, indent=2) + '\n')
            assert not observations['cleanup_live_registered_pids']

if __name__ == '__main__':
    main()
