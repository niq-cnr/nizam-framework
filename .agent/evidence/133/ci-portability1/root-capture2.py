"""Read-only Root admission of independently executed portability QA."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

r = Path('/home/cnross/.tmp/nizam-133-portability-freshqa1')
p = r / '.agent/evidence/133/ci-portability1/qa'
sha = lambda b: hashlib.sha256(b).hexdigest()
vp = r / '.agent/qa/133-ci-portability1.json'
assert sha(vp.read_bytes()) == 'f68d8c25a75fa61cf1fd39a9af70bc421820615945faceaf3ec4ad3f06e6c930'
v = json.loads(vp.read_text())
assert v['qa_pass'] is True and v['final_verdict']['approved'] is True
for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims', 'required_fixes'):
    assert v[k] == []
assert v['checks_run'] == v['checks_passed'] == len(v['checks']) == 18
assert v['adversarial']['performed'] and v['adversarial']['count'] == 1
idx = p / 'index.json'
assert sha(idx.read_bytes()) == '19cface42f39684976baba4db4bceed8c481afb8341799aec7b3b6ef58945d98'
rows = json.loads(idx.read_text())
assert len(rows) == 242
for name, rec in rows.items():
    b = (r / name).read_bytes()
    assert sha(b) == rec['sha256'] and len(b) == rec['bytes'], name
frames = list(p.glob('*.execution.json'))
assert len(frames) == 35
negatives = 0
for path in frames:
    f = json.loads(path.read_text())
    assert f['exercised_revision'] == v['exercised_revision']
    assert f.get('child_pid', f.get('pid', 0)) > 0 and f['timed_out'] is False
    expected = 1 if path.name.startswith('guard-') and path.name.split('.')[0].split('-')[-1] in ('global', 'helper', 'signature') else 0
    assert f['actual_exit'] == expected, (path, f['actual_exit'])
    negatives += expected
    for key in ('stdin', 'stdout', 'stderr'):
        d = f.get(key)
        if d is None:
            continue
        stream = Path(d['path'])
        b = (stream if stream.is_absolute() else p / stream).read_bytes()
        assert len(b) == d['bytes'] and sha(b) == d['sha256'], (path, key)
assert negatives == 9
befores = list(p.glob('*.preservation-before.json.gz'))
assert len(befores) == 22
for before in befores:
    after = Path(str(before).replace('.preservation-before.', '.preservation-after.'))
    assert before.read_bytes() == after.read_bytes(), before
    d = json.loads(gzip.decompress(before.read_bytes()))
    assert len(d['rows']) == 14909
for check in v['checks']:
    f = json.loads((r / check['evidence']).read_text())
    assert f['argv'] == check['command'] and f['actual_exit'] == check['exit_code'] == 0
for name, digest in v['source_bindings'].items():
    b = subprocess.check_output(['git', '-C', str(r), 'show', v['exercised_revision'] + ':' + name])
    assert sha(b) == digest
assert subprocess.check_output(['git', '-C', str(r), 'status', '--porcelain']).strip() == b''
print('ROOT_PORTABILITY_CAPTURE_PASS: strict QA18+one, 242 hashes, 35 frames/streams, 22 exact full14909 preservation pairs; source identities checked.')
print('Historical full48/fixturebank not rerun; new exact-head hosted6/main5 and disjoint cost supplement remain.')
