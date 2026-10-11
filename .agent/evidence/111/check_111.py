#!/usr/bin/env python3
"""Independent Feature111 schema/record controls; no live conformance assertions."""
import argparse,ast,copy,hashlib,json,os,re,shutil,subprocess,sys,tempfile,tarfile
from pathlib import Path
import jsonschema,yaml
BASE='a15be05d9ede7eadf4a2b848989f9386cfb2f617'
ORIGINAL='290254c16554f515c1e524a7f977d44adc0df8cf'
RECOVERY_BASE='d93496346e1fa699e7c91d4b1b9ce98e71faf970'
APPROVED='060d1511f4fa27dde3ccea66a7982b82ff75ef47'
DETAIL_AUTHORITY='55e39d790588afed9fa59e11b247cad9ce688edb'
HISTORICAL_CHECKER='244a48f10dd0c905f29e1e6ec37356e095beba25fca05b278c0108f050b599e5'
HISTORICAL_DETAIL_CHECKER='ed6f7313933f7fb64ccf87a669b5cc9c1aea320ab1b6ab14ee79a03a0d4d6178'
DETAIL_FAILURE_MANIFEST_SHA='3ad74f75c50e02a9c72138b71df1755cbd52c9dde0b425910e67c7770b343c28'
AUTHORITY='0bf3bd6617880870c8e9dc8ed9b1b74efaf41931'
TEST_AUTHOR='/root/release_evaluator'
CONTRACT='.agent/contracts/111.json'
DIR=Path('.agent/evidence/111')
FAMILIES=('runtime_session','runtime_operation')
class InvariantError(Exception):pass
def need(value,code):
    if not value:raise InvariantError(code)
def git(*args):return subprocess.check_output(['git',*args])
def old(path,revision=BASE):return git('show',revision+':'+str(path)).decode()
def read(path):return Path(path).read_text()
def load(path):return json.loads(read(path))
def approved():return json.loads(old(CONTRACT,APPROVED))
def feature():return next(x for x in json.loads(old('.agent/feature_list_015.json'))['features'] if x['id']=='111')
def norm(s):return re.sub(r'\s+',' ',re.sub(r'<!--.*?-->','',s,flags=re.S)).lower()
def schema(family):return load('schema/'+family+'.schema.json')
def run(args,cwd=None):return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
def relations(family,path):return run(['bash','-c','source "$1"; vlib_runtime_record_relations "$2" "$3"','bash','tools/verify_lib.sh',family,str(path)])
def target(path):return run(['bash','tools/validate.sh','--target',str(path)])
def data_run(data,family,which='target'):
    with tempfile.TemporaryDirectory(prefix='nizam111-record-') as tmp:
        p=Path(tmp)/'record.json';p.write_text(json.dumps(data));return target(p) if which=='target' else relations(family,p)
def errors(data,family):return list(jsonschema.Draft202012Validator(schema(family)).iter_errors(data))
def walk(v):
    if isinstance(v,dict):
        yield v
        for item in v.values():yield from walk(item)
    elif isinstance(v,list):
        for item in v:yield from walk(item)

def schemas():
    props={}
    for family in FAMILIES:
        path='schema/'+family+'.schema.json';need(Path(path).is_file(),'schema-missing:'+family);s=schema(family);jsonschema.Draft202012Validator.check_schema(s)
        need(s['$schema']=='https://json-schema.org/draft/2020-12/schema' and s['$id']=='urn:nizam-framework:schema:'+family+'.schema.json','schema-identity:'+family)
        need(s.get('type')=='object' and s.get('title') and s.get('description'),'schema-root:'+family)
        for node in walk(s):
            typ=node.get('type');need(not (typ=='object' or isinstance(typ,list) and 'object' in typ) or node.get('additionalProperties') is False,'schema-closed:'+family)
            if '$ref' in node:
                need(node['$ref'].startswith('#/'),'schema-self-contained:'+family)
                resolved=s
                for part in node['$ref'][2:].split('/'):
                    token=part.replace('~1','/').replace('~0','~');need(isinstance(resolved,dict) and token in resolved,'schema-reference-target:'+family);resolved=resolved[token]
                need(resolved,'schema-reference-target:'+family)
            for key,value in node.get('properties',{}).items():
                if typ=='object':need(value and any(x in value for x in ('type','$ref','allOf','anyOf','oneOf','const','enum')),'schema-typed-property:'+key)
                if any(x in value for x in ('type','$ref','const','enum')):props.setdefault(key,value)
        required={'session_id','purpose','owner','generation','lease_epoch'} if family=='runtime_session' else {'operation_id','session_id','requester','owner','expected_generation','generation','expected_lease_epoch','lease_epoch','contract_id','step_key','attempt','kind','status','executed','image_consistent','evidence_class'}
        need(set(s.get('required',[]))==required,'minimal-required-identity:'+family)
        need(set(s['$defs']['principal']['properties']['role']['enum'])=={'Orchestrator','Planner','Generator','Validator','Evaluator','review_trial'},'schema-principal-roles:'+family)
        if family=='runtime_session':need(set(s['properties']['purpose']['enum'])=={'develop','accept'},'schema-session-purpose')
        else:
            need(set(s['properties']['status']['enum'])=={'completed','condition_signalled','cancelled','terminated','rejected','running','cancel_requested','unknown'},'schema-operation-status')
            need(set(s['properties']['kind']['enum'])=={'load_source','compile_source','evaluate','run_tests','observe'},'schema-operation-kind')
    need(set(feature()['schema_obligations']['phase016_fields_represented'])<=set(props),'phase016-field-representation')
    for key in feature()['schema_obligations']['phase016_fields_represented']:need(props[key]!= {'type':'object'},'schema-meaningful-field:'+key)

def repair(data,name):
    d=copy.deepcopy(data)
    if 'foreign_executed' in name:d['requester']=copy.deepcopy(d['owner'])
    elif 'stale_generation_executed' in name:d['expected_generation']=copy.deepcopy(d['generation'])
    elif 'stale_lease_executed' in name:d['expected_lease_epoch']=d['lease_epoch']
    elif 'failed_load_consistent' in name:d['image_consistent']=False
    elif 'timeout_cancelled' in name:d['status']='running'
    elif 'session_result_acceptance' in name:d['evidence_class']='development'
    elif 'trial_executed' in name:
        d['requester']['role']='Generator';d['owner']['role']='Generator'
    elif 'accept_inherited_cache' in name:d['isolation']['build_cache']='fresh_private_empty'
    else:raise RuntimeError('Unknown approved negative '+name)
    return d

