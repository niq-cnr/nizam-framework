"""Proposal identity/schema/delta checks only; no product or test execution."""
import copy, hashlib, json, subprocess
from pathlib import Path
import jsonschema
def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout
def read(path):
    return json.loads(Path(path).read_bytes())
revision = git('rev-parse', 'HEAD').decode().strip()
assert revision == 'af1dd974bb6c7a89ad4aace93a2658edd6ec5abc'
oldref = 'ca3f3917c1d6caf28748877cb47514d0302a4534'
newref = '757b0c61c1f586307d8fd7adfc5160718ce7a374'
data = git('show', newref + ':.agent/contracts/122.json')
assert hashlib.sha256(data).hexdigest() == '829aab4a4ba65966c3fa1e01e0bc689f60d2ae718f70192f448c7456e8b0c160'
assert data == Path('.agent/contracts/122.json').read_bytes()
old = json.loads(git('show', oldref + ':.agent/contracts/122.json')); new = json.loads(data)
for schema in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(read(schema)).validate(new)
    print('VALID', schema)
normalized = copy.deepcopy(new)
normalized['api']['continuity'] = old['api']['continuity']
normalized['verification'][3]['acceptance_test'] = old['verification'][3]['acceptance_test']
normalized['approvals']['revisions'] = old['approvals']['revisions']
assert normalized == old
print('EXACT_DELTA api.continuity, verification[3].acceptance_test, approvals.revisions only')
state = read('.agent/run_state.json')
assert state['current_feature'] == '122' and state['status'] == 'in_progress'
for key in ('122-contract', '122-mode-a', '122-contract-review'):
    assert state['circuit_breaker'][key]['attempts'] == 2 and state['circuit_breaker'][key]['limit'] == 3
    print(key, json.dumps(state['circuit_breaker'][key]))
for path in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py'):
    assert git('show', oldref + ':' + path) == Path(path).read_bytes()
    print('UNCHANGED_BYTES', path, hashlib.sha256(Path(path).read_bytes()).hexdigest())
print('CONTINUITY', new['api']['continuity'])
for path in ('.agent/contracts/122.json', 'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/run_state.json'):
    print('PIN', revision, git('ls-tree', 'HEAD', '--', path).decode().strip(), hashlib.sha256(Path(path).read_bytes()).hexdigest())
print('STATIC_COMPLETE; no Source/test behavior; no inventory count executed or claimed')
