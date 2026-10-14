"""Root capture of existing independent evidence; lifecycle advances separately."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

import jsonschema

E = Path('.agent/evidence/127')
SOURCE = '88996ee9405f9467ff2debd6e3115b34d064019a'
TEST_SHA = '3628f1b2b833a0f504cced79252391ff213bd75197dd2d5261494fbb646eb12e'
CONTRACT_SHA = 'b221434834b68dd0273a0bdd0f6f8c0988bee0165f9c31255f4e33b150191cb7'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate(path):
    value = read(path)
    assert value['final_verdict']['approved'] is True, path
    assert all(value[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
    return value


contract_path = '.agent/contracts/127.json'
contract = read(contract_path)
assert contract['status'] == 'approved' and sha(contract_path) == CONTRACT_SHA
gate_paths = ['.agent/validator/127-mode-a-2.json', '.agent/qa/127-contract-review-2.json',
              '.agent/validator/127-bundle-review-2.json',
              '.agent/validator/127-executable-bundle-review.json',
              '.agent/validator/127-mode-b.json', '.agent/qa/127.json',
              str(E / 'public-projection-review3.json')]
gates = {path: gate(path) for path in gate_paths}
qa = gates['.agent/qa/127.json']
mode_b = gates['.agent/validator/127-mode-b.json']
jsonschema.validate(qa, read('.nizam/schema/qa_verdict.schema.json'))
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == 14
assert qa['evaluator']['session'] == '/root/runtime_qa127'
assert qa['source_revision'] == mode_b['source_candidate'] == SOURCE
assert qa['contract_sha256'] == mode_b['contract_sha256'] == CONTRACT_SHA
assert qa['test_sha256'] == mode_b['test_sha256'] == sha('tools/test_runtime_session.py') == TEST_SHA
assert qa['api_sha256'] == mode_b['API_sha256'] == sha(E / 'runtime-api127.json')
prior = read('.agent/evidence/126/ci-c3-receipt.json')
expected = [x['command'] for x in prior['commands']] + [x['command'] for x in contract['verification']]
assert expected == read(E / 'acceptance1-obligations.json')['fourteen_commands']
assert [x['command'] for x in qa['checks']] == expected
manifest = read(E / 'final-qa/evidence-manifest.json')
for path, digest in manifest.items():
    assert sha(path) == digest, path
evidence = set(qa['evidence_files']) | set(manifest) | set(gate_paths)
baseline = read(qa['identity_before'])
immutable_keys = ('files', 'installed_inventory', 'runtime_schema_tools_fixture_inventory', 'run_state_sha256')


def identity(path):
    value = read(path)
    assert value['source_revision'] == SOURCE
    for key in immutable_keys:
        assert value[key] == baseline[key], (path, key)
    evidence.add(path)


for key in ('installed_inventory', 'runtime_schema_tools_fixture_inventory'):
    for path, digest in baseline[key].items():
        assert sha(path) == digest, path
for item in baseline['files']:
    assert sha(item['path']) == item['sha256'], item['path']
    content = subprocess.check_output(['git', 'show', SOURCE + ':' + item['path']])
    assert hashlib.sha256(content).hexdigest() == item['sha256']
identity(qa['identity_final'])
extra = qa['adversarial']
assert extra['performed'] is True and extra['count'] == 1 and extra['exit_code'] == 0
extra_record = read(extra['result_ref'])
checks = qa['checks'] + qa['repository_checks']
assert [x['command'] for x in qa['repository_checks']] == [
    'PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh',
    'PYTHONDONTWRITEBYTECODE=1 bash tools/fixtures_self_test.sh']
checks += [{'command': extra_record['command'], 'exit_code': extra['exit_code'], 'evidence': extra['result_ref']}]
assert len(checks) == 17
for check in checks:
    record = read(check['evidence'])
    assert record['command'] == check['command'] and record['exit_code'] == check['exit_code'] == 0
    assert record['source_revision'] == SOURCE and record['test_sha256'] == TEST_SHA
    assert record['timed_out'] is False and record['preserved_inputs'] is True
    assert record['environment_override']['PYTHONDONTWRITEBYTECODE'] == '1'
    for stream in ('stdout', 'stderr'):
        assert sha(record[stream]) == record[stream + '_sha256'], record[stream]
        evidence.add(record[stream])
    assert Path(record['stdout']).stat().st_size > 0
    identity(record['identity_before'])
    identity(record['identity_after'])
    evidence.update((check['evidence'], record['runtime_ref']))
observations = read(extra['observations_ref'])
assert observations['passed'] is True and observations['cleanup_live_registered_pids'] == []
assert read(E / 'final-qa/post-process-scan.json')['live_candidate_runtime_pids'] == []
assert read(E / 'final-qa/verdict-validation.json')['artifact_sha256'] == sha('.agent/qa/127.json')
seal_path = E / 'semantic1-test-seal.json'
seal = read(seal_path)
assert seal['source_candidate'] == SOURCE and seal['test']['sha256'] == TEST_SHA
pins = set()


def git_pins(value):
    if isinstance(value, dict):
        if {'path', 'revision', 'sha256'} <= value.keys():
            raw = subprocess.check_output(['git', 'show', value['revision'] + ':' + value['path']])
            assert hashlib.sha256(raw).hexdigest() == value['sha256'], value['path']
            pins.add((value['revision'], value['path']))
        for child in value.values():
            git_pins(child)
    elif isinstance(value, list):
        for child in value:
            git_pins(child)


git_pins(seal)
ci = read(E / 'ci-c1-receipt.json')
assert ci['source'] == SOURCE and [x['command'] for x in ci['commands']] == expected
assert len(ci['commands']) == 14 and all(x['actual_exit'] == 0 for x in ci['commands'])
for path, digest in ci['source_sha256'].items():
    assert sha(path) == digest, path
    assert subprocess.check_output(['git', 'show', SOURCE + ':' + path]) == Path(path).read_bytes()
verify = ['python3', '.github/scripts/verify_self_governance.py']
run = subprocess.run(verify, capture_output=True, text=True,
                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=30)
(E / 'capture-installed.stdout.txt').write_text(run.stdout)
(E / 'capture-installed.stderr.txt').write_text(run.stderr)
assert run.returncode == 0
evidence.update((str(seal_path), str(E / 'ci-c1-receipt.json'), ci['raw_log'], ci['run_record'],
                 str(E / 'capture-installed.stdout.txt'), str(E / 'capture-installed.stderr.txt')))
assert all(Path(path).is_file() for path in evidence)
result = {'feature': '127', 'owner': '/root', 'passed': True,
          'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'capture_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
          'revision': SOURCE, 'test_revision': ci['test_revision'], 'checks_captured': 14,
          'repository_checks_captured': 2, 'adversarial_captured': True,
          'qa_ref': '.agent/qa/127.json', 'qa_sha256': sha('.agent/qa/127.json'),
          'mode_b_ref': '.agent/validator/127-mode-b.json',
          'bundle_ref': str(seal_path), 'bundle_sha256': sha(seal_path), 'git_pins_verified': len(pins),
          'strict_gate_sha256': {path: sha(path) for path in gate_paths},
          'source_sha256': ci['source_sha256'], 'ci_ref': str(E / 'ci-c1-receipt.json'),
          'ci_run': ci['run'], 'ci_job': ci['job'], 'ci_checkout': ci['checkout'],
          'installed_fidelity': {'argv': verify, 'actual_exit': run.returncode, 'release': 'v1.5.0',
                                 'released_files': 238, 'inventory_including_provenance': 239},
          'evidence_sha256': {path: sha(path) for path in sorted(evidence)},
          'boundary': 'Partial stub scope only. Lifecycle and measured budget advance separately; no full adapter, SBCL runtime, fresh acceptance or comparative claim.'}
(E / 'evidence-capture.json').write_text(json.dumps(result, indent=2) + '\n')
print('CAPTURE PASS: fourteen exact runtime commands, two repository checks, one own adversarial check, strict independent gates, capable CI, immutable evidence and installed fidelity')
