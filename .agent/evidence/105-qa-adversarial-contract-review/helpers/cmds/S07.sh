python3 - <<'PY'
import json, os, re, subprocess, sys, yaml
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
P = json.load(open('.agent/contracts/105.json'))['design_notes']['pinned_texts']
body = lambda t: t.split('---', 2)[2]
fm = lambda t: yaml.safe_load(t.split('---', 2)[1])
old, new = run('git', 'show', A + ':tools/README.md'), open('tools/README.md').read()
fo, fn = fm(old), fm(new)
if (fo['version'], fn['version']) != ('0.13.0', '0.14.0'): bad.append('version %s -> %s, expected 0.13.0 -> 0.14.0' % (fo['version'], fn['version']))
h = fn['change_log'][0]
if h['version'] != '0.14.0' or h['summary'] != P['readme_change_log_summary'] or re.fullmatch(r'\d{4}-\d\d-\d\d', str(h['date'])) is None: bad.append('change_log head entry')
if fn['change_log'][1:] != fo['change_log']: bad.append('older change_log entries altered')
if {k: v for k, v in fn.items() if k not in ('version', 'change_log')} != {k: v for k, v in fo.items() if k not in ('version', 'change_log')}: bad.append('another frontmatter key changed')
o, n = norm(body(old)), norm(body(new))
para = norm(P['readme_paragraph'])
SEC = '### Fixture self-test'
so, sn = norm(old.split(SEC)[1]), norm(new.split(SEC)[1])
if sn.count(para) != 1 or n.count(para) != 1: bad.append('the pinned paragraph does not occur exactly once, inside the Fixture self-test section')
if norm(n.replace(para, '', 1)) != o: bad.append('the body differs from base by more than the pinned paragraph')
if not sn.startswith(so): bad.append('the existing Fixture self-test text (including the completeness-guard sentence) was altered')
if old.split(SEC)[1].count('\n### ') or old.split(SEC)[1].count('\n## '): bad.append('premise: the Fixture self-test section is no longer the last section at <A>')
if not new.endswith('\n') or new.endswith('\n\n'): bad.append('the file must end with exactly one newline')
slice_ = lambda t: t.split(SEC)[1].split('\n## ')[0].split('\n### ')[0]
if 'claim map' in slice_(old) or 'claim map' not in slice_(new): bad.append('AT4 predicate is not discriminating (false at base, true after)')
for tok in re.findall(r'`([^`]+)`', P['readme_paragraph']):
    if '/' in tok and not os.path.exists(tok.rstrip('/')): bad.append('C9: backticked path does not resolve: ' + tok)
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
