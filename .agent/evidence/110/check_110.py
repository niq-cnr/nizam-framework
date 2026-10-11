#!/usr/bin/env python3
"""Independent documented-policy checks. These assertions never enforce a live session."""
import argparse,copy,hashlib,json,re,subprocess,sys
from pathlib import Path
import yaml,jsonschema
BASE='06c0ae0a273facce80c57506260648c41f566ebb'
APPROVED='d1ba9e99f148b3e42d8cf705aef0eb3b12de944c'
TASK='110'
DIR=Path('.agent/evidence/110')
DOC='methodology/10_live_runtime_sessions.md'
NIP3='docs/nips/NIP-0003-live-runtime-sessions.md'
NIP4='docs/nips/NIP-0004-workflow-assurance.md'
CONTRACT='.agent/contracts/110.json'
class InvariantError(Exception):pass
def need(value,name):
    if not value:raise InvariantError(name)
def git(*args):return subprocess.check_output(['git',*args])
def old(path,ref=BASE):return git('show',ref+':'+str(path)).decode()
def read(path):return Path(path).read_text()
def load(path):return json.loads(read(path))
def clean(text):return re.sub(r'<!--.*?-->','',text,flags=re.S)
def norm(text):return re.sub(r'\s+',' ',clean(text)).strip().lower()
def section(path,heading):
    text=clean(read(path));m=re.search(r'(?m)^'+heading+r'\s*$',text);need(m is not None,'section-missing:'+path+':'+heading)
    depth=len(m.group().split(' ',1)[0]);tail=text[m.end():];end=re.search(r'(?m)^#{1,'+str(depth)+r'} ',tail);s=tail[:end.start()] if end else tail
    need(len(norm(s))>40,'section-empty:'+path);return s
def fm(path,version,status='active'):
    text=read(path);need(text.startswith('---\n'),'frontmatter:'+path);v=yaml.safe_load(text.split('---',2)[1]);jsonschema.validate(v,load('schema/frontmatter.schema.json'));need(v['version']==version and v['status']==status and v['change_log'][0]['version']==version,'version:'+path);return v
def table(text):
    rows=[]
    for line in clean(text).splitlines():
        if line.startswith('|') and not re.fullmatch(r'[| :\-]+',line):rows.append([x.strip().strip('`') for x in line.strip('|').split('|')])
    return rows
def has(text,pattern,name):need(re.search(pattern,norm(text)) is not None,name)

