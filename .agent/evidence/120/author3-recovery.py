"""One-shot fixture-only development confirmation, not final controls or QA."""
import hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'; os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api = t.load_api()
expected_source = '733c1478a8eb237339efe914d29d2be2c93d01172ed399e3baea340d6ec3982a'
assert hashlib.sha256(pathlib.Path('tools/workflow_assurance.py').read_bytes()).hexdigest() == expected_source
with tempfile.TemporaryDirectory(prefix='nizam120-author3-idempotence-') as directory:
    f = t.ReceiptFixture(api, directory); original = f.ref(f.policy['operator']['path'])
    before = t.git(f.root, 'rev-parse', 'HEAD'); repeated = f.pin(original['path'], f.operator)
    assert original == repeated and before == t.git(f.root, 'rev-parse', 'HEAD')
    changed = f.pin('proof/real-new-content.json', {'fixture': 'actual change'})
    assert changed['revision'] != before and t.git(f.root, 'show', changed['revision'] + ':' + changed['path'])
    pathlib.Path('.agent/evidence/120/author3-idempotence-proof.json').write_text(json.dumps(dict(root=str(f.root), original_ref=original, identical_ref=repeated, unchanged_revision=before, changed_ref=changed, result='identical content reuses immutable revision; actual content change creates real commit'), indent=2) + '\n')
os.environ.pop('NIZAM_WA120_FIXTURE')
records = []
for label, name in [('failed-selector-restored', 'reject-invalidated')] + [('all11-' + name, name) for name in t.RECEIPT_CASES]:
    argv = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
    result = subprocess.run(argv, capture_output=True, env=os.environ); prefix = '.agent/evidence/120/author3-' + label
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout); pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/120.json']
    records.append(dict(label=label, argv=argv, cwd=str(ROOT), revision=t.git(ROOT, 'rev-parse', 'HEAD'), exit=result.returncode,
        environment={'PYTHONDONTWRITEBYTECODE': '1'}, stdout=prefix + '.stdout.txt', stderr=prefix + '.stderr.txt',
        stdout_sha256=hashlib.sha256(result.stdout).hexdigest(), stderr_sha256=hashlib.sha256(result.stderr).hexdigest(),
        inputs={p: dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), git_blob=t.git(ROOT, 'hash-object', '-w', p)) for p in paths}))
    pathlib.Path('.agent/evidence/120/author3-development-captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 0 and ('PASS ' + name).encode() in result.stdout, (name, result.returncode, result.stderr)
    assert hashlib.sha256(pathlib.Path('tools/workflow_assurance.py').read_bytes()).hexdigest() == expected_source
print('PASS fixture-only no-op repair: failing selector restored0 and all11 actual0; Source unchanged; final controls/QA not claimed')
