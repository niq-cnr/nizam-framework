"""Final frozen-manifest reconciliation; does not rerun static preparation."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT=Path(__file__).resolve().parents[3]
RELEASE='0e892bc5e261f10644c044e5474831e56b25d534'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def sha(data):return hashlib.sha256(data).hexdigest()
def ref(row):
    data=git('show',row['revision']+':'+row['path']);header=git('ls-tree',row['revision'],'--',row['path']).split(b'\t')[0].decode().split()
    assert header==[row['git_mode'],'blob',row['git_blob']] and sha(data)==row['sha256']
    target=ROOT/row['path'];assert target.is_file() and not target.is_symlink() and target.stat().st_nlink==1 and target.read_bytes()==data
    assert bool(target.stat().st_mode&0o111)==(row['git_mode']=='100755')
    return data
def snapshot():
    paths=git('ls-tree','-r','--name-only',RELEASE,'--','.nizam').decode().splitlines()
    paths+=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/123.json','.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml']
    return {p:(stat.S_IMODE((ROOT/p).lstat().st_mode),(ROOT/p).lstat().st_nlink,sha((ROOT/p).read_bytes())) for p in paths}

assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1' and git('rev-parse','HEAD').decode().strip()==RELEASE
before=snapshot();admission=json.loads((ROOT/'.agent/evidence/123/root-author3-admission.json').read_bytes())
bundle_ref=admission['author_bundle_ref'];bundle_raw=git('show',bundle_ref['revision']+':'+bundle_ref['path'])
assert sha(bundle_raw)==bundle_ref['sha256'] and bundle_raw==(ROOT/bundle_ref['path']).read_bytes()
bundle=json.loads(bundle_raw);records=bundle['owned_code_refs']+bundle['independent_static_refs']+[bundle['approved_contract'],bundle['source_anchor']]
for row in records:ref(row)
assert len(records)==admission['verified_immutable_refs']==10
assert bundle['code_revision']=='9718b72ab1a988fe384c8f0d69afd6d1c4ac56e8'
proof=json.loads((ROOT/'.agent/evidence/123/provisional3-preparation-static.stdout.txt').read_bytes())
execution=json.loads((ROOT/'.agent/evidence/123/provisional3-preparation-static.execution.json').read_bytes())
assert proof['actual_exit']==execution['actual_exit']==0 and proof['code_checkpoint']==execution['code_checkpoint']==bundle['code_revision']
assert proof['owned_code_refs']==bundle['owned_code_refs']
assert proof['formal_approval'] is False and proof['behavior_executed'] is False
for key,value in bundle['independent_static_observation'].items():assert proof[key]==value
assert execution['exercised_revision']=='792c1674870ae29996e14636057cb70825f5eb07'
assert sha((ROOT/'tools/test_workflow_assurance.py').read_bytes())==proof['test_sha256']=='9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'
assert sha((ROOT/'tools/workflow_assurance.py').read_bytes())==proof['source_sha256']=='fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6'
assert bundle['behavior_executions']==0 and bundle['default_count']==48
assert proof['stage_frame_static_bindings_present'] is True and proof['nested_a10_outer_frame_static_binding_present'] is True
assert len(before)==245 and snapshot()==before
print(json.dumps({'role':'independent final provisional reviewer3','reviewed_revision':RELEASE,'actual_exit':0,'reconciled_immutable_refs':10,
    'author_bundle_ref':bundle_ref,'code_revision':bundle['code_revision'],'test_sha256':proof['test_sha256'],'source_sha256':proof['source_sha256'],
    'independent_static_proof_revision':'6316501ef7703ca62d93b334ad11084bdd62f5e1','static_preparation_rerun':False,
    'current_final_release_inputs_preserved':len(before),'historical_coordination_checked_at_recorded_ref':True,
    'behavior_executed':False,'scope':'Final manifest/code/proof reconciliation only; does not establish constructor/API/acceptance or hosted success.'},sort_keys=True))
