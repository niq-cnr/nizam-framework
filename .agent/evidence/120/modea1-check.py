import ast,hashlib,json,subprocess,copy
from pathlib import Path
import jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text()); c=load('.agent/contracts/120.json')
assert hashlib.sha256(P('.agent/contracts/120.json').read_bytes()).hexdigest()=='620130f2e63ff117192d83ac9dda2f51afc6aa87d4d0e54067bd60373626a2a8'
jsonschema.validate(c,load('.nizam/schema/contract.schema.json'))
f=next(x for x in load('.agent/feature_list_018.json')['features'] if x['id']=='120');assert len(c['verification'])==11 and [x['command'] for x in c['verification']]==f['acceptance_tests']
assert c['estimated_lines']==2750==sum(c['budget'][k] for k in ('product','independent_tests','process')) and c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360
s=load('.agent/run_state.json');assert s['circuit_breaker']['120-mode-a']=={'attempts':1,'limit':3}
rs=load('.nizam/schema/run_state.schema.json');jsonschema.validate(s,rs)
event={'at':'2026-10-14T15:40:00+00:00','event':'wa-receipt-transition','operation_id':'modea-proof','feature_id':'120','stage':'qa-passed','candidate_sha256':'a'*64,'receipt_sha256':'b'*64}
proposed=copy.deepcopy(s);proposed['history'].append(event)
errors=list(jsonschema.Draft202012Validator(rs).iter_errors(proposed));assert any(e.validator=='required' and 'detail' in e.message for e in errors)
print('ISSUE120-A1 installed run_state rejects exact contracted transition event:',[e.message for e in errors])
print('CONTRACT_EVENT',json.dumps(event,sort_keys=True))
approved=json.loads(subprocess.check_output(['git','show','9ef2db5:.agent/contracts/119.json']));capture=json.loads(subprocess.check_output(['git','show','92fecd8:.agent/evidence/119/evidence-capture.json']))
assert approved['status']=='approved' and approved['approvals']['validator_mode_a'] is True and approved['approvals']['evaluator_contract_review'] is True
assert capture['passed'] is True and capture['actual_exit']==0
for name,artifact in [('approved-contract',approved),('evidence-capture',capture)]:
 missing=[key for key in ('final_verdict','issues','missing_acceptance_coverage','unsupported_claims') if key not in artifact]
 assert len(missing)==4;print('ISSUE120-A2 actual',name,'missing universal AGF fields:',missing)
print('APPLICABLE_SCHEMAS',[p for p in load('.nizam/NIZAM.json')['schemas'] if any(k in p for k in ('contract','qa_verdict','capture'))])
functions={n.name:ast.unparse(n.args) for n in ast.parse(P('tools/workflow_assurance.py').read_text()).body if isinstance(n,ast.FunctionDef)}
for name in ('validate_identity','compare_identity','relative_path','regular_file','verify_record_update','assess_repository'):
 print('EXISTING_HELPER',name,functions[name])
print('PASS proposal schema/hash/exact11/budget/attempt; two bounded contract contradictions confirmed without Source or absentAPI execution')
