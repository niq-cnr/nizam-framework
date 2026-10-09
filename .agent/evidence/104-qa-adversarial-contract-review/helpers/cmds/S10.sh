python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
D = '.agent/evidence/104/'
names = ['ci-positive-run', 'ci-positive-log', 'ci-negative-run', 'ci-negative-log', 'ci-negative-mutation', 'ci-negative-pr-state', 'ci-negative-branch-absent']
T = {}
for n in names:
    T[n] = open(D + n + '.txt').read().splitlines()
    if len(T[n]) < 2 or re.fullmatch(r'EXIT:[0-9]+', T[n][-1]) is None or not T[n][0].strip() or T[n][0].startswith('EXIT:'): bad.append(n + ': not in the Section-5 shape (invocation on line 1, EXIT:<code> last)')
def cap(n):
    m = re.fullmatch(r'gh run view ([0-9]+) --json headSha,headBranch,conclusion,jobs', T[n][0])
    return (m.group(1), json.loads('\n'.join(T[n][1:-1]))) if m else (None, None)
key = lambda r: (r['headSha'], r['headBranch'], r['conclusion'], sorted((j['databaseId'], j['name'], j['conclusion']) for j in r['jobs']))
runs = {}
for k in ('positive', 'negative'):
    rid, r = cap('ci-%s-run' % k)
    if rid is None: bad.append(k + ': line 1 is not the pinned gh run view invocation'); continue
    runs[k] = r
    live = sh('gh', 'run', 'view', rid, '--json', 'headSha,headBranch,conclusion,jobs')
    if live.returncode != 0 or live.stderr.strip() or key(json.loads(live.stdout)) != key(r): bad.append(k + ': the captured run does not match the live run (evidence is not truthful)')
    if r['conclusion'] == 'cancelled' or any(j['conclusion'] == 'cancelled' for j in r['jobs']): bad.append(k + ': a cancelled run or job (concurrency cancel-in-progress)')
    lg = T['ci-%s-log' % k]
    ml = re.fullmatch(r'gh run view --job ([0-9]+) --log', lg[0])
    jb = [j for j in r['jobs'] if ml and str(j['databaseId']) == ml.group(1)]
    if not ml or len(jb) != 1 or jb[0]['name'] != 'convergent_review': bad.append(k + ': the log capture is not for the convergent_review job of that run'); continue
    liv = sh('gh', 'run', 'view', '--job', ml.group(1), '--log')
    if liv.returncode != 0 or liv.stderr.strip(): bad.append(k + ': the live job log could not be re-fetched cleanly (log retention is 90 days; stderr must be empty)')
    elif liv.stdout.splitlines() != lg[1:-1]: bad.append(k + ': the captured job log differs from the live job log (tampered or incomplete)')
neg_other = None
if len(runs) == 2:
    if {j['name'] for j in runs['positive']['jobs']} != {j['name'] for j in runs['negative']['jobs']}: bad.append('positive and negative runs ran different job sets')
    if any(j['conclusion'] != 'success' for j in runs['positive']['jobs']): bad.append('positive: every job must succeed')
    neg_other = [(j['name'], j['conclusion']) for j in runs['negative']['jobs'] if j['name'] != 'convergent_review']
    wf = yaml.safe_load(run('git', 'show', runs['positive']['headSha'] + ':.github/workflows/compliance.yml'))['jobs']
    cur = yaml.safe_load(open('.github/workflows/compliance.yml'))['jobs']
    if wf.get('convergent_review') != cur.get('convergent_review'): bad.append('the job at the positive headSha differs from the job at HEAD (the run did not exercise the deliverable)')
print('positive', runs.get('positive', {}).get('headBranch'), runs.get('positive', {}).get('headSha'), 'negative', runs.get('negative', {}).get('headBranch'), 'other jobs on negative (informational):', neg_other, 'problems:', bad)
sys.exit(1 if bad else 0)
PY
