"""Static pre-code evidence only; never imports or executes product/test modules."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

ROOT = Path.cwd()
PROPOSAL = 'ca3f3917c1d6caf28748877cb47514d0302a4534'
EXPECTED = '2755c628685458009fb763e1d985339cef87e37608cefabd346253fc69d5183f'
def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout
def read(path):
    return json.loads((ROOT / path).read_bytes())
def digest(data):
    return hashlib.sha256(data).hexdigest()

print('exercised_revision', git('rev-parse', 'HEAD').decode().strip())
assert git('rev-parse', 'HEAD').decode().strip() == '713b8e9b752a0ff7158e8a996ad5319df7b8aee6'
proposal = git('show', PROPOSAL + ':.agent/contracts/122.json')
assert digest(proposal) == EXPECTED
assert proposal == (ROOT / '.agent/contracts/122.json').read_bytes()
contract = json.loads(proposal)
for path in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(read(path)).validate(contract)
    print('contract_schema_valid', path)
state = read('.agent/run_state.json')
jsonschema.Draft202012Validator(read('schema/run_state.schema.json')).validate(state)
print('selected_state', json.dumps({k: state[k] for k in ('repository', 'current_phase', 'current_feature', 'status')}))
print('selected_counters', json.dumps({k:v for k,v in state['circuit_breaker'].items() if k.startswith('122-')}, sort_keys=True))
assert state['current_feature'] == '122' and state['status'] == 'in_progress'
assert state['circuit_breaker']['122-mode-a'] == dict(attempts=1, limit=3, status='dispatched')
features = read('.agent/feature_list_018.json')
feature = next(f for f in features['features'] if f['id'] == '122')
assert [v['command'] for v in contract['verification']] == feature['acceptance_tests']
assert contract['estimated_lines'] == feature['estimated_lines'] == 950
assert contract['budget']['phase_original'] == 7200 and contract['budget']['phase_ceiling'] == 9360
assert contract['approvals'] == dict(validator_mode_a=False, evaluator_contract_review=False, revisions=0)
source = (ROOT / 'tools/workflow_assurance.py').read_text()
tree = ast.parse(source)
update = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_record_update')
text = ast.get_source_segment(source, update)
assert "type(value) not in (dict, list) or parts == ('history',)" in text
assert "lanes = state.get('execution_lanes'); require(type(lanes) is list" in source
assert '/execution_lanes' in contract['api']['continuity']
print('STATIC_BLOCKER helper rejects owned list except history; contract allows execution_lanes list pointer')
print('live_execution_lanes_present', 'execution_lanes' in state)
for first, last in ((90, 105), (1094, 1101)):
    for number, line in enumerate(source.splitlines(), 1):
        if first <= number <= last:
            print(str(number) + ':' + line)
test_tree = ast.parse((ROOT / 'tools/test_workflow_assurance.py').read_bytes())
inventories = {}
for node in test_tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        try: inventories[node.targets[0].id] = ast.literal_eval(node.value)
        except (ValueError, TypeError): pass
assert sum(len(inventories[k]) for k in ('CASES', 'AGF_CASES', 'RECEIPT_CASES', 'LANE_CASES')) == 42
print('inherited_default_inventory', 42)
paths = ['.agent/contracts/122.json', '.agent/run_state.json', '.agent/product_spec_018.md',
         '.agent/feature_list_018.json', 'docs/planning/phase_018.yaml',
         'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py',
         'schema/contract.schema.json', '.nizam/schema/contract.schema.json',
         'schema/run_state.schema.json', 'schema/contract_review.schema.json',
         '.nizam/schema/contract_review.schema.json', '.nizam/standard/AGF.md',
         '.nizam/methodology/01_execution.md', '.nizam/methodology/03_circuit_breaker.md']
for path in paths:
    data = (ROOT / path).read_bytes()
    print('PIN', json.dumps(dict(path=path, revision=git('rev-parse','HEAD').decode().strip(),
        sha256=digest(data), git_entry=git('ls-tree','HEAD','--',path).decode().strip())))
print('STATIC_REVIEW_COMPLETE; proposal schema passes; substantive continuity finding requires rejection')
