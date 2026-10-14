#!/usr/bin/env python3
"""Independent black-box acceptance for the partial feature126 stub controller.

No source import, development record or missing-source failure establishes acceptance.
Each selection needs a real subprocess; later features own SBCL and isolation proofs.
"""
import argparse
import ast
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
ORCH = {'principal_kind': 'agent', 'role': 'Orchestrator', 'agent_id': 'root'}
OWNER = {'principal_kind': 'agent', 'role': 'Generator', 'agent_id': 'owner'}
OTHER = {**OWNER, 'agent_id': 'foreign'}
HUMAN = {'principal_kind': 'human'}
TRIAL = {'principal_kind': 'agent', 'role': 'review_trial', 'agent_id': 'trial'}
ACTIONS = ('open-session', 'submit-operation', 'poll-operation', 'transfer-session', 'close-session')
CHECKS = ('lifecycle-no-evaluation', 'record-schema', 'fixture-claim-registered')
CASES = (1, 2, 3, 8, 9, 13)


def require(ok, message):
    if not ok:
        raise AssertionError('BEHAVIOR_ASSERTION: ' + message)


def wait_for(call, message, seconds=6):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = call()
        if value:
            return value
        time.sleep(.02)
    raise AssertionError('BEHAVIOR_ASSERTION: bounded wait: ' + message)


def load(path):
    return json.loads(Path(path).read_text())


def wait_marker(path, operation_id):
    def correlated():
        value = load(path) if path.exists() else None
        return value if value and value.get('operation_id') == operation_id else None
    return wait_for(correlated, 'correlated peer marker before unlink or next request')