def fixtures():
    schemas();inventory=approved()['implementation_requirements']['fixture_inventory'];plan=feature()['fixture_plan'];need(len(inventory)==len(plan)==18,'fixture-inventory')
    keys=('path','family','kind','cases','expected_exit','expected_diagnostic');need([{k:x[k] for k in keys} for x in inventory]==[{k:x[k] for k in keys} for x in plan],'fixture-plan-binding')
    actual=set(str(p) for family in FAMILIES for p in Path('tools/fixtures').glob(family+'_*.json'));need(actual=={x['path'] for x in inventory},'fixture-top-level-exact')
    for item in inventory:
        path=item['path'];name=Path(path).name;family='runtime_'+item['family'];data=load(path);shape=errors(data,family);rel=relations(family,path);result=target(path)
        if item['kind']=='positive':need(not shape and rel.returncode==0,'fixture-positive:'+name)
        else:
            codes={ 'runtime_operation_neg_foreign_executed.json':'foreign_requester','runtime_operation_neg_stale_generation_executed.json':'stale_generation','runtime_operation_neg_stale_lease_executed.json':'stale_lease'}
            if name in codes:need(not shape and rel.returncode==1 and family+':'+codes[name] in rel.stdout,'fixture-relation:'+name)
            else:need(shape and rel.returncode==0,'fixture-schema-only-negative:'+name)
            fixed=repair(data,name);need(fixed!=data and not errors(fixed,family),'fixture-counterfactual-shape:'+name);r=data_run(fixed,family);rr=data_run(fixed,family,'relation');need(r.returncode==0 and '[C12] PASS' in r.stdout and rr.returncode==0,'fixture-counterfactual-target:'+name)
        need(result.returncode==item['expected_exit'] and item['expected_diagnostic'] in result.stdout,'fixture-target:'+name)
        print('FIXTURE:',name,'schema_errors='+str(len(shape)),'relation_exit='+str(rel.returncode),'target_exit='+str(result.returncode))
    positive={Path(x['path']).name:load(x['path']) for x in inventory if x['kind']=='positive'}
    reattach=positive['runtime_session_valid_reattach_pending.json'];need(reattach.get('transition')=='reattach' and all(k in reattach for k in ('previous_generation','previous_owner','previous_outstanding_operation_ref','outstanding_operation_ref')),'reattach-provenance')
    handoff=positive['runtime_session_valid_replayable_handoff.json'];need(handoff.get('source_revision') and handoff.get('source_manifest') and handoff.get('command_refs'),'handoff-provenance')
    transfer=positive['runtime_session_valid_transfer_lease.json'];need(transfer.get('transition')=='transfer' and transfer['lease_epoch']>transfer['previous_lease_epoch'] and transfer['owner']['principal_kind']!=transfer['previous_owner']['principal_kind'],'transfer-provenance')
    rows=feature()['case_matrix'];need(len(rows)==13 and all(x['claim_working'] is False and x['live_required'] is True and x['live_status'].startswith('pending') for x in rows),'schema-not-live-proof');need(not rows[1]['schema_fixtures'] and rows[11]['schema_fixtures']==rows[6]['schema_fixtures'],'case2-case12-boundaries')

def py_segment(name):
    s=read('tools/validate.sh').split(name+'() {',1)[1];return s.split("<<'PY'\n",1)[1].split('\nPY',1)[0]
def routing():
    s=read('tools/validate.sh');router=ast.parse(py_segment('check_c11_or_c4_target'));calls=[(n.lineno,n.args[0].value) for n in ast.walk(router) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='print' and len(n.args)==1 and isinstance(n.args[0],ast.Constant)];pos={v:k for k,v in calls}
    for family in FAMILIES:need(pos.get('ecosystem:'+family,10**9)<pos['contract'],'routing-priority:'+family)
    for function,variable in [('check_c12_ecosystem_fixtures','FAMILIES'),('check_c12_target','schema_paths')]:
        tree=ast.parse(py_segment(function));mapping=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==variable for t in n.targets));need(len(mapping)==10 and all(mapping[f]=='schema/'+f+'.schema.json' for f in FAMILIES),'routing-family-registration:'+function)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run']
        scripts=[v.value for n in calls for arg in n.args[:1] if isinstance(arg,ast.List) for v in arg.elts if isinstance(v,ast.Constant) and isinstance(v.value,str)]
        need(any(re.search(r'(?:^|;)\s*vlib_runtime_record_relations\s+',v) for v in scripts),'shared-relations-call:'+function)
    result=run(['bash','-c','source tools/verify_lib.sh']);need(result.returncode==0 and not result.stdout,'library-pure-source')
    for family in FAMILIES:
        item=next(x for x in approved()['implementation_requirements']['fixture_inventory'] if 'runtime_'+x['family']==family and x['kind']=='positive');data=load(item['path']);data['contract_id']='111';data['review']='route spoof';r=data_run(data,family);need(r.returncode==1 and '[C12] FAIL' in r.stdout and '[C11]' not in r.stdout,'runtime-before-generic:'+family)
    need({int(x) for x in re.findall(r'(?m)^check_c([0-9]+)_\w+\(\)\s*\{',s)}==set(range(1,17)),'check-count-boundary')

def registration():
    d=load('NIZAM.json');b=json.loads(old('NIZAM.json'));need(d['framework']==b['framework'],'framework-version-frozen');need(d['capabilities']==b['capabilities'],'no-adapter-capability')
    normalized=copy.deepcopy(d);newpaths={'schema/'+f+'.schema.json' for f in FAMILIES};normalized['schemas']=[x for x in normalized['schemas'] if x not in newpaths]
    for module in normalized['modules']:module['key_documents']=[x for x in module['key_documents'] if x not in newpaths]
    need(normalized==b,'index-only-schema-registration')
    for family in FAMILIES:
        path='schema/'+family+'.schema.json';need(path in json.dumps(d['schemas']) and path in json.dumps(d['modules']),'schema-index:'+family)
        need(re.search(r'(?m)^\|.*'+re.escape(family+'.schema.json')+r'.*\|',read('schema/README.md')),'schema-readme-row:'+family)
    rows=read('tools/fixtures_self_test.sh');inventory=approved()['implementation_requirements']['fixture_inventory']
    for x in inventory:need(re.search(r'(?m)^assert_target\s+'+re.escape(Path(x['path']).name)+r'\s+C12\s+'+('PASS' if x['kind']=='positive' else 'FAIL')+r'\s*$',rows),'fixture-standing-row:'+Path(x['path']).name)
    oldmap=re.search(r'(?ms)^FIXTURE_CLAIMS=\(.*?^\)',old('tools/fixtures_self_test.sh'));newmap=re.search(r'(?ms)^FIXTURE_CLAIMS=\(.*?^\)',rows);need(oldmap is not None and newmap is not None and oldmap.group()==newmap.group(),'frozen-claim-map');need(not Path('tools/fixtures/runtime_session').exists(),'no-nested-live-fixtures')
    path='methodology/10_live_runtime_sessions.md';source=read(path);fm=yaml.safe_load(source.split('---',2)[1]);need(fm['version']=='0.1.1' and fm['status']=='active' and fm['enforcement']=='consumer-aspirational','protocol-enforcement-boundary')
    opening=norm(source.split('This normative protocol',1)[1].split('A runtime session is',1)[0]);last=norm(source.split('## 12. Durable records',1)[1])
    need(re.search(r'framework publishes.{0,150}(?:two|both).{0,80}schemas.{0,80}c12 record.relational validation',opening),'protocol-schema-availability')
    need(re.search(r'schemas and executable c12 relational checks validate session and operation records',last),'protocol-section12-availability')
    need(re.search(r'cannot prove live.{0,180}(?:enforcement|conformance)',opening) and re.search(r'never live runtime behavior',last),'record-proof-limit')
    need(not re.search(r'(?:future|pending).{0,50}(?:feature )?111|does not yet supply.{0,80}schemas',opening+last),'stale-schema-absence')