def protocol():
    need(Path(DOC).is_file(),'protocol-document-missing');v=fm(DOC,'0.1.0');need(v.get('enforcement')=='consumer-aspirational','protocol-enforcement-honesty')
    need(not re.search(r'\b(?:sbcl|asdf|common lisp|slime|sly)\b',norm(read(DOC))),'neutral-not-language-binding')
    source=section(DOC,r'## [0-9]+[.] Source, image and durable records');has(source,r'source.{0,180}image.{0,250}(?:durable|record)','source-image-distinction');has(source,r'(?:record|provenance).{0,160}(?:not|never|cannot).{0,80}prov(?:e|en|ing)|record.{0,180}not.{0,80}prov','records-not-live-proof')
    own=section(DOC,r'## [0-9]+[.] Ownership and leases');has(own,r'(?:reject.{0,100}foreign|foreign.{0,100}reject).{0,180}before.{0,40}execut','owner-before-execution');has(own,r'reject.{0,140}stale lease|stale lease.{0,150}reject','lease-before-execution');has(own,r'transfer.{0,200}(?:increment|advance).{0,50}lease','explicit-lease-transfer')
    acceptance=section(DOC,r'## [0-9]+[.] Fresh-environment acceptance');has(acceptance,r'committed.{0,100}source','acceptance-committed-source');has(acceptance,r'fresh.{0,50}process','acceptance-fresh-process');has(acceptance,r'(?:fresh|empty|private).{0,80}(?:build|cache)','acceptance-fresh-build');has(acceptance,r'(?:development|session).{0,150}(?:never|not|cannot).{0,100}acceptance.{0,60}evidence','development-not-acceptance')
    # Structured rows identify obligations; semantic review assesses the normative meaning.
    rows=table(read(DOC));need(any(len(r)>=3 and 'requirement' in r[0].lower() for r in rows),'protocol-policy-table')
    anchors=[('R1','Source, image and durable records'),('R2','Ownership and leases'),('R3','Process generations'),('R4','Serialized operations'),('R5','Status and wait outcomes'),('R6','Condition capture and failed loads'),('R7','Fresh-environment acceptance'),('R8','Handoff and context-reset re-entry'),('R9','External resources'),('R10','Review trials'),('R11','Implementation lanes'),('R12','Durable records')]
    for rid,title in anchors:
        part=section(DOC,r'## [0-9]+[.] '+re.escape(title));rows=table(part)
        need(any([v.lower() for v in row]==['requirement-id','normative-rule','evidence-boundary'] for row in rows),'policy-header:'+rid)
        row=[r for r in rows if r[0]==rid];need(len(row)==1 and len(row[0])==3 and all(row[0]),'policy-row:'+rid)
        prose=re.sub(r'(?m)^\|.*$', '',part);need(len(norm(prose))>80,'policy-explanation:'+rid)
        rules={
          'R1':r'(?:MUST NOT|cannot).{0,100}(?:assert source/heap identity|acceptance evidence)',
          'R2':r'reject foreign.{0,100}stale leases before execution',
          'R3':r'reject a stale expected_generation before execution',
          'R4':r'reject concurrent submits while an operation is outstanding',
          'R5':r'stopped_waiting MUST NOT imply cancelled or terminated',
          'R6':r'capture conditions before unwinding and MUST NOT claim image consistency after a failed',
          'R7':r'acceptance from committed source in a fresh process with a fresh private build cache',
          'R8':r're.entry MUST check durable records.{0,150}reconstruct',
          'R9':r'declare synchronization limits and explicitly coordinate shared effects',
          'R10':r'MUST be denied a session endpoint and all lifecycle, operate and accept permissions',
          'R11':r'one implementation lane by default.{0,80}additional lanes require separate authorization',
          'R12':r'preserve unowned fields.{0,100}coordination and circuit counters to the Orchestrator',
        }
        has(' '.join(row[0][1:]),rules[rid].lower(),'policy-obligation:'+rid)
    text=norm(read(DOC));checks={
      'runtime-agent-distinction':r'runtime session is.{0,130}process.{0,400}agent session is.{0,140}context',
      'generation-before-execution':r'(?:reject.{0,60}stale.{0,50}generation|stale.{0,80}generation.{0,120}reject).{0,80}before.{0,40}execut',
      'single-operation':r'(?:at most one|one operation).{0,100}(?:in.flight|outstanding)',
      'timeout-not-cancelled':r'(?:timeout|stopped_waiting).{0,200}(?:not|never|does not).{0,100}(?:cancel|stop|end)',
      'capture-before-unwind':r'captur.{0,120}before.{0,60}unwind',
      'failed-load-not-consistent':r'(?:not|never).{0,40}claim image consistency after a failed|inconsistent after a failed',
      'handoff-reentry':r'(?:context.reset|re.entry).{0,600}outstanding.{0,250}(?:manifest|source)',
      'external-synchronization':r'external.{0,300}(?:synchroni|transaction|rollback)',
      'trial-no-endpoint':r'trial.{0,200}(?:never|denied|no).{0,100}(?:endpoint|capabilit)',
      'single-lane':r'(?:one|single) implementation lane',
      'durable-field-ownership':r'(?:field ownership|owned fields|field.owner|preserve unowned fields)',
    }
    for code,pattern in checks.items():has(text,pattern,code)
    for status in ('completed','condition_signalled','cancelled','terminated','rejected','running','cancel_requested','unknown'):need(status in text,'status-vocabulary:'+status)
    has(text,r'rejected.{0,180}(?:never|not|without).{0,50}execut','rejected-never-executed')
    has(text,r'(?:future|later).{0,60}features? 111[–-]113|feature.{0,150}111.{0,200}112.{0,200}113','future-mechanisms-not-claimed')

