#!/usr/bin/env python3
"""Independent bounded NIP planning truth, structural design and preservation checks."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import yaml
import jsonschema

BASE = '4663ab4dc39020f4d3226dc0f7e5016a835b4b04'
TASK = 'post-ga-nip-planning'
DIR = Path('.agent/evidence') / TASK
NIP3 = 'docs/nips/NIP-0003-live-runtime-sessions.md'
NIP4 = 'docs/nips/NIP-0004-workflow-assurance.md'
DAG = 'docs/planning/backlog_dag.json'
DELIVERIES = {'A03-RT','A03-WA-DRAFT','A03-WA-FINAL'}
TOPICS = {'identity','invalidation','gates','verdict','test-ownership','routing','profiles','concurrency'}
COLS = ['topic','obligation','accountable-owner','actual-input-or-proposed-precondition','executable-check-or-reviewed-design-assertion','evidence-artifact','blocking-outcome','allowed-transition','required-gate-dependencies']
CHOICES = ['choice-id','proposed-options','accountable-decision-owner','required-gate-dependencies','blocked-transition','decision-status']
ROLES = {'orchestrator','planner','generator','validator','evaluator'}
PRODUCT = {NIP3,NIP4,DAG,'docs/planning/backlog_reconciliation.md','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md','docs/planning/operator_gates.md','CHANGELOG.md'}


def need(condition, code):
    if not condition: raise ValueError(code)


def git(*args):
    return subprocess.check_output(['git',*args])


def baseline(path):
    return git('show',BASE+':'+path).decode()


def text(path):
    return Path(path).read_text()


def frontmatter(contents):
    need(contents.startswith('---\n'),'frontmatter-missing')
    value=yaml.safe_load(contents.split('---',2)[1]);jsonschema.validate(value,json.loads(text('schema/frontmatter.schema.json')))
    need(value['version']==value['change_log'][0]['version'],'frontmatter-version')
    return value


def table(contents, header):
    rows=contents.splitlines();start=next((i for i,line in enumerate(rows) if line.startswith('|') and [c.strip().lower() for c in line.strip('|').split('|')]==header),None)
    need(start is not None,'matrix-header:'+header[0]);out=[]
    for line in rows[start+2:]:
        if not line.startswith('|'):break
        fields=[x.strip() for x in line.strip('|').split('|')];need(len(fields)==len(header),'matrix-width')
        out.append(dict(zip(header,fields)))
    return out


def case_table(contents):
    match=re.search(r'(?m)^\| # \| Case \|.*(?:\n\|[^\n]*)+',contents)
    need(match is not None,'case-table-missing');return match.group()


def validate_nip3(contents, observed):
    fm=frontmatter(contents);need(fm['status']=='draft','nip3-status')
    record={r['field']:r['value'] for r in table(contents,['field','value'])};need(record.get('Decision')=='PROPOSED — awaiting H-NIP','nip3-proposal-decision')
    need(case_table(contents)==re.sub(r'\b(10[3-9]|11[0-3])\b',lambda m:str(int(m.group())+7),case_table(baseline(NIP3))),'protected-case-table')
    old=[line for line in baseline(NIP3).splitlines() if line.startswith('| Operator decision —')]
    new=[line for line in contents.splitlines() if line.startswith('| Operator decision —')]
    need(len(old)==4 and old==new,'protected-decisions')
    ids=re.findall(r'(?m)^\| (\d{3}) \|',contents);need(ids==[str(n) for n in range(110,121)],'future-feature-identities')
    need('SBCL '+observed in contents or observed in contents,'sbcl-current-version')
    need(not re.search(r'No SBCL is available locally|SBCL is not installed',contents,re.I),'stale-sbcl-premise')
    jobs=set(yaml.safe_load(text('.github/workflows/compliance.yml'))['jobs'])
    need(jobs=={'validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'},'actual-ci-jobs')
    need(all(job in contents for job in jobs),'ci-job-names')
    need(bool(re.search(r'\bfive\b',contents)) and bool(re.search(r'\bsixth\b|\bsix\b',contents)),'ci-job-count')
    need(not re.search(r'four(?:-job| CI jobs| jobs)|all four (?:CI )?jobs|four to five',contents,re.I),'stale-ci-job-count')
    need('f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852' in contents and 'v1.5.0' in contents,'release-pin')
    need(bool(re.search(r'phase\s*0?14.{0,35}complet',contents,re.I)),'phase-completion')
    need('100' in contents and '101' in contents and 'cancel' in contents.lower(),'cancelled-pilot-review')
    need('105' in contents and 'claim map' in contents.lower() and 'reus' in contents.lower(),'delivered-claim-map')
    dossier=json.loads(text('.agent/evidence/102/ga-readiness.json'))
    need(dossier['preconditions']['real_production_pilot']['status']=='not_met' and dossier['preconditions']['recorded_consumer_adoptions']['status']=='insufficient_evidence','historical-ga-input')
    debt=text('docs/planning/DEBT.md').split('## Open',1)[1].split('## Resolved',1)[0]
    need(set(re.findall(r'(?m)^\| (NDEBT-\d+) \|',debt))=={'NDEBT-040','NDEBT-034'},'current-open-debt')
    need('not_met' in contents and 'insufficient_evidence' in contents,'historical-ga-gaps')
    need('NDEBT-040' in contents and 'NDEBT-034' in contents,'current-debt-input')
    need('.agent/qa/self-commission-v1.5.0.json' in contents and '.agent/qa/post-ga-maintenance.json' in contents,'actual-planning-proof-inputs')
    need('required' in contents.lower() and 'default' in contents.lower(),'isolation-default')
    need(not re.search(r'--require-isolation[^\n]{0,55}optional|optional[^\n]{0,55}--require-isolation',contents,re.I),'isolation-optionality')
    need(not re.search(r'Expected (?:release|version)[^\n]*v1\.[45]\.0',contents,re.I),'stale-release-forecast')
    need(not re.search(r'(?:requires|depends on|prerequisite:)[^\n.]{0,80}F101|F101[^\n.]{0,80}findings (?:are )?required',contents,re.I),'stale-f101-premise')
    need('awaiting' in contents.lower() and 'H-NIP' in contents and 'selection is not activation' in contents.lower(),'nip3-pending-gates')


def validate_wa(contents):
    need(frontmatter(contents)['status']=='draft','wa-status')
    rows=table(contents,COLS);need(len(rows)==8 and {r['topic'] for r in rows}==TOPICS,'wa-topic-coverage')
    for row in rows:
        need(all(row[k] for k in COLS),'wa-empty-row')
        need(row['accountable-owner'].lower() in ROLES,'wa-owner')
        need('H-NIP' in row['required-gate-dependencies'] and 'H-PHASE' in row['required-gate-dependencies'],'wa-gate-dependencies')
        need(row['allowed-transition'].lower().split(';',1)[0].strip()=='draft-review only','wa-transition-bypass')
        need(not re.search(r'(?:pass\s+(?:accepts|activates|satisfies)|(?:automatically|bypass)\s+(?:accept|activat|H-NIP))',row['allowed-transition'],re.I),'wa-transition-bypass')
        need(re.search(r'block|reject|fail',row['blocking-outcome'],re.I),'wa-blocking-outcome')
    choices=table(contents,CHOICES);need({'candidate-invalidation','acceptance-ownership','routing-profiles','conflict-retry'}<={r['choice-id'] for r in choices} and len({r['choice-id'] for r in choices})==len(choices),'wa-choice-coverage')
    for row in choices:
        need(all(row.values()),'wa-choice-empty')
        need(row['accountable-decision-owner'].lower()=='operator','wa-decision-owner')
        need('H-NIP' in row['required-gate-dependencies'],'wa-choice-gates')
        need('pending' in row['decision-status'].lower() and 'accept' in row['decision-status'].lower(),'wa-choice-status')
        need(row['blocked-transition'].lower().startswith('draft to ') and len(row['blocked-transition'])>12,'wa-choice-blocked')
    need('proposed' in contents.lower() and 'H-NIP' in contents and 'H-PHASE' in contents,'wa-pending-gates')
    lower=" ".join(contents.lower().split())
    for code,terms in [('wa-cause-routing',['cause-based','NIP3-110']),('wa-risk-profiles',['Routine','Standard','High-assurance','preregister','shadow','A10','A11']),('wa-convergent-mapping',['convergent','AGF','blocking','advisory','empty-array']),('wa-owned-fields',['NDEBT-040','parsed','owned-field']),('wa-release-assessment',['MINOR','MAJOR']),('wa-reuse-not-scheduler',['no second scheduler'])]:
        need(all(term.lower() in lower for term in terms),code)


def registry(contents):
    rows=lambda s:[line for line in s.splitlines() if re.match(r'^\| `H-[A-Za-z0-9-]+` \|',line)]
    need(rows(contents)==rows(baseline('docs/planning/operator_gates.md')),'registry-gate-decisions')


def planning(current):
    draft_path=str(DIR/'draft-source-review.txt');draft=text(draft_path)
    need(re.search(r'(?m)^EXIT: 0$',draft) and draft.count('ACTUAL_EXIT: 0')==2,'actual-draft-review')
    recorded=json.loads(next(line.split(': ',1)[1] for line in draft.splitlines() if line.startswith('WORKTREE_SHA256: ')))
    need(all(recorded[name]==hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (NIP3,NIP4)),'draft-source-identity')
    old=json.loads(baseline(DAG));a={p['id']:p for p in old['packets']};b={p['id']:p for p in current['packets']};need(set(a)==set(b),'packet-inventory')
    for pid,p in a.items():
        q=b[pid];need(set(q)-set(p)<={'available_inputs'},'new-packet-field:'+pid);need(set(p)<=set(q),'removed-packet-field:'+pid)
        if pid in DELIVERIES:
            need(draft_path in q['evidence'],'draft-delivery-proof:'+pid)
            need(q['status']=='complete' and q['authority_status']=='authorized','draft-delivery:'+pid)
            need(q['prerequisites']['authority']['satisfied'] is True,'draft-authority:'+pid)
            exempt={'status','objective','scope','acceptance','evidence','prerequisites','available_inputs','dependency_edges','non_goals'}
            if pid=='A03-RT':exempt.add('authority_status')
            need(all(q[k]==p[k] for k in set(p)-exempt),'draft-unrelated-field:'+pid)
        else:
            need(q['status']==p['status'] and q['authority_status']==p['authority_status'] and q['prerequisites']['authority']==p['prerequisites']['authority'],'frozen-authority:'+pid)
            need(all(q[k]==p[k] for k in set(p)-{'objective','acceptance','evidence','prerequisites','available_inputs','dependency_edges','non_goals'}),'frozen-packet-fields:'+pid)
            if pid.startswith('F'):need(q==p,'canonical-feature:'+pid)
        need('F101' not in q['dependency_edges']['depends_on'],'cancelled-review-dependency:'+pid)
        for dep in q['dependency_edges']['depends_on']:
            need(dep in b and pid in b[dep]['dependency_edges']['consumed_by'],'inverse-edge:'+pid+':'+dep)
        for consumer in q['dependency_edges']['consumed_by']:
            need(consumer in b and pid in b[consumer]['dependency_edges']['depends_on'],'inverse-consumer:'+pid+':'+consumer)
    visiting=set();visited=set()
    def visit(pid):
        need(pid not in visiting,'dependency-cycle:'+pid)
        if pid in visited:return
        visiting.add(pid)
        for dep in b[pid]['dependency_edges']['depends_on']:visit(dep)
        visiting.remove(pid);visited.add(pid)
    for pid in b:visit(pid)
    for k in set(old)|set(current):
        if k not in {'packets','generated_at','base_commit','base_commit_note','plan_status_note','authorized_follow_up'}:need(current.get(k)==old.get(k),'dag-envelope:'+k)
    need(current['activated_phase']==old['activated_phase'],'phase-activation')
    need(current['authorized_follow_up'].get('numeric_feature_ids_allocated') is False,'numeric-feature-allocation')
    registry(text('docs/planning/operator_gates.md'))
    for path in ['docs/planning/backlog_reconciliation.md','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md']:
        body=text(path).split('---',2)[-1]
        if path.endswith('backlog_reconciliation.md'):body=body.split('## Prior reconciliation history',1)[0]
        elif path.endswith('HANDOVER.md'):body=body.split('## Historical handover snapshot',1)[0]
        else:body=body.split('## ',1)[-1].split('\n## ',1)[0]
        need(not re.search(r'(?:NIP-000[34]|NIP[34]|Workflow Assurance)\s+(?:is\s+)?(?:accepted|activated|implemented)\b',body,re.I),'human-current-acceptance:'+path)
    authority=json.loads(text('.agent/run_state.json'));events=authority['history'];need(any(e.get('event')=='operator_work_authorization' and e.get('contract_id')==TASK for e in events),'actual-drafting-authorization')


def scope():
    def allowed(path):
        return path in PRODUCT or path=='.agent/run_state.json' or bool(re.fullmatch(r'\.agent/(?:product_spec_post_ga_nip_planning\.md|contracts/post-ga-nip-planning\.json|(?:validator|qa)/post-ga-nip-planning(?:-[A-Za-z0-9_-]+)?\.json|evidence/post-ga-nip-planning/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+)',path))
    for line in git('diff','--name-status',BASE).decode().splitlines():
        parts=line.split('\t');need(len(parts)==2 and parts[0] in {'A','M'} and allowed(parts[1]),'scope:'+line)
    for path in git('ls-files','--others','--exclude-standard').decode().splitlines():need(allowed(path),'untracked-scope:'+path)
    old=json.loads(baseline('.agent/run_state.json'));new=json.loads(text('.agent/run_state.json'));owned={'updated_at','active_contract_id','last_action','history','circuit_breaker'}
    need(all(old.get(k)==new.get(k) for k in (set(old)|set(new))-owned),'frozen-coordinator-fields')
    need(new['history'][:len(old['history'])]==old['history'],'frozen-history')
    for event in new['history'][len(old['history']):]:
        need(event.get('contract_id',event.get('feature'))==TASK,'history-owner')
        need(event.get('event') not in {'operator_gate_decision','phase_activated'},'unapproved-gate-event')
    for k in set(old.get('circuit_breaker',{}))|set(new.get('circuit_breaker',{})):
        a=old.get('circuit_breaker',{}).get(k);b=new.get('circuit_breaker',{}).get(k)
        if a!=b:need(k.startswith(TASK+'-') and b and b['limit']==3 and 0<=b['attempts']<=3,'counter-owner')
    need(new.get('active_contract_id') in (None,old.get('active_contract_id'),TASK),'active-contract-owner')
    need(new['last_action']==old['last_action'] or TASK in new['last_action'].lower(),'last-action-owner')
    for path,marker in [('CHANGELOG.md','## [1.5.0]'),('docs/planning/HANDOVER.md','## Historical handover snapshot')]:need(baseline(path).split(marker,1)[1]==text(path).split(marker,1)[1],'frozen-section:'+path)
    old=baseline('docs/planning/backlog_reconciliation.md');new=text('docs/planning/backlog_reconciliation.md')
    marker='## Prior reconciliation history';need(old.split(marker,1)[1]==new.split(marker,1)[1],'frozen-reconciliation-history')
    provenance='96b8396c5e15e67f8e15fbadbe0798e2caf806dc'
    for path in git('ls-tree','-r','--name-only',provenance,str(DIR)).decode().splitlines():
        if '/proposal-approved/' in path or '/proposal-rejected-attempt1/' in path:
            need(git('show',provenance+':'+path)==Path(path).read_bytes(),'frozen-task-provenance:'+path)


def rejection(label, function):
    try:function()
    except ValueError as error:
        need(str(error)==label,'negative-wrong-diagnostic:'+label+':'+str(error));print('NEGATIVE REJECTED:',label)
    else:raise ValueError('negative-accepted:'+label)


def negative(observed):
    nip=text(NIP3);wa=text(NIP4);dag=json.loads(text(DAG));validate_nip3(nip,observed);validate_wa(wa);planning(dag);print('POSITIVE: complete actual proposed documents and planning pass')
    rejection('nip3-proposal-decision',lambda:validate_nip3(nip.replace('| Decision | PROPOSED — awaiting H-NIP |','| Decision | ACCEPTED — H-NIP satisfied |',1),observed))
    rejection('protected-decisions',lambda:validate_nip3(nip.replace('Neutral protocol + SBCL binding (Recommended)','forged choice',1),observed))
    rejection('protected-case-table',lambda:validate_nip3(nip.replace('| 13 | A human and an agent','| 13 | A different principal and an agent',1),observed))
    rejection('future-feature-identities',lambda:validate_nip3(re.sub(r'(?m)^\| 110 \|','| 103 |',nip,count=1),observed))
    rejection('stale-ci-job-count',lambda:validate_nip3(nip+'\nCurrent compliance: four CI jobs.\n',observed))
    rejection('stale-f101-premise',lambda:validate_nip3(nip+'\nF101 simplification findings are required.\n',observed))
    rejection('sbcl-current-version',lambda:validate_nip3(nip.replace(observed,'SBCL-NOT-PRESENT'),observed))
    rows=table(wa,COLS);victim=rows[0];old='| '+' | '.join(victim[k] for k in COLS)+' |'
    need(old in wa,'negative-table-layout')
    changed=dict(victim);changed['accountable-owner']='unknown';rejection('wa-owner',lambda:validate_wa(wa.replace(old,'| '+' | '.join(changed[k] for k in COLS)+' |',1)))
    changed=dict(victim);changed['obligation']='';rejection('wa-empty-row',lambda:validate_wa(wa.replace(old,'| '+' | '.join(changed[k] for k in COLS)+' |',1)))
    changed=dict(victim);changed['allowed-transition']='accept H-NIP automatically on pass';rejection('wa-transition-bypass',lambda:validate_wa(wa.replace(old,'| '+' | '.join(changed[k] for k in COLS)+' |',1)))
    future=next(p for p in dag['packets'] if p['id']=='PLAN-NEXT');altered=copy.deepcopy(dag);packet=next(p for p in altered['packets'] if p['id']==future['id']);packet['status']='complete';packet['authority_status']='authorized';packet['prerequisites']['authority']['satisfied']=True
    rejection('frozen-authority:PLAN-NEXT',lambda:planning(altered))
    registered=text('docs/planning/operator_gates.md');rows=[line for line in registered.splitlines() if re.match(r'^\| `H-NIP` \|',line)];need(len(rows)==1,'negative-registry-layout')
    rejection('registry-gate-decisions',lambda:registry(registered.replace(rows[0],rows[0]+' ACCEPTED NIP-0003',1)))
    print('NEGATIVE CONTROLS PASS: no setup failures count as rejection')


def observed_runtime():
    receipt=json.loads(text(DIR/'runtime.json'));actual=subprocess.check_output(['sbcl','--version'],text=True).strip();need(actual==receipt['version'],'runtime-receipt-version');return actual


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('nip3','wa','planning','scope','negative'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    try:
        if args.nip3:validate_nip3(text(NIP3),observed_runtime())
        elif args.wa:validate_wa(text(NIP4))
        elif args.planning:planning(json.loads(text(DAG)))
        elif args.scope:scope()
        else:negative(observed_runtime())
        print('CHECK PASS:',next(k for k,v in vars(args).items() if v));return 0
    except (ValueError,KeyError,OSError,subprocess.SubprocessError,jsonschema.ValidationError) as error:print('CHECK FAIL:',error);return 1


if __name__=='__main__':raise SystemExit(main())
