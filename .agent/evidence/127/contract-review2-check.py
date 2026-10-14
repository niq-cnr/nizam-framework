"""Independent round2 ownership and preservation review; no implementation acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from jsonschema import Draft202012Validator

root = Path.cwd()
out = root / '.agent/evidence/127'
def git(*args):
    return subprocess.check_output(['git',*args])
def sha(data):
    return hashlib.sha256(data).hexdigest()
old_ref = 'cf02c6ee79a8d82ca5b468f153f03e82de417956'
proposal = 'bac04b8d94092343437ad95b07b99c2eb6592c11'
expected = 'a98180d2c1456d95f0ec120dba40f043b7c367b92f884f8d58f784d07679b13a'
raw = Path('.agent/contracts/127.json').read_bytes()
assert sha(raw) == expected and raw == git('show',proposal+':.agent/contracts/127.json')
old = json.loads(git('show',old_ref+':.agent/contracts/127.json'))
new = json.loads(raw)
Draft202012Validator(json.load(open('.nizam/schema/contract.schema.json'))).validate(new)
assert new['status']=='proposed' and new['contract_attempt']==2
assert new['approvals']==dict(validator_mode_a=False,evaluator_contract_review=False,revisions=1)
normalized=copy.deepcopy(new)
for key in ('scope','non_goals','contract_attempt','approvals'):
    normalized[key]=old[key]
assert normalized==old
assert new['scope']['files_modify'][:6]==old['scope']['files_modify']
assert new['scope']['files_create'][0]['path']==old['scope']['files_create'][0]['path']
assert new['non_goals'][:2]==old['non_goals'][:2]
added_create={x['path']:x['purpose'] for x in new['scope']['files_create'][1:]}
assert set(added_create)=={'.agent/validator/127-*.json','.agent/qa/127*.json','.agent/evidence/127-qa-adversarial.txt'}
added_modify={x['path']:x['purpose'] for x in new['scope']['files_modify'][6:]}
assert set(added_modify)=={'.agent/contracts/127.json','.agent/run_state.json','.agent/feature_list_016.json','docs/planning/phase_016.yaml','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'}
feature=next(x for x in json.load(open('.agent/feature_list_016.json'))['features'] if x['id']=='127')
assert [x['command'] for x in new['verification']]==feature['acceptance_tests']
ident=json.load(open(out/'contract-review-identities.json'))
for path, identity in ident['files'].items():
    if path != '.agent/contracts/127.json':
        assert sha(Path(path).read_bytes())==identity['sha256'], path
seal=json.load(open(out/'contract-review-finalization.json'))
for path,digest in seal['artifact_sha256'].items():
    assert sha(Path(path).read_bytes())==digest, path
    assert Path(path).read_bytes()==git('show','b0bdbb7873e972e01e4ccf0df32b1f9297c67a69:'+path)
state=json.load(open('.agent/run_state.json'))
assert state['circuit_breaker']['127-contract-review']['attempts']==2
snapshot=dict(reviewer='/root/contract_review127',attempt=2,exercised_revision=git('rev-parse','HEAD').decode().strip(),
    proposal_commit=proposal,proposal_sha256=expected,
    unchanged_review_inputs_except_contract=list(p for p in ident['files'] if p!='.agent/contracts/127.json'),
    prior_control_commit='b0bdbb7873e972e01e4ccf0df32b1f9297c67a69',
    preserved_prior_artifact_sha256=seal['artifact_sha256'],
    added_create=added_create,added_modify=added_modify,
    projection_sha256=sha(json.dumps({k:v for k,v in new.items() if k not in ('scope','non_goals','contract_attempt','approvals')},sort_keys=True,separators=(',',':')).encode()))
(out/'contract-review2-preservation.json').write_text(json.dumps(snapshot,indent=2)+'\n')
print('PASS exact revised proposal, installed schema, ownership-only delta, exact five commands and unchanged behavior/testability/budget')
print('PASS all prior review inputs except contract and every sealed baseline-control artifact match immutable Git identity')
