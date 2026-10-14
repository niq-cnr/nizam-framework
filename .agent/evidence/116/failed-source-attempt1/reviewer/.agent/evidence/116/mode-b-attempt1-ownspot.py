import importlib.util,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=load("frozen_test",ROOT/"tools/test_workflow_assurance.py");a=load("actual_source",ROOT/"tools/workflow_assurance.py")
with tempfile.TemporaryDirectory(prefix="nizam116-modeb-generic-error-") as temp:
 f=t.BundleFixture(temp);assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS ownspot setup: actual real Git fixture, valid complete bundle/current bytes, positive accepted")
 row=f.row("reject-setup-as-red");path=row["red"]["path"];original=(f.root/path).read_bytes();data=original+b"SETUP_OR_UNRELATED_ERROR: RuntimeError: unrelated fixture setup failure\n"
 f.write(path,data);row["red"]["sha256"]=t.sha(data);f.refresh()
 missed=False
 try:a.verify_acceptance_bundle(f.root,f.bundle,f.review)
 except a.AssuranceError as exc:print("PASS explicit generic setup/unrelated marker rejected:",str(exc))
 else:missed=True;print("FALSE_PASS: redproof retains intended POLICY_ASSERTION andEXIT1 but explicit baseline-driver SETUP_OR_UNRELATED_ERROR RuntimeError inSTDERR is accepted")
 f.write(path,original);row["red"]["sha256"]=t.sha(original);f.refresh();assert a.verify_acceptance_bundle(f.root,f.bundle,f.review) is True
 print("PASS restored legitimate complete bundle accepted; real delivered Source/test/helper/proofs unchanged")
 if missed:raise AssertionError("generic setup/unrelated error qualified as intended red")
