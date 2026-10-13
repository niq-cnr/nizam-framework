"""Independent repository-only feature117 scope and canonical receipt checks.

Private mock transitions exercise this guard's structural receipt parser only;
the public entry never accepts mock receipts or grants implementation authority.
"""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import yaml
import jsonschema

BASE = '79af0276408ba03e80c709af127133e2b55e7bea'
APPROVED = '970ea233f77b4468105ddf6e401babbd0049d0b2'
PROPOSAL = 'f42e1b91d21c99a16d90f1e403f48ec37341b1ac'
ROOT = Path(__file__).resolve().parents[3]
CORE = ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py',
        '.agent/evidence/117/api-interface.json', '.agent/evidence/117/scope-guard.py')
CANDIDATE = '.agent/evidence/117/source-candidate.json'
MODE_B = '.agent/validator/117-mode-b.json'
QA = '.agent/qa/117.json'
CAPTURE = '.agent/evidence/117/evidence-capture.json'
BUNDLE = '.agent/evidence/117/acceptance-bundle.json'
REVIEW = '.agent/validator/117-test-bundle-review.json'
_CONTROL_FIXTURE = None


def require(ok, message):
    if not ok: raise AssertionError('POLICY_ASSERTION: ' + message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(data): return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE).decode().strip()


def read_at(revision, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + path], stderr=subprocess.PIPE)


