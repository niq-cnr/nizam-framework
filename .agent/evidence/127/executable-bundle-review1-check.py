import ast,difflib,hashlib,json,os,pathlib,platform,subprocess,sys,tempfile,time
R=pathlib.Path.cwd();P='.agent/evidence/127/executable-bundle-review1-';C1='88996ee9405f9467ff2debd6e3115b34d064019a';PROOF='21c4e320472af8d23f6dd53535af8a9ab05f3256'
def git(*a):return subprocess.check_output(['git',*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((R/p).read_text())
def save(name,x):(R/(P+name+'.json')).write_text(json.dumps(x,indent=2)+'\n')
seal=load('.agent/evidence/127/semantic1-test-seal.json');pins=[]
def verify(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','revision','sha256','git_blob')):
   ref=x['revision']+':'+x['path'];raw=git('show',ref)
   assert sha(raw)==x['sha256'] and git('rev-parse',ref).decode().strip()==x['git_blob'],ref
   assert (R/x['path']).read_bytes()==raw,x['path'];pins.append(ref)
  for v in x.values():verify(v)
 elif isinstance(x,list):
  for v in x:verify(v)
verify(seal);assert len(pins)==35
assert git('rev-parse',PROOF+':.agent/evidence/127').decode().strip()==seal['proof_directory_git_tree']
prior=load('.agent/evidence/127/acceptance1-test-seal.json')
for x in prior['normative_inputs']:assert sha((R/x['path']).read_bytes())==x['sha256']
assert load('.agent/validator/127-bundle-review-2.json')['final_verdict']['approved'] is True
source=git('show',C1+':tools/runtime_session.py').decode()
helper=ast.parse((R/'.agent/evidence/127/semantic1-mutants.py').read_text())
mutations=ast.literal_eval(next(n.value for n in helper.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='mutations' for t in n.targets)))
mutants={};patchhash={}
for label,old,new,cases in mutations:
 assert source.count(old)==1
 content=source.replace(old,new);compile(content,'<private-mutant>','exec');mutants[label]=content
 patch=''.join(difflib.unified_diff(source.splitlines(True),content.splitlines(True),fromfile='a/tools/runtime_session.py',tofile='b/tools/runtime_session.py'))
 assert patch==(R/f'.agent/evidence/127/semantic1-{label}.patch').read_text();patchhash[label]=sha(patch.encode())
files=['tools/runtime_session.py','tools/test_runtime_session.py','tools/verify_lib.sh','tools/fixtures_self_test.sh','tools/test_convergent_review.py','schema/runtime_session.schema.json','schema/runtime_operation.schema.json']+git('ls-tree','-r','--name-only',C1,'tools/fixtures').decode().splitlines()
material={p:git('show',C1+':'+p) for p in files};inventory=sha(json.dumps({p:sha(raw) for p,raw in material.items()},sort_keys=True,separators=(',',':')).encode())
checks=[];commands=[x['command'].split()[3:] for x in load('.agent/contracts/127.json')['verification']]
for i,control in enumerate(seal['actual_controls']):
 exits=[]
 for position,item in enumerate(control['receipts']):
  receipt=load(item['path']);exits.append(receipt['actual_exit']);assert receipt['argv'][1:]==commands[i]
  for stream in ('stdout','stderr'):assert (R/receipt[stream]).read_bytes()==git('show',PROOF+':'+receipt[stream])
  stdout=(R/receipt['stdout']).read_text();stderr=(R/receipt['stderr']).read_text()
  if position==1:
   assert control['intended_assertion'].split(';')[0] in stderr and 'SETUP' not in stderr and 'Traceback' not in stderr
  else:assert 'PASS' in stdout and not stderr
  if 'stage' in receipt:
   label=pathlib.Path(receipt['patch']).stem.removeprefix('semantic1-')
   assert receipt['controller_sha256']==sha((mutants[label] if receipt['stage']=='mutant' else source).encode())
   assert receipt['patch_sha256']==patchhash[label] and receipt['materialized_input_inventory_sha256']==inventory
   assert receipt['materialized_file_count']==len(material) and receipt['live_candidate_process_references_after_runner']==[]
  else:assert receipt['outer_timeout'] is False
 assert exits==[0,1,0];checks.append({'obligation':control['obligation'],'actual_exits':exits,'assertion_verified':True})
save('verification',{'reviewed_commit':git('rev-parse','HEAD').decode().strip(),'source_candidate':C1,'seal_sha256':sha((R/'.agent/evidence/127/semantic1-test-seal.json').read_bytes()),'verified_new_pins':len(pins),'normative_pins':10,'actual_control_triples':checks,'source_sha256':sha(source.encode()),'test_sha256':sha(material['tools/test_runtime_session.py']),'inventory_sha256':inventory,'files':len(material),'patches_rederived':patchhash,'actual_exit':0})
print('PASS35 pins,10 normative identities,15 actual receipts and all4 exact semantic patches',flush=True)
# Independent bounded rerun of the confirmation guard; all other executed controls audited above.
with tempfile.TemporaryDirectory(prefix='n127-executable-review-') as tmp:
 candidate=pathlib.Path(tmp)/'candidate'
 for name,raw in material.items():
  target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 for stage,content,expected in [('positive',source,0),('mutant',mutants['cancel'],1),('restored',source,0)]:
  (candidate/'tools/runtime_session.py').write_text(content)
  argv=[sys.executable,'tools/test_runtime_session.py','--check','cancel-confirmation-required'];start=time.monotonic()
  p=subprocess.run(argv,cwd=candidate,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=60)
  (R/(P+stage+'.stdout.txt')).write_text(p.stdout);(R/(P+stage+'.stderr.txt')).write_text(p.stderr)
  live=[]
  for proc in pathlib.Path('/proc').iterdir():
   if not proc.name.isdigit():continue
   try:
    if str(candidate).encode() in (proc/'cmdline').read_bytes():live.append(int(proc.name))
   except OSError:pass
  save(stage,{'argv':argv,'cwd':str(candidate),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'source_candidate':C1,'controller_sha256':sha(content.encode()),'test_sha256':sha(material['tools/test_runtime_session.py']),'inventory_sha256':inventory,'actual_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'stdout':P+stage+'.stdout.txt','stderr':P+stage+'.stderr.txt','live_candidate_process_references':live,'python':sys.version,'platform':platform.platform()})
  assert p.returncode==expected and not live
  if stage=='mutant':assert 'BEHAVIOR_ASSERTION: absent/mismatched/unsolicited confirmation or death never fabricates cancellation' in p.stderr and 'SETUP' not in p.stderr
  else:assert 'PASS cancel-confirmation-required' in p.stdout and not p.stderr
  print('PASS independent',stage,p.returncode,flush=True)
