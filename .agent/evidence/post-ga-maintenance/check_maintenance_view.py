#!/usr/bin/env python3
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



# Runtime wrapper: all paths are repository-relative; reviewed predicates above.
import argparse
import json
import subprocess
from pathlib import Path

CONTRACT = Path('.agent/contracts/post-ga-maintenance.json')


def git(*args):
    return subprocess.check_output(['git', *args])


def source(contract):
    import jsonschema
    import yaml
    help_text = subprocess.check_output(['bash', 'tools/validate.sh', '--help'], text=True)
    paragraph = help_text.split('  --payload           ', 1)[1].split('  --help, -h', 1)[0]
    need(all(x in paragraph for x in ('methodology/', 'ecosystem/', '12 counted checks', 'C13 and C16', 'C6 is skipped')), 'payload-help')
    def remove_help(text):
        return re.sub(r'  --payload           .*?(?=  --help, -h)', '', text, flags=re.S)
    old = git('show', contract['base_revision'] + ':tools/validate.sh').decode()
    need(remove_help(old) == remove_help(Path('tools/validate.sh').read_text()), 'validator-behavior-change')
    need('Loop 1' in Path('standard/AGF.md').read_text().split('| **Evaluator** |',1)[1].split('\n',1)[0] and 'Loop 2' in Path('standard/AGF.md').read_text().split('| **Evaluator** |',1)[1].split('\n',1)[0], 'agf-role')
    template=Path('templates/AGENTS.md').read_text()
    need('`@evaluator` for independent Loop 1 contract testability review and Loop 2 implementation QA verdicts.' in template, 'template-role')
    schema=json.loads(Path('schema/frontmatter.schema.json').read_text())
    for path in ('standard/AGF.md','templates/AGENTS.md','tools/README.md','docs/planning/DEBT.md','docs/planning/backlog_reconciliation.md','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'):
        fm=yaml.safe_load(Path(path).read_text().split('---',2)[1])
        jsonschema.Draft202012Validator(schema).validate(fm)
        need(fm['version']==fm['change_log'][0]['version'], 'frontmatter-version')
    workflow=yaml.safe_load(Path('.github/workflows/compliance.yml').read_text())
    for job, required in [('fixtures_self_test',[contract['verification'][0]['command']]),('convergent_review',[contract['verification'][1]['command'],contract['verification'][2]['command'],'pip install jsonschema pyyaml'])]:
        steps=workflow['jobs'][job]['steps'];commands=[s.get('run','') for s in steps]
        need(all(x in commands for x in required), 'exact-ci-command')
        receipts=[s for s in steps if s.get('name')=='Record maintenance checkout source identity']
        need(len(receipts)==1 and 'MAINTENANCE_CHECKOUT_RECEIPT=' in receipts[0]['run'], 'ci-identity-step')
        need(all(p in receipts[0]['run'] for p in SOURCES), 'ci-source-list')
        need('source-candidate.json' not in receipts[0]['run'], 'ci-future-dependency')
    need('--allow-unsupported-isolation' not in '\n'.join(s.get('run','') for s in workflow['jobs']['convergent_review']['steps']), 'ci-required-mode')
    print('SOURCE PASS: exact help-only delta, both evaluator stages, frontmatter and stateless exact CI commands')


def scope(contract):
    base=contract['base_revision']
    product={p['path'] for p in contract['scope']['files_modify']} | {p['path'] for p in contract['scope']['files_create'] if '<' not in p['path'] and '[' not in p['path']}
    def allowed(path):
        return path in product or bool(re.fullmatch(r'\.agent/(?:product_spec_post_ga_maintenance\.md|contracts/post-ga-maintenance\.json|(?:validator|qa)/post-ga-maintenance(?:-[A-Za-z0-9_-]+)?\.json|evidence/post-ga-maintenance/[A-Za-z0-9_.-]+)',path))
    for line in git('diff','--name-status',base).decode().splitlines():
        parts=line.split('\t');need(len(parts)==2 and parts[0] in ('A','M') and allowed(parts[1]), 'source-scope:'+line)
    for path in git('ls-files','--others','--exclude-standard').decode().splitlines():need(allowed(path),'untracked-scope:'+path)
    old=json.loads(git('show',base+':.agent/run_state.json'));new=json.loads(Path('.agent/run_state.json').read_text())
    owned={'updated_at','active_contract_id','last_action','history','circuit_breaker'}
    need(all(old.get(k)==new.get(k) for k in (set(old)|set(new))-owned),'frozen-coordinator-fields')
    need(new['history'][:len(old['history'])]==old['history'],'append-only-history')
    for event in new['history'][len(old['history']):]:need(event.get('contract_id',event.get('feature'))=='post-ga-maintenance','history-ownership')
    for k in set(old.get('circuit_breaker',{}))|set(new.get('circuit_breaker',{})):
        a=old.get('circuit_breaker',{}).get(k);b=new.get('circuit_breaker',{}).get(k)
        if a!=b:need(k.startswith('post-ga-maintenance-') and b and b['limit']==3 and 0<=b['attempts']<=3,'counter-ownership')
    need(new.get('active_contract_id') in (None,old.get('active_contract_id'),'post-ga-maintenance'),'active-contract-owner')
    need(new['last_action']==old['last_action'] or 'post-ga-maintenance' in new['last_action'].lower(),'last-action-owner')
    for path,marker in [('CHANGELOG.md','## [1.5.0]'),('docs/planning/HANDOVER.md','## Historical handover snapshot')]:
        need(git('show',base+':'+path).decode().split(marker,1)[1]==Path(path).read_text().split(marker,1)[1],'frozen-history:'+path)
    current=json.loads(Path('docs/planning/backlog_dag.json').read_text());original=json.loads(git('show',base+':docs/planning/backlog_dag.json'))
    old_packets={p['id']:p for p in original['packets']};new_packets={p['id']:p for p in current['packets']}
    need(set(old_packets)==set(new_packets),'packet-inventory')
    for pid,p in old_packets.items():
        q=new_packets[pid]
        if pid=='A04a':
            need(q['authority_status']==p['authority_status'] and q['prerequisites']['authority']==p['prerequisites']['authority'],'a04a-authority')
            need(q['status'] in ('pending','complete'),'a04a-status')
            if q['status']=='pending':need(q==p,'intake-a04a-packet')
            else:
                need(all(q[k]==p[k] for k in set(p)-{'status','prerequisites','evidence'}),'final-a04a-packet')
                state,proof=load_closure('final',contract);closure('final',state,proof,contract)
        else:need(q==p,'frozen-packet:'+pid)
    need(all(current.get(k)==original.get(k) for k in (set(current)|set(original))-{'packets','authorized_follow_up'}),'frozen-dag-envelope')
    notice=current['authorized_follow_up'];need(notice['concerns']==['NDEBT-047','NDEBT-046','NDEBT-045','A04a'] and notice['numeric_feature_ids_allocated'] is False,'maintenance-boundary')
    print('SCOPE PASS: bounded source/coordination; prior evidence, installed tree, sandbox, historical sections and future packet authority unchanged')


