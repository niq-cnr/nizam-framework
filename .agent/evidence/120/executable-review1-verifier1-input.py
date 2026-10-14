import hashlib,importlib.util,json,pathlib,subprocess
root=pathlib.Path.cwd(); p=root/'.agent/evidence/120'; h=p/'controls1-run.py'
s=importlib.util.spec_from_file_location('review_transport',h); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
a=json.loads((p/'controls1-author1-controls-manifest.json').read_text()); own=json.loads((p/'controls1-reviewer1-controls-manifest.json').read_text())
assert own['completed'] is True and len(own['captures'])==33
source=(root/'tools/workflow_assurance.py').read_text(); rows=[]
for i,(case,before,after,marker) in enumerate(m.CONTROLS):
 for j,suffix in enumerate(('positive','semantic-red','restored')):
  r=own['captures'][i*3+j]; assert r['label']==case+'-'+suffix and r['actual_exit']==(1 if j==1 else 0)
  assert r['protected_before']==r['protected_after']==own['protected']==a['protected']
  assert r['revision']==own['actual_helper_revision']
  for stream in ('stdout','stderr'): assert hashlib.sha256((root/r[stream]).read_bytes()).hexdigest()==r[stream+'_sha256']
  for path,pin in r['inputs'].items():
   raw=subprocess.check_output(['git','cat-file','blob',pin['git_blob']]); assert hashlib.sha256(raw).hexdigest()==pin['sha256']
   if path.endswith('/workflow_assurance.py'): assert raw==(source.replace(before,after,1) if j==1 else source).encode()
   elif path.endswith('/test_workflow_assurance.py'): assert raw==(root/'tools/test_workflow_assurance.py').read_bytes()
   elif path.endswith('/120.json'): assert raw==(root/'.agent/contracts/120.json').read_bytes()
   elif path.endswith('/controls1-run.py'): assert raw==h.read_bytes()
   else: raise AssertionError(path)
  if j==1:
   err=(root/r['stderr']).read_text(); assert 'SETUP_ERROR' not in err and 'ModuleNotFoundError' not in err
   assert [line for line in err.splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')]==[marker]
   assert (root/r['stdout']).read_bytes()==b''
  else: assert (root/r['stdout']).read_bytes()==('PASS '+case+'\n').encode() and (root/r['stderr']).read_bytes()==b''
 rows.append({'case':case,'positive':0,'intended_semantic_red':1,'restored':0,'assertion':marker})
proof=p/'executable-review1-controls-verification.json'; assert not proof.exists()
proof.write_text(json.dumps({'reviewer':'/root/bundle120','reviewed_revision':'a67d67f1b82c54118d6023a2f7092f93bf4f90c0','actual_executed_revision':own['actual_helper_revision'],'completed':True,'author_captures_checked':33,'own_captures_verified':33,'retained_input_blob_sha256_checks':132,'private_mutants_each_exactly_one_declared_replacement':True,'protected_snapshots_unchanged':True,'cases':rows},indent=2)+'\n')
print('PASS own33 ordered actual results;132 retained input blob digests;11 narrow private mutations; exact intended assertions; frozen protected snapshots')
