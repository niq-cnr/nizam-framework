"""Independent contract audit and PRIVATE abstract lifecycle projection probes.
The private model tests constructibility only, not future receipt verification.
"""
import copy,hashlib,json,stat,subprocess
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
E='.agent/evidence/118/'
def read(p):return json.loads(Path(p).read_bytes())
def git(*a):return subprocess.check_output(['git',*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def typed(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def validate(v,path):Draft202012Validator(read(path)).validate(v)
o=read(E+'recovery1-mode-a-owner.json');assert str(Path.cwd())==o['root'] and o['owner']=='/root/wa_validator118' and git('rev-parse','HEAD').decode().strip()==o['base']
auth=read(E+'recovery-authorization.json');assert auth['authorized'] is True and auth['recovery_epoch']==1
h=read(E+'recovery1-contract-handoff.json');assert h['proposal_revision']=='70e1bab0be7cd90d0db053541c112a34ee6b4f5f'
c=read('.agent/contracts/118.json');a=read(E+'api-interface.json');p=read(E+'producer-interface.json')
for path,key in [('.agent/contracts/118.json','contract_sha256'),(E+'api-interface.json','api_sha256'),(E+'producer-interface.json','producer_sha256')]:
 data=Path(path).read_bytes();assert data==git('show',h['proposal_revision']+':'+path) and sha(data)==h[key]
 mode=git('ls-tree',h['proposal_revision'],'--',path).decode().split()[0];st=Path(path).lstat();assert stat.S_ISREG(st.st_mode) and mode==('100755' if st.st_mode&0o111 else '100644');print('PASS immutable proposal/current bytes/modes',path,sha(data))
validate(c,'.nizam/schema/contract.schema.json')
for k in ['precode_gate_policy','acceptance_successor_policy','recovery_state_policy']:assert c[k]==a[k]==p[k]
assert c['precode_gate_policy']['revision']==3 and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':3,'gate_refs':None}
old=read(E+'pre-recovery1-contract.json');oa=read(E+'pre-recovery1-api-interface.json');op=read(E+'pre-recovery1-producer-interface.json')
for k in ['verification','estimated_lines','budget_categories','phase_budget','execution_order','readiness_boundary','lifecycle_values','dependency_features']:assert c[k]==old[k],k
for k in ['api','current_cases','core_paths','historical_paths','historical_base','candidate','prerequisite_consumer','failure_controls']:assert a[k]==oa[k],k
for k in ['candidate','prerequisite','mode_b','qa','capture','ordering','core_paths','historical_paths']:assert p[k]==op[k],k
assert c['estimated_lines']==650 and len(c['verification'])==3
prov=read(E+'recovery1-contract-predecessors.json')
for path,row in prov['snapshots'].items():assert Path(row['snapshot']).read_bytes()==git('show',row['revision']+':'+path) and sha(Path(row['snapshot']).read_bytes())==row['sha256']
assert sha(Path(E+'recovery-authorization.json').read_bytes())==prov['authorization_sha256']
state=read('.agent/run_state.json');base=json.loads(git('show',h['base_revision']+':.agent/run_state.json'))
for k,v in base['circuit_breaker'].items():assert typed(state['circuit_breaker'][k])==typed(v)
assert typed(state['history'][:len(base['history'])])==typed(base['history'])
assert state['scope_budget']==base['scope_budget'] and state['scope_budget']['total_lines_changed']==4012 and state['scope_budget']['historical_inflight_measurements'][-1]['actual']==559
assert Path('docs/planning/DEBT.md').read_bytes()==git('show',h['base_revision']+':docs/planning/DEBT.md')
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py',E+'foundation-fixtures.py',E+'scope-guard.py']:assert Path(path).read_bytes()==git('show',h['base_revision']+':'+path)
print('PASS proposal schema, shared policy consistency, exact functional obligations, authorization and predecessor hashes; historical budget/counters/fixtures preserved')
# Abstract projections only. A boolean here represents the result of the required
# independent receipt predicate, NOT a public flag, real receipt, or implementation.
snapshot=copy.deepcopy(c);snapshot['status']='approved';snapshot_bytes=(json.dumps(snapshot,indent=2)+'\n').encode();mapped=sha(snapshot_bytes)
def strict(raw):
 def pairs(rows):
  result={}
  for k,v in rows:
   if k in result:raise ValueError('duplicate')
   result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))
def projection(raw,capture_predicate_result,anchor=snapshot_bytes,expected=mapped):
 if sha(anchor)!=expected:raise ValueError('immutable anchor')
 current=strict(raw);approved=strict(anchor)
 if type(current.get('status')) is not str:raise ValueError('status type')
 if current['status']=='approved':
  if raw!=anchor:raise ValueError('approved bytes')
 elif current['status']=='complete':
  if capture_predicate_result is not True:raise ValueError('capture predicate')
  current['status']='approved'
  if typed(current)!=typed(approved):raise ValueError('typed obligation change')
 else:raise ValueError('unknown status')
 return True
complete=copy.deepcopy(snapshot);complete['status']='complete'
raw=lambda v:(json.dumps(v,indent=2)+'\n').encode()
assert projection(snapshot_bytes,False) and projection(raw(complete),True) and sha(raw(complete))!=mapped
cases=[('premature complete',raw(complete),False)]
for label,key,value in [('boolean status','status',True),('null status','status',None),('unknown status','status','implemented'),('estimate changed','estimated_lines',651),('estimate type changed','estimated_lines',650.0),('extra key','extra',True),('recovery policy changed','recovery_state_policy',{}),('approval changed','approvals',{})]:
 bad=copy.deepcopy(complete);bad[key]=value;cases.append((label,raw(bad),True))
cases += [('duplicate JSON',raw(complete).rstrip()[:-1]+b',"status":"complete"}',True),('nonfinite JSON',raw(complete).rstrip()[:-1]+b',"extra":NaN}',True)]
for label,data,captured in cases:
 try:projection(data,captured)
 except ValueError:print('PASS private projection rejects',label)
 else:raise AssertionError(label)
try:projection(raw(complete),True,snapshot_bytes+b'\n')
except ValueError:print('PASS immutable approved anchor hash cannot change')
else:raise AssertionError('anchor change')
print('PASS private constructibility model: approved needs no future receipts; complete changes only status after independent receipt predicate; no product or actual capture claim')
phase=yaml.safe_load(Path('docs/planning/phase_017.yaml').read_text());fl=read('.agent/feature_list_017.json');manifest=read('docs/planning/manifest.json')
for stage,step in [('blocked','BLOCKED'),('in_progress','IN_PROGRESS'),('complete','COMPLETED')]:
 ph=copy.deepcopy(phase);ph['status']=stage;ph['steps'][-1]['status']=step;validate(ph,'.nizam/schema/phase.schema.json')
 f=copy.deepcopy(fl);f['phase_status']=stage;f['features'][-1]['status']=stage;f['features'][-1]['passes']=stage=='complete';validate(f,'.nizam/schema/feature_list.schema.json')
 m=copy.deepcopy(manifest);next(row for row in m['phases'] if row['id']==ph['id'])['status']=stage;validate(m,'.nizam/schema/manifest.schema.json')
 st=copy.deepcopy(state);st['status']=stage;st['active_contract_id']='118' if stage=='in_progress' else None;st['current_feature']=None if stage=='complete' else '118';validate(st,'.nizam/schema/run_state.schema.json');print('PASS in-memory installed lifecycle schemas',stage)
print('PROPOSAL_DIFF_BEGIN');print(git('diff',h['base_revision'],h['proposal_revision'],'--','.agent/contracts/118.json',E+'api-interface.json',E+'producer-interface.json').decode());print('PROPOSAL_DIFF_END')
