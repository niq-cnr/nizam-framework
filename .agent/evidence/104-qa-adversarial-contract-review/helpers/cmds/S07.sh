python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
import jsonschema
P = json.load(open('.agent/contracts/104.json'))['design_notes']['pinned_texts']
old, new = run('git', 'show', A + ':CHANGELOG.md'), open('CHANGELOG.md').read()
bullet = norm(P['changelog_bullet'])
nn = norm(new)
if nn.count(bullet) != 1: bad.append('CHANGELOG: the pinned bullet does not occur exactly once')
elif norm(nn.replace(bullet, '', 1)) != norm(old): bad.append('CHANGELOG: differs from base by more than the one pinned bullet')
if not (nn.index('## [Unreleased]') < (nn.index(bullet) if bullet in nn else -1) < nn.index('## [1.4.0]')): bad.append('CHANGELOG: bullet not inside [Unreleased]')
o = yaml.safe_load(run('git', 'show', A + ':docs/planning/phase_014.yaml')); n = yaml.safe_load(open('docs/planning/phase_014.yaml'))
jsonschema.validate(n, json.load(open('schema/phase.schema.json')))
if {k: v for k, v in n.items() if k != 'steps'} != {k: v for k, v in o.items() if k != 'steps'}: bad.append('phase yaml: top-level keys changed')
if [x['id'] for x in o['steps']] != [x['id'] for x in n['steps']]: bad.append('phase yaml: step set/order changed')
os_, ns = {x['id']: x for x in o['steps']}, {x['id']: x for x in n['steps']}
for i in os_:
    if i != '104' and os_[i] != ns.get(i): bad.append('phase yaml: step ' + i + ' changed')
a, b = os_['104'], ns['104']
if {k: v for k, v in b.items() if k not in ('docs_updated', 'changelog_entry', 'evidence', 'status')} != {k: v for k, v in a.items() if k != 'status'}: bad.append('phase yaml: step 104 changed beyond the three keys')
if (b.get('docs_updated'), b.get('changelog_entry'), b.get('evidence')) != (P['phase_yaml_docs_updated'], P['phase_yaml_changelog_entry'], P['phase_yaml_evidence']): bad.append('phase yaml: step 104 values differ from the pinned values')
if b.get('status') == 'BLOCKED': bad.append('phase yaml: step 104 is BLOCKED')
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
