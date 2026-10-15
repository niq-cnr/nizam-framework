"""Mechanical capture/seal only; run after explicit Root strict Mode B release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/122'
PREPARATION = '16052d76bf10520f35d24a05384ca235b7b5ca6c'
NAMES = ['qa1-capture.py', 'qa1-adversarial.py', 'qa1-plan.json', 'qa1-outercapture.py']
def sha(raw): return hashlib.sha256(raw).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE)
def write(name, value):
    path = E / ('qa1-outer-' + name)
    assert not path.exists(), 'refuse to overwrite outer evidence: ' + str(path)
    path.write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
def file_pin(path, revision):
    p = ROOT / path
    s = p.lstat()
    assert stat.S_ISREG(s.st_mode), path
    raw = p.read_bytes()
    committed = git('show',revision+':'+path)
    tree = git('ls-tree',revision,'--',path).decode().strip()
    mode = tree.split()[0]
    return {'path':path,'sha256':sha(raw),'full_fs_mode':s.st_mode,'git_revision':revision,'git_tree_entry':tree,'matches_git_bytes':raw==committed,'matches_git_exec':bool(s.st_mode & 0o111)==(mode=='100755')}
def own_pins(revision):
    return [file_pin('.agent/evidence/122/'+name,revision if name=='qa1-outercapture.py' else PREPARATION) for name in NAMES]
def selected_pins(revision):
    names = ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json','schema/contract.schema.json','schema/contract_review.schema.json','schema/qa_verdict.schema.json','schema/run_state.schema.json','.nizam/NIZAM.json']
    return [file_pin(path,revision) for path in names]
def installed_seal():
    rows = [[p.relative_to(ROOT).as_posix(),p.lstat().st_mode,sha(p.read_bytes())] for p in sorted((ROOT/'.nizam').rglob('*')) if p.is_file()]
    assert len(rows)==239
    return {'regular_files':239,'full_modes_and_bytes_sha256':sha(json.dumps(rows,separators=(',',':')).encode())}
p=argparse.ArgumentParser()
for name in ('revision','mode-b','mode-b-revision','source-sha256','test-sha256','contract-sha256','historical-root'): p.add_argument('--'+name,required=True)
a=p.parse_args()
assert git('rev-parse','HEAD').decode().strip()==a.revision
# Invoke in an explicit minimal environment; capture the complete actual environment.
allowed={'PATH','HOME','LANG','LC_ALL','PYTHONDONTWRITEBYTECODE'}
assert set(os.environ)<=allowed and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1', 'use explicit minimal environment'
assert os.environ.get('LC_ALL')=='C'
environment=dict(os.environ)
own_before=own_pins(a.revision); selected_before=selected_pins(a.revision); installed_before=installed_seal()
assert all(row['matches_git_bytes'] and row['matches_git_exec'] for row in own_before+selected_before)
outer_argv=[part.decode() for part in Path('/proc/self/cmdline').read_bytes().split(b'\0') if part]
argv=['python3','.agent/evidence/122/qa1-capture.py',*sys.argv[1:]]
write('before.json',{'revision':a.revision,'argv':outer_argv,'cwd':str(ROOT),'environment':environment,'runner_argv':argv,'own_pins':own_before,'selected_pins':selected_before,'installed':installed_before,'original_preparation_revision':PREPARATION})
started=time.time()
result=subprocess.run(argv,cwd=ROOT,env=environment,capture_output=True)
for name,raw in [('stdout',result.stdout),('stderr',result.stderr)]:
    target=E/('qa1-outer.'+name)
    assert not target.exists()
    target.write_bytes(raw)
own_after=own_pins(a.revision); selected_after=selected_pins(a.revision); installed_after=installed_seal()
preserved=own_before==own_after and selected_before==selected_after and installed_before==installed_after and git('rev-parse','HEAD').decode().strip()==a.revision
write('after.json',{'revision':git('rev-parse','HEAD').decode().strip(),'own_pins':own_after,'selected_pins':selected_after,'installed':installed_after,'preserved':preserved})
write('execution.json',{'argv':argv,'outer_argv':outer_argv,'cwd':str(ROOT),'environment':environment,'revision':a.revision,'actual_exit':result.returncode,'elapsed_seconds':round(time.time()-started,3),'stdout':'.agent/evidence/122/qa1-outer.stdout','stderr':'.agent/evidence/122/qa1-outer.stderr','stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr),'sealed_helpers_preserved':preserved,'wrapper_exit':result.returncode if preserved else 1})
raise SystemExit(result.returncode if preserved else 1)
