"""Independent narrow static audit; no acceptance bank or private controls execution."""
import ast, hashlib, json, os, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT)
OLD = 'a8ba0c53ac5f646d50df2ae58e622f4b231aafc6'
AUTHOR = '1d0f731346ee4bceb2aa13f27383df9bf8e5a613'
AUTHORED = 'b680724dab6dc7df93ec94428cbcc930ab6f3774'
INPUT = '4f0f5f885f899d09275f3d259367128a923b135e'
BASE = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
TEST = 'tools/test_workflow_assurance.py'
SOURCE = 'tools/workflow_assurance.py'
def git(*args): return subprocess.check_output(['git', *args])
def blob(ref, path): return git('show', ref + ':' + path)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return pathlib.Path(path).read_bytes()
def tree(raw): return ast.parse(raw)
def dump(node): return ast.dump(node, include_attributes=False)
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
seal = json.loads(read('.agent/evidence/121/author3-provisional-seal.json'))
assert len(seal['files']) == 14
for path, pin in seal['files'].items():
    assert sha(read(path)) == pin['sha256'] == sha(blob(AUTHOR, path)), path
    assert git('hash-object', path).decode().strip() == pin['git_blob'], path
assert read(SOURCE) == blob('704e19563827171dc001f72056b91707303d7cbe', SOURCE) == blob(OLD, SOURCE)
assert read('.agent/contracts/121.json') == blob(OLD, '.agent/contracts/121.json')
contract = json.loads(read('.agent/contracts/121.json')); assert contract['status'] == 'approved'
assert sha(read(TEST)) == 'c94a59e1330680003a1a92ad5881911f7b99bdced2f01504e4335b80469d25c6'
assert sha(read(SOURCE)) == 'f588ad0282ed80d8f380d4f230a95bbfddc2ad2326bcf1189d9aaac8eabbc6a3'
assert sha(read('.agent/contracts/121.json')) == '145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e'
old, new, base = blob(OLD, TEST), read(TEST), blob(BASE, TEST)
assert old.split(b'LANE_CASES =')[0] == new.split(b'LANE_CASES =')[0]
assert base.split(b'def main():')[0] == new.split(b'LANE_CASES =')[0]
names = ('require', 'lane_reject', 'rejected')
def assertions(raw):
    return [dump(n) for n in ast.walk(tree(raw)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names]
assert assertions(old) == assertions(new)
def definitions(raw):
    return {n.name: dump(n) for n in tree(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
assert definitions(old)['main'] == definitions(new)['main']
assert all(definitions(new)[k] == v for k, v in definitions(base).items() if k != 'main')
expected = ('independent-lanes', 'shared-state-serialized', 'reject-terminal-spoof', 'reject-fourth', 'owned-rollback')
assign = next(n for n in tree(new).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'LANE_CASES' for t in n.targets))
assert ast.literal_eval(assign.value) == expected
assert len(contract['verification']) == 5
assert all(row['command'].endswith('--case ' + name) for row, name in zip(contract['verification'], expected))
# Every changed test line is an assignment/restoration copy, never a changed condition.
changes = git('diff', '--unified=0', OLD, AUTHORED, '--', TEST).decode().splitlines()
changed = [line[1:] for line in changes if line[:1] in ('+', '-') and not line.startswith(('+++', '---'))]
assert len(changed) == 27 and all('copy.deepcopy' in line or line.strip().startswith(('self.request.update(changes)', 'f.request = original', 'f.policy = policy')) for line in changed)
numstat = git('diff', '--numstat', BASE, 'HEAD', '--', TEST).decode().split()
assert sum(map(int, numstat[:2])) == 276 <= contract['budget']['independent_tests'] == 450
preserved = []
for path in git('ls-tree', '-r', '--name-only', OLD, '.agent/evidence/121').decode().splitlines():
    if path.endswith('-seal.json'):
        assert read(path) == blob(OLD, path), path
        preserved.append(path)
failure = json.loads(read('.agent/evidence/121/source1-root-failure-capture.json'))
assert failure['actual_exit'] == 1 and failure['completed_markers'] == 37
for path, digest in failure['files_sha256'].items(): assert sha(read(path)) == digest, path
for record in seal['actual_commands']:
    assert record['revision'] == AUTHORED and type(record['actual_exit']) is int and record['actual_exit'] == 0
    for stream in ('stdout', 'stderr'): assert sha(read(record[stream])) == record[stream + '_sha256']
assert read('.agent/evidence/121/author3-independent-lanes.stdout.txt') == b'PASS independent-lanes\n'
lines = read('.agent/evidence/121/author3-alias-proof.stdout.txt').decode().splitlines()
frozen, corrected = json.loads(lines[1]), json.loads(lines[2])
for key in ('request_saved_snapshot_mutated', 'policy_saved_snapshot_mutated'):
    assert frozen[key] is True and corrected[key] is False
assert frozen['label'] == 'frozen' and corrected['label'] == 'corrected'
assert frozen['schemas'] == corrected['schemas'] == ['contract', 'run_state', 'feature_list']
assert 'PASS bounded real fixture/schema' in lines[-1]
proof = dict(reviewed_revision=INPUT, author_revision=AUTHOR, authored_revision=AUTHORED,
    exercised_revision=git('rev-parse', 'HEAD').decode().strip(), seal_pins_verified=14,
    source_sha256=sha(read(SOURCE)), test_sha256=sha(new), approved_contract_sha256=sha(read('.agent/contracts/121.json')),
    inherited37_prefix_unchanged=True, inherited_definitions_unchanged=True,
    acceptance_assertion_calls_unchanged=len(assertions(new)), ordered_lane_cases=expected,
    whole121_test_lines=276, allowance=450, historical_seals_preserved=preserved,
    original_failed_capture_preserved=True, author_actual_commands_verified=seal['actual_commands'],
    snapshot_observations=dict(frozen=frozen, corrected=corrected), own_runtime_lane_tests=False,
    limitation='Managed .ocr skill absent; installed AGF/execution independent review performed. No OCR phase claim, full bank, private controls or final executable QA claim.')
pathlib.Path('.agent/evidence/121/provisional-review3-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print('PASS independent static audit: 14 pins, unchanged 37 prefix/assertions/inventories, fixture copies, 276/450, preserved failures/seals, actual alias0 and independent-lanes0 evidence')
