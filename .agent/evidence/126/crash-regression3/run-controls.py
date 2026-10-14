"""Execute the committed independent crash regression against immutable C2/C3."""
import ast,difflib,hashlib,importlib.metadata,json,os,pathlib,platform,subprocess,sys,tempfile
ROOT=pathlib.Path.cwd();OUT=ROOT/'.agent/evidence/126/crash-regression3';TEST_REV='43fb052e305816bfbafce3d82feaf9b69a01926b';C2='b6c0b097ecf2e12ee638a60273af568a8b86523a';C3='c40975126ff1f42cad1906355b81e62b0894bd1c'
def git(*args):return subprocess.check_output(['git',*args])
def sha(raw):return hashlib.sha256(raw).hexdigest()
paths=['tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/verify_lib.sh','schema/runtime_session.schema.json','schema/runtime_operation.schema.json']
test=git('show',TEST_REV+':tools/test_runtime_session.py');assert sha(test)=='4bd422c7e95430dce33efb560b7b6249e28ab51f49e930127cc645cc48d1ccbe';compile(test,'<committed-B3-test>','exec')
function=next(n for n in ast.parse(test).body if isinstance(n,ast.FunctionDef) and n.name=='crash_disagreement')
fault=next(n.args[1].value for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='lines' and n.func.attr=='insert')
runtime={'python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),'jsonschema_version':importlib.metadata.version('jsonschema')}
summary=[]
for label,revision,expected in [('C2',C2,1),('C3',C3,0)]:
 files={p:git('show',revision+':'+p) for p in paths};files['tools/test_runtime_session.py']=test
 source=files['tools/runtime_session.py'].decode();publisher=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='atomic_json');lines=source.splitlines(keepends=True);lines.insert(publisher.end_lineno,fault);injected=''.join(lines)
 (OUT/(label+'-fault.patch')).write_text(''.join(difflib.unified_diff(source.splitlines(True),injected.splitlines(True),fromfile=label+'/tools/runtime_session.py',tofile='private-crash/tools/runtime_session.py')))
 manifest={'source_revision':revision,'source_tree':git('rev-parse',revision+'^{tree}').decode().strip(),'test_revision':TEST_REV,'test_sha256':sha(test),'test_blob':git('rev-parse',TEST_REV+':tools/test_runtime_session.py').decode().strip(),'files':{p:{'revision':TEST_REV if p=='tools/test_runtime_session.py' else revision,'sha256':sha(raw),'git_blob':git('rev-parse',(TEST_REV if p=='tools/test_runtime_session.py' else revision)+':'+p).decode().strip()} for p,raw in files.items()},'private_fault_source_sha256':sha(injected.encode()),'runtime':runtime,'fault':'Original atomic_json publishes and fsyncs first; test-only AST-placed wrapper exits86 once after a running operation publication, before dispatch; no production hook.'}
 (OUT/(label+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
 with tempfile.TemporaryDirectory(prefix='n126-reg3-') as home:
  candidate=pathlib.Path(home)
  for name,raw in files.items():
   target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  argv=[sys.executable,'tools/test_runtime_session.py','--check','record-schema'];p=subprocess.run(argv,cwd=candidate,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=55)
  (OUT/(label+'.stdout.txt')).write_text(p.stdout);(OUT/(label+'.stderr.txt')).write_text(p.stderr)
  record={'argv':argv,'cwd':str(candidate),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'actual_exit':p.returncode,'expected_exit':expected,'stdout':'.agent/evidence/126/crash-regression3/'+label+'.stdout.txt','stderr':'.agent/evidence/126/crash-regression3/'+label+'.stderr.txt','manifest':'.agent/evidence/126/crash-regression3/'+label+'-manifest.json','source_revision':revision,'test_revision':TEST_REV,'test_sha256':sha(test),'runtime':runtime,'cleanup':'Returned normally via sealed finally cleanup. Unexpected successful C2 reopen is registered with private ownership proof before the assertion, so replacement children are stopped before temporary roots are removed.'}
  (OUT/(label+'-result.json')).write_text(json.dumps(record,indent=2)+'\n');summary.append(record)
  print(label,'actual_exit',p.returncode);print(p.stdout,end='');print(p.stderr,end='')
  assert p.returncode==expected and 'CONTROL crash: real transport and clean restart positive' in p.stdout and manifest['private_fault_source_sha256'] in p.stdout
  if label=='C2':assert 'BEHAVIOR_ASSERTION: crash disagreement must refuse reopen before a new incarnation' in p.stderr and 'SETUP' not in p.stderr
  else:assert 'CONTROL crash: ambiguous reopen and fresh dispatch refused; evidence preserved' in p.stdout and 'PASS record-schema' in p.stdout
(OUT/'control-summary.json').write_text(json.dumps({'author':'/root/acceptance126','test_revision':TEST_REV,'test_sha256':sha(test),'C2_actual_exit':summary[0]['actual_exit'],'C3_actual_exit':summary[1]['actual_exit'],'intended_assertion':'BEHAVIOR_ASSERTION: crash disagreement must refuse reopen before a new incarnation','positive_control':'Each actual check ran real set/get and clean closed restart before fault; C3 also refused ambiguous reopen and new dispatch while preserving evidence/attempt bytes.','boundary':'Existing contract crash-disagreement regression/control only; not pristine-base red or final QA/CI/feature acceptance.'},indent=2)+'\n')
