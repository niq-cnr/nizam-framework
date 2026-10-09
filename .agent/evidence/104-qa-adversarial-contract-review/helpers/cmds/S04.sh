python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
P = json.load(open('.agent/contracts/104.json'))['design_notes']['pinned_texts']
old = yaml.safe_load(run('git', 'show', A + ':.github/workflows/compliance.yml')); new = yaml.safe_load(open('.github/workflows/compliance.yml'))
if {k: v for k, v in old.items() if k != 'jobs'} != {k: v for k, v in new.items() if k != 'jobs'}: bad.append('a top-level key (name/on/permissions/concurrency) changed')
oj, nj = old['jobs'], new['jobs']
added = [k for k in nj if k not in oj]
if added != ['convergent_review'] or list(nj)[:len(oj)] != list(oj) or any(nj[k] != oj[k] for k in oj): bad.append('not exactly one added job after three byte-identical jobs: added=%r' % added)
pinned = yaml.safe_load(P['workflow_job_yaml'])
if nj.get('convergent_review') != pinned['convergent_review']: bad.append('the job differs from the pinned job')
j = nj.get('convergent_review') or {}
refs = {s['uses'] for b in oj.values() for s in b['steps'] if 'uses' in s}
if not {s['uses'] for s in j.get('steps', []) if 'uses' in s} <= refs: bad.append('a uses: ref is not already pinned elsewhere in the workflow')
text = json.dumps(j)
for w in ('UNSUPPORTED', 'skipped', 'allow-unsupported', 'continue-on-error', ' -k ', 'FAIL: test_', 'ERROR: test_'):
    if w in text: bad.append('forbidden text in the job: ' + w)
if any('if' in s for s in j.get('steps', [])) or 'name' in j: bad.append('a step-level if or a job-level name is present')
steps = [s.get('run') or '' for s in j.get('steps', [])]
suite = [i for i, r in enumerate(steps) if 'tools/test_convergent_review.py' in r]
guard = [i for i, r in enumerate(steps) if 'sysctl' in r]
pip = [i for i, r in enumerate(steps) if 'pip install' in r and 'jsonschema' in r]
if len(suite) != 1 or steps[suite[0]].strip() != 'python3 tools/test_convergent_review.py' or set(j['steps'][suite[0]]) != {'run'}: bad.append('the suite step is not the bare pinned command')
if len(guard) != 1 or len(pip) != 1 or not (pip[0] < suite[0] and guard[0] < suite[0]): bad.append('pip/guard/suite order or count')
print('jobs:', list(nj), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
