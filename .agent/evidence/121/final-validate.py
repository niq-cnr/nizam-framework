"""Root final integration validation after lifecycle/docs changes; no case-bank rerun."""
import hashlib
import json
import os
import pathlib
import stat
import subprocess

ROOT = pathlib.Path.cwd(); E = ROOT / '.agent/evidence/121'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
paths = subprocess.check_output(['git', 'ls-files', '-z', 'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.nizam/', 'schema/']).decode().rstrip('\0').split('\0')
def snapshot(): return {p: {'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest(), 'filesystem_mode': stat.S_IMODE((ROOT / p).stat().st_mode)} for p in paths}
before = snapshot(); records = []
commands = [('default', ['bash', 'tools/validate.sh']), ('payload', ['bash', 'tools/validate.sh', '--payload']), ('maintained-diff', ['git', 'diff', '--check', 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb..HEAD', '--', '.', ':(exclude).agent/evidence/**'])]
for label, argv in commands:
    result = subprocess.run(argv, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': 'C'})
    record = {'argv': argv, 'cwd': str(ROOT), 'environment': {'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': 'C'}, 'exercised_revision': revision, 'actual_exit': result.returncode}
    for stream in ('stdout', 'stderr'):
        data = getattr(result, stream); path = E / ('final-validation1-' + label + '.' + stream + '.txt'); path.write_bytes(data)
        record[stream] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}
    records.append(record)
    (E / 'final-validation1-records.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 0, label
after = snapshot(); assert before == after
(E / 'final-validation1-preservation.json').write_text(json.dumps({'revision': revision, 'before': before, 'after': after}, indent=2) + '\n')
(E / 'final-validation1-result.json').write_text(json.dumps({'role': 'Root', 'actual_exit': 0, 'passed': True, 'exercised_revision': revision, 'commands': 3, 'installed_count': sum(p.startswith('.nizam/') for p in paths), 'protected_before_after_equal': True}, indent=2) + '\n')
print('PASS both compliance modes/maintained diff; Source/test/schema/installed preserved')
