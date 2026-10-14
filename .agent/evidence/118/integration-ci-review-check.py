import copy,hashlib,json,os,re,subprocess
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[3]
os.chdir(ROOT)
def git(*args): return subprocess.check_output(['git',*args])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
revision=git('rev-parse','HEAD').decode().strip()
assert revision=='a87e62929959a2b6f58414a335e4369b33dfac29'
p='.github/workflows/compliance.yml'
old=yaml.safe_load(git('show','HEAD^:'+p)); new=yaml.safe_load(Path(p).read_bytes())
checkout=new['jobs']['fixtures_self_test']['steps'][0]
assert type(checkout['with']['fetch-depth']) is int and checkout['with']['fetch-depth']==0
assert checkout['with']['persist-credentials'] is False
assert checkout['uses']=='actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683'
normalized=copy.deepcopy(new); del normalized['jobs']['fixtures_self_test']['steps'][0]['with']['fetch-depth']
assert normalized==old
changed=git('diff','--name-only','HEAD^','HEAD').decode().splitlines()
assert all(x==p or x.startswith('.agent/evidence/118/integration-ci-') for x in changed)
print('PASS typed sole workflow delta: strict integer fetch-depth0; SHA pin, persist-credentials false, jobs and all remaining steps exact')
handoff=json.loads(Path('.agent/evidence/118/integration-ci-handoff.json').read_text())
for path,digest in handoff['evidence_sha256'].items(): assert sha(path)==digest,path
for name,expected in [('shallow-default20',1),('full-default20',0),('full-readiness',0)]:
 raw=Path('.agent/evidence/118/integration-ci-'+name+'.txt').read_text()
 assert re.findall(r'^EXIT: (.*)$',raw,re.M)==[str(expected)]
 assert re.findall(r'^REVISION: (.*)$',raw,re.M)==[handoff['base_revision']]
 assert raw.count('\nPASS ')==(16 if name=='shallow-default20' else 20 if name=='full-default20' else 1)
print('PASS actual author receipt hashes, same exercised baseline, shallow16/red1 and full20/readiness0')
ledger=json.loads(Path('.agent/evidence/118/historical-runtime-inputs.json').read_text())
for row in ledger['inputs']:
 assert hashlib.sha256(git('show',row['revision']+':'+row['path'])).hexdigest()==row['sha256']
 # Full checkout receives history reachable from the PR head and release tags.
 reachable=subprocess.run(['git','merge-base','--is-ancestor',row['revision'],revision]).returncode==0
 if not reachable:
  assert git('tag','--contains',row['revision']).strip(),row['revision']
assert git('rev-parse','refs/tags/'+ledger['tag']+'^{commit}').decode().strip()==ledger['tag_revision']
print('PASS 23 exact historical Git blobs are reachable from reviewed head or fetched tags; actual installed tag pinned')
assert git('rev-parse','--is-shallow-repository').strip()==b'false'
command=['python3','tools/test_workflow_assurance.py']
p=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),text=True,capture_output=True)
print('PERSONAL_COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py')
print('PERSONAL_EXIT:',p.returncode)
print(p.stdout,end=''); print(p.stderr,end='')
assert p.returncode==0 and len(re.findall(r'^PASS ',p.stdout,re.M))==20
print('PASS independent current full-history default20; remote GitHub rerun remains pending')
