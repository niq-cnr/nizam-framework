(progn (sb-ext:run-program "/usr/bin/python3" (list "-c" "import json, os, signal, time
from pathlib import Path
os.setpgid(0, os.getpgid(os.getppid()))
signal.signal(signal.SIGTERM, signal.SIG_IGN)
ready=Path('/home/cnross/.tmp/nizam-129-group-native-qualification1-j1lnd8du/private-native-718ph73x/group-ready-c798151fce6eb9f1334b9cdece4bf423'); pulse=Path('/home/cnross/.tmp/nizam-129-group-native-qualification1-j1lnd8du/private-native-718ph73x/group-pulse-c798151fce6eb9f1334b9cdece4bf423')
ready.write_text(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'pgid':os.getpgid(0),'nonce':'c798151fce6eb9f1334b9cdece4bf423','operation_id':'qualification-group-1'}))
end=time.monotonic()+45; count=0
while time.monotonic()<end:
 count+=1; tmp=pulse.with_suffix('.tmp'); tmp.write_text(str(count)); tmp.replace(pulse); time.sleep(.02)
") :search nil :wait nil :input nil :output nil :error nil) 42)
