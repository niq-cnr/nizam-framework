"""Capture an observed successful main run after the authorized PR103 merge."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

run_id,merge = sys.argv[1:]
E = Path('.agent/evidence/122')
argv = ['gh','run','view',run_id,'--repo','niq-cnr/nizam-framework','--json','databaseId,headSha,status,conclusion,jobs']
revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
p = subprocess.run(argv,capture_output=True)
out,err = E/'pr103-main-ci.stdout.txt',E/'pr103-main-ci.stderr.txt'
out.write_bytes(p.stdout);err.write_bytes(p.stderr)
execution = {'argv':argv,'cwd':str(Path.cwd()),'actual_exit':p.returncode,'exercised_revision':revision,'stdout':str(out),'stderr':str(err),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest()}
(E/'pr103-main-ci.execution.json').write_text(json.dumps(execution,indent=2)+'\n')
assert p.returncode == 0
d = json.loads(p.stdout)
assert d['databaseId'] == int(run_id) and d['headSha'] == merge
assert d['status'] == 'completed' and d['conclusion'] == 'success'
assert len(d['jobs']) == 5
assert {j['name'] for j in d['jobs']} == {'validate','fixtures_self_test','e2e_bootstrap','convergent_review','self_governance'}
assert all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in d['jobs'])
bindings = {}
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
    raw = subprocess.check_output(['git','show',merge+':'+path])
    assert raw == Path(path).read_bytes()
    bindings[path] = {'sha256':hashlib.sha256(raw).hexdigest(),'git_blob':subprocess.check_output(['git','rev-parse',merge+':'+path],text=True).strip()}
execution.update(role='Root',passed=True,run=int(run_id),head=merge,jobs=[{k:j[k] for k in ('name','status','conclusion')} for j in d['jobs']],bindings=bindings)
(E/'pr103-main-ci.json').write_text(json.dumps(execution,indent=2)+'\n')
print('PASS actual PR103 merge main CI all5; Source/test bindings verified')