def attempts():
    fm('methodology/02_adversarial_tdd.md','0.5.0');fm('methodology/03_circuit_breaker.md','0.3.0')
    s=section('methodology/02_adversarial_tdd.md',r'## 2[.] Evaluator Independence');has(s,r'4[.].{0,150}own execution context','own-context-item4');has(s,r'fresh.{0,60}process','own-context-process');has(s,r'(?:fresh|private).{0,80}(?:build|cache)','own-context-build');has(s,r'fixtures.{0,100}committed source','own-context-fixtures')
    s=section('methodology/03_circuit_breaker.md',r'### 3[.]2[.]? What counts as an attempt');n=norm(s)
    for identity in ('contract_id','step_key','attempt'):need(identity in n,'attempt-identity:'+identity)
    for label in ('process','agent','context','worktree','generation','stage'):need(label in n,'attempt-continuity:'+label)
    has(s,r'(?:process|generation).{0,200}(?:not|never).{0,80}reset','attempt-no-reset')
    has(s,r'(?:before|pre.declar).{0,130}(?:outcome|negative)|(?:outcome|negative).{0,100}before','predeclared-outcome');has(s,r'(?:failed|failure).{0,180}(?:not|never|cannot).{0,100}(?:relabel|probe)','failed-repair-not-probe');has(s,r'(?:distinct|separate).{0,130}(?:step|counter)','distinct-step-counters')
    base=old('methodology/03_circuit_breaker.md').split('## 3. The Per-Attempt Strategy Table',1)[1];current=read('methodology/03_circuit_breaker.md').split('## 3. The Per-Attempt Strategy Table',1)[1];need(base.split('### 3.1 Attempt isolation')[0]==current.split('### 3.1 Attempt isolation')[0],'frozen-three-strike-ladder');need(old('methodology/03_circuit_breaker.md').split('## 4. Attempt 4 Is Forbidden',1)[1]==read('methodology/03_circuit_breaker.md').split('## 4. Attempt 4 Is Forbidden',1)[1],'frozen-halt-and-counter-mechanics')

def permissions():
    fm('standard/permission_classes.md','0.3.0');s=section('standard/permission_classes.md',r'## 5[.] Runtime Session Permission Classes');rows=table(s);by={r[0]:r for r in rows if r and r[0].startswith('runtime.session.')};need(set(by)=={'runtime.session.lifecycle','runtime.session.operate','runtime.session.accept'},'permission-class-inventory')
    for key,role in [('lifecycle','Orchestrator'),('operate','Generator'),('accept','Evaluator')]:need(by['runtime.session.'+key][1]==role,'permission-role:'+key)
    lifecycle=by['runtime.session.lifecycle'];need(len(lifecycle)==4 and any(r[2].lower().startswith('allowed') and r[3].lower().startswith('denied') for r in rows if len(r)==4),'permission-allow-deny-columns');has(lifecycle[2],r'open.{0,100}transfer.{0,100}close','lifecycle-only');need(not re.search(r'evaluat|load|compil|run tests|observe|bash',norm(lifecycle[2])) and all(x in norm(lifecycle[3]) for x in ('evaluate','load','compile','observe','bash')),'lifecycle-no-evaluation');has(' '.join(by['runtime.session.operate']),r'own.{0,40}session','operate-own-image');has(' '.join(by['runtime.session.accept']),r'(?:fresh|hermetic)','accept-hermetic-only');has(s,r'trial.{0,140}(?:denied|no|never).{0,140}(?:three|all|class|session)','trial-all-classes-denied')
    need(clean(old('standard/permission_classes.md')).split('## 2.',1)[1].strip()==clean(read('standard/permission_classes.md')).split('## 2.',1)[1].split('## 5.',1)[0].strip(),'existing-permission-defaults')
    fm('standard/convergent_code_review.md','1.3.1');s=section('standard/convergent_code_review.md',r'## 5[.] Three Independent Trials');has(s,r'trial.{0,100}(?:never|no|denied).{0,100}session endpoint','review-trial-no-endpoint')
    fm('standard/definition_of_done.md','0.3.0');s=section('standard/definition_of_done.md',r'## 4[.].*');has(s,r'(?:handoff|runtime).{0,500}(?:reconstruct|provenance)','runtime-handoff-done')

