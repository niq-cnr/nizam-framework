"""Root evidence gate120: verify immutable execution records, never rerun behavior."""
import hashlib
import json
import pathlib
import shlex
import subprocess

import jsonschema

E = pathlib.Path('.agent/evidence/120')
QA1 = '32655c54392e2f98a895aa0166c9e1e2b33cd935'
QA2 = '1aa764afe390df82ade75d912096b27472b77f37'
BUNDLE = '0edf4c64496e145d4b936292d72e6f14827ce845'
ANCHOR = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
APPROVED = '3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
def read(path): return json.loads(pathlib.Path(path).read_bytes())
def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(rev, path): return subprocess.check_output(['git', 'show', rev + ':' + path])
def strict(path):
    value = read(path)
    assert value['final_verdict']['approved'] is True, path
    assert all(type(value[key]) is list and value[key] == [] for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
    return value
def pins(rev, path, per_file_revision=False):
    value = json.loads(blob(rev, path))
    for name, pin in value['files'].items():
        selected = pin['revision'] if per_file_revision else rev
        data = blob(selected, name)
        assert sha(data) == pin['sha256'] and git('rev-parse', selected + ':' + name) == pin['git_blob'], name
    return value

contract = read('.agent/contracts/120.json')
assert contract['status'] == 'approved' and sha(pathlib.Path('.agent/contracts/120.json').read_bytes()) == APPROVED
assert contract['approvals']['validator_mode_a'] is True and contract['approvals']['evaluator_contract_review'] is True
gates = ['.agent/validator/120-mode-a-rev2.json', '.agent/qa/120-contract-review-rev2.json', '.agent/qa/120-provisional-bundle-review-rev2.json', '.agent/qa/120-bundle-review.json', '.agent/validator/120-mode-b.json', '.agent/qa/120.json']
verdicts = [strict(path) for path in gates]
assert verdicts[0]['contract_sha256'] == verdicts[1]['proposal_sha256'] == contract['approval_evidence']['proposal_sha256']
assert all(value['approved_contract_sha256'] == APPROVED for value in verdicts[2:])
q = verdicts[-1]
jsonschema.validate(q, read('.nizam/schema/qa_verdict.schema.json'))
assert q['qa_pass'] is True and type(q['checks_run']) is int and q['checks_run'] == q['checks_passed'] == 11
assert q['adversarial']['performed'] is True and q['adversarial']['logical_checks'] == 1 and q['adversarial']['executions'] == 2
assert q['mandatory_evidence_commit'] == QA1
assert all(pathlib.Path(path).is_file() for path in q['evidence_files'])
bundle = pins(BUNDLE, str(E / 'executable-review1-seal.json'), True)
assert len(bundle['files']) == 230 and len(bundle['identity_objects']) == 17
for oid, pin in bundle['identity_objects'].items():
    assert git('cat-file', '-t', oid) == pin['type'] == 'blob'
    data = subprocess.check_output(['git', 'cat-file', 'blob', oid])
    assert sha(data) == pin['sha256'] and len(data) == pin['size_bytes']
partial = pins(QA1, str(E / 'qa1/partial-manifest.json'))
final = pins(QA2, str(E / 'qa2/manifest.json'))
assert len(partial['files']) == 70 and len(final['files']) == 12
assert read(E / 'qa1/identity-before.json') == read(E / 'qa1/identity-after-partial.json')
before = read(E / 'qa1/identity-before.json')
assert before['installed_count'] == 239 and before['revision'] == q['mandatory_exercised_revision']
for path, pin in before['files'].items():
    current = pathlib.Path(path)
    assert current.is_file() and not current.is_symlink() and sha(current.read_bytes()) == pin['sha256'], path
    for revision in ('HEAD', q['approved_input'], q['mandatory_exercised_revision'], q['reviewed_revision']):
        assert git('rev-parse', revision + ':' + path) == pin['git_blob'], (revision, path)
subprocess.run(['git', 'merge-base', '--is-ancestor', q['approved_input'], q['reviewed_revision']], check=True)
summary = read(E / 'qa1/partial-summary.json')
assert len(summary['results']) == 19 and summary['mandatory_results_passed'] == 18
records = {row['name']: row for row in summary['results']}
assert len(records) == 19
for name, row in records.items():
    assert read(E / ('qa1/' + name + '.result.json')) == row
    assert type(row['exit_code']) is int and type(row['expected_exit_code']) is int
    assert row['environment_overrides']['PYTHONDONTWRITEBYTECODE'] == '1'
    assert pathlib.Path(row['stdout']).is_file() and pathlib.Path(row['stderr']).is_file()
    if name == 'adversarial':
        assert row['exit_code'] == 1 and row['passed'] is False
        assert 'GuardDenied' in pathlib.Path(row['stderr']).read_text()
    else:
        assert row['passed'] is True and row['exit_code'] == row['expected_exit_code'], name
commands = [value['command'] for value in contract['verification']]
assert [value['command'] for value in q['checks']] == commands
for command, check in zip(commands, q['checks']):
    argv = shlex.split(command)
    assert argv.pop(0) == 'PYTHONDONTWRITEBYTECODE=1'
    row = read(check['evidence'])
    assert row == records['case-' + argv[-1]] and row['argv'] == argv and row['exit_code'] == 0
    assert check['evidence_commit'] == QA1 and row['revision'] == q['mandatory_exercised_revision']
    assert pathlib.Path(row['stdout']).read_text().splitlines() == ['PASS ' + argv[-1]]
ci = read(E / 'ci2-receipt.json')
assert ci['passed'] is True and ci['default37_passed'] is True and ci['exit_code'] == 0
assert len(ci['all37_ordered']) == 37 and ci['new11'] == [shlex.split(command)[-1] for command in commands]
assert pathlib.Path(records['default37']['stdout']).read_text().splitlines() == ['PASS ' + name for name in ci['all37_ordered']]
assert records['historical-foundation']['revision'] == ANCHOR and records['historical-foundation']['exit_code'] == 0
assert 'PASS foundation-ready:' in pathlib.Path(records['historical-foundation']['stdout']).read_text()
assert records['live-stale-foundation']['exit_code'] == 1
assert 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in pathlib.Path(records['live-stale-foundation']['stderr']).read_text()
for name in ('compliance-default', 'compliance-payload'):
    assert records[name]['exit_code'] == 0 and '0 failed' in pathlib.Path(records[name]['stdout']).read_text()
spot = read(E / 'qa2/adversarial.result.json')
assert spot['exit_code'] == 0 and spot['passed'] is True and spot['revision'] == q['reviewed_revision']
assert 'PASS exactly one independent command-nonexecution spot:' in pathlib.Path(spot['stdout']).read_text()
assert sha(pathlib.Path(ci['raw_log']).read_bytes()) == ci['raw_log_sha256']
for path, pin in ci['source_bindings'].items():
    assert sha(pathlib.Path(path).read_bytes()) == pin['sha256'] and git('rev-parse', 'HEAD:' + path) == pin['git_blob']
assert all(row['actual_exit'] == 0 for row in read(E / 'ci2-fetch-results.json'))
parser = read(E / 'ci2-parser-result.json')
assert parser['actual_exit'] == 0 and parser['helper_sha256'] == sha((E / 'capture-hosted.py').read_bytes())
installed = [path for path in git('ls-files', '-z', '.nizam/').split('\0') if path]
assert len(installed) == 239
for path in installed:
    assert pathlib.Path(path).read_bytes() == blob('92fecd8d376964f5e3dd7e34bc201035acfe8bc6', path)
provenance = read('.nizam/provenance.json')
assert provenance['framework_version'] == '1.5.0' and provenance['resolved_sha'] == 'f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852'
assert read('.agent/evidence/phase018-preflight/activation-result.json')['passed'] is True
failures = ['source-release1-failure.json', 'source1-failure.json', 'executable-review1-verifier1.json', 'ci1-validate-log.stdout.txt', 'qa1/adversarial.result.json']
for path in failures: assert (E / path).is_file(), path
result = {'role': 'Root', 'feature': '120', 'attempt': 1, 'passed': True, 'actual_exit': 0, 'revision': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'), 'approved_contract_sha256': APPROVED, 'strict_gates': gates, 'final_bundle_revision': BUNDLE, 'verified_bundle_files': 230, 'verified_retained_blobs': 17, 'qa_mandatory_revision': q['mandatory_exercised_revision'], 'qa_spot_revision': q['reviewed_revision'], 'qa_evidence_commits': [QA1, QA2], 'qa_sealed_files': [70, 12], 'actual_QA_commands': 20, 'mandatory_results': 18, 'exact_commands': commands, 'current_default_cases': 37, 'historical_foundation_revision': ANCHOR, 'live_stale_exit': 1, 'independent_adversarial': {'logical_checks': 1, 'executions': 2, 'original_helper_failure_preserved': True}, 'source_commit': q['source_commit'], 'test_commit': q['test_commit'], 'hosted_receipt': str(E / 'ci2-receipt.json'), 'installed_count': 239, 'installed_provenance': provenance, 'preserved_failure_paths': [str(E / path) for path in failures], 'boundary': 'Evidence gate before canonical120 completion. Aligned-record API library only; live Root binding migration unapplied. No controls-ready123, full runtime, release or comparative claim.'}
(E / 'evidence-capture.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS final120 evidence: six strict gates,230+17 bundle pins,70+12 QA pins,20 actual QA commands,hosted37 and installed239')
