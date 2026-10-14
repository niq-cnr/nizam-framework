"""Independent fixture architecture review; not final acceptance controls or QA."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
INPUT = '7ab5fc43a52ba96be552e69262cf261e5cfc32fb'
PRIOR = '945d37a69af3dc371bd277f50697846e8d507eae'
PREFIX = '.agent/evidence/120/provisional-review3'
def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
def sha(data): return hashlib.sha256(data).hexdigest()
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
subprocess.run(['git', 'merge-base', '--is-ancestor', INPUT, 'HEAD'], check=True)
seal = json.loads(pathlib.Path('.agent/evidence/120/author3-provisional-seal.json').read_text())
for path, pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes()) == pin['sha256'], path
    assert git('hash-object', path) == pin['git_blob'] == git('rev-parse', 'HEAD:' + path), path
assert git('rev-parse', '1689f0dc1f1ef20e96c7cb7ee1e3375232a83ce5:tools/workflow_assurance.py') == seal['files']['tools/workflow_assurance.py']['git_blob']
before = ast.parse(subprocess.check_output(['git', 'show', PRIOR + ':tools/test_workflow_assurance.py'], text=True))
after = ast.parse(pathlib.Path('tools/test_workflow_assurance.py').read_text())
old_class = next(n for n in before.body if isinstance(n, ast.ClassDef) and n.name == 'ReceiptFixture')
new_class = next(n for n in after.body if isinstance(n, ast.ClassDef) and n.name == 'ReceiptFixture')
old_commit = next(n for n in old_class.body if isinstance(n, ast.FunctionDef) and n.name == 'commit')
new_commit = next(n for n in new_class.body if isinstance(n, ast.FunctionDef) and n.name == 'commit')
new_class.body[new_class.body.index(new_commit)] = old_commit
assert ast.dump(before) == ast.dump(after), 'only fixture commit method changed; assertions/inventory identical'
prior_evidence = git('diff', '--name-status', '105e8fb1bb098345a84047ca6dd1d1c1ed2e2c72', INPUT, '--', '.agent/evidence/120', '.agent/qa/120-provisional-bundle-review.json', '.agent/qa/120-provisional-bundle-review-rev1.json').splitlines()
assert prior_evidence and all(row.startswith('A\t') for row in prior_evidence)
spec = importlib.util.spec_from_file_location('reviewed_tests', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t); api = t.load_api()
assert len(t.CASES) == 20 and len(t.AGF_CASES) == 6 and len(t.RECEIPT_CASES) == 11
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
with tempfile.TemporaryDirectory(prefix='nizam120-review3-') as directory:
    f = t.ReceiptFixture(api, directory); ref = f.policy['operator']; start = t.git(f.root, 'rev-parse', 'HEAD')
    repeated = f.pin(ref['path'], f.operator)
    assert repeated == ref and start == t.git(f.root, 'rev-parse', 'HEAD')
    changed = f.pin('proof/reviewer-new-content.json', {'reviewer': 'real content'})
    assert changed['revision'] != start and t.git(f.root, 'cat-file', '-t', changed['revision']) == 'commit'
    assert json.loads(subprocess.check_output(['git', '-C', str(f.root), 'show', changed['revision'] + ':' + changed['path']])) == {'reviewer':'real content'}
    errors = []
    def expected_error(label, operation):
        head = t.git(f.root, 'rev-parse', 'HEAD')
        try: operation()
        except subprocess.CalledProcessError as error:
            assert error.returncode != 0 and head == t.git(f.root, 'rev-parse', 'HEAD')
            for suffix, raw in (('stdout', error.output or b''), ('stderr', error.stderr or b'')):
                path = pathlib.Path(PREFIX + '-' + label + '.' + suffix + '.txt'); assert not path.exists(); path.write_bytes(raw)
            errors.append(dict(label=label, argv=error.cmd, actual_exit=error.returncode, unchanged_head=head, stdout=PREFIX+'-'+label+'.stdout.txt', stderr=PREFIX+'-'+label+'.stderr.txt'))
        else: raise AssertionError('Git error swallowed: ' + label)
    lock = f.root / '.git/index.lock'; lock.write_text('owned scratch lock')
    try: expected_error('git-add-failure', lambda: f.commit('must fail staging'))
    finally: lock.unlink()
    hook = f.root / '.git/hooks/pre-commit'; hook.write_text('#!/bin/sh\nexit 17\n'); hook.chmod(0o755)
    expected_error('git-commit-failure', lambda: f.pin('proof/denied-change.json', {'fixture':'deny commit'}))
    fixture = dict(original_ref=ref, repeated_ref=repeated, real_changed_ref=changed, propagated_errors=errors)
records = json.loads(pathlib.Path('.agent/evidence/120/author3-development-captures.json').read_text())
assert len(records) == 12 and [r['argv'][-1] for r in records[1:]] == list(t.RECEIPT_CASES)
for row in records:
    assert row['exit'] == 0 and pathlib.Path(row['stdout']).read_bytes() == ('PASS '+row['argv'][-1]+'\n').encode()
    assert pathlib.Path(row['stderr']).read_bytes() == b''
    for stream in ('stdout','stderr'): assert sha(pathlib.Path(row[stream]).read_bytes()) == row[stream+'_sha256']
    for path, pin in row['inputs'].items(): assert pin == seal['files'][path]
path = pathlib.Path(PREFIX+'-proof.json'); assert not path.exists()
path.write_text(json.dumps(dict(reviewed_revision=INPUT, actual_executed_revision=git('rev-parse','HEAD'), environment={'PYTHONDONTWRITEBYTECODE':'1'}, pins=seal['files'], fixture=fixture, authored_development_captures_checked=12, assertions_and_old_AST_preserved=True, prior_evidence_additions_only=True, final_controls_or_QA=False), indent=2)+'\n')
print('PASS pins11; identical artifact real HEAD reuse; changed bytes real commit; add/commit errors propagate; unchanged assertions; truthful development captures12')
