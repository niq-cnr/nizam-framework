"""Historical-only capture after a receipt-helper failure; no product changes."""
import hashlib, json, os, pathlib, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
records = []; prefix = ROOT / '.agent/evidence/119/author1-executable-historical2'
def run(label, argv, cwd=ROOT):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    out = str(prefix) + '-' + label + '.stdout.txt'; err = str(prefix) + '-' + label + '.stderr.txt'
    pathlib.Path(out).write_bytes(result.stdout); pathlib.Path(err).write_bytes(result.stderr)
    records.append({'argv': argv, 'cwd': str(cwd), 'exit': result.returncode, 'stdout': str(pathlib.Path(out).relative_to(ROOT)), 'stderr': str(pathlib.Path(err).relative_to(ROOT)), 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()})
    pathlib.Path(str(prefix) + '-captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 0, (label, result.returncode, result.stderr)
with tempfile.TemporaryDirectory(prefix='nizam119-historical2-') as directory:
    history = pathlib.Path(directory) / 'repository'
    run('clone', ['git', 'clone', '-q', '--shared', '--no-checkout', str(ROOT), str(history)])
    run('checkout', ['git', '-C', str(history), 'checkout', '--detach', '-q', '8ac94f6808e8197111197c9acbf59b2aa92efc7c'])
    paths = [history / 'tools/workflow_assurance.py', history / 'tools/test_workflow_assurance.py', ROOT / '.agent/contracts/119.json']
    identities = {'revision': subprocess.check_output(['git', '-C', str(history), 'rev-parse', 'HEAD'], text=True).strip(), 'inputs': {str(p): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'git_blob': subprocess.check_output(['git', 'hash-object', '-w', str(p)], text=True).strip()} for p in paths}, 'environment': {'PYTHONDONTWRITEBYTECODE': '1'}, 'author': '/root/evaluator119'}
    pathlib.Path(str(prefix) + '-identities.json').write_text(json.dumps(identities, indent=2) + '\n')
    run('foundation-ready', ['python3', 'tools/test_workflow_assurance.py', '--check', 'foundation-ready'], history)
print('PASS unchanged historical8ac94f6 foundation-ready exit0; actual command/exit/identities captured')
