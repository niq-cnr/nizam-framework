"""Root evidence admission only; never executes Source or changes lifecycle."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import jsonschema

E = Path('.agent/evidence/122')
def read(path):
    return json.loads(Path(path).read_text())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args])
def ref(row, current=True):
    path, revision = row['path'], row['revision']
    raw = git('show', revision + ':' + path)
    entry = git('ls-tree', revision, '--', path).decode().split()
    assert sha(raw) == row['sha256'], path
    assert entry[2] == row['git_blob'] and entry[0] == row['git_mode'], path
    if current:
        assert Path(path).read_bytes() == raw, path
        assert bool(Path(path).stat().st_mode & 0o111) == (entry[0] == '100755'), path

revision = git('rev-parse', 'HEAD').decode().strip()
gates = {
    '.agent/validator/122-mode-a-rev1.json': 'contract_review',
    '.agent/qa/122-contract-review-rev1.json': 'contract_review',
    '.agent/qa/122-provisional-bundle-review-rev3.json': 'qa_verdict',
    '.agent/qa/122-executable-bundle-review.json': 'qa_verdict',
    '.agent/validator/122-mode-b.json': 'contract_review',
    '.agent/qa/122.json': 'qa_verdict',
}
for path, family in gates.items():
    data = read(path)
    assert data['final_verdict']['approved'] is True, path
    for field in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        assert type(data[field]) is list and data[field] == [], (path, field)
    for prefix in ('', '.nizam/'):
        jsonschema.validate(data, read(prefix + 'schema/' + family + '.schema.json'))
qa = read('.agent/qa/122.json')
assert qa['qa_pass'] is True
for path in qa['evidence_files']:
    assert Path(path).is_file(), path
seal = read(E / 'qa1-artifact-seal.json')
assert seal['artifact_refs_verified'] is True
assert len(seal['artifacts']) == seal['verified_artifact_count'] == 54
for row in seal['artifacts']:
    ref(row, current=row['path'] != '.agent/run_state.json')
results = read(E / 'qa1-results.json')
assert results['all_passed'] is True and results['protected_preserved'] is True
assert results['mandatory_command_count'] == 9
assert results['additional_adversarial_command_count'] == 1
commands = results['commands']
assert len(commands) == 10
assert [r['actual_exit'] for r in commands] == [0,0,0,0,0,0,1,0,0,0]
for row in commands:
    assert row['passed'] is True and row['actual_exit'] == row['expected_exit']
    assert row['argv'] and row['cwd'] and row['environment']['PYTHONDONTWRITEBYTECODE'] == '1'
    assert Path(row['stdout']).is_file() and Path(row['stderr']).is_file()
assert commands[5]['revision'] == '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
assert all(r['revision'] == qa['exercised_revision'] for i,r in enumerate(commands) if i != 5)
ci = read(E / 'ci2-receipt.json')
assert ci['passed'] is True and ci['default46_passed'] is True and ci['failed_jobs'] == []
assert ci['actual_exit'] == 0 and len(ci['all46_ordered']) == 46
assert sha(Path(ci['raw_log']).read_bytes()) == ci['raw_log_sha256']
actual_order = [line.split('PASS ', 1)[1] for line in Path(commands[4]['stdout']).read_text().splitlines() if line.startswith('PASS ')]
assert actual_order == ci['all46_ordered']
assert 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in Path(commands[6]['stderr']).read_text()
assert 'duplicate JSON key: approved' in Path('.agent/evidence/122-qa-adversarial.txt').read_text()
before, after = read(E / 'qa1-before.json'), read(E / 'qa1-after.json')
assert after['preserved'] is True and after['changed_paths'] == []
for key in ('protected_aggregate','protected_count','historical_aggregate'):
    assert before[key] == after[key]
outer = read(E / 'qa1-outer-execution.json')
assert outer['actual_exit'] == outer['wrapper_exit'] == 0 and outer['sealed_helpers_preserved'] is True
for stream in ('stdout','stderr'):
    assert sha(Path(outer[stream]).read_bytes()) == outer[stream + '_sha256']
oa, ob = read(E / 'qa1-outer-after.json'), read(E / 'qa1-outer-before.json')
assert oa['preserved'] is True and oa['installed'] == ob['installed']
assert oa['installed']['regular_files'] == 239
bundle = read(E / 'executable1-current-seal.json')
assert bundle['approved'] is True and bundle['author_and_replay_command_counts'] == [24,24]
for row in bundle['refs']:
    ref(row, current=row['path'] != '.agent/run_state.json')
for row in bundle['portable_objects'].values():
    raw = git('cat-file', 'blob', row['git_oid'])
    assert sha(raw) == row['sha256'] and len(raw) == row['size_bytes']
for row in bundle['historical_state_anchors']:
    pin = row['snapshot_pin']
    raw = git('show', row['revision'] + ':' + row['path'])
    assert sha(raw) == pin['sha256']
    assert git('rev-parse', row['revision'] + ':' + row['path']).decode().strip() == pin['git_blob']
pins = {p: sha(Path(p).read_bytes()) for p in ['.agent/contracts/122.json','tools/workflow_assurance.py','tools/test_workflow_assurance.py']}
assert pins['.agent/contracts/122.json'] == '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
assert read('.agent/contracts/122.json')['status'] == 'approved'
assert len(git('ls-files','.nizam').decode().splitlines()) == 239
assert git('diff','--name-only','HEAD','--','.nizam') == b''
print(json.dumps({'role':'Root','feature':'122','attempt':1,'passed':True,'actual_exit':0,'revision':revision,'strict_gates':list(gates),'pins':pins,'qa_artifact_refs_verified':54,'bundle_refs_verified':len(bundle['refs']),'portable_objects_verified':len(bundle['portable_objects']),'mandatory_commands':9,'additional_checks':1,'actual_exits':[r['actual_exit'] for r in commands],'default_cases':46,'protected_count':after['protected_count'],'installed_count':239,'hosted_receipt':str(E / 'ci2-receipt.json'),'historical_state_comparison':'at recorded immutable refs only','incidental_readonly_parser_errors':['portable_objects initially sliced as list; actual type is object','circuit_breaker initially queried through nonexistent steps wrapper; actual keys are direct'],'boundary':'Evidence admission before canonical completion; final docs/scope/PR103 integration remain pending. No feature123, live Root API adoption, runtime, benchmark, release or installed upgrade claim.'},indent=2))
