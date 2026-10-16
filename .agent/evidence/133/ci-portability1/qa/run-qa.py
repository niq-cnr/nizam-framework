"""Operational fresh-QA sequence; no product or assertion changes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

repo = Path('/home/cnross/.tmp/nizam-133-portability-freshqa1')
out = Path('/home/cnross/.tmp/nizam-133-portability-freshqa1-raw')
driver = repo / '.agent/evidence/123/fresh-qa-capture1.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest() == 'e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0'
assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == 'ab2ad3d6a352d5482867bcd0d06341843708d921'
sentinel = out / 'outside-sentinel.txt'
with sentinel.open('x') as target:
    target.write('Fresh Evaluator preservation sentinel; leave unchanged.\n')
interpreters = ['/usr/bin/python3.12', '/home/cnross/.local/share/uv/python/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13', '/home/cnross/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/bin/python3.14']
selectors = ['real-git-count-reduction', 'semantic-equivalence', 'fresh-mutations', 'literal-paths-and-modes']
runtime_code = 'import ast,hashlib,json,pathlib,platform,sys; print(json.dumps(dict(version=platform.python_version(),executable=sys.executable,executable_sha256=hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),ast_file=ast.__file__,ast_sha256=hashlib.sha256(pathlib.Path(ast.__file__).read_bytes()).hexdigest()),sort_keys=True))'
commands = []
for index, interpreter in enumerate(interpreters):
    commands.append(('runtime-' + str(index), [interpreter, '-c', runtime_code]))
    for selector in selectors:
        commands.append(('python-' + str(index) + '-' + selector, [interpreter, 'tools/test_receipt_candidate_batching.py', '--check', selector]))
commands += [('guard-controls', [interpreters[0], str(out / 'controls.py'), str(repo), str(out), 'guards']), ('default-four', [interpreters[2], 'tools/test_receipt_candidate_batching.py']), ('validate-default', ['bash', 'tools/validate.sh']), ('validate-payload', ['bash', 'tools/validate.sh', '--payload']), ('self-governance', [interpreters[0], '.github/scripts/verify_self_governance.py']), ('self-governance-negatives', [interpreters[0], '.github/scripts/test_self_governance.py']), ('adversarial-extra', [interpreters[0], str(out / 'controls.py'), str(repo), str(out), 'extra'])]
for name, command in commands:
    argv = [interpreters[0], str(driver), '--repo', str(repo), '--output', str(out), '--name', name, '--sentinel', str(sentinel), '--expected-exit', '0', '--timeout', '600', '--'] + command
    result = subprocess.run(argv, capture_output=True)
    (out / (name + '.capture.stdout.txt')).write_bytes(result.stdout)
    (out / (name + '.capture.stderr.txt')).write_bytes(result.stderr)
    print(name + ': capture_exit=' + str(result.returncode), flush=True)
    if result.returncode:
        sys.exit(result.returncode)
print('ALL TARGETED QA COMMANDS COMPLETED', flush=True)
