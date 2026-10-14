import os,json,subprocess,hashlib,datetime
from pathlib import Path
root=Path.cwd(); out=root/'.agent/evidence/127'
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
commands=[('scope',['git','diff','--numstat','1147d1cda9049c153a98e050ea8a53fabe91f838','88996ee9405f9467ff2debd6e3115b34d064019a']),('source-diff',['git','diff','1147d1cda9049c153a98e050ea8a53fabe91f838','88996ee9405f9467ff2debd6e3115b34d064019a','--','tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh','tools/README.md','CHANGELOG.md']),('test-diff',['git','diff','c2b95a1262d49ebd615dcd0d577fad584712dc40','HEAD','--','tools/test_runtime_session.py']),('whole-cost',['python3','.agent/evidence/scope-budget-014/measure.py','--range','127=c2b95a1262d49ebd615dcd0d577fad584712dc40..','--files']),('cancel',['python3','tools/test_runtime_session.py','--check','cancel-confirmation-required']),('handoff',['python3','tools/test_runtime_session.py','--check','handoff-source-bound']),('wait',['python3','tools/test_runtime_session.py','--case','5','--runtime','stub'])]
results=[]
for name,argv in commands:
 p=subprocess.run(argv,cwd=root,env=env,capture_output=True,timeout=100)
 stdout=out/f'modeb1-{name}.stdout.txt'; stderr=out/f'modeb1-{name}.stderr.txt'
 stdout.write_bytes(p.stdout); stderr.write_bytes(p.stderr)
 results.append(dict(name=name,argv=argv,cwd=str(root),actual_exit=p.returncode,stdout=str(stdout.relative_to(root)),stderr=str(stderr.relative_to(root)),exercised_revision=revision))
 print(name,p.returncode,flush=True)
paths=['.agent/contracts/127.json','.agent/evidence/127/runtime-api127.json','tools/test_runtime_session.py','tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh','tools/README.md','CHANGELOG.md','.agent/evidence/scope-budget-014/measure.py']
identities={p:dict(sha256=hashlib.sha256((root/p).read_bytes()).hexdigest(),git_blob=subprocess.check_output(['git','rev-parse','HEAD:'+p],text=True).strip()) for p in paths}
(out/'modeb1-preparation-results.json').write_text(json.dumps(dict(kind='ModeB preparation only; final bundle approval dependency pending',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),revision=revision,environment={'PYTHONDONTWRITEBYTECODE':'1'},identities=identities,results=results),indent=2)+'\n')
assert all(r['actual_exit']==0 for r in results)
