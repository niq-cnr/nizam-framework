"""Independent QA: reject a proof symlink even when its bytes/hash remain valid."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/118/'
spec = importlib.util.spec_from_file_location('qa_assurance', ROOT / 'tools/workflow_assurance.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
good = json.loads((ROOT / (E + 'prerequisite20.json')).read_text())
assert api.verify_foundation_ready(ROOT, good) is True
print('PASS actual candidate positive control')
with tempfile.TemporaryDirectory(prefix='nizam118-qa-proof-link-') as scratch:
    repo = Path(scratch) / 'repo'
    subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(ROOT), str(repo)], check=True)
    paths = set(good['source_sha256']) | set(good['runtime_sha256']) | set(good['historical_sha256'])
    paths |= {E + 'source-candidate.json', E + 'prerequisite20.json'} | {row['evidence'] for row in good['checks']}
    for path in paths:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    assert api.verify_foundation_ready(repo, good) is True
    print('PASS isolated identical proof control')
    row = good['checks'][0]
    proof = repo / row['evidence']
    saved = proof.read_bytes()
    destination = Path(scratch) / 'same-proof-outside-repository.txt'
    destination.write_bytes(saved)
    try:
        proof.unlink()
        proof.symlink_to(destination)
        assert hashlib.sha256(proof.read_bytes()).hexdigest() == row['sha256']
        try:
            api.verify_foundation_ready(repo, good)
        except api.AssuranceError as exc:
            assert 'symlink' in str(exc), str(exc)
            print('PASS correctly hashed proof redirected outside repository rejected:', str(exc))
        else:
            raise AssertionError('Redirected evidence was accepted')
    finally:
        if proof.is_symlink():
            proof.unlink()
        proof.write_bytes(saved)
    assert api.verify_foundation_ready(repo, good) is True
    print('PASS restored regular proof control')
assert api.verify_foundation_ready(ROOT, good) is True
print('PASS original candidate remains ready; no source, installed, or lifecycle mutation')
