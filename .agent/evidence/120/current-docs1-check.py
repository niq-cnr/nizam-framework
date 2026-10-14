import hashlib,json,subprocess
from pathlib import Path
BASE='3231fdbdb79126656f0b70af338dbc1cd9eda8e1'
paths=['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md','.agent/product_spec_018.md']
def old(p):return subprocess.check_output(['git','show',f'{BASE}:{p}']).decode()
checks={};marker='All earlier sections below, including older “Current” headings, are historical snapshots.'
for p in paths[:2]:
 a,b=old(p),Path(p).read_text();assert a[a.index(marker):]==b[b.index(marker):]
 checks[p]={'historical_suffix_unchanged':True,'sha256':hashlib.sha256(b[b.index(marker):].encode()).hexdigest()}
p=paths[2];a,b=old(p),Path(p).read_text()
for start,end in [('## Architecture and external prerequisites','## Acceptance position and independent ownership'),('Its --case NAME','## Full counted proposed budget')]:assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
start='## Full counted proposed budget';assert a[a.index(start):]==b[b.index(start):]
checks[p]={'architecture_DAG_requirements_unchanged':True,'independent_gate_protocol_unchanged':True,'entire_budget_section_unchanged':True,'version':'0.1.3','feature_list_sync_owner':'Root'}
c=json.loads(Path('.agent/evidence/120/evidence-capture.json').read_text());q=json.loads(Path('.agent/qa/120.json').read_text());h=json.loads(Path('.agent/evidence/120/ci2-receipt.json').read_text());close=json.loads(Path('.agent/evidence/120/closure.json').read_text())
assert c['passed'] is True and c['actual_exit']==0 and c['mandatory_results']==18 and c['current_default_cases']==37
assert c['independent_adversarial']=={'logical_checks':1,'executions':2,'original_helper_failure_preserved':True}
assert q['final_verdict']['approved'] is True and all(q[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
assert h['passed'] is True and h['default37_passed'] is True and h['compliance_run']==38610323583 and len(h['all37_ordered'])==37
assert close['canonical_step']=='COMPLETED' and close['later_pending']==['121','122','123']
merge=json.loads(Path('.agent/evidence/119/pr100-merge-receipt.json').read_text());assert merge['merged_commit']=='92fecd8d376964f5e3dd7e34bc201035acfe8bc6'
assert set(subprocess.check_output(['git','diff','--name-only']).decode().splitlines())==set(paths)
commands=[]
for argv in [['git','diff','--check','--',*paths],['git','diff','--numstat','--',*paths]]:
 r=subprocess.run(argv,text=True,capture_output=True);commands.append({'argv':argv,'actual_exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0
count=sum(int(n) for row in commands[1]['stdout'].splitlines() for n in row.split('\t')[:2]);assert count==41
raw=subprocess.run(['git','diff','--',*paths],capture_output=True,text=True);assert raw.returncode==0
Path('.agent/evidence/120/current-docs1-diff.txt').write_text(raw.stdout)
result={'role':'Planner','attempt':1,'input_revision':BASE,'root':str(Path.cwd()),'actual_exit':0,'checks':checks,'facts_verified':{'capture':'.agent/evidence/120/evidence-capture.json','qa':'.agent/qa/120.json','hosted':'.agent/evidence/120/ci2-receipt.json','closure':'.agent/evidence/120/closure.json','119merge':'.agent/evidence/119/pr100-merge-receipt.json'},'counted_document_lines':count,'commands':commands,'raw_diff':'.agent/evidence/120/current-docs1-diff.txt','boundary':'Documentation-only current projection. No runtime/QA/regression reruns; no maintained Source/test/lifecycle write. Root owns final measured budget/spec_version sync and PR integration. Raw unified diff context whitespace is diagnostic evidence and is excluded from maintained-document whitespace check.'}
Path('.agent/evidence/120/current-docs1-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'actual_exit':0,'counted_document_lines':count,'historical_and_requirement_sections_unchanged':True}))
