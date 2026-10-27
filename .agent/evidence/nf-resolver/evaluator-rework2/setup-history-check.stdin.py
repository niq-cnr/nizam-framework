from pathlib import Path
import sys,json,subprocess,tempfile,hashlib,shutil
root=Path.cwd();sys.path.insert(0,str(root/'tools'));import start_path as sp
history=sp._task_capture_history(root,'nf-resolver');failed=[d for d in history if not sp._successful_task_capture(root,d)];assert len(failed)==5,len(failed)
sha='0f7564595aff062364ccb097b17bf2f2eaac49c2';area=Path(tempfile.mkdtemp(prefix='nf-resolver-independent-r2-'));clone=area/'repo'
subprocess.run(['git','clone','--quiet','--no-hardlinks','--no-checkout',str(root),str(clone)],check=True);subprocess.run(['git','checkout','--quiet','--detach',sha],cwd=clone,check=True);assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone)
fp=clone/'.agent/evidence/nf-resolver/generator/source-freeze-rework2.json';freeze=json.loads(fp.read_text());mode=json.loads((root/'.agent/validator/nf-resolver-mode-b-rework2.json').read_text());assert mode['assessed_commit']==sha and hashlib.sha256(fp.read_bytes()).hexdigest()==mode['source_freeze_sha256'];assert hashlib.sha256((clone/'.agent/contracts/nf-resolver.json').read_bytes()).hexdigest()==freeze['contract_sha256']
for path,digest in freeze['source_sha256'].items():assert hashlib.sha256((clone/path).read_bytes()).hexdigest()==digest,path
for p in (root/'.agent/evidence/nf-resolver').rglob('*'):
 if not p.is_file():continue
 target=clone/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==p.read_bytes(),p
 else:shutil.copyfile(p,target)
cloned_history=sp._task_capture_history(clone,'nf-resolver');cloned_failed=[d for d in cloned_history if not sp._successful_task_capture(clone,d)];assert len(cloned_failed)==5
out=root/'.agent/evidence/nf-resolver/evaluator-rework2';out.mkdir(parents=True,exist_ok=True);(out/'clone-identity.json').write_text(json.dumps({'candidate_sha':sha,'initial_status':'clean before prior evidence copy','source_manifest_sha256':freeze['source_manifest_sha256'],'mode_b':'.agent/validator/nf-resolver-mode-b-rework2.json','source_hashes':'all12 product paths and contract matched','clone':str(clone),'failed_execution_count_before_qa':len(failed),'failed_capture_paths':[d['capture_path'] for d in failed],'failure_ceiling':6,'no_reset':True,'environment':'Darwin arm64 CPython3.14.6','sandbox':'unavailable; dedicated filesystem/effects tests only'},indent=2)+'\n')
prior=root/'.agent/qa/nf-resolver-qa-attempt1.json';data=(root/'.agent/qa/nf-resolver-qa.json').read_bytes()
if prior.exists():assert prior.read_bytes()==data
else:prior.write_bytes(data)
Path('/tmp/nf-resolver-evaluator-location-r2.txt').write_text(str(clone));print(json.dumps({'clone':str(clone),'actual_task_failures':len(failed),'remaining_failures_before_required_stop':1,'source_sha':sha}))
