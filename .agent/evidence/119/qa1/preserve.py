"""QA-originated compatibility inspection, anchored to immutable feature118."""
import ast
import importlib.util
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[4]
anchor = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
def old(path):
    return subprocess.check_output(['git', 'show', anchor + ':' + path], cwd=root).decode()
def syntax(text):
    return ast.parse(text)
def functions(tree):
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
source = 'tools/workflow_assurance.py'
before = syntax(old(source)); after = syntax((root/source).read_text())
b, a = functions(before), functions(after)
assert set(a) == set(b) | {'convergent_agf_verdict'}
assert all(a[k] == v for k, v in b.items()), 'inherited source API body changed'
after.body = [n for n in after.body if not (isinstance(n, ast.FunctionDef) and n.name == 'convergent_agf_verdict') and not (isinstance(n, ast.Import) and len(n.names) == 1 and n.names[0].name == 'copy')]
assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), 'inherited source module changed'
test = 'tools/test_workflow_assurance.py'
b, a = functions(syntax(old(test))), functions(syntax((root/test).read_text()))
assert all(a[k] == v for k, v in b.items() if k != 'main'), 'inherited acceptance functions changed'
spec = importlib.util.spec_from_file_location('qa_inventory', root/test)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
expected = ('identity-positive', 'invalidate-source', 'invalidate-contract', 'invalidate-tests', 'invalidate-tool', 'invalidate-environment', 'invalidate-unknown', 'record-continuity', 'reject-unowned-field', 'reject-history-edit', 'allow-owned-append', 'reject-self-review', 'reject-seal-change', 'reject-missing-red', 'reject-setup-as-red', 'independent-handoff', 'accepted-entry', 'reject-foreign-repo', 'reject-stale-pin', 'reject-role-write')
assert module.CASES == expected, repr(module.CASES)
assert module.AGF_CASES == ('approve-empty', 'advisory-visible', 'block-carried', 'reject-issues', 'reject-missing-coverage', 'reject-unsupported')
print('PASS inherited source module and API AST unchanged; twenty-case inventory and inherited test functions preserved; six119 separate')
