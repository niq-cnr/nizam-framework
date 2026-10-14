import ast,hashlib,json,os,pathlib,runpy,subprocess,sys,tempfile
R=pathlib.Path.cwd(); PREFIX='.agent/evidence/127/bundle-review1-'
def git(*a):return subprocess.check_output(['git',*a])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,x):(R/(PREFIX+name+'.json')).write_text(json.dumps(x,indent=2)+'\n')
seal=json.loads((R/'.agent/evidence/127/acceptance1-test-seal.json').read_text()); identities=[]
def verify(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','revision','sha256','git_blob')):
   ref=x['revision']+':'+x['path']; raw=git('show',ref)
   assert sha(raw)==x['sha256'] and git('rev-parse',ref).decode().strip()==x['git_blob'],ref
   identities.append({'ref':ref,'sha256':sha(raw)})
  for v in x.values():verify(v)
 elif isinstance(x,list):
  for v in x:verify(v)
verify(seal)
raw=(R/'tools/test_runtime_session.py').read_bytes();assert sha(raw)==seal['test']['sha256'];compile(raw,'<sealed-test>','exec')
old=ast.parse(git('show',seal['baseline']+':tools/test_runtime_session.py')); new=ast.parse(raw)
def defs(t):return {n.name:n for n in t.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
a,b=defs(old),defs(new)
changed=[k for k in a if ast.dump(a[k])!=ast.dump(b[k])]
assert changed==['Session','trial_policy','fixture_claim','main'],changed
ma,mb=defs(a['Session']),defs(b['Session']);assert [k for k in ma if ast.dump(ma[k])!=ast.dump(mb[k])]==['call','poll']
assert not git('diff',seal['baseline'],'HEAD','--','tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh')
m=runpy.run_path(str(R/'tools/test_runtime_session.py'))
with tempfile.TemporaryDirectory(prefix='n127-bundle-review-') as h:
 m['claim_controls'](h,(R/'tools/fixtures_self_test.sh').read_text())
with tempfile.TemporaryDirectory(prefix='n127-bundle-review-') as h:
 inputs=m['source_inputs'](h);repo=pathlib.Path(inputs['workspace_path'])
 for entry in inputs['source_manifest']:
  assert sha(subprocess.check_output(['git','-C',str(repo),'show',inputs['source_revision']+':'+entry['path']]))==entry['sha256']
 m['git_fixture'](repo,'worktree','add','--quiet','--detach',str(pathlib.Path(h)/'fresh'),inputs['source_revision'])
 print('PASS committed manifest/template/resource hashes and fresh worktree')
# Execute actual inherited Bash scheduler with harmless argv recorder, no recursive suite.
text=(R/'tools/fixtures_self_test.sh').read_text();function=m['extract_function'](text,'runtime_session_checks')
script="python3() { printf '%s\n' \"$*\"; return 0; }\n"+function+'\nruntime_session_checks\n'
p=subprocess.run(['bash','-c',script],text=True,capture_output=True,timeout=8);assert p.returncode==0
(R/(PREFIX+'scheduler.stdout.txt')).write_text(p.stdout);(R/(PREFIX+'scheduler.stderr.txt')).write_text(p.stderr)
actual=[line.removeprefix('COMMAND: ') for line in p.stdout.splitlines() if line.startswith('COMMAND: ')]
assert len(actual)==9
projection=json.loads((R/'.agent/evidence/127/acceptance1-obligations.json').read_text())
contract=json.loads((R/'.agent/contracts/127.json').read_text());expected=actual+[x['command'] for x in contract['verification']]
differences=[{'position':i+1,'projected':a,'required':b} for i,(a,b) in enumerate(zip(projection['fourteen_commands'],expected)) if a!=b]
assert differences and len(differences)==3
save('findings',{'reviewed_commit':git('rev-parse','HEAD').decode().strip(),'verified_identity_count':len(identities),'identities':identities,'preserved_old_functions_except':changed,'preserved_cleanup_and_crash_regression':True,'scheduler_actual_exit':p.returncode,'required_fourteen_commands':expected,'sealed_projection_order_disagreement':differences,'note':'Runner fixture_claim uses inherited actual order correctly; only sealed obligation projection is inconsistent.'})
argv=[sys.executable,'tools/test_runtime_session.py','--case','1','--runtime','stub'];p=subprocess.run(argv,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=35)
(R/(PREFIX+'inherited-positive.stdout.txt')).write_text(p.stdout);(R/(PREFIX+'inherited-positive.stderr.txt')).write_text(p.stderr)
save('inherited-positive-result',{'argv':argv,'actual_exit':p.returncode,'source_sha256':sha((R/'tools/runtime_session.py').read_bytes()),'test_sha256':sha(raw),'stdout':PREFIX+'inherited-positive.stdout.txt','stderr':PREFIX+'inherited-positive.stderr.txt','boundary':'Inherited126 working ownership transport only, not127 semantic red or new capability.'})
assert p.returncode==0 and 'PASS' in p.stdout
print('PASS',len(identities),'sealed identities; prior checks/cleanup/crash preserved; inherited real transport0')
print('CONFIRMED sealed fourteen_commands differs at positions',[x['position'] for x in differences])
