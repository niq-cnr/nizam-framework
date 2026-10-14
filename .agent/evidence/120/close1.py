"""Root-only canonical-first closure; validate every proposed document before writes."""
import datetime
import json
import pathlib
import subprocess

import jsonschema
import yaml

E = pathlib.Path('.agent/evidence/120')
def read(path): return json.loads(pathlib.Path(path).read_bytes())
def encoded(value): return json.dumps(value, indent=2) + '\n'
capture = read(E / 'evidence-capture.json')
assert capture['feature'] == '120' and capture['passed'] is True and capture['actual_exit'] == 0
assert read('.agent/qa/120.json')['qa_pass'] is True
assert read(E / 'ci2-receipt.json')['passed'] is True
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
capture_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(E / 'evidence-capture.json')], text=True).strip()
assert len(capture_commit) == 40
updates = {}
path = 'docs/planning/phase_018.yaml'
text = pathlib.Path(path).read_text()
phase = yaml.safe_load(text)
assert phase['status'] == 'in_progress'
assert next(row for row in phase['steps'] if row['id'] == '120')['status'] == 'IN_PROGRESS'
old = "- id: '120'\n  description: Receipt gates and idempotent recovery\n  status: IN_PROGRESS"
assert text.count(old) == 1
text = text.replace(old, old.replace('IN_PROGRESS', 'COMPLETED') + '\n  evidence: .agent/evidence/120/evidence-capture.json', 1)
description = 'description: ' + phase['description']
assert text.count(description) == 1
text = text.replace(description, 'description: Active controls119-123;119 merged and120 captured complete,121 conflict lanes next;121-123 remain pending.', 1)
updates[path] = ('phase', text, yaml.safe_load(text))
path = 'docs/planning/manifest.json'
value = read(path)
row = next(row for row in value['phases'] if row['id'] == '018-workflow-assurance-controls')
assert row['status'] == 'in_progress'
row['note'] = 'Active controls119-123 within original7200/9360.119 merged;120 captured through strict independent gates, fresh11/default37 QA, historical success/live stale-proof rejection, existing hosted37 and Root evidence capture.121-123 pending. Actual legacy Root repository binding migration remains a reviewed proposal; no controls-ready/runtime/comparison or installed upgrade claim.'
value['updated_at'] = now
updates[path] = ('manifest', encoded(value), value)
path = '.agent/contracts/120.json'
text = pathlib.Path(path).read_text()
value = json.loads(text)
assert value['status'] == 'approved'
assert capture['approved_contract_sha256'] == '3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
text = text.replace('"status": "approved"', '"status": "complete"', 1)
updates[path] = ('contract', text, json.loads(text))
path = '.agent/feature_list_018.json'
text = pathlib.Path(path).read_text()
start = text.index('      "id": "120"')
end = text.index('      "id": "121"', start)
block = text[start:end]
assert block.count('"status": "in_progress"') == 1 and block.count('"passes": false') == 1
block = block.replace('"status": "in_progress"', '"status": "complete"', 1).replace('"passes": false', '"passes": true', 1)
old_stage = '      "stage": "contract-preparation"'
assert block.count(old_stage) == 1
block = block.replace(old_stage, '      "stage": "captured",\n      "evidence_ref": ".agent/evidence/120/evidence-capture.json",\n      "contract_ref": ".agent/contracts/120.json",\n      "qa_ref": ".agent/qa/120.json",\n      "completed_at": "' + now + '"', 1)
text = text[:start] + block + text[end:]
updates[path] = ('feature_list', text, json.loads(text))
path = '.agent/run_state.json'
value = read(path)
assert value['current_feature'] == '120' and value['status'] == 'in_progress'
assert '120' not in value['completed_contract_ids']
value['completed_contract_ids'].append('120')
for key in ('120-QA', '120-hosted-ci', '120-evidence-capture'):
    value['circuit_breaker'][key]['result'] = 'passed'
value['updated_at'] = now
value['last_action'] = '120 captured complete; phase018 active,121 next after clean PR101 merge/main CI. Legacy Root binding migration remains unapplied.'
value['history'].append({'at': now, 'event': '120-captured-complete', 'detail': 'Canonical120 COMPLETED first, then derived contract/list/manifest/state after verified independent QA, hosted37 and evidence capture. Source unchanged since initial1689f0d; historical failures and installed239 preserved.121-123 pending; no full controls-ready or comparative claim.', 'evidence': str(E / 'evidence-capture.json')})
updates[path] = ('run_state', encoded(value), value)
errors = []
for path, (schema_name, text, value) in updates.items():
    schema = read('.nizam/schema/' + schema_name + '.schema.json')
    errors.extend(path + ': ' + error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(value))
assert not errors, errors
for path, (_, text, _) in updates.items():
    pathlib.Path(path).write_text(text)
(E / 'closure.json').write_text(encoded({'role': 'Root', 'at': now, 'attempt': 1, 'capture_commit': capture_commit, 'evidence_capture': str(E / 'evidence-capture.json'), 'canonical_step': 'COMPLETED', 'contract': 'complete', 'feature_list_passes': True, 'phase_status': 'in_progress', 'next': '121', 'later_pending': ['121', '122', '123'], 'boundary': 'No release, installed upgrade, live Root receipt API adoption, full runtime or comparative result.'}))
print('PASS complete-schema closure: canonical120 COMPLETED; derived complete; phase018 active;121-123 pending')
