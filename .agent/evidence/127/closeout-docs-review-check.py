import hashlib, json, re, subprocess
from pathlib import Path
import jsonschema, yaml

CANDIDATE = '0c79284baf5a1c624cb4afcf9ec597ac2895b268'
BASE = '12436dd6a5f3407786d575ff1bd32be6fdbca198'
SOURCE = '88996ee9405f9467ff2debd6e3115b34d064019a'
def git(*args):
    return subprocess.check_output(['git', *args])
def data(path):
    return json.loads(Path(path).read_text())
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE
assert data('.agent/contracts/127.json')['status'] == 'approved'
schema = data('.nizam/schema/frontmatter.schema.json')
docs = {}
for name, marker, version in [
    ('ROADMAP', '## Current position — phase 016, 2026-10-14', '0.65.3'),
    ('HANDOVER', '## Current handoff — feature 126, 2026-10-14', '1.0.16')]:
    path = Path('docs/planning') / (name + '.md')
    current, old = path.read_bytes(), git('show', BASE + ':' + str(path))
    boundary = marker.encode()
    assert current[current.index(boundary):] == old[old.index(boundary):]
    text = current.decode()
    front = yaml.safe_load(text.split('---', 2)[1])
    previous = yaml.safe_load(old.decode().split('---', 2)[1])
    jsonschema.validate(front, schema)
    assert front['version'] == front['change_log'][0]['version'] == version
    assert front['change_log'][1:] == previous['change_log']
    for key in previous:
        if key not in ('version', 'change_log'):
            assert front[key] == previous[key]
    overlay = text[text.index('## Current '):text.index(marker)]
    links = re.findall(r'\]\(([^)]+)\)', overlay)
    for link in links:
        if not link.startswith('https://'):
            assert (path.parent / link.split('#')[0]).resolve().is_file(), link
        else:
            assert link == 'https://github.com/niq-cnr/nizam-framework/pull/98'
    for claim in ['5,650/7,345', '5,203/7,020', 'v1.5.0', '017 → 016 → 018 → 020 → 019',
                  '127 only', '128 — core evidence and close', 'partial stub scope',
                  'Full adapter, SBCL runtime, fresh phase-020 acceptance and final CI 131 remain pending',
                  'unmeasured and makes no superiority claim']:
        assert claim in overlay, claim
    docs[str(path)] = {'sha256': sha(current), 'historical_boundary': marker,
                       'historical_sha256': sha(current[current.index(boundary):]),
                       'history_byte_identical': True, 'links_checked': links, 'version': version}

cap, qa, ci = [data(p) for p in ['.agent/evidence/127/evidence-capture.json', '.agent/qa/127.json', '.agent/evidence/127/ci-c1-receipt.json']]
assert cap['passed'] and cap['revision'] == qa['source_revision'] == ci['source'] == SOURCE
assert cap['checks_captured'] == len(qa['checks']) == 14
assert cap['repository_checks_captured'] == len(qa['repository_checks']) == 2
assert qa['adversarial']['count'] == 1 and qa['adversarial']['exit_code'] == 0
assert qa['final_verdict']['approved'] and not any(qa[k] for k in ['issues', 'missing_acceptance_coverage', 'unsupported_claims'])
for check in qa['checks'] + qa['repository_checks']:
    record = data(check['evidence'])
    assert check['exit_code'] == record['exit_code'] == 0
    assert record['source_revision'] == SOURCE
    for stream in ['stdout', 'stderr']:
        assert sha(Path(record[stream]).read_bytes()) == record[stream + '_sha256']
assert data(qa['adversarial']['result_ref'])['exit_code'] == 0
assert qa['test_sha256'].startswith('3628f1b2')
assert ci['run'] == 38557965408 and len(ci['commands']) == 14
assert {x['command'] for x in ci['commands']} == {x['command'] for x in qa['checks']}
assert all(x['actual_exit'] == 0 for x in ci['commands'])
raw_ci = Path(ci['raw_log']).read_text()
for check in ci['commands']:
    segment = raw_ci.split('COMMAND: ' + check['command'] + '\n', 1)[1].split('COMMAND:', 1)[0]
    assert 'ACTUAL_EXIT: 0' in segment
for path, expected in cap['source_sha256'].items():
    assert sha(Path(path).read_bytes()) == sha(git('show', SOURCE + ':' + path)) == expected
    assert sha(git('show', ci['checkout'] + ':' + path)) == expected
assert cap['source_sha256'] == ci['source_sha256']
assert sha(Path(cap['qa_ref']).read_bytes()) == cap['qa_sha256']

old_cap, old_qa, old_ci = [data(p) for p in ['.agent/evidence/126/evidence-capture.json', '.agent/qa/126.json', '.agent/evidence/126/ci-c3-receipt.json']]
assert old_cap['passed'] and old_qa['qa_pass']
assert old_qa['source_revision'].startswith('d965c2c') and old_qa['test_lines'] == 795
assert len(old_qa['checks']) == len(old_ci['commands']) == 9
assert all(x['actual_exit'] == 0 for x in old_ci['commands'])
assert old_qa['adversarial']['count'] == 1
assert data('.agent/evidence/126/pr97-merge-receipt.json')['merge'].startswith('c2b95a1')
main_ci = data('.agent/evidence/126/pr97-main-ci.json')['run']
assert main_ci['databaseId'] == 38551059606 and main_ci['conclusion'] == 'success'
assert len(main_ci['jobs']) == 5 and all(x['conclusion'] == 'success' for x in main_ci['jobs'])
fl, state = data('.agent/feature_list_016.json'), data('.agent/run_state.json')
assert (fl['original_estimate_lines'], fl['ceiling_130pct']) == (5650, 7345)
assert (state['scope_budget']['original_estimate_lines'], state['scope_budget']['ceiling_130pct']) == (5650, 7345)
assert (state['phase_017_scope_budget_final']['total_lines_changed'], state['phase_017_scope_budget_final']['ceiling_130pct']) == (5203, 7020)
assert {(x['case'], x['layer']) for x in fl['case_matrix']} == {(1,'live'), (2,'live'), (3,'live'), (5,'live'), (6,'live'), (8,'policy'), (9,'live'), (10,'live'), (13,'live')}
assert all(x['runtime'] == 'stub' and x['proof_kind'] == 'live' for x in fl['case_matrix'])
assert next(x for x in fl['features'] if x['id'] == '128')['status'] == 'pending'
assert data('.nizam/NIZAM.json')['framework']['version'] == '1.5.0'
assert not git('diff', BASE, CANDIDATE, '--', '.nizam', 'tools', '.agent/run_state.json', 'docs/planning/phase_016.yaml', 'docs/planning/phase_017.yaml')
subprocess.run(['git', 'diff', '--check', BASE, CANDIDATE], check=True)
print(json.dumps({'candidate': CANDIDATE, 'base': BASE, 'source': SOURCE, 'passed': True, 'documents': docs,
                  'checks': ['frontmatter/schema/version/history', 'historical-suffix-byte-equality', 'overlay-links', 'QA14+2+1', 'actual-CI14-zero', 'source/test/checkout-hashes', '126-historical-facts', 'case-matrix/next128', 'budgets/installed-pin', 'protected-paths/whitespace'],
                  'boundary': 'Documentation factual review only; existing recorded runtime evidence inspected without runtime rerun.'}, indent=2))
