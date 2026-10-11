#!/usr/bin/env python3
"""Parent-owned evidence gate; completion changes only declared lifecycle fields."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import jsonschema
import yaml

directory = Path('.agent/evidence/110')
contract = json.loads(Path('.agent/contracts/110.json').read_text())
qa = json.loads(Path('.agent/qa/110.json').read_text())
candidate = json.loads((directory / 'source-candidate.json').read_text())
review = json.loads(Path('.agent/validator/110-mode-b.json').read_text())
seal = json.loads((directory / 'sealed-bundle.json').read_text())
for verdict in (qa, review):
    assert verdict['final_verdict']['approved'] is True
    for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        assert verdict[key] == [], key
assert qa['qa_pass'] is True and qa['required_fixes'] == []
jsonschema.validate(qa, json.loads(Path('.nizam/schema/qa_verdict.schema.json').read_text()))
jsonschema.validate(contract, json.loads(Path('.nizam/schema/contract.schema.json').read_text()))
assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == len(contract['verification']) == 21
assert qa['candidate_sha'] == candidate['candidate_sha'] == seal['candidate_sha']
assert qa['source_sha256'] == candidate['source_sha256'] == seal['source_sha256']
assert seal['test_author'] != seal['acceptance_reviewer']
assert qa['acceptance_reviewer'] == seal['acceptance_reviewer']
assert re.fullmatch(r'[0-9a-f]{40}', candidate['candidate_sha'])

def completion_delta(path, previous_blob):
    """Allow the three precise post-QA projections; no content changes."""
    before = yaml.safe_load(previous_blob) if path.endswith('.yaml') else json.loads(previous_blob)
    after = yaml.safe_load(Path(path).read_text()) if path.endswith('.yaml') else json.loads(Path(path).read_text())
    normalized = copy.deepcopy(after)
    if path == '.agent/contracts/110.json':
        assert before['status'] == 'approved' and after['status'] == 'complete'
        assert after['completion']['source_candidate_sha'] == candidate['candidate_sha']
        assert after['completion']['qa'] == '.agent/qa/110.json'
        assert after['completion']['evidence_gate'] == '.agent/evidence/110/evidence-gate.txt'
        for key in ('status', 'completed_at', 'completion'):
            if key in before:
                normalized[key] = before[key]
            else:
                normalized.pop(key, None)
    elif path == '.agent/feature_list_015.json':
        original = next(item for item in before['features'] if item['id'] == '110')
        current = next(item for item in normalized['features'] if item['id'] == '110')
        assert current['status'] == 'complete' and current['passes'] is True
        for key in ('status', 'passes', 'completed_at', 'qa', 'contract_ref', 'evidence'):
            if key in original:
                current[key] = original[key]
            else:
                current.pop(key, None)
    elif path == 'docs/planning/phase_015.yaml':
        original = next(item for item in before['steps'] if item['id'] == '110')
        current = next(item for item in normalized['steps'] if item['id'] == '110')
        assert current['status'] == 'COMPLETED'
        assert current['evidence'] == '.agent/evidence/110/evidence-gate.txt'
        for key in ('status', 'evidence', 'docs_updated', 'changelog_entry'):
            if key in original:
                current[key] = original[key]
            else:
                current.pop(key, None)
    elif path == 'docs/planning/backlog_dag.json':
        old_packets = {item['id']: item for item in before['packets']}
        packets = {item['id']: item for item in normalized['packets']}
        assert set(old_packets) == set(packets)
        current = packets['NIP3-110']
        assert current['status'] == 'complete'
        assert current['prerequisites']['evidence']['satisfied'] is True
        for key in ('status', 'evidence'):
            current[key] = old_packets['NIP3-110'][key]
        current['prerequisites']['evidence'] = old_packets['NIP3-110']['prerequisites']['evidence']
        assert packets['NIP3-111']['status'] == 'pending'
        assert packets['NIP3-111']['prerequisites']['technical']['satisfied'] is True
        packets['NIP3-111']['prerequisites']['technical'] = old_packets['NIP3-111']['prerequisites']['technical']
        if 'updated_at' in before:
            normalized['updated_at'] = before['updated_at']
    else:
        raise AssertionError('unapproved candidate delta: ' + path)
    assert normalized == before, path

for path, expected in candidate['source_sha256'].items():
    blob = subprocess.check_output(['git', 'show', candidate['candidate_sha'] + ':' + path])
    assert hashlib.sha256(blob).hexdigest() == expected, path
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
        completion_delta(path, blob)
for path, expected in review['reviewed_sha256'].items():
    assert candidate['source_sha256'][path] == expected, path
for required, actual in zip(contract['verification'], qa['checks']):
    assert actual['command'] == required['command']
    assert actual['evidence'] == required['evidence'] and actual['exit_code'] == 0
    assert actual['evidence'] in qa['evidence_files']
    text = Path(actual['evidence']).read_text()
    assert text.startswith('COMMAND: ' + required['command'] + '\n')
    assert 'CANDIDATE_SHA: ' + candidate['candidate_sha'] + '\n' in text
    assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', text, re.M) == ['0']
for path in qa['evidence_files']:
    assert path.startswith(str(directory) + '/') and Path(path).is_file()
    assert Path(path).stat().st_size > 0
assert qa['adversarial']['performed'] is True
assert qa['adversarial']['evidence'] in qa['evidence_files']
spot = Path(qa['adversarial']['evidence']).read_text()
assert 'CANDIDATE_SHA: ' + candidate['candidate_sha'] + '\n' in spot
assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', spot, re.M) == ['0']
print('EVIDENCE GATE PASS: 21/21 actual candidate-bound checks; independent sealed-bundle acceptance; only declared lifecycle projections may change.')
