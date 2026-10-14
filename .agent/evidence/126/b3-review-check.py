import ast, hashlib, json, pathlib, subprocess, sys
ROOT=pathlib.Path.cwd()
OUT=ROOT/'.agent/evidence/126/b3-review-controls'
OUT.mkdir(exist_ok=False)
def git(*args): return subprocess.check_output(['git',*args])
def sha(data): return hashlib.sha256(data).hexdigest()
seal_path=ROOT/'.agent/evidence/126/test-seal-b3.json'
seal=json.loads(seal_path.read_text()); verified=[]
def verify(node):
 if isinstance(node,dict):
  if all(k in node for k in ('path','sha256','git_blob')):
   rev=node.get('revision','HEAD'); ref=rev+':'+node['path']; raw=git('show',ref)
   assert sha(raw)==node['sha256'], ref
   assert git('rev-parse',ref).decode().strip()==node['git_blob'], ref
   if node.get('revision')!=seal['preserved_old_test']['revision'] or node['path']!='tools/test_runtime_session.py':
    assert (ROOT/node['path']).read_bytes()==raw, node['path']
   verified.append({'ref':ref,'sha256':sha(raw)})
  for value in node.values(): verify(value)
 elif isinstance(node,list):
  for value in node: verify(value)
verify(seal)
assert sha((ROOT/'.agent/contracts/126.json').read_bytes())==seal['contract_sha256']
old=ast.parse(git('show',seal['preserved_old_test']['revision']+':tools/test_runtime_session.py'))
new=ast.parse((ROOT/'tools/test_runtime_session.py').read_bytes())
def functions(tree):
 return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=functions(old),functions(new)
assert set(b)-set(a)=={'crash_disagreement'}
assert [k for k in a if a[k]!=b[k]]==['Session','records']
oldclass=next(n for n in old.body if isinstance(n,ast.ClassDef)); newclass=next(n for n in new.body if isinstance(n,ast.ClassDef))
x,y=functions(oldclass),functions(newclass)
assert x.keys()==y.keys() and [k for k in x if x[k]!=y[k]]==['call']
r=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='records')
assert ast.unparse(r.body.pop())=='crash_disagreement(s.home)'
assert ast.dump(r,include_attributes=False)==a['records']
manifest={'reviewer':'/root/capability_review','reviewed_commit':git('rev-parse','HEAD').decode().strip(),'seal_sha256':sha(seal_path.read_bytes()),'verified_identity_count':len(verified),'verified':verified,'protected_test_structure':'All preexisting top-level functions unchanged except records appends crash_disagreement; all Session methods unchanged except reviewed integer-equivalent call envelope checking.','actual_exit':0}
(OUT/'identity-review.json').write_text(json.dumps(manifest,indent=2)+'\n')
runner=(ROOT/'.agent/evidence/126/crash-regression3/run-final-controls.py').read_text()
runner=runner.replace('.agent/evidence/126/crash-regression3/final','.agent/evidence/126/b3-review-controls').replace("'author':'/root/acceptance126'", "'reviewer':'/root/capability_review'")
(OUT/'rerun-driver.py').write_text(runner)
p=subprocess.run([sys.executable,str(OUT/'rerun-driver.py')],capture_output=True,text=True)
(OUT/'driver.stdout.txt').write_text(p.stdout); (OUT/'driver.stderr.txt').write_text(p.stderr)
(OUT/'driver-result.json').write_text(json.dumps({'argv':[sys.executable,str(OUT/'rerun-driver.py')],'actual_exit':p.returncode,'reviewed_commit':manifest['reviewed_commit'],'stdout':'.agent/evidence/126/b3-review-controls/driver.stdout.txt','stderr':'.agent/evidence/126/b3-review-controls/driver.stderr.txt','derivation':'Reexecuted inspected author driver; only output paths and author attribution changed. Immutable source/test bytes independently checked above.'},indent=2)+'\n')
print('identity_checks',len(verified),'control_driver_exit',p.returncode); print(p.stdout); print(p.stderr)
sys.exit(p.returncode)
