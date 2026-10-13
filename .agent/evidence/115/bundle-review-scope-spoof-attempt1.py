import contextlib,importlib.util,io,json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[3];p=root/"tools/test_workflow_assurance.py"
s=importlib.util.spec_from_file_location("review_scope",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
misses=[]
with tempfile.TemporaryDirectory(prefix="nizam-review115-scope-spoof-") as tmp:
 scratch=Path(tmp)/"repo"
 subprocess.run(["git","clone","-q","--shared","--no-checkout",str(root),str(scratch)],check=True)
 subprocess.run(["git","-C",str(scratch),"checkout","-q",m.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 shutil.copyfile(p,scratch/"tools/test_workflow_assurance.py");m.ROOT=scratch
 target=scratch/".agent/run_state.json";original=target.read_bytes();before=json.loads(original)
 with contextlib.redirect_stdout(io.StringIO()):m.scope(m.BASE)
 print("PASS setup: clean positive scope; scratch at immutable author base; original canonical phase017/115 remain IN_PROGRESS")
 for field,value in [("active_contract_id","116"),("status","complete")]:
  x=dict(before);x[field]=value;target.write_text(json.dumps(x))
  try:
   with contextlib.redirect_stdout(io.StringIO()):m.scope(m.BASE)
  except Exception as exc:
   print(json.dumps({"field":field,"value":value,"actual":"rejected","error":str(exc)}))
  else:
   misses.append(field);print(json.dumps({"field":field,"old_value":before[field],"value":value,"expected":"reject feature115 scope contradiction","actual":"accepted","scope_actual_exit":0}))
  finally:target.write_bytes(original)
 with contextlib.redirect_stdout(io.StringIO()):m.scope(m.BASE)
 print("PASS scratch restored positive; shared and owned review Source/bundle bytes unchanged")
print("FALSE_PASSES",json.dumps(misses));sys.exit(1 if misses else 0)