def process_token(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except (FileNotFoundError, ProcessLookupError):
        return None


class Session:
    def __init__(self, home, name='one', candidate=ROOT):
        self.home, self.name, self.candidate = Path(home), name, Path(candidate)
        self.state = self.home / 'state'
        self.directory = self.state / name
        self.runstate = self.home / 'run_state.json'
        if not self.runstate.exists():
            self.runstate.write_text(json.dumps({'repository': 'scratch', 'current_phase': '016',
                'current_feature': '126', 'status': 'in_progress', 'history': [],
                'updated_at': '2026-10-14T00:00:00Z',
                'scope_budget': {'original_estimate_lines': 5650, 'total_lines_changed': 0, 'per_feature': []},
                'circuit_breaker': {'126-implementation': {'attempts': 2, 'limit': 3}}}))
        self.record = None
        self.serial = 0
        self.processes = {}
        self.group = None
        self.supervisor = None
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('PYTHONPATH', 'PYTHONHOME', 'CL_SOURCE_REGISTRY', 'ASDF_OUTPUT_TRANSLATIONS')}
        self.env.update(PYTHONDONTWRITEBYTECODE='1', HOME=str(self.home),
                        XDG_CACHE_HOME=str(self.home / 'cache'), XDG_CONFIG_HOME=str(self.home / 'config'),
                        XDG_DATA_HOME=str(self.home / 'data'))

    def opening(self, owner=OWNER):
        r = {'session_id': self.name, 'requester': ORCH, 'owner': owner, 'purpose': 'develop',
             'contract_id': '126', 'step_key': '126-implementation', 'attempt': 2,
             'run_state_path': str(self.runstate)}
        if self.record:
            r.update(expected_generation=self.record['generation'],
                     expected_lease_epoch=self.record['lease_epoch'])
        return r

    def identity(self, requester=None):
        return {'session_id': self.name, 'requester': requester or self.record['owner'],
                'expected_generation': self.record['generation'],
                'expected_lease_epoch': self.record['lease_epoch']}

    def call(self, action, request, expected=0):
        self.serial += 1
        path = self.home / f'{self.name}-request-{self.serial}.json'
        path.write_text(json.dumps(request))
        p = subprocess.run([sys.executable, str(self.candidate / 'tools/runtime_session.py'),
                            action, '--root', str(self.state), '--request', str(path)],
                           cwd=self.candidate, env=self.env, text=True, capture_output=True, timeout=12)
        try:
            response = json.loads(p.stdout)
        except (ValueError, TypeError):
            raise AssertionError(f'BEHAVIOR_ASSERTION: one JSON response required: {p.returncode}: {p.stdout!r}: {p.stderr!r}')
        require(type(response) is dict and type(response.get('ok')) is bool, 'response envelope')
        allowed = expected if isinstance(expected, tuple) else (expected,)
        require(p.returncode in allowed, f'{action} exit {p.returncode}, expected {expected}: {response}')
        require(response['ok'] is (p.returncode == 0), f'{action} envelope agrees with exit')
        return response

    def owns_lock(self, pid):
        try:
            target = (self.directory / 'supervisor.lock').stat()
            private_fd = False
            for p in Path(f'/proc/{pid}/fd').iterdir():
                try:
                    st = p.stat()
                    private_fd |= (st.st_dev, st.st_ino) == (target.st_dev, target.st_ino)
                except OSError:
                    pass
            if private_fd:
                with (self.directory / 'supervisor.lock').open('a') as probe:
                    try:
                        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        return True
                    fcntl.flock(probe, fcntl.LOCK_UN)
            return False
        except (OSError, ValueError):
            return False

    def runs_stub(self, pid):
        try:
            cwd = Path(f'/proc/{pid}/cwd').resolve(strict=True)
            argv = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
            stub = (self.candidate / 'tools/fixtures/runtime_session/stub_runtime.py').resolve()
            return stub in [(cwd / os.fsdecode(arg)).resolve() for arg in argv[1:] if arg]
        except (OSError, ValueError):
            return False

    def owned_pid(self, pid):
        try:
            return (pid in self.processes and process_token(pid) == self.processes[pid] and
                    os.getpgid(pid) == self.group and
                    (self.owns_lock(pid) if pid == self.supervisor else self.runs_stub(pid)))
        except OSError:
            return False

    def remember(self):
        meta = load(self.directory / 'controller.json')
        supervisor, child, group = (meta[k] for k in ('supervisor_pid', 'child_pid', 'supervisor_pgid'))
        require(all(type(p) is int and p > 1 for p in (supervisor, child, group)) and
                child != supervisor, 'distinct private process metadata')
        try:
            parent = int(Path(f'/proc/{child}/stat').read_text().split(') ', 1)[1].split()[1])
            related = parent == supervisor and os.getpgid(supervisor) == group and os.getpgid(child) == group
        except (OSError, ValueError):
            related = False
        require(related and self.owns_lock(supervisor) and self.runs_stub(child),
                'initial process ownership: private flock, actual child ancestry/group and candidate stub')
        tokens = {pid: process_token(pid) for pid in (supervisor, child)}
        require(all(tokens.values()), 'owned processes remain live during registration')
        self.group = group
        self.supervisor = supervisor
        self.processes.update(tokens)
        return meta

    def open(self, owner=OWNER):
        self.record = self.call('open-session', self.opening(owner))['result']
        g = self.record['generation']
        require(type(g['counter']) is int and g['counter'] >= 1 and re.fullmatch('[0-9a-f]{32}', g['nonce']),
                'counter and unpredictable nonce generation shape')
        self.remember()
        return self.record

    def request(self, op, value=None, requester=None, kind='evaluate', operation_id=None):
        self.serial += 1
        expression = {'op': op, 'name': 'symbol'}
        if op == 'set':
            expression['value'] = value
        if op == 'gate':
            expression = {'op': 'gate', 'release_path': str(value)}
        return {**self.identity(requester), 'operation_id': operation_id or f'op-{self.serial}',
                'contract_id': '126', 'step_key': '126-implementation', 'attempt': 2,
                'kind': kind, 'payload': {'expression': json.dumps(expression)}, 'context': {}, 'limits': {}}

    def submit(self, request, expected=0, reason=None):
        response = self.call('submit-operation', request, expected)
        if reason:
            require(response.get('error') == reason, f'exact {reason} refusal: {response}')
            if reason != 'conflict':
                r = response['result']
                require(r['status'] == 'rejected' and r['executed'] is False and
                        r['rejection_reason'] == reason, 'correlated rejection record')
                require(r['operation_id'] == request['operation_id'], 'rejection operation identity')
        return response

    def operation(self, operation_id):
        return self.directory / 'operations' / f'{operation_id}.json'

    def result_path(self, operation_id):
        return self.directory / 'operations' / f'{operation_id}.result.json'

    def poll(self, operation_id):
        return self.call('poll-operation', {**self.identity(), 'operation_id': operation_id})['result']

    def finish(self, request):
        operation_id = request['operation_id']
        r = wait_for(lambda: (x if (x := self.poll(operation_id))['status'] == 'completed' else None),
                     'normal operation completion')
        require(r['executed'] is True and r['image_consistent'] is True, 'observed success')
        return load(self.result_path(operation_id))['result']

    def execute(self, op, value=None, **kwargs):
        request = self.request(op, value, **kwargs)
        self.submit(request)
        return self.finish(request)

    def receipts(self):
        path = self.directory / 'child.stdout.log'
        values = []
        for line in path.read_text().splitlines() if path.exists() else []:
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and 'received_operation_id' in value:
                values.append(value['received_operation_id'])
        return values

    def no_dispatch(self, operation_id):
        require(operation_id not in self.receipts(), 'refused operation never reached child')

    def transfer(self, owner):
        before = copy.deepcopy(self.record)
        self.record = self.call('transfer-session', {**self.identity(ORCH), 'new_owner': owner})['result']
        require(self.record['owner'] == owner and self.record['lease_epoch'] == before['lease_epoch'] + 1,
                'explicit transfer changes owner and increments lease once')
        require(self.record['previous_owner'] == before['owner'] and
                self.record['previous_lease_epoch'] == before['lease_epoch'], 'transfer history')

    def close(self):
        if not self.record:
            return
        response = self.call('close-session', self.identity(ORCH))['result']
        require(response['closed'] is True and response['session_id'] == self.name, 'observed close response')
        for pid, token in self.processes.items():
            wait_for(lambda: process_token(pid) != token, 'owned process stopped')

    def cleanup(self):
        try:
            if self.record:
                self.close()
        except Exception:
            pass
        # Only terminate identities observed in this private scratch session, never a reused PID.
        if not self.processes and (self.directory / 'controller.json').exists():
            try:
                self.remember()
            except Exception:
                pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            members = []
            if self.supervisor and self.owned_pid(self.supervisor):
                for path in Path('/proc').iterdir():
                    try:
                        if path.name.isdigit() and os.getpgid(int(path.name)) == self.group:
                            members.append(int(path.name))
                    except OSError:
                        pass
            if members and all(self.owned_pid(pid) for pid in members):
                try:
                    os.killpg(self.group, sig)
                except ProcessLookupError:
                    pass
            for pid, token in self.processes.items():
                if self.owned_pid(pid):
                    try:
                        os.kill(pid, sig)
                    except ProcessLookupError:
                        pass
            time.sleep(.05)


