"""Frozen private acceptance controls; run only after Root releases initial Source.

The semantic mutant changes only the in-memory implementation of the new API.
Assertions, fixture inputs and setup remain intact. It validates the first
positive with actual Source, then deliberately accepts invalid subsequent proof.
This is synthetic discrimination, never evidence of actual hosted execution.
"""
import argparse
import copy
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selector',required=True,choices=('ci-candidate-bound','ci-blocker-rejected','controls-ready'))
    parser.add_argument('--stage',required=True,choices=('positive','semantic-negative','restored'))
    args=parser.parse_args()
    if os.environ.get('PYTHONDONTWRITEBYTECODE')!='1':raise SystemExit('SETUP_ERROR: PYTHONDONTWRITEBYTECODE=1 required')
    sys.path.insert(0,str(ROOT/'tools'))
    spec=importlib.util.spec_from_file_location('frozen123_acceptance',ROOT/'tools/test_workflow_assurance.py')
    tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
    api=tests.load_api()
    if not callable(getattr(api,'verify_controls_ready',None)):
        print('SETUP_ERROR: missing executable new API, not semantic red',file=sys.stderr);return 2
    if args.stage=='semantic-negative':
        actual=api.verify_controls_ready; golden=[]
        def deliberately_accept_invalid(repo,evidence,*,policy):
            if not golden:golden.append(copy.deepcopy(actual(repo,evidence,policy=policy)))
            return copy.deepcopy(golden[0])
        api.verify_controls_ready=deliberately_accept_invalid
    if args.selector=='controls-ready':tests.run_controls_ready(api)
    else:tests.run_controls_case(args.selector,api)
    print('PASS frozen123 '+args.selector+' '+args.stage)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(1)
