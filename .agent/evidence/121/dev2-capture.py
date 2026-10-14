"""Generator verification-only attempt2: one actual default42, immutable input capture."""
import ast, hashlib, json, os, pathlib, stat, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
E = pathlib.Path('.agent/evidence/121'); BASE = 'fc167ee325cd85ec4f011053aaeb223d5e4dc684'; OLD = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
git = lambda *a: subprocess.check_output(['git', *a], text=True).strip()
write = lambda name, value: (E / ('dev2-' + name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
revision = git('rev-parse', 'HEAD'); subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, revision], check=True)
dispatch = json.loads((E / 'dev2-dispatch.json').read_text()); assert str(ROOT) == dispatch['root']
pins = {'tools/workflow_assurance.py': dispatch['source_sha256'], 'tools/test_workflow_assurance.py': dispatch['test_sha256'], '.agent/contracts/121.json': dispatch['approved_contract_sha256']}
paths = sorted(set(list(pins) + git('ls-files', 'schema', '.nizam', 'tools/README.md', 'CHANGELOG.md').splitlines()))
protected = [p for p in git('ls-files').splitlines() if not p.startswith(str(E / 'dev2-'))]
def identity():
    rows = {p: dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), git_blob=git('hash-object', p), mode=stat.S_IMODE(pathlib.Path(p).lstat().st_mode)) for p in paths}
    inventory = []
    for p in protected:
        q = pathlib.Path(p); mode = q.lstat().st_mode
        data = os.readlink(q).encode() if stat.S_ISLNK(mode) else q.read_bytes()
        inventory.append([p, mode, hashlib.sha256(data).hexdigest()])
    return dict(files=rows, protected_count=len(inventory), protected_paths_bytes_modes_sha256=hashlib.sha256(json.dumps(inventory, separators=(',', ':')).encode()).hexdigest())
before = identity(); write('identity-before', before)
assert all(before['files'][p]['sha256'] == h for p, h in pins.items())
assert git('diff', 'HEAD', '--', *protected) == ''
functions = lambda s: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(s).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
inventories = lambda s: {t.id: ast.literal_eval(n.value) for n in ast.parse(s).body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name) and t.id in ('AGF_CASES', 'RECEIPT_CASES', 'LANE_CASES')}
preservation = {}
for path, exempt in [('tools/workflow_assurance.py', set()), ('tools/test_workflow_assurance.py', {'main'})]:
    original_text = subprocess.check_output(['git', 'show', OLD + ':' + path], text=True); actual_text = pathlib.Path(path).read_text()
    original = functions(original_text); actual = functions(actual_text); inherited = sorted(set(original) - exempt)
    assert all(actual.get(k) == original[k] for k in inherited)
    if 'test_' in path:
        old_inventory = inventories(original_text); current_inventory = inventories(actual_text)
        assert all(current_inventory[k] == v for k, v in old_inventory.items())
    preservation[path] = dict(base=OLD, unchanged_symbols=inherited, approved_dispatch_exemption=sorted(exempt))
assert len(git('ls-files', '.nizam').splitlines()) == 239
assert git('diff', OLD, 'HEAD', '--', 'schema', '.nizam') == ''
bank = inventories(pathlib.Path('tools/test_workflow_assurance.py').read_text())
expected = [r['case'] for r in json.loads(pathlib.Path('.agent/evidence/118/api-interface.json').read_text())['current_cases']] + list(bank['AGF_CASES']) + list(bank['RECEIPT_CASES']) + list(bank['LANE_CASES'])
assert len(expected) == 42 and len(set(expected)) == 42
write('preservation', dict(base=BASE, historical_base=OLD, revision=revision, inherited=preservation, installed_count=239, inventories=bank, expected_order=expected))
argv = ['python3', 'tools/test_workflow_assurance.py']; env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
r = subprocess.run(argv, capture_output=True, env=env)
(E / 'dev2-default42.stdout.txt').write_bytes(r.stdout); (E / 'dev2-default42.stderr.txt').write_bytes(r.stderr)
after = identity(); write('identity-after', after); markers = [x[5:] for x in r.stdout.decode().splitlines() if x.startswith('PASS ')]
write('result', dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE': '1'}, revision=revision, input_ancestor=BASE, exit=r.returncode, stdout=str(E / 'dev2-default42.stdout.txt'), stderr=str(E / 'dev2-default42.stderr.txt'), stdout_sha256=hashlib.sha256(r.stdout).hexdigest(), stderr_sha256=hashlib.sha256(r.stderr).hexdigest(), ordered_markers=markers, ordered42_match=markers == expected, protected_unchanged=before == after, protected_identity_before=str(E / 'dev2-identity-before.json'), protected_identity_after=str(E / 'dev2-identity-after.json')))
print('default42 actual_exit', r.returncode, 'ordered42_match', markers == expected, 'protected_unchanged', before == after, flush=True)
if r.returncode:
    print(r.stderr.decode(), flush=True); raise SystemExit(r.returncode)
assert markers == expected and before == after
