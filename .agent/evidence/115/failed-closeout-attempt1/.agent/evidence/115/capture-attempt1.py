"""Orchestrator-only receipt capture; does not author product or QA decisions."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import jsonschema

root = Path(__file__).resolve().parents[3]
def load(path):
    return json.loads((root / path).read_text())
def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()
candidate = load('.agent/evidence/115/source-candidate.json')
qa_path = '.agent/qa/115.json'
mode_path = '.agent/validator/115-mode-b.json'
qa, mode = load(qa_path), load(mode_path)
contract = load('.agent/contracts/115.json')
for record, schema in ((qa, 'qa_verdict'), (mode, 'contract_review')):
    jsonschema.validate(record, load('.nizam/schema/' + schema + '.schema.json'))
    assert record['final_verdict']['approved'] is True
    assert all(record[key] == [] for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    assert record['revision'] == candidate['revision']
    assert record['source_sha256'] == candidate['source_sha256']
assert qa['actor'] == '/root/wa_acceptance_115' and mode['actor'] == '/root/wa_validator'
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(contract['verification']) == 17
assert len(qa['checks']) == 17
for path, expected in candidate['source_sha256'].items():
    assert digest(path) == expected
    blob = subprocess.check_output(['git', '-C', str(root), 'show', candidate['revision'] + ':' + path])
    assert hashlib.sha256(blob).hexdigest() == expected
for path, expected in {**qa['evidence_sha256'], **qa['proof_source_sha256']}.items():
    assert digest(path) == expected
for expected, observed in zip(contract['verification'], qa['checks']):
    assert expected['command'] == observed['command'] and observed['exit_code'] == 0
    assert observed['evidence'] in qa['evidence_files']
    text = (root / observed['evidence']).read_text()
    assert re.findall(r'^COMMAND: (.*)$', text, re.M) == [expected['command']]
    assert re.findall(r'^REVISION: (.*)$', text, re.M) == [candidate['revision']]
    assert re.findall(r'^EXIT: (-?[0-9]+)$', text, re.M) == ['0']
spot = qa['adversarial']
assert spot['performed'] is True and spot['exit_code'] == 0 and spot['evidence'] in qa['evidence_files']
assert re.findall(r'^EXIT: (-?[0-9]+)$', (root / spot['evidence']).read_text(), re.M) == ['0']
capture = {'passed': True, 'owner': '/root', 'feature': '115', 'revision': candidate['revision'],
           'source_sha256': candidate['source_sha256'], 'qa_ref': qa_path, 'mode_b_ref': mode_path,
           'qa_sha256': digest(qa_path), 'mode_b_sha256': digest(mode_path),
           'checks_captured': 17, 'adversarial_captured': True,
           'evidence_sha256': qa['evidence_sha256'],
           'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
target = root / '.agent/evidence/115/evidence-capture.json'
assert not target.exists()
target.write_text(json.dumps(capture, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('frozen_115_scope', root / '.agent/evidence/115/recovery-scope-guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
try:
    guard.completed_receipts(contract)
except Exception:
    target.rename(root / '.agent/evidence/115/failed-capture-attempt1.json')
    raise
print('PASS distinct Root capture: exact17commands/zero-exits/SourceC revisions, own spot, all proof hashes and strict independent receipts verified')
