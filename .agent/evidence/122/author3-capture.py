"""One static command and one acceptance regression command; retain actual red1 truthfully."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'.agent/evidence/122'
env = {k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
env.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
def sha(data): return hashlib.sha256(data).hexdigest()
def protected():
    paths = set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0'))-{''}
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'.nizam').rglob('*') if p.is_file())
    rows = [[p,stat.S_IMODE((ROOT/p).lstat().st_mode),sha((ROOT/p).read_bytes())] for p in sorted(paths)]
    selected = ('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json','schema/qa_verdict.schema.json','schema/contract_review.schema.json','.agent/evidence/122/author3-verify.py','.agent/evidence/122/author3-capture.py','.agent/evidence/122/api-interface.json')
    return dict(count=len(rows),all_bytes_modes_sha256=sha(json.dumps(rows,separators=(',',':')).encode()),pins={p:dict(mode=mode,sha256=digest,git_blob=subprocess.check_output(['git','-C',str(ROOT),'hash-object',p]).decode().strip()) for p,mode,digest in rows if p in selected})
before = protected()
for label,argv in (('static',[sys.executable,'.agent/evidence/122/author3-verify.py']),('semantic-regression',[sys.executable,'tools/test_workflow_assurance.py','--case','semantic-failed'])):
    result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
    for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
        with (E/('author3-'+label+suffix)).open('xb') as handle: handle.write(data)
    after = protected()
    record = dict(argv=argv,cwd=str(ROOT),environment=env,exercised_revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),expected_acceptance_exit=0,actual_exit=result.returncode,
        classification='fixture/schema-only validation' if label=='static' else 'genuine unchanged Source false-rejection; acceptance remains failed1',
        stdout='author3-'+label+'.stdout',stderr='author3-'+label+'.stderr',protected_before=before,protected_after=after,protected_unchanged=before==after)
    with (E/('author3-'+label+'.execution.json')).open('x') as handle: json.dump(record,handle,indent=2); handle.write('\n')
    print(label,'actual_exit='+str(result.returncode),flush=True)
    if before != after or (label=='static' and result.returncode != 0): sys.exit(1)
    if label=='semantic-regression':
        expected = b'SEMANTIC_SCHEMA_CONTEXT legacy-final-false: failure routing invalid: failure semantic verdict shape'
        if result.returncode != 1 or expected not in result.stderr or b'SETUP_ERROR' in result.stderr: sys.exit(1)
print('Expected genuine regression retained; selector actual exit1, wrapper exit0; Source repair and later QA remain required')
