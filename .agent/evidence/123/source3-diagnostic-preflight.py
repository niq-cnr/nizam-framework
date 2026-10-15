"""Private partial diagnosis; Root release required before execution.

Never a public selector, full-bank pass, gate or semantic-red substitution.
Uses frozen fixture/assertions; only six known diagnostic mismatches may continue
after executing the frozen genuine-positive restoration sequence. All other
unexpected failures stop. Source2 diagnosis and Source3 check retain distinct
actual exercised revisions/argv/output/exits under separate Root releases.
"""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TEST_SHA = '9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'
RUNNER_SHA = '7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905'
CONTRACT_SHA = '64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
CANDIDATE_NAMES = ('claimed-ref-future', 'claimed-ref-dangling', 'claimed-ref-self', 'claimed-ref-loop')
KNOWN_DIAGNOSTIC_NAMES = frozenset(('claimed-ref-dangling', 'incoming-issues',
    'incoming-missing_acceptance_coverage', 'incoming-unsupported_claims',
    'carried-blocker', 'carried-important'))


def emit(kind, **fields):
    print(json.dumps(dict(kind=kind, **fields), sort_keys=True), flush=True)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def tracked_snapshot():
    names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).split(b'\0')
    rows = []
    for name in filter(None, names):
        relative = os.fsdecode(name); path = ROOT / relative; info = path.lstat()
        value = os.readlink(path) if stat.S_ISLNK(info.st_mode) else digest(path)
        rows.append((relative, info.st_mode, info.st_nlink, value))
    return rows


def frozen_tail(tests, raw):
    """Execute original unchanged candidate suffix, without preceding full loop."""
    tree = ast.parse(raw, filename=str(ROOT / 'tools/test_workflow_assurance.py'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'controls_candidate']
    if len(functions) != 1:
        raise RuntimeError('SETUP_ERROR: unique frozen candidate function required')
    function = functions[0]
    starts = [i for i, node in enumerate(function.body) if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'saved']
    if starts != [3] or not isinstance(function.body[2], ast.For):
        raise RuntimeError('SETUP_ERROR: frozen candidate tail structural boundary changed')
    suffix = copy.deepcopy(function.body[starts[0]:])
    tail = copy.deepcopy(function); tail.name = '_private_frozen_candidate_tail'; tail.body = suffix
    tail.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[tail], type_ignores=[]))
    namespace = dict(tests.__dict__)
    exec(compile(module, str(ROOT / 'tools/test_workflow_assurance.py'), 'exec'), namespace)
    emit('frozen-tail', source_sha256=TEST_SHA, first_line=suffix[0].lineno,
        last_line=suffix[-1].end_lineno,
        ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=suffix, type_ignores=[]), include_attributes=False).encode()).hexdigest(),
        scope='Unchanged policy/nonfinite/cycle/current-input/hardlink/observer suffix only; preceding full variant loop not executed')
    return namespace[tail.name]


def restore_positive(tests, api, fixture):
    # Exact restoration operations used after the context manager in controls_variant.
    tests.git(fixture.root, 'restore', '--source=' + fixture.materialized_tip,
        '--staged', '--worktree', '--', tests.CONTROL_PREFIX)
    fixture.write('.agent/evidence/123/selection.json', fixture.raw(fixture.verify_selection))
    fixture.commit('SYNTHETIC restored original positive materialization')
    tests.controls_call(api, fixture)


def variant(tests, api, fixture, defect, failures):
    name = defect['name']; emit('start-variant', name=name, site=defect['site'])
    try:
        tests.controls_variant(api, fixture, defect)
    except AssertionError as exc:
        prefix = 'POLICY_ASSERTION: rejection must identify intended cause ' + name + ': '
        if name not in KNOWN_DIAGNOSTIC_NAMES or not str(exc).startswith(prefix):
            raise
        failures.append(dict(name=name, diagnostic=str(exc)))
        emit('diagnostic-mismatch', name=name, diagnostic=str(exc), semantic_red=False)
        restore_positive(tests, api, fixture)
        emit('restored-after-diagnostic-mismatch', name=name, genuine_api=True,
            deviation='Standard full bank stops; this explicitly bounded diagnosis executes the identical frozen restoration before continuing known diagnostic mismatches')
    else:
        emit('targeted-rejection-and-restoration-passed', name=name)


