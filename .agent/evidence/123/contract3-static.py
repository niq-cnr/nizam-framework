"""Final proposal static schema/reference/format and dependency analysis only."""
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

path=Path('.agent/contracts/123.json');c=json.loads(path.read_text())
for name in ['schema/contract.schema.json','.nizam/schema/contract.schema.json']:
 s=json.loads(Path(name).read_text());jsonschema.Draft202012Validator.check_schema(s)
 jsonschema.Draft202012Validator(s).validate(c);print('STATIC schema valid: '+name)
assert c['status']=='proposed' and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':2}
assert 'approved_at' not in c['approvals'] and 'approval_evidence' not in c
feature=next(x for x in json.loads(Path('.agent/feature_list_018.json').read_text())['features'] if x['id']=='123')
assert [x['command'] for x in c['verification']][:5]==feature['acceptance_tests']
assert c['estimated_lines']==1200 and [c['budget'][k] for k in ['product','independent_tests','process','phase_original','phase_ceiling','prior_actual']]==[300,350,550,7200,9360,4303]
for key in ['spec_ref','dod_ref']:assert Path(c[key]).is_file()
for row in c['scope']['files_modify']:assert Path(row['path']).is_file()
q=c['protocol']
for name in ['policy','selection','evidence','checkout','host','trial','artifact','hosted_review','result','report','a10_result','capability','process','invocation','host_metadata','fetch','experiment_authority','shadow_state']:
 assert set(q[name])=={'keys','binding'} and q[name]['keys'] and q[name]['binding']
assert set(q['bundle_transport'])=={'raw','produce','manifest','import','archive','limits'}
assert set(q['external_formats'])=={'json_policy','run','jobs','artifacts','log'}
assert len(q['payload_catalog'])>=25
# Architectural DAG only: dependencies encode the declared commit order, not behavior.
deps={
 'original-authority':[], 'dual-gates':[], 'approved-metadata':['dual-gates'],
 'provisional':['approved-metadata'], 'source':['provisional'],
 'capture-selection':['source','original-authority'], 'trial-execution':['capture-selection'],
 'capture-outputs':['trial-execution'], 'capture-json':['capture-outputs'],
 'capture-tip':['capture-json'], 'capture-bundle':['capture-tip'],
 'capture-manifest':['capture-bundle'], 'capture-invocation':['capture-manifest'],
 'raw-capture-fetch':['capture-invocation'], 'capture-normalization':['raw-capture-fetch'],
 'receipt':['capture-normalization'], 'a10-policy':['receipt'],
 'verify-selection':['a10-policy'], 'verify-execution':['verify-selection'],
 'verify-outputs':['verify-execution'], 'verify-json':['verify-outputs'],
 'verify-tip':['verify-json','capture-tip'], 'verify-bundle':['verify-tip'],
 'verify-manifest':['verify-bundle'], 'verify-invocation':['verify-manifest'],
 'raw-verify-fetch':['verify-invocation'], 'verify-normalization':['raw-verify-fetch'],
 'evidence':['verify-normalization','capture-normalization'],
 'hosted-review':['evidence'], 'final-policy':['hosted-review'], 'local-observation':['final-policy']}
def walk(node,active):
 assert node not in active,'cyclic commitment order'
 for dep in deps[node]:walk(dep,active|{node})
for node in deps:walk(node,set())
state=json.loads(Path('.agent/run_state.json').read_text())
assert state['circuit_breaker']['123-contract']['attempts']==3 and state['circuit_breaker']['123-contract']['limit']==3
for name in ['.agent/validator/123-mode-a-rev1.json','.agent/qa/123-contract-review-rev1.json']:
 v=json.loads(Path(name).read_text());assert v['final_verdict']['approved'] is True
 assert all(v[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
rows=json.loads(Path('.agent/evidence/123/source-prerequisite.json').read_text())['adjacent_prior_feature_evidence'];assert len(rows)==28
for r in rows:
 data=subprocess.check_output(['git','show',r['revision']+':'+r['path']]);assert hashlib.sha256(data).hexdigest()==r['sha256']
 fields=subprocess.check_output(['git','ls-tree',r['revision'],'--',r['path']],text=True).split();assert fields[:3]==[r['git_mode'],'blob',r['git_blob']]
 assert Path(r['path']).read_bytes()==data
assert subprocess.check_output(['git','diff','HEAD','--name-only'],text=True).splitlines()==['.agent/contracts/123.json']
print('STATIC exact acceptance/budget/path references and all closed format declarations checked')
print('STATIC payload catalog entries='+str(len(q['payload_catalog']))+'; declared commit graph acyclic nodes='+str(len(deps)))
print('STATIC current attempt3, historical approved gates and exact28 adjacent blob/mode rows preserved')
print('No Source, fixture, API, test, bank, CI, compliance, namespace, model or behavioral execution; declaration checks are not acceptance proof')
