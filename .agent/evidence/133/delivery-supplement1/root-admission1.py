"""Admit retained raw accounting evidence; never execute its measurement again."""
import gzip
import hashlib
import json
from pathlib import Path

base = Path('.agent/evidence/133/delivery-supplement1/measurement1')
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda name: json.loads((base / name).read_bytes())
index = read('capture-index.json')
for path, expected in index.items():
    data = Path(path).read_bytes()
    assert sha(data) == expected['sha256'] and len(data) == expected['bytes'], path
report_data = (base / 'supplement-report.json').read_bytes()
assert sha(report_data) == '388ebd62e35c83c7b727db10c79c82f3c8771e8672406095d49d3d5dabe3ab9b'
report = json.loads(report_data)
assert report['endpoint'] == 'c3345ff4a7a4a1c61673fa046a4801cf13a19f03'
assert report['historical_cost'] == 3024 and report['historical_budget_gate_passed'] is False
assert report['views']['snapshot']['133'] == 3180 and report['views']['chronological']['133'] == 3196
assert report['supplement'] == max(report['views'][v]['133'] for v in ['snapshot', 'chronological']) == 3196
assert report['cumulative_retained_lines'] == 3024 + report['supplement'] == 6220
assert len(report['rows']) == 2454 and len(report['merges']) == 50
assert all(m['actual_exit'] == 0 and m['stdout']['bytes'] == m['stderr']['bytes'] == 0 for m in report['merges'])
frame = read('measurement.execution.json')
assert frame['actual_exit'] == 0 and frame['child_pid'] == 3733617 and frame['timed_out'] is False
assert frame['exercised_revision'] == report['endpoint']
for key in ['stdout', 'stderr']:
    data = (base / Path(frame[key]['path']).name).read_bytes()
    assert sha(data) == frame[key]['sha256'] and len(data) == frame[key]['bytes'] == 0
before = json.loads(gzip.decompress((base / 'measurement.preservation-before.json.gz').read_bytes()))
after = json.loads(gzip.decompress((base / 'measurement.preservation-after.json.gz').read_bytes()))
assert before == after and before['head'] == report['endpoint'] and len(before['rows']) == 15810
assert len([r for r in before['rows'] if r['path'].startswith('.nizam/')]) == 239
assert sha((base / 'input-inventory.json').read_bytes()) == report['inventory_sha256']
assert (base / 'input-inventory.json').read_bytes() == Path('.agent/evidence/133/delivery-supplement1/final-inventory.json').read_bytes()
print(json.dumps({'admitted': 'disjoint retained-line observation only', 'supplement': 3196, 'cumulative': 6220, 'indexed_files': len(index), 'later_administration': 'separate and unmeasured', 'budget_gate_passed': False}, sort_keys=True))
