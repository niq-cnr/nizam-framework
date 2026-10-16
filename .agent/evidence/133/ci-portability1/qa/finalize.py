"""Inspect completed receipts and write this independent QA handoff once."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
import jsonschema

repo = Path('/home/cnross/.tmp/nizam-133-portability-freshqa1')
raw = Path('/home/cnross/.tmp/nizam-133-portability-freshqa1-raw')
base = Path('.agent/evidence/133/ci-portability1/qa')
destination = repo / base
head = 'ab2ad3d6a352d5482867bcd0d06341843708d921'
assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == head
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
selectors = ['real-git-count-reduction', 'semantic-equivalence', 'fresh-mutations', 'literal-paths-and-modes']
versions = ['3.12.3', '3.13.13', '3.14.3']
bindings = {p: sha(repo / p) for p in ['tools/workflow_assurance.py', 'tools/test_receipt_candidate_batching.py', 'tools/fixtures_self_test.sh', '.agent/contracts/133.json', '.agent/evidence/123/fresh-qa-capture1.py']}
assert list(bindings.values()) == ['5f5e15df384e9ef41e934f644b7a218717be680ed1cec99f68c6129e1072ee9d', 'd4d2e4df39ffabc24135d414e478c417bfab28a8914aaa6d91a90fe0ebb0bc44', '098641d301c50cfa2815cffc3d49380e6a6c398b29e860e67713edc76dcb338e', 'af3dce10147b7cc79af35ca02f681cf896d2a0821b2a219a9e703e5e7d308899', 'e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0']
summaries = sorted(raw.glob('*.capture-summary.json'))
assert len(summaries) == 22
for path in summaries:
    summary = json.loads(path.read_text())
    assert summary['success'] and summary['preservation_equal'] and summary['actual_exit'] == 0
    before = json.loads(gzip.decompress(Path(summary['before']['path']).read_bytes()))
    after = json.loads(gzip.decompress(Path(summary['after']['path']).read_bytes()))
    assert before == after and before['head'] == head and len(before['rows']) == 14909
    assert sum(r['path'].startswith('.nizam/') for r in before['rows']) == 239
frames = sorted(raw.glob('*.execution.json'))
assert len(frames) == 35
for path in frames:
    frame = json.loads(path.read_text())
    assert frame['exercised_revision'] == head and not frame['timed_out'] and frame.get('child_pid', frame.get('pid', 0)) > 0
    for kind in ['stdout', 'stderr']:
        item = frame[kind]
        stream = Path(item['path'])
        if not stream.is_absolute(): stream = raw / stream
        assert len(stream.read_bytes()) == item['bytes'] and sha(stream) == item['sha256']
    expected = 1 if path.name.startswith('guard-') and not path.name.endswith('-body-only.execution.json') and path.name != 'guard-controls.execution.json' else 0
    assert frame['actual_exit'] == expected, path
runtime = []
checks = []
for index, version in enumerate(versions):
    identity = json.loads((raw / ('runtime-' + str(index) + '.stdout.txt')).read_text())
    assert identity['version'] == version
    identity['evidence'] = str(base / ('runtime-' + str(index) + '.execution.json'))
    runtime.append(identity)
    for selector in selectors:
        name = 'python-' + str(index) + '-' + selector
        labels = [line for line in (raw / (name + '.stdout.txt')).read_text().splitlines() if line.startswith('PASS ')]
        assert labels == ['PASS ' + selector]
        frame = json.loads((raw / (name + '.execution.json')).read_text())
        checks.append(dict(name=name, command=frame['argv'], exit_code=0, evidence=str(base / (name + '.execution.json')), runtime_evidence=identity['evidence']))
for name in ['guard-controls', 'default-four', 'validate-default', 'validate-payload', 'self-governance', 'self-governance-negatives']:
    frame = json.loads((raw / (name + '.execution.json')).read_text())
    checks.append(dict(name=name, command=frame['argv'], exit_code=0, evidence=str(base / (name + '.execution.json'))))
assert [line for line in (raw / 'default-four.stdout.txt').read_text().splitlines() if line.startswith('PASS ')] == ['PASS ' + name for name in selectors]
assert 'PASS independent-full-fingerprint-and-body-mask-controls' in (raw / 'guard-controls.stdout.txt').read_text().splitlines()
assert 'SELF-GOVERNANCE TESTS PASS: 10 drift negatives; real installation preserved' in (raw / 'self-governance-negatives.stdout.txt').read_text().splitlines()
assert 'PASS adversarial-cwd-decoy' in (raw / 'adversarial-extra.stdout.txt').read_text().splitlines()
destination.mkdir(parents=True, exist_ok=False)
for path in sorted(raw.iterdir()):
    assert path.is_file()
    shutil.copyfile(path, destination / path.name)
shutil.copyfile(raw / 'adversarial-extra.stdout.txt', destination / '133-qa-adversarial.txt')
verdict = dict(feature_id='133', role='Distinct fresh Evaluator /root/portability_freshqa133; no author, Generator or bundle-review role', root_release='267e40c0', exercised_revision=head, source_candidate='7f080b16af45c72a852f77acce387c87961e6586', executed_at=datetime.now(timezone.utc).isoformat(), qa_pass=True, checks_run=len(checks), checks_passed=len(checks), checks=checks, source_bindings=bindings, runtimes=runtime, preservation=dict(outer_commands=22, inventories=44, physical_rows=14909, installed_files=239, all_equal=True, frames=35, guard_expected_exit1=9, index=str(base / 'index.json')), adversarial=dict(performed=True, count=1, description='Actual Python3.14.3 absolute runner invocation from an owned outside cwd containing a trap workflow_assurance.py. Required successful real-Git count check from sibling API, no trap execution, exact PASS/0 and fixed source hash.', result='pass', evidence=str(base / '133-qa-adversarial.txt'), execution=str(base / 'adversarial-extra.execution.json'), child_execution=str(base / 'adversarial-cwd-decoy.execution.json')), evidence_files=[c['evidence'] for c in checks] + [str(base / 'adversarial-extra.execution.json'), str(base / '133-qa-adversarial.txt'), str(base / 'index.json')], issues=[], unsupported_claims=[], missing_acceptance_coverage=[], required_fixes=[], scope='Targeted portability QA under Root recovery-plan bounded procedural override: unchanged local Workflow Assurance48/full fixture bank deliberately not rerun. Original eight-command QA remains historical;18 scoped checks plus exactly one extra approved here. Nine guard rejections are expected valid-AST outside-body controls; three body-only mask controls succeed.', limitations='Local actual3.14.3 is not hosted3.14.8. This approves only the runner portability delta. Root capture, all six fresh exact-head PR checks with qualified full logs/clear feedback, normal merge and matching-main five checks remain required. No cost-budget recovery or new comparative-performance claim.', final_verdict=dict(approved=True, summary='All18 scoped checks and exactly one independent adversarial extra pass; immutable source/test bindings and every full preservation snapshot match.'), dod_ref='.nizam/standard/definition_of_done.md')
jsonschema.validate(verdict, json.loads((repo / '.nizam/schema/qa_verdict.schema.json').read_text()))
index = {str(base / path.name): dict(sha256=sha(path), bytes=path.stat().st_size) for path in sorted(destination.iterdir())}
(destination / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
(repo / '.agent/qa/133-ci-portability1.json').write_text(json.dumps(verdict, indent=2) + '\n')
print(json.dumps(dict(checks=18, extra=1, frames=35, indexed_files=len(index), qa_sha256=sha(repo / '.agent/qa/133-ci-portability1.json'), index_sha256=sha(destination / 'index.json')), sort_keys=True))
