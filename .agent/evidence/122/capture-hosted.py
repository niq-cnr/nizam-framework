"""Root transport only: validate observed hosted46 logs and immutable checkout objects."""
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys

import yaml

E = pathlib.Path('.agent/evidence/122')
prefix, head, run_id, closeout_id, job_id, candidate, pr = sys.argv[1:]
def read(suffix): return json.loads((E / (prefix + suffix)).read_bytes())
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(rev, path): return subprocess.check_output(['git', 'show', rev + ':' + path])
def sha(raw): return hashlib.sha256(raw).hexdigest()
run, closeout = read('-run.stdout.txt'), read('-closeout.stdout.txt')
assert run['databaseId'] == int(run_id) and closeout['databaseId'] == int(closeout_id)
assert run['headSha'] == closeout['headSha'] == head
assert run['status'] == closeout['status'] == 'completed'
assert closeout['conclusion'] == 'success'
assert len(run['jobs']) == 5 and all(j['status'] == 'completed' for j in run['jobs'])
failed = [j['name'] for j in run['jobs'] if j['conclusion'] != 'success']
assert run['conclusion'] == ('failure' if failed else 'success')
job, = [j for j in run['jobs'] if j['databaseId'] == int(job_id) and j['name'] == 'fixtures_self_test']
assert job['conclusion'] == 'success'
command = 'PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py'
step, = [s for s in job['steps'] if s['name'] == 'Run ' + command]
assert step['status'] == 'completed' and step['conclusion'] == 'success'
log = (E / (prefix + '-job-log.stdout.txt')).read_bytes()
lines = log.decode().splitlines()
checkout_record, = [json.loads(m.group(1)) for line in lines if (m := re.search(r'Z MAINTENANCE_CHECKOUT_RECEIPT=(\{.*\})$', line))]
checkout = checkout_record['checkout_sha']
assert re.fullmatch('[0-9a-f]{40}', checkout)
parents = git('rev-list', '--parents', '-n', '1', checkout).split()[1:]
assert head in parents and '3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03' in parents
paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/convergent_review.py', 'tools/README.md', 'CHANGELOG.md', '.github/workflows/compliance.yml']
bindings = {}
for path in paths:
    raw = blob(checkout, path)
    assert raw == blob(candidate, path), path
    bindings[path] = {'sha256': sha(raw), 'git_blob': git('rev-parse', checkout + ':' + path)}
for path, digest in checkout_record['source_sha256'].items(): assert sha(blob(checkout, path)) == digest
job_config = yaml.safe_load(blob(checkout, '.github/workflows/compliance.yml'))['jobs']['fixtures_self_test']
run_step, = [s for s in job_config['steps'] if s.get('run') == command]
assert not job_config.get('continue-on-error', False) and not run_step.get('continue-on-error', False)
observed = []
for line in lines:
    fields = line.split('\t', 2)
    if len(fields) == 3 and fields[1] == 'Run ' + command and (m := re.search(r'Z PASS (\S+)$', fields[2])): observed.append(m.group(1))
expected = [r['case'] for r in json.loads(blob(candidate, '.agent/evidence/118/api-interface.json'))['current_cases']]
for feature in ['119', '120', '121', '122']:
    expected += [shlex.split(v['command'])[-1] for v in json.loads(blob(candidate, '.agent/contracts/' + feature + '.json'))['verification']]
assert len(expected) == 46 and observed == expected
assert all(row['actual_exit'] == 0 for row in read('-fetch-results.json'))
result = {'role': 'Root', 'passed': not failed, 'default46_passed': True, 'pr': int(pr), 'head': head, 'compliance_run': int(run_id), 'closeout_run': int(closeout_id), 'job': int(job_id), 'checkout': checkout, 'protected_bindings_revision': git('rev-parse', candidate), 'command': command, 'actual_exit': 0, 'exit_basis': 'Successful hosted single-command step; immutable workflow has no continue-on-error.', 'all46_ordered': observed, 'new4': expected[-4:], 'source_bindings': bindings, 'raw_log': str(E / (prefix + '-job-log.stdout.txt')), 'raw_log_sha256': sha(log), 'failed_jobs': failed, 'boundary': 'Observed existing hosted default46 only; no feature123 controls-ready, identical-environment or comparative claim.'}
(E / (prefix + '-receipt.json')).write_text(json.dumps(result, indent=2) + '\n')
print('PASS hosted46/checkout/protected objects; overall failed jobs=' + repr(failed))
