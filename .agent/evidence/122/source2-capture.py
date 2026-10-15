"""Source2 exact legacy probe then default46 once, with compact protected snapshots."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOT = Path.cwd()
E = ROOT / '.agent/evidence/122'
BASE = 'ef3a25d02aa5b0d5fdc0403216c502b13f4995fd'
SOURCE1 = 'd3eeb42705a8790bb09261cf9e071c344a3d0e91'
OLD = '3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03'
def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout

def save(name, value):
    (E / ('source2-' + name + '.json')).write_text(json.dumps(value, separators=(',', ':')) + '\n')

def snapshot(index=False):
    paths = sorted(p for p in git('ls-files', '-z').decode().split('\0') if p and not p.startswith('.agent/evidence/122/source2-'))
    rows = [[p, stat.S_IMODE((ROOT / p).lstat().st_mode), hashlib.sha256((ROOT / p).read_bytes()).hexdigest()] for p in paths]
    if index:
        (E / 'source2-protected-index.jsonl').write_text(''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows))
    selected = {'tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json','.agent/evidence/122/api-interface.json','.agent/evidence/122/compatibility1-probe.py'}
    return {'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),
        'installed_count':sum(p.startswith('.nizam/') for p in paths),
        'pins':{p:{'mode':mode,'sha256':digest,'git_blob':git('hash-object',p).decode().strip()} for p,mode,digest in rows if p in selected}}

def definitions(data):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(data).body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}

before = snapshot(True); save('protected-before', before)
assert before['installed_count'] == 239
for path, digest in {'tools/test_workflow_assurance.py':'e251283add498c699f6c90fd7934f92dcffe570e6c3fdda51326c6dc0e504c21',
    '.agent/contracts/122.json':'13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5',
    '.agent/evidence/122/api-interface.json':'08467029eb810790420c55da2505e68c294848c1e4a5d798363852d311a31348'}.items():
    assert before['pins'][path]['sha256'] == digest, path
current = definitions((ROOT/'tools/workflow_assurance.py').read_bytes())
prior = definitions(git('show', SOURCE1+':tools/workflow_assurance.py'))
assert set(current)==set(prior) and [name for name in prior if prior[name]!=current[name]] == ['_failure_rejection']
legacy = definitions(git('show', OLD+':tools/workflow_assurance.py'))
assert all(current[name]==value for name,value in legacy.items())
old_tests = definitions(git('show', OLD+':tools/test_workflow_assurance.py'))
current_tests = definitions((ROOT/'tools/test_workflow_assurance.py').read_bytes())
assert all(current_tests[name]==value for name,value in old_tests.items() if name!='main')
original=(E/'compatibility1-probe.py').read_bytes()
copied=(E/'source2-compatibility-probe.py').read_bytes()
assert copied==original.replace(b'compatibility1',b'source2-compatibility')
save('static',{'source1_ast_delta':['_failure_rejection'],'old_source_ast_preserved':True,'old_test_ast_preserved_except_additive_main':True,
    'probe_copy_prefix_only':True,'original_probe_sha256':hashlib.sha256(original).hexdigest(),'copied_probe_sha256':hashlib.sha256(copied).hexdigest(),
    'prefix_replacements':original.count(b'compatibility1'),'base':BASE})
commands=[('compatibility',['python3','.agent/evidence/122/source2-compatibility-probe.py']),('default',['python3','tools/test_workflow_assurance.py'])]
for label,argv in commands:
    start=time.time(); run=subprocess.run(argv,cwd=ROOT,env=os.environ.copy(),capture_output=True)
    (E/('source2-'+label+'.stdout.txt')).write_bytes(run.stdout); (E/('source2-'+label+'.stderr.txt')).write_bytes(run.stderr)
    after=snapshot(); save(label+'-protected-after',after)
    record={'role':'Generator','stage':'Source2 development, not independent QA','argv':argv,'cwd':str(ROOT),
        'environment':{'PYTHONDONTWRITEBYTECODE':os.environ.get('PYTHONDONTWRITEBYTECODE'),'NIZAM_WA120_FIXTURE':os.environ.get('NIZAM_WA120_FIXTURE')},
        'python_executable':sys.executable,'python_version':sys.version,'exercised_revision':git('rev-parse','HEAD').decode().strip(),
        'actual_exit':run.returncode,'expected_exit':0,'elapsed_seconds':time.time()-start,
        'stdout':'.agent/evidence/122/source2-'+label+'.stdout.txt','stderr':'.agent/evidence/122/source2-'+label+'.stderr.txt',
        'protected_preserved':before==after,'pins':before['pins']}
    if label=='default':
        expected=list(ast.literal_eval(ast.parse(git('show','8ac94f6808e8197111197c9acbf59b2aa92efc7c:tools/test_workflow_assurance.py')).body[0].value)) if False else None
        # Canonical requirements supply the exact ordered additions to the historical20 inventory.
        module=ast.parse(git('show','8ac94f6808e8197111197c9acbf59b2aa92efc7c:tools/test_workflow_assurance.py'))
        names={}
        def val(n):
            if isinstance(n,ast.Name): return names[n.id]
            if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add): return val(n.left)+val(n.right)
            return ast.literal_eval(n)
        for n in module.body:
            if isinstance(n,ast.Assign):
                for target in n.targets:
                    if isinstance(target,ast.Name) and (target.id=='CASES' or target.id.endswith('_CASES')): names[target.id]=val(n.value)
        expected=list(names['CASES'])
        for feature in ('119','120','121','122'):
            expected.extend(row['command'].split('--case ',1)[1] for row in json.loads((ROOT/('.agent/contracts/'+feature+'.json')).read_text())['verification'])
        passes=[line[5:] for line in run.stdout.decode().splitlines() if line.startswith('PASS ')]
        record.update(ordered_expected=expected,ordered_passes=passes,order_exact=passes==expected)
    save(label+'-execution',record)
    print(json.dumps({'command':label,'actual_exit':run.returncode,'preserved':before==after,'passes':len(record.get('ordered_passes',[]))}),flush=True)
    if run.returncode:
        print(run.stderr.decode(),flush=True); raise SystemExit(run.returncode)
    assert before==after
    if label=='default': assert record['order_exact'] and len(passes)==46
