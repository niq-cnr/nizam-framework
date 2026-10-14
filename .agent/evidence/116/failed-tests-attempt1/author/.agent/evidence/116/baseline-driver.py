"""Replays independently frozen positive/semantic-red operations on naive control.

Exit1 is reserved for a named wrong policy outcome. Setup and unrelated errors
exit2, never qualifying as baseline-red evidence.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
CONTROL = '.agent/evidence/116/naive-policy.py'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(data): return hashlib.sha256(data).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location('baseline_replay_module', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('setup','positive','red'), required=True)
    parser.add_argument('--case', required=True); parser.add_argument('--baseline', required=True)
    parser.add_argument('--operation', required=True); args = parser.parse_args()
    operation = json.loads((ROOT / args.operation).read_text())
    baseline_data = subprocess.check_output(['git','-C',str(ROOT),'show',args.baseline+':'+CONTROL],stderr=subprocess.PIPE)
    assert baseline_data == (ROOT / CONTROL).read_bytes(), 'frozen callable baseline bytes differ'
    control = load(ROOT / CONTROL); harness = load(ROOT / 'tools/test_workflow_assurance.py')
    assert args.case in harness.BUNDLE_CASES and callable(control.verify_acceptance_bundle)
    assert operation['target'] == 'verify_acceptance_bundle'
    if args.stage == 'setup':
        api = harness.load_api(); assert callable(api.assess_repository) and callable(api.verify_record_update) and callable(harness.run_case)
        api.verify_record_update({'unchanged':1},{'unchanged':1},[])
        result = subprocess.run([sys.executable, api.__file__, '--help'],capture_output=True,text=True)
        assert result.returncode == 0 and 'assess' in result.stdout
        print('EXISTING115_API_HARNESS_CLI: PASS')
        print('TARGET_CALLABLE: verify_acceptance_bundle PASS'); return 0
    ref = operation['positive_input' if args.stage == 'positive' else 'case_input']
    data = (ROOT / ref['path']).read_bytes(); assert sha(data) == ref['sha256']
    request = json.loads(data)
    assert set(request) == {'case','mutation','expected_result'} and request['case'] == args.case
    assert request['mutation'] == ('none' if args.stage == 'positive' else args.case)
    expected = 'accept' if args.stage == 'positive' else operation['expected_result']
    assert request['expected_result'] == expected
    with tempfile.TemporaryDirectory(prefix='nizam116-semantic-baseline-') as parent:
        fixture = harness.BundleFixture(parent)
        if args.stage == 'red': harness.bundle_mutate(fixture, args.case)
        print('INPUT_SHA256: ' + sha(data)); print('OPERATION_SHA256: ' + sha(canonical(operation)))
        print('FIXTURE_BASELINE: ' + fixture.bundle['baseline']['commit'])
        print('FIXTURE_CURRENT_HEAD: ' + harness.git(fixture.root,'rev-parse','HEAD'))
        try:
            assert control.verify_acceptance_bundle(fixture.root,fixture.bundle,fixture.review) is True
            observed = 'accept'
        except control.AssuranceError as exc:
            print('NAIVE_POLICY_DIAGNOSTIC: ' + str(exc)); observed = 'reject'
        print('OBSERVED_RESULT: ' + observed)
        if observed != expected:
            print('POLICY_ASSERTION: ' + args.case + ' intended policy outcome mismatch'); return 1
        print('POSITIVE_CONTROL: ' + args.case + ' PASS'); return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except Exception as exc:
        print('SETUP_OR_UNRELATED_ERROR: ' + type(exc).__name__ + ': ' + str(exc),file=sys.stderr); sys.exit(2)
