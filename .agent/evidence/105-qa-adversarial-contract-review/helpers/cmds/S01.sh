python3 - <<'PY'
import json, os, re, subprocess, sys, yaml
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
import jsonschema
c = json.load(open('.agent/contracts/105.json'))
jsonschema.validate(c, json.load(open('schema/contract.schema.json')))
f = next(x for x in json.load(open('.agent/feature_list_014.json'))['features'] if x['id'] == '105')
if (c['contract_id'], c['feature_id']) != ('105', '105'): bad.append('ids')
if c['spec_ref'] != '.agent/product_spec_014.md': bad.append('spec_ref')
if c['status'] not in ('proposed', 'approved', 'implemented', 'complete'): bad.append('status ' + c['status'])
ats = [v for v in c['verification'] if not v.get('supplementary')]
sup = [v for v in c['verification'] if v.get('supplementary')]
if [v['acceptance_test'] for v in ats] != f['acceptance_tests'] or [v['command'] for v in ats] != f['acceptance_tests']: bad.append('acceptance tests are not verbatim and in order against the feature list')
if len(ats) != 5 or len(sup) != 9: bad.append('expected 5 acceptance tests and 9 supplementary checks, got %d/%d' % (len(ats), len(sup)))
if any(not v.get('expected_outcome') or not v.get('state_at_base_A') or v.get('owner') not in ('generator', 'evaluator') for v in c['verification']): bad.append('entry without expected_outcome/state_at_base_A/owner')
ev = [v['evidence_file'] for v in c['verification']]
create = [x['path'] for x in c['scope']['files_create']]
modify = [x['path'] for x in c['scope']['files_modify']]
if len(set(ev)) != len(ev) or any(not e.startswith('.agent/evidence/105/') for e in ev): bad.append('evidence files not unique under .agent/evidence/105/')
if not {v['evidence_file'] for v in c['verification'] if v['owner'] == 'generator'} <= set(create): bad.append('a generator evidence file is missing from files_create')
if any(not v['evidence_file'].startswith('.agent/evidence/105/qa/') for v in c['verification'] if v['owner'] == 'evaluator'): bad.append('evaluator evidence must be under .agent/evidence/105/qa/')
if 'attempt-base.txt' not in ' '.join(create).replace('.agent/evidence/105/', ''): bad.append('attempt-base.txt missing from files_create')
for p in modify:
    if sh('git', 'cat-file', '-e', A + ':' + p).returncode != 0: bad.append('files_modify path absent at base: ' + p)
for p in create:
    if sh('git', 'cat-file', '-e', A + ':' + p).returncode == 0: bad.append('create path already exists at base: ' + p)
if sorted(modify) != sorted(['tools/fixtures_self_test.sh', 'tools/README.md', 'CHANGELOG.md', 'docs/planning/phase_014.yaml']): bad.append('files_modify is not the four sanctioned files: ' + repr(modify))
forbidden = ('.agent/run_state.json', '.agent/feature_list_014.json', '.agent/product_spec_014.md', 'docs/planning/DEBT.md', 'docs/planning/backlog_reconciliation.md')
for p in create + modify:
    if p in forbidden or p.startswith(('tools/fixtures/', '.github/', '.agent/evidence/phase-014-activation', 'docs/nips/', 'schema/', 'standard/')): bad.append('a forbidden path is in scope: ' + p)
    if p.startswith('tools/') and p not in ('tools/fixtures_self_test.sh', 'tools/README.md'): bad.append('a tools/ path other than the two sanctioned files: ' + p)
if c['estimated_lines'] != f['estimated_lines']: bad.append('estimated_lines differs from the feature list')
if not c['version_impact'].startswith('PATCH'): bad.append('version_impact must start with PATCH')
r = c['retry_identity']
if (r['contract_step_key'], r['implementation_step_key'], r['limit']) != ('105-contract', '105-implementation', 3): bad.append('retry identity')
print('verification:', len(c['verification']), 'acceptance tests:', len(ats), 'supplementary:', len(sup), 'files_create:', len(create), 'files_modify:', len(modify), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
