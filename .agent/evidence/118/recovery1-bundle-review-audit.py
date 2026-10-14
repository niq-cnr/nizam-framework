"""Independent B2 input/archive/map audit and public pre-Source adversary."""
import copy,hashlib,importlib.util,json,os,shlex,stat,subprocess,tempfile
from pathlib import Path
E='.agent/evidence/118/';ROOT=Path.cwd();HEAD=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
def read(p):return json.loads(Path(p).read_bytes())
def git(*a):return subprocess.check_output(['git',*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def mode(path):
 st=Path(path).lstat();assert stat.S_ISREG(st.st_mode);return bool(st.st_mode&0o111)
def check_blob(path,revision,digest,executable):
 raw=git('show',revision+':'+path);row=git('ls-tree',revision,'--',path).decode().split();assert row[1]=='blob' and row[0] in ['100644','100755'];assert type(executable) is bool and (row[0]=='100755')==executable and sha(raw)==digest;return raw
h=read(E+'recovery1-test-author-handoff.json');b=read(E+'acceptance-bundle.json');c=read('.agent/contracts/118.json');manifest=read(E+'runtime-inputs.json')
assert b['baseline']==h['baseline'] and b['baseline']['commit']=='07d5a780b16de3d44c5aac263f41404c0b9049d2' and git('rev-parse',b['baseline']['commit']+'^{tree}').decode().strip()==b['baseline']['tree']
assert b['seal_sha256']==h['seal_sha256']=='bd0f7f22e086b780b4b28cefe656c7a0f75e908ed8a098a076d3a253d3203a61' and b['seal_sha256']==sha(canonical({k:v for k,v in b.items() if k!='seal_sha256'}))
assert b['inputs']==h['frozen_inputs'] and len(b['inputs'])==31
expected=(set(manifest['runtime_paths'])|set(manifest['core_paths']))-{'tools/workflow_assurance.py'};assert len(expected)==31 and expected=={row['path'] for row in b['inputs']}
for row in b['inputs']:
 raw=check_blob(row['path'],b['baseline']['commit'],row['sha256'],row['executable']);assert raw==Path(row['path']).read_bytes() and mode(row['path'])==row['executable']
assert b['roles']==read(E+'role-sessions.json')
for k in ['agent_id','session_id']:assert len({r[k] for r in b['roles'].values()})==3
print('PASS independently verified exact B2 commit/tree/seal and31 frozen current/Git bytes/modes and distinct roles')
prov=read(E+'pre-revision2-provenance.json');b1=json.loads(git('show',prov['approved_overlay']+':'+E+'acceptance-bundle.json'));oldrows=[dict(row,revision=b1['baseline']['commit']) for row in b1['inputs']]
for path in [E+'acceptance-bundle.json','.agent/validator/118-test-bundle-review.json']:
 row=git('ls-tree',prov['approved_overlay'],'--',path).decode().split();oldrows.append(dict(path=path,revision=prov['approved_overlay'],sha256=sha(git('show',prov['approved_overlay']+':'+path)),executable=row[0]=='100755'))
assert len(oldrows)==32
for row in oldrows:
 raw=check_blob(row['path'],row['revision'],row['sha256'],row['executable']);archive=E+'predecessor-bundle1/'+row['path'];assert Path(archive).read_bytes()==raw and mode(archive)==row['executable']
print('PASS32 exact B1 input/bundle/review archives against immutable Git and executable modes')
all_paths=set()
for stage in ['precode','inputs','bundle']:
 path=c['acceptance_successor_policy']['stage_records'][stage];m=read(path);assert set(m)=={'feature','stage','actor','predecessor_ref','successor_revision','rows','evidence_refs'} and m['stage']==stage and m['feature']=='118';assert Path(path).read_bytes()==git('show',HEAD+':'+path)
 for row in m['rows']:
  p=row['canonical_path'];assert p not in all_paths;all_paths.add(p);assert set(row)=={'canonical_path','owner','old','new'} and row['new']['revision']==m['successor_revision'] and p in c['acceptance_successor_policy']['canonical_replacements'][row['owner']]
  for side in ['old','new']:
   x=row[side];raw=check_blob(x['path'],x['revision'],x['sha256'],x['executable']);current=x['archive_path'] if side=='old' else p;assert Path(current).read_bytes()==raw and mode(current)==x['executable']
 assert len(m['evidence_refs'])==len(set(m['evidence_refs'])) and all(Path(x).is_file() for x in m['evidence_refs'])
 print('PASS finite committed successor map',stage,len(m['rows']))
assert len(all_paths)==9
assert not Path(c['acceptance_successor_policy']['stage_records']['review']).exists()
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
 assert Path(path).read_bytes()==git('show',h['approved_contract_revision']+':'+path)
print('PASS unchanged product and exact public runner; review map correctly absent before reviewer commit')
# Own public adversary: source-looking change before a committed B2 review map.
with tempfile.TemporaryDirectory(prefix='nizam118-B2-ownspot-') as parent:
 scratch=Path(parent)/'repo';subprocess.run(['git','clone','-q','--shared',str(ROOT),str(scratch)],check=True)
 target=scratch/'tools/workflow_assurance.py';saved=target.read_bytes();target.write_bytes(saved+b'\n# PRIVATE reviewer pre-review source probe\n')
 args=['python3','tools/test_workflow_assurance.py','--scope-118','--base',c['scope_base_revision']];r=subprocess.run(args,cwd=scratch,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 path=Path(E+'recovery1-bundle-review-ownspot-raw.txt');assert not path.exists();path.write_text('COMMAND: PYTHONDONTWRITEBYTECODE=1 '+shlex.join(args)+'\nREVISION: '+HEAD+'\nEXIT: '+str(r.returncode)+'\nSTDOUT:\n'+r.stdout+'\nSTDERR:\n'+r.stderr)
 assert r.returncode!=0 and 'POLICY_ASSERTION: no Source before review mapping' in r.stderr,(r.returncode,r.stdout,r.stderr)
print('PASS independent public adversary: Source modification rejected before actual review mapping, expected semantic diagnostic')
