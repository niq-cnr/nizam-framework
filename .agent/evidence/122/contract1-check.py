"""Static Generator proposal checks only; no acceptance/API execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path.cwd()
base = 'f1dcb482a01e2bf1d8831f3dacccc04ce63b71de'
contract_path = '.agent/contracts/122.json'
contract = json.loads((root / contract_path).read_text())
for schema_path in ('.nizam/schema/contract.schema.json', 'schema/contract.schema.json'):
    jsonschema.Draft202012Validator(json.loads((root / schema_path).read_text())).validate(contract)
assert contract['status'] == 'proposed' and not any(contract['approvals'][key] for key in ('validator_mode_a', 'evaluator_contract_review'))
assert contract['estimated_lines'] == 950
assert sum(contract['budget'][key] for key in ('source_and_docs', 'independent_tests', 'process')) == 950
assert contract['budget']['measurement_base'] == '3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03'
assert contract['budget']['prior_actual']['total'] == 722 + 1397 + 1245 == 3364
feature = next(value for value in json.loads((root / '.agent/feature_list_018.json').read_text())['features'] if value['id'] == '122')
assert [entry['command'] for entry in contract['verification']] == feature['acceptance_tests']
assert len(contract['verification']) == 4
prerequisite = json.loads((root / '.agent/evidence/122/source-prerequisite.json').read_text())
protected = []
for path in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/run_state.json', '.agent/feature_list_018.json', '.agent/product_spec_018.md', 'methodology/03_circuit_breaker.md'):
    data = (root / path).read_bytes()
    original = subprocess.run(['git', 'show', base + ':' + path], check=True, capture_output=True).stdout
    assert data == original, path
    if path.endswith('.py'):
        ast.parse(data)
        assert hashlib.sha256(data).hexdigest() == prerequisite['bindings'][path]['sha256']
    protected.append(path)
changed = subprocess.run(['git', 'diff', '--name-only', base], check=True, capture_output=True, text=True).stdout.splitlines()
untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], check=True, capture_output=True, text=True).stdout.splitlines()
assert all(path == contract_path or path.startswith('.agent/evidence/122/contract1-') for path in changed + untracked), changed + untracked
assert len((root / contract_path).read_text().splitlines()) == 71
print(json.dumps({'static_proposal_checks': 'passed', 'schemas': ['installed', 'authored'], 'verification_commands': 4, 'contract_lines': 71, 'protected_unchanged': protected, 'api_or_acceptance_executed': False}, indent=2))
