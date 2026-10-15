"""Capture the one explicitly released frozen controls execution; never repair or retry."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'.agent/evidence/122'
argv = [sys.executable,'.agent/evidence/122/controls2-run.py','--release-revision','1b8cb802fd4155f949184932a69e4d609cf91901','--run-id','runtime1']
env = {k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
env.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
def sha(data): return hashlib.sha256(data).hexdigest()
def pins():
    paths = ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json']
    paths += ['.agent/evidence/122/controls2-'+name for name in ('run.py','worker.py','identities.json','identities.pack','release.json','runtime1-capture.py')]
    return {p:dict(sha256=sha((ROOT/p).read_bytes()),mode=stat.S_IMODE((ROOT/p).lstat().st_mode),git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',p]).decode().strip()) for p in paths}
before = pins(); result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True); after = pins()
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with (E/('controls2-runtime1-wrapper'+suffix)).open('xb') as handle: handle.write(data)
record = dict(argv=argv,cwd=str(ROOT),environment=env,exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
    actual_exit=result.returncode,expected_exit=0,controls_attempt=1,artifact_generation=2,release_revision='1b8cb802fd4155f949184932a69e4d609cf91901',
    stdout='controls2-runtime1-wrapper.stdout',stderr='controls2-runtime1-wrapper.stderr',pins_before=before,pins_after=after,selected_bytes_modes_unchanged=before==after)
with (E/'controls2-runtime1-wrapper.execution.json').open('x') as handle: json.dump(record,handle,indent=2); handle.write('\n')
print('controls2-runtime1 outer_actual_exit='+str(result.returncode),flush=True)
sys.exit(result.returncode if result.returncode else (0 if before==after else 1))
