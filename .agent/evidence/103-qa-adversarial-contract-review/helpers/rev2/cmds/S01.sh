python3 - <<'PY'
import json, subprocess, sys, jsonschema
BASE = '64444289ad3e183dab60f3307da1c8d70a68ebd0'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
c = json.load(open('.agent/contracts/103.json'))
jsonschema.validate(c, json.load(open('schema/contract.schema.json')))
fl = json.loads(run('git', 'show', BASE + ':.agent/feature_list_014.json'))
f = next(x for x in fl['features'] if x['id'] == '103')
bad = []
if (c['contract_id'], c['feature_id']) != ('103', '103'): bad.append('contract_id/feature_id')
if c['spec_ref'] != '.agent/product_spec_014.md': bad.append('spec_ref')
if c['status'] not in ('proposed', 'approved', 'implemented', 'complete'): bad.append('status ' + c['status'])
ats = [v for v in c['verification'] if not v.get('supplementary')]
if [v['acceptance_test'] for v in ats] != f['acceptance_tests'] or [v['command'] for v in ats] != f['acceptance_tests']: bad.append('acceptance tests are not verbatim and in order')
sup = [v for v in c['verification'] if v.get('supplementary')]
if len(ats) != 8 or len(sup) != 18: bad.append('expected 8 acceptance tests and exactly 18 supplementary checks, got %d/%d' % (len(ats), len(sup)))
if any(not v.get('expected_outcome') or not v.get('state_at_base_A') for v in c['verification']): bad.append('entry without expected_outcome/state_at_base_A')
evidence = [v['evidence_file'] for v in c['verification']]
create = [x['path'] for x in c['scope']['files_create']]
modify = [x['path'] for x in c['scope']['files_modify']]
if len(set(evidence)) != len(evidence) or any(not e.startswith('.agent/evidence/103/') for e in evidence): bad.append('evidence files not unique under .agent/evidence/103/')
if not set(evidence) <= set(create): bad.append('evidence file missing from files_create: ' + str(sorted(set(evidence) - set(create))))
for p in modify:
    if subprocess.run(['git', 'cat-file', '-e', BASE + ':' + p], capture_output=True).returncode != 0: bad.append('files_modify path absent at base: ' + p)
for p in create:
    if subprocess.run(['git', 'cat-file', '-e', BASE + ':' + p], capture_output=True).returncode == 0: bad.append('files_create path already exists at base: ' + p)
if '.agent/run_state.json' in modify + create or '.agent/feature_list_014.json' in modify + create: bad.append('run_state/feature_list must not be in scope')
if c['estimated_lines'] != f['estimated_lines']: bad.append('estimated_lines differs from the feature list')
if not c['version_impact'].startswith('MINOR'): bad.append('version_impact must start with MINOR')
r = c['retry_identity']
if (r['contract_step_key'], r['implementation_step_key'], r['limit']) != ('103-contract', '103-implementation', 3): bad.append('retry identity')
print('verification entries:', len(c['verification']), 'acceptance tests:', len(ats), 'supplementary:', len(sup), 'files_create:', len(create), 'files_modify:', len(modify))
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
