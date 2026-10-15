"""Capture zero-API AST scope proof only; no acceptance or fixture construction."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]; E = ROOT/'.agent/evidence/122'
argv = [sys.executable,'.agent/evidence/122/author4-scope.py']
env = dict(PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin:'+os.defpath,
    GIT_EXEC_PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core',HOME=os.environ['HOME'],LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
assert not any((E/('author4-scope'+s)).exists() for s in ('.stdout','.stderr','.execution.json'))
result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with (E/('author4-scope'+suffix)).open('xb') as handle: handle.write(data)
paths = ['tools/test_workflow_assurance.py','tools/workflow_assurance.py','.agent/contracts/122.json','.agent/evidence/122/author4-scope.py','.agent/evidence/122/author4-preparation-capture.py']
pins = {p:dict(sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',p]).decode().strip(),executable=bool((ROOT/p).stat().st_mode & 0o111)) for p in paths}
with (E/'author4-scope.execution.json').open('x') as handle:
    json.dump(dict(argv=argv,cwd=str(ROOT),environment=env,exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),actual_exit=result.returncode,api_calls=0,pins=pins,stdout='author4-scope.stdout',stderr='author4-scope.stderr'),handle,indent=2); handle.write('\n')
print('author4-static-scope actual_exit='+str(result.returncode),flush=True)
sys.exit(result.returncode)
