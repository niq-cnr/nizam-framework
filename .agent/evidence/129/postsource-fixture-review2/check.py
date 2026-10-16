import ast,hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();candidate='6d1bda89c049c9df1c32153f36d880c3d04e2b72';evidence='e9584f4214ae3e6979093dff5620bba7bef83e7f'
git=lambda *args:subprocess.check_output(['git',*args]);read=lambda rev,path:git('show',rev+':'+path)
sha=lambda raw:hashlib.sha256(raw).hexdigest();runner='tools/test_runtime_session.py'
old=(root/runner).read_bytes();new=read(candidate,runner)
assert sha(old)=='81a7299120ad79cca1765e6c4c47f0d8907bfa6e593804a9ffd97210700dffe4'
assert sha(new)=='a61a2ec17e729a6c6ea0b9090a639beb0903db49c4d9869b948d908d568bdf1e'
assert old.count(b"release = stub.home / 'release-stub'")==1
assert new==old.replace(b"release = stub.home / 'release-stub'",b"release = stub.state / 'release-stub'")
assert git('diff','--name-only',candidate+'^',candidate).decode().splitlines()==[runner]
assert git('rev-parse',candidate+':'+runner).decode().strip()=='915d91be3cd9bd03edaf804fee381863140ffc55'
before=ast.parse(old);after=ast.parse(new)
target=next(n for n in before.body if isinstance(n,ast.FunctionDef) and n.name=='live_runtime_guards')
assignments=[n for n in ast.walk(target) if isinstance(n,ast.Assign) and isinstance(n.value,ast.BinOp) and isinstance(n.value.right,ast.Constant) and n.value.right.value=='release-stub']
assert len(assignments)==1 and assignments[0].value.left.attr=='home';assignments[0].value.left.attr='state'
assert ast.dump(before)==ast.dump(after);compile(new,runner,'exec')
freeze=json.loads((root/'.agent/evidence/129/frozen-bundle1.json').read_bytes())
for path,expected in [('.agent/contracts/129.json',freeze['bundle']['contract_sha256']),('.agent/evidence/129/interface-intent1.json',freeze['bundle']['interface_sha256'])]:
    assert sha(read(candidate,path))==expected and read(candidate,path)==(root/path).read_bytes()
assert read(candidate,'tools/runtime_session.py')==(root/'tools/runtime_session.py').read_bytes()
assert b'insist(release.is_absolute() and release.resolve().is_relative_to(self.root))' in (root/'tools/runtime_session.py').read_bytes()
assert git('rev-parse',candidate+':.nizam')==git('rev-parse','HEAD:.nizam')
assert len([p for p in git('ls-tree','-r','--name-only',candidate,'.nizam').decode().splitlines()])==239
prefix='.agent/evidence/129/fixture-correction1/'
index=json.loads(read(evidence,prefix+'raw-index.json'))
for path,entry in index.items():
    data=read(evidence,prefix+path);assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
frame=json.loads(read(evidence,prefix+'static1.execution.json'))
assert frame['actual_exit']==0 and frame['child_pid']==3781478 and not frame['timed_out']
print('STATIC_PASS exactone-line/ASTattribute-only correction; all other runner bytes/assertions/11commands/nativefixtures unchanged; contract/interface/productguard/installed239 preserved; author indexed evidence/actual0 verified. No native/controller/test rerun.')
