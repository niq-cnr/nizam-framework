import json,hashlib,subprocess,ast
from pathlib import Path
import jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());c=load('.agent/contracts/119.json')
assert hashlib.sha256(P('.agent/contracts/119.json').read_bytes()).hexdigest()=='9de754f810676e2f154aca96cb28c75236ac650ab78a0e06f53f97d66e885226'
jsonschema.validate(c,load('.nizam/schema/contract.schema.json'))
f=next(x for x in load('.agent/feature_list_018.json')['features'] if x['id']=='119')
assert [x['command'] for x in c['verification']]==f['acceptance_tests'] and len(c['verification'])==6
assert c['estimated_lines']==f['estimated_lines']==sum(c['budget'][k] for k in ('product','independent_tests','process'))==1000
assert c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360 and c['budget']['measurement_base']=='fcd0584146fd836df0080292cc2cf10180bb9f31'
assert c['status']=='proposed' and all(c['approvals'][k] is False for k in ('validator_mode_a','evaluator_contract_review'))
assert load('.agent/evidence/phase018-preflight/activation-result.json')['passed']
s=load('.agent/run_state.json');assert s['circuit_breaker']['119-mode-a']=={'attempts':1,'limit':3};assert s['phase_016_scope_budget_final']['total_lines_changed']==5179 and s['phase_017_scope_budget_final']['total_lines_changed']==5203
assert not subprocess.check_output(['git','diff','--name-only','fcd0584','HEAD','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/convergent_review.py','.nizam/'])
function=next(n for n in ast.parse(P('tools/convergent_review.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate_ledger');assert [x.arg for x in function.args.args]==['ledger','ctx']
print('PASS installed contract schema/hash; exact6 ATs; activation/attempt;1000 and7200/9360; preserved0165179/0175203; no product/tests/installed changes; actual authority API matches')
for p in ('.agent/contracts/119.json','.agent/feature_list_018.json','.agent/evidence/phase018-preflight/activation-result.json','tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/convergent_review.py','.nizam/NIZAM.json'):
 print(p,hashlib.sha256(P(p).read_bytes()).hexdigest())
