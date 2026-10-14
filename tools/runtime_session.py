#!/usr/bin/env python3
"""Partial Linux development-session controller (standard library only).

Exit codes: 0 admitted/successful; 1 refused; 64 usage; 70 infrastructure.
Declared identities and exclusive locks coordinate work; they do not authenticate.
The five implemented calls use JSON request files. Only submit-operation sends
an execute frame. Cancellation, reattachment and fresh acceptance are deferred.
"""
import argparse
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import re
import secrets
import select
import selectors
import signal
import socket
import subprocess
import sys
import tempfile
import time

FRAME_LIMIT = 65536
CONTROL_SECONDS = 5
ACTIONS = {'open-session', 'submit-operation', 'poll-operation',
           'transfer-session', 'close-session'}
RESERVED = {'cancel-operation', 'reattach-session', 'accept'}
KINDS = {'load_source', 'compile_source', 'evaluate', 'run_tests', 'observe'}
ROLES = {'Orchestrator', 'Planner', 'Generator', 'Validator', 'Evaluator', 'review_trial'}
IDENTITY = {'session_id', 'requester', 'expected_generation', 'expected_lease_epoch'}
BINDING = ('contract_id', 'step_key', 'attempt')


class SessionError(Exception):
    def __init__(self, code, reason):
        self.code, self.reason = code, reason
        super().__init__(reason)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise SessionError(64, 'usage')


def fail(code, reason):
    raise SessionError(code, reason)


def insist(condition):
    if not condition:
        fail(64, 'usage')


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def string(value):
    return isinstance(value, str) and bool(value)


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None


def object_keys(value, required, optional=()):
    insist(type(value) is dict and set(required) <= value.keys()
           and value.keys() <= set(required) | set(optional))


def principal(value):
    object_keys(value, {'principal_kind'}, {'role', 'agent_id'})
    insist(value['principal_kind'] in ('human', 'agent'))
    if value['principal_kind'] == 'agent':
        insist('role' in value and 'agent_id' in value)
    if 'role' in value:
        insist(isinstance(value['role'], str) and value['role'] in ROLES)
    if 'agent_id' in value:
        insist(string(value['agent_id']))


def generation(value):
    object_keys(value, {'counter', 'nonce'})
    insist(integer(value['counter']) and string(value['nonce']))


def trial(request):
    return isinstance(request, dict) and any(
        isinstance(request.get(key), dict) and request[key].get('role') == 'review_trial'
        for key in ('requester', 'owner', 'new_owner'))


def lifecycle(requester, owner=None):
    return (requester.get('principal_kind') == 'agent' and requester.get('role') == 'Orchestrator'
            or requester.get('principal_kind') == 'human' and requester == owner)


def permitted_owner(owner):
    return owner['principal_kind'] == 'human' or owner.get('role') == 'Generator'


def parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail(64, 'usage')
            result[key] = value
        return result
    def constant(value):
        fail(64, 'usage')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        fail(64, 'usage')


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()


def read_json(path):
    return parse_json(Path(path).read_bytes())


