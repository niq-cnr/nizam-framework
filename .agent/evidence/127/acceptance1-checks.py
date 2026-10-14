"""Independent pre-source author checks; unsupported126 baseline is not semantic red."""
import ast,hashlib,json,os,pathlib,runpy,subprocess,sys,tempfile
ROOT=pathlib.Path.cwd();OUT=ROOT/'.agent/evidence/127';BASE='1debbe16659b589d161376e899e4c0cd9b84cf63';REV='81a421dc74e163c679ae036e0ddfbdb51cfcbb6e';TEST=ROOT/'tools/test_runtime_session.py'
source=TEST.read_text();compile(source,str(TEST),'exec');tree=ast.parse(source);oldtree=ast.parse(subprocess.check_output(['git','show',BASE+':tools/test_runtime_session.py']))
newdefs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for n in oldtree.body:
 if isinstance(n,ast.FunctionDef) and n.name not in ('main','fixture_claim','trial_policy'):
  assert ast.dump(n,include_attributes=False)==ast.dump(newdefs[n.name],include_attributes=False),n.name
oldclass=next(n for n in oldtree.body if isinstance(n,ast.ClassDef) and n.name=='Session');newclass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Session');methods={n.name:n for n in newclass.body if isinstance(n,ast.FunctionDef)}
for n in oldclass.body:
 if isinstance(n,ast.FunctionDef) and n.name not in ('call','poll'):assert ast.dump(n,include_attributes=False)==ast.dump(methods[n.name],include_attributes=False),n.name
call=methods['call'];call.body=[n for n in call.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='last_exit' for t in n.targets))]
assert ast.dump(call,include_attributes=False)==ast.dump(next(n for n in oldclass.body if isinstance(n,ast.FunctionDef) and n.name=='call'),include_attributes=False)
print('PASS preserved old functions including crash regression and all unchanged Session methods; call adds exit observation only; poll extension separately declared')
m=runpy.run_path(str(TEST));assert set((1,2,3,8,9,13))<set(m['CASES']) and len(m['CHECKS'])==5
peers=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='stub' and n.func.attr=='write_text']
for n in peers:
 text=eval(compile(ast.Expression(n.args[0]),'<peer-expression>','eval'),{'repr':repr,'str':str},{'mode':'withhold','marker':pathlib.Path('/tmp/marker'),'base':pathlib.Path('/tmp/private')});compile(text,'<private-peer>','exec')
product=(ROOT/'tools/runtime_session.py').read_text();publisher=next(n for n in ast.parse(product).body if isinstance(n,ast.FunctionDef) and n.name=='atomic_json')
for name in ('cancel_crash','handoff_crash'):
 assignment=next(n for n in ast.walk(newdefs[name]) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='hook' for t in n.targets));hook=eval(compile(ast.Expression(assignment.value),'<hook-expression>','eval'),{'repr':repr},{'boundary':'result'});lines=product.splitlines(keepends=True);lines.insert(publisher.end_lineno,hook);compile(''.join(lines),'<private-publication-fault>','exec')
print('PASS runner and both generated protocol peers and publication fault wrappers compile')
with tempfile.TemporaryDirectory(prefix='n127-author-') as home:
 inputs=m['source_inputs'](home);repo=pathlib.Path(inputs['workspace_path'])
 assert m['git_fixture'](repo,'rev-parse','HEAD')==inputs['source_revision']
 for entry in inputs['source_manifest']:
  raw=subprocess.check_output(['git','-C',str(repo),'show',inputs['source_revision']+':'+entry['path']]);assert hashlib.sha256(raw).hexdigest()==entry['sha256']
 m['git_fixture'](repo,'worktree','add','--quiet','--detach',str(pathlib.Path(home)/'fresh'),inputs['source_revision'])
 print('PASS actual committed source/template/resource fixture and fresh worktree materialization')
with tempfile.TemporaryDirectory(prefix='n127-author-') as home:m['claim_controls'](home,(ROOT/'tools/fixtures_self_test.sh').read_text())
commands=[(['--chec','handoff-source-bound'],2,'parser'),(['--case','4','--runtime','stub'],2,'parser'),(['--case','6','--runtime','stub','--layer','policy'],2,'parser'),(['--case','10'],2,'parser'),(['--case','5','--runtime','sbcl'],2,'parser'),(['--check','handoff-source-bound','--require-isolation'],2,'parser'),(['--allow-unsupported-isolation'],2,'parser'),(['--case','1','--runtime','stub'],0,'inherited-positive'),(['--check','record-schema'],0,'inherited-positive'),(['--case','8','--runtime','stub','--layer','policy'],0,'inherited-positive'),(['--check','fixture-claim-registered'],1,'baseline-harness-only-nine'),(['--case','6','--runtime','stub'],1,'baseline-unsupported-reattach-not-semantic-red')]
manifest={'revision':REV,'baseline':BASE,'test_sha256':hashlib.sha256(TEST.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(product.encode()).hexdigest(),'source_blob':subprocess.check_output(['git','rev-parse',REV+':tools/runtime_session.py'],text=True).strip(),'python':sys.version,'executable':sys.executable}
(OUT/'acceptance1-check-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for i,(args,expected,kind) in enumerate(commands,1):
 argv=[sys.executable,str(TEST),*args];p=subprocess.run(argv,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=40);prefix='acceptance1-'+str(i).zfill(2)
 (OUT/(prefix+'.stdout.txt')).write_text(p.stdout);(OUT/(prefix+'.stderr.txt')).write_text(p.stderr)
 (OUT/(prefix+'-result.json')).write_text(json.dumps({'argv':argv,'cwd':str(ROOT),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'actual_exit':p.returncode,'expected_exit':expected,'classification':kind,'stdout':'.agent/evidence/127/'+prefix+'.stdout.txt','stderr':'.agent/evidence/127/'+prefix+'.stderr.txt','manifest':'.agent/evidence/127/acceptance1-check-manifest.json'},indent=2)+'\n')
 print(prefix,kind,'actual_exit',p.returncode)
 assert p.returncode==expected,(args,p.stdout,p.stderr)
 if kind=='parser':assert 'usage:' in p.stderr and 'SETUP' not in p.stderr
 if kind=='inherited-positive':assert 'PASS' in p.stdout
 if kind=='baseline-harness-only-nine':assert 'actual scheduling selects all fourteen commands exactly' in p.stderr
 if kind=='baseline-unsupported-reattach-not-semantic-red':assert "'error': 'unsupported'" in p.stderr
print('AUTHOR CHECKS COMPLETE: no executable127/new semantic red or final bundle/QA claimed')
