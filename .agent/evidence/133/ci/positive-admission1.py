"""Root admission of CI observations, without rerunning tests or collecting logs."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path.cwd()
base = root / '.agent/evidence/133/ci/pr105-terminal2'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda name: json.loads((base / name).read_bytes())
head = '19efbca54be6b2d58f637b22ee4b4185cf32b342'
parent = 'c8ef3cd44dd795ae249769b79a99ef4ebf3f0ad7'
assert sha((base / 'report.json').read_bytes()) == '4f7cde819d6dae03e1e05a22d712f54a3e12083eccd18d3e54a9e1d523112f46'
index = (base / 'capture-index.sha256').read_bytes()
assert sha(index) == '5c39e85d08e65d765d46f29be9631fcca9493306a9a6942056d9d7a59fa0ebad'
indexed = []
for line in index.decode().splitlines():
    digest, name = line.split(maxsplit=1)
    assert Path(name).name == name
    assert sha((base / name).read_bytes()) == digest, name
    indexed.append(name)
assert len(indexed) == len(set(indexed)) == 172
report = read('report.json')
assert report['head'] == head and report['base'] == parent
assert report['observation_complete'] is True and report['all_required_checks_succeeded'] is True
assert report['run_id'] == 38842030473 and report['workflow_conclusion'] == 'success'
expected = {'validate', 'self_governance', 'e2e_bootstrap', 'convergent_review', 'fixtures_self_test', 'closeout'}
assert set(report['required_checks']) == expected and set(report['required_checks'].values()) == {'SUCCESS'}
frames = list(base.glob('*.execution.json'))
for path in frames:
    frame = json.loads(path.read_bytes())
    expected_exit = 1 if path.name in ('watch.execution.json', 'static-observation.execution.json') else 0
    assert frame['actual_exit'] == expected_exit and frame['timed_out'] is False
    assert frame['exercised_revision'] == head and frame['child_pid'] > 0
    for key in ('stdout', 'stderr', 'stdin'):
        ref = frame.get(key)
        if ref is not None:
            raw = (base / Path(ref['path']).name).read_bytes()
            assert sha(raw) == ref['sha256'] and len(raw) == ref['bytes']
assert read('static-observation2.execution.json')['child_pid'] == 3614701
log = (base / 'terminal-logs.stdout.txt').read_bytes()
assert len(log) == 534528 and sha(log) == report['qualified_log']['sha256'] == '87b05e2fb2fcd6be70f683f5c31793521903a4e11e6b0b6094c263a45e31a040'
assert len(log.splitlines()) == 3278
coverage = report['coverage']
assert len(set(coverage['default_ordered_cases'])) == 48
assert len(coverage['auxiliary_pass_literals']) == 1
assert coverage['fixture_file_inventory_per_shell_job'] == '166/166'
assert len(coverage['new_ordered_checks_per_shell_job']) == 4
assert len(report['unknown_step_associations']) == 2
assert all(a['raw_labels_preserved'] and a['raw_step_label'] == 'UNKNOWN STEP' for a in report['unknown_step_associations'])
assert report['feedback']['pagination_complete'] is True
assert report['feedback']['reviews'] == report['feedback']['review_threads'] == 0
assert report['feedback']['comments'] == 1
commit = (base / 'checkout-commit.stdout.txt').read_bytes()
assert hashlib.sha1(b'commit ' + str(len(commit)).encode() + b'\0' + commit).hexdigest() == report['actual_checkout'] == '77f394489620fae51699628fcd38e6cb8fb9fcf6'
headers = commit.split(b'\n\n', 1)[0].decode().splitlines()
assert [x[7:] for x in headers if x.startswith('parent ')] == [parent, head]
assert headers[0] == 'tree ' + subprocess.check_output(['git', 'rev-parse', head + '^{tree}'], text=True).strip()
for path, digest in {**report['immutable_checkout_pins'], **report['physical_source9_hashes']}.items():
    assert sha(subprocess.check_output(['git', 'show', head + ':' + path])) == digest
assert sha(Path('/home/cnross/.tmp/nizam-gh-collector-repair2-build/bin/gh').read_bytes()) == report['qualified_log']['collector_cli_sha256']
print(json.dumps({'admitted': 'CI2 delivery evidence; fresh premerge recheck still required', 'indexed_files': len(indexed), 'frames': len(frames), 'required_checks': 6, 'log_bytes': len(log), 'source_release': False}, sort_keys=True))
