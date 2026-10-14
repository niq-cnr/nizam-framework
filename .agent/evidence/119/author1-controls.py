"""Author captures; --controls is executable only after independent Source release."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT); os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
records = []
def capture(label, argv, exit_code, diagnostic=None, source=None):
    result = subprocess.run(argv, capture_output=True, env=os.environ)
    prefix = '.agent/evidence/119/author1-' + label
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout); pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    paths = ['tools/test_workflow_assurance.py', str(source or 'tools/workflow_assurance.py'), '.agent/contracts/119.json']
    records.append({'label': label, 'argv': argv, 'cwd': str(ROOT), 'revision': tests.git(ROOT, 'rev-parse', 'HEAD'), 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'exit': result.returncode,
        'inputs': {p: {'sha256': hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), 'git_blob': tests.git(ROOT, 'hash-object', p)} for p in paths},
        'stdout': prefix + '.stdout.txt', 'stderr': prefix + '.stderr.txt', 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(result.stderr).hexdigest(), 'expected_diagnostic': diagnostic})
    pathlib.Path('.agent/evidence/119/author1-captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == exit_code, (label, result.returncode, result.stderr.decode())
    if diagnostic: assert diagnostic.encode() in result.stderr
    if exit_code: assert b'PASS ' not in result.stdout
if sys.argv[1:] == ['--provisional']:
    fixture = "import importlib.util; s=importlib.util.spec_from_file_location('t','tools/test_workflow_assurance.py'); t=importlib.util.module_from_spec(s); s.loader.exec_module(t); assert len(t.CASES)==20 and len(t.AGF_CASES)==6; [(t.agf_severity(t.agf_ledger(c),v)) for c in ('01-no-findings','02-consensus-blocker','05-prior-persisting','08-reopened-finding','06-prior-resolution-two-of-three','11-authorized-suppression-retained') for v in ('minor','important','blocker')]; print('PASS real converged fixtures and inventory20+6')"
    capture('fixture-corrected', ['python3', '-c', fixture], 0)
    for name in tests.AGF_CASES:
        capture('setup-' + name, ['python3', 'tools/test_workflow_assurance.py', '--case', name], 2, 'SETUP_ERROR: missing convergent_agf_verdict API')
    for name in tests.CASES: capture('old-' + name, ['python3', 'tools/test_workflow_assurance.py', '--case', name], 0)
    capture('foundation-ready', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], 0)
elif sys.argv[1:] == ['--controls']:
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
else:
    raise SystemExit('use --provisional or --controls')
print('PASS author capture stage', sys.argv[1])
