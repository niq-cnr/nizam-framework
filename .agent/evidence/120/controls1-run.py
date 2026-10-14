"""Prepared control transport. Execute only after Root releases a dedicated run."""
import argparse, hashlib, json, os, pathlib, re, stat, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]
SOURCE = '733c1478a8eb237339efe914d29d2be2c93d01172ed399e3baea340d6ec3982a'
TESTS = '9c99ff133aacaad158f840e78158792b2b096450560f47dc4b218b8e4ff223f7'
CONTRACT = '3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
INPUT = '7ab5fc43a52ba96be552e69262cf261e5cfc32fb'
INVALID = 'AssertionError: POLICY_ASSERTION: receipt invalid input rejected: invalid input accepted'
STATUS = "receipt['status'] == 'passed'"
CONTROLS = (
 ('reject-missing-operator', "app['approved'] is True, 'receipt operator decision'", "app['approved'] in (True, 1), 'receipt operator decision'", INVALID),
 ('reject-wrong-candidate', "require(compare_identity(receipt['candidate'], policy['candidate']), 'receipt candidate identity mismatch')", "require(True, 'receipt candidate identity mismatch')", INVALID),
 ('reject-unrun', "actual['executed'] is True and type(actual['exit_code']) is int", "type(actual['executed']) is bool and type(actual['exit_code']) is int", INVALID),
 ('reject-setup', 'for actual in (capture, check):', 'for actual in (check,):', INVALID),
 ('reject-pending', STATUS, "receipt['status'] in ('passed', 'pending')", INVALID),
 ('reject-running', STATUS, "receipt['status'] in ('passed', 'running')", INVALID),
 ('reject-failed', STATUS, "receipt['status'] in ('passed', 'failed')", INVALID),
 ('reject-invalidated', STATUS, "receipt['status'] in ('passed', 'invalidated')", INVALID),
 ('idempotent-replay', "action, reason = 'noop', 'Identical receipt transition is already recorded.'", "action, reason = 'advance', 'Identical receipt transition is already recorded.'", 'AssertionError: POLICY_ASSERTION: receipt identical replay noop'),
 ('reject-double-advance', 'canonical(matches[0]) == canonical(event)', "canonical({**matches[0], 'detail': event['detail']}) == canonical(event)", INVALID),
 ('recover-missing-receipt', "action, reason = 'republish', 'Verified original receipt may be republished; no state transition occurred.'", "action, reason = 'advance', 'Verified original receipt may be republished; no state transition occurred.'", 'AssertionError: POLICY_ASSERTION: verified recovery only proposes republish'))