def alarm(_signum, _frame):
    raise TimeoutError('private diagnostic preflight whole-operation 900s bound exceeded')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    if os.environ.get('PYTHONDONTWRITEBYTECODE') != '1' or not re.fullmatch('[0-9a-f]{64}', args.source_sha256):
        emit('setup-error', diagnostic='Explicit env1 and exact released source hash required'); return 2
    expected = {'tools/workflow_assurance.py': args.source_sha256,
        'tools/test_workflow_assurance.py': TEST_SHA,
        'tools/workflow_assurance_ci.py': RUNNER_SHA, '.agent/contracts/123.json': CONTRACT_SHA}
    for relative, wanted in expected.items():
        if digest(ROOT / relative) != wanted:
            emit('setup-error', diagnostic='Released input hash mismatch', path=relative); return 2
    revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip()
    if subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no']).strip():
        emit('setup-error', diagnostic='Tracked owned checkout must be clean'); return 2
    emit('invocation', exercised_revision=revision, argv=sys.argv, cwd=os.getcwd(), root=str(ROOT),
        environment={'PYTHONDONTWRITEBYTECODE': '1'}, input_sha256=expected, whole_timeout_seconds=900,
        scope='Private partial diagnosis, not any exact public selector/default bank or gate')
    before = tracked_snapshot(); failures = []; result = 1
    signal.signal(signal.SIGALRM, alarm); signal.alarm(900)
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            spec = importlib.util.spec_from_file_location('frozen123_diagnostic', ROOT / 'tools/test_workflow_assurance.py')
            tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
            api = tests.load_api()
            if not callable(getattr(api, 'verify_controls_ready', None)):
                raise RuntimeError('missing executable newAPI')
        except Exception as exc:
            emit('setup-error', diagnostic=type(exc).__name__ + ': ' + str(exc)); return 2
        tail = frozen_tail(tests, (ROOT / 'tools/test_workflow_assurance.py').read_bytes())
        with tempfile.TemporaryDirectory(prefix='nizam123-SYNTHETIC-tail-diagnosis-') as parent:
            fixture = tests.controls_construct(api, parent)
            tests.controls_call(api, fixture); emit('baseline-pass', group='candidate')
            available = {row['name']: row for row in tests.controls_defects()}
            for name in CANDIDATE_NAMES:
                variant(tests, api, fixture, available[name], failures)
            emit('start-frozen-candidate-tail'); tail(api, fixture)
            emit('frozen-candidate-tail-pass')
        with tempfile.TemporaryDirectory(prefix='nizam123-SYNTHETIC-blocker-diagnosis-') as parent:
            fixture = tests.controls_construct(api, parent)
            tests.controls_call(api, fixture); emit('baseline-pass', group='blocker')
            defects = tests.controls_defects(True)
            if len(defects) != 12:
                raise RuntimeError('SETUP_ERROR: frozen blocker inventory changed')
            for defect in defects:
                variant(tests, api, fixture, defect, failures)
        emit('partial-diagnostic-summary', diagnostic_mismatches=failures,
            full_bank_executed=False, semantic_red=False, actual_exit=1 if failures else 0)
        result = 1 if failures else 0
    except SystemExit as exc:
        emit('setup-error', diagnostic='Frozen constructor/import/API setup terminated', exit=exc.code)
        result = 2
    except Exception as exc:
        emit('unexpected-stop', diagnostic=type(exc).__name__ + ': ' + str(exc), semantic_red=False)
        result = 1
    finally:
        signal.alarm(0)
        after = tracked_snapshot()
        if after != before:
            emit('preservation-failed', scope='Actual owned tracked inputs bytes/full modes/link counts'); result = 1
        else:
            emit('preservation-pass', tracked_inputs=len(before),
                installed_regular_files=sum(path.startswith('.nizam/') and stat.S_ISREG(mode) for path, mode, links, value in before))
    return result


if __name__ == '__main__':
    raise SystemExit(main())
