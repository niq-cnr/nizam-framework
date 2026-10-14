import hashlib,json,pathlib,subprocess
import jsonschema
root=pathlib.Path.cwd()
def read(p):return json.loads((root/p).read_text())
def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
c=read('.agent/contracts/127.json'); dispatch=read('.agent/evidence/127/precode-dispatch.json')
assert sha('.agent/contracts/127.json')=='16305458df6afb3b4df9b9f9d59c005e0a1103a75811dd0fc70ddca9d7516ac1'
jsonschema.Draft202012Validator(read('.nizam/schema/contract.schema.json')).validate(c)
assert c['status']=='proposed' and not c['approvals']['validator_mode_a'] and not c['approvals']['evaluator_contract_review']
f=next(x for x in read('.agent/feature_list_016.json')['features'] if x['id']=='127')
assert [x['command'] for x in c['verification']]==f['acceptance_tests'] and len(c['verification'])==5
assert len(read('.agent/contracts/126.json')['verification'])==9
assert c['base_revision']==dispatch['source_baseline']
assert c['budget']['phase_original']==5650 and c['budget']['phase_ceiling']==7345 and c['budget']['already_counted']==3003 and c['estimated_lines']==1950
product=[x['path'] for x in c['scope']['files_modify']]
assert not subprocess.check_output(['git','diff',c['base_revision'],'HEAD','--',*product])
assert read('.agent/run_state.json')['circuit_breaker']['127-mode-a']['attempts']==1
inputs=['.nizam/standard/AGF.md','.nizam/methodology/01_execution.md','.nizam/methodology/00_planning.md','methodology/10_live_runtime_sessions.md','methodology/11_sbcl_runtime_binding.md','tools/interface.md','standard/permission_classes.md','docs/nips/NIP-0003-live-runtime-sessions.md','schema/runtime_session.schema.json','schema/runtime_operation.schema.json','tools/verify_lib.sh','tools/runtime_session.py','tools/test_runtime_session.py','.agent/contracts/126.json']
result={'reviewed_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'contract_sha256':sha('.agent/contracts/127.json'),'checks':{'contract_schema':'pass','five_commands_match_feature_exactly':True,'inherited_plus_new_command_count':14,'unchanged_source_and_tests_since_base':True,'mode_a_attempt':1,'original_budget_and_actual_preserved':True},'input_sha256':{p:sha(p) for p in inputs},'scope_gap':{'declared_create':[x['path'] for x in c['scope']['files_create']],'promised_external_evidence_path':'.agent/evidence/127-qa-adversarial.txt','canonical_role_outputs_missing_from_scope':['.agent/contracts/127.json','.agent/validator/127-*.json','.agent/qa/127*.json'],'required_ownership_clarification':'Preserve Root-only approval/lifecycle/run-state/counter/budget updates as separately attributed coordination; no Generator permission and no whole-file freezing.'},'actual_exit':0,'boundary':'Static proposal identity/schema/traceability checks only; not implementation, semantic-red, QA or capability evidence.'}
(root/'.agent/evidence/127/mode-a-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS proposal schema, exact five commands, unchanged product/test baseline, budget and attempt checks; scope gap recorded for gate decision')
