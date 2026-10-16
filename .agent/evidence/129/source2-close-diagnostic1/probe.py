#!/usr/bin/env python3
"""One released public idle-close witness; frozen Source2 and runner unchanged."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[4]
PINS = {
    'tools/runtime_session.py': 'aae6a5cbe09435e39c29153469a9ca13f45065e6248ff70ca44f6ce9bc5d8fa5',
    'tools/sbcl_session_loop.lisp': '2ad3d3b633637e305e428169654929aec80577f55d90477338071247cb5f0cf9',
    'tools/test_runtime_session.py': 'd186e915424040b32ee9c232d952a170ec0a806cf415126abf34a8a81eda0431',
}


def ensure(value, message):
    if not value:
        raise RuntimeError(message)


def emit(tag, value):
    print(tag + ' ' + json.dumps(value, sort_keys=True), flush=True)


def main():
    for name, digest in PINS.items():
        ensure(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'protected identity mismatch')
    spec = importlib.util.spec_from_file_location('frozen_runner', ROOT / 'tools/test_runtime_session.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    with tempfile.TemporaryDirectory(prefix='n129-idle-close-') as temp:
        home = Path(temp)
        executable = frozen.sbcl_preflight(home)
        session = frozen.LiveSession(home, candidate=ROOT)
        unrelated = None
        outcome = None
        try:
            sentinel = home / 'unrelated-sentinel'
            sentinel.write_bytes(os.urandom(32))
            sentinel_bytes = sentinel.read_bytes()
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(55)'],
                                         cwd=home, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, start_new_session=True)
            unrelated_token = frozen.wait_for(lambda: frozen.process_token(unrelated.pid), 'unrelated process ready')
            session.start(executable)
            frozen.live_nonce(session, os.urandom(16).hex())
            leader, leader_token = next(iter(session.live_tokens.items()))
            meta = frozen.load(session.directory / 'controller.json')
            supervisor = meta['supervisor_pid']
            ensure(meta['child_pid'] == leader and meta['child_token'] == leader_token and
                   frozen.live_owned(session.marker).get(supervisor) == meta['supervisor_token'] and
                   session.owns_lock(supervisor), 'actual private supervisor/leader identity and lock')
            spawn_started = time.monotonic()
            descendant, descendant_token = frozen.live_group_descendant(session)
            ready_paths = list(home.glob('group-ready-*'))
            ensure(len(ready_paths) == 1, 'one qualified descendant witness')
            ready = frozen.load(ready_paths[0])
            pulse = home / ('group-pulse-' + ready['nonce'])
            result = frozen.load(session.result_path(ready['operation_id']))
            operation = frozen.load(session.operation(ready['operation_id']))
            durable = frozen.load(session.directory / 'runtime_session.json')
            ensure(type(result['result']) is int and result['result'] == 42 and result['status'] == 'completed' and
                   result['operation_id'] == ready['operation_id'] and result['generation'] == session.record['generation'] and
                   operation['status'] == 'completed' and operation['lease_epoch'] == session.record['lease_epoch'] and
                   operation['attempt'] == 1 and durable['outstanding_operation_ref'] is None and
                   frozen.process_token(leader) == leader_token and frozen.process_token(descendant) == descendant_token and
                   session.runstate.read_bytes() == session.saved_state, 'completed correlated spawn and idle live leader')
            ensure(unrelated.poll() is None and frozen.process_token(unrelated.pid) == unrelated_token and
                   os.getpgid(unrelated.pid) != os.getpgid(leader), 'unrelated process outside runtime group')
            before_pulse = int(pulse.read_text())
            emit('IDLE_CLOSE_BEFORE', {'leader_pid': leader, 'leader_token': leader_token,
                 'supervisor_pid': supervisor, 'supervisor_token': meta['supervisor_token'],
                 'descendant': ready, 'descendant_token': descendant_token, 'pulse': before_pulse,
                 'outstanding_operation_ref': durable['outstanding_operation_ref'], 'spawn_result': result,
                 'unrelated_pid': unrelated.pid, 'unrelated_token': unrelated_token})
            stop = threading.Event()
            observations = []
            def observe():
                while not stop.is_set():
                    observations.append({'since_spawn_seconds': time.monotonic() - spawn_started,
                         'leader_token': frozen.process_token(leader),
                         'descendant_token': frozen.process_token(descendant), 'pulse': int(pulse.read_text()),
                         'supervisor_token': frozen.process_token(supervisor),
                         'endpoint_exists': (session.directory / 'control.sock').exists()})
                    stop.wait(.02)
            observer = threading.Thread(target=observe)
            observer.start()
            try:
                response = session.call('close-session', session.identity(frozen.ORCH))
                acknowledged_at = time.monotonic()
                ensure(response == {'ok': True, 'result': {'closed': True, 'session_id': session.name}},
                       'unambiguous public closed response')
                frozen.wait_for(lambda: frozen.process_token(supervisor) != meta['supervisor_token'] and
                                not (session.directory / 'control.sock').exists() and not session.owns_lock(supervisor),
                                'completed supervisor lifecycle after closed acknowledgement', 2)
                lifecycle = {'supervisor_pid': supervisor, 'original_token': meta['supervisor_token'],
                             'observed_token': frozen.process_token(supervisor),
                             'endpoint_exists': (session.directory / 'control.sock').exists(),
                             'supervisor_owns_lock': session.owns_lock(supervisor),
                             'seconds_since_closed_ack': time.monotonic() - acknowledged_at}
                emit('IDLE_CLOSE_LIFECYCLE', lifecycle)
            finally:
                stop.set()
                observer.join(timeout=1)
                emit('IDLE_CLOSE_TIMELINE', observations)
            ensure(not observer.is_alive() and response == {'ok': True, 'result': {'closed': True, 'session_id': session.name}},
                   'unambiguous public closed response')
            ensure(frozen.process_token(leader) != leader_token, 'original leader must be observed dead after close')
            descendant_live = frozen.process_token(descendant) == descendant_token
            at_response_pulse = int(pulse.read_text())
            if descendant_live:
                frozen.wait_for(lambda: frozen.process_token(descendant) == descendant_token and
                                int(pulse.read_text()) > at_response_pulse, 'same descendant advances after close', .6)
            after_pulse = int(pulse.read_text())
            ensure(time.monotonic() - spawn_started < 30 and unrelated.poll() is None and
                   frozen.process_token(unrelated.pid) == unrelated_token and sentinel.read_bytes() == sentinel_bytes and
                   session.runstate.read_bytes() == session.saved_state, 'before finite backstop; unrelated sentinel/process and attempt preserved')
            witness = {'closed_response': response, 'leader_pid': leader, 'leader_original_token': leader_token,
                       'leader_observed_token': frozen.process_token(leader), 'descendant_pid': descendant,
                       'descendant_original_token': descendant_token, 'descendant_observed_token': frozen.process_token(descendant),
                       'pulse_before_close': before_pulse, 'pulse_at_response': at_response_pulse, 'pulse_after_close': after_pulse,
                       'since_spawn_seconds': time.monotonic() - spawn_started, 'backstop_seconds': 45,
                       'before_cleanup': True, 'unrelated_alive': True, 'sentinel_equal': True, 'attempt_equal': True,
                       'seconds_since_closed_ack': time.monotonic() - acknowledged_at, 'supervisor_lifecycle': lifecycle}
            emit('IDLE_CLOSE_OBSERVATION', witness)
            if descendant_live:
                ensure(witness['descendant_observed_token'] == descendant_token and after_pulse > before_pulse,
                       'same owned descendant survival and fresh progress')
                outcome = 1
            else:
                ensure(witness['descendant_observed_token'] != descendant_token, 'both original runtime processes dead')
                outcome = 0
        finally:
            owned_before = frozen.live_owned(session.marker)
            for sig in (signal.SIGTERM, signal.SIGKILL):
                for pid, token in frozen.live_owned(session.marker).items():
                    if frozen.live_owned(session.marker).get(pid) == token:
                        try:
                            os.kill(pid, sig)
                        except ProcessLookupError:
                            pass
                time.sleep(.1)
            frozen.wait_for(lambda: not frozen.live_owned(session.marker), 'bounded owned scratch cleanup', 2)
            if unrelated is not None:
                if unrelated.poll() is None:
                    unrelated.terminate()
                unrelated.wait(timeout=2)
            emit('IDLE_CLOSE_CLEANUP', {'owned_before': owned_before, 'remaining': frozen.live_owned(session.marker),
                                      'unrelated_pid': None if unrelated is None else unrelated.pid,
                                      'unrelated_exit': None if unrelated is None else unrelated.returncode,
                                      'attempt_equal': session.runstate.read_bytes() == session.saved_state})
        if outcome == 1:
            print('BEHAVIOR_ASSERTION: OWNED_RUNTIME_GROUP_CLOSE_DEATH_BEYOND_LEADER', file=sys.stderr)
        else:
            print('PASS public-idle-close-owned-group-death')
        return outcome


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('SETUP_OR_INFRASTRUCTURE_FAILURE: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(2)
