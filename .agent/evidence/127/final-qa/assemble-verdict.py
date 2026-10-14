#!/usr/bin/env python3
"""Derive the independent QA verdict exclusively from this round's captures."""
import datetime, hashlib, importlib.util, json
from pathlib import Path
import jsonschema
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
REL = '.agent/evidence/127/final-qa/'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads((ROOT / path).read_text())
def write(path, value): (ROOT / path).write_text(json.dumps(value, indent=2) + '\n')
def main():
    spec = importlib.util.spec_from_file_location('capture', OUT / 'run-qa.py')
    capture = importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)
    before = load(REL + 'identity-before.json'); final = capture.identities()
    assert capture.stable(before) == capture.stable(final)
    write(REL + 'identity-final.json', final)
    summary = load(REL + 'summary.json'); rows = summary['checks']
    assert sha(OUT / 'run-qa.py') == summary['helper_sha256']
    expected = load('.agent/evidence/127/acceptance1-obligations.json')['fourteen_commands']
    assert len(rows) == 17 and [r['command'] for r in rows[:14]] == expected
    for i, row in enumerate(rows, 1):
        assert row['exit_code'] == 0 and row['timed_out'] is False and row['preserved_inputs'] is True
        assert row == load(REL + f'{i:02d}-command.json')
        for stream in ('stdout', 'stderr'): assert sha(ROOT / row[stream]) == row[stream + '_sha256']
        assert capture.stable(load(row['identity_before'])) == capture.stable(before)
        assert capture.stable(load(row['identity_after'])) == capture.stable(before)
    obs = load(REL + 'adversarial-observations.json')
    assert obs['passed'] is True and obs['owned_processes_stopped'] is True and obs['cleanup_live_registered_pids'] == []
    assert obs['helper_sha256'] == sha(OUT / 'adversarial.py')
    for call in obs['calls']:
        for stream in ('stdout', 'stderr'): assert sha(ROOT / call[stream]) == call[stream + '_sha256']
    fixture_lines = (ROOT / rows[15]['stdout']).read_text().splitlines()
    scheduled = [line.removeprefix('COMMAND: ') for line in fixture_lines if line.startswith('COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 tools/test_runtime_session.py ')]
    exits = [line for line in fixture_lines if line.startswith('ACTUAL_EXIT: ')]
    assert scheduled == expected and exits == ['ACTUAL_EXIT: 0'] * 14
    live = []
    for proc in Path('/proc').iterdir():
        try:
            argv = (proc / 'cmdline').read_bytes().split(b'\0')
            owned_paths = [str(ROOT / x).encode() for x in ('tools/runtime_session.py', 'tools/fixtures/runtime_session/stub_runtime.py')]
            if any(path in argv for path in owned_paths): live.append(int(proc.name))
        except (OSError, ValueError): pass
    write(REL + 'post-process-scan.json', {'scope': 'Actual argv entries equal this QA checkout controller/stub path; read-only, no signalling.', 'live_candidate_runtime_pids': live})
    assert live == []
    def check(i):
        row = rows[i - 1]
        return {'command': row['command'], 'exit_code': row['exit_code'], 'evidence': REL + f'{i:02d}-command.json'}
    checks = [check(i) for i in range(1, 15)]
    evidence = [REL + f'{i:02d}-command.json' for i in range(1, 18)]
    evidence += [REL + name for name in ('runtime.json', 'identity-before.json', 'identity-final.json', 'summary.json',
        'adversarial-observations.json', 'post-process-scan.json', 'verdict-validation.json', 'evidence-manifest.json')]
    evidence.append('.agent/evidence/127-qa-adversarial.txt')
    verdict = {'feature_id': '127', 'qa_pass': True, 'checks_run': 14, 'checks_passed': 14, 'checks': checks,
        'executed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'evaluator': {'role': 'Evaluator', 'session': '/root/runtime_qa127', 'attempt': 1,
            'independence': 'Fresh session distinct from Generator controller_generator, acceptance author acceptance126, bundle reviewer capability_review and Source Validator modeb127. All results re-executed locally after strict ModeB release.'},
        'candidate_head': before['head'], 'source_revision': capture.C1, 'test_lines': 1344,
        'contract_sha256': 'b221434834b68dd0273a0bdd0f6f8c0988bee0165f9c31255f4e33b150191cb7',
        'test_sha256': capture.seal_test_hash(before), 'api_sha256': 'f8052878dc2566dde5ec35911b485a874e187df57df8f10ade508505afd544b6',
        'mode_b_ref': '.agent/validator/127-mode-b.json', 'release_ref': '.agent/evidence/127/qa1-modeb-release.json',
        'runtime_ref': REL + 'runtime.json', 'identity_before': REL + 'identity-before.json', 'identity_final': REL + 'identity-final.json',
        'repository_checks': [check(i) for i in (15, 16)],
        'adversarial': {'performed': True, 'count': 1, 'exit_code': rows[16]['exit_code'],
            'description': obs['design'], 'result_ref': REL + '17-command.json', 'observations_ref': REL + 'adversarial-observations.json',
            'evidence': '.agent/evidence/127-qa-adversarial.txt'},
        'adversarial_check': {'description': obs['check'],
            'result': 'PASS: confirmed cancellation clears pending transition state; stale handoff reference refuses atomically; refreshed reattach preserves the same live child, owner/generation/lease and warm value; fresh work succeeds; owned processes stop.',
            'evidence': '.agent/evidence/127-qa-adversarial.txt'},
        'evidence_files': sorted(set(evidence)), 'issues': [], 'missing_acceptance_coverage': [], 'unsupported_claims': [], 'required_fixes': [],
        'final_verdict': {'approved': True, 'summary': 'All fourteen exact runtime commands passed independently, as did tools/validate.sh, full tools/fixtures_self_test.sh and exactly one additional Evaluator-originated interaction check.'},
        'preservation': {'source_test_contract_API_fixture_inputs_unchanged': True, 'installed_payload_unchanged': True, 'root_run_state_unchanged': True},
        'claim_boundary': 'Partial stub semantics only. No SBCL runtime, full adapter, fresh acceptance, superiority, authentication or feature-completion claim. Root owns evidence capture, lifecycle, budget and final PR gates.',
        'dod_ref': '.nizam/standard/definition_of_done.md'}
    schema_path = ROOT / '.nizam/schema/qa_verdict.schema.json'
    jsonschema.Draft202012Validator(json.loads(schema_path.read_text())).validate(verdict)
    assert capture.strict(verdict) and len((ROOT / 'tools/test_runtime_session.py').read_text().splitlines()) == 1344
    write('.agent/qa/127.json', verdict)
    # Re-read written artifact and validate the actual persisted bytes.
    jsonschema.Draft202012Validator(json.loads(schema_path.read_text())).validate(load('.agent/qa/127.json'))
    write(REL + 'verdict-validation.json', {'schema': str(schema_path.relative_to(ROOT)), 'schema_sha256': sha(schema_path),
        'artifact': '.agent/qa/127.json', 'artifact_sha256': sha(ROOT / '.agent/qa/127.json'), 'schema_valid': True,
        'strict_four_part_gate': capture.strict(load('.agent/qa/127.json')), 'runtime_ref': REL + 'runtime.json'})
    files = [p for p in OUT.iterdir() if p.is_file() and p.name not in ('evidence-manifest.json', 'assemble.stdout.txt', 'assemble.stderr.txt')]
    files.append(ROOT / '.agent/evidence/127-qa-adversarial.txt')
    write(REL + 'evidence-manifest.json', {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)})
    assert all((ROOT / p).is_file() for p in verdict['evidence_files'])
    print('PASS: actual14/14, repository2/2, own additional1/1; installed QA schema valid; strict four-part gate passes')
    print('qa_sha256=' + sha(ROOT / '.agent/qa/127.json'))
if __name__ == '__main__': main()
