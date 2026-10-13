"""Independent exact ordered117 contract verification with fresh SourceC receipts."""
import hashlib,json,os,pathlib,subprocess,sys
r=pathlib.Path.cwd();e=r/'.agent/evidence/117';o=json.loads((e/'mode-b-attempt2.json').read_text());c=json.loads((r/'.agent/contracts/117.json').read_text());candidate=json.loads((e/'source-candidate.json').read_text())
assert str(r)==o['root'] and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==o['base']
for p,h in candidate['source_sha256'].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h
checks=[]
for i,row in enumerate(c['verification'],1):
 p=e/('mode-b-attempt2-check-'+str(i).zfill(2)+'.txt');assert not p.exists()
 z=subprocess.run(row['command'],shell=True,executable='/bin/bash',text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 p.write_text('COMMAND: '+row['command']+'\nREVISION: '+candidate['revision']+'\nEXIT: '+str(z.returncode)+'\nSTDOUT:\n'+z.stdout+'\nSTDERR:\n'+z.stderr)
 v={**row,'exit_code':z.returncode,'evidence':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};checks.append(v);print(json.dumps({'check':i,'exit':z.returncode,'evidence':v['evidence'],'sha256':v['sha256']}),flush=True)
 if z.returncode:
  (e/'mode-b-attempt2-replays.json').write_text(json.dumps(checks,indent=2)+'\n');sys.exit(1)
(e/'mode-b-attempt2-replays.json').write_text(json.dumps(checks,indent=2)+'\n')
