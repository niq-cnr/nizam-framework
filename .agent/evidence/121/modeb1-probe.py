"""Independent Mode B probe; committed before execution; fixture-only Git roots."""
import copy
import importlib.util
import json
from pathlib import Path
import platform
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[3]


def main():
    spec = importlib.util.spec_from_file_location('modeb121_tests', ROOT / 'tools/test_workflow_assurance.py')
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    api = tests.load_api()
    print('Python ' + platform.python_version(), flush=True)
    with tempfile.TemporaryDirectory(prefix='nizam121-modeb1-loop-') as parent:
        fixture = tests.LaneFixture(parent)
        loop = fixture.attempt_parent / 'self-loop'
        try:
            tests.require(tests.lane_call(api, fixture)['eligible'] is True, 'valid baseline assessment')
            tests.require(tests.lane_call(api, fixture, 'verify_isolated_attempt')['owned_changes'] == [], 'valid baseline registered isolated worktree')
            print('BASELINE_VALID actual_exit=0 assessment eligible; isolation owned_changes=[]', flush=True)
            loop.symlink_to(loop.name, target_is_directory=True)
            fixture.authorize(attempt_root=str(loop))
            inputs = copy.deepcopy((fixture.request, fixture.policy))
            before = fixture.all_files()
            registration = tests.git(fixture.root, 'worktree', 'list', '--porcelain')
            print(json.dumps(dict(probe='self-referential attempt_root', root=str(fixture.root), request=fixture.request, policy=fixture.policy), sort_keys=True), flush=True)
            caught = None
            try:
                api.assess_conflict_lanes(fixture.root, fixture.request, policy=fixture.policy)
            except api.AssuranceError as exc:
                tests.require(bool(str(exc)) and len(str(exc)) <= 500, 'bounded AssuranceError diagnostic')
                caught = 'AssuranceError'
                print('EXPECTED AssuranceError: ' + str(exc), flush=True)
            except RuntimeError as exc:
                caught = type(exc).__name__
                print('OBSERVED_ORDINARY_RUNTIMEERROR ' + repr(exc), flush=True)
                traceback.print_exc()
            tests.require((fixture.request, fixture.policy) == inputs and fixture.all_files() == before and tests.git(fixture.root, 'worktree', 'list', '--porcelain') == registration, 'unsafe path denial preserves inputs files registration')
            print('PRESERVED inputs/files/modes/registration', flush=True)
            tests.require(caught == 'AssuranceError', 'CONTRACT121 api.errors requires AssuranceError for unsafe OS/path data; observed ' + str(caught))
            print('PASS self-loop normalizes AssuranceError', flush=True)
        finally:
            if loop.is_symlink():
                loop.unlink()
            fixture.close()
            print('CLEANUP only owned fixture worktrees and loop', flush=True)


if __name__ == '__main__':
    main()
