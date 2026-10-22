"""Reviewed feature-115 repository scope/transition checks; no product acceptance authority."""
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

BASE = '9ebfd03883486a205ac8c3a211f0cac0af5fddba'
APPROVED = '7032c0a70ef6d1930aec78715dbef0d248d7b764'
ROOT = Path(__file__).resolve().parents[3]
_CONTROL_FIXTURE = None

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def require(ok, message):
    if not ok: raise AssertionError('POLICY_ASSERTION: '+message)

def sha(data): return hashlib.sha256(data).hexdigest()

def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE).decode().strip()

def read_at(revision, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + path], stderr=subprocess.PIPE)


def parsed_at(revision, path):
    return json.loads(read_at(revision, path))


def same(a, b, message):
    require(canonical(a) == canonical(b), message)


def _scope(base):
    require(base == BASE, 'scope requires approved immutable base')
    contract = json.loads((ROOT / '.agent/contracts/115.json').read_text())
    approved = parsed_at(APPROVED, '.agent/contracts/115.json')
    require(contract['status'] in ('approved', 'complete'), 'contract approved/complete only')
    same(contract['approvals'], approved['approvals'], 'actual dual approvals remain exact')
    before_contract = copy.deepcopy(approved); after_contract = copy.deepcopy(contract)
    for value in (before_contract, after_contract):
        value.pop('status', None); value.pop('approvals', None)
    same(before_contract, after_contract, 'approved contract obligations unchanged')
    allowed = {x['path'] for family in ('files_create', 'files_modify') for x in approved['scope'][family] if not x['path'].endswith('/**')}
    changed = set(subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--name-only', '-z', base], stderr=subprocess.PIPE).decode().split('\0')) - {''}
    unknown = set(subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--others', '-z'], stderr=subprocess.PIPE).decode().split('\0')) - {''}
    # Git ignores no unknown paths here: ignored artifacts also receive scope scrutiny.
    changed |= unknown
    for path in changed:
        require(path in allowed or path.startswith(('.agent/evidence/115/', '.agent/evidence/phase017-activation/')), 'unknown scope path ' + path)
    entries = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-rz', APPROVED]).split(b'\0')
    for entry in entries:
        if not entry: continue
        metadata, name = entry.split(b'\t', 1); mode, kind, oid = metadata.decode().split(); path = name.decode()

        if path.startswith(('.agent/evidence/', '.nizam/')) or path.startswith(('.agent/qa/', '.agent/validator/')):
            for part in [(ROOT / path), *(ROOT / path).parents]:
                if part == ROOT: break
                require(not part.is_symlink(), 'protected symlink component ' + path)
            require((ROOT / path).is_file() and not (ROOT / path).is_symlink(), 'protected file type ' + path)
            data = (ROOT / path).read_bytes()
            require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == oid, 'protected immutable bytes ' + path)
            require(mode in ('100644', '100755') and bool((ROOT / path).stat().st_mode & 0o111) == (mode == '100755'), 'protected executable mode ' + path)
    for path in changed:
        target = ROOT / path
        for part in [target, *target.parents]:
            if part == ROOT: break
            require(not part.is_symlink(), 'scope path has symlink component ' + path)
        if target.exists(): require(target.is_file(), 'scope path regular file ' + path)
    # All nonauthorized files are byte-exact by the path delta guard above.
    index = json.loads((ROOT / 'NIZAM.json').read_text()); oldindex = parsed_at(base, 'NIZAM.json')
    for item in index['modules']:
        if item['path'] == 'tools':
            for addition in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py'):
                if addition in item['key_documents']: item['key_documents'].remove(addition)
    same(index, oldindex, 'index only appends two tool documents')
    before = parsed_at(base, '.agent/run_state.json'); after = json.loads((ROOT / '.agent/run_state.json').read_text())
    frozen_state = parsed_at(APPROVED, '.agent/run_state.json')
    require(canonical(after['history'][:len(frozen_state['history'])]) == canonical(frozen_state['history']), 'prior history exact author-base prefix')
    same(after['phase_015_scope_budget_final'], before['scope_budget'], 'phase015 full final budget preserved')
    completed = after.get('completed_contract_ids', [])
    old_completed = before.get('completed_contract_ids', [])
    require(completed == old_completed or completed == old_completed + ['115'], 'completed contracts exact old prefix plus optional115')
    mutable = {'completed_contract_ids', 'current_phase', 'current_feature', 'status', 'updated_at', 'last_action', 'active_contract_id', 'pending_operator_gate', 'history', 'scope_budget', 'circuit_breaker', 'phase_015_scope_budget_final'}
    same({k:v for k,v in after.items() if k not in mutable}, {k:v for k,v in before.items() if k not in mutable}, 'all unowned coordination fields')
    require(after['current_phase'] == '017-workflow-assurance-foundation', 'only authorized017 progression')
    budget = after['scope_budget']; require(budget['original_estimate_lines'] == 5400 and budget['ceiling_130pct'] == 7020, 'authorized017 allowance unchanged')
    frozen_budget = parsed_at(APPROVED, '.agent/run_state.json')['scope_budget']
    measured = {'total_lines_changed', 'evidence_lines_total', 'excluded_lines_total', 'per_feature', 'last_measured_at', 'historical_inflight_measurements'}
    same({k:v for k,v in budget.items() if k not in measured}, {k:v for k,v in frozen_budget.items() if k not in measured}, 'budget immutable categories/authority/rule')
    require(all(str(x['id']) == '115' for x in budget['per_feature']), 'only115 budget measured')
    for key, value in before['circuit_breaker'].items(): same(after['circuit_breaker'][key], value, 'old counter ' + key)
    for key in set(after['circuit_breaker']) - set(before['circuit_breaker']):
        require(key.startswith(('115-', 'phase017-')) and after['circuit_breaker'][key]['limit'] == 3 and 0 <= after['circuit_breaker'][key]['attempts'] <= 3, 'bounded new counter ' + key)
    for key, value in frozen_state['circuit_breaker'].items():
        if key.startswith('115-recovery-1-'):
            require(after['circuit_breaker'][key]['attempts'] >= value['attempts'], 'no reset of recovery counter ' + key)
            same({k:v for k,v in after['circuit_breaker'][key].items() if k != 'attempts'}, {k:v for k,v in value.items() if k != 'attempts'}, 'recovery counter metadata preserved '+key)
        else: same(after['circuit_breaker'][key],value,'historical counter exact '+key)
    features = json.loads((ROOT / '.agent/feature_list_017.json').read_text()); oldfeatures = parsed_at(base, '.agent/feature_list_017.json')
    for key in set(features) | set(oldfeatures):
        if key not in ('features', 'spec_version', 'phase_status'): same(features.get(key), oldfeatures.get(key), 'phase017 list ' + key)
    delivered = (ROOT / 'tools/workflow_assurance.py').exists()
    expected_version = '0.2.0' if delivered else '0.1.0'
    spec = (ROOT / '.agent/product_spec_017.md').read_text()
    require(re.search(r'^version: ' + re.escape(expected_version) + r'$', spec, re.M) is not None, 'spec version matches delivered stage')
    require(features['spec_version'] == expected_version and features['phase_status'] == 'in_progress', 'stage-bound list version/status')
    if completed != old_completed:
        require(features['features'][0]['status'] == 'complete' and features['features'][0]['passes'] is True, 'completion append requires completed115')
    obligations = read_at(base, '.agent/product_spec_017.md').decode()
    for heading, end in [('## Architecture and external prerequisites', '## Future acceptance'), ('## Future acceptance and independent ownership', '## Full counted')]:
        require(heading in spec and end in spec and heading in obligations and end in obligations, 'nonempty spec obligation anchors')
        require(obligations[obligations.index(heading):obligations.index(end)] == spec[spec.index(heading):spec.index(end)], 'spec obligation block unchanged ' + heading)
    table = obligations[obligations.index('| ID |'):obligations.index('Proposed 130% ceiling:')]
    require(table in spec, 'all proposed feature budgets preserved')
    require(len(features['features']) == len(oldfeatures['features']), 'no added feature')
    for actual, original in zip(features['features'], oldfeatures['features']):
        if original['id'] != '115': same(actual, original, 'uncontracted feature ' + original['id'])
        else:
            metadata = {'status', 'passes', 'contract', 'qa', 'evidence', 'completed_at', 'contract_ref', 'qa_ref', 'evidence_ref'}
            same({k:v for k,v in actual.items() if k not in metadata}, {k:v for k,v in original.items() if k not in metadata}, '115 obligations/estimate frozen')
    manifest = json.loads((ROOT / 'docs/planning/manifest.json').read_text()); oldmanifest = parsed_at(base, 'docs/planning/manifest.json')
    require(manifest['current_phase'] == '017-workflow-assurance-foundation', 'only017 current manifest')
    for actual, original in zip(manifest['phases'], oldmanifest['phases']):
        if original['id'] != '017-workflow-assurance-foundation': same(actual, original, 'other manifest row')
        else:
            require(actual['status'] == 'in_progress' and actual['activation_state'] == 'active', '017 manifest stays active/in_progress')
            fields = {'activation_state', 'status', 'note', 'notes', 'updated_at'}
            same({k:v for k,v in actual.items() if k not in fields}, {k:v for k,v in original.items() if k not in fields}, '017 manifest immutable fields')
    require(len(manifest['phases']) == len(oldmanifest['phases']), 'manifest row count')
    for key in set(manifest) | set(oldmanifest):
        if key not in ('phases', 'current_phase', 'updated_at'): same(manifest.get(key), oldmanifest.get(key), 'manifest root ' + key)
    dag = json.loads((ROOT / 'docs/planning/backlog_dag.json').read_text()); anchor = parsed_at(APPROVED, 'docs/planning/backlog_dag.json')
    for key in set(dag) | set(anchor):
        if key not in ('generated_at', 'activated_phase', 'phase017_execution', 'packets'): same(dag.get(key), anchor.get(key), 'DAG preserved ' + key)
    require(dag['activated_phase'] == '017-workflow-assurance-foundation', 'DAG activation stays017')
    execution = dag['phase017_execution']; old_execution = anchor['phase017_execution']
    progress_fields = {'status', 'feature', 'feature_status', 'qa', 'evidence', 'completed_at'}
    same({k:v for k,v in execution.items() if k not in progress_fields}, {k:v for k,v in old_execution.items() if k not in progress_fields}, 'DAG execution identity/lane fixed')
    require(execution['status'] == 'in_progress' and execution['feature'] in ('115', None), 'DAG only115 progress')
    require(len(dag['packets']) == len(anchor['packets']), 'DAG packet count')
    for actual, original in zip(dag['packets'], anchor['packets']):
        if original.get('id') != 'A09': same(actual, original, 'other DAG packet')
        else:
            fields = {'status', 'prerequisites_satisfied', 'completion_evidence', 'evidence', 'qa', 'progress', 'closure', 'completed_at', 'prerequisites'}
            same({k:v for k,v in actual.items() if k not in fields}, {k:v for k,v in original.items() if k not in fields}, 'A09 adopted edges/obligations')
    import yaml
    import jsonschema
    phase_object = yaml.safe_load((ROOT / 'docs/planning/phase_017.yaml').read_text())
    jsonschema.validate(phase_object, json.loads((ROOT / '.nizam/schema/phase.schema.json').read_text()))
    require(phase_object['status'] == 'in_progress' and phase_object['id'] == '017-workflow-assurance-foundation', '115 does not close/redirect phase')
    old_phase = yaml.safe_load(read_at(APPROVED, 'docs/planning/phase_017.yaml'))
    same(phase_object['steps'][1:], old_phase['steps'][1:], '116-118 steps exact')
    require(phase_object['steps'][0]['id'] == '115' and phase_object['steps'][0]['description'] == old_phase['steps'][0]['description'] and phase_object['steps'][0]['status'] in ('IN_PROGRESS', 'COMPLETED'), 'only115 step progress')
    phase_text = (ROOT / 'docs/planning/phase_017.yaml').read_text()
    phase_anchor = read_at(APPROVED, 'docs/planning/phase_017.yaml').decode()
    require(phase_anchor[phase_anchor.index("- id: '116'"):] == phase_text[phase_text.index("- id: '116'"):], 'uncontracted phase steps exact')
    # Doc edits remain bounded by independent ModeB review; immutable historical suffix is mechanical.
    for path, heading in [('docs/planning/HANDOVER.md', '## Historical handover snapshot')]:
        old = read_at(base, path).decode(); actual = (ROOT / path).read_text()
        oldbody = old[old.find('\n# '):]
        require('\n' + heading in oldbody, 'nonempty historical anchor ' + path)
        suffix = oldbody[oldbody.index('\n' + heading):]
        require(len(suffix) > 1000, 'substantive historical suffix ' + path)
        require(suffix in actual, 'historical document body preserved ' + path)
    doc_versions = {'tools/README.md': '0.21.0', 'docs/planning/operator_gates.md': '0.37.0',
                    'docs/planning/ROADMAP.md': '0.62.0', 'docs/planning/HANDOVER.md': '1.0.10',
                    '.agent/product_spec_017.md': '0.2.0'}
    for path, version in doc_versions.items():
        original_text = read_at(base, path).decode(); current_text = (ROOT / path).read_text()
        original_parts = original_text.split('---', 2); current_parts = current_text.split('---', 2)
        require(len(original_parts) == len(current_parts) == 3, 'real document frontmatter ' + path)
        old_meta = yaml.safe_load(original_parts[1]); new_meta = yaml.safe_load(current_parts[1])
        if delivered:
            require(str(new_meta['version']) == version and len(new_meta['change_log']) == len(old_meta['change_log']) + 1, 'one authorized version/log bump ' + path)
            same(new_meta['change_log'][1:], old_meta['change_log'], 'old document change history ' + path)
        else:
            same(new_meta, old_meta, 'pre-source doc metadata unchanged ' + path)
        fields = {'version', 'change_log'} | ({'status', 'description'} if path == '.agent/product_spec_017.md' else set())
        same({k:v for k,v in new_meta.items() if k not in fields}, {k:v for k,v in old_meta.items() if k not in fields}, 'unowned doc metadata ' + path)
        if path == '.agent/product_spec_017.md':
            require(new_meta['status'] == ('active' if delivered else 'draft'), 'stage-bound spec status')
            continue
        body = original_parts[2]
        if path == 'docs/planning/ROADMAP.md':
            body = re.sub(r'^## Current Position[^\n]*\n', '', body, flags=re.M)
            start = body.index('- **Phase015 normative scope is complete.**')
            finish = body.index('- **Local self-governance is commissioned.**', start)
            body = body[:start] + body[finish:]
        elif path == 'docs/planning/HANDOVER.md':
            body = re.sub(r'^## Current status[^\n]*\n', '', body, flags=re.M)
        remaining = iter(current_parts[2].splitlines())
        for line in body.splitlines():
            require(any(candidate == line for candidate in remaining), 'old document body line preserved ' + path + ': ' + line[:60])
    original_changelog = read_at(base, 'CHANGELOG.md').decode()
    current_changelog = (ROOT / 'CHANGELOG.md').read_text()
    released = original_changelog[original_changelog.index('## [1.5.0]'):]
    require(released in current_changelog, 'released change notes exact')
    remaining = iter(current_changelog.splitlines())
    for line in original_changelog.splitlines():
        require(any(candidate == line for candidate in remaining), 'existing change note preserved')
    workflow = (ROOT / '.github/workflows/compliance.yml').read_text(); old = read_at(base, '.github/workflows/compliance.yml').decode()
    command = '      - run: PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py\n'
    require(workflow.count(command) == (1 if delivered else 0), 'one permanent exact workflow command after source delivery')
    if delivered:
        job = workflow[workflow.index('  fixtures_self_test:'):workflow.index('  convergent_review:')]
        require(command in job, 'test remains inside existing fixtures job')
    require(workflow.replace(command, '') == old, 'workflow one additive test command only')
    complete = lifecycle(after, features, phase_object, contract)
    debt_guard(complete)
    print('PASS scope: canonical115 tuple, actual delta, immutable proof and prior history')



CORE = ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py',
        '.agent/evidence/115/recovery-scope-guard.py', '.agent/evidence/115/api-interface.json')
