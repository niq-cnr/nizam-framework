import sys,tempfile,subprocess,json,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import test_start_path as t
def git(r,*a):
 p=subprocess.run(["git","-C",str(r),*a],capture_output=True,text=True);assert p.returncode==0,p.stderr
with tempfile.TemporaryDirectory(prefix="r02-evaluator-adversarial-") as d:
 r=Path(d);git(r,"init");git(r,"config","user.name","evaluator");git(r,"config","user.email","evaluator@example.invalid")
 (r/"app.py").write_text("original\n");(r/"external-link").symlink_to("/nonexistent-r02-evaluator-target-before");git(r,"add",".");git(r,"commit","-m","fixture")
 (r/"external-link").unlink();(r/"external-link").symlink_to("/nonexistent-r02-evaluator-target-inherited")
 t.write(r,".agent/evidence/extra-cause.json",t.cause("extra"));t.write(r,".agent/evidence/extra-scope.json",t.scope("extra",["app.py"]))
 b=t.run(r,"begin","bugfix","--id","extra");assert b.returncode==0,b.stderr
 base=json.loads((r/".agent/evidence/extra-base.json").read_text());observed=base["inherited_observations"]["external-link"]["worktree"];assert observed=={"kind":"symlink","target":"/nonexistent-r02-evaluator-target-inherited"},observed
 (r/"app.py").write_text("repaired\n");ep=".agent/evidence/extra-output.txt";(r/ep).write_text("actual evaluator assertions\n");t.write(r,".agent/qa/extra.json",t.qa("extra",ep))
 unchanged=t.run(r,"done","bugfix","--id","extra");assert unchanged.returncode==0,unchanged.stderr
 (r/"external-link").unlink();(r/"external-link").symlink_to("/nonexistent-r02-evaluator-target-mutated")
 changed=t.run(r,"done","bugfix","--id","extra");assert changed.returncode==1 and "external-link" in changed.stderr,(changed.returncode,changed.stderr)
 print(json.dumps({"case":"inherited dangling absolute-target symlink no-follow","unchanged_exit":unchanged.returncode,"mutated_exit":changed.returncode,"mutated_diagnostic":changed.stderr,"literal_observation":observed,"result":"pass"}))
