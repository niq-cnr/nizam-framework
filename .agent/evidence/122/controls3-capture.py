"""Capture preparation commands only; never release acceptance behavior."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
assert sys.argv[1:] in (['build'],['archive'])
stage = sys.argv[1]; prefix = ROOT/('.agent/evidence/122/controls3-prepare-'+stage)
argv = [sys.executable,'.agent/evidence/122/controls3-build.py'] if stage == 'build' else [sys.executable,'.agent/evidence/122/controls3-run.py','--prepare-check','--run-id','archive1']
environment = {k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
environment.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
environment.update(PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin:'+os.defpath,
    GIT_EXEC_PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core')
result = subprocess.run(argv,cwd=ROOT,env=environment,capture_output=True)
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with Path(str(prefix)+suffix).open('xb') as handle: handle.write(data)
paths = ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json']
paths += ['.agent/evidence/122/controls3-'+name for name in ('run.py','worker.py','build.py','identities.json','identities.pack')]
pins = {path:dict(sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',path]).decode().strip(),executable=bool((ROOT/path).stat().st_mode & 0o111)) for path in paths if (ROOT/path).is_file()}
with Path(str(prefix)+'.execution.json').open('x') as handle:
    json.dump(dict(argv=argv,cwd=str(ROOT),environment=environment,exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
        actual_exit=result.returncode,classification='preparation static/Git blob restoration only; no API behavior',stdout=str(prefix.relative_to(ROOT))+'.stdout',stderr=str(prefix.relative_to(ROOT))+'.stderr',pins=pins),handle,indent=2)
    handle.write('\n')
print(stage+' actual_exit='+str(result.returncode))
sys.exit(result.returncode)