CANDIDATE = '.agent/evidence/115/source-candidate.json'
MODE_B = '.agent/validator/115-mode-b.json'
QA = '.agent/qa/115.json'
CAPTURE = '.agent/evidence/115/evidence-capture.json'


def current_json(path):
    require(type(path) is str and path.startswith(('.agent/evidence/115/', '.agent/qa/', '.agent/validator/')), 'receipt path in approved local scope')
    target = ROOT/path
    require(target.is_file() and not target.is_symlink(), 'required receipt exists: '+path)
    for part in target.parents:
        if part == ROOT: break
        require(not part.is_symlink(), 'receipt parent is not symlink')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate receipt key')
            result[key]=value
        return result
    value=json.loads(target.read_text(), object_pairs_hook=pairs,
                     parse_constant=lambda value: require(False,'nonfinite receipt value'))
    require(type(value) is dict, 'receipt object root')
    return value


def gate_pass(value):
    require(value.get('final_verdict',{}).get('approved') is True, 'receipt gate approved boolean')
    for name in ('issues','missing_acceptance_coverage','unsupported_claims'):
        require(type(value.get(name)) is list and value[name] == [], 'receipt blockers empty '+name)


def completed_receipts(contract):
    candidate=current_json(CANDIDATE); mode_b=current_json(MODE_B); qa=current_json(QA); capture=current_json(CAPTURE)
    is_mock=_CONTROL_FIXTURE is not None and ROOT.resolve() == _CONTROL_FIXTURE
    for value in (candidate,mode_b,qa,capture):
        require(value.get('mock_fixture',False) is is_mock, 'mock receipts confined to private control scratch')
    revision=candidate.get('revision')
    require(type(revision) is str and re.fullmatch('[0-9a-f]{40}', revision) is not None, 'immutable assessed source revision')
    require(git(ROOT,'rev-parse',revision+'^{commit}') == revision, 'candidate actual Git commit')
    require(candidate.get('tree') == git(ROOT,'rev-parse',revision+'^{tree}'), 'candidate actual Git tree')
    inputs=candidate.get('source_sha256')
    require(type(inputs) is dict and set(inputs) == set(CORE), 'noncircular assessed product/test/helper/API inputs')
    for path,digest in inputs.items():
        require(digest == sha((ROOT/path).read_bytes()) == sha(read_at(revision,path)), 'captured assessed bytes unchanged '+path)
        mode=git(ROOT,'ls-tree',revision,path).split()[0]
        require(mode in ('100644','100755') and bool((ROOT/path).stat().st_mode & 0o111) == (mode == '100755'), 'captured assessed executable mode unchanged '+path)
    for record in (mode_b,qa,capture):
        require(record.get('revision') == revision and record.get('source_sha256') == inputs, 'same assessed source bound to all closure receipts')
    jsonschema.validate(mode_b,json.loads((ROOT/'.nizam/schema/contract_review.schema.json').read_text()))
    gate_pass(mode_b); gate_pass(qa)
    require(mode_b.get('actor') not in (None,'/root/wa_test_author','/root/wa_generator'), 'independent ModeB actor')
    require(qa.get('actor') not in (None,'/root/wa_test_author','/root/wa_generator'), 'fresh independent QA actor')
    jsonschema.validate(qa,json.loads((ROOT/'.nizam/schema/qa_verdict.schema.json').read_text()))
    count=len(contract['verification'])
    require(qa.get('qa_pass') is True and type(qa.get('checks_run')) is int and qa['checks_run'] == count and qa.get('checks_passed') == count, 'all contracted checks actually passed')
    require(qa.get('required_fixes') == [] and qa.get('adversarial',{}).get('performed') is True, 'fresh QA and own spot complete')
    evidence=qa['evidence_files'];require(type(evidence) is list and len(evidence) >= count, 'QA external command evidence list')
    texts=[]
    for path in evidence:
        require(type(path) is str and path.startswith('.agent/evidence/115/'), 'QA proof path scope')
        target=ROOT/path;require(target.is_file() and not target.is_symlink(), 'QA external proof exists')
        text=target.read_text();require(bool(text.strip()), 'QA raw proof nonempty');texts.append(text)
    for item in contract['verification']:
        require(any(re.findall(r'^COMMAND: (.*)$',text,re.M) == [item['command']] and re.findall(r'^EXIT: (-?[0-9]+)$',text,re.M) == ['0'] and re.findall(r'^REVISION: (.*)$',text,re.M) == [revision] for text in texts), 'actual unique command/zero exit/revision captured '+item['acceptance_test'])
    spot=qa['adversarial'].get('evidence');require(spot in evidence and (ROOT/spot).is_file(), 'own spot external proof referenced')
    require(capture.get('passed') is True and capture.get('qa_ref') == QA and capture.get('mode_b_ref') == MODE_B, 'distinct successful capture names actual QA/ModeB')
    require(capture.get('qa_sha256') == sha((ROOT/QA).read_bytes()) and capture.get('mode_b_sha256') == sha((ROOT/MODE_B).read_bytes()), 'capture freezes actual gate/QA bytes')


