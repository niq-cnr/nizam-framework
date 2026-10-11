#!/usr/bin/env python3
"""Independent pending-plan assertions; never execute future implementation checks."""
import argparse
import ast
import shlex
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import yaml
import jsonschema

BASE='650770d9b48c31748f24b5ac6967b80a6a46c5f7'
AUTH='87ba2ae9ae9b92565bf8bd6d5582dccb7622f881'
APPROVED='08f97b0e8b1002ac0d8362ed147e7253726a5415'
TASK='post-ga-phase015-planning'
DIR=Path('.agent/evidence')/TASK
CONTRACT=Path('.agent/contracts')/(TASK+'.json')
NIP3='docs/nips/NIP-0003-live-runtime-sessions.md'
NIP4='docs/nips/NIP-0004-workflow-assurance.md'
SPEC='.agent/product_spec_015.md'
FEATURES='.agent/feature_list_015.json'
PHASE='docs/planning/phase_015.yaml'
IDS=[str(i) for i in range(110,115)]


def need(value,code):
    if not value:raise ValueError(code)


def git(*args):return subprocess.check_output(['git',*args])

def old(path,revision=BASE):return git('show',revision+':'+path).decode()

def read(path):return Path(path).read_text()

def load(path):return json.loads(read(path))

def frontmatter(contents):
    need(contents.startswith('---\n'),'frontmatter-missing')
    value=yaml.safe_load(contents.split('---',2)[1]);jsonschema.validate(value,load('schema/frontmatter.schema.json'))
    need(value['version']==value['change_log'][0]['version'],'frontmatter-version');return value


def table(contents,headers):
    lines=contents.splitlines();start=next((i for i,line in enumerate(lines) if line.startswith('|') and [x.strip().lower() for x in line.strip('|').split('|')]==headers),None)
    need(start is not None,'table-header:'+headers[0]);rows=[]
    for line in lines[start+2:]:
        if not line.startswith('|'):break
        cells=[x.strip() for x in line.strip('|').split('|')];need(len(cells)==len(headers),'table-width');rows.append(dict(zip(headers,cells)))
    return rows


def cases(contents):
    match=re.search(r'(?m)^\| # \| Case \|.*(?:\n\|[^\n]*)+',contents);need(match is not None,'nip-cases-missing');return match.group()


def acceptance_events(state):
    return [x for x in state['history'] if x.get('event')=='operator_gate_decision' and x.get('contract_id')==TASK]


def identity():
    authority=json.loads(old('.agent/run_state.json',AUTH));actual=load('.agent/run_state.json');expected=acceptance_events(authority)
    need(len(expected)==2 and acceptance_events(actual)==expected,'accepted-events-immutable')
    for path,proposal,revision in [(NIP3,'NIP-0003','0.2.0'),(NIP4,'NIP-0004','0.1.0')]:
        event=next(e for e in expected if e['proposal']==proposal)
        need(event['accepted_source_sha']==BASE and event['accepted_revision']==revision and event['operator_verbatim']=='Approved and accepted, please proceed.','operator-decision-binding')
        need(hashlib.sha256(old(path).encode()).hexdigest()==event['accepted_document_sha256'],'accepted-source-binding')
        contents=read(path);fm=frontmatter(contents);need(fm['status']=='active' and fm['version']=='1.0.0','accepted-nip-lifecycle')
        need('accepted' in contents.split('## Status',1)[1].split('\n## ',1)[0].lower(),'accepted-nip-status')
    need(cases(read(NIP3))==cases(old(NIP3)),'protected-cases')
    choices=lambda s:[line for line in s.splitlines() if line.startswith('| Operator decision —')]
    need(choices(read(NIP3))==choices(old(NIP3)) and len(choices(read(NIP3)))==4,'protected-choices')
    headers=['choice-id','proposed-options','accountable-decision-owner','required-gate-dependencies','blocked-transition','decision-status']
    baseline=table(old(NIP4),headers);current=table(read(NIP4),headers);need(len(current)==len(baseline)==6,'wa-six-choices')
    for a,b in zip(baseline,current):
        need(all(a[k]==b[k] for k in ('choice-id','proposed-options','accountable-decision-owner')),'wa-choice-redesign')
        normalize=lambda v:re.sub(r'^(?:Draft|Accepted scope) to ', 'Scope to ',v,flags=re.I)
        need(normalize(a['blocked-transition'])==normalize(b['blocked-transition']),'wa-choice-transition-redesign')
        need('pending' in b['decision-status'].lower() and 'decision' in b['decision-status'].lower(),'wa-choice-resolved')
    matrix=['topic','obligation','accountable-owner','actual-input-or-proposed-precondition','executable-check-or-reviewed-design-assertion','evidence-artifact','blocking-outcome','allowed-transition','required-gate-dependencies']
    a=table(old(NIP4),matrix);b=table(read(NIP4),matrix);need(len(a)==len(b)==8,'wa-scope-rows')
    for x,y in zip(a,b):
        need(all(x[k]==y[k] for k in matrix if k not in {'allowed-transition','required-gate-dependencies'}),'wa-obligation-redesign')
        need('H-PHASE' in y['required-gate-dependencies'],'wa-activation-boundary')
        transition=y['allowed-transition'].lower().split(';',1)[0]
        need(('planning' in transition or 'review' in transition) and not re.search(r'(?:directly|automatically)\s+(?:execute|activate|reduce)',transition),'wa-automatic-execution')


