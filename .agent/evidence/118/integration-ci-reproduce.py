#!/usr/bin/python3
"""Reproduce checkout-depth failure without modifying acceptance inputs."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/118'
REVISION = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

def run(name, args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, env=ENV, capture_output=True)
    output = E / ('integration-ci-' + name + '.txt')
    assert not output.exists(), output
    output.write_bytes((f'COMMAND: {shlex.join(args)}\nCWD: {cwd}\nREVISION: {REVISION}\nEXIT: {result.returncode}\nSTDOUT:\n').encode() + result.stdout + b'\nSTDERR:\n' + result.stderr)
    print(name, result.returncode, result.stdout.decode(errors='replace')[-250:], result.stderr.decode(errors='replace')[-350:], flush=True)
    return result

assert run('failure', ['gh', 'run', 'view', '38520905278', '--repo', 'niq-cnr/nizam-framework', '--log-failed']).returncode == 0
with tempfile.TemporaryDirectory(prefix='nizam-ci-depth-', dir=ROOT.parent) as scratch:
    clone = Path(scratch) / 'checkout'
    assert run('clone-shallow', ['git', 'clone', '--depth', '1', ROOT.as_uri(), str(clone)]).returncode == 0
    shallow = run('shallow-state', ['git', 'rev-parse', '--is-shallow-repository'], clone)
    assert shallow.stdout.strip() == b'true'
    negative = run('shallow-default20', ['/usr/bin/python3', 'tools/test_workflow_assurance.py'], clone)
    assert negative.returncode != 0 and b'970ea233f77b4468105ddf6e401babbd0049d0b2' in negative.stderr
    assert run('fetch-full', ['git', 'fetch', '--unshallow', '--tags', 'origin', '+refs/heads/*:refs/remotes/origin/*'], clone).returncode == 0
    assert run('full-state', ['git', 'rev-parse', '--is-shallow-repository'], clone).stdout.strip() == b'false'
    ledger = json.loads((clone / '.agent/evidence/118/historical-runtime-inputs.json').read_text())
    for row in ledger['inputs']:
        data = subprocess.check_output(['git', 'show', row['revision'] + ':' + row['path']], cwd=clone)
        assert hashlib.sha256(data).hexdigest() == row['sha256']
    tag = subprocess.check_output(['git', 'rev-parse', 'refs/tags/' + ledger['tag'] + '^{commit}'], cwd=clone, text=True).strip()
    assert tag == ledger['tag_revision']
    candidate = json.loads((clone / '.agent/evidence/118/source-candidate.json').read_text())
    prerequisite = json.loads((clone / '.agent/evidence/118/prerequisite20.json').read_text())
    for key, value in candidate.items():
        assert prerequisite[key] == value
    actual_tree = subprocess.check_output(['git', 'rev-parse', candidate['revision'] + '^{tree}'], cwd=clone, text=True).strip()
    assert actual_tree == candidate['tree']
    print('Full clone: all 23 historical Git blobs, release tag, SourceC2/tree and prerequisite bindings verified', flush=True)
    assert run('full-default20', ['/usr/bin/python3', 'tools/test_workflow_assurance.py'], clone).returncode == 0
    assert run('full-readiness', ['/usr/bin/python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], clone).returncode == 0
print('PASS shallow failure reproduced; full-history default20 and readiness passed', flush=True)
