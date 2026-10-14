"""Narrow pre-code review of contract126 revision1."""
import hashlib
import json
import subprocess
from pathlib import Path
import jsonschema

old = json.loads(subprocess.check_output(['git', 'show', '9e6fe6daa46a625a2eb2561b5cc8acb202200120:.agent/contracts/126.json']))
raw = Path('.agent/contracts/126.json').read_bytes()
new = json.loads(raw)
assert hashlib.sha256(raw).hexdigest() == '58e6bf758b67bcfb7a8fa6cdb5847f776f78496443ea3d2825123600d3b2f67e'
jsonschema.Draft202012Validator(json.loads(Path('.nizam/schema/contract.schema.json').read_text())).validate(new)
assert new['contract_attempt'] == 2 and new['approvals']['revisions'] == 1
assert new['interface']['serialization'].startswith(old['interface']['serialization'])
assert new['verification'][1]['acceptance_test'].startswith(old['verification'][1]['acceptance_test'])
normalized = json.loads(json.dumps(new))
for key in ('contract_attempt',):
    normalized[key] = old[key]
normalized['approvals']['revisions'] = old['approvals']['revisions']
normalized['interface']['serialization'] = old['interface']['serialization']
normalized['verification'][1]['acceptance_test'] = old['verification'][1]['acceptance_test']
assert normalized == old, 'Unexpected contract change'
feature = next(f for f in json.loads(Path('.agent/feature_list_016.json').read_text())['features'] if f['id'] == '126')
assert [v['command'] for v in new['verification']] == feature['acceptance_tests']
for path in ('tools/runtime_session.py', 'tools/test_runtime_session.py', 'tools/fixtures/runtime_session/stub_runtime.py'):
    assert not Path(path).exists(), path
print(json.dumps({'result': 'pass', 'reviewed_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'contract_sha256': hashlib.sha256(raw).hexdigest(), 'checks': ['installed contract schema', 'exact two appended behavioral clauses plus round metadata', 'all prior contract fields preserved', 'nine commands unchanged', 'source and acceptance runner absent'], 'behavioral_test_execution': 'none: pre-code contract review'}, indent=2))
