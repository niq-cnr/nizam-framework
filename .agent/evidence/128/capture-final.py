"""Root evidence transport/identity gate; lifecycle advances separately."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import jsonschema

E = Path('.agent/evidence/128')
Q = E / 'qa1'
CONTRACT = '8a9cb74fa0b10e8beb312a950d976697aca227c061f7ed03ced44fa7b031be89'
RUNNER = '005ed223ab121c3a1eda7f806ac6acc1e7076e795bf9b8ee75a394ca37d5e534'
SOURCE = '62a83e65c653ba4df69eb784396724a684ffdf79'

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

gate_paths = ['.agent/validator/128-mode-a.json', '.agent/qa/128-contract-review.json',
              '.agent/qa/128-bundle-review.json', '.agent/validator/128-mode-b.json', '.agent/qa/128.json']
for path in gate_paths:
    verdict = read(path)
    assert verdict['final_verdict']['approved'] is True, path
    assert all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
contract = read('.agent/contracts/128.json')
assert contract['status'] == 'approved' and sha('.agent/contracts/128.json') == CONTRACT
qa = read('.agent/qa/128.json')
jsonschema.validate(qa, read('.nizam/schema/qa_verdict.schema.json'))
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == 3
assert qa['approved_contract_sha256'] == CONTRACT and qa['runner_sha256'] == RUNNER
assert qa['source_docs_revision'] == SOURCE and sha('tools/test_runtime_session.py') == RUNNER
expected = [v['command'] for v in contract['verification']]
assert [v['command'] for v in qa['checks']] == expected
manifest = read(Q / 'manifest.json')
evidence = set(gate_paths) | set(qa['evidence_files'])
for path, pin in manifest['files'].items():
    assert sha(path) == pin['sha256'], path
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD:' + path], text=True).strip() == pin['git_blob'], path
    evidence.add(path)
before, after = read(Q / 'identity-before.json'), read(Q / 'identity-after.json')
assert before['revision'] == after['revision'] == qa['exercised_revision']
assert before['protected_sha256'] == after['protected_sha256']
assert before['installed_inventory_count'] == after['installed_inventory_count'] == 239
for path, digest in before['protected_sha256'].items():
    if path.startswith('.nizam/'):
        assert sha(path) == digest, path
assert read(Q / 'environment.json')['effective']['PYTHONDONTWRITEBYTECODE'] == '1'
for check in qa['checks']:
    record = read(check['evidence'])
    assert record['command'] == check['command'] and record['actual_exit'] == check['exit_code'] == 0
    assert record['argv'] == ['bash', '-c', check['command']]
    assert record['exercised_revision'] == before['revision']
    assert Path(record['stdout']).stat().st_size > 0
    evidence.update((record['stdout'], record['stderr']))
record = read(Q / 'core-ready.result.json')
lines = Path(record['stdout']).read_text().splitlines()
leaves = [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('CORE_LEAF ')]
assert len(leaves) == 14 and [x['argv'][2:] for x in leaves] == contract['leaf_argv']
assert all(x['exit'] == 0 and x['proof'] is True and x['cleanup'] is True and x['event'] is None for x in leaves)
assert lines[-1] == 'PASS core-ready'
extra_path = qa['adversarial']['evidence']
extra = read(extra_path)
assert qa['adversarial']['performed'] is True and extra['passed'] is True
assert extra['actual_exit'] == extra['expected_exit'] == 2 and extra['stdout'] == ''
assert extra['expected_reason'] in extra['stderr']
assert extra['argv'] == ['python3', 'tools/test_runtime_session.py', '--check', 'core-ready', '--require-sbcl']
summary = read(Q / 'execution-summary.json')
assert summary['contract_commands_run'] == summary['contract_commands_passed'] == 3
assert all(summary[k] is True for k in ('exactly_one_extra', 'adversarial_passed', 'protected_identities_unchanged', 'all_receipt_markers_valid'))
for path, key in [(E / 'author1-test-seal.json', 'evidence_sha256'), (E / 'bundle1-test-seal.json', 'evidence_sha256')]:
    seal = read(path)
    for item, digest in seal[key].items():
        assert sha(item) == digest, item
        evidence.add(item)
    evidence.add(str(path))
ci_path = E / 'ci-new-runner-2-receipt.json'
ci = read(ci_path)
assert ci['run'] == 38569054719 and ci['source'] == SOURCE and ci['test_revision'] == '441567ef05c3eb68558c6aeb679aa94b0a1a3baa'
prior = read('.agent/evidence/127/ci-c1-receipt.json')
assert [x['command'] for x in ci['commands']] == [x['command'] for x in prior['commands']]
assert len(ci['commands']) == 14 and all(x['actual_exit'] == 0 for x in ci['commands'])
for path, digest in ci['source_sha256'].items():
    assert sha(path) == digest == before['protected_sha256'][path], path
    assert subprocess.check_output(['git', 'show', SOURCE + ':' + path]) == Path(path).read_bytes(), path
evidence.update((str(ci_path), ci['raw_log'], ci['run_record'], extra_path))
verify = ['python3', '.github/scripts/verify_self_governance.py']
run = subprocess.run(verify, capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=30)
(E / 'capture-installed.stdout.txt').write_text(run.stdout)
(E / 'capture-installed.stderr.txt').write_text(run.stderr)
assert run.returncode == 0
evidence.update((str(E / 'capture-installed.stdout.txt'), str(E / 'capture-installed.stderr.txt')))
assert all(Path(path).is_file() for path in evidence)
result = {'feature': '128', 'owner': '/root', 'passed': True,
          'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'capture_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
          'source_docs': SOURCE, 'runner_sha256': RUNNER, 'contract_sha256': CONTRACT,
          'qa_ref': '.agent/qa/128.json', 'checks_captured': 3, 'aggregate_leaves': 14,
          'adversarial_captured': True, 'adversarial_actual_exit': 2,
          'strict_gate_sha256': {p: sha(p) for p in gate_paths},
          'ci_ref': str(ci_path), 'ci_run': ci['run'], 'ci_checkout': ci['checkout'],
          'installed_fidelity': {'argv': verify, 'actual_exit': run.returncode, 'release': 'v1.5.0', 'inventory': 239},
          'evidence_sha256': {p: sha(p) for p in sorted(evidence)},
          'boundary': 'Bounded partial stub core only. Hosted fourteen leaves and fresh QA core-ready are separate executions. No full adapter, SBCL runtime, fresh020, final131 or comparative claim. Lifecycle and measured budget advance separately.'}
(E / 'evidence-capture.json').write_text(json.dumps(result, indent=2) + '\n')
print('CAPTURE PASS: exact3 QA, actual14 aggregate leaves, own negative boundary, strict gates, new-runner hosted14, immutable proof and installed fidelity')
