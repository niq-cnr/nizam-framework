import json,hashlib,subprocess,copy,ast
from pathlib import Path
import jsonschema
P=Path; load=lambda p:json.loads(P(p).read_text()); c=load('.agent/contracts/119.json');old=json.loads(subprocess.check_output(['git','show','04ebe146:.agent/contracts/119.json']))
assert hashlib.sha256(P('.agent/contracts/119.json').read_bytes()).hexdigest()=='81a890a46689455f880f1add0d4027372b4fe2e2d2c2caab4fef496e31a15c54'
jsonschema.validate(c,load('.nizam/schema/contract.schema.json'))
n=copy.deepcopy(c);n['acceptance_ownership']['preservation']=old['acceptance_ownership']['preservation'];n['gate_sequence'][3]=old['gate_sequence'][3];n['approvals']['revisions']=0;assert n==old
s=load('.agent/run_state.json');assert s['circuit_breaker']['119-mode-a']=={'attempts':2,'limit':3}
f=next(x for x in load('.agent/feature_list_018.json')['features'] if x['id']=='119');assert [x['command'] for x in c['verification']]==f['acceptance_tests'] and len(c['verification'])==6
assert c['status']=='proposed' and c['estimated_lines']==1000 and c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360
anchor='8ac94f6808e8197111197c9acbf59b2aa92efc7c'
prereq=json.loads(subprocess.check_output(['git','show',anchor+':.agent/evidence/118/prerequisite20.json']));assert prereq['passed'] and prereq['checks_run']==prereq['checks_passed']==20
for p in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/evidence/118/foundation-fixtures.py','.agent/evidence/118/source-candidate.json']:
 assert subprocess.check_output(['git','show',anchor+':'+p])==P(p).read_bytes(),p
for row in prereq['checks']:
 raw=subprocess.check_output(['git','show',anchor+':'+row['evidence']]);assert hashlib.sha256(raw).hexdigest()==row['sha256'] and row['exit_code']==0
assert not subprocess.check_output(['git','diff','--name-only','fcd0584','HEAD','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/convergent_review.py','.nizam/'])
print('PASS schema/hash; exact preservation+QA-clause+revision metadata delta only; all6 API/commands/budget unchanged; attempt2/3; immutable118 anchor contains complete20 receipts and unchanged source/fixtures; no promoted product/test/installed delta')
print('HISTORICAL_ANCHOR',anchor,'PREREQUISITE_SHA256',hashlib.sha256(subprocess.check_output(['git','show',anchor+':.agent/evidence/118/prerequisite20.json'])).hexdigest())
