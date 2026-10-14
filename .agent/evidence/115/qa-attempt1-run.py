import hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
ROOT=Path('/home/cnross/.tmp/nizam-115-qa-attempt1-0438usyf')
os.chdir(ROOT)
REV='2f324c68bf273c54907ff63ad057995040d84d54'
E=Path('.agent/evidence/115')
def strict(p):
 def pairs(items):
  d={}
  for k,v in items:
   assert k not in d, 'duplicate key'
   d[k]=v
  return d
 return json.loads(Path(p).read_text(),object_pairs_hook=pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
def git(*a): return subprocess.check_output(['git',*a])
owner=strict(E/'qa-attempt1.json')
assert owner['owner']=='/root/wa_acceptance_115' and owner['root']==str(ROOT)
assert git('rev-parse','HEAD').decode().strip()==owner['base']
s=strict(E/'source-candidate.json'); assert s['revision']==REV
assert git('rev-parse',REV+'^{tree}').decode().strip()==s['tree']
observed={}
for path,digest in s['source_sha256'].items():
 data=Path(path).read_bytes(); anchored=git('show',REV+':'+path)
 assert data==anchored and hashlib.sha256(data).hexdigest()==digest,path
 mode=git('ls-tree',REV,'--',path).decode().split()[0]
 assert bool(Path(path).stat().st_mode & 0o111)==(mode=='100755'),path
 observed[path]={'sha256':digest,'git_mode':mode}
for path in ['.agent/validator/115-recovery-1-mode-a.json','.agent/qa/115-recovery-1-contract-review.json','.agent/validator/115-recovery-1-test-bundle-review.json','.agent/validator/115-mode-b.json']:
 d=strict(path); assert d['final_verdict']['approved'] is True
 for key in ['issues','missing_acceptance_coverage','unsupported_claims']: assert d[key]==[]
contract=strict('.agent/contracts/115.json'); assert contract['status']=='approved' and len(contract['verification'])==17
pre=E/'qa-attempt1-preflight.json'; assert not pre.exists()
pre.write_text(json.dumps({'actor':'/root/wa_acceptance_115','revision':REV,'ambient_head':owner['base'],'source':observed,'approved_contract_sha256':hashlib.sha256(Path('.agent/contracts/115.json').read_bytes()).hexdigest(),'gates_strict_approved':True},indent=2)+'\n')
checks=[]
for i,item in enumerate(contract['verification'],1):
 command=item['command']; raw=E/f'qa-attempt1-check-{i:02d}.txt'; assert not raw.exists()
 print(f'RUN {i}/17: {command}',flush=True)
 result=subprocess.run(command,shell=True,executable='/bin/bash',capture_output=True,text=True)
 content=f'COMMAND: {command}\nREVISION: {REV}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nEXIT: {result.returncode}\n'
 raw.write_text(content)
 for prefix in ['COMMAND:','REVISION:','EXIT:']: assert len(re.findall('^'+prefix,content,re.M))==1, 'duplicate proof header'
 checks.append({'acceptance_test':item['acceptance_test'],'command':command,'exit_code':result.returncode,'evidence':str(raw),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
 print(f'CHECK {i}: exit {result.returncode}',flush=True)
 if result.returncode: break
result_path=E/'qa-attempt1-results.json'; assert not result_path.exists()
result_path.write_text(json.dumps({'revision':REV,'checks':checks,'checks_run':len(checks),'checks_passed':sum(c['exit_code']==0 for c in checks)},indent=2)+'\n')
sys.exit(0 if len(checks)==17 and all(c['exit_code']==0 for c in checks) else 1)
