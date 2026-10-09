python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
D = '.agent/evidence/104/'
P = json.load(open('.agent/contracts/104.json'))['design_notes']['pinned_texts']
mut = open(D + 'ci-negative-mutation.txt').read().splitlines()
m = re.fullmatch(r'git diff --no-color ([0-9a-f]{40}) ([0-9a-f]{40})', mut[0])
if not m or mut[-1] != 'EXIT:0': bad.append('ci-negative-mutation.txt: line 1 / EXIT trailer')
pos = json.loads('\n'.join(open(D + 'ci-positive-run.txt').read().splitlines()[1:-1]))
neg = json.loads('\n'.join(open(D + 'ci-negative-run.txt').read().splitlines()[1:-1]))
pr = open(D + 'ci-negative-pr-state.txt').read().splitlines()
mp = re.fullmatch(r'gh pr view ([0-9]+) --json state,mergedAt,headRefName,baseRefName', pr[0])
if m:
    base, negsha = m.groups()
    if base != pos['headSha']: bad.append('the mutation base is not the positive run headSha')
    if negsha != neg['headSha']: bad.append('the mutation diff target is not the negative run headSha')
    if sh('git', 'merge-base', '--is-ancestor', base, 'HEAD').returncode != 0: bad.append('the mutation base is not an ancestor of HEAD')
    for sha in (base, negsha):
        if sh('git', 'cat-file', '-e', sha + '^{commit}').returncode != 0 and mp: sh('git', 'fetch', '-q', 'origin', 'refs/pull/%s/head' % mp.group(1))
    cur = yaml.safe_load(open('.github/workflows/compliance.yml'))['jobs'].get('convergent_review')
    if cur is None: bad.append('HEAD has no convergent_review job')
    for sha in (base, negsha):
        g = sh('git', 'show', sha + ':.github/workflows/compliance.yml')
        j = yaml.safe_load(g.stdout)['jobs'].get('convergent_review') if g.returncode == 0 else None
        if j is None or j != cur: bad.append('the convergent_review job at %s is absent or differs from the job at HEAD' % sha[:12])
    d = sh('git', 'diff', '--no-color', base, negsha)
    if d.returncode != 0 or d.stdout.splitlines() != mut[1:-1]: bad.append('the live git diff of the mutation differs from the capture (or an object is unavailable)')
files, cur_f = {}, None
for l in mut[1:-1]:
    if l.startswith('diff --git '): cur_f = l.split(' b/')[-1]; files[cur_f] = ([], [])
    elif cur_f and l.startswith('-') and not l.startswith('---'): files[cur_f][0].append(l[1:])
    elif cur_f and l.startswith('+') and not l.startswith('+++'): files[cur_f][1].append(l[1:])
exp = P['mutation_replacements']
if set(files) != set(exp): bad.append('the mutation touches %r, expected exactly %r' % (sorted(files), sorted(exp)))
for f, (a, b) in exp.items():
    r, p = files.get(f, ([], []))
    if len(r) != 1 or len(p) != 1 or r[0].count(a) != 1 or r[0].replace(a, b, 1) != p[0]: bad.append(f + ': not exactly the one AT4 replacement ' + repr(a) + ' -> ' + repr(b))
if not mp: bad.append('ci-negative-pr-state.txt: line 1')
else:
    s = json.loads('\n'.join(pr[1:-1]))
    live = sh('gh', 'pr', 'view', mp.group(1), '--json', 'state,mergedAt,headRefName,baseRefName')
    if s.get('state') != 'CLOSED' or s.get('mergedAt') or s.get('headRefName') != neg['headBranch'] or not s['headRefName'].startswith('throwaway/104-'): bad.append('negative PR is not closed-unmerged on the throwaway branch: %r' % (s,))
    if live.returncode != 0 or json.loads(live.stdout) != s: bad.append('negative PR state is not live-true')
br = open(D + 'ci-negative-branch-absent.txt').read().splitlines()
if br[0] != 'git ls-remote --heads origin ' + neg['headBranch'] or br[1:] != ['EXIT:0']: bad.append('ci-negative-branch-absent.txt must record an empty ls-remote result')
live = sh('git', 'ls-remote', '--heads', 'origin', neg['headBranch'])
if live.returncode != 0 or live.stdout.strip(): bad.append('the throwaway branch still exists on the remote')
print('negative branch:', neg['headBranch'], 'problems:', bad)
sys.exit(1 if bad else 0)
PY
