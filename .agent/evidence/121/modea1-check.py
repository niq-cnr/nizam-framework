import ast,hashlib,json,subprocess
from pathlib import Path
import jsonschema
P=Path;load=lambda p:json.loads(P(p).read_text());c=load('.agent/contracts/121.json')
assert hashlib.sha256(P('.agent/contracts/121.json').read_bytes()).hexdigest()=='a7522f23c64c5581aedf15d274a854bf4e41b933ce08542fe46cf9d772b42fd8'
for schema in ('schema/contract.schema.json','.nizam/schema/contract.schema.json'):jsonschema.validate(c,load(schema))
f=next(x for x in load('.agent/feature_list_018.json')['features'] if x['id']=='121');assert [x['command'] for x in c['verification']]==f['acceptance_tests'] and len(c['verification'])==5
assert c['status']=='proposed' and c['estimated_lines']==f['estimated_lines']==1300==sum(c['budget'][k] for k in ('product','independent_tests','process'))
assert c['budget']['phase_original']==7200 and c['budget']['phase_ceiling']==9360 and c['budget']['prior119actual']==722 and c['budget']['prior120actual']==1397
s=load('.agent/run_state.json');assert s['circuit_breaker']['121-mode-a']=={'attempts':1,'limit':3}
assert s['current_feature']=='121' and s['status']=='in_progress';jsonschema.validate(s,load('.nizam/schema/run_state.schema.json'))
assert load('.nizam/schema/run_state.schema.json')['additionalProperties'] is True
assert 'cancelled' in load('.nizam/schema/feature_list.schema.json')['properties']['features']['items']['properties']['status']['enum']
prereq=load('.agent/evidence/121/source-prerequisite.json');assert prereq['passed'] is True and prereq['all_five_success'] is True and prereq['main_run']==38613899275
for path,pin in prereq['source_bindings'].items():assert hashlib.sha256(P(path).read_bytes()).hexdigest()==pin['sha256'] and subprocess.check_output(['git','cat-file','blob',pin['git_blob']])==P(path).read_bytes()
funcs={n.name:ast.unparse(n.args) for n in ast.parse(P('tools/workflow_assurance.py').read_text()).body if isinstance(n,ast.FunctionDef)}
for name in ('pointers','relative_path','regular_file','_entry_blob','_receipt_artifact','verify_record_update'):assert name in funcs;print('HELPER',name,funcs[name])
assert not subprocess.check_output(['git','diff','--name-only','f270bbb','HEAD','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','.nizam/','schema/','.github/'])
print('PASS exact proposal hash/root+installed schemas/fivecommands/1300/7200/9360; actual counters/schema/helpers/predecessor CI source pins; no product/test/installed edits or runtime acceptance')
