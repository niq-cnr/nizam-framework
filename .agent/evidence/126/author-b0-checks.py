"""Provisional test-harness checks; not controller acceptance or semantic red."""
import ast,json,os,pathlib,runpy,shlex,subprocess,sys,tempfile
ROOT=pathlib.Path.cwd();TEST=ROOT/'tools/test_runtime_session.py'
source=TEST.read_text();compile(source,str(TEST),'exec');module=runpy.run_path(str(TEST))
print('PASS compile runner',len(source.splitlines()),'lines')
# Compile generated private peer bytes too, without starting a controller/scaffold.
tree=ast.parse(source)
write=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
           and isinstance(n.func.value,ast.Name) and n.func.value.id=='stub' and n.func.attr=='write_text')
peer=eval(compile(ast.Expression(write.args[0]),'<peer-expression>','eval'),
          {'repr':repr,'str':str},{'mode':'dispatch-order','marker':pathlib.Path('/tmp/probe'), 'base':pathlib.Path('/tmp/private')})
compile(peer,'<private-protocol-peer>','exec');print('PASS compile generated private protocol peer')
for args in [[],['--unknown'],['--check','absent'],['--case','4','--runtime','stub'],['--case','1'],
             ['--case','8','--runtime','stub'],['--case','1','--runtime','sbcl'],['--case','1','--runtime','ci'],
             ['--check','record-schema','--layer','policy'],['--check','record-schema','--case','1'],
             ['--check','record-schema','--require-sbcl'],['--check','record-schema','--require-isolation']]:
 p=subprocess.run([sys.executable,str(TEST),*args],text=True,capture_output=True)
 print('SELECTOR',args,'actual_exit',p.returncode);print(p.stdout,end='');print(p.stderr,end='')
 assert p.returncode==2 and 'usage:' in p.stderr and 'SETUP_FAILURE' not in p.stderr
for item in json.load(open('.agent/contracts/126.json'))['verification']:
 argv=shlex.split(item['command'])[1:];argv[0]=sys.executable
 p=subprocess.run(argv,text=True,capture_output=True)
 print('ABSENCE',argv,'actual_exit',p.returncode);print(p.stdout,end='');print(p.stderr,end='')
 assert p.returncode==2 and 'controller source absent; this is not semantic red' in p.stderr
text=(ROOT/'tools/fixtures_self_test.sh').read_text()
with tempfile.TemporaryDirectory(prefix='n126-h-') as scratch:
 module['claim_controls'](scratch,text)
for label,body in [('always-pass','return 0'),('always-reject','return 1')]:
 with tempfile.TemporaryDirectory(prefix='n126-h-') as scratch:
  try: module['claim_controls'](scratch,'claim_map_check() {\n'+body+'\n}')
  except AssertionError as exc: print('PASS harness rejects',label,str(exc))
  else: raise AssertionError('claim controls accepted '+label)
import jsonschema
for stale in (False,True):
 with tempfile.TemporaryDirectory(prefix='n126-h-') as scratch:
  session=module['Session'](scratch);jsonschema.validate(json.load(open(session.runstate)),json.load(open('.nizam/schema/run_state.schema.json')))
  child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
  try:
   token=module['wait_for'](lambda:module['process_token'](child.pid),'scratch cleanup child started')
   session.processes={child.pid:'wrong-token' if stale else token};session.group=child.pid;session.cleanup()
   if stale: assert child.poll() is None
   else: assert child.wait(timeout=2)<0
   print('PASS scratch process-group cleanup; stale PID identity guarded:',stale)
  finally:
   if child.poll() is None:child.terminate()
   child.wait(timeout=2)
print('B0 ONLY: actual new controller/harness transport, semantic red and final acceptance are PENDING')
