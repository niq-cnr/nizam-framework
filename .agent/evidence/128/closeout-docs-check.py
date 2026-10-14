import hashlib, json, re, subprocess
from pathlib import Path
import jsonschema, yaml

base = '72208732026b9b5bcec13f9fd63ad3b3b053021b'
docs = ['docs/planning/ROADMAP.md', 'docs/planning/HANDOVER.md']
schema = json.loads(Path('.nizam/schema/frontmatter.schema.json').read_text())
for path, anchor, version in zip(docs, ['## Current position — phase 016,', '## Current handoff — feature 126,'], ['0.65.4', '1.0.17']):
    old = subprocess.check_output(['git', 'show', base + ':' + path])
    raw = Path(path).read_bytes()
    suffix = raw[raw.index(anchor.encode()):]
    assert suffix == old[old.index(anchor.encode()):], path + ': historical suffix changed'
    text = raw.decode()
    front = yaml.safe_load(text.split('---', 2)[1])
    jsonschema.validate(front, schema)
    assert front['version'] == version and front['change_log'][0]['version'] == version
    current = text[text.index('## Current '):text.index(anchor)]
    assert current.count('## Current ') == 1 and 'captured 126 and 127' not in current
    for target in re.findall(r'\]\(([^)]+)\)', current):
        if not target.startswith('https://'):
            assert (Path(path).parent / target).is_file(), target
    print(path + ': NDS, current links and historical suffix PASS; suffix SHA256 ' + hashlib.sha256(suffix).hexdigest())
changed = subprocess.check_output(['git', 'diff', '--name-only', base], text=True).splitlines()
assert set(changed) == set(docs), changed
capture = json.loads(Path('.agent/evidence/128/evidence-capture.json').read_text())
qa = json.loads(Path('.agent/qa/128.json').read_text())
ci = json.loads(Path('.agent/evidence/128/ci-new-runner-2-receipt.json').read_text())
assert capture['passed'] and capture['aggregate_leaves'] == 14 and qa['qa_pass']
assert qa['checks_run'] == qa['checks_passed'] == 3 and all(c['exit_code'] == 0 for c in qa['checks'])
assert ci['run'] == 38569054719 and capture['runner_sha256'].startswith('005ed223')
print('Owned document diff only; captured QA and separate hosted receipt identities PASS')
