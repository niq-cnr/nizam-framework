"""Independent B0 controls only; no controller behavior or semantic red claim."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch

root = Path.cwd()
seal = json.loads(Path('.agent/evidence/126/test-seal-b0.json').read_text())
for entry in [seal['test'], seal['api'], seal['obligation_projection'], *seal['normative_inputs']]:
    raw = Path(entry['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    assert subprocess.check_output(['git', 'hash-object', entry['path']], text=True).strip() == entry['git_blob']
contract = json.loads(Path('.agent/contracts/126.json').read_text())
assert contract['status'] == 'approved'
assert hashlib.sha256(Path('.agent/contracts/126.json').read_bytes()).hexdigest() == '7eed25daca89c13a548976a213ddba6e6837acaee90511f0deff152a60697778'
projection = json.loads(Path(seal['obligation_projection']['path']).read_text())
for key in ('verification', 'interface', 'ci_integration'):
    assert projection[key] == contract[key]
test = Path('tools/test_runtime_session.py')
source = test.read_text()
compile(source, str(test), 'exec')
module = runpy.run_path(str(test))
print('PASS exact test/API/projection and ten normative input hashes; approved contract projection; syntax')
text = Path('tools/fixtures_self_test.sh').read_text()
with tempfile.TemporaryDirectory(prefix='n126-review-') as home:
    module['claim_controls'](home, text)
for label, body in [('always-pass', 'return 0'), ('always-reject', 'return 1')]:
    with tempfile.TemporaryDirectory(prefix='n126-review-') as home:
        try:
            module['claim_controls'](home, 'claim_map_check() {\n' + body + '\n}')
        except AssertionError:
            print('PASS independent claim harness rejects', label)
        else:
            raise AssertionError(label + ' accepted')

# Only the reviewer's disposable child is exposed to this ownership counterexample.
with tempfile.TemporaryDirectory(prefix='n126-review-') as home:
    session = module['Session'](home)
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
    try:
        module['wait_for'](lambda: module['process_token'](child.pid), 'review child starts')
        assert str(session.state).encode() not in Path(f'/proc/{child.pid}/cmdline').read_bytes()
        session.directory.mkdir(parents=True)
        (session.directory / 'controller.json').write_text(json.dumps({'supervisor_pid': child.pid, 'child_pid': child.pid, 'supervisor_pgid': child.pid}))
        session.remember()
        session.cleanup()
        outcome = child.wait(timeout=2)
        assert outcome < 0
        print('CONFIRMED cleanup ownership gap: unrelated reviewer-owned child killed; returncode=', outcome)
    finally:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=2)

p = subprocess.run([sys.executable, str(test), '--chec', 'record-schema'], capture_output=True, text=True)
assert p.returncode == 2 and 'SETUP_FAILURE: controller source absent' in p.stderr
print('CONFIRMED abbreviated selector --chec accepted by parser; later source-absence failure only:', p.stderr.strip())

# Replay the independent peer's exact generated source to observe publication order.
tree = ast.parse(source)
write = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == 'stub' and n.func.attr == 'write_text')
with tempfile.TemporaryDirectory(prefix='n126-review-') as home:
    base = Path(home); marker = base / 'sent.json'; operation = base / 'state/one/operations/op.json'
    operation.parent.mkdir(parents=True); operation.write_text('{"operation_id":"op","status":"running"}')
    peer = eval(compile(ast.Expression(write.args[0]), '<peer-expression>', 'eval'), {'repr': repr, 'str': str},
                {'mode': 'late-frame', 'marker': marker, 'base': base})
    frames = []; original_replace = os.replace; order = []
    def observe_replace(src, dst):
        order.append({'result_already_sent': any(f.get('type') == 'result' for f in frames), 'marker_exists': marker.exists()})
        return original_replace(src, dst)
    generation = {'counter': 1, 'nonce': 'a' * 32}
    inputs = io.StringIO(json.dumps({'generation': generation}) + '\n' + json.dumps({'request': {'operation_id': 'op'}}) + '\n')
    with patch('sys.stdin', inputs), patch('sys.stdout', io.StringIO()), patch('os.write', lambda fd, data: frames.append(json.loads(data)) or len(data)), patch('os.replace', observe_replace):
        exec(compile(peer, '<exact-private-peer>', 'exec'), {})
    assert order == [{'result_already_sent': True, 'marker_exists': False}]
    print('CONFIRMED late-frame race window:', json.dumps(order[0]), '; caller uses marker.unlink immediately after finish, without marker wait')
print('REVIEW CONTROLS COMPLETE: defects above are harness findings; no product semantic red or acceptance claimed.')
