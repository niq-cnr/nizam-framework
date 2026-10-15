"""Frozen private semantic controls; execute only on explicit Root release."""
import argparse, functools, hashlib, json, os, pathlib, re, stat, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[3]
PREFIX = '.agent/evidence/121/controls1-'
SOURCE = 'f588ad0282ed80d8f380d4f230a95bbfddc2ad2326bcf1189d9aaac8eabbc6a3'
TEST = 'c94a59e1330680003a1a92ad5881911f7b99bdced2f01504e4335b80469d25c6'
CONTRACT = '145efa18ec1e6b2015c5835900afe4dfec6da44af7581dbdf5e3eeecdbdc642e'
INVALID = 'AssertionError: POLICY_ASSERTION: lane invalid request rejected: invalid input accepted'
CONTROLS = (
 ('independent-lanes', (("return {'eligible': not conflicts, 'conflicts': conflicts, 'operation_id': request['operation_id']}", "return {'eligible': bool(conflicts), 'conflicts': conflicts, 'operation_id': request['operation_id']}"),), 'AssertionError: POLICY_ASSERTION: independent lanes eligible'),
 ('shared-state-serialized', (('if paths or fields: conflicts.append', 'if False: conflicts.append'),), 'AssertionError: POLICY_ASSERTION: same file and pointer prefix conflict in lane order'),
 ('reject-terminal-spoof', (("authority['repository'] == policy['repository'] and authority['approved'] is True, 'lane authority not approved'", "authority['repository'] == policy['repository'] and authority['approved'] in (True, 1), 'lane authority not approved'"),), INVALID),
 ('reject-fourth', (("1 <= request['attempt'] <= 3, 'lane attempt outside max3'", "1 <= request['attempt'] <= 4, 'lane attempt outside max3'"), ("counter['attempts'] == request['attempt'] and", "counter['attempts'] == min(request['attempt'], 3) and")), INVALID),
 ('owned-rollback', (("'attempt_root': request['attempt_root'], 'removed': True}", "'attempt_root': request['attempt_root'], 'removed': False}"),), 'AssertionError: POLICY_ASSERTION: owned rollback exact removal result'))


def sha(data): return hashlib.sha256(data).hexdigest()
def oid(data): return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def write(path, data):
    with pathlib.Path(path).open('xb') as handle: handle.write(data)
def git(*args): return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE).decode().strip()
def identity(data): return dict(git_oid=oid(data), sha256=sha(data), size_bytes=len(data), type='blob')
def snapshot():
    paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/121.json', '.agent/run_state.json', '.agent/feature_list_018.json', 'docs/planning/phase_018.yaml']
    paths += [str(p.relative_to(ROOT)) for base in ('schema', '.nizam') for p in (ROOT / base).rglob('*') if p.is_file()]
    return {p: dict(sha256=sha((ROOT / p).read_bytes()), mode=stat.S_IMODE((ROOT / p).lstat().st_mode)) for p in sorted(paths)}


