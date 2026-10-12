"""Reject a forged semantic candidate in an owned overlay; never mutate real inputs."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/112/'
spec = importlib.util.spec_from_file_location('independent112checker', ROOT / E / 'check_112.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
original = (ROOT / E / 'semantic-review.json').read_bytes()
child = '''import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('spot112', sys.argv[1])
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
try:
    c.semantic_review(c.View(Path(sys.argv[2]) if sys.argv[2] else None))
except c.Rejection as rejection:
    print('FAIL112 ' + str(rejection))
    sys.exit(1)
'''
def execute(overlay, expected):
    result = subprocess.run([sys.executable, '-c', child, str(ROOT / E / 'check_112.py'),
                             str(overlay) if overlay else ''], capture_output=True, text=True)
    print(result.stdout, end='')
    print(result.stderr, end='')
    print('CHILD ACTUAL EXIT: ' + str(result.returncode))
    assert result.returncode == expected, result
    return result
with tempfile.TemporaryDirectory(prefix='qa112-own-semantic-candidate-', dir=ROOT / E) as directory:
    overlay = Path(directory)
    target = overlay / E / 'semantic-review.json'
    target.parent.mkdir(parents=True)
    execute(None, 0)
    forged = json.loads(original)
    forged['candidate_sha'] = '0' * 40
    target.write_text(json.dumps(forged, indent=2) + '\n')
    rejection = execute(overlay, 1)
    assert 'FAIL112 semantic-binding: exact candidate/source/seal' in rejection.stdout
    print('INTENDED MUTANT REJECTED: semantic-binding; actual child failure exit 1')
    target.write_bytes(original)
    execute(overlay, 0)
    assert (ROOT / E / 'semantic-review.json').read_bytes() == original
    print('RESTORED POSITIVE ACCEPTED; real semantic receipt unchanged')
print('OWN ADVERSARIAL PASS: candidate identity falsification rejected independently of source markers')