def json_bytes(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON receipt key'); result[key] = value
        return result
    result = json.loads(data, object_pairs_hook=pairs,
                        parse_constant=lambda value: require(False, 'nonfinite receipt JSON'))
    require(type(result) is dict, 'receipt JSON object'); return result


def safe(path):
    require(type(path) is str and path and not path.startswith('/') and '\\' not in path,
            'portable receipt path')
    require(all(part not in ('', '.', '..', '.git') for part in path.split('/')), 'safe receipt path components')
    target = ROOT / path
    for part in (target, *target.parents):
        if part == ROOT: break
        require(not part.is_symlink(), 'symlink path component ' + path)
    require(target.is_file(), 'required regular file exists: ' + path); return target


def current(path): return json_bytes(safe(path).read_bytes())
def at(path): return json_bytes(read_at(APPROVED, path))
def same(a, b, message): require(canonical(a) == canonical(b), message)


def strip(value, fields): return {k: v for k, v in value.items() if k not in fields}


def tree_entries(revision):
    entries = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-rz', revision]).split(b'\0')
    result = {}
    for entry in entries:
        if entry:
            meta, name = entry.split(b'\t', 1); mode, kind, oid = meta.decode().split()
            require(kind == 'blob' and mode in ('100644', '100755'), 'ordinary immutable Git input')
            result[name.decode()] = (mode, oid)
    return result


def exact_file(path, mode, oid):
    target = safe(path); data = target.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    require(actual == oid, 'protected immutable bytes ' + path)
    require(bool(target.stat().st_mode & 0o111) == (mode == '100755'), 'protected executable mode ' + path)


def approved_contract():
    approved = at('.agent/contracts/117.json'); contract = current('.agent/contracts/117.json')
    same(strip(contract, {'status'}), strip(approved, {'status'}), 'approved117 obligations immutable')
    require(contract['status'] in ('approved', 'complete'), 'current117 contract stage')
    refs = contract['approvals']['gate_refs']; proposal = json_bytes(read_at(PROPOSAL, '.agent/contracts/117.json'))
    require(refs['proposal_revision'] == PROPOSAL and refs['proposal_sha256'] == sha(read_at(PROPOSAL,'.agent/contracts/117.json')),
            'actual immutable proposal117')
    require(refs['api_sha256'] == sha(read_at(PROPOSAL,CORE[2])) == sha(safe(CORE[2]).read_bytes()), 'current117 API binds approved proposal')
    expected = copy.deepcopy(proposal); expected['status'] = contract['status']
    expected['approvals'].update(validator_mode_a=True,evaluator_contract_review=True,gate_refs=refs)
    if 'approved_at' in contract['approvals']: expected['approvals']['approved_at']=contract['approvals']['approved_at']
    same(contract,expected,'strict approved proposal transition')
    for role in ('validator_mode_a','evaluator_contract_review'):
        ref=refs[role]; v=current(ref['path']); policy=contract['gate_reference_policy'][role]
        require(ref['path']==policy['path'] and ref['sha256']==sha(safe(ref['path']).read_bytes()),'actual current-revision gate bytes')
        gate(v)
        require(v['review']==policy['review'] and v['feature']=='117' and type(v['revision_reviewed']) is int and v['revision_reviewed']==2,
                'strict current gate producer identity')
        require(v['proposal_sha256']==refs['proposal_sha256'] and v['api_sha256']==refs['api_sha256'] and v['actor'], 'same proposal/API gate inputs')
    return contract, approved


def sealed_inputs():
    bundle=current(BUNDLE); review=current(REVIEW)
    require(bundle['seal_sha256']==sha(canonical(strip(bundle,{'seal_sha256'}))), 'immutable117 bundle seal')
    keys={'review','feature','actor','reviewer_session_id','seal_sha256','issues','missing_acceptance_coverage','unsupported_claims','final_verdict'}
    require(set(review)==keys,'exact nine-field117 bundle review'); gate(review)
    reviewer=bundle['roles']['acceptance_reviewer']
    require(review['review']=='validator-test-bundle-review' and review['feature']=='117' and
            review['actor']==reviewer['agent_id'] and review['reviewer_session_id']==reviewer['session_id'] and
            review['seal_sha256']==bundle['seal_sha256'], 'independent117 reviewer and exact seal')
    require(set(review['final_verdict'])=={'approved','summary'} and type(review['final_verdict']['summary']) is str and review['final_verdict']['summary'], 'closed reviewed verdict')
    roles=bundle['roles']; require(set(roles)=={'test_author','developer','acceptance_reviewer'},'three acceptance roles')
    for key in ('agent_id','session_id'):
        values=[x[key] for x in roles.values()]
        require(all(type(v) is str and v for v in values) and len(set(values))==3,'three distinct '+key)
    baseline=bundle['baseline']['commit']; require(re.fullmatch('[0-9a-f]{40}',baseline) and git('rev-parse',baseline+'^{commit}')==baseline,'actual117 baseline commit')
    require(bundle['baseline']['tree']==git('rev-parse',baseline+'^{tree}'),'actual117 baseline tree')
    rows=bundle['inputs']; require(type(rows) is list and len({x['path'] for x in rows})==len(rows),'unique sealed input paths')
    required={CORE[1],CORE[2],CORE[3],'.agent/evidence/117/entry-fixtures.py','.agent/evidence/117/naive-policy.py',
              '.agent/evidence/117/baseline-driver.py','.agent/evidence/117/archived-product.py',
              '.agent/evidence/117/source-obligations.json','.agent/evidence/117/role-sessions.json',
              '.agent/evidence/116/bundle-fixtures.py'}
    require(required <= {x['path'] for x in rows},'all transitive runtime helpers sealed')
    for row in rows:
        target=safe(row['path']); require(row['sha256']==sha(target.read_bytes())==sha(read_at(baseline,row['path'])),'sealed current/Git input '+row['path'])
        require(type(row['executable']) is bool and row['executable']==bool(target.stat().st_mode&0o111)==(git('ls-tree',baseline,row['path']).split()[0]=='100755'),'sealed input mode')
    require(bundle['required_cases']==['accepted-entry','reject-foreign-repo','reject-stale-pin','reject-role-write'],'exact four117 baseline cases')
    require([x['case'] for x in bundle['baseline_evidence']]==bundle['required_cases'],'complete ordered117 baseline evidence')
    for row in bundle['baseline_evidence']:
        op=row['operation']; require(op['target']=='verify_authorized_entry','entry baseline target')
        expected='accept' if row['case']=='accepted-entry' else 'reject'
        require(op['expected_result']==expected,'case-specific expected outcome')
        for key in ('positive_input','case_input'):
            item=op[key];require(item['sha256']==sha(safe(item['path']).read_bytes()),'sealed baseline case input')
        for stage in ('setup','positive','red'):
            item=row[stage];text=safe(item['path']).read_text()
            require(item['sha256']==sha(text.encode()),'actual baseline proof bytes')
            require(re.findall(r'^COMMAND: (.*)$',text,re.M)==[item['command']] and re.findall(r'^REVISION: (.*)$',text,re.M)==[baseline],'baseline command/revision exact')
            require(re.findall(r'^EXIT: (-?[0-9]+)$',text,re.M)==['1' if stage=='red' else '0'],'actual baseline stage exit')
            require('STDOUT:\n' in text and 'STDERR:\n' in text and 'SETUP_OR_UNRELATED_ERROR:' not in text,'real baseline streams and no setup failure')
            diagnostic=('TARGET_CALLABLE: verify_authorized_entry PASS' if stage=='setup' else 'POSITIVE_CONTROL: '+row['case']+' PASS' if stage=='positive' else 'POLICY_ASSERTION: '+row['case']+' intended policy outcome mismatch')
            require(diagnostic in text,'case-specific semantic proof')
            if stage!='setup':
                inp=op['positive_input' if stage=='positive' else 'case_input']
                require(re.findall(r'^INPUT_SHA256: (.*)$',text,re.M)==[inp['sha256']] and re.findall(r'^OPERATION_SHA256: (.*)$',text,re.M)==[sha(canonical(op))],'baseline input/operation binding')
            if stage=='red': require(re.findall(r'^OBSERVED_RESULT: (.*)$',text,re.M)==['reject' if expected=='accept' else 'accept'],'discriminating observed red')


def gate(value):
    require(value.get('final_verdict', {}).get('approved') is True, 'receipt strict approved boolean')
    for key in ('issues','missing_acceptance_coverage','unsupported_claims'):
        require(value.get(key) == [] and type(value[key]) is list, 'receipt empty blockers ' + key)


def raw(path, command, revision):
    require(path.startswith('.agent/evidence/117/'), '117 proof scope')
    text = safe(path).read_text()
    require(re.findall(r'^COMMAND: (.*)$', text, re.M) == [command], 'actual unique command ' + command)
    require(re.findall(r'^REVISION: (.*)$', text, re.M) == [revision], 'actual unique source revision')
    require(re.findall(r'^EXIT: (-?[0-9]+)$', text, re.M) == ['0'], 'actual zero exit')
    require('STDOUT:' in text and 'STDERR:' in text, 'external raw stdout/stderr')


def completed_receipts(contract):
    sealed_inputs()
    candidate, mode_b, qa, capture = [current(path) for path in (CANDIDATE, MODE_B, QA, CAPTURE)]
    private = _CONTROL_FIXTURE is not None and ROOT.resolve() == _CONTROL_FIXTURE
    for value in (candidate, mode_b, qa, capture):
        require(value.get('mock_fixture', False) is private, 'mock receipts confined to private scratch')
    revision = candidate.get('revision')
    require(type(revision) is str and re.fullmatch('[0-9a-f]{40}', revision), 'actual SourceC revision')
    require(git('rev-parse', revision + '^{commit}') == revision and candidate.get('tree') == git('rev-parse', revision + '^{tree}'), 'actual SourceC commit/tree')
    hashes = candidate.get('source_sha256')
    require(type(hashes) is dict and set(hashes) == set(CORE), 'exact four SourceC hashes')
    dependencies = {row['path']: row['sha256'] for row in current(BUNDLE)['inputs']}
    for value in (candidate, mode_b, qa, capture):
        same(value.get('sealed_dependencies_sha256'), dependencies, 'all sealed runtime dependency hashes')
    for path, digest in hashes.items():
        target = safe(path); require(digest == sha(target.read_bytes()) == sha(read_at(revision, path)), 'current SourceC digest ' + path)
        require(bool(target.stat().st_mode & 0o111) == (git('ls-tree', revision, path).split()[0] == '100755'), 'SourceC executable mode')
    for value in (mode_b, qa, capture):
        require(value.get('revision') == revision and value.get('source_sha256') == hashes, 'same SourceC bound closure receipts')
    gate(mode_b); gate(qa)
    require(mode_b.get('feature') == '117' and qa.get('feature_id') == '117' and capture.get('feature') == '117', '117-only closure')
    roles = current('.agent/evidence/117/role-sessions.json')
    forbidden = {roles['test_author']['agent_id'], roles['developer']['agent_id']}
    require(mode_b.get('actor') and mode_b['actor'] not in forbidden, 'independent ModeB actor')
    require(qa.get('actor') and qa['actor'] not in forbidden | {mode_b['actor'], roles['acceptance_reviewer']['agent_id']}, 'distinct fresh QA actor')
    jsonschema.validate(qa, json.loads(safe('.nizam/schema/qa_verdict.schema.json').read_text()))
    count = len(contract['verification'])
    require(count == 12 and qa.get('qa_pass') is True and type(qa.get('checks_run')) is int and qa['checks_run'] == count and
            type(qa.get('checks_passed')) is int and qa['checks_passed'] == count and qa.get('required_fixes') == [], 'all twelve exact checks passed')
    checks = qa.get('checks'); require(type(checks) is list and len(checks) == count, 'twelve typed actual QA checks')
    evidence = qa.get('evidence_files'); require(type(evidence) is list and len(evidence) == len(set(evidence)), 'unique QA evidence references')
    for expected, actual in zip(contract['verification'], checks):
        require(actual.get('command') == expected['command'] and actual.get('acceptance_test') == expected['acceptance_test'] and
                type(actual.get('exit_code')) is int and actual['exit_code'] == 0 and actual.get('evidence') in evidence, 'typed QA check matches contracted command')
        raw(actual['evidence'], expected['command'], revision)
        require(actual.get('sha256') == sha(safe(actual['evidence']).read_bytes()), 'QA freezes actual raw command bytes')
    spot = qa.get('adversarial', {})
    require(spot.get('performed') is True and spot.get('evidence') in evidence and spot.get('command') and
            spot['command'] not in [x['command'] for x in checks], 'fresh own additional adversarial spot')
    raw(spot['evidence'], spot['command'], revision)
    require(capture.get('passed') is True and capture.get('owner') == '/root' and capture.get('qa_ref') == QA and
            capture.get('mode_b_ref') == MODE_B and type(capture.get('checks_captured')) is int and capture['checks_captured'] == count and capture.get('adversarial_captured') is True,
            'distinct Root capture names actual complete gates')
    require(capture.get('qa_sha256') == sha(safe(QA).read_bytes()) and capture.get('mode_b_sha256') == sha(safe(MODE_B).read_bytes()), 'capture actual gate/QA hashes')
    inventory = capture.get('evidence_sha256'); require(type(inventory) is dict and set(evidence) <= set(inventory), 'capture covers every actual QA proof')
    for path, digest in inventory.items(): require(digest == sha(safe(path).read_bytes()), 'capture exact proof bytes')


def budget(state, complete):
    old=at('.agent/run_state.json')['scope_budget']; new=state['scope_budget']
    fields={'total_lines_changed','evidence_lines_total','excluded_lines_total','per_feature','last_measured_at','estimated_current_feature_lines'}
    same(strip(new,fields),strip(old,fields),'immutable budget authority and historical measurements')
    if 'estimated_current_feature_lines' in new:
        require(type(new['estimated_current_feature_lines']) is int and new['estimated_current_feature_lines']==1050,'typed117 estimate1050')
    rows=new['per_feature']; prior=old['per_feature']
    require(type(rows) is list and len(rows) in (len(prior),len(prior)+1),'budget row shape')
    same(rows[:len(prior)],prior,'old115116 measured rows exact types')
    if len(rows)==len(prior):
        require(not complete,'complete117 requires measured row')
        same(strip(new,{'estimated_current_feature_lines'}),strip(old,{'estimated_current_feature_lines'}),'no premature measurement')
    else:
        require(complete,'no pre-capture budget append'); row=rows[-1]
        require(row.get('id')=='117' and type(row.get('estimated')) is int and row['estimated']==1050 and
                type(row.get('actual')) is int and row['actual']>=0,'typed actual117 measured row')
        require(type(new['total_lines_changed']) is int and new['total_lines_changed']==3009+row['actual']<=7020,'typed phase sum original ceiling')
        require(row.get('evidence','').startswith('.agent/evidence/117/') and safe(row['evidence']).read_bytes(),'actual measurement evidence')
        for key in ('product_lines','process_overhead_lines','evidence_lines','excluded_lines'):
            require(type(row.get(key)) is int and row[key]>=0,'typed actual measurement category '+key)
        require(row['actual']==row['product_lines']+row['process_overhead_lines'],'counted category sum')
        for key in ('evidence_lines_total','excluded_lines_total'):
            require(type(new[key]) is int and new[key]>=old[key],'typed monotonic '+key)


def documents(delivered):
    for path,version in {'tools/README.md':'0.23.0','docs/planning/ROADMAP.md':'0.64.0','docs/planning/HANDOVER.md':'1.0.12'}.items():
        before=read_at(APPROVED,path).decode(); now=safe(path).read_text()
        if not delivered: require(before==now,'pre-source docs exact'); continue
        oldparts=before.split('---',2); parts=now.split('---',2)
        old=yaml.safe_load(oldparts[1]); new=yaml.safe_load(parts[1])
        require(new['version']==version and len(new['change_log'])==len(old['change_log'])+1,'one117 doc version/log')
        same(new['change_log'][1:],old['change_log'],'prior doc logs exact')
        require(new['change_log'][0]['version']==version,'new log matches version')
        same(strip(new,{'version','change_log'}),strip(old,{'version','change_log'}),'unowned doc metadata exact')
        if path.endswith('HANDOVER.md'):
            require(oldparts[2] in parts[2],'entire prior handover body exact')
        else:
            lines=iter(parts[2].splitlines())
            for line in oldparts[2].splitlines(): require(any(x==line for x in lines),'old doc body retained')
    old=read_at(APPROVED,'CHANGELOG.md').decode(); new=safe('CHANGELOG.md').read_text()
    if not delivered: require(old==new,'pre-source changelog exact')
    else:
        oldlines=old.splitlines(); newlines=new.splitlines(); additions=[]; i=0
        for line in newlines:
            if i<len(oldlines) and line==oldlines[i]: i+=1
            else: additions.append(line)
        nonblank=[x for x in additions if x.strip()]
        require(i==len(oldlines) and nonblank and nonblank[0].startswith('- ') and
                all(x.startswith('  ') for x in nonblank[1:]) and '117' in '\n'.join(nonblank), 'exact one117 changelog bullet')
        start=new.index('### Changed',new.index('## [Unreleased]')); end=new.find('\n##',start+1)
        require(all(x in new[start:end if end!=-1 else None] for x in nonblank),'117 bullet in Unreleased Changed')


def debt(complete):
    before=read_at(APPROVED,'docs/planning/DEBT.md').decode(); now=safe('docs/planning/DEBT.md').read_text()
    if before==now: return
    require(complete,'debt053 transition only after actual capture')
    a=before.split('---',2); b=now.split('---',2); old=yaml.safe_load(a[1]); new=yaml.safe_load(b[1])
    require(new['version']=='0.73.0' and len(new['change_log'])==len(old['change_log'])+1 and
            new['change_log'][0]['version']=='0.73.0','sole debt053 version/log')
    same(new['change_log'][1:],old['change_log'],'old debt logs exact')
    same(strip(new,{'version','change_log'}),strip(old,{'version','change_log'}),'old debt metadata exact')
    oldrow=[x for x in a[2].splitlines() if x.startswith('| NDEBT-053 |')]
    newrow=[x for x in b[2].splitlines() if x.startswith('| NDEBT-053 |')]
    require(len(oldrow)==len(newrow)==1 and 'RESOLVED' in newrow[0].upper() and CAPTURE in newrow[0] and QA in newrow[0], '053 actual resolution refs')
    # Moving the one row between Open and Resolved is permitted; all other bytes remain exact.
    require(a[2].replace(oldrow[0]+'\n','')==b[2].replace(newrow[0]+'\n',''),'all other debt body exact')


def _scope(base):
    require(base==BASE,'exact contracted117 scope base')
    contract,approved=approved_contract()
    allowed={item['path'] for family in ('files_create','files_modify') for item in approved['scope'][family] if not item['path'].endswith('/**')}
    entries=tree_entries(APPROVED); original=tree_entries(BASE)
    for path in set(entries)-set(original):
        require(path in allowed or path.startswith('.agent/evidence/117/'),'approved delta within original117 membership')
    for path,(mode,oid) in entries.items():
        if path not in allowed or path.startswith(('.agent/evidence/','.agent/qa/','.agent/validator/')): exact_file(path,mode,oid)
    # Freeze newly committed proofs at their first appearance; never apply this to product revisions.
    seen=set(entries)
    for revision in git('rev-list','--reverse',APPROVED+'..HEAD').splitlines():
        for path,(mode,oid) in tree_entries(revision).items():
            if path in seen: continue
            seen.add(path)
            if path.startswith(('.agent/evidence/','.agent/qa/','.agent/validator/')): exact_file(path,mode,oid)
    # Without exclude-standard, Git includes ignored files as well as ordinary untracked files.
    known=set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','-z']).decode().split('\0'))-{''}
    for path in known-set(entries):
        require(path in allowed or path.startswith('.agent/evidence/117/'),'unknown scope path '+path); safe(path)
    for path in allowed & set(entries):
        require(bool(safe(path).stat().st_mode&0o111)==(entries[path][0]=='100755'),'contracted executable mode '+path)
    state=current('.agent/run_state.json'); old=at('.agent/run_state.json')
    fields={'status','current_feature','active_contract_id','updated_at','last_action','history','circuit_breaker','scope_budget','completed_contract_ids'}
    same(strip(state,fields),strip(old,fields),'all unowned state exact')
    require(type(state['history']) is list and len(state['history'])>=len(old['history']),'history prefix shape')
    same(state['history'][:len(old['history'])],old['history'],'exact prior history prefix types')
    require(type(state['circuit_breaker']) is dict,'counter object')
    for key,value in old['circuit_breaker'].items():
        actual=state['circuit_breaker'].get(key)
        if key.startswith('117-recovery1-'):
            require(type(actual) is dict and type(actual.get('attempts')) is int and value['attempts']<=actual['attempts']<=3,'typed recovery counter no reset')
            same(strip(actual,{'attempts'}),strip(value,{'attempts'}),'prior recovery counter metadata')
        else: same(actual,value,'historical counter exact '+key)
    for key in set(state['circuit_breaker'])-set(old['circuit_breaker']):
        value=state['circuit_breaker'][key]
        require(key.startswith('117-') and set(value)=={'attempts','limit'} and type(value['attempts']) is int and
                0<=value['attempts']<=3 and type(value['limit']) is int and value['limit']==3,'new117 bounded integer counter')
    features=current('.agent/feature_list_017.json'); prior=at('.agent/feature_list_017.json')
    same(strip(features,{'features'}),strip(prior,{'features'}),'phase/list metadata exact in_progress')
    require(len(features['features'])==4,'exact four features')
    for i in (0,1,3): same(features['features'][i],prior['features'][i],'old115116 and future118 exact')
    feature=features['features'][2]
    same(strip(feature,{'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}),strip(prior['features'][2],{'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}),'117 obligations exact')
    phase=yaml.safe_load(safe('docs/planning/phase_017.yaml').read_text()); prior=yaml.safe_load(read_at(APPROVED,'docs/planning/phase_017.yaml'))
    jsonschema.validate(phase,current('.nizam/schema/phase.schema.json'))
    same(strip(phase,{'steps','description'}),strip(prior,{'steps','description'}),'canonical phase in_progress')
    require(type(phase['description']) is str and phase['description'],'current phase description text')
    require(len(phase['steps'])==4,'exact canonical steps')
    for i in (0,1,3): same(phase['steps'][i],prior['steps'][i],'canonical other steps exact')
    step=phase['steps'][2]; same(strip(step,{'status','evidence'}),strip(prior['steps'][2],{'status','evidence'}),'117 canonical step identity')
    complete=step['status']=='COMPLETED'
    require(state['status']=='in_progress','run remains017 in_progress')
    if complete:
        require(feature['status']=='complete' and feature['passes'] is True and contract['status']=='complete','117 complete tuple')
        require(state['current_feature'] is None and state['active_contract_id'] is None,'captured117 clears active fields')
        same(state['completed_contract_ids'],old['completed_contract_ids']+['117'],'completed117 append once')
        require(feature.get('contract_ref')=='.agent/contracts/117.json' and feature.get('qa_ref')==QA and feature.get('evidence_ref')==CAPTURE and step.get('evidence')==CAPTURE,'exact117 completion refs')
        completed_receipts(contract)
    else:
        require(step['status']=='IN_PROGRESS' and feature['status']=='in_progress' and feature['passes'] is False and contract['status']=='approved','117 in_progress tuple')
        require(state['current_feature']==state['active_contract_id']=='117','current117 active contract')
        same(state['completed_contract_ids'],old['completed_contract_ids'],'old completed IDs exact')
    budget(state,complete); debt(complete)
    manifest=current('docs/planning/manifest.json'); before=at('docs/planning/manifest.json')
    same(strip(manifest,{'updated_at','phases'}),strip(before,{'updated_at','phases'}),'manifest root exact')
    require(len(manifest['phases'])==len(before['phases']),'manifest rows length')
    for actual,prior in zip(manifest['phases'],before['phases']):
        same(strip(actual,{'note'}) if prior['id']=='017-workflow-assurance-foundation' else actual,
             strip(prior,{'note'}) if prior['id']=='017-workflow-assurance-foundation' else prior,'manifest owned current017 note only')
    dag=current('docs/planning/backlog_dag.json'); before=at('docs/planning/backlog_dag.json')
    same(strip(dag,{'generated_at','phase017_execution'}),strip(before,{'generated_at','phase017_execution'}),'all DAG packets/edges exact')
    fields={'feature','feature_status','qa','evidence','completed_at'}
    same(strip(dag['phase017_execution'],fields),strip(before['phase017_execution'],fields),'DAG current117 owned fields only')
    require(dag['phase017_execution']['feature']==(None if complete else '117') and dag['phase017_execution']['feature_status']==('complete' if complete else 'in_progress'),'current117 DAG projection')
    delivered=safe(CORE[0]).read_bytes()!=read_at(APPROVED,CORE[0]); documents(delivered)
    if delivered: sealed_inputs()
    print('PASS scope117: typed current tuple, immutable history, budget, proof and current SourceC boundary')


def scope(base):
    require(_CONTROL_FIXTURE is None,'public scope has no fixture bypass'); _scope(base)


def write(path,value):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(value))


