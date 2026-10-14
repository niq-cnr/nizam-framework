"""Read-only Mode A readiness audit with explicit artifact-family anchors."""
import hashlib, json, pathlib, stat, subprocess
from jsonschema import Draft202012Validator
r = pathlib.Path.cwd()
def git(*args): return subprocess.check_output(['git', *args])
def load(p): return json.loads((r/p).read_text())
def blob(rev,p): return git('show',rev+':'+p)
def digest(b): return hashlib.sha256(b).hexdigest()
def typed(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def same(x,y): return type(x) is type(y) and typed(x)==typed(y)
o=load('.agent/evidence/117/recovery1-mode-a-attempt3.json')
m=load('.agent/evidence/117/recovery1-mode-a-attempt3-inputs.json')
proposal='f42e1b91d21c99a16d90f1e403f48ec37341b1ac'
assert str(r)==o['root'] and git('rev-parse','HEAD').decode().strip()==o['base']
for p,h in m['paths_sha256'].items():
    q=r/p; assert q.is_file() and not q.is_symlink() and digest(q.read_bytes())==h,p
c=load('.agent/contracts/117.json'); a=load('.agent/evidence/117/api-interface.json')
for p in ['.agent/contracts/117.json','.agent/evidence/117/api-interface.json']:
    assert (r/p).read_bytes()==blob(proposal,p),p
Draft202012Validator(load('.nizam/schema/contract.schema.json')).validate(c)
assert c['status']=='proposed' and same(c['approvals'],{'validator_mode_a':False,'evaluator_contract_review':False,'revisions':2,'gate_refs':None})
assert same(c['gate_reference_policy'],a['gate_references']) and same(c['recovery_alignment'],a['recovery_alignment'])
p=c['gate_reference_policy']; assert type(p['revision']) is int and p['revision']==2
assert p['validator_mode_a']=={'path':'.agent/validator/117-mode-a-recovery1.json','review':'contract-mode-a'}
assert p['evaluator_contract_review']=={'path':'.agent/qa/117-contract-review-recovery1.json','review':'contract-testability'}
print('PASS current contract/API immutable proposal hashes, schema and explicit revision2 producer interface',flush=True)
old=load('.agent/evidence/117/pre-revision-contract-attempt1.json')
oldapi=load('.agent/evidence/117/pre-revision-api-attempt1.json')
assert c['verification']==old['verification'] and len(c['verification'])==12
assert c['entry_authority']==old['entry_authority'] and c['entry_write_grants']==old['entry_write_grants']
assert a['baseline_cases']==oldapi['baseline_cases'] and len(a['baseline_cases'])==4
assert c['estimated_lines']==old['estimated_lines']==1050 and c['budget_categories']==old['budget_categories'] and c['phase_budget']==old['phase_budget']
auth=load(c['recovery_alignment']['authorization_ref'])
assert auth['authorized'] is True and auth['recovery_epoch']=='117-recovery1'
assert digest((r/c['recovery_alignment']['authorization_ref']).read_bytes())==c['recovery_alignment']['authorization_sha256']
pres=c['recovery_alignment']['preservation_revision']
for current,archived in [('.agent/contracts/117.json','.agent/evidence/117/pre-recovery-contract-rev1.json'),('.agent/evidence/117/api-interface.json','.agent/evidence/117/pre-recovery-api-rev1.json')]:
    assert blob(pres,current)==(r/archived).read_bytes(),archived
print('PASS original four semantic obligations/twelve commands/1050 budget and exact pre-recovery archives',flush=True)
changes=git('diff','--name-status',proposal,o['base']).decode().splitlines()
for row in changes:
    status,path=row.split('\t')
    assert (status=='A' and (path.startswith('.agent/evidence/117/') or path=='.agent/qa/117-contract-review-recovery1.json')) or (status=='M' and path=='.agent/run_state.json'),row
assert not git('diff','--name-only','HEAD').strip(), 'unexpected tracked working-tree edits'
state=load('.agent/run_state.json'); previous=json.loads(blob(proposal,'.agent/run_state.json'))
assert state['current_feature']==state['active_contract_id']=='117' and state['status']=='in_progress'
assert state['circuit_breaker']['117-contract-review']=={'attempts':3,'limit':3}
assert state['circuit_breaker']['117-recovery1-mode-a']=={'attempts':2,'limit':3}
assert same(previous['history'],state['history'][:len(previous['history'])])
mutable={'history','last_action','updated_at','circuit_breaker'}
assert set(previous)==set(state)
assert all(same(previous[k],state[k]) for k in previous if k not in mutable)
allowed={'117-contract','117-proposal-coordination','117-recovery1-mode-a','117-recovery1-contract-review','117-recovery1-precode-coordination'}
for key,value in previous['circuit_breaker'].items():
    if key not in allowed: assert same(value,state['circuit_breaker'][key]),key
for key,value in state['circuit_breaker'].items():
    if key in allowed:
        assert type(value['attempts']) is int and type(value['limit']) is int and value['limit']==3 and 0<=value['attempts']<=3,key
        if key in previous['circuit_breaker']: assert value['attempts']>=previous['circuit_breaker'][key]['attempts'],key
    elif key not in previous['circuit_breaker']: raise AssertionError(key)
print('PASS additive-only coordination/evidence changed set, exact typed history prefix and preserved original exhausted counter',flush=True)
rows=git('ls-tree','-r',proposal,'.agent/evidence/','.agent/validator/','.agent/qa/','.nizam/').decode().splitlines()
count=0
for row in rows:
    meta,path=row.split('\t'); mode,kind,obj=meta.split(); q=r/path
    assert kind=='blob' and mode in ('100644','100755'),path
    assert stat.S_ISREG(q.lstat().st_mode) and not q.is_symlink(),path
    assert bool(q.stat().st_mode & stat.S_IXUSR)==(mode=='100755'),path
    assert q.read_bytes()==git('cat-file','blob',obj),path
    count+=1
for attempt in [1,2]:
    archive=r/('.agent/evidence/117/failed-recovery1-mode-a-attempt'+str(attempt))
    for path,proof in json.loads((archive/'preservation.json').read_text())['files'].items():
        q=archive/'reviewer'/path
        assert stat.S_ISREG(q.lstat().st_mode) and not q.is_symlink() and digest(q.read_bytes())==proof['sha256'],path
        assert bool(q.stat().st_mode & stat.S_IXUSR) is proof['executable'],path
print('PASS',count,'proposal-anchored evidence/gate/installed files plus both exact failed-review archives; Git type/executable semantics',flush=True)
authority=c['entry_authority']; pin=authority['installed_pin']
assert git('rev-parse',pin['tag']+'^{commit}').decode().strip()==pin['resolved_sha']
assert blob(authority['authorization_revision'],authority['authorization_path'])==(r/authority['authorization_path']).read_bytes()
for path in ['NIZAM.json','tools/SKILL.md','standard/AGF.md','standard/capability_profiles.md','standard/permission_classes.md']:
    assert blob(pin['resolved_sha'],path)==(r/'.nizam'/path).read_bytes(),path
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
    assert blob(c['scope_base_revision'],path)==(r/path).read_bytes(),path
profiles=(r/'.nizam/standard/capability_profiles.md').read_text()
for role,profile in [('Orchestrator','orchestrator-primary'),('Planner','planner-creative'),('Generator','generator-deterministic'),('Validator','validator-structural'),('Evaluator','evaluator-adversarial')]:
    assert any(('`'+profile+'`') in line and ('| '+role+' |') in line for line in profiles.splitlines()),role
print('PASS real released critical pin/authority/five profile pairs; source/test unchanged; future117 policy not executed',flush=True)
