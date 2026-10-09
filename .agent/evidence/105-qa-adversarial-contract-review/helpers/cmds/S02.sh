python3 - <<'PY'
import json, os, re, subprocess, sys, yaml
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
lines = open('.agent/evidence/105/attempt-base.txt').read().splitlines()
if len(lines) != 3 or lines[0] != 'git rev-parse HEAD' or lines[2] != 'EXIT:0' or re.fullmatch(r'[0-9a-f]{40}', lines[1]) is None: bad.append('attempt-base.txt is not the three-line captured form: ' + repr(lines))
B = lines[1] if len(lines) > 1 else ''
c = json.load(open('.agent/contracts/105.json'))
scope = {f['path'] for k in ('files_create', 'files_modify') for f in c['scope'][k]}
if sh('git', 'cat-file', '-t', B).stdout.strip() != 'commit': bad.append('B is not a commit')
if sh('git', 'merge-base', '--is-ancestor', A, B).returncode != 0: bad.append('A is not an ancestor of B')
if sh('git', 'merge-base', '--is-ancestor', B, 'HEAD').returncode != 0: bad.append('B is not an ancestor-or-equal of HEAD')
n = int(sh('git', 'rev-list', '--count', B + '..HEAD').stdout.strip() or 99)
if n not in (0, 1): bad.append('HEAD is %d commits past B (an attempt is exactly one commit)' % n)
bc = sh('git', 'show', B + ':.agent/contracts/105.json')
if bc.returncode != 0 or json.loads(bc.stdout).get('status') != 'approved': bad.append('the contract at B is not approved')
delta = set(run('git', 'diff', '--name-only', '-z', B).split('\0')) - {''}
fields = run('git', 'status', '--porcelain', '--untracked-files=all', '-z').split('\0')
i = 0
while i < len(fields):
    entry = fields[i]; i += 1
    if not entry: continue
    delta.add(entry[3:])
    if entry[0] in 'RC' or entry[1] in 'RC':
        if i < len(fields): delta.add(fields[i]); i += 1
extra = sorted(delta - scope)
if extra: bad.append('paths changed since B outside the contract scope (this includes .agent/run_state.json, .agent/feature_list_014.json, tools/skill.json, anything under tools/fixtures/ and every Orchestrator-owned file): ' + repr(extra))
print('B =', B[:12], 'commits past B:', n, 'delta since B:', len(delta), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
