"""Independent frozen-bundle identity audit and private completion-parser attacks."""
import ast,copy,hashlib,importlib.util,json,stat,subprocess
from pathlib import Path
ROOT=Path.cwd(); E='.agent/evidence/118/'
def read(p):return json.loads(Path(p).read_bytes())
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def load(p):
 s=importlib.util.spec_from_file_location('independent_review_module',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=read(E+'acceptance-bundle.json');h=read(E+'test-author-attempt1-handoff.json');manifest=read(E+'runtime-inputs.json');c=read('.agent/contracts/118.json');a=read(E+'api-interface.json');p=read(E+'producer-interface.json')
assert c['status']=='approved' and c['precode_gate_policy']==a['precode_gate_policy']==p['precode_gate_policy']
assert b['seal_sha256']==h['seal_sha256']==sha(canonical({k:v for k,v in b.items() if k!='seal_sha256'}))
assert b['baseline']==h['baseline'] and b['baseline']['tree']==git('rev-parse',b['baseline']['commit']+'^{tree}').decode().strip()
roles=read(E+'role-sessions.json');assert roles==b['roles']
for key in ['agent_id','session_id']:assert len({r[key] for r in roles.values()})==3 and all(type(r[key]) is str and r[key] for r in roles.values())
assert roles['acceptance_reviewer']=={'agent_id':'/root/wa_validator118','session_id':'/root/wa_validator118'}
assert set(manifest)=={'core_paths','runtime_paths','roles_ref'} and manifest['roles_ref']==E+'role-sessions.json'
assert manifest['core_paths']==a['core_paths']==p['core_paths']
assert len(manifest['runtime_paths'])==len(set(manifest['runtime_paths'])) and not set(manifest['runtime_paths'])&set(manifest['core_paths'])
expected=(set(manifest['core_paths'])|set(manifest['runtime_paths']))-{'tools/workflow_assurance.py'}
assert set(x['path'] for x in b['inputs'])==expected and len(b['inputs'])==len(expected)
for row in b['inputs']:
 path=Path(row['path']);st=path.lstat();assert stat.S_ISREG(st.st_mode)
 raw=path.read_bytes();assert row['sha256']==h['inputs_sha256'][str(path)]==sha(raw)==sha(git('show',b['baseline']['commit']+':'+str(path)))
 mode=git('ls-tree',b['baseline']['commit'],'--',str(path)).decode().split()[0]
 assert type(row['executable']) is bool and row['executable']==bool(st.st_mode&0o111)==(mode=='100755')
print('PASS independently recomputed seal;30 exact frozen Git/current input identities and executable/type modes; three distinct roles')
old=git('show',h['approved_base']+':tools/test_workflow_assurance.py').decode();new=Path('tools/test_workflow_assurance.py').read_text()
old_ast=ast.parse(old);new_ast=ast.parse(new)
old_functions={n.name:ast.get_source_segment(old,n) for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main'}
new_functions={n.name:ast.get_source_segment(new,n) for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main'}
assert old_functions==new_functions
old_assignments=[ast.dump(n) for n in old_ast.body if isinstance(n,ast.Assign)];new_assignments=[ast.dump(n) for n in new_ast.body if isinstance(n,ast.Assign)];assert old_assignments==new_assignments
assert Path('tools/workflow_assurance.py').read_bytes()==git('show',h['approved_base']+':tools/workflow_assurance.py')
assert sha(Path('tools/workflow_assurance.py').read_bytes())==h['source_at_B_sha256']
ledger=read(E+'historical-runtime-inputs.json');assert len(ledger['inputs'])==23
assert len({(r['revision'],r['path']) for r in ledger['inputs']})==23
for row in ledger['inputs']:
 assert sha(git('show',row['revision']+':'+row['path']))==row['sha256']
 mode=git('ls-tree',row['revision'],'--',row['path']).decode().split()[0];assert mode in ('100644','100755') and (mode=='100755') is row['executable']
assert git('rev-parse','refs/tags/'+ledger['tag']+'^{commit}').decode().strip()==ledger['tag_revision']
print('PASS exact prior20 function/class/assignment bytes and unchanged product;23 unique historical Git inputs/modes/tag')
# Capture the author's valid private structural fixture, then originate new mutations.
# This never calls the public closure function or creates a production receipt.
g=load(E+'scope-guard.py');original=g._closure;captured=[]
def observe(contract,values,data):
 if not captured:captured.append((copy.deepcopy(contract),copy.deepcopy(values),copy.deepcopy(data.__self__)))
 return original(contract,values,data)
g._closure=observe;g._private_parser_controls();g._closure=original
contract,values,raw=captured[0]
attacks=[('author-as-ModeB',lambda v,d:v[2].update(actor=roles['test_author']['agent_id'])),('boolean-QA-exit',lambda v,d:v[3]['checks'][0].update(exit_code=False)),('missing-QA-case',lambda v,d:v[3]['checks'].pop()),('foreign-QA-command',lambda v,d:v[3]['checks'][0].update(command='true')),('stale-candidate-tree',lambda v,d:v[3].update(tree='0'*40)),('missing-capture-proof',lambda v,d:v[4]['evidence_sha256'].pop(next(iter(v[4]['evidence_sha256']))))]
for label,mutate in attacks:
 v=copy.deepcopy(values);d=copy.deepcopy(raw);mutate(v,d)
 try:original(contract,v,d.__getitem__)
 except AssertionError as exc:assert str(exc).startswith('POLICY_ASSERTION:');print('PASS reviewer-originated rejection',label,str(exc))
 else:raise AssertionError('Unexpected bypass accepted: '+label)
print('PASS reviewer private-parser attacks; no public completion, source or actual118 prerequisite claimed')
