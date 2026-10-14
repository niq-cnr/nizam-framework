"""Pre-code schema/interface inspection only; no prospective API or acceptance authoring."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path(__file__).resolve().parents[3]
read = lambda p: json.loads((root/p).read_bytes())
contract = read('.agent/contracts/120.json')
assert hashlib.sha256((root/'.agent/contracts/120.json').read_bytes()).hexdigest() == '25f7845d2593f79fb862d322f7dd29ed356e48415b809d439447890e4dadedb2'
jsonschema.validate(contract, read('schema/contract.schema.json'))
feature = next(f for f in read('.agent/feature_list_018.json')['features'] if f['id'] == '120')
assert [v['command'] for v in contract['verification']] == feature['acceptance_tests']
assert len(contract['verification']) == 11 and contract['estimated_lines'] == 2750
assert contract['budget']['phase_original'] == 7200 and contract['budget']['phase_ceiling'] == 9360
print('PASS actual acceptance_tests field: eleven exact commands, proposal schema and unchanged2750/7200/9360')
state = read('.agent/run_state.json'); schema = read('schema/run_state.schema.json')
jsonschema.validate(state, schema)
operation,feature_id,stage,receipt_hash = 'precode-schema-inspection','120','qa-passed','1'*64
event = {'at':'2026-10-14T16:00:00Z','event':'wa-receipt-transition','detail':'Receipt '+operation+' advanced '+feature_id+':'+stage+' ('+receipt_hash+')','operation_id':operation,'feature_id':feature_id,'stage':stage,'candidate_sha256':'2'*64,'receipt_sha256':receipt_hash}
proposed = copy.deepcopy(state); proposed['history'].append(event)
jsonschema.validate(proposed, schema)
del proposed['history'][-1]['detail']
errors = list(jsonschema.Draft202012Validator(schema).iter_errors(proposed))
assert any(e.validator == 'required' and 'detail' in e.message for e in errors)
print('PASS corrected exact history event validates; actual missing-detail control rejected by unchanged schema')
assert schema['properties']['status'] == {'type':'string','description':'Current lifecycle status of the run.'}
print('PASS explicit nonempty policy from/to strings replace nonexistent schema enum; output validation/prefix preservation required')
operator = read('.agent/evidence/phase018-preflight/activation-authority.json')
assert operator['owner'] == '/root' and operator['gate'] == 'H-PHASE-018'
assert operator['scope']['phase'] == '018-workflow-assurance-controls' and '120' in operator['scope']['features']
assert operator['scope']['original_estimate_lines'] == 7200 and operator['scope']['ceiling_130pct'] == 9360
assert operator['operator_instruction_verbatim'] and operator['repository'] == 'niq-cnr/nizam-framework only'
print('PASS concrete normalized Root application can bind actual standing authority fields; old authority needs no invented approved flag')
for kind,path in [('mode-a','.agent/validator/119-mode-a-rev1.json'),('contract-review','.agent/qa/119-contract-review-rev1.json'),('provisional-bundle','.agent/qa/119-provisional-bundle-review.json'),('mode-b','.agent/validator/119-mode-b.json'),('fresh-qa','.agent/qa/119.json'),('evidence-capture','.agent/evidence/119/evidence-capture.json')]:
    artifact = read(path)
    fields = {'mode-a':('feature','reviewed_commit','contract_sha256','reviewer'),'contract-review':('feature','contract_id','reviewed_revision','proposal_sha256','reviewer'),'provisional-bundle':('feature_id','reviewed_revision','approved_contract_sha256','reviewer'),'mode-b':('feature','reviewed_commit','approved_contract_sha256','reviewer'),'fresh-qa':('feature_id','reviewed_revision','approved_contract_sha256','checks_run','checks_passed','adversarial'),'evidence-capture':('role','feature','revision','approved_contract_sha256','passed','actual_exit')}[kind]
    assert all(field in artifact for field in fields)
    if kind != 'evidence-capture':
        assert artifact['final_verdict']['approved'] is True and all(artifact[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
    else:
        assert artifact['role'] == 'Root' and artifact['passed'] is True and type(artifact['actual_exit']) is int and artifact['actual_exit'] == 0
    print('PASS actual kind-specific fields',kind,','.join(fields))
approved_raw = subprocess.check_output(['git','show','42fb4cfd75a3e3be2313b18fda1bcf801b02c649:.agent/contracts/119.json'],cwd=root)
approved = json.loads(approved_raw); jsonschema.validate(approved,read('schema/contract.schema.json'))
assert approved['status'] == 'approved' and approved['approvals']['validator_mode_a'] is True and approved['approvals']['evaluator_contract_review'] is True
assert read('.agent/contracts/119.json')['status'] == 'complete'
print('PASS immutable approved contract remains available despite live complete metadata; artifact predicates can preserve original gate proposal context')
print('INSPECTED independently pinned capture ref/profile:',contract['api']['capture_profile'])
print('INSPECTED receipt versus capture comparison:',contract['api']['actual_execution'])
print('INSPECTED actual restoration requirement:',contract['api']['recovery'])
print('INSPECTED no future-self-gate:',contract['api']['prerequisites'])
print('BOUNDARY: schema/interface probes only; no120 API exists or was run, no existing runtime acceptance rerun, no Source/test/state edits')
