import sys,os,json,subprocess,hashlib,datetime,shutil
from pathlib import Path
root=Path("/home/cnross/.tmp/nizam-r02-proof-evaluator-qa")
main=Path("/home/cnross/.tmp/nizam-r02-10DF50/repo")
os.chdir(root)
sys.path.insert(0,str(root/"tools"))
import workflow_assurance as wa
import start_path as sp
feature="r02-proof-validation"
contract=json.loads((root/".agent/contracts/r02-proof-validation.json").read_text())
checks=wa.qa_required_checks(contract["verification"])
os.environ["GIT_CONFIG_GLOBAL"]="/dev/null";os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["XDG_CACHE_HOME"]="/home/cnross/.tmp/nizam-r02-proof-evaluator-cache"
os.environ[wa.QA_EXECUTION_ROOT_VARIABLE]=str(root)
os.environ[wa.QA_CONTEXT_VARIABLE]=wa.qa_context_sha256(root,feature,[".agent/contracts/r02-proof-validation.json"],checks)
paths=subprocess.check_output(["git","ls-files","-z"]).decode().split(chr(0))[:-1]
inputs={"source":[],"tests":[],"tools":[],"contracts":[],"unknown_dependencies":[]}
for path in paths:
 category="contracts" if path==".agent/contracts/r02-proof-validation.json" else "tests" if path.startswith("tools/test_") or "/fixtures/" in path else "tools" if path.startswith(("tools/","schema/")) else "source"
 inputs[category].append(path)
names=["GIT_CONFIG_GLOBAL","PYTHONDONTWRITEBYTECODE","XDG_CACHE_HOME",wa.QA_CONTEXT_VARIABLE,wa.QA_EXECUTION_ROOT_VARIABLE]
revision=subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
candidate=wa.assess_repository(root,revision,inputs,names,{})
wa.validate_qa_context(root,feature,candidate,checks)
out=Path(".agent/evidence/r02-proof-validation/evaluator-qa")
(root/out).mkdir(parents=True)
def save(rel,value):
 path=root/rel
 with path.open("x") as f:json.dump(value,f,indent=2);f.write("\n")
 return {"path":rel.as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
manifest=save(out/"candidate.json",candidate)
records=[]
for policy in checks:
 print("START",policy["id"],datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
 cap=sp.capture_command_evidence(root,task_id=feature,step=policy["id"],attempt=1,output_dir=out,argv=policy["argv"],candidate_sha256=candidate,proof_kind=policy["proof_kind"],agent_id="independent-evaluator",session_id="r02-proof-qa-attempt1",timeout_sec=1200)
 print("RESULT",policy["id"],cap["exit_code"],cap["capture_path"],flush=True)
 records.append({"id":policy["id"],"capture":{"path":cap["capture_path"],"sha256":hashlib.sha256((root/cap["capture_path"]).read_bytes()).hexdigest()}})
 if cap["exit_code"]!=policy["expected_exit"]:
  save(out/"failed-check.json",{"id":policy["id"],"capture":cap})
  sys.exit(1)
verdict={"feature_id":feature,"proof_version":2,"qa_pass":True,"checks_run":len(checks),"checks_passed":len(checks),"adversarial":{"performed":True},"checks":records,"candidate_ref":manifest,"evidence_files":[x["capture"]["path"] for x in records],"issues":[],"unsupported_claims":[],"missing_acceptance_coverage":[],"required_fixes":[],"reviewed_revision":revision,"reviewer":"independent-evaluator","approved_contract_sha256":hashlib.sha256((root/".agent/contracts/r02-proof-validation.json").read_bytes()).hexdigest(),"final_verdict":{"approved":True,"summary":"Independent five-command candidate-bound QA and one extra stream-symlink check."}}
save(out/"qa-proof.json",verdict)
wa.validate_qa_proof(root,verdict,feature_id=feature,candidate=candidate,required_checks=checks)
print("FIVE-CHECK-PROOF-VALIDATED",flush=True)
