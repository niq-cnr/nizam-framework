import sys,os,json,hashlib,shutil,subprocess
from pathlib import Path
root=Path("/home/cnross/.tmp/nizam-r02-proof-evaluator-qa3");main=Path("/home/cnross/.tmp/nizam-r02-10DF50/repo");os.chdir(root);sys.path.insert(0,str(root/"tools"));import workflow_assurance as wa;import start_path as sp
out=Path(".agent/evidence/r02-proof-validation/evaluator-qa-attempt3");candidate=json.loads((root/out/"candidate.json").read_text());verdict=json.loads((root/out/"qa-proof.json").read_text());checks=wa.qa_required_checks(json.loads((root/".agent/contracts/r02-proof-validation.json").read_text())["verification"])
for k,v in candidate["environment"]["variables"].items():os.environ[k]=v
script=out/"evaluator-adversarial.py";shutil.copyfile("/home/cnross/.tmp/nizam-r02-proof-evaluator-adversarial-qa3.py",root/script)
cap=sp.capture_command_evidence(root,task_id="r02-proof-validation",step="adversarial",attempt=3,output_dir=out,argv=["python",script.as_posix()],candidate_sha256=candidate,proof_kind="success",agent_id="independent-evaluator",session_id="r02-proof-qa-attempt3",timeout_sec=1200)
print("ADVERSARIAL",cap["exit_code"],cap["capture_path"],flush=True)
assert cap["exit_code"]==0,cap
adversarial_text=out/"r02-proof-validation-qa-adversarial.txt"
with (root/adversarial_text).open("xb") as f:f.write((root/cap["stdout"]["path"]).read_bytes())
verdict["adversarial_check"]={"description":"Exactly one evaluator-origin extra check: shared QA rejects stream symlink alias with identical bytes/digest in synthetic negative capture copy.","result":"pass","evidence":adversarial_text.as_posix(),"capture":cap["capture_path"]}
verdict["evidence_files"].append(cap["capture_path"]);verdict["adversarial"]["capture"]=cap["capture_path"]
final=root/out/"qa-final-proof.json"
with final.open("x") as f:json.dump(verdict,f,indent=2);f.write("\n")
wa.validate_qa_proof(root,verdict,feature_id="r02-proof-validation",candidate=candidate,required_checks=checks)
print("FINAL-PROOF-VALIDATED",flush=True)
# Clone uses original source repository's immutable objects. Only QA artifacts transfer.
relocated=Path("/home/cnross/.tmp/nizam-r02-proof-evaluator-replay3")
subprocess.check_call(["git","clone","--no-hardlinks","--no-checkout",str(main),str(relocated)])
subprocess.check_call(["git","-C",str(relocated),"checkout","--detach",candidate["source_commit"]])
subprocess.check_call(["git","-C",str(relocated),"remote","set-url","origin",candidate["repository"]])
shutil.copytree(root/out,relocated/out)
replaycode="""import sys,json,os;from pathlib import Path;root=Path.cwd();sys.path.insert(0,str(root/'tools'));import workflow_assurance as wa;out=Path('.agent/evidence/r02-proof-validation/evaluator-qa-attempt3');candidate=json.loads((out/'candidate.json').read_text());verdict=json.loads((out/'qa-final-proof.json').read_text());checks=wa.qa_required_checks(json.loads(Path('.agent/contracts/r02-proof-validation.json').read_text())['verification']);assert str(root)!=candidate['environment']['variables'][wa.QA_EXECUTION_ROOT_VARIABLE];wa.validate_qa_proof(root,verdict,feature_id='r02-proof-validation',candidate=candidate,required_checks=checks);print('PASS relocated checkout validates original assessed QA proof with explicit original context/environment')"""
r=subprocess.run(["python","-c",replaycode],cwd=relocated,capture_output=True)
print("RELOCATED",r.returncode,r.stdout.decode(),r.stderr.decode(),flush=True)
for suffix,data in [("stdout",r.stdout),("stderr",r.stderr)]:
 with (root/out/("relocated-verification."+suffix+".txt")).open("xb") as f:f.write(data)
with (root/out/"relocated-verification.execution.json").open("x") as f:json.dump({"argv":["python","-c",replaycode],"cwd":str(relocated),"exit_code":r.returncode,"reviewed_revision":candidate["source_commit"],"stdout_sha256":hashlib.sha256(r.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr).hexdigest()},f,indent=2);f.write("\n")
assert r.returncode==0
# Transfer byte-identical official captures and manifest to main delivery records.
shutil.copytree(root/out,main/out)
for marker in (root/".agent/evidence").glob("r02-proof-validation-*-attempt3.reservation.json"):
 destination=main/".agent/evidence"/marker.name
 assert not destination.exists(),str(destination)
 shutil.copyfile(marker,destination)
qa_path=main/".agent/qa/r02-proof-validation-qa.json"
with qa_path.open("x") as f:json.dump(verdict,f,indent=2);f.write("\n")
print("DELIVERED",qa_path,flush=True)
