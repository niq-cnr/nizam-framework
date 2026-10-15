"""Independent frozen-bundle verification and exactly one reviewer controls run."""
import hashlib, json, os, pathlib, stat, subprocess, traceback

ROOT = pathlib.Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/121'
RELEASE = 'dc1a90b3e6d7a0b8daab9f25daafcad6c54e4915'
AUTHOR = '92085a4a833d5c175b5d613fc3f215c33675a7b9'
OLD = '849e29c7fa8ca1d711acfb58bd953ce3e200fbe2'
RECOVERY = '615a36c6343cea4e44916293959cd2c9fef8171f'
REVIEWER = '/root/review121_final'
CASES = ('independent-lanes', 'shared-state-serialized', 'reject-terminal-spoof', 'reject-fourth', 'owned-rollback')

def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE)
def blob(ref, path): return git('show', ref + ':' + path)
def read(path): return json.loads((ROOT / path).read_bytes())
def save(name, value):
    with (E / name).open('x') as out: json.dump(value, out, indent=2); out.write('\n')
def check(condition, message):
    if not condition: raise AssertionError(message)
def oid(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def bind(ref, path):
    data = blob(ref, path); mode, kind, identifier = git('ls-tree', ref, '--', path).decode().split('\t')[0].split()
    check(kind == 'blob' and identifier == oid(data), 'Git binding: ' + path)
    return dict(revision=ref, path=path, git_oid=identifier, sha256=sha(data), size_bytes=len(data), mode=mode)

def verify_run(value, ref, wrapper):
    check(value['complete'] is True and len(value['captures']) == 27, 'complete exact27')
    check(value['protected_before'] == value['protected_after'] and len(value['protected_before']) == 272, 'recorded full-mode preservation')
    check(wrapper['actual_exit'] == 0, 'wrapper actual exit')
    for stream, item in wrapper['outputs'].items():
        data = blob(ref, item['path']) if ref else (ROOT / item['path']).read_bytes()
        check(sha(data) == item['sha256'] and len(data) == item['size_bytes'], 'wrapper raw: ' + stream)
    labels = [r['label'] for r in value['captures']]
    check(sum(label.startswith('archive-') for label in labels) == 12, 'archive exact12')
    for row in value['captures']:
        check(type(row['actual_exit']) is int and row['actual_exit'] == row['expected_exit'], 'actual command exit')
        check(row['protected_unchanged'] is True, 'per-command preservation')
        check(row['revision'] == wrapper['exercised_revision'] and row['release_revision'] == value['release_revision'], 'capture revision')
        raw = {}
        for stream in ('stdout', 'stderr'):
            raw[stream] = blob(ref, row[stream]) if ref else (ROOT / row[stream]).read_bytes()
            check(sha(raw[stream]) == row[stream + '_sha256'], 'raw hash: ' + row['label'])
        if row['label'].startswith('archive-'): check(row['actual_exit'] == 0, 'archive exit0')
        elif row['label'].endswith('-semantic-red'):
            check(row['actual_exit'] == 1, 'intended red exit1')
            markers = [line for line in raw['stderr'].decode().splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')]
            check(markers == [row['expected_assertion']], 'exact semantic assertion')
            check(b'FIXTURE_TRACE ' in raw['stdout'] and b'PASS ' not in raw['stdout'], 'fixture executed without false pass')
            traces = [json.loads(line[10:]) for line in raw['stdout'].decode().splitlines() if line.startswith('API_TRACE ')]
            check(traces[-1] == row['intended_api_trace'] and traces[-1].get('returned') is True, 'target API returned before intended assertion')
            last = traces[-1]; case = row['label'].removesuffix('-semantic-red')
            if case == 'independent-lanes': check(last['result']['eligible'] is False and last['result']['conflicts'] == [], 'independent red semantics')
            elif case == 'shared-state-serialized': check(last['result']['eligible'] is True and last['result']['conflicts'] == [], 'conflict red semantics')
            elif case == 'reject-terminal-spoof': check(type(last['authority_approved']) is int and last['authority_approved'] == 1, 'approved int1 red semantics')
            elif case == 'reject-fourth': check(type(last['attempt']) is int and last['attempt'] == 4, 'fourth red semantics')
            elif case == 'owned-rollback': check(last['method'] == 'rollback_owned_attempt' and last['result']['removed'] is False, 'rollback red semantics')
        else:
            check(row['actual_exit'] == 0 and raw['stdout'].decode().splitlines() == ['PASS ' + row['label'].rsplit('-', 1)[0]] and raw['stderr'] == b'', 'positive/restored exact pass')
    for case in CASES:
        triplet = [next(r for r in value['captures'] if r['label'] == case + '-' + stage)['actual_exit'] for stage in ('positive', 'semantic-red', 'restored')]
        check(triplet == [0, 1, 0], 'triplet: ' + case)

def main():
    os.chdir(ROOT)
    check(os.environ.get('PYTHONDONTWRITEBYTECODE') == '1' and os.environ.get('LC_ALL') == 'C', 'reviewer environment')
    revision = git('rev-parse', 'HEAD').decode().strip()
    recovery = json.loads(blob(RECOVERY, '.agent/evidence/121/executable-review3-root-recovery.json'))
    check(recovery['runtime_executions_before_correction'] == 0 and recovery['reviewed_revision'] == RELEASE, 'Root recovery binding')
    paths = dict(source='tools/workflow_assurance.py', tests='tools/test_workflow_assurance.py', helper='.agent/evidence/121/controls3-run.py',
        pack='.agent/evidence/121/controls3-identities.pack', inventory='.agent/evidence/121/controls3-identities.json', contract='.agent/contracts/121.json')
    bindings = {key: bind(RELEASE, path) for key, path in paths.items()}
    expected = dict(source='1d97f06f32713d3944933680d6b2558fd093d26c158da49546d408d5560beb36', tests='c94a59e1330680003a1a92ad5881911f7b99bdced2f01504e4335b80469d25c6', contract='145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e')
    for key, path in paths.items():
        check(blob(RELEASE, path) == (ROOT / path).read_bytes(), 'live frozen input: ' + key)
        if key in expected: check(bindings[key]['sha256'] == expected[key], 'input hash: ' + key)
    old_source = blob(OLD, paths['source']); new_source = blob(RELEASE, paths['source'])
    before = b'except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:'
    # Existing APIs also use this boundary. Only the three additive lane API boundaries changed.
    check(new_source.count(before) == old_source.count(before) - 3, 'exact3 boundary changes')
    check(git('diff', '--numstat', OLD, RELEASE, '--', paths['source']).decode().split()[:2] == ['3', '3'], 'only3 added/removed source lines')
    check(blob(OLD, paths['tests']) == blob(RELEASE, paths['tests']), 'unchanged tests')
    author_seal = json.loads(blob(AUTHOR, '.agent/evidence/121/controls3-author-seal.json'))
    author_run = json.loads(blob(AUTHOR, '.agent/evidence/121/controls3-author-result.json'))
    author_wrapper = json.loads(blob(AUTHOR, '.agent/evidence/121/controls3-author-wrapper.json'))
    verify_run(author_run, AUTHOR, author_wrapper)
    check(len(author_seal['immutable_artifact_pins']) == 65, 'author exact65 artifact pins')
    for pin in author_seal['immutable_artifact_pins']:
        actual = bind(AUTHOR, pin['path'])
        check(all(actual[k] == pin[k] for k in ('git_oid', 'sha256', 'size_bytes', 'mode')), 'author immutable pin: ' + pin['path'])
    for path, identity in author_run['protected_before'].items():
        actual = bind(author_wrapper['exercised_revision'], path)
        check(actual['sha256'] == identity['sha256'] and (actual['mode'] == '100755') == bool(identity['mode'] & 0o111), 'historical protected Git identity: ' + path)
    inventory = read(paths['inventory'])
    check(len(inventory['objects']) == 8 and sha((ROOT / paths['pack']).read_bytes()) == inventory['pack_sha256'], 'pack8 binding')
    for label, identity in inventory['objects'].items():
        data = git('cat-file', 'blob', identity['git_oid'])
        check(sha(data) == identity['sha256'] and oid(data) == identity['git_oid'] and len(data) == identity['size_bytes'], 'packed identity: ' + label)
    save('executable-review3-preflight.json', dict(reviewer=REVIEWER, passed=True, exercised_revision=revision, release_revision=RELEASE,
        author_revision=AUTHOR, author_captures=27, author_pins=65, author_protected=272, source_delta='three new API catch boundaries only',
        tests_unchanged=True, bindings=bindings, recovery=bind(RECOVERY, '.agent/evidence/121/executable-review3-root-recovery.json')))
    argv = ['python3', '.agent/evidence/121/controls3-run.py', '--release-revision', RELEASE, '--run-id', 'reviewer']
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    outputs = {}
    for stream in ('stdout', 'stderr'):
        data = getattr(result, stream); path = E / ('controls3-reviewer-wrapper.' + stream + '.txt')
        with path.open('xb') as out: out.write(data)
        outputs[stream] = dict(path=str(path.relative_to(ROOT)), sha256=sha(data), size_bytes=len(data))
    wrapper = dict(reviewer=REVIEWER, role='independent Evaluator', frozen_helper_author_label='/root/controls121', attempt=3, limit=3,
        argv=argv, cwd=str(ROOT), environment=dict(PYTHONDONTWRITEBYTECODE='1', LC_ALL='C'), exercised_revision=revision,
        release_revision=RELEASE, actual_exit=result.returncode, outputs=outputs)
    save('controls3-reviewer-wrapper.json', wrapper)
    check(result.returncode == 0, 'frozen controls actual nonzero; STOP')
    run = read('.agent/evidence/121/controls3-reviewer-result.json'); verify_run(run, None, wrapper)
    check(run['release_revision'] == RELEASE and run['helper_revision'] == revision, 'own exercised revision')
    check(run['inputs'] == inventory, 'own exact pack inputs')
    for path, identity in run['protected_before'].items():
        current = ROOT / path
        check(sha(current.read_bytes()) == identity['sha256'] and stat.S_IMODE(current.lstat().st_mode) == identity['mode'], 'own full filesystem identity: ' + path)
    save('executable-review3-runtime-check.json', dict(reviewer=REVIEWER, passed=True, exercised_revision=revision, release_revision=RELEASE,
        captures=27, archive_commands=12, triplets=5, restored_blobs=8, protected_files=272, full_filesystem_modes_equal=True,
        source_sha256=expected['source'], test_sha256=expected['tests'], actual_wrapper_exit=result.returncode))
    print('PASS independent current-source exact27, archive12, five 0/1/0 controls, author65 pins, protected272')

if __name__ == '__main__':
    try: main()
    except BaseException:
        traceback.print_exc()
        raise SystemExit(1)