def lifecycle(state,features,phase,contract):
    feature=features['features'][0]; step=phase['steps'][0]
    require(state['status'] == 'in_progress', 'run.status must match canonical017 in_progress')
    require(state.get('pending_operator_gate') is None, 'no unresolved operator gate in authorized115 execution')
    prior=parsed_at(APPROVED,'.agent/run_state.json')['completed_contract_ids']
    complete=step['status'] == 'COMPLETED'
    if not complete:
        require(step['status'] == 'IN_PROGRESS' and feature['status'] == 'in_progress' and feature['passes'] is False, 'canonical115 in-progress tuple')
        require(state['current_feature'] == '115' and state['active_contract_id'] == '115', 'active_contract_id/current_feature115 match canonical')
        require(state['completed_contract_ids'] == prior and contract['status'] == 'approved', 'no premature contract/list completion')
    else:
        require(feature['status'] == 'complete' and feature['passes'] is True and contract['status'] == 'complete', 'canonical115 captured-complete tuple')
        require(state['current_feature'] is None and state['active_contract_id'] is None, 'captured115 clears both active fields')
        require(state['completed_contract_ids'] == prior+['115'], 'captured115 exactly appended once')
        require(feature.get('contract_ref') == '.agent/contracts/115.json' and feature.get('qa_ref') == QA and feature.get('evidence_ref') == CAPTURE and step.get('evidence') == CAPTURE, 'canonical completion refers to exact real115 receipts')
        completed_receipts(contract)
    return complete


