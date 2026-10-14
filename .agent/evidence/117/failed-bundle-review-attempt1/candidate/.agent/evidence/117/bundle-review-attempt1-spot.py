"""Independent seal audit and typed-actor negative; mutations only in private scratch."""
import contextlib,copy,hashlib,importlib.metadata,importlib.util,io,json,pathlib,platform,shutil,stat,subprocess,tempfile
r=pathlib.Path.cwd(); e=r/'.agent/evidence/117'; b=json.loads((e/'acceptance-bundle.json').read_text())
def sha(x):return hashlib.sha256(x).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def git(*args):return subprocess.check_output(['git',*args])
without=copy.deepcopy(b);without.pop('seal_sha256');assert sha(canonical(without))==b['seal_sha256']=='6b7b30eb06141ea321454beb065d3728caab04b8ba17c3d9b5055c57c695722a'
B=b['baseline']['commit'];assert git('rev-parse',B+'^{tree}').decode().strip()==b['baseline']['tree']
assert len(b['inputs'])==26 and len({v['path'] for v in b['inputs']})==26
for v in b['inputs']:
 p=r/v['path'];assert stat.S_ISREG(p.lstat().st_mode) and not p.is_symlink();assert sha(p.read_bytes())==v['sha256']==sha(git('show',B+':'+v['path']))
 mode=git('ls-tree',B,v['path']).decode().split()[0];assert type(v['executable']) is bool and v['executable']==bool(p.stat().st_mode&0o111)==(mode=='100755')
for row in b['baseline_evidence']:
 for stage in ('setup','positive','red'):
  v=row[stage];assert sha((r/v['path']).read_bytes())==v['sha256']
for v in b['immutable_git_anchors']: assert git('rev-parse',v['revision']+'^{tree}').decode().strip()==v['tree']
actual={'python':platform.python_version(),'implementation':platform.python_implementation(),'system':platform.system(),'machine':platform.machine(),'git':git('--version').decode().strip(),'jsonschema':importlib.metadata.version('jsonschema'),'PyYAML':importlib.metadata.version('PyYAML')}
assert actual==b['environment']
roles=b['roles'];assert json.loads((e/'role-sessions.json').read_text())==roles
for key in ('agent_id','session_id'):assert len({v[key] for v in roles.values()})==3
snap=json.loads((e/'source-obligations.json').read_text());assert snap['api']==json.loads((e/'api-interface.json').read_text())
assert snap['contract']==json.loads(git('show',snap['approved_revision']+':.agent/contracts/117.json'))
old=git('show','99f51caea4a19e7b4105ca186c5bcdaa946ad371:tools/test_workflow_assurance.py');now=(r/'tools/test_workflow_assurance.py').read_bytes();assert old.split(b'def main():')[0]==now.split(b'PRE_ENTRY_CASES = CASES')[0]
assert sha((r/'tools/workflow_assurance.py').read_bytes())=='402eea15a23556b708da6a8c812bdcaaf9833c7b43dc9390a5817ebe3cf312d8'
print('PASS exact seal,26 current/GitB/type/mode inputs,12 proof hashes,all Git anchors,actual environment,distinct roles,snapshot and existing115116 bytes',flush=True)
spec=importlib.util.spec_from_file_location('independent_scope117',e/'scope-guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
with tempfile.TemporaryDirectory(prefix='reviewer117-typed-actor-') as parent:
 scratch=pathlib.Path(parent)/'repo';subprocess.run(['git','clone','-q','--shared','--no-checkout',str(r),str(scratch)],check=True)
 subprocess.run(['git','-C',str(scratch),'checkout','-q',guard.APPROVED],check=True)
 guard.ROOT=scratch
 paths={v['path'] for v in b['inputs']}|{guard.BUNDLE}
 for row in b['baseline_evidence']:paths.update(row[k]['path'] for k in ('setup','positive','red'))
 for path in paths:
  target=scratch/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/path,target)
 reviewer=roles['acceptance_reviewer'];guard.write(guard.REVIEW,{'review':'validator-test-bundle-review','feature':'117','actor':reviewer['agent_id'],'reviewer_session_id':reviewer['session_id'],'seal_sha256':b['seal_sha256'],'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],'final_verdict':{'approved':True,'summary':'PRIVATE structural parser fixture only'}})
 guard._private_complete_fixture()
 try:guard.scope(guard.BASE)
 except AssertionError as exc:assert 'mock receipts confined' in str(exc);print('PASS public completion refuses private mock receipts',flush=True)
 else:raise AssertionError('public mock false-pass')
 guard._CONTROL_FIXTURE=scratch.resolve()
 with contextlib.redirect_stdout(io.StringIO()):guard._scope(guard.BASE)
 print('PASS genuinely valid private completion parser baseline with string actors',flush=True)
 mode=guard.current(guard.MODE_B);mode['actor']=True;guard.write(guard.MODE_B,mode)
 capture=guard.current(guard.CAPTURE);capture['mode_b_sha256']=guard.sha(guard.safe(guard.MODE_B).read_bytes());guard.write(guard.CAPTURE,capture)
 try:
  with contextlib.redirect_stdout(io.StringIO()):guard._scope(guard.BASE)
 except AssertionError as exc:
  print('PASS invalid Boolean ModeB actor rejected: '+str(exc),flush=True)
 else:
  print('OBSERVED_FALSE_PASS: canonical completed117 parser accepts ModeB actor Boolean true with matching updated capture hash',flush=True)
  raise AssertionError('POLICY_ASSERTION: producer requires nonempty string actor; Boolean is not an independent actor identity')
