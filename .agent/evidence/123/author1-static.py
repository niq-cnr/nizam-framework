"""Static-only freeze checks; never imports or executes product/acceptance modules."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = '99f8a0bf952922f84d410b74cd501f11212f7ac5'
PRESERVATION = 'f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])
def tree(data):
    return ast.parse(data)
def dump(node):
    return ast.dump(node, include_attributes=False)
def definitions(module):
    return {n.name: dump(n) for n in module.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def inventories(module):
    values = {}
    def literal(node):
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return literal(node.left) + literal(node.right)
        return ast.literal_eval(node)
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.endswith('CASES'): values[name] = literal(node.value)
    return values

assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
contract = json.loads((ROOT / '.agent/contracts/123.json').read_bytes())
assert contract['status'] == 'approved'
assert hashlib.sha256((ROOT / '.agent/contracts/123.json').read_bytes()).hexdigest() == '0eb09db2d8758a7762e1b9ac9fb1a7de9b2db9882be343235aea88c2a6c29838'
for path in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py'):
    old = tree(git('show', PRESERVATION + ':' + path))
    new = tree((ROOT / path).read_bytes())
    expected, actual = definitions(old), definitions(new)
    for name in expected:
        if name != 'main': assert actual[name] == expected[name], path + ' inherited definition changed: ' + name
    if path.endswith('test_workflow_assurance.py'):
        before, after = inventories(old), inventories(new)
        assert all(after[key] == value for key, value in before.items()), 'inherited inventories changed'
        labels = sum((after[k] for k in ('CASES', 'AGF_CASES', 'RECEIPT_CASES', 'LANE_CASES', 'FAILURE_CASES')), ())
        assert len(labels) == 46 and len(set(labels)) == 46
        if 'CONTROL_CASES' in after:
            assert after['CONTROL_CASES'] == ('ci-candidate-bound', 'ci-blocker-rejected')
            assert len(set(labels + after['CONTROL_CASES'])) == 48
        compile((ROOT / path).read_bytes(), str(ROOT / path), 'exec')
    else:
        assert (ROOT / path).read_bytes() == git('show', BASE + ':' + path), 'author touched Source'
allowed = ('tools/test_workflow_assurance.py', '.agent/evidence/123/author1-', '.agent/evidence/123/api-interface.json')
changed = git('diff', '--name-only', BASE).decode().splitlines()
untracked = git('ls-files', '--others', '--exclude-standard').decode().splitlines()
assert all(any(path == p or (p.endswith('-') and path.startswith(p)) for p in allowed) for path in changed + untracked), 'unowned path changed'
rows = git('ls-tree', '-rz', BASE, '--', '.nizam').split(b'\0')
rows = [row for row in rows if row]
regular = 0
for row in rows:
    header, path = row.split(b'\t'); mode, kind, blob = header.split()
    path = path.decode(); target = ROOT / path
    assert not target.is_symlink() and target.is_file(), 'installed path nonregular'
    assert target.read_bytes() == git('cat-file', 'blob', blob.decode()), 'installed bytes changed'
    assert bool(target.stat().st_mode & 0o111) == (mode == b'100755'), 'installed mode changed'
    regular += kind == b'blob' and mode in (b'100644', b'100755')
assert regular == 239
print(json.dumps({'static_only': True, 'exercised_revision': git('rev-parse', 'HEAD').decode().strip(), 'preservation_anchor': PRESERVATION, 'inherited_cases': 46, 'installed_regular_files': regular, 'changed_paths': changed, 'untracked_paths': untracked}, sort_keys=True))