def debt_guard(complete):
    old=read_at(APPROVED,'docs/planning/DEBT.md').decode();current=(ROOT/'docs/planning/DEBT.md').read_text()
    oldparts=old.split('---',2); parts=current.split('---',2)
    oldmeta=yaml.safe_load(oldparts[1]);meta=yaml.safe_load(parts[1])
    if not complete:
        require(current == old, 'NDEBT052 stays authorized/Open before capture');return
    require(str(meta['version']) == '0.71.0' and len(meta['change_log']) == len(oldmeta['change_log'])+1, 'capture-only debt closure version/log')
    same(meta['change_log'][1:],oldmeta['change_log'],'old debt change history immutable')
    same({k:v for k,v in meta.items() if k not in ('version','change_log')}, {k:v for k,v in oldmeta.items() if k not in ('version','change_log')}, 'unowned debt frontmatter')
    def rows(body):
        result={}
        for line in body.splitlines():
            match=re.match(r'^\|\s*(NDEBT-[0-9]+)\s*\|',line)
            if match:
                require(match[1] not in result,'unique debt row');result[match[1]]=line
        return result
    before=rows(oldparts[2]); after=rows(parts[2]);require(set(before)==set(after),'no unrelated debt added/removed')
    for key in before:
        if key != 'NDEBT-052':require(before[key] == after[key],'other debt exact '+key)
    require(before['NDEBT-052'].split('|')[:5] == after['NDEBT-052'].split('|')[:5], 'original052 halt description preserved')
    require('RESOLVED' in after['NDEBT-052'] and CAPTURE in after['NDEBT-052'], '052 resolution cites actual capture')
    require(after['NDEBT-052'] in current[current.index('## Resolved'):], '052 moved to Resolved only')