def refused(s, request, reason):
    s.submit(request, 1, reason)
    s.no_dispatch(request['operation_id'])


def lifecycle(s):
    for key, value, exit_code in [('requester', OTHER, 1), ('owner', OTHER | {'role': 'Evaluator'}, 1),
                                  ('purpose', 'accept', 1), ('runtime_command', 'forbidden', 64)]:
        s.call('open-session', {**s.opening(), key: value}, exit_code)
    s.open()
    pids = s.remember()
    require(all(process_token(pids[k]) for k in ('supervisor_pid', 'child_pid')), 'detached processes survive client exit')
    lock = s.directory / 'supervisor.lock'
    inode = lock.stat().st_ino
    with lock.open('a') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise AssertionError('BEHAVIOR_ASSERTION: supervisor does not hold exclusive lock')
    s.call('open-session', s.opening(), 1)
    require(lock.stat().st_ino == inode and s.remember()['child_pid'] == pids['child_pid'], 'duplicate open preserves locked incarnation')
    for action, request in [('transfer-session', {**s.identity(ORCH), 'new_owner': HUMAN}),
                            ('close-session', s.identity(ORCH))]:
        s.call(action, {**request, 'payload': {'expression': 'forbidden'}}, 64)
        s.call(action, {**request, 'requester': OTHER}, 1)
    s.transfer(HUMAN)
    require(s.receipts() == [], 'open and transfer never execute')
    s.transfer(OWNER)
    gate = s.state / 'release'
    r = s.request('gate', gate)
    s.submit(r)
    wait_for(lambda: r['operation_id'] in s.receipts(), 'gate reached child')
    refused(s, s.request('set', 'wrong'), 'session_busy')
    preserved = s.operation(r['operation_id']).read_bytes()
    s.call('transfer-session', {**s.identity(ORCH), 'new_owner': HUMAN}, 1)
    require(s.operation(r['operation_id']).read_bytes() == preserved, 'busy transfer preserves operation')
    s.close()
    terminal = load(s.operation(r['operation_id']))
    require(terminal['status'] == 'terminated' and terminal['executed'] is True, 'close observes outstanding termination')
    require(s.receipts() == [r['operation_id']], 'no lifecycle execute frame')
    s.record = None


def ownership(s):
    s.open()
    s.execute('set', 'owner-value')
    for kind in ('evaluate', 'observe'):
        refused(s, s.request('set', 'foreign-value', requester=OTHER, kind=kind), 'foreign_owner')
    require(s.execute('get') == 'owner-value', 'foreign operation cannot change owner memory')
    for role in ('Planner', 'Validator', 'Evaluator', 'Orchestrator'):
        s.submit(s.request('set', 'role-abuse', requester={**OWNER, 'role': role}), 1)
    require(s.execute('get') == 'owner-value', 'unsupported role cannot execute')


def isolated(s, second):
    s.open(); second.open()
    a, b = s.remember(), second.remember()
    require(a['child_pid'] != b['child_pid'] and s.record['generation'] != second.record['generation'],
            'independent live child identities and generations')
    s.execute('set', 'left'); second.execute('set', 'right')
    for _ in range(3):
        require(s.execute('get') == 'left' and second.execute('get') == 'right', 'separate image values')


