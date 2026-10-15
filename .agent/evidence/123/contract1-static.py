"""Static proposal checks only; never import or execute acceptance/Source APIs."""
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path.cwd()
contract = json.loads(Path('.agent/contracts/123.json').read_text())
for path in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    schema = json.loads(Path(path).read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(contract)
    print('STATIC schema valid: ' + path)
assert contract['status'] == 'proposed'
assert not any(contract['approvals'][key] for key in ('validator_mode_a', 'evaluator_contract_review'))
features = json.loads(Path('.agent/feature_list_018.json').read_text())['features']
feature, = [row for row in features if row['id'] == '123']
commands = [row['command'] for row in contract['verification']]
assert commands[:5] == feature['acceptance_tests']
assert contract['estimated_lines'] == feature['estimated_lines'] == 1200
assert contract['budget']['product'] == feature['budget_categories']['product'] == 300
assert contract['budget']['independent_tests'] == feature['budget_categories']['tests'] == 350
assert contract['budget']['process'] == feature['budget_categories']['process'] == 550
for key in ('spec_ref', 'dod_ref'):
    assert Path(contract[key]).is_file(), key
for row in contract['scope']['files_modify']:
    assert Path(row['path']).is_file(), row['path']
prerequisite = json.loads(Path('.agent/evidence/123/source-prerequisite.json').read_text())
rows = prerequisite['adjacent_prior_feature_evidence']
assert len(rows) == prerequisite['adjacent_count'] == 28
for row in rows:
    data = subprocess.check_output(['git', 'show', row['revision'] + ':' + row['path']])
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    entry = subprocess.check_output(['git', 'ls-tree', row['revision'], '--', row['path']], text=True).split()
    assert entry[:3] == [row['git_mode'], 'blob', row['git_blob']]
    assert Path(row['path']).read_bytes() == data
for path, expected in {
    'tools/workflow_assurance.py': 'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6',
    'tools/test_workflow_assurance.py': '800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'
}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
state = json.loads(Path('.agent/run_state.json').read_text())
assert state['current_feature'] == '123'
assert state['circuit_breaker']['123-contract'] == {'attempts': 1, 'limit': 3, 'status': 'prepared'}
assert state['scope_budget']['total_lines_changed'] == 4303
assert contract['budget']['measurement_base'] == prerequisite['merge']
print('STATIC acceptance references, budgets, existing paths and exact28 adjacent blobs/modes valid')
print('STATIC original Source/test digests and Root-owned prepared state preserved')
print('No acceptance, API, bank, compliance or CI command executed')
