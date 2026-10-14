"""FreshQA120 capture, one execution per released obligation; fail and stop."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import time
ROOT=Path(__file__).resolve().parents[4];E=ROOT/'.agent/evidence/120/qa1'
INPUT='5c011078fae6b596bc3cddd2cdb9e7fc276f19af';HIST=Path('/home/cnross/.tmp/nizam-feature120-qa1-historical118');ANCHOR='8ac94f6808e8197111197c9acbf59b2aa92efc7c'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',LC_ALL='C.UTF-8');results=[]
def write(name,value): (E/name).write_text(json.dumps(value,indent=2)+'\n')
def git(*args,root=ROOT): return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
def identity(root,current=True):
    install=[p for p in git('ls-files','-z','.nizam',root=root).split('\0') if p]
    paths=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/README.md','CHANGELOG.md']+install+[p for p in git('ls-files','-z','schema',root=root).split('\0') if p]
    if current: paths+=['.agent/contracts/120.json']
    return {'revision':git('rev-parse','HEAD',root=root),'tree':git('rev-parse','HEAD^{tree}',root=root),'installed_count':len(install),'files':{p:{'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'git_blob':git('rev-parse','HEAD:'+p,root=root)} for p in sorted(set(paths))}}
def capture(name,argv,cwd=ROOT,expected=0,marker=None,lines=None):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();p=subprocess.run(argv,cwd=cwd,env=ENV,capture_output=True,timeout=600)
    (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
    result={'name':name,'argv':argv,'cwd':str(cwd),'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'},'revision':git('rev-parse','HEAD',root=cwd),'started_at':start,'elapsed_seconds':time.monotonic()-t,'exit_code':p.returncode,'expected_exit_code':expected,'stdout':'.agent/evidence/120/qa1/'+name+'.stdout.txt','stderr':'.agent/evidence/120/qa1/'+name+'.stderr.txt'}
    result['passed']=p.returncode==expected and (marker is None or marker in (p.stdout+p.stderr).decode()) and (lines is None or p.stdout.decode().splitlines()==lines)
    write(name+'.result.json',result);results.append(result);write('progress.json',{'results':results,'all_observed_passed':all(x['passed'] for x in results)})
    print(name+': actual='+str(p.returncode)+' expected='+str(expected)+' passed='+str(result['passed']),flush=True)
    if not result['passed']: raise RuntimeError('QA obligation failed; stop before dependent steps: '+name)
os.chdir(ROOT);subprocess.run(['git','merge-base','--is-ancestor',INPUT,'HEAD'],cwd=ROOT,check=True)
dispatch=json.loads((ROOT/'.agent/evidence/120/qa1-dispatch.json').read_bytes());contract=json.loads((ROOT/'.agent/contracts/120.json').read_bytes());gate=json.loads((ROOT/'.agent/validator/120-mode-b.json').read_bytes());state=json.loads((ROOT/'.agent/run_state.json').read_bytes())
assert state['circuit_breaker']['120-QA']['attempts']==1 and contract['status']=='approved'
assert gate['final_verdict']['approved'] is True and all(gate[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
before=identity(ROOT);write('identity-before.json',before)
assert before['installed_count']==239 and all(git('rev-parse',INPUT+':'+p)==row['git_blob'] for p,row in before['files'].items())
for p,key in [('tools/workflow_assurance.py','source_sha256'),('tools/test_workflow_assurance.py','test_sha256'),('.agent/contracts/120.json','approved_contract_sha256')]: assert before['files'][p]['sha256']==dispatch[key]
write('environment.json',{'actor':'/root/qa119','python':platform.python_version(),'platform':platform.platform(),'selected_environment':{k:ENV.get(k) for k in ('PYTHONDONTWRITEBYTECODE','LC_ALL','LANG')},'approved_input':INPUT,'exercised_revision':before['revision'],'historical_root':str(HIST)})
assert not HIST.exists();capture('historical-setup',['git','worktree','add','--detach',str(HIST),ANCHOR]);write('historical-identity.json',identity(HIST,False))
for row in contract['verification']:
    argv=row['command'].split();assert argv.pop(0)=='PYTHONDONTWRITEBYTECODE=1';capture('case-'+argv[-1],argv,lines=['PASS '+argv[-1]])
spec=importlib.util.spec_from_file_location('qa120_inventory',ROOT/'tools/test_workflow_assurance.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert len(module.CASES)==20 and len(module.AGF_CASES)==6 and len(module.RECEIPT_CASES)==11
capture('default37',['python3','tools/test_workflow_assurance.py'],lines=['PASS '+name for name in module.CASES+module.AGF_CASES+module.RECEIPT_CASES])
capture('preservation',['python3','.agent/evidence/120/qa1/preserve.py'],marker='PASS inherited source module/API/CLI AST')
capture('historical-foundation',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],cwd=HIST,marker='PASS foundation-ready:')
capture('live-stale-foundation',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],expected=1,marker='pinned entry bytes/mode changed: tools/workflow_assurance.py')
capture('compliance-default',['bash','tools/validate.sh'],marker='SUMMARY: 16 passed, 0 failed')
capture('compliance-payload',['bash','tools/validate.sh','--payload'],marker='SUMMARY (payload mode): 12 passed, 0 failed')
capture('adversarial',['python3','.agent/evidence/120/qa1/adversarial.py'],marker='PASS exactly one independent command-nonexecution spot:')
(ROOT/'.agent/evidence/120-qa-adversarial.txt').write_text(json.dumps({'description':'Exactly one QA-originated process guard over actual valid receipt verification/advance/noop with deliberate nonGit attempt control','result':results[-1]},indent=2)+'\n')
after=identity(ROOT);write('identity-after.json',after);assert before==after
write('execution-summary.json',{'actor':'/root/qa119','attempt':1,'revision':before['revision'],'approved_input':INPUT,'all_commands_passed':True,'protected_identities_unchanged':True,'exact_contract_commands':11,'default_cases':37,'exactly_one_adversarial':True,'results':results})
print('PASS final freshQA120 capture and protected identities',flush=True)