def check_plan(f,p,contents):
    fm=frontmatter(contents)
    jsonschema.validate(f,load('schema/feature_list.schema.json'));jsonschema.validate(p,load('schema/phase.schema.json'))
    need(fm['status']=='draft' and p['status']=='pending' and f['activation_state']=='proposed' and f['phase_status']=='pending','phase-not-activated')
    need([x['id'] for x in f['features']]==IDS,'canonical-allocation')
    need(all(x['status']=='pending' and x.get('passes',False) is False and x['required_activation_gate']=='H-PHASE-015' for x in f['features']),'feature-not-started')
    need([str(x['id']) for x in p['steps']]==IDS and all(x['status']=='PENDING' for x in p['steps']),'canonical-phase-steps')
    need(f['spec_version']==fm['version'],'spec-feature-version')
    need([x['dependencies'] for x in f['features']]==[[],['110'],['111'],['112'],['113']],'canonical-dag-chain')
    need(sum(x['estimated_lines'] for x in f['features'])==f['original_estimate_lines']==7200 and f['ceiling_130pct']==9360,'budget-sum-ceiling')
    basis=f['budget_basis'];ledger=json.loads(old('.agent/run_state.json'))['scope_budget'];chosen=[x for x in ledger['per_feature'] if x['id'] in basis['selected_comparables']['ids']]
    need(basis['proposed_only'] is True and 'inside' in basis['phase_level_costs'].lower() and '7200' in basis['phase_level_costs'],'proposed-budget-envelope')
    need(basis['selected_comparables']['ids']==['104','105','106','107','109','108','102'] and sum(x['actual'] for x in chosen)==basis['selected_comparables']['actual_total']==5933 and sum(x['estimated'] for x in chosen)==basis['selected_comparables']['estimate_total']==5110,'budget-observed-basis')
    need(basis['prior_three_actuals']==[x['actual'] for x in ledger['per_feature'][-3:]]==[836,851,906],'budget-rolling-basis')
    need(basis['historical_phase014_total']==ledger['total_lines_changed']==8705 and basis['historical_phase014_feature_sum']==sum(x['actual'] for x in ledger['per_feature'])==7414 and basis['historical_phase014_phase_level_items']==sum(x['actual'] for x in ledger['phase_level_items'])==1291,'historical-budget-basis')
    need(set(basis['counted'])=={'product','contract','verdict','audit','planning'} and set(basis['excluded'])=={'raw evidence','run_state'} and basis['unclassified']=='fail closed','counting-classification')
    need('7200' in contents and '9360' in contents and 'H-PHASE-015' in contents and 'OUTSTANDING' in contents,'plan-budget-gate-text')
    for feature in f['features']:
        availability=feature['acceptance_availability'].lower();need('future' in availability and re.search(r'not executed|executes no feature acceptance',availability),'future-ac-stage')
        need(set(feature['new_output_targets'])|set(feature['existing_targets_to_amend'])==set(feature['future_output_targets']),'future-target-classification')
        need(all(not Path(path).exists() for path in feature['new_output_targets']),'future-output-present')
        need(all(Path(path).is_file() for path in feature['existing_targets_to_amend']),'amended-source-missing')
        for command in feature['acceptance_tests']:
            argv=shlex.split(command);need(argv[:2] in (['python3','-c'],['bash','-c']) or (len(argv)>1 and Path(argv[1]).is_file()),'future-command-tool')
            need(subprocess.run(['bash','-n'],input=command,text=True,capture_output=True).returncode==0,'future-command-syntax')
            if argv[:2]==['python3','-c']:
                tree=ast.parse(argv[2])
                for node in ast.walk(tree):
                    if isinstance(node,ast.GeneratorExp) and isinstance(node.elt,ast.Compare) and any(isinstance(op,ast.In) for op in node.elt.ops):
                        need(not any(isinstance(gen.iter,(ast.List,ast.Tuple)) and all(isinstance(v,ast.Constant) and isinstance(v.value,str) for v in gen.iter.elts) for gen in node.generators),'marker-only-ac')
            need(not any(token in (';','&&','||') for token in argv),'non-atomic-ac')
    fixture_owner=f['features'][1];fixtures=fixture_owner['fixture_plan'];need(len(fixtures)==f['fixtures_total']==18 and len({x['name'] for x in fixtures})==18,'fixture-inventory')
    byname={x['name']:x for x in fixtures}
    for fixture in fixtures:
        need(fixture['path']=='tools/fixtures/'+fixture['name'] and fixture['path'] in fixture_owner['new_output_targets'],'fixture-top-level')
        need(fixture['owner_feature']=='111' and fixture['proof_stage']=='015 schema-level only','fixture-proof-owner')
        positive=fixture['kind']=='positive';need(fixture['kind'] in {'positive','negative'} and fixture['family'] in {'session','operation'} and fixture['name'].startswith('runtime_'+fixture['family']+'_') and ('_valid_' if positive else '_neg_') in fixture['name'],'fixture-family-kind')
        expected=0 if positive else 1;diagnostic='[C12] PASS' if positive else '[C12] FAIL';need(fixture['expected_exit']==expected and fixture['expected_diagnostic']==diagnostic,'fixture-exit-diagnostic')
        commands=[c for c in fixture_owner['acceptance_tests'] if '--target '+fixture['path'] in c]
        need(len(commands)==1 and diagnostic in commands[0] and ('-eq '+str(expected)) in commands[0],'fixture-target-exit-diagnostic')
        need(fixture['cases'] and all(1<=case<=13 and case!=2 for case in fixture['cases']) and fixture['purpose'],'fixture-case-ownership')
    for family in ('session','operation'):need({x['kind'] for x in fixtures if x['family']==family}=={'positive','negative'},'fixture-family-coverage')
    matrix=f['case_matrix'];need([r['case'] for r in matrix]==list(range(1,14)) and fixture_owner['case_matrix']==matrix,'case-matrix-inventory')
    runtimes={1:'Stub',2:'Stub',3:'Stub',4:'SBCL',5:'Stub and SBCL',6:'Stub and SBCL',7:'SBCL',8:'Stub policy and CI isolation mechanism',9:'Stub',10:'Stub and SBCL',11:'SBCL',12:'SBCL',13:'Stub'}
    for row in matrix:
        need(row['schema_owner']=='111' and row['live_required'] is True and row['claim_working'] is False and row['live_status'].startswith('pending') and 'phase016' in row['live_owner'],'case-proof-stage')
        need(row['live_runtime']==runtimes[row['case']],'case-live-runtime')
        need(set(row['schema_fixtures'])=={x['name'] for x in fixtures if row['case'] in x['cases']},'fixture-case-map')
    need(not matrix[1]['schema_fixtures'] and matrix[11]['schema_fixtures']==matrix[6]['schema_fixtures'] and 'runtime-only' in matrix[11]['schema_limit'],'runtime-only-limit')
    adapter=f['adapter_obligations'];need(adapter=={'optional_capability':'live_runtime_session','required':False,'interface_section5_item_count':10,'existing_nonclaiming_adapters_conformant':True,'no_trial_session_execution':True,'source_registration_owner':'113','installed_upgrade':False},'optional-compatibility')
    registration=f['source_registration_obligations'];need([r['feature'] for r in registration]==['110','111','112','113'],'source-registration-wave')
    for row in registration:need(set(row['modules']+row['same_feature_registry'])<=set(next(x for x in f['features'] if x['id']==row['feature'])['future_output_targets']),'same-feature-registration')
    need(re.search(r'no (?:fixed release|release version forecast)',contents,re.I),'no-release-forecast')
    obligations=fixture_owner['schema_obligations'];need(obligations['draft']=='2020-12' and obligations['all_object_nodes_closed'] is True and obligations['required_fields_minimal'] is True and obligations['router_before_contract_id'] is True and obligations['consumer_payload_compatibility'] is True and obligations['c17_free'] is True,'schema-protocol-obligations')
    need(set(obligations['phase016_fields_represented'])=={'isolation','toolchain_identity','lock_ref','core_provenance','wait_outcome','lease_epoch','lane_authorization_ref'},'schema-fields-from-outset')
    need(obligations['stale_generation_relational_negative']=='tools/fixtures/runtime_operation_neg_stale_generation_executed.json' and obligations['stale_generation_expected_exit']==1 and obligations['stale_generation_expected_diagnostic']=='[C12] FAIL','schema-relational-proof')
    need(all(token in contents for token in ('C17 stays','router before contract_id','0.2.0','0.3.0','next MINOR','H-FRAMEWORK-RELEASE')),'normative-surface-boundaries')