def load_closure(stage, contract):
    debt=Path('docs/planning/DEBT.md').read_text()
    open_body=debt.split('## Open',1)[1].split('## Resolved',1)[0]
    resolved=debt.split('## Resolved',1)[1]
    rows=lambda body:set(re.findall(r'(?m)^\| (NDEBT-\d+) \|',body))
    packets=json.loads(Path('docs/planning/backlog_dag.json').read_text())['packets']
    state={'open':rows(open_body),'resolved':rows(resolved),'a04a':next(p['status'] for p in packets if p['id']=='A04a')}
    if stage=='intake':return state,{}
    candidate=json.loads(Path(PROOF+'source-candidate.json').read_text());sha=candidate['candidate_sha']
    state['candidate_object_exists']=subprocess.run(['git','cat-file','-e',sha+'^{commit}'],capture_output=True).returncode==0
    state['git_source_sha256']={p:hashlib.sha256(git('show',sha+':'+p)).hexdigest() for p in SOURCES}
    state['current_source_sha256']={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}
    archive_paths={x['evidence'] for x in contract['verification']}|{PROOF+'00-c13-red-base.txt',PROOF+'evidence-gate.txt'}
    archives={p:Path(p).read_bytes() for p in archive_paths if Path(p).is_file()}
    proof={'candidate':candidate,'ci':json.loads(Path(PROOF+'capable-ci-receipt.json').read_text()),'red':json.loads(Path(PROOF+'red-base-receipt.json').read_text()),'qa':json.loads(Path('.agent/qa/post-ga-maintenance.json').read_text()),'archives':archives}
    return state,proof


def main():
    parser=argparse.ArgumentParser(description='Bounded maintenance source/intake/final proof checker')
    modes=parser.add_mutually_exclusive_group(required=True);modes.add_argument('--source',action='store_true');modes.add_argument('--scope',action='store_true');modes.add_argument('--stage',choices=['intake','final'])
    parser.add_argument('--self-test',action='store_true');args=parser.parse_args();contract=json.loads(CONTRACT.read_text())
    try:
        if args.source:source(contract)
        elif args.scope:scope(contract)
        else:
            if args.self_test:controls(contract)
            state,proof=load_closure(args.stage,contract);closure(args.stage,state,proof,contract)
            if args.stage=='final' and args.self_test:
                mutations={
                    'ci-missing': lambda s,p:p.pop('ci'),
                    'ci-candidate': lambda s,p:p['ci'].update(candidate_sha='0'*40),
                    'ci-checkout-source': lambda s,p:p['ci']['checks'][0].update(source_sha256={}),
                    'qa-missing': lambda s,p:p.pop('qa'),
                    'qa-candidate': lambda s,p:p['qa'].update(candidate_sha='0'*40),
                    'source-digest': lambda s,p:s.update(current_source_sha256={}),
                    'gate-missing': lambda s,p:p['archives'].pop(PROOF+'evidence-gate.txt'),
                    'final-debt': lambda s,p:s.update(open=['NDEBT-047']),
                    'final-a04a': lambda s,p:s.update(a04a='pending'),
                }
                for code,mutate in mutations.items():
                    altered_state,altered_proof=copy.deepcopy((state,proof));mutate(altered_state,altered_proof)
                    try:closure('final',altered_state,altered_proof,contract)
                    except ValueError as error:need(str(error)==code,'actual-negative-diagnostic');print('ACTUAL PROOF NEGATIVE REJECTED:',code)
                    else:raise ValueError('actual proof mutation passed:'+code)
            print('REAL PARSED STAGE PASS:',args.stage)
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as error:
        print('MAINTENANCE CHECK FAIL:',error);return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
