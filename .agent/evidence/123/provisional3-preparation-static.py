"""Single independent review3 static observation; never execute product/tests."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import jsonschema

ROOT=Path(__file__).resolve().parents[3]
CODE='9718b72ab1a988fe384c8f0d69afd6d1c4ac56e8'
RELEASE='61f55a2f9677339c513cd0d4dd0a70ccef467e82'
PRESERVED='f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(node):return ast.dump(node,include_attributes=False)
def definitions(tree):return {n.name:dump(n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def inventories(tree):
    names={}
    def value(node):
        if isinstance(node,ast.Name):return names[node.id]
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return value(node.left)+value(node.right)
        return ast.literal_eval(node)
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id.endswith('CASES'):
            names[node.targets[0].id]=value(node.value)
    return names
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
installed=[r for r in git('ls-tree','-rz',CODE,'--','.nizam').split(b'\0') if r]
installed_paths=[r.split(b'\t')[1].decode() for r in installed]
current_paths=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/123.json','.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml']
owned=['tools/test_workflow_assurance.py','.agent/evidence/123/author3-api-interface.json','.agent/evidence/123/author3-controls.py','.agent/evidence/123/author3-preparation.json']
def snapshot():
    return {p:(stat.S_IMODE((ROOT/p).lstat().st_mode),(ROOT/p).lstat().st_nlink,sha((ROOT/p).read_bytes())) for p in installed_paths+current_paths+owned[1:]}

assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
revision=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',CODE,revision)
before=snapshot();refs=[]
for path in owned:
    data=git('show',CODE+':'+path);mode,kind,blob=git('ls-tree',CODE,'--',path).split(b'\t')[0].decode().split()
    assert (ROOT/path).read_bytes()==data and kind=='blob' and mode in ('100644','100755')
    refs.append(dict(path=path,revision=CODE,sha256=sha(data),git_mode=mode,git_blob=blob))
assert sorted(git('diff','--name-only',RELEASE,CODE).decode().splitlines())==sorted(owned)
contract_bytes=(ROOT/'.agent/contracts/123.json').read_bytes();contract=json.loads(contract_bytes)
assert sha(contract_bytes)=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
assert contract_bytes==git('show','452a5a5f748b5234ce1da3ad765b0da8f622cb53:.agent/contracts/123.json')
for path in ('schema/contract.schema.json','.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(json.loads((ROOT/path).read_bytes())).validate(contract)
state=json.loads((ROOT/'.agent/run_state.json').read_bytes())
for key in ('123-author','123-author-static','123-provisional-review'):
    assert state['circuit_breaker'][key]['attempts']==state['circuit_breaker'][key]['limit']==3
for path in current_paths[3:]:assert (ROOT/path).read_bytes()==git('show',RELEASE+':'+path)
source=(ROOT/'tools/workflow_assurance.py').read_bytes();text=(ROOT/'tools/test_workflow_assurance.py').read_text();test_bytes=text.encode()
assert source==git('show',PRESERVED+':tools/workflow_assurance.py')
assert sha(test_bytes)=='9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'
old=ast.parse(git('show',PRESERVED+':tools/test_workflow_assurance.py'));new=ast.parse(text)
old_defs,new_defs=definitions(old),definitions(new)
assert len(old_defs)==74 and all(new_defs[k]==v for k,v in old_defs.items() if k!='main')
main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
assert dump(InheritedMain().visit(copy.deepcopy(main)))==old_defs['main']
old_inv,new_inv=inventories(old),inventories(new)
assert all(new_inv[k]==v for k,v in old_inv.items())
labels=sum((old_inv[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')),())
assert len(labels)==len(set(labels))==46 and new_inv['CONTROL_CASES']==('ci-candidate-bound','ci-blocker-rejected')
fixture=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='ControlsFixture')
methods={n.name:n for n in fixture.body if isinstance(n,ast.FunctionDef)}
init=methods['__init__'];init_text=ast.get_source_segment(text,init)
assess=[n for n in ast.walk(init) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='assess_repository']
sparse=[n for n in ast.walk(init) if isinstance(n,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='sparse-checkout' for a in n.args)]
assert len(assess)==1 and sparse and all(assess[0].lineno<n.lineno for n in sparse)
assert 'assessed_revision=actual[field]' in init_text
stage=ast.get_source_segment(text,methods['stage_checkout']);host=ast.get_source_segment(text,methods['host']);bindings=ast.get_source_segment(text,methods['assert_bindings'])
assert "path='.agent/evidence/123/selection.json'" in stage and 'self.raw(selection)' in stage
assert "revision=self.commit(" in stage and 'sha=revision' in stage and "revision+'^{tree}'" in stage
assert "self.stage_checkout('capture',self.capture_selection)" in init_text and "self.stage_checkout('verify',self.verify_selection)" in init_text
assert 'checkout=self.checkouts[mode]' in host and 'checkout=checkout' in host
assert "head_sha=checkout['event_head']" in host and "checkout_sha=checkout['sha']" in host
assert 'actual==self.raw(selected)' in bindings and "checkout['sha']+':'+path" in bindings
assert "self.checkouts['verify']['sha']" in init_text and 'cwd=self.root' in init_text
assert methods['capture'].args.args[-1].arg=='cwd'
assert "capture['argv']==outer['argv']" in bindings and "capture['cwd']==outer['cwd']==str(self.root)" in bindings
assert "capture['revision']==outer['checkout']['sha']==self.checkouts['verify']['sha']" in bindings
interface=json.loads((ROOT/'.agent/evidence/123/author3-api-interface.json').read_bytes())
assert interface['approved_contract']['sha256']==sha(contract_bytes) and interface['selectors']==list(new_inv['CONTROL_CASES']) and interface['default_count']==48
for path in owned:
    if path.endswith('.py'):compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
full_modes=[]
for row in installed:
    header,path=row.split(b'\t');mode,kind,blob=header.decode().split();target=ROOT/path.decode()
    assert mode in ('100644','100755') and kind=='blob' and target.is_file() and not target.is_symlink()
    assert target.stat().st_nlink==1 and target.read_bytes()==git('cat-file','blob',blob)
    assert bool(target.stat().st_mode&0o111)==(mode=='100755')
    full_modes.append((path.decode(),stat.S_IMODE(target.stat().st_mode)))
assert len(installed)==239 and snapshot()==before
print(json.dumps({'role':'independent reviewer3 static preparation','static_only':True,'actual_exit':0,'exercised_revision':revision,'code_checkpoint':CODE,'released_base':RELEASE,
    'owned_code_refs':refs,'approved_contract_sha256':sha(contract_bytes),'source_sha256':sha(source),'test_sha256':sha(test_bytes),
    'inherited_source_definitions':len(definitions(ast.parse(source))),'inherited_test_definitions':len(old_defs),'inherited_cases':46,'default_cases':48,'additive_main':True,
    'structural_fixture_class_scope':fixture.name,'actual_assess_line':assess[0].lineno,'later_sparse_lines':[n.lineno for n in sparse],
    'payload_catalog_groups':len(contract['protocol']['payload_catalog']),'stage_frame_static_bindings_present':True,'nested_a10_outer_frame_static_binding_present':True,'installed_regular_files':239,
    'installed_full_modes_sha256':sha(json.dumps(full_modes,separators=(',',':')).encode()),'same_run_preserved_inputs':len(before),'current_coordination_unchanged':True,
    'behavior_executed':False,'formal_approval':False,'limitation':'AST/Ref/byte/mode inspection only; no constructor/API/observer acceptance or hosted execution proof.'},sort_keys=True))
