"""Author captures; --controls is executable only after independent Source release."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT); os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
records = []
def capture(label, argv, exit_code, diagnostic=None, source=None, cwd=None):
    root = pathlib.Path(cwd or ROOT)
    result = subprocess.run(argv, capture_output=True, env=os.environ, cwd=root)
    prefix = '.agent/evidence/119/author1-executable-' + label
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout); pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    paths = ['tools/test_workflow_assurance.py', str(source or 'tools/workflow_assurance.py'), '.agent/contracts/119.json']
    records.append({'label': label, 'argv': argv, 'cwd': str(root), 'revision': tests.git(root, 'rev-parse', 'HEAD'), 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'exit': result.returncode,
        'inputs': {p: {'sha256': hashlib.sha256((root / p).read_bytes()).hexdigest(), 'git_blob': tests.git(root, 'hash-object', '-w', p)} for p in paths},
        'stdout': prefix + '.stdout.txt', 'stderr': prefix + '.stderr.txt', 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(result.stderr).hexdigest(), 'expected_diagnostic': diagnostic})
    pathlib.Path('.agent/evidence/119/author1-executable-' + sys.argv[1][2:] + '-captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == exit_code, (label, result.returncode, result.stderr.decode())
    if diagnostic: assert diagnostic.encode() in result.stderr
    if exit_code: assert b'PASS ' not in result.stdout
if sys.argv[1:] == ['--controls']:
    source = (ROOT / 'tools/workflow_assurance.py').read_text()
    for index, name in enumerate(tests.AGF_CASES):
        command = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
        capture(name + '-positive', command, 0)
        body = "out['final_verdict']['approved'] = False" if index == 0 else "out['advisory_minor'] = []" if index == 1 else "out['issues'] = []; out['required_fixes'] = []; out['final_verdict']['approved'] = True" if index == 2 else "out[%r] = []; out['final_verdict']['approved'] = True" % tests.AGF_ARRAYS[index - 3]
        mutant = source + "\n_original_agf = convergent_agf_verdict\ndef convergent_agf_verdict(*args, **kwargs):\n    out = _original_agf(*args, **kwargs)\n    " + body + "\n    return out\n"
        with tempfile.TemporaryDirectory(prefix='nizam119-mutant-') as directory:
            path = pathlib.Path(directory) / 'workflow_assurance.py'; path.write_text(mutant)
            code = "import sys; sys.path.insert(0,'tools'); import test_workflow_assurance as t; t.run_agf_case(%r,t.load_api(%r)); print('PASS '+%r)" % (name, str(path), name)
            assertion = ('empty valid AGF approves exactly', 'active minor visible separately', 'active full findings appended in ledger order')[index] if index < 3 else 'nonempty blocking array preserved: ' + tests.AGF_ARRAYS[index - 3]
            capture(name + '-semantic-red', ['python3', '-c', code], 1, 'POLICY_ASSERTION: ' + assertion, path)
        capture(name + '-restored', command, 0)
elif sys.argv[1:] == ['--preservation']:
    for name in tests.CASES: capture('legacy-' + name, ['python3', 'tools/test_workflow_assurance.py', '--case', name], 0)
    capture('live-stale118', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], 1, 'AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py')
    with tempfile.TemporaryDirectory(prefix='nizam119-foundation-') as directory:
        history = pathlib.Path(directory) / 'repository'
        capture('history-clone', ['git', 'clone', '-q', '--shared', '--no-checkout', str(ROOT), str(history)], 0)
        capture('history-checkout', ['git', '-C', str(history), 'checkout', '--detach', '-q', '8ac94f6808e8197111197c9acbf59b2aa92efc7c'], 0)
        capture('historical-foundation-ready', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], 0, cwd=history)
else:
    raise SystemExit('use --controls or --preservation')
print('PASS author capture stage', sys.argv[1])
