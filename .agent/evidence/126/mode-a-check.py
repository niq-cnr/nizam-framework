"""Feature126 pre-code shape, identity and traceability checks only."""
import hashlib
import json
import subprocess
from pathlib import Path
import jsonschema

candidate = '9e6fe6daa46a625a2eb2561b5cc8acb202200120'
expected_hash = '4c9ba69d48fced7782bbe8b2a3dcaa0fe4431f78392cb2b943df4abf87698b02'
contract_path = Path('.agent/contracts/126.json')
contract = json.loads(contract_path.read_text())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == candidate
assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == expected_hash
schema = json.loads(Path('.nizam/schema/contract.schema.json').read_text())
jsonschema.Draft202012Validator(schema).validate(contract)
features = json.loads(Path('.agent/feature_list_016.json').read_text())
feature = next(f for f in features['features'] if f['id'] == '126')
assert features['phase_status'] == 'in_progress'
assert feature['status'] == 'in_progress' and feature['passes'] is False
assert contract['status'] == 'proposed'
assert contract['approvals']['validator_mode_a'] is False
assert contract['approvals']['evaluator_contract_review'] is False
assert len(contract['verification']) == 9
assert [v['command'] for v in contract['verification']] == feature['acceptance_tests']
assert contract['estimated_lines'] == feature['estimated_lines'] == 2900
assert sum(contract['budget'][k] for k in ('product', 'independent_tests', 'process')) == 2900
assert contract['budget']['phase_total'] == features['original_estimate_lines'] == 5650
assert contract['budget']['phase_ceiling'] == features['ceiling_130pct'] == 7345
assert set(item['path'] for item in contract['scope']['files_modify']) == {'tools/fixtures_self_test.sh', 'tools/README.md', 'CHANGELOG.md'}
for path in ('tools/runtime_session.py', 'tools/test_runtime_session.py', 'tools/fixtures/runtime_session/stub_runtime.py'):
    assert not Path(path).exists(), path
activation = json.loads(Path('.agent/evidence/phase016-preflight/activation-decision.json').read_text())
assert activation['selected_feature'] == '126' and activation['implementation_approved'] is False
for reference in json.loads(Path('.agent/evidence/126/proposal-inputs.json').read_text())['references']:
    actual = subprocess.check_output(['git', 'hash-object', reference['path']], text=True).strip()
    assert actual == reference['blob'], reference['path']
print(json.dumps({'result': 'pass', 'candidate': candidate, 'contract_sha256': expected_hash, 'checks': ['installed contract schema', 'activated phase and pending implementation', 'exact nine-command acceptance mapping', 'original budget and estimate', 'bounded modified-file allowlist', 'no product or acceptance runner exists', 'all proposal input blobs still match'], 'behavioral_acceptance': 'not run; pre-code review only'}, indent=2))
