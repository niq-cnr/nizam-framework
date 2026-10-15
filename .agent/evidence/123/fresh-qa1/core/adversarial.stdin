import hashlib,importlib.util,json,os,stat,subprocess
from pathlib import Path
root=Path.cwd();out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/core')
def sha(b):return hashlib.sha256(b).hexdigest()
def get(r):
 b=subprocess.check_output(['git','show',r['revision']+':'+r['path']]);assert sha(b)==r['sha256'];return json.loads(b)
path=root/'tools/workflow_assurance.py';assert sha(path.read_bytes())=='2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8'
spec=importlib.util.spec_from_file_location('freshqa_actual_api',path);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
policy=json.loads((root/'.agent/evidence/123/controls-policy.json').read_bytes());evidence=get(policy['evidence_ref']);original=json.dumps([policy,evidence],sort_keys=True)
ref=evidence['capture_host']['metadata_ref'];target=root/ref['path'];raw=target.read_bytes();info=target.lstat();assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and sha(raw)==ref['sha256']
proof=api._ControlsProof(root);baseline=proof.verify(evidence,policy)
expected=dict(schema_version=1,feature_id='123',source_commit=evidence['candidate']['source_commit'],checkout_sha=evidence['checkout']['sha'],candidate_sha256=sha(api.canonical(evidence['candidate'])),capture_run_id=evidence['capture_host']['run_id'],verify_run_id=evidence['verify_host']['run_id'],a11_verdict='approve',a10_receipt_sha256=evidence['a10_receipt_ref']['sha256'],transition_actions=['advance','noop','republish','rerun-required'],hosted_review_sha256=policy['hosted_review_ref']['sha256'])
assert baseline==expected and (ref['revision'],ref['path']) in proof.cache
print('POSITIVE genuine selected proof verified and exact capture HostMetadata cached',flush=True)
link=out/'own-extra-metadata-hardlink';assert not link.exists();linked=False
try:
 os.link(target,link);linked=True;mutated=target.lstat();assert mutated.st_ino==link.lstat().st_ino and mutated.st_nlink==2 and mutated.st_mode==info.st_mode and target.read_bytes()==raw
 print('MUTATED '+json.dumps(dict(selected_ref=ref,inode=mutated.st_ino,nlink=mutated.st_nlink,mode=mutated.st_mode,sha256=sha(raw)),sort_keys=True),flush=True)
 try:proof.verify(evidence,policy)
 except api.AssuranceError as exc:
  assert str(exc)=='capture metadata current artifact regular mode/hardlink',str(exc)
  print('EXPECTED_REJECTION same warmed parser: '+str(exc),flush=True)
 else:raise AssertionError('warmed immutable cache accepted newly hardlinked selected metadata')
finally:
 if linked:
  assert link.lstat().st_ino==target.lstat().st_ino;link.unlink()
 assert target.read_bytes()==raw and target.lstat().st_mode==info.st_mode and target.lstat().st_nlink==1
restored=proof.verify(evidence,policy);assert restored==baseline and json.dumps([policy,evidence],sort_keys=True)==original
print('RESTORED same warmed parser returns identical genuine result '+json.dumps(restored,sort_keys=True),flush=True)
print('PASS exactly one independently selected extra: warmed-cache physical metadata hardlink rejection and restoration',flush=True)
