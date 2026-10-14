"""Independent immutable-C1 semantic controls; never changes shared product/tests."""
import difflib,hashlib,importlib.metadata,json,os,pathlib,platform,subprocess,sys,tempfile
ROOT=pathlib.Path.cwd();OUT=ROOT/'.agent/evidence/126/semantic-controls';C1='755b859703de29065885ccd7bc6031dabb702872'
TEST_SHA='60f6797100f15eb32b4f9e870eafe699627d17b835c8cc2ad44b703fcfb67e14'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args])
seal=json.load(open(ROOT/'.agent/evidence/126/test-seal-b0-2.json'))
for e in [seal['test'],seal['api'],seal['obligation_projection'],*seal['normative_inputs']]:assert sha((ROOT/e['path']).read_bytes())==e['sha256'],e['path']
assert sha((ROOT/'.agent/contracts/126.json').read_bytes())=='7eed25daca89c13a548976a213ddba6e6837acaee90511f0deff152a60697778'
paths=['tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/test_runtime_session.py','tools/verify_lib.sh','schema/runtime_session.schema.json','schema/runtime_operation.schema.json']
files={p:git('show',C1+':'+p) for p in paths};assert sha(files['tools/test_runtime_session.py'])==TEST_SHA
manifest={'c1_commit':C1,'c1_tree':git('rev-parse',C1+'^{tree}').decode().strip(),'evaluator_revision':git('rev-parse','HEAD').decode().strip(),'files':{p:{'git_blob':git('rev-parse',C1+':'+p).decode().strip(),'sha256':sha(raw)} for p,raw in files.items()},'runtime':{'python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),'jsonschema_version':importlib.metadata.version('jsonschema')},'test_sha256':TEST_SHA,'boundary':'Only the six immutable required files are materialized; no nested repository/evidence copy. Each sealed test invocation creates fresh private runtime state.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
old=b"        if actor != self.session['owner'] and not (permit_orchestrator and lifecycle(actor)):\n"
new=b"        if actor != self.session['owner'] and not (permit_orchestrator and lifecycle(actor)) and not (actor.get('principal_kind') == 'agent' and actor.get('role') == 'Generator'):\n"
assert files['tools/runtime_session.py'].count(old)==1
mutated=files['tools/runtime_session.py'].replace(old,new);compile(mutated,'<private-C1-foreign-owner-mutant>','exec')
(OUT/'foreign-owner-bypass.patch').write_text(''.join(difflib.unified_diff(files['tools/runtime_session.py'].decode().splitlines(True),mutated.decode().splitlines(True),fromfile='C1/tools/runtime_session.py',tofile='private-mutant/tools/runtime_session.py')))
mutation={'name':'foreign-owner-admission-bypass','source_path':'tools/runtime_session.py','original_sha256':sha(files['tools/runtime_session.py']),'mutant_sha256':sha(mutated),'changed_guard_count':1,'test_sha256':TEST_SHA,'patch':'.agent/evidence/126/semantic-controls/foreign-owner-bypass.patch','effect':'Only bypass foreign-owner comparison for a well-shaped Generator requester. Existing role, generation, lease, attempt, transport, response and execution paths remain intact. No fabricated response or test change.'}
(OUT/'mutation.json').write_text(json.dumps(mutation,indent=2)+'\n')
results=[]
def run(label,is_mutant=False):
 with tempfile.TemporaryDirectory(prefix='n126-sem-') as home:
  candidate=pathlib.Path(home)
  for name,raw in files.items():
   target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(mutated if is_mutant and name=='tools/runtime_session.py' else raw)
  assert sha((candidate/'tools/test_runtime_session.py').read_bytes())==TEST_SHA
  argv=[sys.executable,'tools/test_runtime_session.py','--case','1','--runtime','stub'];env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
  p=subprocess.run(argv,cwd=candidate,env=env,text=True,capture_output=True,timeout=45)
  stdout=OUT/(label+'.stdout.txt');stderr=OUT/(label+'.stderr.txt');stdout.write_text(p.stdout);stderr.write_text(p.stderr)
  record={'label':label,'argv':argv,'cwd':str(candidate),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'actual_exit':p.returncode,'stdout':str(stdout.relative_to(ROOT)),'stderr':str(stderr.relative_to(ROOT)),'manifest':'.agent/evidence/126/semantic-controls/manifest.json','c1_commit':C1,'source_sha256':sha(mutated if is_mutant else files['tools/runtime_session.py']),'test_sha256':TEST_SHA,'mutated':is_mutant,'runtime':manifest['runtime'],'cleanup':'Sealed runner finally-cleanup executes before this private TemporaryDirectory is removed; run returned normally without subprocess timeout.'}
  (OUT/(label+'.result.json')).write_text(json.dumps(record,indent=2)+'\n');results.append(record)
  print(label,'actual_exit',p.returncode);print(p.stdout,end='');print(p.stderr,end='')
  return p
first=run('01-unmodified-positive')
status='blocked: unmodified C1 failed; no mutant red credited'
if first.returncode==0 and 'PASS case1/stub' in first.stdout:
 mutant=run('02-foreign-owner-mutant',True)
 intended=mutant.returncode==1 and 'BEHAVIOR_ASSERTION: submit-operation exit 0, expected 1:' in mutant.stderr and 'SETUP' not in mutant.stderr
 last=run('03-fresh-unmodified-positive')
 status='paired intended semantic mutant red observed' if intended and last.returncode==0 and 'PASS case1/stub' in last.stdout else 'control failed: preserve actual output, do not claim intended paired red'
(OUT/'handoff.json').write_text(json.dumps({'author':'/root/acceptance126','stage':'independent C1 transport/semantic controls only','status':status,'c1_commit':C1,'test_sha256':TEST_SHA,'runs':[str((OUT/(r['label']+'.result.json')).relative_to(ROOT)) for r in results],'plan':'.agent/evidence/126/semantic-control-plan.json','manifest':'.agent/evidence/126/semantic-controls/manifest.json','mutation':'.agent/evidence/126/semantic-controls/mutation.json','not_claimed':['pristine-base semantic red','final bundle approval','Mode B or fresh final QA','capable CI live-case acceptance'],'source_or_test_repairs':False},indent=2)+'\n');print('HANDOFF:',status)
