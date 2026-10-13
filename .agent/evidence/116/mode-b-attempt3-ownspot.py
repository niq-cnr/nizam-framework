import importlib.util,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=load("frozen_tests",ROOT/"tools/test_workflow_assurance.py");a=load("source3",ROOT/"tools/workflow_assurance.py")
b=json.loads((ROOT/".agent/evidence/116/acceptance-bundle.json").read_text());review=json.loads((ROOT/".agent/validator/116-test-bundle-review.json").read_text())
assert a.verify_acceptance_bundle(ROOT,b,review) is True
print("PASS actual complete project bundle and independent canonical nine-field review")
with tempfile.TemporaryDirectory(prefix="nizam116-modeb3-proof-grammar-") as temp:
 f=t.BundleFixture(temp);assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 row=f.row("reject-setup-as-red");path=row["red"]["path"];saved=(f.root/path).read_bytes();old_command=row["red"]["command"]
 for marker in ["SETUP_OR_UNRELATED_ERROR: RuntimeError: unrelated fixture setup failure","Exception: unrelated failure","Error: unrelated failure","package.CustomError: unrelated failure","SystemExit: unrelated failure","UnknownFault: unexpected raw output","SETUP_OR_UNRELATED_ERROR: AttributeError: missing policy API"]:
  data=saved+marker.encode()+b"\n";f.write(path,data);row["red"]["sha256"]=t.sha(data);f.refresh()
  try:a.verify_acceptance_bundle(f.root,f.bundle,f.review)
  except a.AssuranceError as exc:
   assert str(exc)=="setup/transport failure cannot satisfy proof";print("PASS grammar targeted reject",marker)
  else:raise AssertionError("output grammar falsepass "+marker)
  finally:f.write(path,saved);row["red"]["sha256"]=t.sha(saved);f.refresh()
  assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS genuine restored proof positive after each of seven rejects")
 data=saved.replace((row["red"]["diagnostic"]+"\n").encode(),b"").replace(b"STDERR:\n",("STDERR:\n"+row["red"]["diagnostic"]+"\n").encode())
 f.write(path,data);row["red"]["sha256"]=t.sha(data);f.refresh();assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS declared valid named policy diagnostic in STDERR")
 f.write(path,saved);row["red"]["command"]=old_command+" --label RuntimeError: metadata-only"
 data=saved.replace(("COMMAND: "+old_command).encode(),("COMMAND: "+row["red"]["command"]).encode());f.write(path,data);row["red"]["sha256"]=t.sha(data);f.refresh();assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS valid exception-like command metadata remains outside error output channels")
 f.write(path,saved);row["red"]["command"]=old_command;row["red"]["sha256"]=t.sha(saved);f.refresh();assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
print("EXIT 0")
