"""Actual bounded Generator development captures for Source120."""
import ast,hashlib,json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[3];os.chdir(root);os.environ['PYTHONDONTWRITEBYTECODE']='1'
git=lambda *a:subprocess.check_output(['git',*a],text=True).strip()
paths=('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/120.json')
inputs={p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p)) for p in paths}
base='e79e80bb4125df841a4ae4704c0ad6ebb012e278'
functions=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
old=functions(subprocess.check_output(['git','show',base+':tools/workflow_assurance.py'],text=True));new=functions(pathlib.Path(paths[0]).read_text())
assert all(new.get(k)==v for k,v in old.items())
assert git('diff',base,'HEAD','--','tools/test_workflow_assurance.py','schema','.nizam')==''
pathlib.Path('.agent/evidence/120/source1-preservation.txt').write_text('PASS all '+str(len(old))+' existing top-level function/class ASTs unchanged; tests/schemas/installed unchanged\nBASE: '+base+'\nREVISION: '+git('rev-parse','HEAD')+'\nEXIT: 0\n')
cases=('reject-missing-operator','reject-wrong-candidate','reject-unrun','reject-setup','reject-pending','reject-running','reject-failed','reject-invalidated','idempotent-replay','reject-double-advance','recover-missing-receipt')
commands=[(n,['python3','tools/test_workflow_assurance.py','--case',n]) for n in cases]+[('default37',['python3','tools/test_workflow_assurance.py'])]
records=[]
for label,argv in commands:
    result=subprocess.run(argv,capture_output=True);prefix='.agent/evidence/120/source1-'+label
    pathlib.Path(prefix+'.stdout.txt').write_bytes(result.stdout);pathlib.Path(prefix+'.stderr.txt').write_bytes(result.stderr)
    records.append(dict(label=label,argv=argv,cwd=str(root),revision=git('rev-parse','HEAD'),environment={'PYTHONDONTWRITEBYTECODE':'1'},exit=result.returncode,inputs=inputs,stdout=prefix+'.stdout.txt',stderr=prefix+'.stderr.txt'))
    pathlib.Path('.agent/evidence/120/source1-results.json').write_text(json.dumps(records,indent=2)+'\n')
    print(label,'actual_exit',result.returncode,flush=True)
    if result.returncode:
        print(result.stderr.decode(),flush=True);raise SystemExit(result.returncode)
assert inputs=={p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p)) for p in paths}
print('PASS eleven exact cases/default37 and preserved immutable inputs')
