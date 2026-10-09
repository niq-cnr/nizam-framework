python3 - <<'PY'
import json, subprocess, sys
BASE = '64444289ad3e183dab60f3307da1c8d70a68ebd0'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
c = json.load(open('.agent/contracts/103.json'))
scope = {f['path'] for k in ('files_create', 'files_modify') for f in c['scope'][k]}
required_modified = {f['path'] for f in c['scope']['files_modify']}
orchestrator_owned = {'.agent/contracts/103.json', '.agent/run_state.json', '.agent/feature_list_014.json'}
owned_prefixes = ('.agent/validator/103', '.agent/qa/103', '.agent/evidence/103/qa/', '.agent/evidence/103/failed-attempt', '.agent/evidence/103-qa-adversarial')
changed = set(run('git', 'diff', '--name-only', '-z', BASE).split('\0')) - {''}
fields = run('git', 'status', '--porcelain', '--untracked-files=all', '-z').split('\0')
i = 0
while i < len(fields):
    entry = fields[i]; i += 1
    if not entry: continue
    changed.add(entry[3:])
    if entry[0] in 'RC' or entry[1] in 'RC':
        if i < len(fields): changed.add(fields[i]); i += 1
extra = sorted(p for p in changed if p not in scope and p not in orchestrator_owned and not p.startswith(owned_prefixes))
missing = sorted(required_modified - changed)
bad_fl = []
if '.agent/feature_list_014.json' in changed:
    old = json.loads(run('git', 'show', BASE + ':.agent/feature_list_014.json'))
    new = json.load(open('.agent/feature_list_014.json'))
    enum = json.load(open('schema/feature_list.schema.json'))['properties']['features']['items']['properties']['status']['enum']
    if {k: v for k, v in old.items() if k != 'features'} != {k: v for k, v in new.items() if k != 'features'}: bad_fl.append('a non-features key changed')
    if [f['id'] for f in old['features']] != [f['id'] for f in new['features']]: bad_fl.append('ordered feature id list changed')
    else:
        for o, n in zip(old['features'], new['features']):
            if {k: v for k, v in o.items() if k != 'status'} != {k: v for k, v in n.items() if k != 'status'}: bad_fl.append(o['id'] + ': non-status key changed')
            if o['id'] != '103' and o.get('status') != n.get('status'): bad_fl.append(o['id'] + ': status changed')
            if o['id'] == '103' and n.get('status') not in enum: bad_fl.append('103: status not in schema enum')
print('changed:', len(changed), 'extra:', extra, 'modify paths not changed:', missing, 'feature_list violations:', bad_fl)
sys.exit(1 if (extra or missing or bad_fl) else 0)
PY