def atomic_json(path, value):
    """Publish complete JSON, preserving the old pathname until replacement."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_request(action, request):
    if action == 'open-session':
        required = {'session_id', 'requester', 'owner', 'purpose', 'run_state_path', *BINDING}
        object_keys(request, required, {'expected_generation', 'expected_lease_epoch'})
        principal(request['owner'])
        insist(string(request['purpose']) and string(request['run_state_path'])
               and Path(request['run_state_path']).is_absolute())
        insist(('expected_generation' in request) == ('expected_lease_epoch' in request))
    else:
        extra = {'submit-operation': {'operation_id', 'kind', 'payload', 'context', 'limits', *BINDING},
                 'poll-operation': {'operation_id'}, 'transfer-session': {'new_owner'},
                 'close-session': set()}[action]
        object_keys(request, IDENTITY | extra)
    insist(identifier(request['session_id']))
    principal(request['requester'])
    if 'expected_generation' in request:
        generation(request['expected_generation'])
        insist(integer(request['expected_lease_epoch']))
    if 'operation_id' in request:
        insist(identifier(request['operation_id']))
    if action in ('open-session', 'submit-operation'):
        insist(identifier(request['contract_id']) and identifier(request['step_key'])
               and integer(request['attempt'], 1))
    if action == 'transfer-session':
        principal(request['new_owner'])
    if action != 'submit-operation':
        return
    insist(isinstance(request['kind'], str) and request['kind'] in KINDS)
    context = request['context']
    object_keys(context, set(), {'working_dir', 'namespace', 'reader_config_ref', 'test_config_ref'})
    insist(all(string(value) for value in context.values()))
    limits = request['limits']
    object_keys(limits, set(), {'timeout_seconds', 'output_bytes'})
    if 'timeout_seconds' in limits:
        value = limits['timeout_seconds']
        insist(type(value) in (int, float) and math.isfinite(value) and value >= 0)
    if 'output_bytes' in limits:
        insist(integer(limits['output_bytes'], 1))
    payload = request['payload']
    object_keys(payload, {'expression'})
    insist(string(payload['expression']))
    expression = parse_json(payload['expression'])
    insist(type(expression) is dict and isinstance(expression.get('op'), str))
    op = expression['op']
    insist(op in ('set', 'get', 'gate'))
    object_keys(expression, {'op', 'release_path'} if op == 'gate'
                else {'op', 'name', 'value'} if op == 'set' else {'op', 'name'})
    insist(string(expression['release_path' if op == 'gate' else 'name']))


def attempt_matches(binding, request):
    if any(request.get(key) != binding.get(key) for key in BINDING):
        return False
    try:
        state = read_json(binding['run_state_path'])
        count = state['circuit_breaker'][binding['step_key']]['attempts']
        return integer(count, 1) and count == binding['attempt']
    except (OSError, KeyError, TypeError, SessionError):
        return False


def response_error(reason, record=None):
    result = {'ok': False, 'error': reason}
    if record is not None:
        result['result'] = record
    return result


def response_code(response):
    if response['ok']:
        return 0
    return {'usage': 64, 'infrastructure': 70}.get(response['error'], 1)


def receive_line(source, deadline):
    data = bytearray()
    fd = source if isinstance(source, int) else source.fileno()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            fail(70, 'infrastructure')
        part = os.read(fd, FRAME_LIMIT + 1 - len(data))
        if not part:
            fail(70, 'infrastructure')
        data.extend(part)
        if len(data) > FRAME_LIMIT:
            fail(64, 'usage')
        if b'\n' in data:
            insist(data.count(b'\n') == 1 and data.endswith(b'\n'))
            return parse_json(data)


def live_token(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except (OSError, IndexError):
        return None


class Supervisor:
    def __init__(self, root, request, lock_fd):
        self.root, self.request, self.lock_fd = root, request, lock_fd
        self.directory = root / request['session_id']
        self.child = None
        self.selector = selectors.DefaultSelector()
        self.protocol = bytearray()
        self.ready = False
        self.broken = False
        self.outstanding = None
        self.stop = False
        self.server = None
        self.log_truncated = set()

    def session_write(self):
        atomic_json(self.directory / 'runtime_session.json', self.session)

    def operation_path(self, operation_id):
        return self.directory / 'operations' / f'{operation_id}.json'

    def prepare(self):
        request = self.request
        session_path = self.directory / 'runtime_session.json'
        previous = read_json(session_path) if session_path.exists() else None
        meta_path = self.directory / 'controller.json'
        previous_meta = read_json(meta_path) if meta_path.exists() else None
        if previous:
            if (request.get('expected_generation') != previous['generation']
                    or request.get('expected_lease_epoch') != previous['lease_epoch']):
                fail(1, 'stale_generation')
            if previous['owner'] != request['owner']:
                fail(1, 'foreign_owner')
            if previous.get('outstanding_operation_ref'):
                fail(1, 'session_busy')
            if not previous_meta or any(previous_meta.get(k) != request[k]
                                        for k in (*BINDING, 'run_state_path')):
                fail(1, 'attempt_mismatch')
        elif previous_meta or 'expected_generation' in request:
            fail(70, 'infrastructure')
        if not attempt_matches(request, request):
            fail(1, 'attempt_mismatch')
        counter = previous['generation']['counter'] + 1 if previous else 1
        self.session = {'session_id': request['session_id'], 'purpose': 'develop',
                        'owner': request['owner'], 'lease_epoch': previous['lease_epoch'] if previous else 0,
                        'generation': {'counter': counter, 'nonce': secrets.token_hex(16)},
                        'outstanding_operation_ref': None}
        self.meta = {key: request[key] for key in (*BINDING, 'run_state_path')}
        self.meta.update(supervisor_pid=os.getpid(), supervisor_pgid=os.getpgrp(),
                         supervisor_token=live_token(os.getpid()), child_pid=None,
                         previous_generation=previous['generation'] if previous else None)
        (self.directory / 'operations').mkdir(exist_ok=True)
        # Reserve the incarnation durably before any child exists.
        atomic_json(meta_path, self.meta)
        self.session_write()
        read_fd, write_fd = os.pipe()
        def child_fd3():
            os.dup2(write_fd, 3)
        stub = Path(__file__).resolve().parent / 'fixtures/runtime_session/stub_runtime.py'
        try:
            self.child = subprocess.Popen(
                [sys.executable, str(stub)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, pass_fds=tuple({write_fd, 3}), preexec_fn=child_fd3,
                cwd=self.root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        finally:
            os.close(write_fd)
        self.meta['child_pid'] = self.child.pid
        atomic_json(meta_path, self.meta)
        for fd, channel in ((read_fd, 'protocol'), (self.child.stdout.fileno(), 'stdout'),
                            (self.child.stderr.fileno(), 'stderr')):
            os.set_blocking(fd, False)
            self.selector.register(fd, selectors.EVENT_READ, channel)
        self.child.stdin.write(encode({'type': 'init', 'generation': self.session['generation']}))
        self.child.stdin.flush()
        end = time.monotonic() + CONTROL_SECONDS
        while not self.ready and not self.broken and time.monotonic() < end:
            self.pump(min(.1, max(0, end - time.monotonic())))
        if not self.ready or self.broken:
            fail(70, 'infrastructure')
        endpoint = self.directory / 'control.sock'
        if endpoint.exists():
            endpoint.unlink()
        self.server = socket.socket(socket.AF_UNIX)
        self.server.bind(str(endpoint))
        self.server.listen(16)
        self.selector.register(self.server, selectors.EVENT_READ, 'server')

    def log(self, channel, data):
        path = self.directory / f'child.{channel}.log'
        size = path.stat().st_size if path.exists() else 0
        marker = b'\n[diagnostic output truncated]\n'
        available = max(0, FRAME_LIMIT - len(marker) - size)
        with path.open('ab') as stream:
            stream.write(data[:available])
            if len(data) > available and channel not in self.log_truncated:
                stream.write(marker[:max(0, FRAME_LIMIT - size - min(len(data), available))])
                self.log_truncated.add(channel)

    def protocol_fault(self):
        self.broken = True
        self.protocol.clear()
        if self.outstanding:
            record = read_json(self.operation_path(self.outstanding))
            record.update(status='unknown', image_consistent=False)
            atomic_json(self.operation_path(self.outstanding), record)

    def frame(self, data):
        if self.broken:
            return
        try:
            value = parse_json(data)
            if not self.ready:
                object_keys(value, {'type', 'generation'})
                insist(value['type'] == 'ready')
                generation(value['generation'])
                insist(value['generation'] == self.session['generation'])
                self.ready = True
                return
            object_keys(value, {'type', 'operation_id', 'generation', 'status', 'result', 'image_consistent'})
            generation(value['generation'])
            insist(value['type'] == 'result' and value['operation_id'] == self.outstanding
                   and self.outstanding is not None and value['generation'] == self.session['generation']
                   and value['status'] == 'completed' and value['image_consistent'] is True)
            path = self.operation_path(self.outstanding)
            record = read_json(path)
            atomic_json(path.with_suffix('.result.json'), value)
            record.update(status='completed', image_consistent=True)
            atomic_json(path, record)
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.session_write()
        except (SessionError, ValueError, KeyError, TypeError):
            self.protocol_fault()

    def pump(self, seconds):
        for key, _ in self.selector.select(seconds):
            if key.data == 'server':
                self.serve()
                continue
            try:
                data = os.read(key.fd, FRAME_LIMIT + 1)
            except BlockingIOError:
                continue
            if not data:
                self.selector.unregister(key.fd)
                if key.data == 'protocol' and not self.stop:
                    self.protocol_fault()
                continue
            if key.data != 'protocol':
                self.log(key.data, data)
                continue
            self.protocol.extend(data)
            while b'\n' in self.protocol and not self.broken:
                index = self.protocol.index(b'\n') + 1
                if index > FRAME_LIMIT:
                    self.protocol_fault()
                    break
                line = bytes(self.protocol[:index])
                del self.protocol[:index]
                self.frame(line)
            if len(self.protocol) >= FRAME_LIMIT:
                self.protocol_fault()
            if self.broken:
                self.protocol.clear()

    def operation_record(self, request, reason=None):
        record = {key: copy.deepcopy(request[key]) for key in
                  ('operation_id', 'session_id', 'requester', 'expected_generation', 'expected_lease_epoch',
                   *BINDING, 'kind', 'payload', 'context', 'limits')}
        record.update(owner=self.session['owner'], generation=self.session['generation'],
                      lease_epoch=self.session['lease_epoch'], evidence_class='development',
                      status='rejected' if reason else 'running', executed=reason is None,
                      image_consistent=False)
        if reason:
            record['rejection_reason'] = reason
        # A refused foreign binding describes the request, not a transition of
        # this session's governed step. Never assert continuity between them.
        if (self.meta['previous_generation']
                and all(request[key] == self.meta[key] for key in BINDING)):
            record.update(previous_generation=self.meta['previous_generation'],
                          **{'previous_' + key: self.meta[key] for key in BINDING})
        return record

    def identity_reason(self, request, permit_orchestrator=False):
        if trial(request):
            return 'review_trial'
        actor = request['requester']
        if actor != self.session['owner'] and not (permit_orchestrator and lifecycle(actor)):
            return 'foreign_owner'
        if request['expected_generation'] != self.session['generation']:
            return 'stale_generation'
        if request['expected_lease_epoch'] != self.session['lease_epoch']:
            return 'stale_lease'
        return None

    def dispatch(self, action, request):
        if action not in ACTIONS or action == 'open-session':
            fail(1, 'unsupported')
        validate_request(action, request)
        if request['session_id'] != self.session['session_id']:
            fail(1, 'foreign_owner')
        if action == 'submit-operation':
            path = self.operation_path(request['operation_id'])
            if path.exists() or path.with_suffix('.result.json').exists():
                return response_error('conflict')
            reason = self.identity_reason(request)
            if not reason and not permitted_owner(request['requester']):
                reason = 'foreign_owner'
            if not reason and not attempt_matches(self.meta, request):
                reason = 'attempt_mismatch'
            if not reason and self.outstanding:
                reason = 'session_busy'
            if not reason and self.broken:
                fail(70, 'infrastructure')
            expression = parse_json(request['payload']['expression'])
            if expression['op'] == 'gate':
                release = Path(expression['release_path'])
                insist(release.is_absolute() and release.resolve().is_relative_to(self.root))
            record = self.operation_record(request, reason)
            atomic_json(path, record)
            if reason:
                return response_error(reason, record)
            self.outstanding = request['operation_id']
            self.session['outstanding_operation_ref'] = str(path)
            self.session_write()
            try:
                self.child.stdin.write(encode({'type': 'execute', 'request': request,
                                              'generation': self.session['generation']}))
                self.child.stdin.flush()
            except (BrokenPipeError, OSError):
                self.protocol_fault()
                fail(70, 'infrastructure')
            return {'ok': True, 'result': record}
        reason = self.identity_reason(request, permit_orchestrator=True)
        if reason:
            fail(1, reason)
        if action == 'poll-operation':
            path = self.operation_path(request['operation_id'])
            if not path.is_file():
                fail(1, 'unknown_operation')
            return {'ok': True, 'result': read_json(path)}
        if not lifecycle(request['requester'], self.session['owner']):
            fail(1, 'foreign_owner')
        if action == 'transfer-session':
            if not permitted_owner(request['new_owner']):
                fail(1, 'foreign_owner')
            if self.outstanding:
                fail(1, 'session_busy')
            if request['new_owner'] == self.session['owner']:
                fail(1, 'same_owner')
            self.session.update(transition='transfer', previous_owner=self.session['owner'],
                                previous_lease_epoch=self.session['lease_epoch'],
                                owner=request['new_owner'], lease_epoch=self.session['lease_epoch'] + 1)
            self.session_write()
            return {'ok': True, 'result': self.session}
        self.stop_child()
        if self.outstanding:
            record = read_json(self.operation_path(self.outstanding))
            record.update(status='terminated', image_consistent=False)
            atomic_json(self.operation_path(self.outstanding), record)
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.session_write()
        self.stop = True
        return {'ok': True, 'result': {'closed': True, 'session_id': self.session['session_id']}}

    def serve(self):
        connection, _ = self.server.accept()
        with connection:
            connection.settimeout(CONTROL_SECONDS)
            try:
                envelope = receive_line(connection, time.monotonic() + CONTROL_SECONDS)
                object_keys(envelope, {'action', 'request'})
                insist(isinstance(envelope['action'], str))
                response = self.dispatch(envelope['action'], envelope['request'])
            except SessionError as exc:
                response = response_error(exc.reason)
            except (OSError, KeyError, TypeError):
                response = response_error('infrastructure')
            try:
                connection.sendall(encode(response))
            except OSError:
                pass  # A disconnected caller cannot erase admitted work.

    def stop_child(self):
        if self.child and self.child.poll() is None:
            self.child.terminate()
            try:
                self.child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.child.kill()
                self.child.wait(timeout=2)

    def cleanup(self):
        self.stop_child()
        if self.server:
            self.server.close()
            (self.directory / 'control.sock').unlink(missing_ok=True)
        self.selector.close()
        os.close(self.lock_fd)


def open_session(root, request):
    if not lifecycle(request['requester']) or not permitted_owner(request['owner']):
        fail(1, 'foreign_owner')
    if request['purpose'] != 'develop':
        fail(1, 'unsupported')
    if not attempt_matches(request, request):
        fail(1, 'attempt_mismatch')
    directory = root / request['session_id']
    directory.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(directory / 'supervisor.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        fail(1, 'session_busy')
    read_fd, write_fd = os.pipe()
    supervisor_pid = os.fork()
    if supervisor_pid == 0:
        os.close(read_fd)
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        for target in (0, 1, 2):
            os.dup2(null, target)
        os.close(null)
        supervisor = Supervisor(root, request, lock_fd)
        def terminate(signum, frame):
            raise SystemExit(0)
        signal.signal(signal.SIGTERM, terminate)
        try:
            supervisor.prepare()
            os.write(write_fd, encode({'ok': True, 'result': supervisor.session}))
            os.close(write_fd)
            write_fd = None
            while not supervisor.stop:
                supervisor.pump(.1)
        except SessionError as exc:
            if write_fd is not None:
                os.write(write_fd, encode(response_error(exc.reason)))
        except (OSError, ValueError, KeyError, TypeError):
            if write_fd is not None:
                os.write(write_fd, encode(response_error('infrastructure')))
        finally:
            supervisor.cleanup()
            if write_fd is not None:
                os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    os.close(lock_fd)
    try:
        response = receive_line(read_fd, time.monotonic() + CONTROL_SECONDS + 1)
        if not response['ok']:
            os.waitpid(supervisor_pid, 0)
        return response
    except SessionError:
        os.kill(supervisor_pid, signal.SIGTERM)
        os.waitpid(supervisor_pid, 0)
        raise
    finally:
        os.close(read_fd)


def client(action, root, request):
    if trial(request):
        fail(1, 'review_trial')
    if action in RESERVED:
        fail(1, 'unsupported')
    validate_request(action, request)
    if action == 'open-session':
        return open_session(root, request)
    directory = root / request['session_id']
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(CONTROL_SECONDS)
        connection.connect(str(directory / 'control.sock'))
        connection.sendall(encode({'action': action, 'request': request}))
        response = receive_line(connection, time.monotonic() + CONTROL_SECONDS)
    if action == 'close-session' and response['ok']:
        meta = read_json(directory / 'controller.json')
        deadline = time.monotonic() + CONTROL_SECONDS
        while live_token(meta['supervisor_pid']) == meta['supervisor_token']:
            if time.monotonic() >= deadline:
                fail(70, 'infrastructure')
            time.sleep(.01)
    return response


def main():
    parser = ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('action', choices=sorted(ACTIONS | RESERVED))
    parser.add_argument('--root', required=True)
    parser.add_argument('--request', required=True)
    try:
        args = parser.parse_args()
        root = Path(args.root)
        insist(root.is_absolute())
        with open(args.request, 'rb') as stream:
            raw = stream.read(FRAME_LIMIT + 1)
        insist(len(raw) <= FRAME_LIMIT)
        request = parse_json(raw)
        response = client(args.action, root.resolve(), request)
    except SessionError as exc:
        response = response_error(exc.reason)
    except (OSError, ValueError, KeyError, TypeError):
        response = response_error('infrastructure')
    print(json.dumps(response, sort_keys=True))
    return response_code(response)


if __name__ == '__main__':
    sys.exit(main())
