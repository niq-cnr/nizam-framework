import hashlib,json,os,selectors,signal,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
root=Path('/home/cnross/.tmp/nizam-feature123-constructor-matrix4-preparation')
out=Path(__file__).resolve().parent
argv=['python3',str(root/'.agent/evidence/123/constructor-matrix4.py'),'--repository',str(root),'--workspace','/home/cnross/.tmp/nizam-feature123-constructor-matrix4-run1','--output','/home/cnross/.tmp/nizam-feature123-constructor-matrix4-run1-evidence']
start=time.monotonic();at=datetime.now(timezone.utc).isoformat()
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
child=subprocess.Popen(argv,cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
frame=dict(argv=argv,cwd=str(root),environment={'PYTHONDONTWRITEBYTECODE':'1'},revision=revision,driver_pid=child.pid,start_at=at,helper_sha256=hashlib.sha256((root/'.agent/evidence/123/constructor-matrix4.py').read_bytes()).hexdigest(),outer_argv=[sys.executable,str(Path(__file__).resolve())],wall_bound_seconds=1860,stream_limit_bytes=2097152,release_revision='42a974311a58e6c6e0c5df9cfab7e8fefbb7bca5')
(out/'start.json').write_text(json.dumps(frame,indent=2)+'\n')
print(json.dumps(dict(status='ACTUAL_STARTED',pid=child.pid,revision=revision,start_at=at)),flush=True)
counts=dict(stdout=0,stderr=0);eof=set();reason=None;cleanup=None;limit=2097152
def stop(why):
 global reason,cleanup
 if cleanup is None:
  reason=why;cleanup=time.monotonic()+2
  try:os.killpg(child.pid,signal.SIGKILL)
  except ProcessLookupError:pass
with (out/'outer.stdout').open('xb') as so,(out/'outer.stderr').open('xb') as se:
 handles=dict(stdout=so,stderr=se)
 with selectors.DefaultSelector() as sel:
  sel.register(child.stdout,selectors.EVENT_READ,'stdout');sel.register(child.stderr,selectors.EVENT_READ,'stderr')
  while sel.get_map():
   if time.monotonic()-start>=1860:stop('timeout')
   if cleanup is not None and time.monotonic()>=cleanup:break
   for key,_ in sel.select(.1):
    name=key.data;data=os.read(key.fileobj.fileno(),min(65536,max(1,limit-counts[name]+1)))
    if not data:
     eof.add(name);sel.unregister(key.fileobj);key.fileobj.close();continue
    handles[name].write(data[:max(0,limit-counts[name])]);counts[name]+=len(data)
    if counts[name]>limit:stop(name+'-oversize')
  for key in list(sel.get_map().values()):sel.unregister(key.fileobj);key.fileobj.close()
try:actual=child.wait(timeout=max(0,(cleanup if cleanup else start+1860)-time.monotonic()))
except subprocess.TimeoutExpired:
 stop('timeout')
 try:actual=child.wait(timeout=max(0,cleanup-time.monotonic()))
 except subprocess.TimeoutExpired:actual=None
frame.update(actual_exit=actual,stop_reason=reason,finish_at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,streams={name:dict(path='outer.'+name,bytes=(out/('outer.'+name)).stat().st_size,observed_bytes=counts[name],sha256=hashlib.sha256((out/('outer.'+name)).read_bytes()).hexdigest(),complete=name in eof and counts[name]<=limit) for name in counts})
(out/'outer.execution.json').write_text(json.dumps(frame,indent=2)+'\n')
print(json.dumps(dict(status='ACTUAL_COMPLETED',actual_exit=actual,stop_reason=reason,elapsed_seconds=frame['elapsed_seconds'])),flush=True)
sys.exit(0 if actual==0 and reason is None else 1)
