"""QA2 pending-only capture; preserve immutable QA1 results and failed helper."""
import hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; E=ROOT/'.agent/evidence/121'
spec=importlib.util.spec_from_file_location('qa1_frozen', E/'qa1-helper.py'); old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
ENV={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C'}
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,value):(E/name).write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
def read(name):return json.loads((E/name).read_text())
def require(ok,message):
    if not ok:raise AssertionError(message)
def rev():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
def snapshot():return {k:v for k,v in old.snapshot().items() if not k.startswith('.agent/evidence/121/qa2-')}
def preflight():
    dispatch=read('qa2-dispatch.json');require(rev()=='e2edfcea6922da7b4c2e6d2f94f867491aa7e78f','new owned QA2 revision')
    require(dispatch['root']==str(ROOT) and dispatch['attempt']==2,'QA2 dispatch')
    state=json.loads((ROOT/'.agent/run_state.json').read_text());require(state['circuit_breaker']['121-QA']['attempts']==2,'allocated QA2')
    for path,key in [('tools/workflow_assurance.py','source_sha256'),('tools/test_workflow_assurance.py','test_sha256'),('.agent/contracts/121.json','approved_contract_sha256')]:require(sha((ROOT/path).read_bytes())==dispatch[key],'current dispatch identity '+path)
    frozen=subprocess.check_output(['git','show',dispatch['frozen_helper_revision']+':'+dispatch['frozen_helper']],cwd=ROOT)
    require((ROOT/dispatch['frozen_helper']).read_bytes()==frozen,'frozen helper byte equality')
    records=[read('qa1-'+label+'.json') for label in ['contract1','contract2','contract3','contract4','contract5','default42','historical118','current-stale118']]
    seal=read('qa1-partial-seal.json')
    for record in records:
        require(record['actual_exit']==record['expected_exit'],'reused actual expected exit')
        for stream in ['stdout','stderr']:
            raw=record[stream];data=(ROOT/raw['path']).read_bytes();require(sha(data)==raw['sha256'] and len(data)==raw['size_bytes'],'reused raw hash')
            require(seal['files'][raw['path']]['revision']==dispatch['partial_raw_revision'] and seal['files'][raw['path']]['sha256']==raw['sha256'],'immutable containing ref')
    require('pinned entry bytes/mode changed: tools/workflow_assurance.py' in (E/'qa1-current-stale118.stderr.txt').read_text(),'exact real stale diagnostic')
    write('qa2-protected-before.json',snapshot());write('qa2-preflight.json',dict(passed=True,revision=rev(),dispatch=dispatch,reused_records=8,frozen_helper_sha256=sha(frozen),no_prior_extra_execution=True))
    print('PASS QA2 pending-only preflight; eight immutable results reused')
def capture(label,argv):
    result=subprocess.run(argv,cwd=ROOT,env=ENV,capture_output=True)
    streams={}
    for name,data in [('stdout',result.stdout),('stderr',result.stderr)]:
        path='.agent/evidence/121/qa2-'+label+'.'+name+'.txt';(ROOT/path).write_bytes(data);streams[name]=dict(path=path,sha256=sha(data),size_bytes=len(data))
    record=dict(argv=argv,cwd=str(ROOT),environment={'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C','other_environment':'inherited process environment; no additional changes'},exercised_revision=rev(),actual_exit=result.returncode,expected_exit=0,**streams)
    write('qa2-'+label+'.json',record);require(result.returncode==0,'actual runtime failure: stop, preserve and do not repair/rerun')
    return record

def pending():
    records=[capture('compliance',['bash','tools/validate.sh']),capture('payload',['bash','tools/validate.sh','--payload']),capture('adversarial',['python3','.agent/evidence/121/qa1-helper.py','extra'])]
    extra=records[-1];out=(ROOT/extra['stdout']['path']).read_text();err=(ROOT/extra['stderr']['path']).read_text()
    require('PASS additional locked-worktree Git failure preserved without fallback or successful-removal claim' in out,'first additional semantic success')
    (ROOT/'.agent/evidence/121-qa-adversarial.txt').write_text(json.dumps(extra,sort_keys=True)+'\nSTDOUT:\n'+out+'\nSTDERR:\n'+err)
    after=snapshot();require(after==read('qa2-protected-before.json'),'QA2 protected bytes/modes identical');write('qa2-protected-after.json',after)
    write('qa2-pending-summary.json',dict(passed=True,records=records,prior_expected_commands=8,pending_mandatory_completed=2,additional_check_executions=1,protected_equal=True,protected_files=len(after),original_wrapper_actual_exit=1,original_wrapper_failure_preserved=True,boundary='Eight prior expected command results plus two pending compliance commands and one first adversarial execution; original capture helper failure remains1; no reruns or product changes.'))
    print('PASS both pending compliance commands and first additional adversarial execution; protected equality')
if __name__=='__main__':globals()[sys.argv[1]]()
