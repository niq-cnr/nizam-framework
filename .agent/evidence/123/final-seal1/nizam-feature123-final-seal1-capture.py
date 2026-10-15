import datetime,gzip,hashlib,json,os,selectors,signal,stat,subprocess,sys,time
from pathlib import Path
R=Path('/home/cnross/.tmp/nizam-feature123-final-seal1')
O=Path('/home/cnross/.tmp/nizam-feature123-final-seal1-captures');O.mkdir(exist_ok=False)
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode().strip()
def snapshot():
 rows=[]
 for name in subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'):
  if not name:continue
  p=R/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,name
  rows.append([name,s.st_mode,s.st_nlink,sha(p.read_bytes())])
 installed=[x for x in rows if x[0].startswith('.nizam/')];assert len(installed)==239
 return dict(head=git('rev-parse','HEAD'),origin=git('remote','get-url','origin'),rows=rows,installed=installed,status=git('status','--porcelain','--untracked-files=all'),refs=git('show-ref'))
def saved(name,value):
 raw=enc(value);payload=gzip.compress(raw,mtime=0);(O/name).write_bytes(payload)
 return dict(path=name,sha256=sha(payload),raw_sha256=sha(raw),raw_bytes=len(raw))
pins={'.agent/contracts/123.json':'64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5','tools/workflow_assurance.py':'2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8','tools/test_workflow_assurance.py':'06eba273dbfd615df7f0ea3b6b52592ed208f9ec267b52a1e06996488b850f13','.agent/evidence/123/author3-controls.py':'79352536f9db966c73d7552dc5112db08a4fa356d507bf9c6482aef27f06e8bd','.agent/evidence/123/controls-policy.json':'cc1ee6cde9faa0f6aaaab3cf2647fb509c04c8644fdca37fea9347e1ba52b53e'}
assert all(sha((R/p).read_bytes())==h for p,h in pins.items())
assert git('rev-parse','HEAD')=='f3a9fffa0a5ad5ff002097a1be810e798988247a'
assert not (R/'.git/objects/info/alternates').exists()
for stage,expected in [('positive',0),('semantic-negative',1),('restored',0)]:
 before=snapshot();br=saved(stage+'.before.json.gz',before)
 argv=['python3','.agent/evidence/123/author3-controls.py','--selector','controls-ready','--stage',stage]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic()
 child=subprocess.Popen(argv,cwd=R,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 frame=dict(stage=stage,argv=argv,cwd=str(R),environment={'PYTHONDONTWRITEBYTECODE':'1'},exercised_revision=before['head'],source_commit='9886e5fadad31845349e54235820edac71c7b7fb',pins=pins,child_pid=child.pid,started_at=started,expected_exit=expected,wall_bound_seconds=7200,stream_bound_bytes=2097152,before=br)
 (O/(stage+'.start.json')).write_bytes(enc(frame));print(json.dumps(dict(stage=stage,pid=child.pid,status='STARTED')),flush=True)
 counts={'stdout':0,'stderr':0};eof=set();reason=None
 handles={n:(O/(stage+'.'+n)).open('xb') for n in counts}
 with selectors.DefaultSelector() as sel:
  sel.register(child.stdout,selectors.EVENT_READ,'stdout');sel.register(child.stderr,selectors.EVENT_READ,'stderr')
  while sel.get_map():
   if time.monotonic()-start>7200:reason='timeout'
   if reason:
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   for key,_ in sel.select(.1):
    n=key.data;b=os.read(key.fileobj.fileno(),65536)
    if not b:eof.add(n);sel.unregister(key.fileobj);key.fileobj.close();continue
    handles[n].write(b[:max(0,2097152-counts[n])]);counts[n]+=len(b)
    if counts[n]>2097152:reason=n+'-oversize'
 for h in handles.values():h.close()
 actual=child.wait();after=snapshot();ar=saved(stage+'.after.json.gz',after)
 streams={n:dict(path=stage+'.'+n,bytes=(O/(stage+'.'+n)).stat().st_size,observed_bytes=counts[n],sha256=sha((O/(stage+'.'+n)).read_bytes()),complete=n in eof and counts[n]<=2097152) for n in counts}
 err=(O/(stage+'.stderr')).read_text();out=(O/(stage+'.stdout')).read_text()
 intended=('AssertionError: POLICY_ASSERTION: synthetic invalid controls proof accepted: readiness missing trials' in err) if stage=='semantic-negative' else ('PASS frozen123 author3 controls-ready '+stage in out)
 ok=actual==expected and reason is None and before==after and intended and all(x['complete'] for x in streams.values())
 frame.update(actual_exit=actual,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,stop_reason=reason,streams=streams,after=ar,preservation_equal=before==after,tracked_count=len(before['rows']),installed_count=len(before['installed']),expected_observation_observed=intended,accepted=ok,root_shared_refs_claimed_unchanged=False)
 (O/(stage+'.execution.json')).write_bytes(enc(frame));print(json.dumps(dict(stage=stage,pid=child.pid,status='COMPLETED',actual_exit=actual,accepted=ok,elapsed_seconds=frame['elapsed_seconds'])),flush=True)
 if not ok:sys.exit(1)
