"""Root evidence capture121: verify recorded immutable proofs, no behavioral reruns."""
import hashlib
import json
import pathlib
import subprocess

import jsonschema

E = pathlib.Path('.agent/evidence/121')
QA = '9dc1e951a9af931213fa8df2498b140e46e081a5'
PARTIAL = '98dd46340a7d53c0ba700e3913b57bb987598d37'
REVIEW = 'daadb7c29f738acd97e04c05170bb66eb84e323f'
APPROVED = '145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e'
def read(path): return json.loads(pathlib.Path(path).read_bytes())
def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(ref, path): return subprocess.check_output(['git', 'show', ref + ':' + path])
def historical(ref, path): return json.loads(blob(ref, path))
def strict(path):
    value = read(path)
    assert value['final_verdict']['approved'] is True, path
    assert all(type(value[k]) is list and value[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
    schema = 'qa_verdict' if path == '.agent/qa/121.json' else 'contract_review'
    for root in ('schema/', '.nizam/schema/'):
        jsonschema.validate(value, read(root + schema + '.schema.json'))
    return value
def pin(value):
    data = blob(value['revision'], value['path'])
    assert sha(data) == value['sha256'] and len(data) == value['size_bytes'], value['path']
    oid = value.get('git_oid', value.get('git_blob'))
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == oid
def streams(record):
    assert record['environment']['PYTHONDONTWRITEBYTECODE'] == '1'
    for stream in ('stdout', 'stderr'):
        p = record[stream]; data = pathlib.Path(p['path']).read_bytes()
        assert sha(data) == p['sha256'] and len(data) == p['size_bytes']

contract = read('.agent/contracts/121.json')
assert contract['status'] == 'approved' and sha(pathlib.Path('.agent/contracts/121.json').read_bytes()) == APPROVED
gates = ['.agent/validator/121-mode-a.json', '.agent/qa/121-contract-review.json', '.agent/qa/121-provisional-bundle-review-rev2.json', '.agent/qa/121-executable-bundle-review-rev1.json', '.agent/validator/121-mode-b-rev1.json', '.agent/qa/121.json']
verdicts = [strict(path) for path in gates]; q = verdicts[-1]
assert verdicts[0]['contract_sha256'] == verdicts[1]['proposal_sha256'] == contract['approval_evidence']['proposal_sha256']
assert verdicts[2]['approved_contract_sha256'] == verdicts[4]['contract_sha256'] == APPROVED
assert read(E / 'precode-final-capture.json')['passed'] is True
assert read(E / 'source-prerequisite.json')['passed'] is True
source = sha(pathlib.Path('tools/workflow_assurance.py').read_bytes())
tests = sha(pathlib.Path('tools/test_workflow_assurance.py').read_bytes())
assert source == '1d97f06f32713d3944933680d6b2558fd093d26c158da49546d408d5560beb36'
assert tests == verdicts[2]['test_sha256'] == verdicts[4]['test_sha256'] == 'c94a59e1330680003a1a92ad5881911f7b99bdced2f01504e4335b80469d25c6'
assert verdicts[4]['source_sha256'] == source
bundle = historical(REVIEW, str(E / 'executable-review3-seal.json'))
bundle_pins = bundle['immutable_artifact_pins'] + list(bundle['inputs'].values()) + [bundle[k] for k in ('author_seal', 'historical_baseline_review', 'recovery', 'verifier')]
for value in bundle_pins: pin(value)
assert bundle['inputs']['source']['sha256'] == source and bundle['inputs']['tests']['sha256'] == tests
assert bundle['actual_wrapper_exit'] == bundle['actual_verifier_exit'] == 0
assert bundle['captures'] == 27 and bundle['triplets'] == 5 and bundle['restored_blobs'] == 8
for path in ('controls3-root-binding.json', 'executable-review3-root-binding.json'):
    binding = read(E / path); assert binding['passed'] is True and binding['source_sha256'] == source
for ref, path in ((PARTIAL, 'qa1-partial-seal.json'), (QA, 'qa2-final-seal.json')):
    for value in historical(ref, str(E / path))['files'].values(): pin(value)
partial = read(E / 'qa1-partial-summary.json'); pending = read(E / 'qa2-pending-summary.json')
assert partial['mandatory_wrapper']['actual_exit'] == pending['original_wrapper_actual_exit'] == 1
assert partial['complete'] is False and pending['passed'] is True
assert partial['completed_mandatory_commands'] == 8 and pending['pending_mandatory_completed'] == 2
assert pending['additional_check_executions'] == q['adversarial']['executions'] == 1 and q['adversarial']['performed'] is True
assert read(E / 'qa1-protected-before.json') == read(E / 'qa1-protected-after.json')
assert read(E / 'qa2-protected-before.json') == read(E / 'qa2-protected-after.json')
records = partial['verification_commands'] + pending['records']; assert len(records) == 11
for record in records:
    assert type(record['actual_exit']) is int and record['actual_exit'] == record['expected_exit']
    streams(record)
assert q['qa_pass'] is True and type(q['checks_run']) is int and q['checks_run'] == q['checks_passed'] == 5
assert [c['command'] for c in q['checks']] == [c['command'] for c in contract['verification']]
for index, check in enumerate(q['checks'], 1):
    assert check['exit_code'] == 0 and check['evidence_revision'] == '1172435f54d3825134d461950dea6e56f6469fa0'
    assert read(check['evidence']) == records[index - 1]
    assert pathlib.Path(records[index - 1]['stdout']['path']).read_text().splitlines() == ['PASS ' + records[index - 1]['argv'][-1]]
assert records[6]['exercised_revision'] == '8ac94f6808e8197111197c9acbf59b2aa92efc7c' and records[6]['actual_exit'] == 0
assert records[7]['actual_exit'] == 1
assert 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in pathlib.Path(records[7]['stderr']['path']).read_text()
extra = read(E / 'qa2-adversarial-git.json'); assert extra['actual_exit'] == 128
streams(extra)
assert pathlib.Path('.agent/evidence/121-qa-adversarial.txt').is_file()
assert all(pathlib.Path(p).is_file() for p in q['evidence_files'])
ci = read(E / 'ci2-receipt.json'); assert ci['passed'] is True and ci['default42_passed'] is True and ci['actual_exit'] == 0
assert len(ci['all42_ordered']) == 42
assert pathlib.Path(records[5]['stdout']['path']).read_text().splitlines() == ['PASS ' + name for name in ci['all42_ordered']]
assert sha(pathlib.Path(ci['raw_log']).read_bytes()) == ci['raw_log_sha256']
for path, value in ci['source_bindings'].items():
    assert sha(pathlib.Path(path).read_bytes()) == value['sha256'] and git('rev-parse', 'HEAD:' + path) == value['git_blob']
assert read(E / 'ci2-capture-wrapper.json')['actual_exit'] == 0
assert all(r['actual_exit'] == 0 for r in read(E / 'ci2-fetch-results.json'))
installed = [p for p in git('ls-files', '-z', '.nizam/').split('\0') if p]; assert len(installed) == 239
for path in installed:
    p = pathlib.Path(path); assert p.is_file() and not p.is_symlink()
    assert p.read_bytes() == blob('f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb', path)
provenance = read('.nizam/provenance.json')
assert provenance['framework_version'] == '1.5.0' and provenance['resolved_sha'] == 'f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852'
failures = ['source1-root-failure-capture.json', 'controls1-author-wrapper.json', 'executable-review1-postrun-failure.json', 'modeb1-probe-run.json', 'executable-review3-inspection-failure.json', 'executable-review3-assembly-failure.json', 'qa1-partial-summary.json']
assert all((E / p).is_file() for p in failures)
result = {'role': 'Root', 'feature': '121', 'attempt': 1, 'passed': True, 'actual_exit': 0, 'revision': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'), 'approved_contract_sha256': APPROVED, 'source_sha256': source, 'test_sha256': tests, 'strict_gates': gates, 'bundle_revision': REVIEW, 'bundle_pins_verified': len(bundle_pins), 'qa_revision': QA, 'qa_raw_seal_pins': [33, 29], 'qa_mandatory_commands': 10, 'additional_checks': 1, 'additional_executions': 1, 'actual_nested_git_failure': 128, 'original_QA_wrapper_failure_retained': 1, 'historical_foundation_revision': records[6]['exercised_revision'], 'live_stale_exit': 1, 'hosted_receipt': str(E / 'ci2-receipt.json'), 'default_cases': 42, 'installed_count': 239, 'preserved_failure_paths': [str(E / p) for p in failures], 'boundary': 'Evidence gate before canonical121 completion. No live Root library adoption, controls-ready123, full runtime, benchmark, release, tag or installed upgrade claim.'}
(E / 'evidence-capture.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS evidence121: six strict gates,73 bundle+62 QA pins,10 mandatory+one extra,hosted42,installed239; original failures retained')
