"""Independent provisional fixture proof; no absent lane API behavior is simulated."""
import ast, copy, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
INPUT='272dffdeb68ee377bef7cdb980b01adbddeea6c9'
AUTHOR='f7a2715e44e2ca8d671dc416a8e4d6d935e2b21f'
BASE='478844edfb9fb1de96d1c372e1e794c875941e78'
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def sha(raw): return hashlib.sha256(raw).hexdigest()
assert os.environ['PYTHONDONTWRITEBYTECODE']=='1'
subprocess.run(['git','merge-base','--is-ancestor',INPUT,'HEAD'],check=True)
seal=json.loads(pathlib.Path('.agent/evidence/121/author1-provisional-seal.json').read_text())
assert len(seal['files'])==94
for path,pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes())==pin['sha256']
    assert git('hash-object',path)==pin['git_blob']==git('rev-parse',AUTHOR+':'+path)
spec=importlib.util.spec_from_file_location('reviewed_acceptance',ROOT/'tools/test_workflow_assurance.py')
t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api=t.load_api()
assert all(not hasattr(api,k) for k in ('assess_conflict_lanes','verify_isolated_attempt','rollback_owned_attempt'))
old=ast.parse(subprocess.check_output(['git','show',BASE+':tools/test_workflow_assurance.py'],text=True))
new={n.name:ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert all(new[n.name]==ast.dump(n) for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main')
assert len(t.CASES+t.AGF_CASES+t.RECEIPT_CASES)==37 and len(t.LANE_CASES)==5
captures=json.loads(pathlib.Path('.agent/evidence/121/author1-captures.json').read_text())
assert len(captures)==42
for row in captures:
    name=row['argv'][-1]
    assert row['actual_exit']==(2 if name in t.LANE_CASES else 0)
    assert pathlib.Path(row['stdout']).read_bytes()==(b'' if name in t.LANE_CASES else ('PASS '+name+'\n').encode())
    assert pathlib.Path(row['stderr']).read_bytes()==(b'SETUP_ERROR: missing lane APIs\n' if name in t.LANE_CASES else b'')
    for path,pin in row['inputs'].items(): assert pin==seal['files'][path]
with tempfile.TemporaryDirectory(prefix='nizam121-review1-') as parent:
    f=t.LaneFixture(parent)
    try:
        registration=t.git(f.root,'worktree','list','--porcelain')
        assert t.git(f.attempt,'rev-parse','HEAD')==f.base
        assert any(('worktree '+str(f.attempt)+'\n') in r and '\ndetached' in r for r in registration.split('\n\n'))
        assert t.git(f.attempt,'rev-parse','--git-common-dir')==str(f.root/'.git')
        for name,value in (('contract',json.loads((f.root/'contract.json').read_text())),('contract_review',json.loads((f.root/'proof/contract-review.json').read_text())),('run_state',f.state),('feature_list',f.features)):
            jsonschema.validate(value,json.loads(pathlib.Path('schema/'+name+'.schema.json').read_text()))
        assert f.pin('coordination.json',f.state)==f.ref('coordination.json')
        authority=json.loads((f.root/'proof/dispatch.json').read_text()); unsafe=copy.deepcopy(f.request); unsafe['writes']=['../escape']
        assert unsafe['writes']!=authority['writes']
        failure=f.proof(f.request,True); release=f.proof(f.lane())
        failure_record=json.loads((f.root/failure['path']).read_text())
        alias=f.attempt_parent/'review-alias'; alias.symlink_to(f.attempt,target_is_directory=True)
        f.authorize(attempt_root=str(alias))
        assert failure_record['attempt_root']!=f.request['attempt_root']
        alias.unlink()
        fixture=dict(root=str(f.root),base_revision=f.base,registration=registration,schema_checks=4,actual_process_captures=f.proof_captures,unsafe_writes_probe_request=unsafe['writes'],pinned_authority_writes=authority['writes'],rollback_root_probe_request=f.request['attempt_root'],retained_failure_proof_root=failure_record['attempt_root'],note='Actual fixture construction and conflicting bindings only. No121API pass, intended red or rollback is claimed.')
    finally: f.close()
path=pathlib.Path('.agent/evidence/121/provisional-review1-proof.json'); assert not path.exists()
path.write_text(json.dumps(dict(reviewed_revision=INPUT,actual_executed_revision=git('rev-parse','HEAD'),author_pins=seal['files'],fixture=fixture,authored_old37_pass_and_new5_setup_captures_checked=42,inherited_ASTs_preserved=True,runtime_bank_rerun=False,new_api_execution=False),indent=2)+'\n')
print('PASS pins94; inherited ASTs; author captures42; actual detached fixture/schemas4/exits7,0; mismatched authority and rollback-proof bindings observed; no newAPI execution')
