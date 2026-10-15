"""Capture exactly one frozen compatibility command, preserving its actual exit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path.cwd()
E = ROOT / '.agent/evidence/122'
argv = [sys.executable, '.agent/evidence/122/compatibility1-probe.py']
pins = {}
for name in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/122.json', '.agent/evidence/122/compatibility1-probe.py', '.agent/evidence/122/compatibility1-capture.py'):
    p = ROOT / name
    pins[name] = dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), mode=p.lstat().st_mode,
        git_blob=subprocess.check_output(['git', 'rev-parse', 'HEAD:' + name]).decode().strip())
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
p = subprocess.run(argv, cwd=ROOT, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
(E / 'compatibility1-probe.stdout').write_bytes(p.stdout)
(E / 'compatibility1-probe.stderr').write_bytes(p.stderr)
(E / 'compatibility1-execution.json').write_text(json.dumps(dict(argv=argv, cwd=str(ROOT), revision=revision,
    environment={'PYTHONDONTWRITEBYTECODE': '1'}, expected_exit=0, actual_exit=p.returncode, pins=pins,
    stdout='.agent/evidence/122/compatibility1-probe.stdout', stderr='.agent/evidence/122/compatibility1-probe.stderr'), indent=2) + '\n')
print(p.stdout.decode(), end=''); print(p.stderr.decode(), end='', file=sys.stderr)
print('ACTUAL_OUTER_EXIT=' + str(p.returncode), flush=True)
raise SystemExit(p.returncode)
