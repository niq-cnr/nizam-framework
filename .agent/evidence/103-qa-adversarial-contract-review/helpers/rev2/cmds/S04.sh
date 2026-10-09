python3 - <<'PY'
import json, re, subprocess, sys, yaml
BASE = '64444289ad3e183dab60f3307da1c8d70a68ebd0'
P = json.load(open('.agent/contracts/103.json'))['design_notes']['pinned_texts']
fm = lambda text: yaml.safe_load(text.split('---')[1])
old = fm(subprocess.run(['git', 'show', BASE + ':tools/README.md'], capture_output=True, text=True, check=True).stdout)
new = fm(open('tools/README.md').read())
bad = []
if str(old['version']) != '0.11.0': bad.append('base version is not 0.11.0')
if str(new['version']) != '0.12.0': bad.append('version != 0.12.0')
head = new['change_log'][0]
if str(head['version']) != str(new['version']): bad.append('change_log head version != version')
if head['summary'] != P['readme_change_log_summary']: bad.append('change_log head summary is not the pinned text')
if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(head['date'])) is None: bad.append('change_log head date is not YYYY-MM-DD')
if new['change_log'][1:] != old['change_log']: bad.append('prior change_log entries altered')
if {k: v for k, v in new.items() if k not in ('version', 'change_log')} != {k: v for k, v in old.items() if k not in ('version', 'change_log')}: bad.append('a frontmatter key other than version/change_log changed')
print(old['version'], '->', new['version'], 'problems:', bad)
sys.exit(1 if bad else 0)
PY
