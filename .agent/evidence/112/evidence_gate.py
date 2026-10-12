#!/usr/bin/env python3
"""Parent capture adapter: authenticate actual acceptance before lifecycle closure."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/112/'


def read(path):
    p = ROOT / path
    assert not p.is_symlink() and p.is_file(), path
    return p.read_bytes()


def obj(path):
    return json.loads(read(path))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def approved(record):
    assert record['final_verdict']['approved'] is True
    for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        assert record[key] == [], key


def receipt(path, command, candidate):
    raw = read(path).decode()
    assert raw.startswith('COMMAND: ' + command + '\n'), path
    assert 'CANDIDATE_SHA: ' + candidate + '\n' in raw, path
    assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', raw, re.M) == ['0'], path


def main():
    contract = obj('.agent/contracts/112.json')
    qa = obj('.agent/qa/112.json')
    seal = obj(E + 'qa-inputs.json')
    mode_b = obj('.agent/validator/112-mode-b.json')
    approved(mode_b)
    approved(qa)
    jsonschema.validate(qa, obj('.nizam/schema/qa_verdict.schema.json'))
    jsonschema.validate(contract, obj('.nizam/schema/contract.schema.json'))
    assert contract['status'] == 'approved'
    assert qa['feature_id'] == '112' and qa['qa_pass'] is True and qa['required_fixes'] == []
    assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == len(contract['verification']) == 20
    candidate = seal['candidate_sha']
    assert re.fullmatch('[0-9a-f]{40}', candidate)
    assert read(E + 'qa-inputs.sha256').decode().strip() == digest(read(E + 'qa-inputs.json'))
    assert qa['candidate_sha'] == candidate and qa['source_sha256'] == seal['source_sha256']
    assert qa['qa_inputs_sha256'] == digest(read(E + 'qa-inputs.json'))
    assert qa['mode_b_sha256'] == seal['mode_b_sha256'] == digest(read('.agent/validator/112-mode-b.json'))
    assert mode_b['reviewed_sha256'] == seal['source_sha256']
    actors = [seal[k] for k in ('generator', 'test_author', 'checker_reviewer', 'acceptance_reviewer')]
    assert all(isinstance(actor, str) and actor for actor in actors) and len(set(actors)) == 4
    assert qa['acceptance_reviewer'] == seal['acceptance_reviewer']
    assert digest(read('.agent/contracts/112.json')) == seal['approved_contract_sha256']
    for group in ('source_sha256', 'verification_sha256', 'immutable_input_sha256'):
        for path, expected in seal[group].items():
            assert digest(read(path)) == expected, path
            blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', candidate + ':' + path])
            assert digest(blob) == expected, path + ' candidate replay'
    assert seal['primary_sources_sha256'] == digest(read(E + 'primary-sources.json'))
    semantic = obj(E + 'semantic-review.json')
    approved(semantic)
    assert semantic['reviewer'] == seal['acceptance_reviewer'] and semantic['personally_reviewed'] is True
    assert semantic['candidate_sha'] == candidate and semantic['source_sha256'] == seal['source_sha256']
    assert semantic['qa_inputs_sha256'] == digest(read(E + 'qa-inputs.json'))
    evidence = [required['evidence'] for required in contract['verification']]
    spot = qa['adversarial']['evidence']
    assert qa['adversarial']['performed'] is True and spot == E + '112-qa-adversarial.txt'
    assert len(qa['evidence_files']) == 21 and set(qa['evidence_files']) == set(evidence + [spot])
    for required, actual in zip(contract['verification'], qa['checks']):
        assert actual['command'] == required['command'] and actual['evidence'] == required['evidence']
        assert actual['exit_code'] == 0
        receipt(actual['evidence'], required['command'], candidate)
    receipt(spot, qa['adversarial']['command'], candidate)
    print('EVIDENCE GATE PASS: actual sealed candidate, 20/20 checks, independent semantic review and own adversarial receipt; source and assessed inputs replay exactly from Git.')


if __name__ == '__main__':
    main()
