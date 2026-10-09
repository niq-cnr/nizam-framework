python3 - <<'PY'
import json, subprocess, sys, yaml, jsonschema
BASE = '88959c9'
P = json.load(open('.agent/contracts/103.json'))['design_notes']['pinned_texts']
old = yaml.safe_load(subprocess.run(['git', 'show', BASE + ':docs/planning/phase_014.yaml'], capture_output=True, text=True, check=True).stdout)
new = yaml.safe_load(open('docs/planning/phase_014.yaml'))
jsonschema.validate(new, json.load(open('schema/phase.schema.json')))
bad = []
if {k: v for k, v in new.items() if k != 'steps'} != {k: v for k, v in old.items() if k != 'steps'}: bad.append('top-level keys changed')
if [x['id'] for x in old['steps']] != [x['id'] for x in new['steps']]: bad.append('step set/order changed')
os_ = {x['id']: x for x in old['steps']}; ns = {x['id']: x for x in new['steps']}
for i in os_:
    if i != '103' and os_[i] != ns.get(i): bad.append('step ' + i + ' changed')
o, n = os_['103'], ns['103']
if {k: v for k, v in n.items() if k not in ('docs_updated', 'changelog_entry', 'evidence', 'status')} != {k: v for k, v in o.items() if k != 'status'}: bad.append('step 103 changed beyond docs_updated/changelog_entry/evidence (status excluded)')
if n.get('status') == 'BLOCKED': bad.append('step 103 is BLOCKED')
if set(n) - set(o) != {'docs_updated', 'changelog_entry', 'evidence'}: bad.append('step 103 must gain exactly docs_updated, changelog_entry and evidence, gained ' + str(sorted(set(n) - set(o))))
if n.get('docs_updated') != 'tools/README.md': bad.append('docs_updated != tools/README.md')
if n.get('changelog_entry') != P['phase_yaml_changelog_entry']: bad.append('changelog_entry is not the pinned text')
if n.get('evidence') != '.agent/evidence/103/at1-required-mode.txt': bad.append('evidence != .agent/evidence/103/at1-required-mode.txt')
print('step 103 keys:', sorted(n), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
