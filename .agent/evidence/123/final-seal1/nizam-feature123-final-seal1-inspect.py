import ast,datetime,gzip,hashlib,json,os,stat,subprocess,sys,time
from pathlib import Path
R=Path('/home/cnross/.tmp/nizam-feature123-final-seal1');O=Path('/home/cnross/.tmp/nizam-feature123-final-seal1-captures')
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def snapshot():
 rows=[]
 for p in git('ls-files','-z').decode().split('\0'):
  if not p:continue
  q=R/p;s=q.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,p
  rows.append([p,s.st_mode,s.st_nlink,sha(q.read_bytes())])
 return dict(rows=rows,head=git('rev-parse','HEAD').decode().strip(),origin=git('remote','get-url','origin').decode().strip(),status=git('status','--porcelain','--untracked-files=all').decode(),refs=git('show-ref').decode())
def save(name,x):
 b=enc(x);z=gzip.compress(b,mtime=0);(O/name).write_bytes(z);return dict(path=name,bytes=len(z),sha256=sha(z),raw_sha256=sha(b))
def command(label,argv,data=None,refs_change=False):
 before=snapshot();br=save(label+'.before.json.gz',before);start=time.monotonic();at=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=subprocess.run(argv,cwd=R,input=data,capture_output=True,timeout=120)
 after=snapshot();ar=save(label+'.after.json.gz',after)
 for stream in ('stdout','stderr'):(O/(label+'.'+stream)).write_bytes(getattr(p,stream))
 comparable=lambda v:{k:x for k,x in v.items() if k!='refs'} if refs_change else v
 frame=dict(argv=argv,cwd=str(R),exercised_revision=before['head'],environment={'PYTHONDONTWRITEBYTECODE':'1'},started_at=at,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,actual_exit=p.returncode,before=br,after=ar,preservation_equal=comparable(before)==comparable(after),intentional_owned_ref_change=refs_change,streams={n:dict(path=label+'.'+n,bytes=len(getattr(p,n)),sha256=sha(getattr(p,n))) for n in ('stdout','stderr')})
 (O/(label+'.execution.json')).write_bytes(enc(frame));assert p.returncode==0 and frame['preservation_equal'],label
e=json.loads((R/'.agent/evidence/123/controls-evidence.json').read_bytes());bundle=(R/e['pack_ref']['path']).read_bytes();assert sha(bundle)==e['pack_ref']['sha256']
assert bundle.startswith(b'# v2 git bundle\n') and b'\n\n' in bundle
bundle_path=O/'verify.bundle';bundle_path.write_bytes(bundle);pack=bundle.split(b'\n\n',1)[1];(O/'verify.pack.stdin').write_bytes(pack)
command('seal-index-pack',['git','index-pack','--strict','--fix-thin','--stdin'],pack)
command('seal-bundle-verify',['git','bundle','verify',str(bundle_path)])
command('seal-fetch',['git','fetch','--no-tags','--no-write-fetch-head',str(bundle_path),'refs/wa123/proof:refs/wa123/final-seal1'],refs_change=True)
print('PASS final-seal evidence strict imports',flush=True)
