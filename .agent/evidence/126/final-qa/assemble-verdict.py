#!/usr/bin/env python3
"""Assemble evaluator verdict from actual captured results; no product execution."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import jsonschema

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    spec = importlib.util.spec_from_file_location('capture', OUT / 'run-qa.py')
    capture = importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)
    before = json.loads((OUT / 'identity-before.json').read_text())
    final = capture.identities()
    assert before['files'] == final['files']
    assert before['installed_inventory'] == final['installed_inventory']
    assert before['root_run_state_sha256'] == final['root_run_state_sha256']
    (OUT / 'identity-final.json').write_text(json.dumps(final, indent=2) + '\n')
    checks = []
    summary = json.loads((OUT / 'summary.json').read_text())
    for i, row in enumerate(summary['checks'], 1):
        evidence = OUT / f'{i:02d}-command.json'
        for stream in ('stdout', 'stderr'):
            assert sha(ROOT / row[stream]) == row[stream + '_sha256']
        checks.append({**row, 'evidence': str(evidence.relative_to(ROOT)), 'evidence_sha256': sha(evidence)})
    adv = json.loads((OUT / 'adversarial-result.json').read_text())
    obs = json.loads((OUT / 'adversarial-observations.json').read_text())
    assert adv['actual_exit_code'] == 0 and obs['passed'] and obs['owned_processes_stopped']
    assert obs['cleanup_live_registered_pids'] == []
    assert sha(ROOT / adv['stdout']) == adv['stdout_sha256']
    assert sha(ROOT / adv['stderr']) == adv['stderr_sha256']
    assert sha(OUT / 'adversarial.py') == adv['helper_sha256']
    assert sha(OUT / 'run-qa.py') == summary['helper_sha256']
    evidence_files = [str(p.relative_to(ROOT)) for p in sorted(OUT.iterdir()) if p.is_file()]
    evidence_files.append('.agent/evidence/126-qa-adversarial.txt')
    verdict = {'feature_id': '126', 'qa_pass': True, 'checks_run': len(checks),
        'checks_passed': sum(c['exit_code'] == 0 for c in checks), 'checks': checks,
        'executed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'evaluator': {'role': 'Evaluator', 'session': '/root/runtime_qa126', 'attempt': 1,
            'independence': 'Distinct from source author controller_generator, test author acceptance126, and validator capability_review. Re-executed all commands; no Generator result supplies acceptance.',
            'transport_reuse': 'Additional check imports only sealed Session transport/ownership cleanup helpers; its check design and behavioral assertions are evaluator-authored.'},
        'candidate_head': before['head'], 'source_revision': capture.SOURCE, 'test_revision': capture.TEST,
        'contract_sha256': before['contract_sha256'],
        'source_sha256': 'e8878af1a6bbfbf71f8866fd19a2789b9d5f00dff4e8617999ce796f8232bfb4',
        'test_sha256': '626ff4194baee472d27065906e12a0109f2f9878e326a5d6d2212ad2f584fe88',
        'test_lines': 795, 'runtime_identity_ref': '.agent/evidence/126/final-qa/runtime.json',
        'source_runtime_test_identity_ref': '.agent/evidence/126/final-qa/identity-final.json',
        'adversarial': {'performed': True, 'count': 1, 'exit_code': 0,
            'description': 'Idle same-owner transfer must refuse atomically; valid distinct human transfer and new-owner mutation/read remain usable.',
            'evidence': '.agent/evidence/126-qa-adversarial.txt',
            'result_ref': '.agent/evidence/126/final-qa/adversarial-result.json',
            'observations_ref': '.agent/evidence/126/final-qa/adversarial-observations.json'},
        'adversarial_check': {'description': 'Same-owner transfer refusal atomicity with legitimate handover positive control.',
            'result': 'PASS: exact same_owner/1; durable bytes, lease and child receipts preserved; legitimate transfer increments once and operations succeed; registered owned processes stopped.',
            'evidence': '.agent/evidence/126-qa-adversarial.txt'},
        'evidence_files': evidence_files, 'issues': [], 'unsupported_claims': [],
        'missing_acceptance_coverage': [], 'required_fixes': [],
        'final_verdict': {'approved': True, 'summary': 'All nine exact contract commands independently passed and exactly one evaluator-originated adversarial check passed. No required product fixes found within feature126 development-session scope.'},
        'claim_boundary': 'Five development-session calls and fixed stub only. No timeout/replay/SBCL/full-adapter/security/benchmark acceptance or feature-completion claim. Root owns separate evidence-capture and lifecycle gates.',
        'preservation': {'source_test_unchanged': True, 'installed_payload_unchanged': True, 'root_run_state_unchanged': True},
        'dod_ref': '.nizam/standard/definition_of_done.md'}
    assert len(checks) == 9 and verdict['checks_passed'] == 9
    schema = json.loads((ROOT / '.nizam/schema/qa_verdict.schema.json').read_text())
    jsonschema.Draft202012Validator(schema).validate(verdict)
    for p in evidence_files:
        assert (ROOT / p).is_file(), p
    assert verdict['final_verdict']['approved'] is True
    assert all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    (ROOT / '.agent/qa/126.json').write_text(json.dumps(verdict, indent=2) + '\n')
    print('PASS evolved QA schema; strict four-part gate; 9/9 captured exact commands; one additional adversarial; source/test/installed/run_state unchanged')
    print('qa_sha256=' + sha(ROOT / '.agent/qa/126.json'))

if __name__ == '__main__':
    main()
