import argparse, datetime, hashlib, json, os, subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument("--ids",nargs="+",required=True);ap.add_argument("--attempt",type=int,default=1);args=ap.parse_args()
root=Path.cwd();base=Path(".agent/evidence/NIZAM-R02-COMPLETION")
contract=Path(".agent/contracts/NIZAM-R02-COMPLETION.json");document=json.loads(contract.read_text())
assert document["status"]=="approved" and document["implementation_hold"]["active"] is False
for row in document["verification"]:
 if row["id"] not in args.ids: continue
 step="generator-"+row["id"].lower();out=base/(step+f"-{args.attempt:02d}");out.mkdir()
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path("tools/start_path.py"),Path("tools/test_start_path.py"))}
 argv=["python3",".nizam/tools/start_path.py","capture","--id","NIZAM-R02-COMPLETION","--step",step,"--attempt",str(args.attempt),"--output-dir",str(out),"--root",".","--","bash","-c",row["command"]]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (out/"capture-command.stdout.json").open("xb") as stdout,(out/"capture-command.stderr.txt").open("xb") as stderr:
  proc=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
 result={"verification_id":row["id"],"argv":argv,"cwd":str(root),"started_at":started,"completed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit_code":proc.returncode,"contract_sha256":hashlib.sha256(contract.read_bytes()).hexdigest(),"source_before_sha256":before,"source_after_sha256":{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before},"capture_stdout":str(out/"capture-command.stdout.json"),"capture_stderr":str(out/"capture-command.stderr.txt")}
 with (out/"execution.json").open("x") as f:json.dump(result,f,indent=2);f.write("\n")
 assert result["source_before_sha256"]==result["source_after_sha256"],"candidate changed during verification"
 print(json.dumps({"id":row["id"],"exit":proc.returncode,"record":str(out/"execution.json")}),flush=True)
 if proc.returncode:
  try:
   capture=json.loads((out/"capture-command.stdout.json").read_text())
   print(Path(capture["stderr"]["path"]).read_text(),flush=True)
  except (ValueError,KeyError): print((out/"capture-command.stderr.txt").read_text(),flush=True)
  raise SystemExit(proc.returncode)
