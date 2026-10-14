"""One-shot fixture/interface proof; absent APIs are setup2, never semantic red."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'; os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api = t.load_api()
base = '82709fdb19a7e53c85bcc75c5c6b8a0551b39fae'; old = '05421787419630483a0d9ce8aafbb0869def45c7'
assert subprocess.run(['git', 'merge-base', '--is-ancestor', base, 'HEAD']).returncode == 0
prior_seal = '.agent/evidence/120/author1-provisional-seal.json'
assert pathlib.Path(prior_seal).read_bytes() == subprocess.check_output(['git', 'show', old + ':' + prior_seal])
prior = json.loads(pathlib.Path(prior_seal).read_text())
assert hashlib.sha256(subprocess.check_output(['git', 'show', old + ':tools/test_workflow_assurance.py'])).hexdigest() == prior['files']['tools/test_workflow_assurance.py']['sha256']
original = ast.parse(subprocess.check_output(['git', 'show', '345ad4f1d97cd262a572bd60ccbbe97391e25a24:tools/test_workflow_assurance.py'], text=True))
current = {n.name: ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
assert all(current[n.name] == ast.dump(n) for n in original.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main')
assert len(t.CASES + t.AGF_CASES + t.RECEIPT_CASES) == 37 and len(t.RECEIPT_CASES) == 11
with tempfile.TemporaryDirectory(prefix='nizam120-author2-') as directory:
    f = t.ReceiptFixture(api, directory); api.validate_identity(f.candidate)
    reference = f.policy['operator']; malformed = f.nonregular_artifact(reference)
    raw = subprocess.check_output(['git', '-C', str(f.root), 'show', malformed['revision'] + ':' + malformed['path']])
    assert hashlib.sha256(raw).hexdigest() == reference['sha256'] == malformed['sha256']
    assert json.loads(raw) == f.operator and not (f.root / reference['path']).is_symlink()
    for kind, path in (('contract', 'contract.json'), ('contract_review', 'proof/contract-review.json'), ('qa_verdict', 'proof/fresh-qa.json')):
        jsonschema.validate(json.loads((f.root / path).read_text()), json.loads((ROOT / ('schema/' + kind + '.schema.json')).read_text()))
    jsonschema.validate(f.state, json.loads((ROOT / 'schema/run_state.schema.json').read_text()))
    row = t.git(f.root, 'ls-tree', malformed['revision'], '--', malformed['path'])
    proof = dict(root=str(f.root), candidate=f.candidate, original_operator_ref=reference, nonregular_ref=malformed,
        actual_ls_tree=row, exact_bytes_sha256=hashlib.sha256(raw).hexdigest(), actual_process_capture=f.capture,
        note='actual owned fixture construction only; no absent newAPI semantic execution')
    pathlib.Path('.agent/evidence/120/author2-fixture-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
os.environ.pop('NIZAM_WA120_FIXTURE')
records = []
for name in t.RECEIPT_CASES:
    argv = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
    result = subprocess.run(argv, capture_output=True, env=os.environ); prefix = '.agent/evidence/120/author2-setup-' + name
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout); pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    records.append(dict(argv=argv, cwd=str(ROOT), revision=t.git(ROOT, 'rev-parse', 'HEAD'), exit=result.returncode, stdout=prefix + '.stdout.txt', stderr=prefix + '.stderr.txt'))
    pathlib.Path('.agent/evidence/120/author2-setup-captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 2 and b'SETUP_ERROR: missing receipt APIs' in result.stderr and b'PASS ' not in result.stdout
print('PASS isolated artifact Gitmode/bytes fixture, actual schemas, old26 AST preservation, exact11 setup2; no semantic-red claim')
