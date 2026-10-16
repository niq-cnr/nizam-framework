import ast, hashlib, json, subprocess
from pathlib import Path
root = Path.cwd()
out = root/'.agent/evidence/129/bundle-review-qualification1'
git = lambda *args: subprocess.check_output(['git', *args])
sha = lambda raw: hashlib.sha256(raw).hexdigest()
runner = (root/'tools/test_runtime_session.py').read_bytes()
assert sha(runner) == '1cb7c33f15454fe6c8babf2541b7c24fdfa794c39b2f8ce70a34569c9ba12f27'
old = ast.parse(git('show','599d7c5aa0c0c80ce8da596c7aeae2924d7dca04:tools/test_runtime_session.py'))
new = ast.parse(runner)
for node in old.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
        peer = next(n for n in new.body if type(n) is type(node) and n.name == node.name)
        assert ast.dump(node,include_attributes=False)==ast.dump(peer,include_attributes=False),node.name
for name in ('CHECKS','CASES','CORE_LEAVES'):
    value = lambda tree: next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    assert ast.dump(value(old))==ast.dump(value(new)),name
protected = ('tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','.nizam','schema','.github','tools/fixtures_self_test.sh')
assert not git('diff','--name-only','d66ff730248dec4f086365be55eb4ad060a350c5','HEAD','--',*protected)
assert sha((root/'.agent/contracts/129.json').read_bytes())=='71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6'
assert sha((root/'.agent/evidence/129/interface-intent1.json').read_bytes())=='402e7d02486f7ff29697433c13d05d9d86b691c67eba2310a24bc0817cbbf773'
manifest=json.loads((out/'manifest.json').read_bytes())
assert len(manifest['sources'])==11
for row in manifest['sources']:
    assert sha(Path(row['path']).read_bytes())==row['sha256']
frame=json.loads((out/'native1.execution.json').read_bytes())
assert frame['actual_exit']==0 and not frame['timed_out'] and frame['exercised_revision']=='12729c2d1eb4522a8f58ed3853f54e11c2e8753e'
for stream in ('stdout','stderr'):
    raw=(out/Path(frame[stream]['path']).name).read_bytes()
    assert sha(raw)==frame[stream]['sha256'] and len(raw)==frame[stream]['bytes']
lines=(out/'native1.stdout.txt').read_text().splitlines()
assert len([line for line in lines if line.startswith('FIXTURE_READ ')])==11
assert [line.split()[1] for line in lines if line.startswith('ACTIVE_DONE ')]==['evaluate','load_source','compile_source']
assert lines.count('QUALIFICATION_DONE READ=11 ACTIVE=3')==1
for row in manifest['sources']:
    if row['active']:
        assert ('ACTIVE_CAPTURE '+row['kind']+' '+row['condition']+' '+row['frame']+' '+row['restart']) in lines
        for key in ('progress','cleanup'): assert Path(row[key]).read_text().splitlines()==[row['witness']]
        assert not Path(row['invoked']).exists()
print('STATIC_PASS pinned runner/contract/interface, inherited14 functions and selection inventories, protected paths, exact11 native source hashes and actual0 direct frame; no controller execution')
print('SBCL_EXECUTABLE_SHA256',sha(Path('/usr/bin/sbcl').read_bytes()))