def plan():check_plan(load(FEATURES),yaml.safe_load(read(PHASE)),read(SPEC))

def projection():
    current=load('docs/planning/manifest.json');baseline=json.loads(old('docs/planning/manifest.json'))
    need(current['phases'][:-1]==baseline['phases'] and len(current['phases'])==len(baseline['phases'])+1,'manifest-append-only')
    appended=current['phases'][-1];need(appended['id']=='015-live-runtime-normative' and appended['status']=='pending' and appended['activation_state']=='proposed','manifest-candidate-only')
    need(current['current_phase']==baseline['current_phase']=='014-ga-track','manifest-current-phase')
    need(all(current.get(k)==baseline.get(k) for k in (set(current)|set(baseline))-{'updated_at','phases'}),'manifest-frozen-fields')
    need(appended['feature_list']==FEATURES and appended['phase_definition']==PHASE,'manifest-canonical-links')
    previous=json.loads(old('docs/planning/backlog_dag.json'));actual=load('docs/planning/backlog_dag.json');a={x['id']:x for x in previous['packets']};b={x['id']:x for x in actual['packets']}
    need(set(a)==set(b),'packet-inventory');special={'PLAN-NEXT','PLAN-WA','PLAN-016'}
    for pid,p in a.items():
        q=b[pid];need(set(q)-set(p)<={'canonical_feature_id','allocation_status','available_inputs'},'new-packet-field:'+pid)
        if pid=='PLAN-NEXT':
            need(q['status']=='complete' and q['prerequisites']['authority']['satisfied'] is True,'plan-delivery')
            proof=load(DIR/'plan-source-proof.json');need(proof['exit_code']==0 and proof['proof_stage']=='independent-development-plan-assessment','actual-plan-review')
            need(all(proof['source_sha256'][path]==hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in (SPEC,FEATURES,PHASE)),'plan-delivery-identity')
            need(str(DIR/'plan-source-review.txt') in q['evidence'],'plan-delivery-evidence')
        elif pid.startswith('NIP3-') and pid[-3:] in IDS:
            need(q['status']=='pending' and q['prerequisites']['authority']['satisfied'] is False and q['authority_status']=='blocked-on-H-PHASE-015','implementation-not-authorized:'+pid)
            need(q.get('canonical_feature_id')==pid[-3:],'canonical-packet-mapping:'+pid)
        elif pid in {'PLAN-WA','PLAN-016'}:
            need(q['status']=='pending' and q['prerequisites']['authority']['satisfied'] is True and q['prerequisites']['technical']['satisfied'] is False,'follow-on-planning-stage:'+pid)
        else:
            need(q['status']==p['status'] and q['authority_status']==p['authority_status'] and q['prerequisites']['authority']['satisfied']==p['prerequisites']['authority']['satisfied'] and set(q['prerequisites']['authority'])==set(p['prerequisites']['authority']),'frozen-authority:'+pid)
            if pid.startswith('F'):need(q==p,'frozen-canonical014:'+pid)
        need(q['dependency_edges']==p['dependency_edges'],'frozen-dependency-edges:'+pid)
        allowed={'objective','mapped_ids','provisional_feature_id','acceptance','evidence','prerequisites','available_inputs','canonical_feature_id','allocation_status'}
        if pid.startswith('NIP3-') and pid[-3:] in IDS:
            allowed|={'phase_id_proposed','retry_identity','estimate'}
            expected=next(x['estimated_lines'] for x in load(FEATURES)['features'] if x['id']==pid[-3:]);need(q['estimate']['weighted_lines']==[expected,expected],'canonical-estimate:'+pid)
        if pid in special:allowed|={'status','authority_status'}
        need(all(q[k]==p[k] for k in set(p)-allowed),'packet-unrelated-field:'+pid)
    need(actual['activated_phase']==previous['activated_phase'],'dag-current-phase')
    need('NIP3-114' in b['PLAN-WA']['dependency_edges']['serialize_after'] and b['PLAN-016']['dependency_edges']['serialize_after']==['PLAN-WA'],'follow-on-ordering')
    for path in ['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md','docs/planning/backlog_reconciliation.md']:
        contents=read(path).split('---',2)[-1];contents=contents.split('## Prior reconciliation history',1)[0].split('## Historical handover snapshot',1)[0]
        need(not re.search(r'H-PHASE-0?15[^\n]{0,40}(?:SATISFIED|EXERCISED|ACTIVATED)',contents,re.I),'human-activation-spoof:'+path)


