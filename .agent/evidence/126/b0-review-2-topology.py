"""Reviewer-owned group topology: supervisor is not group leader."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

m = runpy.run_path('tools/test_runtime_session.py')
with tempfile.TemporaryDirectory(prefix='n126-independent-') as home:
    base = Path(home); candidate = base / 'candidate'
    stub = candidate / 'tools/fixtures/runtime_session/stub_runtime.py'
    stub.parent.mkdir(parents=True); stub.write_text('import time\ntime.sleep(30)\n')
    session = m['Session'](base, candidate=candidate); session.directory.mkdir(parents=True)
    supervisor = base / 'supervisor.py'
    supervisor.write_text('''import fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
d=Path(sys.argv[1]); f=(d/'supervisor.lock').open('a'); fcntl.flock(f,fcntl.LOCK_EX)
child=subprocess.Popen([sys.executable,sys.argv[2]])
def stop(*args): raise SystemExit
signal.signal(signal.SIGTERM,stop)
try:
 (d/'controller.json').write_text(json.dumps({'supervisor_pid':os.getpid(),'child_pid':child.pid,'supervisor_pgid':os.getpgrp()}))
 time.sleep(30)
finally:
 if child.poll() is None: child.terminate()
 child.wait(timeout=2)
''')
    # The launcher remains in the group but owns no session resources.
    launcher = subprocess.Popen([sys.executable, '-c', 'import subprocess,sys,time; p=subprocess.Popen(sys.argv[1:]); time.sleep(30)',
        sys.executable, str(supervisor), str(session.directory), str(stub)], start_new_session=True)
    meta = None
    try:
        def metadata():
            try:
                return json.loads((session.directory / 'controller.json').read_text())
            except (FileNotFoundError, ValueError):
                return None
        meta = m['wait_for'](metadata, 'independent group topology ready')
        m['wait_for'](lambda: session.runs_stub(meta['child_pid']), 'child exec observed')
        assert meta['supervisor_pgid'] == launcher.pid != meta['supervisor_pid']
        session.remember(); session.cleanup()
        assert launcher.poll() is None, 'cleanup killed unrelated group member'
        for key in ('supervisor_pid', 'child_pid'):
            m['wait_for'](lambda: not m['process_token'](meta[key]), 'owned process stopped')
        print('PASS nonleader supervisor accepted; owned supervisor/child stopped; unrelated live group leader survived')
    finally:
        session.cleanup()
        if launcher.poll() is None:
            launcher.terminate()
        launcher.wait(timeout=2)
