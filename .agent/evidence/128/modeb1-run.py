import os,subprocess,json,hashlib,pathlib,sys,time
P=pathlib.Path
commands=[('core',['python3','tools/test_runtime_session.py','--check','core-ready']),('preservation',['python3','.agent/evidence/128/author1-preservation.py']),('cost',['python3','.agent/evidence/scope-budget-014/measure.py','--range','128=ec0b21c64f8bf003faa42d6a17dbe4f3903b065b..','--files']),('diff',['git','diff','--check','ec0b21c64f8bf003faa42d6a17dbe4f3903b065b','HEAD'])]
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
receipts=[]
for name,argv in commands:
 start=time.monotonic(); r=subprocess.run(argv,capture_output=True,text=True,timeout=1800)
 prefix='.agent/evidence/128/modeb1-'+name
 P(prefix+'.stdout.txt').write_text(r.stdout); P(prefix+'.stderr.txt').write_text(r.stderr)
 receipts.append({'name':name,'argv':argv,'cwd':os.getcwd(),'environment':{'PYTHONDONTWRITEBYTECODE':os.getenv('PYTHONDONTWRITEBYTECODE')},'actual_exit':r.returncode,'seconds':round(time.monotonic()-start,3),'exercised_revision':head,'stdout':prefix+'.stdout.txt','stderr':prefix+'.stderr.txt'})
 print(name,'actual_exit',r.returncode,flush=True)
P('.agent/evidence/128/modeb1-execution.json').write_text(json.dumps({'reviewer':'/root/validator128','receipts':receipts,'source_sha256':hashlib.sha256(P('tools/runtime_session.py').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(P('tools/test_runtime_session.py').read_bytes()).hexdigest(),'contract_sha256':hashlib.sha256(P('.agent/contracts/128.json').read_bytes()).hexdigest()},indent=2)+'\n')
assert all(x['actual_exit']==0 for x in receipts)
