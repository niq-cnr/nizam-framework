"""Independent bounded documentation review; no product acceptance execution."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml
import jsonschema

CANDIDATE = 'e36aa45a2d603836e5b2fe1c358791ddcc25bfc6'
BASE = '58bc675c5ee4e845f8069893f08a77bd52002a78'
def git(*args):
    return subprocess.check_output(['git', *args])
def load(path):
    return json.loads(Path(path).read_bytes())
def digest(data):
    return hashlib.sha256(data).hexdigest()
def checked_hash(path, expected):
    assert digest(Path(path).read_bytes()) == expected, path

assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE
schema = load('.nizam/schema/frontmatter.schema.json')
report = {'candidate': CANDIDATE, 'base': BASE, 'documents': {}}
for path, expected in [('docs/planning/ROADMAP.md', '0.65.2'), ('docs/planning/HANDOVER.md', '1.0.15')]:
    old = git('show', BASE + ':' + path)
    new = Path(path).read_bytes()
    oldfm, oldbody = old.split(b'---\n', 2)[1:]
    newfm, newbody = new.split(b'---\n', 2)[1:]
    before, after = yaml.safe_load(oldfm), yaml.safe_load(newfm)
    jsonschema.validate(after, schema)
    assert after['version'] == expected
    assert after['status'] == before['status'] == 'active'
    assert after['authoritative_source'] == path
    assert after['change_log'][0]['version'] == expected
    assert after['change_log'][0]['date'] == '2026-10-14'
    assert after['change_log'][1:] == before['change_log']
    stripped = dict(after); stripped['version'] = before['version']; stripped['change_log'] = before['change_log']
    assert stripped == before, 'unexpected frontmatter alteration'
    oldtitle, suffix = oldbody.split(b'\n\n', 1)
    assert newbody.startswith(oldtitle + b'\n\n') and newbody.endswith(suffix)
    overlay = newbody[len(oldtitle) + 2:-len(suffix)].decode()
    assert len(overlay.splitlines()) == 14
    assert 'historical snapshots' in overlay and 'older' in overlay
    links = re.findall(r'\]\(([^)]+)\)', overlay)
    for link in links:
        assert (Path(path).parent / link).resolve().is_file(), link
    assert '**contract attempt 1 preparation only**' in overlay
    assert '1/2/3/8 (policy)/9/13' in overlay and 'full adapter and SBCL acceptance remain pending' in overlay
    for token in ['3,003/7,345', '2,657', '346', '5,650', '5,203/7,020', 'v1.5.0', '017 → 016 → 018 → 020 → 019', '127 only', 'unmeasured', 'no superiority claim']:
        assert token in overlay, token
    report['documents'][path] = {'version': expected, 'sha256': digest(new), 'historical_suffix_bytes': len(suffix), 'historical_suffix_sha256': digest(suffix), 'overlay_lines': 14, 'resolved_links': links}
changed = git('diff', '--name-only', BASE, CANDIDATE).decode().splitlines()
assert sorted(p for p in changed if not p.startswith('.agent/evidence/127/public-projection-')) == sorted(report['documents'])
nums = git('diff', '--numstat', BASE, CANDIDATE, '--', *report['documents']).decode().splitlines()
assert sum(sum(map(int, row.split()[:2])) for row in nums) == 38
report['counted_document_lines'] = 38

capture = load('.agent/evidence/126/evidence-capture.json')
qa = load('.agent/qa/126.json')
ci = load('.agent/evidence/126/ci-c3-receipt.json')
feature = load('.agent/feature_list_016.json')
assert capture['passed'] and capture['revision'].startswith('d965c2c')
checked_hash(capture['qa_ref'], capture['qa_sha256'])
checked_hash(capture['mode_b_ref'], capture['mode_b_sha256'])
checked_hash(capture['bundle_ref'], capture['bundle_sha256'])
for path, sha in capture['source_sha256'].items():
    checked_hash(path, sha)
    identity_revision = capture['test_revision'] if path == 'tools/test_runtime_session.py' else capture['revision']
    assert digest(git('show', identity_revision + ':' + path)) == sha
for path, sha in capture['evidence_sha256'].items():
    checked_hash(path, sha)
assert len(Path('tools/test_runtime_session.py').read_bytes().splitlines()) == qa['test_lines'] == 795
assert qa['test_sha256'].startswith('626ff419')
assert qa['source_revision'] == capture['revision'] == ci['source']
assert qa['qa_pass'] and qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == 9
assert qa['final_verdict']['approved'] and not any(qa[k] for k in ['issues','unsupported_claims','missing_acceptance_coverage'])
for check in qa['checks']:
    assert check['exit_code'] == 0 and check['source_revision'] == capture['revision']
    for key in ['stdout','stderr','evidence']:
        checked_hash(check[key], check[key + '_sha256'])
assert qa['adversarial']['performed'] and qa['adversarial']['count'] == 1 and qa['adversarial']['exit_code'] == 0
adv = load(qa['adversarial']['result_ref'])
assert adv['actual_exit_code'] == 0
for key in ['stdout','stderr']:
    checked_hash(adv[key], adv[key + '_sha256'])
assert len(ci['commands']) == 9 and all(c['actual_exit'] == 0 for c in ci['commands'])
assert {c['command'] for c in ci['commands']} == set(feature['features'][0]['acceptance_tests'])
log = Path(ci['raw_log']).read_text()
assert all('COMMAND: ' + c['command'] in log for c in ci['commands'])
assert 'CONFORMANCE: FULL' in log and ci['environment']['environment']['RUNNER_OS'] == 'Linux'
pr = load('.agent/evidence/126/pr97-merge-receipt.json')
main = load('.agent/evidence/126/pr97-main-ci.json')
assert pr['number'] == 97 and pr['merge'] == main['run']['headSha'] == 'c2b95a1262d49ebd615dcd0d577fad584712dc40'
assert len(pr['checks']) == 6 and all(c['status'] == 'completed' and c['conclusion'] == 'success' for c in pr['checks'])
assert main['actual_api_exit'] == 0 and main['run']['databaseId'] == 38551059606
assert len(main['run']['jobs']) == 5 and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in main['run']['jobs'])
report['receipts'] = {'capture_passed': True, 'source': capture['revision'], 'test_lines': 795, 'test_sha256': qa['test_sha256'], 'qa_checks': 9, 'independent_adversarial_checks': 1, 'actual_hosted_commands': 9, 'capture_evidence_hashes_verified': len(capture['evidence_sha256']), 'merge': pr['merge'], 'head_checks_green': 6, 'main_run': main['run']['databaseId'], 'main_jobs_green': 5}

state = load('.agent/run_state.json'); budget = state['scope_budget']
assert (budget['original_estimate_lines'],budget['ceiling_130pct'],budget['total_lines_changed']) == (5650,7345,3003)
assert budget['per_feature'][0]['actual'] == 2657
assert sum(x['actual'] for x in budget['phase_level_items']) == 346
archived = state['phase_017_scope_budget_final']
assert archived['total_lines_changed'] == 5203 and archived['ceiling_130pct'] == 7020
assert [(f['id'],f['status']) for f in feature['features']] == [('126','complete'),('127','in_progress'),('128','pending')]
selection = load('.agent/evidence/127/selection.json')
assert selection['contract_attempt'] == 1 and selection['base_revision'] == pr['merge']
assert load('.agent/evidence/127/orchestration-next.json')['stage'] == '127 contract1 preparation only'
assert budget['feature127_measurement_base'] == pr['merge']
assert load('.agent/feature_list_018.json')['cross_phase_prerequisites'][1]['requires'] == ['127']
assert load('.nizam/NIZAM.json')['framework']['version'] == '1.5.0'
proposal = Path('docs/planning/agentic-excellence.md').read_text()
assert 'remain unmeasured' in proposal
report['boundaries'] = {'scope': 'Only current overlays and frontmatter; all prior bodies retained as byte-identical suffixes.', 'snapshot': '127 contract attempt 1 preparation; 128 pending; no implementation or gate approval.', 'acceptance': '126 partial stub cases 1/2/3/8 policy/9/13 only; future timeout/replay/SBCL/full adapter/fresh acceptance and benchmark claims not accepted.', 'accounting': '38 counted lines once within feature127 from c2b95a1; 3003/7345 snapshot retained, no separate allowance.', 'preservation': 'No source, acceptance, requirements, budgets, lifecycle, circuit, contracts, phase history, installed payload or comparator changes.'}
print(json.dumps(report, indent=2))