def digest(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def git(root, *args): return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()
def write(path, data):
    with pathlib.Path(path).open('xb') as handle: handle.write(data)
def snapshot():
    paths = ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/120.json',
        '.agent/run_state.json', '.agent/feature_list_018.json', 'docs/planning/phase_018.yaml')
    return {p: {'sha256': digest(ROOT / p), 'mode': stat.S_IMODE((ROOT / p).lstat().st_mode)} for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('stage', choices=('controls', 'preservation'))
    parser.add_argument('--run-id', required=True); args = parser.parse_args()
    assert re.fullmatch('[a-z0-9][a-z0-9-]*', args.run_id)
    os.chdir(ROOT); os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    for path, expected in (('tools/workflow_assurance.py', SOURCE), ('tools/test_workflow_assurance.py', TESTS), ('.agent/contracts/120.json', CONTRACT)):
        assert digest(ROOT / path) == expected, 'frozen input changed: ' + path
    subprocess.run(['git', 'merge-base', '--is-ancestor', INPUT, 'HEAD'], check=True)
    prefix = '.agent/evidence/120/controls1-' + args.run_id + '-' + args.stage
    manifest = prefix + '-manifest.json'; assert not pathlib.Path(manifest).exists(), 'new execution paths required'
    records = []; protected = snapshot(); completed = False
    def capture(label, argv, expected_exit, marker=None, cwd=ROOT, source=None, mutation=None):
        assert snapshot() == protected, 'protected records changed before command'
        revision = git(cwd, 'rev-parse', 'HEAD'); result = subprocess.run(argv, cwd=cwd, capture_output=True, env=os.environ)
        out = prefix + '-' + label + '.stdout.txt'; err = prefix + '-' + label + '.stderr.txt'
        write(out, result.stdout); write(err, result.stderr)
        paths = (pathlib.Path(source or (cwd / 'tools/workflow_assurance.py')), cwd / 'tools/test_workflow_assurance.py', ROOT / '.agent/contracts/120.json', pathlib.Path(__file__))
        row = dict(label=label, argv=argv, cwd=str(cwd), revision=revision, environment={'PYTHONDONTWRITEBYTECODE': '1'},
            actual_exit=result.returncode, expected_exit=expected_exit, expected_assertion_line=marker, mutation=mutation,
            inputs={str(p): {'sha256': digest(p), 'git_blob': git(ROOT, 'hash-object', '-w', str(p))} for p in paths},
            stdout=out, stderr=err, stdout_sha256=hashlib.sha256(result.stdout).hexdigest(), stderr_sha256=hashlib.sha256(result.stderr).hexdigest(),
            protected_before=protected, protected_after=snapshot())
        records.append(row)
        assert row['protected_after'] == protected, 'command changed protected records'
        assert result.returncode == expected_exit, (label, result.returncode, result.stderr.decode())
        if marker: assert [line for line in result.stderr.decode().splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')] == [marker]
        if expected_exit: assert not any(line.startswith(b'PASS ') for line in result.stdout.splitlines())
        else: assert label.startswith('history-') or any(line.startswith(b'PASS ') for line in result.stdout.splitlines()), 'positive must emit actual PASS'
        print(label + ': actual exit ' + str(result.returncode), flush=True)
    try:
        if args.stage == 'controls':
            source = (ROOT / 'tools/workflow_assurance.py').read_text()
            for name, before, after, marker in CONTROLS:
                assert source.count(before) == 1, 'mutant anchor must be unique: ' + name
                command = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
                capture(name + '-positive', command, 0)
                with tempfile.TemporaryDirectory(prefix='nizam120-control-') as directory:
                    mutant = pathlib.Path(directory) / 'workflow_assurance.py'; mutant.write_text(source.replace(before, after, 1))
                    code = "import sys;sys.path.insert(0,'tools');import test_workflow_assurance as t;t.run_receipt_case(%r,t.load_api(%r));print('PASS '+%r)" % (name, str(mutant), name)
                    capture(name + '-semantic-red', ['python3', '-c', code], 1, marker, source=mutant, mutation={'before': before, 'after': after})
                capture(name + '-restored', command, 0)
        else:
            sys.path.insert(0, str(ROOT / 'tools')); import test_workflow_assurance as tests
            for name in tests.CASES + tests.AGF_CASES: capture(name, ['python3', 'tools/test_workflow_assurance.py', '--case', name], 0)
            capture('live-stale118', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], 1)
            assert pathlib.Path(records[-1]['stderr']).read_text().splitlines() == ['AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py']
            with tempfile.TemporaryDirectory(prefix='nizam120-historical-') as directory:
                history = pathlib.Path(directory) / 'repository'
                capture('history-clone', ['git', 'clone', '-q', '--shared', '--no-checkout', str(ROOT), str(history)], 0)
                capture('history-checkout', ['git', '-C', str(history), 'checkout', '--detach', '-q', '8ac94f6808e8197111197c9acbf59b2aa92efc7c'], 0)
                capture('historical-foundation-ready', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], 0, cwd=history)
        completed = True
    finally:
        write(manifest, (json.dumps(dict(stage=args.stage, completed=completed, actual_helper_revision=git(ROOT, 'rev-parse', 'HEAD'),
            original_source_commit='1689f0dc1f1ef20e96c7cb7ee1e3375232a83ce5', protected=protected, captures=records), indent=2) + '\n').encode())


if __name__ == '__main__': main()
