"""Create independent QA only from observed contract checks and fixed candidate bindings."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import jsonschema

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/118/'
ACTOR = '/root/wa_acceptance118'
def read(path):
    return json.loads((ROOT / path).read_text())
def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])
def create(path, value):
    with (ROOT / path).open('x') as out:
        json.dump(value, out, indent=2); out.write('\n')
candidate = read(E + 'source-candidate.json')
assert set(candidate) == {'revision','tree','source_sha256','runtime_sha256','historical_sha256'}
assert candidate['revision'] == '60cf91d1e2f0781382c20a5a18bb1673a381c0d8'
assert candidate['tree'] == 'b64616bc09108ecc7a329f286a84dfd6e60889b4'
assert git('rev-parse', candidate['revision'] + '^{tree}').decode().strip() == candidate['tree']
assert git('rev-parse', 'HEAD').decode().strip() == '89a379e1c35d31ed01988d755f9660dbbc0bac04'
assert git('diff', 'HEAD', '--exit-code') == b''
verified = []
for group, count in [('source_sha256',4),('runtime_sha256',28),('historical_sha256',12)]:
    assert len(candidate[group]) == count
    for path, sha in candidate[group].items():
        current = ROOT / path
        assert current.is_file() and not current.is_symlink()
        assert digest(path) == sha
        revisions = [candidate['revision']]
        if group == 'historical_sha256':
            revisions.append(read(E + 'api-interface.json')['historical_base'])
        for revision in revisions:
            assert hashlib.sha256(git('show', revision + ':' + path)).hexdigest() == sha
            mode = git('ls-tree', revision, '--', path).decode().split()[0]
            assert mode in ('100644', '100755')
            assert bool(current.stat().st_mode & 0o111) == (mode == '100755')
        verified.append(path)
roles = read(E + 'role-sessions.json')
prerequisite = read(E + 'prerequisite20.json')
mode_b = read('.agent/validator/118-mode-b.json')
prerequisite_sha = digest(E + 'prerequisite20.json')
assert prerequisite_sha == '04ce2913faa240344829eb9dac0d264b79e555a5387ead3d5d2abbb26c16b116'
for key,value in candidate.items():
    assert prerequisite[key] == value and mode_b[key] == value
identities = {role['agent_id'] for role in roles.values()}
assert ACTOR not in identities | {prerequisite['actor'],mode_b['actor']}
assert prerequisite['actor'] not in identities
assert prerequisite['passed'] is True and type(prerequisite['checks_run']) is int and prerequisite['checks_run'] == 20
assert type(prerequisite['checks_passed']) is int and prerequisite['checks_passed'] == 20
assert mode_b['final_verdict']['approved'] is True
for key in ['issues','missing_acceptance_coverage','unsupported_claims']:
    assert mode_b[key] == []
assert mode_b['prerequisite_sha256'] == prerequisite_sha
contract = read('.agent/contracts/118.json')
assert contract['status'] == 'approved'
for gate in contract['approvals']['gate_refs'].values():
    if isinstance(gate,dict):
        assert digest(gate['path']) == gate['sha256']
        value = read(gate['path'])
        assert value['final_verdict']['approved'] is True
        assert all(value[key] == [] for key in ['issues','missing_acceptance_coverage','unsupported_claims'])
review = read(E + 'recovery1-closeout-review.json')
assert review['final_verdict']['approved'] is True
for field in ['adapter','original_guard','authorization']:
    assert digest(review[field + '_ref']) == review[field + '_sha256']
assert review['adapter_sha256'] == '411b55a075db5ad36bdf8eab37d9c4f236433f1fd9bbd6f6c5d0bdeb9d546d43'
def check_raw(path, command):
    raw = (ROOT / path).read_text()
    for key,value in [('COMMAND',command),('REVISION',candidate['revision']),('EXIT','0')]:
        assert re.findall(r'^' + key + r': (.*)$',raw,re.M) == [value]
    assert raw.count('\nSTDOUT:\n') == raw.count('\nSTDERR:\n') == 1
    assert raw.split('\nSTDOUT:\n')[1].split('\nSTDERR:\n')[0].strip()
checks = []
for number, row in enumerate(contract['verification'],1):
    path = E + f'recovery1-qa-check-{number}.txt'
    check_raw(path,row['command'])
    checks.append(dict(row, exit_code=0, evidence=path,sha256=digest(path)))
assert len(checks) == 3
spot = E + 'recovery1-qa-ownspot.txt'
command = 'PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/118/recovery1-qa-ownspot.py'
check_raw(spot,command)
files = [row['evidence'] for row in checks] + [spot]
assert len(set(files)) == 4
report = {'actor':ACTOR,'candidate':candidate,'verified_input_count':len(verified),'verified_inputs':verified,'current_and_git_bytes_modes_unchanged':True,'prerequisite_sha256':prerequisite_sha,'independent_roles':{'test_author':roles['test_author']['agent_id'],'developer':roles['developer']['agent_id'],'bundle_reviewer':roles['acceptance_reviewer']['agent_id'],'mode_b':mode_b['actor'],'prerequisite':prerequisite['actor'],'qa':ACTOR},'limited_closeout_override':mode_b['limited_closeout_override'],'claim_boundary':'Independent QA only. No future evidence capture, feature completion, or unmodified terminal scope pass is asserted.'}
create(E + 'recovery1-qa-invariants.json',report)
qa = dict(candidate, feature_id='118',actor=ACTOR,prerequisite_sha256=prerequisite_sha,qa_pass=True,checks_run=3,checks_passed=3,checks=checks,required_fixes=[],evidence_files=files,adversarial={'performed':True,'command':command,'evidence':spot,'sha256':digest(spot)},adversarial_check={'description':'Correctly hashed prerequisite proof redirected through symlink outside repository must be rejected; actual and isolated valid controls and restored controls pass.','result':'pass','evidence':spot},issues=[],missing_acceptance_coverage=[],unsupported_claims=[],final_verdict={'approved':True,'summary':'Three personally executed contract commands passed at immutable SourceC2. Independent proof-redirection attack rejected with passing valid/restored controls; candidate hashes/modes and role independence verified. Ready for separate Root evidence capture, without a completion claim.'},evidence_sha256={path:digest(path) for path in files},invariants_ref=E + 'recovery1-qa-invariants.json',limited_closeout_override=mode_b['limited_closeout_override'])
jsonschema.validate(qa,read('.nizam/schema/qa_verdict.schema.json'))
assert set(read(E + 'producer-interface.json')['qa']['required']) <= set(qa)
assert type(qa['checks_run']) is int and type(qa['checks_passed']) is int
create('.agent/qa/118.json',qa)
print('PASS all 44 candidate current/Git hashes and modes; historical anchor, strict counts, role separation, actual gates and supplemental adapter bindings')
print('PASS exactly three ordered contract raw proofs and distinct semantic adversarial proof; installed QA schema and producer required fields')
print('QA_SHA256:',digest('.agent/qa/118.json'))
