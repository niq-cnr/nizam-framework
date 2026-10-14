"""Replay actual setup plus a naive-policy positive and intended missing-proof red."""
import argparse
from pathlib import Path
import sys
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('foundation_fixture',HERE/'foundation-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('setup','positive','red','fixture-selfcheck'),required=True);parser.add_argument('--workspace',required=True);args=parser.parse_args()
    if args.stage=='fixture-selfcheck':
        f.load(HERE/'fixture-path-selfcheck.py').main();return
    api=f.load(HERE/'naive-policy.py');f.require(callable(api.verify_foundation_ready),'callable naive readiness target')
    root=Path(args.workspace)
    if args.stage=='setup':
        f.baseline_setup(root);print('TARGET_CALLABLE: verify_foundation_ready PASS');return
    marker=f.read(root,f.E+'FIXTURE-NOT-SOURCEC.json');f.require(marker['purpose'].startswith('Independent naive'),'qualified fixture only')
    receipt=f.read(root,f.E+'prerequisite20.json');f.require(len(receipt['checks'])==20 and all((root/r['evidence']).is_file() for r in receipt['checks']),'real completed setup proof exists')
    print('FIXTURE_ONLY: not actual118 SourceC prerequisite')
    if args.stage=='positive':
        f.require(api.verify_foundation_ready(root,receipt) is True,'valid baseline receipt positive');print('POSITIVE_CONTROL: missing-proof PASS');return
    (root/receipt['checks'][0]['evidence']).unlink()
    observed=api.verify_foundation_ready(root,receipt)
    print('OBSERVED_RESULT: '+('accept' if observed is True else 'reject'))
    f.require(observed is not True,'missing-proof intended policy outcome mismatch')

if __name__=='__main__':
    try: main()
    except AssertionError as exc: print(str(exc),file=sys.stderr);raise SystemExit(1)
    except Exception as exc: print('SETUP_OR_UNRELATED_ERROR: '+str(exc),file=sys.stderr);raise SystemExit(2)