def expected_rejection(operation, diagnostic):
    try: operation()
    except AssertionError as exc:
        require('POLICY_ASSERTION:' in str(exc) and diagnostic in str(exc),'intended rejection '+diagnostic+': '+str(exc)); return
    require(False,'scope false-pass '+diagnostic)


def _private_complete_fixture():
    """Parser-only fixture in a scratch clone; public scope rejects its mock bit."""
    (ROOT/CORE[0]).write_text('# PRIVATE mock parser candidate; no product acceptance\n')
    for path,version in {'tools/README.md':'0.23.0','docs/planning/ROADMAP.md':'0.64.0','docs/planning/HANDOVER.md':'1.0.12'}.items():
        p=ROOT/path;parts=p.read_text().split('---',2);meta=yaml.safe_load(parts[1]);meta['version']=version
        meta['change_log'].insert(0,{'version':version,'date':'2026-10-13','summary':'Private117 parser fixture.'})
        p.write_text('---\n'+yaml.safe_dump(meta,sort_keys=False,allow_unicode=True)+'---'+parts[2])
    p=ROOT/'CHANGELOG.md';text=p.read_text();text=text.replace('### Changed','### Changed\n- Private117 parser fixture.',1);p.write_text(text)
    git('config','user.name','Independent Private Receipt Fixture');git('config','user.email','fixture@example.invalid')
    git('add',*CORE);git('commit','-qm','PRIVATE117 receipt parser SourceC')
    revision=git('rev-parse','HEAD');hashes={p:sha(safe(p).read_bytes()) for p in CORE}
    deps={r['path']:r['sha256'] for r in current(BUNDLE)['inputs']}
    binding={'mock_fixture':True,'revision':revision,'source_sha256':hashes,'sealed_dependencies_sha256':deps}
    write(CANDIDATE,{**binding,'tree':git('rev-parse',revision+'^{tree}')})
    verdict={**binding,'review':'validator-mode-b','feature':'117','actor':'private-mode-b',
             'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],
             'final_verdict':{'approved':True,'summary':'PRIVATE parser fixture only'}}
    write(MODE_B,verdict);contract=current('.agent/contracts/117.json');checks=[];evidence=[]
    for index,item in enumerate(contract['verification']):
        path='.agent/evidence/117/private-check-'+str(index)+'.txt'
        (ROOT/path).write_text('PRIVATE parser fixture\nCOMMAND: '+item['command']+'\nREVISION: '+revision+'\nEXIT: 0\nSTDOUT:\nmock\nSTDERR:\n')
        checks.append({**item,'exit_code':0,'evidence':path,'sha256':sha(safe(path).read_bytes())});evidence.append(path)
    spot='.agent/evidence/117/private-spot.txt';command='private117 additional parser spot'
    (ROOT/spot).write_text('PRIVATE parser fixture\nCOMMAND: '+command+'\nREVISION: '+revision+'\nEXIT: 0\nSTDOUT:\nmock\nSTDERR:\n');evidence.append(spot)
    write(QA,{**verdict,'actor':'private-fresh-qa','feature_id':'117','qa_pass':True,'checks_run':12,'checks_passed':12,
              'checks':checks,'required_fixes':[],'evidence_files':evidence,'adversarial':{'performed':True,'evidence':spot,'command':command}})
    write(CAPTURE,{**binding,'feature':'117','owner':'/root','passed':True,'qa_ref':QA,'mode_b_ref':MODE_B,
                   'qa_sha256':sha(safe(QA).read_bytes()),'mode_b_sha256':sha(safe(MODE_B).read_bytes()),
                   'checks_captured':12,'adversarial_captured':True,'evidence_sha256':{p:sha(safe(p).read_bytes()) for p in evidence}})
    contract['status']='complete';write('.agent/contracts/117.json',contract)
    features=current('.agent/feature_list_017.json');features['features'][2].update(status='complete',passes=True,contract_ref='.agent/contracts/117.json',qa_ref=QA,evidence_ref=CAPTURE);write('.agent/feature_list_017.json',features)
    phase=yaml.safe_load(safe('docs/planning/phase_017.yaml').read_text());phase['steps'][2].update(status='COMPLETED',evidence=CAPTURE);(ROOT/'docs/planning/phase_017.yaml').write_text(yaml.safe_dump(phase,sort_keys=False,allow_unicode=True))
    state=current('.agent/run_state.json');state.update(current_feature=None,active_contract_id=None);state['completed_contract_ids'].append('117')
    measure='.agent/evidence/117/private-measure.txt';(ROOT/measure).write_text('PRIVATE parser measurement fixture\n')
    state['scope_budget']['per_feature'].append({'id':'117','estimated':1050,'actual':100,'product_lines':50,'process_overhead_lines':50,'evidence_lines':0,'excluded_lines':0,'evidence':measure})
    state['scope_budget']['total_lines_changed']=3109;write('.agent/run_state.json',state)
    dag=current('docs/planning/backlog_dag.json');dag['phase017_execution'].update(feature=None,feature_status='complete',qa=QA,evidence=CAPTURE);write('docs/planning/backlog_dag.json',dag)


