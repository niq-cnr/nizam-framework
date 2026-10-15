"""Independent static review; no product/test imports or fixture execution."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT=Path(__file__).resolve().parents[3]
RELEASE='532086c3ab8e9df5275d0ad2cb724823935a5fb9'
BASE='f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(node):return ast.dump(node,include_attributes=False)
def definitions(tree):return {n.name:dump(n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def inventories(tree):
    result={}
    def value(node):
        if isinstance(node,ast.Name):return result[node.id]
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return value(node.left)+value(node.right)
        return ast.literal_eval(node)
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id.endswith('CASES'):
            result[node.targets[0].id]=value(node.value)
    return result
class InheritedMain(ast.NodeTransformer):
    def visit_BinOp(self,node):
        node=self.generic_visit(node)
        return node.left if isinstance(node.op,ast.Add) and isinstance(node.right,ast.Name) and node.right.id=='CONTROL_CASES' else node
    def visit_IfExp(self,node):
        node=self.generic_visit(node)
        return node.orelse if any(isinstance(n,ast.Name) and n.id=='CONTROL_CASES' for n in ast.walk(node.test)) else node
    def visit_If(self,node):
        if any(isinstance(n,ast.Constant) and n.value=='controls-ready' for n in ast.walk(node.test)):return None
        return self.generic_visit(node)
    def visit_Tuple(self,node):
        node=self.generic_visit(node);node.elts=[n for n in node.elts if not isinstance(n,ast.Constant) or n.value!='controls-ready'];return node
def snapshot():
    paths=[row.split(b'\t')[1].decode() for row in git('ls-tree','-rz',RELEASE,'--','.nizam').split(b'\0') if row]
    paths+=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/123.json','.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml']
    return {p:(stat.S_IMODE((ROOT/p).lstat().st_mode),(ROOT/p).lstat().st_nlink,sha((ROOT/p).read_bytes())) for p in paths}
assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1' and git('rev-parse','HEAD').decode().strip()==RELEASE
before=snapshot();freeze=json.loads((ROOT/'.agent/evidence/123/author2-freeze.json').read_bytes())
for row in freeze['owned_refs']+[freeze['approved_contract'],freeze['source_anchor']]:
    data=git('show',row['revision']+':'+row['path']);header=git('ls-tree',row['revision'],'--',row['path']).split(b'\t')[0].decode().split()
    assert sha(data)==row['sha256'] and header==[row['git_mode'],'blob',row['git_blob']]
    assert (ROOT/row['path']).read_bytes()==data
source=(ROOT/'tools/workflow_assurance.py').read_bytes();tests=(ROOT/'tools/test_workflow_assurance.py').read_bytes()
assert source==git('show',BASE+':tools/workflow_assurance.py')
assert sha(tests)=='846688d44ea34a20045c9a9f34fae7580cc772aa977a3c2b06dc9b2f13778871'
old=ast.parse(git('show',BASE+':tools/test_workflow_assurance.py'));new=ast.parse(tests)
old_defs,new_defs=definitions(old),definitions(new)
assert all(new_defs[k]==v for k,v in old_defs.items() if k!='main')
main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
assert dump(InheritedMain().visit(copy.deepcopy(main)))==old_defs['main']
old_inv,new_inv=inventories(old),inventories(new)
assert all(new_inv[k]==v for k,v in old_inv.items())
cases=sum((old_inv[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')),())
assert len(cases)==46 and new_inv['CONTROL_CASES']==('ci-candidate-bound','ci-blocker-rejected')
for path in ('tools/test_workflow_assurance.py','.agent/evidence/123/author2-controls.py','.agent/evidence/123/author2-static.py'):
    compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
contract=json.loads((ROOT/'.agent/contracts/123.json').read_bytes())
assert sha((ROOT/'.agent/contracts/123.json').read_bytes())=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
assert len(contract['protocol']['payload_catalog'])==31
assert 'sparse-checkout' not in tests.decode().split('self.candidate =',1)[0].split('class ControlsFixture',1)[1]
assert 'assessed_revision=actual[field]' in tests.decode()
assert 'actual Root .agent/evidence/123/selection.json' in contract['protocol']['bundle_transport']['produce']
assert not git('ls-tree',RELEASE,'--','.agent/evidence/123/selection.json')
assert 'self.checkout = dict(sha=self.source' in tests.decode() and "path='.agent/evidence/123/synthetic-root/%s/%04d-%s'" in tests.decode()
assert len([p for p in before if p.startswith('.nizam/')])==239 and snapshot()==before
print(json.dumps({'static_only':True,'actual_static_exit':0,'exercised_revision':RELEASE,'verified_owned_refs':len(freeze['owned_refs']),
    'inherited_source_definitions':len(definitions(ast.parse(source))),'inherited_test_definitions':len(old_defs),'inherited_cases':46,'default_cases':48,'additive_main':True,
    'payload_groups':31,'installed_regular_files':239,'current_protected_inputs_unchanged':len(before),'source_sha256':sha(source),'test_sha256':sha(tests),
    'fixed_outer_selection_path_in_source_checkout':False,'producer_selection_path':'unique synthetic-root namespace','checkout_sha_expression':'self.source, predating selection creation',
    'behavior_executed':False,'constructor_executed':False,'scope':'Static inspection success is not provisional approval; selection/checkout producer binding evaluated in separate verdict.'},sort_keys=True))
