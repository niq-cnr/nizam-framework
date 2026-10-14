import hashlib,json,re,subprocess
from pathlib import Path
import yaml,jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());base='3231fdbdb79126656f0b70af338dbc1cd9eda8e1';old=lambda p:subprocess.check_output(['git','show',base+':'+p],text=True)
paths=['.agent/product_spec_018.md','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'];versions=['0.1.3','0.65.6','1.0.19']
for p,v in zip(paths,versions):
 text=P(p).read_text();front=yaml.safe_load(text.split('---',2)[1]);jsonschema.validate(front,load('.nizam/schema/frontmatter.schema.json'));assert front['version']==front['change_log'][0]['version']==v
 current=text if p.startswith('.agent/') else text[:text.index('All earlier sections below, including older “Current” headings, are historical snapshots.')]
 for target in re.findall(r'\]\(([^)]+)\)',current):
  if not target.startswith('https://'):assert (P(p).parent/target).is_file(),(p,target)
for p in paths[1:]:
 marker='All earlier sections below, including older “Current” headings, are historical snapshots.';a=old(p);b=P(p).read_text();assert a[a.index(marker):]==b[b.index(marker):];print('PASS history',p,hashlib.sha256(b[b.index(marker):].encode()).hexdigest())
p=paths[0];a=old(p);b=P(p).read_text()
for start,end in [('## Architecture and external prerequisites','## Acceptance position and independent ownership'),('Its --case NAME','## Full counted proposed budget')]:assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
start='## Full counted proposed budget';assert a[a.index(start):]==b[b.index(start):]
f=load('.agent/feature_list_018.json');before=json.loads(old('.agent/feature_list_018.json'));assert f['spec_version']=='0.1.3';f.pop('spec_version');before.pop('spec_version');assert f==before
c=load('.agent/evidence/120/evidence-capture.json');assert c['passed'] is True and c['actual_exit']==0 and c['mandatory_results']==18 and c['current_default_cases']==37 and c['independent_adversarial']=={'logical_checks':1,'executions':2,'original_helper_failure_preserved':True}
q=load('.agent/qa/120.json');assert q['final_verdict']['approved'] is True and all(q[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
h=load('.agent/evidence/120/ci2-receipt.json');assert h['passed'] is True and h['default37_passed'] is True and h['compliance_run']==38610323583 and len(h['all37_ordered'])==37 and h['exit_code']==0
close=load('.agent/evidence/120/closure.json');assert close['canonical_step']=='COMPLETED' and close['later_pending']==['121','122','123']
assert load('.agent/evidence/120/repository-binding-decision-proposal.json')['status']=='proposal-only'
canary=load('.agent/evidence/agentic-excellence/runtime-canary-proposal-rev2.json');assert canary['superiority_established'] is False and 'proposal-only' in canary['status']
assert 'PR101 draft, not merged yet' in load('.agent/evidence/120/current-docs1-dispatch.json')['state']
stat=subprocess.check_output(['git','diff','--numstat',base,'d1e8f59','--',*paths],text=True);assert sum(sum(map(int,r.split()[:2])) for r in stat.splitlines())==41
print('PASS41doclines+Rootversionalias; NDS/currentlinks; unchanged requirements/DAG/gates/budgets; actualcapture18+onecheck/execution2/hosted37; PR101documentedsnapshot; pending121-123; migration/canary remainproposals')