def scope_controls(base):
    """Real scratch transitions; mock receipts are explicit parser fixtures only."""
    global ROOT, _CONTROL_FIXTURE
    require(base == BASE,'approved controls base')
    original_root=ROOT
    with tempfile.TemporaryDirectory(prefix='nizam-115-recovery-scope-') as temp:
        scratch=Path(temp)/'repo'
        subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(scratch)],check=True)
        subprocess.run(['git','-C',str(scratch),'checkout','-q',APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for path in ('tools/test_workflow_assurance.py','.agent/evidence/115/recovery-scope-guard.py'):
            (scratch/path).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,scratch/path)
        ROOT=scratch
        try:
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            require(parsed_at(APPROVED,'.agent/run_state.json')['circuit_breaker']['115-tests']['attempts'] == 3 and parsed_at(APPROVED,'.agent/run_state.json')['circuit_breaker']['115-tests']['limit'] == 3, 'historical exhausted3/3 counter preserved')
            halt=json.loads((ROOT/'.agent/evidence/115/circuit-breaker-halt.json').read_text());require(halt['exhausted_counter']['attempts']==3 and halt['product_source_started'] is False, 'historical halt preserved, never Source permission')
            print('PASS scope-controls valid pre-source IN_PROGRESS017/115 and preserved historical halt3/3')
            probes=[('known-contract116-substitution','.agent/run_state.json',lambda p:change_json(p,None,'active_contract_id','116'),'active_contract_id/current_feature115'),
                    ('known-premature-run-complete','.agent/run_state.json',lambda p:change_json(p,None,'status','complete'),'run.status must match canonical017'),
                    ('old-proof-byte','.agent/evidence/115/api-interface.json',lambda p:p.write_bytes(p.read_bytes()+b'\n'),'protected immutable bytes'),
                    ('old-proof-mode','.agent/evidence/115/api-interface.json',lambda p:p.chmod(0o755),'protected executable mode'),
                    ('archived015-budget','.agent/run_state.json',lambda p:change_json(p,'phase_015_scope_budget_final','total_lines_changed',0),'phase015 full final budget'),
                    ('phase017-terminal','docs/planning/manifest.json',manifest_complete,'017 manifest stays active/in_progress'),
                    ('foreign-current-feature','.agent/run_state.json',lambda p:change_json(p,None,'current_feature','116'),'active_contract_id/current_feature115')]
            for name,path,mutate,expected in probes:
                target=ROOT/path; data=target.read_bytes();mode=target.stat().st_mode
                try:
                    mutate(target);expected_rejection(lambda:scope(base),expected)
                    print('PASS scope-controls targeted reject '+name)
                finally:target.write_bytes(data);target.chmod(mode)
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            print('PASS scope-controls restored pre-source after seven exact rejects')
            mock_delivered()
            with contextlib.redirect_stdout(io.StringIO()):scope(base)
            print('PASS scope-controls PRIVATE MOCK delivered/in-progress shape; no product acceptance claimed')
            mock_completed()
            expected_rejection(lambda:scope(base),'mock receipts confined to private control scratch')
            _CONTROL_FIXTURE=ROOT.resolve()
            with contextlib.redirect_stdout(io.StringIO()):_scope(base)
            print('PASS scope-controls PRIVATE MOCK after-capture canonical tuple with actual fixture Git revision/digests; no actual115 QA claimed')
            (ROOT/CAPTURE).unlink()
            expected_rejection(lambda:_scope(base),'required receipt exists')
            print('PASS scope-controls missing capture blocks canonical completion')
        finally:ROOT=original_root;_CONTROL_FIXTURE=None


def expected_rejection(operation,diagnostic):
    try:operation()
    except AssertionError as exc:
        require('POLICY_ASSERTION:' in str(exc) and diagnostic in str(exc),'intended targeted assertion, not setup failure: '+str(exc));return
    require(False,'control false-pass '+diagnostic)


def change_json(path,parent,key,value):
    obj=json.loads(path.read_text());target=obj[parent] if parent else obj;target[key]=value;path.write_text(json.dumps(obj))


def manifest_complete(path):
    obj=json.loads(path.read_text())
    for row in obj['phases']:
        if row['id']=='017-workflow-assurance-foundation':row['status']='complete'
    path.write_text(json.dumps(obj))


def write_json(path,value):
    target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,indent=2)+'\n')


