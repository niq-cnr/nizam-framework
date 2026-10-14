"""Independent B2 seal and targeted semantic controls, before product repair."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path.cwd()
OUT = ROOT / '.agent/evidence/126/bundle-review-controls'
OUT.mkdir(exist_ok=True)
def read(path):
    return json.loads(Path(path).read_text())
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args])
seal_path = Path('.agent/evidence/126/test-seal-b2.json')
seal = read(seal_path)
entries = [seal['test'], seal['api'], seal['obligation_projection'], *seal['normative_inputs'],
           *seal['source_stub_harness_docs'], seal['exercised_manifest'],
           seal['transport_and_mutant_controls']['mutation'], seal['actual_c1_red']['record']]
for entry in entries:
    raw = Path(entry['path']).read_bytes()
    assert sha(raw) == entry['sha256'], entry['path']
    assert git('hash-object', entry['path']).decode().strip() == entry['git_blob']
    if 'revision' in entry:
        assert git('show', entry['revision'] + ':' + entry['path']) == raw
assert sha(Path('.agent/contracts/126.json').read_bytes()) == seal['contract_sha256']
assert git('rev-parse', seal['c1_commit'] + '^{tree}').decode().strip() == seal['c1_tree']
# Raw control records and outputs are anchored to the immutable proof commit.
for path in Path('.agent/evidence/126/semantic-controls').iterdir():
    if path.is_file():
        assert git('show', seal['proof_revision'] + ':' + str(path)) == path.read_bytes(), str(path)
previous = read('.agent/evidence/126/test-seal-b0-2.json')
assert previous['test']['sha256'] == seal['test']['sha256']
assert previous['api']['sha256'] == seal['api']['sha256']
assert previous['normative_inputs'] == seal['normative_inputs']
print('PASS sealed source/test/API/projection/normative identities and immutable proof records')

# Reexecute the inspected immutable helpers with output paths redirected only.
# Product, mutant definition, assertions and sealed tests remain byte-identical.
for name in ('run-c1-controls.py', 'inspect-c1-case9.py'):
    original = Path('.agent/evidence/126/semantic-controls') / name
    source = original.read_text().replace('.agent/evidence/126/semantic-controls', '.agent/evidence/126/bundle-review-controls')
    target = OUT / name
    target.write_text(source)
    proc = subprocess.run([sys.executable, str(target)], capture_output=True, text=True,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=60)
    (OUT / (name + '.stdout.txt')).write_text(proc.stdout)
    (OUT / (name + '.stderr.txt')).write_text(proc.stderr)
    (OUT / (name + '.execution.json')).write_text(json.dumps({'command': [sys.executable, str(target)], 'cwd': str(ROOT), 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'actual_exit': proc.returncode, 'original_helper': str(original), 'original_sha256': sha(original.read_bytes()), 'adaptation': 'Evidence destination paths only; product/test/mutation/assertions unchanged.', 'stdout': str((OUT / (name + '.stdout.txt')).relative_to(ROOT)), 'stderr': str((OUT / (name + '.stderr.txt')).relative_to(ROOT))}, indent=2) + '\n')
    assert proc.returncode == 0, proc.stderr
    print(proc.stdout, end='')
results = [read(OUT / (n + '.result.json')) for n in ('01-unmodified-positive', '02-foreign-owner-mutant', '03-fresh-unmodified-positive')]
assert [r['actual_exit'] for r in results] == [0, 1, 0]
assert 'BEHAVIOR_ASSERTION: submit-operation exit 0, expected 1:' in (OUT / '02-foreign-owner-mutant.stderr.txt').read_text()
inspection = read(OUT / 'case9-record-inspection.json')
assert [inspection['results'][n]['actual_exit'] for n in ('current', 'rejected')] == [0, 1]
assert inspection['executed'] is False and inspection['observed_current_attempt'] == 1 and inspection['observed_previous_attempt'] == 2
manifest = read(OUT / 'manifest.json')
with tempfile.TemporaryDirectory(prefix='n126-review-c9-') as home:
    candidate = Path(home)
    for name, identity in manifest['files'].items():
        raw = git('show', seal['c1_commit'] + ':' + name)
        assert sha(raw) == identity['sha256']
        dest = candidate / name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(raw)
    command = [sys.executable, 'tools/test_runtime_session.py', '--case', '9', '--runtime', 'stub']
    p = subprocess.run(command, cwd=candidate, capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=45)
    (OUT / 'exact-case9.stdout.txt').write_text(p.stdout); (OUT / 'exact-case9.stderr.txt').write_text(p.stderr)
    (OUT / 'exact-case9.result.json').write_text(json.dumps({'command': command, 'cwd': str(candidate), 'actual_exit': p.returncode, 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'source_commit': seal['c1_commit'], 'manifest': str((OUT / 'manifest.json').relative_to(ROOT)), 'stdout': str((OUT / 'exact-case9.stdout.txt').relative_to(ROOT)), 'stderr': str((OUT / 'exact-case9.stderr.txt').relative_to(ROOT))}, indent=2) + '\n')
    assert p.returncode == 1 and 'BEHAVIOR_ASSERTION: existing C12 relations:' in p.stderr and 'runtime_operation:attempt_continuity' in p.stderr and 'SETUP' not in p.stderr
    print('CONFIRMED exact sealed case9 actual_exit=1: C12 attempt_continuity; no setup failure')
print('B2 REVIEW CONTROL PASS; C1 product remains failing and unrepaired.')
