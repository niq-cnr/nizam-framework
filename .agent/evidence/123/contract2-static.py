"""Revision2 syntax/schema/reference/order analysis; no Source/API execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

p=Path('.agent/contracts/123.json'); c=json.loads(p.read_text())
for path in ['schema/contract.schema.json','.nizam/schema/contract.schema.json']:
 schema=json.loads(Path(path).read_text());jsonschema.Draft202012Validator.check_schema(schema)
 jsonschema.Draft202012Validator(schema).validate(c);print('STATIC contract schema valid: '+path)
assert c['status']=='proposed' and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':1}
f=next(r for r in json.loads(Path('.agent/feature_list_018.json').read_text())['features'] if r['id']=='123')
assert [r['command'] for r in c['verification']][:5]==f['acceptance_tests']
assert c['estimated_lines']==1200 and [c['budget'][k] for k in ['product','independent_tests','process','phase_original','phase_ceiling','prior_actual']]==[300,350,550,7200,9360,4303]
for key in ['spec_ref','dod_ref']: assert Path(c[key]).is_file()
for r in c['scope']['files_modify']: assert Path(r['path']).is_file()
for path in ['tools/evaluate_convergent_review_prompt.py','tools/linux_trial_sandbox.sh','tools/isolated_trial_adapter.py','.github/scripts/test_sandbox_boundaries.py','templates/convergent-review-prompt.md','.agent/evidence/agentic-excellence/runtime-preflight-namespace-canary.txt','.agent/evidence/phase016-preflight/local-1.txt']:
 assert Path(path).is_file(),path
q=c['protocol']
for name in ['policy','selection','evidence','checkout','host','trial','artifact','hosted_review','result','report','a10_result']:
 assert set(q[name])=={'keys','binding'} and q[name]['keys'] and q[name]['binding']
assert set(q['command_plan'])=={'capture','packet','trials','map','verify','boundary','observation','substitution'}
assert len(q['order'])==7 and all(row.startswith(str(i)+' ') for i,row in enumerate(q['order'],1))
# Parse conceptual command topology, not executable implementation.
edges={'capture':['packet','trials','map'],'packet':[],'trials':['observation'],'observation':[],'map':[],'verify':[],'controls-ready':['verify_controls_ready'],'verify_controls_ready':[]}
def visit(name,active):
 assert name not in active,'recursive command topology'
 for target in edges[name]: visit(target,active|{name})
for name in edges: visit(name,set())
state=json.loads(Path('.agent/run_state.json').read_text())
assert state['circuit_breaker']['123-contract']['attempts']==2
assert state['circuit_breaker']['123-contract']['limit']==3
assert state['current_feature']=='123' and state['scope_budget']['total_lines_changed']==4303
for path in ['.agent/validator/123-mode-a.json','.agent/qa/123-contract-review.json']:
 v=json.loads(Path(path).read_text());assert v['final_verdict']['approved'] is False and v['issues']
rows=json.loads(Path('.agent/evidence/123/source-prerequisite.json').read_text())['adjacent_prior_feature_evidence'];assert len(rows)==28
for r in rows:
 data=subprocess.check_output(['git','show',r['revision']+':'+r['path']]);assert hashlib.sha256(data).hexdigest()==r['sha256']
 fields=subprocess.check_output(['git','ls-tree',r['revision'],'--',r['path']],text=True).split();assert fields[:3]==[r['git_mode'],'blob',r['git_blob']]
 assert Path(r['path']).read_bytes()==data
owned=subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines();assert owned==['.agent/contracts/123.json'],owned
print('STATIC acceptance/budget/path references, closed record declarations and nonrecursive order valid')
print('STATIC rejected gates, exact28 predecessor blobs/modes and Root attempt2 state preserved')
print('No Source/API/test/bank/compliance/namespace/CI execution; no semantic acceptance claim')
