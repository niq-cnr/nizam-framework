import importlib.util,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=load("frozen_suite",ROOT/"tools/test_workflow_assurance.py");a=load("actual_source2",ROOT/"tools/workflow_assurance.py")
with tempfile.TemporaryDirectory(prefix="nizam116-modeb2-error-grammar-") as temp:
 f=t.BundleFixture(temp);assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS clean complete fixture positive; real baseline Git and known valid proof bytes")
 row=f.row("reject-setup-as-red");path=row["red"]["path"];saved=(f.root/path).read_bytes();missed=[]
 for marker in ["SETUP_OR_UNRELATED_ERROR: RuntimeError: unrelated fixture setup failure", "RuntimeError: unrelated fixture failure", "Exception: unrelated fixture failure"]:
  data=saved+marker.encode()+b"\n";f.write(path,data);row["red"]["sha256"]=t.sha(data);f.refresh()
  try:a.verify_acceptance_bundle(f.root,f.bundle,f.review)
  except a.AssuranceError as exc:
   assert str(exc)=="setup/transport failure cannot satisfy proof";print("PASS exact producer/error marker rejection",marker,str(exc))
  else:missed.append(marker);print("FALSE_PASS generic exception marker",marker,"accepted with named POLICY_ASSERTION/EXIT1")
  finally:f.write(path,saved);row["red"]["sha256"]=t.sha(saved);f.refresh()
  assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True;print("PASS genuine restored complete proof positive")
  if missed:break
 if missed:raise AssertionError("generic bare Exception still qualifies as behavioral red")
print("EXIT 0")
