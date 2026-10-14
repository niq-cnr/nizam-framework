import ast,hashlib,importlib.util,json,os,pathlib,subprocess,tempfile
ROOT=pathlib.Path.cwd(); E=ROOT/'.agent/evidence/119'; ENV={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.check_output(['git',*a]).decode().strip()
def pin(p):
    b=pathlib.Path(p).read_bytes(); return {'sha256':sha(b),'git_blob':subprocess.check_output(['git','hash-object','--stdin'],input=b).decode().strip()}
spec=importlib.util.spec_from_file_location('t',ROOT/'tools/test_workflow_assurance.py'); t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
assert json.loads((ROOT/'.agent/run_state.json').read_text())['circuit_breaker']['119-executable-bundle']['attempts']==1
source=(ROOT/'tools/workflow_assurance.py').read_text(); records=[]
inputs={p:pin(ROOT/p) for p in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/119.json')}
def capture(label,argv,expected,marker,cwd=ROOT,mutant=None):
    r=subprocess.run(argv,cwd=cwd,env=ENV,capture_output=True,timeout=90)
    stem='executable-review1-'+label
    for k,b in (('stdout',r.stdout),('stderr',r.stderr)): (E/(stem+'.'+k+'.txt')).write_bytes(b)
    row={'label':label,'argv':argv,'cwd':str(cwd),'revision':git('rev-parse','HEAD'),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'exit':r.returncode,'inputs':inputs,'expected_exit':expected,'expected_marker':marker,'stdout':str((E/(stem+'.stdout.txt')).relative_to(ROOT)),'stderr':str((E/(stem+'.stderr.txt')).relative_to(ROOT)),'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr)}
    if mutant: row['private_mutant']={'sha256':sha(mutant[0].encode()),'git_blob':subprocess.check_output(['git','hash-object','--stdin'],input=mutant[0].encode()).decode().strip(),'append_only_delta':mutant[1]}
    records.append(row); (E/'executable-review1-captures.json').write_text(json.dumps(records,indent=2)+'\n')
    assert r.returncode==expected,(label,r.returncode,r.stderr.decode())
    assert marker.encode() in (r.stdout if expected==0 else r.stderr),(label,r.stdout,r.stderr)
    if expected: assert b'PASS ' not in r.stdout
for index,name in enumerate(t.AGF_CASES):
    argv=['python3','tools/test_workflow_assurance.py','--case',name]
    capture(name+'-positive',argv,0,'PASS '+name)
    body="out['final_verdict']['approved'] = False" if index==0 else "out['advisory_minor'] = []" if index==1 else "out['issues'] = out['issues'][1:]" if index==2 else "out['final_verdict']['approved'] = True"
    delta="\n_review_original = convergent_agf_verdict\ndef convergent_agf_verdict(*args, **kwargs):\n    out = _review_original(*args, **kwargs)\n    "+body+"\n    return out\n"
    mutant=source+delta
    with tempfile.TemporaryDirectory(prefix='nizam119-review-mutant-') as directory:
        p=pathlib.Path(directory)/'workflow_assurance.py'; p.write_text(mutant)
        code="import sys; sys.path.insert(0,'tools'); import test_workflow_assurance as t; t.run_agf_case(%r,t.load_api(%r)); print('PASS '+%r)"%(name,str(p),name)
        message=('empty valid AGF approves exactly','active minor visible separately','active full findings appended in ledger order')[index] if index<3 else 'nonempty blocking array preserved: '+t.AGF_ARRAYS[index-3]
        capture(name+'-semantic-red',['python3','-c',code],1,'POLICY_ASSERTION: '+message,mutant=(mutant,delta))
    capture(name+'-restored',argv,0,'PASS '+name)
capture('default26',['python3','tools/test_workflow_assurance.py'],0,'PASS reject-unsupported')
r=records[-1]; lines=(ROOT/r['stdout']).read_text().splitlines(); assert lines==['PASS '+n for n in t.CASES+t.AGF_CASES]
capture('live-stale-foundation',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1,'pinned entry bytes/mode changed: tools/workflow_assurance.py')
old=subprocess.check_output(['git','show','e55f0400dfc8d6f93fca3e2b93e744c04ce6cae4:tools/workflow_assurance.py'])
def defs(b): return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=defs(old); b=defs(source); assert all(b[k]==v for k,v in a.items())
assert {p:pin(ROOT/p) for p in inputs}==inputs
print('PASS independent six positives, six intended semantic reds, six restored controls; ordered current20+six default; unchanged old source ASTs; live stale118 receipt rejection')
