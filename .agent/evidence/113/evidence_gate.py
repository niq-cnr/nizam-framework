#!/usr/bin/env python3
"""Disclosed Parent adapter: authenticate feature113 evidence before closure."""
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/113/'


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


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def receipt(path, command, candidate):
    raw = read(path).decode()
    assert raw.startswith('COMMAND: ' + command + '\n'), path
    assert 'CANDIDATE_SHA: ' + candidate + '\n' in raw, path
    assert re.findall(r'^EXIT:\s*(-?\d+)\s*$', raw, re.M) == ['0'], path
    assert raw.rstrip().endswith('EXIT: 0'), path


def replay(files, candidate):
    for path, expected in files.items():
        assert not Path(path).is_absolute() and '..' not in Path(path).parts, path
        assert re.fullmatch('[0-9a-f]{64}', expected['sha256']), path
        assert expected['mode'] in ('100644', '100755'), path
        assert digest(read(path)) == expected['sha256'], path
        mode = '100755' if stat.S_IMODE((ROOT / path).stat().st_mode) & 0o111 else '100644'
        assert mode == expected['mode'], path + ' current mode'
        assert digest(git('show', candidate + ':' + path)) == expected['sha256'], path + ' Git replay'
        entry = git('ls-tree', candidate, '--', path).decode().split('\t')[0].split()
        assert len(entry) == 3 and entry[:2] == [expected['mode'], 'blob'], path + ' Git mode'


def main():
    contract = obj('.agent/contracts/113.json')
    qa = obj('.agent/qa/113.json')
    fixed = obj(E + 'fixed-inputs.json')
    source = obj(E + 'current-source-inputs.json')
    source_seal = obj(E + 'current-source-seal.json')
    mode_b = obj('.agent/validator/113-mode-b.json')
    semantic = obj(E + 'source-review.json')
    bundle = obj('.agent/validator/113-test-bundle-review.json')
    for record in (qa, mode_b, semantic, bundle):
        approved(record)
    jsonschema.validate(qa, obj('.nizam/schema/qa_verdict.schema.json'))
    jsonschema.validate(contract, obj('.nizam/schema/contract.schema.json'))
    assert contract['status'] == 'approved'
    assert qa['feature_id'] == '113' and qa['qa_pass'] is True and qa['required_fixes'] == []
    assert len(contract['verification']) == 16
    assert qa['checks_run'] == qa['checks_passed'] == len(qa['checks']) == 16
    fixed_hash = digest(read(E + 'fixed-inputs.json'))
    source_hash = digest(read(E + 'current-source-inputs.json'))
    assert obj(E + 'fixed-inputs-seal.json')['manifest_sha256'] == fixed_hash
    assert source_seal['manifest_sha256'] == source_hash
    assert source['fixed_inputs_sha256'] == fixed_hash
    contract_hash = digest(read('.agent/contracts/113.json'))
    assert source['contract_sha256'] == fixed['contract_sha256'] == contract_hash
    candidate = source['candidate']['commit']
    assert re.fullmatch('[0-9a-f]{40}', candidate)
    assert source_seal['candidate_commit'] == candidate
    assert git('rev-parse', candidate + '^{tree}').decode().strip() == source['candidate']['tree']
    assert subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', candidate, 'HEAD'], capture_output=True).returncode == 0
    actors = fixed['actors']
    actor_values = [actors[k] for k in ('generator', 'test_author', 'bundle_reviewer', 'final_qa')]
    assert all(isinstance(actor, str) and actor for actor in actor_values) and len(set(actor_values)) == 4
    assert qa['actor'] == semantic['actor'] == actors['final_qa']
    assert mode_b['actor'] == bundle['actor'] == actors['bundle_reviewer']
    bundle_path = '.agent/validator/113-test-bundle-review.json'
    bundle_hash = digest(read(bundle_path))
    assert qa['bundle_review_sha256'] == bundle_hash
    assert digest(git('show', candidate + ':' + bundle_path)) == bundle_hash
    for record in (qa, semantic, mode_b):
        assert record['candidate_commit'] == candidate
        assert record['source_manifest_sha256'] == source_hash
        assert record['fixed_inputs_sha256'] == fixed_hash
    assert qa['mode_b_sha256'] == digest(read('.agent/validator/113-mode-b.json'))
    assert len(source['source_paths']) == 8
    replay(fixed['files'], candidate)
    replay(source['source_paths'], candidate)
    expected_evidence = [E + 'qa-%02d.txt' % i for i in range(1, 17)]
    for required, actual, path in zip(contract['verification'], qa['checks'], expected_evidence):
        assert actual['command'] == required['command'] and actual['evidence'] == path
        assert actual['exit_code'] == 0
        receipt(path, required['command'], candidate)
    spot = E + '113-qa-adversarial.txt'
    assert qa['adversarial']['performed'] is True and qa['adversarial']['evidence'] == spot
    assert qa['adversarial']['command'] not in [x['command'] for x in contract['verification']]
    receipt(spot, qa['adversarial']['command'], candidate)
    assert len(qa['evidence_files']) == 17 and set(qa['evidence_files']) == set(expected_evidence + [spot])
    assert semantic['evidence'] and all(read(path) for path in semantic['evidence'])
    print('EVIDENCE GATE PASS: feature113 actual sealed Git candidate; sixteen independent checks, semantic review, own adversarial receipt; fixed/source bytes and modes replay exactly.')


if __name__ == '__main__':
    main()
