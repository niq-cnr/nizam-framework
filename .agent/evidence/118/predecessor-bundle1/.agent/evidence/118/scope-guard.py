"""Independent feature118 scope, typed lifecycle and closure receipt checks."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import yaml
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[3]
BASE='587c40670d850d21183b7bbd7fd1e600ae84896c'
APPROVED='ccac65be80fa8750afeea728b69200be76c47ebf'
E='.agent/evidence/118/'
CONTRACT='.agent/contracts/118.json'
QA='.agent/qa/118.json'
MODE_B='.agent/validator/118-mode-b.json'
CAPTURE=E+'evidence-capture.json'
BUNDLE=E+'acceptance-bundle.json'
REVIEW='.agent/validator/118-test-bundle-review.json'

def require(ok,msg):
    if not ok: raise AssertionError('POLICY_ASSERTION: '+msg)
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def same(a,b,msg): require(canonical(a)==canonical(b),msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def strip(v,keys): return {k:x for k,x in v.items() if k not in keys}
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE).decode().strip()
def at(path,revision=APPROVED): return subprocess.check_output(['git','-C',str(ROOT),'show',revision+':'+path],stderr=subprocess.PIPE)
def parse(data):
    def pairs(items):
        d={}
        for k,v in items: require(k not in d,'duplicate JSON key');d[k]=v
        return d
    v=json.loads(data,object_pairs_hook=pairs,parse_constant=lambda _:require(False,'nonfinite JSON'));require(type(v) is dict,'JSON object');return v
def safe(path):
    require(type(path) is str and path and not path.startswith('/') and '\\' not in path and all(x not in ('','.','..','.git') for x in path.split('/')),'safe relative path')
    target=ROOT/path
    for part in (target,*target.parents):
        if part==ROOT: break
        require(not part.is_symlink(),'symlink path '+path)
    require(target.is_file() and stat.S_ISREG(target.stat().st_mode),'regular file '+path);return target
def read(path): return parse(safe(path).read_bytes())
def original(path): return parse(at(path))
def load(path):
    spec=importlib.util.spec_from_file_location('scope_module',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def gate(v):
    require(v.get('final_verdict',{}).get('approved') is True,'strict gate approved')
    for k in ('issues','missing_acceptance_coverage','unsupported_claims'): require(type(v.get(k)) is list and not v[k],'empty gate '+k)
def actor(v): require(type(v) is str and bool(v.strip()),'strict nonempty actor');return v

def entries(revision):
    result={}
    for row in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-rz',revision]).split(b'\0'):
        if row:
            meta,path=row.split(b'\t',1);mode,kind,oid=meta.decode().split();result[path.decode()]=(mode,kind,oid)
    return result

def exact(path,row):
    mode,kind,oid=row;require(kind=='blob' and mode in ('100644','100755'),'ordinary Git mode '+path);p=safe(path);b=p.read_bytes();require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'protected bytes '+path);require(bool(p.stat().st_mode&0o111)==(mode=='100755'),'protected executable mode '+path)

def approved():
    c=read(CONTRACT);old=original(CONTRACT);same(strip(c,{'status'}),strip(old,{'status'}),'immutable approved obligations');require(c['status'] in ('approved','complete'),'contract stage')
    refs=c['approvals']['gate_refs'];proposal=parse(at(CONTRACT,refs['proposal_revision']));require(refs['proposal_sha256']==sha(at(CONTRACT,refs['proposal_revision'])),'proposal digest')
    api=E+'api-interface.json';require(refs['api_sha256']==sha(at(api,refs['proposal_revision']))==sha(safe(api).read_bytes()),'approved API digest')
    expected=copy.deepcopy(proposal);expected['status']=c['status'];expected['approvals'].update(validator_mode_a=True,evaluator_contract_review=True,gate_refs=refs)
    if 'approved_at' in c['approvals']:actor(c['approvals']['approved_at']);expected['approvals']['approved_at']=c['approvals']['approved_at']
    same(c,expected,'approved proposal transition')
    for key in ('validator_mode_a','evaluator_contract_review'):
        item=refs[key];policy=c['precode_gate_policy'][key];require(item['path']==policy['path'] and item['sha256']==sha(safe(item['path']).read_bytes()),'current gate reference');v=read(item['path']);gate(v);actor(v['actor']);require(v['feature']=='118' and v['review']==policy['review'] and type(v['revision_reviewed']) is int and v['revision_reviewed']==1,'revision1 gate identity');require(v['proposal_sha256']==refs['proposal_sha256'] and v['api_sha256']==refs['api_sha256'],'gate inputs')
    return c

def seal_check(require_review):
    b=read(BUNDLE);require(b['seal_sha256']==sha(canonical(strip(b,{'seal_sha256'}))),'bundle seal')
    roles=read(E+'role-sessions.json');same(b['roles'],roles,'frozen roles')
    for key in ('agent_id','session_id'):
        values=[actor(v[key]) for v in roles.values()];require(len(values)==len(set(values))==3,'independent roles')
    revision=b['baseline']['commit'];require(re.fullmatch('[0-9a-f]{40}',revision) and git('rev-parse',revision+'^{tree}')==b['baseline']['tree'],'actual GitB')
    paths=[x['path'] for x in b['inputs']];manifest=read(E+'runtime-inputs.json');required=set(manifest['runtime_paths'])|set(manifest['core_paths'])-{'tools/workflow_assurance.py'};require(set(paths)==required and len(paths)==len(set(paths)),'complete frozen runtime/test inputs')
    for row in b['inputs']:
        require(row['sha256']==sha(safe(row['path']).read_bytes())==sha(at(row['path'],revision)),'frozen input '+row['path']);require(type(row['executable']) is bool and row['executable']==bool(safe(row['path']).stat().st_mode&0o111)==(entries(revision)[row['path']][0]=='100755'),'frozen input executable')
    for stage,exitcode,diagnostic in [('setup',0,'CURRENT20_SETUP: 20 actual commands PASS'),('positive',0,'POSITIVE_CONTROL: missing-proof PASS'),('red',1,'POLICY_ASSERTION: missing-proof intended policy outcome mismatch')]:
        row=b['baseline_evidence'][stage];text=safe(row['path']).read_text();require(row['sha256']==sha(text.encode()),'baseline proof digest');raw_text(text,row['command'],revision,exitcode);require(diagnostic in text and 'SETUP_OR_UNRELATED_ERROR:' not in text,'intended baseline '+stage)
    if require_review:
        v=read(REVIEW);require(set(v)=={'review','feature','actor','reviewer_session_id','seal_sha256','issues','missing_acceptance_coverage','unsupported_claims','final_verdict'},'nine field bundle review');gate(v);require(v['feature']=='118' and v['review']=='validator-test-bundle-review' and v['actor']==roles['acceptance_reviewer']['agent_id'] and v['reviewer_session_id']==roles['acceptance_reviewer']['session_id'] and v['seal_sha256']==b['seal_sha256'],'distinct exact bundle review');require(set(v['final_verdict'])=={'approved','summary'} and type(v['final_verdict']['summary']) is str,'review verdict shape')

def raw_text(text,command,revision,exitcode=0):
    for header,value in [('COMMAND',command),('REVISION',revision),('EXIT',str(exitcode))]:require(re.findall('^'+header+': (.*)$',text,re.M)==[value],'unique '+header+' proof')
    require(text.count('STDOUT:\n')==text.count('STDERR:\n')==1 and text.split('STDOUT:\n')[1].split('STDERR:\n')[0].strip(),'actual raw stdout/stderr')

def _closure(c,values,data):
    """Structural parser; data is a private byte reader for isolated controls."""
    candidate,prereq,mode,qa,capture=values;roles=read(E+'role-sessions.json');forbidden={actor(v['agent_id']) for v in roles.values()};ma=actor(mode.get('actor'));pa=actor(prereq.get('actor'));qa_actor=actor(qa.get('actor'));require(ma not in {roles['test_author']['agent_id'],roles['developer']['agent_id'],pa},'independent ModeB');require(qa_actor not in forbidden|{ma,pa},'fresh QA actor')
    for value in (mode,qa,capture):
        for key,v in candidate.items():same(value.get(key),v,'candidate-bound '+key)
        require(value.get('prerequisite_sha256')==sha(data(E+'prerequisite20.json')),'current prerequisite hash')
    gate(mode);gate(qa);require(mode.get('feature')=='118' and qa.get('feature_id')=='118' and capture.get('feature')=='118','closure feature')
    require(qa.get('qa_pass') is True and type(qa.get('checks_run')) is int and qa['checks_run']==3 and type(qa.get('checks_passed')) is int and qa['checks_passed']==3 and qa.get('required_fixes')==[],'strict QA counts')
    require(type(qa.get('checks')) is list and len(qa['checks'])==3,'three QA checks');proofs=[]
    for item,row in zip(c['verification'],qa['checks']):
        for k,v in item.items():same(row.get(k),v,'exact QA command/criterion')
        require(type(row.get('exit_code')) is int and row['exit_code']==0,'strict QA exit');proof=row['evidence'];require(type(proof) is str and proof.startswith(E),'118 proof path');raw=data(proof);require(row['sha256']==sha(raw),'QA raw digest');raw_text(raw.decode(),item['command'],candidate['revision']);proofs.append(proof)
    spot=qa['adversarial'];require(spot.get('performed') is True and spot.get('command') not in [x['command'] for x in c['verification']],'distinct ownspot');proofs.append(spot['evidence']);raw_text(data(spot['evidence']).decode(),spot['command'],candidate['revision']);require(len(set(proofs))==4 and type(qa['evidence_files']) is list and len(qa['evidence_files'])==len(set(qa['evidence_files'])) and set(proofs)<=set(qa['evidence_files']),'unique QA and ownspot evidence')
    require(capture.get('owner')=='/root' and capture.get('passed') is True and type(capture.get('checks_captured')) is int and capture['checks_captured']==3 and capture.get('adversarial_captured') is True,'actual Root capture counts')
    for name,path in [('qa',QA),('mode_b',MODE_B)]:require(capture[name+'_ref']==path and capture[name+'_sha256']==sha(data(path)),'capture exact '+name)
    proofs += [x['evidence'] for x in prereq['checks']];same(capture['evidence_sha256'],{p:sha(data(p)) for p in proofs},'capture all24 raw proofs')

def closure(c):
    candidate,prereq,mode,qa,capture=[read(p) for p in (E+'source-candidate.json',E+'prerequisite20.json',MODE_B,QA,CAPTURE)]
    load(ROOT/'tools/workflow_assurance.py').verify_foundation_ready(ROOT,prereq)
    Draft202012Validator(read('.nizam/schema/qa_verdict.schema.json')).validate(qa)
    _closure(c,(candidate,prereq,mode,qa,capture),lambda p:safe(p).read_bytes())

def doc(path,version,changed):
    old=at(path).decode();now=safe(path).read_text()
    if not changed:require(old==now,'pretransition doc '+path);return
    a=old.split('---',2);b=now.split('---',2);om=yaml.safe_load(a[1]);nm=yaml.safe_load(b[1]);require(nm['version']==version and len(nm['change_log'])==len(om['change_log'])+1 and nm['change_log'][0]['version']==version,'one new doc version/log '+path);same(nm['change_log'][1:],om['change_log'],'old doc log');same(strip(nm,{'version','change_log'}),strip(om,{'version','change_log'}),'old doc metadata')
    if path.endswith('HANDOVER.md'):require(a[2] in b[2],'contiguous prior handover')
    else:
        lines=iter(b[2].splitlines());require(all(any(x==line for x in lines) for line in a[2].splitlines()),'prior document body '+path)

def scope(base):
    require(base==BASE,'exact selected118 base');c=approved();allowed={x['path'] for family in ('files_create','files_modify') for x in c['scope'][family] if not x['path'].endswith('/**')};old_entries=entries(APPROVED)
    known=set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','-z']).decode().split('\0'))-{''}
    for path in known-set(old_entries):require(path in allowed or path.startswith(E),'unknown/staged/ignored path '+path);safe(path)
    for path,row in old_entries.items():
        if path not in allowed or path.startswith(('.agent/evidence/','.agent/qa/','.agent/validator/')):exact(path,row)
        else:require(bool(safe(path).stat().st_mode&0o111)==(row[0]=='100755'),'contracted Git executable '+path)
    seen=set(old_entries)
    for revision in git('rev-list','--reverse',APPROVED+'..HEAD').splitlines():
        for path,row in entries(revision).items():
            if path in seen:continue
            seen.add(path)
            if path.startswith(('.agent/evidence/','.agent/qa/','.agent/validator/')):exact(path,row)
    for path in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py'):
        before=at(path).decode();after=safe(path).read_text();old={n.name:ast.get_source_segment(before,n) for n in ast.parse(before).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};new={n.name:ast.get_source_segment(after,n) for n in ast.parse(after).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        for name,source in old.items():
            if name=='main':continue
            require(new.get(name)==source,'old function body '+name)
    state=read('.agent/run_state.json');old=original('.agent/run_state.json');fields={'status','current_feature','active_contract_id','updated_at','last_action','history','circuit_breaker','scope_budget','completed_contract_ids'};same(strip(state,fields),strip(old,fields),'unowned run_state');require(type(state['history']) is list and len(state['history'])>=len(old['history']),'history shape');same(state['history'][:len(old['history'])],old['history'],'prior typed history prefix')
    for key,value in old['circuit_breaker'].items():
        actual=state['circuit_breaker'].get(key)
        if key.startswith('118-'):require(type(actual) is dict and type(actual.get('attempts')) is int and value['attempts']<=actual['attempts']<=3,'current bounded counter');same(strip(actual,{'attempts'}),strip(value,{'attempts'}),'counter metadata')
        else:same(actual,value,'old counter '+key)
    for key in set(state['circuit_breaker'])-set(old['circuit_breaker']):
        row=state['circuit_breaker'][key];require(key.startswith('118-') and set(row)=={'attempts','limit'} and type(row['attempts']) is int and 0<=row['attempts']<=3 and type(row['limit']) is int and row['limit']==3,'new bounded118 counter')
    f=read('.agent/feature_list_017.json');fo=original('.agent/feature_list_017.json');same(strip(f,{'features','phase_status','spec_version'}),strip(fo,{'features','phase_status','spec_version'}),'feature list metadata');same(f['features'][:3],fo['features'][:3],'old115116117 feature records');require(len(f['features'])==4,'four features');feature=f['features'][3];same(strip(feature,{'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}),strip(fo['features'][3],{'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}),'118 obligations')
    phase=yaml.safe_load(safe('docs/planning/phase_017.yaml').read_text());po=yaml.safe_load(at('docs/planning/phase_017.yaml'));Draft202012Validator(read('.nizam/schema/phase.schema.json')).validate(phase);same(strip(phase,{'status','description','steps'}),strip(po,{'status','description','steps'}),'phase metadata');same(phase['steps'][:3],po['steps'][:3],'old phase steps');require(len(phase['steps'])==4,'four phase steps');step=phase['steps'][3];same(strip(step,{'status','evidence'}),strip(po['steps'][3],{'status','evidence'}),'118 step identity');complete=step['status']=='COMPLETED'
    require(phase['status']==('complete' if complete else 'in_progress') and f['phase_status']==phase['status'],'phase/list lifecycle');require(state['status']==('complete' if complete else 'in_progress'),'run lifecycle');require(state['current_feature']==state['active_contract_id']==(None if complete else '118'),'active IDs');same(state['completed_contract_ids'],old['completed_contract_ids']+(['118'] if complete else []),'completed prefix once');require(feature['status']==('complete' if complete else 'in_progress') and feature['passes'] is complete and c['status']==('complete' if complete else 'approved'),'complete tuple')
    if complete:
        require(feature.get('qa_ref')==QA and feature.get('evidence_ref')==CAPTURE and feature.get('contract_ref')==CONTRACT and step.get('evidence')==CAPTURE,'canonical captured refs');closure(c)
    else:require(step['status']=='IN_PROGRESS','active step')
    budget=state['scope_budget'];bo=old['scope_budget'];same(strip(budget,{'per_feature','total_lines_changed','evidence_lines_total','excluded_lines_total','last_measured_at'}),strip(bo,{'per_feature','total_lines_changed','evidence_lines_total','excluded_lines_total','last_measured_at'}),'budget frozen categories/history');same(budget['per_feature'][:3],bo['per_feature'],'prior measured rows');require(len(budget['per_feature'])==(4 if complete else 3),'one measurement only after capture')
    if complete:
        row=budget['per_feature'][3];require(row['id']=='118' and type(row['estimated']) is int and row['estimated']==650,'118 estimated row')
        for k in ('actual','product_lines','process_overhead_lines','evidence_lines','excluded_lines'):require(type(row[k]) is int and row[k]>=0,'integer measured '+k)
        require(row['actual']==row['product_lines']+row['process_overhead_lines'],'measured counted sum');safe(row['evidence']);require(type(budget['total_lines_changed']) is int and budget['total_lines_changed']==4012+row['actual']<=7020,'phase ceiling measured')
        for k,rk in [('evidence_lines_total','evidence_lines'),('excluded_lines_total','excluded_lines')]:require(type(budget[k]) is int and budget[k]==bo[k]+row[rk],'measured '+k)
    else:same(budget,bo,'active budget exact')
    manifest=read('docs/planning/manifest.json');mo=original('docs/planning/manifest.json');Draft202012Validator(read('.nizam/schema/manifest.schema.json')).validate(manifest);same(strip(manifest,{'updated_at','phases'}),strip(mo,{'updated_at','phases'}),'manifest root');require(len(manifest['phases'])==len(mo['phases']),'manifest rows')
    for row,prior in zip(manifest['phases'],mo['phases']):
        if prior['id']=='017-workflow-assurance-foundation':same(strip(row,{'status','finished_at','note'}),strip(prior,{'status','finished_at','note'}),'manifest017 fields');require(row['status']==phase['status'],'manifest017 lifecycle')
        else:same(row,prior,'other manifest rows')
    dag=read('docs/planning/backlog_dag.json');do=original('docs/planning/backlog_dag.json');same(strip(dag,{'generated_at','phase017_execution','packets','planned_additional_nodes'}),strip(do,{'generated_at','phase017_execution','packets','planned_additional_nodes'}),'DAG original/proposed/adopted edges')
    require(len(dag['packets'])==len(do['packets']),'DAG packet count')
    for row,prior in zip(dag['packets'],do['packets']):
        if complete and prior['id']=='A04b':same(strip(row,{'status','qa','completion_evidence','completed_at'}),strip(prior,{'status','qa','completion_evidence','completed_at'}),'foundation ownership packet');require(row['status']=='complete' and row.get('completion_evidence')==CAPTURE and row.get('qa')==QA,'foundation ownership actual capture')
        else:same(row,prior,'other packets immutable')
    require(len(dag['planned_additional_nodes'])==len(do['planned_additional_nodes']),'node count')
    for row,prior in zip(dag['planned_additional_nodes'],do['planned_additional_nodes']):
        if complete and prior['feature_id'] in ('117','118'):same(strip(row,{'status','evidence'}),strip(prior,{'status','evidence'}),'foundation node');require(row['status']=='complete' and row['evidence']=='.agent/evidence/'+prior['feature_id']+'/evidence-capture.json','foundation node capture')
        else:same(row,prior,'other nodes')
    fields={'status','feature','feature_status','qa','evidence','completed_at'};same(strip(dag['phase017_execution'],fields),strip(do['phase017_execution'],fields),'DAG projection ownership');require(dag['phase017_execution']['feature']==(None if complete else '118') and dag['phase017_execution']['status']==phase['status'] and dag['phase017_execution']['feature_status']==feature['status'],'DAG current lifecycle')
    delivered=safe('tools/workflow_assurance.py').read_bytes()!=at('tools/workflow_assurance.py')
    for path,version in [('tools/README.md','0.24.0'),('docs/planning/ROADMAP.md','0.65.0'),('docs/planning/HANDOVER.md','1.0.13')]:doc(path,version,delivered)
    for path,version in [('.agent/product_spec_017.md','0.3.0'),('docs/planning/operator_gates.md','0.38.0')]:doc(path,version,complete)
    require(f['spec_version']==('0.3.0' if complete else '0.2.0'),'spec/list mirror')
    before=at('CHANGELOG.md').decode();after=safe('CHANGELOG.md').read_text()
    if not delivered:require(before==after,'pre-source changelog')
    else:
        oldlines=before.splitlines();i=0;added=[]
        for line in after.splitlines():
            if i<len(oldlines) and line==oldlines[i]:i+=1
            else:added.append(line)
        body=[x for x in added if x.strip()];require(i==len(oldlines) and body and body[0].startswith('- ') and '118' in '\n'.join(body) and all(x.startswith('  ') for x in body[1:]),'one118 changelog bullet');start=after.index('### Changed',after.index('## [Unreleased]'));end=after.find('\n##',start+1);require(all(x in after[start:end if end>=0 else None] for x in body),'Unreleased Changed location')
    if (ROOT/BUNDLE).exists():seal_check(delivered)
    if delivered:require((ROOT/BUNDLE).is_file(),'delivered frozen bundle')
    historical=read(E+'historical-runtime-inputs.json')
    require(git('rev-parse','refs/tags/'+historical['tag']+'^{commit}')==historical['tag_revision'],'historical installed tag')
    for row in historical['inputs']:
        require(row['sha256']==sha(at(row['path'],row['revision'])) and row['executable']==(entries(row['revision'])[row['path']][0]=='100755'),'immutable transitive historical input')
    print('PASS scope118: selected scope, typed history/budget/lifecycle, frozen inputs and bounded closure')

def _private_parser_controls():
    """Synthetic dictionaries test this parser only; cannot call public completion."""
    c=read(CONTRACT);candidate=dict(revision='1'*40,tree='2'*40,source_sha256={},runtime_sha256={},historical_sha256={});data={};prereq=dict(candidate,actor='fixture-prereq',checks=[])
    for i in range(20):
        path=E+'private-prereq-'+str(i);data[path]=b'PRIVATE parser fixture only';prereq['checks'].append({'evidence':path})
    data[E+'prerequisite20.json']=canonical(prereq);common=dict(candidate,prerequisite_sha256=sha(data[E+'prerequisite20.json']),issues=[],missing_acceptance_coverage=[],unsupported_claims=[],final_verdict={'approved':True,'summary':'PRIVATE parser fixture only'})
    mode=dict(common,feature='118',actor='fixture-mode-b');data[MODE_B]=canonical(mode);checks=[];paths=[]
    for i,item in enumerate(c['verification']):
        path=E+'private-qa-'+str(i);data[path]=('COMMAND: '+item['command']+'\nREVISION: '+candidate['revision']+'\nEXIT: 0\nSTDOUT:\nPRIVATE parser fixture only\nSTDERR:\n').encode();checks.append(dict(item,exit_code=0,evidence=path,sha256=sha(data[path])));paths.append(path)
    spot=E+'private-ownspot';command='private parser spot';data[spot]=('COMMAND: '+command+'\nREVISION: '+candidate['revision']+'\nEXIT: 0\nSTDOUT:\nPRIVATE parser fixture only\nSTDERR:\n').encode();paths.append(spot)
    qa=dict(common,feature_id='118',actor='fixture-fresh-qa',qa_pass=True,checks_run=3,checks_passed=3,required_fixes=[],checks=checks,evidence_files=paths,adversarial={'performed':True,'command':command,'evidence':spot});data[QA]=canonical(qa)
    capture=dict(candidate,feature='118',owner='/root',passed=True,prerequisite_sha256=common['prerequisite_sha256'],qa_ref=QA,mode_b_ref=MODE_B,qa_sha256=sha(data[QA]),mode_b_sha256=sha(data[MODE_B]),checks_captured=3,adversarial_captured=True,evidence_sha256={p:sha(b) for p,b in data.items() if p in paths or p.startswith(E+'private-prereq-')})
    values=(candidate,prereq,mode,qa,capture);_closure(c,values,data.__getitem__)
    attacks=[(2,'actor',[]),(3,'actor',mode['actor']),(3,'qa_pass',1),(3,'checks_run',True),(4,'checks_captured',True),(4,'owner','not-root'),(4,'qa_sha256','0'*64),(4,'evidence_sha256',{})]
    for index,key,value in attacks:
        bad=copy.deepcopy(values);bad[index][key]=value
        try:_closure(c,bad,data.__getitem__)
        except AssertionError:continue
        require(False,'private closure parser attack accepted '+key)
    print('PASS private closure parser: valid structure plus actor/count/hash/coverage rejection; no production receipt claim')

def scope_controls(base):
    global ROOT
    require(base==BASE,'exact controls base');scope(base);_private_parser_controls();source=ROOT
    with tempfile.TemporaryDirectory(prefix='nizam118-scope-controls-') as parent:
        scratch=Path(parent)/'repo';subprocess.run(['git','clone','-q','--shared',str(source),str(scratch)],check=True)
        ROOT=scratch
        try:
            scope(base)
            attacks=[('.agent/run_state.json',lambda v:v['history'].__setitem__(0,{'altered':True})),('.agent/run_state.json',lambda v:v['circuit_breaker'][next(k for k in v['circuit_breaker'] if not k.startswith('118-'))].update(attempts=True)),('.agent/run_state.json',lambda v:v['scope_budget']['per_feature'][0].update(actual=0)),('.agent/feature_list_017.json',lambda v:v['features'][0].update(passes=False))]
            for path,change in attacks:
                target=safe(path);saved=target.read_bytes();v=parse(saved);change(v);target.write_bytes(canonical(v))
                try:
                    try:scope(base)
                    except AssertionError:pass
                    else:require(False,'scope accepted mutation '+path)
                finally:target.write_bytes(saved)
            (ROOT/'.git/info/exclude').write_text('.hidden118/\n')
            for path,staged in [('unknown118.txt',False),('unknown118-staged.txt',True),('.hidden118/unknown.bin',False)]:
                target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('unknown')
                if staged:git('add',path)
                try:
                    try:scope(base)
                    except AssertionError:pass
                    else:require(False,'scope accepted unknown/staged path')
                finally:
                    if staged:git('rm','--cached','-q',path)
                    target.unlink()
            target=ROOT/'docs/planning/DEBT.md';saved=target.read_bytes();mode=target.stat().st_mode;target.chmod(mode^0o111)
            try:
                try:scope(base)
                except AssertionError:pass
                else:require(False,'scope accepted executable drift')
            finally:target.chmod(mode)
            target.unlink();target.symlink_to(ROOT/'CHANGELOG.md')
            try:
                try:scope(base)
                except AssertionError:pass
                else:require(False,'scope accepted symlink')
            finally:target.unlink();target.write_bytes(saved);target.chmod(mode)
            scope(base)
        finally:ROOT=source
    print('PASS scope-controls118: private positive/negative parser plus isolated history/counter/budget/unknown/staged/mode/symlink controls')
