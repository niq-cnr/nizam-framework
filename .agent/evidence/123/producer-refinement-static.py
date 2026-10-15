"""Static-only producer bounds refinement inspection, no product imports."""
import ast,hashlib,subprocess
from pathlib import Path
base='893655b3a35183b9da2f253eba53107dbdf3b093'
runner='tools/workflow_assurance_ci.py'
def old(path):return subprocess.check_output(['git','show',base+':'+path])
def defs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
raw=Path(runner).read_bytes();compile(raw,runner,'exec')
before=defs(old(runner));after=defs(raw)
changed={name for name in before if before[name]!=after.get(name)}
assert changed=={'command','put','failed_child','stage_command','OperationTee','run_verify','main'},changed
for name in ['observe','run_map','run_capture','prepare','capture_record','encoded','bundle_outputs']:
 assert before[name]==after[name],name
for path,digest in [('tools/workflow_assurance.py','7385ee079e47c70e7939692f7505898f2dc81f07629a5d9dc11e89ded3cf90ae'),('tools/test_workflow_assurance.py','9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'),('.agent/contracts/123.json','64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5')]:
 value=Path(path).read_bytes();assert value==old(path) and hashlib.sha256(value).hexdigest()==digest
 print('STATIC preserved '+path+' '+digest)
assert Path('.agent/run_state.json').read_bytes()==old('.agent/run_state.json')
assert subprocess.check_output(['git','diff','--name-only',base],text=True).splitlines()==[runner]
assert not subprocess.check_output(['git','diff',base,'--','.nizam'])
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','.nizam'])
assert Path(runner).stat().st_mode&0o111
assert b'capture_output=True' not in raw
subprocess.run(['git','diff','--check'],check=True)
print('STATIC in-memory compile; only producer helpers and necessary strict-index/A10/failure callsites changed')
print('STATIC exact observer/map/capture/prepare/public-record producer ASTs preserved')
print('STATIC runner SHA256 '+hashlib.sha256(raw).hexdigest())
print('No product import, helper behavior, API, selector, constructor, namespace, model, compliance or hosted execution')
