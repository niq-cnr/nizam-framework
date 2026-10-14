import fcntl,json,os,subprocess,sys,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix="nizam126-lock-probe-") as d:
 p=Path(d)/"supervisor.lock"; f=p.open("a+"); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 child=subprocess.Popen([sys.executable,"-c","import os,sys; print(os.getpid(),flush=True); sys.stdin.buffer.read(1)"],pass_fds=(f.fileno(),),stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 try:
  child_pid=int(child.stdout.readline()); inode=str(p.stat().st_ino); f.close()
  rows=[x for x in Path("/proc/locks").read_text().splitlines() if x.split()[5].split(":")[-1]==inode]
  with p.open("a+") as other:
   try: fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB); held=False
   except BlockingIOError: held=True
  assert held and rows
  print(json.dumps({"acquirer_pid":os.getpid(),"inheriting_child_pid":child_pid,"lock_still_held_after_parent_fd_close":held,"proc_lock_rows":rows}))
 finally: child.communicate("x",timeout=5)
