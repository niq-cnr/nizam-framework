import hashlib,json,pathlib,subprocess
R=pathlib.Path.cwd();oldrev='3040ff032d2e5a0f1b0a5669447ce3268402e5fc'
def git(*a):return subprocess.check_output(['git',*a])
def load(p):return json.loads((R/p).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
seal=load('.agent/evidence/127/acceptance2-test-seal.json'); oldseal=load('.agent/evidence/127/acceptance1-test-seal.json');pins=[]
def verify(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','revision','sha256','git_blob')):
   ref=x['revision']+':'+x['path']; raw=git('show',ref)
   assert sha(raw)==x['sha256'] and git('rev-parse',ref).decode().strip()==x['git_blob'],ref
   pins.append(ref)
  for v in x.values():verify(v)
 elif isinstance(x,list):
  for v in x:verify(v)
verify(oldseal);assert len(pins)==70;verify(seal)
path='.agent/evidence/127/acceptance1-obligations.json';a=json.loads(git('show',oldrev+':'+path));b=load(path)
expected=load('.agent/evidence/127/bundle-review1-findings.json')['required_fourteen_commands']
assert b['fourteen_commands']==expected
changed=[i+1 for i,(x,y) in enumerate(zip(a['fourteen_commands'],b['fourteen_commands'])) if x!=y];assert changed==[7,8,9]
a['fourteen_commands']=b['fourteen_commands'];assert a==b
assert sha((R/path).read_bytes())=='904ac202d71652ab07875f89e20234d6d8f4892d12600e7a75c458203ebb4ec2'
protected=['tools/test_runtime_session.py','.agent/evidence/127/runtime-api127.json','.agent/contracts/127.json','tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh','.nizam','.agent/evidence/127/acceptance1-test-seal.json','.agent/evidence/127/acceptance1-handoff.json']
assert not git('diff',oldrev,'HEAD','--',*protected)
assert git('diff-tree','--no-commit-id','--name-only','-r',seal['correction_revision']).decode().splitlines()==[path]
for name in ('bundle-review1-findings.json','bundle-review1-execution.json','bundle-review1-inherited-positive-result.json','bundle-review1-peer-compilation.json'):
 p='.agent/evidence/127/'+name;assert git('show','df91bf7434f5ca46e3acd3d9450b79b56aa5a445:'+p)==(R/p).read_bytes()
result={'reviewed_commit':git('rev-parse','HEAD').decode().strip(),'new_seal_sha256':sha((R/'.agent/evidence/127/acceptance2-test-seal.json').read_bytes()),'verified_immutable_pins':len(pins),'prior_pin_count':70,'changed_projection_positions':changed,'exact_required_fourteen_commands':True,'test_sha256':sha((R/'tools/test_runtime_session.py').read_bytes()),'api_sha256':sha((R/'.agent/evidence/127/runtime-api127.json').read_bytes()),'corrected_projection_sha256':sha((R/path).read_bytes()),'protected_inputs_unchanged':True,'prior_independent_controls_unchanged':True,'actual_exit':0,'boundary':'Delta identity/scope review only; prior executed controls reused unchanged, no127 capability or semantic-red inference.'}
(R/'.agent/evidence/127/bundle-review2-check-result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS corrected exact14 order, only positions7-9 changed; runner/API/source/contract unchanged;70 prior and10 delta pins verified')
