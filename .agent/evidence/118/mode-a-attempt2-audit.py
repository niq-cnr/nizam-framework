"""Independent Mode A structural audit; no acceptance or lifecycle execution."""
import ast, copy, hashlib, json, stat, subprocess
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

def read(p): return json.loads(Path(p).read_text())
def git(*args): return subprocess.check_output(['git', *args])
def validate(obj, path):
    schema=read(path); Draft202012Validator.check_schema(schema); Draft202012Validator(schema).validate(obj)
def same_git(path, rev):
    data=Path(path).read_bytes(); assert data == git('show',rev+':'+path), path
    mode=git('ls-tree',rev,'--',path).decode().split()[0]
    st=Path(path).lstat(); assert stat.S_ISREG(st.st_mode)
    assert mode == ('100755' if st.st_mode & 0o111 else '100644'), (path,mode,st.st_mode)
    return hashlib.sha256(data).hexdigest()

owner=read('.agent/evidence/118/mode-a-attempt2.json')
head=git('rev-parse','HEAD').decode().strip()
assert owner['owner']=='/root/wa_validator118' and str(Path.cwd())==owner['root']
assert head==owner['base']=='a51600409fdfa80c527bd3106be934efc071837d'
state=read('.agent/run_state.json'); phase=yaml.safe_load(Path('docs/planning/phase_017.yaml').read_text())
assert state['current_feature']==state['active_contract_id']=='118' and state['status']=='in_progress'
assert state['circuit_breaker']['118-mode-a']=={'attempts':1,'limit':3}
assert phase['status']=='in_progress' and phase['steps'][-1]['id']=='118' and phase['steps'][-1]['status']=='IN_PROGRESS'
print('PASS owned detached attempt2 and canonical/derived active118/counter1')
c=read('.agent/contracts/118.json'); a=read('.agent/evidence/118/api-interface.json'); p=read('.agent/evidence/118/producer-interface.json')
h=read('.agent/evidence/118/contract-proposal-handoff-attempt2.json')
assert h['proposal_revision']=='489380a1807245fe33b9ea79f98b9880f7f2673b'
for path,key in [('.agent/contracts/118.json','contract_sha256'),('.agent/evidence/118/api-interface.json','api_sha256'),('.agent/evidence/118/producer-interface.json','producer_sha256')]:
    digest=same_git(path,h['proposal_revision']); assert digest==h[key]; print('PASS proposal blob/current mode',path,digest)
validate(c,'.nizam/schema/contract.schema.json')
assert c['status']=='proposed' and c['contract_attempt']==2 and c['approvals']=={'validator_mode_a':False,'evaluator_contract_review':False,'revisions':1,'gate_refs':None}
assert c['precode_gate_policy']==a['precode_gate_policy']==p['precode_gate_policy']
assert c['lifecycle_values']==a['lifecycle_values']==p['lifecycle_values']
assert c['execution_order']==p['ordering']
features=read('.agent/feature_list_017.json'); target=features['features'][-1]
assert target['id']=='118'
assert [v['command'] for v in c['verification']]==target['acceptance_tests'] and len(c['verification'])==3
assert c['estimated_lines']==target['estimated_lines']==650 and c['budget_categories']==target['budget_categories']
assert c['dependency_features']==target['dependencies']==['116','117']
assert state['scope_budget']['total_lines_changed']==4012 and state['scope_budget']['original_estimate_lines']==5400 and state['scope_budget']['ceiling_130pct']==7020
assert [f['status'] for f in features['features'][:-1]]==['complete']*3
assert [f['passes'] for f in features['features'][:-1]]==[True]*3
expected=[cmd for f in features['features'][:-1] for cmd in f['acceptance_tests']]
assert [r['command'] for r in a['current_cases']]==expected and len(expected)==20
assert len(set(r['case'] for r in a['current_cases']))==20
assert a['core_paths']==p['core_paths'] and a['historical_paths']==p['historical_paths'] and len(a['historical_paths'])==12
for path in a['historical_paths']: same_git(path,a['historical_base'])
print('PASS exact planning traceability: three commands,650 estimate,20 prerequisite cases,12 immutable historical records')
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']: same_git(path,a['historical_base'])
module=ast.parse(Path('tools/test_workflow_assurance.py').read_text())
entry=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='run_entry_case')
assert '.agent/evidence/117/entry-fixtures.py' in ast.unparse(entry)
fixture=ast.parse(Path('.agent/evidence/117/entry-fixtures.py').read_text())
for n in fixture.body:
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['APPROVED','PROPOSAL']:
        rev=ast.literal_eval(n.value); git('cat-file','-e',rev+'^{commit}'); print('PASS existing entry fixture immutable revision',n.targets[0].id,rev)
values=c['lifecycle_values']; phase['status']=values['phase_status']['after']; phase['steps'][-1]['status']=values['phase_step118_status']['after']
validate(phase,'.nizam/schema/phase.schema.json')
manifest=read('docs/planning/manifest.json'); row=next(x for x in manifest['phases'] if x['id']==phase['id']); row['status']=values['manifest_phase017_status']['after']
validate(manifest,'.nizam/schema/manifest.schema.json')
assert phase['status']==row['status']=='complete' and phase['steps'][-1]['status']=='COMPLETED'
validate(state,'.nizam/schema/run_state.schema.json')
assert read('.nizam/provenance.json')['resolved_sha']=='f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852'
print('PASS in-memory lifecycle schema projection complete/COMPLETED and current runstate schema; no canonical state changed')
print('PASS structural review only: SourceC, current20 execution, ready behavior, QA and capture remain future gates')
