"""Independent Mode B preparation: static only, no API import or behavior."""
import ast
import copy
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[3]
BASE = '3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03'
REVIEW = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
def read(path):
    return (ROOT / path).read_bytes()
def tree(raw):
    return ast.parse(raw)
def nodes(raw):
    return {n.name: ast.dump(n) for n in tree(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def validate(value, schema):
    jsonschema.Draft202012Validator(json.loads(read(schema))).validate(value)
contract = json.loads(read('.agent/contracts/122.json'))
validate(contract, 'schema/contract.schema.json')
assert contract['status'] == 'approved'
assert contract['approvals']['validator_mode_a'] is True and contract['approvals']['evaluator_contract_review'] is True
pins = {}
for path, digest in [('tools/workflow_assurance.py', 'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6'), ('tools/test_workflow_assurance.py', '800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'), ('.agent/contracts/122.json', '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5')]:
    assert hashlib.sha256(read(path)).hexdigest() == digest
    assert git('show', REVIEW + ':' + path) == read(path)
    entry = git('ls-tree', REVIEW, '--', path).decode().split()
    assert entry[0] == '100644' and not ((ROOT / path).stat().st_mode & 0o111)
    pins[path] = dict(sha256=digest, git_blob=entry[2], git_mode=entry[0])
old = nodes(git('show', BASE + ':tools/workflow_assurance.py')); new = nodes(read('tools/workflow_assurance.py'))
assert all(new.get(k) == v for k, v in old.items())
assert sorted(set(new) - set(old)) == ['_failure_continuity', '_failure_rejection', 'route_failed_attempt']
old_tests = tree(git('show', BASE + ':tools/test_workflow_assurance.py')); new_tests = tree(read('tools/test_workflow_assurance.py'))
old = nodes(git('show', BASE + ':tools/test_workflow_assurance.py')); new = nodes(read('tools/test_workflow_assurance.py'))
assert all(new.get(k) == v for k, v in old.items() if k != 'main')
for node in old_tests.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.endswith('CASES') for t in node.targets):
        assert any(ast.dump(node) == ast.dump(other) for other in new_tests.body)
reduced = copy.deepcopy(new_tests)
fixture = next(n for n in reduced.body if isinstance(n, ast.ClassDef) and n.name == 'FailureFixture')
hook = next(n for n in fixture.body if isinstance(n, ast.FunctionDef) and n.name == 'commit'); fixture.body.remove(hook)
assert ast.dump(reduced) == ast.dump(tree(git('show', 'd96cc8295f79bccd990041375b92e4e03a71012d:tools/test_workflow_assurance.py')))
changed = git('diff', '--name-only', BASE, REVIEW).decode().splitlines()
allowed = [i['path'] for group in ('files_create', 'files_modify') for i in contract['scope'][group]]
assert all(any(fnmatch.fnmatchcase(path, pattern) for pattern in allowed) for path in changed)
assert not any(p.startswith(('.nizam/', 'schema/')) for p in changed)
assert git('show', BASE + ':.agent/evidence/scope-budget-014/measure.py') == read('.agent/evidence/scope-budget-014/measure.py')
for path in ('methodology/03_circuit_breaker.md', 'tools/README.md'):
    fm = yaml.safe_load(read(path).decode().split('---', 2)[1]); validate(fm, 'schema/frontmatter.schema.json')
    assert fm['change_log'][0]['version'] == fm['version'] and fm['status'] == 'active'
for path in (contract['approval_evidence']['mode_a'], contract['approval_evidence']['contract_review']):
    verdict = json.loads(read(path)); validate(verdict, 'schema/contract_review.schema.json'); validate(verdict, '.nizam/schema/contract_review.schema.json')
    assert verdict['final_verdict']['approved'] is True and all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
state = json.loads(read('.agent/run_state.json')); validate(state, 'schema/run_state.schema.json')
assert state['circuit_breaker']['122-mode-b']['attempts'] == 1
assert state['scope_budget']['original_estimate_lines'] == 7200 and state['scope_budget']['ceiling_130pct'] == 9360
assert [(v['id'], v['actual']) for v in state['scope_budget']['per_feature']] == [('119', 722), ('120', 1397), ('121', 1245)]
assert [v['command'].split('--case ')[1] for v in contract['verification']] == ['infrastructure-failed', 'semantic-failed', 'reject-cause-relabel', 'counter-continuity']
recovery = json.loads(read('.agent/evidence/122/fixture-portability-recovery.json'))
assert recovery['author_attempt'] == recovery['author_limit'] == recovery['review_attempt'] == recovery['review_limit'] == 4
assert 'Root interpretation' in recovery['authority_interpretation'] and 'not a new task-specific operator reply' in recovery['authority_interpretation']
print(json.dumps(dict(reviewed_revision=REVIEW, measurement_base=BASE, pins=pins, inherited_source_asts=True, inherited_test_asts_and_inventories=True, narrow_hook_only=True, exact_scope=True, immutable_classifier=True, doc_frontmatter=True, contract_gates=True, phase_budget_prior_actuals_preserved=True, api_calls=0, final_gate=False), sort_keys=True))
