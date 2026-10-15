"""Root final121 accounting; original classifier, whole range and estimates retained."""
import copy
import datetime
import json
import pathlib
import re
import subprocess

E = pathlib.Path('.agent/evidence/121')
BASE = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
argv = ['python3', '.agent/evidence/scope-budget-014/measure.py', '--range', '121=' + BASE + '..' + revision, '--files']
run = subprocess.run(argv, capture_output=True)
for stream in ('stdout', 'stderr'):
    (E / ('scope-measurement-final.' + ('txt' if stream == 'stdout' else 'stderr.txt'))).write_bytes(getattr(run, stream))
result = {'role': 'Root', 'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'actual_exit': run.returncode, 'revision': revision, 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'stdout': str(E / 'scope-measurement-final.txt'), 'stderr': str(E / 'scope-measurement-final.stderr.txt')}
(E / 'scope-measurement-final-result.json').write_text(json.dumps(result, indent=2) + '\n')
assert run.returncode == 0
def metric(name):
    values = re.findall(r'^\s*' + name + r'=(\d+)(?:\s+.*)?$', run.stdout.decode(), re.MULTILINE)
    assert len(values) == 1, (name, values)
    return int(values[0])
product, process, actual, evidence, excluded, unknown = [metric(name) for name in ('PRODUCT_LINES', 'PROCESS_OVERHEAD_LINES', 'BUDGET_COUNTED_LINES', 'EVIDENCE_LINES', 'EXCLUDED_LINES', 'UNCLASSIFIED_LINES')]
assert product == 470 and actual == product + process and unknown == 0 and actual <= 1300
state_path = pathlib.Path('.agent/run_state.json'); state = json.loads(state_path.read_bytes()); budget = state['scope_budget']
assert budget['original_estimate_lines'] == 7200 and budget['ceiling_130pct'] == 9360
assert state['phase_016_scope_budget_final']['total_lines_changed'] == 5179
assert state['phase_017_scope_budget_final']['total_lines_changed'] == 5203
assert [row['id'] for row in budget['per_feature']] == ['119', '120']
prior = copy.deepcopy(budget['per_feature']); assert [row['actual'] for row in prior] == [722, 1397]
assert actual + 2119 <= 9360
row = {'id': '121', 'estimated': 1300, 'actual': actual, 'product_lines': product, 'source_lines': 194, 'independent_test_lines': 276, 'process_overhead_lines': process, 'evidence_lines': evidence, 'excluded_lines': excluded, 'range': BASE + '..' + revision, 'evidence': str(E / 'scope-measurement-final.txt'), 'measurement_status': 'final whole121 before PR102, appended once', 'measurement_revision': revision, 'capture_revision': subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(E / 'evidence-capture.json')], text=True).strip(), 'baseline': {'prior_features': ['119', '120'], 'rolling_average': 1059.5, 'three_times_threshold': 3178.5, 'first_feature_exception': False, 'flagged': actual > 3178.5}, 'category_estimates_unchanged': {'source_and_docs': 300, 'tests': 450, 'process': 550}, 'process_variance_from_estimate': process - 550, 'note': 'Whole121 once from actualPR101merge, including all gates/recoveries, adjacent append-only120archive review, Source/docs194, tests276, QA/capture/closure/current planning. Original1300 total and category estimates retained; no new allowance or prior119/120/016/017 rebaseline. Raw evidence and run_state use unchanged classifier exclusions.'}
budget['per_feature'].append(row); assert budget['per_feature'][:2] == prior
budget['total_lines_changed'] = 2119 + actual
budget['evidence_lines_total'] = sum(r['evidence_lines'] for r in budget['per_feature'])
budget['excluded_lines_total'] = sum(r['excluded_lines'] for r in budget['per_feature'])
now = datetime.datetime.now(datetime.timezone.utc).isoformat(); budget['last_measured_at'] = now
state['updated_at'] = now
state['last_action'] = '121 captured, current planning refreshed and whole-feature scope measured; exact-final-head PR102 CI/authorized clean merge remain.122-123 pending.'
state['history'].append({'at': now, 'event': '121-final-scope-capture', 'detail': 'Whole121=' + str(actual) + '/1300; phase=' + str(2119 + actual) + '/9360; process actual=' + str(process) + ' versus original550 estimate, no category estimate or total allowance changed. Prior119722/1201397 and archived0165179/0175203 preserved.', 'evidence': str(E / 'scope-measurement-final.txt')})
state_path.write_text(json.dumps(state, indent=2) + '\n')
print('PASS final121=' + str(actual) + '/1300; phase=' + str(2119 + actual) + '/9360; unclassified0')
