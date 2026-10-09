python3 - <<'PY'
import json, re, subprocess, sys, yaml
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
P = json.load(open('.agent/contracts/104.json'))['design_notes']['pinned_texts']
body = lambda t: t.split('---', 2)[2]
fm = lambda t: yaml.safe_load(t.split('---', 2)[1])
def load(path, old_v, new_v, summary):
    old, new = run('git', 'show', A + ':' + path), open(path).read()
    fo, fn = fm(old), fm(new)
    if (fo['version'], fn['version']) != (old_v, new_v): bad.append('%s: version %s -> %s, expected %s -> %s' % (path, fo['version'], fn['version'], old_v, new_v))
    h = fn['change_log'][0]
    if h['version'] != new_v or h['summary'] != summary or re.fullmatch(r'\d{4}-\d\d-\d\d', str(h['date'])) is None: bad.append(path + ': change_log head entry')
    if fn['change_log'][1:] != fo['change_log']: bad.append(path + ': older change_log entries altered')
    if {k: v for k, v in fn.items() if k not in ('version', 'change_log')} != {k: v for k, v in fo.items() if k not in ('version', 'change_log')}: bad.append(path + ': another frontmatter key changed')
    return old, new, norm(body(old)), norm(body(new))
_, _, o, n = load('standard/definition_of_done.md', '0.1.0', '0.2.0', P['dod_change_log_summary'])
for a, b in P['dod_replacements']:
    if o.count(norm(a)) != 1: bad.append('DoD: replacement source not found exactly once: ' + a)
    o = o.replace(norm(a), norm(b), 1)
if o != n: bad.append('DoD: the body differs from base by more than the four pinned replacements')
old, new, o, n = load('tools/README.md', '0.12.0', '0.13.0', P['readme_change_log_summary'])
para = norm(P['readme_paragraph'])
sec = norm(new.split('## Machine Validation')[1].split('\n## ')[0])
if sec.count(para) != 1 or n.count(para) != 1: bad.append('tools/README.md: the pinned paragraph is not exactly once inside Machine Validation')
if norm(n.replace(para, '', 1)) != o: bad.append('tools/README.md: the body differs from base by more than the pinned paragraph')
old, new, o, n = load('schema/README.md', '0.18.0', '0.19.0', P['schema_change_log_summary'])
line = P['schema_readme_line'].strip()
secs = new.split('## Schemas')[1].split('\n## ')[0]
if [l.strip() for l in secs.splitlines()].count(line) != 1: bad.append('schema/README.md: the pinned statement is not exactly one physical line inside ## Schemas')
if norm(n.replace(norm(line), '', 1)) != o: bad.append('schema/README.md: the body differs from base by more than the pinned line')
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
