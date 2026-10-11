#!/usr/bin/env python3
"""Orchestrator gate for actual, immutable planning QA receipts."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import jsonschema

task = 'post-ga-phase015-planning'
root = Path('.agent/evidence') / task
contract = json.loads(Path(f'.agent/contracts/{task}.json').read_text())
qa = json.loads(Path(f'.agent/qa/{task}.json').read_text())
record = json.loads((root / 'source-candidate.json').read_text())
review = json.loads(Path(f'.agent/validator/{task}-mode-b.json').read_text())
jsonschema.validate(contract, json.loads(Path('.nizam/schema/contract.schema.json').read_text()))
jsonschema.validate(qa, json.loads(Path('.nizam/schema/qa_verdict.schema.json').read_text()))
for verdict in (qa, review):
    assert verdict['final_verdict']['approved'] is True
    for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        assert verdict[key] == [], key
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert qa['checks_run'] == qa['checks_passed'] == len(contract['verification']) == 6
assert len(qa['checks']) == 6
assert qa['candidate_sha'] == record['candidate_sha']
assert qa['source_sha256'] == record['source_sha256']
assert re.fullmatch(r'[0-9a-f]{40}', record['candidate_sha'])
assert len(record['source_sha256']) == 18
for path, expected in record['source_sha256'].items():
    blob = subprocess.check_output(['git', 'show', record['candidate_sha'] + ':' + path])
    assert hashlib.sha256(blob).hexdigest() == expected, path
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
for path, expected in review['reviewed_sha256'].items():
    assert record['source_sha256'][path] == expected, path
for required, actual in zip(contract['verification'], qa['checks']):
    assert actual['command'] == required['command']
    assert actual['evidence'] == required['evidence'] and actual['exit_code'] == 0
    assert actual['evidence'] in qa['evidence_files']
    capture = Path(actual['evidence']).read_text()
    assert capture.startswith('COMMAND: ' + required['command'] + '\n')
    assert 'CANDIDATE_SHA: ' + record['candidate_sha'] + '\n' in capture
    assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', capture, re.M) == ['0']
    assert 'CHECK PASS:' in capture or 'SUMMARY: 16 passed, 0 failed' in capture
for path in qa['evidence_files']:
    assert path.startswith(str(root) + '/') and Path(path).is_file()
    assert Path(path).stat().st_size > 0
assert qa['adversarial']['performed'] is True
assert qa['adversarial']['evidence'] in qa['evidence_files']
spot = Path(qa['adversarial']['evidence']).read_text()
assert 'CANDIDATE_SHA: ' + record['candidate_sha'] + '\n' in spot
assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', spot, re.M) == ['0']
assert qa['adversarial']['mutations_checked'] >= 1
print('EVIDENCE GATE PASS: 6/6 exact candidate-bound captures, 18 immutable source hashes, Mode B binding and independent adversarial proof.')