def snapshot():
    temp=Path(tempfile.mkdtemp(prefix='nizam111-private-'));r=run(['git','clone','--quiet','--no-hardlinks',str(Path.cwd()),str(temp/'tree')]);need(r.returncode==0,'private-snapshot-clone');tree=temp/'tree';r=run(['git','checkout','--quiet','--detach',APPROVED],tree);need(r.returncode==0,'private-snapshot-base')
    changed=set(git('diff','--name-only',APPROVED).decode().splitlines())|set(git('ls-files','--others','--exclude-standard').decode().splitlines())
    for path in changed:
        source=Path(path);dest=tree/path
        if source.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        elif dest.exists():dest.unlink()
    return temp,tree

def compatibility():
    need(load('NIZAM.json')['framework']['version']=='1.5.0','compatibility-framework-version');need(load('tools/skill.json')['runtime_requirements']==json.loads(old('tools/skill.json'))['runtime_requirements'],'compatibility-runtime-requirements');need(not Path('methodology/11_sbcl_runtime_binding.md').exists(),'no-binding112')
    temp,tree=snapshot()
    try:
        r=run(['bash','tools/validate.sh','--payload'],tree);need(r.returncode==0,'payload-without-session-records')
        sessions=tree/'.agent/sessions';sessions.mkdir(exist_ok=True);(sessions/'malformed.json').write_text('{ not valid JSON')
        r=run(['bash','tools/validate.sh','--payload'],tree);need(r.returncode==0,'no-consumer-session-auto-sweep')
        source=next(x for x in approved()['implementation_requirements']['fixture_inventory'] if x['kind']=='negative');r=run(['bash','tools/validate.sh','--target',source['path']],tree);need(r.returncode==1 and '[C12] FAIL' in r.stdout,'explicit-record-validation')
    finally:shutil.rmtree(temp)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def gate_ok(d):return d.get('final_verdict',{}).get('approved') is True and all(d.get(k)==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
def history_projection(state):
    remedy=approved()['implementation_requirements']['history_detail_remedy'];receipt=load(DIR/'history-detail-approved-base.json')
    need(receipt['approved_base']==APPROVED and receipt['authority_revision']==DETAIL_AUTHORITY and receipt['historical_operator_authority_revision']==AUTHORITY and receipt['historical_recovery_base']==RECOVERY_BASE and receipt['original_implementation_base']==ORIGINAL and receipt['phase_base']==BASE,'history-detail-approved-base')
    need(receipt['approved_contract_sha256']==hashlib.sha256(git('show',APPROVED+':'+CONTRACT)).hexdigest(),'history-detail-approved-contract')
    authorization=remedy['authorization_record'];need(remedy['authority_revision']==DETAIL_AUTHORITY and sha(authorization)==remedy['authorization_record_sha256'] and Path(authorization).read_bytes()==git('show',DETAIL_AUTHORITY+':'+authorization),'history-detail-authorization')
    for path,digest in receipt['approval_evidence_sha256'].items():need(sha(path)==digest and gate_ok(load(path)),'history-detail-precode-gate:'+path)
    original=json.loads(old('.agent/run_state.json',AUTHORITY))['history'][402];expected=approved()['implementation_requirements']['recovery_reconciliation']['operator_event'];need(original==expected and 'detail' not in original and json.loads(old('.agent/run_state.json',RECOVERY_BASE))['history'][402]==original,'history-original-authority')
    history=state.get('history',[]);need(len(history)>402 and isinstance(history[402],dict),'history-authority-position-or-count');event=history[402]
    matches=lambda e:isinstance(e,dict) and e.get('event')=='operator_gate_decision' and e.get('contract_id')=='111' and e.get('gate')=='H-CIRCUIT-111-CHECKER'
    if not set(original)<=set(event):need(matches(event),'history-authority-position-or-count')
    need({k:v for k,v in event.items() if k!='detail'}==original,'history-authority-content')
    need([i for i,e in enumerate(history) if matches(e)]==[402],'history-authority-position-or-count')
    if 'detail' not in event and any(e.get('detail')==original['corrected_approach'] for e in history if isinstance(e,dict)):raise InvariantError('history-authority-position-or-count')
    need('detail' in event,'history-detail-required');need(event['detail']==original['corrected_approach']==remedy['current_annotation']['exact_value'],'history-detail-exact')
    need(set(event)==set(original)|{'detail'} and remedy['current_annotation']['history_index']==402 and remedy['current_annotation']['field']=='detail','history-authority-content')
    normalized=copy.deepcopy(history);del normalized[402]['detail']
    for revision in (AUTHORITY,RECOVERY_BASE):
        before=json.loads(old('.agent/run_state.json',revision))['history'];need(normalized[:len(before)]==before,'operator-history-frozen')
    before=json.loads(old('.agent/run_state.json',APPROVED))['history'];need(history[:len(before)]==before,'operator-history-frozen')
    schema_state=load('.nizam/schema/run_state.schema.json');need(not list(jsonschema.Draft202012Validator(schema_state).iter_errors(state)),'current-installed-runstate-schema')
    return normalized

def history_projection_state():return history_projection(load('.agent/run_state.json'))

def counter_continuity(state):
    initial=json.loads(old('.agent/run_state.json',APPROVED))['circuit_breaker'];current=state['circuit_breaker']
    for key,prior in initial.items():
        value=current.get(key);need(isinstance(value,dict),'recovery-other-counter:'+key)
        if key in {'111-checker-development','111-checker-review','111-implementation','111-qa'}:
            need({k:v for k,v in value.items() if k!='attempts'}=={k:v for k,v in prior.items() if k!='attempts'} and max(prior['attempts'],2 if key in {'111-checker-development','111-checker-review','111-implementation'} else prior['attempts'])<=value['attempts']<=prior['limit'],'history-counter-continuity:'+key)
        else:need(value==prior,'recovery-other-counter:'+key)
    for key in set(current)-set(initial):need(key.startswith('111-') and current[key].get('limit')==3 and 0<=current[key]['attempts']<=3,'history-new-counter:'+key)
    need(current['111-contract']['limit']==4 and current['111-contract']['attempts']==4 and current['111-contract']['human_authorized_extension']==initial['111-contract']['human_authorized_extension'],'history-contract-limit')

def mutable_acceptance_outputs():
    a=approved();inventory=a['implementation_requirements']['fixture_inventory'];need(len(inventory)==18,'mutable-output-inventory')
    inner=set()
    for item,verification in zip(inventory,a['verification'][6:24]):
        expected=str(DIR/(Path(item['path']).name+'.txt'));matches=re.findall(r'>\s*(\.agent/evidence/111/[A-Za-z0-9_.-]+)\s+2>&1',verification['command'])
        need(matches==[expected] and ('--target '+item['path']+' ') in verification['command'],'mutable-output-command:'+item['path']);inner.add(expected)
    need(len(inner)==18,'mutable-output-exact18');outer={v['evidence'] for v in a['verification']};need(len(outer)==38,'mutable-output-exact38')
    archive_path=DIR/'failed-qa-attempt1/preservation.json';need(Path(archive_path).read_bytes()==git('show',APPROVED+':'+str(archive_path)),'mutable-output-archive-manifest');archive=load(archive_path)['snapshot_sha256'];tracked=set(git('ls-tree','-r','--name-only',APPROVED).decode().splitlines())
    for path in sorted(inner|outer|{'.agent/qa/111.json'}):
        if path not in tracked:continue
        saved=str(DIR/'failed-qa-attempt1'/Path(path).name);need(saved in archive and Path(saved).is_file() and sha(saved)==archive[saved]==hashlib.sha256(git('show',APPROVED+':'+path)).hexdigest(),'mutable-output-archive:'+saved)
    return inner|outer

def historical_checkpoint2():
    directory=DIR/'failed-detail-implementation2';manifest_path=directory/'preservation.json';need(sha(manifest_path)==DETAIL_FAILURE_MANIFEST_SHA,'historical-checkpoint2-manifest');manifest=load(manifest_path)
    for path,digest in manifest['snapshot_sha256'].items():need(Path(path).is_file() and sha(path)==digest,'historical-checkpoint2-archive:'+path)
    for name in ('checker-review-detail.json','recovery-epoch1-development-checkpoint2.json'):
        need(Path(DIR/name).read_bytes()==Path(directory/name).read_bytes(),'historical-checkpoint2-record:'+name)
    review=load(DIR/'checker-review-detail.json');proof=load(DIR/'recovery-epoch1-development-checkpoint2.json');need(gate_ok(review) and review['checker_sha256']==proof['checker_sha256']==HISTORICAL_DETAIL_CHECKER and proof['actual_exit']==0 and proof['approved_base']==APPROVED and proof['checks_run']==proof['checks_passed']==8,'historical-checkpoint2-proof')
    tar_path=directory/'untracked.tar.gz';need(sha(tar_path)==manifest['untracked_tar_sha256'],'historical-checkpoint2-tar')
    with tarfile.open(tar_path) as archive:
        for check in proof['checks']:
            path=check['evidence'];member=archive.extractfile(path);need(member is not None and Path(path).read_bytes()==member.read() and check['actual_exit']==0,'historical-checkpoint2-receipt:'+path)

def recovery():
    a=approved()['implementation_requirements']['recovery_reconciliation'];receipt=load(DIR/'recovery-approved-base.json')
    need(receipt['approved_base']==RECOVERY_BASE and receipt['operator_authority_revision']==AUTHORITY and receipt['original_implementation_base']==ORIGINAL and receipt['phase_base']==BASE and receipt['recovery_epoch']==1,'recovery-approved-base')
    need(receipt['approved_contract_sha256']==hashlib.sha256(git('show',RECOVERY_BASE+':'+CONTRACT)).hexdigest(),'recovery-approved-contract-hash')
    need(run(['git','merge-base','--is-ancestor',AUTHORITY,APPROVED]).returncode==0,'recovery-authority-ancestry')
    state=load('.agent/run_state.json');committed=json.loads(old('.agent/run_state.json',AUTHORITY));archive=load(DIR/'recovery-authorization.json');expected=a['operator_event']
    need(a['operator_authority_revision']==AUTHORITY and expected in committed['history'] and expected in history_projection(state),'recovery-operator-event')
    need(archive['operator_authority_revision']==AUTHORITY and archive['operator_event']==expected,'recovery-archive-authority')
    need(archive['prior_exhausted_counter']==committed['circuit_breaker']['111-checker-development']=={'attempts':3,'limit':3} and archive['prior_circuit_breaker']==committed['circuit_breaker'],'recovery-exhausted-counter')
    need(sha(DIR/'blocked-checker3/checkpoint3.txt')==archive['checkpoint3_sha256'] and sha(DIR/'blocked-checker3/quarantine.json')==archive['quarantine_sha256'],'recovery-halt-proof')
    counter=state['circuit_breaker']['111-checker-development'];initial=json.loads(old('.agent/run_state.json',APPROVED))
    need(counter.get('recovery_epoch')==1 and counter.get('human_authorized_restart')==str(DIR/'recovery-authorization.json') and counter['limit']==3 and 0<=counter['attempts']<=3,'recovery-current-counter')
    counter_continuity(state)
    resets=[e for e in state['history'] if e.get('event')=='operator_authorized_step_restart' and e.get('contract_id')=='111']
    need(len(resets)==1 and resets[0]['step_key']=='111-checker-development' and resets[0]['authority_revision']==AUTHORITY and resets[0]['prior_attempts']==3 and resets[0]['new_attempts']==0 and resets[0]['limit']==3 and resets[0]['recovery_epoch']==1,'recovery-reset-history')
    for path in ('.agent/validator/111-mode-a-recovery.json','.agent/qa/111-contract-review-recovery.json'):
        need(gate_ok(load(path)),'recovery-precode-gate:'+path)
    inventory=a['frozen_product_inventory'];need(sha(inventory['path'])==inventory['sha256'],'recovery-frozen-inventory')
    products=load(inventory['path'])['products'];need(len(products)==28,'recovery-frozen-count')
    for path,digest in products.items():need(Path(path).is_file() and sha(path)==digest,'recovery-frozen-product:'+path)
    review_path=DIR/'checker-review-detail3.json';review=load(review_path) if review_path.exists() else None
    if review is not None:
        need(review.get('test_author')==TEST_AUTHOR and review.get('checker_reviewer') not in {None,TEST_AUTHOR} and review.get('checker_sha256')==sha(DIR/'check_111.py') and review.get('approved_base')==APPROVED and gate_ok(review),'recovery-independent-checker-review')
    seal_path=DIR/'acceptance-seal-detail.json'
    if seal_path.exists():
        seal=load(seal_path);need(review is not None and seal.get('test_author')==TEST_AUTHOR and seal.get('acceptance_reviewer') not in {None,TEST_AUTHOR,review['checker_reviewer']},'recovery-independent-final-review')
    debt=read('docs/planning/DEBT.md');baseline=old('docs/planning/DEBT.md',APPROVED)
    other=lambda text:[line for line in text.splitlines() if line.startswith('| NDEBT-') and not line.startswith(('| NDEBT-048 |','| NDEBT-049 |'))]
    need(other(debt)==other(baseline),'recovery-other-debt-frozen')
    rows49=[line for line in debt.splitlines() if line.startswith('| NDEBT-049 |')];prior49=[line for line in baseline.splitlines() if line.startswith('| NDEBT-049 |')];need(len(rows49)==len(prior49)==1,'history-debt049-row')
    if rows49!=prior49 or (rows49[0] in debt.split('## Open',1)[1].split('## Resolved',1)[0])!=(prior49[0] in baseline.split('## Open',1)[1].split('## Resolved',1)[0]):
        need(load('.agent/feature_list_015.json')['features'][1]['status']=='complete' and Path('.agent/qa/111.json').is_file() and (DIR/'evidence-gate.txt').is_file(),'history-premature-debt049-resolution')
        qa=load('.agent/qa/111.json');need(qa.get('qa_pass') is True and qa.get('checks_run')==qa.get('checks_passed')==38 and gate_ok(qa) and qa.get('required_fixes')==[] and 'PASS' in read(DIR/'evidence-gate.txt'),'history-premature-debt049-resolution')
        original=prior49[0];cells=original.split('|');need(len(cells)==7,'history-debt049-row')
        cells[5]=' RESOLVED 2026-10-11: the current history402 detail equals the exact original corrected_approach; original authority, prior history and failedQA1 remain preserved. Independent current checker review, ModeB and fresh38/38 acceptance plus own adversarial spot verified the bounded remedy; evidence gate captured at .agent/evidence/111/evidence-gate.txt and .agent/qa/111.json. No other history annotation, counter reset, source change or live conformance claim. '
        expected=baseline.replace('version: 0.61.0','version: 0.62.0',1).replace('change_log:\n','change_log:\n  - version: "0.62.0"\n    date: "2026-10-11"\n    summary: "Resolve only NDEBT-049 after fresh independent acceptance and evidence gate; preserve original authorization/history and failedQA1, all prior debt rows and logs."\n',1).replace(original+'\n','',1)
        anchor='|----|------|----------|-------------|------------|\n';need(expected.count(anchor)==1,'history-debt049-layout');expected=expected.replace(anchor,anchor+'|'.join(cells)+'\n',1);need(debt==expected,'history-debt049-transition')
    row=[line for line in debt.splitlines() if line.startswith('| NDEBT-048 |')];need(len(row)==1,'recovery-debt-row')
    halted=old('docs/planning/DEBT.md',archive['halt_revision']);need(archive['prior_debt_row'] in halted,'recovery-original-halt-row')
    open_section=debt.split('## Open',1)[1].split('## Resolved',1)[0];is_open=row[0] in open_section
    if not is_open:
        proof_path=DIR/'recovery-epoch1-development.json';need((DIR/'checker-review.json').exists() and proof_path.exists(),'recovery-premature-debt-resolution');proof=load(proof_path)
        need(proof.get('approved_base')==RECOVERY_BASE and proof.get('checker_sha256')==HISTORICAL_CHECKER and proof.get('test_author')==TEST_AUTHOR and proof.get('actual_exit')==0,'recovery-development-proof')
        checks=proof.get('checks',[]);need(len(checks)==8 and {x.get('mode') for x in checks}=={'schemas','fixtures','routing','registration','compatibility','lifecycle','scope','negative'},'recovery-development-coverage')
        for check in checks:
            path=check.get('evidence','');need(check.get('actual_exit')==0 and Path(path).is_file(),'recovery-development-capture')
            text=read(path);need(len(re.findall(r'(?m)^EXIT:\s*0\s*$',text))==1 and re.search(r'(?m)^COMMAND: .*--'+check['mode']+r'\s*$',text) and ('APPROVED_BASE: '+RECOVERY_BASE) in text,'recovery-development-capture')
        need(proof.get('source_sha256')==products,'recovery-development-source-binding')
        old_review=load(DIR/'checker-review.json');need(old_review.get('checker_sha256')==HISTORICAL_CHECKER and gate_ok(old_review) and old_review.get('test_author')==TEST_AUTHOR and old_review.get('checker_reviewer')!=TEST_AUTHOR,'historical-checkpoint1-review')
    current_proof_path=DIR/'recovery-epoch1-development-checkpoint3.json'
    if current_proof_path.exists():
        proof=load(current_proof_path);need(review is not None and proof.get('approved_base')==APPROVED and proof.get('checker_sha256')==sha(DIR/'check_111.py') and proof.get('test_author')==TEST_AUTHOR and proof.get('actual_exit')==0 and proof.get('source_sha256')==products,'history-current-checkpoint3-proof')
        checks=proof.get('checks',[]);need(len(checks)==8 and {x.get('mode') for x in checks}=={'schemas','fixtures','routing','registration','compatibility','lifecycle','scope','negative'},'history-current-checkpoint3-coverage')
        for check in checks:
            path=check.get('evidence','');need(check.get('actual_exit')==0 and Path(path).is_file(),'history-current-checkpoint3-capture');text=read(path)
            need(len(re.findall(r'(?m)^EXIT:\s*0\s*$',text))==1 and re.search(r'(?m)^COMMAND: .*--'+check['mode']+r'\s*$',text) and ('APPROVED_BASE: '+APPROVED) in text and ('CHECKER_SHA256: '+sha(DIR/'check_111.py')) in text,'history-current-checkpoint3-capture')
    historical_checkpoint2()
    return products

def lifecycle():
    f=load('.agent/feature_list_015.json');base=json.loads(old('.agent/feature_list_015.json'));items=f['features'];need(items[0]==base['features'][0] and items[2:]==base['features'][2:],'other-feature-position-frozen');current=items[1];need(current['acceptance_tests']==feature()['acceptance_tests'],'original26-ac-frozen');need(current['status'] in {'in_progress','complete'},'111-authorized-position')
    p=yaml.safe_load(read('docs/planning/phase_015.yaml'));step=p['steps'][1];state=current['status'];need(step['status']=={'in_progress':'IN_PROGRESS','complete':'COMPLETED'}[state],'canonical111-step-lifecycle');need(p['status']=='in_progress' and f['original_estimate_lines']==7200 and f['ceiling_130pct']==9360,'phase-budget-frozen')
    if state=='complete':
        need(Path('.agent/qa/111.json').is_file() and (DIR/'evidence-gate.txt').is_file(),'early111-completion-without-proof');q=load('.agent/qa/111.json');need(q['qa_pass'] and q['checks_run']==q['checks_passed']==38 and q['final_verdict']['approved'] and all(q[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims','required_fixes')) and 'PASS' in read(DIR/'evidence-gate.txt'),'early111-completion-without-proof');seal=load(DIR/'acceptance-seal-detail.json');need(seal['test_author']!=seal['acceptance_reviewer'],'independent-acceptance-owner')
    source=read('.agent/product_spec_015.md');fm=yaml.safe_load(source.split('---',2)[1]);need(fm['version']==f['spec_version']=='1.0.1','current-spec-version');need(not re.search(r'(?i)(?:features?\s*)?111[–-]114 remain pending',norm(source)) or re.search(r'(?:activation.time|at activation|historical).{0,150}111[–-]114 remain pending',norm(source)),'stale-spec-current-position');need(not re.search(r'111[–-]114.{0,30}(?:remain|are) pending',norm(p['description'])),'stale-phase-current-position')
    dag=load('docs/planning/backlog_dag.json');need(dag['activated_phase']['spec_version']=='1.0.1','dag-spec-version');state=load('.agent/run_state.json');need(state['current_phase']=='015-live-runtime-normative' and str(state['current_feature']) in ({'111','112','None'} if current['status']=='complete' else {'111'}),'derived111-position')
    recovery()

def scope():
    a=approved();current=load(CONTRACT)
    for key in ('scope','spec_ref','base_revision','non_goals','verification','implementation_requirements'):need(current[key]==a[key],'approved-contract-binding:'+key)
    files={x['path'] for group in ('files_modify','files_create') for x in a['scope'][group] if not any(c in x['path'] for c in '<[')}
    allowed=lambda p:p in files or bool(re.fullmatch(r'\.agent/(?:validator|qa)/111(?:-[A-Za-z0-9_-]+)?\.json|\.agent/evidence/111/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+',p))
    for line in git('diff','--name-status',BASE).decode().splitlines():
        fields=line.split('\t');need(len(fields)==2 and fields[0] in {'A','M'} and allowed(fields[1]),'scope:'+line)
    for path in git('ls-files','--others','--exclude-standard').decode().splitlines():need(allowed(path),'untracked-scope:'+path)
    for x in a['scope']['files_modify']:
        path=x['path']
        if path.endswith('.md') and old(path).startswith('---\n'):
            before=yaml.safe_load(old(path).split('---',2)[1])['change_log'];after=yaml.safe_load(read(path).split('---',2)[1])['change_log'];need(after[-len(before):]==before,'historical-change-log:'+path)
    before=json.loads(old('.agent/run_state.json',APPROVED));after=load('.agent/run_state.json');owned={'current_feature','updated_at','status','active_contract_id','last_action','scope_budget','history','circuit_breaker','completed_contract_ids'};need(all(before.get(k)==after.get(k) for k in (set(before)|set(after))-owned),'unowned-runstate-fields');need(after['history'][:len(before['history'])]==before['history'],'operator-history-frozen')
    for event in after['history'][len(before['history']):]:need(event.get('contract_id',event.get('feature'))=='111' and event.get('event') not in {'operator_gate_decision','operator_design_decision'},'parent-history-owner')
    counter_continuity(after)
    need(after['scope_budget']['original_estimate_lines']==7200 and after['scope_budget']['ceiling_130pct']==9360,'immutable-approved-budget')
    need(after['scope_budget']['per_feature'][:len(before['scope_budget']['per_feature'])]==before['scope_budget']['per_feature'],'prior-phase015-measurements-frozen')
    need(after['completed_contract_ids'][:len(before['completed_contract_ids'])]==before['completed_contract_ids'] and set(after['completed_contract_ids'][len(before['completed_contract_ids']):])<={'111'},'completed-contract-owner')
    dag=load('docs/planning/backlog_dag.json');prior=json.loads(old('docs/planning/backlog_dag.json'));a_packets={x['id']:x for x in dag['packets']};b_packets={x['id']:x for x in prior['packets']};need(set(a_packets)==set(b_packets),'backlog-inventory-frozen')
    for pid,q in a_packets.items():
        b=b_packets[pid];need(q['dependency_edges']==b['dependency_edges'],'backlog-edges-frozen:'+pid)
        if pid not in {'NIP3-111','NIP3-112'}:need(q==b,'unrelated-backlog-packet:'+pid)
    need(dag['historical_phase014']==prior['historical_phase014'],'historical-phase014-frozen')
    f=load('.agent/feature_list_015.json');b=json.loads(old('.agent/feature_list_015.json'));need(f['features'][1]['fixture_plan']==b['features'][1]['fixture_plan'] and f['case_matrix']==b['case_matrix'],'protected-fixture-case-plan');need(read('CHANGELOG.md').split('## [1.5.0]',1)[1]==old('CHANGELOG.md').split('## [1.5.0]',1)[1],'released-history-frozen')
    need(read('tools/verify_lib.sh').startswith(old('tools/verify_lib.sh').rstrip()),'existing-eleven-primitives-frozen')
    path='methodology/10_live_runtime_sessions.md';before=old(path);after=read(path)
    need(before.split('A runtime session is',1)[1].split('The Orchestrator alone',1)[0]==after.split('A runtime session is',1)[1].split('The Orchestrator alone',1)[0],'neutral-prose-boundaries-frozen')
    role_prefix=before.split('The Orchestrator alone',1)[1].split('Schema-governed records',1)[0]
    need(norm(after.split('The Orchestrator alone',1)[1]).startswith(norm(role_prefix)),'neutral-role-ownership-frozen')
    path='.agent/product_spec_015.md';before_body=old(path).split('---',2)[2];after_body=read(path).split('---',2)[2];replacement='At phase activation, features 111–114 were pending;\ncurrent feature progress is read from the canonical lifecycle records above.'
    need(after_body.replace(replacement,'Features 111–114 remain pending.')==before_body,'spec-only-current-progress-clarification')
    f=load('.agent/feature_list_015.json');b=json.loads(old('.agent/feature_list_015.json'));need(all(f['features'][1][k]==b['features'][1][k] for k in set(b['features'][1])-{'status','passes'}),'111-plan-obligations-frozen')
    phase=yaml.safe_load(read('docs/planning/phase_015.yaml'));prior=yaml.safe_load(old('docs/planning/phase_015.yaml'));need(phase['steps'][0]==prior['steps'][0] and phase['steps'][2:]==prior['steps'][2:],'other-phase-steps-frozen')
    path='methodology/10_live_runtime_sessions.md';a_rows=[l for l in old(path).splitlines() if l.startswith('| R')];b_rows=[l for l in read(path).splitlines() if l.startswith('| R')];need(a_rows==b_rows,'neutral-R1-R12-frozen')
    mutable_outputs=mutable_acceptance_outputs()
    for path in git('ls-tree','-r','--name-only',APPROVED).decode().splitlines():
        if (path.startswith('.agent/evidence/111/') and path not in {str(DIR/'check_111.py'),str(DIR/'evidence_gate.py')} and path not in mutable_outputs) or path in {'.agent/validator/111-mode-a.json','.agent/qa/111-contract-review.json','.agent/validator/111-mode-b.json'}:
            need(Path(path).is_file() and Path(path).read_bytes()==git('show',APPROVED+':'+path),'recovery-prior-proof:'+path)
    recovery()

def override(path,value,operation):
    original=globals()['read'];globals()['read']=lambda p:value if str(p)==str(path) else original(p)
    try:return operation()
    finally:globals()['read']=original

def rejects(code,operation):
    try:operation()
    except InvariantError as e:need(str(e)==code,'wrong-negative:'+code+':'+str(e));print('NEGATIVE REJECTED:',code)
    else:raise InvariantError('negative-accepted:'+code)

def negative():
    schemas();fixtures();routing();registration();lifecycle();scope()
    for family in FAMILIES:
        s=schema(family);s['additionalProperties']=True;rejects('schema-closed:'+family,lambda:override('schema/'+family+'.schema.json',json.dumps(s),schemas))
        s=schema(family);s['required'].remove('owner');rejects('minimal-required-identity:'+family,lambda:override('schema/'+family+'.schema.json',json.dumps(s),schemas))
    good=load('tools/fixtures/runtime_operation_valid_running_stopped_waiting.json')
    for label,mutate in [('wrong-counter-type',lambda d:d['generation'].update(counter='1')),('unknown-nested-field',lambda d:d['owner'].update(unauthorized=True)),('invalid-status',lambda d:d.update(status='debugger_paused')),('invalid-role',lambda d:d['requester'].update(role='Unowned')),('nonintegral-counter',lambda d:d['generation'].update(counter=1.5)),('boolean-counter',lambda d:d['generation'].update(counter=True))]:
        d=copy.deepcopy(good);mutate(d);need(errors(d,'runtime_operation'),'negative-schema-accepted:'+label);r=data_run(d,'runtime_operation');need(r.returncode==1 and '[C12] FAIL' in r.stdout,'negative-target-accepted:'+label);print('NEGATIVE REJECTED:',label)
    numeric=copy.deepcopy(good);numeric['generation']['counter']=numeric['expected_generation']['counter']=1.0;numeric['lease_epoch']=numeric['expected_lease_epoch']=1.0;need(not errors(numeric,'runtime_operation'),'integer-representation-schema');r=data_run(numeric,'runtime_operation');need(r.returncode==0 and '[C12] PASS' in r.stdout,'integer-representation-positive');print('POSITIVE: integral JSON number representation accepted')
    d=load('tools/fixtures/runtime_operation_valid_new_generation_same_attempt.json');d['attempt']+=1;r=data_run(d,'runtime_operation');need(not errors(d,'runtime_operation') and r.returncode==1 and 'runtime_operation:attempt_continuity' in r.stdout,'attempt-continuity-load-bearing');print('NEGATIVE REJECTED: attempt-continuity')
    d=load('tools/fixtures/runtime_session_valid_transfer_lease.json');d['lease_epoch']=d['previous_lease_epoch'];r=data_run(d,'runtime_session');need(not errors(d,'runtime_session') and r.returncode==1 and 'runtime_session:transfer_lease' in r.stdout,'transfer-lease-load-bearing');print('NEGATIVE REJECTED: transfer-lease')
    d=load('tools/fixtures/runtime_session_valid_reattach_pending.json');d['generation']['nonce']='new-generation';r=data_run(d,'runtime_session');need(not errors(d,'runtime_session') and r.returncode==1 and 'runtime_session:reattach_generation' in r.stdout,'reattach-generation-load-bearing');print('NEGATIVE REJECTED: reattach-generation')
    d=load('tools/fixtures/runtime_session_valid_accept_hermetic.json');d['isolation']['process']='retained';r=data_run(d,'runtime_session');need(errors(d,'runtime_session') and r.returncode==1 and '[C12] FAIL' in r.stdout,'acceptance-isolation-load-bearing');print('NEGATIVE REJECTED: acceptance-isolation')
    path='methodology/10_live_runtime_sessions.md';source=read(path);text=source.replace('two closed\nruntime provenance schemas and C12 record-relational validation','no schemas; future feature111 will provide C12 validation',1);need(source!=text,'negative-protocol-layout');rejects('protocol-schema-availability',lambda:override(path,text,registration))
    row=next(l for l in source.splitlines() if l.startswith('| R2 |'));rejects('neutral-prose-boundaries-frozen',lambda:override(path,source.replace(row,row.replace('reject foreign','execute foreign')),scope))
    path='.agent/product_spec_015.md';source=read(path);fm_text=source.split('---',2)[1];parsed=yaml.safe_load(fm_text);parsed['change_log'][-1]['summary']='rewritten prior scope';text='---\n'+yaml.safe_dump(parsed,sort_keys=False)+'---'+source.split('---',2)[2];rejects('historical-change-log:'+path,lambda:override(path,text,scope))
    f=load('.agent/feature_list_015.json');f['features'][1]['status']='complete';phase=yaml.safe_load(read('docs/planning/phase_015.yaml'));phase['steps'][1]['status']='COMPLETED';rejects('early111-completion-without-proof',lambda:override('.agent/feature_list_015.json',json.dumps(f),lambda:override('docs/planning/phase_015.yaml',yaml.safe_dump(phase),lifecycle)))
    f=load('.agent/feature_list_015.json');f['spec_version']='1.0.0';rejects('current-spec-version',lambda:override('.agent/feature_list_015.json',json.dumps(f),lifecycle))
    c=load(CONTRACT);c['scope']['files_create'].append({'path':'tools/unauthorized.py','purpose':'scope spoof'});rejects('approved-contract-binding:scope',lambda:override(CONTRACT,json.dumps(c),scope))
    path='methodology/10_live_runtime_sessions.md';source=read(path)
    rejects('protocol-section12-availability',lambda:override(path,source.replace('The two schemas and executable C12 relational\nchecks validate session and operation records.','Schema records and C12 checks remain future feature111 scope.',1),registration))
    rejects('protocol-enforcement-boundary',lambda:override(path,source.replace('enforcement: consumer-aspirational','enforcement: partially-enforced',1),registration))
    rejects('record-proof-limit',lambda:override(path,source.replace('they cannot prove live','they prove live',1),registration))
    path='.agent/product_spec_015.md';source=read(path);rejects('stale-spec-current-position',lambda:override(path,source+'\nFeatures111-114 remain pending.\n',lifecycle))
    phase=yaml.safe_load(read('docs/planning/phase_015.yaml'));phase['description']='Features111-114 remain pending.';rejects('stale-phase-current-position',lambda:override('docs/planning/phase_015.yaml',yaml.safe_dump(phase),lifecycle))
    f=load('.agent/feature_list_015.json');f['case_matrix'][0]['claim_working']=True;rejects('protected-fixture-case-plan',lambda:override('.agent/feature_list_015.json',json.dumps(f),scope))
    state=load('.agent/run_state.json');state['scope_budget']['original_estimate_lines']=7300;rejects('immutable-approved-budget',lambda:override('.agent/run_state.json',json.dumps(state),scope))
    receipt=load(DIR/'recovery-approved-base.json');receipt['approved_base']=ORIGINAL;rejects('recovery-approved-base',lambda:override(DIR/'recovery-approved-base.json',json.dumps(receipt),recovery))
    archive=load(DIR/'recovery-authorization.json');archive['operator_event']['operator_text']='invented';rejects('recovery-archive-authority',lambda:override(DIR/'recovery-authorization.json',json.dumps(archive),recovery))
    state=load('.agent/run_state.json');state['history'].pop(402);rejects('history-authority-position-or-count',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    archive=load(DIR/'recovery-authorization.json');archive['prior_exhausted_counter']['attempts']=0;rejects('recovery-exhausted-counter',lambda:override(DIR/'recovery-authorization.json',json.dumps(archive),recovery))
    state=load('.agent/run_state.json');state['circuit_breaker']['111-generator-validation']['attempts']=0;rejects('recovery-other-counter:111-generator-validation',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    state=load('.agent/run_state.json');state['circuit_breaker']['111-checker-development']['limit']=4;rejects('recovery-current-counter',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    archive=load(DIR/'recovery-authorization.json');archive['operator_authority_revision']=ORIGINAL;rejects('recovery-archive-authority',lambda:override(DIR/'recovery-authorization.json',json.dumps(archive),recovery))
    review={'test_author':TEST_AUTHOR,'checker_reviewer':TEST_AUTHOR,'checker_sha256':sha(DIR/'check_111.py'),'final_verdict':{'approved':True},'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[]}
    original_exists=Path.exists
    Path.exists=lambda path:True if str(path)==str(DIR/'checker-review-detail3.json') else original_exists(path)
    try:rejects('recovery-independent-checker-review',lambda:override(DIR/'checker-review-detail3.json',json.dumps(review),recovery))
    finally:Path.exists=original_exists
    receipt=load(DIR/'recovery-approved-base.json');receipt['original_implementation_base']=AUTHORITY;rejects('recovery-approved-base',lambda:override(DIR/'recovery-approved-base.json',json.dumps(receipt),recovery))
    c=load(CONTRACT);c['scope']=json.loads(old(CONTRACT,ORIGINAL))['scope'];rejects('approved-contract-binding:scope',lambda:override(CONTRACT,json.dumps(c),scope))
    path='docs/planning/DEBT.md';source=read(path);row=next(line for line in source.splitlines() if line.startswith('| NDEBT-048 |'));text=source.replace(row+'\n','',1);text+='\n'+row+'\n';proof_path=DIR/'recovery-epoch1-development.json';original_exists=Path.exists
    Path.exists=lambda p:False if str(p)==str(proof_path) else original_exists(p)
    try:rejects('recovery-premature-debt-resolution',lambda:override(path,text,recovery))
    finally:Path.exists=original_exists
    state=load('.agent/run_state.json');state['history'][402].pop('detail');rejects('history-detail-required',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'][402]['detail']+=' ';rejects('history-detail-exact',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'][402]['operator_text']='altered';rejects('history-authority-content',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'][402]['extra']='unapproved';rejects('history-authority-content',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');detail=state['history'][402].pop('detail');state['history'][401]['detail']=detail;rejects('history-authority-position-or-count',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'][402],state['history'][403]=state['history'][403],state['history'][402];rejects('history-authority-position-or-count',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'].append(copy.deepcopy(state['history'][402]));rejects('history-authority-position-or-count',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['history'][0]['detail']+=' rewritten';rejects('operator-history-frozen',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['current_feature']=111;rejects('current-installed-runstate-schema',lambda:override('.agent/run_state.json',json.dumps(state),history_projection_state))
    state=load('.agent/run_state.json');state['circuit_breaker']['111-checker-development']['attempts']=0;rejects('history-counter-continuity:111-checker-development',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    state=load('.agent/run_state.json');state['circuit_breaker']['111-checker-development']['attempts']=1;rejects('history-counter-continuity:111-checker-development',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    state=load('.agent/run_state.json');state['circuit_breaker']['111-contract']['limit']=5;rejects('recovery-other-counter:111-contract',lambda:override('.agent/run_state.json',json.dumps(state),recovery))
    receipt=load(DIR/'history-detail-approved-base.json');receipt['approved_base']=RECOVERY_BASE;rejects('history-detail-approved-base',lambda:override(DIR/'history-detail-approved-base.json',json.dumps(receipt),history_projection_state))
    receipt=load(DIR/'history-detail-approved-base.json');receipt['authority_revision']=AUTHORITY;rejects('history-detail-approved-base',lambda:override(DIR/'history-detail-approved-base.json',json.dumps(receipt),history_projection_state))
    review=load(DIR/'checker-review-detail3.json');review['checker_sha256']=HISTORICAL_CHECKER;rejects('recovery-independent-checker-review',lambda:override(DIR/'checker-review-detail3.json',json.dumps(review),recovery))
    state=load('.agent/run_state.json');before=json.loads(old('.agent/run_state.json',APPROVED));need(state['circuit_breaker']['111-checker-development']['attempts']>=before['circuit_breaker']['111-checker-development']['attempts'],'history-counter-positive')
    print('HISTORY DETAIL VALID CONTROL: exact402single-field projection, installed schema and monotonic epoch accepted; historical244 checkpoint retained')
    print('RECOVERY VALID CONTROL: immutable authority, archived3/3 and fresh bounded epoch accepted')
    temp,tree=snapshot()
    try:
        def checked(mode,code):
            r=run(['python3',str(DIR/'check_111.py'),'--'+mode],tree);need(r.returncode==1 and 'CHECK FAIL: '+code in r.stdout,'private-negative:'+code+':'+r.stdout[-200:]);print('PRIVATE NEGATIVE REJECTED:',code)
        checker=tree/DIR/'check_111.py';shutil.copyfile(DIR/'check_111.py',checker)
        path=tree/'schema/runtime_session.schema.json';original=path.read_bytes();s=json.loads(original);s['additionalProperties']=True;path.write_text(json.dumps(s));checked('schemas','schema-closed:runtime_session');path.write_bytes(original)
        path=tree/'tools/verify_lib.sh';original=path.read_bytes();s=original.decode();needle='vlib_runtime_record_relations() {';need(needle in s,'negative-helper-layout');path.write_text(s.replace(needle,needle+'\n  return 0',1));checked('fixtures','fixture-relation:runtime_operation_neg_foreign_executed.json');path.write_bytes(original)
        path=tree/'tools/validate.sh';original=path.read_bytes();s=original.decode();needle='    "runtime_operation": "schema/runtime_operation.schema.json",';need(s.count(needle)==2,'negative-family-layout');path.write_text(s.replace(needle,'',1));checked('routing','routing-family-registration:check_c12_ecosystem_fixtures');path.write_bytes(original)
        path=tree/'tools/validate.sh';original=path.read_bytes()
        for function in ('check_c12_ecosystem_fixtures','check_c12_target'):
            text=original.decode();start=text.index(function+'() {');tail=text[start:];needle='vlib_runtime_record_relations "$1" "$2"';need(needle in tail,'negative-relation-call-layout');changed=tail.replace(needle,'true "$1" "$2"',1);path.write_text(text[:start]+changed);checked('routing','shared-relations-call:'+function);path.write_bytes(original)
        source=tree/'tools/fixtures/runtime_operation_neg_foreign_executed.json';original=source.read_bytes();renamed=source.with_name('runtime_operation_lookalike_foreign.json');source.rename(renamed);checked('fixtures','fixture-top-level-exact');renamed.rename(source)
        path=tree/'tools/fixtures_self_test.sh';original=path.read_bytes();line='assert_target runtime_operation_neg_foreign_executed.json C12 FAIL';need(line in original.decode(),'negative-standing-layout');path.write_text(original.decode().replace(line,'# '+line,1));checked('registration','fixture-standing-row:runtime_operation_neg_foreign_executed.json');path.write_bytes(original)
        path=tree/'tools/fixtures/runtime_operation_neg_foreign_executed.json';original=path.read_bytes();fixed=repair(json.loads(original),path.name);path.write_text(json.dumps(fixed));checked('fixtures','fixture-relation:runtime_operation_neg_foreign_executed.json');path.write_bytes(original)
        extra=tree/'.nizam/unauthorized-111.txt';extra.write_text('unowned');checked('scope','untracked-scope:.nizam/unauthorized-111.txt');extra.unlink()
        prior=tree/'.agent/qa/110.json';original=prior.read_bytes();prior.write_bytes(original+b'\n');checked('scope','scope:M\t.agent/qa/110.json');prior.write_bytes(original)
        path=tree/'schema/runtime_session.schema.json';original=path.read_bytes();path.write_bytes(original+b'\n');checked('scope','recovery-frozen-product:schema/runtime_session.schema.json');path.write_bytes(original)
        path=tree/DIR/'blocked-checker3/checkpoint3.txt';original=path.read_bytes();path.write_bytes(original+b'\n');checked('scope','recovery-prior-proof:'+str(DIR/'blocked-checker3/checkpoint3.txt'));path.write_bytes(original)
        path=tree/DIR/'history-detail-authorization.json';original=path.read_bytes();path.write_bytes(original+b'\n');checked('lifecycle','history-detail-authorization');path.write_bytes(original)
        inner=[str(DIR/(Path(item['path']).name+'.txt')) for item in approved()['implementation_requirements']['fixture_inventory']];saved={path:(tree/path).read_bytes() for path in inner};need(len(saved)==18,'recapture-positive-exact18')
        for path,blob in saved.items():(tree/path).write_bytes(blob+b'\nPRIVATE DEVELOPMENTAL RECAPTURE simulation\n')
        result=run(['python3',str(DIR/'check_111.py'),'--scope'],tree);need(result.returncode==0 and 'CHECK PASS: scope' in result.stdout,'recaptured-all18-positive:'+result.stdout[-200:]);print('PRIVATE POSITIVE: all18 canonical inner outputs recaptured; exact archived bytes preserved; scope PASS')
        path=tree/DIR/'blocked-checker3/checkpoint3.txt';original=path.read_bytes();path.write_bytes(original+b'\n');checked('scope','recovery-prior-proof:'+str(DIR/'blocked-checker3/checkpoint3.txt'));path.write_bytes(original)
        for path,blob in saved.items():(tree/path).write_bytes(blob)

    finally:shutil.rmtree(temp)
    print('NEGATIVE CONTROLS PASS: typed/schema/record-relation/truth/lifecycle/scope and actual private-source bypasses reject intentionally; restored positive fixtures valid; no setup-error substitution')

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for mode in ('schemas','fixtures','routing','registration','compatibility','lifecycle','scope','negative'):g.add_argument('--'+mode,action='store_true')
    a=p.parse_args();mode=next(k for k,v in vars(a).items() if v)
    try:globals()[mode]();print('CHECK PASS:',mode);return 0
    except InvariantError as e:print('CHECK FAIL:',e);return 1
    except Exception as e:print('SETUP ERROR:',type(e).__name__,e);return 2
if __name__=='__main__':sys.exit(main())
