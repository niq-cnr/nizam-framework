"""One-shot provisional setup capture; no absent121 API execution claims."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT); os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
base = '478844edfb9fb1de96d1c372e1e794c875941e78'; prefix = '.agent/evidence/121/author1-'
assert not pathlib.Path(prefix + 'captures.json').exists(), 'one-shot evidence paths'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
old = ast.parse(subprocess.check_output(['git', 'show', base + ':tools/test_workflow_assurance.py'], text=True))
new = {n.name: ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
inherited = [n.name for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main']
assert all(new[n.name] == ast.dump(n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main')
assert len(t.CASES + t.AGF_CASES + t.RECEIPT_CASES) == 37 and len(t.LANE_CASES) == 5
with tempfile.TemporaryDirectory(prefix='nizam121-provisional-') as directory:
    f = t.LaneFixture(directory)
    try:
        registration = t.git(f.root, 'worktree', 'list', '--porcelain')
        assert t.git(f.attempt, 'rev-parse', '--show-toplevel') == str(f.attempt)
        assert t.git(f.attempt, 'rev-parse', 'HEAD') == f.base
        assert any(('worktree ' + str(f.attempt) + '\n') in row and '\ndetached' in row for row in registration.split('\n\n'))
        for name, value in (('contract', json.loads((f.root / 'contract.json').read_text())), ('contract_review', json.loads((f.root / 'proof/contract-review.json').read_text())), ('run_state', f.state), ('feature_list', f.features)):
            jsonschema.validate(value, json.loads((ROOT / ('schema/' + name + '.schema.json')).read_text()))
        original = f.ref('coordination.json'); assert f.pin('coordination.json', f.state) == original
        lane = f.lane(); release = f.proof(lane); failure = f.proof(f.request, True)
        assert [r['actual_exit'] for r in f.proof_captures] == [0, 7]
        proof = dict(root=str(f.root), attempt_root=str(f.attempt), base_revision=f.base, registration=registration,
            request=f.request, policy=f.policy, schema_checks=['contract', 'contract_review', 'run_state', 'feature_list'],
            no_op_pin=original, release=release, failure=failure, actual_process_captures=f.proof_captures,
            outside_sentinel_sha256=hashlib.sha256(f.outside.read_bytes()).hexdigest(), inherited_actual_symbols=inherited,
            note='Synthetic authority/role parser fixtures. Real owned repositories/worktrees and actual capture exits; no121 API pass/red claimed.')
        pathlib.Path(prefix + 'fixture-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    finally: f.close()
records = []
for name in t.LANE_CASES + t.CASES + t.AGF_CASES + t.RECEIPT_CASES:
    argv = ['python3', 'tools/test_workflow_assurance.py', '--case', name]
    result = subprocess.run(argv, capture_output=True, env=os.environ); stem = prefix + name
    for suffix, data in (('.stdout.txt', result.stdout), ('.stderr.txt', result.stderr)):
        with pathlib.Path(stem + suffix).open('xb') as output: output.write(data)
    paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/121.json']
    records.append(dict(argv=argv, cwd=str(ROOT), revision=t.git(ROOT, 'rev-parse', 'HEAD'), actual_exit=result.returncode,
        environment={'PYTHONDONTWRITEBYTECODE': '1'}, stdout=stem + '.stdout.txt', stderr=stem + '.stderr.txt',
        inputs={p: dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), git_blob=t.git(ROOT, 'hash-object', '-w', p)) for p in paths}))
    pathlib.Path(prefix + 'captures.json').write_text(json.dumps(records, indent=2) + '\n')
    if name in t.LANE_CASES: assert result.returncode == 2 and b'SETUP_ERROR: missing lane APIs' in result.stderr and b'PASS ' not in result.stdout
    else: assert result.returncode == 0, (name, result.returncode, result.stderr)
print('PASS four real fixture schemas, registered detached roots, noop pin, actual proof exits0/7, inherited ASTs, old37pass and new5setup2 only')
