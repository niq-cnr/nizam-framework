import copy,hashlib,json,subprocess
from pathlib import Path
import jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());c=load('.agent/contracts/120.json');old=json.loads(subprocess.check_output(['git','show','c7c6239:.agent/contracts/120.json']))
assert hashlib.sha256(P('.agent/contracts/120.json').read_bytes()).hexdigest()=='b194978a60c36b64f31e7cf78282781820d118712e917865798889617973f08d'
jsonschema.validate(c,load('.nizam/schema/contract.schema.json'))
n=copy.deepcopy(c);n['api']['operator_application']=old['api']['operator_application'];n['approvals']['revisions']=1;assert n==old
assert c['status']=='proposed' and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':2}
s=load('.agent/run_state.json');assert s['circuit_breaker']['120-mode-a']=={'attempts':3,'limit':3}
f=next(x for x in load('.agent/feature_list_018.json')['features'] if x['id']=='120');assert [x['command'] for x in c['verification']]==f['acceptance_tests'] and len(c['verification'])==11
assert c['estimated_lines']==2750==sum(c['budget'][k] for k in ('product','independent_tests','process')) and c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360
op=c['api']['operator_application']
for term in ('Application owner/gate must exactly match those actual pinned authority values','compare these four projected values exactly against actual authority.scope','never public algorithm constants','dogfood fixture values only','other consistently pinned authorized scopes are valid','do not authenticate consent'):
 assert term in op,term
for former in ('phase==018-workflow-assurance-controls','owner==/root','gate==H-PHASE-018','strictinteger7200/9360'):assert former not in op
actual=load('.agent/evidence/phase018-preflight/activation-authority.json');scope={k:actual['scope'][k] for k in ('phase','features','original_estimate_lines','ceiling_130pct')}
assert type(scope['phase']) is str and scope['phase'] and type(scope['features']) is list and len(set(scope['features']))==len(scope['features']) and '120' in scope['features']
assert all(type(scope[k]) is int and scope[k]>=0 for k in ('original_estimate_lines','ceiling_130pct')) and scope['ceiling_130pct']>=scope['original_estimate_lines']
assert all(type(actual[k]) is str and actual[k] for k in ('owner','gate','operator_instruction_verbatim'))
assert not subprocess.check_output(['git','diff','--name-only','92fecd8','HEAD','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','.nizam/'])
print('PASS exact proposal SHA/schema; ONLY operator_application+revision changed; all previous3 corrected semantics preserved verbatim; actual operator/scope projection satisfies generic predicates; no hardcoded algorithm values;11commands/twoAPIs/2750/7200/9360 unchanged; attempt3/3')
print('ACTUAL_FIXTURE_PROJECTION',json.dumps({'owner':actual['owner'],'gate':actual['gate'],'scope':scope},sort_keys=True))
print('PASS static inspection only; no runtime acceptance, Source/tests/coord/schema/pin edits')
