"""Capture observed hosted results; does not grant product acceptance."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

E = Path('.agent/evidence/126')
RUN, JOB = 38548355878, 115799921707
SOURCE = 'd965c2ca9dd845f9a094153c7328d90a5398d06f'
TEST = 'd89d79fcdb9c5b3d3098f5ed8162b11467bb3284'


def capture(stem, argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=50)
    (E / (stem + '.stdout.txt')).write_text(result.stdout)
    (E / (stem + '.stderr.txt')).write_text(result.stderr)
    (E / (stem + '-capture.json')).write_text(json.dumps({
        'argv': argv, 'actual_exit': result.returncode,
        'boundary': 'Retrieval exit; actual CI outcomes are separate.'}, indent=2) + '\n')
    assert result.returncode == 0, (stem, result.returncode)
    return result.stdout


run = json.loads(capture('ci-c3-run', ['gh', 'run', 'view', str(RUN), '--json',
    'databaseId,headSha,status,conclusion,url,jobs']))
raw = capture('ci-c3-capable-job', ['gh', 'run', 'view', str(RUN), '--job', str(JOB), '--log'])
assert run['status'] == 'completed' and run['conclusion'] == 'success'
assert len(run['jobs']) == 5 and all(j['conclusion'] == 'success' for j in run['jobs'])
job = next(j for j in run['jobs'] if j['databaseId'] == JOB)
steps = {s['name']: s['conclusion'] for s in job['steps']}
for name in ('Check SBCL version', 'Check fresh SBCL without init files',
             'Run required isolation suite', 'Run fixture self-test'):
    assert steps[name] == 'success', name
lines = [re.sub(r'^\S+\s', '', line.split('\t', 2)[-1]) for line in raw.splitlines()]
environment = next(json.loads(s.split('=', 1)[1]) for s in lines
                   if s.startswith('CAPABILITY_RUNNER_RECEIPT='))
maintenance = next(json.loads(s.split('=', 1)[1]) for s in lines
                   if s.startswith('MAINTENANCE_CHECKOUT_RECEIPT='))
checkout = maintenance['checkout_sha']
assert checkout == environment['environment']['GITHUB_SHA']
assert str(RUN) == environment['environment']['GITHUB_RUN_ID']
assert 'CONFORMANCE: FULL' in lines
version = next(s for s in lines if re.match(r'^SBCL [0-9]', s))
commands, pending = [], None
for line in lines:
    if line.startswith('COMMAND: '):
        assert pending is None
        pending = line.removeprefix('COMMAND: ')
    elif line.startswith('ACTUAL_EXIT: '):
        assert pending is not None
        commands.append({'command': pending, 'actual_exit': int(line.split(': ', 1)[1])})
        pending = None
contract = json.loads(Path('.agent/contracts/126.json').read_text())
assert pending is None and len(commands) == 9
assert sorted(c['command'] for c in commands) == sorted(v['command'] for v in contract['verification'])
assert all(c['actual_exit'] == 0 for c in commands)
identities = {}
paths = ['tools/runtime_session.py', 'tools/fixtures/runtime_session/stub_runtime.py',
         'tools/test_runtime_session.py', 'tools/fixtures_self_test.sh', 'tools/README.md', 'CHANGELOG.md']
for path in paths:
    revision = TEST if path == 'tools/test_runtime_session.py' else SOURCE
    actual = subprocess.check_output(['git', 'show', checkout + ':' + path])
    expected = subprocess.check_output(['git', 'show', revision + ':' + path])
    assert actual == expected == Path(path).read_bytes(), path
    identities[path] = hashlib.sha256(actual).hexdigest()
result = {'kind': 'actual-hosted-C3-command-receipt', 'run': RUN, 'job': JOB,
    'run_head': run['headSha'], 'checkout': checkout, 'source': SOURCE, 'test_revision': TEST,
    'source_sha256': identities, 'environment': environment, 'SBCL_version': version,
    'required_isolation': 'CONFORMANCE: FULL', 'step_conclusions': steps, 'commands': commands,
    'raw_log': str(E / 'ci-c3-capable-job.stdout.txt'),
    'run_record': str(E / 'ci-c3-run.stdout.txt'),
    'boundary': 'Actual same-job capable-host nine-command success. ModeB, freshQA and Root capture remain independent gates; no SBCL runtime or full adapter acceptance.'}
(E / 'ci-c3-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'run': RUN, 'job': JOB, 'checkout': checkout, 'commands': len(commands), 'all_zero': True}))
