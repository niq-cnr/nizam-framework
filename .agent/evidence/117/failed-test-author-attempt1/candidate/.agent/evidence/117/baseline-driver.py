"""Execute frozen callable entry-policy baseline; only semantic mismatch exits1.

Setup, imports, transport, shape and unrelated errors exit2. Every stage runs
against actual Git B inputs; immutable archived product supplies existing APIs.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
CONTROL='.agent/evidence/117/naive-policy.py'


def canonical(v): return json.dumps(v,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()
def sha(data): return hashlib.sha256(data).hexdigest()
def load(path):
    spec=importlib.util.spec_from_file_location('baseline117_module',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('setup','positive','red'),required=True)
    p.add_argument('--case',required=True);p.add_argument('--baseline',required=True)
    p.add_argument('--operation',required=True);args=p.parse_args()
    inventory=json.loads((ROOT/'.agent/evidence/117/baseline-inputs.json').read_text())
    for path in inventory['paths']:
        data=(ROOT/path).read_bytes()
        assert data==subprocess.check_output(['git','-C',str(ROOT),'show',args.baseline+':'+path]),'changed frozen dependency '+path
    control=load(ROOT/CONTROL);harness=load(ROOT/'tools/test_workflow_assurance.py')
    fixtures=load(ROOT/'.agent/evidence/117/entry-fixtures.py')
    operation=json.loads((ROOT/args.operation).read_text())
    assert args.case in fixtures.CASES and operation['target']=='verify_authorized_entry'
    assert callable(control.verify_authorized_entry)
    if args.stage=='setup':
        api=harness.load_api(ROOT/'.agent/evidence/117/archived-product.py')
        assert callable(api.assess_repository) and callable(api.verify_record_update) and callable(api.verify_acceptance_bundle)
        harness.run_case('identity-positive',api);harness.run_bundle_case('independent-handoff',api)
        result=subprocess.run([sys.executable,api.__file__,'--help'],capture_output=True,text=True)
        assert result.returncode==0 and 'assess' in result.stdout and 'bundle' in result.stdout
        with tempfile.TemporaryDirectory(prefix='nizam117-baseline-setup-') as parent:
            f=fixtures.EntryFixture(parent)
            assert control.verify_authorized_entry(f.root,f.entry) is True
        print('EXISTING115116_API_HARNESS_CLI: PASS')
        print('TARGET_CALLABLE: verify_authorized_entry PASS');return 0
    ref=operation['positive_input' if args.stage=='positive' else 'case_input']
    data=(ROOT/ref['path']).read_bytes();assert sha(data)==ref['sha256']
    request=json.loads(data)
    assert set(request)=={'case','mutation','expected_result'} and request['case']==args.case
    assert request['mutation']==('none' if args.stage=='positive' else args.case)
    expected='accept' if args.stage=='positive' else operation['expected_result']
    assert request['expected_result']==expected
    with tempfile.TemporaryDirectory(prefix='nizam117-semantic-baseline-') as parent:
        f=fixtures.EntryFixture(parent)
        if args.stage=='red':fixtures.mutate(f,args.case)
        print('INPUT_SHA256: '+sha(data));print('OPERATION_SHA256: '+sha(canonical(operation)))
        print('FIXTURE_APPROVED_SNAPSHOT: '+fixtures.APPROVED)
        print('FIXTURE_PROPOSAL: '+f.contract['approvals']['gate_refs']['proposal_revision'])
        print('OBSERVED_ORIGIN: '+fixtures.git(f.root,'remote','get-url','origin'))
        try:
            assert control.verify_authorized_entry(f.root,f.entry) is True
            observed='accept'
        except control.AssuranceError as exc:
            print('NAIVE_POLICY_DIAGNOSTIC: '+str(exc));observed='reject'
        print('OBSERVED_RESULT: '+observed)
        if observed!=expected:
            print('POLICY_ASSERTION: '+args.case+' intended policy outcome mismatch');return 1
        print('POSITIVE_CONTROL: '+args.case+' PASS');return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('SETUP_OR_UNRELATED_ERROR: '+type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(2)
