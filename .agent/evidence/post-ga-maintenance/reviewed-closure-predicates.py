"""Executable proposal predicates; synthetic fixtures are controls, never QA proof."""
import copy
import hashlib
import re

DEBTS = {'NDEBT-047', 'NDEBT-046', 'NDEBT-045'}
SOURCES = {'tools/fixtures_self_test.sh', 'tools/test_convergent_review.py', 'tools/validate.sh', 'standard/AGF.md', 'templates/AGENTS.md', 'tools/README.md', '.github/scripts/test_c13_cleanup.py', '.github/scripts/test_sandbox_boundaries.py', '.github/workflows/compliance.yml'}
PROOF = '.agent/evidence/post-ga-maintenance/'


def need(ok, code):
    if not ok:
        raise ValueError(code)


def closure(stage, state, proof, contract):
    """state/proof must be populated from real parsed files by the task checker."""
    need(stage in {'intake', 'final'}, 'stage-required')
    if stage == 'intake':
        need(DEBTS <= set(state['open']) and not DEBTS.intersection(state['resolved']), 'intake-debt')
        need(state['a04a'] == 'pending', 'intake-a04a')
        return
    need(DEBTS <= set(state['resolved']) and not DEBTS.intersection(state['open']), 'final-debt')
    need(state['a04a'] == 'complete', 'final-a04a')
    c = proof.get('candidate')
    need(bool(c), 'candidate-missing')
    sha = c['candidate_sha']
    need(bool(re.fullmatch('[0-9a-f]{40}', sha)) and c['base_sha'] == contract['base_revision'] and c['recorded_at'], 'candidate-identity')
    need(state['candidate_object_exists'] and set(c['source_sha256']) == SOURCES, 'candidate-tree')
    need(c['source_sha256'] == state['git_source_sha256'] == state['current_source_sha256'], 'source-digest')
    archives = proof['archives']
    red = proof.get('red')
    need(bool(red), 'red-missing')
    need(red['source_ref'] == contract['base_revision'] and red['command'] == contract['verification'][0]['red_command'], 'red-base')
    need(red['exit_code'] == 1 and red['recorded_before_repair'] is True, 'red-result')
    need(red['evidence'] == PROOF + '00-c13-red-base.txt' and red['required_diagnostic'] == 'C13 RESTORATION FAIL', 'red-binding')
    need(red['evidence'] in archives and red['required_diagnostic'] in archives[red['evidence']].decode(), 'red-output')
    need(hashlib.sha256(archives[red['evidence']]).hexdigest() == red['log_sha256'], 'red-digest')
    ci = proof.get('ci')
    need(bool(ci), 'ci-missing')
    need(ci['candidate_sha'] == sha and ci['repository'] == 'niq-cnr/nizam-framework' and ci['conclusion'] == 'success', 'ci-candidate')
    need(isinstance(ci['run_id'], int) and ci['run_url'] == 'https://github.com/niq-cnr/nizam-framework/actions/runs/' + str(ci['run_id']), 'ci-run')
    need(ci['started_at'] and ci['completed_at'] and len(ci['checks']) == 3, 'ci-checks')
    for actual, expected in zip(ci['checks'], contract['verification'][:3]):
        need(actual['candidate_sha'] == sha and actual['command'] == expected['command'] and actual['evidence'] == expected['evidence'], 'ci-command')
        need(bool(re.fullmatch('[0-9a-f]{40}', actual['checkout_sha'])) and actual['source_sha256'] == c['source_sha256'], 'ci-checkout-source')
        need(actual['exit_code'] == 0 and actual['conclusion'] == 'success', 'ci-result')
        need(actual['run_id'] == ci['run_id'] and actual['run_url'] == ci['run_url'], 'ci-run-binding')
        need(isinstance(actual['job_id'], int) and actual['job_url'] == ci['run_url'] + '/job/' + str(actual['job_id']), 'ci-job')
        need(actual['step_name'] and actual['started_at'] and actual['completed_at'], 'ci-step')
        need(actual['evidence'] in archives and hashlib.sha256(archives[actual['evidence']]).hexdigest() == actual['log_sha256'], 'ci-log')
    qa = proof.get('qa')
    need(bool(qa), 'qa-missing')
    need(qa['candidate_sha'] == sha and qa['qa_pass'] is True and qa['final_verdict']['approved'] is True, 'qa-candidate')
    need(qa['checks_run'] == qa['checks_passed'] == 6 and all(not qa[k] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), 'qa-result')
    need(len(qa['checks']) == 6, 'qa-checks')
    for actual, expected in zip(qa['checks'], contract['verification']):
        need(actual['command'] == expected['command'] and actual['evidence'] == expected['evidence'] and actual['exit_code'] == 0, 'qa-binding')
        need(actual['evidence'] in archives, 'qa-archive')
    need(PROOF + 'evidence-gate.txt' in archives and re.search(rb'(?m)^EXIT(?:[ \t]*[:=][ \t]*|[ \t]+)0[ \t]*$', archives[PROOF + 'evidence-gate.txt']), 'gate-missing')


