import ast, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path
from types import SimpleNamespace
root=Path.cwd();runner=root/'tools/test_runtime_session.py';raw=runner.read_bytes()
sha=lambda value:hashlib.sha256(value).hexdigest()
git=lambda *args:subprocess.check_output(['git',*args])
assert sha(raw)=='81a7299120ad79cca1765e6c4c47f0d8907bfa6e593804a9ffd97210700dffe4'
current=ast.parse(raw)
previous=ast.parse(git('show','063a44f8dc326e7a8bb5667e660eb88e5ef2b4fc:tools/test_runtime_session.py'))
historical=ast.parse(git('show','599d7c5aa0c0c80ce8da596c7aeae2924d7dca04:tools/test_runtime_session.py'))
definition=lambda tree,name:next(node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name==name)
for name in ('condition_fixture','capture_fixture','capture_bindings','capture_deadline','capture_observation','live_unresolved_capture','live_printing','admission','live_main','live_selection_refusals','live_runtime_guards'):
    assert ast.dump(definition(current,name))==ast.dump(definition(previous,name)),name
for node in historical.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
        assert ast.dump(node)==ast.dump(definition(current,node.name)),node.name
for name in ('CHECKS','CASES','CORE_LEAVES'):
    value=lambda tree:next(node.value for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))
    assert ast.dump(value(current))==ast.dump(value(historical)),name
changed=git('diff','--name-only','05ed4b61f8e16c3000c280aabd1d7e22fbcc8d58','4578e341b46388e07c48d73c0766096702208aa9').decode().splitlines()
assert all(p=='tools/test_runtime_session.py' or p.startswith('.agent/evidence/129/E129/author3/') for p in changed)
for path,expected in json.loads((root/'.agent/evidence/129/E129/author3/repair3-receipt.json').read_bytes())['input_and_runner_sha256'].items():
    assert sha((root/path).read_bytes())==expected,path
body=definition(current,'live_condition').body
guard=next(i for i,node in enumerate(body) if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='live_rendered_guard')
early=next(i for i,node in enumerate(body) if isinstance(node,ast.If) and any(isinstance(child,ast.Return) for child in ast.walk(node)))
assert guard<early
aborted=definition(current,'aborted_capture_observation')
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('capture_deadline','capture_observation') for n in ast.walk(aborted))
spec=importlib.util.spec_from_file_location('proposed129',runner)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
cases=[('zero',0,0,False),('boundary',1024,1024,False),('log-overflow',2049,0,True),('diagnostic-overflow',0,2049,True),('combined-overflow',1024,1025,True)]
for label,log_size,diagnostic_size,negative in cases:
    with tempfile.TemporaryDirectory(prefix='n129-review3-owned-') as temporary:
        directory=Path(temporary);(directory/'diagnostics').mkdir()
        (directory/'child.old.log').write_bytes(b'oldlog')
        (directory/'diagnostics'/'old-operation').write_bytes(b'old diagnostic')
        session=SimpleNamespace(directory=directory)
        before=module.live_rendered_snapshot(session)
        if log_size:(directory/'child.control.log').write_bytes(b'x'*log_size)
        if diagnostic_size:(directory/'diagnostics'/'new-control').write_bytes(b'x'*diagnostic_size)
        try:module.live_rendered_guard(session,before,{'output_bytes':2048})
        except AssertionError as exc:
            assert negative and str(exc)=='BEHAVIOR_ASSERTION: DIAGNOSTIC_BYTE_BUDGET',(label,str(exc))
        else:assert not negative,label
        print('OWNED_GUARD_CONTROL',json.dumps({'case':label,'log_bytes':log_size,'diagnostic_bytes':diagnostic_size,'expected_rejection':negative,'result':'pass','scope':'pure file-observation mechanics; no backend status or controller'}))
print('QUALIFICATION_PASS unchanged native2/helper/parser/admission/inherited14 AST; protected scope/pins; common guard before early return; aborted clocks descriptive; five owned-file controls')
