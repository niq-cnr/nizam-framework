import json,subprocess,hashlib,re
from pathlib import Path
import yaml,jsonschema
P=Path; baseline='6770458cce17b54a9cf17aca5f2c8a480c11df36'; plan='3a9614173f8acce152aa5ad85ac37a0d4b411c80'
load=lambda p:json.loads(P(p).read_text())
f=load('.agent/feature_list_018.json'); old=json.loads(subprocess.check_output(['git','show',baseline+':.agent/feature_list_018.json']))
assert f['features']==old['features'] and f['shared_file_lanes']==old['shared_file_lanes'] and f['future_interfaces']==old['future_interfaces']
assert f['phase_status']=='pending' and all(x['status']=='pending' and not x['passes'] for x in f['features'])
assert f['original_estimate_lines']==7200 and f['ceiling_130pct']==9360 and f['features'][0]['estimated_lines']==1000
assert sum(x['estimated_lines'] for x in f['features'])==7200 and sum(f['budget_categories'].values())==7200
jsonschema.validate(f,load('.nizam/schema/feature_list.schema.json'))
seen=set()
for x in f['features']:
 assert set(x['dependencies'])<=seen;seen.add(x['id'])
assert seen=={'119','120','121','122','123'}
assert [x['requires'] for x in f['cross_phase_prerequisites']]==[['118'],['127']]
for prereq in f['cross_phase_prerequisites']:
 for receipt in prereq['evidence']: assert load(receipt)['passed']
spec=P('.agent/product_spec_018.md').read_text();front=yaml.safe_load(spec.split('---',2)[1]);jsonschema.validate(front,load('.nizam/schema/frontmatter.schema.json'))
assert front['version']==front['change_log'][0]['version']=='0.1.1' and front['status']=='active'
for target in re.findall(r'\]\(([^)]+)\)',spec):assert (P('.agent')/target).is_file(),target
for term in ('A09-after-NIP3-120','no implementation approval','5,179','fcd0584','planning is not activation'):
 assert term in spec,term
ci=load('.agent/evidence/128/pr99-main-ci.json');assert ci['actual_api_exit']==0 and ci['run']['databaseId']==38572390067 and ci['run']['status']=='completed' and ci['run']['conclusion']=='success'
assert ci['run']['headSha']=='fcd0584146fd836df0080292cc2cf10180bb9f31' and len(ci['run']['jobs'])==5 and all(j['conclusion']=='success' for j in ci['run']['jobs'])
a=load('.agent/evidence/phase018-preflight/activation-authority.json');assert a['repository']=='niq-cnr/nizam-framework only' and a['scope']['unchanged'] and a['scope']['features']==['119','120','121','122','123']
assert a['scope']['original_estimate_lines']==7200 and a['scope']['ceiling_130pct']==9360 and a['scope']['feature119']==1000
s=load('.agent/run_state.json');oldstate=json.loads(subprocess.check_output(['git','show','ffed4d4:.agent/run_state.json']));assert s['scope_budget']==oldstate['scope_budget'] and s['scope_budget']['total_lines_changed']==5179
assert s['phase_016_scope_budget_final']==oldstate['phase_016_scope_budget_final']
assert s['circuit_breaker']['018-activation-review']=={'attempts':1,'limit':3}
m=load('docs/planning/manifest.json');phase=next(x for x in m['phases'] if x['id']=='016-runtime-controller-core');assert phase['status']=='complete'
assert yaml.safe_load(P('docs/planning/phase_016.yaml').read_text())['status']=='complete' and yaml.safe_load(P('docs/planning/phase_018.yaml').read_text())['status']=='pending'
changed=subprocess.check_output(['git','diff','--name-only',baseline,plan],text=True).splitlines();assert all(x in ('.agent/product_spec_018.md','.agent/feature_list_018.json') or x.startswith('.agent/evidence/phase018-preflight/activation-plan-') for x in changed)
inputs=['.agent/product_spec_018.md','.agent/feature_list_018.json','.agent/evidence/phase018-preflight/activation-authority.json','.agent/evidence/phase018-preflight/readiness-report.json','.agent/evidence/118/evidence-capture.json','.agent/evidence/127/evidence-capture.json','.agent/evidence/128/pr99-main-ci.json','.agent/evidence/128/pr99-merge-receipt.json','docs/planning/phase_016.yaml','docs/planning/manifest.json','.nizam/NIZAM.json','.nizam/tools/SKILL.md']
print('PASS unchanged features/commands/budgets/DAG; actual118127 receipt paths; NDS/link checks; actual main5CI; complete016/pending018; immutable5179 archive; scoped Planner amendment')
print(json.dumps({p:hashlib.sha256(P(p).read_bytes()).hexdigest() for p in inputs},indent=2))
