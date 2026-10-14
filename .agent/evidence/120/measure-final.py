"""Root final120 budget snapshot, using the unchanged phase014 classifier."""
import copy
import datetime
import json
import pathlib
import re
import subprocess

E = pathlib.Path('.agent/evidence/120')
BASE = '92fecd8d376964f5e3dd7e34bc201035acfe8bc6'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
argv = ['python3', '.agent/evidence/scope-budget-014/measure.py', '--range', '120=' + BASE + '..' + revision, '--files']
run = subprocess.run(argv, capture_output=True)
(E / 'scope-measurement-final.txt').write_bytes(run.stdout)
(E / 'scope-measurement-final.stderr.txt').write_bytes(run.stderr)
result = {'role': 'Root', 'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'actual_exit': run.returncode, 'revision': revision, 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'stdout': str(E / 'scope-measurement-final.txt'), 'stderr': str(E / 'scope-measurement-final.stderr.txt')}
(E / 'scope-measurement-final-result.json').write_text(json.dumps(result, indent=2) + '\n')
assert run.returncode == 0
def metric(name):
    values = re.findall(r'^\s*' + name + r'=(\d+)(?:\s+.*)?$', run.stdout.decode(), re.MULTILINE)
    assert len(values) == 1, (name, values)
    return int(values[0])
product, process, actual, evidence, excluded, unknown = [metric(name) for name in ('PRODUCT_LINES', 'PROCESS_OVERHEAD_LINES', 'BUDGET_COUNTED_LINES', 'EVIDENCE_LINES', 'EXCLUDED_LINES', 'UNCLASSIFIED_LINES')]
assert product == 740 and actual == product + process and unknown == 0
state_path = pathlib.Path('.agent/run_state.json')
state = json.loads(state_path.read_bytes())
budget = state['scope_budget']
assert budget['original_estimate_lines'] == 7200 and budget['ceiling_130pct'] == 9360
assert state['phase_016_scope_budget_final']['total_lines_changed'] == 5179
assert state['phase_017_scope_budget_final']['total_lines_changed'] == 5203
assert [row['id'] for row in budget['per_feature']] == ['119', '120']
prior = copy.deepcopy(budget['per_feature'][0])
assert prior['actual'] == 722
assert actual <= 2750 and actual + prior['actual'] <= 9360
row = budget['per_feature'][1]
row.update({'actual': actual, 'product_lines': product, 'source_lines': 305, 'independent_test_lines': 435, 'process_overhead_lines': process, 'evidence_lines': evidence, 'excluded_lines': excluded, 'range': BASE + '..' + revision, 'evidence': str(E / 'scope-measurement-final.txt'), 'measurement_status': 'final counted120 before PR101; replaces interim row once', 'measurement_revision': revision, 'capture_revision': subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(E / 'evidence-capture.json')], text=True).strip(), 'baseline': {'prior_features': ['119'], 'rolling_average': 722.0, 'three_times_threshold': 2166.0, 'first_feature_exception': False, 'flagged': actual > 2166}, 'note': 'Whole120 from immutable PR100 merge once, including all contract/review/fixture/helper recoveries, independent acceptance, Source/docs305, tests435, final QA/capture/closure and current planning. Raw canary planning and transport remain evidence, no implementation claim.119722 and archived0165179/0175203 preserved.'})
assert budget['per_feature'][0] == prior
budget['total_lines_changed'] = prior['actual'] + actual
budget['evidence_lines_total'] = prior['evidence_lines'] + evidence
budget['excluded_lines_total'] = prior['excluded_lines'] + excluded
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
budget['last_measured_at'] = now
for key in ('120-current-docs', '120-current-docs-review', '120-final-validation'):
    state['circuit_breaker'][key]['result'] = 'passed'
state['circuit_breaker']['runtime-canary-shape-review']['result'] = 'accepted for preparatory contract authoring only; execution prerequisites unresolved'
state['updated_at'] = now
state['last_action'] = '120 final docs reviewed and local16/0; measured once within original budget. Final exact-head PR101 CI and merge follow;121-123 pending.'
state['history'].append({'at': now, 'event': '120-final-scope-capture', 'detail': 'Whole120=' + str(actual) + ', prior119722 preserved, phase=' + str(budget['total_lines_changed']) + '/9360; Source/docs305+tests435 unchanged. All actual failed attempts retained. Final exact-head hosted checks and authorized clean merge remain.', 'evidence': str(E / 'scope-measurement-final.txt')})
state_path.write_text(json.dumps(state, indent=2) + '\n')
print('PASS final120 counted=' + str(actual) + '/2750; phase=' + str(budget['total_lines_changed']) + '/9360; unclassified0')
