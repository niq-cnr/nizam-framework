import sys,tempfile,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import test_start_path as t
def git(r,*a):
 p=subprocess.run(["git","-C",str(r),*a],capture_output=True,text=True);assert p.returncode==0,p.stderr;return p
def case(schema):
 with tempfile.TemporaryDirectory(prefix="r02-evaluator-baseline-") as d:
  r=Path(d);git(r,"init");git(r,"config","user.name","diagnostic");git(r,"config","user.email","diagnostic@example.invalid")
  target="schema/demo.json" if schema else "app.py"
  (r/target).parent.mkdir(parents=True,exist_ok=True);(r/target).write_text("initial\n");(r/"notes.txt").write_text("original\n");git(r,"add",".");git(r,"commit","-m","fixture")
  ident="diag"
  t.write(r,".agent/evidence/diag-cause.json",t.cause(ident));t.write(r,".agent/evidence/diag-scope.json",t.scope(ident,[target],"c1" if schema else None))
  if schema:t.write(r,".agent/contracts/c1.json",t.contract("approved",[target]))
  else:(r/"notes.txt").write_text("inherited\n")
  b=t.run(r,"begin","bugfix","--id",ident);assert b.returncode==0,b.stderr
  (r/target).write_text("repaired\n")
  if not schema:(r/"notes.txt").write_text("mutated after begin\n")
  ep=".agent/evidence/diag-output.txt";(r/ep).write_text("diagnostic fixture output\n");t.write(r,".agent/qa/diag.json",t.qa(ident,ep))
  q=t.run(r,"done","bugfix","--id",ident)
  print(json.dumps({"case":"F1-approved-schema" if schema else "F2-inherited-tracked-mutated","diagnostic_only":False,"expected_exit":0 if schema else 1,"observed_exit":q.returncode,"stdout":q.stdout,"stderr":q.stderr}))
  assert q.returncode==(0 if schema else 1),"repair regression"
case(True)
case(False)
