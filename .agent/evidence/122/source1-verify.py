"""Frozen Source1 preservation and one default acceptance execution."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path.cwd()
BASE = '59375cf49fad8b6caaec8dd3911f2cc1f685dcf3'
PREFIX = Path('.agent/evidence/122/source1-default')

def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout

def inventory(data):
    names = {}
    def value(node):
        if isinstance(node, ast.Name): return names[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return value(node.left) + value(node.right)
        return ast.literal_eval(node)
    for node in ast.parse(data).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and (target.id.endswith('_CASES') or target.id == 'CASES'):
                    names[target.id] = value(node.value)
    return names

def record(path):
    item = ROOT / path
    mode = item.lstat().st_mode
    return {'sha256': hashlib.sha256(item.read_bytes()).hexdigest(), 'mode': stat.S_IMODE(mode),
        'git_blob': hashlib.sha1(b'blob ' + str(item.stat().st_size).encode() + b'\0' + item.read_bytes()).hexdigest(),
        'executable': bool(mode & 0o111)}

tracked = git('ls-files', '-z').decode().split('\0')[:-1]
protected = sorted(path for path in tracked if path.startswith(('.nizam/', 'schema/', '.agent/evidence/')) or path in
    ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/122.json', '.agent/run_state.json'))
protected = [path for path in protected if not path.startswith('.agent/evidence/122/source1-')]
before = {path: record(path) for path in protected}
Path('.agent/evidence/122/source1-preservation-before.json').write_text(json.dumps(before, indent=2) + '\n')
assert before['tools/test_workflow_assurance.py']['sha256'] == '8b0b8f2d3e2bea397eaf8b9bc6761aaedd38ba3bcdc5f47d7b62e0bec9938fa4'
assert before['.agent/contracts/122.json']['sha256'] == '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
source = Path('tools/workflow_assurance.py').read_bytes()
old_ast = ast.parse(git('show', BASE + ':tools/workflow_assurance.py'))
new_ast = ast.parse(source)
def definitions(tree):
    return {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))}
old_defs, new_defs = definitions(old_ast), definitions(new_ast)
assert all(new_defs.get(name) == body for name, body in old_defs.items()), 'Inherited function/class/CLI AST changed'
current = inventory(Path('tools/test_workflow_assurance.py').read_bytes())
historical = inventory(git('show', '8ac94f6808e8197111197c9acbf59b2aa92efc7c:tools/test_workflow_assurance.py'))['CASES']
expected = list(historical)
for feature in ('119', '120', '121', '122'):
    contract = json.loads(Path('.agent/contracts/' + feature + '.json').read_text())
    expected.extend(row['command'].split('--case ', 1)[1] for row in contract['verification'])
actual = list(current['CASES'] + current['AGF_CASES'] + current['RECEIPT_CASES'] + current['LANE_CASES'] + current['FAILURE_CASES'])
assert actual == expected and len(actual) == 46
argv = ['python3', 'tools/test_workflow_assurance.py']
revision = git('rev-parse', 'HEAD').decode().strip()
started = time.time()
run = subprocess.run(argv, cwd=ROOT, env=os.environ.copy(), capture_output=True)
Path(str(PREFIX) + '.stdout.txt').write_bytes(run.stdout)
Path(str(PREFIX) + '.stderr.txt').write_bytes(run.stderr)
after = {path: record(path) for path in protected}
Path('.agent/evidence/122/source1-preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
passed = [line.removeprefix('PASS ') for line in run.stdout.decode('utf-8').splitlines() if line.startswith('PASS ')]
result = {'role': 'Generator', 'stage': 'development-default-once', 'argv': argv, 'cwd': str(ROOT),
    'environment': {'PYTHONDONTWRITEBYTECODE': os.environ.get('PYTHONDONTWRITEBYTECODE'), 'python': git('hash-object', 'tools/test_workflow_assurance.py').decode().strip()},
    'exercised_revision': revision, 'actual_exit': run.returncode, 'elapsed_seconds': time.time() - started,
    'stdout': str(PREFIX) + '.stdout.txt', 'stderr': str(PREFIX) + '.stderr.txt', 'ordered_expected': expected,
    'ordered_passes': passed, 'order_exact': passed == expected, 'protected_count': len(protected),
    'installed_count': len([p for p in protected if p.startswith('.nizam/')]), 'preserved': before == after,
    'inherited_definitions_unchanged': sorted(old_defs), 'pins': {p: before[p] for p in
    ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/122.json', '.agent/run_state.json')}}
Path(str(PREFIX) + '-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'actual_exit': run.returncode, 'ordered_passes': len(passed), 'order_exact': passed == expected,
    'preserved': before == after, 'protected_count': len(protected), 'result': str(PREFIX) + '-result.json'}))
if run.returncode:
    print(run.stderr.decode('utf-8'))
    raise SystemExit(run.returncode)
assert before == after and passed == expected, 'Preservation or ordered acceptance mismatch'
