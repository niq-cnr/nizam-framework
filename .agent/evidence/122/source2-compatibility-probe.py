"""One independent legacy-QA compatibility observation; expected outer exit zero."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import traceback
import jsonschema

ROOT = Path.cwd()
E = ROOT / '.agent/evidence/122'

def save(name, value):
    (E / ('source2-compatibility-' + name + '.json')).write_text(json.dumps(value, indent=2) + '\n')

def snapshot():
    paths = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / '.nizam').rglob('*') if p.is_file() or p.is_symlink()]
    rows = []
    for name in sorted(set(paths) - {''}):
        if name.startswith('.agent/evidence/122/source2-compatibility-'): continue
        p = ROOT / name
        rows.append([name, p.lstat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest()])
    pins = {name: [mode, digest] for name, mode, digest in rows if name in (
        'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/122.json',
        '.agent/run_state.json', 'schema/qa_verdict.schema.json', 'schema/contract_review.schema.json')}
    return dict(count=len(rows), fingerprint=hashlib.sha256(json.dumps(rows).encode()).hexdigest(), pins=pins)

before = snapshot(); save('protected-before', before)
parent = tempfile.mkdtemp(prefix='nizam122-source2-compatibility-')
observation = dict(role='independent compatibility inspector', final_gate_approval=False,
    fixture_parent=parent, authority='synthetic selected Root authority, not real operator consent',
    expected_outer_exit=0, baseline_passed=False, legacy_schema_valid=False,
    lookup_diagnostic=dict(actual_exit=1, reason='Initial read-only cat used nonexistent .agent/evidence/feature-122 path; corrected to indexed .agent/evidence/122 before behavior execution. No behavior retry.'))
try:
    spec = importlib.util.spec_from_file_location('frozen_acceptance', ROOT / 'tools/test_workflow_assurance.py')
    tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
    api = tests.load_api()
    os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
    f = tests.FailureFixture(api, parent, cause='semantic')
    tests.failure_call(api, f)
    observation['baseline_passed'] = True
    print('BASELINE: current unchanged API accepts frozen semantic fixture', flush=True)
    verdict = dict(feature_id='122', verdict='fail', executed_at='2026-10-15T00:00:00Z',
        checks=[dict(command=' '.join(f.capture['argv']), exit_code=f.capture['exit_code'], evidence=f.capture['stdout']['path'])],
        required_fixes=['Repair the independently classified semantic failure.'],
        issues=[dict(criterion='Observed failed wrapper requires semantic repair', evidence=f.capture['stdout']['path'])])
    schema = json.loads((ROOT / 'schema/qa_verdict.schema.json').read_text())
    jsonschema.Draft202012Validator(schema).validate(verdict)
    jsonschema.Draft202012Validator(schema['anyOf'][0]).validate(verdict)
    tests.require(not jsonschema.Draft202012Validator(schema['anyOf'][1]).is_valid(verdict), 'legacy branch distinct from evolved')
    tests.require(f.capture['exit_code'] == 7, 'real outer failed wrapper retained')
    observation['legacy_schema_valid'] = True
    observation['legacy_verdict'] = verdict
    f.evidence['verdict_ref'] = f.pin_new('legacy-qa-verdict', verdict)
    f.bind()
    observation.update(fixture_revision=tests.git(f.root, 'rev-parse', 'HEAD'),
        policy=copy.deepcopy(f.policy), request=copy.deepcopy(f.request),
        capture=copy.deepcopy(f.capture), evidence=copy.deepcopy(f.evidence))
    fixture_before = f.files(); inputs_before = repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence))
    print('LEGACY_SCHEMA: union and legacy branch valid; evolved branch invalid; real outer exit7', flush=True)
    try:
        result = api.route_failed_attempt(f.root, f.request, policy=f.policy)
        expected = dict(f.request, outcome='failed', route='semantic-repair', attempts_used=1, limit=3, remaining=2, capture_ref=f.authority['capture_ref'])
        tests.require(result == expected, 'legacy semantic verdict must yield exact failed semantic-repair route')
        observation['route_result'] = result
    finally:
        observation['fixture_preserved'] = fixture_before == f.files() and inputs_before == repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence))
        tests.require(observation['fixture_preserved'], 'API preserves all fixture bytes/modes, prior proof, outside sentinel and inputs')
    print('PASS: legacy QA compatibility', flush=True)
except Exception as exc:
    observation.update(status='failed', error_type=type(exc).__name__, diagnostic=str(exc))
    traceback.print_exc()
    raise
else:
    observation['status'] = 'passed'
finally:
    after = snapshot(); save('protected-after', after)
    observation['protected_preserved'] = before == after
    save('observation', observation)
    assert before == after, 'protected repository changed'
