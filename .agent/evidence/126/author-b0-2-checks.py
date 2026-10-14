"""Bounded author repair2 controls; no controller acceptance or semantic red."""
import ast,fcntl,io,json,os,pathlib,runpy,signal,subprocess,sys,tempfile,threading,time
from unittest.mock import patch
root=pathlib.Path.cwd();test=root/'tools/test_runtime_session.py';source=test.read_text();compile(source,str(test),'exec');m=runpy.run_path(str(test))
print('PASS syntax',len(source.splitlines()),'lines')
for args in [['--chec','record-schema'],['--case','1','--runt','stub'],['--check','record-schema','--require-isol']]:
 p=subprocess.run([sys.executable,str(test),*args],text=True,capture_output=True)
 assert p.returncode==2 and 'usage:' in p.stderr and 'SETUP_FAILURE' not in p.stderr
 print('PASS B0-3 parser-before-source',args,'actual_exit',p.returncode);print(p.stderr,end='')
p=subprocess.run([sys.executable,str(test),'--check','record-schema'],text=True,capture_output=True)
assert p.returncode==2 and 'not semantic red' in p.stderr
print('SOURCE ABSENCE ONLY actual_exit',p.returncode,p.stderr.strip())
# The reviewer's unrelated-process reproducer, using only our own disposable child.
with tempfile.TemporaryDirectory(prefix='n126-fix-') as home:
 s=m['Session'](home);s.directory.mkdir(parents=True)
 p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
 try:
  token=m['wait_for'](lambda:m['process_token'](p.pid),'own unrelated control starts')
  (s.directory/'controller.json').write_text(json.dumps({'supervisor_pid':p.pid,'child_pid':p.pid,'supervisor_pgid':p.pid}))
  try:s.remember()
  except AssertionError:pass
  else:raise AssertionError('unrelated metadata registered')
  assert not s.processes;s.cleanup();assert p.poll() is None
  # Even a previously injected token cannot bypass the proof immediately before a signal.
  s.processes={p.pid:token};s.group=s.supervisor=p.pid;s.cleanup();assert p.poll() is None
  print('PASS B0-1 live unrelated control survived registration refusal and pre-signal ownership check')
 finally:p.terminate();p.wait(timeout=2)
# Actual private lock/child topology, including an inherited open-file-description lock.
for inherited,stale in [(False,False),(True,False),(False,True)]:
 with tempfile.TemporaryDirectory(prefix='n126-fix-') as home:
  base=pathlib.Path(home);candidate=base/'candidate';stub=candidate/'tools/fixtures/runtime_session/stub_runtime.py';stub.parent.mkdir(parents=True);stub.write_text('import time\ntime.sleep(30)\n')
  s=m['Session'](base,candidate=candidate);s.directory.mkdir(parents=True);supervisor=base/'supervisor.py'
  supervisor.write_text('''import fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
d=Path(sys.argv[1]); inherited=int(sys.argv[3])
f=os.fdopen(inherited,'a') if inherited>=0 else (d/'supervisor.lock').open('a')
if inherited<0:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
child=subprocess.Popen([sys.executable,sys.argv[2]])
def stop(*args):raise SystemExit
signal.signal(signal.SIGTERM,stop)
try:
 (d/'controller.json').write_text(json.dumps({'supervisor_pid':os.getpid(),'child_pid':child.pid,'supervisor_pgid':os.getpgrp()}))
 time.sleep(30)
finally:
 if child.poll() is None:child.terminate()
 child.wait(timeout=2)
''')
  held=(s.directory/'supervisor.lock').open('a') if inherited else None
  if held:fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  p=subprocess.Popen([sys.executable,str(supervisor),str(s.directory),str(stub),str(held.fileno()) if held else '-1'],start_new_session=True,pass_fds=(held.fileno(),) if held else ())
  if held:held.close()
  try:
   def metadata():
    try:return json.loads((s.directory/'controller.json').read_text())
    except (FileNotFoundError,ValueError):return None
   meta=m['wait_for'](metadata,'private owner metadata ready');m['wait_for'](lambda:s.runs_stub(meta['child_pid']),'private child exec ready')
   s.remember();assert set(s.processes)=={p.pid,meta['child_pid']}
   if stale:s.processes={pid:'reused-token' for pid in s.processes}
   s.cleanup()
   if stale:assert p.poll() is None and m['process_token'](meta['child_pid'])
   else:assert p.wait(timeout=2) in (0,-signal.SIGTERM,-signal.SIGKILL);m['wait_for'](lambda:not m['process_token'](meta['child_pid']),'private child stopped')
   print('PASS B0-1 legitimate cleanup and token guard; inherited_lock=',inherited,'stale_token=',stale)
  finally:
   if p.poll() is None:p.terminate()
   p.wait(timeout=2)
# Replay the exact generated peer; hold publication after delivering its result.
tree=ast.parse(source);write=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='stub' and n.func.attr=='write_text')
with tempfile.TemporaryDirectory(prefix='n126-fix-') as home:
 base=pathlib.Path(home);marker=base/'sent.json';operation=base/'state/one/operations/first.json';operation.parent.mkdir(parents=True);operation.write_text('{"operation_id":"first","status":"running"}')
 peer=eval(compile(ast.Expression(write.args[0]),'<peer-expression>','eval'),{'repr':repr,'str':str},{'mode':'late-frame','marker':marker,'base':base});compile(peer,'<exact-peer>','exec')
 sent,waiting,publish=threading.Event(),threading.Event(),threading.Event();frames=[];errors=[];returned=[];original_replace=os.replace
 def emit(fd,data):
  frame=json.loads(data);frames.append(frame)
  if frame.get('type')=='result':sent.set()
  return len(data)
 def delayed_replace(src,dst):
  waiting.set();assert publish.wait(3);return original_replace(src,dst)
 def run_peer():
  try:exec(compile(peer,'<exact-peer>','exec'),{})
  except BaseException as e:errors.append(repr(e))
 generation={'counter':1,'nonce':'a'*32};inputs=io.StringIO(json.dumps({'generation':generation})+'\n'+json.dumps({'request':{'operation_id':'first'}})+'\n')
 with patch('sys.stdin',inputs),patch('sys.stdout',io.StringIO()),patch('os.write',emit),patch('os.replace',delayed_replace):
  worker=threading.Thread(target=run_peer);worker.start()
  try:
   assert sent.wait(2) and waiting.wait(2) and not marker.exists()
   marker.write_text('{"operation_id":"stale-marker"}')
   waiter=threading.Thread(target=lambda:returned.append(m['wait_marker'](marker,'first')));waiter.start();waiter.join(.1);assert waiter.is_alive() and not returned
   publish.set();waiter.join(2);worker.join(2)
   assert not worker.is_alive() and not waiter.is_alive() and not errors and returned[0]['operation_id']=='first'
   marker.unlink()  # The repaired caller unlinks only after the expected marker, before second request.
  finally:publish.set();worker.join(2)
 print('PASS B0-2 exact peer result precedes delayed marker; correlated wait rejects stale marker before unlink/second request')
with tempfile.TemporaryDirectory(prefix='n126-fix-') as home:m['claim_controls'](home,(root/'tools/fixtures_self_test.sh').read_text())
print('REPAIR2 CONTROLS PASS; product source, transport positive, semantic red, final bundle/QA remain PENDING')
