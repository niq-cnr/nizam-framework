"""Author3 static-only qualification. No runner/product/native execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

root = Path.cwd()
base = '05ed4b61f8e16c3000c280aabd1d7e22fbcc8d58'


def git(*args):
    argv = ['git', *args]; child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = child.communicate(timeout=15)
    print(json.dumps({'argv': argv, 'pid': child.pid, 'actual_exit': child.returncode,
                      'stdout_sha256': hashlib.sha256(out).hexdigest(), 'stderr': err.decode()}))
    assert child.returncode == 0
    return out


dump = lambda node: ast.dump(node, include_attributes=False)
source = (root / 'tools/test_runtime_session.py').read_bytes()
compile(source, 'tools/test_runtime_session.py', 'exec'); tree = ast.parse(source)
old = ast.parse(git('show', base + ':tools/test_runtime_session.py'))
named = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
old_named = {n.name: n for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
changed = {'live_condition', 'live_negative_controls'}
added = {'live_rendered_snapshot', 'live_rendered_guard', 'aborted_capture_observation', 'live_rendered_overflow_control'}
assert set(named) - set(old_named) == added
for name, node in old_named.items():
    assert name in changed or dump(node) == dump(named[name]), name
assert [dump(n) for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))] == [
    dump(n) for n in old.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))]
historical = ast.parse(git('show', '599d7c5aa0c0c80ce8da596c7aeae2924d7dca04:tools/test_runtime_session.py'))
for node in historical.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        assert dump(node) == dump(named[node.name]), node.name
body = named['live_condition'].body
guard = next(i for i, n in enumerate(body) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
             and isinstance(n.value.func, ast.Name) and n.value.func.id == 'live_rendered_guard')
early = next(i for i, n in enumerate(body) if isinstance(n, ast.If) and dump(n.test) == dump(ast.parse('record is None', mode='eval').body))
assert guard < early and isinstance(body[early].body[-1], ast.Return)
assert isinstance(body[early].body[0], ast.Expr) and body[early].body[0].value.func.id == 'aborted_capture_observation'
assert not any(isinstance(n, ast.Name) and n.id in ('capture_deadline', 'capture_observation')
               for n in ast.walk(named['aborted_capture_observation']))
assert any(isinstance(n, ast.Name) and n.id == 'capture_bindings' for n in ast.walk(named['aborted_capture_observation']))
wrapper = next(n.value for n in ast.walk(named['live_control_candidate']) if isinstance(n, ast.Constant)
               and isinstance(n.value, str) and n.value.startswith('import json, subprocess, sys\n'))
compile(wrapper.replace('FAULT', repr('unbounded')), 'unchanged-private-observation-wrapper', 'exec')
git('diff', '--check', base)
paths = git('diff', '--name-only', base).decode().splitlines()
paths += [line[3:] for line in git('status', '--porcelain', '--untracked-files=all').decode().splitlines()]
assert all(p == 'tools/test_runtime_session.py' or p.startswith('.agent/evidence/129/E129/author3/') for p in paths)
assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/niq-cnr/nizam-framework.git'
assert not (root / 'tools/sbcl_session_loop.lisp').exists()
for path, expected in {
    '.agent/contracts/129.json': '71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6',
    '.agent/evidence/129/interface-intent1.json': '402e7d02486f7ff29697433c13d05d9d86b691c67eba2310a24bc0817cbbf773',
    'tools/runtime_session.py': 'fe5917389ee3bdec342bd440d7ce48adf7d7e933cb4cf3f4dc1d1bbb1cecb345',
    '.agent/evidence/123/fresh-qa-capture1.py': 'e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0',
}.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path
print(json.dumps({'status': 'STATIC_ONLY_PASS', 'runner_sha256': hashlib.sha256(source).hexdigest(),
                  'runner_git_blob': git('hash-object', 'tools/test_runtime_session.py').decode().strip(),
                  'qualified_native_helpers_ast_unchanged': True, 'original_acceptance_and_inherited14_preserved': True,
                  'common_guard_before_none_return': True, 'aborted_elapsed_descriptive_only': True,
                  'native_backend_mutant_executions': 0,
                  'changed_added_ast_sha256': {name: hashlib.sha256(dump(named[name]).encode()).hexdigest()
                                              for name in sorted(changed | added)}}))
