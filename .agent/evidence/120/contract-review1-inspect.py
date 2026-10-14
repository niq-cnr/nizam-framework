"""Independent pre-code testability probes; no prospective120 API execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path(__file__).resolve().parents[3]
read = lambda path: json.loads((root/path).read_bytes())
contract = read('.agent/contracts/120.json')
assert hashlib.sha256((root/'.agent/contracts/120.json').read_bytes()).hexdigest() == '620130f2e63ff117192d83ac9dda2f51afc6aa87d4d0e54067bd60373626a2a8'
jsonschema.validate(contract, read('schema/contract.schema.json'))
features = read('.agent/feature_list_018.json')
items = features['features'] if isinstance(features,dict) else features
feature = next(f for f in items if f['id'] == '120')
commands = [v['command'] for v in contract['verification']]
expected = feature.get('verification_commands', feature.get('verification', []))
if isinstance(expected,list) and expected and isinstance(expected[0],dict): expected = [v['command'] for v in expected]
assert commands == expected, (commands, expected)
print('PASS proposal schema and all eleven exact canonical acceptance commands; no missing API run attempted')
schema = read('schema/run_state.schema.json'); state = read('.agent/run_state.json')
jsonschema.validate(state, schema)
event = {'at':'2026-10-14T16:00:00Z','event':'wa-receipt-transition','operation_id':'fixture-precode-only','feature_id':'120','stage':'qa-passed','candidate_sha256':'1'*64,'receipt_sha256':'2'*64}
proposed = copy.deepcopy(state); proposed['history'].append(event)
errors = list(jsonschema.Draft202012Validator(schema).iter_errors(proposed))
assert any(error.validator == 'required' and 'detail' in error.message for error in errors)
print('CONFIRMED transition event exactly specified by proposal violates shipped run-state schema:', [(list(error.path),error.message) for error in errors])
for kind,path in [('approved-contract','.agent/contracts/119.json'),('evidence-capture','.agent/evidence/119/evidence-capture.json'),('fresh-qa','.agent/qa/119.json')]:
    obj = read(path)
    agf = isinstance(obj.get('final_verdict'),dict) and obj['final_verdict'].get('approved') is True and all(obj.get(k) == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
    print('ACTUAL ARTIFACT', kind, json.dumps({'path':path,'status':obj.get('status'),'approvals':obj.get('approvals'),'passed':obj.get('passed'),'actual_exit':obj.get('actual_exit'),'strict_agf_gate':agf},sort_keys=True))
    assert agf == (kind == 'fresh-qa')
raw = read('.agent/evidence/119/qa1/case-approve-empty.result.json')
assert type(raw['exit_code']) is int and raw['exit_code'] == 0 and isinstance(raw['argv'],list)
print('ACTUAL execution capture binds argv/cwd/revision/actual exit and output paths:', json.dumps({k:raw[k] for k in ('argv','cwd','revision','exit_code','stdout','stderr')},sort_keys=True))
assert 'stdout and stderr artifact references' in contract['api']['receipt_shape']
assert 'actual strict integer exit_code==policy.expected_exit==0' in contract['api']['actual_execution']
print('CONFIRMED receipt declares exit/executed itself; contracted check fields have no immutable capture-result ref from which to cross-check actual exit/argv/revision. Hashing matching PASS bytes alone supplies no actual-exit observation.')
operator = read('.agent/evidence/phase018-preflight/activation-authority.json')
assert '120' in operator['scope']['features']
print('PASS standing operator authorization explicitly covers120; Root application may bind actual stage/candidate without asking operator again')
print('OBSERVED shipped run-state status is unrestricted string, not enum:', json.dumps(schema['properties']['status']))
print('REVIEWED_REVISION', subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip())