def mock_delivered():
    (ROOT/'tools/workflow_assurance.py').write_text('# PRIVATE MOCK structural fixture; never actual product or acceptance.\n')
    versions={'tools/README.md':'0.21.0','docs/planning/operator_gates.md':'0.37.0','docs/planning/ROADMAP.md':'0.62.0','docs/planning/HANDOVER.md':'1.0.10','.agent/product_spec_017.md':'0.2.0'}
    for path,version in versions.items():
        target=ROOT/path;parts=target.read_text().split('---',2);meta=yaml.safe_load(parts[1]);meta['version']=version
        meta['change_log'].insert(0,{'version':version,'date':'2026-10-13','summary':'PRIVATE MOCK document transition fixture; no acceptance claim.'})
        if path=='.agent/product_spec_017.md':meta['status']='active'
        target.write_text('---\n'+yaml.safe_dump(meta,sort_keys=False,allow_unicode=True)+'---'+parts[2])
    change_json(ROOT/'.agent/feature_list_017.json',None,'spec_version','0.2.0')
    workflow=ROOT/'.github/workflows/compliance.yml';text=workflow.read_text();anchor='      - run: bash tools/fixtures_self_test.sh\n'
    require(text.count(anchor)==1,'existing fixtures insertion anchor')
    workflow.write_text(text.replace(anchor,anchor+'      - run: PYTHONDONTWRITECODE=1 python3 tools/test_workflow_assurance.py\n').replace('PYTHONDONTWRITECODE','PYTHONDONTWRITEBYTECODE'))


