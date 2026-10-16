"""Owned author2 static qualification only; does not import/run the runner."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd()
BASE = '2130e795e4075cf0d28845d0f5220dcf4dd4571c'
HISTORICAL = '599d7c5aa0c0c80ce8da596c7aeae2924d7dca04'


def git(*args):
    argv = ['git', *args]
    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = child.communicate(timeout=15)
    print(json.dumps({'argv': argv, 'pid': child.pid, 'actual_exit': child.returncode,
                      'stdout_sha256': hashlib.sha256(out).hexdigest(), 'stderr': err.decode()}))
    assert child.returncode == 0
    return out


def dump(node):
    return ast.dump(node, include_attributes=False)


source = (ROOT / 'tools/test_runtime_session.py').read_bytes()
compile(source, 'tools/test_runtime_session.py', 'exec')
tree = ast.parse(source)
named = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
historical = ast.parse(git('show', HISTORICAL + ':tools/test_runtime_session.py'))
for node in historical.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        assert dump(node) == dump(named[node.name]), node.name
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in
                                            ('CHECKS', 'CASES', 'CORE_LEAVES') for t in node.targets):
        assert any(dump(node) == dump(current) for current in tree.body)
base_tree = ast.parse(git('show', BASE + ':tools/test_runtime_session.py'))
base_named = {node.name: node for node in base_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
for name in ('condition_fixture', 'live_gate', 'live_main', 'live_cancel', 'live_terminate', 'diagnostic'):
    assert dump(named[name]) == dump(base_named[name]), name

admission = ast.get_source_segment(source.decode(), named['admission'])
assert admission.index("opening.pop('runtime')") < admission.index('core_ready()')
assert admission.index('core_ready()') < admission.index("if s.last_exit == 64:")
assert admission.index('SBCL_ADMISSION_UNAVAILABLE:') < admission.index('live_runtime_guards(s, executable)')
assert 'live_runtime_guards' not in admission[:admission.index('SBCL_ADMISSION_UNAVAILABLE:')]

wrapper = next(node.value for node in ast.walk(named['live_control_candidate'])
               if isinstance(node, ast.Constant) and isinstance(node.value, str) and
               node.value.startswith('import json, subprocess, sys\n'))
controls = next(ast.literal_eval(node.value) for node in ast.walk(named['live_negative_controls'])
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'controls' for t in node.targets))
for pairs in controls.values():
    for fault, expected in pairs:
        compile(wrapper.replace('FAULT', repr(fault)), 'public-observation-mutant:' + fault, 'exec')
        assert expected in source.decode()
assert controls[5] == [('runtime-refusal-accepted', 'RUNTIME_SELECTION_GUARD')]
assert ('print-level', 'CAPTURE_PRINT_LEVEL') in controls['bounded-printing']
assert ('print-length', 'CAPTURE_PRINT_LENGTH') in controls['bounded-printing']
assert ('print-circle', 'CAPTURE_PRINT_CIRCLE') in controls['bounded-printing']
reports = ast.literal_eval(named['live_printing'].body[0].value)
assert len(reports) == 8 and reports == ast.literal_eval(base_named['live_printing'].body[0].value)

changed = git('diff', '--name-only', BASE).decode().splitlines()
git('diff', '--check', BASE)
assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/niq-cnr/nizam-framework.git'
status = git('status', '--porcelain', '--untracked-files=all').decode().splitlines()
assert all(path == 'tools/test_runtime_session.py' or path.startswith('.agent/evidence/129/E129/author2/')
           for path in changed + [line[3:] for line in status])
assert not (ROOT / 'tools/sbcl_session_loop.lisp').exists()
for path, expected in {
    '.agent/contracts/129.json': '71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6',
    '.agent/evidence/129/interface-intent1.json': '402e7d02486f7ff29697433c13d05d9d86b691c67eba2310a24bc0817cbbf773',
    'tools/runtime_session.py': 'fe5917389ee3bdec342bd440d7ce48adf7d7e933cb4cf3f4dc1d1bbb1cecb345',
    '.agent/evidence/123/fresh-qa-capture1.py': 'e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0',
}.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
print(json.dumps({'status': 'STATIC_ONLY_PASS', 'runner_sha256': hashlib.sha256(source).hexdigest(),
                  'runner_git_blob': git('hash-object', 'tools/test_runtime_session.py').decode().strip(),
                  'inherited_definitions_ast_preserved': True, 'common_condition_fixture_unchanged': True,
                  'admission_guard_order_static': True, 'wrapper_compilation_only': True,
                  'runtime_executions': 0, 'native_fixture_qualification': 'NOT_RUN; new wrapper requires Root decision',
                  'ast_function_sha256': {name: hashlib.sha256(dump(named[name]).encode()).hexdigest() for name in
                    ('capture_fixture', 'capture_bindings', 'capture_deadline', 'capture_observation',
                     'live_unresolved_capture', 'live_condition', 'live_printing', 'live_selection_refusals',
                     'live_runtime_guards', 'live_control_candidate', 'live_negative_controls', 'admission')}}))
