#!/usr/bin/env python3
"""Independent feature133 controls; synthetic real Git, never hosted acceptance."""
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch

CHECKS = ('real-git-count-reduction', 'semantic-equivalence', 'fresh-mutations', 'literal-paths-and-modes')
MASKED_AST = '09e5fe17512b479669de145a8498cf0ba0d25dea60e43ecbc486cff62f79cbc9'
ORIGIN = 'https://github.com/niq-cnr/nizam-framework.git'
ENV = 'NIZAM_RECEIPT_BATCH_TEST'


class SetupError(Exception):
    pass


def require(value, diagnostic):
    if not value:
        raise AssertionError(diagnostic)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sealed(value):
    value = copy.deepcopy(value)
    value['identity_sha256'] = sha(canonical({k: v for k, v in value.items() if k != 'identity_sha256'}))
    return value


def git(root, *args, input=None):
    result = subprocess.run(['git', '-C', str(root), *args], input=input, capture_output=True)
    if result.returncode:
        raise SetupError('fixture Git ' + repr(args) + ': ' + result.stderr.decode(errors='replace'))
    return result.stdout.decode().strip()


class Fixture:
    def __init__(self, seed='one'):
        self.temp = tempfile.TemporaryDirectory(prefix='nizam133-')
        self.root = Path(self.temp.name) / 'repo'; self.root.mkdir()
        self.previous = {k: v for k, v in os.environ.items() if k.startswith('GIT_') or k == ENV}
        for key in self.previous: os.environ.pop(key)
        os.environ.update({ENV: 'baseline', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
        try:
            git(self.root, 'init', '--quiet', '--object-format=sha1')
            for key, value in [('user.name', 'Synthetic133'), ('user.email', 'fixture133@example.invalid'), ('commit.gpgsign', 'false'), ('tag.gpgsign', 'false'), ('gc.auto', '0'), ('core.autocrlf', 'false'), ('core.filemode', 'true')]:
                git(self.root, 'config', key, value)
            git(self.root, 'remote', 'add', 'origin', ORIGIN)
            self.inputs = dict(source=[f'src/input{i:02}.txt' for i in range(10)], tests=[f'tests/input{i}.txt' for i in range(4)], tools=[f'tools/input{i}.sh' for i in range(4)], contracts=['contracts/owned.json', 'contracts/unowned.json'], unknown_dependencies=[])
            self.inputs['source'] += ['src/with space.txt', 'src/tab\tname.txt', 'src/new\nline.txt', 'src/café.txt', '-leading.txt', ':(glob)*.txt', 'src/[*?].txt', 'src/colon:name.txt']
            self.expected = {}
            for category in ('source', 'tests', 'tools'):
                for i, path in enumerate(self.inputs[category]):
                    raw = (seed + ':' + path + '\n').encode(); executable = bool(i % 2)
                    self.write(path, raw, executable); self.expected[path] = (raw, executable)
            # Two distinct paths share bytes but not mode: OID is not path authority.
            shared = b'identical object, distinct path and executable mode\n'
            for path, mode in [('src/input00.txt', False), ('tools/input0.sh', True)]:
                self.write(path, shared, mode); self.expected[path] = (shared, mode)
            self.records = {'contracts/owned.json': {'status': 'proposed', 'fixed': 7, 'history': ['original']}, 'contracts/unowned.json': {'fixed': 8}, 'state/progress.json': {'status': 'pending', 'fixed': 9}}
            for path, value in self.records.items():
                raw = json.dumps(value, indent=2).encode() + b'\n'
                self.write(path, raw); self.expected[path] = (raw, False)
            self.commit('independent anchor'); self.anchor = git(self.root, 'rev-parse', 'HEAD')
            self.ownership = {'contracts/owned.json': ['/history', '/status'], 'state/progress.json': ['/status']}
            self.candidate = api.assess_repository(self.root, self.anchor, self.inputs, [ENV], self.ownership)
            self.commit('distinct executed commit', empty=True); self.executed = git(self.root, 'rev-parse', 'HEAD')
            require(self.anchor != self.executed, 'fixture commits must differ')
        except Exception as exc:
            self.close()
            raise SetupError('fixture construction failed: ' + str(exc)) from exc

    def write(self, path, raw, executable=False):
        target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw); target.chmod(0o755 if executable else 0o644)

    def commit(self, message, empty=False):
        git(self.root, 'add', '--all')
        git(self.root, 'commit', '--quiet', *(['--allow-empty'] if empty else []), '-m', message)

    def close(self):
        for key in list(os.environ):
            if key.startswith('GIT_') or key == ENV: os.environ.pop(key)
        os.environ.update(self.previous)
        self.temp.cleanup()

    def __enter__(self): return self
    def __exit__(self, *unused): self.close()

    def readset(self):
        rows = [(commit, entry['path']) for category in ('source', 'tests', 'tools') for entry in self.candidate['assessed_inputs'][category] for commit in (self.anchor, self.executed)]
        return rows + [(self.anchor, entry['path']) for entry in self.candidate['assessed_inputs']['contracts']] + [(self.anchor, path) for path in self.ownership]

    def call(self, candidate=None, revision=None, rejection=None):
        try:
            result = api._receipt_candidate(self.root, self.candidate if candidate is None else candidate, revision)
        except api.AssuranceError as exc:
            require(rejection is not None and any(str(exc).startswith(text) for text in rejection), 'unexpected rejection: ' + str(exc))
            print('EXPECTED_REJECTION ' + str(exc)); return
        except Exception as exc:
            raise AssertionError('unexpected product exception: ' + repr(exc)) from exc
        require(rejection is None, 'intended rejection accepted: ' + repr(rejection))
        require(result is None, 'successful return changed')


class Trace:
    """Observe actual Popen launches; never synthesize a Git result."""
    def __init__(self, fixture, label):
        self.fixture = fixture; self.label = label; self.processes = []; self.entries = {}; self.objects = {}

    def __enter__(self):
        original_popen, original_git, original_blobs = subprocess.Popen, api.git, api.blobs
        def launch(*args, **kwargs):
            process = original_popen(*args, **kwargs)
            self.processes.append((list(args[0] if args else kwargs['args']), process)); return process
        def observe_git(root, *args):
            raw = original_git(root, *args)
            if 'ls-tree' in args:
                commits = set(args).intersection((self.fixture.anchor, self.fixture.executed))
                require(len(commits) == 1, 'unattributed ls-tree revision')
                for row in raw.split(b'\0'):
                    if not row: continue
                    metadata, name = row.split(b'\t', 1); mode, kind, oid = metadata.decode().split()
                    self.entries[(next(iter(commits)), name.decode())] = (mode, kind, oid)
            return raw
        def observe_blobs(root, ids):
            values = original_blobs(root, ids); self.objects.update(values); return values
        self.patches = [patch.object(subprocess, 'Popen', launch), patch.object(api, 'git', observe_git), patch.object(api, 'blobs', observe_blobs)]
        for guard in self.patches: guard.start()
        return self

    def __exit__(self, *unused):
        for guard in reversed(self.patches): guard.stop()
        rows = [dict(argv=argv, pid=p.pid, actual_exit=p.returncode) for argv, p in self.processes]
        print('REAL_GIT_TRACE ' + json.dumps(dict(label=self.label, launches=rows), sort_keys=True))

    def validate(self):
        require(self.processes and all(argv[0] == 'git' and p.returncode == 0 for argv, p in self.processes), 'all counted launches must be successful real Git')
        require(set(self.entries) == set(self.fixture.readset()), 'exact per-revision/path observation set')
        for (revision, path), (mode, kind, oid) in self.entries.items():
            raw, executable = self.fixture.expected[path]
            expected_oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            require((mode, kind, oid) == ('100755' if executable else '100644', 'blob', expected_oid), 'Git path/mode/type observation differs: ' + path)
            require(self.objects.get(oid) == raw, 'actual observed blob bytes differ: ' + path)


def count_reduction():
    with Fixture() as f:
        require(len(set(f.inputs['source'] + f.inputs['tests'] + f.inputs['tools'])) >= 16, 'metric needs >=16 distinct protected paths')
        with Trace(f, 'unchanged-entry-blob-oracle') as oracle:
            for revision, path in f.readset():
                require(api._entry_blob(f.root, revision, path) == f.expected[path], 'oracle bytes/mode must match independent fixture')
        oracle.validate()
        with Trace(f, 'full-candidate-including-fixed-identity') as optimized:
            f.call(revision=f.executed)
        optimized.validate()
        counts = {}
        for label, trace in [('oracle', oracle), ('optimized', optimized)]:
            verbs = {}
            for argv, process in trace.processes:
                verb = next((word for word in argv[3:] if word in ('rev-parse', 'ls-tree', 'cat-file', 'merge-base', 'remote')), 'other')
                verbs[verb] = verbs.get(verb, 0) + 1
            counts[label] = dict(total=len(trace.processes), by_verb=verbs)
        print('REAL_GIT_COUNTS ' + json.dumps(dict(counts=counts, readset_pairs=len(f.readset()), full_candidate_denominator=True, identity_classification='merge-base/remote/tree rev-parse are fixed; commit-resolution rev-parse includes fixed identity and immutable reads; nothing excluded'), sort_keys=True), flush=True)
        require(len(optimized.processes) * 2 <= len(oracle.processes), 'real-git-count-reduction: expected >=50% fewer actual Git launches')


def candidate_change(f, field, value):
    candidate = copy.deepcopy(f.candidate); candidate[field] = value; return sealed(candidate)


def semantics():
    with Fixture() as f:
        f.call(); f.call(revision=f.anchor); f.call(revision=f.executed)
        f.call(candidate_change(f, 'source_tree', '0' * 40), rejection=('receipt candidate actual tree',))
        f.call(candidate_change(f, 'repository', ORIGIN + '/different'), rejection=('receipt actual repository',))
        f.call(candidate_change(f, 'source_commit', '0' * 40), rejection=('Git observation failed:',))
        f.call(candidate_change(f, 'source_commit', f.candidate['source_tree']), rejection=('Git observation failed:',))
        f.call(revision='HEAD', rejection=('invalid receipt executed revision',))
        f.call(revision='0' * 40, rejection=('Git observation failed:',))
        f.call(revision=f.candidate['source_tree'], rejection=('Git observation failed:',))
        git(f.root, 'tag', '--annotate', 'annotated', '-m', 'noncommit object', f.anchor)
        tag = git(f.root, 'rev-parse', 'annotated')
        f.call(candidate_change(f, 'source_commit', tag), rejection=('receipt candidate exact commit',))
        f.call(revision=tag, rejection=('receipt executed exact commit',))
        orphan = git(f.root, 'commit-tree', f.candidate['source_tree'], input=b'independent unrelated commit\n')
        f.call(revision=orphan, rejection=('Git observation failed:',))
        candidate = copy.deepcopy(f.candidate); candidate['assessed_inputs']['source'][0]['sha256'] = '0' * 64
        f.call(sealed(candidate), rejection=('receipt protected Git input changed',))
        # Only the anchor is wrong: executed/current facts match the altered identity.
        path = 'src/input00.txt'; raw, mode = f.expected[path]
        for new_raw, new_mode in ((raw + b'anchor digest discriminator', mode), (raw, not mode)):
            f.write(path, new_raw, new_mode); f.commit('isolated anchor discriminator')
            candidate = copy.deepcopy(f.candidate)
            entry = next(e for e in candidate['assessed_inputs']['source'] if e['path'] == path)
            entry.update(sha256=sha(new_raw), executable=new_mode)
            try: f.call(sealed(candidate), rejection=('receipt protected Git input changed',))
            finally: git(f.root, 'checkout', '--quiet', '--force', '--detach', f.executed)
            f.call()
        for path in ('contracts/owned.json', 'contracts/unowned.json'):
            candidate = copy.deepcopy(f.candidate)
            next(e for e in candidate['assessed_inputs']['contracts'] if e['path'] == path)['sha256'] = '0' * 64
            f.call(sealed(candidate), rejection=('receipt contract assessed digest',))
        for path in f.ownership:
            raw, mode = f.expected[path]; value = copy.deepcopy(f.records[path]); value['status'] = 'allowed'
            if 'history' in value: value['history'].append('append allowed')
            f.write(path, canonical(value)); f.call(); f.write(path, raw, mode)
            value['fixed'] = 999; f.write(path, canonical(value))
            f.call(rejection=('unowned record value changed:',)); f.write(path, raw, mode); f.call()
        path = 'contracts/owned.json'; value = copy.deepcopy(f.records[path]); value['history'][0] = 'rewritten'
        f.write(path, canonical(value)); f.call(rejection=('history original prefix changed',)); f.write(path, f.expected[path][0]); f.call()
        candidate = copy.deepcopy(f.candidate); candidate['environment']['runtime']['version'] += '-wrong'
        f.call(sealed(candidate), rejection=('receipt observed environment changed',))


def mutations():
    with Fixture() as f:
        f.call()
        for path in ('src/input00.txt', 'contracts/unowned.json', 'state/progress.json'):
            raw, mode = f.expected[path]; target = f.root / path
            if path.startswith('state/'):
                value = copy.deepcopy(f.records[path]); value['fixed'] += 1; altered = canonical(value)
                diagnostic = ('unowned record value changed:',)
            else:
                altered = raw + b' '; diagnostic = ('receipt protected current input changed',) if path.startswith('src/') else ('receipt unowned contract changed',)
            f.write(path, altered, mode); f.call(rejection=diagnostic); f.write(path, raw, mode); f.call()
            target.unlink(); target.symlink_to(f.root / 'tests/input0.txt')
            f.call(rejection=('symlink path component:',)); target.unlink(); f.write(path, raw, mode); f.call()
            target.unlink(); target.mkdir()
            f.call(rejection=('missing/nonregular file:',)); target.rmdir(); f.write(path, raw, mode); f.call()
        for path in ('src/input00.txt', 'contracts/owned.json', 'state/progress.json'):
            raw, mode = f.expected[path]; f.write(path, raw, not mode)
            f.call(rejection=('receipt protected current input changed', 'receipt record mode changed')); f.write(path, raw, mode); f.call()
        directory = f.root / 'src'; saved = f.root / 'saved-src'; directory.rename(saved); directory.symlink_to(saved)
        try: f.call(rejection=('symlink path component:',))
        finally: directory.unlink(); saved.rename(directory)
        f.call()
        os.environ[ENV] = 'mutated'; f.call(rejection=('receipt observed environment changed',)); os.environ[ENV] = 'baseline'; f.call()
        os.environ.pop(ENV); f.call(rejection=('receipt observed environment changed',)); os.environ[ENV] = 'baseline'; f.call()
        # Standalone never owned hardlink policy; inherited48 tests its caller boundary.
        alias = Path(f.temp.name) / 'outside-hardlink'; os.link(f.root / 'src/input00.txt', alias)
        try: f.call()
        finally: alias.unlink()
        f.call()
        for expression in (f.anchor + ':src/input00.txt', f.executed):
            oid = git(f.root, 'rev-parse', expression); obj = f.root / '.git/objects' / oid[:2] / oid[2:]
            raw = obj.read_bytes(); mode = stat.S_IMODE(obj.stat().st_mode); obj.unlink()
            try: f.call(rejection=('missing/nonblob Git input', 'Git observation failed:'))
            finally: obj.write_bytes(raw); obj.chmod(mode)
            f.call()
        with Fixture('different-root') as other:
            other.call(); other.call(f.candidate, rejection=('Git observation failed:',)); other.call()
        f.call()


def literal_paths():
    with Fixture() as f:
        for revision, path in f.readset():
            require(api._entry_blob(f.root, revision, path) == f.expected[path], 'literal path oracle observation')
        f.call()
        for name in ('src', 'src/absent', 'src/*', ':(glob)src/*'):
            candidate = copy.deepcopy(f.candidate); candidate['assessed_inputs']['source'][0]['path'] = name
            candidate['assessed_inputs']['source'].sort(key=lambda e: e['path'])
            f.call(sealed(candidate), rejection=('unsafe entry Git input', 'missing entry Git input:', 'missing/nonblob Git input'))
        for path in ('../outside', '/absolute', 'src/../input00.txt', 'src//input00.txt', '.git/config'):
            candidate = copy.deepcopy(f.candidate); candidate['assessed_inputs']['source'][0]['path'] = path
            candidate['assessed_inputs']['source'].sort(key=lambda e: e['path'])
            f.call(sealed(candidate), rejection=('unsafe or aliased relative path:',))
        path = 'src/input00.txt'; oid = git(f.root, 'rev-parse', f.anchor + ':' + path)
        for mode, object_id in [('100755', oid), ('120000', oid), ('160000', f.anchor)]:
            git(f.root, 'update-index', '--cacheinfo', mode, object_id, path)
            git(f.root, 'commit', '--quiet', '-m', 'isolated executed mode/type mutation')
            try: f.call(revision=git(f.root, 'rev-parse', 'HEAD'), rejection=('receipt protected Git input changed', 'unsafe entry Git input', 'missing/nonblob Git input'))
            finally: git(f.root, 'checkout', '--quiet', '--force', '--detach', f.executed)
            f.call()
        git(f.root, 'update-index', '--force-remove', '--', path); git(f.root, 'commit', '--quiet', '-m', 'isolated missing executed path')
        try: f.call(rejection=('missing entry Git input:', 'missing/nonblob Git input'))
        finally: git(f.root, 'checkout', '--quiet', '--force', '--detach', f.executed)
        f.call()
        raw, mode = f.expected[path]; f.write(path, raw + b'changed Git bytes', mode); f.commit('isolated executed digest mutation')
        try: f.call(rejection=('receipt protected Git input changed',))
        finally: git(f.root, 'checkout', '--quiet', '--force', '--detach', f.executed)
        f.call()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=CHECKS)
    parser.add_argument('--check-historical-ast-freeze', action='store_true',
                        help='Opt-in historical feature-133 whole-module AST freeze check')
    args = parser.parse_args()
    try:
        if args.check_historical_ast_freeze:
            tree = ast.parse(Path(__file__).with_name('workflow_assurance.py').read_bytes())
            target = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_receipt_candidate')
            target.body = []
            dump_options = {'show_empty': True} if sys.version_info >= (3, 13) else {}
            require(sha(ast.dump(tree, include_attributes=False, **dump_options).encode()) == MASKED_AST, 'product AST outside _receipt_candidate body changed')
        global api
        import workflow_assurance as api
        actions = dict(zip(CHECKS, (count_reduction, semantics, mutations, literal_paths)))
        for name in ((args.check,) if args.check else CHECKS):
            actions[name](); print('PASS ' + name, flush=True)
        return 0
    except AssertionError as exc:
        print('ASSERTION_FAILURE: ' + str(exc), file=sys.stderr); return 1
    except Exception as exc:
        print('SETUP_ERROR: ' + repr(exc), file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
