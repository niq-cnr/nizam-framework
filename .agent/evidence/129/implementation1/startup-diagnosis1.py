#!/usr/bin/env python3
"""One unchanged fixed-worker startup diagnosis; no acceptance or repair."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
output = Path(sys.argv[1]).resolve(strict=True)
assert root not in output.parents
source = root / 'tools/runtime_session.py'
spec = importlib.util.spec_from_file_location('candidate_controller', source)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
product_revision = 'ee1ce1dfb6b0f235c23eae439e00328645098c42'
for name in ('tools/runtime_session.py', 'tools/sbcl_session_loop.lisp'):
    assert (root/name).read_bytes() == subprocess.check_output(['git', 'show', product_revision + ':' + name], cwd=root)
scratch = output / 'private-runtime'
scratch.mkdir(mode=0o700)
session = scratch / 'session'
session.mkdir(mode=0o700)
init = {'type': 'init', 'generation': {'counter': 1, 'nonce': os.urandom(16).hex()}, 'directory': str(session) + '/'}
input_bytes = (controller.lisp_frame(init) + '\n').encode()
(output/'worker.stdin').write_bytes(input_bytes)
command = [shutil.which('sbcl'), '--noinform', '--no-sysinit', '--no-userinit', '--disable-debugger',
           '--script', str(root/'tools/sbcl_session_loop.lisp')]
read_fd, write_fd = os.pipe()
def child_fd3():
    os.dup2(write_fd, 3)
started = time.monotonic()
child = subprocess.Popen(command, start_new_session=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, pass_fds=tuple({write_fd, 3}), preexec_fn=child_fd3,
                         cwd=scratch, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
os.close(write_fd)
(output/'worker.started.json').write_text(json.dumps({'argv':command,'pid':child.pid,'cwd':str(scratch),
    'exercised_revision':revision,'product_revision':product_revision,'input_path':'worker.stdin'},indent=2)+'\n')
timed_out = False
try:
    stdout, stderr = child.communicate(input=input_bytes, timeout=6)
except subprocess.TimeoutExpired:
    timed_out = True
    os.killpg(child.pid, signal.SIGTERM)
    try:
        stdout, stderr = child.communicate(timeout=.25)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate(timeout=1)
protocol = bytearray()
while True:
    part = os.read(read_fd, 65537 - len(protocol))
    if not part:
        break
    protocol.extend(part)
    assert len(protocol) <= 65536
os.close(read_fd)
for name, data in [('stdout',stdout),('stderr',stderr),('protocol',bytes(protocol))]:
    (output/('worker.'+name)).write_bytes(data)
result = {'argv':command,'cwd':str(scratch),'pid':child.pid,'actual_exit':child.returncode,
          'timed_out':timed_out,'elapsed_seconds':time.monotonic()-started,'exercised_revision':revision,
          'product_revision':product_revision,'purpose':'Actual startup diagnosis only; no backend acceptance',
          'input_sha256':hashlib.sha256(input_bytes).hexdigest(),
          'streams':{name:{'path':'worker.'+name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
                     for name,data in [('stdout',stdout),('stderr',stderr),('protocol',bytes(protocol))]}}
(output/'worker.execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
print(stderr.decode(errors='replace'))
assert not timed_out, 'Unexpected startup diagnostic timeout'
