import ast, hashlib, importlib.util, json, os, pathlib, subprocess
ROOT=pathlib.Path.cwd(); BASE='e55f0400dfc8d6f93fca3e2b93e744c04ce6cae4'; CANDIDATE='833b97b2116d630c4af937e23b7ad89eb442ee77'
def git(*args): return subprocess.check_output(['git',*args])
def sha(b): return hashlib.sha256(b).hexdigest()
def dump_ast(b): return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert git('rev-parse','HEAD').decode().strip()=='6c46691e17f1e27fb2bb2fc69882b5f60503a56a'
s=json.loads((ROOT/'.agent/run_state.json').read_text()); assert s['circuit_breaker']['119-provisional-bundle']['attempts']==1
contract=ROOT/'.agent/contracts/119.json'; assert sha(contract.read_bytes())=='0ff9b2860ac6a24b4bf40cf42cbde0a0cc62a24a27a0fe7f77d57ed5c34945e6'
for path in ('.agent/validator/119-mode-a-rev1.json','.agent/qa/119-contract-review-rev1.json'):
    v=json.loads((ROOT/path).read_text()); assert v['final_verdict']['approved'] is True
    assert all(v[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
p='tools/test_workflow_assurance.py'; old=dump_ast(git('show',BASE+':'+p)); new=dump_ast((ROOT/p).read_bytes())
assert all(new[k]==v for k,v in old.items() if k!='main')
assert sha((ROOT/p).read_bytes())=='6e7c4e9df367bbe1173997525c3d7ad6dbfa29912574173f18403876e14cb480'
for path,pin in json.loads((ROOT/'.agent/evidence/119/author1-provisional-seal.json').read_text())['files'].items():
    data=git('show',CANDIDATE+':'+path); assert sha(data)==pin['sha256']; assert git('rev-parse',CANDIDATE+':'+path).decode().strip()==pin['git_blob']
    if path!='.agent/contracts/119.json': assert (ROOT/path).read_bytes()==data
records=json.loads((ROOT/'.agent/evidence/119/author1-captures.json').read_text())
assert len(records)==28 and sum(r['label'].startswith('old-') and r['exit']==0 for r in records)==20
for row in records:
    for key in ('stdout','stderr'): assert sha((ROOT/row[key]).read_bytes())==row[key+'_sha256']
spec=importlib.util.spec_from_file_location('test',ROOT/p); t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
assert len(t.CASES)==20 and t.AGF_CASES==('approve-empty','advisory-visible','block-carried','reject-issues','reject-missing-coverage','reject-unsupported')
for case in ('01-no-findings','02-consensus-blocker','05-prior-persisting','08-reopened-finding','06-prior-resolution-two-of-three','11-authorized-suppression-retained'):
    for severity in ('minor','important','blocker'): t.agf_severity(t.agf_ledger(case),severity)
print('PASS strict approved clarification; all historical author pins; old function ASTs; twenty+six inventory; author28 capture hashes; eighteen authentic ledger variants')
results=[]
for name in t.AGF_CASES:
    argv=['python3',p,'--case',name]; r=subprocess.run(argv,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert r.returncode==2 and r.stdout==b'' and b'SETUP_ERROR: missing convergent_agf_verdict API' in r.stderr
    results.append({'argv':argv,'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),'classification':'setup only, never semantic red'})
argv=['python3',p,'--check','foundation-ready']; r=subprocess.run(argv,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
assert r.returncode==1 and r.stdout==b'' and b'pinned entry bytes/mode changed: tools/test_workflow_assurance.py' in r.stderr
results.append({'argv':argv,'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),'classification':'expected stale historical proof rejection on changed live runner'})
(ROOT/'.agent/evidence/119/provisional-review1-results.json').write_text(json.dumps({'revision':git('rev-parse','HEAD').decode().strip(),'cwd':str(ROOT),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'checks':results},indent=2)+'\n')
print('PASS six actual setup2; live historical foundation receipt correctly rejected1; no product behavior or executable-control approval claimed')
