import os,subprocess,json,pathlib,time
P=pathlib.Path;head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();receipts=[]
commands=[('default26',['python3','tools/test_workflow_assurance.py'],0),('live-stale118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1),('bundle-pins',['python3','.agent/evidence/119/executable-review1-verify.py'],0),('cost',['python3','.agent/evidence/scope-budget-014/measure.py','--range','119=fcd0584146fd836df0080292cc2cf10180bb9f31..','--files'],0),('diff',['git','diff','--check','fcd0584','HEAD'],0)]
for name,argv,expected in commands:
 start=time.monotonic();r=subprocess.run(argv,capture_output=True,text=True,timeout=1200);prefix='.agent/evidence/119/modeb1-'+name
 P(prefix+'.stdout.txt').write_text(r.stdout);P(prefix+'.stderr.txt').write_text(r.stderr)
 receipts.append({'name':name,'argv':argv,'cwd':os.getcwd(),'environment':{'PYTHONDONTWRITEBYTECODE':os.getenv('PYTHONDONTWRITEBYTECODE')},'actual_exit':r.returncode,'expected_exit':expected,'seconds':round(time.monotonic()-start,3),'exercised_revision':head,'stdout':prefix+'.stdout.txt','stderr':prefix+'.stderr.txt'})
 print(name,'actual_exit',r.returncode,'expected',expected,flush=True)
P('.agent/evidence/119/modeb1-execution.json').write_text(json.dumps({'reviewer':'/root/validator128','receipts':receipts},indent=2)+'\n')
assert all(x['actual_exit']==x['expected_exit'] for x in receipts)
