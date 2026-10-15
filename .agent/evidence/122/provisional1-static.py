"""Independent static bundle inspection; never runs acceptance or routing behavior."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path(__file__).resolve().parents[3]
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])
def digest(data):
    return hashlib.sha256(data).hexdigest()
freeze = json.loads((root/'.agent/evidence/122/author1-freeze.json').read_bytes())
for ref in freeze['refs']:
    data = git('show', ref['revision']+':'+ref['path'])
    row = git('ls-tree', ref['revision'], '--', ref['path']).decode().split()
    assert digest(data) == ref['sha256'] and row[:3] == [ref['git_mode'], 'blob', ref['git_blob']]
    assert (root/ref['path']).read_bytes() == data
print('FREEZE_REFS_VERIFIED', len(freeze['refs']))
base = 'd9dd92db6ae7b4b6aaa5fc7c99060e6bfbb2752a'
old = ast.parse(git('show', base+':tools/test_workflow_assurance.py'))
new = ast.parse((root/'tools/test_workflow_assurance.py').read_bytes())
nodes = {n.name:n for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for node in old.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name != 'main':
        assert ast.dump(node) == ast.dump(nodes[node.name]), node.name
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        assert any(ast.dump(node) == ast.dump(n) for n in new.body)
inventories = {}
def inventory_value(node):
    if isinstance(node, ast.Name): return inventories[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return inventory_value(node.left) + inventory_value(node.right)
    return ast.literal_eval(node)
for n in new.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.endswith('CASES'):
        inventories[n.targets[0].id] = inventory_value(n.value)
inventories = {k:inventories[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')}
assert sum(len(inventories[k]) for k in inventories if k != 'FAILURE_CASES') == 42
assert inventories['FAILURE_CASES'] == ('infrastructure-failed','semantic-failed','reject-cause-relabel','counter-continuity')
assert (root/'tools/workflow_assurance.py').read_bytes() == git('show', base+':tools/workflow_assurance.py')
interface = json.loads((root/'.agent/evidence/122/api-interface.json').read_bytes())
contract = json.loads((root/'.agent/contracts/122.json').read_bytes())
assert interface['profiles'] == contract['api'] and interface['default_count'] == 46
for label in ('fixture-static', *inventories['FAILURE_CASES']):
    proof = json.loads((root/('.agent/evidence/122/author1-'+label+'.json')).read_bytes())
    assert proof['actual_exit'] == (0 if label == 'fixture-static' else 2)
    assert proof['exercised_revision'] == freeze['frozen_bundle_revision']
    if label != 'fixture-static':
        assert b'SETUP_ERROR: missing route_failed_attempt API' in (root/('.agent/evidence/122/'+proof['stderr'])).read_bytes()
print('STATIC_OK inherited ASTs/inventories retained; inherited42+new4=46; Source unchanged; interface matches contract; author raw setup proof inspected')
print('REVIEW_BLOCKER output invalid-UTF8 acceptance absent; stdout drift only changes current bytes and stderr is never independently mutated')
print('REVIEW_BLOCKER cycle/nonfinite probes use unknown extra key and cannot distinguish exact-key rejection from malformed-value handling on an otherwise exact request')
verdict = dict(review='synthetic review', feature='122', feature_id='122', final_verdict={'approved':True,'summary':'independent','metadata':{'nested':[1]}}, issues=['blocking fixture finding'], missing_acceptance_coverage=[], unsupported_claims=[], required_fixes=[])
schema = json.loads((root/'schema/contract_review.schema.json').read_bytes())
errors = list(jsonschema.Draft202012Validator(schema).iter_errors(verdict))
assert len(errors) == 1 and list(errors[0].absolute_path) == ['issues',0]
print('REVIEW_BLOCKER semantic intended-positive contract_review issues[0] string violates object schema:', errors[0].message)
review = json.loads((root/'.agent/qa/122-provisional-bundle-review.json').read_bytes())
for path in ('schema/qa_verdict.schema.json','.nizam/schema/qa_verdict.schema.json'):
    jsonschema.Draft202012Validator(json.loads((root/path).read_bytes())).validate(review)
print('REVIEW_VERDICT_VALID root+installed QA schemas; acceptance commands executed=0')
