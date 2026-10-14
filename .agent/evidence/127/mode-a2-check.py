import copy,hashlib,json,pathlib,subprocess
import jsonschema
R=pathlib.Path.cwd()
def git(*a):return subprocess.check_output(['git',*a])
def load(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
a=json.loads(git('show','cf02c6ee79a8d82ca5b468f153f03e82de417956:.agent/contracts/127.json')); b=load('.agent/contracts/127.json')
assert sha('.agent/contracts/127.json')=='a98180d2c1456d95f0ec120dba40f043b7c367b92f884f8d58f784d07679b13a'
jsonschema.Draft202012Validator(load('.nizam/schema/contract.schema.json')).validate(b)
assert b['status']=='proposed' and b['contract_attempt']==2 and b['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':1}
normalized=copy.deepcopy(b)
for k in ('scope','non_goals','contract_attempt','approvals'):normalized[k]=a[k]
assert normalized==a
assert b['scope']['files_modify'][:len(a['scope']['files_modify'])]==a['scope']['files_modify']
assert b['non_goals'][:2]==a['non_goals'][:2]
newcreate={x['path']:x['purpose'] for x in b['scope']['files_create']}
assert set(newcreate)=={'.agent/evidence/127/','.agent/validator/127-*.json','.agent/qa/127*.json','.agent/evidence/127-qa-adversarial.txt'}
newmodify={x['path']:x['purpose'] for x in b['scope']['files_modify'][len(a['scope']['files_modify']):]}
assert set(newmodify)=={'.agent/contracts/127.json','.agent/run_state.json','.agent/feature_list_016.json','docs/planning/phase_016.yaml','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md'}
assert load('.agent/run_state.json')['circuit_breaker']['127-mode-a']['attempts']==2
prior=load('.agent/evidence/127/mode-a-check-result.json')
assert all(sha(p)==h for p,h in prior['input_sha256'].items())
assert not git('diff',b['base_revision'],'HEAD','--',*[x['path'] for x in a['scope']['files_modify']])
result={'reviewed_commit':git('rev-parse','HEAD').decode().strip(),'proposal_commit':'bac04b8d94092343437ad95b07b99c2eb6592c11','contract_sha256':sha('.agent/contracts/127.json'),'prior_contract_sha256':prior['contract_sha256'],'checks':['installed contract schema valid','only scope attribution/non-goals and round metadata changed','original six product/test entries unchanged','full prior behavior/verification/budget/gate sequence exactly preserved','new role-owned create/modify sets checked','all14 prior normative/source/test input hashes unchanged','no source/test implementation since original baseline','current Mode A attempt2; approval fields false'],'reviewed_create_ownership':newcreate,'reviewed_added_modify_ownership':newmodify,'actual_exit':0}
(R/'.agent/evidence/127/mode-a2-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS narrow delta, complete role-owned artifact scope, protected product/verification/budget, schema and immutable inputs')
