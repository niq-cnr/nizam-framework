"""Private Source control worker; execution requires Root release through controls runner."""
import argparse
import functools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TEST_SHA256 = 'e251283add498c699f6c90fd7934f92dcffe570e6c3fdda51326c6dc0e504c21'
CONTRACT_SHA256 = '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'


def worker(name, source):
    sys.path.insert(0, str(ROOT/'tools'))
    import test_workflow_assurance as tests
    assert name in tests.FAILURE_CASES
    assert tests.sha((ROOT/'tools/test_workflow_assurance.py').read_bytes()) == TEST_SHA256
    assert tests.sha((ROOT/'.agent/contracts/122.json').read_bytes()) == CONTRACT_SHA256
    api = tests.load_api(source); actual = api.route_failed_attempt
    @functools.wraps(actual)
    def traced(repo, request, *, policy):
        row = dict(method='route_failed_attempt', request=repr(request), source_sha256=tests.sha(source.read_bytes()))
        if type(request) is dict: row.update(cause=repr(request.get('cause')), attempt=repr(request.get('attempt')))
        try:
            authority = json.loads((Path(repo)/policy['authority_ref']['path']).read_bytes())
            row.update(authority_approved=authority.get('approved'), authority_cause=authority.get('cause'))
            evidence = json.loads((Path(repo)/authority['evidence_ref']['path']).read_bytes())
            if evidence.get('verdict_ref'):
                verdict = json.loads((Path(repo)/evidence['verdict_ref']['path']).read_bytes())
                row['semantic_verdict'] = {k:verdict.get(k) for k in ('final_verdict','issues','missing_acceptance_coverage','unsupported_claims')}
            state = json.loads((Path(repo)/policy['coordination_ref']['path']).read_bytes())
            row['scope_budget'] = state.get('scope_budget')
        except (OSError, ValueError, TypeError, KeyError, AttributeError): pass
        try:
            result = actual(repo, request, policy=policy); row.update(returned=True, result=result)
            return result
        except BaseException as exc:
            row.update(raised=type(exc).__name__, diagnostic=str(exc)[:400]); raise
        finally: print('API_TRACE '+json.dumps(row, allow_nan=False), flush=True)
    api.route_failed_attempt = traced
    original = tests.FailureFixture.__init__
    def setup(self, *args, **kwargs):
        original(self, *args, **kwargs)
        print('FIXTURE_TRACE '+json.dumps(dict(root=str(self.root), candidate=self.candidate['source_commit'],
            synthetic_authority_ref=self.policy['authority_ref'], observed_exit=self.capture['exit_code'])), flush=True)
    tests.FailureFixture.__init__ = setup
    tests.run_failure_case(name, api)
    print('PASS '+name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True); parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    try: worker(args.case, args.source)
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc), file=sys.stderr); sys.exit(1)