def registration():
    d=load('NIZAM.json');b=json.loads(old('NIZAM.json'));need(d['framework']==b['framework'],'framework-version-unchanged');need(any(x['authoritative_source']==DOC for x in d['capabilities']),'protocol-capability-indexed');need(DOC in json.dumps(d['modules']),'protocol-key-document-indexed')
    need([x for x in d['capabilities'] if x['authoritative_source']!=DOC]==b['capabilities'],'unrelated-index-capabilities')
    normalized=copy.deepcopy(d)
    normalized['capabilities']=[x for x in normalized['capabilities'] if x['authoritative_source']!=DOC]
    for module in normalized['modules']:
        module['key_documents']=[x for x in module['key_documents'] if x!=DOC]
    need(normalized==b,'index-only-registration')
    skill=load('tools/skill.json');previous=json.loads(old('tools/skill.json'));need(skill['version']=='0.5.0' and skill['runtime_requirements']==previous['runtime_requirements'],'skill-no-adapter-implementation');need(any(x.get('module')==DOC or x.get('authoritative_source')==DOC for x in skill['capabilities']),'neutral-skill-module')
    fm('methodology/README.md','0.5.0');need('10_live_runtime_sessions.md' in read('methodology/README.md'),'methodology-source-index');guide=read('docs/guide/index.html');need('methodology/10_live_runtime_sessions.md' in guide,'guide-source-card');need('v1.5.0' in guide,'guide-current-release')
    for path in ('schema/runtime_session.schema.json','schema/runtime_operation.schema.json','methodology/11_sbcl_runtime_binding.md'):need(not Path(path).exists(),'future-source-out-of-scope:'+path)

def step_state(feature_state,step_status):
    enums=load('schema/phase.schema.json')['properties']['steps']['items']['properties']['status']['enum']
    need(step_status in enums,'schema-phase-step-state')
    need(step_status=={'in_progress':'IN_PROGRESS','complete':'COMPLETED'}[feature_state],'canonical110-step-lifecycle')

