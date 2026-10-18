#!/usr/bin/env python3
"""Partial Linux development-session controller (standard library only).

Exit codes: 0 admitted/successful; 1 refused; 64 usage; 70 infrastructure.
Declared identities and exclusive locks coordinate work; they do not authenticate.
The seven calls use JSON request files. Only submit-operation sends an execute
frame. Source-bound replay uses explicit submits; fresh acceptance is deferred.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import select
import selectors
import signal
import shutil
import socket
import subprocess
import sys
import tempfile
import time

FRAME_LIMIT = 65536
CONTROL_SECONDS = 5
# Separate from the cancellation-confirmation deadline. Contract 127 already
# caps an explicit timed poll at 30 seconds; a helper that is still reading
# retained history at this ceiling is infrastructure failure, not cancellation.
HELPER_RECONCILE_SECONDS = 30
CERTIFICATE_KEYS = (
    'type', 'job', 'ok', 'error', 'attempt_ok', 'attempt_value', 'contract_id',
    'step_key', 'owner', 'generation', 'lease', 'outstanding', 'request_digest',
    'input_digest',
)
ACTIONS = {'open-session', 'submit-operation', 'poll-operation',
           'transfer-session', 'close-session', 'cancel-operation', 'reattach-session'}
RESERVED = {'accept'}
TERMINAL = {'completed', 'condition_signalled', 'cancelled', 'terminated', 'rejected'}
SOURCE_KEYS = ('source_revision', 'source_manifest', 'command_refs', 'external_resources')
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


def validate_request(action, request, runtime=None):
    if action == 'open-session':
        required = {'session_id', 'requester', 'owner', 'purpose', 'run_state_path', *BINDING}
        object_keys(request, required, {'expected_generation', 'expected_lease_epoch', 'runtime'})
        insist(request.get('runtime', 'stub') in ('stub', 'sbcl'))
        principal(request['owner'])
        insist(string(request['purpose']) and string(request['run_state_path'])
               and Path(request['run_state_path']).is_absolute())
        insist(('expected_generation' in request) == ('expected_lease_epoch' in request))
    else:
        extra = {'submit-operation': {'operation_id', 'kind', 'payload', 'context', 'limits', *BINDING},
                 'poll-operation': {'operation_id'}, 'transfer-session': {'new_owner'},
                 'close-session': set(), 'cancel-operation': {'operation_id', *BINDING},
                 'reattach-session': {'expected_outstanding_operation_ref', 'handoff', *BINDING}}[action]
        object_keys(request, IDENTITY | extra, {'limits'} if action == 'poll-operation' else ())
    insist(identifier(request['session_id']))
    principal(request['requester'])
    if 'expected_generation' in request:
        generation(request['expected_generation'])
        insist(integer(request['expected_lease_epoch']))
    if 'operation_id' in request:
        insist(identifier(request['operation_id']))
    if action in ('open-session', 'submit-operation', 'cancel-operation', 'reattach-session'):
        insist(identifier(request['contract_id']) and identifier(request['step_key'])
               and integer(request['attempt'], 1))
    if action == 'transfer-session':
        principal(request['new_owner'])
    if action == 'poll-operation' and 'limits' in request:
        object_keys(request['limits'], {'timeout_seconds'})
        value = request['limits']['timeout_seconds']
        insist(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 30)
    if action == 'reattach-session':
        ref = request['expected_outstanding_operation_ref']
        insist(ref is None or string(ref))
        handoff_shape(request['handoff'])
    if action == 'submit-operation':
        operation_data(request, runtime)


def operation_data(request, runtime=None):
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
    if runtime != 'stub':
        return  # Runtime grammar is checked only after selection is known.
    expression = parse_json(payload['expression'])
    insist(type(expression) is dict and isinstance(expression.get('op'), str))
    op = expression['op']
    insist(op in ('set', 'get', 'gate'))
    object_keys(expression, {'op', 'release_path'} if op == 'gate'
                else {'op', 'name', 'value'} if op == 'set' else {'op', 'name'})
    insist(string(expression['release_path' if op == 'gate' else 'name']))


def relative_file(value):
    insist(string(value) and not Path(value).is_absolute() and '..' not in Path(value).parts
           and value == Path(value).as_posix() and value != '.')


def handoff_shape(value):
    object_keys(value, {'workspace_path', *SOURCE_KEYS})
    insist(string(value['workspace_path']) and Path(value['workspace_path']).is_absolute())
    insist(isinstance(value['source_revision'], str) and re.fullmatch(r'[0-9a-f]{40}', value['source_revision']))
    insist(type(value['source_manifest']) is list and value['source_manifest'])
    names = set()
    for entry in value['source_manifest']:
        object_keys(entry, {'path', 'sha256'})
        relative_file(entry['path'])
        insist(entry['path'] not in names)
        names.add(entry['path'])
        insist(isinstance(entry['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', entry['sha256']))
    insist(type(value['command_refs']) is list and value['command_refs'])
    for name in value['command_refs']:
        relative_file(name)
    insist(type(value['external_resources']) is list)
    for resource in value['external_resources']:
        object_keys(resource, {'ref', 'owner', 'isolation'}, {'reset_command_ref'})
        principal(resource['owner'])
        insist(string(resource['ref']) and resource['isolation'] in ('isolated', 'reset', 'shared'))
        if 'reset_command_ref' in resource:
            insist(string(resource['reset_command_ref']))


def digest_buffers(parts):
    """SHA-256 over gating buffers in this stable order.

    Each part is ``(label, buffer)``. The digest is updated, in that order,
    with the UTF-8 label, one NUL, the 8-byte big-endian length, and the
    buffer. Callers parse and hash a path's single private read, never a
    later one.
    """
    digest = hashlib.sha256()
    for label, buffer in parts:
        digest.update(label.encode())
        digest.update(b'\0')
        digest.update(len(buffer).to_bytes(8, 'big'))
        digest.update(buffer)
    return digest.hexdigest()


def governed_count(raw, step_key):
    """Return the attempts integer from this run_state buffer, or None."""
    try:
        state = parse_json(raw)
        count = state['circuit_breaker'][step_key]['attempts']
    except (SessionError, KeyError, TypeError, ValueError):
        return None
    return count if integer(count, 1) else None


def capture_source(value, runtime='stub'):
    """Validate provenance from one read of each declared workspace file.

    After the caller's run_state buffer, digest order is git HEAD stdout, then
    each source_manifest entry in request order: ls-tree stdout, the committed
    blob, and that one workspace read. Template checks use the committed blob
    already captured here.
    """
    repo = Path(value['workspace_path'])
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    deadline = time.monotonic() + CONTROL_SECONDS
    parts = []

    def git(*args):
        try:
            result = subprocess.run(['git', '-C', str(repo), *args], env=env,
                                    capture_output=True, timeout=max(.01, deadline - time.monotonic()))
        except (OSError, subprocess.TimeoutExpired):
            fail(70, 'infrastructure')
        if result.returncode:
            fail(1, 'source_mismatch')
        return result.stdout

    head = git('rev-parse', 'HEAD')
    if head.decode().strip() != value['source_revision']:
        fail(1, 'source_mismatch')
    parts.append(('git-head', head))
    contents = {}
    for entry in value['source_manifest']:
        name = entry['path']
        path = repo / name
        try:
            regular = path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(repo.resolve())
            listing = git('ls-tree', 'HEAD', '--', name) if regular else b''
            if not regular or not listing.startswith((b'100644 ', b'100755 ')):
                fail(1, 'source_mismatch')
            committed = git('show', 'HEAD:' + name)
            workspace = path.read_bytes()
            if any(hashlib.sha256(raw).hexdigest() != entry['sha256'] for raw in (committed, workspace)):
                fail(1, 'source_mismatch')
            contents[name] = committed
            parts.append((f'git-ls-tree:{name}', listing))
            parts.append((f'git-show:{name}', committed))
            parts.append((f'workspace:{name}', workspace))
        except OSError:
            fail(1, 'source_mismatch')
    for name in value['command_refs']:
        if name not in contents:
            fail(1, 'source_mismatch')
        template = parse_json(contents[name])
        object_keys(template, {'kind', 'payload', 'context', 'limits'})
        operation_data(template, runtime)
    return {key: copy.deepcopy(value[key]) for key in SOURCE_KEYS}, parts


def source_provenance(value, runtime='stub'):
    provenance, _parts = capture_source(value, runtime)
    return provenance


def failure_certificate(nonce):
    """Constant-size infrastructure result. It never carries a files array."""
    return {
        'type': 'job-result', 'job': nonce, 'ok': False, 'error': 'infrastructure',
        'attempt_ok': False, 'attempt_value': None, 'contract_id': None, 'step_key': None,
        'owner': None, 'generation': None, 'lease': None, 'outstanding': None,
        'request_digest': hashlib.sha256(b'').hexdigest(), 'input_digest': None,
    }


def validate_job_result(frame, nonce):
    """Accept only the fixed certificate. A files array or path row is rejected."""
    object_keys(frame, CERTIFICATE_KEYS)
    insist(frame['type'] == 'job-result' and frame['job'] == nonce)
    insist(type(frame['ok']) is bool and type(frame['attempt_ok']) is bool)
    insist(frame['error'] is None or string(frame['error']))
    insist(frame['attempt_value'] is None or integer(frame['attempt_value'], 1))
    insist(frame['contract_id'] is None or identifier(frame['contract_id']))
    insist(frame['step_key'] is None or identifier(frame['step_key']))
    if frame['owner'] is not None:
        principal(frame['owner'])
    if frame['generation'] is not None:
        generation(frame['generation'])
    insist(frame['lease'] is None or integer(frame['lease']))
    insist(frame['outstanding'] is None or identifier(frame['outstanding']))
    insist(isinstance(frame['request_digest'], str) and re.fullmatch(r'[0-9a-f]{64}', frame['request_digest']))
    digest_ok = isinstance(frame['input_digest'], str) and re.fullmatch(r'[0-9a-f]{64}', frame['input_digest'])
    if frame['ok']:
        insist(frame['error'] is None and digest_ok)
    else:
        insist(frame['attempt_ok'] is False and (frame['input_digest'] is None or digest_ok))


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
    return {'usage': 64, 'infrastructure': 70, 'ambiguous_state': 70}.get(response['error'], 1)


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


def lisp_frame(value):
    """Private data only: no reader evaluation, caller executable or shell."""
    if type(value) is dict:
        return '(' + ' '.join(':' + k.replace('_', '-') + ' ' + lisp_frame(v)
                              for k, v in value.items()) + ')'
    if isinstance(value, str):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if value is None:
        return 'nil'
    if type(value) is bool:
        return 't' if value else 'nil'
    if type(value) in (int, float):
        return repr(value).replace('e', 'd')
    raise ValueError('unsupported internal frame value')


def live_token(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except (OSError, IndexError):
        return None


def process_identity(pid):
    """Linux group/session identity; zombies have stopped executing."""
    path = Path('/proc') / str(pid)
    fields = (path / 'stat').read_text().split(') ', 1)[1].split()
    return {'pid': pid, 'state': fields[0], 'pgid': int(fields[2]), 'sid': int(fields[3]),
            'token': fields[19], 'uid': path.stat().st_uid}


def owned_group(pid, token):
    row = process_identity(pid)
    if (row['token'] != token or row['pgid'] != pid or row['sid'] != pid
            or row['uid'] != os.getuid() or pid == os.getpgrp()):
        fail(70, 'infrastructure')
    return dict(row, dead=False, phase=None)


def group_members(group):
    """A complete namespace observation, not leader liveness or kill success.

    The setsid-created PGID/SID remains reserved by surviving group members.
    Changed ownership, an obscured namespace, or a reused leader is uncertainty.
    Never signal after a trusted empty observation has ended this group.
    """
    if group['dead']:
        return {}
    members = {}
    end = time.monotonic() + .05
    try:
        for path in Path('/proc').iterdir():
            if not path.name.isdecimal():
                continue
            if time.monotonic() >= end:
                return None
            try:
                row = process_identity(int(path.name))
            except (FileNotFoundError, ProcessLookupError):
                continue
            if row['pgid'] != group['pgid']:
                continue
            if (row['sid'] != group['sid'] or row['uid'] != group['uid']
                    or int(row['token']) < int(group['token'])
                    or row['pid'] == group['pid'] and row['token'] != group['token']):
                return None
            if row['state'] not in ('Z', 'X'):
                members[row['pid']] = row['token']
        return members
    except (OSError, ValueError, IndexError):
        return None


def stop_group(group):
    """Advance finite TERM/KILL/death observation without waiting on a child."""
    if group['dead']:
        return True
    now = time.monotonic()
    members = group_members(group)
    if members == {}:
        group['dead'] = True
        return True
    if group['phase'] is None:
        group.update(phase='term', kill_at=now + .20, observe_end=now + 1.20)
        if members is not None:
            try:
                os.killpg(group['pgid'], signal.SIGTERM)
            except ProcessLookupError:
                pass  # Observe the boundary; ESRCH alone is not proof.
            except OSError:
                group['phase'] = 'unknown'
    elif group['phase'] == 'term' and now >= group['kill_at']:
        group['phase'] = 'kill'
        if members is not None:
            try:
                os.killpg(group['pgid'], signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                group['phase'] = 'unknown'
        else:
            group['phase'] = 'unknown'
    if now >= group['observe_end']:
        group['phase'] = 'unknown'
    return False


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
        self.waiters = {}
        self.runtime = request.get('runtime', 'stub')
        self.cancel_deadline = None
        self.quarantined = False
        self.group = None
        self.clients = {}
        self.jobs = {}
        self.version = 0
        self.verification = None
        self.bound_attempt = None
        self.bound_provenance = None
        self.closing = False
        self.close_clients = []
        self.job_cursor = 0

    def clear_transition(self):
        self.session.pop('transition', None)
        for key in tuple(self.session):
            if key.startswith('previous_'):
                del self.session[key]

    def session_write(self):
        self.version += 1
        atomic_json(self.directory / 'runtime_session.json', self.session)

    def operation_path(self, operation_id):
        return self.directory / 'operations' / f'{operation_id}.json'

    def check_handoff(self, session, metadata):
        path = self.directory / 'handoff.json'
        if metadata and metadata.get('handoff_pending'):
            fail(70, 'ambiguous_state')
        digest = (metadata or {}).get('handoff_digest')
        if path.exists() != bool(digest):
            fail(70, 'ambiguous_state')
        if digest:
            snapshot = read_json(path)
            if (hashlib.sha256(path.read_bytes()).hexdigest() != digest
                    or any(snapshot.get(k) != metadata['source_provenance'][k]
                           or session.get(k) != metadata['source_provenance'][k] for k in SOURCE_KEYS)):
                fail(70, 'ambiguous_state')

    def check_live(self):
        # A waiting certificate is not currentness. Re-read the live session
        # files even when a job result is about to be applied.
        if (read_json(self.directory / 'runtime_session.json') != self.session
                or read_json(self.directory / 'controller.json') != self.meta):
            fail(70, 'ambiguous_state')
        self.reconcile_idle(self.session, self.meta, self.outstanding)

    def reconcile_idle(self, session, metadata, pending=None):
        """Check published state without repairing it or inventing an outcome.

        Admission and completion each publish several files. A null pointer is
        necessary but not sufficient: a crash can precede its publication, or
        leave a result without the corresponding terminal operation. Generation
        reservation likewise needs matching metadata and session publications.
        """
        try:
            self.check_handoff(session, metadata)
            operation_dir = self.directory / 'operations'
            paths = list(operation_dir.glob('*.json'))
            if session is None:
                if metadata is not None or paths:
                    fail(70, 'ambiguous_state')
                return
            generation(session['generation'])
            generation(metadata['generation'])
            if (metadata['generation'] != session['generation']
                    or session.get('outstanding_operation_ref') != (str(self.operation_path(pending)) if pending else None)):
                fail(70, 'ambiguous_state')
            records = {path.name: path for path in paths if not path.name.endswith('.result.json')}
            results = {path.name: path for path in paths if path.name.endswith('.result.json')}
            known = {session['generation']['counter']: session['generation']['nonce']}
            for name, path in records.items():
                record = read_json(path)
                oid = record['operation_id']
                insist(identifier(oid))
                generation(record['generation'])
                counter, nonce = record['generation']['counter'], record['generation']['nonce']
                if (name != oid + '.json' or record['session_id'] != session['session_id']
                        or counter > session['generation']['counter']
                        or known.get(counter, nonce) != nonce):
                    fail(70, 'ambiguous_state')
                known[counter] = nonce
                status = record['status']
                if oid == pending and status in ('running', 'cancel_requested', 'unknown'):
                    if (record['generation'] != session['generation'] or record.get('executed') is not True
                            or oid + '.result.json' in results):
                        fail(70, 'ambiguous_state')
                    continue
                if oid == pending or status not in TERMINAL:
                    fail(70, 'ambiguous_state')
                if record.get('executed') is not (status != 'rejected'):
                    fail(70, 'ambiguous_state')
                result_path = results.pop(oid + '.result.json', None)
                if status in ('completed', 'cancelled'):
                    if result_path is None:
                        fail(70, 'ambiguous_state')
                    result = read_json(result_path)
                    extra = {'session_id', 'lease_epoch', 'cancellation_confirmed'} if status == 'cancelled' else set()
                    object_keys(result, {'type', 'operation_id', 'generation', 'status', 'result', 'image_consistent'} | extra)
                    generation(result['generation'])
                    if (result['type'] != 'result' or result['operation_id'] != oid
                            or result['generation'] != record['generation']
                            or result['status'] != status or type(result['image_consistent']) is not bool
                            or result['image_consistent'] != record.get('image_consistent')
                            or status == 'completed' and result['image_consistent'] is not True):
                        fail(70, 'ambiguous_state')
                    if status == 'cancelled' and (result['session_id'] != record['session_id']
                            or type(result['lease_epoch']) is not int or result['lease_epoch'] != record['lease_epoch']
                            or result['cancellation_confirmed'] is not True
                            or record.get('cancellation_confirmed') is not True or result['result'] is not None):
                        fail(70, 'ambiguous_state')
                elif result_path is not None:
                    fail(70, 'ambiguous_state')
            if results or pending and pending + '.json' not in records:
                fail(70, 'ambiguous_state')
        except (OSError, KeyError, TypeError, ValueError, SessionError):
            fail(70, 'ambiguous_state')

    def prepare(self):
        request = self.request
        session_path = self.directory / 'runtime_session.json'
        previous = read_json(session_path) if session_path.exists() else None
        meta_path = self.directory / 'controller.json'
        previous_meta = read_json(meta_path) if meta_path.exists() else None
        if previous:
            if previous_meta and previous_meta.get('runtime', 'stub') != self.runtime:
                fail(1, 'runtime_mismatch')
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
        self.reconcile_idle(previous, previous_meta)
        if not attempt_matches(request, request):
            fail(1, 'attempt_mismatch')
        counter = previous['generation']['counter'] + 1 if previous else 1
        self.session = {'session_id': request['session_id'], 'purpose': 'develop',
                        'owner': request['owner'], 'lease_epoch': previous['lease_epoch'] if previous else 0,
                        'generation': {'counter': counter, 'nonce': secrets.token_hex(16)},
                        'outstanding_operation_ref': None}
        self.meta = {key: request[key] for key in (*BINDING, 'run_state_path')}
        self.meta.update(runtime=self.runtime, ended=False, supervisor_pid=os.getpid(), supervisor_pgid=os.getpgrp(),
                         supervisor_token=live_token(os.getpid()), child_pid=None,
                         generation=self.session['generation'],
                         previous_generation=previous['generation'] if previous else None)
        if previous_meta and previous_meta.get('source_provenance'):
            self.meta.update(source_provenance=previous_meta['source_provenance'],
                             handoff_digest=previous_meta['handoff_digest'])
            self.session.update(previous_meta['source_provenance'], source_state='committed')
        (self.directory / 'operations').mkdir(exist_ok=True)
        # Reserve the incarnation durably before any child exists.
        atomic_json(meta_path, self.meta)
        self.session_write()
        read_fd, write_fd = os.pipe()
        def child_fd3():
            os.dup2(write_fd, 3)
        stub = Path(__file__).resolve().parent / 'fixtures/runtime_session/stub_runtime.py'
        executable = shutil.which('sbcl') if self.runtime == 'sbcl' else None
        if self.runtime == 'sbcl' and not executable:
            fail(70, 'infrastructure')
        command = ([executable, '--noinform', '--no-sysinit', '--no-userinit', '--disable-debugger',
                    '--script', str(Path(__file__).resolve().with_name('sbcl_session_loop.lisp'))]
                   if self.runtime == 'sbcl' else [sys.executable, str(stub)])
        try:
            self.child = subprocess.Popen(
                command, start_new_session=self.runtime == 'sbcl', stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, pass_fds=tuple({write_fd, 3}), preexec_fn=child_fd3,
                cwd=self.root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        finally:
            os.close(write_fd)
        self.meta['child_pid'] = self.child.pid
        self.meta['child_token'] = live_token(self.child.pid)
        if self.runtime == 'sbcl':
            self.group = owned_group(self.child.pid, self.meta['child_token'])
            self.meta['runtime_group'] = {k: self.group[k] for k in ('pid', 'token', 'pgid', 'sid', 'uid')}
            os.set_blocking(self.child.stdin.fileno(), False)
            self.outbound = bytearray()
        atomic_json(meta_path, self.meta)
        for fd, channel in ((read_fd, 'protocol'), (self.child.stdout.fileno(), 'stdout'),
                            (self.child.stderr.fileno(), 'stderr')):
            os.set_blocking(fd, False)
            self.selector.register(fd, selectors.EVENT_READ, channel)
        self.send({'type': 'init', 'generation': self.session['generation'],
                   **({'directory': str(self.directory) + '/'} if self.runtime == 'sbcl' else {})})
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
        if self.runtime == 'sbcl':
            self.server.setblocking(False)
        self.selector.register(self.server, selectors.EVENT_READ, 'server')

    def send(self, value):
        raw = ((lisp_frame(value) + '\n').encode() if self.runtime == 'sbcl' else encode(value))
        insist(len(raw) <= FRAME_LIMIT)
        if self.runtime == 'sbcl':
            if len(self.outbound) + len(raw) > FRAME_LIMIT * 2:
                fail(70, 'infrastructure')
            self.outbound.extend(raw)
            try:
                self.selector.modify(self.child.stdin.fileno(), selectors.EVENT_WRITE, 'runtime-write')
            except KeyError:
                self.selector.register(self.child.stdin.fileno(), selectors.EVENT_WRITE, 'runtime-write')
        else:
            self.child.stdin.write(raw)
            self.child.stdin.flush()

    def log(self, channel, data):
        if self.runtime == 'sbcl':
            # The worker's bounded stream already shares its budget with results
            # and diagnostics. Startup output has no project attribution.
            if not self.outstanding:
                return
            path = self.directory / f'child.{channel}.log'
            with path.open('ab') as stream:
                stream.write(data[:self.render_remaining])
            self.render_remaining = max(0, self.render_remaining - len(data))
            return
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
        self.version += 1
        self.broken = True
        self.protocol.clear()
        if self.outstanding:
            record = read_json(self.operation_path(self.outstanding))
            record.update(status='unknown', image_consistent=False)
            atomic_json(self.operation_path(self.outstanding), record)
            if self.runtime == 'sbcl' and self.cancel_deadline is None:
                self.cancel_deadline = time.monotonic() + min(1.0, record['limits'].get('timeout_seconds', 1.0))

    def frame(self, data):
        if self.runtime == 'sbcl' and self.ready:
            self.sbcl_result(data)
            return
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
            insist(type(value) is dict)
            cancelled = value.get('status') == 'cancelled'
            extra = {'session_id', 'lease_epoch', 'cancellation_confirmed'} if cancelled else set()
            object_keys(value, {'type', 'operation_id', 'generation', 'status', 'result', 'image_consistent'} | extra)
            generation(value['generation'])
            insist(value['type'] == 'result' and value['operation_id'] == self.outstanding
                   and self.outstanding is not None and value['generation'] == self.session['generation']
                   and value['status'] in ('completed', 'cancelled') and value['image_consistent'] is True)
            path = self.operation_path(self.outstanding)
            record = read_json(path)
            if cancelled:
                insist(record['status'] == 'cancel_requested' and value['cancellation_confirmed'] is True
                       and value['session_id'] == record['session_id']
                       and type(value['lease_epoch']) is int and value['lease_epoch'] == record['lease_epoch']
                       and value['result'] is None)
            atomic_json(path.with_suffix('.result.json'), value)
            record.update(status=value['status'], image_consistent=True)
            if cancelled:
                record['cancellation_confirmed'] = True
            if 'wait_outcome' in record:
                record['wait_outcome'] = 'completed_wait'
            atomic_json(path, record)
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.clear_transition()
            self.session_write()
        except (SessionError, ValueError, KeyError, TypeError):
            self.protocol_fault()

    def sbcl_result(self, data):
        if self.broken:
            return
        try:
            value = parse_json(data)
            object_keys(value, {'type', 'session_id', 'operation_id', 'generation', 'lease_epoch',
                                'status', 'result', 'image_consistent', 'cancellation_confirmed', 'diagnostic'})
            generation(value['generation'])
            insist(value['type'] == 'result' and self.outstanding is not None
                   and value['operation_id'] == self.outstanding
                   and value['session_id'] == self.session['session_id']
                   and value['generation'] == self.session['generation']
                   and type(value['lease_epoch']) is int and value['lease_epoch'] == self.session['lease_epoch']
                   and type(value['image_consistent']) is bool
                   and type(value['cancellation_confirmed']) is bool
                   and value['status'] in ('completed', 'cancelled', 'condition_signalled'))
            # One bounded read per stream; never drain an unbounded producer.
            for stream, channel in ((self.child.stdout, 'stdout'), (self.child.stderr, 'stderr')):
                try:
                    chunk = os.read(stream.fileno(), FRAME_LIMIT + 1)
                except BlockingIOError:
                    continue
                if chunk:
                    self.log(channel, chunk)
            path = self.operation_path(self.outstanding)
            record = read_json(path)
            status = value['status']
            insist(status != 'completed' or value['image_consistent'] is True)
            insist(status != 'cancelled' or (record['status'] == 'cancel_requested'
                   and value['cancellation_confirmed'] is True and value['result'] is None))
            insist(status == 'cancelled' or value['cancellation_confirmed'] is False)
            if status == 'condition_signalled':
                raw = value['diagnostic']
                insist(isinstance(raw, str) and 0 < len(raw.encode()) <= self.render_remaining + 1)
                parse_json(raw)
                directory = self.directory / 'diagnostics'
                directory.mkdir(mode=0o700, exist_ok=True)
                diagnostic = directory / (self.outstanding + '.json')
                insist(not diagnostic.exists() and not diagnostic.is_symlink())
                with diagnostic.open('xb') as stream:
                    stream.write(raw.encode())
                record.update(condition_ref=str(diagnostic), condition_capture='before_unwind')
            else:
                insist(value['diagnostic'] is None)
                result = {k: value[k] for k in ('type', 'operation_id', 'generation', 'status',
                                               'result', 'image_consistent')}
                if status == 'cancelled':
                    result.update({k: value[k] for k in ('session_id', 'lease_epoch', 'cancellation_confirmed')})
                atomic_json(path.with_suffix('.result.json'), result)
            record.update(status=status, image_consistent=value['image_consistent'])
            if status == 'cancelled':
                record['cancellation_confirmed'] = True
            if 'wait_outcome' in record:
                record['wait_outcome'] = 'completed_wait'
            atomic_json(path, record)
            self.quarantined |= not value['image_consistent']
            self.cancel_deadline = None
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.clear_transition()
            self.session_write()
        except (SessionError, ValueError, KeyError, TypeError, OSError):
            self.protocol_fault()

    def end_generation(self):
        self.broken = True
        self.quarantined = True
        self.cancel_deadline = None
        if self.group and self.group['phase'] is None:
            stop_group(self.group)
        if not self.group or not self.group['dead']:
            return
        self.child.poll()  # Reap the leader separately from group observation.
        if self.outstanding:
            path = self.operation_path(self.outstanding)
            record = read_json(path)
            record.update(status='terminated', image_consistent=False)
            if 'wait_outcome' in record:
                record['wait_outcome'] = 'completed_wait'
            atomic_json(path, record)
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.clear_transition()
            self.session_write()
        if not self.meta.get('ended'):
            self.meta['ended'] = True
            atomic_json(self.directory / 'controller.json', self.meta)
            self.version += 1

    def pump(self, seconds):
        if self.runtime == 'sbcl':
            self.tick()
            seconds = min(seconds, .01)
        if self.cancel_deadline is not None:
            seconds = min(seconds, max(0, self.cancel_deadline - time.monotonic()))
        for key, events in self.selector.select(seconds):
            if self.runtime == 'sbcl':
                self.tick()
                if isinstance(key.data, tuple):
                    kind, value = key.data
                    if kind == 'client':
                        self.client_event(value, events)
                    else:
                        self.job_event(value)
                    continue
                if key.data == 'runtime-write':
                    try:
                        count = os.write(key.fd, self.outbound[:FRAME_LIMIT])
                        del self.outbound[:count]
                        if not self.outbound:
                            self.selector.unregister(key.fd)
                    except BlockingIOError:
                        pass
                    except OSError:
                        self.selector.unregister(key.fd)
                        self.protocol_fault()
                    continue
            if key.data == 'waiter':
                self.finish_waiter(key.fileobj, None)
                continue
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
        if self.runtime == 'sbcl' and self.cancel_deadline is not None and time.monotonic() >= self.cancel_deadline:
            self.end_generation()
        if self.runtime == 'sbcl':
            self.tick()
        for connection, (request, end) in list(self.waiters.items()):
            record = read_json(self.operation_path(request['operation_id']))
            if record['status'] in TERMINAL or record['status'] == 'unknown' or time.monotonic() >= end:
                self.finish_waiter(connection, self.poll_response(request, expired=True))

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
        if action == 'open-session' and self.runtime == 'sbcl' and self.meta.get('ended'):
            validate_request(action, request)
            if (not lifecycle(request['requester']) or request['owner'] != self.session['owner']
                    or request.get('expected_generation') != self.session['generation']
                    or request.get('expected_lease_epoch') != self.session['lease_epoch']
                    or request.get('runtime', 'stub') != self.runtime
                    or not self.verified_attempt(request)):
                fail(1, 'stale_generation')
            if self.jobs:
                fail(70, 'infrastructure')
            self.closing = True
            return {'ok': True, 'result': {'closed': True}}
        if action not in ACTIONS or action == 'open-session':
            fail(1, 'unsupported')
        validate_request(action, request, self.runtime)
        if request['session_id'] != self.session['session_id']:
            fail(1, 'foreign_owner')
        if action == 'submit-operation':
            path = self.operation_path(request['operation_id'])
            if path.exists() or path.with_suffix('.result.json').exists():
                return response_error('conflict')
            reason = self.identity_reason(request)
            if not reason and not permitted_owner(request['requester']):
                reason = 'foreign_owner'
            if not reason and not self.verified_attempt(request):
                reason = 'attempt_mismatch'
            if not reason and self.outstanding:
                reason = 'session_busy'
            if not reason and self.quarantined:
                reason = 'inconsistent_image'
            if not reason and self.broken:
                fail(70, 'infrastructure')
            if not reason:
                self.check_live()
            expression = parse_json(request['payload']['expression']) if self.runtime == 'stub' else {}
            if expression.get('op') == 'gate':
                release = Path(expression['release_path'])
                insist(release.is_absolute() and release.resolve().is_relative_to(self.root))
            record = self.operation_record(request, reason)
            atomic_json(path, record)
            if reason:
                return response_error(reason, record)
            self.outstanding = request['operation_id']
            self.session['outstanding_operation_ref'] = str(path)
            self.clear_transition()
            self.session_write()
            try:
                self.render_budget = min(16384, request['limits'].get('output_bytes', 16384))
                self.render_remaining = max(0, self.render_budget - 1)
                self.send({'type': 'execute', 'request': request, 'generation': self.session['generation']})
            except (BrokenPipeError, OSError):
                self.protocol_fault()
                fail(70, 'infrastructure')
            return {'ok': True, 'result': record}
        reason = self.identity_reason(request, permit_orchestrator=action not in ('cancel-operation', 'reattach-session'))
        if reason:
            fail(1, reason)
        if action == 'poll-operation':
            return self.poll_response(request)
        if action in ('cancel-operation', 'reattach-session'):
            if not permitted_owner(request['requester']):
                fail(1, 'foreign_owner')
            if not self.verified_attempt(request):
                fail(1, 'attempt_mismatch')
            if action == 'reattach-session':
                self.check_live()
                return self.reattach(request)
            # Cancel publishes one record and one frame. It does not glob history.
            path = self.operation_path(request['operation_id'])
            if not path.is_file():
                fail(1, 'unknown_operation')
            record = read_json(path)
            if record['status'] in TERMINAL or record['status'] == 'cancel_requested':
                return {'ok': True, 'result': record}
            if self.broken or record['status'] == 'unknown':
                return response_error('infrastructure', record)
            if request['operation_id'] != self.outstanding:
                fail(70, 'ambiguous_state')
            record.update(status='cancel_requested', cancellation_confirmed=False)
            atomic_json(path, record)
            self.version += 1
            if self.runtime == 'sbcl':
                self.cancel_deadline = time.monotonic() + min(1.0, record['limits'].get('timeout_seconds', 1.0))
            try:
                self.send({'type': 'cancel', 'session_id': record['session_id'],
                           'operation_id': self.outstanding, 'generation': record['generation'],
                           'lease_epoch': record['lease_epoch']})
            except (BrokenPipeError, OSError):
                self.protocol_fault()
            return {'ok': True, 'result': record}
        if not lifecycle(request['requester'], self.session['owner']):
            fail(1, 'foreign_owner')
        if action == 'transfer-session':
            if not permitted_owner(request['new_owner']):
                fail(1, 'foreign_owner')
            if self.outstanding:
                fail(1, 'session_busy')
            if request['new_owner'] == self.session['owner']:
                fail(1, 'same_owner')
            self.clear_transition()
            self.session.update(transition='transfer', previous_owner=self.session['owner'],
                                previous_lease_epoch=self.session['lease_epoch'],
                                owner=request['new_owner'], lease_epoch=self.session['lease_epoch'] + 1)
            self.session_write()
            return {'ok': True, 'result': self.session}
        if self.runtime == 'sbcl':
            self.closing = True
            self.version += 1
            self.close_clients.append(self.current_client)
            self.clients[self.current_client]['phase'] = 'close'
            for job in self.jobs.values():
                job['failure'] = 'infrastructure'
                job['abandoned'] = True
            self.end_generation()
            return None
        dead = self.stop_child()
        if not dead:
            self.protocol_fault()
            fail(70, 'infrastructure')
        if self.outstanding:
            record = read_json(self.operation_path(self.outstanding))
            record.update(status='terminated', image_consistent=False)
            if 'wait_outcome' in record:
                record['wait_outcome'] = 'completed_wait'
            atomic_json(self.operation_path(self.outstanding), record)
            self.outstanding = None
            self.session['outstanding_operation_ref'] = None
            self.clear_transition()
            self.session_write()
        self.stop = True
        return {'ok': True, 'result': {'closed': True, 'session_id': self.session['session_id']}}

    def reattach(self, request):
        if self.broken:
            fail(70, 'infrastructure')
        if request['expected_outstanding_operation_ref'] != self.session.get('outstanding_operation_ref'):
            fail(1, 'continuity_mismatch')
        if self.runtime == 'sbcl':
            provenance = self.bound_provenance
            if provenance is None:
                fail(70, 'infrastructure')
        else:
            provenance = source_provenance(request['handoff'], self.runtime)
        if self.meta.get('source_provenance', provenance) != provenance:
            fail(1, 'source_mismatch')
        snapshot = {k: copy.deepcopy(self.session[k]) for k in
                    ('session_id', 'purpose', 'owner', 'generation', 'lease_epoch', 'outstanding_operation_ref')}
        snapshot.update(provenance, source_state='committed', transition='handoff')
        current = dict(snapshot, transition='reattach')
        for key in ('owner', 'generation', 'lease_epoch', 'outstanding_operation_ref'):
            current['previous_' + key] = copy.deepcopy(snapshot[key])
        self.meta['handoff_pending'] = True
        atomic_json(self.directory / 'controller.json', self.meta)
        atomic_json(self.directory / 'handoff.json', snapshot)
        atomic_json(self.directory / 'runtime_session.json', current)
        self.meta.update(source_provenance=provenance, handoff_digest=hashlib.sha256(encode(snapshot)).hexdigest())
        self.meta.pop('handoff_pending')
        atomic_json(self.directory / 'controller.json', self.meta)
        self.session = current
        return {'ok': True, 'result': current}

    def poll_response(self, request, expired=False):
        path = self.operation_path(request['operation_id'])
        if not path.is_file():
            fail(1, 'unknown_operation')
        record = read_json(path)
        if 'limits' in request and (expired or record['status'] in TERMINAL):
            record['wait_outcome'] = 'completed_wait' if record['status'] in TERMINAL else 'stopped_waiting'
            atomic_json(path, record)
        return (response_error('infrastructure', record) if record['status'] == 'unknown'
                else {'ok': True, 'result': record})

    def finish_waiter(self, connection, response):
        if connection in self.waiters:
            del self.waiters[connection]
            self.selector.unregister(connection)
        try:
            if response is not None:
                connection.sendall(encode(response))
        except OSError:
            pass  # Disconnect does not cancel admitted work.
        finally:
            connection.close()

    def serve(self):
        if self.runtime == 'sbcl':
            self.accept_client()
            return
        connection, _ = self.server.accept()
        connection.settimeout(CONTROL_SECONDS)
        try:
            envelope = receive_line(connection, time.monotonic() + CONTROL_SECONDS)
            object_keys(envelope, {'action', 'request'})
            action, request = envelope['action'], envelope['request']
            insist(isinstance(action, str))
            response = self.dispatch(action, request)
            if action == 'poll-operation' and 'limits' in request:
                seconds = request['limits']['timeout_seconds']
                if seconds and response['ok'] and response['result']['status'] not in TERMINAL:
                    self.waiters[connection] = (request, time.monotonic() + seconds)
                    self.selector.register(connection, selectors.EVENT_READ, 'waiter')
                    return
                response = self.poll_response(request, expired=True)
        except SessionError as exc:
            response = response_error(exc.reason)
        except (OSError, KeyError, TypeError):
            response = response_error('infrastructure')
        self.finish_waiter(connection, response)

    def verified_attempt(self, request):
        """Refuse a changed governed attempt before execution.

        Without a certificate, read run_state once through attempt_matches.
        With a certificate, use only the integer parsed from the pre-apply
        buffer. The cached attempt_ok flag is never applied.
        """
        if self.verification is None:
            return attempt_matches(self.meta, request)
        count = self.bound_attempt
        certificate = self.verification
        if not integer(count, 1) or count != certificate.get('attempt_value'):
            return False
        if count != self.meta.get('attempt') or count != request.get('attempt'):
            return False
        if any(request.get(key) != self.meta.get(key) for key in BINDING):
            return False
        return (certificate.get('contract_id') == self.meta.get('contract_id')
                and certificate.get('step_key') == self.meta.get('step_key'))

    def accept_client(self):
        try:
            connection, _ = self.server.accept()
        except BlockingIOError:
            return
        connection.setblocking(False)
        if len(self.clients) >= 32 or self.closing:
            connection.close()
            return
        self.clients[connection] = {'phase': 'input', 'input': bytearray(),
                                    'end': time.monotonic() + CONTROL_SECONDS}
        self.selector.register(connection, selectors.EVENT_READ, ('client', connection))

    def drop_client(self, connection):
        self.clients.pop(connection, None)
        try:
            self.selector.unregister(connection)
        except (KeyError, ValueError):
            pass
        connection.close()

    def reply(self, connection, response):
        if connection not in self.clients:
            return
        self.clients[connection].update(phase='reply', output=bytearray(encode(response)),
                                        end=time.monotonic() + CONTROL_SECONDS)
        self.selector.modify(connection, selectors.EVENT_WRITE, ('client', connection))

    def client_event(self, connection, events):
        state = self.clients.get(connection)
        if state is None:
            return
        try:
            if state['phase'] == 'reply':
                count = connection.send(state['output'][:FRAME_LIMIT])
                del state['output'][:count]
                if not state['output']:
                    self.drop_client(connection)
                return
            data = connection.recv(FRAME_LIMIT + 1)
            if not data:
                self.drop_client(connection)
                return  # A disconnect abandons a wait, never runtime execution.
            if state['phase'] != 'input':
                self.reply(connection, response_error('usage'))
                return
            state['input'].extend(data)
            insist(len(state['input']) <= FRAME_LIMIT)
            if b'\n' not in state['input']:
                return
            insist(state['input'].count(b'\n') == 1 and state['input'].endswith(b'\n'))
            envelope = parse_json(state['input'])
            object_keys(envelope, {'action', 'request'})
            action, request = envelope['action'], envelope['request']
            insist(isinstance(action, str))
            if action not in ACTIONS:
                fail(1, 'unsupported')
            validate_request(action, request, self.runtime)
            state.update(action=action, request=request)
            if action == 'submit-operation':
                path = self.operation_path(request['operation_id'])
                if path.exists() or path.with_suffix('.result.json').exists():
                    self.reply(connection, response_error('conflict'))
                    return
            if action in ('poll-operation', 'cancel-operation', 'close-session'):
                # Poll, cancel, and close stay on the supervisor. Cancel and
                # close do not start a helper and do not glob operations/*.json.
                self.apply_request(connection, None)
            else:
                self.start_job(connection)
        except BlockingIOError:
            pass
        except SessionError as exc:
            self.reply(connection, response_error(exc.reason))
        except (OSError, KeyError, ValueError, TypeError):
            self.reply(connection, response_error('infrastructure'))

    def apply_request(self, connection, verification):
        state = self.clients.get(connection)
        if state is None:
            return
        self.verification = verification
        self.current_client = connection
        try:
            action, request = state['action'], state['request']
            response = self.dispatch(action, request)
            if response is None:
                return
            if action == 'poll-operation' and 'limits' in request:
                seconds = request['limits']['timeout_seconds']
                if seconds and response['ok'] and response['result']['status'] not in TERMINAL:
                    state.update(phase='poll', end=time.monotonic() + seconds)
                    return
                response = self.poll_response(request, expired=True)
            self.reply(connection, response)
        except SessionError as exc:
            self.reply(connection, response_error(exc.reason))
        except (OSError, KeyError, ValueError, TypeError):
            self.reply(connection, response_error('infrastructure'))
        finally:
            self.verification = None
            self.bound_attempt = None
            self.bound_provenance = None
            self.current_client = None

    def buffer_attempt_ok(self, attempt_value, request, action):
        if not integer(attempt_value, 1) or attempt_value != self.meta.get('attempt'):
            return False
        if action == 'transfer-session':
            return True
        return all(request.get(key) == self.meta.get(key) for key in BINDING)

    def capture_gating(self, action, request):
        """Read each gating input once. The attempt integer comes from that buffer.

        Digest order is run_state, then reattach source parts only when the
        governed attempt matches and live identity is acceptable. That keeps
        attempt refusal ahead of source refusal without a second run_state read.
        """
        raw = Path(self.meta['run_state_path']).read_bytes()
        parts = [('run_state', raw)]
        attempt_value = governed_count(raw, self.meta['step_key'])
        attempt_ok = self.buffer_attempt_ok(attempt_value, request, action)
        provenance = None
        if action == 'reattach-session' and attempt_ok and self.identity_reason(request) is None:
            provenance, source_parts = capture_source(request['handoff'], self.runtime)
            parts.extend(source_parts)
        return parts, attempt_value, attempt_ok, provenance

    def accept_certificate(self, version, action, request, certificate):
        """Re-read gating inputs immediately before apply and refuse on mismatch.

        Supervisor version is necessary but not sufficient. An external edit
        that leaves the version unchanged is caught by recomputing input_digest
        from the same path order. Transfer has no request attempt; its governed
        meta attempt must match the re-read integer. Other actions keep their
        existing refusal reason inside dispatch.
        """
        if version != self.version:
            return 'ambiguous_state'
        if hashlib.sha256(encode(request)).hexdigest() != certificate['request_digest']:
            return 'ambiguous_state'
        try:
            parts, attempt_value, _attempt_ok, provenance = self.capture_gating(action, request)
        except SessionError as exc:
            return exc.reason
        except (OSError, KeyError, TypeError, ValueError):
            return 'infrastructure'
        if digest_buffers(parts) != certificate['input_digest'] or attempt_value != certificate['attempt_value']:
            return 'ambiguous_state'
        if (certificate['contract_id'] != self.meta.get('contract_id')
                or certificate['step_key'] != self.meta.get('step_key')
                or certificate['owner'] != self.session['owner']
                or certificate['generation'] != self.session['generation']
                or certificate['lease'] != self.session['lease_epoch']
                or certificate['outstanding'] != self.outstanding):
            return 'ambiguous_state'
        if action == 'transfer-session' and not self.buffer_attempt_ok(attempt_value, request, action):
            return 'attempt_mismatch'
        self.bound_attempt = attempt_value
        self.bound_provenance = provenance
        return None

    def start_job(self, connection):
        state = self.clients.get(connection)
        if state is None:
            return
        if self.closing or any(job.get('uncertain') for job in self.jobs.values()):
            self.reply(connection, response_error('infrastructure'))
            return
        request, action = state['request'], state['action']
        nonce = secrets.token_hex(16)
        result_read, result_write = os.pipe()
        ack_read, ack_write = os.pipe()
        version = self.version
        pid = os.fork()
        if pid == 0:
            # Fork references are kernel ownership: explicitly remove EVERY
            # inherited lock/listener/client/runtime/protocol/selector/job FD.
            # Only this job's result writer, start-authorization reader and
            # deliberately rebound standard streams survive before work.
            try:
                os.setsid()
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                null = os.open(os.devnull, os.O_RDWR)
                for target in (0, 1, 2):
                    os.dup2(null, target)
                keep = {0, 1, 2, result_write, ack_read}
                for name in os.listdir('/proc/self/fd'):
                    fd = int(name)
                    if fd not in keep:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                os.set_inheritable(result_write, False)
                os.set_inheritable(ack_read, False)
                def send(value):
                    raw = encode(value)
                    if len(raw) > FRAME_LIMIT:
                        raw = encode(failure_certificate(nonce))
                    while raw:
                        raw = raw[os.write(result_write, raw):]
                send({'type': 'job-ready', 'job': nonce, 'pid': os.getpid(),
                      'token': live_token(os.getpid())})
                authorization = receive_line(ack_read, time.monotonic() + CONTROL_SECONDS)
                if authorization != {'job': nonce}:
                    os._exit(71)
                result = {
                    'type': 'job-result', 'job': nonce, 'ok': True, 'error': None,
                    'attempt_ok': False, 'attempt_value': None,
                    'contract_id': self.meta.get('contract_id'), 'step_key': self.meta.get('step_key'),
                    'owner': copy.deepcopy(self.session['owner']),
                    'generation': copy.deepcopy(self.session['generation']),
                    'lease': self.session['lease_epoch'], 'outstanding': self.outstanding,
                    'request_digest': hashlib.sha256(encode(request)).hexdigest(),
                    'input_digest': None,
                }
                try:
                    # One run_state buffer feeds attempt_value and input_digest.
                    # Reconciliation may read retained operation files and must
                    # not put them, or any per-path row, in this result.
                    parts, attempt_value, attempt_ok, _provenance = self.capture_gating(action, request)
                    self.check_live()
                    result.update(attempt_ok=attempt_ok, attempt_value=attempt_value,
                                  input_digest=digest_buffers(parts))
                except SessionError as exc:
                    result.update(ok=False, error=exc.reason, attempt_ok=False)
                except (OSError, KeyError, TypeError, ValueError):
                    result.update(ok=False, error='infrastructure', attempt_ok=False)
                send(result)
            finally:
                os._exit(0)
        os.close(result_write)
        os.close(ack_read)
        os.set_blocking(result_read, False)
        os.set_blocking(ack_write, False)
        self.jobs[nonce] = {'pid': pid, 'token': live_token(pid), 'group': None,
                            'reader': result_read, 'ack': ack_write, 'buffer': bytearray(),
                            'end': time.monotonic() + HELPER_RECONCILE_SECONDS, 'version': version,
                            'connection': connection, 'result': None, 'failure': None,
                            'eof': False, 'reaped': False}
        state.update(phase='job', end=time.monotonic() + HELPER_RECONCILE_SECONDS)
        self.selector.register(result_read, selectors.EVENT_READ, ('job', nonce))

    def job_event(self, nonce):
        job = self.jobs.get(nonce)
        if job is None:
            return
        try:
            part = os.read(job['reader'], FRAME_LIMIT + 1)
            if not part:
                self.selector.unregister(job['reader'])
                job['eof'] = True
                if job['result'] is None:
                    job['failure'] = 'infrastructure'
                return
            job['buffer'].extend(part)
            if len(job['buffer']) > FRAME_LIMIT * 2:
                fail(70, 'infrastructure')
            for _ in range(2):
                if b'\n' not in job['buffer']:
                    break
                end = job['buffer'].index(b'\n') + 1
                if end > FRAME_LIMIT:
                    fail(70, 'infrastructure')
                frame = parse_json(bytes(job['buffer'][:end]))
                del job['buffer'][:end]
                if frame.get('job') != nonce:
                    fail(70, 'infrastructure')
                if frame.get('type') == 'job-ready' and job['group'] is None:
                    object_keys(frame, {'type', 'job', 'pid', 'token'})
                    insist(frame['pid'] == job['pid'] and frame['token'] == job['token'])
                    job['group'] = owned_group(job['pid'], job['token'])
                    os.write(job['ack'], encode({'job': nonce}))
                    os.close(job['ack'])
                    job['ack'] = None
                elif frame.get('type') == 'job-result' and job['group'] and job['result'] is None:
                    validate_job_result(frame, nonce)
                    job['result'] = frame
                else:
                    fail(70, 'infrastructure')
        except (SessionError, OSError, ValueError, KeyError, TypeError):
            job['failure'] = 'infrastructure'

    def tick_jobs(self):
        # A bounded round-robin batch prevents many pending provenance jobs
        # from occupying an entire cancellation/TERM-to-KILL interval.
        keys = list(self.jobs)
        if not keys:
            return
        self.job_cursor %= len(keys)
        nonce = keys[self.job_cursor]
        self.job_cursor += 1
        for nonce, job in [(nonce, self.jobs[nonce])]:
            now = time.monotonic()
            if now >= job['end'] or job.get('abandoned'):
                job['failure'] = 'infrastructure'
            group = job['group']
            if group is None:
                # No descendants can start before the isolated handshake is
                # authorized. An unacknowledged child can only be stopped by
                # its retained fork PID/start token, never an unproven group.
                if job['failure'] and live_token(job['pid']) == job['token']:
                    try:
                        os.kill(job['pid'], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                dead = live_token(job['pid']) is None
            else:
                members = group_members(group)
                if members == {}:
                    group['dead'] = True
                elif job['failure'] or job['eof'] or group['phase'] is not None:
                    stop_group(group)
                dead = group['dead']
                if group['phase'] == 'unknown' and not dead:
                    job['uncertain'] = True
            if not dead:
                continue
            if not job['reaped']:
                try:
                    reaped, _ = os.waitpid(job['pid'], os.WNOHANG)
                    job['reaped'] = bool(reaped)
                except ChildProcessError:
                    job['reaped'] = True
            if not job['reaped'] or not (job['eof'] or job['failure']):
                continue
            result = job['result']
            if result and result['ok'] and not job['failure']:
                # Expiry and abandonment already set infrastructure above and
                # must not apply the certificate or report cancellation.
                state = self.clients.get(job['connection'])
                if state is None:
                    job['failure'] = 'infrastructure'
                else:
                    reason = self.accept_certificate(job['version'], state['action'], state['request'], result)
                    if reason:
                        job['failure'] = reason
            connection = job['connection']
            try:
                self.selector.unregister(job['reader'])
            except KeyError:
                pass
            os.close(job['reader'])
            if job['ack'] is not None:
                os.close(job['ack'])
            del self.jobs[nonce]
            if connection not in self.clients:
                continue
            if job['failure']:
                self.reply(connection, response_error(job['failure']))
            elif result and not result['ok']:
                self.reply(connection, response_error(result['error']))
            elif result:
                self.apply_request(connection, result)
            else:
                self.reply(connection, response_error('infrastructure'))

    def tick(self):
        now = time.monotonic()
        if self.cancel_deadline is not None and now >= self.cancel_deadline:
            self.end_generation()
        if self.group and self.group['phase'] is not None:
            stop_group(self.group)
            self.end_generation()
        self.tick_jobs()
        for connection, state in list(self.clients.items()):
            if state['phase'] == 'poll':
                record = read_json(self.operation_path(state['request']['operation_id']))
                if record['status'] in TERMINAL or record['status'] == 'unknown' or now >= state['end']:
                    self.reply(connection, self.poll_response(state['request'], expired=True))
            elif state['phase'] not in ('job', 'close') and now >= state['end']:
                if state['phase'] == 'input':
                    self.reply(connection, response_error('infrastructure'))
                else:
                    self.drop_client(connection)
        if self.closing and self.group and self.group['dead'] and not self.jobs:
            for connection in self.close_clients:
                self.reply(connection, {'ok': True, 'result': {'closed': True, 'session_id': self.session['session_id']}})
            self.close_clients.clear()
            # Discard unrelated partial clients; they cannot retain a closed
            # session, its flock, or an ended generation's supervisor.
            for connection, state in list(self.clients.items()):
                if state['phase'] != 'reply':
                    self.drop_client(connection)
            if not self.clients:
                self.stop = True

    def stop_child(self):
        if self.runtime == 'sbcl':
            if not self.group:
                return self.child is None or self.child.poll() is not None
            end = time.monotonic() + 1.3
            while time.monotonic() < end:
                if stop_group(self.group):
                    self.child.poll()
                    return True
                time.sleep(.005)
            return False
        if self.child and self.child.poll() is None:
            self.child.terminate()
            try:
                self.child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.child.kill()
                self.child.wait(timeout=2)
        return True

    def cleanup(self):
        if self.runtime == 'sbcl':
            for job in self.jobs.values():
                job['failure'] = 'infrastructure'
                job['abandoned'] = True
            end = time.monotonic() + 1.3
            while self.jobs and time.monotonic() < end:
                self.tick_jobs()
                time.sleep(.005)
            # Unresolved ownership keeps this supervisor/lock alive.
            while self.jobs or self.group and not self.stop_child():
                self.tick_jobs()
                time.sleep(.01)
            for connection in list(self.clients):
                self.drop_client(connection)
        for connection in list(self.waiters):
            self.finish_waiter(connection, None)
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
    metadata_path = directory / 'controller.json'
    metadata = read_json(metadata_path) if metadata_path.exists() else None
    if metadata and metadata.get('runtime', 'stub') != request.get('runtime', 'stub'):
        fail(1, 'runtime_mismatch')
    lock_fd = os.open(directory / 'supervisor.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        if metadata and metadata.get('runtime') == 'sbcl' and metadata.get('ended'):
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(directory / 'control.sock'))
                connection.sendall(encode({'action': 'open-session', 'request': request}))
                response = receive_line(connection, time.monotonic() + CONTROL_SECONDS)
            if not response['ok']:
                return response
            end = time.monotonic() + CONTROL_SECONDS
            while live_token(metadata['supervisor_pid']) == metadata['supervisor_token']:
                if time.monotonic() >= end:
                    fail(70, 'infrastructure')
                time.sleep(.01)
            return open_session(root, request)
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
        wait = request.get('limits', {}).get('timeout_seconds', 0) if action == 'poll-operation' else 0
        response = receive_line(connection, time.monotonic() + CONTROL_SECONDS + wait)
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
