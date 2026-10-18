#!/usr/bin/env python3
"""Sealed preparation: public SBCL completed-history/idle-close witness only.

Do not execute until separate Root release. Exit1 is narrowly classified B2 red;
exit0 is a bounded positive, exit2 is setup/unexpected/inapplicable, never red.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

PINS = {
    'tools/runtime_session.py': 'e8e5571d365d8bf84df34c0bac1a08b002297543100f1fd6e33c9e6c046712ce',
    'tools/sbcl_session_loop.lisp': '2ad3d3b633637e305e428169654929aec80577f55d90477338071247cb5f0cf9',
    'tools/test_runtime_session.py': 'd186e915424040b32ee9c232d952a170ec0a806cf415126abf34a8a81eda0431',
    '.agent/contracts/129.json': '71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6',
}
MAX_OPERATIONS = 512
WORK_SECONDS = 270


def ensure(value, message):
    if not value:
        raise RuntimeError(message)


def emit(tag, value):
    print(tag + ' ' + json.dumps(value, sort_keys=True), flush=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected(root):
    names = set(PINS) | {'.agent/run_state.json'}
    names.update(str(p.relative_to(root)) for p in (root / '.nizam').rglob('*') if p.is_file())
    return {name: digest(root / name) for name in sorted(names)}


def cleanup(frozen, session):
    # Qualified frozen ownership discovery + start-token recheck; close is not
    # called here and its possibly broken public response cannot gate cleanup.
    before = frozen.live_owned(session.marker)
    groups = {pid: os.getpgid(pid) for pid in before if frozen.process_token(pid) == before[pid]}
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid, token in frozen.live_owned(session.marker).items():
            try:
                ensure(pid > 1 and pid != os.getpid(), 'scratch cleanup identity')
                group = os.getpgid(pid)
                if frozen.live_owned(session.marker).get(pid) == token and os.getpgid(pid) == group:
                    os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(.1)
    frozen.wait_for(lambda: not frozen.live_owned(session.marker), 'owned scratch cleanup', 2)
    emit('B2_CLEANUP', {'session': session.name, 'owned_tokens_before': before,
         'pgids_before': groups, 'remaining': frozen.live_owned(session.marker)})


def close_observed(frozen, session):
    meta = frozen.load(session.directory / 'controller.json')
    response = session.call('close-session', session.identity(frozen.ORCH), (0, 1, 70))
    emit('B2_CLOSE_RESPONSE', {'session': session.name, 'response': response, 'exit': session.last_exit})
    if session.last_exit == 0:
        ensure(response == {'ok': True, 'result': {'closed': True, 'session_id': session.name}}, 'exact closed acknowledgement')
        frozen.wait_for(lambda: not frozen.live_owned(session.marker) and
            not (session.directory / 'control.sock').exists() and not session.owns_lock(meta['supervisor_pid']),
            'observed complete close lifecycle', 2)
        return True
    ensure(session.last_exit == 70 and response == {'ok': False, 'error': 'infrastructure'},
           'unexpected close refusal is not B2 red')
    ensure(frozen.live_owned(session.marker) and session.owns_lock(meta['supervisor_pid']) and
           (session.directory / 'control.sock').exists(), 'refusal observed before cleanup with live owned supervisor')
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    root = args.candidate.resolve(strict=True)
    ensure(os.environ.get('TMPDIR') == '/tmp', 'explicit short TMPDIR=/tmp required')
    for name, expected in PINS.items():
        ensure(digest(root / name) == expected, 'sealed identity mismatch: ' + name)
    baseline = protected(root)
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD', '--', *PINS], check=True)
    emit('B2_BINDINGS', {'head': head, 'pins': PINS, 'max_operations': MAX_OPERATIONS,
         'work_seconds': WORK_SECONDS, 'scope': 'public idle close only; no cancellation claim'})
    spec = importlib.util.spec_from_file_location('frozen_runner', root / 'tools/test_runtime_session.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    def expired(signum, frame):
        raise RuntimeError('bounded diagnostic deadline; no semantic classification')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(WORK_SECONDS)
    sessions = []
    unrelated = None
    unrelated_token = None
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='n129-history-', dir='/tmp') as temp:
        home = Path(temp)
        try:
            sentinel = home / 'unrelated-sentinel'
            sentinel.write_bytes(os.urandom(32)); saved_sentinel = sentinel.read_bytes()
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'],
                cwd=home, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
            unrelated_token = frozen.wait_for(lambda: frozen.process_token(unrelated.pid), 'unrelated identity')
            executable = frozen.sbcl_preflight(home)
            for name in ('positive', 'history'):
                directory = home / name; directory.mkdir()
                session = frozen.LiveSession(directory, name=name, candidate=root); sessions.append(session)
                session.start(executable)
                frozen.live_nonce(session, os.urandom(16).hex())
                meta = frozen.load(session.directory / 'controller.json')
                ensure(frozen.live_owned(session.marker).get(meta['supervisor_pid']) == meta['supervisor_token'] and
                       session.owns_lock(meta['supervisor_pid']) and
                       frozen.process_token(meta['child_pid']) == meta['child_token'] and
                       os.getpgid(unrelated.pid) != os.getpgid(meta['child_pid']), 'positive native identities/lock/PGID isolation')
                emit('B2_NATIVE_POSITIVE', {'session': name, 'controller': meta, 'nonce_operations': 2})
                if name == 'positive':
                    ensure(close_observed(frozen, session), 'small-history public close positive required')
            session = sessions[-1]
            original = {str(p): digest(p) for p in (session.directory / 'operations').glob('*.json')}
            completed = 2
            refusal = None
            for number in range(MAX_OPERATIONS - completed - 2):
                nonce = os.urandom(16).hex(); marker = session.home / 'latest-native-nonce'
                request = session.lisp('(progn ' + frozen.lisp_write(marker, nonce) + ' (+ 19 23))')
                response = session.call('submit-operation', request, (0, 1, 70))
                if session.last_exit:
                    ensure(session.last_exit == 70 and response == {'ok': False, 'error': 'infrastructure'} and
                           not session.operation(request['operation_id']).exists() and not marker.read_text().strip() == nonce,
                           'only non-dispatched infrastructure admission refusal is eligible')
                    refusal = {'request': request, 'response': response, 'exit': session.last_exit}
                    break
                session.terminal(request)
                result = frozen.load(session.result_path(request['operation_id']))
                ensure(result['result'] == 42 and type(result['result']) is int and
                       marker.read_text().splitlines() == [nonce], 'each genuine completed native operation and nonce')
                completed += 1
            # Preserve an immutable snapshot of every public completed record;
            # there is no seeded history, result mutation or private wire frame.
            records = {str(p): digest(p) for p in (session.directory / 'operations').glob('*.json')}
            ensure(all(records.get(p) == value for p, value in original.items()), 'original history unchanged')
            durable = frozen.load(session.directory / 'runtime_session.json')
            ensure(durable['outstanding_operation_ref'] is None and session.runstate.read_bytes() == session.saved_state,
                   'idle session and unchanged governed attempt')
            closed = close_observed(frozen, session)
            ensure({str(p): digest(p) for p in (session.directory / 'operations').glob('*.json')} == records,
                   'full actual history preserved by close/refusal')
            ensure(unrelated.poll() is None and frozen.process_token(unrelated.pid) == unrelated_token and
                   sentinel.read_bytes() == saved_sentinel and protected(root) == baseline,
                   'unrelated process/sentinel and protected repository preservation')
            emit('B2_OBSERVATION', {'before_cleanup': True, 'completed_operations': completed,
                 'record_hashes': records, 'admission_refusal': refusal, 'close_succeeded': closed,
                 'elapsed_seconds': time.monotonic() - started, 'attempt_equal': True,
                 'sentinel_equal': True, 'unrelated_pid': unrelated.pid, 'unrelated_token': unrelated_token})
            if not closed:
                ensure(refusal is not None and completed > 2, 'history growth and preceding public success required for B2 red')
                print('BEHAVIOR_ASSERTION: B2_VALID_COMPLETED_HISTORY_DISABLES_IDLE_CLOSE', file=sys.stderr)
                return 1
            ensure(refusal is None, 'close recovery with failed admission is unexpected, not full positive')
            print('PASS B2 bounded public history and observed idle close; no unlimited-history claim')
            return 0
        finally:
            signal.alarm(0)
            errors = []
            for session in sessions:
                try:
                    cleanup(frozen, session)
                    ensure(session.runstate.read_bytes() == session.saved_state, 'private governed attempt preserved')
                except Exception as exc:
                    errors.append(str(exc))
            if unrelated is not None:
                if unrelated_token is not None:
                    if not (unrelated.poll() is None and frozen.process_token(unrelated.pid) == unrelated_token and
                            sentinel.read_bytes() == saved_sentinel):
                        errors.append('unrelated identity/sentinel did not survive owned cleanup')
                    emit('B2_SENTINEL_AFTER_OWNED_CLEANUP', {'pid': unrelated.pid,
                         'original_token': unrelated_token, 'observed_token': frozen.process_token(unrelated.pid),
                         'sentinel_equal': sentinel.read_bytes() == saved_sentinel})
                if unrelated.poll() is None:
                    unrelated.terminate()
                unrelated.wait(timeout=2)
            ensure(protected(root) == baseline, 'all protected bytes preserved')
            ensure(not errors, 'cleanup failures: ' + repr(errors))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('SETUP_OR_UNEXPECTED_OR_APPLICABILITY_FAILURE: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(2)
