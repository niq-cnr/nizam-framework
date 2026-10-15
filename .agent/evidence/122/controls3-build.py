"""Build concrete private new122 semantic mutants and a self-contained blob pack; no API execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PREFIX = '.agent/evidence/122/controls3-'
source = (ROOT/'tools/workflow_assurance.py').read_bytes()
assert hashlib.sha256(source).hexdigest() == 'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6'
targets = {
 'infrastructure-failed': ('route_failed_attempt', "request['cause'] + ('-diagnosis' if request['cause'] == 'infrastructure' else '-repair'),", "request['cause'] + ('-repair' if request['cause'] == 'infrastructure' else '-repair'),", 'AssertionError: POLICY_ASSERTION: exact failed routing result and integer counts'),
 'semantic-failed': ('_failure_rejection', "require(rejected or any(verdict.get(key, []) for key in arrays), 'failure semantic verdict passed')", "require(True or any(verdict.get(key, []) for key in arrays), 'failure semantic verdict passed')", 'AssertionError: POLICY_ASSERTION: invalid failure routing input accepted'),
 'reject-cause-relabel': ('route_failed_attempt', "authority['role'] == 'Orchestrator' and authority['approved'] is True and", "authority['role'] == 'Orchestrator' and authority['approved'] in (True, 1) and", 'AssertionError: POLICY_ASSERTION: invalid failure routing input accepted'),
 'counter-continuity': ('_failure_continuity', '    verify_record_update(anchor, current, owned)', "    verify_record_update(anchor, current, owned + ['/scope_budget/total_lines_changed'])", 'AssertionError: POLICY_ASSERTION: invalid failure routing input accepted')}
objects = {'source':source,'tests':(ROOT/'tools/test_workflow_assurance.py').read_bytes(), 'helper':(ROOT/(PREFIX+'run.py')).read_bytes(), 'worker':(ROOT/(PREFIX+'worker.py')).read_bytes()}
assert hashlib.sha256(objects['tests']).hexdigest() == '800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'
original = ast.parse(source)
controls = {}
for name,(function,old,new,assertion) in targets.items():
    assert source.count(old.encode()) == 1
    mutant = source.replace(old.encode(),new.encode())
    parsed = ast.parse(mutant)
    assert len(original.body) == len(parsed.body)
    for left,right in zip(original.body,parsed.body):
        if getattr(left,'name',None) == function: assert ast.dump(left) != ast.dump(right)
        else: assert ast.dump(left) == ast.dump(right), name
    objects[name] = mutant
    controls[name] = dict(function=function,old=old,new=new,assertion=assertion)
identities = {}
for label,data in objects.items():
    oid = subprocess.check_output(['git','-C',str(ROOT),'hash-object','-w','--stdin'],input=data).decode().strip()
    identities[label] = dict(git_oid=oid,sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data),type='blob')
prior = json.loads((ROOT/'.agent/evidence/122/controls2-identities.json').read_bytes())
assert all(identities[label] == prior['objects'][label] for label in ('source',*targets))
pack = subprocess.check_output(['git','-C',str(ROOT),'pack-objects','--stdout'],input=('\n'.join(v['git_oid'] for v in identities.values())+'\n').encode())
with (ROOT/(PREFIX+'identities.pack')).open('xb') as handle: handle.write(pack)
with (ROOT/(PREFIX+'identities.json')).open('x') as handle:
    json.dump(dict(source_revision='09e0eb6b1257cd676d107bd8abea4844a25494de',objects=identities,controls=controls,
        pack_sha256=hashlib.sha256(pack).hexdigest(),mutant_private_file_mode='0600',trust='Synthetic fixtures; no API or acceptance behavior executed during preparation'),handle,indent=2)
    handle.write('\n')
print('PACK_BUILT_STATIC',len(identities),'blobs',hashlib.sha256(pack).hexdigest())
