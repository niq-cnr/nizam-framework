"""Independent receipt and bounded activation-proposal validation."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
import yaml

ROOT = Path('.agent/evidence/phase016-preflight')
def read(path):
    return json.loads(Path(path).read_text())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
def blob(rev, path):
    return subprocess.check_output(['git', 'show', f'{rev}:{path}'])

r = read(ROOT / 'hosted-result.json')
p = read(ROOT / 'activation-proposal.json')
job = read(ROOT / 'activation-review-live-job.json')
run = read(ROOT / 'activation-review-live-run.json')
jobs = read(ROOT / 'activation-review-live-jobs.json')['jobs']
assert run['id'] == r['run_id'] == job['run_id'] == 38532840713
assert job['id'] == r['job_id'] == 115748548462
assert run['head_sha'] == job['head_sha'] == r['source_head'] == p['base_revision']
assert run['status'] == job['status'] == 'completed'
assert run['conclusion'] == job['conclusion'] == 'success'
assert len(jobs) == 5 and all(j['conclusion'] == 'success' for j in jobs)
for key in ('id', 'run_id', 'head_sha', 'steps', 'runner_name', 'run_attempt'):
    assert read(ROOT / 'hosted-job.json')[key] == job[key]
for artifact in r['artifacts']:
    assert sha(Path(artifact['path']).read_bytes()) == artifact['sha256']
live_log = next(c for c in read(ROOT / 'activation-review-live-execution.json')['commands'] if c['name'] == 'log')
assert live_log['exit_code'] == 0 and live_log['sha256'] == sha((ROOT / 'hosted-job.log').read_bytes())
log = re.sub(r'\x1b\[[0-9;]*m', '', (ROOT / 'hosted-job.log').read_text())
for marker, expected in [('CAPABILITY_RUNNER_RECEIPT=', r['environment']), ('MAINTENANCE_CHECKOUT_RECEIPT=', r['checkout'])]:
    values = []
    for line in log.splitlines():
        if marker in line:
            try:
                values.append(json.loads(line.split(marker, 1)[1]))
            except json.JSONDecodeError:
                pass
    assert values == [expected]
env = r['environment']['environment']
assert env['RUNNER_OS'] == 'Linux' and env['RUNNER_NAME'] == job['runner_name']
assert env['GITHUB_SHA'] == r['checkout']['checkout_sha']
assert env['GITHUB_RUN_ID'] == str(run['id']) and env['GITHUB_RUN_ATTEMPT'] == str(job['run_attempt'])
assert env['GITHUB_JOB'] == job['name'] == 'convergent_review'
for path, expected in r['checkout']['source_sha256'].items():
    assert sha(blob(r['source_head'], path)) == expected
    assert sha(Path(path).read_bytes()) == expected
workflow = yaml.safe_load(blob(r['source_head'], '.github/workflows/compliance.yml'))
steps = {s.get('name'): s for s in workflow['jobs']['convergent_review']['steps']}
actual_steps = {s['name']: s for s in job['steps']}
features = read('.agent/feature_list_016.json')
assert [c['command'] for c in r['commands']] == features['activation_preflight']['commands']
for c in r['commands']:
    assert steps[c['step']] == {'name': c['step'], 'run': c['command']}
    assert actual_steps[c['step']]['conclusion'] == 'success'
    assert c['exit_code'] == 0 and 'successful step' in c['exit_code_basis']
    group = log.split('##[group]Run ' + c['command'], 1)[1].split('##[endgroup]', 1)[0]
    assert 'shell: /usr/bin/bash -e {0}' in group
assert 'CONFORMANCE: FULL' in log and 'SBCL 2.2.9.debian' in log
assert '--allow-unsupported-isolation' not in log
for path, expected in p['protected_input_sha256'].items():
    assert sha(Path(path).read_bytes()) == expected, path
immutable = p['immutable_obligations']
for f in features['features']:
    assert canonical(f['acceptance_tests']) == immutable['feature_acceptance_hashes'][f['id']]
    assert f['dependencies'] == immutable['feature_dependency_arrays'][f['id']]
    assert f['estimated_lines'] == immutable['feature_estimates'][f['id']]
    assert f['status'] == 'pending' and f['passes'] is False
for key in ('case_matrix', 'shared_file_lanes'):
    assert canonical(features[key]) == immutable[key + '_sha256']
for key, expected in [('original_estimate_lines', 5650), ('ceiling_130pct', 7345)]:
    assert features[key] == immutable[key] == expected
assert features['budget_categories'] == immutable['budget_categories']
assert features['cross_phase_prerequisites'][0]['requires'] == immutable['cross_phase_requires']
assert not p['implementation_permission'] and not p['activation_claimed']
foundation = read('.agent/evidence/118/evidence-capture.json')
assert foundation['passed'] is True
assert foundation['revision'] == p['prerequisites']['foundation']['captured_revision']
for path, expected in foundation['evidence_sha256'].items():
    assert sha(Path(path).read_bytes()) == expected
for prefix in ('qa', 'mode_b'):
    assert sha(Path(foundation[prefix + '_ref']).read_bytes()) == foundation[prefix + '_sha256']
pr = read(ROOT / 'activation-review-live-pr94.json')
main = read(ROOT / 'activation-review-live-main-run.json')
assert pr['merged'] is True and pr['number'] == 94
assert pr['merge_commit_sha'] == main['head_sha'] == p['prerequisites']['foundation']['merge_revision']
assert main['status'] == 'completed' and main['conclusion'] == 'success'
assert main['html_url'] == p['prerequisites']['foundation']['main_ci_url']
assert not Path(p['stale_reference']['old']).exists()
assert Path(p['stale_reference']['replacement']).is_file()
cost = p['cost_treatment']['ci_transport']
start, end = cost['source_range'].split('..')
measurement = subprocess.check_output(['git', 'diff', '--numstat', start, end, '--', cost['path']], text=True).split()
assert measurement[:2] == ['19', '1'] and cost['counted'] == 20
assert 'once' in cost['charge'] and 'must not add it again' in p['cost_treatment']['activation_and_registration']
print(json.dumps({'result': 'pass', 'reviewed_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'live_run_id': run['id'], 'live_job_id': job['id'], 'checks': ['live GitHub identity and five passing jobs', 'raw job log equality and artifact hashes', 'same Linux job and exact commands with fail-closed shell exit basis', 'source hashes match exercised head and current inputs', 'full isolation and SBCL version/no-init', 'all protected planning and acceptance hashes', 'dependencies and original budget', 'foundation evidence hashes and PR94/main CI linkage', 'once-only 20-line CI preparation measurement'], 'limits': 'Capability prerequisite and conditional plan transaction only; canonical edits and compliance remain to be checked after application.'}, indent=2))