def restart(s):
    before = copy.deepcopy(s.record)
    s.close(); s.open(before['owner'])
    require(s.record['generation']['counter'] > before['generation']['counter'] and
            s.record['generation']['nonce'] != before['generation']['nonce'], 'new process counter and nonce')
    require(s.record['owner'] == before['owner'] and s.record['lease_epoch'] == before['lease_epoch'],
            'restart preserves owner and lease')
    return before


def generation(s):
    s.open(); old = restart(s)
    for kind in ('evaluate', 'observe'):
        request = s.request('set', 'stale', kind=kind)
        request['expected_generation'] = old['generation']
        refused(s, request, 'stale_generation')
    s.execute('set', 'current')
    require(s.execute('get') == 'current', 'current generation positive control')
    child_probe(s.home, 'bad-ready')
    child_probe(s.home, 'wrong-generation')


def trial_policy(s):
    # A sentinel socket proves upstream denial never even contacts an existing endpoint.
    s.directory.mkdir(parents=True)
    endpoint = socket.socket(socket.AF_UNIX)
    endpoint.bind(str(s.directory / 'control.sock')); endpoint.listen(10); endpoint.settimeout(.05)
    try:
        for action in ACTIONS:
            request = s.opening() if action == 'open-session' else s.identity_for_trial()
            if action in ('submit-operation', 'poll-operation'):
                request['operation_id'] = 'trial-op'
            if action == 'submit-operation':
                request.update(contract_id='126', step_key='126-implementation', attempt=2,
                    kind='evaluate', payload={'expression': '{"op":"set","name":"symbol","value":9}'}, context={}, limits={})
            if action == 'transfer-session':
                request['new_owner'] = OWNER
            request['requester'] = TRIAL
            response = s.call(action, request, 1)
            require(response['error'] == 'review_trial', 'upstream trial error before shape/endpoint')
            try:
                connection, _ = endpoint.accept(); connection.close()
            except socket.timeout:
                pass
            else:
                raise AssertionError('BEHAVIOR_ASSERTION: trial contacted endpoint')
        response = s.call('open-session', {**s.opening(), 'owner': TRIAL}, 1)
        require(response['error'] == 'review_trial', 'trial cannot be proposed owner')
        response = s.call('transfer-session', {**s.identity_for_trial(), 'requester': ORCH, 'new_owner': TRIAL}, 1)
        require(response['error'] == 'review_trial', 'trial cannot be proposed transfer owner')
        require(not (s.directory / 'operations').exists(), 'upstream trial denial writes no operations')
    finally:
        endpoint.close(); (s.directory / 'control.sock').unlink()
    absent = Session(s.home, 'denied')
    require(absent.call('open-session', {**absent.opening(), 'requester': TRIAL}, 1)['error'] == 'review_trial' and
            not absent.directory.exists(), 'trial open creates no session endpoint or state')
    s.open()
    before = (s.directory / 'runtime_session.json').read_bytes()
    request = s.request('set', 'trial-mutated', requester=TRIAL)
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(6); client.connect(str(s.directory / 'control.sock'))
        client.sendall((json.dumps({'action': 'submit-operation', 'request': request}) + '\n').encode())
        data = b''
        while not data.endswith(b'\n') and len(data) <= 65536:
            part = client.recv(65536)
            require(part, 'socket closed before response frame')
            data += part
    response = json.loads(data)
    require(response['ok'] is False and response['error'] == 'review_trial', 'supervisor independently refuses trial')
    r = load(s.operation(request['operation_id']))
    require(r['requester'] == TRIAL and r['executed'] is False and r['status'] == 'rejected', 'supervisor rejection record')
    s.no_dispatch(request['operation_id'])
    require((s.directory / 'runtime_session.json').read_bytes() == before, 'trial preserves session')
    s.execute('set', 'legitimate'); require(s.execute('get') == 'legitimate', 'trial refusal positive control')


# Only used to construct a denied upstream request before any actual session exists.
Session.identity_for_trial = lambda self: {'session_id': self.name, 'requester': TRIAL,
    'expected_generation': {'counter': 0, 'nonce': '0' * 32}, 'expected_lease_epoch': 0}


