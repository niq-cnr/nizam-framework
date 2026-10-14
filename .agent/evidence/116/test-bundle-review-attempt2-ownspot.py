import contextlib,importlib.util,io,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location("scope_typed_review",ROOT/".agent/evidence/116/scope-guard.py");g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
with tempfile.TemporaryDirectory(prefix="nizam116-review2-typed-") as temp:
 scratch=Path(temp)/"repo";subprocess.run(["git","clone","-q","--shared","--no-checkout",str(ROOT),str(scratch)],check=True)
 subprocess.run(["git","-C",str(scratch),"checkout","-q",g.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 tracked=g.tree_entries(g.APPROVED)
 for path in [ROOT/"tools/test_workflow_assurance.py", *[p for p in (ROOT/".agent/evidence/116").rglob("*") if p.is_file()]]:
  relative=path.relative_to(ROOT).as_posix()
  if relative in tracked and relative!="tools/test_workflow_assurance.py":continue
  target=scratch/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
 g.ROOT=scratch;target=scratch/".agent/run_state.json";saved=target.read_bytes();before=json.loads(saved)
 with contextlib.redirect_stdout(io.StringIO()):g.scope(g.BASE)
 print("PASS independent genuine unchanged116 in-progress positive on real approved clone")
 assert before["history"][331]["ga_declared"] is True
 assert type(before["scope_budget"]["per_feature"][0]["actual"]) is int and before["scope_budget"]["per_feature"][0]["actual"]==1863
 for name,diagnostic in [("original-history-bool-int","exact prior history prefix types"),("related-budget-int-float","immutable115 measured entry/prefix exact types")]:
  x=json.loads(saved)
  if name=="original-history-bool-int":x["history"][331]["ga_declared"]=1
  else:x["scope_budget"]["per_feature"][0]["actual"]=1863.0
  target.write_text(json.dumps(x))
  try:g.scope(g.BASE)
  except AssertionError as exc:
   assert diagnostic in str(exc);print("PASS own targeted type rejection",name,str(exc))
  else:raise AssertionError("typed preserved boundary falsepass "+name)
  finally:target.write_bytes(saved)
  with contextlib.redirect_stdout(io.StringIO()):g.scope(g.BASE)
  print("PASS independently restored unchanged positive after",name)
print("EXIT 0")
