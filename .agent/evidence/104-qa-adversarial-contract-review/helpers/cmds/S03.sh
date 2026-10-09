python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
c = json.load(open('.agent/contracts/104.json'))
scope = {f['path'] for k in ('files_create', 'files_modify') for f in c['scope'][k]}
orch = {f['path'] for f in c['scope']['orchestrator_owned_create']}
modify = {f['path'] for f in c['scope']['files_modify']}
owned = {'.agent/contracts/104.json', '.agent/run_state.json', '.agent/feature_list_014.json'}
prefixes = ('.agent/validator/104', '.agent/qa/104', '.agent/evidence/104/qa/', '.agent/evidence/104/failed-attempt', '.agent/evidence/104-qa-')
changed = set(run('git', 'diff', '--name-only', '-z', A).split('\0')) - {''}
fields = run('git', 'status', '--porcelain', '--untracked-files=all', '-z').split('\0')
i = 0
while i < len(fields):
    entry = fields[i]; i += 1
    if not entry: continue
    changed.add(entry[3:])
    if entry[0] in 'RC' or entry[1] in 'RC':
        if i < len(fields): changed.add(fields[i]); i += 1
extra = sorted(p for p in changed if p not in scope and p not in orch and p not in owned and not p.startswith(prefixes))
missing = sorted(modify - changed)
if extra: bad.append('paths outside scope and allowlist: ' + repr(extra))
if missing: bad.append('files_modify paths not changed (non-vacuity): ' + repr(missing))
if '.agent/feature_list_014.json' in changed:
    old = json.loads(run('git', 'show', A + ':.agent/feature_list_014.json')); new = json.load(open('.agent/feature_list_014.json'))
    if {k: v for k, v in old.items() if k != 'features'} != {k: v for k, v in new.items() if k != 'features'}: bad.append('feature list: a non-features key changed')
    if [x['id'] for x in old['features']] != [x['id'] for x in new['features']]: bad.append('feature list: id order changed')
    else:
        for o, n in zip(old['features'], new['features']):
            if {k: v for k, v in o.items() if k != 'status'} != {k: v for k, v in n.items() if k != 'status'}: bad.append(o['id'] + ': non-status key changed')
            if o['id'] != '104' and o.get('status') != n.get('status'): bad.append(o['id'] + ': status changed')
print('changed:', len(changed), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
