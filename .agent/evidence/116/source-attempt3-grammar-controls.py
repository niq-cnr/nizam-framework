"""Generator architecture selfchecks; only private parser fixtures are mutated."""
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
api = load('actual_source3', ROOT / 'tools/workflow_assurance.py')
actual_bundle = api.parse_json((ROOT / '.agent/evidence/116/acceptance-bundle.json').read_bytes())
actual_review = api.parse_json((ROOT / '.agent/validator/116-test-bundle-review.json').read_bytes())
assert api.verify_acceptance_bundle(ROOT, actual_bundle, actual_review) is True
print('PASS genuine full actual project bundle: all five setup/positive/red triples, immutable inputs and review')
markers = (
    'SETUP_OR_UNRELATED_ERROR: RuntimeError: unrelated fixture setup failure',
    'RuntimeError: unrelated exception', 'Exception: unrelated exception',
    'Error: unrelated error', 'BaseException: unrelated failure',
    'builtins.Exception: qualified unrelated exception', 'package.CustomError: custom error',
    'AssertionError: unrelated assertion', 'SystemExit: unrelated exit',
    'KeyboardInterrupt: interrupted setup', 'GeneratorExit: stopped setup',
    'StopIteration: unrelated iterator failure', 'StopAsyncIteration: unrelated async failure',
    'Traceback (most recent call last):', 'command not found',
    'unsupported producer output',
)
count = 0
with tempfile.TemporaryDirectory(prefix='nizam116-generator-grammar-controls-') as scratch:
    fixture = runner.BundleFixture(scratch)
    assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
    print('PASS valid complete real-Git parser fixture; later record-only HEAD supported')
    fixture.transition()
    assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
    for stage in ('setup', 'positive', 'red'):
        row = fixture.row('reject-setup-as-red'); proof = row[stage]; path = proof['path']
        original = (fixture.root / path).read_bytes()
        for channel in ('stdout', 'stderr'):
            for marker in markers:
                text = original.decode()
                if channel == 'stdout': text = text.replace('\nSTDERR:\n', '\n' + marker + '\nSTDERR:\n')
                else: text += marker + '\n'
                try:
                    fixture.write(path, text.encode()); proof['sha256'] = runner.sha(text.encode()); fixture.refresh()
                    try: api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review)
                    except api.AssuranceError as exc:
                        assert str(exc) == 'setup/transport failure cannot satisfy proof', str(exc)
                    else: raise AssertionError('FALSE_PASS: ' + stage + ' ' + channel + ' ' + marker)
                    count += 1
                finally:
                    fixture.write(path, original); proof['sha256'] = runner.sha(original); fixture.refresh()
                assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
        print('PASS ' + stage + ' producer-marker/bare/subclass/base-exception/traceback/unknown grammar rejects and restored positives')
    row = fixture.row('reject-setup-as-red'); proof = row['red']; path = proof['path']
    original = (fixture.root / path).read_bytes(); old_command = proof['command']
    command = old_command + ' --metadata-path ExampleException/SomeError.py'
    text = original.decode().replace('COMMAND: ' + old_command, 'COMMAND: ' + command)
    try:
        fixture.write(path, text.encode()); proof.update(command=command, sha256=runner.sha(text.encode())); fixture.refresh()
        assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
        print('PASS metadata command path containing Exception/Error does not enter output classifier')
    finally:
        fixture.write(path, original); proof.update(command=old_command, sha256=runner.sha(original)); fixture.refresh()
    diagnostic = proof['diagnostic']
    text = original.decode().replace(diagnostic + '\n', '').replace('\nSTDERR:\n', '\nSTDERR:\n' + diagnostic + '\n')
    try:
        fixture.write(path, text.encode()); proof['sha256'] = runner.sha(text.encode()); fixture.refresh()
        assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
        print('PASS permitted intended policy assertion in stderr remains valid')
    finally:
        fixture.write(path, original); proof['sha256'] = runner.sha(original); fixture.refresh()
    assert api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review) is True
assert api.verify_acceptance_bundle(ROOT, actual_bundle, actual_review) is True
print('PASS ' + str(count) + ' targeted grammar rejects with restored positives; actual project sealed proof bytes unchanged')
print('Generator selfcheck only; no independent QA or lifecycle completion claim')
