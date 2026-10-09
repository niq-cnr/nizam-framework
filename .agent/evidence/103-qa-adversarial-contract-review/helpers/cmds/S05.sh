python3 - <<'PY'
import json, subprocess, sys
BASE = '88959c9'
P = json.load(open('.agent/contracts/103.json'))['design_notes']['pinned_texts']
norm = lambda x: ' '.join(x.split())
body = lambda t: t.split('---', 2)[2]
old = subprocess.run(['git', 'show', BASE + ':tools/README.md'], capture_output=True, text=True, check=True).stdout
new = open('tools/README.md').read()
para = norm(P['readme_paragraph'])
bad = []
section = norm(new.split('## Machine Validation')[1].split('\n## ')[0])
if section.count(para) != 1: bad.append('the pinned paragraph does not occur exactly once inside the Machine Validation section')
if norm(body(new)).count(para) != 1: bad.append('the pinned paragraph does not occur exactly once in the document')
if norm(norm(body(new)).replace(para, '', 1)) != norm(body(old)): bad.append('the document body differs from base by more than the pinned paragraph')
print('paragraph occurrences in section:', section.count(para), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