def scope():
    current_contract=load(CONTRACT);c=json.loads(old(str(CONTRACT),APPROVED))
    for key in ('scope','non_goals','spec_ref','base_revision','verification','design_notes','estimated_lines','evidence_dir','evidence_convention'):
        need(current_contract[key]==c[key],'approved-contract-binding:'+key)
    need(read(c['spec_ref'])==old(c['spec_ref'],APPROVED),'approved-task-spec')
    products={x['path'] for x in c['scope']['files_modify']}|{x['path'] for x in c['scope']['files_create'] if '<' not in x['path'] and '[' not in x['path']}
    def allowed(path):return path in products or bool(re.fullmatch(r'\.agent/(?:product_spec_post_ga_phase015_planning\.md|contracts/post-ga-phase015-planning\.json|(?:validator|qa)/post-ga-phase015-planning(?:-[A-Za-z0-9_-]+)?\.json|evidence/post-ga-phase015-planning/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+)',path))
    for line in git('diff','--name-status',BASE).decode().splitlines():
        fields=line.split('\t');need(len(fields)==2 and fields[0] in {'A','M'} and allowed(fields[1]),'scope:'+line)
    for path in git('ls-files','--others','--exclude-standard').decode().splitlines():need(allowed(path),'untracked-scope:'+path)
    before=json.loads(old('.agent/run_state.json',APPROVED));after=load('.agent/run_state.json');owned={'updated_at','active_contract_id','last_action','history','circuit_breaker'}
    need(all(before.get(k)==after.get(k) for k in (set(before)|set(after))-owned),'frozen-position-budget-fields')
    need(after['history'][:len(before['history'])]==before['history'],'frozen-operator-history')
    for event in after['history'][len(before['history']):]:
        need(event.get('contract_id',event.get('feature'))==TASK,'history-owner');need(event.get('event') not in {'operator_gate_decision','phase_activated'},'new-gate-smuggling')
    for key in set(before.get('circuit_breaker',{}))|set(after.get('circuit_breaker',{})):
        a=before.get('circuit_breaker',{}).get(key);b=after.get('circuit_breaker',{}).get(key)
        if a!=b:need(key.startswith(TASK+'-') and b and b['limit']==3 and 0<=b['attempts']<=3,'counter-owner')
    need(after.get('active_contract_id') in (None,before.get('active_contract_id'),TASK),'active-contract-owner')
    need(after['last_action']==before['last_action'] or TASK in after['last_action'].lower(),'last-action-owner')
    for path,marker in [('CHANGELOG.md','## [1.5.0]'),('docs/planning/HANDOVER.md','## Historical handover snapshot'),('docs/planning/backlog_reconciliation.md','## Prior reconciliation history')]:need(old(path).split(marker,1)[1]==read(path).split(marker,1)[1],'frozen-history:'+path)
    for path in git('ls-tree','-r','--name-only',APPROVED,str(DIR)).decode().splitlines():
        if '/proposal-' in path:need(git('show',APPROVED+':'+path)==Path(path).read_bytes(),'frozen-proposal-proof:'+path)


