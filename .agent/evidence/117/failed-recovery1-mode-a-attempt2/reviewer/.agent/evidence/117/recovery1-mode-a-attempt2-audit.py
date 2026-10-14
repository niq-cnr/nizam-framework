"""Read-only pre-code input/interface audit; no future117 policy execution."""
import hashlib, json, pathlib, stat, subprocess
from jsonschema import Draft202012Validator
r = pathlib.Path.cwd()
def read(p): return json.loads((r / p).read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*args): return subprocess.check_output(['git', *args])
def blob(rev, p): return git('show', rev + ':' + p)
owner = read('.agent/evidence/117/recovery1-mode-a-attempt2.json')
inputs = read('.agent/evidence/117/recovery1-mode-a-attempt2-inputs.json')
assert str(r) == owner['root'] and git('rev-parse', 'HEAD').decode().strip() == owner['base']
for p, h in inputs['paths_sha256'].items():
    assert (r / p).is_file() and not (r / p).is_symlink() and sha((r / p).read_bytes()) == h, p
c = read('.agent/contracts/117.json'); a = read('.agent/evidence/117/api-interface.json')
s = read('.agent/run_state.json'); f = read('.agent/feature_list_017.json')
for p in ['.agent/contracts/117.json', '.agent/evidence/117/api-interface.json']:
    assert blob(owner['proposal_revision'], p) == (r / p).read_bytes(), p
Draft202012Validator(read('.nizam/schema/contract.schema.json')).validate(c)
assert c['status'] == 'proposed' and c['approvals'] == {'validator_mode_a': False, 'evaluator_contract_review': False, 'revisions': 2, 'gate_refs': None}
assert type(c['approvals']['revisions']) is int
assert c['gate_reference_policy'] == a['gate_references'] and c['recovery_alignment'] == a['recovery_alignment']
policy = c['gate_reference_policy']; assert type(policy['revision']) is int and policy['revision'] == 2
assert policy['validator_mode_a'] == {'path': '.agent/validator/117-mode-a-recovery1.json', 'review': 'contract-mode-a'}
assert policy['evaluator_contract_review'] == {'path': '.agent/qa/117-contract-review-recovery1.json', 'review': 'contract-testability'}
old = read('.agent/evidence/117/pre-revision-contract-attempt1.json')
old_api = read('.agent/evidence/117/pre-revision-api-attempt1.json')
assert sha((r/'.agent/evidence/117/pre-revision-contract-attempt1.json').read_bytes()) == '5ccf00e7083bff630809a2b3d8fb6e688307e7c4294879d2ba5aaa6fee5c631f'
assert c['verification'] == old['verification'] and len(c['verification']) == 12
assert c['entry_authority'] == old['entry_authority'] and c['entry_write_grants'] == old['entry_write_grants']
assert a['baseline_cases'] == old_api['baseline_cases'] and len(a['baseline_cases']) == 4
assert c['estimated_lines'] == old['estimated_lines'] == 1050 and c['budget_categories'] == old['budget_categories']
assert c['phase_budget'] == old['phase_budget'] and c['phase_budget']['prior_completed_total'] == 3009
auth = read(c['recovery_alignment']['authorization_ref'])
assert auth['authorized'] is True and auth['recovery_epoch'] == '117-recovery1'
assert sha((r/c['recovery_alignment']['authorization_ref']).read_bytes()) == c['recovery_alignment']['authorization_sha256']
assert s['circuit_breaker']['117-contract-review'] == {'attempts': 3, 'limit': 3}
assert s['circuit_breaker']['117-recovery1-mode-a'] == {'attempts': 1, 'limit': 3}
assert s['current_feature'] == s['active_contract_id'] == '117' and s['status'] == 'in_progress'
features = {v['id']: v for v in f['features']}
assert features['115']['passes'] is True and features['116']['passes'] is True and features['117']['passes'] is False and features['118']['status'] == 'pending'
preserved = 0
pres = c['recovery_alignment']['preservation_revision']
for row in git('ls-tree', '-r', pres, '.agent/evidence/', '.agent/validator/', '.agent/qa/').decode().splitlines():
    meta, p = row.split('\t'); mode, kind, obj = meta.split()
    assert kind == 'blob' and mode in ('100644', '100755'), p
    q = r/p; assert q.is_file() and not q.is_symlink() and sha(q.read_bytes()) == sha(git('cat-file','blob',obj)), p
    assert stat.S_ISREG(q.lstat().st_mode) and bool(q.stat().st_mode & stat.S_IXUSR) == (mode == '100755'), p
    preserved += 1
for p in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
    assert blob(c['scope_base_revision'], p) == (r/p).read_bytes(), p
authority = c['entry_authority']; pin = authority['installed_pin']
assert git('rev-parse', pin['tag']+'^{commit}').decode().strip() == pin['resolved_sha']
assert blob(authority['authorization_revision'],authority['authorization_path']) == (r/authority['authorization_path']).read_bytes()
for p in ['NIZAM.json','tools/SKILL.md','standard/AGF.md','standard/capability_profiles.md','standard/permission_classes.md']:
    assert blob(pin['resolved_sha'],p) == (r/'.nizam'/p).read_bytes(), p
archive = r/'.agent/evidence/117/failed-recovery1-mode-a-attempt1'
for p, proof in read(str(archive.relative_to(r))+'/preservation.json')['files'].items():
    q = archive/'reviewer'/p
    assert q.is_file() and not q.is_symlink() and sha(q.read_bytes()) == proof['sha256'], p
    assert bool(q.stat().st_mode & stat.S_IXUSR) is proof['executable'], p
profiles = (r/'.nizam/standard/capability_profiles.md').read_text()
for role, profile in [('Orchestrator','orchestrator-primary'),('Planner','planner-creative'),('Generator','generator-deterministic'),('Validator','validator-structural'),('Evaluator','evaluator-adversarial')]:
    assert any(('`'+profile+'`') in line and ('| '+role+' |') in line for line in profiles.splitlines()), role
print(json.dumps({'proposal_schema':'valid','proposal_revision':owner['proposal_revision'],'gate_policy_matches_api':True,'gate_reference_revision':2,'old_evidence_and_gates_preserved':preserved,'behavioral_cases':list(a['baseline_cases']),'verification_count':len(c['verification']),'estimated_lines':1050,'phase_prior_completed':3009,'phase_original_estimate':5400,'phase_ceiling':7020,'source_and_test_unchanged':True,'future117_policy_exercised':False}, indent=2))