def mock_completed():
    git(ROOT,'config','user.email','mock-control@example.invalid');git(ROOT,'config','user.name','Explicit Mock Control')
    git(ROOT,'add',*CORE);git(ROOT,'commit','-qm','PRIVATE MOCK assessed fixture source, not feature115 product')
    revision=git(ROOT,'rev-parse','HEAD');inputs={path:sha((ROOT/path).read_bytes()) for path in CORE}
    binding={'mock_fixture':True,'revision':revision,'source_sha256':inputs}
    write_json(CANDIDATE,{**binding,'tree':git(ROOT,'rev-parse',revision+'^{tree}')})
    gate={**binding,'review':'validator-mode-b','feature':'115','actor':'mock-independent-validator','issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],'final_verdict':{'approved':True,'summary':'PRIVATE MOCK shape only.'}}
    write_json(MODE_B,gate)
    contract=json.loads((ROOT/'.agent/contracts/115.json').read_text());paths=[]
    for index,item in enumerate(contract['verification']):
        path=f'.agent/evidence/115/private-mock-check-{index}.txt';(ROOT/path).write_text('PRIVATE MOCK FIXTURE ONLY; never actual QA\nCOMMAND: '+item['command']+'\nREVISION: '+revision+'\nSTDOUT: explicitly mock fixture\nEXIT: 0\n');paths.append(path)
    spot='.agent/evidence/115/private-mock-spot.txt';(ROOT/spot).write_text('PRIVATE MOCK SPOT ONLY\nCOMMAND: mock private spot\nREVISION: '+revision+'\nEXIT: 0\n');paths.append(spot)
    qa={**gate,'feature_id':'115','actor':'mock-fresh-evaluator','qa_pass':True,'checks_run':len(contract['verification']),'checks_passed':len(contract['verification']),'required_fixes':[],'adversarial':{'performed':True,'evidence':spot},'evidence_files':paths}
    write_json(QA,qa)
    write_json(CAPTURE,{**binding,'passed':True,'qa_ref':QA,'mode_b_ref':MODE_B,'qa_sha256':sha((ROOT/QA).read_bytes()),'mode_b_sha256':sha((ROOT/MODE_B).read_bytes())})
    contract['status']='complete';write_json('.agent/contracts/115.json',contract)
    features=json.loads((ROOT/'.agent/feature_list_017.json').read_text());features['features'][0].update(status='complete',passes=True,contract_ref='.agent/contracts/115.json',qa_ref=QA,evidence_ref=CAPTURE);write_json('.agent/feature_list_017.json',features)
    phase=yaml.safe_load((ROOT/'docs/planning/phase_017.yaml').read_text());phase['steps'][0].update(status='COMPLETED',evidence=CAPTURE);(ROOT/'docs/planning/phase_017.yaml').write_text(yaml.safe_dump(phase,sort_keys=False,allow_unicode=True))
    state=json.loads((ROOT/'.agent/run_state.json').read_text());state.update(current_feature=None,active_contract_id=None);state['completed_contract_ids'].append('115');write_json('.agent/run_state.json',state)
    target=ROOT/'docs/planning/DEBT.md';parts=target.read_text().split('---',2);meta=yaml.safe_load(parts[1]);meta['version']='0.71.0';meta['change_log'].insert(0,{'version':'0.71.0','date':'2026-10-13','summary':'PRIVATE MOCK capture-only052 closure shape.'})
    row=next(line for line in parts[2].splitlines() if line.startswith('| NDEBT-052 |'));cells=row.split('|');cells[-2]=' RESOLVED — PRIVATE MOCK fixture only; '+CAPTURE+'. '
    body=parts[2].replace(row+'\n','');start=body.index('## Resolved');separator=body.index('\n',body.index('|----',start))+1;body=body[:separator]+'|'.join(cells)+'\n'+body[separator:]
    target.write_text('---\n'+yaml.safe_dump(meta,sort_keys=False,allow_unicode=True)+'---'+body)


def scope(base):
    require(_CONTROL_FIXTURE is None,'private mock context unavailable to public scope interface')
    _scope(base)
