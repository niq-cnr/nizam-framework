"""One independent frozen replay capture; invoke only after explicit Root release."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'.agent/evidence/122'
parser=argparse.ArgumentParser();parser.add_argument('--release-revision',required=True);args=parser.parse_args()
assert re.fullmatch('[0-9a-f]{40}',args.release_revision)
prefix=E/'executable1-current-replay'
assert not any(Path(str(prefix)+s).exists() for s in ('.stdout','.stderr','.execution.json'))
pins={'tools/workflow_assurance.py':'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6','tools/test_workflow_assurance.py':'800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae','.agent/contracts/122.json':'13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5','.agent/evidence/122/controls3-run.py':'2e5f6e8dfac4479ed035fe50efbccaea73a0a89ef55b2c5de31661b4a6b04110','.agent/evidence/122/controls3-identities.pack':'9454336d15029f7520c3c5dee04ffce62fe44a7415a30f81096d66aa19611004'}
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in pins.items())
binary=Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='81ba53616316440d4afc8a99107301b32790eb1a9157bdd97274017fbd4d0e4b'
env=dict(PATH=str(binary.parent)+':'+os.defpath,GIT_EXEC_PATH='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core',HOME=os.environ['HOME'],LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
argv=[sys.executable,'.agent/evidence/122/controls3-run.py','--release-revision',args.release_revision,'--run-id','executable-review1']
revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip()
result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
for suffix,data in (('.stdout',result.stdout),('.stderr',result.stderr)):
    with Path(str(prefix)+suffix).open('xb') as f:f.write(data)
with Path(str(prefix)+'.execution.json').open('x') as f:
    json.dump(dict(argv=argv,cwd=str(ROOT),environment=env,exercised_revision=revision,release_revision=args.release_revision,actual_exit=result.returncode,stdout=str(prefix.relative_to(ROOT))+'.stdout',stderr=str(prefix.relative_to(ROOT))+'.stderr',stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr_sha256=hashlib.sha256(result.stderr).hexdigest(),pins=pins,classification='independent current24-command executable replay; failure is retained and never retried here'),f,indent=2);f.write('\n')
print('INDEPENDENT_REPLAY_ACTUAL_EXIT',result.returncode,flush=True)
sys.exit(result.returncode)
