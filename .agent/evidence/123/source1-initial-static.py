"""Authorized initial Source syntax/preservation inspection, no product imports."""
import ast
import hashlib
from pathlib import Path
import subprocess

base='3e824cbc7b18b458edc82e8f63d900b510c68d2c'
for path in ['tools/workflow_assurance.py','tools/workflow_assurance_ci.py']:
 raw=Path(path).read_bytes();compile(raw,path,'exec');print('STATIC in-memory compile: '+path)
old=subprocess.check_output(['git','show',base+':tools/workflow_assurance.py'])
old_tree=ast.parse(old);new_tree=ast.parse(Path('tools/workflow_assurance.py').read_bytes())
def definitions(tree):return {node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
prior=definitions(old_tree);current=definitions(new_tree)
assert len(prior)==55 and all(current.get(k)==v for k,v in prior.items())
assert {'verify_controls_ready','_ControlsProof'}<=set(current)
for path in ['tools/test_workflow_assurance.py','.agent/contracts/123.json','.agent/run_state.json']:
 expected=subprocess.check_output(['git','show',base+':'+path]);assert Path(path).read_bytes()==expected
 print('STATIC preserved '+path+' sha256='+hashlib.sha256(expected).hexdigest())
changed=subprocess.check_output(['git','diff','--name-only',base],text=True).splitlines()
allowed={'tools/workflow_assurance.py','.github/workflows/compliance.yml','tools/fixtures_self_test.sh','tools/README.md','CHANGELOG.md'}
assert set(changed)<=allowed,changed
assert subprocess.check_output(['git','diff',base,'--','.nizam'])==b''
assert Path('tools/workflow_assurance_ci.py').stat().st_mode&0o111
print('STATIC all55 inherited Source ASTs, frozen test/contract/Root state and installed payload preserved')
print('No Source import, constructor, API, test, checker, bank, namespace, model, compliance or CI behavior executed')
