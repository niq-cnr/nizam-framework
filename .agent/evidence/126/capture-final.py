"""Root evidence-capture gate; lifecycle changes happen only after this passes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

import jsonschema

E = Path('.agent/evidence/126')
SOURCE = 'd965c2ca9dd845f9a094153c7328d90a5398d06f'
TEST = 'd89d79fcdb9c5b3d3098f5ed8162b11467bb3284'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate(path):
    value = read(path)
    assert value['final_verdict']['approved'] is True, path
    assert all(value[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
    return value


contract_path = '.agent/contracts/126.json'
contract = read(contract_path)
assert contract['status'] == 'approved'
assert sha(contract_path) == '7eed25daca89c13a548976a213ddba6e6837acaee90511f0deff152a60697778'
bundle = read(E / 'test-seal-b3.json')
bundle_review = gate('.agent/validator/126-bundle-review-2.json')
mode_b = gate('.agent/validator/126-mode-b-2.json')
gate('.agent/validator/126-mode-a-2.json')
gate('.agent/qa/126-contract-review-2.json')
qa = gate('.agent/qa/126.json')
jsonschema.validate(qa, read('.nizam/schema/qa_verdict.schema.json'))
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == 9
assert qa['evaluator']['session'] == '/root/runtime_qa126'
assert qa['source_revision'] == SOURCE and qa['test_revision'] == TEST
assert qa['source_sha256'] == sha('tools/runtime_session.py')
assert mode_b['source_candidate'] == SOURCE and mode_b['source_sha256'] == qa['source_sha256']
assert mode_b['contract_sha256'] == qa['contract_sha256'] == sha(contract_path)
assert mode_b['bundle_sha256'] == sha(E / 'test-seal-b3.json')
assert qa['test_sha256'] == bundle['test']['sha256'] == sha('tools/test_runtime_session.py')
assert mode_b['test_sha256'] == bundle_review['test_sha256'] == qa['test_sha256']
assert [c['command'] for c in qa['checks']] == [c['command'] for c in contract['verification']]
evidence = set(qa['evidence_files'])
for check in qa['checks']:
    assert check['exit_code'] == 0
    assert sha(check['evidence']) == check['evidence_sha256']
    record = read(check['evidence'])
    assert record['command'] == check['command'] and record['exit_code'] == 0
    assert record['source_revision'] == SOURCE and record['test_revision'] == TEST
    for stream in ('stdout', 'stderr'):
        assert sha(check[stream]) == check[stream + '_sha256']
        evidence.add(check[stream])
    assert Path(check['stdout']).stat().st_size > 0
    assert check['environment_override']['PYTHONDONTWRITEBYTECODE'] == '1'
    evidence.update((check['runtime_ref'], check['identity_ref']))
extra = qa['adversarial']
assert extra['performed'] is True and extra['count'] == 1 and extra['exit_code'] == 0
extra_result = read(extra['result_ref'])
assert extra_result['actual_exit_code'] == 0
for stream in ('stdout', 'stderr'):
    assert sha(extra_result[stream]) == extra_result[stream + '_sha256']
    evidence.add(extra_result[stream])
evidence.update((extra['evidence'], extra['result_ref'], extra['observations_ref']))
for item in read(E / 'final-qa/evidence-manifest.json')['files']:
    assert sha(item['path']) == item['sha256'], item['path']
    assert Path(item['path']).stat().st_size == item['bytes']
for item in [bundle['test'], bundle['api'], bundle['obligation_projection'], *bundle['normative_inputs']]:
    assert sha(item['path']) == item['sha256'], item['path']
ci = read(E / 'ci-c3-receipt.json')
assert ci['source'] == SOURCE and ci['test_revision'] == TEST
assert len(ci['commands']) == 9 and all(c['actual_exit'] == 0 for c in ci['commands'])
assert sorted(c['command'] for c in ci['commands']) == sorted(c['command'] for c in qa['checks'])
for path, digest in ci['source_sha256'].items():
    assert sha(path) == digest, path
    revision = TEST if path == 'tools/test_runtime_session.py' else SOURCE
    assert subprocess.check_output(['git', 'show', revision + ':' + path]) == Path(path).read_bytes()
verify = ['python3', '.github/scripts/verify_self_governance.py']
run = subprocess.run(verify, capture_output=True, text=True,
                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=30)
(E / 'capture-installed.stdout.txt').write_text(run.stdout)
(E / 'capture-installed.stderr.txt').write_text(run.stderr)
assert run.returncode == 0
evidence.update((str(E / 'capture-installed.stdout.txt'), str(E / 'capture-installed.stderr.txt'),
                str(E / 'ci-c3-receipt.json'), ci['raw_log'], ci['run_record']))
assert all(Path(path).is_file() for path in evidence)
result = {'feature': '126', 'owner': '/root', 'passed': True,
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'capture_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'revision': SOURCE, 'test_revision': TEST, 'checks_captured': 9, 'adversarial_captured': True,
    'qa_ref': '.agent/qa/126.json', 'qa_sha256': sha('.agent/qa/126.json'),
    'mode_b_ref': '.agent/validator/126-mode-b-2.json',
    'mode_b_sha256': sha('.agent/validator/126-mode-b-2.json'),
    'bundle_ref': str(E / 'test-seal-b3.json'), 'bundle_sha256': sha(E / 'test-seal-b3.json'),
    'bundle_review_ref': '.agent/validator/126-bundle-review-2.json',
    'source_sha256': ci['source_sha256'], 'ci_ref': str(E / 'ci-c3-receipt.json'),
    'ci_run': ci['run'], 'ci_job': ci['job'], 'ci_checkout': ci['checkout'],
    'installed_fidelity': {'argv': verify, 'actual_exit': run.returncode,
                           'release': 'v1.5.0', 'files': 238},
    'evidence_sha256': {path: sha(path) for path in sorted(evidence)},
    'boundary': 'Captured partial stub development scope only; no full adapter/SBCL/fresh acceptance or comparative claim. Lifecycle and budget advance separately.'}
(E / 'evidence-capture.json').write_text(json.dumps(result, indent=2) + '\n')
print('CAPTURE PASS: nine exact commands, own adversarial check, strict independent gates, source-bound capable CI and installed fidelity')
