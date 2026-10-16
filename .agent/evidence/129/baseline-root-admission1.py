"""Root evidence admission only; does not rerun the baseline or issue QA."""
import gzip
import hashlib
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[3]
base = root / '.agent/evidence/129/baseline-admission1'
load = lambda name: json.loads((base / name).read_text())
digest = lambda data: hashlib.sha256(data).hexdigest()
report = load('report.json')
revision = '09d227d0210db72c9b09d8b2d508eef91fa95b9a'
assert report['exercised_revision'] == revision
assert digest((base / 'report.json').read_bytes()) == '1424ad43650832c0446bd97f12fe4ef1c5de29f3990a431461dcb7750398b500'
index = load('index.json')
for row in index['files']:
    data = (root / row['path']).read_bytes()
    assert digest(data) == row['sha256'] and len(data) == row['bytes'], row['path']
for path, sha in report['source_bindings_sha256'].items():
    assert digest(subprocess.check_output(['git', 'show', revision + ':' + path], cwd=root)) == sha
    assert digest((root / path).read_bytes()) == sha
assert not (root / 'tools/sbcl_session_loop.lisp').exists()
review = json.loads((root / '.agent/validator/129-bundle-api3.json').read_text())
assert digest(json.dumps(review['bundle'], sort_keys=True, separators=(',', ':')).encode()) == report['frozen_bundle_identity_sha256']
assert review['final_verdict']['approved'] is True
assert all(review[key] == [] for key in ['issues', 'missing_acceptance_coverage', 'unsupported_claims'])
frame = load('admission-red.execution.json')
assert frame['exercised_revision'] == revision and frame['child_pid'] == 3469101
assert frame['actual_exit'] == 1 and frame['timed_out'] is False
assert frame['argv'] == ['python3', 'tools/test_runtime_session.py', '--check', 'sbcl-admission', '--require-sbcl']
for key in ['stdout', 'stderr']:
    data = (base / pathlib.Path(frame[key]['path']).name).read_bytes()
    assert len(data) == frame[key]['bytes'] and digest(data) == frame[key]['sha256']
stdout = (base / 'admission-red.stdout.txt').read_text()
stderr = (base / 'admission-red.stderr.txt').read_text()
assert stderr.startswith('SBCL_ADMISSION_UNAVAILABLE:')
commands = [json.loads(line.partition(' ')[2]) for line in stdout.splitlines() if line.startswith('LIVE_COMMAND ')]
leaves = [json.loads(line.partition(' ')[2]) for line in stdout.splitlines() if line.startswith('CORE_LEAF ')]
assert len(leaves) == 14 and all(row['exit'] == 0 and row['proof'] is True and row['cleanup'] is True for row in leaves)
assert 'PASS core-ready\n' in stdout
assert commands[0]['pid'] == 3469103 and commands[0]['exit'] == 0
assert commands[1]['pid'] == 3469104 and commands[1]['exit'] == 0
assert report['positive_controls']['direct_sbcl']['nonce'] + ':42' in commands[1]['stdout']
product = commands[-1]
assert product['pid'] == 3471490 and product['exit'] == 64 and product['timeout'] is False
assert json.loads(product['stdout']) == {'error': 'usage', 'ok': False} and product['stderr'] == ''
assert stdout.index('PASS core-ready') < stdout.rindex('LIVE_REQUEST ')
before = json.loads(gzip.decompress((base / 'admission-red.preservation-before.json.gz').read_bytes()))
after = json.loads(gzip.decompress((base / 'admission-red.preservation-after.json.gz').read_bytes()))
assert before == after and before['head'] == revision and before['status'] == ''
assert before['origin'] == 'https://github.com/niq-cnr/nizam-framework.git'
assert len(before['rows']) == 15511
installed = [row for row in before['rows'] if row['path'].startswith('.nizam/')]
assert len(installed) == 239
assert load('driver.execution.json')['actual_exit'] == 0
assert load('driver.execution.json')['pid'] == 3469061
assert load('admission-red.capture-summary.json')['success'] is True
print(json.dumps({'admitted': 'narrow actual SBCL admission deficiency only', 'indexed_files': len(index['files']), 'core_positive_leaves': len(leaves), 'physical_rows': len(before['rows']), 'installed_rows': len(installed), 'selector_exit': frame['actual_exit'], 'product_exit': product['exit'], 'source_release': False, 'limitation': 'Inherited core leaf records omit individual PIDs; retained argv/output/exit/proof/cleanup remain explicit.'}, sort_keys=True))
