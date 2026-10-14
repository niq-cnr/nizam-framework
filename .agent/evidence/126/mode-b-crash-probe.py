"""Owned scratch crash injection at the required write-ahead boundary; no repairs."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile

C2 = 'b6c0b097ecf2e12ee638a60273af568a8b86523a'
OUT = Path('.agent/evidence/126')
paths = ['tools/runtime_session.py', 'tools/test_runtime_session.py',
         'tools/fixtures/runtime_session/stub_runtime.py', 'tools/verify_lib.sh',
         'schema/runtime_session.schema.json', 'schema/runtime_operation.schema.json']
files = {p: subprocess.check_output(['git', 'show', C2 + ':' + p]) for p in paths}
original = files['tools/runtime_session.py'].decode()
anchor = '\n\ndef validate_request(action, request):'
assert original.count(anchor) == 1
fault = '''
    # Reviewer-only process-death injection immediately after durable op write.
    marker = path.parent.parent / 'review-fault.once'
    if path.parent.name == 'operations' and value.get('status') == 'running' and not marker.exists():
        marker.write_text('crashed-after-running-record-before-session-pointer')
        os._exit(86)
'''
instrumented = original.replace(anchor, '\n' + fault + anchor)
compile(instrumented, '<private-C2-crash-injection>', 'exec')
(OUT / 'mode-b-crash-injection.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), instrumented.splitlines(True), fromfile='C2/tools/runtime_session.py', tofile='private-crash-probe/tools/runtime_session.py')))
with tempfile.TemporaryDirectory(prefix='n126-crash-src-') as source_home, tempfile.TemporaryDirectory(prefix='n126-crash-run-') as state_home:
    candidate = Path(source_home)
    for name, raw in files.items():
        path = candidate / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(instrumented.encode() if name == 'tools/runtime_session.py' else raw)
    m = runpy.run_path(str(candidate / 'tools/test_runtime_session.py'))
    s = m['Session'](state_home, candidate=candidate)
    try:
        s.open()
        marker = s.directory / 'review-fault.once'; marker.touch()
        assert s.execute('set', 'before-crash') == 'before-crash'
        assert s.execute('get') == 'before-crash'
        print('POSITIVE: real open/set/get transport works before process-death injection')
        marker.unlink()
        request = s.request('set', 'never-dispatched')
        response = s.call('submit-operation', request, 70)
        assert response['error'] == 'infrastructure'
        for pid, token in s.processes.items():
            m['wait_for'](lambda: m['process_token'](pid) != token, 'crashed incarnation stops')
        pending = json.loads(s.operation(request['operation_id']).read_text())
        session_record = json.loads((s.directory / 'runtime_session.json').read_text())
        assert pending['status'] == 'running' and session_record['outstanding_operation_ref'] is None
        s.no_dispatch(request['operation_id'])
        (OUT / 'mode-b-crash-orphan-record.json').write_text(json.dumps(pending, indent=2) + '\n')
        (OUT / 'mode-b-crash-session-before-reopen.json').write_text(json.dumps(session_record, indent=2) + '\n')
        old_generation = s.record['generation']
        reopened = s.open()
        assert reopened['generation']['counter'] > old_generation['counter']
        assert s.execute('set', 'after-ambiguous-crash') == 'after-ambiguous-crash'
        assert s.execute('get') == 'after-ambiguous-crash'
        assert json.loads(s.operation(request['operation_id']).read_text())['status'] == 'running'
        print('DEFECT CONFIRMED: durable running operation + null session pointer survives crash; reopen succeeds and new execute dispatches while orphan remains running')
        (OUT / 'mode-b-crash-observation.json').write_text(json.dumps({'source_C2': C2, 'source_sha256': hashlib.sha256(files['tools/runtime_session.py']).hexdigest(), 'private_fault_source_sha256': hashlib.sha256(instrumented.encode()).hexdigest(), 'test_sha256': hashlib.sha256(files['tools/test_runtime_session.py']).hexdigest(), 'fault': 'os._exit(86) only after running record is atomically persisted and before outstanding session pointer write', 'positive_before': True, 'submit_actual_exit': 70, 'orphan_status': pending['status'], 'session_pointer_before_reopen': None, 'reopen_succeeded': True, 'subsequent_execute_completed': True, 'old_generation': old_generation, 'new_generation': reopened['generation'], 'shared_source_modified': False}, indent=2) + '\n')
    finally:
        s.cleanup()
