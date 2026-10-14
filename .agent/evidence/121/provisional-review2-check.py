"""Independent review of frozen fixture repairs, without executing missing lane APIs."""
import ast, copy, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
INPUT='faee538eee21421791eb49b1e9f03e132dfd8809'; AUTHOR='9b95f8c0601ec59e0023ef3c9b44e15126402c82'
PREFIX='.agent/evidence/121/provisional-review2-'
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def sha(raw): return hashlib.sha256(raw).hexdigest()
assert os.environ['PYTHONDONTWRITEBYTECODE']=='1'
subprocess.run(['git','merge-base','--is-ancestor',INPUT,'HEAD'],check=True)
seal=json.loads(pathlib.Path('.agent/evidence/121/author2-provisional-seal.json').read_text()); assert len(seal['files'])==24
for path,pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes())==pin['sha256']
    assert git('hash-object',path)==pin['git_blob']==git('rev-parse',AUTHOR+':'+path)
old_seal=json.loads(pathlib.Path('.agent/evidence/121/author1-provisional-seal.json').read_text())
for path,pin in old_seal['files'].items():
    if path!='tools/test_workflow_assurance.py': assert sha(pathlib.Path(path).read_bytes())==pin['sha256']
spec=importlib.util.spec_from_file_location('reviewed_tests',ROOT/'tools/test_workflow_assurance.py')
t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api=t.load_api()
assert all(not hasattr(api,k) for k in ('assess_conflict_lanes','verify_isolated_attempt','rollback_owned_attempt'))
old=ast.parse(subprocess.check_output(['git','show','478844edfb9fb1de96d1c372e1e794c875941e78:tools/test_workflow_assurance.py'],text=True))
new={n.name:ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert all(new[n.name]==ast.dump(n) for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='main')
with tempfile.TemporaryDirectory(prefix='nizam121-review2-') as parent:
    f=t.LaneFixture(parent)
    try:
        original=copy.deepcopy(f.request); probes=[]; malformed=[]
        for key,value in (('writes',['../escape']),('state_fields',['/bad~escape'])):
            f.request=copy.deepcopy(original); f.authorize(**{key:value})
            dispatch=json.loads((f.root/'proof/dispatch.json').read_text())
            assert all(dispatch[k]==v for k,v in f.request.items())
            malformed.append(dict(field=key,request_value=f.request[key],authority_value=dispatch[key]))
        f.request=copy.deepcopy(original); f.authorize()
        for kind in ('staged','committed','rename','mode','symlink','unmerged','submodule'):
            root,writes=f.inventory_probe(kind); f.authorize(attempt_root=str(root),writes=writes)
            dispatch=json.loads((f.root/'proof/dispatch.json').read_text()); assert all(dispatch[k]==v for k,v in f.request.items())
            if kind=='staged': assert t.git(root,'diff','--cached','--name-only')=='src/b.py'
            if kind=='committed': assert t.git(root,'diff','--name-only',f.base,'HEAD')=='src/b.py'
            if kind=='rename': assert t.git(root,'diff','--cached','--name-status').split()==['R100','src/a.py','src/cross-owner.py']
            if kind=='mode': assert 'mode change 100644 => 100755 src/b.py' in t.git(root,'diff','--summary')
            if kind=='symlink': assert (root/'src/a.py').is_symlink() and writes==['src/a.py']
            if kind=='unmerged':
                assert {r.split()[2] for r in t.git(root,'ls-files','--unmerged').splitlines()}=={'1','2','3'}
                for stream in ('stdout','stderr'): pathlib.Path(PREFIX+'conflict.'+stream+'.txt').write_bytes((f.root/('proof/unmerged-setup.'+stream)).read_bytes())
            if kind=='submodule': assert '160000 '+f.base+' 0\towned-gitlink' in t.git(root,'ls-files','--stage')
            probes.append(dict(kind=kind,root=str(root),writes=writes,actual_status=t.git(root,'status','--porcelain=v1')))
        f.request=copy.deepcopy(original); f.authorize()
        for name,value in (('contract',json.loads((f.root/'contract.json').read_text())),('contract_review',json.loads((f.root/'proof/contract-review.json').read_text())),('run_state',f.state),('feature_list',f.features)):
            jsonschema.validate(value,json.loads(pathlib.Path('schema/'+name+'.schema.json').read_text()))
        alias=f.attempt_parent/'reviewer-alias'; alias.symlink_to(f.attempt,target_is_directory=True)
        f.authorize(attempt_root=str(alias)); failure_ref=f.proof(f.request,True); record=json.loads((f.root/failure_ref['path']).read_text())
        dispatch=json.loads((f.root/'proof/dispatch.json').read_text())
        bindings=('operation_id','feature_id','owner','attempt','base_revision','attempt_root')
        assert all(record[k]==f.request[k]==dispatch[k] for k in bindings) and record['actual_exit']==7
        fixture=dict(matched_malformed_dispatches=malformed,actual_inventory_probes=probes,matching_unsafe_failure=record,actual_process_captures=f.proof_captures,expected_merge_setup=f.git_probe_log[-2] if f.git_probe_log[-2].get('actual_exit')==1 else next(x for x in f.git_probe_log if x.get('actual_exit')==1),schema_checks=4,no_newAPI_execution=True)
    finally: f.close()
records=json.loads(pathlib.Path('.agent/evidence/121/author2-captures.json').read_text()); assert len(records)==5
for row,name in zip(records,t.LANE_CASES):
    assert row['argv'][-1]==name and row['actual_exit']==2 and pathlib.Path(row['stdout']).read_bytes()==b''
    assert pathlib.Path(row['stderr']).read_bytes()==b'SETUP_ERROR: missing lane APIs\n'
path=pathlib.Path(PREFIX+'proof.json'); assert not path.exists()
path.write_text(json.dumps(dict(reviewed_revision=INPUT,actual_executed_revision=git('rev-parse','HEAD'),author_file_pins=seal['files'],prior_author_files_preserved=True,inherited_ASTs_preserved=True,fixture=fixture,old37_rerun=False,newAPI_execution=False),indent=2)+'\n')
print('PASS pins24; old proof/ASTs; matching malformed authority; seven real Git inventory defects; matching failure7; schemas4; five setup2 only')