def attempts(s):
    s.open(); initial = s.runstate.read_bytes(); old = restart(s)
    request = s.request('set', 'same-attempt'); s.submit(request); s.finish(request)
    record = load(s.operation(request['operation_id']))
    require(record['previous_generation'] == old['generation'] and record['previous_contract_id'] == '126' and
            record['previous_step_key'] == '126-implementation' and record['previous_attempt'] == 2,
            'replacement generation emits unchanged governed attempt provenance')
    require(s.runstate.read_bytes() == initial, 'controller never changes Root run_state bytes')
    current = load(s.runstate)
    for count in (0, 1, 3, None, '2', True, -1):
        altered = copy.deepcopy(current)
        if count is None:
            altered['circuit_breaker'].pop('126-implementation')
        else:
            altered['circuit_breaker']['126-implementation']['attempts'] = count
        s.runstate.write_text(json.dumps(altered))
        preserved = s.runstate.read_bytes()
        refused(s, s.request('set', 'reset-budget'), 'attempt_mismatch')
        require(s.runstate.read_bytes() == preserved, 'invalid counter preserved byte for byte')
    s.runstate.write_bytes(initial)
    for key, value in [('attempt', 1), ('contract_id', 'other'), ('step_key', 'other')]:
        request = s.request('set', 'identity-change'); request[key] = value
        refused(s, request, 'attempt_mismatch')
    require(s.execute('get') == 'same-attempt', 'attempt guard preserves image and resumes valid identity')
    require(s.runstate.read_bytes() == initial, 'initial circuit state unchanged after positives')


def handover(s):
    s.open(HUMAN); s.execute('set', 'shared')
    for new_owner in (OWNER, HUMAN):
        old = copy.deepcopy(s.record)
        receipts = s.receipts()
        s.transfer(new_owner)
        require(s.receipts() == receipts, 'handover never executes')
        request = s.request('set', 'old-holder', requester=old['owner'])
        refused(s, request, 'foreign_owner')
        request = s.request('set', 'old-lease'); request['expected_lease_epoch'] = old['lease_epoch']
        refused(s, request, 'stale_lease')
        require(s.execute('get') == 'shared', 'new holder accesses shared image')
    gate = s.state / 'handover-release'; request = s.request('gate', gate); s.submit(request)
    wait_for(lambda: request['operation_id'] in s.receipts(), 'handover gate started')
    before = (s.directory / 'runtime_session.json').read_bytes()
    s.call('transfer-session', {**s.identity(ORCH), 'new_owner': OWNER}, 1)
    require((s.directory / 'runtime_session.json').read_bytes() == before, 'busy handover preserves outstanding lane')
    gate.touch(); s.finish(request)
    require(s.execute('get') == 'shared', 'busy handover cannot corrupt image')


def validate_records(s):
    import jsonschema
    for family, paths in [('runtime_session', [s.directory / 'runtime_session.json']),
                          ('runtime_operation', list((s.directory / 'operations').glob('*.json')))]:
        schema = load(ROOT / f'schema/{family}.schema.json')
        for path in paths:
            if path.name.endswith('.result.json') or not path.exists():
                continue
            jsonschema.validate(load(path), schema)
            p = subprocess.run(['bash', '-c', 'source "$1"; vlib_runtime_record_relations "$2" "$3"',
                '_', str(ROOT / 'tools/verify_lib.sh'), family, str(path)], capture_output=True, text=True, timeout=8)
            require(p.returncode == 0, f'existing C12 relations: {p.stdout} {p.stderr}')


def child_probe(parent, mode):
    """Alter only a disposable sibling stub; public CLI has no executable selector."""
    with tempfile.TemporaryDirectory(prefix='p', dir=parent) as home:
        base = Path(home); candidate = base / 'repo'; stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
        stub.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tools/runtime_session.py', candidate / 'tools/runtime_session.py')
        marker = base / 'sent.json'
        # This independent protocol peer records the exact operation seen at dispatch.
        stub.write_text('''import json,os,sys
from pathlib import Path
MODE = ''' + repr(mode) + '\nMARKER = ' + repr(str(marker)) + '\nSTATE = ' + repr(str(base / 'state' / 'one')) + '''
def send(x): os.write(3,(json.dumps(x)+'\\n').encode())
init=json.loads(sys.stdin.readline()); g=init['generation']
send({'type':'ready','generation': {'counter':True,'nonce':g['nonce']} if MODE=='bad-ready' else g})
last=None
for line in sys.stdin:
 frame=json.loads(line); request=frame['request']; oid=request['operation_id']
 print(json.dumps({'received_operation_id':oid}),flush=True)
 observed=json.loads((Path(STATE)/'operations'/(oid+'.json')).read_text())
 answer={'type':'result','operation_id':oid,'generation':g,'status':'completed','result':'probe-positive','image_consistent':True}
 if MODE=='bad-json': os.write(3,b'not-json\\n')
 elif MODE=='oversize': os.write(3,b'x'*65537+b'\\n')
 elif MODE=='wrong-generation': send(dict(answer,generation=dict(g,nonce=('0' if g['nonce'][0]!='0' else '1')+g['nonce'][1:])))
 elif MODE=='unsolicited': send(dict(answer,operation_id='unrequested'))
 elif MODE=='late-frame' and last: send(dict(last,result='corrupted-late'))
 else: send(answer)
 temporary=Path(MARKER+'.tmp'); temporary.write_text(json.dumps(observed)); os.replace(temporary,MARKER)
 last=answer
''')
        peer = Session(base, candidate=candidate)
        try:
            if mode == 'bad-ready':
                peer.call('open-session', peer.opening(), 70)
                return
            peer.open(); request = peer.request('set', 'probe-positive'); peer.submit(request)
            if mode in ('dispatch-order', 'late-frame'):
                require(peer.finish(request) == 'probe-positive', 'private peer transport positive')
            if mode == 'late-frame':
                original_path = peer.result_path(request['operation_id']); original = original_path.read_bytes()
                wait_marker(marker, request['operation_id'])
                marker.unlink(); request = peer.request('set', 'second'); peer.submit(request)
            observed = wait_for(lambda: load(marker) if marker.exists() else None, 'private peer emitted frame')
            require(observed['operation_id'] == request['operation_id'] and observed['status'] == 'running',
                    'durable running state exists before child dispatch')
            if mode == 'dispatch-order':
                validate_records(peer)
                return
            # Fault was emitted after an observed handshake and execute receipt, not a missing setup.
            for _ in range(4):
                require(peer.poll(request['operation_id'])['status'] in ('running', 'unknown'),
                        'malformed/late/unsolicited frame cannot manufacture completion')
                time.sleep(.04)
            require(not peer.result_path(request['operation_id']).exists(), 'untrusted frame cannot publish result')
            refused(peer, peer.request('set', 'blocked'), 'session_busy')
            if mode == 'late-frame':
                require(original_path.read_bytes() == original,
                        'late frame cannot replace prior result')
            validate_records(peer)
        finally:
            peer.cleanup()