def scope_controls(base):
    global ROOT, _CONTROL_FIXTURE
    require(base==BASE,'exact controls117 base'); original_root=ROOT
    with tempfile.TemporaryDirectory(prefix='nizam117-scope-controls-') as parent:
        scratch=Path(parent)/'repo'
        subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(scratch)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subprocess.run(['git','-C',str(scratch),'checkout','-q',APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Honest pre-source approved snapshot; API117 comes from the approved revision.
        ROOT=scratch
        try:
            with contextlib.redirect_stdout(io.StringIO()): scope(base)
            print('PASS scope-controls117 actual active117 approved snapshot')
            statepath='.agent/run_state.json'; before=current(statepath); original=safe(statepath).read_bytes()
            positive=copy.deepcopy(before);positive['history'].append({'event':'117-private-control','detail':'scratch only'})
            positive['circuit_breaker']['117-control-positive']={'attempts':1,'limit':3}
            positive['scope_budget']['estimated_current_feature_lines']=1050;write(statepath,positive)
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            safe(statepath).write_bytes(original);print('PASS scope-controls117 owned append/counter/estimate positive')
            probes=[(['active_contract_id'],'118','current117 active contract'),
                    (['status'],'complete','run remains017'),
                    (['history',331,'ga_declared'],1,'exact prior history prefix types'),
                    (['history',331,'workflow_run'],True,'exact prior history prefix types'),
                    (['scope_budget','per_feature',0,'actual'],1863.0,'old115116 measured rows exact types'),
                    (['scope_budget','per_feature',1,'actual'],True,'old115116 measured rows exact types'),
                    (['circuit_breaker','000-contract','attempts'],True,'historical counter exact'),
                    (['circuit_breaker','117-contract-review','attempts'],0,'historical counter exact'),
                    (['phase_015_scope_budget_final','total_lines_changed'],7319.0,'all unowned state exact'),
                    (['scope_budget','estimated_current_feature_lines'],1050.0,'typed117 estimate1050')]
            for location,value,diagnostic in probes:
                obj=copy.deepcopy(before);target=obj
                for key in location[:-1]:target=target[key]
                target[location[-1]]=value;write(statepath,obj)
                expected_rejection(lambda:scope(base),diagnostic);safe(statepath).write_bytes(original)
                print('PASS scope-controls117 typed rejection '+str(location))
            for path,mode in [('.agent/evidence/115/api-interface.json','bytes'),('.agent/evidence/116/api-interface.json','mode'),
                              (CORE[2],'bytes'),('.nizam/tools/SKILL.md','bytes'),('docs/planning/DEBT.md','bytes')]:
                p=ROOT/path;data=p.read_bytes();permissions=p.stat().st_mode
                if mode=='mode':p.chmod(0o755)
                else:p.write_bytes(data+b'\n')
                expected_rejection(lambda:scope(base),'debt053 transition' if path.endswith('DEBT.md') else 'current117 API' if path==CORE[2] else 'protected')
                p.write_bytes(data);p.chmod(permissions)
                print('PASS scope-controls117 protected '+path)
            for path in ('stray117.txt','__pycache__/ignored117.pyc'):
                p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('scratch only\n')
                expected_rejection(lambda:scope(base),'unknown scope path');p.unlink()
            print('PASS scope-controls117 unknown and ignored paths')
            p=ROOT/'staged117.txt';p.write_text('scratch only\n');git('add','staged117.txt')
            expected_rejection(lambda:scope(base),'unknown scope path');git('rm','-q','staged117.txt')
            p=ROOT/'tools/README.md';saved=p.read_bytes();p.unlink();p.symlink_to('../README.md')
            expected_rejection(lambda:scope(base),'symlink path component');p.unlink();p.write_bytes(saved)
            print('PASS scope-controls117 staged unknown and symlink')
            features=current('.agent/feature_list_017.json');features['features'][2].update(status='complete',passes=True)
            write('.agent/feature_list_017.json',features);expected_rejection(lambda:scope(base),'117 in_progress tuple')
            print('PASS scope-controls117 premature list completion')
            (ROOT/'.agent/feature_list_017.json').write_bytes(read_at(APPROVED,'.agent/feature_list_017.json'))
            # Copy the real sealed author bundle, not any old116 acceptance seal.
            real_bundle=json_bytes((original_root/BUNDLE).read_bytes())
            paths={row['path'] for row in real_bundle['inputs']}|{BUNDLE}
            for row in real_bundle['baseline_evidence']:
                paths.update(row[k]['path'] for k in ('setup','positive','red'))
            for path in paths:
                target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original_root/path,target)
            reviewer=real_bundle['roles']['acceptance_reviewer']
            write(REVIEW,{'review':'validator-test-bundle-review','feature':'117','actor':reviewer['agent_id'],
                  'reviewer_session_id':reviewer['session_id'],'seal_sha256':real_bundle['seal_sha256'],
                  'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],
                  'final_verdict':{'approved':True,'summary':'PRIVATE receipt parser fixture, not a live gate'}})
            _private_complete_fixture()
            expected_rejection(lambda:scope(base),'mock receipts confined')
            _CONTROL_FIXTURE=ROOT.resolve()
            with contextlib.redirect_stdout(io.StringIO()):_scope(base)
            print('PASS scope-controls117 PRIVATE completion parser positive; public rejects mock receipts')
            for path,location,value,diagnostic in [
                (CAPTURE,['checks_captured'],12.0,'distinct Root capture'),
                (QA,['checks_run'],12.0,'all twelve exact checks passed'),
                (CANDIDATE,['sealed_dependencies_sha256',CORE[3]],'0'*64,'all sealed runtime dependency hashes'),
                (CANDIDATE,['source_sha256',CORE[0]],'0'*64,'current SourceC digest'),
                ('.agent/run_state.json',['scope_budget','per_feature',2,'actual'],100.0,'typed actual117 measured row')]:
                target=ROOT/path;saved=target.read_bytes();obj=current(path);container=obj
                for key in location[:-1]:container=container[key]
                container[location[-1]]=value;write(path,obj)
                expected_rejection(lambda:_scope(base),diagnostic);target.write_bytes(saved)
                print('PASS scope-controls117 PRIVATE typed receipt reject '+str(location))
            target=ROOT/CAPTURE;saved=target.read_bytes();target.unlink()
            expected_rejection(lambda:_scope(base),'required regular file exists');target.write_bytes(saved)
            with contextlib.redirect_stdout(io.StringIO()):_scope(base)
            print('PASS scope-controls117 PRIVATE missing capture rejects, restored positive')
        finally: ROOT=original_root; _CONTROL_FIXTURE=None


