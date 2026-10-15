"""Capture authorized final read-only inspections and whole-feature measurement."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/122'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
commands = [('final-static', [sys.executable, '.agent/evidence/122/modeb2-static.py']), ('final-seal', [sys.executable, '.agent/evidence/122/modeb2-final-seal.py']), ('final-scope', [sys.executable, '.agent/evidence/scope-budget-014/measure.py', '--range', '122=3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03..' + revision, '--files'])]
for label, argv in commands:
    p = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True)
    prefix = 'modeb2-' + label
    (E / (prefix + '.stdout')).write_bytes(p.stdout); (E / (prefix + '.stderr')).write_bytes(p.stderr)
    result = dict(argv=argv, cwd=str(ROOT), PYTHONDONTWRITEBYTECODE='1', actual_exit=p.returncode, exercised_revision=revision, stdout='.agent/evidence/122/' + prefix + '.stdout', stderr='.agent/evidence/122/' + prefix + '.stderr', stdout_sha256=hashlib.sha256(p.stdout).hexdigest(), stderr_sha256=hashlib.sha256(p.stderr).hexdigest(), api_calls=0)
    (E / (prefix + '.execution.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(label, p.returncode)
    if p.returncode: raise SystemExit(p.returncode)
