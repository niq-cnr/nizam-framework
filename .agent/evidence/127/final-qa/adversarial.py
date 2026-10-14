#!/usr/bin/env python3
"""Evaluator-originated interaction: cancellation after a checked pending handoff."""
import copy, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sealed_transport', ROOT / 'tools/test_runtime_session.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(name, value): (OUT / name).write_text(json.dumps(value, indent=2) + '\n')
calls = []
class Session(t.Session):
    def call(self, action, request, expected=0):
        self.serial += 1; prefix = f'adversarial-call-{self.serial:02d}'
        path = self.home / (prefix + '.json'); path.write_text(json.dumps(request))
        argv = [sys.executable, str(self.candidate / 'tools/runtime_session.py'), action, '--root', str(self.state), '--request', str(path)]
        p = subprocess.run(argv, cwd=self.candidate, env=self.env, capture_output=True, timeout=12)
        streams = {}
        for name, raw in [('stdout', p.stdout), ('stderr', p.stderr)]:
            dest = OUT / (prefix + '.' + name + '.txt'); dest.write_bytes(raw)
            streams[name] = str(dest.relative_to(ROOT)); streams[name + '_sha256'] = sha(raw)
        row = dict(argv=argv, cwd=str(self.candidate), request=request, exit_code=p.returncode, environment_override={k: self.env[k] for k in ('HOME', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'PYTHONDONTWRITEBYTECODE')}, **streams)
        calls.append(row); write(prefix + '.json', row); print(json.dumps(row), flush=True)
        response = json.loads(p.stdout); allowed = expected if isinstance(expected, tuple) else (expected,)
        assert p.returncode in allowed and response['ok'] is (p.returncode == 0), response
        self.last_exit = p.returncode
        return response
def main():
    obs = {'designer': '/root/runtime_qa127', 'check': 'pending handoff cancellation transition and stale-snapshot refusal',
        'anchor': '.agent/contracts/127.json interface.cancel_protocol, reattach_request, handoff_records',
        'design': 'Bind a pending gate handoff, confirm cancellation, reject its now-stale pending reference atomically, reattach the refreshed null reference, preserve the same live child and pre-gate warm value; fresh work stays usable.',
        'transport_reuse': 'Only sealed Session transport, ownership/cleanup, fixture construction and bounded wait helpers; assertions are Evaluator-originated.',
        'helper_sha256': sha(Path(__file__).read_bytes())}
    with tempfile.TemporaryDirectory(prefix='qa127-own-') as home:
        s = Session(home, 'own-interaction'); obs['scratch_root'] = home
        try:
            inputs = t.source_inputs(s.home); obs['source_inputs'] = copy.deepcopy(inputs)
            repo = Path(inputs['workspace_path'])
            obs['fixture_bytes'] = {e['path']: (repo / e['path']).read_text() for e in inputs['source_manifest']}
            s.open(); meta = s.remember(); tokens = s.processes.copy(); initial = copy.deepcopy(s.record)
            obs['ownership'] = dict(controller=meta, start_tokens=tokens, group=s.group, lock=s.owns_lock(s.supervisor), child_ancestry_verified=True)
            state = s.runstate.read_bytes()
            assert s.execute('set', 'warm-before-cancel') == 'warm-before-cancel'
            gate, release = t.gate_operation(s, 'own-cancel-gate'); op = gate['operation_id']
            stale = t.attachment(s, inputs)
            s.record = s.call('reattach-session', stale)['result']
            pending = t.load(s.directory / 'runtime_session.json'); historical = (s.directory / 'handoff.json').read_bytes()
            assert pending['outstanding_operation_ref'] == str(s.operation(op))
            assert pending['previous_outstanding_operation_ref'] == pending['outstanding_operation_ref']
            receipts = s.receipts(); assert receipts.count(op) == 1
            assert s.call('cancel-operation', t.cancel_request(s, op))['result']['status'] == 'cancel_requested'
            terminal = t.wait_for(lambda: (r if (r := s.poll(op))['status'] == 'cancelled' else None), 'own confirmed cancellation')
            result = t.load(s.result_path(op)); current = t.load(s.directory / 'runtime_session.json')
            assert terminal['cancellation_confirmed'] is True and result['cancellation_confirmed'] is True
            assert result['status'] == 'cancelled' and result['result'] is None and not release.exists()
            assert current['outstanding_operation_ref'] is None and 'transition' not in current
            assert not any(k.startswith('previous_') for k in current)
            assert (s.directory / 'handoff.json').read_bytes() == historical and s.receipts() == receipts
            durable = {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')}
            response = s.call('reattach-session', stale, 1); assert response['error'] == 'continuity_mismatch'
            assert durable == {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')}
            assert (s.directory / 'handoff.json').read_bytes() == historical and t.load(s.directory / 'runtime_session.json') == current
            s.record = s.call('reattach-session', t.attachment(s, inputs))['result']
            assert s.record['previous_outstanding_operation_ref'] is None and s.record['outstanding_operation_ref'] is None
            assert all(s.record[k] == initial[k] for k in ('owner', 'generation', 'lease_epoch'))
            assert all(t.process_token(pid) == token for pid, token in tokens.items()) and s.remember()['child_pid'] == meta['child_pid']
            assert s.receipts() == receipts and s.execute('get') == 'warm-before-cancel'
            assert s.execute('set', 'positive-after-cancel') == 'positive-after-cancel' and s.execute('get') == 'positive-after-cancel'
            assert s.runstate.read_bytes() == state
            assert all(sha((repo / e['path']).read_bytes()) == e['sha256'] for e in inputs['source_manifest'])
            for name in ('runtime_session.json', 'handoff.json', 'controller.json', 'child.stdout.log', 'child.stderr.log'):
                path = s.directory / name
                if path.exists(): (OUT / ('adversarial-' + name)).write_bytes(path.read_bytes())
            for path in (s.directory / 'operations').glob('*.json'):
                (OUT / ('adversarial-' + path.name)).write_bytes(path.read_bytes())
            obs.update(pending=pending, after_cancel=current, terminal=terminal, cancelled_result=result,
                refreshed=copy.deepcopy(s.record), stale_refusal=response, same_live_processes=True, no_duplicate_dispatch=True,
                warm_value_preserved=True, new_work_succeeded=True, attempt_unchanged=True, fixture_inputs_unchanged=True)
            s.close(); obs['owned_processes_stopped'] = all(t.process_token(pid) != token for pid, token in s.processes.items())
            assert obs['owned_processes_stopped']; obs['passed'] = True
            print('PASS own pending handoff/cancel interaction: stale snapshot refused atomically, refreshed reattach preserves live image, fresh work succeeds', flush=True)
        finally:
            s.cleanup(); obs['cleanup_live_registered_pids'] = [pid for pid, token in s.processes.items() if t.process_token(pid) == token]
            obs['calls'] = calls; write('adversarial-observations.json', obs)
            assert obs['cleanup_live_registered_pids'] == []
if __name__ == '__main__': main()
