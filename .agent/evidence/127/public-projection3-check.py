"""Bounded factual/NDS/path/history proof for the feature127 public overlay."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml
from jsonschema import validate

BASE = 'db70886'
DOCS = {'docs/planning/ROADMAP.md': '0.65.2', 'docs/planning/HANDOVER.md': '1.0.15'}
report = {'base': BASE, 'exercised_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'documents': {}}
for filename, version in DOCS.items():
    path = Path(filename)
    before = subprocess.check_output(['git', 'show', f'{BASE}:{filename}'], text=True)
    after = path.read_text()
    fm = yaml.safe_load(after.split('---\n', 2)[1])
    validate(fm, json.loads(Path('.nizam/schema/frontmatter.schema.json').read_text()))
    assert fm['version'] == version and fm['authoritative_source'] == filename
    assert fm['change_log'][0]['version'] == version and fm['change_log'][0]['date'] == '2026-10-14'
    old_body = before.split('---\n', 2)[2]
    old_title, old_suffix = old_body.split('\n\n', 1)
    assert after.split('---\n', 2)[2].startswith(old_title + '\n\n')
    assert after.endswith(old_suffix), filename + ': historical suffix changed'
    overlay = after.split('---\n', 2)[2][len(old_title) + 2:-len(old_suffix)]
    assert len(overlay.splitlines()) == 14
    assert 'is selected for' in overlay and 'current gate/status follows [Root state]' in overlay
    assert 'preparation only' not in overlay and 'attempt 1 preparation' not in overlay
    links = re.findall(r'\]\(([^)]+)\)', overlay)
    for link in links:
        assert (path.parent / link).resolve().is_file(), link
    for needle in ('626ff419', 'd965c2c', '795', '1/2/3/8 (policy)/9/13', '3,003/7,345', '2,657', '346', '5,650', '5,203/7,020', '017 → 016 → 018 → 020 → 019', '127 only', 'unmeasured', 'historical snapshots'):
        assert needle in overlay, needle
    report['documents'][filename] = {'version': version, 'overlay_lines': 14, 'local_links_resolve': len(links), 'historical_suffix_sha256': hashlib.sha256(old_suffix.encode()).hexdigest(), 'document_sha256': hashlib.sha256(after.encode()).hexdigest()}
s = json.loads(Path('.agent/run_state.json').read_text())
f = json.loads(Path('.agent/feature_list_016.json').read_text())
assert [(v['id'], v['status']) for v in f['features']] == [('126', 'complete'), ('127', 'in_progress'), ('128', 'pending')]
b = s['scope_budget']
assert (b['original_estimate_lines'], b['ceiling_130pct'], b['total_lines_changed']) == (5650, 7345, 3003)
assert b['per_feature'][0]['actual'] == 2657 and sum(v['actual'] for v in b['phase_level_items']) == 346
capture = json.loads(Path('.agent/evidence/126/evidence-capture.json').read_text())
qa = json.loads(Path('.agent/qa/126.json').read_text())
ci = json.loads(Path('.agent/evidence/126/ci-c3-receipt.json').read_text())
assert capture['passed'] and capture['revision'].startswith('d965c2c')
assert qa['qa_pass'] and qa['checks_run'] == qa['checks_passed'] == 9 and qa['adversarial']['performed']
assert qa['test_lines'] == 795 and qa['test_sha256'].startswith('626ff419')
assert len(ci['commands']) == 9 and all(v['actual_exit'] == 0 for v in ci['commands'])
pr = json.loads(Path('.agent/evidence/126/pr97-merge-receipt.json').read_text())
main = json.loads(Path('.agent/evidence/126/pr97-main-ci.json').read_text())['run']
assert pr['merge'] == main['headSha'] == 'c2b95a1262d49ebd615dcd0d577fad584712dc40'
assert len(pr['checks']) == 6 and all(v['conclusion'] == 'success' for v in pr['checks'])
assert main['databaseId'] == 38551059606 and len(main['jobs']) == 5 and all(v['conclusion'] == 'success' for v in main['jobs'])
selection = json.loads(Path('.agent/evidence/127/selection.json').read_text())
assert selection['contract_attempt'] == 1  # Historical selection, not current attempt.
assert s['circuit_breaker']['127-public-projection']['attempts'] == 3
controller = json.loads(Path('.agent/feature_list_018.json').read_text())['cross_phase_prerequisites'][1]
assert controller['requires'] == ['127']
changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], text=True).splitlines()
assert {p for p in changed if not p.startswith('.agent/evidence/127/public-projection3-')} == set(DOCS), changed
contract = json.loads(Path('.agent/contracts/127.json').read_text())
assert contract['status'] == 'approved'
old = 'Required order: both independent pre-code gates and Root approval precede independent acceptance authoring, sealing/review and intended semantic red before source work; later Mode B, fresh QA, actual CI and capture remain required.'
new = 'Follow the [approved127 contract](../../.agent/contracts/127.json) for the authoritative acceptance authoring, executable-candidate controls, implementation, QA, CI and capture gates.'
for filename in DOCS:
    prior = subprocess.check_output(['git', 'show', '5be6c60:' + filename], text=True)
    expected = prior.replace(old, new, 1) if filename.endswith('HANDOVER.md') else prior
    assert Path(filename).read_text() == expected, filename + ': scope exceeds single HANDOVER line correction'
report['candidate2_delta'] = 'ROADMAP identical; HANDOVER only Required order line replaced by approved-contract gate pointer.'
report['approved_contract_sha256'] = hashlib.sha256(Path('.agent/contracts/127.json').read_bytes()).hexdigest()
report['canonical_facts_confirmed'] = True
numstat = subprocess.check_output(['git', 'diff', '--numstat', BASE, '--', *DOCS], text=True)
report['numstat'] = numstat.splitlines()
report['counted_document_lines'] = sum(int(v) for line in numstat.splitlines() for v in line.split('\t')[:2])
assert report['counted_document_lines'] == 38
prior = subprocess.check_output(['git', 'diff', '--numstat', 'e36aa45^', 'e36aa45', '--', *DOCS], text=True)
assert sum(int(v) for line in prior.splitlines() for v in line.split('\t')[:2]) == 38
report['candidate1_cost_correction'] = '38 lines, not previously stated40; no allowance change.'
report['boundary'] = 'Author proof only; distinct Validator approval required before promotion. No lifecycle, Root state, historical source, or installed payload changes.'
print(json.dumps(report, indent=2))
