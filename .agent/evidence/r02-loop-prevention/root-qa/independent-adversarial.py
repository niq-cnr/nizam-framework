import sys,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,"tools")
import start_path as sp
with tempfile.TemporaryDirectory(prefix="nizam-loop-independent-") as tmp:
 root=Path(tmp);subprocess.run(["git","init","-q",str(root)],check=True)
 cap=sp.capture_command_evidence(root,task_id="repair",step="first",attempt=1,output_dir=root/".agent/evidence/one",argv=[sys.executable,"-c","print('original evidence')"])
 (root/cap["stdout"]["path"]).write_text("tampered evidence")
 sentinel=root/"unexpected"
 try:
  sp.capture_command_evidence(root,task_id="repair",step="renamed",attempt=1,output_dir=root/".agent/evidence/two",argv=[sys.executable,"-c",f"from pathlib import Path;Path({str(sentinel)!r}).touch()"])
 except sp.StartPathError as exc:
  assert "corrupt task capture history" in str(exc),str(exc)
 else: raise AssertionError("tampered relocated history accepted")
 assert not sentinel.exists(),"refused command executed"
 control=sp.capture_command_evidence(root,task_id="unrelated",step="control",attempt=1,output_dir=root/".agent/evidence/control",argv=[sys.executable,"-c","print('independent task')"])
 assert control["exit_code"]==0
print("PASS independent stream tamper refuses renamed-step dispatch; unrelated task remains eligible")
