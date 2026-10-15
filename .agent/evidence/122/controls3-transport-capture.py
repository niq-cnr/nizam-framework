"""Mechanical one-shot transport for released selector then controls; frozen children stay unchanged."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]; E = ROOT/'.agent/evidence/122'
RELEASE = '394dddc472abe8bb072ff426055d4f6ab7a73076'
assert sys.argv[1:] in (['selector'],['controls'])
stage = sys.argv[1]; prefix = E/('controls3-transport-'+stage)
assert not any(Path(str(prefix)+suffix).exists() for suffix in ('.stdout','.stderr','.execution.json')), 'transport output already used'
argv = [sys.executable,'.agent/evidence/122/author4-selector-capture.py','--release-revision',RELEASE,'--run-id','git2551'] if stage=='selector' else [sys.executable,'.agent/evidence/122/controls3-run.py','--release-revision',RELEASE,'--run-id','runtime2']
env = dict(PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin:'+os.defpath,
    GIT_EXEC_PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core',HOME=os.environ['HOME'],LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
def sha(data): return hashlib.sha256(data).hexdigest()
def pins():
    paths = ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json','.agent/evidence/122/author4-selector-capture.py']
    paths += ['.agent/evidence/122/controls3-'+name for name in ('run.py','worker.py','identities.json','identities.pack','release.json','transport-capture.py')]
    values = {p:dict(sha256=sha((ROOT/p).read_bytes()),mode=stat.S_IMODE((ROOT/p).lstat().st_mode),git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',p],env=env).decode().strip()) for p in paths}
    binary = Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
    values['selected_git_binary'] = dict(path=str(binary),sha256=sha(binary.read_bytes()),mode=stat.S_IMODE(binary.stat().st_mode))
    return values
before = pins(); result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True); after = pins()
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with Path(str(prefix)+suffix).open('xb') as handle: handle.write(data)
record = dict(argv=argv,cwd=str(ROOT),environment=env,release_revision=RELEASE,
    exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],env=env).decode().strip(),
    actual_exit=result.returncode,expected_exit=0,controls_attempt=2,artifact_generation=3,pins_before=before,pins_after=after,selected_bytes_modes_unchanged=before==after,
    stdout=str(prefix.relative_to(ROOT))+'.stdout',stderr=str(prefix.relative_to(ROOT))+'.stderr')
with Path(str(prefix)+'.execution.json').open('x') as handle: json.dump(record,handle,indent=2); handle.write('\n')
print(stage+' outer_actual_exit='+str(result.returncode),flush=True)
sys.exit(result.returncode if result.returncode else (0 if before==after else 1))
