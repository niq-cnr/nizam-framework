"""Independent frozen SourceC audit and caller self-grant negative in scratch."""
import hashlib,importlib.util,json,pathlib,stat,subprocess,tempfile
r=pathlib.Path.cwd();e=r/'.agent/evidence/117';candidate=json.loads((e/'source-candidate.json').read_text());b=json.loads((e/'acceptance-bundle.json').read_text())
def sha(x):return hashlib.sha256(x).hexdigest()
def git(*args):return subprocess.check_output(['git',*args])
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=candidate['revision'];B=b['baseline']['commit'];assert git('rev-parse',C+'^{tree}').decode().strip()==candidate['tree']
assert candidate['sealed_dependencies_sha256']=={v['path']:v['sha256'] for v in b['inputs']}
for path,h in candidate['source_sha256'].items():assert sha((r/path).read_bytes())==h==sha(git('show',C+':'+path))
for v in b['inputs']:
 p=r/v['path'];assert stat.S_ISREG(p.lstat().st_mode) and not p.is_symlink()
 assert sha(p.read_bytes())==v['sha256']==sha(git('show',B+':'+v['path']))==sha(git('show',C+':'+v['path']))
 for rev in (B,C):assert v['executable']==bool(p.stat().st_mode&0o111)==(git('ls-tree',rev,v['path']).decode().split()[0]=='100755')
for row in b['baseline_evidence']:
 for stage in ('setup','positive','red'):
  v=row[stage];assert sha((r/v['path']).read_bytes())==v['sha256']==sha(git('show',C+':'+v['path']))
old=git('show','2be0cf4d5773d9d0d7e7c4fb5de935ff4fd67d57:tools/workflow_assurance.py');current=(r/'tools/workflow_assurance.py').read_bytes()
assert old.split(b'def main():')[0]==current.split(b'def _entry_blob(')[0].rstrip()+b'\n\n'
print('PASS actual SourceC commit/tree/four hashes/all27 current-GitB-SourceC bytes/modes and12 frozen proof hashes',flush=True)
api=load(r/'tools/workflow_assurance.py','mode_b117_product');fixtures=load(e/'entry-fixtures.py','mode_b117_fixture')
with tempfile.TemporaryDirectory(prefix='reviewer117-selfgrant-') as parent:
 f=fixtures.EntryFixture(parent);assert api.verify_authorized_entry(f.root,f.entry) is True
 print('PASS actual valid Generator product grant',flush=True)
 original=(f.root/fixtures.CONTRACT).read_bytes();contract=f.read(fixtures.CONTRACT)
 contract['entry_write_grants'].append({'role':'Generator','profile':'generator-deterministic','path':'.agent/run_state.json','fields':['/current_feature'],'operation':'write','full_file':False,'create_only':False})
 f.write(fixtures.CONTRACT,contract);f.rehash_contract();f.entry['writes']=[{'path':'.agent/run_state.json','fields':['/current_feature'],'operation':'write'}]
 try:api.verify_authorized_entry(f.root,f.entry)
 except api.AssuranceError as exc:
  assert 'unapproved entry obligation change' in str(exc);print('PASS caller-rehashed coordination self-grant rejects: '+str(exc),flush=True)
 else:raise AssertionError('POLICY_ASSERTION: unauthorized caller-rehashed grant accepted')
 f.write(fixtures.CONTRACT,original);f.rehash_contract();f.entry['writes']=[{'path':'tools/workflow_assurance.py','fields':[],'operation':'write'}]
 assert api.verify_authorized_entry(f.root,f.entry) is True;print('PASS restored approved actual entry',flush=True)
