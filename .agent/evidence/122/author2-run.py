"""Capture the single frozen attempt2 fixture-only verification without retries."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
environment = {k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
environment.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
argv = [sys.executable,'.agent/evidence/122/author2-verify.py']
result = subprocess.run(argv,cwd=ROOT,env=environment,capture_output=True)
(OUT/'author2-fixture-static.stdout').write_bytes(result.stdout); (OUT/'author2-fixture-static.stderr').write_bytes(result.stderr)
pins = {}
for path in ('tools/test_workflow_assurance.py','tools/workflow_assurance.py','.agent/contracts/122.json','.agent/evidence/122/api-interface.json','.agent/evidence/122/author2-verify.py','.agent/evidence/122/author2-run.py'):
    target = ROOT/path
    pins[path] = dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(),git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',path]).decode().strip(),executable=bool(target.stat().st_mode & 0o111))
(OUT/'author2-fixture-static.execution.json').write_text(json.dumps(dict(argv=argv,cwd=str(ROOT),environment=environment,
    exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),actual_exit=result.returncode,
    classification='fixture/schema/type checks only; Source behavior unexecuted',stdout='author2-fixture-static.stdout',stderr='author2-fixture-static.stderr',pins=pins),indent=2)+'\n')
print('author2-fixture-static actual_exit='+str(result.returncode))
if result.returncode:
    print('AUTHOR_VERIFICATION_FAILURE: retained; stop without retry',file=sys.stderr)
sys.exit(result.returncode)
