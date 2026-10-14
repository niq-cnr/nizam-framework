"""Verify immutable prior proof, then execute only corrected logical spot once."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[4];E=ROOT/'.agent/evidence/120/qa2';PARTIAL='32655c54392e2f98a895aa0166c9e1e2b33cd935'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).decode().strip()
def old(path):return subprocess.check_output(['git','-C',str(ROOT),'show',PARTIAL+':'+path])
def write(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n')
def protected(before):
    files={}
    for path,row in before['files'].items():
        data=(ROOT/path).read_bytes();blob=git('rev-parse','HEAD:'+path)
        assert hashlib.sha256(data).hexdigest()==row['sha256'] and blob==row['git_blob'],path
        files[path]=row
    assert before['installed_count']==239
    return files
os.chdir(ROOT);dispatch=json.loads((ROOT/'.agent/evidence/120/qa2-dispatch.json').read_bytes())
subprocess.run(['git','merge-base','--is-ancestor',dispatch['approved_input'],'HEAD'],cwd=ROOT,check=True)
manifest=json.loads(old('.agent/evidence/120/qa1/partial-manifest.json'))
for path,row in manifest['files'].items():
    data=old(path);assert hashlib.sha256(data).hexdigest()==row['sha256'],path
    assert git('rev-parse',PARTIAL+':'+path)==row['git_blob'],path
    assert (ROOT/path).read_bytes()==data,path
before=json.loads(old('.agent/evidence/120/qa1/identity-before.json'));files=protected(before)
progress=json.loads(old('.agent/evidence/120/qa1/progress.json'));mandatory=[r for r in progress['results'] if r['name']!='adversarial']
assert len(mandatory)==18 and all(r['passed'] is True for r in mandatory)
contract=json.loads((ROOT/'.agent/contracts/120.json').read_bytes());cases=[r for r in mandatory if r['name'].startswith('case-')]
assert len(cases)==11
for expected,actual in zip(contract['verification'],cases):
    assert expected['command']=='PYTHONDONTWRITEBYTECODE=1 '+' '.join(actual['argv']) and actual['exit_code']==0
    assert actual['revision']==dispatch['original_exercised_revision']
assert progress['results'][-1]['exit_code']==1
revision=git('rev-parse','HEAD');write('carry-forward.json',{'actor':'/root/qa119','partial_commit':PARTIAL,'original_exercised_revision':dispatch['original_exercised_revision'],'spot_exercised_revision':revision,'verified_immutable_file_pins':len(manifest['files']),'mandatory_records':mandatory,'protected_files':files,'installed_count':239,'all_verified':True,'no_mandatory_commands_reexecuted':True})
argv=['python3','.agent/evidence/120/qa2/adversarial.py'];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',LC_ALL='C.UTF-8');start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic()
p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=90)
(E/'adversarial.stdout.txt').write_bytes(p.stdout);(E/'adversarial.stderr.txt').write_bytes(p.stderr)
result={'logical_extra_check':1,'execution_attempt':2,'argv':argv,'cwd':str(ROOT),'revision':revision,'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'},'started_at':start,'elapsed_seconds':time.monotonic()-t,'exit_code':p.returncode,'expected_exit_code':0,'stdout':'.agent/evidence/120/qa2/adversarial.stdout.txt','stderr':'.agent/evidence/120/qa2/adversarial.stderr.txt','passed':p.returncode==0 and p.stdout.startswith(b'PASS exactly one independent command-nonexecution spot:')}
write('adversarial.result.json',result);print(json.dumps(result),flush=True)
assert protected(before)==files,'protected inputs changed'
write('identity-after.json',{'revision':git('rev-parse','HEAD'),'files':files,'protected_inputs_unchanged':True})
if not result['passed']:raise SystemExit(1)
print('PASS corrected same logical spot; preserved mandatory18 and failed execution1; protected inputs unchanged')
