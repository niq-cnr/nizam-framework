"""Root coordination only: captured121 closes canonical-first, then derived state."""
import datetime
import hashlib
import json
import pathlib
import subprocess

import jsonschema
import yaml

E = pathlib.Path('.agent/evidence/121')
def read(path): return json.loads(pathlib.Path(path).read_bytes())
def encoded(value): return json.dumps(value, indent=2) + '\n'
capture = read(E / 'evidence-capture.json')
assert capture['feature'] == '121' and capture['passed'] is True and capture['actual_exit'] == 0
assert read('.agent/qa/121.json')['qa_pass'] is True
assert read(E / 'ci2-receipt.json')['passed'] is True
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
capture_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(E / 'evidence-capture.json')], text=True).strip()
assert len(capture_commit) == 40
updates = {}
path = 'docs/planning/phase_018.yaml'
text = pathlib.Path(path).read_text(); phase = yaml.safe_load(text)
assert phase['status'] == 'in_progress'
assert all(row['status'] == 'PENDING' for row in phase['steps'] if row['id'] in ('122', '123'))
old = "- id: '121'\n  description: Conflict lanes, isolated retries and owned rollback\n  status: IN_PROGRESS"
assert text.count(old) == 1
text = text.replace(old, old.replace('IN_PROGRESS', 'COMPLETED') + '\n  evidence: .agent/evidence/121/evidence-capture.json', 1)
description = 'description: ' + phase['description']; assert text.count(description) == 1
text = text.replace(description, 'description: Active controls119-123;119-121 captured,122-123 pending.', 1)
updates[path] = ('phase', text, yaml.safe_load(text))
path = 'docs/planning/manifest.json'; value = read(path)
row = next(row for row in value['phases'] if row['id'] == '018-workflow-assurance-controls')
assert row['status'] == 'in_progress'
row['note'] = 'Active119-123 within original7200/9360.119-121 captured;121 has independent currentSource controls, ModeB, fresh5/default42 QA, historical118/stale-current checks, hosted42 and Root capture. PR102 final checks/merge remain;122-123 pending. Legacy Root binding migration unapplied; no controls-ready/full-runtime/comparison or installed upgrade claim.'
value['updated_at'] = now; updates[path] = ('manifest', encoded(value), value)
path = '.agent/contracts/121.json'; text = pathlib.Path(path).read_text()
assert json.loads(text)['status'] == 'approved'
assert hashlib.sha256(text.encode()).hexdigest() == capture['approved_contract_sha256'] == '145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e'
text = text.replace('"status": "approved"', '"status": "complete"', 1)
updates[path] = ('contract', text, json.loads(text))
path = '.agent/feature_list_018.json'; value = read(path)
row = next(row for row in value['features'] if row['id'] == '121')
assert row['status'] == 'in_progress' and row['passes'] is False
row.update(status='complete', passes=True, stage='captured', evidence_ref=str(E / 'evidence-capture.json'), contract_ref='.agent/contracts/121.json', qa_ref='.agent/qa/121.json', completed_at=now)
updates[path] = ('feature_list', encoded(value), value)
path = '.agent/run_state.json'; value = read(path)
assert value['current_feature'] == '121' and value['status'] == 'in_progress'
assert '121' not in value['completed_contract_ids']; value['completed_contract_ids'].append('121')
for key in ('121-QA', '121-ci', '121-evidence-capture'):
    value['circuit_breaker'][key]['status'] = 'passed'
value['updated_at'] = now
value['last_action'] = '121 captured complete; final PR102 checks/merge and mainCI precede122 selection.122-123 pending; installedv1.5.0 unchanged.'
value['history'].append({'at': now, 'event': '121-captured-complete', 'detail': 'Canonical121 COMPLETED first, then derived contract/list/manifest/state after independent currentSource controls/ModeB/freshQA/hosted42/Root capture. All failures and explicit pre-runtime inspection recovery retained.122-123 pending; no release/runtime/comparative claim.', 'evidence': str(E / 'evidence-capture.json')})
updates[path] = ('run_state', encoded(value), value)
for path, (name, text, value) in updates.items():
    for root in ('.nizam/schema/', 'schema/'):
        jsonschema.validate(value, read(root + name + '.schema.json'))
for path, (_, text, _) in updates.items(): pathlib.Path(path).write_text(text)
(E / 'closure.json').write_text(encoded({'role': 'Root', 'at': now, 'capture_commit': capture_commit, 'canonical_step': 'COMPLETED', 'contract': 'complete', 'phase_status': 'in_progress', 'later_pending': ['122', '123'], 'boundary': 'Final PR102 integration pending; no release/install/full-runtime/comparison claim.'}))
print('PASS canonical121 completed then derived state;122-123 pending')
