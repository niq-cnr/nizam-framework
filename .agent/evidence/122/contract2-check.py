"""Static contract2 type/interface correction; no behavior execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

base = 'aea3c99f9635d7dec48f3323f777c19df1d39a1f'
path = Path('.agent/contracts/122.json')
c = json.loads(path.read_text())
for schema in ('.nizam/schema/contract.schema.json', 'schema/contract.schema.json'):
    jsonschema.Draft202012Validator(json.loads(Path(schema).read_text())).validate(c)
f = next(row for row in json.loads(Path('.agent/feature_list_018.json').read_text())['features'] if row['id'] == '122')
assert [row['command'] for row in c['verification']] == f['acceptance_tests'] and len(c['verification']) == 4
assert c['status'] == 'proposed' and c['approvals'] == {'validator_mode_a': False, 'evaluator_contract_review': False, 'revisions': 1}
assert c['estimated_lines'] == 950 and len(path.read_text().splitlines()) == 71
original = json.loads(subprocess.run(['git', 'show', base + ':stray'], capture_output=True).stdout or b'null') if False else json.loads(subprocess.run(['git', 'show', base + ':' + str(path)], check=True, capture_output=True).stdout)
assert c['budget'] == original['budget']
original['api']['continuity'] = c['api']['continuity']
original['verification'][3]['acceptance_test'] = c['verification'][3]['acceptance_test']
original['approvals']['revisions'] = 1
assert original == c, 'Only approved narrow clauses and revision count change'
protected = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/run_state.json', '.agent/feature_list_018.json', '.agent/product_spec_018.md', 'methodology/03_circuit_breaker.md']
for item in protected:
    assert Path(item).read_bytes() == subprocess.run(['git', 'show', base + ':' + item], check=True, capture_output=True).stdout, item
print(json.dumps({'static_checks': 'passed', 'schemas': ['installed', 'authored'], 'exact_commands': 4, 'protected_unchanged': protected, 'contract_lines': 71, 'proposal_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'behavior_executed': False}, indent=2))
