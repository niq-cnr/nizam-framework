"""Static final-context repair proof; no product imports or behavior."""
import ast,hashlib,subprocess
from pathlib import Path
base='a8a519bbac32631fc733652761baa2a3f72d1488';path='tools/workflow_assurance.py'
def old(name,revision=base):return subprocess.check_output(['git','show',revision+':'+name])
def defs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
raw=Path(path).read_bytes();compile(raw,path,'exec');before=defs(old(path));after=defs(raw)
assert {n for n in before if before[n]!=after[n]}=={'_ControlsProof'}
def methods(value):
 cls=next(n for n in ast.parse(value).body if isinstance(n,ast.ClassDef) and n.name=='_ControlsProof')
 return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
prior=methods(old(path));current=methods(raw)
assert set(prior)==set(current) and {n for n in prior if prior[n]!=current[n]}=={'exact_commit','entry','replay'}
original=defs(old(path,'3e824cbc7b18b458edc82e8f63d900b510c68d2c'))
assert len(original)==55 and all(after[n]==v for n,v in original.items())
for name,digest in [('tools/workflow_assurance_ci.py','7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905'),('tools/test_workflow_assurance.py','9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'),('.agent/contracts/123.json','64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5')]:
 data=Path(name).read_bytes();assert data==old(name) and hashlib.sha256(data).hexdigest()==digest
 print('STATIC preserved '+name+' '+digest)
assert Path('.agent/run_state.json').read_bytes()==old('.agent/run_state.json')
assert subprocess.check_output(['git','diff','--name-only',base],text=True).splitlines()==[path]
assert not subprocess.check_output(['git','diff',base,'--','.nizam'])
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','.nizam'])
assert sum(p.is_file() and not p.is_symlink() for p in Path('.nizam').rglob('*'))==239
subprocess.run(['git','diff','--check'],check=True)
print('STATIC compile; exactly3private methods changed; all55 inherited and all other private method ASTs exact')
print('STATIC installed239/Root coordination/unrelated tracked bytes and modes preserved')
print('STATIC Source SHA256 '+hashlib.sha256(raw).hexdigest())
print('No product import/API/constructor/helper/selector/observer/namespace/compliance/model/hosted behavior')
