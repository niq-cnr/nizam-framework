import contextlib, copy, importlib.util, io, json, os, shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load("reviewed_suite",ROOT/"tools/test_workflow_assurance.py")
b=load("frozen_naive",ROOT/".agent/evidence/115/recovery-naive-baseline-attempt1.py")
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
h=load("corrected_scope",ROOT/".agent/evidence/115/recovery-scope-guard.py")
with tempfile.TemporaryDirectory(prefix="nizam-review115-recovery-controls-") as temp:
 scratch=Path(temp)/"repo";subprocess.run(["git","clone","-q","--shared","--no-checkout",str(ROOT),str(scratch)],check=True)
 subprocess.run(["git","-C",str(scratch),"checkout","-q",h.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for path in ("tools/test_workflow_assurance.py",".agent/evidence/115/recovery-scope-guard.py"):
  (scratch/path).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,scratch/path)
 h.ROOT=scratch
 with contextlib.redirect_stdout(io.StringIO()):h.scope(h.BASE)
 print("PASS independent clean pre-source canonical115 positive")
 target=scratch/".agent/run_state.json";saved=target.read_bytes();before=json.loads(saved)
 for field,value,diagnostic in [("active_contract_id","116","active_contract_id/current_feature115"),("status","complete","run.status must match canonical017")]:
  x=dict(before);x[field]=value;target.write_text(json.dumps(x))
  try:h.scope(h.BASE)
  except AssertionError as exc:
   assert diagnostic in str(exc);print("PASS independent exact regression",field,value,str(exc))
  else:raise AssertionError("known falsepass persists "+field)
  finally:target.write_bytes(saved)
 with contextlib.redirect_stdout(io.StringIO()):h.scope(h.BASE)
 print("PASS independent restored pre-source positive")
 h.mock_delivered()
 with contextlib.redirect_stdout(io.StringIO()):h.scope(h.BASE)
 print("PASS independent delivered/in-progress structural fixture positive; no product implementation claimed")
 h.mock_completed();h._CONTROL_FIXTURE=scratch.resolve()
 with contextlib.redirect_stdout(io.StringIO()):h._scope(h.BASE)
 print("PASS independent private captured tuple positive with actual fixture Git revision/digests; no actual feature QA claimed")
 target=scratch/h.MODE_B;saved=target.read_bytes();obj=json.loads(saved);obj["source_sha256"]["tools/workflow_assurance.py"]="0"*64;target.write_text(json.dumps(obj))
 try:h._scope(h.BASE)
 except AssertionError as exc:
  assert "same assessed source bound to all closure receipts" in str(exc);print("PASS own additional adversary: wrong assessed-source digest in ModeB rejected at exact binding diagnostic",str(exc))
 else:raise AssertionError("wrong ModeB digest false pass")
 finally:target.write_bytes(saved)
 with contextlib.redirect_stdout(io.StringIO()):h._scope(h.BASE)
 print("PASS own closure digest adversary restored positive")
 h._CONTROL_FIXTURE=None
 try:h.scope(h.BASE)
 except AssertionError as exc:
  assert "mock receipts confined to private control scratch" in str(exc);print("PASS public interface rejects private closure mock labels")
 else:raise AssertionError("public mock admission")
print("EXIT 0")
