"""Independent exact sealed-command capture; no source/test mutation."""
import hashlib,json,os,pathlib,platform,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[3]
C1='88996ee9405f9467ff2debd6e3115b34d064019a'
def identity(path):
 data=(R/path).read_bytes(); committed=subprocess.check_output(['git','show',C1+':'+path],cwd=R);assert data==committed
 return {'path':path,'source_revision':C1,'git_blob':subprocess.check_output(['git','rev-parse',C1+':'+path],cwd=R,text=True).strip(),'sha256':hashlib.sha256(data).hexdigest()}
manifest={'exercised_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'immutable_source_candidate':C1,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'inputs':[identity(p) for p in ['tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh','tools/test_runtime_session.py','.agent/evidence/127/runtime-api127.json','.agent/evidence/127/acceptance1-obligations.json','.agent/contracts/127.json']]}
E=R/'.agent/evidence/127';(E/'semantic1-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
commands=[('cancel',['--check','cancel-confirmation-required']),('handoff',['--check','handoff-source-bound']),('wait',['--case','5','--runtime','stub']),('reattach',['--case','6','--runtime','stub']),('replay',['--case','10','--runtime','stub'])]
if len(sys.argv)>1:commands=[x for x in commands if x[0] in sys.argv[1:]]
for name,args in commands:
 prefix=E/f'semantic1-base-{name}';assert not prefix.with_suffix('.json').exists()
 argv=[sys.executable,'tools/test_runtime_session.py',*args];start=time.monotonic()
 try:
  p=subprocess.run(argv,cwd=R,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=150)
  code=p.returncode;out=p.stdout;err=p.stderr;timedout=False
 except subprocess.TimeoutExpired as exc:
  code=None;out=exc.stdout or b'';err=exc.stderr or b'';timedout=True
  if isinstance(out,bytes):out=out.decode(errors='replace')
  if isinstance(err,bytes):err=err.decode(errors='replace')
 prefix.with_suffix('.stdout.txt').write_text(out);prefix.with_suffix('.stderr.txt').write_text(err)
 result={'argv':argv,'cwd':str(R),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'actual_exit':code,'outer_timeout':timedout,'elapsed_seconds':time.monotonic()-start,'manifest':'.agent/evidence/127/semantic1-manifest.json','stdout':str(prefix.with_suffix('.stdout.txt').relative_to(R)),'stderr':str(prefix.with_suffix('.stderr.txt').relative_to(R)),'classification':'pending independent assessment; no arbitrary nonzero counts as intended red'}
 prefix.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(name,code,'timeout',timedout,out[-500:],err[-1200:],flush=True)
