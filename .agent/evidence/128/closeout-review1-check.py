import hashlib,json,re,subprocess
from pathlib import Path
import yaml,jsonschema
P=Path; base='72208732026b9b5bcec13f9fd63ad3b3b053021b'
docs=['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md']
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],text=True).splitlines()
assert set(x for x in changed if not x.startswith('.agent/evidence/128/closeout-docs-check'))==set(docs)
numstat=subprocess.check_output(['git','diff','--numstat',base,'HEAD','--',*docs],text=True)
assert sum(sum(map(int,x.split()[:2])) for x in numstat.splitlines())==28
for doc,anchor,version in zip(docs,['## Current position — phase 016,','## Current handoff — feature 126,'],['0.65.4','1.0.17']):
 raw=P(doc).read_bytes(); old=subprocess.check_output(['git','show',base+':'+doc]); a=anchor.encode()
 assert raw[raw.index(a):]==old[old.index(a):]
 text=raw.decode(); front=yaml.safe_load(text.split('---',2)[1]); jsonschema.validate(front,json.loads(P('.nizam/schema/frontmatter.schema.json').read_text()))
 assert front['version']==front['change_log'][0]['version']==version
 current=text[text.index('## Current '):text.index(anchor)]
 for term in ('captured complete','62a83e6','005ed223','38569054719','did not execute `core-ready`','119–123','127 only','5,650/7,345','5,203/7,020','v1.5.0','131 remain pending','unmeasured','pull/99'):
  assert term in current,(doc,term)
 for target in re.findall(r'\]\(([^)]+)\)',current):
  if not target.startswith('https://'): assert (P(doc).parent/target).is_file(),target
 assert not any(x in current.lower() for x in ('pr 99 merged','pr 99 pending','5/5','6/6'))
 print('PASS',doc,'NDS/current links/history',hashlib.sha256(raw[raw.index(a):]).hexdigest())
c=json.loads(P('.agent/evidence/128/evidence-capture.json').read_text()); q=json.loads(P('.agent/qa/128.json').read_text()); ci=json.loads(P(c['ci_ref']).read_text())
assert c['passed'] and c['checks_captured']==3 and c['aggregate_leaves']==14 and c['adversarial_actual_exit']==2
assert json.loads(P('.agent/evidence/128/capture1-result.json').read_text())['actual_exit']==0
assert q['qa_pass'] and q['checks_run']==q['checks_passed']==3 and all(x['exit_code']==0 for x in q['checks'])
assert ci['run']==38569054719 and len(ci['commands'])==14 and all(x['actual_exit']==0 and 'core-ready' not in x['command'] for x in ci['commands'])
f=json.loads(P('.agent/feature_list_018.json').read_text()); assert [x['id'] for x in f['features']]==['119','120','121','122','123']
assert next(x for x in f['cross_phase_prerequisites'] if x['phase']=='016-runtime-controller-core')['requires']==['127']
assert yaml.safe_load(P('docs/planning/phase_016.yaml').read_text())['status']=='complete'
print('PASS factual capture/QA3/core14/hosted14/next018-prerequisite/scope28; no runtime or full validation rerun')
