"""Bounded evidence-only development batch after independently reviewed fixture repair."""
import ast,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];os.chdir(ROOT)
BASE='69e8346f7b0a6b05da48d2f064479fbae96c2226';HISTORICAL='92fecd8d376964f5e3dd7e34bc201035acfe8bc6'
E=pathlib.Path('.agent/evidence/120');git=lambda *args:subprocess.check_output(['git',*args],text=True).strip()
revision=git('rev-parse','HEAD');subprocess.run(['git','merge-base','--is-ancestor',BASE,revision],check=True)
paths=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/120.json']
paths+=git('ls-files','schema','.nizam').splitlines();paths=sorted(set(paths))
def identity():
    return {p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p),executable=bool(pathlib.Path(p).stat().st_mode&0o111)) for p in paths}
before=identity();(E/'dev2-identity-before.json').write_text(json.dumps(before,indent=2)+'\n')
assert before['tools/workflow_assurance.py']['sha256']=='733c1478a8eb237339efe914d29d2be2c93d01172ed399e3baea340d6ec3982a'
assert before['tools/test_workflow_assurance.py']['sha256']=='9c99ff133aacaad158f840e78158792b2b096450560f47dc4b218b8e4ff223f7'
assert before['.agent/contracts/120.json']['sha256']=='3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
functions=lambda text:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
preservation={}
for p in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py'):
    original=functions(subprocess.check_output(['git','show',HISTORICAL+':'+p],text=True));actual=functions(pathlib.Path(p).read_text())
    exempt={'main'} if p.endswith('test_workflow_assurance.py') else set()
    assert all(actual.get(k)==v for k,v in original.items() if k not in exempt)
    preservation[p]={'unchanged_inherited_definitions':len(set(original)-exempt),'approved_dispatch_exemption':sorted(exempt)}
installed=git('ls-files','.nizam').splitlines();assert len(installed)==239
for p in git('ls-files','schema','.nizam').splitlines():
    assert pathlib.Path(p).read_bytes()==subprocess.check_output(['git','show',HISTORICAL+':'+p])
# Literal inventories are observed through the reviewed AST without importing or executing fixture setup.
module=ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text());inventories={}
for node in module.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in ('CASES','BASE_CASES','PRE_ENTRY_CASES','BUNDLE_CASES','ENTRY_CASES','AGF_CASES','RECEIPT_CASES'):
                try:inventories[target.id]=ast.literal_eval(node.value)
                except (ValueError,TypeError):pass
# The historical twenty selectors are bound to their published immutable API inventory.
old20=[r['case'] for r in json.loads(pathlib.Path('.agent/evidence/118/api-interface.json').read_text())['current_cases']]
expected=old20+list(inventories['AGF_CASES'])+list(inventories['RECEIPT_CASES']);assert len(expected)==37 and len(set(expected))==37
(E/'dev2-preservation.json').write_text(json.dumps({'base':BASE,'revision':revision,'historical':HISTORICAL,'inherited':preservation,'installed_count':239,'schemas_installed_equal_historical':True,'expected_order':expected},indent=2)+'\n')
argv=['python3','tools/test_workflow_assurance.py'];env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
result=subprocess.run(argv,capture_output=True,env=env)
(E/'dev2-default37.stdout.txt').write_bytes(result.stdout);(E/'dev2-default37.stderr.txt').write_bytes(result.stderr)
markers=[line[5:] for line in result.stdout.decode().splitlines() if line.startswith('PASS ')]
after=identity();(E/'dev2-identity-after.json').write_text(json.dumps(after,indent=2)+'\n')
record={'argv':argv,'cwd':str(ROOT),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'revision':revision,'input_ancestor':BASE,'exit':result.returncode,'stdout':str(E/'dev2-default37.stdout.txt'),'stderr':str(E/'dev2-default37.stderr.txt'),'ordered_markers':markers,'ordered37_match':markers==expected,'protected_unchanged':before==after}
(E/'dev2-result.json').write_text(json.dumps(record,indent=2)+'\n')
print('default37 actual_exit',result.returncode,'ordered37_match',markers==expected,'protected_unchanged',before==after,flush=True)
if result.returncode:raise SystemExit(result.returncode)
assert markers==expected and before==after
print('PASS default37 exact order and preserved source/tests/contract/schemas/installed')
