"""One-shot real fixture/schema and absent-API captures before independent review."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
api = t.load_api(); base = '345ad4f1d97cd262a572bd60ccbbe97391e25a24'
records = []; manifest = pathlib.Path('.agent/evidence/120/author1-provisional-captures.json')
assert not manifest.exists(), 'one-shot paths: preserve previous actual outputs'
assert subprocess.run(['git', 'merge-base', '--is-ancestor', base, 'HEAD']).returncode == 0
assert hashlib.sha256(pathlib.Path('.agent/contracts/120.json').read_bytes()).hexdigest() == '3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
old = ast.parse(subprocess.check_output(['git', 'show', base + ':tools/test_workflow_assurance.py'], text=True))
new = {n.name: ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
assert all(new[n.name] == ast.dump(n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main')
assert len(t.CASES) == 20 and len(t.AGF_CASES) == 6 and len(t.RECEIPT_CASES) == 11
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
with tempfile.TemporaryDirectory(prefix='nizam120-provisional-') as directory:
    for alternate in (False, True):
        f = t.ReceiptFixture(api, directory, alternate)
        api.validate_identity(f.candidate)
        for kind in ('contract', 'contract_review', 'qa_verdict', 'run_state'):
            value = f.state if kind == 'run_state' else json.loads((f.root / ('contract.json' if kind == 'contract' else 'proof/' + ('contract-review' if kind == 'contract_review' else 'fresh-qa') + '.json')).read_text())
            jsonschema.validate(value, json.loads((ROOT / ('schema/' + kind + '.schema.json')).read_text()))
        assert f.capture['exit_code'] == 0 and f.capture['executed'] is True
        assert f.diagnostic in (f.root / f.capture['stdout']['path']).read_text().splitlines()
        receipt = dict(root=str(f.root), revision=t.git(f.root, 'rev-parse', 'HEAD'), candidate=f.candidate,
            policy=f.policy, receipt=f.receipt, actual_capture=f.capture, synthetic_authority_gate_fixtures=True)
        pathlib.Path('.agent/evidence/120/author1-fixture-' + str(alternate).lower() + '.json').write_text(json.dumps(receipt, indent=2) + '\n')
os.environ.pop('NIZAM_WA120_FIXTURE')
for name in t.RECEIPT_CASES + t.CASES + t.AGF_CASES:
    argv = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
    result = subprocess.run(argv, capture_output=True, env=os.environ)
    prefix = '.agent/evidence/120/author1-provisional-' + name
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout); pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/120.json']
    records.append(dict(argv=argv, cwd=str(ROOT), revision=t.git(ROOT, 'rev-parse', 'HEAD'), exit=result.returncode,
        environment={'PYTHONDONTWRITEBYTECODE': '1'}, stdout=prefix + '.stdout.txt', stderr=prefix + '.stderr.txt',
        inputs={p: dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), git_blob=t.git(ROOT, 'hash-object', '-w', p)) for p in paths}))
    manifest.write_text(json.dumps(records, indent=2) + '\n')
    if name in t.RECEIPT_CASES:
        assert result.returncode == 2 and b'SETUP_ERROR: missing receipt APIs' in result.stderr and b'PASS ' not in result.stdout
    else: assert result.returncode == 0, (name, result.stderr)
print('PASS real alternate fixtures/schemas/identities; preserved26; new11 setup2 only, no semantic-red claim')
