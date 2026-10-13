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
candidate = load('.agent/evidence/116/source-candidate.json')
qa_path = '.agent/qa/116.json'
mode_path = '.agent/validator/116-mode-b.json'
qa, mode = load(qa_path), load(mode_path)
contract = load('.agent/contracts/116.json')
for record, schema in ((qa, 'qa_verdict'), (mode, 'contract_review')):
    jsonschema.validate(record, load('.nizam/schema/' + schema + '.schema.json'))
    assert record['final_verdict']['approved'] is True
    assert all(record[key] == [] for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    assert record['revision'] == candidate['revision']
    assert record['source_sha256'] == candidate['source_sha256']
assert qa['actor'] == '/root/wa_acceptance_116' and mode['actor'] == '/root/wa_validator'
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(contract['verification']) == 12
assert len(qa['checks']) == 12
for path, expected in candidate['source_sha256'].items():
    assert digest(path) == expected
    blob = subprocess.check_output(['git', '-C', str(root), 'show', candidate['revision'] + ':' + path])
    assert hashlib.sha256(blob).hexdigest() == expected
for path, expected in {**qa['evidence_sha256'], **qa['proof_source_sha256']}.items():
    assert digest(path) == expected
# All reviewed dependencies and captured baseline artifacts are also SourceC Git-bound.
assert subprocess.check_output(['git', '-C', str(root), 'rev-parse', candidate['revision'] + '^{tree}'], text=True).strip() == candidate['tree']
for path, expected in qa['proof_source_sha256'].items():
    assert hashlib.sha256(subprocess.check_output(['git', '-C', str(root), 'show', candidate['revision'] + ':' + path])).hexdigest() == expected
    mode = subprocess.check_output(['git', '-C', str(root), 'ls-tree', candidate['revision'], path], text=True).split()[0]
    assert bool((root / path).stat().st_mode & 0o111) is (mode == '100755')
bundle = load('.agent/evidence/116/acceptance-bundle.json')
for item in bundle['inputs']:
    assert digest(item['path']) == item['sha256'] == hashlib.sha256(subprocess.check_output(['git', '-C', str(root), 'show', bundle['baseline']['commit'] + ':' + item['path']])).hexdigest()
assert type(qa['checks_run']) is int and type(qa['checks_passed']) is int
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
capture = {'passed': True, 'owner': '/root', 'feature': '116', 'revision': candidate['revision'],
           'source_sha256': candidate['source_sha256'], 'qa_ref': qa_path, 'mode_b_ref': mode_path,
           'qa_sha256': digest(qa_path), 'mode_b_sha256': digest(mode_path),
           'checks_captured': 12, 'adversarial_captured': True,
           'evidence_sha256': qa['evidence_sha256'],
           'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
target = root / '.agent/evidence/116/evidence-capture.json'
assert not target.exists()
target.write_text(json.dumps(capture, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('frozen_116_scope', root / '.agent/evidence/116/scope-guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
try:
    guard.completed_receipts(contract)
except Exception:
    target.rename(root / '.agent/evidence/116/failed-capture-attempt1.json')
    raise
print('PASS distinct Root capture: exact12commands/zero-exits/SourceC revisions, own spot, all proof hashes and strict independent receipts verified')
