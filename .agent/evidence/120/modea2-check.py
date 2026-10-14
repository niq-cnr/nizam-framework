import copy,hashlib,json,subprocess
from pathlib import Path
import jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());c=load('.agent/contracts/120.json');old=json.loads(subprocess.check_output(['git','show','63f3bb9:.agent/contracts/120.json']))
assert hashlib.sha256(P('.agent/contracts/120.json').read_bytes()).hexdigest()=='25f7845d2593f79fb862d322f7dd29ed356e48415b809d439447890e4dadedb2'
jsonschema.validate(c,load('.nizam/schema/contract.schema.json'));assert c['verification']==old['verification'] and c['scope']==old['scope'] and c['budget']==old['budget']
assert len(c['verification'])==11 and c['estimated_lines']==2750 and c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360
s=load('.agent/run_state.json');assert s['circuit_breaker']['120-mode-a']=={'attempts':2,'limit':3}
rs=load('.nizam/schema/run_state.schema.json');jsonschema.validate(s,rs)
operation='modea2-proof';feature='120';stage='qa-passed';digest='b'*64
entry={'at':'2026-10-14T16:10:00+00:00','event':'wa-receipt-transition','detail':'Receipt '+operation+' advanced '+feature+':'+stage+' ('+digest+')','operation_id':operation,'feature_id':feature,'stage':stage,'candidate_sha256':'a'*64,'receipt_sha256':digest}
after=copy.deepcopy(s);after['history'].append(entry);jsonschema.validate(after,rs)
assert 'detail' in c['api']['transition'] and 'validate output schema' in c['api']['transition'] and 'deterministic detail' in c['api']['idempotence']
qa=load('.agent/qa/119.json');jsonschema.validate(qa,load('schema/qa_verdict.schema.json'))
review=load('.agent/qa/119-contract-review-rev1.json');jsonschema.validate(review,load('.nizam/schema/contract_review.schema.json'))
contract=json.loads(subprocess.check_output(['git','show','9ef2db5:.agent/contracts/119.json']));jsonschema.validate(contract,load('.nizam/schema/contract.schema.json'));assert contract['status']=='approved' and all(contract['approvals'][k] is True for k in ('validator_mode_a','evaluator_contract_review'))
capture=load('.agent/evidence/119/evidence-capture.json');assert capture['role']=='Root' and capture['passed'] is True and type(capture['actual_exit']) is int and capture['actual_exit']==0
assert 'no AGF arrays invented for capture' in c['api']['artifact_predicates'] and 'contract_sha256' in c['api']['artifact_predicates']
assert 'capture immutable independently selected reference' in c['api']['actual_execution'] and 'executedTrue' in c['api']['actual_execution'] and 'actual restore/revalidation' in c['api']['recovery']
print('RESOLVED original3: schema-valid deterministicdetail/input-output state checks; actual per-kind predicates/schema fields; independently pinned actual capture record and restored-proof exercise')
operator=c['api']['operator_application']
for literal in ('phase==018-workflow-assurance-controls','strictinteger7200/9360','owner==/root','gate==H-PHASE-018'):assert literal in operator
print('ISSUE120-A3 shipped operator_application constants:',operator)
print('SPEC120',P('.agent/product_spec_018.md').read_text().split('Feature 120 ',1)[1].split('Feature 121',1)[0])
print('NIP-A10',P('docs/nips/NIP-0004-workflow-assurance.md').read_text().split('A10 would reuse ',1)[1].split('### Proposed execution',1)[0])
print('PRODUCT_GUIDANCE',P('README.md').read_text().split('Nizam is order,',1)[1].split('Nizam does not',1)[0])
assert not subprocess.check_output(['git','diff','--name-only','92fecd8','HEAD','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','.nizam/'])
print('PASS focused static inspection; exact11/twoAPIs/2750/7200/9360 retained; no runtime or absentAPI commands; no product/test/installed edits')
