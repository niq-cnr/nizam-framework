"""Root final119 evidence gate; checks committed proof, never reruns behavior."""
import hashlib, json, pathlib, re, shlex, subprocess
import jsonschema
ROOT = pathlib.Path.cwd(); E = pathlib.Path('.agent/evidence/119')
def read(path): return json.loads(pathlib.Path(path).read_bytes())
def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def blob(rev, path): return subprocess.check_output(['git', 'show', rev + ':' + path])
def strict(path):
    d = read(path)
    assert d['final_verdict']['approved'] is True, path
    assert all(type(d[k]) is list and d[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), path
    return d

def seal(rev, path):
    rows = json.loads(blob(rev, path))['files']
    for p, v in rows.items():
        b = blob(rev, p)
        assert sha(b) == v['sha256'] and git('rev-parse', rev + ':' + p) == v['git_blob'], p
        if 'bytes' in v: assert len(b) == v['bytes'], p
    return {'revision': rev, 'path': path, 'verified_files': len(rows)}

contract_path = '.agent/contracts/119.json'; c = read(contract_path); approved_sha = sha(pathlib.Path(contract_path).read_bytes())
assert c['status'] == 'approved' and c['approvals']['validator_mode_a'] is True and c['approvals']['evaluator_contract_review'] is True
jsonschema.validate(c, read('.nizam/schema/contract.schema.json'))
gates = ['.agent/validator/119-mode-a-rev1.json', '.agent/qa/119-contract-review-rev1.json', '.agent/qa/119-provisional-bundle-review.json', '.agent/qa/119-bundle-review.json', '.agent/validator/119-mode-b.json', '.agent/qa/119.json']
verdicts = [strict(p) for p in gates]
assert verdicts[0]['contract_sha256'] == verdicts[1]['proposal_sha256'] == c['approval_evidence']['proposal_sha256']
assert all(d['approved_contract_sha256'] == approved_sha for d in verdicts[2:])
q = verdicts[-1]; jsonschema.validate(q, read('.nizam/schema/qa_verdict.schema.json'))
assert q['qa_pass'] is True and type(q['checks_run']) is int and q['checks_run'] == q['checks_passed'] == 6
assert q['adversarial']['performed'] is True and q['adversarial']['count'] == 1 and q['adversarial_check']['result'] == 'pass'
for p in q['evidence_files']: assert pathlib.Path(p).is_file(), p
seals = [seal('833b97b2116d630c4af937e23b7ad89eb442ee77', str(E/'author1-provisional-seal.json')), seal('d68c04b3fa28389b50f7b7d5f3003e1d85f17e31', str(E/'provisional-review1-seal.json')), seal('9a999591d64d05458d8dc650b00f05361516203f', str(E/'author1-executable-seal.json')), seal('cb9f97e828e8bf4082edc01de1b255304e0b0d63', str(E/'executable-review1-seal.json')), seal('89339bf594b4b645db98a108b1858359e30557fc', str(E/'qa1/manifest.json'))]
summary = read(E/'qa1/execution-summary.json'); results = summary['results']; by_name = {r['name']: r for r in results}
assert len(results) == len(by_name) == 14 and summary['all_commands_passed'] is True and summary['exactly_one_adversarial'] is True
assert summary['protected_identities_unchanged'] is True and summary['revision'] == q['reviewed_revision']
for r in results:
    assert type(r['exit_code']) is int and type(r['expected_exit_code']) is int and r['exit_code'] == r['expected_exit_code'] and r['passed'] is True, r['name']
    assert read(E/('qa1/'+r['name']+'.result.json')) == r, r['name']
    assert r['environment_overrides']['PYTHONDONTWRITEBYTECODE'] == '1'
    for p in (r['stdout'], r['stderr']): assert pathlib.Path(p).is_file(), p
commands = [v['command'] for v in c['verification']]
assert [v['command'] for v in q['checks']] == commands
for command, check in zip(commands, q['checks']):
    argv = shlex.split(command); assert argv.pop(0) == 'PYTHONDONTWRITEBYTECODE=1'
    r = read(check['evidence']); assert r == by_name['case-'+argv[-1]] and r['argv'] == argv and r['exit_code'] == 0
    assert pathlib.Path(r['stdout']).read_text().splitlines() == ['PASS '+argv[-1]]
old = [r['case'] for r in read('.agent/evidence/118/api-interface.json')['current_cases']]
new = [shlex.split(command)[-1] for command in commands]
assert len(old) == 20 and len(new) == 6
assert pathlib.Path(by_name['default26']['stdout']).read_text().splitlines() == ['PASS '+name for name in old+new]
anchor = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
historical = by_name['historical-foundation']; assert historical['revision'] == anchor and historical['exit_code'] == 0
assert 'PASS foundation-ready:' in pathlib.Path(historical['stdout']).read_text()
stale = by_name['live-stale-foundation']; assert stale['exit_code'] == 1
assert 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in pathlib.Path(stale['stderr']).read_text()
for name in ('compliance-default', 'compliance-payload'):
    assert by_name[name]['exit_code'] == 0 and '0 failed' in pathlib.Path(by_name[name]['stdout']).read_text()
extra = read(q['adversarial_check']['evidence']); assert extra['exit_code'] == 0 and extra['passed'] is True and extra['name'] == 'adversarial'
assert 'PASS one independent purity check:' in pathlib.Path(extra['stdout']).read_text()
before = read(E/'qa1/identity-before.json'); after = read(E/'qa1/identity-after.json'); assert before == after and before['revision'] == q['reviewed_revision'] and before['installed_count'] == 239
subprocess.run(['git', 'merge-base', '--is-ancestor', q['approved_input'], q['reviewed_revision']], check=True)
for path, row in before['files'].items():
    p = pathlib.Path(path); assert p.is_file() and not p.is_symlink() and sha(p.read_bytes()) == row['sha256'], path
    assert git('rev-parse', 'HEAD:'+path) == git('rev-parse', q['reviewed_revision']+':'+path) == row['git_blob'], path
hist_identity = read(E/'qa1/historical-identity.json'); assert hist_identity['revision'] == anchor
for path, row in hist_identity['files'].items(): assert sha(blob(anchor, path)) == row['sha256'] and git('rev-parse', anchor+':'+path) == row['git_blob'], path
ci = read(E/'ci2-receipt.json'); assert ci['passed'] is True and ci['all26_ordered'] == old+new and ci['exit_code'] == 0
assert sha(pathlib.Path(ci['raw_log']).read_bytes()) == ci['raw_log_sha256'] and ci['source_candidate'] == q['source_commit']
for path, row in ci['source_bindings'].items(): assert sha(pathlib.Path(path).read_bytes()) == row['sha256'] and git('rev-parse', 'HEAD:'+path) == row['git_blob'], path
parser = read(E/'ci2-parser-result.json'); assert parser['actual_exit'] == 0 and parser['helper_sha256'] == sha((E/'capture-ci2.py').read_bytes())
assert all(r['actual_exit'] == 0 for r in read(E/'ci2-fetch-results.json'))
installed = [p for p in subprocess.check_output(['git','ls-files','-z','.nizam/']).decode().split('\0') if p]; assert len(installed) == 239
base = 'fcd0584146fd836df0080292cc2cf10180bb9f31'
for path in installed:
    p = pathlib.Path(path); assert p.is_file() and not p.is_symlink() and p.read_bytes() == blob(base, path), path
provenance = read('.nizam/provenance.json'); assert provenance['framework_version'] == '1.5.0' and provenance['resolved_sha'] == 'f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852'
failures = [str(E/p) for p in ('precode-capture1-failure.json','author1-fixture-failure.json','ci1-failure.json','qa1-helper-attempt1-failure.txt')]
for p in failures: assert pathlib.Path(p).is_file(), p
assert read('.agent/evidence/phase018-preflight/activation-result.json')['passed'] is True
result = {'role':'Root','feature':'119','attempt':1,'passed':True,'actual_exit':0,'revision':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'approved_contract_sha256':approved_sha,'strict_gates':gates,'verified_seals':seals,'qa_commit':'89339bf594b4b645db98a108b1858359e30557fc','qa_exercised_revision':q['reviewed_revision'],'qa_actual_commands':14,'six_exact_commands':commands,'current_default_cases':26,'historical_foundation_revision':anchor,'live_stale_exit':1,'exactly_one_independent_adversarial':True,'source_commit':q['source_commit'],'test_commit':q['test_commit'],'hosted_receipt':str(E/'ci2-receipt.json'),'installed_count':239,'installed_provenance':provenance,'preserved_failure_paths':failures,'boundary':'Evidence gate passed before canonical119 completion. No phase018 close/120implementation/123fullCI/SBCL/comparison or release claim.'}
(E/'evidence-capture.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS final119 evidence: six strict gates, immutable seals,14 QA commands, hosted26, historical/stale controls and239 installed files')
