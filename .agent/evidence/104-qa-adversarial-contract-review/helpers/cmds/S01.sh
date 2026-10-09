python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
import jsonschema
c = json.load(open('.agent/contracts/104.json'))
jsonschema.validate(c, json.load(open('schema/contract.schema.json')))
f = next(x for x in json.load(open('.agent/feature_list_014.json'))['features'] if x['id'] == '104')
if (c['contract_id'], c['feature_id']) != ('104', '104'): bad.append('ids')
if c['spec_ref'] != '.agent/product_spec_014.md': bad.append('spec_ref')
if c['status'] not in ('proposed', 'approved', 'implemented', 'complete'): bad.append('status ' + c['status'])
ats = [v for v in c['verification'] if not v.get('supplementary')]
sup = [v for v in c['verification'] if v.get('supplementary')]
if [v['acceptance_test'] for v in ats] != f['acceptance_tests'] or [v['command'] for v in ats] != f['acceptance_tests']: bad.append('acceptance tests are not verbatim and in order against the feature list')
if len(ats) != 10 or len(sup) != 11: bad.append('expected 10 acceptance tests and 11 supplementary checks, got %d/%d' % (len(ats), len(sup)))
if any(not v.get('expected_outcome') or not v.get('state_at_base_A') or v.get('owner') not in ('generator', 'evaluator') for v in c['verification']): bad.append('entry without expected_outcome/state_at_base_A/owner')
ev = [v['evidence_file'] for v in c['verification']]
create = [x['path'] for x in c['scope']['files_create']]
modify = [x['path'] for x in c['scope']['files_modify']]
orch = [x['path'] for x in c['scope']['orchestrator_owned_create']]
if len(set(ev)) != len(ev) or any(not e.startswith('.agent/evidence/104/') for e in ev): bad.append('evidence files not unique under .agent/evidence/104/')
if not {v['evidence_file'] for v in c['verification'] if v['owner'] == 'generator'} <= set(create): bad.append('a generator evidence file is missing from files_create')
if any(not v['evidence_file'].startswith('.agent/evidence/104/qa/') for v in c['verification'] if v['owner'] == 'evaluator'): bad.append('evaluator evidence must be under .agent/evidence/104/qa/')
if set(create) & set(orch): bad.append('files_create and orchestrator_owned_create overlap')
for p in modify:
    if sh('git', 'cat-file', '-e', A + ':' + p).returncode != 0: bad.append('files_modify path absent at base: ' + p)
for p in create + orch:
    if sh('git', 'cat-file', '-e', A + ':' + p).returncode == 0: bad.append('create path already exists at base: ' + p)
forbidden = ('.agent/run_state.json', '.agent/feature_list_014.json', '.agent/product_spec_014.md', 'docs/planning/DEBT.md')
if any(p in forbidden or p.startswith(('tools/linux_', 'tools/isolated_', 'tools/test_', 'tools/convergent_', 'tools/validate', 'tools/fixtures', '.agent/evidence/phase-014-activation')) for p in create + modify + orch): bad.append('a forbidden path is in scope')
if c['estimated_lines'] != f['estimated_lines']: bad.append('estimated_lines differs from the feature list')
if not c['version_impact'].startswith('MINOR'): bad.append('version_impact must start with MINOR')
r = c['retry_identity']
if (r['contract_step_key'], r['implementation_step_key'], r['limit']) != ('104-contract', '104-implementation', 3): bad.append('retry identity')
print('verification:', len(c['verification']), 'acceptance tests:', len(ats), 'supplementary:', len(sup), 'files_create:', len(create), 'files_modify:', len(modify), 'orchestrator_owned:', len(orch), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
