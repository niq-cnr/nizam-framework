"""Static-only syntax, ownership and preservation checks; no product imports."""
import ast
import hashlib
from pathlib import Path
import subprocess

base='5e1891db72dd0645c693ec24cd4dc7188806f652'
original='3e824cbc7b18b458edc82e8f63d900b510c68d2c'
source='tools/workflow_assurance.py'
runner='tools/workflow_assurance_ci.py'
def frozen(path,revision=base):return subprocess.check_output(['git','show',revision+':'+path])
def definitions(raw):return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(raw).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
for path in [source,runner]:
 raw=Path(path).read_bytes();compile(raw,path,'exec');print('STATIC compile '+path+' SHA256 '+hashlib.sha256(raw).hexdigest())
prior=definitions(frozen(source,original));current=definitions(Path(source).read_bytes())
assert len(prior)==55 and all(current.get(name)==value for name,value in prior.items())
print('STATIC all55 inherited Source top-level AST definitions unchanged')
for path,expected in [('tools/test_workflow_assurance.py','9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'),('.agent/contracts/123.json','64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5')]:
 raw=Path(path).read_bytes();assert raw==frozen(path) and hashlib.sha256(raw).hexdigest()==expected
 print('STATIC immutable '+path+' '+expected)
assert Path('.agent/run_state.json').read_bytes()==frozen('.agent/run_state.json')
changed=subprocess.check_output(['git','diff','--name-only',base],text=True).splitlines()
assert set(changed)=={source,runner},changed
assert subprocess.check_output(['git','diff',base,'--','.nizam'])==b''
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','.nizam'])
assert Path(runner).stat().st_mode&0o111
subprocess.run(['git','diff','--check'],check=True)
print('STATIC only contracted new Source/runner changed; Root state, installed payload, frozen tests/contract preserved')
print('No product import, API, constructor, selector, namespace, bank, compliance, hosted or model execution')
