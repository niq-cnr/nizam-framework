"""Independent narrow static review; no acceptance or routing API execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import jsonschema

root = Path(__file__).resolve().parents[3]
def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
freeze = json.loads((root/'.agent/evidence/122/author2-freeze.json').read_bytes())
for ref in freeze['refs']:
    raw = git('show',ref['revision']+':'+ref['path']); row = git('ls-tree',ref['revision'],'--',ref['path']).decode().split()
    assert hashlib.sha256(raw).hexdigest() == ref['sha256'] and row[:3] == [ref['git_mode'],'blob',ref['git_blob']]
    assert (root/ref['path']).read_bytes() == raw and not bool((root/ref['path']).stat().st_mode & 0o111)
print('FREEZE_REFS_VERIFIED',len(freeze['refs']))
old = ast.parse(git('show','d9dd92db6ae7b4b6aaa5fc7c99060e6bfbb2752a:tools/test_workflow_assurance.py'))
new = ast.parse((root/'tools/test_workflow_assurance.py').read_bytes()); nodes = {n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n in old.body:
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name != 'main': assert ast.dump(n) == ast.dump(nodes[n.name]),n.name
    elif isinstance(n,(ast.Assign,ast.AnnAssign)): assert any(ast.dump(n)==ast.dump(x) for x in new.body)
inventory = {}
def value(n):
    if isinstance(n,ast.Name): return inventory[n.id]
    if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add): return value(n.left)+value(n.right)
    return ast.literal_eval(n)
for n in new.body:
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id.endswith('CASES'): inventory[n.targets[0].id]=value(n.value)
assert sum(len(inventory[k]) for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES'))==42 and len(inventory['FAILURE_CASES'])==4
prior = ast.parse(git('show','933b1335f877c728c98c87338c78757743223fc1:tools/test_workflow_assurance.py'))
changed = [n.name for n in prior.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and ast.dump(n)!=ast.dump(nodes[n.name])]
assert changed == ['failure_infrastructure','failure_semantic','failure_relabel']
assert not git('diff','--name-only','933b1335f877c728c98c87338c78757743223fc1','HEAD','--','tools/workflow_assurance.py','.agent/contracts/122.json','.agent/evidence/122/author1-*','.agent/qa/122-provisional-bundle-review.json')
interface=json.loads((root/'.agent/evidence/122/api-interface.json').read_bytes()); contract=json.loads((root/'.agent/contracts/122.json').read_bytes())
assert interface['profiles']==contract['api'] and interface['test_sha256']==freeze['test_sha256']
proof=json.loads((root/'.agent/evidence/122/author2-fixture-static.execution.json').read_bytes())
assert proof['actual_exit']==0 and proof['exercised_revision']==freeze['frozen_bundle_revision']
raw=(root/'.agent/evidence/122/author2-fixture-static.stdout').read_text()
assert raw.count('UTF8_FIXTURE_OK ')==2 and raw.count('EXACT_KEY_MALFORMED_FIXTURE_OK ')==3 and raw.count('SEMANTIC_VERDICT_SCHEMA_OK ')==6
namespace={'copy':copy}; exec(compile(ast.Module(body=[nodes['failure_verdict']],type_ignores=[]),'<frozen-fixture-builder>','exec'),namespace)
loop=next(n for n in nodes['failure_semantic'].body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple))
for approved,issues in ast.literal_eval(loop.iter):
    for family in ('contract_review','qa_verdict'):
        f=SimpleNamespace(gate=dict(final_verdict={'approved':True,'summary':'independent'},issues=[],missing_acceptance_coverage=[],unsupported_claims=[],required_fixes=[]))
        verdict=namespace['failure_verdict'](f,family,approved,issues)
        jsonschema.Draft202012Validator(json.loads((root/('schema/'+family+'.schema.json')).read_bytes())).validate(verdict)
print('STATIC_OK inherited42/default46; narrow three repairs; unchanged Source/contract/prior evidence; both semantic families/all six schema-valid combinations')
review=json.loads((root/'.agent/qa/122-provisional-bundle-review-rev1.json').read_bytes())
for p in ('schema/qa_verdict.schema.json','.nizam/schema/qa_verdict.schema.json'): jsonschema.Draft202012Validator(json.loads((root/p).read_bytes())).validate(review)
print('PROVISIONAL_APPROVED_STATIC_ONLY; output UTF8 bindings and exact-key malformed probes reviewed; no API behavior executed; executable controls/seal remain later')
