import datetime,hashlib,json,os,selectors,signal,subprocess,time
from pathlib import Path
R=Path('/home/cnross/.tmp/nizam-feature123-final-seal1');O=Path('/home/cnross/.tmp/nizam-feature123-final-seal1-captures');label='seal-supplemental'
argv=['python3','/home/cnross/.tmp/nizam-feature123-final-seal1-supplemental.py'];start=time.monotonic();at=datetime.datetime.now(datetime.timezone.utc).isoformat()
child=subprocess.Popen(argv,cwd=R,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
frame=dict(argv=argv,cwd=str(R),environment={'PYTHONDONTWRITEBYTECODE':'1'},child_pid=child.pid,started_at=at,exercised_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip(),wall_bound_seconds=120,stream_bound_bytes=2097152)
(O/(label+'.start.json')).write_text(json.dumps(frame,indent=2)+'\n');print(json.dumps(dict(status='STARTED',pid=child.pid)),flush=True)
counts={'stdout':0,'stderr':0};eof=set();reason=None;files={n:(O/(label+'.'+n)).open('xb') for n in counts}
with selectors.DefaultSelector() as sel:
 sel.register(child.stdout,selectors.EVENT_READ,'stdout');sel.register(child.stderr,selectors.EVENT_READ,'stderr')
 while sel.get_map():
  if time.monotonic()-start>120:reason='timeout'
  if reason:
   try:os.killpg(child.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  for key,_ in sel.select(.1):
   n=key.data;b=os.read(key.fileobj.fileno(),65536)
   if not b:eof.add(n);sel.unregister(key.fileobj);key.fileobj.close();continue
   files[n].write(b[:max(0,2097152-counts[n])]);counts[n]+=len(b)
   if counts[n]>2097152:reason=n+'-oversize'
for f in files.values():f.close()
actual=child.wait();frame.update(actual_exit=actual,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,stop_reason=reason,streams={n:dict(path=label+'.'+n,bytes=(O/(label+'.'+n)).stat().st_size,observed_bytes=counts[n],complete=n in eof and counts[n]<=2097152,sha256=hashlib.sha256((O/(label+'.'+n)).read_bytes()).hexdigest()) for n in counts})
(O/(label+'.execution.json')).write_text(json.dumps(frame,indent=2)+'\n');print(json.dumps(dict(status='COMPLETED',actual_exit=actual,stop_reason=reason)),flush=True)
raise SystemExit(0 if actual==0 and reason is None else 1)
