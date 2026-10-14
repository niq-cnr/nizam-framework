"""Independent provisional inspection; no missing receipt API is simulated."""
import ast, hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT)
PREFIX = ROOT / '.agent/evidence/120/provisional-review1'
INPUT = 'cbae9c9652026fa454b643af075ba19471ae75e6'
AUTHOR = '05421787419630483a0d9ce8aafbb0869def45c7'
BASE = '345ad4f1d97cd262a572bd60ccbbe97391e25a24'
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
def sha(data):
    return hashlib.sha256(data).hexdigest()
def write(suffix, value):
    path = pathlib.Path(str(PREFIX) + suffix)
    assert not path.exists(), 'preserve one-shot actual evidence: ' + str(path)
    path.write_text(json.dumps(value, indent=2) + '\n')

assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
executed = git('rev-parse', 'HEAD')
subprocess.run(['git', 'merge-base', '--is-ancestor', INPUT, executed], check=True)
seal = json.loads((ROOT / '.agent/evidence/120/author1-provisional-seal.json').read_text())
pins = {}
for path, expected in seal['files'].items():
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected['sha256']
    assert git('rev-parse', AUTHOR + ':' + path) == expected['git_blob']
    assert git('hash-object', path) == expected['git_blob']
    pins[path] = expected
spec = importlib.util.spec_from_file_location('independent_tests', ROOT / 'tools/test_workflow_assurance.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
api = t.load_api()
assert not hasattr(api, 'verify_stage_receipt') and not hasattr(api, 'plan_receipt_transition')
old = ast.parse(subprocess.check_output(['git', 'show', BASE + ':tools/test_workflow_assurance.py'], text=True))
new = ast.parse((ROOT / 'tools/test_workflow_assurance.py').read_text())
definitions = {n.name: ast.dump(n) for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
preserved = [n.name for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main']
assert all(definitions[n.name] == ast.dump(n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name != 'main')
assert len(t.CASES) == 20 and len(t.AGF_CASES) == 6 and len(t.RECEIPT_CASES) == 11
assert len(set(t.CASES + t.AGF_CASES + t.RECEIPT_CASES)) == 37
contract = json.loads((ROOT / '.agent/contracts/120.json').read_text())
assert [v['command'].split()[-1] for v in contract['verification']] == list(t.RECEIPT_CASES)
precode = json.loads((ROOT / '.agent/evidence/120/precode-final-capture.json').read_text())
reviewers = []
for ref in precode['gates']:
    raw = (ROOT / ref['path']).read_bytes()
    assert sha(raw) == ref['sha256']
    gate = json.loads(raw)
    assert gate['final_verdict']['approved'] is True
    assert all(gate[k] == [] for k in t.AGF_ARRAYS)
    reviewers.append(gate.get('reviewer', gate.get('actor')))
assert all(reviewers) and reviewers[0] != reviewers[1]
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
fixtures = []
with tempfile.TemporaryDirectory(prefix='nizam120-review1-') as parent:
    for alternate in (False, True):
        f = t.ReceiptFixture(api, parent, alternate)
        api.validate_identity(f.candidate)
        for kind, path in (('contract', 'contract.json'), ('contract_review', 'proof/contract-review.json'), ('qa_verdict', 'proof/fresh-qa.json'), ('run_state', 'record.json')):
            jsonschema.validate(json.loads((f.root / path).read_text()), json.loads((ROOT / ('schema/' + kind + '.schema.json')).read_text()))
        captures = []
        for outcome in ('success', 'semantic-negative', 'failed', 'setup-error'):
            capture = f.capture if outcome == 'success' else f.actual_capture(outcome)
            assert capture['exit_code'] == {'failed': 7, 'setup-error': 2}.get(outcome, 0)
            assert f.diagnostic in (f.root / capture['stdout']['path']).read_text().splitlines()
            captures.append(capture)
        fixtures.append(dict(alternate=alternate, synthetic_authority_gate_fixtures=True, candidate=f.candidate, captures=captures))
os.environ.pop('NIZAM_WA120_FIXTURE')
write('-fixtures.json', fixtures)
cases = []
for name in t.CASES + t.AGF_CASES:
    argv = [sys.executable, 'tools/test_workflow_assurance.py', '--case', name]
    result = subprocess.run(argv, capture_output=True, env=os.environ)
    for label, raw in (('stdout', result.stdout), ('stderr', result.stderr)):
        path = pathlib.Path(str(PREFIX) + '-' + name + '.' + label + '.txt')
        assert not path.exists()
        path.write_bytes(raw)
    cases.append(dict(argv=argv, actual_exit=result.returncode, stdout=str(PREFIX.relative_to(ROOT)) + '-' + name + '.stdout.txt', stderr=str(PREFIX.relative_to(ROOT)) + '-' + name + '.stderr.txt'))
    write('-case-progress-' + str(len(cases)) + '.json', cases[-1])
    assert result.returncode == 0 and result.stdout.splitlines() == [('PASS ' + name).encode()], name
write('-proof.json', dict(reviewed_revision=INPUT, actual_executed_revision=executed, author_commit=AUTHOR, environment={'PYTHONDONTWRITEBYTECODE': '1'}, pins=pins, preserved_definitions=preserved, existing_cases=cases, new_api_execution=False, fixture_setup='two schema-valid actual Git/process graphs; exits 0/0/7/2', receipt_selectors=list(t.RECEIPT_CASES)))
print('PASS independent final-byte pins9/schema fixtures2/actual captures8/old cases26; no new-API behavior claimed')