def crash_disagreement(parent):
    """Real process death after durable admission, before any execute frame."""
    with tempfile.TemporaryDirectory(prefix='crash-', dir=parent) as home:
        base = Path(home); candidate = base / 'repo'
        stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
        stub.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tools/fixtures/runtime_session/stub_runtime.py', stub)
        source = (ROOT / 'tools/runtime_session.py').read_text()
        publishers = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'atomic_json']
        require(len(publishers) == 1, 'unique durable publication site for private crash injection')
        lines = source.splitlines(keepends=True)
        # AST placement avoids dependence on neighboring function names or formatting.
        lines.insert(publishers[0].end_lineno, '''
_test_saved_publish = atomic_json
def atomic_json(path, value):
    _test_saved_publish(path, value)
    path = Path(path)
    marker = path.parent.parent / 'test-crash.once'
    if path.parent.name == 'operations' and value.get('status') == 'running' and not marker.exists():
        marker.touch()
        os._exit(86)
''')
        injected = ''.join(lines); compile(injected, '<private-crash-candidate>', 'exec')
        (candidate / 'tools/runtime_session.py').write_text(injected)
        print('CONTROL crash source=' + hashlib.sha256(source.encode()).hexdigest() +
              ' fault=' + hashlib.sha256(injected.encode()).hexdigest())
        peer = Session(base, candidate=candidate)
        try:
            peer.open(); marker = peer.directory / 'test-crash.once'; marker.touch()
            require(peer.execute('set', 'before-crash') == 'before-crash' and
                    peer.execute('get') == 'before-crash', 'crash probe working transport positive')
            restart(peer)
            require(peer.execute('set', 'clean-restart') == 'clean-restart' and
                    peer.execute('get') == 'clean-restart', 'normal clean restart remains usable')
            print('CONTROL crash: real transport and clean restart positive')
            state = peer.runstate.read_bytes(); marker.unlink()
            request = peer.request('set', 'never-dispatched')
            require(peer.call('submit-operation', request, 70)['error'] == 'infrastructure',
                    'injected process death surfaces as infrastructure failure')
            for pid, token in peer.processes.items():
                wait_for(lambda: process_token(pid) != token, 'crashed owned incarnation stopped')
            original = peer.operation(request['operation_id']).read_bytes()
            require(load(peer.operation(request['operation_id']))['status'] == 'running' and
                    not peer.result_path(request['operation_id']).exists(), 'durable nonterminal crash witness')
            peer.no_dispatch(request['operation_id'])
            response = peer.call('open-session', peer.opening(), (0, 1, 70))
            if response['ok']:
                # Track an erroneously admitted replacement before failing, so finally can reap it.
                peer.record = response['result']; peer.remember()
            require(response['ok'] is False, 'crash disagreement must refuse reopen before a new incarnation')
            require(response['error'] in ('infrastructure', 'session_busy', 'ambiguous_state'),
                    'crash refusal reports continuity uncertainty or busy, not unrelated policy/setup')
            fresh = peer.request('set', 'must-not-dispatch')
            peer.call('submit-operation', fresh, (1, 70)); peer.no_dispatch(fresh['operation_id'])
            require(not peer.operation(fresh['operation_id']).exists() and
                    peer.operation(request['operation_id']).read_bytes() == original and
                    not peer.result_path(request['operation_id']).exists() and
                    peer.runstate.read_bytes() == state, 'crash refusal preserves evidence and attempt identity')
            print('CONTROL crash: ambiguous reopen and fresh dispatch refused; evidence preserved')
        finally:
            peer.cleanup()


