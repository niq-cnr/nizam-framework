"""Run sealed tests on narrow private C1 mutants, then exact restored C1 bytes."""
import ast,difflib,hashlib,json,os,pathlib,subprocess,sys,tempfile,time
R=pathlib.Path(__file__).resolve().parents[3]; E=R/'.agent/evidence/127'
C1='88996ee9405f9467ff2debd6e3115b34d064019a'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path):return subprocess.check_output(['git','show',C1+':'+path],cwd=R)
source=blob('tools/runtime_session.py').decode(); test=blob('tools/test_runtime_session.py')
assert sha(test)=='3628f1b2b833a0f504cced79252391ff213bd75197dd2d5261494fbb646eb12e'
files=['tools/runtime_session.py','tools/test_runtime_session.py','tools/verify_lib.sh','tools/fixtures_self_test.sh','tools/test_convergent_review.py','schema/runtime_session.schema.json','schema/runtime_operation.schema.json']
files+=subprocess.check_output(['git','ls-tree','-r','--name-only',C1,'tools/fixtures'],cwd=R,text=True).splitlines()
material={path:blob(path) for path in files}; inventory_sha=sha(json.dumps({p:sha(b) for p,b in material.items()},sort_keys=True,separators=(',',':')).encode())
mutations=[
 ('cancel',"record['status'] == 'cancel_requested' and value['cancellation_confirmed'] is True", "record['status'] == 'cancel_requested'",[('cancel',['--check','cancel-confirmation-required'])]),
 ('manifest',"for raw in (committed, path.read_bytes())", "for raw in (committed,)",[('handoff',['--check','handoff-source-bound']),('replay',['--case','10','--runtime','stub'])]),
 ('wait',"            atomic_json(path, record)\n        return (response_error('infrastructure', record)","            if expired and record['status'] not in TERMINAL:\n                record['status'] = 'cancelled'\n            atomic_json(path, record)\n        return (response_error('infrastructure', record)",[('wait',['--case','5','--runtime','stub'])]),
 ('reattach',"if request['expected_outstanding_operation_ref'] != self.session.get('outstanding_operation_ref'):","if False:  # private mutant bypasses only pending snapshot equality",[('reattach',['--case','6','--runtime','stub'])])]
def live_refs(path):
 found=[]
 for proc in pathlib.Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   cmd=(proc/'cmdline').read_bytes()
   if str(path).encode() in cmd:found.append(int(proc.name))
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 return found
for mutant,old,new,cases in mutations:
 assert source.count(old)==1,(mutant,source.count(old)); changed=source.replace(old,new)
 ast.parse(changed)
 patch=''.join(difflib.unified_diff(source.splitlines(True),changed.splitlines(True),fromfile='a/tools/runtime_session.py',tofile='b/tools/runtime_session.py'))
 patchfile=E/f'semantic1-{mutant}.patch';assert not patchfile.exists();patchfile.write_text(patch)
 with tempfile.TemporaryDirectory(prefix='nizam127-semantic-') as tmp:
  candidate=pathlib.Path(tmp)/'candidate'
  for path,data in material.items():
   dst=candidate/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
  controller=candidate/'tools/runtime_session.py'
  for stage,content in [('mutant',changed),('restored',source)]:
   controller.write_text(content);assert (candidate/'tools/test_runtime_session.py').read_bytes()==test
   for case,args in cases:
    name=f'semantic1-{mutant}-{stage}-{case}';prefix=E/name;assert not prefix.with_suffix('.json').exists()
    argv=[sys.executable,'tools/test_runtime_session.py',*args];start=time.monotonic()
    p=subprocess.run(argv,cwd=candidate,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=150)
    prefix.with_suffix('.stdout.txt').write_text(p.stdout);prefix.with_suffix('.stderr.txt').write_text(p.stderr)
    refs=live_refs(candidate)
    result={'argv':argv,'cwd':str(candidate),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'source_candidate':C1,'test_sha256':sha(test),'controller_sha256':sha(content.encode()),'base_controller_sha256':sha(source.encode()),'materialized_input_inventory_sha256':inventory_sha,'materialized_file_count':len(material),'patch':str(patchfile.relative_to(R)),'patch_sha256':sha(patch.encode()),'stage':stage,'actual_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'stdout':str(prefix.with_suffix('.stdout.txt').relative_to(R)),'stderr':str(prefix.with_suffix('.stderr.txt').relative_to(R)),'live_candidate_process_references_after_runner':refs,'classification':'pending exact assertion assessment; private mutant is not pristine-base red'}
    prefix.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(name,p.returncode,p.stdout[-250:],p.stderr[-1600:],flush=True)
    assert not refs,('owned candidate process remains; no unverified process will be signalled',refs)
    if p.returncode!=(1 if stage=='mutant' else 0):raise SystemExit('unexpected control exit; preserve exact output before any follow-up')
