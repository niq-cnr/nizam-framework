import ast, hashlib, importlib.util, json, subprocess
from pathlib import Path
root=Path.cwd();out=root/'.agent/evidence/129/bundle-review-qualification2'
git=lambda *args:subprocess.check_output(['git',*args])
sha=lambda raw:hashlib.sha256(raw).hexdigest()
runner=root/'tools/test_runtime_session.py';raw=runner.read_bytes()
assert sha(raw)=='3a9bc25eb29c5368be51aa47728d5c7ad4a4f4829716bfbd7c1f1a1dda4969bb'
old=ast.parse(git('show','599d7c5aa0c0c80ce8da596c7aeae2924d7dca04:tools/test_runtime_session.py'));new=ast.parse(raw)
for node in old.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
        peer=next(n for n in new.body if type(n) is type(node) and n.name==node.name)
        assert ast.dump(node)==ast.dump(peer),node.name
for name in ('CHECKS','CASES','CORE_LEAVES'):
    get=lambda tree:next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    assert ast.dump(get(old))==ast.dump(get(new))
assert not git('diff','--name-only','2130e795e4075cf0d28845d0f5220dcf4dd4571c','HEAD','--','tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','.nizam','schema','.github','.agent/contracts/129.json','.agent/evidence/129/interface-intent1.json')
frame=json.loads((out/'native1.execution.json').read_bytes())
assert frame['actual_exit']==0 and not frame['timed_out'] and frame['child_pid']>0 and frame['exercised_revision']=='6aa7dfd3841b94adefc0fbfc126645ae8759c463'
for key in ('stdout','stderr'):
    data=(out/Path(frame[key]['path']).name).read_bytes()
    assert sha(data)==frame[key]['sha256'] and len(data)==frame[key]['bytes']
lines=(out/'native1.stdout.txt').read_text().splitlines();rows=json.loads((out/'manifest.json').read_bytes())['sources']
assert len(rows)==14 and sum(l.startswith('FIXTURE_READ ') for l in lines)==14
assert sum(l.startswith('ACTIVE_DONE ') for l in lines)==6 and lines.count('QUALIFICATION_DONE READ=14 ACTIVE=6')==1
spec=importlib.util.spec_from_file_location('proposed129',runner);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for row in rows:
    assert sha(Path(row['path']).read_bytes())==row['sha256']
    if not row['active']:continue
    assert ('ACTIVE_CAPTURE '+row['label']+' '+row['condition']+' '+row['frame']+' '+row['restart']) in lines
    for key in ('progress','cleanup'):assert Path(row[key]).read_text().splitlines()==[row['witness']]
    assert not Path(row['invoked']).exists() and Path(row['ended']).is_file()
    if row['label'].startswith('finite'):
        try:module.capture_observation(Path(row['callback']),Path(row['ended']),row['limits'])
        except AssertionError as exc:assert str(exc)=='BEHAVIOR_ASSERTION: CAPTURE_REQUESTED_DEADLINE'
        else:raise AssertionError('finite300ms counterexample not rejected')
        print('FINITE_NEGATIVE_PASS',row['label'],'actual native callback overrun rejected exactly')
    else:module.capture_observation(Path(row['callback']),Path(row['ended']),row['limits'])
for text,reason in [('7/32/T','CAPTURE_PRINT_LEVEL'),('6/33/T','CAPTURE_PRINT_LENGTH'),('6/32/NIL','CAPTURE_PRINT_CIRCLE')]:
    try:module.capture_bindings(text)
    except AssertionError as exc:assert str(exc)=='BEHAVIOR_ASSERTION: '+reason
    else:raise AssertionError('binding negative escaped')
print('STATIC_PASS source/selection/protected preservation; native14read/6active; exact finite deadline and pure binding assertion controls. No controller/backend execution.')
