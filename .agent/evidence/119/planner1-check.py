import hashlib,json,re,subprocess
from pathlib import Path
BASE='b18d1e02a8c7dae97c64fdb143669b3042df5ee2'
paths=['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md','.agent/product_spec_018.md']
def old(p): return subprocess.check_output(['git','show',f'{BASE}:{p}']).decode()
checks={}
marker='All earlier sections below, including older “Current” headings, are historical snapshots.'
for p in paths[:2]:
 a,b=old(p),Path(p).read_text()
 assert a[a.index(marker):]==b[b.index(marker):]
 checks[p]={'historical_suffix_sha256':hashlib.sha256(b[b.index(marker):].encode()).hexdigest(),'historical_suffix_unchanged':True,'current_overlay_count':b[:b.index(marker)].count('## Current ')}
 assert checks[p]['current_overlay_count']==1
p=paths[2];a,b=old(p),Path(p).read_text()
for start,end in [('## Architecture and external prerequisites','## Future acceptance and independent ownership'),('| ID | Product','The unchanged 130% ceiling')]:
 if start.startswith('##'):
  assert a[a.index(start):a.index(end)]==b[b.index(start):b.index('## Acceptance position and independent ownership')]
 else: assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
start='Its --case NAME';end='## Full counted proposed budget'
assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
checks[p]={'architecture_requirements_and_dependencies_unchanged':True,'acceptance_gate_protocol_unchanged':True,'budget_table_unchanged':True,'spec_version':'0.1.2','feature_list_metadata_sync_owner':'Root'}
capture=json.loads(Path('.agent/evidence/119/evidence-capture.json').read_text())
qa=json.loads(Path('.agent/qa/119.json').read_text());ci=json.loads(Path('.agent/evidence/119/ci2-receipt.json').read_text());closure=json.loads(Path('.agent/evidence/119/closure.json').read_text())
assert capture['passed'] is True and capture['current_default_cases']==26 and capture['live_stale_exit']==1
assert qa['final_verdict']['approved'] is True and all(qa[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
assert qa['checks_passed']==6 and qa['adversarial']['count']==1
assert qa['supplementary_checks']['historical-foundation']['exit_code']==0 and qa['supplementary_checks']['live-stale-foundation']['exit_code']==1
assert ci['passed'] is True and ci['compliance_run']==38583535629 and len(ci['all26_ordered'])==26
assert closure['canonical_step']=='COMPLETED' and closure['phase_status']=='in_progress' and closure['later_pending']==['120','121','122','123']
changed=subprocess.check_output(['git','diff','--name-only']).decode().splitlines();assert set(changed)==set(paths)
commands=[]
for argv in [['git','diff','--check'],['git','diff','--numstat'],['git','diff','--',*paths]]:
 r=subprocess.run(argv,text=True,capture_output=True)
 commands.append({'argv':argv,'actual_exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0
Path('.agent/evidence/119/planner1-diff.txt').write_text(commands[-1]['stdout'])
numstat=commands[1]['stdout'];count=sum(int(n) for row in numstat.splitlines() for n in row.split('\t')[:2]);assert count==47
result={'role':'Planner','attempt':1,'input_revision':BASE,'owned_root':str(Path.cwd()),'actual_exit':0,'checks':checks,'evidence_verified':{'capture_revision':'96ef3ff6318d2d17b3491317c88f1076792a7bad','qa':'.agent/qa/119.json','hosted':'.agent/evidence/119/ci2-receipt.json','closure':'.agent/evidence/119/closure.json'},'diff_numstat':numstat,'counted_document_lines':count,'commands':commands[:2],'boundary':'Documentation-only current projection. No runtime or regression reruns. Root owns feature-list spec_version synchronization, final measurement and integration. Historical requirements, gates, budgets and installed payload preserved.'}
Path('.agent/evidence/119/planner1-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'actual_exit':0,'counted_document_lines':count,'historical_suffixes_unchanged':True,'requirements_dag_allowances_unchanged':True}))
