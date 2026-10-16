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
ACTIONS = ('open-session', 'submit-operation', 'poll-operation', 'transfer-session', 'close-session',
           'cancel-operation', 'reattach-session')
CHECKS = ('lifecycle-no-evaluation', 'record-schema', 'fixture-claim-registered',
          'cancel-confirmation-required', 'handoff-source-bound')
CASES = (1, 2, 3, 5, 6, 8, 9, 10, 13)


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
        self.last_exit = p.returncode
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
        response = self.call('poll-operation', {**self.identity(), 'operation_id': operation_id}, (0, 70))
        if not response['ok']:
            require(response['error'] == 'infrastructure' and response['result']['status'] == 'unknown',
                    'failed observation preserves explicit unknown record')
        return response['result']

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
            if action in ('cancel-operation', 'reattach-session'):
                request.update(governed(s))
            if action == 'cancel-operation':
                request['operation_id'] = 'trial-op'
            if action == 'reattach-session':
                request.update(expected_outstanding_operation_ref=None, handoff={
                    'workspace_path': str(s.home), 'source_revision': '0' * 40,
                    'source_manifest': [{'path': 'source.txt', 'sha256': '0' * 64}],
                    'command_refs': ['source.txt'], 'external_resources': []})
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
            known_busy = bool(load(peer.directory / 'runtime_session.json').get('outstanding_operation_ref'))
            response = peer.call('open-session', peer.opening(), (0, 1) if known_busy else (0, 70))
            if response['ok']:
                # Track an erroneously admitted replacement before failing, so finally can reap it.
                peer.record = response['result']; peer.remember()
            require(response['ok'] is False, 'crash disagreement must refuse reopen before a new incarnation')
            require(response['error'] in (('session_busy',) if known_busy else ('infrastructure', 'ambiguous_state')),
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
    expected = [['tools/test_runtime_session.py', '--check', x] for x in CHECKS[:3]]
    expected += [['tools/test_runtime_session.py', '--case', str(x), '--runtime', 'stub'] for x in (1, 2, 3, 9, 13)]
    expected += [['tools/test_runtime_session.py', '--case', '8', '--runtime', 'stub', '--layer', 'policy']]
    expected += [['tools/test_runtime_session.py', '--check', x] for x in CHECKS[3:]]
    expected += [['tools/test_runtime_session.py', '--case', str(x), '--runtime', 'stub'] for x in (5, 6, 10)]
    for fail_at in (0, 4, 12):
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
        require(calls == expected, f'actual scheduling selects all fourteen commands exactly: {calls}')
        require(p.returncode == 0 if fail_at == 0 else p.returncode != 0, 'targeted suite failure propagates')
        require('23' in p.stdout if fail_at else '0' in p.stdout, 'actual per-command status reported')


def governed(s):
    return {key: s.opening()[key] for key in ('contract_id', 'step_key', 'attempt')}


def gate_operation(s, name):
    release = s.state / name
    request = s.request('gate', release); s.submit(request)
    wait_for(lambda: request['operation_id'] in s.receipts(), 'real gate execute receipt')
    return request, release


def timed_snapshot(s, operation_id, seconds):
    start = time.monotonic()
    response = s.call('poll-operation', {**s.identity(), 'operation_id': operation_id,
                                      'limits': {'timeout_seconds': seconds}}, (0, 70))
    record = response['result']
    require(time.monotonic() - start <= seconds + 5.5, 'timed poll bounded by deadline and control grace')
    require(record['operation_id'] == operation_id, 'timed poll correlates operation')
    if record['status'] == 'unknown':
        require(not response['ok'] and response['error'] == 'infrastructure', 'unknown is infrastructure uncertainty')
    else:
        require(response['ok'], 'known poll snapshot successful')
    return record, time.monotonic() - start


def control_refused(s, action, request, code, reason=None):
    before = {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')}
    snapshots = {p.name: p.read_bytes() for p in (s.directory / 'runtime_session.json', s.directory / 'handoff.json') if p.exists()}
    receipts = s.receipts()
    response = s.call(action, request, code)
    if reason:
        require(response['error'] in ((reason,) if isinstance(reason, str) else reason), 'correlated control refusal')
    require(before == {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')} and
            receipts == s.receipts(), 'refused control preserves operation/result evidence and executes nothing')
    require(snapshots == {p.name: p.read_bytes() for p in (s.directory / 'runtime_session.json', s.directory / 'handoff.json') if p.exists()},
            'refused control preserves checked session and handoff snapshots')


def cancel_request(s, operation_id):
    return {**s.identity(), **governed(s), 'operation_id': operation_id}


def control_counter(s, action, request):
    raw = s.runstate.read_bytes(); altered = json.loads(raw)
    altered['circuit_breaker'][request['step_key']]['attempts'] = request['attempt'] + 1
    s.runstate.write_text(json.dumps(altered)); changed = s.runstate.read_bytes()
    try:
        control_refused(s, action, request, 1, 'attempt_mismatch')
        require(s.runstate.read_bytes() == changed, 'control never mutates Root counter input')
    finally:
        s.runstate.write_bytes(raw)


def direct_trial_control(s, action, request):
    before = {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')}
    receipts = s.receipts()
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(6); client.connect(str(s.directory / 'control.sock'))
        client.sendall((json.dumps({'action': action, 'request': {**request, 'requester': TRIAL}}) + '\n').encode())
        with client.makefile('rb') as stream:
            raw = stream.readline(65537)
    require(len(raw) <= 65536 and raw.endswith(b'\n'), 'bounded direct control response')
    response = json.loads(raw)
    require(not response['ok'] and response['error'] == 'review_trial' and receipts == s.receipts() and
            before == {p.name: p.read_bytes() for p in (s.directory / 'operations').glob('*.json')},
            'supervisor independently denies trial control without overwritten outcomes or execution')


def timed_waits(s):
    s.open(); request, release = gate_operation(s, 'wait-release')
    operation_id = request['operation_id']; state = s.runstate.read_bytes()
    meta = s.remember(); session = load(s.directory / 'runtime_session.json')
    for limits in ({}, {'timeout_seconds': -1}, {'timeout_seconds': True}, {'timeout_seconds': 31},
                   {'timeout_seconds': float('inf')}, {'timeout_seconds': '1'}, {'output_bytes': 1}):
        control_refused(s, 'poll-operation', {**s.identity(), 'operation_id': operation_id, 'limits': limits}, 64)
    for seconds in (0, .25):
        record, elapsed = timed_snapshot(s, operation_id, seconds)
        require(record['status'] == 'running' and record['wait_outcome'] == 'stopped_waiting', 'deadline stops waiting only')
        if seconds:
            require(elapsed >= seconds * .8, 'finite poll actually waited for its deadline')
        require(not s.result_path(operation_id).exists() and process_token(meta['child_pid']) and
                load(s.directory / 'runtime_session.json')['outstanding_operation_ref'] == session['outstanding_operation_ref'],
                'deadline retains live child and original busy lane')
    preserved = s.operation(operation_id).read_bytes()
    s.submit(s.request('set', 'duplicate', operation_id=operation_id), 1, 'conflict')
    require(s.operation(operation_id).read_bytes() == preserved, 'duplicate conflict precedes timed busy admission')
    for kind in ('evaluate', 'observe'):
        refused(s, s.request('set', 'conflict', kind=kind), 'session_busy')
    # Observe a connected real waiting CLI before killing our own client process.
    path = s.home / 'waiting-client.json'
    path.write_text(json.dumps({**s.identity(), 'operation_id': operation_id, 'limits': {'timeout_seconds': 3}}))
    client = subprocess.Popen([sys.executable, str(s.candidate / 'tools/runtime_session.py'), 'poll-operation',
        '--root', str(s.state), '--request', str(path)], cwd=s.candidate, env=s.env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        def connected():
            if client.poll() is not None:
                return False
            try:
                inodes = {os.readlink(p)[8:-1] for p in Path(f'/proc/{client.pid}/fd').iterdir()
                          if os.readlink(p).startswith('socket:[')}
                return any(len(row) > 6 and row[5] == '03' and row[6] in inodes
                           for row in (line.split() for line in Path('/proc/net/unix').read_text().splitlines()[1:]))
            except OSError:
                return False
        wait_for(connected, 'real timed client connected before disconnect')
        require(client.poll() is None, 'client still waiting before disconnect')
        start = time.monotonic(); refused(s, s.request('set', 'while-client-waits'), 'session_busy')
        require(time.monotonic() - start < 2.5 and client.poll() is None,
                'supervisor services other controls before the active timed wait ends')
        client.terminate(); client.communicate(timeout=2)
        require(client.returncode < 0, 'owned waiting client was terminated')
    finally:
        if client.poll() is None:
            client.kill(); client.communicate(timeout=2)
    require(s.poll(operation_id)['status'] == 'running' and s.receipts().count(operation_id) == 1,
            'client disconnect never cancels or duplicates work')
    refused(s, s.request('set', 'after-disconnect'), 'session_busy')
    release.touch(); require(s.finish(request) is None, 'normal completion after deadline/disconnect')
    require(load(s.operation(operation_id))['wait_outcome'] == 'completed_wait', 'terminal observation replaces stopped_waiting')
    terminal, elapsed = timed_snapshot(s, operation_id, 30)
    require(terminal['status'] == 'completed' and terminal['wait_outcome'] == 'completed_wait' and elapsed < 5.5,
            'maximum valid wait returns an already observed terminal result immediately')
    s.execute('set', 'fresh-after-wait'); require(s.execute('get') == 'fresh-after-wait', 'lane reopens after real completion')
    require(s.runstate.read_bytes() == state and s.remember()['child_pid'] == meta['child_pid'], 'wait preserves governed attempt and child')


def cancellation(s):
    s.open(); request, release = gate_operation(s, 'cancel-release'); operation_id = request['operation_id']
    control = cancel_request(s, operation_id)
    control_counter(s, 'cancel-operation', control)
    direct_trial_control(s, 'cancel-operation', control)
    for key, value, code, reason in [('requester', OTHER, 1, 'foreign_owner'), ('requester', ORCH, 1, 'foreign_owner'),
            ('requester', TRIAL, 1, 'review_trial'), ('requester', OWNER | {'role': 'Evaluator'}, 1, 'foreign_owner'),
            ('expected_generation', {'counter': 0, 'nonce': '0' * 32}, 1, 'stale_generation'),
            ('expected_lease_epoch', 1, 1, 'stale_lease'), ('attempt', 1, 1, 'attempt_mismatch'), ('attempt', True, 64, None),
            ('payload', {'expression': 'forbidden'}, 64, None), ('operation_id', 'unknown', 1, 'unknown_operation')]:
        control_refused(s, 'cancel-operation', {**control, key: value}, code, reason)
    response = s.call('cancel-operation', control)['result']
    require(response['status'] == 'cancel_requested' and response['cancellation_confirmed'] is False,
            'cancel request returns nonterminal unconfirmed snapshot')
    terminal = wait_for(lambda: (r if (r := s.poll(operation_id))['status'] == 'cancelled' else None), 'cooperative cancellation confirmation')
    frame = load(s.result_path(operation_id))
    require(terminal['cancellation_confirmed'] is True and frame['cancellation_confirmed'] is True and
            frame['session_id'] == s.name and frame['operation_id'] == operation_id and
            frame['generation'] == s.record['generation'] and frame['lease_epoch'] == s.record['lease_epoch'] and
            frame['status'] == 'cancelled' and frame['result'] is None, 'only correlated confirmed stop yields cancelled')
    require(not release.exists() and s.receipts().count(operation_id) == 1, 'cancelled gate never released or reexecuted')
    s.execute('set', 'after-cancel'); require(s.execute('get') == 'after-cancel', 'fresh work after observed stop')
    validate_records(s); restart(s)
    s.execute('set', 'after-reopen'); require(s.execute('get') == 'after-reopen', 'confirmed cancellation reconciles on clean reopen')
    completed, release = gate_operation(s, 'completion-wins'); release.touch(); s.finish(completed)
    before = s.operation(completed['operation_id']).read_bytes(); result = s.result_path(completed['operation_id']).read_bytes()
    observed = s.call('cancel-operation', cancel_request(s, completed['operation_id']))['result']
    require(observed == json.loads(before) and observed['status'] == 'completed' and
            s.operation(completed['operation_id']).read_bytes() == before and
            s.result_path(completed['operation_id']).read_bytes() == result, 'completion winning cancel race is immutable')
    s.transfer(HUMAN); human, _ = gate_operation(s, 'human-cancel')
    s.call('cancel-operation', cancel_request(s, human['operation_id']))
    wait_for(lambda: s.poll(human['operation_id'])['status'] == 'cancelled', 'current human owner cancellation')
    s.transfer(OWNER)
    for mode in ('withhold', 'missing-confirmation', 'false-confirmation', 'string-confirmation', 'wrong-id', 'wrong-generation',
                 'wrong-lease', 'wrong-session', 'unsolicited', 'child-death', 'completion-wins'):
        cancel_fault(s.home, mode)
    for boundary in ('result', 'terminal'):
        cancel_crash(s.home, boundary)


def diagnostic_values(s, key):
    path = s.directory / 'child.stdout.log'; values = []
    for line in path.read_text().splitlines() if path.exists() else []:
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and key in value:
            values.append(value[key])
    return values


def cancel_fault(parent, mode):
    with tempfile.TemporaryDirectory(prefix='c-', dir=parent) as home:
        base = Path(home); candidate = base / 'r'; stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
        stub.parent.mkdir(parents=True); shutil.copyfile(ROOT / 'tools/runtime_session.py', candidate / 'tools/runtime_session.py')
        stub.write_text('''import json,os,sys
from pathlib import Path
MODE = ''' + repr(mode) + '\nSTATE = ' + repr(str(base / 'state/one')) + '''
def send(value): os.write(3,(json.dumps(value)+'\\n').encode())
g=json.loads(sys.stdin.readline())['generation']; send({'type':'ready','generation':g}); pending=None
for line in sys.stdin:
 f=json.loads(line)
 if f['type']=='execute':
  pending=f['request']; print(json.dumps({'received_operation_id':pending['operation_id']}),flush=True)
  if MODE!='unsolicited': continue
 else:
  print(json.dumps({'received_cancel_operation_id':f['operation_id']}),flush=True)
  record=json.loads((Path(STATE)/'operations'/(f['operation_id']+'.json')).read_text())
  print(json.dumps({'cancel_observation':{'status':record['status'],'confirmed':record.get('cancellation_confirmed')}}),flush=True)
  if MODE=='withhold': continue
  if MODE=='child-death': os._exit(87)
  if MODE=='completion-wins':
   send({'type':'result','operation_id':pending['operation_id'],'generation':g,'status':'completed','result':None,'image_consistent':True}); continue
 ack={'type':'result','session_id':pending['session_id'],'operation_id':pending['operation_id'],'generation':g,
      'lease_epoch':pending['expected_lease_epoch'],'status':'cancelled','result':None,'image_consistent':True,'cancellation_confirmed':True}
 if MODE=='missing-confirmation': del ack['cancellation_confirmed']
 if MODE=='false-confirmation': ack['cancellation_confirmed']=False
 if MODE=='string-confirmation': ack['cancellation_confirmed']='true'
 if MODE=='wrong-id': ack['operation_id']='other'
 if MODE=='wrong-generation': ack['generation']=dict(g,counter=g['counter']+1)
 if MODE=='wrong-lease': ack['lease_epoch']+=1
 if MODE=='wrong-session': ack['session_id']='other'
 send(ack)
''')
        peer = Session(base, candidate=candidate)
        try:
            peer.open(); request, _ = gate_operation(peer, 'fault-release'); operation_id = request['operation_id']
            if mode != 'unsolicited':
                require(peer.call('cancel-operation', cancel_request(peer, operation_id))['result']['status'] == 'cancel_requested',
                        'private peer received real nonterminal cancel request')
                def cancels():
                    return diagnostic_values(peer, 'received_cancel_operation_id')
                wait_for(lambda: cancels(), 'private peer cancellation receipt')
                observations = wait_for(lambda: diagnostic_values(peer, 'cancel_observation'), 'durable cancel publication witness')
                require(observations[0] == {'status': 'cancel_requested', 'confirmed': False}, 'unconfirmed cancel is durable before control frame')
                if mode == 'completion-wins':
                    record = wait_for(lambda: (r if (r := peer.poll(operation_id))['status'] == 'completed' else None), 'normal completion wins pending cancellation')
                    require(record.get('cancellation_confirmed') is not True and
                            load(peer.result_path(operation_id))['status'] == 'completed', 'completion cannot be relabelled cancelled')
                    return
                if mode == 'withhold':
                    peer.call('cancel-operation', cancel_request(peer, operation_id))
                    record, _ = timed_snapshot(peer, operation_id, .1)
                    require(record['status'] == 'cancel_requested' and record['cancellation_confirmed'] is False and
                            record['wait_outcome'] == 'stopped_waiting' and cancels() == [operation_id],
                            'repeated cancellation is idempotent; withheld acknowledgement cannot free lane')
            for _ in range(4):
                record, _ = timed_snapshot(peer, operation_id, 0)
                require(record['status'] in ('running', 'cancel_requested', 'unknown') and
                        record.get('cancellation_confirmed') is not True and not peer.result_path(operation_id).exists(),
                        'absent/mismatched/unsolicited confirmation or death never fabricates cancellation')
                time.sleep(.03)
            refused(peer, peer.request('set', 'forbidden-after-fault'), 'session_busy')
            validate_records(peer)
        finally:
            peer.cleanup()


def cancel_crash(parent, boundary):
    with tempfile.TemporaryDirectory(prefix='cc-', dir=parent) as home:
        base = Path(home); candidate = base / 'r'; stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
        stub.parent.mkdir(parents=True); shutil.copyfile(ROOT / 'tools/fixtures/runtime_session/stub_runtime.py', stub)
        source = (ROOT / 'tools/runtime_session.py').read_text(); tree = ast.parse(source)
        publisher = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'atomic_json']
        require(len(publisher) == 1, 'unique private cancellation publication fault site')
        hook = '''
_cancel_saved_publish = atomic_json
def atomic_json(path, value):
    _cancel_saved_publish(path, value)
    path=Path(path)
    if path.parent.name=='operations' and value.get('status')=='cancelled' and ''' + repr(boundary) + ''' == ('result' if path.name.endswith('.result.json') else 'terminal'):
        os._exit(86)
'''
        lines = source.splitlines(keepends=True); lines.insert(publisher[0].end_lineno, hook)
        (candidate / 'tools/runtime_session.py').write_text(''.join(lines))
        peer = Session(base, candidate=candidate)
        try:
            peer.open(); peer.execute('set', 'transport-positive')
            request, _ = gate_operation(peer, 'cancel-crash-release')
            peer.call('cancel-operation', cancel_request(peer, request['operation_id']))
            for pid, token in peer.processes.items():
                wait_for(lambda: process_token(pid) != token, 'cancel publication crash processes stop')
            before = {p.name: p.read_bytes() for p in (peer.directory / 'operations').glob('*.json')}
            require(peer.result_path(request['operation_id']).exists(), 'cancel crash witness follows real result publication')
            response = peer.call('open-session', peer.opening(), (0, 1, 70))
            if response['ok']:
                peer.record = response['result']; peer.remember()
            require(not response['ok'] and response['error'] in ('session_busy', 'ambiguous_state', 'infrastructure'),
                    'cancel result/terminal/pointer crash disagreement refuses reopen')
            require(peer.last_exit == (1 if response['error'] == 'session_busy' else 70),
                    'cancel crash busy and infrastructure uncertainty retain distinct exit classes')
            require(before == {p.name: p.read_bytes() for p in (peer.directory / 'operations').glob('*.json')},
                    'cancel crash preserves unresolved operation/result bytes')
        finally:
            peer.cleanup()


def git_fixture(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    p = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-C', str(repo), *args],
                       env=env, text=True, capture_output=True, timeout=8)
    require(p.returncode == 0, f'private committed fixture Git command: {p.stderr}')
    return p.stdout.strip()


def source_inputs(home, malformed=False):
    repo = Path(home) / 'source'; repo.mkdir(parents=True)
    git_fixture(repo, 'init', '-q')
    files = {'source.txt': 'committed input\n', 'resource.txt': 'private fixture resource\n'}
    for name, expression in [('set.json', {'op': 'set', 'name': 'symbol', 'value': 'pinned'}),
                             ('get.json', {'op': 'get', 'name': 'symbol'})]:
        template = {'kind': 'evaluate', 'payload': {'expression': json.dumps(expression)}, 'context': {}, 'limits': {}}
        if malformed and name == 'set.json':
            template['unrecognized'] = True
        files[name] = json.dumps(template)
    for name, value in files.items():
        (repo / name).write_text(value)
    git_fixture(repo, 'add', '--', '.')
    git_fixture(repo, '-c', 'user.name=Acceptance Fixture', '-c', 'user.email=acceptance@example.invalid', 'commit', '-qm', 'pinned replay inputs')
    return {'workspace_path': str(repo), 'source_revision': git_fixture(repo, 'rev-parse', 'HEAD'),
            'source_manifest': [{'path': name, 'sha256': hashlib.sha256((repo / name).read_bytes()).hexdigest()} for name in sorted(files)],
            'command_refs': ['set.json', 'get.json'], 'external_resources': [
                {'ref': str(repo / 'resource.txt'), 'owner': OWNER, 'isolation': 'isolated'}]}


def attachment(s, inputs):
    return {**s.identity(), **governed(s), 'expected_outstanding_operation_ref':
            load(s.directory / 'runtime_session.json').get('outstanding_operation_ref'), 'handoff': copy.deepcopy(inputs)}


def check_attachment(s, inputs, before):
    import jsonschema
    current = load(s.directory / 'runtime_session.json'); handoff = load(s.directory / 'handoff.json')
    for record in (current, handoff):
        jsonschema.validate(record, load(ROOT / 'schema/runtime_session.schema.json'))
        require(record['owner'] == before['owner'] and record['generation'] == before['generation'] and
                record['lease_epoch'] == before['lease_epoch'] and
                record.get('outstanding_operation_ref') == before.get('outstanding_operation_ref'), 'checked reattach snapshot identity')
        for key in ('source_revision', 'source_manifest', 'command_refs', 'external_resources'):
            require(record[key] == inputs[key], 'actual committed source/command/resource binding')
        require(record['source_state'] == 'committed', 'source state derived committed')
    require(handoff['transition'] == 'handoff' and current['transition'] == 'reattach', 'handoff is a snapshot, not executable action')
    for key in ('owner', 'generation', 'lease_epoch', 'outstanding_operation_ref'):
        require(current['previous_' + key] == before.get(key), 'reattach previous identity remains equal to checked snapshot')
    p = subprocess.run(['bash', '-c', 'source "$1"; vlib_runtime_record_relations runtime_session "$2"',
        '_', str(ROOT / 'tools/verify_lib.sh'), str(s.directory / 'handoff.json')], capture_output=True, text=True, timeout=8)
    require(p.returncode == 0, 'handoff snapshot existing C12 relations')
    validate_records(s)


def attach_refusals(s, inputs):
    request = attachment(s, inputs)
    control_counter(s, 'reattach-session', request)
    direct_trial_control(s, 'reattach-session', request)
    for key, value, code, reason in [('requester', OTHER, 1, 'foreign_owner'), ('requester', ORCH, 1, 'foreign_owner'),
            ('requester', TRIAL, 1, 'review_trial'), ('requester', OWNER | {'role': 'Evaluator'}, 1, 'foreign_owner'),
            ('expected_generation', {'counter': 0, 'nonce': '0' * 32}, 1, 'stale_generation'),
            ('expected_lease_epoch', s.record['lease_epoch'] + 1, 1, 'stale_lease'), ('attempt', 1, 1, 'attempt_mismatch'),
            ('contract_id', 'other', 1, 'attempt_mismatch'), ('step_key', 'other', 1, 'attempt_mismatch'),
            ('expected_outstanding_operation_ref', 'wrong-operation', 1, 'continuity_mismatch'),
            ('payload', {'expression': 'must-not-evaluate'}, 64, None)]:
        control_refused(s, 'reattach-session', {**request, key: value}, code, reason)


def reattachment(s):
    inputs = source_inputs(s.home); s.open(); request, release = gate_operation(s, 'reattach-release')
    before = load(s.directory / 'runtime_session.json'); meta = s.remember(); state = s.runstate.read_bytes(); receipts = s.receipts()
    s.record = s.call('reattach-session', attachment(s, inputs))['result']
    check_attachment(s, inputs, before); attach_refusals(s, inputs)
    require(meta['child_pid'] == s.remember()['child_pid'] and process_token(meta['child_pid']) and
            s.receipts() == receipts and s.runstate.read_bytes() == state, 'fresh client reattaches live pending image without execution/budget change')
    endpoint = s.directory / 'control.sock'; saved = s.directory / 'control.saved'
    endpoint.rename(saved)
    try:
        control_refused(s, 'reattach-session', attachment(s, inputs), 70, 'infrastructure')
    finally:
        saved.rename(endpoint)
    stale_snapshot = attachment(s, inputs)
    release.touch(); s.finish(request)
    control_refused(s, 'reattach-session', stale_snapshot, 1, 'continuity_mismatch')
    s.call('reattach-session', attachment(s, inputs))
    s.execute('set', 'after-reattach'); require(s.execute('get') == 'after-reattach', 'original pending operation resolves before fresh work')
    validate_records(s)
    # Corrupt only a separate private session; an ambiguous record must not auto-restart.
    with tempfile.TemporaryDirectory(prefix='d-', dir=s.home) as home:
        peer = Session(home)
        try:
            peer.open(); pending, _ = gate_operation(peer, 'disagreement-release'); req = attachment(peer, inputs)
            path = peer.directory / 'runtime_session.json'; raw = path.read_bytes(); record = json.loads(raw)
            record['outstanding_operation_ref'] = 'unrelated-durable-operation'; path.write_text(json.dumps(record))
            try:
                control_refused(peer, 'reattach-session', req, 70, ('infrastructure', 'ambiguous_state'))
                peer.no_dispatch(pending['operation_id'] + '-new')
            finally:
                path.write_bytes(raw)
        finally:
            peer.cleanup()


def source_bound(s):
    inputs = source_inputs(s.home); repo = Path(inputs['workspace_path']); s.open(); s.execute('set', 'warm-only')
    before = load(s.directory / 'runtime_session.json'); receipts = s.receipts()
    s.record = s.call('reattach-session', attachment(s, inputs))['result']; check_attachment(s, inputs, before)
    require(s.receipts() == receipts and s.execute('get') == 'warm-only', 'reattach never executes committed replay commands')
    attach_refusals(s, inputs)
    variants = []
    for key, value, code in [('source_revision', '0' * 40, 1), ('workspace_path', 'relative', 64),
                             ('source_state', 'committed', 64), ('extra', True, 64)]:
        bad = copy.deepcopy(inputs); bad[key] = value; variants.append((bad, code))
    for entry in ({'path': '../escape', 'sha256': '0' * 64}, {'path': '/absolute', 'sha256': '0' * 64}):
        bad = copy.deepcopy(inputs); bad['source_manifest'].append(entry); variants.append((bad, 64))
    bad = copy.deepcopy(inputs); bad['source_manifest'].append(bad['source_manifest'][0]); variants.append((bad, 64))
    bad = copy.deepcopy(inputs); bad['source_manifest'][0]['sha256'] = '0' * 64; variants.append((bad, 1))
    bad = copy.deepcopy(inputs); bad['command_refs'] = ['source.txt']; variants.append((bad, 64))
    bad = copy.deepcopy(inputs); bad['external_resources'][0]['extra'] = True; variants.append((bad, 64))
    bad = copy.deepcopy(inputs); bad['external_resources'][0]['isolation'] = 'unknown'; variants.append((bad, 64))
    for bad, code in variants:
        req = attachment(s, bad); control_refused(s, 'reattach-session', req, code, 'source_mismatch' if code == 1 else None)
    source = repo / 'source.txt'; original = source.read_bytes()
    for corruption in ('dirty', 'missing', 'symlink'):
        source.unlink()
        if corruption == 'dirty': source.write_text('dirty workspace\n')
        if corruption == 'symlink':
            outside = s.home / 'outside-source'; outside.write_bytes(original); source.symlink_to(outside)
        try:
            control_refused(s, 'reattach-session', attachment(s, inputs), 1, 'source_mismatch')
        finally:
            if source.exists() or source.is_symlink(): source.unlink()
            source.write_bytes(original)
    uncommitted = repo / 'uncommitted.json'; uncommitted.write_bytes((repo / 'set.json').read_bytes())
    bad = copy.deepcopy(inputs); bad['source_manifest'].append({'path': uncommitted.name, 'sha256': hashlib.sha256(uncommitted.read_bytes()).hexdigest()}); bad['command_refs'] = [uncommitted.name]
    control_refused(s, 'reattach-session', attachment(s, bad), 1, 'source_mismatch'); uncommitted.unlink()
    template = repo / 'set.json'; raw = template.read_bytes(); template.unlink()
    try:
        control_refused(s, 'reattach-session', attachment(s, inputs), 1, 'source_mismatch')
    finally:
        template.write_bytes(raw)
    source.write_text('different committed source\n'); git_fixture(repo, 'add', '--', 'source.txt')
    git_fixture(repo, '-c', 'user.name=Acceptance Fixture', '-c', 'user.email=acceptance@example.invalid', 'commit', '-qm', 'different valid provenance')
    changed = copy.deepcopy(inputs); changed['source_revision'] = git_fixture(repo, 'rev-parse', 'HEAD')
    changed['source_manifest'] = [{**x, 'sha256': hashlib.sha256((repo / x['path']).read_bytes()).hexdigest()} for x in inputs['source_manifest']]
    try:
        control_refused(s, 'reattach-session', attachment(s, changed), 1, 'source_mismatch')
    finally:
        git_fixture(repo, 'checkout', '--quiet', '--detach', inputs['source_revision'])
    s.call('reattach-session', attachment(s, inputs)); require(s.execute('get') == 'warm-only', 'valid manifest remains accepted after negative controls')
    snapshot = s.directory / 'handoff.json'; raw = snapshot.read_bytes(); corrupted = json.loads(raw); corrupted['source_revision'] = '0' * 40
    snapshot.write_text(json.dumps(corrupted))
    try:
        control_refused(s, 'reattach-session', attachment(s, inputs), 70, ('infrastructure', 'ambiguous_state'))
    finally:
        snapshot.write_bytes(raw)
    with tempfile.TemporaryDirectory(prefix='bad-', dir=s.home) as home:
        bad_inputs = source_inputs(home, malformed=True); peer = Session(home)
        try:
            peer.open(); control_refused(peer, 'reattach-session', attachment(peer, bad_inputs), 64)
        finally:
            peer.cleanup()
    with tempfile.TemporaryDirectory(prefix='human-', dir=s.home) as home:
        peer = Session(home)
        try:
            peer.open(HUMAN); before = load(peer.directory / 'runtime_session.json')
            peer.call('reattach-session', attachment(peer, inputs)); check_attachment(peer, inputs, before)
        finally:
            peer.cleanup()
    handoff_crash(s.home, inputs)
    fixture_claim(s.home / 'fourteen-harness')


def handoff_crash(parent, inputs):
    with tempfile.TemporaryDirectory(prefix='hc-', dir=parent) as home:
        base = Path(home); candidate = base / 'r'; stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
        stub.parent.mkdir(parents=True); shutil.copyfile(ROOT / 'tools/fixtures/runtime_session/stub_runtime.py', stub)
        source = (ROOT / 'tools/runtime_session.py').read_text()
        publishers = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'atomic_json']
        require(len(publishers) == 1, 'unique private handoff publication fault site')
        hook = '''
_handoff_saved_publish = atomic_json
def atomic_json(path, value):
    path=Path(path); marker=path.parent/'handoff-crash.once'
    snapshot=path.name in ('handoff.json','runtime_session.json') and value.get('transition') in ('handoff','reattach')
    if snapshot and marker.exists(): os._exit(88)
    _handoff_saved_publish(path,value)
    if snapshot: marker.touch()
'''
        lines = source.splitlines(keepends=True); lines.insert(publishers[0].end_lineno, hook)
        (candidate / 'tools/runtime_session.py').write_text(''.join(lines))
        peer = Session(base, candidate=candidate)
        try:
            peer.open(); peer.execute('set', 'handoff-transport-positive')
            peer.call('reattach-session', attachment(peer, inputs), 70)
            for pid, token in peer.processes.items():
                wait_for(lambda: process_token(pid) != token, 'handoff publication crash processes stop')
            published = {p.name: p.read_bytes() for p in (peer.directory / 'handoff.json', peer.directory / 'runtime_session.json') if p.exists()}
            require((peer.directory / 'handoff-crash.once').exists(), 'crash follows first real snapshot publication')
            response = peer.call('open-session', peer.opening(), (0, 70))
            if response['ok']:
                peer.record = response['result']; peer.remember()
            require(not response['ok'] and response['error'] in ('infrastructure', 'ambiguous_state'),
                    'partial handoff/session publication fails closed without replacement')
            require(published == {p.name: p.read_bytes() for p in (peer.directory / 'handoff.json', peer.directory / 'runtime_session.json') if p.exists()},
                    'partial snapshot evidence is not silently repaired or overwritten')
        finally:
            peer.cleanup()


def replay(s):
    inputs = source_inputs(s.home); s.open(); s.execute('set', 'warm-only')
    s.call('reattach-session', attachment(s, inputs)); meta = s.remember(); state = s.runstate.read_bytes()
    snapshot = load(s.directory / 'handoff.json')
    relocated = s.home / 'fresh-source'
    git_fixture(Path(inputs['workspace_path']), 'worktree', 'add', '--quiet', '--detach', str(relocated), inputs['source_revision'])
    replay_inputs = copy.deepcopy(inputs); replay_inputs['workspace_path'] = str(relocated)
    s.call('reattach-session', attachment(s, replay_inputs))  # Same committed content may relocate.
    replay_inputs['external_resources'][0]['ref'] = str(relocated / 'resource.txt')
    second = Session(s.home, 'replay')
    try:
        second.open(); other = second.remember()
        require(other['child_pid'] != meta['child_pid'] and second.record['generation'] != s.record['generation'], 'fresh replay process and generation')
        before = load(second.directory / 'runtime_session.json')
        second.call('reattach-session', attachment(second, replay_inputs)); check_attachment(second, replay_inputs, before)
        values = []
        for name in snapshot['command_refs']:
            template = load(relocated / name); request = second.request('get'); request.update(template)
            second.submit(request); values.append(second.finish(request))
        require(values == ['pinned', 'pinned'] and s.execute('get') == 'warm-only', 'only committed ordered templates reproduce result; warm memory remains separate')
        require(second.runstate.read_bytes() == state and governed(second) == governed(s), 'replay never creates governed attempt budget')
        changed = relocated / 'get.json'; raw = changed.read_bytes(); changed.write_text('{}')
        try:
            control_refused(second, 'reattach-session', attachment(second, replay_inputs), 1, 'source_mismatch')
        finally:
            changed.write_bytes(raw)
        second.call('reattach-session', attachment(second, replay_inputs)); second.execute('set', 'positive-after-replay')
        require(second.execute('get') == 'positive-after-replay', 'replay positive after missing/changed command control')
        validate_records(second)
    finally:
        second.cleanup()



# Independent explicit inventory: CHECKS remains the inherited fourteen-leaf harness API.
CORE_LEAVES = (
    ('--check', 'lifecycle-no-evaluation'), ('--check', 'record-schema'),
    ('--check', 'fixture-claim-registered'), ('--case', '1', '--runtime', 'stub'),
    ('--case', '2', '--runtime', 'stub'), ('--case', '3', '--runtime', 'stub'),
    ('--case', '9', '--runtime', 'stub'), ('--case', '13', '--runtime', 'stub'),
    ('--case', '8', '--runtime', 'stub', '--layer', 'policy'),
    ('--check', 'cancel-confirmation-required'), ('--check', 'handoff-source-bound'),
    ('--case', '5', '--runtime', 'stub'), ('--case', '6', '--runtime', 'stub'),
    ('--case', '10', '--runtime', 'stub'))


def core_owned(marker):
    owned = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            pid = int(path.name); token = process_token(pid)
            if (token and path.stat().st_uid == os.getuid() and
                    ('NIZAM_CORE_OWNER=' + marker).encode() in (path / 'environ').read_bytes().split(b'\0') and
                    process_token(pid) == token):
                owned[pid] = token
        except (OSError, ValueError):
            pass
    return owned


def core_cleanup(marker):
    observed = {}; end = time.monotonic() + 3
    while time.monotonic() < end:
        owned = core_owned(marker); observed.update(owned)
        if not owned:
            break
        for pid, token in owned.items():
            if core_owned(marker).get(pid) == token:
                try:
                    os.kill(pid, signal.SIGTERM if time.monotonic() < end - 2.5 else signal.SIGKILL)
                except ProcessLookupError:
                    pass
        time.sleep(.05)
    remaining = core_owned(marker)
    print('CORE_CLEANUP', json.dumps({'owned_tokens': observed, 'remaining': remaining}), flush=True)
    return not remaining


def core_ready(seconds=90):
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    failed = False
    try:
        for leaf in CORE_LEAVES:
            argv = [sys.executable, str(ROOT / 'tools/test_runtime_session.py'), *leaf]
            marker = os.urandom(24).hex(); process = None; event = None; out = err = ''; rc = None
            with tempfile.TemporaryDirectory(prefix='n128-') as home:
                try:
                    process = subprocess.Popen(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, start_new_session=True,
                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': home,
                             'NIZAM_CORE_OWNER': marker})
                    out, err = process.communicate(timeout=seconds)
                except subprocess.TimeoutExpired:
                    event = 'timeout'
                except KeyboardInterrupt:
                    event = 'interrupted'
                except OSError as exc:
                    event = 'setup'; err = str(exc)
                finally:
                    # Repeated interrupts cannot bypass ownership-scoped bounded cleanup.
                    for sig in previous:
                        signal.signal(sig, signal.SIG_IGN)
                    clean = core_cleanup(marker)
                    if process is not None:
                        if process.poll() is None:
                            process.kill()  # The directly spawned, unreaped Popen identity is ours.
                        out, err = process.communicate(timeout=3); rc = process.returncode
                    for sig in previous:
                        signal.signal(sig, interrupted)
                expected = 'PASS ' + (leaf[1] if leaf[0] == '--check' else f'case{leaf[1]}/stub')
                proof = bool(out.splitlines()) and out.splitlines()[-1] == expected
                ok = rc == 0 and proof and clean and event is None
                print('CORE_LEAF', json.dumps({'argv': argv, 'stdout': out, 'stderr': err, 'exit': rc,
                    'expected_final_marker': expected, 'proof': proof, 'event': event, 'cleanup': clean}), flush=True)
                failed |= not ok
                if event == 'interrupted':
                    return 130
        if not failed:
            print('PASS core-ready')
        return int(failed)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--check', choices=(*CHECKS, 'core-ready'))
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
    if args.check == 'core-ready':
        return core_ready()
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
                     'cancel-confirmation-required': cancellation, 'handoff-source-bound': source_bound,
                     1: ownership, 3: generation, 5: timed_waits, 6: reattachment, 8: trial_policy,
                     9: attempts, 10: replay, 13: handover}[args.check or args.case](s)
                for session in sessions:
                    validate_records(session)
            print('PASS', args.check or f'case{args.case}/stub')
            return 0
        finally:
            for session in reversed(sessions):
                session.cleanup()


# Feature129 additions: separate public-CLI driver; inherited leaves above are frozen.
LIVE_CHECKS = ('sbcl-admission', 'capture-before-unwind', 'bounded-printing',
               'cancel-confirmed', 'termination-ends-generation')
LIVE_TERMINAL = {'completed', 'condition_signalled', 'cancelled', 'terminated', 'rejected'}
HERMETIC_CHECKS = ('committed-source-archive', 'no-init-process', 'private-home-xdg',
                   'empty-output-cache', 'ignore-inherited-resolution', 'toolchain-lock-core-bound',
                   'asdf-noop-control', 'asdf-failure-control')
HERMETIC_CASES = (7, 10, 11, 12)
HERMETIC_PASS = '''(unless (equal (n130:token) "COMMITTED") (error "unsaved-or-stale-token"))
(unless (equal (n130:n130-use) "COMMITTED-MACRO") (error "unsaved-macro-fasl"))
(when (fboundp 'n130-deleted) (error "development-image-definition"))
"pass"
'''
HERMETIC_MUST_FAIL = (
    '(unless (equal (n130:token) "UNSAVED") (error "unsaved-definition"))\n"pass"\n',
    '(unless (equal (n130:n130-use) "UNSAVED-MACRO") (error "unsaved-macro-fasl"))\n"pass"\n',
    '(unless (fboundp \'n130-deleted) (error "development-image-definition"))\n"pass"\n',
)


def live_selection(argv):
    names = (*LIVE_CHECKS, *HERMETIC_CHECKS)
    return ('--runtime' in argv and argv[argv.index('--runtime') + 1:][:1] == ['sbcl'] or
            '--check' in argv and argv[argv.index('--check') + 1:][:1] in [[x] for x in names])


def live_process(argv, cwd, env, timeout=12):
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill(); out, err = p.communicate(timeout=3)
        print('LIVE_COMMAND', json.dumps({'argv': argv, 'pid': p.pid, 'exit': p.returncode,
              'stdout': out, 'stderr': err, 'timeout': True}), flush=True)
        raise RuntimeError('bounded subprocess timeout; never intended admission red')
    print('LIVE_COMMAND', json.dumps({'argv': argv, 'pid': p.pid, 'exit': p.returncode,
          'stdout': out, 'stderr': err, 'timeout': False}), flush=True)
    return p.returncode, out, err


def sbcl_preflight(home):
    executable = shutil.which('sbcl')
    if not executable:
        raise RuntimeError('actual SBCL executable absent')
    nonce = os.urandom(16).hex(); executable = str(Path(executable).resolve())
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
               XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'))
    for key in ('CL_SOURCE_REGISTRY', 'ASDF_OUTPUT_TRANSLATIONS', 'SBCL_HOME'):
        env.pop(key, None)
    version, out, _ = live_process([executable, '--version'], home, env)
    if version or not out.strip().startswith('SBCL '):
        raise RuntimeError('SBCL executable/version preflight unsuccessful')
    form = '(format t "~&' + nonce + ':~D~%" (+ 19 23))'
    code, out, _ = live_process([executable, '--no-sysinit', '--no-userinit', '--non-interactive', '--eval', form], home, env)
    if code or out.splitlines().count(nonce + ':42') != 1:
        raise RuntimeError('SBCL arithmetic/nonce preflight unsuccessful')
    print('SBCL_PREFLIGHT', json.dumps({'executable': executable, 'sha256': hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
          'nonce': nonce, 'arithmetic': 42}), flush=True)
    return executable


def live_owned(marker):
    owned = {}
    for path in Path('/proc').iterdir():
        try:
            pid = int(path.name); token = process_token(pid)
            if (token and path.stat().st_uid == os.getuid() and
                    ('NIZAM_LIVE_OWNER=' + marker).encode() in (path / 'environ').read_bytes().split(b'\0') and
                    process_token(pid) == token):
                owned[pid] = token
        except (OSError, ValueError):
            pass
    return owned


class LiveSession(Session):
    def __init__(self, home, name='live', candidate=ROOT):
        super().__init__(home, name, candidate)
        self.marker = os.urandom(24).hex(); self.env['NIZAM_LIVE_OWNER'] = self.marker
        self.runstate.write_text(json.dumps({'repository': 'scratch', 'current_phase': '020',
            'current_feature': '129', 'status': 'in_progress', 'history': [], 'updated_at': '2026-10-16T00:00:00Z',
            'scope_budget': {'original_estimate_lines': 7350, 'total_lines_changed': 0, 'per_feature': []},
            'circuit_breaker': {'129-implementation': {'attempts': 1, 'limit': 3}}}))
        self.saved_state = self.runstate.read_bytes(); self.live_tokens = {}

    def opening(self, owner=OWNER):
        return {**super().opening(owner), 'runtime': 'sbcl',
                'contract_id': '129', 'step_key': '129-implementation', 'attempt': 1}

    def call(self, action, request, expected=0):
        self.serial += 1; path = self.home / f'live-request-{self.serial}.json'
        path.write_text(json.dumps(request))
        argv = [sys.executable, str(self.candidate / 'tools/runtime_session.py'), action,
                '--root', str(self.state), '--request', str(path)]
        print('LIVE_REQUEST', json.dumps({'action': action, 'request': request}), flush=True)
        code, out, _ = live_process(argv, self.candidate, self.env)
        self.last_exit = code
        try:
            response = json.loads(out)
        except ValueError as exc:
            raise RuntimeError('controller response is not JSON') from exc
        if code not in (expected if isinstance(expected, tuple) else (expected,)):
            raise RuntimeError(f'unexpected controller exit {code}: {response}')
        require(type(response.get('ok')) is bool and response['ok'] is (code == 0), 'CLI envelope and actual exit agree')
        return response

    def observe_runtime(self, executable):
        observed = {}
        for pid, token in live_owned(self.marker).items():
            try:
                if Path(f'/proc/{pid}/exe').resolve() == Path(executable):
                    observed[pid] = {'token': token, 'pgid': os.getpgid(pid),
                                     'argv': Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')}
            except OSError:
                pass
        require(len(observed) == 1, 'exactly one actual owned SBCL runtime, no stub fallback')
        require(any(os.getpgid(pid) != next(iter(observed.values()))['pgid'] for pid in live_owned(self.marker)
                    if pid not in observed), 'supervisor/control lifetime has a distinct process group')
        self.live_tokens = {pid: row['token'] for pid, row in observed.items()}
        print('LIVE_RUNTIME', repr(observed), flush=True)
        return observed

    def start(self, executable):
        self.record = self.call('open-session', self.opening())['result']
        self.observe_runtime(executable)
        require(self.runstate.read_bytes() == self.saved_state, 'actual Root counters untouched in private fixture')

    def lisp(self, expression, kind='evaluate', limits=None):
        self.serial += 1
        return {**self.identity(), 'operation_id': f'live-{self.serial}', 'contract_id': '129',
                'step_key': '129-implementation', 'attempt': 1, 'kind': kind,
                'payload': {'expression': expression}, 'context': {}, 'limits': limits or {}}

    def terminal(self, request, statuses=('completed',), seconds=12):
        def observed():
            record = self.poll(request['operation_id'])
            return record if record['status'] in LIVE_TERMINAL else None
        record = wait_for(observed, 'actual correlated terminal observation', seconds)
        require(record['status'] in statuses and record['operation_id'] == request['operation_id'] and
                record['session_id'] == self.name and record['generation'] == self.record['generation'] and
                record['lease_epoch'] == self.record['lease_epoch'] and record['contract_id'] == '129' and
                record['step_key'] == '129-implementation' and record['attempt'] == 1,
                'TERMINAL_CORRELATION')
        return record

    def eval(self, expression):
        request = self.lisp(expression); self.submit(request); self.terminal(request)
        return request

    def cancellation(self, request):
        return {**self.identity(), 'operation_id': request['operation_id'],
                'contract_id': '129', 'step_key': '129-implementation', 'attempt': 1}

    def cleanup(self):
        if self.record:
            try:
                self.call('close-session', self.identity(ORCH), (0, 1, 70))
            except Exception:
                pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for pid, token in live_owned(self.marker).items():
                if live_owned(self.marker).get(pid) == token:
                    try:
                        os.kill(pid, sig)
                    except ProcessLookupError:
                        pass
            time.sleep(.1)
        require(not live_owned(self.marker), 'owned scratch processes all stopped')


def lisp_write(path, value):
    return '(with-open-file (s ' + json.dumps(str(path)) + ' :direction :output :if-exists :supersede) (write-line ' + json.dumps(value) + ' s))'


def live_nonce(s, nonce):
    path = s.home / ('positive-' + nonce)
    request = s.eval('(progn ' + lisp_write(path, nonce) + ' (+ 19 23))')
    require(path.read_text().splitlines() == [nonce], 'real SBCL exact nonce side effect')
    result = load(s.result_path(request['operation_id']))
    require(type(result['result']) is int and result['result'] == 42 and result['operation_id'] == request['operation_id'] and
            result['generation'] == s.record['generation'] and result['status'] == 'completed', 'real correlated SBCL arithmetic result42')
    request = s.eval(json.dumps(nonce)); result = load(s.result_path(request['operation_id']))
    require(type(result['result']) is str and result['result'] == nonce and result['operation_id'] == request['operation_id'] and
            result['generation'] == s.record['generation'] and result['status'] == 'completed', 'real correlated exact JSON string nonce result')


def admission(home, executable):
    nonce = os.urandom(16).hex(); stubhome = home / 'stub'; stubhome.mkdir(); stub = LiveSession(stubhome)
    try:
        opening = stub.opening(); opening.pop('runtime')
        stub.record = stub.call('open-session', opening)['result']
        stub.remember(); ids = []
        for op in ('set', 'get'):
            request = {**stub.request(op, nonce), **governed(stub)}
            ids.append(request['operation_id'])
            stub.submit(request); result = stub.finish(request)
            require(result == nonce, 'paired omitted-runtime request and actual exact stub nonce control')
        require(stub.receipts() == ids, 'paired stub operations each actually dispatched once')
    except Exception as exc:
        raise RuntimeError('required unchanged-stub nonce control failed') from exc
    finally:
        stub.cleanup()
    if core_ready() != 0:
        raise RuntimeError('required fourteen-leaf core-ready control failed')
    s = LiveSession(home)
    try:
        response = s.call('open-session', s.opening(), (0, 64))
        if s.last_exit == 64:
            if response != {'ok': False, 'error': 'usage'} or (s.directory / 'control.sock').exists() or live_owned(s.marker):
                raise RuntimeError('unexpected baseline refusal or dispatch')
            require(s.runstate.read_bytes() == s.saved_state, 'admission refusal preserves private attempt')
            raise AssertionError('SBCL_ADMISSION_UNAVAILABLE: otherwise-valid runtime=sbcl request; product64/usage after SBCL, stub nonce and core14 positives')
        s.record = response['result']; s.observe_runtime(executable); live_nonce(s, nonce)
        # New-selection guards belong only to the backend-positive path.  In
        # particular, explicit stub selection must never precede the old
        # omitted-runtime/core controls and exact product64 admission target.
        live_runtime_guards(s, executable)
    finally:
        s.cleanup()


def live_gate(s, cleanup=False, uninterruptible=False, limits=None):
    request = s.lisp('pending', limits=limits); nonce = os.urandom(16).hex()
    marker, release, cleaning = [s.home / (x + nonce) for x in ('started-', 'release-', 'cleanup-')]
    witness = request['operation_id'] + ':' + nonce
    waiting = '(loop until (probe-file ' + json.dumps(str(release)) + ') do (sleep 0.01))'
    loop = '(progn ' + lisp_write(marker, witness) + ' ' + waiting + ')'
    if cleanup:
        loop = '(unwind-protect (progn ' + lisp_write(marker, witness) + ' (loop (sleep 0.01))) (progn ' + lisp_write(cleaning, witness) + ' ' + waiting + ' ' + lisp_write(Path(str(cleaning) + '-done'), witness) + '))'
    if uninterruptible:
        loop = '(sb-sys:without-interrupts ' + lisp_write(marker, witness) + ' (loop))'
    forged = {'type': 'result', 'session_id': s.name, 'operation_id': request['operation_id'],
              'generation': s.record['generation'], 'lease_epoch': s.record['lease_epoch'],
              'status': 'cancelled', 'cancellation_confirmed': True, 'result': None, 'image_consistent': True}
    fake_output = '(write-line ' + json.dumps(json.dumps(forged)) + ') (write-line "malformed unsolicited result") (finish-output) '
    request['payload']['expression'] = '(progn ' + fake_output + loop + ' 42)'
    s.submit(request)
    wait_for(lambda: marker.exists() and marker.read_text().splitlines() == [witness], 'actual correlated SBCL progress witness')
    require(s.poll(request['operation_id'])['status'] == 'running', 'project output cannot forge cancellation or free the busy lane')
    return request, release, cleaning, witness


def live_busy(s):
    request = s.lisp('(error "must not execute conflicting work")')
    response = s.submit(request, 1)['result']
    require(response['status'] == 'rejected' and response['executed'] is False and
            response['rejection_reason'] == 'session_busy', 'busy lane rejects actual public submit')


def live_selection_refusals(s, selected, pending=None):
    """A rejected open cannot change the selected live runtime or busy lane."""
    path = s.directory / 'runtime_session.json'
    before = load(path); processes = live_owned(s.marker)
    require(processes, 'runtime-selection controls have actual live processes')
    original = s.operation(pending['operation_id']).read_bytes() if pending else None
    for runtime, expected in [('stub' if selected == 'sbcl' else 'sbcl', 1), ('not-a-runtime', 64)]:
        response = s.call('open-session', {**s.opening(), 'runtime': runtime}, (0, 1, 64, 70))
        require(s.last_exit == expected and response['ok'] is False and
                (expected != 64 or response == {'ok': False, 'error': 'usage'}), 'RUNTIME_SELECTION_GUARD')
        after = load(path)
        require(all(after.get(k) == before.get(k) for k in
                    ('owner', 'generation', 'lease_epoch', 'outstanding_operation_ref')) and
                live_owned(s.marker) == processes and s.runstate.read_bytes() == s.saved_state and
                (pending is None or s.operation(pending['operation_id']).read_bytes() == original),
                'RUNTIME_SELECTION_PRESERVES_IDENTITY')
    if pending:
        require(s.poll(pending['operation_id'])['status'] == 'running', 'runtime refusal preserves actual busy work')


def live_runtime_guards(s, executable):
    # Check idle as well as busy: session_busy must not mask a missing selector
    # check.  Every CLI below is a fresh client of the same session.
    live_selection_refusals(s, 'sbcl')
    request, release, _, _ = live_gate(s)
    live_selection_refusals(s, 'sbcl', request); live_busy(s)
    release.touch(); s.terminal(request); s.observe_runtime(executable)
    live_nonce(s, os.urandom(16).hex())
    with tempfile.TemporaryDirectory(prefix='explicit-stub-', dir=s.home) as temp:
        stub = LiveSession(Path(temp))
        try:
            stub.record = stub.call('open-session', {**stub.opening(), 'runtime': 'stub'})['result']
            stub.remember()  # /proc ancestry, private flock and actual stub argv.
            nonce = os.urandom(16).hex()
            for op in ('set', 'get'):
                control = {**stub.request(op, nonce), **governed(stub)}
                stub.submit(control); require(stub.finish(control) == nonce, 'explicit stub exact nonce positive')
            live_selection_refusals(stub, 'stub')
            release = stub.state / 'release-stub'
            request = {**stub.request('gate', release), **governed(stub)}
            stub.submit(request)
            wait_for(lambda: request['operation_id'] in stub.receipts(), 'explicit stub actual gate dispatch')
            live_selection_refusals(stub, 'stub', request)
            conflict = {**stub.request('get'), **governed(stub)}
            require(stub.submit(conflict, 1)['result']['rejection_reason'] == 'session_busy',
                    'explicit stub runtime refusal retains busy lane')
            release.touch(); stub.finish(request)
            control = {**stub.request('get'), **governed(stub)}
            stub.submit(control); require(stub.finish(control) == nonce, 'explicit stub state survives guarded reopening')
        finally:
            stub.cleanup()


def live_wait(s):
    request, release, _, _ = live_gate(s); before = load(s.directory / 'runtime_session.json')
    tokens = dict(s.live_tokens)
    original = s.operation(request['operation_id']).read_bytes()
    duplicate = {**request, 'payload': {'expression': '(error "duplicate must not execute")'}}
    require(s.submit(duplicate, 1)['error'] == 'conflict' and s.operation(request['operation_id']).read_bytes() == original,
            'duplicate-ID conflict precedes busy admission and preserves original operation')
    for seconds in (0, .15):
        started = time.monotonic()
        record = s.call('poll-operation', {**s.identity(), 'operation_id': request['operation_id'],
                        'limits': {'timeout_seconds': seconds}})['result']
        require(record['status'] == 'running' and record['wait_outcome'] == 'stopped_waiting' and
                time.monotonic() - started < 3 and (not seconds or time.monotonic() - started >= seconds * .8),
                'bounded wait stops waiting only, while real Lisp continues')
        live_busy(s)
    path = s.home / 'disconnect-request.json'
    path.write_text(json.dumps({**s.identity(), 'operation_id': request['operation_id'], 'limits': {'timeout_seconds': 3}}))
    argv = [sys.executable, str(s.candidate / 'tools/runtime_session.py'), 'poll-operation', '--root', str(s.state), '--request', str(path)]
    child = subprocess.Popen(argv, cwd=s.candidate, env=s.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        def connected():
            try:
                sockets = {os.readlink(p)[8:-1] for p in Path(f'/proc/{child.pid}/fd').iterdir()
                           if os.readlink(p).startswith('socket:[')}
                return any(len(row) > 6 and row[5] == '03' and row[6] in sockets
                           for row in (line.split() for line in Path('/proc/net/unix').read_text().splitlines()[1:]))
            except OSError:
                return False
        wait_for(connected, 'fresh waiting client connected before disconnect')
        live_busy(s); require(child.poll() is None, 'waiting client has not completed')
        child.terminate(); out, err = child.communicate(timeout=3)
        print('LIVE_DISCONNECT', repr({'argv': argv, 'pid': child.pid, 'exit': child.returncode, 'stdout': out, 'stderr': err}), flush=True)
        require(child.returncode < 0, 'owned client actually disconnected')
    finally:
        if child.poll() is None:
            child.kill(); child.communicate(timeout=3)
    record = s.poll(request['operation_id'])
    require(record['status'] == 'running' and all(process_token(p) == t for p, t in tokens.items()) and
            load(s.directory / 'runtime_session.json')['outstanding_operation_ref'] == before['outstanding_operation_ref'],
            'disconnection preserves actual runtime identity and pending work')
    live_busy(s); release.touch(); s.terminal(request); live_nonce(s, os.urandom(16).hex())
    require(s.runstate.read_bytes() == s.saved_state, 'wait/disconnect never resets attempt')


def live_reattach(s):
    inputs = source_inputs(s.home); repo = Path(inputs['workspace_path'])
    for name, expression in [('set.json', '(defparameter *n129-replay* 42)'), ('get.json', '*n129-replay*')]:
        template = {'kind': 'evaluate', 'payload': {'expression': expression}, 'context': {}, 'limits': {}}
        (repo / name).write_text(json.dumps(template))
    git_fixture(repo, 'add', '--', '.'); git_fixture(repo, '-c', 'user.name=Acceptance Fixture',
                '-c', 'user.email=acceptance@example.invalid', 'commit', '-qm', 'committed SBCL handoff templates')
    inputs['source_revision'] = git_fixture(repo, 'rev-parse', 'HEAD')
    for row in inputs['source_manifest']:
        row['sha256'] = hashlib.sha256((repo / row['path']).read_bytes()).hexdigest()
    request, release, _, _ = live_gate(s); before = load(s.directory / 'runtime_session.json'); tokens = dict(s.live_tokens)
    attach = attachment(s, inputs)
    s.record = s.call('reattach-session', attach)['result']  # Every call is a new OS client process.
    for key in ('owner', 'generation', 'lease_epoch', 'outstanding_operation_ref'):
        require(s.record.get(key) == before.get(key), 'reattach recovers checked live identity and pending operation')
    require(all(process_token(p) == t for p, t in tokens.items()), 'reattach preserves actual live SBCL process')
    for key, value, reason in [('requester', OTHER, 'foreign_owner'), ('expected_lease_epoch', before['lease_epoch'] + 1, 'stale_lease'),
            ('expected_generation', {'counter': 0, 'nonce': '0' * 32}, 'stale_generation'),
            ('expected_outstanding_operation_ref', 'wrong-operation', 'continuity_mismatch')]:
        response = s.call('reattach-session', {**attach, key: value}, 1)
        require(response['error'] == reason, 'stale/foreign/mismatched continuity refused')
    path = s.directory / 'runtime_session.json'; original = path.read_bytes(); changed = json.loads(original)
    changed['outstanding_operation_ref'] = 'unrelated-pending-operation'; path.write_text(json.dumps(changed))
    try:
        response = s.call('reattach-session', attachment(s, inputs), 70)
        require(response['error'] in ('infrastructure', 'ambiguous_state') and
                all(process_token(p) == t for p, t in tokens.items()), 'ambiguous continuity refuses reattachment without replacing runtime')
    finally:
        path.write_bytes(original)
    live_busy(s); release.touch(); s.terminal(request); live_nonce(s, os.urandom(16).hex())
    require(s.runstate.read_bytes() == s.saved_state, 'reattach preserves governed attempt')


def live_cancel(s, executable):
    request, release, cleaning, witness = live_gate(s, cleanup=True); control = s.cancellation(request)
    for key, value in [('operation_id', 'unknown'), ('expected_generation', {'counter': 0, 'nonce': '0' * 32}),
                       ('expected_lease_epoch', 100), ('requester', OTHER)]:
        response = s.call('cancel-operation', {**control, key: value}, 1)
        require(response['ok'] is False and s.poll(request['operation_id'])['status'] == 'running',
                'uncorrelated cancellation cannot stop actual pending work')
    response = s.call('cancel-operation', control)['result']
    require(response['status'] == 'cancel_requested' and response.get('cancellation_confirmed') is False,
            'CANCEL_REQUEST_IS_UNCONFIRMED')
    wait_for(lambda: cleaning.exists() and cleaning.read_text().splitlines() == [witness], 'real unwind-protect cleanup starts')
    response = s.poll(request['operation_id'])
    require(response['status'] in ('cancel_requested', 'unknown') and response.get('cancellation_confirmed') is not True,
            'cleanup still blocked; runtime has not stopped')
    live_busy(s); s.call('cancel-operation', control); release.touch()
    terminal = s.terminal(request, ('cancelled',))
    require(terminal['cancellation_confirmed'] is True and cleaning.read_text().splitlines() == [witness] and
            Path(str(cleaning) + '-done').is_file() and Path(str(cleaning) + '-done').read_text().splitlines() == [witness],
            'only finished correlated cleanup permits confirmed cancellation')
    with tempfile.TemporaryDirectory(prefix='completion-race-', dir=s.home) as temp:
        peer = LiveSession(Path(temp), candidate=s.candidate)
        try:
            peer.start(executable); live_nonce(peer, os.urandom(16).hex())
            completed = peer.eval('42'); before = peer.operation(completed['operation_id']).read_bytes()
            require(peer.call('cancel-operation', peer.cancellation(completed))['result']['status'] == 'completed' and
                    peer.operation(completed['operation_id']).read_bytes() == before, 'completion-winning cancellation is immutable')
        finally:
            peer.cleanup()
    require(s.runstate.read_bytes() == s.saved_state, 'cancellation does not reset attempt')


def group_descendant_fixture(home, operation_id, nonce):
    """Exact private native spawn form; finite lifetime is a cleanup backstop."""
    ready, pulse = [Path(home) / (prefix + nonce) for prefix in ('group-ready-', 'group-pulse-')]
    program = ("import json, os, signal, time\nfrom pathlib import Path\n"
               "os.setpgid(0, os.getpgid(os.getppid()))\n"
               "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
               "ready=Path(" + repr(str(ready)) + "); pulse=Path(" + repr(str(pulse)) + ")\n"
               "ready.write_text(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'pgid':os.getpgid(0),"
               "'nonce':" + repr(nonce) + ",'operation_id':" + repr(operation_id) + "}))\n"
               "end=time.monotonic()+45; count=0\n"
               "while time.monotonic()<end:\n count+=1; tmp=pulse.with_suffix('.tmp'); tmp.write_text(str(count)); tmp.replace(pulse); time.sleep(.02)\n")
    program_literal = '"' + program.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"') + '"'
    form = ('(progn (sb-ext:run-program ' + json.dumps(sys.executable) + ' (list "-c" ' + program_literal +
            ') :search nil :wait nil :input nil :output nil :error nil) 42)')
    return form, ready, pulse


def live_group_descendant(s):
    request = s.lisp('pending'); nonce = os.urandom(16).hex()
    form, ready, pulse = group_descendant_fixture(s.home, request['operation_id'], nonce)
    request['payload']['expression'] = form; s.submit(request); s.terminal(request)
    wait_for(lambda: ready.is_file() and pulse.is_file(), 'actual runtime-spawned descendant readiness')
    witness = load(ready); pid = witness['pid']; token = process_token(pid)
    leader, leader_token = next(iter(s.live_tokens.items())); group = os.getpgid(leader)
    require(witness == {'pid': pid, 'ppid': leader, 'pgid': group, 'nonce': nonce,
                        'operation_id': request['operation_id']} and token is not None and
            process_token(leader) == leader_token and group == leader and
            group != os.getpgrp() and live_owned(s.marker).get(pid) == token and os.getpgid(pid) == group,
            'actual descendant belongs to the proven owned runtime group')
    before = int(pulse.read_text()); os.kill(pid, signal.SIGTERM)
    wait_for(lambda: process_token(pid) == token and int(pulse.read_text()) > before,
             'actual descendant continues progress after TERM')
    print('LIVE_GROUP_DESCENDANT', json.dumps({**witness, 'token': token, 'leader_token': leader_token,
          'term_ignored_with_progress': True, 'spawn_form_sha256': hashlib.sha256(form.encode()).hexdigest()}), flush=True)
    return pid, token


def live_partial_frame_deadline(s, executable):
    """An accepted incomplete request cannot defer an existing cancellation."""
    s.start(executable); live_nonce(s, os.urandom(16).hex())
    request, _, _, _ = live_gate(s, uninterruptible=True, limits={'timeout_seconds': 1})
    tokens = dict(s.live_tokens); meta = load(s.directory / 'controller.json')
    supervisor = meta['supervisor_pid']; supervisor_token = process_token(supervisor)
    require(supervisor_token and live_owned(s.marker).get(supervisor) == supervisor_token and s.owns_lock(supervisor),
            'deadline control proves private supervisor identity and lock')
    response = s.call('cancel-operation', s.cancellation(request))['result']; durable_at = time.monotonic()
    durable = load(s.operation(request['operation_id']))
    require(response['status'] == durable['status'] == 'cancel_requested' and
            durable.get('cancellation_confirmed') is False and
            load(s.directory / 'runtime_session.json')['outstanding_operation_ref'] == str(s.operation(request['operation_id']).resolve()) and
            all(process_token(pid) == token for pid, token in tokens.items()),
            'deadline control begins after durable unconfirmed cancellation of actual pending work')
    def sockets():
        try:
            return {link[8:-1] for fd in Path(f'/proc/{supervisor}/fd').iterdir()
                    if (link := os.readlink(fd)).startswith('socket:[')}
        except OSError:
            return set()
    before = sockets()
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(1); client.connect(str(s.directory / 'control.sock')); client.sendall(b'{')
        def accepted():
            connected = {row[6] for line in Path('/proc/net/unix').read_text().splitlines()[1:]
                         if len(row := line.split()) > 6 and row[5] == '03'}
            return sorted((sockets() - before) & connected)
        inodes = wait_for(accepted, 'private supervisor accepted the incomplete client frame', .6)
        require(process_token(supervisor) == supervisor_token and s.owns_lock(supervisor) and
                load(s.operation(request['operation_id']))['status'] == 'cancel_requested' and
                any(process_token(pid) == token for pid, token in tokens.items()),
                'accepted partial frame overlaps actual unresolved cancellation')
        # Contract1s + TERM-to-KILL.25s + death observation1s + scheduling.25s.
        bound = 2.5
        while time.monotonic() - durable_at < bound:
            durable = load(s.operation(request['operation_id']))
            if durable['status'] == 'terminated' and all(process_token(pid) != token for pid, token in tokens.items()):
                break
            time.sleep(.01)
        elapsed = time.monotonic() - durable_at
        print('LIVE_PARTIAL_FRAME_DEADLINE', json.dumps({'operation_id': request['operation_id'],
              'supervisor_pid': supervisor, 'supervisor_token': supervisor_token, 'accepted_socket_inodes': inodes,
              'runtime_tokens': tokens, 'elapsed_seconds': elapsed, 'bound_seconds': bound,
              'durable_status': durable['status'], 'runtime_still_live': [pid for pid, token in tokens.items() if process_token(pid) == token]}), flush=True)
        require(durable['status'] == 'terminated' and durable.get('cancellation_confirmed') is not True and
                durable['image_consistent'] is False and elapsed <= bound + .05 and
                all(process_token(pid) != token for pid, token in tokens.items()),
                'CANCEL_DEADLINE_SERVICED_DURING_PARTIAL_FRAME')
    s.terminal(request, ('terminated',))
    require(load(s.directory / 'runtime_session.json')['outstanding_operation_ref'] is None and
            s.runstate.read_bytes() == s.saved_state, 'deadline resolution clears only observed dead work and preserves attempt')


def live_terminate(s, executable):
    descendant, descendant_token = live_group_descendant(s)
    request, _, _, _ = live_gate(s, uninterruptible=True); tokens = dict(s.live_tokens)
    sentinel_marker = s.home / 'unrelated-runtime'
    argv = [executable, '--no-sysinit', '--no-userinit', '--non-interactive', '--eval',
            '(progn ' + lisp_write(sentinel_marker, 'unrelated') + ' (sleep 60))']
    sentinel = subprocess.Popen(argv, cwd=s.home, env={**os.environ}, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        wait_for(sentinel_marker.exists, 'unrelated SBCL positive control started')
        s.call('cancel-operation', s.cancellation(request)); terminal = s.terminal(request, ('terminated',), 30)
        require(terminal['image_consistent'] is False and terminal.get('cancellation_confirmed') is not True and
                all(process_token(p) != t for p, t in tokens.items()), 'terminated only after actual owned runtime death')
        require(process_token(descendant) != descendant_token, 'OWNED_RUNTIME_GROUP_DEATH_BEYOND_LEADER')
        require(sentinel.poll() is None, 'unrelated SBCL survives owned-group termination')
        stale_marker = s.home / 'forbidden-stale-execution'
        stale = s.lisp('(progn ' + lisp_write(stale_marker, 'forbidden') + ' 42)')
        before = dict(s.record); rejected = s.call('submit-operation', stale, (1, 70))
        require(rejected['ok'] is False and not any(process_token(p) == t for p, t in tokens.items()),
                'old generation cannot execute or silently auto-restart')
        s.record = s.call('open-session', s.opening())['result']
        require(s.record['generation']['counter'] > before['generation']['counter'] and
                s.record['generation']['nonce'] != before['generation']['nonce'], 'NEW_GENERATION')
        require(s.call('submit-operation', {**stale, 'operation_id': 'stale-after-reconstruction'}, 1)['error'] == 'stale_generation' and not stale_marker.exists(),
                'old-generation work cannot execute after explicit reconstruction')
        s.observe_runtime(executable); live_nonce(s, os.urandom(16).hex())
        require(s.runstate.read_bytes() == s.saved_state, 'reconstruction preserves governed attempt')
    finally:
        sentinel.terminate(); out, err = sentinel.communicate(timeout=3)
        print('LIVE_UNRELATED_CONTROL', repr({'argv': argv, 'pid': sentinel.pid, 'exit': sentinel.returncode,
              'stdout': out, 'stderr': err}), flush=True)


def diagnostic(s, record, budget=16384, full=False):
    """Proposed interface-intent1 adapter; joint independent bundle/API review required."""
    require(record.get('condition_capture') == 'before_unwind', 'CAPTURE_BEFORE_UNWIND')
    path = Path(record['condition_ref']); directory = s.directory / 'diagnostics'
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and
            path.resolve().is_relative_to(directory.resolve()), 'diagnostic reference resolves inside this private session')
    relative = path.relative_to(directory)
    require(all(not p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(s.directory)),
            'diagnostic reference has no symlink components')
    require(record['operation_id'] in [p.split('.')[0] for p in relative.parts], 'diagnostic artifact keyed to this operation')
    require(0 < path.stat().st_size <= budget, 'DIAGNOSTIC_BYTE_BUDGET')
    with path.open('rb') as stream:
        data = stream.read(budget + 1)
    require(0 < len(data) <= budget, 'DIAGNOSTIC_BYTE_BUDGET')
    print('LIVE_DIAGNOSTIC', json.dumps({'operation_id': record['operation_id'], 'condition_ref': str(path),
          'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'content': data.decode('utf-8')}), flush=True)
    if data == b'0':
        require(not full, 'FULL_CAPTURE_NOT_OMISSION_SENTINEL')
        return None
    value = json.loads(data)
    require(type(value) is dict and set(value) == {'condition', 'backtrace', 'restarts', 'truncated', 'capture_failed'},
            'diagnostic structured sections and explicit capture markers')
    condition = value['condition']
    require(type(condition) is dict and set(condition) == {'type', 'text', 'fallback'} and
            all(type(condition[k]) is str for k in ('type', 'text')) and type(condition['fallback']) is bool and
            all(type(value[k]) is bool for k in ('truncated', 'capture_failed')), 'typed condition identity and bounded fallback markers')
    require(type(value['backtrace']) is list and type(value['restarts']) is list, 'structural backtrace/restart arrays')
    previous = -1
    for frame in value['backtrace']:
        require(type(frame) is dict and set(frame) == {'index', 'frame'} and type(frame['index']) is int and
                frame['index'] > previous and type(frame['frame']) is str, 'actual ordered bounded backtrace entries')
        previous = frame['index']
    for restart in value['restarts']:
        require(type(restart) is dict and set(restart) == {'name', 'description'} and
                (restart['name'] is None or type(restart['name']) is str) and type(restart['description']) is str,
                'serialized restart descriptions, not invocable objects')
    return value


def condition_fixture(s, kind='evaluate', report=None, restart_report=None):
    request = s.lisp('pending', kind); nonce = os.urandom(12).hex().upper()
    condition, frame, restart = ['N129-' + name + '-' + nonce for name in ('CONDITION', 'FRAME', 'RESTART')]
    progress, cleanup, invoked = [s.home / (prefix + nonce) for prefix in ('condition-progress-', 'unwound-', 'restart-invoked-')]
    witness = request['operation_id'] + ':' + nonce
    body = ('(define-condition ' + condition + ' (error) () (:report (lambda (c stream) (declare (ignore c)) ' +
            (report or '(write-string "plain-condition-identity" stream)') + '))) ' +
            '(declaim (optimize (debug 3) (speed 0)) (notinline ' + frame + ')) ' +
            '(defun ' + frame + ' () (restart-case (error (quote ' + condition + ')) (' + restart +
            ' () :report ' + (restart_report or '"active-restart-description"') + ' ' + lisp_write(invoked, witness) + '))) ' +
            lisp_write(progress, witness) + ' (unwind-protect (' + frame + ') ' + lisp_write(cleanup, witness) + ')')
    if kind == 'compile_source':
        body = '(eval-when (:compile-toplevel :load-toplevel :execute) ' + body + ')'
    request['payload']['expression'] = body
    return request, progress, cleanup, invoked, witness, (condition, frame, restart)


def capture_fixture(s, kind, report, restart_report, limits):
    """Private project witnesses, not backend fields or callback requirements.

    The common native-qualified fixture stays unchanged.  When a project
    callback actually runs, record its printer bindings and native start tick;
    cleanup records its end tick.  CLI startup/poll latency is excluded.
    Safe metadata fallback may avoid the callback entirely.
    """
    nonce = os.urandom(12).hex(); callback = s.home / ('capture-callback-' + nonce)
    ended = s.home / ('capture-end-' + nonce)
    prefix = ('(with-open-file (probe ' + json.dumps(str(callback)) +
              ' :direction :output :if-exists nil :if-does-not-exist :create) '
              '(when probe (format probe "~D ~D~%~S/~S/~S~%" (get-internal-real-time) internal-time-units-per-second '
              '*print-level* *print-length* *print-circle*))) ')
    rendering = '(format stream "N129-CAPTURE/~S/~S/~S/END~%" *print-level* *print-length* *print-circle*) '
    wrapped_report = (prefix + rendering + '(let ((n129-report-start (get-internal-real-time))) ' + report +
                      ' (format stream "~&N129-CAPTURE-TICKS/~D/~D/~D/END~%" n129-report-start '
                      '(get-internal-real-time) internal-time-units-per-second))') if report is not None else None
    wrapped_restart = None
    if restart_report is not None:
        # Existing restart-report fixture is a lambda; this wrapper observes
        # invocation without requiring the producer to invoke project code.
        wrapped_restart = '(lambda (out) ' + prefix + ' (funcall ' + restart_report + ' out))'
    fixture = condition_fixture(s, kind, wrapped_report, wrapped_restart)
    request, _, cleanup, _, witness, _ = fixture
    original = lisp_write(cleanup, witness)
    ending = ('(progn (with-open-file (probe ' + json.dumps(str(ended)) +
              ' :direction :output :if-exists :supersede) (format probe "~D~%" (get-internal-real-time))) ' + original + ')')
    require(request['payload']['expression'].count(original) == 1, 'private capture fixture has one cleanup witness')
    request['payload']['expression'] = request['payload']['expression'].replace(original, ending)
    request['limits'] = limits or {}
    return fixture, callback, ended


def capture_bindings(text):
    fields = text.split('/')
    require(len(fields) == 3, 'complete printer binding observation')
    require(fields[0] == '6', 'CAPTURE_PRINT_LEVEL')
    require(fields[1] == '32', 'CAPTURE_PRINT_LENGTH')
    require(fields[2] == 'T', 'CAPTURE_PRINT_CIRCLE')


def capture_deadline(start, end, units, limits):
    require(units >= 200, 'native callback clock resolution at most5ms')
    elapsed = (end - start) / units
    bound = min(.25, limits.get('timeout_seconds', .25))
    print('LIVE_CAPTURE_DEADLINE', json.dumps({'elapsed_seconds': elapsed, 'requested_bound_seconds': bound,
          'unwind_scheduling_allowance_seconds': .025}), flush=True)
    require(0 <= elapsed <= bound + .025, 'CAPTURE_REQUESTED_DEADLINE')


def capture_observation(callback, ended, limits):
    # A scheduling allowance of25ms is for the signal/unwind and one witness
    # write, not CLI latency.  It cannot hide the finite300ms printer below.
    # Native clocks coarser than5ms are unsuitable for this observation.
    if not callback.exists():
        print('LIVE_CAPTURE_CALLBACK', json.dumps({'invoked': False, 'proof': 'safe capture/fallback checked separately'}), flush=True)
        return
    lines = callback.read_text().splitlines()
    require(len(lines) == 2, 'complete project callback witness')
    start, units = map(int, lines[0].split())
    capture_bindings(lines[1])
    require(ended.is_file(), 'completed capture has actual cleanup clock')
    print('LIVE_CAPTURE_CALLBACK', json.dumps({'invoked': True, 'bindings': lines[1],
          'callback_witness': str(callback), 'cleanup_clock': str(ended)}), flush=True)
    capture_deadline(start, int(ended.read_text()), units, limits)


def live_unresolved_capture(s, request, progress, cleanup, invoked, witness):
    """A stuck printer is still work; only real stop/death resolves it."""
    wait_for(lambda: progress.exists() and progress.read_text().splitlines() == [witness], 'actual hostile-condition dispatch')
    started = time.monotonic()
    response = s.call('poll-operation', {**s.identity(), 'operation_id': request['operation_id'],
                      'limits': {'timeout_seconds': .1}}, (0, 70))
    require(time.monotonic() - started < 3, 'bounded client wait for hostile capture; not diagnostic budget proof')
    record = response['result']
    if record['status'] == 'condition_signalled':
        return s.terminal(request, ('condition_signalled',))
    tokens = dict(s.live_tokens)
    if record['status'] != 'terminated':
        require(record['status'] in ('running', 'unknown', 'cancel_requested') and
                record.get('cancellation_confirmed') is not True and not invoked.exists(), 'HOSTILE_CAPTURE_REMAINS_UNRESOLVED')
        before = load(s.directory / 'runtime_session.json')
        require(before['outstanding_operation_ref'] == str(s.operation(request['operation_id']).resolve()) and
                any(process_token(pid) == token for pid, token in tokens.items()), 'unresolved capture retains actual runtime and outstanding work')
        live_busy(s)
        s.call('cancel-operation', s.cancellation(request), (0, 70))
        record = s.terminal(request, ('condition_signalled', 'cancelled', 'terminated'), 8)
    else:
        record = s.terminal(request, ('terminated',))
    if record['status'] == 'condition_signalled':
        return record  # A completion-winning race must satisfy all strict capture assertions.
    require(record['image_consistent'] is False and not invoked.exists(), 'HOSTILE_STOP_FALSE_CONSISTENCY')
    if record['status'] == 'cancelled':
        require(record.get('cancellation_confirmed') is True and cleanup.is_file() and
                cleanup.read_text().splitlines() == [witness], 'HOSTILE_CANCEL_CONFIRMED_CLEANUP')
    else:
        require(record.get('cancellation_confirmed') is not True and
                all(process_token(pid) != token for pid, token in tokens.items()), 'HOSTILE_TERMINATED_OBSERVED_DEATH')
    marker = s.home / ('forbidden-hostile-reuse-' + request['operation_id'])
    response = s.call('submit-operation', s.lisp('(progn ' + lisp_write(marker, 'forbidden') + ' 42)'), (1, 70))
    require(response['ok'] is False and not marker.exists() and s.runstate.read_bytes() == s.saved_state,
            'unsafe hostile image remains quarantined without replacement or attempt reset')
    print('LIVE_HOSTILE_RESOLUTION', json.dumps({'operation_id': request['operation_id'], 'status': record['status'],
          'image_consistent': record['image_consistent'], 'completed_capture_proof': False}), flush=True)
    return None


def live_rendered_snapshot(s):
    logs, diagnostics = {}, {}
    for path in s.directory.glob('child.*.log'):
        require(not path.is_symlink() and path.is_file() and path.stat().st_uid == os.getuid(), 'owned regular captured output')
        logs[path.name] = path.stat().st_size
    directory = s.directory / 'diagnostics'
    require(not directory.is_symlink(), 'private diagnostics directory has no symlink')
    if directory.exists():
        require(directory.is_dir(), 'private diagnostics directory')
        for path in directory.rglob('*'):
            require(not path.is_symlink() and path.stat().st_uid == os.getuid() and
                    (path.is_dir() or path.is_file()), 'owned regular diagnostic material')
            if path.is_file():
                st = path.stat()
                diagnostics[str(path.relative_to(directory))] = (st.st_size, st.st_mtime_ns, st.st_ino)
    return logs, diagnostics


def live_rendered_guard(s, before, limits):
    logs, diagnostics = live_rendered_snapshot(s); old_logs, old_diagnostics = before
    require(all(logs.get(name, -1) >= size for name, size in old_logs.items()) and
            all(diagnostics.get(name) == stamp for name, stamp in old_diagnostics.items()),
            'rendering cannot discard captured output or overwrite earlier diagnostics')
    log_bytes = sum(logs.values()) - sum(old_logs.values())
    diagnostic_bytes = sum(stamp[0] for name, stamp in diagnostics.items() if name not in old_diagnostics)
    budget = min(16384, limits.get('output_bytes', 16384))
    print('LIVE_RENDERED_BYTES', json.dumps({'log_bytes': log_bytes, 'diagnostic_bytes': diagnostic_bytes,
          'budget': budget, 'condition_ref_required': False}), flush=True)
    require(log_bytes + diagnostic_bytes <= budget, 'DIAGNOSTIC_BYTE_BUDGET')


def aborted_capture_observation(callback, ended):
    # These are lifetime observations, never an assertion about when capture
    # was abandoned. A killed callback need not finish either witness file.
    if not callback.exists():
        return
    text = callback.read_text(); lines = text.splitlines()
    if len(lines) == 2 and text.endswith('\n'):
        capture_bindings(lines[1])
    observation = {'callback_witness': str(callback), 'complete_binding_witness': len(lines) == 2 and text.endswith('\n'),
                   'completed_capture_proof': False, 'deadline_asserted': False}
    if lines and ended.is_file():
        first = lines[0].split(); end = ended.read_text().strip()
        if len(first) == 2 and all(value.isdigit() for value in [*first, end]) and int(first[1]) > 0:
            observation['aborted_lifetime_seconds'] = (int(end) - int(first[0])) / int(first[1])
    print('LIVE_ABORTED_CALLBACK', json.dumps(observation), flush=True)


def live_condition(s, kind='evaluate', report=None, limits=None, full=True, omission_required=False,
                   restart_report=None, allow_unresolved=False):
    fixture, callback, ended = capture_fixture(s, kind, report, restart_report, limits)
    request, progress, cleanup, invoked, witness, names = fixture
    request['limits'] = limits or {}; before = live_rendered_snapshot(s)
    s.submit(request)
    record = (live_unresolved_capture(s, request, progress, cleanup, invoked, witness) if allow_unresolved else
              s.terminal(request, ('condition_signalled',)))
    live_rendered_guard(s, before, request['limits'])
    if record is None:
        aborted_capture_observation(callback, ended)
        return  # Actual busy-to-observed-stop proof above; never a fabricated diagnostic success.
    require(progress.read_text().splitlines() == [witness] and cleanup.read_text().splitlines() == [witness],
            'correlated project progress and actual unwind happened; setup is successful')
    require(not invoked.exists(), 'no arbitrary or durable restart automatically invoked')
    if kind in ('load_source', 'compile_source'):
        require(record['image_consistent'] is False, 'partial load/compile never claims rollback or image consistency')
    budget = min(16384, request['limits'].get('output_bytes', 16384))
    value = diagnostic(s, record, budget, full)
    capture_observation(callback, ended, request['limits'])
    if value is not None:
        require(value['condition']['type'].rsplit(':', 1)[-1].upper() == names[0], 'actual captured condition identity')
        # Public report text is an additional observation when project printing
        # runs.  Metadata-only fallback need not invent this report output.
        for observed in re.findall(r'N129-CAPTURE/([^\r\n]+)/END', value['condition']['text']):
            capture_bindings(observed)
        for ticks in re.findall(r'N129-CAPTURE-TICKS/(\d+)/(\d+)/(\d+)/END', value['condition']['text']):
            capture_deadline(*map(int, ticks), request['limits'])
    if full:
        symbols = lambda text: [word.rsplit(':', 1)[-1].upper() for word in re.findall(r'[A-Za-z0-9_:+*/<>=!?-]+', text)]
        require(any(names[1] in symbols(item['frame']) for item in value['backtrace']), 'CAPTURE_ACTIVE_FRAME')
        require(any(item['name'] is not None and item['name'].rsplit(':', 1)[-1].upper() == names[2]
                    for item in value['restarts']), 'CAPTURE_ACTIVE_RESTART')
    elif omission_required:
        require(value is None or value['condition']['fallback'] or value['truncated'] or value['capture_failed'],
                'hostile/omitted rendering has explicit fallback, truncation or capture failure')
    if kind in ('load_source', 'compile_source'):
        response = s.call('submit-operation', s.lisp('42'), 1)['result']
        require(response['status'] == 'rejected' and response['executed'] is False, 'inconsistent image is quarantined')
    validate_records(s)


def live_capture(s, executable):
    live_condition(s)
    with tempfile.TemporaryDirectory(prefix='compile-', dir=s.home) as temp:
        peer = LiveSession(Path(temp), candidate=s.candidate)
        try:
            peer.start(executable); live_nonce(peer, os.urandom(16).hex()); live_condition(peer, 'compile_source')
        finally:
            peer.cleanup()


def live_printing(s, executable):
    reports = [
        ('(write (loop repeat 100 collect (loop repeat 100 collect (list 1 2 3))) :stream stream)', {'output_bytes': 2048}),
        ('(let ((x (list 1))) (setf (cdr x) x) (write x :stream stream))', {'output_bytes': 2048}),
        ('(write-string (make-string 200000 :initial-element #\\x) stream)', {'output_bytes': 2048}),
        ('(error "hostile report callback")', {'output_bytes': 2048}),
        ('(loop (sleep 0.01))', {'output_bytes': 2048, 'timeout_seconds': .1}),
        ('(loop (sleep 0.01))', {'output_bytes': 1}),
        ('(loop (sleep 0.01))', {'output_bytes': 2048, 'timeout_seconds': 0}),
        ('(progn (defclass n129-unsafe-printer () ()) (defmethod print-object ((obj n129-unsafe-printer) out) '
         '(declare (ignore obj out)) (loop (sleep 0.01))) (write (make-instance (quote n129-unsafe-printer)) :stream stream))',
         {'output_bytes': 2048, 'timeout_seconds': .1})]
    live_condition(s)  # Mandatory nonvacuous healthy type/frame/restart proof.
    for index, (report, limits) in enumerate(reports):
        with tempfile.TemporaryDirectory(prefix='printer-', dir=s.home) as temp:
            peer = LiveSession(Path(temp), candidate=s.candidate)
            try:
                peer.start(executable); live_nonce(peer, os.urandom(16).hex())
                live_condition(peer, report=report, limits=limits, full=False, omission_required=index != 1,
                               allow_unresolved=index in (4, 5, 6, 7))
            finally:
                peer.cleanup()
    # Finite300ms reports expose a renderer that silently ignores .1/0 but
    # returns within the old3second hang guard.  If project code is safely
    # skipped, normal diagnostic/fallback proof is still mandatory.  If it
    # runs and returns, its own clock must meet min(.25, requested)+25ms.
    for seconds in (.1, 0):
        with tempfile.TemporaryDirectory(prefix='finite-printer-', dir=s.home) as temp:
            peer = LiveSession(Path(temp), candidate=s.candidate)
            try:
                peer.start(executable); live_nonce(peer, os.urandom(16).hex())
                live_condition(peer, report='(sleep 0.3) (write-string "finite-report-complete" stream)',
                               limits={'output_bytes': 2048, 'timeout_seconds': seconds}, full=False,
                               omission_required=True, allow_unresolved=True)
            finally:
                peer.cleanup()
    with tempfile.TemporaryDirectory(prefix='restart-printer-', dir=s.home) as temp:
        peer = LiveSession(Path(temp), candidate=s.candidate)
        try:
            peer.start(executable); live_nonce(peer, os.urandom(16).hex())
            live_condition(peer, limits={'output_bytes': 2048, 'timeout_seconds': .1}, full=False,
                           restart_report='(lambda (out) (declare (ignore out)) (loop (sleep 0.01)))', allow_unresolved=True)
        finally:
            peer.cleanup()
    with tempfile.TemporaryDirectory(prefix='tiny-result-', dir=s.home) as temp:
        peer = LiveSession(Path(temp), candidate=s.candidate)
        try:
            peer.start(executable); live_nonce(peer, os.urandom(16).hex())
            marker = peer.home / 'scalar-dispatched'; request = peer.lisp('(progn ' + lisp_write(marker, '42') + ' 42)', limits={'output_bytes': 1})
            peer.submit(request); wait_for(marker.exists, 'tiny scalar actually dispatched')
            record = wait_for(lambda: (r if (r := peer.poll(request['operation_id']))['status'] != 'running' else None), 'truthful tiny scalar outcome')
            require(record['status'] in ('condition_signalled', 'unknown', 'terminated'), 'unrepresentable scalar never becomes altered completed value')
        finally:
            peer.cleanup()


def live_control_candidate(home, fault):
    """Disposable observation mutant: real backend runs; only public observations change.

    Never used for baseline admission, production repair, or an accepted candidate.
    Diagnostic mutations use proposed interface-intent1, reviewed with this bundle.
    """
    candidate = home / 'candidate'; (candidate / 'tools/fixtures/runtime_session').mkdir(parents=True)
    for relative in ('tools/sbcl_session_loop.lisp', 'tools/fixtures/runtime_session/stub_runtime.py'):
        shutil.copyfile(ROOT / relative, candidate / relative)
    shutil.copyfile(ROOT / 'tools/runtime_session.py', candidate / 'tools/real_runtime_session.py')
    wrapper = '''import json, subprocess, sys
from pathlib import Path
fault = FAULT
p = subprocess.Popen([sys.executable, str(Path(__file__).with_name('real_runtime_session.py')), *sys.argv[1:]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(timeout=35)
print(json.dumps({'control_real_cli_pid': p.pid, 'actual_exit': p.returncode, 'original_stdout': out, 'original_stderr': err}), file=sys.stderr, flush=True)
response = json.loads(out); record = response.get('result', {}); code = p.returncode
root = Path(sys.argv[sys.argv.index('--root') + 1])
request = json.loads(Path(sys.argv[sys.argv.index('--request') + 1]).read_text())
if fault == 'runtime-refusal-accepted' and sys.argv[1] == 'open-session' and p.returncode in (1, 64) and request.get('runtime') in ('stub', 'not-a-runtime'):
 response = {'ok': True, 'result': {}}; record = {}; code = 0
if isinstance(record, dict):
 if fault == 'premature-cancel' and sys.argv[1] == 'cancel-operation' and record.get('status') == 'cancel_requested':
  record.update(status='cancelled', cancellation_confirmed=True)
 if fault == 'mismatched-cancel' and record.get('status') == 'cancelled': record['operation_id'] = 'wrong-correlated-operation'
 if record.get('status') == 'condition_signalled':
  if fault == 'late-capture': record['condition_capture'] = 'after_unwind'
  if fault in ('missing-restart', 'missing-frame'):
   path = Path(record['condition_ref']); value = json.loads(path.read_text())
   value['restarts' if fault == 'missing-restart' else 'backtrace'] = []
   path.write_text(json.dumps(value))
  if fault == 'unbounded':
   directory = Path(sys.argv[sys.argv.index('--root') + 1]) / record['session_id']
   path = Path(record['condition_ref']); path = path if path.is_absolute() else directory / path
   path.write_bytes(path.read_bytes() + b' ' * 65536)
  if fault in ('print-level', 'print-length', 'print-circle'):
   path = Path(record['condition_ref'])
   if path.read_bytes() != b'0':
    value = json.loads(path.read_text())
    value['condition']['text'] = 'N129-CAPTURE/' + {'print-level': '7/32/T', 'print-length': '6/33/T', 'print-circle': '6/32/NIL'}[fault] + '/END'
    path.write_text(json.dumps(value))
 if fault == 'generation-reuse' and sys.argv[1] == 'open-session' and response.get('ok'):
  path = Path(sys.argv[sys.argv.index('--root') + 1]) / 'control-first-generation.json'
  if path.exists(): record['generation'] = json.loads(path.read_text())
  else: path.write_text(json.dumps(record['generation']))
print(json.dumps(response), flush=True)
sys.exit(code)
'''.replace('FAULT', repr(fault))
    (candidate / 'tools/runtime_session.py').write_text(wrapper)
    print('LIVE_MUTANT', json.dumps({'fault': fault, 'candidate': str(candidate),
          'real_product_sha256': hashlib.sha256((candidate / 'tools/real_runtime_session.py').read_bytes()).hexdigest(),
          'wrapper_sha256': hashlib.sha256(wrapper.encode()).hexdigest()}), flush=True)
    return candidate


def live_scenario(selection, home, executable, candidate=ROOT):
    s = LiveSession(home, candidate=candidate)
    try:
        s.start(executable); live_nonce(s, os.urandom(16).hex()); live_runtime_guards(s, executable)
        if selection == 5:
            live_wait(s)
        elif selection == 6:
            live_reattach(s)
        elif selection == 'cancel-confirmed':
            live_cancel(s, executable)
            with tempfile.TemporaryDirectory(prefix='partial-frame-deadline-', dir=home) as temp:
                peer = LiveSession(Path(temp), candidate=candidate)
                try:
                    live_partial_frame_deadline(peer, executable)
                finally:
                    peer.cleanup()
        elif selection == 'termination-ends-generation':
            live_terminate(s, executable)
            with tempfile.TemporaryDirectory(prefix='zero-deadline-', dir=home) as temp:
                peer = LiveSession(Path(temp), candidate=candidate)
                try:
                    peer.start(executable); live_nonce(peer, os.urandom(16).hex())
                    request, _, _, _ = live_gate(peer, uninterruptible=True, limits={'timeout_seconds': 0})
                    tokens = dict(peer.live_tokens); started = time.monotonic()
                    response = peer.call('cancel-operation', peer.cancellation(request), (0, 70))
                    require(response['result']['status'] != 'cancelled', 'zero confirmation deadline never fabricates clean cancellation')
                    peer.terminal(request, ('terminated',), 5)
                    require(time.monotonic() - started < 4 and all(process_token(p) != t for p, t in tokens.items()),
                            'zero requested deadline leads to bounded observed owned-process death')
                finally:
                    peer.cleanup()
        elif selection == 'capture-before-unwind':
            live_capture(s, executable)
        elif selection == 'bounded-printing':
            live_printing(s, executable)
        elif selection == 4:
            live_condition(s, 'load_source')
        else:
            raise RuntimeError('unknown deep selector; never intended semantic red')
    finally:
        s.cleanup()


def live_rendered_overflow_control(home, executable):
    """Common guard mechanics after real positives; no fabricated runtime status.

    A conforming metadata-only producer may never expose unresolved reporting.
    The production branch uses this same guard before its None return; this
    control corrupts only disposable file observations, not backend outcomes.
    """
    # Short prefixes keep the nested control socket inside the 107-byte sockaddr_un limit.
    with tempfile.TemporaryDirectory(prefix='ro-', dir=home) as temp:
        s = LiveSession(Path(temp))
        try:
            s.start(executable); live_nonce(s, os.urandom(16).hex()); live_condition(s)
            for kind in ('log', 'diagnostic'):
                before = live_rendered_snapshot(s)
                path = (s.directory / 'child.guard-control.log' if kind == 'log' else
                        s.directory / 'diagnostics' / 'guard-control-overflow')
                require(not path.exists(), 'overflow control uses a fresh private observation path')
                try:
                    path.write_bytes(b'x' * 2049)
                    try:
                        live_rendered_guard(s, before, {'output_bytes': 2048})
                    except AssertionError as exc:
                        require(str(exc) == 'BEHAVIOR_ASSERTION: DIAGNOSTIC_BYTE_BUDGET', 'overflow control exact assertion')
                        print('LIVE_NEGATIVE_CONTROL', json.dumps({'fault': kind + '-overflow-after-resolution',
                              'observed_assertion': str(exc), 'scope': 'common guard file-observation mechanics after real nonce/full-condition progress',
                              'unresolved_backend_branch_executed': False, 'fabricated_backend_status': False}), flush=True)
                    else:
                        raise AssertionError('BEHAVIOR_ASSERTION: common rendering guard accepted overflow')
                finally:
                    path.unlink()
            # A real evaluate condition may conservatively quarantine its image.
            # The subsequent execution positive belongs to a fresh private image.
            with tempfile.TemporaryDirectory(prefix='op-', dir=s.home) as fresh:
                peer = LiveSession(Path(fresh), candidate=s.candidate)
                try:
                    peer.start(executable); live_nonce(peer, os.urandom(16).hex())
                    require(peer.runstate.read_bytes() == peer.saved_state, 'fresh overflow positive preserves governed attempt')
                finally:
                    peer.cleanup()
            require(s.runstate.read_bytes() == s.saved_state, 'overflow control preserves governed attempt')
        finally:
            s.cleanup()


def live_negative_controls(selection, home, executable):
    controls = {5: [('runtime-refusal-accepted', 'RUNTIME_SELECTION_GUARD')],
                'cancel-confirmed': [('premature-cancel', 'CANCEL_REQUEST_IS_UNCONFIRMED'),
                                   ('mismatched-cancel', 'TERMINAL_CORRELATION')],
                'termination-ends-generation': [('generation-reuse', 'NEW_GENERATION')],
                'capture-before-unwind': [('late-capture', 'CAPTURE_BEFORE_UNWIND'), ('missing-restart', 'CAPTURE_ACTIVE_RESTART'),
                                          ('missing-frame', 'CAPTURE_ACTIVE_FRAME')],
                'bounded-printing': [('unbounded', 'DIAGNOSTIC_BYTE_BUDGET'), ('print-level', 'CAPTURE_PRINT_LEVEL'),
                                     ('print-length', 'CAPTURE_PRINT_LENGTH'), ('print-circle', 'CAPTURE_PRINT_CIRCLE')]}
    if selection == 'bounded-printing':
        live_rendered_overflow_control(home, executable)
    for fault, expected in controls.get(selection, []):
        with tempfile.TemporaryDirectory(prefix='mutant-', dir=home) as temp:
            scratch = Path(temp); candidate = live_control_candidate(scratch, fault)
            fixture = scratch / 'fixture'; fixture.mkdir()
            try:
                live_scenario(selection, fixture, executable, candidate)
            except AssertionError as exc:
                require(str(exc) == 'BEHAVIOR_ASSERTION: ' + expected, 'targeted mutant must fail the exact intended assertion')
                print('LIVE_NEGATIVE_CONTROL', json.dumps({'fault': fault, 'expected_assertion': expected,
                      'observed_assertion': str(exc), 'result': 'rejected', 'accepted_product': False}), flush=True)
            else:
                raise AssertionError('BEHAVIOR_ASSERTION: targeted faulty observation escaped its assertion')


def registry_sexp(path):
    """Explicit source registry. An empty variable is not this configuration."""
    return '(:source-registry (:directory "%s") :ignore-inherited-configuration)' % (str(path) + '/')


def translation_sexp(path):
    """Explicit output translations. An empty variable is not this configuration."""
    return '(:output-translations (t ("%s" :implementation)) :ignore-inherited-configuration)' % (str(path) + '/')


def private_sbcl_env(home, **extra):
    """Build a private SBCL environment without copying inherited Lisp configuration."""
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(home), 'LC_ALL': 'C',
           'XDG_CONFIG_HOME': str(home / 'config'), 'XDG_CACHE_HOME': str(home / 'cache'),
           'XDG_DATA_HOME': str(home / 'data')}
    env.update(extra)
    return env


def run_sbcl(executable, home, program, env, extra_argv=(), timeout=30):
    """Run one fresh no-init SBCL and return its actual exit, output, and argv."""
    home.mkdir(parents=True, exist_ok=True)
    path = home / 'probe.lisp'
    path.write_text(program)
    argv = [str(executable), *extra_argv, '--noinform', '--no-sysinit', '--no-userinit',
            '--non-interactive', '--load', str(path)]
    code, out, err = live_process(argv, home, env, timeout=timeout)
    return code, out, err


def git_bytes(repo, *args):
    """Return committed Git output bytes without stripping the blob."""
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    completed = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-C', str(repo), *args],
                               env=env, capture_output=True, timeout=20)
    require(completed.returncode == 0, 'committed blob is readable')
    return completed.stdout


def fasl_hashes(root):
    """Hash fasl files under one cache. A fresh process can reuse them unchanged."""
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in Path(root).rglob('*.fasl')}


def prepare_hermetic_hazards(home, executable):
    """Commit a source fixture, then plant unsaved, stale-fasl, decoy, and development-image hazards."""
    repo = home / 'source'
    repo.mkdir()
    git_fixture(repo, 'init', '-q')
    files = {
        'n130.asd': '(defsystem "n130" :components ((:file "n130-macro") (:file "n130-main" :depends-on ("n130-macro"))))\n',
        'n130-macro.lisp': '(defpackage :n130 (:use :cl) (:export #:token #:n130-use #:n130-macro))\n'
                           '(in-package :n130)\n(defmacro n130-macro () \'"COMMITTED-MACRO")\n',
        'n130-main.lisp': '(in-package :n130)\n(defun token () "COMMITTED")\n(defun n130-use () (n130-macro))\n',
        'n130-noop.asd': '(defsystem "n130-noop" :components ())\n',
        'n130-failure.asd': '(defsystem "n130-failure" :components ((:file "n130-failure")))\n',
        'n130-failure.lisp': '(eval-when (:compile-toplevel :load-toplevel :execute) (error "genuine-failure"))\n',
    }
    for name, text in files.items():
        (repo / name).write_text(text)
    sources = [{'path': name, 'sha256': hashlib.sha256((repo / name).read_bytes()).hexdigest()}
               for name in sorted(files)]
    (repo / 'acceptance.lock').write_text(json.dumps({
        'failure_system': 'n130-failure', 'noop_system': 'n130-noop', 'primary_system': 'n130', 'sources': sources,
    }, indent=2, sort_keys=True) + '\n')
    git_fixture(repo, 'add', '--', '.')
    git_fixture(repo, '-c', 'user.name=Acceptance Fixture', '-c', 'user.email=acceptance@example.invalid',
                'commit', '-qm', 'pin committed source')
    (repo / 'n130-main.lisp').write_text('(in-package :n130)\n(defun token () "UNSAVED")\n(defun n130-use () (n130-macro))\n')
    (repo / 'n130-macro.lisp').write_text('(defpackage :n130 (:use :cl) (:export #:token #:n130-use #:n130-macro))\n'
                                          '(in-package :n130)\n(defmacro n130-macro () \'"UNSAVED-MACRO")\n')
    decoy = home / 'decoy'
    decoy.mkdir()
    (decoy / 'n130.asd').write_text('(defsystem "n130" :components ((:file "n130-main")))\n')
    (decoy / 'n130-main.lisp').write_text('(defpackage :n130 (:use :cl) (:export #:token #:n130-use #:n130-macro))\n'
                                          '(in-package :n130)\n(defun token () "DECOY")\n(defun n130-use () "DECOY")\n'
                                          '(defmacro n130-macro () \'"DECOY")\n')
    shared = home / 'shared-cache'
    shared.mkdir()
    hazard_env = private_sbcl_env(home / 'hazard-home', CL_SOURCE_REGISTRY=registry_sexp(repo),
                                  ASDF_OUTPUT_TRANSLATIONS=translation_sexp(shared))
    hazard_program = '(require :asdf)\n(asdf:load-system "n130")\n(format t "N130-HAZARD:~A:~A~%" (n130:token) (n130:n130-use))\n(sb-ext:quit :unix-status 0)\n'
    code, out, err = run_sbcl(executable, home / 'hazard-compile', hazard_program, hazard_env)
    require(code == 0 and 'N130-HAZARD:UNSAVED:UNSAVED-MACRO' in out, 'dirty tree compiles an unsaved fasl')
    future = time.time() + 86400
    for path in shared.rglob('*.fasl'):
        os.utime(path, (future, future))
    stale = fasl_hashes(shared)
    require(stale, 'unsaved macro fasl is present in the shared cache')
    code, out, err = run_sbcl(executable, home / 'hazard-reuse', hazard_program, hazard_env)
    require(code == 0 and 'N130-HAZARD:UNSAVED:UNSAVED-MACRO' in out, 'fresh process reuses the unsaved fasl')
    require('compiling file' not in (out + err).lower() and fasl_hashes(shared) == stale,
            'fresh process is not a fresh build')
    dev_core = home / 'dev.core'
    code, out, err = run_sbcl(executable, home / 'dev-save',
                              '(defun n130-deleted () "DELETED-SURVIVOR")\n(save-lisp-and-die ' + json.dumps(str(dev_core)) + ')\n',
                              private_sbcl_env(home / 'dev-home'))
    require(code == 0 and dev_core.is_file(), 'development image can be saved')
    code, out, err = run_sbcl(executable, home / 'dev-boot',
                              '(format t "SURVIVOR:~A~%" (n130-deleted))\n(sb-ext:quit :unix-status 0)\n',
                              private_sbcl_env(home / 'dev-boot-home'), ('--core', str(dev_core)))
    require(code == 0 and 'SURVIVOR:DELETED-SURVIVOR' in out, 'deleted definition survives only in the development image')
    version = subprocess.run([str(executable), '--version'], capture_output=True, text=True, timeout=10,
                             env=private_sbcl_env(home / 'version-home'))
    require(version.returncode == 0 and version.stdout.strip(), 'pinned toolchain version is readable')
    return {'repo': repo, 'revision': git_fixture(repo, 'rev-parse', 'HEAD'), 'decoy': decoy, 'shared': shared,
            'registry': registry_sexp(decoy), 'translations': translation_sexp(shared), 'fasl_hashes': stale,
            'dev_core': dev_core, 'dev_sha': hashlib.sha256(dev_core.read_bytes()).hexdigest(),
            'ambient_home': str(Path.home()), 'executable': str(Path(executable).resolve()),
            'executable_sha': hashlib.sha256(Path(executable).resolve().read_bytes()).hexdigest(),
            'version_text': version.stdout, 'asd_sha': hashlib.sha256((repo / 'n130.asd').read_bytes()).hexdigest()}


def hermetic_role(receipt, role):
    found = [item for item in receipt['processes'] if item.get('role') == role]
    require(len(found) == 1, role + ' process captured once')
    return found[0]


def assert_hermetic_controls(receipt, record, hazards):
    """Require the shared hermetic proof: archive, fresh process, private locations, and distinct controls."""
    repo = hazards['repo']
    require(receipt['controls_ok'] is True and receipt['failure_reason'] is None, 'hermetic controls completed')
    require(receipt['fresh_process_is_fresh_build'] is False, 'a fresh process is not a fresh build')
    require(receipt['empty_environment_sufficient'] is False, 'empty environment variables are not sufficient')
    require(receipt['illustrative_forms_are_launcher'] is False, 'section 9 forms are not a tested launcher')
    require(receipt['source_revision'] == hazards['revision'] == record['source_revision'], 'actual source revision')
    require(record['source_state'] == 'committed' and record['lock_ref'] == receipt['lock_ref'], 'committed lock binding')
    archive = Path(receipt['archive_root'])
    private_root = archive.parent
    require(archive.is_dir() and archive.resolve() != repo.resolve(), 'git archive has a private root')
    manifest = {item['path']: item['sha256'] for item in receipt['source_manifest']}
    archived = sorted(path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file())
    require(archived == sorted([*manifest, 'acceptance.lock']), 'archive contains the lock and the locked sources')
    for name, digest in manifest.items():
        blob = (archive / name).read_bytes()
        require(hashlib.sha256(blob).hexdigest() == digest and git_bytes(repo, 'show', 'HEAD:' + name) == blob,
                'archived source is the committed blob')
        require(not path_is_symlink(archive / name), 'archived source is a regular file')
    lock_bytes = (archive / 'acceptance.lock').read_bytes()
    require(git_bytes(repo, 'show', 'HEAD:acceptance.lock') == lock_bytes, 'archived lock is committed')
    require(receipt['lock_ref'] == hashlib.sha256(lock_bytes).hexdigest() != hazards['asd_sha'],
            'lock digest is not an ASDF system definition')
    require(b'UNSAVED' in (repo / 'n130-main.lisp').read_bytes() and b'UNSAVED' not in (archive / 'n130-main.lisp').read_bytes(),
            'unsaved worktree definition is outside the archive')
    require(b'UNSAVED-MACRO' in (repo / 'n130-macro.lisp').read_bytes()
            and b'UNSAVED-MACRO' not in (archive / 'n130-macro.lisp').read_bytes(),
            'unsaved macro is outside the archive')
    require(b'DECOY' in (hazards['decoy'] / 'n130-main.lisp').read_bytes(), 'decoy source is a distinct hazard')
    output = Path(receipt['output_cache'])
    require(receipt['output_cache_empty_before'] is True and output.is_dir() and output.resolve() != hazards['shared'].resolve(),
            'private ASDF output cache starts empty')
    require(str(output) + '/' in receipt['output_translations'] and ':ignore-inherited-configuration' in receipt['output_translations'],
            'output translations name the private cache')
    require(str(archive) + '/' in receipt['source_registry'] and ':ignore-inherited-configuration' in receipt['source_registry'],
            'source registry names the private archive')
    require(receipt['inherited']['CL_SOURCE_REGISTRY'] == hazards['registry']
            and receipt['inherited']['ASDF_OUTPUT_TRANSLATIONS'] == hazards['translations']
            and receipt['inherited']['HOME'] != receipt['private_home'],
            'inherited registry and translations were visible and were replaced')
    home = Path(receipt['private_home'])
    xdg = receipt['xdg']
    require(home.is_dir() and home.resolve() != Path(hazards['ambient_home']).resolve(), 'private HOME')
    for key in ('config', 'cache', 'data'):
        require(Path(xdg[key]).is_dir() and Path(xdg[key]).resolve().is_relative_to(home.resolve()), 'private XDG ' + key)
    processes = receipt['processes']
    require(len(processes) == 5, 'core, setup, no-op, failure, and primary processes')
    flags = ('--no-sysinit', '--no-userinit', '--non-interactive')
    for item in processes:
        argv = item['observed_argv']
        require(argv and argv == item['requested_argv'], 'captured argv is the live command line')
        require(all(flag in argv for flag in flags) and '--script' not in argv, 'fresh no-init non-interactive process')
        require(Path(item['observed_cwd']).resolve().is_relative_to(private_root.resolve()), 'private process cwd')
        env = item['observed_env']
        require(env.get('HOME') == str(home) and env.get('XDG_CONFIG_HOME') == xdg['config']
                and env.get('XDG_CACHE_HOME') == xdg['cache'] and env.get('XDG_DATA_HOME') == xdg['data'],
                'observed private HOME and XDG locations')
        text = item.get('driver_text') or ''
        require('initialize-source-registry' not in text and 'initialize-output-translations' not in text
                and '/candidate/src/' not in text and '/candidate/deps/' not in text and '/candidate/build/' not in text,
                'illustrative section 9 forms are not the launcher')
    for role in ('setup', 'noop', 'failure', 'primary'):
        item = hermetic_role(receipt, role)
        require(item['core_argument'] is True and item['fresh_flags'] is True, role + ' uses the pinned fresh core')
        registry = item['observed_env'].get('CL_SOURCE_REGISTRY') or ''
        translations = item['observed_env'].get('ASDF_OUTPUT_TRANSLATIONS') or ''
        require(registry not in ('', hazards['registry']) and translations not in ('', hazards['translations']),
                'empty or inherited configuration was not reused')
        require(':ignore-inherited-configuration' in registry and ':ignore-inherited-configuration' in translations,
                'explicit ignore-inherited configuration')
        require(str(hazards['decoy']) not in registry and str(hazards['shared']) not in translations,
                'decoy registry and shared cache are not the acceptance configuration')
        require(str(hazards['dev_core']) not in ' '.join(item['observed_argv']), 'development image is not booted')
    setup, noop, failure, primary = (hermetic_role(receipt, role) for role in ('setup', 'noop', 'failure', 'primary'))
    require(setup['condition'] == 'MISSING-COMPONENT' and setup['new_files'] == [] and setup['rebuild_proof'] is False
            and setup.get('setup_failure') is True, 'setup failure is not rebuild proof')
    require(noop['ok'] is True and noop['condition'] is None and noop['new_files'] == [] and noop.get('noop') is True
            and noop.get('genuine_failure') is not True, 'ASDF no-op is not a genuine failure')
    require(failure['condition'] == 'SIMPLE-ERROR' and failure['ok'] is False and failure['new_files'] == []
            and failure.get('genuine_failure') is True and failure['condition'] != setup['condition'],
            'genuine ASDF failure is distinct from the no-op and the setup failure')
    require('failure-output' in (failure['observed_env'].get('ASDF_OUTPUT_TRANSLATIONS') or '')
            and receipt['output_cache'] in (noop['observed_env'].get('ASDF_OUTPUT_TRANSLATIONS') or ''),
            'failure control uses a different output cache from the no-op')
    require(primary['markers'].get('N130-LOAD') == 'ok', 'committed system loaded')
    source = Path(primary['markers'].get('N130-SOURCE', ''))
    require(source.is_file() and source.resolve().is_relative_to(archive.resolve())
            and b'DECOY' not in source.read_bytes() and b'UNSAVED' not in source.read_bytes(),
            'loaded system source is the archived committed file')
    core = receipt['core_provenance']
    core_path = Path(core['ref'])
    require(core['kind'] == 'trusted_base' and core_path.is_file()
            and hashlib.sha256(core_path.read_bytes()).hexdigest() == core['sha256']
            and core['sha256'] != hazards['dev_sha'] and core_path.resolve() != hazards['dev_core'].resolve(),
            'clean core provenance is not the development image')
    require(record['core_provenance'] == core, 'operation core provenance matches the receipt')
    toolchain = receipt['toolchain']
    require(toolchain['implementation'] == 'SBCL' and toolchain['version_text'] == hazards['version_text']
            and toolchain['executable'] == hazards['executable']
            and toolchain['executable_sha256'] == hazards['executable_sha'] and toolchain['asdf_version'],
            'actual toolchain executable, version, and ASDF')
    require(record['toolchain_identity']['implementation'] == 'SBCL'
            and record['toolchain_identity']['version'] == toolchain['version'], 'operation toolchain identity')
    require(record['command_refs'] == primary['observed_argv'], 'command provenance is the observed primary argv')
    require(record['isolation'] == {'process': 'fresh', 'build_cache': 'fresh_private_empty',
            'fixtures': 'committed_source', 'configuration': 'ignore_inherited', 'dependencies': 'hermetic',
            'resources': 'isolated_or_reset'}, 'operation isolation is hermetic')
    fresh = {hashlib.sha256((output / name).read_bytes()).hexdigest() for name in primary['new_files']}
    require(primary['new_files'] and fresh.isdisjoint(hazards['fasl_hashes'].values()),
            'acceptance compiled committed source into the private cache')
    for relative, digest in hazards['fasl_hashes'].items():
        require(hashlib.sha256((hazards['shared'] / relative).read_bytes()).hexdigest() == digest,
                'inherited fasl bytes stayed unchanged')
    require(fasl_hashes(hazards['shared']) == hazards['fasl_hashes'], 'shared fasl set stayed unchanged')


def path_is_symlink(path):
    return Path(path).is_symlink()


def assert_hermetic_focus(name, receipt, hazards):
    """Discriminate the named obligation inside the shared proof."""
    if name == 'committed-source-archive':
        require(b'COMMITTED' in Path(hermetic_role(receipt, 'primary')['markers']['N130-SOURCE']).read_bytes()
                or b'COMMITTED' in (Path(receipt['archive_root']) / 'n130-main.lisp').read_bytes(),
                'private archive holds committed definitions')
    elif name == 'no-init-process':
        require(all(item['fresh_flags'] for item in receipt['processes']), 'every acceptance process is fresh no-init')
        require(hermetic_role(receipt, 'setup')['rebuild_proof'] is False and receipt['rebuild_proof'] is True,
                'fresh setup process is not rebuild proof')
    elif name == 'private-home-xdg':
        require(Path(receipt['private_home']).resolve() != Path(hazards['ambient_home']).resolve(),
                'HOME is not the ambient home')
    elif name == 'empty-output-cache':
        require(receipt['output_cache_empty_before'] is True and receipt['output_translations'].strip(),
                'newly created output cache is configured explicitly')
    elif name == 'ignore-inherited-resolution':
        require(':ignore-inherited-configuration' in receipt['source_registry']
                and ':ignore-inherited-configuration' in receipt['output_translations'],
                'both replacement configurations ignore inherited configuration')
    elif name == 'toolchain-lock-core-bound':
        require(receipt['toolchain']['executable_sha256'] == hazards['executable_sha']
                and receipt['core_provenance']['sha256'] != hazards['dev_sha']
                and receipt['lock_ref'] != hazards['asd_sha'],
                'toolchain, lock, and clean core are bound')
    elif name == 'asdf-noop-control':
        require(hermetic_role(receipt, 'noop')['condition'] is None
                and hermetic_role(receipt, 'failure')['condition'] == 'SIMPLE-ERROR',
                'no-op control stays distinct from genuine failure')
    elif name == 'asdf-failure-control':
        require(hermetic_role(receipt, 'failure')['condition'] == 'SIMPLE-ERROR'
                and hermetic_role(receipt, 'setup')['condition'] == 'MISSING-COMPONENT'
                and hermetic_role(receipt, 'setup')['rebuild_proof'] is False,
                'genuine failure stays distinct from setup failure')
    else:
        raise RuntimeError('unknown hermetic check')


def hermetic_once(home, executable, hazards, expression, accepted):
    """Run one acceptance in a fresh session. A rejected expression quarantines that session."""
    home.mkdir()
    session = LiveSession(home)
    session.env['CL_SOURCE_REGISTRY'] = hazards['registry']
    session.env['ASDF_OUTPUT_TRANSLATIONS'] = hazards['translations']
    try:
        session.start(executable)
        request = session.lisp(expression, kind='run_tests')
        request['context'] = {'working_dir': str(hazards['repo'])}
        session.submit(request)
        record = session.terminal(request, ('completed', 'condition_signalled'), 50)
        receipt_path = session.directory / 'acceptance' / (request['operation_id'] + '.json')
        require(receipt_path.is_file(), 'acceptance receipt written')
        receipt = load(receipt_path)
        operation = load(session.operation(request['operation_id']))
        require(operation['status'] == record['status'] and operation['evidence_class'] == 'development',
                'operation evidence class and status')
        if accepted:
            require(record['status'] == 'completed' and record['image_consistent'] is True, 'accepted image stays consistent')
            require(receipt['accepted'] is True and receipt['expression_passed'] is True and receipt['rebuild_proof'] is True,
                    'committed expression accepted with rebuild proof')
            require(hermetic_role(receipt, 'primary')['markers'].get('N130-VALUE') == '"pass"', 'expression value is pass')
            result = load(session.result_path(request['operation_id']))
            require(result['result'] == 'pass' and result['status'] == 'completed' and result['image_consistent'] is True,
                    'completed result is pass')
            follow = session.lisp('(+ 19 23)')
            session.submit(follow)
            session.terminal(follow)
            require(load(session.result_path(follow['operation_id']))['result'] == 42, 'session loop still evaluates')
            session.observe_runtime(executable)
        else:
            require(record['status'] == 'condition_signalled' and record['image_consistent'] is False,
                    'rejected acceptance signals a condition')
            require(receipt['accepted'] is False and receipt['expression_passed'] is False and receipt['rebuild_proof'] is False,
                    'must-fail expression does not count as acceptance or rebuild proof')
            require(str(hermetic_role(receipt, 'primary')['markers'].get('N130-VALUE', '')).startswith('fail:'),
                    'must-fail expression reaches a Lisp condition')
            require(not session.result_path(request['operation_id']).exists(), 'signalled acceptance has no result file')
        assert_hermetic_controls(receipt, operation, hazards)
        try:
            validate_records(session)
        except AssertionError:
            raise
        except Exception as exc:
            require(False, f'operation record schema: {type(exc).__name__}: {exc}')
        return receipt
    finally:
        session.cleanup()


def hermetic_command(check, case, home, executable):
    """Run one feature 130 command. Cases 7, 10, 11, and 12 share one proof."""
    hazards = prepare_hermetic_hazards(home, executable)
    if case is not None:
        receipt = hermetic_once(home / 'accepted', executable, hazards, HERMETIC_PASS, True)
        assert_hermetic_focus('committed-source-archive', receipt, hazards)
        assert_hermetic_focus('asdf-noop-control', receipt, hazards)
        assert_hermetic_focus('asdf-failure-control', receipt, hazards)
        for index, expression in enumerate(HERMETIC_MUST_FAIL, start=1):
            hermetic_once(home / f'must-fail-{index}', executable, hazards, expression, False)
        return
    receipt = hermetic_once(home / 'accepted', executable, hazards, HERMETIC_PASS, True)
    assert_hermetic_focus(check, receipt, hazards)


def live_main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', choices=(*LIVE_CHECKS, *HERMETIC_CHECKS))
    choice.add_argument('--case', type=int, choices=(4, 5, 6, *HERMETIC_CASES))
    parser.add_argument('--runtime', choices=('sbcl',)); parser.add_argument('--require-sbcl', action='store_true')
    args = parser.parse_args()
    if args.case is not None and args.runtime != 'sbcl' or args.check and args.runtime:
        parser.error('SBCL cases require --runtime sbcl; named checks select SBCL intrinsically')
    if not (ROOT / 'tools/runtime_session.py').is_file():
        raise RuntimeError('controller source absent, never intended admission red')
    with tempfile.TemporaryDirectory(prefix='n129-') as temp:
        home = Path(temp); executable = sbcl_preflight(home)
        if args.check in HERMETIC_CHECKS or args.case in HERMETIC_CASES:
            hermetic_command(args.check, args.case, home, executable)
        elif args.check == 'sbcl-admission':
            admission(home, executable)
        else:
            live_scenario(args.check or args.case, home, executable)
            live_negative_controls(args.check or args.case, home, executable)
        print('PASS', args.check or f'case{args.case}/sbcl')
        return 0


if __name__ == '__main__':
    try:
        sys.exit(live_main() if live_selection(sys.argv[1:]) else main())
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f'SETUP_OR_INFRASTRUCTURE_FAILURE: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(2)
