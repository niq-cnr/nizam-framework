"""Capture one author-only fixture check and one missing-API setup per selector."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
environment = {k: os.environ[k] for k in ('PATH', 'HOME', 'LANG') if k in os.environ}
environment.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
commands = [('fixture-static', [sys.executable, '.agent/evidence/122/author1-verify.py'], 0)]
commands += [(name, [sys.executable, 'tools/test_workflow_assurance.py', '--case', name], 2) for name in
    ('infrastructure-failed','semantic-failed','reject-cause-relabel','counter-continuity')]
for label, argv, expected in commands:
    result = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True)
    prefix = OUT/('author1-'+label)
    prefix.with_suffix('.stdout').write_bytes(result.stdout); prefix.with_suffix('.stderr').write_bytes(result.stderr)
    pins = {}
    for path in ('tools/test_workflow_assurance.py','tools/workflow_assurance.py','.agent/contracts/122.json', '.agent/evidence/122/author1-verify.py'):
        target = ROOT/path
        pins[path] = dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(), git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',path]).decode().strip(), executable=bool(target.stat().st_mode & 0o111))
    metadata = dict(argv=argv,cwd=str(ROOT),environment=environment,exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),actual_exit=result.returncode,
        classification='fixture-static-only' if expected == 0 else 'SETUP missing API, never behavioral red', stdout=prefix.with_suffix('.stdout').name,stderr=prefix.with_suffix('.stderr').name,pins=pins)
    prefix.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(label, 'actual_exit='+str(result.returncode))
    if result.returncode != expected or (expected == 2 and b'SETUP_ERROR: missing route_failed_attempt API' not in result.stderr):
        print('AUTHOR_VERIFICATION_FAILURE: retained; stop without retry', file=sys.stderr); sys.exit(1)