def rejects(expected,operation):
    try:operation()
    except ValueError as error:need(str(error)==expected,'wrong-negative-diagnostic:'+expected+':'+str(error));print('NEGATIVE REJECTED:',expected)
    else:raise ValueError('negative-accepted:'+expected)


def override(path,contents,operation):
    original=globals()['read'];globals()['read']=lambda name:contents if str(name)==path else original(name)
    try:return operation()
    finally:globals()['read']=original


def negative():
    identity();plan();projection();scope();print('POSITIVE: actual accepted scopes, pending plan and preserved current projection pass')
    f=load(FEATURES);p=yaml.safe_load(read(PHASE));contents=read(SPEC)
    controls=[
        ('phase-not-activated',lambda f,p:p.update(status='in_progress')),
        ('feature-not-started',lambda f,p:f['features'][0].update(status='complete')),
        ('canonical-allocation',lambda f,p:f['features'].append(copy.deepcopy(f['features'][-1]))),
        ('canonical-dag-chain',lambda f,p:f['features'][2].update(dependencies=['999'])),
        ('canonical-dag-chain',lambda f,p:f['features'][0].update(dependencies=['114'])),
        ('budget-sum-ceiling',lambda f,p:f.update(original_estimate_lines=7201)),
        ('budget-sum-ceiling',lambda f,p:f.update(ceiling_130pct=9400)),
        ('fixture-proof-owner',lambda f,p:f['features'][1]['fixture_plan'][0].update(owner_feature='110')),
        ('case-proof-stage',lambda f,p:(f['case_matrix'][0].update(claim_working=True),f['features'][1]['case_matrix'][0].update(claim_working=True))),
        ('optional-compatibility',lambda f,p:f['adapter_obligations'].update(required=True)),
        ('future-ac-stage',lambda f,p:f['features'][0].update(acceptance_availability='Future implementation acceptance already passed')),
        ('marker-only-ac',lambda f,p:f['features'][0]['acceptance_tests'].append("python3 -c 's=open(\"methodology/10_live_runtime_sessions.md\").read(); assert all(t in s for t in [\"owner\",\"image\"])'")),
    ]
    for expected,mutate in controls:
        a,b=copy.deepcopy((f,p));mutate(a,b);rejects(expected,lambda:check_plan(a,b,contents))
    source=read(NIP3);rejects('protected-cases',lambda:override(NIP3,source.replace('| 13 | A human and an agent','| 13 | A changed agent and human',1),identity))
    source=read(NIP4);line=next(line for line in source.splitlines() if line.startswith('| candidate-invalidation |'));altered=re.sub(r'pending operator[^|]*','resolved operator decision ',line,flags=re.I)
    need(altered!=line,'negative-choice-layout');rejects('wa-choice-resolved',lambda:override(NIP4,source.replace(line,altered,1),identity))
    manifest=load('docs/planning/manifest.json');manifest['current_phase']='015-live-runtime-normative';rejects('manifest-current-phase',lambda:override('docs/planning/manifest.json',json.dumps(manifest),projection))
    contract=load(CONTRACT);contract['scope']['files_create'].append({'path':'tools/forged-runtime.py','purpose':'forged scope'});rejects('approved-contract-binding:scope',lambda:override(str(CONTRACT),json.dumps(contract),scope))
    state=load('.agent/run_state.json');state['history'].append({'event':'operator_gate_decision','contract_id':TASK,'gate':'H-PHASE-015','decision':'activated'});rejects('new-gate-smuggling',lambda:override('.agent/run_state.json',json.dumps(state),scope))
    dag=load('docs/planning/backlog_dag.json');packet=next(x for x in dag['packets'] if x['id']=='NIP3-110');packet['status']='in_progress';packet['authority_status']='authorized';packet['prerequisites']['authority']['satisfied']=True
    rejects('implementation-not-authorized:NIP3-110',lambda:override('docs/planning/backlog_dag.json',json.dumps(dag),projection))
    print('NEGATIVE CONTROLS PASS: eighteen independent intended failures; setup/schema errors cannot count as rejection')


def main():
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    for mode in ('identity','plan','projection','scope','negative'):g.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    try:
        mode=next(k for k,v in vars(args).items() if v);globals()[mode]();print('CHECK PASS:',mode);return 0
    except (ValueError,KeyError,IndexError,StopIteration,OSError,subprocess.SubprocessError,jsonschema.ValidationError) as e:print('CHECK FAIL:',e);return 1


if __name__=='__main__':raise SystemExit(main())
