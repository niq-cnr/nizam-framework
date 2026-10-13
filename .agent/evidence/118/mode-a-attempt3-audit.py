"""Independent revision2 architectural diagnosis; in-memory only."""
import copy,hashlib,json,stat,subprocess
from pathlib import Path
from jsonschema import Draft202012Validator

def read(p):return json.loads(Path(p).read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
owner=read('.agent/evidence/118/mode-a-attempt3.json');rev=git('rev-parse','HEAD').decode().strip()
assert owner['owner']=='/root/wa_validator118' and owner['root']==str(Path.cwd()) and rev==owner['base']=='fc54d5082c5aa5042e42b18719d4eeb4adf9f7ac'
s=read('.agent/run_state.json');assert s['circuit_breaker']['118-mode-a']=={'attempts':2,'limit':3}
c=read('.agent/contracts/118.json');a=read('.agent/evidence/118/api-interface.json');p=read('.agent/evidence/118/producer-interface.json');h=read('.agent/evidence/118/contract-proposal-handoff-attempt3.json');prov=read('.agent/evidence/118/pre-revision2-provenance.json')
assert h['proposal_revision']=='7fd14f99367525caa2bf403a13bf0f3be798763c'
for path,key in [('.agent/contracts/118.json','contract_sha256'),('.agent/evidence/118/api-interface.json','api_sha256'),('.agent/evidence/118/producer-interface.json','producer_sha256')]:
 raw=Path(path).read_bytes();assert raw==git('show',h['proposal_revision']+':'+path) and sha(raw)==h[key]
 mode=git('ls-tree',h['proposal_revision'],'--',path).decode().split()[0];st=Path(path).lstat();assert stat.S_ISREG(st.st_mode) and mode==('100755' if st.st_mode&0o111 else '100644')
 print('PASS actual proposal/Git/current mode',path,sha(raw))
for canonical,row in prov['snapshots'].items():assert Path(row['path']).read_bytes()==git('show',row['revision']+':'+canonical) and sha(Path(row['path']).read_bytes())==row['sha256']
assert c['acceptance_successor_policy']==a['acceptance_successor_policy']==p['acceptance_successor_policy'] and c['precode_gate_policy']==a['precode_gate_policy']==p['precode_gate_policy']
schema=read('.nizam/schema/contract.schema.json');Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(c)
assert c['status']=='proposed' and c['contract_attempt']==3 and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':2,'gate_refs':None}
old=read('.agent/evidence/118/pre-revision2-contract.json')
for key in ['verification','estimated_lines','budget_categories','phase_budget','execution_order','readiness_boundary','canonical_close','lifecycle_values','dependency_features']:assert c[key]==old[key],key
assert c['estimated_lines']==650 and len(c['verification'])==3
print('PASS installed proposal schema, exact predecessor snapshots, unchanged commands/budget/API lifecycle obligations')
policy=c['acceptance_successor_policy']
for key in ['canonical_replacements','record_shape','stage_order','guard_rule']:print('POLICY '+key+': '+json.dumps(policy[key]))
print('CANONICAL_CLOSE: '+c['canonical_close'])
print('APPROVAL_PRESERVE: '+c['precode_gate_policy']['root_approval_changes']['preserve'])
# Pure in-memory status projection, retaining proposal metadata. These are NOT
# approved contracts or fabricated gate receipts; this isolates the byte invariant.
approved=copy.deepcopy(c);approved['status']='approved';complete=copy.deepcopy(approved);complete['status']='complete'
for value in [approved,complete]:Draft202012Validator(schema).validate(value)
def raw(value):return (json.dumps(value,indent=2)+'\n').encode()
assert raw(approved)!=raw(complete) and sha(raw(approved))!=sha(raw(complete))
print('REPRODUCTION: both lifecycle values satisfy installed contract schema; isolated status mutation changes full contract bytes/SHA')
print('IN_MEMORY_APPROVED_SHA256: '+sha(raw(approved)))
print('IN_MEMORY_COMPLETE_SHA256: '+sha(raw(complete)))
print('BLOCKER: precode maps the approved canonical contract; exact current-byte mapping fails after required complete status. No explicit terminal normalization or separate lifecycle observation rule reconciles these obligations. No pipeline artifact changed.')
print('PROPOSAL_DIFF_BEGIN')
print(git('diff',h['base_revision'],h['proposal_revision'],'--','.agent/contracts/118.json','.agent/evidence/118/api-interface.json','.agent/evidence/118/producer-interface.json').decode())
print('PROPOSAL_DIFF_END')
