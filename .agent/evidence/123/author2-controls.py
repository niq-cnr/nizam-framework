"""Frozen author2 private discrimination; execute only after Root Source release.

Positive/restored use actual newAPI and unchanged assertions. Semantic-negative
accepts invalid proof only after its actual baseline has succeeded. All synthetic
constructor/import/missingAPI failures are SETUP2, never intended semantic red.
"""
import argparse
import copy
import importlib.util
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selector',required=True,choices=('ci-candidate-bound','ci-blocker-rejected','controls-ready'))
    parser.add_argument('--stage',required=True,choices=('positive','semantic-negative','restored'))
    args=parser.parse_args()
    if os.environ.get('PYTHONDONTWRITEBYTECODE')!='1':raise SystemExit('SETUP_ERROR: PYTHONDONTWRITEBYTECODE=1 required')
    sys.path.insert(0,str(ROOT/'tools'))
    try:
        spec=importlib.util.spec_from_file_location('frozen123_author2',ROOT/'tools/test_workflow_assurance.py')
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests);api=tests.load_api()
    except Exception as exc:
        print('SETUP_ERROR: import '+type(exc).__name__+': '+str(exc),file=sys.stderr);return 2
    if not callable(getattr(api,'verify_controls_ready',None)):
        print('SETUP_ERROR: missing executable newAPI, never semantic red',file=sys.stderr);return 2
    if args.stage=='semantic-negative':
        actual=api.verify_controls_ready;golden=[]
        def deliberately_accept_invalid(repo,evidence,*,policy):
            if not golden:golden.append(copy.deepcopy(actual(repo,evidence,policy=policy)))
            return copy.deepcopy(golden[0])
        api.verify_controls_ready=deliberately_accept_invalid
    try:
        if args.selector=='controls-ready':tests.run_controls_ready(api)
        else:tests.run_controls_case(args.selector,api)
    except Exception as exc:
        intended=isinstance(exc,AssertionError) and 'POLICY_ASSERTION: synthetic invalid controls proof accepted:' in str(exc)
        if args.stage=='semantic-negative' and not intended:
            print('SETUP_ERROR: not intended semantic rejection: '+type(exc).__name__+': '+str(exc),file=sys.stderr);return 2
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);return 1
    if args.stage=='semantic-negative':
        print('SETUP_ERROR: invalid-proof acceptance mutant escaped frozen assertions',file=sys.stderr);return 2
    print('PASS frozen123 author2 '+args.selector+' '+args.stage);return 0

if __name__=='__main__':raise SystemExit(main())
