"""Independent replay with new raw outputs; never rewrites authored proofs."""
import hashlib,json,os,pathlib,shlex,subprocess,sys
r=pathlib.Path.cwd();e=r/'.agent/evidence/117';b=json.loads((e/'acceptance-bundle.json').read_text());o=json.loads((e/'bundle-review-attempt1.json').read_text())
assert str(r)==o['root'] and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==o['base']
checks=[]
for row in b['baseline_evidence']:
 for stage in ('setup','positive','red'):
  command=row[stage]['command'];argv=shlex.split(command);assert argv.pop(0)=='PYTHONDONTWRITEBYTECODE=1'
  target=e/('bundle-review-attempt1-'+row['case']+'-'+stage+'-raw.txt');assert not target.exists()
  z=subprocess.run(argv,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  target.write_text('COMMAND: '+command+'\nREVISION: '+b['baseline']['commit']+'\nREVIEW_CHECKOUT: '+o['base']+'\nEXIT: '+str(z.returncode)+'\nSTDOUT:\n'+z.stdout+'\nSTDERR:\n'+z.stderr)
  expected=1 if stage=='red' else 0
  item={'case':row['case'],'stage':stage,'exit':z.returncode,'expected':expected,'raw':str(target.relative_to(r)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()};checks.append(item)
  print(json.dumps(item),flush=True)
  if z.returncode!=expected:
   (e/'bundle-review-attempt1-replays.json').write_text(json.dumps(checks,indent=2)+'\n');sys.exit(1)
for label,args in [('existing16',['--pre-entry-cases']),('scope',['--scope-117','--base','79af0276408ba03e80c709af127133e2b55e7bea']),('scope-controls',['--scope-controls-117','--base','79af0276408ba03e80c709af127133e2b55e7bea'])]:
 argv=['/usr/bin/python3','tools/test_workflow_assurance.py',*args];command='PYTHONDONTWRITEBYTECODE=1 '+shlex.join(argv)
 target=e/('bundle-review-attempt1-'+label+'-raw.txt');assert not target.exists()
 z=subprocess.run(argv,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 target.write_text('COMMAND: '+command+'\nREVISION: '+o['base']+'\nEXIT: '+str(z.returncode)+'\nSTDOUT:\n'+z.stdout+'\nSTDERR:\n'+z.stderr)
 item={'check':label,'exit':z.returncode,'expected':0,'raw':str(target.relative_to(r)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()};checks.append(item);print(json.dumps(item),flush=True)
 if z.returncode:
  (e/'bundle-review-attempt1-replays.json').write_text(json.dumps(checks,indent=2)+'\n');sys.exit(1)
(e/'bundle-review-attempt1-replays.json').write_text(json.dumps(checks,indent=2)+'\n')