def authority_events():return json.loads(old('.agent/run_state.json'))['history']
def activation():
    events=authority_events();e=next(x for x in events if x.get('gate')=='H-PHASE-015' and x.get('contract_id')=='110');need(e['original_estimate_lines']==7200 and e['ceiling_130pct']==9360,'actual-activation-budget')
    for path,digest in e['accepted_plan_sha256'].items():need(hashlib.sha256(old(path,e['accepted_source_sha']).encode()).hexdigest()==digest,'accepted-plan-binding:'+path)
    f=load('.agent/feature_list_015.json');p=yaml.safe_load(read('docs/planning/phase_015.yaml'));fm('.agent/product_spec_015.md','1.0.0');need(f['spec_version']=='1.0.0' and f['activation_state']=='active' and f['phase_status']=='in_progress' and p['status']=='in_progress','canonical-activation');need(f['original_estimate_lines']==7200 and f['ceiling_130pct']==9360 and f['budget_basis']['proposed_only'] is False,'approved-budget-projection')
    features=f['features'];need([x['id'] for x in features]==[str(x) for x in range(110,115)] and all(x['status']=='pending' for x in features[1:]),'remaining-features-pending');first=features[0]['status'];need(first in {'in_progress','complete'},'110-lifecycle')
    if first=='complete':
        need(Path('.agent/qa/110.json').is_file() and (DIR/'evidence-gate.txt').is_file(),'early110-completion-without-proof')
        qa=load('.agent/qa/110.json');need(qa['qa_pass'] is True and qa['final_verdict']['approved'] is True and all(qa[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims','required_fixes')) and qa['checks_run']==qa['checks_passed']==21,'early110-completion-without-proof')
        need('PASS' in read(DIR/'evidence-gate.txt'),'early110-completion-without-proof')
        step_state(first,p['steps'][0]['status'])
    else:step_state(first,p['steps'][0]['status'])
    base=json.loads(old('.agent/feature_list_015.json'));need(all(x['acceptance_tests']==y['acceptance_tests'] and x['estimated_lines']==y['estimated_lines'] for x,y in zip(features,base['features'])),'inherited-ac-budget-frozen')
    need(features[1:]==base['features'][1:] and all(features[0][k]==base['features'][0][k] for k in set(base['features'][0])-{'status','passes'}),'future-feature-plan-frozen')
    m=load('docs/planning/manifest.json');mb=json.loads(old('docs/planning/manifest.json'));need(m['phases'][:-1]==mb['phases'][:-1] and m['current_phase']=='015-live-runtime-normative','manifest-canonical-activation');need(m['phases'][-1]['status']=='in_progress' and m['phases'][-1]['activation_state']=='active','manifest015-activation')
    state=load('.agent/run_state.json');before=json.loads(old('.agent/run_state.json'));need(state['current_phase']=='015-live-runtime-normative' and str(state['current_feature']) in ({'110','111','None'} if first=='complete' else {'110'}) and state['status']=='in_progress','derived-runstate-position');need(load(DIR/'prior-phase014-scope-budget.json')==before['scope_budget'],'old014-budget-archive');need(state['scope_budget']['original_estimate_lines']==7200 and state['scope_budget']['ceiling_130pct']==9360,'derived-budget')
    for key in before:
        if key.startswith('phase_') and key.endswith('_scope_budget_final'):need(state[key]==before[key],'historical-final-budget:'+key)

def choices():
    events=[x for x in authority_events() if x.get('event')=='operator_design_decision' and x.get('contract_id')=='110'];expected=json.loads(old(CONTRACT,APPROVED))['implementation_requirements']['wa_selected_recommendations'];need(len(events)==len(expected)==6 and {x['choice_id'] for x in events}==set(expected),'six-real-choice-events')
    text=clean(read(NIP4))
    for event in events:need(event['selected_recommendation']==expected[event['choice_id']] and event['selected_recommendation'] in text and event['choice_id'] in text,'exact-choice-projection:'+event['choice_id'])
    actual_rows={row[0]:row for row in table(text) if row and row[0] in expected}
    baseline_rows={row[0]:row for row in table(old(NIP4)) if row and row[0] in expected}
    need(set(actual_rows)==set(baseline_rows)==set(expected),'choice-row-inventory')
    for event in events:
        row=actual_rows[event['choice_id']];oldrow=baseline_rows[event['choice_id']]
        need(len(row)==8 and row[1:3]==oldrow[1:3],'original-choice-options:'+event['choice_id'])
        need(row[5]=='selected; implementation pending' and row[6]==event['selected_recommendation'] and BASE in row[7] and event['at'] in row[7],'choice-row-provenance:'+event['choice_id'])
    for row in table(text):
        if row and row[0] in {'identity','invalidation','gates','verdict','test-ownership','routing','profiles','concurrency'}:
            need('unresolved design decision' not in row[-1].lower() and 'awaits decision' not in row[-2].lower(),'selected-policy-still-not-implemented')
    for path in (NIP3,NIP4):need('Approved and accepted, please proceed.' in read(path),'accepted-nip-source')
    cases=lambda s:re.search(r'(?m)^\| # \| Case \|.*(?:\n\|[^\n]*)+',s).group();need(cases(read(NIP3))==cases(old(NIP3)),'protected-thirteen-cases');quotes=lambda s:[x for x in s.splitlines() if x.startswith('| Operator decision —')];need(quotes(read(NIP3))==quotes(old(NIP3)),'protected-four-decisions')
    dag=load('docs/planning/backlog_dag.json');packets={x['id']:x for x in dag['packets']};need(packets['PLAN-WA']['status']=='pending' and 'NIP3-114' in packets['PLAN-WA']['dependency_edges']['serialize_after'],'wa-remains-future');need(packets['PLAN-016']['status']=='pending','016-not-activated');need(not Path('docs/planning/phase_016.yaml').exists(),'016-not-allocated')

def scope():
    approved=json.loads(old(CONTRACT,APPROVED));current=load(CONTRACT)
    for key in ('scope','spec_ref','base_revision','non_goals','verification','implementation_requirements','checker_interface'):need(current[key]==approved[key],'approved-contract-binding:'+key)
    files={x['path'] for x in approved['scope']['files_modify']}|{x['path'] for x in approved['scope']['files_create'] if not any(v in x['path'] for v in '<[')}
    allowed=lambda path:path in files or bool(re.fullmatch(r'\.agent/(?:validator|qa)/110(?:-[A-Za-z0-9_-]+)?\.json|\.agent/evidence/110/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+',path))
    for line in git('diff','--name-status',BASE).decode().splitlines():
        fields=line.split('\t');need(len(fields)==2 and fields[0] in {'A','M'} and allowed(fields[1]),'scope:'+line)
    for path in git('ls-files','--others','--exclude-standard').decode().splitlines():need(allowed(path),'untracked-scope:'+path)
    before=json.loads(old('.agent/run_state.json',APPROVED));after=load('.agent/run_state.json');owned={'current_phase','current_feature','status','updated_at','circuit_breaker','scope_budget','active_contract_id','history','last_action','completed_contract_ids'};need(all(before.get(k)==after.get(k) for k in (set(before)|set(after))-owned),'unowned-runstate-fields');need(after['history'][:len(before['history'])]==before['history'],'operator-history-frozen')
    for e in after['history'][len(before['history']):]:need(e.get('contract_id',e.get('feature'))=='110' and e.get('event') not in {'operator_gate_decision','operator_design_decision'},'parent-history-owner')
    for k in set(before['circuit_breaker'])|set(after['circuit_breaker']):
        if before['circuit_breaker'].get(k)!=after['circuit_breaker'].get(k):need(k.startswith('110-') and after['circuit_breaker'][k]['limit']==3 and 0<=after['circuit_breaker'][k]['attempts']<=3,'bounded110-counter')
    for entry in approved['scope']['files_modify']:
        path=entry['path']
        if path.endswith('.md'):
            baseline=old(path)
            if baseline.startswith('---\n'):
                before_log=yaml.safe_load(baseline.split('---',2)[1])['change_log']
                current_log=yaml.safe_load(read(path).split('---',2)[1])['change_log']
                need(current_log[-len(before_log):]==before_log,'historical-change-log:'+path)
    for path,marker in [('CHANGELOG.md','## [1.5.0]'),('docs/planning/HANDOVER.md','## Historical handover snapshot'),('docs/planning/backlog_reconciliation.md','## Prior reconciliation history')]:need(old(path).split(marker,1)[1]==read(path).split(marker,1)[1],'frozen-history:'+path)


def override(path,value,op):
    original=globals()['read'];globals()['read']=lambda p:value if str(p)==str(path) else original(p)
    try:return op()
    finally:globals()['read']=original

def rejects(code,op):
    try:op()
    except InvariantError as error:need(str(error)==code,'wrong-negative:'+code+':'+str(error));print('NEGATIVE REJECTED:',code)
    else:raise InvariantError('negative-accepted:'+code)

def negative():
    for mode in (protocol,attempts,permissions,registration,activation,choices,scope):mode()
    text=read(DOC)
    def mutate(old,new,code,op=protocol,path=DOC):
        source=read(path);need(old in source,'negative-source-shape:'+code);rejects(code,lambda:override(path,source.replace(old,new,1),op))
    mutate('reject foreign requesters or stale leases before execution','execute foreign requesters or stale leases immediately','owner-before-execution')
    mutate('reject a stale expected_generation before execution','execute a stale expected_generation immediately','policy-obligation:R3')
    mutate('stopped_waiting MUST NOT imply cancelled or terminated','stopped_waiting MUST imply cancelled or terminated','policy-obligation:R5')
    mutate('acceptance from committed source in a fresh process with a fresh private build cache','acceptance from committed source in a warm process with an inherited build cache','policy-obligation:R7')
    row=next(line for line in text.splitlines() if line.startswith('| R3 |'))
    rejects('policy-row:R3',lambda:override(DOC,text.replace(row,'<!-- '+row+' -->',1),protocol))
    rejects('policy-row:R3',lambda:override(DOC,text.replace(row,'',1)+'\n'+row+'\n',protocol))
    row=next(line for line in text.splitlines() if line.startswith('| R9 |'))
    rejects('policy-obligation:R9',lambda:override(DOC,text.replace(row,'| R9 | external resources ownership synchronization | evidence |',1),protocol))
    mutate('A failed repair MUST NOT be relabeled as a probe','A failed repair MAY be relabeled as a probe','failed-repair-not-probe',attempts,'methodology/03_circuit_breaker.md')
    mutate('stage handoff MUST NOT reset an existing','stage handoff MUST reset an existing','attempt-no-reset',attempts,'methodology/03_circuit_breaker.md')
    mutate('Open, transfer and close a session only','Open, transfer and close a session and evaluate project code','lifecycle-no-evaluation',permissions,'standard/permission_classes.md')
    mutate('Review trials MUST be denied a session endpoint','Review trials MUST receive a session endpoint','policy-obligation:R10')
    index=load('NIZAM.json');index['capabilities']=[x for x in index['capabilities'] if x['authoritative_source']!=DOC];rejects('protocol-capability-indexed',lambda:override('NIZAM.json',json.dumps(index),registration))
    features=load('.agent/feature_list_015.json');features['features'][0]['status']='complete';rejects('early110-completion-without-proof',lambda:override('.agent/feature_list_015.json',json.dumps(features),activation))
    features=load('.agent/feature_list_015.json');features['ceiling_130pct']=9361;rejects('approved-budget-projection',lambda:override('.agent/feature_list_015.json',json.dumps(features),activation))
    state=load('.agent/run_state.json');state['phase_014_scope_budget_final']['original_estimate_lines']+=1;rejects('historical-final-budget:phase_014_scope_budget_final',lambda:override('.agent/run_state.json',json.dumps(state),activation))
    contract=load(CONTRACT);contract['scope']['files_create'].append({'path':'tools/fake-controller.py','purpose':'forged scope'});rejects('approved-contract-binding:scope',lambda:override(CONTRACT,json.dumps(contract),scope))
    selected=next(e for e in authority_events() if e.get('event')=='operator_design_decision' and e.get('contract_id')=='110');mutate(selected['selected_recommendation'],'All policy gates removed immediately','exact-choice-projection:'+selected['choice_id'],choices,NIP4)
    step_state('in_progress','IN_PROGRESS');step_state('complete','COMPLETED')
    rejects('schema-phase-step-state',lambda:step_state('complete','COMPLETE'))
    rejects('canonical110-step-lifecycle',lambda:step_state('complete','IN_PROGRESS'))
    path='docs/planning/operator_gates.md';source=read(path);fm_text=source.split('---',2)[1];parsed=yaml.safe_load(fm_text);need(len(parsed['change_log'])>1,'historical-negative-layout');parsed['change_log'][1]['version']='9.9.9';mutated='---\n'+yaml.safe_dump(parsed,sort_keys=False)+'---'+source.split('---',2)[2]
    rejects('historical-change-log:'+path,lambda:override(path,mutated,scope))
    path=NIP4;source=read(path);fm_text=source.split('---',2)[1];parsed=yaml.safe_load(fm_text);parsed['change_log'][-1]['summary']='Changed historical decision history';mutated='---\n'+yaml.safe_dump(parsed,sort_keys=False)+'---'+source.split('---',2)[2]
    rejects('historical-change-log:'+path,lambda:override(path,mutated,scope))
    print('NEGATIVE CONTROLS PASS: twenty-one named failures plus real positives and typed lifecycle enum positives; setup errors cannot count')

def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('protocol','attempts','permissions','registration','activation','choices','scope','negative'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args();mode=next(k for k,v in vars(args).items() if v)
    try:globals()[mode]();print('CHECK PASS:',mode);return 0
    except InvariantError as e:print('CHECK FAIL:',e);return 1
    except Exception as e:print('SETUP ERROR:',type(e).__name__,e);return 2
if __name__=='__main__':sys.exit(main())
