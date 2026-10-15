"""One independent QA122 check: duplicate keys in a freshly pinned authority."""
import copy
import importlib.util
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('qa122_test_fixture', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
api = t.load_api()
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
with tempfile.TemporaryDirectory(prefix='nizam122-qa1-duplicate-authority-') as parent:
    f = t.FailureFixture(api, parent)
    original = copy.deepcopy(f.policy)
    def observe(deny=False):
        inputs = copy.deepcopy((f.request, f.policy, f.state, f.authority, f.capture, f.evidence))
        files = f.files()
        try:
            result = api.route_failed_attempt(f.root, f.request, policy=f.policy)
        except api.AssuranceError as exc:
            assert deny and 0 < len(str(exc)) <= 1000, str(exc)
            assert 'duplicate JSON key: approved' in str(exc), str(exc)
            print('EXPECTED_REJECTION ' + str(exc))
            result = None
        else:
            assert not deny, 'ambiguous duplicate-key authority accepted'
            assert result['outcome'] == 'failed' and result['route'] == 'infrastructure-diagnosis'
            assert result['attempts_used'] == 1 and result['limit'] == 3 and result['remaining'] == 2
        assert inputs == (f.request, f.policy, f.state, f.authority, f.capture, f.evidence)
        assert files == f.files(), 'API changed fixture bytes or full filesystem modes'
        return result
    baseline = observe()
    raw = t.canonical(f.authority)
    needle = b'"approved":true'
    assert raw.count(needle) == 1
    duplicate = raw.replace(needle, b'"approved":true,"approved":false', 1)
    f.policy['authority_ref'] = f.pin_new('duplicate-approved-authority', duplicate)
    observe(True)
    f.policy = original
    assert observe() == baseline, 'restored original routing changed'
    print('PASS independent duplicate-key authority baseline/rejection/restored; inputs/files/full modes preserved')
