"""Static-only freeze: no product/fixture/test import or behavior execution."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import jsonschema

ROOT=Path(__file__).resolve().parents[3]
BASE='298ff148d0d2f28beda70a7e9063787c28d6fc0e'
PRESERVED='f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def dump(node):return ast.dump(node,include_attributes=False)
def definitions(module):return {n.name:dump(n) for n in module.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def inventories(module):
    values={}
    def literal(node):
        if isinstance(node,ast.Name):return values[node.id]
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return literal(node.left)+literal(node.right)
        return ast.literal_eval(node)
    for node in module.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id.endswith('CASES'):
            values[node.targets[0].id]=literal(node.value)
    return values
class ProjectInheritedMain(ast.NodeTransformer):
    def visit_BinOp(self,node):
        node=self.generic_visit(node)
        return node.left if isinstance(node.op,ast.Add) and isinstance(node.right,ast.Name) and node.right.id=='CONTROL_CASES' else node
    def visit_IfExp(self,node):
        node=self.generic_visit(node)
        if isinstance(node.test,ast.Compare) and any(isinstance(n,ast.Name) and n.id=='CONTROL_CASES' for n in ast.walk(node.test)):return node.orelse
        return node
    def visit_If(self,node):
        if isinstance(node.test,ast.Compare) and any(isinstance(n,ast.Constant) and n.value=='controls-ready' for n in ast.walk(node.test)):return None
        return self.generic_visit(node)
    def visit_Tuple(self,node):
        node=self.generic_visit(node);node.elts=[n for n in node.elts if not isinstance(n,ast.Constant) or n.value!='controls-ready'];return node

assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
contract_path=ROOT/'.agent/contracts/123.json'; contract=json.loads(contract_path.read_bytes())
assert hashlib.sha256(contract_path.read_bytes()).hexdigest()=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
assert contract['status']=='approved' and contract['approval_evidence']['proposal_sha256']=='cc441e823e3dcf430228527d938ad0aa5944e5181f7a5a8a6181774b37cb1f74'
interface=json.loads((ROOT/'.agent/evidence/123/api-interface.json').read_bytes())
assert interface['approved_contract']['sha256']==hashlib.sha256(contract_path.read_bytes()).hexdigest()
assert interface['selectors']==['ci-candidate-bound','ci-blocker-rejected'] and interface['default_count']==48
for schema in ('schema/contract.schema.json','.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(json.loads((ROOT/schema).read_bytes())).validate(contract)
proof={}
for path in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py'):
    old=ast.parse(git('show',PRESERVED+':'+path));new=ast.parse((ROOT/path).read_bytes())
    before,after=definitions(old),definitions(new)
    for name,value in before.items():
        if name!='main':assert after[name]==value,'inherited definition changed: '+name
    if path.endswith('/workflow_assurance.py'):
        assert (ROOT/path).read_bytes()==git('show',BASE+':'+path),'author touched Source'
    else:
        expected,actual=inventories(old),inventories(new)
        assert all(actual[k]==v for k,v in expected.items()),'inherited inventory changed'
        labels=sum((actual[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')),())
        assert len(labels)==46 and len(set(labels))==46
        assert actual['CONTROL_CASES']==('ci-candidate-bound','ci-blocker-rejected')
        assert len(set(labels+actual['CONTROL_CASES']))==48
        main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        assert dump(ProjectInheritedMain().visit(main))==before['main'],'main is not exactly additive dispatch'
    proof[path]={'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),'inherited_definitions':len(before)}
    compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
for path in ('.agent/evidence/123/author1-concrete-static.py','.agent/evidence/123/author1-controls.py'):
    compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
rows=[row for row in git('ls-tree','-rz',BASE,'--','.nizam').split(b'\0') if row]
for row in rows:
    header,path=row.split(b'\t');mode,kind,blob=header.split();target=ROOT/path.decode()
    assert kind==b'blob' and mode in (b'100644',b'100755') and target.is_file() and not target.is_symlink()
    assert target.stat().st_nlink==1 and target.read_bytes()==git('cat-file','blob',blob.decode()),'installed bytes/type changed'
    assert stat.S_IMODE(target.stat().st_mode)==(0o755 if mode==b'100755' else 0o644),'installed full mode changed'
assert len(rows)==239
allowed=('tools/test_workflow_assurance.py','.agent/evidence/123/api-interface.json','.agent/evidence/123/author1-concrete-', '.agent/evidence/123/author1-controls.py')
changed=git('diff','--name-only',BASE).decode().splitlines()+git('ls-files','--others','--exclude-standard').decode().splitlines()
assert all(any(p==a or (a.endswith('-') and p.startswith(a)) for a in allowed) for p in changed),'unowned changed path'
for path in ('.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml'):
    assert (ROOT/path).read_bytes()==git('show',BASE+':'+path),'coordination changed'
print(json.dumps({'static_only':True,'revision':git('rev-parse','HEAD').decode().strip(),'contract_revision':'452a5a5f748b5234ce1da3ad765b0da8f622cb53',
    'proof':proof,'inherited_cases':46,'default_cases':48,'installed_regular_files':239,'preservation_anchor':PRESERVED,'changed_paths':changed},sort_keys=True))