def records(s):
    import jsonschema
    s.open(); s.execute('set', 'baseline')
    gate = s.state / 'duplicate-release'; request = s.request('gate', gate); s.submit(request)
    wait_for(lambda: request['operation_id'] in s.receipts(), 'pending duplicate control active')
    original = s.operation(request['operation_id']).read_bytes()
    duplicate = s.request('set', 'duplicate-effect', operation_id=request['operation_id'])
    s.submit(duplicate, 1, 'conflict')
    require(s.operation(request['operation_id']).read_bytes() == original and
            not s.result_path(request['operation_id']).exists(), 'pending duplicate preserves bytes and result absence')
    require(s.receipts().count(request['operation_id']) == 1, 'pending duplicate not dispatched')
    validate_records(s)
    gate.touch(); s.finish(request)
    completed = s.operation(request['operation_id']).read_bytes()
    result = s.result_path(request['operation_id']).read_bytes()
    s.submit(duplicate, 1, 'conflict')
    require(s.operation(request['operation_id']).read_bytes() == completed and
            s.result_path(request['operation_id']).read_bytes() == result, 'completed duplicate preserves both records')
    require(s.receipts().count(request['operation_id']) == 1 and s.execute('get') == 'baseline', 'duplicate has no receipt/effect')
    s.execute('set', 'fresh'); require(s.execute('get') == 'fresh', 'fresh-ID positive excludes always-conflict')
    errors, stop = [], threading.Event()
    def reader():
        while not stop.is_set():
            try:
                load(s.directory / 'runtime_session.json')
                for p in (s.directory / 'operations').glob('op-*.json'):
                    load(p)
            except Exception as exc:
                errors.append(repr(exc))
    thread = threading.Thread(target=reader); thread.start()
    try:
        for i in range(8):
            s.execute('set', i)
    finally:
        stop.set(); thread.join(timeout=2)
    require(not thread.is_alive() and not errors, f'concurrent readers see complete JSON: {errors}')
    validate_records(s)
    schema = load(ROOT / 'schema/runtime_operation.schema.json')
    sample = load(s.operation(request['operation_id']))
    for key, value in [('executed', 'yes'), ('forbidden_field', 1), ('evidence_class', 'acceptance')]:
        bad = {**sample, key: value}
        require(list(jsonschema.Draft202012Validator(schema).iter_errors(bad)), f'schema rejects {key}')
    before = sorted(p.name for p in (s.directory / 'operations').iterdir())
    for key, value in [('operation_id', '../escape'), ('attempt', True), ('kind', 'unknown'),
                       ('context', {'extra': 'x'}), ('payload', {'expression': 7}), ('extra', 1)]:
        bad = s.request('set', 'malformed'); bad[key] = value
        s.call('submit-operation', bad, 64)
    bad = s.request('set', 'missing-identity'); del bad['requester']
    s.call('submit-operation', bad, 64)
    require(sorted(p.name for p in (s.directory / 'operations').iterdir()) == before, 'malformed requests write no operation')
    for mode in ('dispatch-order', 'bad-json', 'oversize', 'wrong-generation', 'unsolicited', 'late-frame'):
        child_probe(s.home, mode)
    crash_disagreement(s.home)


def extract_function(text, name):
    found = re.findall(r'(?m)^' + re.escape(name) + r'\(\) \{\n[\s\S]*?^\}', text)
    require(len(found) == 1, f'unique actual Bash function {name}')
    return found[0]


def claim_controls(home, text):
    actual = extract_function(text, 'claim_map_check')
    scratch = Path(home) / 'claims'; (scratch / 'fixtures/runtime_session').mkdir(parents=True)
    (scratch / 'tools').mkdir(); (scratch / 'tools/test_runtime_session.py').write_text('# scratch owner\n')
    row = 'runtime_session|tools/test_runtime_session.py'
    for variant, claims, expected, diagnostic in [('valid', [row], 0, ''), ('missing', [], 1, 'unclaimed'),
            ('duplicate', [row, row], 1, 'doubly-claimed'),
            ('missing-suite', ['runtime_session|tools/absent.py'], 1, 'does not exist')]:
        script = actual + '\nclaim_map_check "$@"\n'
        p = subprocess.run(['bash', '-c', script, '_', str(scratch / 'fixtures'), str(scratch), *claims],
                           text=True, capture_output=True, timeout=8)
        require(p.returncode == expected and (diagnostic in p.stdout if diagnostic else not p.stdout),
                f'actual claim-map {variant}: {p.returncode} {p.stdout}')
        print(f'CONTROL claim-map {variant}: actual_exit={p.returncode}; {p.stdout.strip()}')


