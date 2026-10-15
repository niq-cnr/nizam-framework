"""Independent static review only; never import or execute product/tests."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[3]
RELEASE = '103689535a5b21bdc950a0090ec8397c0ef469d1'
BASE = 'f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args): return subprocess.check_output(['git', '-C', str(ROOT), *args])
def digest(data): return hashlib.sha256(data).hexdigest()
def syntax(data): return ast.parse(data)
def definitions(tree): return {n.name:ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def inventory(tree):
    names = {}
    def value(n):
        if isinstance(n,ast.Name): return names[n.id]
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add): return value(n.left)+value(n.right)
        return ast.literal_eval(n)
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.endswith('CASES'):
            names[n.targets[0].id]=value(n.value)
    return names
def snapshot():
    paths = [r.split(b'\t')[1].decode() for r in git('ls-tree','-rz',RELEASE,'--','.nizam').split(b'\0') if r]
    paths += ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/123.json','.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml']
    return {p:(stat.S_IMODE((ROOT/p).lstat().st_mode),(ROOT/p).lstat().st_nlink,digest((ROOT/p).read_bytes())) for p in paths}

assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
assert git('rev-parse','HEAD').decode().strip()==RELEASE
before=snapshot()
freeze=json.loads((ROOT/'.agent/evidence/123/author1-concrete-freeze.json').read_bytes())
for row in freeze['owned_refs']+[freeze['approved_contract'],freeze['source_ref']]:
    raw=git('show',row['revision']+':'+row['path'])
    header=git('ls-tree',row['revision'],'--',row['path']).split(b'\t')[0].decode().split()
    assert digest(raw)==row['sha256'] and header==[row['git_mode'],'blob',row['git_blob']]
    assert (ROOT/row['path']).read_bytes()==raw
contract=json.loads((ROOT/'.agent/contracts/123.json').read_bytes())
assert digest((ROOT/'.agent/contracts/123.json').read_bytes())=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
source=(ROOT/'tools/workflow_assurance.py').read_bytes();tests=(ROOT/'tools/test_workflow_assurance.py').read_bytes()
assert source==git('show',BASE+':tools/workflow_assurance.py')
old=syntax(git('show',BASE+':tools/test_workflow_assurance.py'));new=syntax(tests)
old_defs,new_defs=definitions(old),definitions(new)
assert all(new_defs[k]==v for k,v in old_defs.items() if k!='main')
old_inv,new_inv=inventory(old),inventory(new)
assert all(new_inv[k]==v for k,v in old_inv.items())
old_cases=sum((old_inv[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')),())
assert len(old_cases)==46 and new_inv['CONTROL_CASES']==('ci-candidate-bound','ci-blocker-rejected')
for path in ('tools/test_workflow_assurance.py','.agent/evidence/123/author1-controls.py'):
    compile((ROOT/path).read_bytes(),str(ROOT/path),'exec')
ae=contract['approval_evidence'];gate_bindings={}
for kind,key,field in (('mode-a','mode_a','reviewed_commit'),('contract-review','contract_review','reviewed_revision')):
    value=json.loads((ROOT/ae[key]).read_bytes())
    gate_bindings[kind]={'actual_gate_assessed_revision':value[field],'fixture_assessed_revision':ae['proposal_revision'],'mismatch':value[field]!=ae['proposal_revision']}
    assert value[field]!=ae['proposal_revision']
assert "assessed_revision=ae['proposal_revision']" in tests.decode()
assert "'sparse-checkout', 'set'" in tests.decode()
assert "for path, (mode, oid) in baseline.items():" in source.decode() and 'target = regular_file(root, path)' in source.decode()
assert len([p for p in before if p.startswith('.nizam/')])==239
assert snapshot()==before
print(json.dumps({'static_only':True,'actual_static_exit':0,'exercised_revision':RELEASE,'verified_owned_refs':len(freeze['owned_refs']),
    'inherited_cases':46,'default_cases':48,'inherited_test_definitions':len(old_defs),'payload_groups':len(contract['protocol']['payload_catalog']),
    'installed_regular_files':239,'preserved_current_inputs':len(before),'source_sha256':digest(source),'test_sha256':digest(tests),
    'gate_binding_static_counterexample':gate_bindings,'constructor_executed':False,'behavior_executed':False,
    'scope':'Static success proves inspection/preservation only; provisional acceptance is rejected by separately recorded findings.'},sort_keys=True))
