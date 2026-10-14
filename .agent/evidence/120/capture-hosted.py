"""Root transport verifier for observed feature120 hosted logs; executes no tests."""
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys

import yaml

E = pathlib.Path('.agent/evidence/120')
prefix, expected_head, expected_run, expected_closeout, expected_job = sys.argv[1:]
def read(name): return json.loads((E / name).read_bytes())
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(revision, path): return subprocess.check_output(['git', 'show', revision + ':' + path])
def digest(data): return hashlib.sha256(data).hexdigest()
run = read(prefix + '-run.stdout.txt')
closeout = read(prefix + '-closeout.stdout.txt')
assert run['databaseId'] == int(expected_run) and closeout['databaseId'] == int(expected_closeout)
assert run['status'] == closeout['status'] == 'completed'
assert run['headSha'] == closeout['headSha'] == expected_head
assert closeout['conclusion'] == 'success'
assert len(run['jobs']) == 5 and all(j['status'] == 'completed' for j in run['jobs'])
failed = [j['name'] for j in run['jobs'] if j['conclusion'] != 'success']
assert (prefix == 'ci1' and failed == ['validate'] and run['conclusion'] == 'failure') or (prefix == 'ci2' and failed == [] and run['conclusion'] == 'success')
job, = [j for j in run['jobs'] if j['databaseId'] == int(expected_job) and j['name'] == 'fixtures_self_test']
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
assert expected_head in parents and '92fecd8d376964f5e3dd7e34bc201035acfe8bc6' in parents
candidate = '5c011078fae6b596bc3cddd2cdb9e7fc276f19af'
paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/convergent_review.py', 'tools/README.md', 'CHANGELOG.md', '.github/workflows/compliance.yml']
bindings = {}
for path in paths:
    actual = blob(checkout, path)
    assert actual == blob(candidate, path)
    bindings[path] = {'sha256': digest(actual), 'git_blob': git('rev-parse', checkout + ':' + path)}
for path, expected in checkout_record['source_sha256'].items():
    assert digest(blob(checkout, path)) == expected
workflow = yaml.safe_load(blob(checkout, '.github/workflows/compliance.yml'))
job_config = workflow['jobs']['fixtures_self_test']
run_step, = [s for s in job_config['steps'] if s.get('run') == command]
assert not job_config.get('continue-on-error', False) and not run_step.get('continue-on-error', False)
observed = []
for line in lines:
    fields = line.split('\t', 2)
    if len(fields) == 3 and fields[1] == 'Run ' + command and (match := re.search(r'Z PASS (\S+)$', fields[2])):
        observed.append(match.group(1))
old = [row['case'] for row in json.loads(pathlib.Path('.agent/evidence/118/api-interface.json').read_bytes())['current_cases']]
prior = [shlex.split(v['command'])[-1] for v in json.loads(pathlib.Path('.agent/contracts/119.json').read_bytes())['verification']]
new = [shlex.split(v['command'])[-1] for v in json.loads(pathlib.Path('.agent/contracts/120.json').read_bytes())['verification']]
assert len(old) == 20 and len(prior) == 6 and len(new) == 11 and observed == old + prior + new
assert all(row['actual_exit'] == 0 for row in read(prefix + '-fetch-results.json'))
result = {'role': 'Root', 'attempt': int(prefix[-1]), 'passed': not failed, 'default37_passed': True, 'pr': 101, 'head': expected_head, 'compliance_run': int(expected_run), 'closeout_run': int(expected_closeout), 'job': int(expected_job), 'checkout': checkout, 'protected_bindings_revision': git('rev-parse', candidate), 'initial_source_commit': '1689f0dc1f1ef20e96c7cb7ee1e3375232a83ce5', 'test_author_commit': 'b9cab92e940f691ee003af5e2acb835f3359fc94', 'command': command, 'exit_code': 0, 'exit_basis': 'Successful hosted single-command Python step, pinned workflow has no continue-on-error.', 'all37_ordered': observed, 'new11': new, 'source_bindings': bindings, 'raw_log': str(E / (prefix + '-job-log.stdout.txt')), 'raw_log_sha256': digest(log), 'fetch_results': str(E / (prefix + '-fetch-results.json')), 'failed_jobs': failed, 'boundary': 'Existing hosted default37 only; different hosted/local environments are not claimed identical. No feature123 controls-ready or comparative result.'}
(E / (prefix + '-receipt.json')).write_text(json.dumps(result, indent=2) + '\n')
print('PASS hosted default37 and exact checkout/protected objects; overall failed jobs=' + repr(failed))
