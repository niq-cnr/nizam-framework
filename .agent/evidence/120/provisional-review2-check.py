"""Focused independent provisional repair verification; receipt APIs remain absent."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT)
INPUT = 'ea6a84ee20f0639154ba3de72aff7fe26b0cf8cc'
AUTHOR = '945d37a69af3dc371bd277f50697846e8d507eae'
PRIOR = '05421787419630483a0d9ce8aafbb0869def45c7'
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
def sha(data):
    return hashlib.sha256(data).hexdigest()
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
subprocess.run(['git', 'merge-base', '--is-ancestor', INPUT, 'HEAD'], check=True)
seal = json.loads(pathlib.Path('.agent/evidence/120/author2-provisional-seal.json').read_text())
for path, pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes()) == pin['sha256'], path
    assert git('hash-object', path) == pin['git_blob'] == git('rev-parse', AUTHOR + ':' + path), path
prior_paths = [p for p in git('ls-tree', '-r', '--name-only', PRIOR, '.agent/evidence/120').splitlines() if p.startswith('.agent/evidence/120/author1-')]
assert prior_paths, 'nonvacuous author1 preservation inventory'
for path in prior_paths:
    assert pathlib.Path(path).read_bytes() == subprocess.check_output(['git', 'show', PRIOR + ':' + path]), path
prior_ast = ast.parse(subprocess.check_output(['git', 'show', PRIOR + ':tools/test_workflow_assurance.py'], text=True))
now_ast = ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text())
now = {n.name: ast.dump(n) for n in now_ast.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
changed = [n.name for n in prior_ast.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and now[n.name] != ast.dump(n)]
assert changed == ['ReceiptFixture', 'receipt_operator', 'receipt_unrun'], changed
spec = importlib.util.spec_from_file_location('reviewed_tests', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api = t.load_api()
assert not hasattr(api, 'verify_stage_receipt') and not hasattr(api, 'plan_receipt_transition')
assert len(t.CASES) == 20 and len(t.AGF_CASES) == 6 and len(t.RECEIPT_CASES) == 11
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
with tempfile.TemporaryDirectory(prefix='nizam120-provisional-review2-') as directory:
    f = t.ReceiptFixture(api, directory); api.validate_identity(f.candidate)
    before_index = (f.root / '.git/index').read_bytes(); before_head = t.git(f.root, 'rev-parse', 'HEAD')
    ref = f.policy['operator']; altered = f.nonregular_artifact(ref)
    raw = subprocess.check_output(['git', '-C', str(f.root), 'show', altered['revision'] + ':' + altered['path']])
    assert sha(raw) == ref['sha256'] == altered['sha256'] and json.loads(raw) == f.operator
    assert ref['path'] == altered['path'] and not (f.root / ref['path']).is_symlink()
    assert before_index == (f.root / '.git/index').read_bytes() and before_head == t.git(f.root, 'rev-parse', 'HEAD')
    tree_row = t.git(f.root, 'ls-tree', altered['revision'], '--', altered['path'])
    assert tree_row.startswith('120000 blob ')
    for kind, path in (('contract', 'contract.json'), ('contract_review', 'proof/contract-review.json'), ('qa_verdict', 'proof/fresh-qa.json'), ('run_state', 'record.json')):
        jsonschema.validate(json.loads((f.root / path).read_text()), json.loads(pathlib.Path('schema/' + kind + '.schema.json').read_text()))
    revisions = ['0' * 40, t.git(f.root, 'hash-object', ref['path']), 'HEAD']
    assert subprocess.run(['git', '-C', str(f.root), 'cat-file', '-e', revisions[0]], capture_output=True).returncode != 0
    assert t.git(f.root, 'cat-file', '-t', revisions[1]) == 'blob'
    output = f.root / f.capture['stdout']['path']; data = output.read_bytes(); alias = f.root / 'proof/current-output-alias'
    alias.write_bytes(data); output.unlink(); output.symlink_to(alias)
    try: assert output.is_symlink() and output.read_bytes() == data
    finally: output.unlink(); output.write_bytes(data); alias.unlink()
    assert not output.is_symlink() and output.read_bytes() == data
    fixture = dict(candidate=f.candidate, capture=f.capture, operator_ref=ref, nonregular_ref=altered, actual_ls_tree=tree_row, same_bytes_sha256=sha(raw), invalid_revision_inputs=revisions, scratch_index_and_head_preserved=True, current_output_same_bytes_symlink_restored=True)
records = json.loads(pathlib.Path('.agent/evidence/120/author2-setup-captures.json').read_text())
assert len(records) == 11
for row, name in zip(records, t.RECEIPT_CASES):
    assert row['argv'][-1] == name and row['exit'] == 2
    assert pathlib.Path(row['stdout']).read_bytes() == b''
    assert pathlib.Path(row['stderr']).read_bytes() == b'SETUP_ERROR: missing receipt APIs\n'
proof = pathlib.Path('.agent/evidence/120/provisional-review2-proof.json'); assert not proof.exists()
proof.write_text(json.dumps(dict(reviewed_revision=INPUT, actual_executed_revision=git('rev-parse', 'HEAD'), environment={'PYTHONDONTWRITEBYTECODE':'1'}, pins=seal['files'], changed_existing_definitions=changed, prior_runtime_evidence='.agent/evidence/120/provisional-review1-proof.json', fixture=fixture, authored_setup_captures_checked=11, new_api_execution=False), indent=2) + '\n')
print('PASS final pins9; isolated historical mode/same bytes; safe index/HEAD; schemas4; output symlink restore; unchanged old26 definitions; prior setup11 only')
