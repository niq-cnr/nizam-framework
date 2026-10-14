import ast,fnmatch,hashlib,json,subprocess
from pathlib import Path
import jsonschema,yaml
P=Path;load=lambda p:json.loads(P(p).read_text());sha=lambda b:hashlib.sha256(b).hexdigest();base='92fecd8d376964f5e3dd7e34bc201035acfe8bc6'
c=load('.agent/contracts/120.json');assert c['status']=='approved' and sha(P('.agent/contracts/120.json').read_bytes())=='3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9';jsonschema.validate(c,load('.nizam/schema/contract.schema.json'))
for key in ('validator_mode_a','evaluator_contract_review'):assert c['approvals'][key] is True
source=P('tools/workflow_assurance.py').read_text();start=source.index('def _receipt_text(');end=source.index('def main():',start);normalized=source[:start]+source[end:]
assert ast.dump(ast.parse(normalized),include_attributes=False)==ast.dump(ast.parse(subprocess.check_output(['git','show',base+':tools/workflow_assurance.py'])),include_attributes=False)
text=P('tools/test_workflow_assurance.py').read_text();start=text.index('RECEIPT_CASES =');end=text.index('def main():',start);normalized=text[:start]+text[end:]
normalized=normalized.replace('CASES + AGF_CASES + RECEIPT_CASES','CASES + AGF_CASES').replace('(run_receipt_case if name in RECEIPT_CASES else run_agf_case','(run_agf_case')
assert ast.dump(ast.parse(normalized),include_attributes=False)==ast.dump(ast.parse(subprocess.check_output(['git','show',base+':tools/test_workflow_assurance.py'])),include_attributes=False)
assert P('tools/workflow_assurance.py').read_bytes()==subprocess.check_output(['git','show','1689f0d:tools/workflow_assurance.py'])
seal=load('.agent/evidence/120/executable-review1-seal.json');assert len(seal['files'])==230 and len(seal['identity_objects'])==17
for path,pin in seal['files'].items():
 data=P(path).read_bytes();assert sha(data)==pin['sha256'] and subprocess.check_output(['git','cat-file','blob',pin['git_blob']])==data,path
 assert subprocess.check_output(['git','rev-parse',pin['revision']+':'+path],text=True).strip()==pin['git_blob'],path
for blob,pin in seal['identity_objects'].items():assert sha(subprocess.check_output(['git','cat-file','blob',blob]))==pin['sha256']
commands=[x['command'].split()[-1] for x in c['verification']];assert len(commands)==11
for who in ('author1','reviewer1'):
 rows=load('.agent/evidence/120/controls1-'+who+'-controls-manifest.json')['captures'];assert len(rows)==33
 for i,name in enumerate(commands):
  a,b,d=rows[3*i:3*i+3];assert [x['actual_exit'] for x in (a,b,d)]==[0,1,0] and [x['label'] for x in (a,b,d)]==[name+'-positive',name+'-semantic-red',name+'-restored']
  for row in (a,b,d):
   for key in ('stdout','stderr'):assert sha(P(row[key]).read_bytes())==row[key+'_sha256']
   assert row['protected_before']==row['protected_after']
  assert P(a['stdout']).read_text().strip()==P(d['stdout']).read_text().strip()=='PASS '+name
  assert not P(b['stdout']).read_bytes() and P(b['stderr']).read_text().splitlines()[-1]==b['expected_assertion_line']
rows=load('.agent/evidence/120/controls1-reviewer1-preservation-manifest.json')['captures'];assert len(rows)==30 and [x['actual_exit'] for x in rows]==[0]*26+[1,0,0,0]
for row in rows:
 for key in ('stdout','stderr'):assert sha(P(row[key]).read_bytes())==row[key+'_sha256']
 assert row['protected_before']==row['protected_after']
lines=P('.agent/evidence/120/dev2-default37.stdout.txt').read_text().splitlines();assert len(lines)==37 and all(x.startswith('PASS ') for x in lines) and lines[-11:]==['PASS '+x for x in commands]
assert not subprocess.check_output(['git','diff','--name-only',base,'HEAD','--','.nizam/','schema/','.agent/evidence/118/','tools/convergent_review.py','tools/fixtures/','tools/runtime_session.py','tools/fixtures_self_test.sh','.github/'])
paths=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],text=True).splitlines();patterns=[x['path'] for k in ('files_create','files_modify') for x in c['scope'][k]]
assert all(p.startswith('.agent/evidence/') or any(fnmatch.fnmatchcase(p,q) for q in patterns) for p in paths)
front=yaml.safe_load(P('tools/README.md').read_text().split('---',2)[1]);jsonschema.validate(front,load('.nizam/schema/frontmatter.schema.json'));assert front['version']==front['change_log'][0]['version']=='0.29.1'
assert 'aligned synthetic fixtures prove' in P('tools/README.md').read_text() and 'before live adoption' in P('tools/README.md').read_text()
s=load('.agent/run_state.json');assert s['circuit_breaker']['120-mode-b']=={'attempts':1,'limit':3} and s['scope_budget']['per_feature'][0]['actual']==722 and s['phase_016_scope_budget_final']['total_lines_changed']==5179 and s['phase_017_scope_budget_final']['total_lines_changed']==5203
print('PASS exact approved hash/schema; whole old Source/test AST preserved except approved additions/dispatch; initial Source unchanged;230filepins+17retainedblobs; author33/reviewer33 exact semantic controls;30preservation/default37 receipts; protected payload/pins/workflows; role scope/NDS/knownnamespace limitation/budget archives')
