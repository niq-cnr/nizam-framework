import hashlib,json,os,stat,subprocess,tempfile,shutil
from pathlib import Path
root=Path.cwd(); base='d52f0d134581caf0cff4fc0454551671559c1ce9'
def git(*args):return subprocess.check_output(['git',*args])
lines=git('ls-tree','-r','-z',base,'--','tools/fixtures').split(b'\0')
before={};modes={}
for line in lines:
 if not line:continue
 meta,path=line.split(b'\t',1); mode,kind,oid=meta.decode().split(); assert kind=='blob'
 rel=Path(path.decode()).relative_to('tools/fixtures').as_posix()
 before[rel]=hashlib.sha256(git('cat-file','blob',oid)).hexdigest();modes[rel]=mode
fixtures=root/'tools/fixtures'
after={p.relative_to(fixtures).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures.rglob('*') if p.is_file()}
assert set(before)==set(after),'fixture paths added or removed'
changed=sorted(p for p in before if before[p]!=after[p])
assert changed==['skill_index_neg_dangling_module.json','skill_index_neg_unindexed_capability.json'],changed
for rel,mode in modes.items():
 p=fixtures/rel; assert not p.is_symlink(),rel
 assert ('100755' if p.stat().st_mode & 0o111 else '100644')==mode,rel
def foundation(m):return {k:v for k,v in m.items() if k.split('/')[0]!='runtime_session'}
def digest(m):return hashlib.sha256(json.dumps(foundation(m),sort_keys=True,separators=(',',':')).encode()).hexdigest()
old=digest(before);new=digest(after)
assert old=='886374b8b18c9433a56a265dafa98dce43e9c9fa2a9008d4d4cc74af7c31f396'
assert new=='341fb00a82de3d09f80631c4ae4ea266f823a18115c4535fc4b7fd7d36642724'
prior=git('show','HEAD:tools/test_runtime_session.py')
current=(root/'tools/test_runtime_session.py').read_bytes()
assert current==prior.replace(old.encode(),new.encode(),1),'test source changed beyond one derived digest'
with tempfile.TemporaryDirectory(prefix='nf-fixture-anchor-independent-') as temp:
 scratch=Path(temp);shutil.copytree(root/'tools',scratch/'tools',ignore=shutil.ignore_patterns('__pycache__'))
 command=['python3','tools/test_runtime_session.py','--check','fixture-claim-registered']
 def run():return subprocess.run(command,cwd=scratch,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 positive=run();assert positive.returncode==0,positive.stdout+positive.stderr
 (scratch/'tools/test_runtime_session.py').write_bytes(prior)
 stale=run();assert stale.returncode==1 and 'foundation fixture bytes and paths preserved' in stale.stderr,stale.stdout+stale.stderr
 (scratch/'tools/test_runtime_session.py').write_bytes(current)
 victim=scratch/'tools/fixtures'/next(p for p in sorted(after) if p not in changed and not p.startswith('runtime_session/'))
 victim.write_bytes(victim.read_bytes()+b'\nindependent corruption\n')
 corrupted=run();assert corrupted.returncode==1 and 'foundation fixture bytes and paths preserved' in corrupted.stderr,corrupted.stdout+corrupted.stderr
print(json.dumps({'all_fixture_paths':len(after),'changed_files':changed,'all_other_fixture_bytes_equal':True,'all_fixture_modes_preserved':True,'baseline_digest':old,'updated_digest':new,'repair_source_diff':'one digest only','current_exit':positive.returncode,'stale_anchor_exit':stale.returncode,'unrelated_corruption_exit':corrupted.returncode,'whole_fixture_suite':'not_run; CI still required'},indent=2))
