"""Parse observed completed PR100 logs; no CI/test rerun or network retry."""
import hashlib, json, pathlib, re, shlex, subprocess
import yaml
E = pathlib.Path('.agent/evidence/119')
def read(name): return json.loads((E / name).read_text())
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(rev, path): return subprocess.check_output(['git', 'show', rev + ':' + path])
def digest(data): return hashlib.sha256(data).hexdigest()
run = read('ci2-run.stdout.txt'); closeout = read('ci2-closeout.stdout.txt')
head = '09d459149c23c79d717abb2ff727065b4de3d08a'
source = '9ef2db5b0106c7f92520d18015562c85faf64fc2'
assert run['databaseId'] == 38583535629 and closeout['databaseId'] == 38583533579
for item in (run, closeout):
    assert item['headSha'] == head and item['status'] == 'completed' and item['conclusion'] == 'success'
assert len(run['jobs']) == 5 and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in run['jobs'])
job, = [j for j in run['jobs'] if j['databaseId'] == 115919372298 and j['name'] == 'fixtures_self_test']
command = 'PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py'
step, = [s for s in job['steps'] if s['name'] == 'Run ' + command]
assert step['status'] == 'completed' and step['conclusion'] == 'success'
log_bytes = (E / 'ci2-job-log.stdout.txt').read_bytes(); lines = log_bytes.decode().splitlines()
receipts = [json.loads(m.group(1)) for line in lines if (m := re.search(r'Z MAINTENANCE_CHECKOUT_RECEIPT=(\{.*\})$', line))]
assert len(receipts) == 1
checkout = receipts[0]['checkout_sha']; assert re.fullmatch('[0-9a-f]{40}', checkout)
parents = git('rev-list', '--parents', '-n', '1', checkout).split()[1:]
assert head in parents and 'fcd0584146fd836df0080292cc2cf10180bb9f31' in parents
paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/convergent_review.py', 'tools/README.md', 'CHANGELOG.md', '.github/workflows/compliance.yml']
bindings = {}
for path in paths:
    actual, expected = blob(checkout, path), blob(source, path)
    assert actual == expected and git('rev-parse', checkout + ':' + path) == git('rev-parse', source + ':' + path)
    bindings[path] = {'sha256': digest(actual), 'git_blob': git('rev-parse', checkout + ':' + path)}
for path, expected in receipts[0]['source_sha256'].items():
    assert digest(blob(checkout, path)) == expected
workflow = yaml.safe_load(blob(checkout, '.github/workflows/compliance.yml'))
job_config = workflow['jobs']['fixtures_self_test']; run_step, = [s for s in job_config['steps'] if s.get('run') == command]
assert not job_config.get('continue-on-error', False) and not run_step.get('continue-on-error', False)
observed = []
for line in lines:
    fields = line.split('\t', 2)
    if len(fields) == 3 and fields[1] == 'Run ' + command and (m := re.search(r'Z PASS (\S+)$', fields[2])):
        observed.append(m.group(1))
old = [r['case'] for r in read('../118/api-interface.json')['current_cases']]
new = [shlex.split(v['command'])[-1] for v in json.loads(pathlib.Path('.agent/contracts/119.json').read_text())['verification']]
assert len(old) == 20 and len(new) == 6 and observed == old + new
assert all(r['actual_exit'] == 0 for r in read('ci2-fetch-results.json'))
assert not git('diff', '--name-only', source, checkout, '--', 'tools', 'schema', '.agent/evidence/115', '.agent/evidence/116', '.agent/evidence/117', '.agent/evidence/118')
result = {'role': 'Root', 'attempt': 2, 'passed': True, 'pr': 100, 'head': head, 'compliance_run': run['databaseId'], 'closeout_run': closeout['databaseId'], 'job': job['databaseId'], 'checkout': checkout, 'source_candidate': source, 'command': command, 'exit_code': 0, 'exit_basis': 'Successful hosted single-command Python step; pinned workflow has no continue-on-error at step or job.', 'old_cases': old, 'new_cases': new, 'all26_ordered': observed, 'source_bindings': bindings, 'raw_log': str(E / 'ci2-job-log.stdout.txt'), 'raw_log_sha256': digest(log_bytes), 'fetch_results': str(E / 'ci2-fetch-results.json'), 'earlier_failure': str(E / 'ci1-failure.json'), 'boundary': 'Actual existing default26 CI only; no phase123 full controls-ready CI or comparative run claim.'}
(E / 'ci2-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS hosted default26: historical20 + new119six; checkout/source equivalence and successful step verified')
