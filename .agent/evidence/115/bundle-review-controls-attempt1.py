import contextlib, copy, importlib.util, io, json, os, shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load("reviewed_suite",ROOT/"tools/test_workflow_assurance.py")
b=load("frozen_naive",ROOT/".agent/evidence/115/naive-baseline-attempt3.py")
# Independent minimal controlled record oracle, external NIP4 typed ownership/history rules.
def owned(before,after,fields):
 if type(before) is not dict or type(after) is not dict or set(before)!=set(after):raise b.AssuranceError("record shape")
 leaves=set(fields)
 def check(x,y,p=""):
  if type(x) is not type(y):raise b.AssuranceError("typed value changed")
  if p=="/history" and p in leaves:
   if type(x) is not list or r.canonical(y[:len(x)])!=r.canonical(x):raise b.AssuranceError("history prefix")
   return
  if type(x) is dict:
   if set(x)!=set(y):raise b.AssuranceError("keys")
   for k in x:check(x[k],y[k],p+"/"+k.replace("~","~0").replace("/","~1"))
  elif type(x) is list:
   if r.canonical(x)!=r.canonical(y):raise b.AssuranceError("unowned list")
  elif p not in leaves and r.canonical(x)!=r.canonical(y):raise b.AssuranceError("unowned leaf")
 check(before,after);return True
class ControlledRecord:
 AssuranceError=b.AssuranceError
 assess_repository=staticmethod(b.assess_repository)
 compare_identity=staticmethod(b.compare_identity)
 verify_record_update=staticmethod(owned)
r.run_case("allow-owned-append",ControlledRecord)
print("PASS independently controlled typed-record implementation: complete allow-owned-append case recognizes correct allowed append and rejects type drift; fixture setup successful")
try:r.run_case("allow-owned-append",b)
except AssertionError as e:
 assert str(e)=="POLICY_ASSERTION: owned type change denied: invalid input accepted";print("PASS contrasting wrong-record control rejected at exact policy assertion")
else:raise AssertionError("wrong record control false pass")
with tempfile.TemporaryDirectory(prefix="nizam-review115-ownspot-") as temp:
 scratch=Path(temp)/"repo";subprocess.run(["git","clone","-q","--shared","--no-checkout",str(ROOT),str(scratch)],check=True)
 subprocess.run(["git","-C",str(scratch),"checkout","-q",r.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 shutil.copyfile(ROOT/"tools/test_workflow_assurance.py",scratch/"tools/test_workflow_assurance.py");r.ROOT=scratch
 with contextlib.redirect_stdout(io.StringIO()):r.scope(r.BASE)
 print("PASS own scope adversary setup: actual committed source baseline and clean positive")
 ignored=scratch/"reviewer-unknown.ignored";subprocess.run(["git","-C",str(scratch),"config","core.excludesfile",str(Path(temp)/"ignore")],check=True)
 (Path(temp)/"ignore").write_text("reviewer-unknown.ignored\n");ignored.write_text("unclassified source input\n")
 assert subprocess.run(["git","-C",str(scratch),"check-ignore",str(ignored)],capture_output=True).returncode==0
 try:r.scope(r.BASE)
 except AssertionError as e:
  assert str(e)=="POLICY_ASSERTION: unknown scope path reviewer-unknown.ignored";print("PASS own ignored-untracked adversary: exact unknown scope path rejected; actual ignored fixture verified")
 else:raise AssertionError("ignored unknown scope false pass")
 ignored.unlink()
 with contextlib.redirect_stdout(io.StringIO()):r.scope(r.BASE)
 print("PASS own adversary scratch restored positive")
print("EXIT 0")
