python3 - <<'PY'
import subprocess, sys, yaml
BASE = '483f016'
bad = []
fm = lambda text: yaml.safe_load(text.split('---')[1])
ver = lambda v: tuple(int(x) for x in str(v).split('.'))
for p in ('ecosystem/06_simplification_review.md', 'ecosystem/08_ga_gate.md', 'ecosystem/README.md', 'docs/planning/operator_gates.md'):
    old = fm(subprocess.run(['git', 'show', BASE + ':' + p], capture_output=True, text=True, check=True).stdout)
    new = fm(open(p).read())
    if not ver(new['version']) > ver(old['version']): bad.append(p + ': version not bumped over base')
    if str(new['change_log'][0]['version']) != str(new['version']): bad.append(p + ': change_log head != version')
r = ' '.join(open('ecosystem/README.md').read().split())
for phrase in ('proposal-grade (status `draft`)', 'reserved `H-CONSOLIDATION`', 'reserved `H-GA`'):
    if phrase in r: bad.append('ecosystem/README.md still contains: ' + phrase)
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
problems: []
EXIT:0
