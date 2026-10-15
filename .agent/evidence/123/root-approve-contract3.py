"""Root-only lifecycle publisher; invoke only with actual third-gate refs."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import jsonschema

proposal_revision, proposal_digest, mode_a_revision, review_revision = sys.argv[1:]
path = Path('.agent/contracts/123.json')
raw = path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == proposal_digest
assert subprocess.check_output(['git','show',proposal_revision+':'+str(path)]) == raw
original = json.loads(raw)
assert original['status'] == 'proposed' and original['approvals']['revisions'] == 2
assert original['approvals']['validator_mode_a'] is False
assert original['approvals']['evaluator_contract_review'] is False
assert 'approval_evidence' not in original
gates = [
    ('.agent/validator/123-mode-a-rev2.json',mode_a_revision,'reviewed_commit','contract_sha256'),
    ('.agent/qa/123-contract-review-rev2.json',review_revision,'reviewed_revision','proposal_sha256'),
]
reviewed = []
for name, revision, revision_key, digest_key in gates:
    data = Path(name).read_bytes()
    assert data == subprocess.check_output(['git','show',revision+':'+name])
    verdict = json.loads(data)
    assert verdict['final_verdict']['approved'] is True
    for key in ('issues','missing_acceptance_coverage','unsupported_claims'):
        assert type(verdict[key]) is list and verdict[key] == []
    assert verdict['feature'] == '123' and verdict[digest_key] == proposal_digest
    for prefix in ('','.nizam/'):
        jsonschema.validate(verdict,json.loads(Path(prefix+'schema/contract_review.schema.json').read_text()))
    reviewed.append(verdict[revision_key])
assert reviewed[0] == reviewed[1]
assert subprocess.check_output(['git','show',reviewed[0]+':'+str(path)]) == raw
state = json.loads(Path('.agent/run_state.json').read_text())
assert state['current_feature'] == state['active_contract_id'] == '123'
assert state['circuit_breaker']['123-contract']['attempts'] == 3
assert all(state['circuit_breaker'][key]['attempts'] == 3 for key in ('123-mode-a','123-contract-review'))
expected = copy.deepcopy(original)
expected['status'] = 'approved'
expected['approvals'].update(validator_mode_a=True,evaluator_contract_review=True,
    approved_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
evidence = {'mode_a':gates[0][0],'contract_review':gates[1][0],
    'proposal_sha256':proposal_digest,'proposal_revision':proposal_revision}
expected['approval_evidence'] = evidence
text = raw.decode()
def replace_value(text, key, value):
    marker = '  '+json.dumps(key)+':'
    assert text.count('\n'+marker) == 1
    start = text.index(marker)+len(marker)
    while text[start].isspace():
        start += 1
    _, length = json.JSONDecoder().raw_decode(text[start:])
    replacement = json.dumps(value,indent=2,ensure_ascii=False).replace('\n','\n  ')
    return text[:start]+replacement+text[start+length:]
text = replace_value(text,'status','approved')
text = replace_value(text,'approvals',expected['approvals'])
marker = '  "dod_ref":'
assert text.count('\n'+marker) == 1
text = text.replace(marker,'  "approval_evidence": '+json.dumps(evidence,ensure_ascii=False)+',\n'+marker,1)
assert json.loads(text) == expected
for prefix in ('','.nizam/'):
    jsonschema.validate(expected,json.loads(Path(prefix+'schema/contract.schema.json').read_text()))
assert hashlib.sha256(Path('tools/workflow_assurance.py').read_bytes()).hexdigest() == 'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6'
assert hashlib.sha256(Path('tools/test_workflow_assurance.py').read_bytes()).hexdigest() == '800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'
path.write_text(text)
print(json.dumps({'role':'Root','feature':'123','passed':True,'actual_exit':0,
    'proposal_revision':proposal_revision,'proposal_sha256':proposal_digest,
    'approved_contract_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'strict_gate_refs':[{'path':r[0],'revision':r[1]} for r in gates],
    'approval_evidence':evidence,'reviewed_revision':reviewed[0],
    'previous_lines':len(raw.splitlines()),'current_lines':len(text.splitlines()),
    'boundary':'Root approval metadata only. Concrete author freeze and distinct provisional approval still required before Source.'},indent=2))
