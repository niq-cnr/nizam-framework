"""Attempt2 fixture/type verification; no route API or inherited behavior runs."""
import ast
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
BASE = 'd9dd92db6ae7b4b6aaa5fc7c99060e6bfbb2752a'
path = ROOT/'tools/test_workflow_assurance.py'
old = ast.parse(subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE+':tools/test_workflow_assurance.py']))
new = ast.parse(path.read_bytes())
index = {n.name:n for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for node in old.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name != 'main':
        assert ast.dump(node) == ast.dump(index[node.name]), node.name
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        assert any(ast.dump(node) == ast.dump(n) for n in new.body), 'inherited inventory'
spec = importlib.util.spec_from_file_location('independent_author2_bank', path)
bank = importlib.util.module_from_spec(spec); spec.loader.exec_module(bank)
assert len(bank.CASES+bank.AGF_CASES+bank.RECEIPT_CASES+bank.LANE_CASES) == 42
assert len(bank.CASES+bank.AGF_CASES+bank.RECEIPT_CASES+bank.LANE_CASES+bank.FAILURE_CASES) == 46
api = bank.load_api(); assert not hasattr(api, 'route_failed_attempt'), 'Source not authorized'
assert bank.sha((ROOT/'.agent/contracts/122.json').read_bytes()) == '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
schema = lambda name: jsonschema.Draft202012Validator(json.loads((ROOT/'schema'/(name+'.schema.json')).read_bytes()))
def pinned(f, reference):
    raw = subprocess.check_output(['git','-C',str(f.root),'show',reference['revision']+':'+reference['path']])
    assert bank.sha(raw) == reference['sha256'] and (f.root/reference['path']).read_bytes() == raw
    assert subprocess.check_output(['git','-C',str(f.root),'ls-tree',reference['revision'],'--',reference['path']]).startswith(b'100644 blob ')
    return raw
for cause in ('infrastructure', 'semantic'):
    with tempfile.TemporaryDirectory(prefix='nizam122-author2-setup-') as parent:
        f = bank.FailureFixture(api, parent, cause)
        schema('run_state').validate(f.state); schema('contract').validate(json.loads((f.root/'contract.json').read_bytes()))
        assert f.capture['executed'] is True and f.capture['exit_code'] == 7
        if cause == 'infrastructure':
            saved = copy.deepcopy((f.capture, f.evidence, f.authority, f.policy))
            for stream in ('stdout', 'stderr'):
                f.capture[stream] = f.pin_new('invalid-utf8-'+stream, b'\xff'); f.bind()
                raw = pinned(f, f.capture[stream]); assert raw == b'\xff'
                try: raw.decode('utf8')
                except UnicodeDecodeError: pass
                else: raise AssertionError('negative must fail UTF8 decoding')
                authority = json.loads(pinned(f, f.policy['authority_ref']))
                capture = json.loads(pinned(f, authority['capture_ref'])); evidence = json.loads(pinned(f, authority['evidence_ref']))
                assert capture == f.capture and evidence['capture_ref'] == authority['capture_ref'] and capture[stream] == f.capture[stream]
                assert capture['candidate_sha256'] == bank.sha(bank.canonical(f.candidate)) and capture['producer'] == f.producer
                assert capture['environment'] == f.candidate['environment'] and capture['revision'] == saved[0]['revision']
                print('UTF8_FIXTURE_OK', stream, json.dumps(dict(output_ref=f.capture[stream], capture_ref=authority['capture_ref'], evidence_ref=authority['evidence_ref'], authority_ref=f.policy['authority_ref']), sort_keys=True))
                f.capture, f.evidence, f.authority, f.policy = copy.deepcopy(saved)
                for output in ('stdout','stderr'): pinned(f, f.capture[output]).decode('utf8')
                assert json.loads(pinned(f, f.policy['authority_ref'])) == f.authority
            cycle = []; cycle.append(cycle)
            for value, label in ((float('nan'),'nan'), (float('inf'),'infinity'), (cycle,'cycle')):
                malformed = copy.deepcopy(f.request); malformed['attempt'] = value
                assert set(malformed) == set(f.request) and all(malformed[k] == f.request[k] for k in f.request if k != 'attempt')
                assert (value[0] is value) if type(value) is list else not math.isfinite(value)
                print('EXACT_KEY_MALFORMED_FIXTURE_OK', label, sorted(malformed))
            calls = [n for n in ast.walk(index['failure_relabel']) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'failure_probe']
            assert any(len(c.args) > 3 and isinstance(c.args[3], ast.Constant) and c.args[3].value == 'attempt' for c in calls)
        else:
            semantic = index['failure_semantic']
            loop = next(n for n in semantic.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple))
            outcomes = ast.literal_eval(loop.iter)
            assert outcomes == ((True, []), (False, []), (True, [{'criterion':'blocking synthetic fixture finding'}]))
            for approved, issues in outcomes:
                for family in ('contract_review','qa_verdict'):
                    verdict = bank.failure_verdict(f, family, approved, issues); schema(family).validate(verdict)
                    assert bool(verdict['issues']) == bool(issues) and verdict['final_verdict']['approved'] is approved
                    rejected = approved is False or bool(issues)
                    print('SEMANTIC_VERDICT_SCHEMA_OK', family, 'approved='+str(approved), 'issues='+str(len(issues)), 'rejecting='+str(rejected))
print('AUTHOR2_STATIC_OK inherited42/default46; fresh UTF8 bindings and all six semantic profiles; no Source behavior')
