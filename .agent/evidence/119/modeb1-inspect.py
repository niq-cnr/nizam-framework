import ast,fnmatch,hashlib,json,re,subprocess
from pathlib import Path
import yaml,jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());base='fcd0584146fd836df0080292cc2cf10180bb9f31';c=load('.agent/contracts/119.json')
assert c['status']=='approved' and all(c['approvals'][k] is True for k in ('validator_mode_a','evaluator_contract_review'))
assert hashlib.sha256(P('.agent/contracts/119.json').read_bytes()).hexdigest()=='0ff9b2860ac6a24b4bf40cf42cbde0a0cc62a24a27a0fe7f77d57ed5c34945e6'
for p in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
 old=subprocess.check_output(['git','show',base+':'+p],text=True);new=P(p).read_text()
 if p.endswith('/workflow_assurance.py'):
  normalized=new.replace('import copy\n','',1);start=normalized.index('def convergent_agf_verdict(');end=normalized.index('def main():',start);normalized=normalized[:start]+normalized[end:]
 else:
  start=new.index('AGF_CASES =');end=new.index('def main():',start);normalized=new[:start]+new[end:]
  normalized=normalized.replace('choices=CASES + AGF_CASES','choices=CASES').replace('else CASES + AGF_CASES):','else CASES):').replace('(run_agf_case if name in AGF_CASES else run_entry_case','(run_entry_case')
 assert normalized==old,'whole historical module bytes except exact additions '+p
seal=load('.agent/evidence/119/executable-review1-seal.json')
for p,pin in seal['files'].items():
 data=P(p).read_bytes();assert hashlib.sha256(data).hexdigest()==pin['sha256'] and subprocess.check_output(['git','cat-file','blob',pin['git_blob']])==data,p
assert len(seal['files'])==60
assert not subprocess.check_output(['git','diff','--name-only',base,'HEAD','--','.nizam/','.agent/evidence/118/','tools/convergent_review.py','tools/fixtures/','tools/runtime_session.py','tools/fixtures_self_test.sh','.github/','schema/'])
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],text=True).splitlines();patterns=[x['path'] for key in ('files_create','files_modify') for x in c['scope'][key]]
assert all(p.startswith('.agent/evidence/') or any(fnmatch.fnmatchcase(p,q) for q in patterns) for p in changed)
for p in ('tools/README.md',):
 front=yaml.safe_load(P(p).read_text().split('---',2)[1]);jsonschema.validate(front,load('.nizam/schema/frontmatter.schema.json'));assert front['version']==front['change_log'][0]['version']=='0.28.0'
s=load('.agent/run_state.json');assert s['circuit_breaker']['119-mode-b']=={'attempts':1,'limit':3};assert s['phase_016_scope_budget_final']['total_lines_changed']==5179 and s['phase_017_scope_budget_final']['total_lines_changed']==5203
assert s['scope_budget']['original_estimate_lines']==7200 and s['scope_budget']['ceiling_130pct']==9360 and not s['scope_budget']['per_feature']
lines=P('.agent/evidence/119/modeb1-default26.stdout.txt').read_text().splitlines();assert len(lines)==26 and all(x.startswith('PASS ') for x in lines)
assert [x.removeprefix('PASS ') for x in lines[-6:]]==[x['command'].split()[-1] for x in c['verification']]
assert 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in P('.agent/evidence/119/modeb1-live-stale118.stderr.txt').read_text()
r=subprocess.run(['git','diff','--check',base,'HEAD','--',':!.agent/evidence/**'],capture_output=True,text=True);assert r.returncode==0
broad=P('.agent/evidence/119/modeb1-diff.stdout.txt').read_text();assert all(x.startswith('.agent/evidence/agentic-excellence/') for x in broad.splitlines() if 'trailing whitespace.' in x)
print('PASS full inherited Source/test modules preserved except exact approved additions/dispatch;60 finalseal Git/SHA pins; protected payload/fixtures/workflows; NDS; exact26; live stale rejection; role scope; original budget/archives')
print('PASS maintained-file diffcheck0; broad diagnostic2 only unmodified raw incoming comparison help/HTML whitespace, preserved as external-system capture')
