"""One-shot corrected fixture setup, not absent121 API behavioral acceptance."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT); os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
base = '791cb27c2a72816a5c036a0af910fed8b20c08b1'; prefix = '.agent/evidence/121/author2-'
assert not pathlib.Path(prefix + 'captures.json').exists(), 'one-shot evidence paths'
spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
old = ast.parse(subprocess.check_output(['git', 'show', '478844edfb9fb1de96d1c372e1e794c875941e78:tools/test_workflow_assurance.py'], text=True))
new = {n.name: ast.dump(n) for n in ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
assert all(new[n.name] == ast.dump(n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main')
with tempfile.TemporaryDirectory(prefix='nizam121-author2-') as directory:
    f = t.LaneFixture(directory)
    try:
        original = dict(f.request); original['owner'] = dict(f.request['owner'])
        f.authorize(writes=['../escape']); dispatch = json.loads((f.root / 'proof/dispatch.json').read_text())
        assert dispatch['writes'] == f.request['writes'] == ['../escape']
        f.request = original; f.authorize()
        for kind in ('staged', 'committed', 'rename', 'mode', 'symlink', 'unmerged', 'submodule'):
            root, writes = f.inventory_probe(kind); f.authorize(attempt_root=str(root), writes=writes)
            if kind == 'unmerged': assert t.git(root, 'ls-files', '--unmerged') and writes == ['src/b.py']
            if kind == 'submodule': assert '160000 ' in t.git(root, 'ls-files', '--stage') and writes == ['owned-gitlink']
        f.request = original; f.authorize()
        for name, value in (('contract', json.loads((f.root / 'contract.json').read_text())), ('contract_review', json.loads((f.root / 'proof/contract-review.json').read_text())), ('run_state', f.state), ('feature_list', f.features)):
            jsonschema.validate(value, json.loads((ROOT / ('schema/' + name + '.schema.json')).read_text()))
        alias = f.attempt_parent / 'proof-bound-alias'; alias.symlink_to(f.attempt, target_is_directory=True)
        f.authorize(attempt_root=str(alias)); reference = f.proof(f.request, True)
        failure = json.loads((f.root / reference['path']).read_text()); assert failure['attempt_root'] == str(alias) and failure['actual_exit'] == 7
        proof = dict(root=str(f.root), base_revision=f.base, git_probes=f.git_probe_log, bound_malformed_dispatch=dispatch,
            matching_unsafe_failure=failure, failure_ref=reference, actual_process_captures=f.proof_captures,
            registration=t.git(f.root, 'worktree', 'list', '--porcelain'), no_newAPI_execution=True,
            note='Actual expected Git conflict exit1 is fixture setup, not a121 semantic red; Source absent.')
        pathlib.Path(prefix + 'fixture-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    finally: f.close()
records = []
for name in t.LANE_CASES:
    argv = ['python3', 'tools/test_workflow_assurance.py', '--case', name]; result = subprocess.run(argv, capture_output=True, env=os.environ); stem = prefix + name
    for suffix, raw in (('.stdout.txt', result.stdout), ('.stderr.txt', result.stderr)):
        with pathlib.Path(stem + suffix).open('xb') as output: output.write(raw)
    records.append(dict(argv=argv, cwd=str(ROOT), revision=t.git(ROOT, 'rev-parse', 'HEAD'), actual_exit=result.returncode, stdout=stem + '.stdout.txt', stderr=stem + '.stderr.txt'))
    pathlib.Path(prefix + 'captures.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 2 and b'SETUP_ERROR: missing lane APIs' in result.stderr and b'PASS ' not in result.stdout
print('PASS real staged/committed/rename/mode/symlink/conflict/gitlink setup, schemas, bound unsafe proof and fiveAPIabsence2; old37 ASTs unchanged')
