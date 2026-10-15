"""Prepared once-only pinned-Git affected selector; run only after renewed review and explicit Root release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
GIT = Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
GIT_SHA256 = '81ba53616316440d4afc8a99107301b32790eb1a9157bdd97274017fbd4d0e4b'
TEST_SHA256 = '800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'
def sha(data): return hashlib.sha256(data).hexdigest()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--release-revision',required=True); parser.add_argument('--run-id',required=True)
args = parser.parse_args(); assert re.fullmatch('[0-9a-f]{40}',args.release_revision) and re.fullmatch('[a-z0-9-]+',args.run_id)
prefix = ROOT/('.agent/evidence/122/author4-'+args.run_id)
assert not any(prefix.parent.glob(prefix.name+'*')), 'selector output prefix already used'
assert sha(GIT.read_bytes()) == GIT_SHA256 and sha((ROOT/'tools/test_workflow_assurance.py').read_bytes()) == TEST_SHA256
env = dict(PATH=str(GIT.parent)+':'+os.defpath,GIT_EXEC_PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core',
    HOME=os.environ['HOME'],LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
assert subprocess.check_output([str(GIT),'-C',str(ROOT),'show',args.release_revision+':tools/test_workflow_assurance.py'],env=env) == (ROOT/'tools/test_workflow_assurance.py').read_bytes()
subprocess.run([str(GIT),'-C',str(ROOT),'merge-base','--is-ancestor',args.release_revision,'HEAD'],env=env,check=True)
paths = set(subprocess.check_output([str(GIT),'-C',str(ROOT),'ls-files','-z'],env=env).decode().split('\0'))-{''}
paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'.nizam').rglob('*') if p.is_file())
def snapshot():
    rows = [[p,stat.S_IMODE((ROOT/p).lstat().st_mode),sha((ROOT/p).read_bytes())] for p in sorted(paths)]
    return dict(count=len(rows),all_bytes_modes_sha256=sha(json.dumps(rows,separators=(',',':')).encode()),selected={p:[m,s] for p,m,s in rows if p in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json')})
before = snapshot(); argv = [sys.executable,'tools/test_workflow_assurance.py','--case','semantic-failed']
result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True); after = snapshot()
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with Path(str(prefix)+suffix).open('xb') as handle: handle.write(data)
with Path(str(prefix)+'.execution.json').open('x') as handle:
    json.dump(dict(argv=argv,cwd=str(ROOT),environment=env,exercised_revision=subprocess.check_output([str(GIT),'-C',str(ROOT),'rev-parse','HEAD'],env=env).decode().strip(),
        release_revision=args.release_revision,git_binary_sha256=GIT_SHA256,test_sha256=TEST_SHA256,actual_exit=result.returncode,expected_exit=0,
        protected_before=before,protected_after=after,protected_unchanged=before==after,stdout=str(prefix.relative_to(ROOT))+'.stdout',stderr=str(prefix.relative_to(ROOT))+'.stderr'),handle,indent=2)
    handle.write('\n')
print('affected-selector actual_exit='+str(result.returncode))
sys.exit(result.returncode if result.returncode else (0 if before==after else 1))
