"""Validate the contracted schema union and immutable fixture bindings without routing behavior."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import jsonschema
ROOT = Path(__file__).resolve().parents[3]
baseline = ast.parse(subprocess.check_output(['git','-C',str(ROOT),'show','b18955c3375f2c0fc75ec4ecc17e8b7968e2a93e:tools/test_workflow_assurance.py']))
current = ast.parse((ROOT/'tools/test_workflow_assurance.py').read_bytes())
nodes = {n.name:n for n in current.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n in baseline.body:
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name != 'failure_semantic': assert ast.dump(n) == ast.dump(nodes[n.name]), n.name
    elif isinstance(n,(ast.Assign,ast.AnnAssign)): assert any(ast.dump(n) == ast.dump(m) for m in current.body), 'inventory changed'
spec = importlib.util.spec_from_file_location('frozen_author3',ROOT/'tools/test_workflow_assurance.py')
bank = importlib.util.module_from_spec(spec); spec.loader.exec_module(bank)
assert len(bank.CASES+bank.AGF_CASES+bank.RECEIPT_CASES+bank.LANE_CASES) == 42
assert len(bank.CASES+bank.AGF_CASES+bank.RECEIPT_CASES+bank.LANE_CASES+bank.FAILURE_CASES) == 46
assert bank.sha((ROOT/'tools/workflow_assurance.py').read_bytes()) == 'e4d17fb258bbcf19d1b6c7011661368dbe196323c4bb1f94af6540296d204e46'
assert bank.sha((ROOT/'.agent/contracts/122.json').read_bytes()) == '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
api = bank.load_api(); os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
schemas = {name:json.loads((ROOT/'schema'/(name+'.schema.json')).read_bytes()) for name in ('qa_verdict','contract_review','run_state','contract')}
def pinned(f, reference):
    raw = subprocess.check_output(['git','-C',str(f.root),'show',reference['revision']+':'+reference['path']])
    assert bank.sha(raw) == reference['sha256'] and (f.root/reference['path']).read_bytes() == raw
    assert subprocess.check_output(['git','-C',str(f.root),'ls-tree',reference['revision'],'--',reference['path']]).startswith(b'100644 blob ')
    return json.loads(raw)
with tempfile.TemporaryDirectory(prefix='nizam122-author3-schema-') as parent:
    f = bank.FailureFixture(api,parent,'semantic'); assert f.capture['exit_code'] == 7
    for name,value in (('contract',json.loads((f.root/'contract.json').read_bytes())),('run_state',f.state)):
        jsonschema.Draft202012Validator(schemas[name]).validate(value)
    rows = bank.failure_legacy_verdicts(f)
    assert len(rows) == 24 and sum(not deny for label,verdict,deny in rows) == 4
    for label,verdict,deny in rows:
        jsonschema.Draft202012Validator(schemas['qa_verdict']).validate(verdict)
        jsonschema.Draft202012Validator(schemas['qa_verdict']['anyOf'][0]).validate(verdict)
        assert not jsonschema.Draft202012Validator(schemas['qa_verdict']['anyOf'][1]).is_valid(verdict)
        f.evidence['verdict_ref'] = f.pin_new(label,verdict); f.bind()
        authority = pinned(f,f.policy['authority_ref']); evidence = pinned(f,authority['evidence_ref']); capture = pinned(f,authority['capture_ref'])
        assert evidence['capture_ref'] == authority['capture_ref'] and pinned(f,evidence['verdict_ref']) == verdict
        assert capture == f.capture and capture['candidate_sha256'] == bank.sha(bank.canonical(f.candidate))
        print('LEGACY_SCHEMA_BINDING_OK',label,'expected_rejection='+str(deny),json.dumps(evidence['verdict_ref'],sort_keys=True))
    outcomes = next(n.iter for n in nodes['failure_semantic'].body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple))
    for approved,issues in ast.literal_eval(outcomes):
        for family in ('qa_verdict','contract_review'):
            jsonschema.Draft202012Validator(schemas[family]).validate(bank.failure_verdict(f,family,approved,issues))
            print('EXISTING_SCHEMA_OK',family,approved,len(issues))
print('AUTHOR3_STATIC_OK inherited42/default46 and other3 unchanged; legacy4 positives/20 typed or passing negatives; no route API executed')