def fixture_claim(home):
    text = (ROOT / 'tools/fixtures_self_test.sh').read_text()
    block = re.search(r'(?m)^FIXTURE_CLAIMS=\(\n([\s\S]*?)^\)', text)
    require(block is not None, 'real FIXTURE_CLAIMS array')
    rows = re.findall(r'^\s*"([^"\n]+)"', block[1], re.M)
    require(rows.count('runtime_session|tools/test_runtime_session.py') == 1 and
            rows.count('convergent_review|tools/test_convergent_review.py') == 1, 'exact new and preserved foundation claims')
    require((ROOT / 'tools/fixtures/runtime_session/stub_runtime.py').is_file(), 'real nested stub fixture')
    # External anchor: fixture tree d1348ac7 at approved base9f361154, excluding only the new owned subdirectory.
    fixtures = ROOT / 'tools/fixtures'
    foundation = {str(p.relative_to(fixtures)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in fixtures.rglob('*') if p.is_file() and p.relative_to(fixtures).parts[0] != 'runtime_session'}
    digest = hashlib.sha256(json.dumps(foundation, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(digest == '4ef85dba4c5dbd3b47a691cbea0d3de3ac99f7251544d786299230f8d0639d5b',
            'foundation fixture bytes and paths preserved')
    claim_controls(home, text)
    scheduled = extract_function(text, 'runtime_session_checks')
    require(re.search(r'(?m)^runtime_session_checks\s*\|\|\s*fail=1\s*$', text), 'real harness propagates suite failure')
    expected = [['tools/test_runtime_session.py', '--check', x] for x in CHECKS]
    expected += [['tools/test_runtime_session.py', '--case', str(x), '--runtime', 'stub'] for x in (1, 2, 3, 9, 13)]
    expected += [['tools/test_runtime_session.py', '--case', '8', '--runtime', 'stub', '--layer', 'policy']]
    for fail_at in (0, 4):
        log = Path(home) / f'schedule-{fail_at}.txt'
        script = '''set -uo pipefail
count=0
python3() {
  count=$((count+1)); printf '%s\\n' "$*" >> "$LOG"
  if [ "$count" -eq "$FAIL_AT" ]; then return 23; fi
  return 0
}
''' + scheduled + '\nruntime_session_checks\n'
        p = subprocess.run(['bash', '-c', script], env={**os.environ, 'LOG': str(log), 'FAIL_AT': str(fail_at)},
                           text=True, capture_output=True, timeout=8)
        calls = [line.split() for line in log.read_text().splitlines()]
        require(calls == expected, f'actual scheduling selects all nine commands exactly: {calls}')
        require(p.returncode == 0 if fail_at == 0 else p.returncode != 0, 'targeted suite failure propagates')
        require('23' in p.stdout if fail_at else '0' in p.stdout, 'actual per-command status reported')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--check', choices=CHECKS)
    selection.add_argument('--case', type=int, choices=CASES)
    parser.add_argument('--runtime', choices=('stub',))
    parser.add_argument('--layer', choices=('policy',))
    parser.add_argument('--require-sbcl', action='store_true')
    parser.add_argument('--require-isolation', action='store_true')
    args = parser.parse_args()
    if args.require_sbcl or args.require_isolation:
        parser.error('requested capability proof is unavailable in this partial stub suite; no skip permitted')
    if (args.case is not None) != (args.runtime == 'stub') or (args.layer == 'policy') != (args.case == 8):
        parser.error('cases require --runtime stub; case8 requires --layer policy only')
    if not (ROOT / 'tools/runtime_session.py').is_file():
        print('SETUP_FAILURE: controller source absent; this is not semantic red', file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix='n126-') as home:
        sessions = []
        try:
            if args.check == 'fixture-claim-registered':
                fixture_claim(home)
            else:
                s = Session(home); sessions.append(s)
                if args.case == 2:
                    second = Session(home, 'two'); sessions.append(second); isolated(s, second)
                else:
                    {'lifecycle-no-evaluation': lifecycle, 'record-schema': records,
                     1: ownership, 3: generation, 8: trial_policy, 9: attempts, 13: handover}[args.check or args.case](s)
                for session in sessions:
                    validate_records(session)
            print('PASS', args.check or f'case{args.case}/stub')
            return 0
        finally:
            for session in reversed(sessions):
                session.cleanup()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f'SETUP_OR_INFRASTRUCTURE_FAILURE: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(2)
