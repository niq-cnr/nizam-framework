"""Generator actual default42 and preservation capture; no private control execution."""
import ast,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];os.chdir(ROOT)
E=pathlib.Path('.agent/evidence/121');BASE='274043a0f779aea9c5905969f4d08cea5ffcac39';OLD='f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
git=lambda *a:subprocess.check_output(['git',*a],text=True).strip()
revision=git('rev-parse','HEAD');subprocess.run(['git','merge-base','--is-ancestor',BASE,revision],check=True)
paths=sorted(set(['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/121.json']+git('ls-files','schema','.nizam').splitlines()))
def identity():return {p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p),executable=bool(pathlib.Path(p).stat().st_mode&0o111)) for p in paths}
before=identity();(E/'source1-identity-before.json').write_text(json.dumps(before,indent=2)+'\n')
assert before['tools/test_workflow_assurance.py']['sha256']=='c7273078ababd7aef1f9f72601fa93d8b5698baf608e7a86128b2502f3d456bc'
assert before['.agent/contracts/121.json']['sha256']=='145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e'
functions=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
preservation={}
for path,base,exempt in [('tools/workflow_assurance.py',BASE,set()),('tools/test_workflow_assurance.py',OLD,{'main'})]:
    original=functions(subprocess.check_output(['git','show',base+':'+path],text=True));actual=functions(pathlib.Path(path).read_text())
    inherited=sorted(set(original)-exempt);assert all(actual.get(k)==original[k] for k in inherited)
    preservation[path]=dict(base=base,unchanged_symbols=inherited,approved_dispatch_exemption=sorted(exempt))
assert len(git('ls-files','.nizam').splitlines())==239
assert git('diff',BASE,'HEAD','--','schema','.nizam','tools/test_workflow_assurance.py','.agent/contracts/121.json')==''
module=ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text());inventories={}
for node in module.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in ('AGF_CASES','RECEIPT_CASES','LANE_CASES'):inventories[target.id]=ast.literal_eval(node.value)
expected=[r['case'] for r in json.loads(pathlib.Path('.agent/evidence/118/api-interface.json').read_text())['current_cases']]+list(inventories['AGF_CASES'])+list(inventories['RECEIPT_CASES'])+list(inventories['LANE_CASES'])
assert len(expected)==42 and len(set(expected))==42
(E/'source1-preservation.json').write_text(json.dumps(dict(base=BASE,revision=revision,inherited=preservation,installed_count=239,expected_order=expected),indent=2)+'\n')
argv=['python3','tools/test_workflow_assurance.py'];env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
r=subprocess.run(argv,capture_output=True,env=env)
(E/'source1-default42.stdout.txt').write_bytes(r.stdout);(E/'source1-default42.stderr.txt').write_bytes(r.stderr)
after=identity();(E/'source1-identity-after.json').write_text(json.dumps(after,indent=2)+'\n');markers=[x[5:] for x in r.stdout.decode().splitlines() if x.startswith('PASS ')]
record=dict(argv=argv,cwd=str(ROOT),environment={'PYTHONDONTWRITEBYTECODE':'1'},revision=revision,input_ancestor=BASE,exit=r.returncode,stdout=str(E/'source1-default42.stdout.txt'),stderr=str(E/'source1-default42.stderr.txt'),stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest(),ordered_markers=markers,ordered42_match=markers==expected,protected_unchanged=before==after)
(E/'source1-result.json').write_text(json.dumps(record,indent=2)+'\n')
print('default42 actual_exit',r.returncode,'ordered42_match',markers==expected,'protected_unchanged',before==after,flush=True)
if r.returncode:
    print(r.stderr.decode(),flush=True);raise SystemExit(r.returncode)
assert markers==expected and before==after
print('PASS exact default42 and inherited API/test/schema/installed/contract preservation')
