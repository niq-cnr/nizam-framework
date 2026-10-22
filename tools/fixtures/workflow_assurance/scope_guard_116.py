"""Independent repository-only feature116 scope and canonical receipt checks.

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

BASE = '3d81ff2af002b118e3747551f740848a9ffb3cd9'
APPROVED = 'abe4626044da4425d5d5a01bf586c8b40fd2b2e2'
ROOT = Path(__file__).resolve().parents[3]
CORE = ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py',
        '.agent/evidence/116/api-interface.json', '.agent/evidence/116/scope-guard.py')
CANDIDATE = '.agent/evidence/116/source-candidate.json'
MODE_B = '.agent/validator/116-mode-b.json'
QA = '.agent/qa/116.json'
CAPTURE = '.agent/evidence/116/evidence-capture.json'
BUNDLE = '.agent/evidence/116/acceptance-bundle.json'
REVIEW = '.agent/validator/116-test-bundle-review.json'
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
    approved = at('.agent/contracts/116.json'); contract = current('.agent/contracts/116.json')
    require(approved['status'] == 'approved' and approved['approvals']['validator_mode_a'] is True and
            approved['approvals']['evaluator_contract_review'] is True, 'actual dual approved contract')
    same(strip(contract, {'status'}), strip(approved, {'status'}), 'approved116 obligations immutable')
    require(contract['status'] in ('approved', 'complete'), 'current contract stage'); return contract, approved


def sealed_inputs():
    bundle = current(BUNDLE); review = current(REVIEW)
    require(bundle['seal_sha256'] == sha(canonical(strip(bundle, {'seal_sha256'}))), 'actual immutable bundle seal')
    keys = {'review','feature','actor','reviewer_session_id','seal_sha256','issues',
            'missing_acceptance_coverage','unsupported_claims','final_verdict'}
    require(set(review) == keys, 'exact nine-field independent bundle review')
    reviewer = bundle['roles']['acceptance_reviewer']
    require(review['review'] == 'validator-test-bundle-review' and review['feature'] == '116' and
            review['actor'] == reviewer['agent_id'] and review['reviewer_session_id'] == reviewer['session_id'] and
            review['seal_sha256'] == bundle['seal_sha256'], 'review binds exact sealed bundle and reviewer')
    gate(review)
    require(set(review['final_verdict']) == {'approved','summary'} and bool(review['final_verdict']['summary']), 'closed review verdict')
    revision = bundle['baseline']['commit']
    require(re.fullmatch('[0-9a-f]{40}', revision) and git('rev-parse', revision + '^{commit}') == revision,
            'bundle actual baseline Git commit')
    require(bundle['baseline']['tree'] == git('rev-parse', revision + '^{tree}'), 'bundle actual baseline tree')
    for item in bundle['inputs']:
        target = safe(item['path'])
        require(item['sha256'] == sha(target.read_bytes()) == sha(read_at(revision, item['path'])), 'sealed input current/Git bytes ' + item['path'])
        mode = git('ls-tree', revision, item['path']).split()[0]
        require(type(item['executable']) is bool and item['executable'] == (mode == '100755') == bool(target.stat().st_mode & 0o111), 'sealed input executable mode')
    for row in bundle['baseline_evidence']:
        for record in (row['setup'], row['positive'], row['red'], row['operation']['positive_input'], row['operation']['case_input']):
            require(sha(safe(record['path']).read_bytes()) == record['sha256'], 'sealed proof/input current bytes')


def gate(value):
    require(value.get('final_verdict', {}).get('approved') is True, 'receipt strict approved boolean')
    for key in ('issues','missing_acceptance_coverage','unsupported_claims'):
        require(value.get(key) == [] and type(value[key]) is list, 'receipt empty blockers ' + key)


def raw(path, command, revision):
    require(path.startswith('.agent/evidence/116/'), '116 proof scope')
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
    for path, digest in hashes.items():
        target = safe(path); require(digest == sha(target.read_bytes()) == sha(read_at(revision, path)), 'current SourceC digest ' + path)
        require(bool(target.stat().st_mode & 0o111) == (git('ls-tree', revision, path).split()[0] == '100755'), 'SourceC executable mode')
    for value in (mode_b, qa, capture):
        require(value.get('revision') == revision and value.get('source_sha256') == hashes, 'same SourceC bound closure receipts')
    gate(mode_b); gate(qa)
    require(mode_b.get('feature') == '116' and qa.get('feature_id') == '116' and capture.get('feature') == '116', '116-only closure')
    roles = current('.agent/evidence/116/role-sessions.json')
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
    old = at('.agent/run_state.json')['scope_budget']; new = state['scope_budget']
    allowed = {'total_lines_changed','evidence_lines_total','excluded_lines_total','per_feature','last_measured_at','estimated_current_feature_lines'}
    same(strip(new, allowed), strip(old, allowed), 'immutable budget authority/categories/old inflight records')
    if 'estimated_current_feature_lines' in new:
        require(type(new['estimated_current_feature_lines']) is int and new['estimated_current_feature_lines'] == 1400, '116 estimate typed integer1400')
    prior = old['per_feature']; rows = new['per_feature']
    require(type(rows) is list and len(rows) in (len(prior), len(prior) + 1), 'immutable115 measured entry/prefix shape')
    same(rows[:len(prior)], prior, 'immutable115 measured entry/prefix exact types')
    require(prior[0]['id'] == '115' and prior[0]['actual'] == 1863 and prior[0]['estimated'] == 2300, 'captured115 actual1863 estimate2300')
    if len(rows) == len(prior):
        require(not complete, 'captured116 requires actual budget entry')
        same(strip(new, {'estimated_current_feature_lines'}), strip(old, {'estimated_current_feature_lines'}), 'no premature actual measurement')
    else:
        require(complete, 'no pre-capture116 budget append')
        row = rows[-1]; require(type(row) is dict and row.get('id') == '116' and type(row.get('estimated')) is int and row['estimated'] == 1400 and
                                type(row.get('actual')) is int and row['actual'] >= 0, 'canonical counted116 budget schema')
        require(type(new['total_lines_changed']) is int and new['total_lines_changed'] == 1863 + row['actual'] <= 7020, 'actual017 typed integer sum within original7020')
        require(row.get('evidence', '').startswith('.agent/evidence/116/') and safe(row['evidence']).read_text().strip(), 'actual116 measurement external proof')
        for key in ('evidence_lines_total', 'excluded_lines_total'):
            require(type(new[key]) is int and new[key] >= old[key], 'monotonic measured ' + key)


def documents(delivered):
    versions = {'tools/README.md': '0.22.0', 'docs/planning/ROADMAP.md': '0.63.0', 'docs/planning/HANDOVER.md': '1.0.11'}
    for path, version in versions.items():
        before = read_at(APPROVED, path).decode(); now = safe(path).read_text()
        if not delivered: require(before == now, 'pre-source documentation unchanged ' + path); continue
        original = before.split('---', 2); actual = now.split('---', 2)
        old, new = yaml.safe_load(original[1]), yaml.safe_load(actual[1])
        require(str(new['version']) == version and len(new['change_log']) == len(old['change_log']) + 1, 'one116 version/log ' + path)
        same(new['change_log'][1:], old['change_log'], 'historical doc logs exact')
        same(strip(new, {'version','change_log'}), strip(old, {'version','change_log'}), 'unowned doc metadata exact')
        body = original[2]
        if path.endswith('HANDOVER.md'):
            anchor = '\n## Previous current-status snapshot'; require(anchor in body and body[body.index(anchor):] in actual[2], 'whole previous handover/history body exact')
        else:
            # Additive overlay keeps existing authored body and earlier allocations intact.
            iterator = iter(actual[2].splitlines())
            for line in body.splitlines(): require(any(candidate == line for candidate in iterator), 'old document body line preserved ' + path)
    before = read_at(APPROVED, 'CHANGELOG.md').decode(); now = safe('CHANGELOG.md').read_text()
    if not delivered: require(before == now, 'pre-source change notes unchanged')
    else:
        iterator = iter(now.splitlines())
        for line in before.splitlines(): require(any(candidate == line for candidate in iterator), 'all earlier change notes exact')


def _scope(base):
    require(base == BASE, 'exact contracted116 scope base')
    contract, approved = approved_contract()
    allowed = {item['path'] for family in ('files_create','files_modify') for item in approved['scope'][family] if not item['path'].endswith('/**')}
    entries = tree_entries(APPROVED)
    for path, (mode, oid) in entries.items():
        if path not in allowed: exact_file(path, mode, oid)
        elif path.startswith(('.agent/evidence/','.agent/validator/','.agent/qa/')): exact_file(path, mode, oid)
    # Independently frozen authored evidence/guard/proofs remain exact after promotion.
    seen = set(entries)
    for revision in git('rev-list', '--reverse', APPROVED + '..HEAD').splitlines():
        for path, (mode, oid) in tree_entries(revision).items():
            if path in seen: continue
            seen.add(path)
            if path.startswith(('.agent/evidence/','.agent/qa/','.agent/validator/')): exact_file(path, mode, oid)
    known = set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','-z']).decode().split('\0')) - {''}
    for path in known - set(entries):
        require(path in allowed or path.startswith('.agent/evidence/116/'), 'unknown scope path ' + path)
        safe(path)
    for path in allowed & set(entries):
        target = safe(path); mode = entries[path][0]
        require(bool(target.stat().st_mode & 0o111) == (mode == '100755'), 'contracted file mode unchanged ' + path)
    state = current('.agent/run_state.json'); old = at('.agent/run_state.json')
    state_fields = {'status','current_feature','active_contract_id','updated_at','last_action','history','circuit_breaker','scope_budget','completed_contract_ids'}
    same(strip(state, state_fields), strip(old, state_fields), 'all unowned state/installedauthority/finalbudgets exact')
    require(type(state['history']) is list and len(state['history']) >= len(old['history']), 'exact prior history prefix list shape')
    same(state['history'][:len(old['history'])], old['history'], 'exact prior history prefix types')
    require(type(state['circuit_breaker']) is dict, 'typed circuit breaker object')
    for key, value in old['circuit_breaker'].items():
        actual = state['circuit_breaker'].get(key)
        if key.startswith('116-'):
            require(type(actual) is dict and type(actual.get('attempts')) is int and value['attempts'] <= actual['attempts'] <= 3, '116 typed integer counter no reset/overflow')
            same(strip(actual, {'attempts'}), strip(value, {'attempts'}), 'existing116 counter metadata preserved')
        else: same(actual, value, 'old circuit counter exact ' + key)
    for key in set(state['circuit_breaker']) - set(old['circuit_breaker']):
        value = state['circuit_breaker'][key]
        require(key.startswith('116-') and type(value) is dict and type(value.get('limit')) is int and value['limit'] == 3 and type(value.get('attempts')) is int and 0 <= value['attempts'] <= 3, 'new116-only typed integer bounded counter')
    features, original = current('.agent/feature_list_017.json'), at('.agent/feature_list_017.json')
    same(strip(features, {'features'}), strip(original, {'features'}), 'phase/list frozen metadata and in_progress')
    require(len(features['features']) == 4 and [x['id'] for x in features['features']] == ['115','116','117','118'], 'exact ordered feature list')
    for index in (0,2,3): same(features['features'][index], original['features'][index], 'other feature record exact')
    feature = features['features'][1]; same(strip(feature, {'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}), strip(original['features'][1], {'status','passes','contract_ref','qa_ref','evidence_ref','completed_at'}), '116 obligations/estimate exact')
    phase = yaml.safe_load(safe('docs/planning/phase_017.yaml').read_text())
    previous = yaml.safe_load(read_at(APPROVED, 'docs/planning/phase_017.yaml'))
    jsonschema.validate(phase, json.loads(safe('.nizam/schema/phase.schema.json').read_text()))
    same(strip(phase, {'steps'}), strip(previous, {'steps'}), '017 canonical phase remains in_progress')
    require(len(phase['steps']) == 4, 'exact phase steps')
    for index in (0,2,3): same(phase['steps'][index], previous['steps'][index], 'old115/future117118 canonical step exact')
    step = phase['steps'][1]; same(strip(step, {'status','evidence'}), strip(previous['steps'][1], {'status','evidence'}), '116 canonical step identity')
    complete = step['status'] == 'COMPLETED'
    require(state['status'] == 'in_progress', 'run remains017 in_progress')
    if complete:
        require(feature['status'] == 'complete' and feature['passes'] is True and contract['status'] == 'complete', 'captured116 canonical complete tuple')
        require(state['current_feature'] is None and state['active_contract_id'] is None, 'captured116 clears active fields')
        same(state['completed_contract_ids'], old['completed_contract_ids'] + ['116'], 'captured116 typed completed IDs append once')
        require(feature.get('contract_ref') == '.agent/contracts/116.json' and feature.get('qa_ref') == QA and feature.get('evidence_ref') == CAPTURE and step.get('evidence') == CAPTURE, 'exact116 completion receipt paths')
        completed_receipts(contract)
    else:
        require(step['status'] == 'IN_PROGRESS' and feature['status'] == 'in_progress' and feature['passes'] is False and contract['status'] == 'approved', 'canonical116 in_progress tuple')
        require(state['current_feature'] == state['active_contract_id'] == '116', 'current_feature/active_contract_id116')
        same(state['completed_contract_ids'], old['completed_contract_ids'], 'typed completed IDs preserve exact historical prefix')
    budget(state, complete)
    manifest, before = current('docs/planning/manifest.json'), at('docs/planning/manifest.json')
    same(strip(manifest, {'updated_at','phases'}), strip(before, {'updated_at','phases'}), 'manifest root exact')
    require(len(manifest['phases']) == len(before['phases']), 'manifest exact rows')
    for actual, prior in zip(manifest['phases'], before['phases']):
        if prior['id'] != '017-workflow-assurance-foundation': same(actual, prior, 'all other manifest phases exact')
        else:
            same(strip(actual, {'note','notes','updated_at'}), strip(prior, {'note','notes','updated_at'}), '017 manifest active/in_progress and other fields exact')
    dag, before = current('docs/planning/backlog_dag.json'), at('docs/planning/backlog_dag.json')
    same(strip(dag, {'generated_at','phase017_execution'}), strip(before, {'generated_at','phase017_execution'}), 'all DAG packets/edges/allocations exact')
    fields = {'feature','feature_status','qa','evidence','completed_at'}
    same(strip(dag['phase017_execution'], fields), strip(before['phase017_execution'], fields), 'DAG phase017 fixed identity/status/lane')
    require(dag['phase017_execution']['feature'] == (None if complete else '116') and dag['phase017_execution']['feature_status'] == ('complete' if complete else 'in_progress'), 'DAG current116 projection')
    delivered = safe('tools/workflow_assurance.py').read_bytes() != read_at(APPROVED, 'tools/workflow_assurance.py')
    documents(delivered)
    if delivered: sealed_inputs()
    print('PASS scope116: canonical tuple, exact immutable inventory/history, SourceC receipt/budget boundary')


def scope(base):
    require(_CONTROL_FIXTURE is None, 'public scope has no mock context'); _scope(base)


def write(path, value):
    target = ROOT / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(canonical(value))


def expected_rejection(operation, diagnostic):
    try: operation()
    except AssertionError as exc:
        require(diagnostic in str(exc) and 'POLICY_ASSERTION:' in str(exc), 'intended scope diagnostic, not setup error: ' + str(exc)); return
    require(False, 'scope false-pass ' + diagnostic)


def mock_delivered():
    (ROOT / 'tools/workflow_assurance.py').write_text('# PRIVATE MOCK SourceC structural parser fixture only\n')
    for path, version in {'tools/README.md':'0.22.0','docs/planning/ROADMAP.md':'0.63.0','docs/planning/HANDOVER.md':'1.0.11'}.items():
        target = ROOT / path; parts = target.read_text().split('---',2); meta = yaml.safe_load(parts[1]); meta['version'] = version
        meta['change_log'].insert(0, {'version':version,'date':'2026-10-13','summary':'PRIVATE MOCK structural doc fixture only.'})
        target.write_text('---\n' + yaml.safe_dump(meta,sort_keys=False,allow_unicode=True) + '---' + parts[2])


def mock_complete():
    git('config','user.name','Private Receipt Fixture'); git('config','user.email','mock@example.invalid')
    git('add', *CORE); git('commit','-qm','PRIVATE MOCK actual fixture SourceC, never product acceptance')
    revision = git('rev-parse','HEAD'); hashes = {path: sha(safe(path).read_bytes()) for path in CORE}
    binding = {'mock_fixture':True,'revision':revision,'source_sha256':hashes}
    write(CANDIDATE, {**binding,'tree':git('rev-parse',revision+'^{tree}')})
    verdict = {**binding,'review':'validator-mode-b','feature':'116','actor':'mock-independent-mode-b',
               'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],
               'final_verdict':{'approved':True,'summary':'PRIVATE MOCK parser fixture only.'}}
    write(MODE_B, verdict); contract = current('.agent/contracts/116.json'); evidence = []; checks = []
    for index, item in enumerate(contract['verification']):
        path = '.agent/evidence/116/private-mock-check-' + str(index) + '.txt'; target = ROOT / path
        target.write_text('PRIVATE MOCK only\nCOMMAND: '+item['command']+'\nREVISION: '+revision+'\nEXIT: 0\nSTDOUT:\nmock only\nSTDERR:\n')
        evidence.append(path); checks.append({**item,'exit_code':0,'evidence':path,'sha256':sha(target.read_bytes())})
    spot = '.agent/evidence/116/private-mock-spot.txt'; command = 'private mock additional spot'
    (ROOT/spot).write_text('PRIVATE MOCK only\nCOMMAND: '+command+'\nREVISION: '+revision+'\nEXIT: 0\nSTDOUT:\nmock only\nSTDERR:\n'); evidence.append(spot)
    write(QA, {**verdict,'actor':'mock-fresh-independent-evaluator','feature_id':'116','qa_pass':True,
               'checks_run':12,'checks_passed':12,'checks':checks,'required_fixes':[],
               'evidence_files':evidence,'adversarial':{'performed':True,'evidence':spot,'command':command}})
    write(CAPTURE, {**binding,'feature':'116','owner':'/root','passed':True,'qa_ref':QA,'mode_b_ref':MODE_B,
                    'qa_sha256':sha(safe(QA).read_bytes()),'mode_b_sha256':sha(safe(MODE_B).read_bytes()),
                    'checks_captured':12,'adversarial_captured':True,'evidence_sha256':{p:sha(safe(p).read_bytes()) for p in evidence}})
    contract['status']='complete'; write('.agent/contracts/116.json',contract)
    features=current('.agent/feature_list_017.json'); features['features'][1].update(status='complete',passes=True,contract_ref='.agent/contracts/116.json',qa_ref=QA,evidence_ref=CAPTURE);write('.agent/feature_list_017.json',features)
    phase=yaml.safe_load(safe('docs/planning/phase_017.yaml').read_text());phase['steps'][1].update(status='COMPLETED',evidence=CAPTURE);(ROOT/'docs/planning/phase_017.yaml').write_text(yaml.safe_dump(phase,sort_keys=False,allow_unicode=True))
    state=current('.agent/run_state.json');state.update(current_feature=None,active_contract_id=None);state['completed_contract_ids'].append('116')
    measure='.agent/evidence/116/private-mock-measure.txt';(ROOT/measure).write_text('PRIVATE MOCK counted measurement only\n')
    state['scope_budget']['per_feature'].append({'id':'116','estimated':1400,'actual':100,'evidence':measure});state['scope_budget']['total_lines_changed']=1963;write('.agent/run_state.json',state)
    dag=current('docs/planning/backlog_dag.json');dag['phase017_execution'].update(feature=None,feature_status='complete',qa=QA,evidence=CAPTURE);write('docs/planning/backlog_dag.json',dag)


def scope_controls(base):
    global ROOT, _CONTROL_FIXTURE
    require(base==BASE,'exact controls116 base');original_root=ROOT
    with tempfile.TemporaryDirectory(prefix='nizam116-scope-controls-') as temp:
        scratch=Path(temp)/'repo';subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(scratch)],check=True)
        subprocess.run(['git','-C',str(scratch),'checkout','-q',APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Copy authored E116 inputs/receipts; do not alter any already approved path.
        for path in [Path('tools/test_workflow_assurance.py'), *[p.relative_to(ROOT) for p in (ROOT/'.agent/evidence/116').rglob('*') if p.is_file()]]:
            if path.as_posix() in tree_entries(APPROVED): continue
            target=scratch/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
        shutil.copy2(ROOT/'tools/test_workflow_assurance.py',scratch/'tools/test_workflow_assurance.py')
        ROOT=scratch
        try:
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            print('PASS scope-controls116 genuine pre-source in-progress positive')
            def field(path, parent, key, value):
                data=current(path);target=data[parent] if parent else data;target[key]=value;write(path,data)
            state_path=ROOT/'.agent/run_state.json'; saved_state=state_path.read_bytes()
            partial=current('.agent/run_state.json')
            partial['history'].append({'event':'116-private-control-partial-append','detail':'PRIVATE fixture, no authority.'})
            partial['circuit_breaker']['116-tests']['attempts']+=1
            partial['circuit_breaker']['116-control-partial']={'attempts':1,'limit':3}
            partial['scope_budget']['estimated_current_feature_lines']=1400
            write('.agent/run_state.json',partial)
            try:
                with contextlib.redirect_stdout(io.StringIO()):scope(base)
                print('PASS scope-controls116 valid partial Root116 history/counter/estimate append')
            finally:state_path.write_bytes(saved_state)
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            def typed_edit(location, value):
                data=current('.agent/run_state.json');target=data
                for component in location[:-1]:target=target[component]
                target[location[-1]]=value;write('.agent/run_state.json',data)
            before=current('.agent/run_state.json')
            require(before['history'][331]['ga_declared'] is True, 'real historical GA boolean fixture')
            historical_run=before['history'][331]['workflow_run']
            require(type(historical_run) is int, 'real historical workflow integer fixture')
            require(before['circuit_breaker']['000-contract']['attempts']==1 and type(before['circuit_breaker']['000-contract']['attempts']) is int, 'real old counter integer-one fixture')
            typed_probes=[
                ('history-ga-bool-to-int',['history',331,'ga_declared'],1,'exact prior history prefix types'),
                ('history-ga-bool-to-float',['history',331,'ga_declared'],1.0,'exact prior history prefix types'),
                ('history-run-int-to-float',['history',331,'workflow_run'],float(historical_run),'exact prior history prefix types'),
                ('history-run-int-to-bool',['history',331,'workflow_run'],True,'exact prior history prefix types'),
                ('old-budget-prefix-int-to-float',['scope_budget','per_feature',0,'actual'],1863.0,'immutable115 measured entry/prefix exact types'),
                ('old-budget-prefix-int-to-bool',['scope_budget','per_feature',0,'actual'],True,'immutable115 measured entry/prefix exact types'),
                ('old-budget-estimate-int-to-float',['scope_budget','per_feature',0,'estimated'],2300.0,'immutable115 measured entry/prefix exact types'),
                ('old-counter-int-to-bool',['circuit_breaker','000-contract','attempts'],True,'old circuit counter exact'),
                ('old-counter-int-to-float',['circuit_breaker','000-contract','attempts'],1.0,'old circuit counter exact'),
                ('current116-counter-int-to-bool',['circuit_breaker','116-tests','attempts'],True,'116 typed integer counter'),
                ('current116-counter-int-to-float',['circuit_breaker','116-tests','attempts'],1.0,'116 typed integer counter'),
                ('closed015-budget-int-to-float',['phase_015_scope_budget_final','total_lines_changed'],7319.0,'all unowned state'),
                ('current-estimate-float',['scope_budget','estimated_current_feature_lines'],1400.0,'116 estimate typed integer1400'),
                ('new-counter-float-limit',['circuit_breaker','116-extra-limit'],{'attempts':1,'limit':3.0},'new116-only typed integer bounded counter')]
            for name,location,value,diagnostic in typed_probes:
                with contextlib.redirect_stdout(io.StringIO()):scope(base)
                saved=state_path.read_bytes()
                try:
                    typed_edit(location,value);expected_rejection(lambda:scope(base),diagnostic)
                finally:state_path.write_bytes(saved)
                with contextlib.redirect_stdout(io.StringIO()):scope(base)
                print('PASS scope-controls116 typed clean/reject/restored '+name)
            probes=[('active117','.agent/run_state.json',lambda:field('.agent/run_state.json',None,'active_contract_id','117'),'current_feature/active_contract_id116'),
                    ('premature-run-complete','.agent/run_state.json',lambda:field('.agent/run_state.json',None,'status','complete'),'run remains017'),
                    ('old-proof-byte','.agent/evidence/115/api-interface.json',lambda:(ROOT/'.agent/evidence/115/api-interface.json').write_bytes(safe('.agent/evidence/115/api-interface.json').read_bytes()+b'\n'),'protected immutable bytes'),
                    ('old-proof-mode','.agent/evidence/115/api-interface.json',lambda:(ROOT/'.agent/evidence/115/api-interface.json').chmod(0o755),'protected executable mode'),
                    ('old-debt','docs/planning/DEBT.md',lambda:(ROOT/'docs/planning/DEBT.md').write_bytes(safe('docs/planning/DEBT.md').read_bytes()+b'\n'),'protected immutable bytes'),
                    ('closed015-budget','.agent/run_state.json',lambda:field('.agent/run_state.json','phase_015_scope_budget_final','total_lines_changed',0),'all unowned state'),
                    ('history-prefix','.agent/run_state.json',lambda:field('.agent/run_state.json',None,'history',[]),'exact prior history prefix'),
                    ('measured115-budget','.agent/run_state.json',lambda:field('.agent/run_state.json','scope_budget','per_feature',[]),'immutable115 measured entry/prefix')]
            for name,path,mutation,diagnostic in probes:
                target=ROOT/path;data=target.read_bytes();mode=target.stat().st_mode
                try:
                    mutation();expected_rejection(lambda:scope(base),diagnostic);print('PASS scope-controls116 targeted reject '+name)
                finally:target.write_bytes(data);target.chmod(mode)
            # Unknown ignored files and symlinks are independently checked.
            target=ROOT/'stray116.txt';target.write_text('scratch stray\n')
            try:expected_rejection(lambda:scope(base),'unknown scope path')
            finally:target.unlink()
            print('PASS scope-controls116 unknown path rejection')
            # The canonical reviewed bundle is a separate fixture-shaped gate here.
            bundle=current(BUNDLE);reviewer=bundle['roles']['acceptance_reviewer']
            write(REVIEW,{'review':'validator-test-bundle-review','feature':'116','actor':reviewer['agent_id'],
                          'reviewer_session_id':reviewer['session_id'],'seal_sha256':bundle['seal_sha256'],
                          'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],
                          'final_verdict':{'approved':True,'summary':'PRIVATE MOCK seal-review fixture only.'}})
            mock_delivered()
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            print('PASS scope-controls116 PRIVATE MOCK delivered/in-progress fixture; no product acceptance')
            mock_complete()
            expected_rejection(lambda:scope(base),'mock receipts confined')
            _CONTROL_FIXTURE=ROOT.resolve()
            with contextlib.redirect_stdout(io.StringIO()):_scope(base)
            print('PASS scope-controls116 PRIVATE MOCK actual Git SourceC/postcapture canonical receipt shape')
            postcapture_types=[
                ('postcapture-old-budget-prefix','.agent/run_state.json',['scope_budget','per_feature',0,'actual'],1863.0,'immutable115 measured entry/prefix exact types'),
                ('postcapture-new-estimate','.agent/run_state.json',['scope_budget','per_feature',1,'estimated'],1400.0,'canonical counted116 budget schema'),
                ('postcapture-new-actual','.agent/run_state.json',['scope_budget','per_feature',1,'actual'],100.0,'canonical counted116 budget schema'),
                ('postcapture-total','.agent/run_state.json',['scope_budget','total_lines_changed'],1963.0,'actual017 typed integer sum'),
                ('capture-count-float',CAPTURE,['checks_captured'],12.0,'distinct Root capture'),
                ('capture-count-bool',CAPTURE,['checks_captured'],True,'distinct Root capture'),
                ('qa-count-float',QA,['checks_run'],12.0,'all twelve exact checks passed')]
            for name,path,location,value,diagnostic in postcapture_types:
                with contextlib.redirect_stdout(io.StringIO()):_scope(base)
                target=ROOT/path;saved=target.read_bytes();obj=current(path);container=obj
                for component in location[:-1]:container=container[component]
                container[location[-1]]=value;write(path,obj)
                try:expected_rejection(lambda:_scope(base),diagnostic)
                finally:target.write_bytes(saved)
                with contextlib.redirect_stdout(io.StringIO()):_scope(base)
                print('PASS scope-controls116 PRIVATE MOCK typed clean/reject/restored '+name)
            target=ROOT/CAPTURE;data=target.read_bytes();target.unlink()
            expected_rejection(lambda:_scope(base),'required regular file exists');target.write_bytes(data)
            candidate=current(CANDIDATE);candidate['source_sha256'][CORE[0]]='0'*64;write(CANDIDATE,candidate)
            expected_rejection(lambda:_scope(base),'current SourceC digest')
            print('PASS scope-controls116 missing capture/wrong SourceC digest fail closed')
        finally:ROOT=original_root;_CONTROL_FIXTURE=None
