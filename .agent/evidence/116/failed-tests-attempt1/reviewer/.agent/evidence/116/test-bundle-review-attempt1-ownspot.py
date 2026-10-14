import contextlib,importlib.util,io,json,shutil,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];path=ROOT/".agent/evidence/116/scope-guard.py"
s=importlib.util.spec_from_file_location("review_guard",path);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
with tempfile.TemporaryDirectory(prefix="nizam116-review-type-history-") as temp:
 scratch=Path(temp)/"repo";subprocess.run(["git","clone","-q","--shared","--no-checkout",str(ROOT),str(scratch)],check=True)
 subprocess.run(["git","-C",str(scratch),"checkout","-q",g.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 tracked=g.tree_entries(g.APPROVED)
 for path in [ROOT/"tools/test_workflow_assurance.py", *[p for p in (ROOT/".agent/evidence/116").rglob("*") if p.is_file()]]:
  relative=path.relative_to(ROOT).as_posix()
  if relative in tracked and relative!="tools/test_workflow_assurance.py":continue
  target=scratch/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
 g.ROOT=scratch
 with contextlib.redirect_stdout(io.StringIO()):g.scope(g.BASE)
 print("PASS ownspot setup: real immutable clone, unchanged115Source, current116canonical in-progress, positive scope")
 target=scratch/".agent/run_state.json";saved=target.read_bytes();x=json.loads(saved)
 assert x["history"][331]["ga_declared"] is True
 x["history"][331]["ga_declared"]=1;target.write_text(json.dumps(x))
 falsepass=False
 try:
  with contextlib.redirect_stdout(io.StringIO()):g.scope(g.BASE)
 except AssertionError as exc:print("REJECT",str(exc))
 else:falsepass=True;print("FALSE_PASS: history[331].ga_declared True(bool) changed to1(int), exact prior history guard accepted; actual scope exit0")
 finally:target.write_bytes(saved)
 with contextlib.redirect_stdout(io.StringIO()):g.scope(g.BASE)
 print("PASS restored valid history; all shared Source/bundle/proof files remain unchanged")
 sys.exit(1 if falsepass else 0)
