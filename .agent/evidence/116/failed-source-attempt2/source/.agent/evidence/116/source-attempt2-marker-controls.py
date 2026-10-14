"""Generator selfcheck of the frozen producer error grammar, scratch fixtures only."""
import importlib.util
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[3]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

runner = load('frozen_runner', ROOT / 'tools/test_workflow_assurance.py')
api = load('actual_source', ROOT / 'tools/workflow_assurance.py')
with tempfile.TemporaryDirectory(prefix='nizam116-generator-marker-controls-') as scratch:
    fixture = runner.BundleFixture(scratch)
    assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
    print('PASS selfcheck setup: actual real Git fixture and valid complete bundle')
    for stage, marker in (
        ('red', 'SETUP_OR_UNRELATED_ERROR: RuntimeError: unrelated fixture setup failure'),
        ('setup', 'SETUP_OR_UNRELATED_ERROR: RuntimeError: setup failure'),
        ('positive', 'SETUP_OR_UNRELATED_ERROR: ValueError: unrelated positive failure'),
        ('red', 'RuntimeError: unrelated exception without the producer wrapper'),
        ('red', 'Traceback (most recent call last):'),
    ):
        row = fixture.row('reject-setup-as-red')
        proof = row[stage]
        path = proof['path']
        original = (fixture.root / path).read_bytes()
        data = original + marker.encode() + b'\n'
        try:
            fixture.write(path, data)
            proof['sha256'] = runner.sha(data)
            fixture.refresh()
            try:
                api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review)
            except api.AssuranceError as exc:
                assert 'setup/transport failure cannot satisfy proof' in str(exc), str(exc)
                print('PASS targeted rejection: ' + stage + ' ' + marker)
            else:
                raise AssertionError('FALSE_PASS: explicit setup/unrelated error accepted')
        finally:
            fixture.write(path, original)
            proof['sha256'] = runner.sha(original)
            fixture.refresh()
        assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
        print('PASS restored legitimate setup/positive/intended behavioral red')
print('PASS Generator marker selfcheck only; no independent QA or real proof mutation')
