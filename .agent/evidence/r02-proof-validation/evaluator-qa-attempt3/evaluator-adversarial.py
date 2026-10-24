import sys,os,json,copy,tempfile,hashlib
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/"tools"));import workflow_assurance as wa
out=Path(".agent/evidence/r02-proof-validation/evaluator-qa-attempt3")
verdict=json.loads((root/out/"qa-proof.json").read_text());candidate=json.loads((root/out/"candidate.json").read_text());checks=wa.qa_required_checks(json.loads((root/".agent/contracts/r02-proof-validation.json").read_text())["verification"])
for k,v in candidate["environment"]["variables"].items():assert os.environ.get(k)==v,(k,os.environ.get(k),v)
with tempfile.TemporaryDirectory(prefix="stream-alias-",dir=root/out) as directory:
 scratch=Path(directory);bad=copy.deepcopy(verdict);cap=json.loads((root/bad["checks"][0]["capture"]["path"]).read_text());original=root/cap["stdout"]["path"]
 alias=scratch/"same-bytes-symlink.stdout";alias.symlink_to(original)
 assert alias.read_bytes()==original.read_bytes()
 cap["stdout"]["path"]=alias.relative_to(root).as_posix()
 cp=scratch/"synthetic-negative.capture.json";cap["capture_path"]=cp.relative_to(root).as_posix();cp.write_text(json.dumps(cap,indent=2)+"\n")
 bad["checks"][0]["capture"]={"path":cp.relative_to(root).as_posix(),"sha256":hashlib.sha256(cp.read_bytes()).hexdigest()}
 try:wa.validate_qa_proof(root,bad,feature_id="r02-proof-validation",candidate=candidate,required_checks=checks)
 except wa.AssuranceError as exc:
  assert "symlink" in str(exc),str(exc)
  print(json.dumps({"check":"shared structured QA stream same-bytes symlink alias","result":"pass","expected":"refuse symlink despite exact bytes and digest","observed_diagnostic":str(exc),"synthetic_negative_metadata":True}))
 else:raise AssertionError("Shared proof accepted aliased symlink stream")
