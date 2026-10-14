import hashlib,json,re,subprocess
from pathlib import Path
import yaml,jsonschema
base='12436dd6a5f3407786d575ff1bd32be6fdbca198'
root=Path.cwd(); prefix=Path('.agent/evidence/127/closeout-docs-')
results=[]
def run(name,argv):
 p=subprocess.run(argv,capture_output=True,text=True)
 for suffix,data in [('stdout.txt',p.stdout),('stderr.txt',p.stderr)]:
  Path(str(prefix)+name+'.'+suffix).write_text(data)
 r={'name':name,'argv':argv,'actual_exit':p.returncode,'stdout':str(prefix)+name+'.stdout.txt','stderr':str(prefix)+name+'.stderr.txt'}
 results.append(r);assert p.returncode==0,r
 return p.stdout
run('diff',['git','diff','--unified=0',base,'--','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'])
run('numstat',['git','diff','--numstat',base,'--','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'])
run('whitespace',['git','diff','--check',base,'--','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'])
proof={};schema=json.loads(Path('.nizam/schema/frontmatter.schema.json').read_text())
for name,marker in [('ROADMAP','## Current position — phase 016, 2026-10-14'),('HANDOVER','## Current handoff — feature 126, 2026-10-14')]:
 p=Path('docs/planning/'+name+'.md');raw=p.read_bytes();s=raw.decode();old=subprocess.check_output(['git','show',base+':'+str(p)]).decode()
 meta=yaml.safe_load(s.split('---',2)[1]);jsonschema.validate(meta,schema)
 assert meta['version']==meta['change_log'][0]['version']
 assert meta['version']!=yaml.safe_load(old.split('---',2)[1])['version']
 assert s[s.index(marker):]==old[old.index(marker):]
 overlay=s[s.index('## Current '):s.index(marker)]
 assert 'selected 127' not in overlay and '3,003' not in overlay and '1,736' not in overlay and '4,739' not in overlay
 links=re.findall(r'\]\(([^)]+)\)',overlay)
 for link in links:
  if not link.startswith('https://'):assert (p.parent/link.split('#')[0]).resolve().is_file(),link
 proof[str(p)]={'sha256':hashlib.sha256(raw).hexdigest(),'version':meta['version'],'historical_start':marker,'historical_sha256':hashlib.sha256(s[s.index(marker):].encode()).hexdigest(),'history_byte_identical':True,'current_overlay_links':links}
def data(path):return json.loads(Path(path).read_text())
cap=data('.agent/evidence/127/evidence-capture.json');qa=data('.agent/qa/127.json');ci=data('.agent/evidence/127/ci-c1-receipt.json')
assert cap['passed'] is True and cap['revision']=='88996ee9405f9467ff2debd6e3115b34d064019a'
assert cap['checks_captured']==14 and cap['repository_checks_captured']==2 and cap['adversarial_captured'] is True
assert qa['qa_pass'] is True and qa['checks_run']==qa['checks_passed']==14 and len(qa['repository_checks'])==2
assert qa['adversarial']['count']==1 and qa['adversarial']['exit_code']==0
assert qa['test_sha256'].startswith('3628f1b2') and qa['source_revision']==cap['revision']
assert len(ci['commands'])==14 and all(x['actual_exit']==0 for x in ci['commands']) and ci['run']==38557965408 and ci['source']==cap['revision']
assert ci['source_sha256']==cap['source_sha256']
assert data('.agent/evidence/126/evidence-capture.json')['passed'] is True
assert data('.agent/qa/126.json')['qa_pass'] is True
fl=data('.agent/feature_list_016.json');assert all(any(x['case']==n and x['runtime']=='stub' and x['layer']=='live' and x['owner']=='127' for x in fl['case_matrix']) for n in [5,6,10])
assert any(x['id']=='128' and x['name']=='Bounded core evidence and close' for x in fl['features'])
changed=subprocess.check_output(['git','diff','--name-only',base],text=True).splitlines()
assert {'docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'} <= set(changed),changed
assert all(x in {'docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'} or x.startswith('.agent/evidence/127/closeout-docs-') for x in changed),changed
out={'base_revision':base,'exercise':'documentation-only scoped verification; no runtime reruns','documents':proof,'factual_inputs':['.agent/evidence/126/evidence-capture.json','.agent/qa/126.json','.agent/evidence/126/ci-c3-receipt.json','.agent/evidence/126/pr97-merge-receipt.json','.agent/evidence/126/pr97-main-ci.json','.agent/evidence/127/evidence-capture.json','.agent/qa/127.json','.agent/evidence/127/ci-c1-receipt.json','.agent/feature_list_016.json'],'commands':results,'tracked_changes':changed,'source_runtime_installed_root_state_unchanged':True,'passed':True,'boundary':'Author scoped verification only. Independent factual review remains required; no self approval.'}
Path(str(prefix)+'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':True,'history_preserved':list(proof),'checks':['NDS/schema/version-log','local-overlay-paths','capture/QA/CI factual bindings','case-matrix/next128','owned-scope','diff/numstat/whitespace']}))