def controls(contract):
    """Construct isolated synthetic control data; never write into the repository."""
    sha, base = 'a' * 40, contract['base_revision']
    hashes = {p: 'b' * 64 for p in SOURCES}
    state = {'open': [], 'resolved': list(DEBTS), 'a04a': 'complete', 'candidate_object_exists': True, 'git_source_sha256': hashes, 'current_source_sha256': hashes}
    archives = {x['evidence']: b'synthetic checker control' for x in contract['verification']}
    archives[PROOF + '00-c13-red-base.txt'] = b'C13 RESTORATION FAIL\nEXIT: 1\n'
    archives[PROOF + 'evidence-gate.txt'] = b'EXIT: 0\n'
    url = 'https://github.com/niq-cnr/nizam-framework/actions/runs/1'
    checks = [dict(candidate_sha=sha, checkout_sha='d'*40, source_sha256=hashes, command=x['command'], evidence=x['evidence'], exit_code=0, conclusion='success', run_id=1, run_url=url, job_id=2, job_url=url+'/job/2', step_name='control', started_at='control', completed_at='control', log_sha256=hashlib.sha256(archives[x['evidence']]).hexdigest()) for x in contract['verification'][:3]]
    proof = {'candidate': {'candidate_sha': sha, 'base_sha': base, 'recorded_at': 'control', 'source_sha256': hashes}, 'archives': archives, 'red': {'source_ref': base, 'command': contract['verification'][0]['red_command'], 'exit_code': 1, 'recorded_before_repair': True, 'evidence': PROOF+'00-c13-red-base.txt', 'required_diagnostic': 'C13 RESTORATION FAIL', 'log_sha256': hashlib.sha256(archives[PROOF+'00-c13-red-base.txt']).hexdigest()}, 'ci': {'candidate_sha': sha, 'repository': 'niq-cnr/nizam-framework', 'conclusion': 'success', 'run_id': 1, 'run_url': url, 'started_at': 'control', 'completed_at': 'control', 'checks': checks}, 'qa': {'candidate_sha': sha, 'qa_pass': True, 'final_verdict': {'approved': True}, 'checks_run': 6, 'checks_passed': 6, 'issues': [], 'missing_acceptance_coverage': [], 'unsupported_claims': [], 'checks': [dict(command=x['command'], evidence=x['evidence'], exit_code=0) for x in contract['verification']]}}
    closure('final', state, proof, contract)
    for marker in (b'EXIT:0\n', b'EXIT: 0\n'):
        p = copy.deepcopy(proof)
        p['archives'][PROOF + 'evidence-gate.txt'] = marker
        closure('final', state, p, contract)
        print('MARKER POSITIVE PASS:', marker.decode().strip())
    for marker in (b'EXIT:1\n', b'no exit marker\n'):
        p = copy.deepcopy(proof)
        p['archives'][PROOF + 'evidence-gate.txt'] = marker
        try: closure('final', state, p, contract)
        except ValueError as error: need(str(error) == 'gate-missing', 'unexpected-marker-diagnostic');print('MARKER NEGATIVE REJECTED:', marker.decode().strip())
        else: raise ValueError('bad gate marker accepted')
    intake = dict(state, open=list(DEBTS), resolved=[], a04a='pending')
    closure('intake', intake, {}, contract)
    mutations = {
        'ci-missing': lambda s,p: p.pop('ci'),
        'ci-candidate': lambda s,p: p['ci'].update(candidate_sha='c'*40),
        'ci-checks': lambda s,p: p['ci']['checks'].pop(),
        'ci-checkout-source': lambda s,p: p['ci']['checks'][0].update(source_sha256={}),
        'ci-command': lambda s,p: p['ci']['checks'][0].update(command='true'),
        'qa-missing': lambda s,p: p.pop('qa'),
        'qa-candidate': lambda s,p: p['qa'].update(candidate_sha='c'*40),
        'source-digest': lambda s,p: s.update(current_source_sha256={}),
        'gate-missing': lambda s,p: p['archives'].pop(PROOF+'evidence-gate.txt'),
        'final-debt': lambda s,p: s.update(open=['NDEBT-047']),
        'final-a04a': lambda s,p: s.update(a04a='pending'),
        'red-result': lambda s,p: p['red'].update(exit_code=2),
    }
    for code, mutate in mutations.items():
        s,p = copy.deepcopy((state,proof));mutate(s,p)
        try: closure('final',s,p,contract)
        except ValueError as error: need(str(error)==code, 'unexpected-negative-diagnostic');print('NEGATIVE REJECTED:',code)
        else: raise ValueError('negative passed: '+code)
    try: closure('final', intake, {}, contract)
    except ValueError as error: need(str(error)=='final-debt', 'intake-final-control')
    else: raise ValueError('intake accepted as final')
    print('SYNTHETIC CLOSURE CONTROLS PASS: 15 negatives and two gate-marker positives; no acceptance evidence generated')


if __name__ == '__main__':
    import json
    from pathlib import Path
    controls(json.loads(Path('/home/cnross/.tmp/nizam-maint-contract-attempt2-vq9bvve9/post-ga-maintenance-contract-r1.json').read_text()))