def worker(name, source):
    sys.path.insert(0, str(ROOT / 'tools')); import test_workflow_assurance as tests
    assert name in tests.LANE_CASES and tests.sha((ROOT / 'tools/test_workflow_assurance.py').read_bytes()) == TEST
    api = tests.load_api(pathlib.Path(source)); original = tests.LaneFixture.__init__
    def setup(self, parent):
        original(self, parent)
        print('FIXTURE_TRACE ' + json.dumps(dict(root=str(self.root), attempt=str(self.attempt), base=self.base,
            registration=tests.git(self.root, 'worktree', 'list', '--porcelain'), source=sha(pathlib.Path(source).read_bytes()))), flush=True)
    tests.LaneFixture.__init__ = setup
    for method in ('assess_conflict_lanes', 'verify_isolated_attempt', 'rollback_owned_attempt'):
        actual = getattr(api, method)
        @functools.wraps(actual)
        def traced(repo, request, *, policy, _actual=actual, _method=method):
            row = dict(method=_method, request=repr(request))
            if type(request) is dict: row['attempt'] = request.get('attempt')
            try:
                ref = policy.get('authority_ref'); authority = json.loads((pathlib.Path(repo) / ref['path']).read_bytes())
                row['authority_approved'] = authority.get('approved')
            except (OSError, ValueError, TypeError, KeyError, AttributeError): pass
            try:
                result = _actual(repo, request, policy=policy); row['result'] = result; row['returned'] = True
                return result
            except BaseException as exc:
                row['raised'] = type(exc).__name__; row['diagnostic'] = str(exc)[:400]; raise
            finally: print('API_TRACE ' + json.dumps(row, allow_nan=True), flush=True)
        setattr(api, method, traced)
    tests.run_lane_case(name, api); print('PASS ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', choices=[c[0] for c in CONTROLS]); parser.add_argument('--source')
    parser.add_argument('--release-revision'); parser.add_argument('--run-id'); args = parser.parse_args()
    if args.worker:
        assert args.source and not args.release_revision and not args.run_id; worker(args.worker, args.source); return
    assert args.release_revision and re.fullmatch('[0-9a-f]{40}', args.release_revision), 'explicit Root release revision required'
    assert args.run_id and re.fullmatch('[a-z0-9][a-z0-9-]*', args.run_id)
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert not any(os.environ.get(k) for k in ('GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'))
    os.chdir(ROOT)
    for path, expected in (('tools/workflow_assurance.py', SOURCE), ('tools/test_workflow_assurance.py', TEST), ('.agent/contracts/121.json', CONTRACT)):
        assert sha((ROOT / path).read_bytes()) == expected
        assert subprocess.check_output(['git', '-C', str(ROOT), 'show', args.release_revision + ':' + path]) == (ROOT / path).read_bytes()
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', args.release_revision, 'HEAD'], check=True)
    manifest_path = ROOT / (PREFIX + 'identities.json'); inventory = json.loads(manifest_path.read_bytes())
    pack = (ROOT / (PREFIX + 'identities.pack')).read_bytes(); assert sha(pack) == inventory['pack_sha256']
    prefix = ROOT / (PREFIX + args.run_id); records = []; protected = snapshot(); complete = False
    output_manifest = str(prefix) + '-result.json'; assert not pathlib.Path(output_manifest).exists()
    def capture(label, argv, expected, marker=None, cwd=ROOT, env=None, data=None):
        assert snapshot() == protected
        result = subprocess.run(argv, cwd=cwd, env=env, input=data, capture_output=True)
        out = str(prefix) + '-' + label + '.stdout.txt'; err = str(prefix) + '-' + label + '.stderr.txt'
        write(out, result.stdout); write(err, result.stderr)
        row = dict(label=label, argv=argv, cwd=str(cwd), environment=env or {'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': os.environ.get('LC_ALL')},
            revision=git('rev-parse', 'HEAD'), release_revision=args.release_revision, actual_exit=result.returncode, expected_exit=expected,
            expected_assertion=marker, stdout=str(pathlib.Path(out).relative_to(ROOT)), stderr=str(pathlib.Path(err).relative_to(ROOT)),
            stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr), protected_unchanged=snapshot() == protected)
        records.append(row); assert row['protected_unchanged']; assert result.returncode == expected, row
        if marker:
            assert [line for line in result.stderr.decode().splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')] == [marker]
            assert b'PASS ' not in result.stdout and b'FIXTURE_TRACE ' in result.stdout
            traces = [json.loads(line[10:]) for line in result.stdout.decode().splitlines() if line.startswith('API_TRACE ')]
            assert traces and traces[-1].get('returned') is True, 'target API must return before intended assertion'
            last = traces[-1]; row['intended_api_trace'] = last
            case = label.removesuffix('-semantic-red')
            if case == 'independent-lanes': assert last['result']['eligible'] is False and last['result']['conflicts'] == []
            elif case == 'shared-state-serialized': assert last['result']['eligible'] is True and last['result']['conflicts'] == []
            elif case == 'reject-terminal-spoof': assert type(last['authority_approved']) is int and last['authority_approved'] == 1
            elif case == 'reject-fourth': assert type(last['attempt']) is int and last['attempt'] == 4
            elif case == 'owned-rollback': assert last['method'] == 'rollback_owned_attempt' and last['result']['removed'] is False
        elif label.endswith(('-positive', '-restored')): assert result.stdout.decode().splitlines() == ['PASS ' + label.rsplit('-', 1)[0]]
        return result.stdout
    try:
        with tempfile.TemporaryDirectory(prefix='nizam121-controls1-') as directory:
            private = pathlib.Path(directory); bare = private / 'empty.git'; home = private / 'home'; home.mkdir()
            env = {'PATH': os.defpath, 'HOME': str(home), 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null', 'LC_ALL': 'C'}
            capture('archive-init', ['git', 'init', '--bare', '--template=', str(bare)], 0, cwd=private, env=env)
            def archive(label, *argv, data=None): return capture(label, ['git', '--git-dir', str(bare), *argv], 0, cwd=private, env=env, data=data)
            assert archive('archive-empty', 'cat-file', '--batch-all-objects', '--batch-check') == b''
            assert not (bare / 'objects/info/alternates').exists()
            archive('archive-import', 'index-pack', '--stdin', '--strict', data=pack)
            rows = archive('archive-restored', 'cat-file', '--batch-all-objects', '--batch-check').decode().splitlines()
            assert {r.split()[0] for r in rows} == {v['git_oid'] for v in inventory['objects'].values()}
            recovered = {}
            for label, expected in inventory['objects'].items():
                payload = archive('archive-blob-' + label, 'cat-file', 'blob', expected['git_oid']); assert identity(payload) == expected
                recovered[label] = payload
            assert not (bare / 'objects/info/alternates').exists() and not (bare / 'objects/info/http-alternates').exists()
            assert recovered['source'] == (ROOT / 'tools/workflow_assurance.py').read_bytes()
            assert recovered['tests'] == (ROOT / 'tools/test_workflow_assurance.py').read_bytes()
            assert recovered['helper'] == pathlib.Path(__file__).read_bytes()
            for name, changes, marker in CONTROLS:
                command = [sys.executable, 'tools/test_workflow_assurance.py', '--case', name]
                capture(name + '-positive', command, 0)
                mutant = private / (name + '.py'); write(mutant, recovered[name])
                capture(name + '-semantic-red', [sys.executable, str(pathlib.Path(__file__).resolve()), '--worker', name, '--source', str(mutant)], 1, marker)
                capture(name + '-restored', command, 0)
        complete = True
    finally:
        write(output_manifest, (json.dumps(dict(author='/root/controls121', complete=complete, helper_revision=git('rev-parse', 'HEAD'), release_revision=args.release_revision,
            inputs=inventory, protected_before=protected, protected_after=snapshot(), captures=records), indent=2) + '\n').encode())


if __name__ == '__main__': main()
