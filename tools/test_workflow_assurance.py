#!/usr/bin/env python3
"""Independent behavioral acceptance for Workflow Assurance feature 115."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

BASE = '9ebfd03883486a205ac8c3a211f0cac0af5fddba'
ROOT = Path(__file__).resolve().parents[1]
CASES = ('identity-positive', 'invalidate-source', 'invalidate-contract',
         'invalidate-tests', 'invalidate-tool', 'invalidate-environment',
         'invalidate-unknown', 'record-continuity', 'reject-unowned-field',
         'reject-history-edit', 'allow-owned-append')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError('POLICY_ASSERTION: ' + message)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def load_api(path=None):
    path = path or ROOT / 'tools/workflow_assurance.py'
    spec = importlib.util.spec_from_file_location('assurance_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejected(api, operation, message):
    try:
        operation()
    except api.AssuranceError as exc:
        require(bool(str(exc)), message + ': empty diagnostic')
        return
    require(False, message + ': invalid input accepted')


class Fixture:
    def __init__(self, parent):
        self.root = Path(parent) / 'repo'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.email', 'acceptance@example.invalid')
        git(self.root, 'config', 'user.name', 'Independent Acceptance')
        git(self.root, 'remote', 'add', 'origin', 'https://example.invalid/fixture.git')
        self.inputs = dict(source=['src/code.py'], contracts=['contract.json'],
                           tests=['tests/test.py'], tools=['tools/check.py'],
                           unknown_dependencies=[])
        for path, data in {'src/code.py': 'value = 1\n', 'contract.json': '{"history":[],"revision":1,"status":"pending"}',
                           'tests/test.py': 'assert True\n', 'tools/check.py': '# tool\n',
                           'other.txt': 'unassessed but tracked\n',
                           '.gitignore': 'ignored/\n',
                           'record.json': json.dumps(record())}.items():
            self.write(path, data)
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'immutable acceptance anchor')
        self.commit = git(self.root, 'rev-parse', 'HEAD')
        self.mask = {'record.json': ['/current_feature', '/history', '/status']}

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data)

    def assess(self, api, **kwargs):
        return api.assess_repository(self.root, kwargs.get('commit', self.commit),
                                     kwargs.get('inputs', self.inputs),
                                     kwargs.get('names', ['NIZAM_WA_TEST_VALUE']),
                                     kwargs.get('mask', self.mask))


def record():
    return {'phase': '017', 'budget': 5400, 'operator': {'approved': True},
            'current_feature': '115', 'status': 'in_progress',
            'history': [{'kind': 'gate', 'approved': True, 'count': 1}]}


def identity_positive(api, f):
    actual = f.assess(api)
    require(set(actual) == {'schema_version', 'repository', 'source_commit', 'source_tree',
                           'assessed_inputs', 'environment', 'record_ownership',
                           'identity_sha256'}, 'identity has closed keys')
    require(type(actual['schema_version']) is int and actual['schema_version'] == 1,
            'identity schema version is integer one')
    require(actual['repository'] == git(f.root, 'remote', 'get-url', 'origin'), 'observed origin')
    require(actual['source_commit'] == f.commit, 'explicit source commit')
    require(actual['source_tree'] == git(f.root, 'rev-parse', f.commit + '^{tree}'), 'actual Git tree')
    for category in ('source', 'contracts', 'tests', 'tools'):
        expected = [{'path': path, 'sha256': sha((f.root / path).read_bytes()),
                     'executable': bool((f.root / path).stat().st_mode & 0o111)}
                    for path in sorted(f.inputs[category])]
        require(canonical(actual['assessed_inputs'][category]) == canonical(expected), 'observed typed ' + category + ' bytes/mode')
    env_values = list(flatten(actual['environment']))
    for value in (platform.python_implementation(), platform.python_version(),
                  platform.system(), platform.machine(), os.environ['NIZAM_WA_TEST_VALUE']):
        require(value in env_values, 'observed environment bound: ' + value)
    require(actual['record_ownership'] == f.mask, 'exact record ownership')
    body = {k: v for k, v in actual.items() if k != 'identity_sha256'}
    require(actual['identity_sha256'] == sha(canonical(body)), 'canonical actual identity hash')
    require(api.compare_identity(actual, copy.deepcopy(actual)) is True, 'same identity positive')
    malformed = copy.deepcopy(actual); malformed['identity_sha256'] = '0' * 64
    rejected(api, lambda: api.compare_identity(actual, malformed), 'reject fabricated digest')
    malformed = copy.deepcopy(actual); malformed['extra'] = True
    rejected(api, lambda: api.compare_identity(actual, malformed), 'reject unknown identity field')
    malformed = copy.deepcopy(actual); malformed['schema_version'] = True
    malformed['identity_sha256'] = sha(canonical({k: v for k, v in malformed.items() if k != 'identity_sha256'}))
    rejected(api, lambda: api.compare_identity(actual, malformed), 'reject bool schema version')
    cli_controls(api, f, actual)
    git(f.root, 'remote', 'remove', 'origin')
    rejected(api, lambda: f.assess(api), 'missing origin is not identity')


def cli_controls(api, f, identity):
    controls = f.root.parent / 'cli-controls'; controls.mkdir()
    inputs = controls / 'inputs.json'; names = controls / 'names.json'; mask = controls / 'mask.json'
    inputs.write_text(json.dumps(f.inputs)); names.write_text('["NIZAM_WA_TEST_VALUE"]'); mask.write_text(json.dumps(f.mask))
    command = [sys.executable, api.__file__, 'assess', '--repo', str(f.root),
               '--source-commit', f.commit, '--inputs', str(inputs), '--environment-names', str(names), '--record-ownership', str(mask)]
    result = subprocess.run(command, capture_output=True, text=True)
    require(result.returncode == 0 and result.stdout.strip(), 'CLI actual assess succeeds after fixture setup')
    require(canonical(json.loads(result.stdout)) == canonical(identity), 'CLI assess matches observed API identity')
    text = inputs.read_text(); inputs.write_text(text[:-1] + ',"source":' + json.dumps(f.inputs['source']) + '}')
    result = subprocess.run(command, capture_output=True, text=True)
    require(result.returncode != 0 and result.stderr.strip() and not result.stdout.strip(), 'CLI duplicate manifest key rejected after successful setup')
    inputs.write_text(text)
    before = controls / 'before.json'; after = controls / 'after.json'; fields = controls / 'fields.json'
    before.write_text(json.dumps(record())); after.write_text(json.dumps(record())); fields.write_text('[]')
    command = [sys.executable, api.__file__, 'record', '--before', str(before), '--after', str(after), '--owned-fields', str(fields)]
    result = subprocess.run(command, capture_output=True, text=True)
    require(result.returncode == 0, 'CLI unchanged valid record positive')
    for data in (after.read_text()[:-1] + ',"phase":"017"}', after.read_text().replace('5400', 'NaN')):
        after.write_text(data); result = subprocess.run(command, capture_output=True, text=True)
        require(result.returncode != 0 and result.stderr.strip(), 'CLI duplicate/nonfinite record rejected after positive setup')


def flatten(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from flatten(child)
    elif isinstance(value, list):
        for child in value:
            yield from flatten(child)
    else:
        yield value


def category_drift(api, f, category):
    original = f.assess(api)
    path = f.inputs[category][0]; target = f.root / path
    saved = target.read_bytes(); target.write_bytes(saved + b'changed\n')
    rejected(api, lambda: f.assess(api), category + ' current bytes differ from immutable anchor')
    git(f.root, 'add', path)
    rejected(api, lambda: f.assess(api), category + ' staged drift rejected')
    target.write_bytes(saved); git(f.root, 'add', path)
    require(api.compare_identity(original, f.assess(api)) is True, category + ' restoration accepted')
    target.chmod(target.stat().st_mode | 0o111)
    rejected(api, lambda: f.assess(api), category + ' executable mode drift rejected')
    target.chmod(0o644); target.unlink()
    rejected(api, lambda: f.assess(api), category + ' deletion rejected')


def environment_drift(api, f):
    original = f.assess(api)
    os.environ['NIZAM_WA_TEST_VALUE'] = 'changed-observed-value'
    changed = f.assess(api)
    require(api.compare_identity(original, changed) is False, 'environment drift invalidates')
    del os.environ['NIZAM_WA_TEST_VALUE']
    rejected(api, lambda: f.assess(api), 'missing environment variable rejected')
    for names in (['DUP', 'DUP'], [1], ['']):
        rejected(api, lambda names=names: f.assess(api, names=names), 'invalid environment names rejected')
    os.environ['NIZAM_WA_TEST_VALUE'] = 'initial-observed-value'
    require(api.compare_identity(original, f.assess(api)) is True, 'restored environment continuity')


def unknown_drift(api, f):
    original = f.assess(api)
    for path in ('other.txt', 'untracked.txt', 'ignored/build.bin'):
        target = f.root / path; saved = target.read_bytes() if target.exists() else None
        f.write(path, 'unknown mutation\n')
        rejected(api, lambda: f.assess(api), 'unknown tracked/untracked/ignored path: ' + path)
        if saved is None: target.unlink()
        else: target.write_bytes(saved)
    require(api.compare_identity(original, f.assess(api)) is True, 'unknown scratch removal restores identity')
    bad = copy.deepcopy(f.inputs); bad['unknown_dependencies'] = ['unknown']
    rejected(api, lambda: f.assess(api, inputs=bad), 'explicit unknown dependencies rejected')
    for path in ('/etc/passwd', '../other.txt', 'src/../src/code.py', 'src//code.py',
                 'src/./code.py', r'src\code.py', '.git/config', 'src', 'missing.py'):
        bad = copy.deepcopy(f.inputs); bad['source'] = [path]
        rejected(api, lambda bad=bad: f.assess(api, inputs=bad), 'unsafe/missing path: ' + path)
    bad = copy.deepcopy(f.inputs); bad['tools'] = list(bad['source'])
    rejected(api, lambda: f.assess(api, inputs=bad), 'cross-category alias rejected')
    bad = copy.deepcopy(f.inputs); bad['extra'] = []
    rejected(api, lambda: f.assess(api, inputs=bad), 'manifest extra key rejected')
    target = f.root / 'src/code.py'; saved = target.read_bytes(); target.unlink()
    target.symlink_to('../other.txt')
    rejected(api, lambda: f.assess(api), 'symlink leaf rejected')
    target.unlink(); target.write_bytes(saved)
    git(f.root, 'mv', 'src', 'src-real')
    (f.root / 'src').symlink_to('src-real', target_is_directory=True)
    rejected(api, lambda: f.assess(api), 'symlink parent rejected')
    rejected(api, lambda: f.assess(api, commit='HEAD'), 'ambient symbolic commit rejected')


def continuity(api, f):
    original = f.assess(api)
    different_mask = {'record.json': ['/status']}
    require(api.compare_identity(original, f.assess(api, mask=different_mask)) is False, 'valid unchanged record masks bind distinct identities')
    contract_bytes = (f.root / 'contract.json').read_bytes()
    contract_mask = {**f.mask, 'contract.json': ['/history', '/status']}
    masked_identity = f.assess(api, mask=contract_mask)
    f.write('contract.json', '{"revision":1,"status":"complete","history":[{"kind":"capture"}]}')
    current = f.assess(api, mask=contract_mask)
    require(api.compare_identity(masked_identity, current) is True, 'masked assessed contract retains immutable canonical baseline digest')
    require(current['assessed_inputs']['contracts'][0]['sha256'] == sha(canonical(json.loads(contract_bytes))), 'contract identity uses canonical baseline bytes')
    f.write('contract.json', '{"revision":2,"status":"complete","history":[{"kind":"capture"}]}')
    rejected(api, lambda: f.assess(api, mask=contract_mask), 'masked contract still rejects unowned revision')
    (f.root / 'contract.json').write_bytes(contract_bytes)
    after = record(); after['status'] = 'complete'; after['history'].append({'kind': 'capture'})
    f.write('record.json', json.dumps(after, indent=3))
    require(api.compare_identity(original, f.assess(api)) is True, 'allowed record-only bytes retain identity')
    git(f.root, 'add', 'record.json'); git(f.root, 'commit', '-qm', 'record-only later head')
    require(git(f.root, 'rev-parse', 'HEAD') != f.commit, 'actual HEAD advanced')
    require(api.compare_identity(original, f.assess(api)) is True, 'explicit anchor survives ambient HEAD')
    rejected(api, lambda: f.assess(api, mask={'record.json': ['/status']}), 'changed ownership mask cannot authorize old append')
    # Strict JSON is exercised via actual tracked record parsing, not json.loads in this runner.
    for data in ('{"status":"complete","status":"complete"}', '{"x":NaN}', '[]', '{broken'):
        f.write('record.json', data)
        rejected(api, lambda: f.assess(api), 'strict record JSON rejected: ' + data)


def unowned(api, f):
    before = record(); fields = ['/status', '/current_feature', '/history']
    for key, value in (('phase', '999'), ('budget', 9999), ('operator', {'approved': False})):
        after = copy.deepcopy(before); after[key] = value
        rejected(api, lambda after=after: api.verify_record_update(before, after, fields), 'unowned ' + key)
    after = copy.deepcopy(before); after['operator']['approved'] = 1
    rejected(api, lambda: api.verify_record_update(before, after, fields), 'bool vs integer is not continuity')
    for mutation in ('extra', 'remove', 'nested'):
        after = copy.deepcopy(before)
        if mutation == 'extra': after['extra'] = True
        elif mutation == 'remove': del after['status']
        else: after['operator']['extra'] = True
        rejected(api, lambda after=after: api.verify_record_update(before, after, fields), 'key set ' + mutation)
    for invalid in ([ '/operator'], ['/history/0'], ['/missing'], ['/status', '/status'],
                    ['/status/child'], ['status'], [''], ['/a~2b']):
        rejected(api, lambda invalid=invalid: api.verify_record_update(before, before, invalid), 'invalid owned pointer ' + repr(invalid))
    for bad in ({'x': float('nan')}, {'x': (1,)}, {'x': {1: 'bad'}}, []):
        rejected(api, lambda bad=bad: api.verify_record_update(bad, bad, []), 'non-JSON record rejected')
    f.write('record.json', json.dumps({**before, 'budget': 9999}))
    rejected(api, lambda: f.assess(api), 'nonassessed owned record still checked')
    f.write('record.json', json.dumps(before))
    f.write('src/code.py', '{"value":1}')
    git(f.root, 'add', 'src/code.py'); git(f.root, 'commit', '-qm', 'valid JSON source for mask-permission boundary')
    f.commit = git(f.root, 'rev-parse', 'HEAD')
    rejected(api, lambda: f.assess(api, mask={**f.mask, 'src/code.py': ['/value']}), 'valid JSON source cannot receive record mask')


def history_edit(api, f):
    before = record()
    for history in ([], [{'kind': 'edited', 'approved': True, 'count': 1}],
                    [{'kind': 'gate', 'approved': 1, 'count': 1}], {}, None):
        after = copy.deepcopy(before); after['history'] = history
        rejected(api, lambda after=after: api.verify_record_update(before, after, ['/history']), 'exact typed history prefix')
    after = copy.deepcopy(before); after['history'].append({'kind': 'new'})
    rejected(api, lambda: api.verify_record_update(before, after, ['/status']), 'unowned history append rejected')
    f.write('record.json', json.dumps({**before, 'history': []}))
    rejected(api, lambda: f.assess(api), 'repository record history edit rejected')


def owned_append(api, f):
    before = record(); after = copy.deepcopy(before)
    after['status'] = 'complete'; after['current_feature'] = None
    # Owned leaves retain type, including rejecting string-to-null.
    rejected(api, lambda: api.verify_record_update(before, after, ['/status', '/current_feature']), 'owned type change denied')
    after['current_feature'] = '116'; after['history'].append({'kind': 'captured', 'result': True})
    require(api.verify_record_update(before, after, ['/status', '/current_feature', '/history']) is True, 'owned scalar and history append allowed')
    require(api.verify_record_update(before, copy.deepcopy(before), []) is True, 'unchanged no-owner record allowed')
    escaped = {'a/b': {'~leaf': 1}, 'history': []}; changed = copy.deepcopy(escaped); changed['a/b']['~leaf'] = 2
    require(api.verify_record_update(escaped, changed, ['/a~1b/~0leaf']) is True, 'RFC6901 escaped scalar pointer')
    original = f.assess(api); f.write('record.json', json.dumps(after))
    require(api.compare_identity(original, f.assess(api)) is True, 'owned append assessed identity positive')


def run_case(name, api):
    saved = os.environ.get('NIZAM_WA_TEST_VALUE')
    os.environ['NIZAM_WA_TEST_VALUE'] = 'initial-observed-value'
    try:
        with tempfile.TemporaryDirectory(prefix='nizam-wa115-') as root:
            f = Fixture(root)
            if name.startswith('invalidate-') and name.split('-')[1] in ('source', 'contract', 'tests', 'tool'):
                category_drift(api, f, {'contract': 'contracts', 'tool': 'tools'}.get(name.split('-')[1], name.split('-')[1]))
            else:
                {'identity-positive': identity_positive, 'invalidate-environment': environment_drift,
                 'invalidate-unknown': unknown_drift, 'record-continuity': continuity,
                 'reject-unowned-field': unowned, 'reject-history-edit': history_edit,
                 'allow-owned-append': owned_append}[name](api, f)
    finally:
        if saved is None: os.environ.pop('NIZAM_WA_TEST_VALUE', None)
        else: os.environ['NIZAM_WA_TEST_VALUE'] = saved


BASE_CASES = CASES
BUNDLE_CASES = ('reject-self-review', 'reject-seal-change', 'reject-missing-red',
                'reject-setup-as-red', 'independent-handoff')
CASES = BASE_CASES + BUNDLE_CASES


BundleFixture = load_api(ROOT / 'tools/fixtures/workflow_assurance/bundle_fixtures.py').BundleFixture


def bundle_rejected(api, fixture, message):
    try: api.verify_acceptance_bundle(fixture.root, fixture.bundle, fixture.review)
    except api.AssuranceError as exc:
        require(bool(str(exc)), message + ': meaningful diagnostic'); return
    require(False, message + ': invalid policy accepted')


def bundle_mutate(f, name):
    if name == 'reject-self-review':
        f.bundle['roles']['acceptance_reviewer'] = copy.deepcopy(f.bundle['roles']['test_author']); f.refresh()
    elif name == 'reject-seal-change':
        f.bundle['seal_sha256'] = '0' * 64
    elif name == 'reject-missing-red':
        del f.row(name)['red']; f.refresh()
    elif name == 'reject-setup-as-red':
        row = f.row(name); path = row['red']['path']
        text = (f.root / path).read_text().replace('EXIT: 1', 'EXIT: 127') + 'ModuleNotFoundError: transport fixture\n'
        f.write(path, text.encode()); row['red']['sha256'] = sha(text.encode()); f.refresh()
    elif name == 'independent-handoff': f.transition()
    else: require(False, 'unknown mutation')


def bundle_isolated_negative(api, change, message):
    with tempfile.TemporaryDirectory(prefix='nizam-bundle-negative-') as parent:
        f = BundleFixture(parent); change(f); bundle_rejected(api, f, message)


def run_bundle_case(name, api):
    require(name in CASES, 'known116 case')
    require(callable(getattr(api, 'verify_acceptance_bundle', None)), '116 API availability; never commissioning red')
    with tempfile.TemporaryDirectory(prefix='nizam-bundle-') as parent:
        f = BundleFixture(parent)
        require(api.verify_acceptance_bundle(f.root, f.bundle, f.review) is True, name + ' valid baseline positive')
        bundle_mutate(f, name)
        if name == 'independent-handoff':
            require(api.verify_acceptance_bundle(f.root, f.bundle, f.review) is True, 'independent-handoff immutable baseline survives later record-only HEAD')
            bundle_cli_controls(api, f)
        else: bundle_rejected(api, f, name)
    if name == 'reject-self-review':
        for field in ('agent_id', 'session_id'):
            for role in ('developer', 'acceptance_reviewer'):
                def overlap(f, field=field, role=role):
                    f.bundle['roles'][role][field] = f.bundle['roles']['test_author'][field]; f.refresh()
                bundle_isolated_negative(api, overlap, 'pairwise independent ' + field)
        for change in (lambda f: f.review.update(actor='wrong-reviewer'),
                       lambda f: f.review.update(reviewer_session_id='wrong-session'),
                       lambda f: f.review.update(extra='forbidden'),
                       lambda f: f.review['final_verdict'].update(approved=1),
                       lambda f: f.review['issues'].append('blocked')):
            bundle_isolated_negative(api, change, 'closed truthful independent review')
    elif name == 'reject-seal-change':
        for item in ('test', 'obligation', 'interface', 'baseline_control'):
            def drift(f, item=item):
                row = next(x for x in f.bundle['inputs'] if x['kind'] == item)
                f.write(row['path'], (f.root / row['path']).read_bytes() + b'\n')
            bundle_isolated_negative(api, drift, 'actual ' + item + ' Git/current byte drift')
        def executable(f): (f.root / f.bundle['inputs'][0]['path']).chmod(0o755)
        def environment_drift(f): f.bundle['environment']['runtime']['version'] = 'fabricated'; f.refresh()
        def wrong_tree(f): f.bundle['baseline']['tree'] = '0' * 40; f.refresh()
        def symlink(f):
            p = f.root / f.bundle['inputs'][0]['path']; p.unlink(); p.symlink_to('record.json')
        def wrong_blob(f):
            f.bundle['inputs'][0]['sha256'] = '0' * 64; f.refresh()
        for change in (executable, environment_drift, wrong_tree, symlink, wrong_blob):
            bundle_isolated_negative(api, change, 'immutable observed bytes/mode/environment/Git objects')
    elif name == 'reject-missing-red':
        for change in (lambda f: f.bundle['baseline_evidence'].pop(),
                       lambda f: f.bundle['baseline_evidence'].append(copy.deepcopy(f.bundle['baseline_evidence'][0])),
                       lambda f: f.row(name)['operation'].update(extra=True),
                       lambda f: f.row(name)['positive'].update(path=f.row(name)['setup']['path'])):
            def malformed(f, change=change): change(f); f.refresh()
            bundle_isolated_negative(api, malformed, 'complete unique closed independent proof rows')
        def absent_file(f): (f.root / f.row(name)['red']['path']).unlink()
        def changed_input(f):
            p = f.row(name)['operation']['case_input']['path']; f.write(p, b'{"different":true}')
        for change in (absent_file, changed_input): bundle_isolated_negative(api, change, 'actual proof/input sidecar required')
    elif name == 'reject-setup-as-red':
        replacements = [('EXIT: 1', 'EXIT: 0'), ('EXIT: 1', 'EXIT: 2'),
                        ('OBSERVED_RESULT: accept', 'OBSERVED_RESULT: reject'),
                        ('INPUT_SHA256: ', 'INPUT_WRONG: '), ('OPERATION_SHA256: ', 'OPERATION_WRONG: '),
                        ('POLICY_ASSERTION: ', 'UNRELATED_EXCEPTION: ')]
        for before, after in replacements:
            def bad_proof(f, before=before, after=after):
                row = f.row(name); p = row['red']['path']; text = (f.root / p).read_text().replace(before, after)
                f.write(p, text.encode()); row['red']['sha256'] = sha(text.encode()); f.refresh()
            bundle_isolated_negative(api, bad_proof, 'only intended bounded behavioral red')
        for suffix in ('EXIT: 1\n', 'COMMAND: duplicate\n', 'REVISION: other\n'):
            def duplicate(f, suffix=suffix):
                row = f.row(name); p = row['red']['path']; text = (f.root / p).read_text() + suffix
                f.write(p, text.encode()); row['red']['sha256'] = sha(text.encode()); f.refresh()
            bundle_isolated_negative(api, duplicate, 'unique raw capture headers')


def bundle_cli_controls(api, f):
    bundle = f.root / 'cli-bundle.json'; reviewer = f.root / 'cli-review.json'
    bundle.write_bytes(canonical(f.bundle)); reviewer.write_bytes(canonical(f.review))
    command = [sys.executable, api.__file__, 'bundle', '--repo', str(f.root), '--bundle', str(bundle), '--review', str(reviewer)]
    result = subprocess.run(command, capture_output=True, text=True)
    require(result.returncode == 0 and 'PASS' in result.stdout, 'CLI valid immutable handoff accepted')
    for data in (bundle.read_text()[:-1] + ',"feature_id":"116"}', '{"x":NaN}', '[]', '{broken'):
        bundle.write_text(data); result = subprocess.run(command, capture_output=True, text=True)
        require(result.returncode != 0 and result.stderr.strip() and 'PASS' not in result.stdout, 'CLI strict malformed bundle rejection')
    bundle.write_bytes(canonical(f.bundle)); bad = copy.deepcopy(f.review); bad['seal_sha256'] = '0' * 64
    reviewer.write_bytes(canonical(bad)); result = subprocess.run(command, capture_output=True, text=True)
    require(result.returncode != 0 and result.stderr.strip() and 'PASS' not in result.stdout, 'CLI stale review seal rejected')


PRE_ENTRY_CASES = CASES
ENTRY_CASES = ('accepted-entry', 'reject-foreign-repo', 'reject-stale-pin', 'reject-role-write')
CASES = PRE_ENTRY_CASES + ENTRY_CASES


def run_entry_case(name, api):
    helper = load_api(ROOT / 'tools/fixtures/workflow_assurance/entry_fixtures.py')
    helper.run_case(name, api)


AGF_CASES = ('approve-empty', 'advisory-visible', 'block-carried', 'reject-issues',
             'reject-missing-coverage', 'reject-unsupported')
AGF_ARRAYS = ('issues', 'missing_acceptance_coverage', 'unsupported_claims')


def agf_ledger(case='01-no-findings'):
    cr = load_api(ROOT / 'tools/convergent_review.py')
    directory = ROOT / 'tools/fixtures/convergent_review' / case
    read = lambda name: json.loads((directory / name).read_text())
    packet = read('packet.json'); trials = [read('trial-%d.json' % n) for n in (1, 2, 3)]
    prior = read('prior-ledger.json') if (directory / 'prior-ledger.json').exists() else None
    suppression = [read('suppression.json')] if (directory / 'suppression.json').exists() else []
    digest = lambda value: sha(cr.canonical_json_bytes(value))
    ledger = cr.converge_documents(packet, digest(packet), trials,
        {n: digest(trials[n - 1]) for n in (1, 2, 3)}, prior,
        digest(prior) if prior is not None else None, [(s, digest(s)) for s in suppression])
    cr.validate_ledger(ledger)
    if case == '05-prior-persisting':
        require(all(t['observations'] == [] for t in trials), 'carried fixture omits all prior observations')
        require(ledger['findings'][0]['lifecycle'] == 'persisting', 'real convergent unresolved carry')
    return ledger


def agf_severity(ledger, severity):
    cr = load_api(ROOT / 'tools/convergent_review.py'); ledger = copy.deepcopy(ledger)
    for finding in ledger['findings']:
        finding['severity'] = severity
        finding['fingerprint'] = agf_fingerprint(cr, ledger, finding)
    ledger['findings'].sort(key=lambda f: f['fingerprint'])
    ledger['counts'] = cr.calculate_counts(ledger['findings'])
    ledger['verdict'] = 'request_changes' if any(ledger['counts']['active_' + s] for s in ('blocker', 'important')) else 'approve'
    cr.validate_ledger(ledger)
    return ledger


def agf_fingerprint(cr, ledger, finding):
    return cr.semantic_fingerprint(ledger['repository'], {k: finding[k] for k in ('severity', 'category', 'path', 'symbol', 'rule', 'title', 'description')})


def agf_report():
    return {'final_verdict': {'approved': True, 'summary': 'independent', 'metadata': {'nested': [1]}},
            **{key: [] for key in AGF_ARRAYS}, 'extra_metadata': {'allowed': [2]}}


def agf_call(api, ledger, report):
    before = copy.deepcopy((ledger, report))
    result = api.convergent_agf_verdict(ledger, report, expected_repository=ledger['repository'], expected_head_sha=ledger['head_sha'])
    require((ledger, report) == before, 'AGF inputs unchanged')
    require(set(result) == {'final_verdict', *AGF_ARRAYS, 'required_fixes', 'advisory_minor'}, 'AGF exact output keys')
    def mutable_ids(value):
        if type(value) not in (dict, list): return set()
        children = value.values() if type(value) is dict else value
        return {id(value)}.union(*(mutable_ids(child) for child in children))
    require(not mutable_ids(result) & mutable_ids([ledger, report]), 'AGF deep output independence')
    require(result == api.convergent_agf_verdict(ledger, report, expected_repository=ledger['repository'], expected_head_sha=ledger['head_sha']), 'AGF deterministic output')
    return result


def agf_invalid(api, ledger, report, **binding):
    kwargs = {'expected_repository': 'example/reviewed-repo', 'expected_head_sha': '2' * 40, **binding}
    before = repr((ledger, report))
    rejected(api, lambda: api.convergent_agf_verdict(ledger, report, **kwargs), 'AGF invalid input fails closed')
    require(repr((ledger, report)) == before, 'invalid AGF inputs unchanged')


def agf_approve(api):
    ledger = agf_ledger(); report = agf_report(); out = agf_call(api, ledger, report)
    require(out == {key: copy.deepcopy(report[key]) for key in ('final_verdict', *AGF_ARRAYS)} | {'required_fixes': [], 'advisory_minor': []}, 'empty valid AGF approves exactly')
    report['final_verdict']['approved'] = False
    require(agf_call(api, ledger, report)['final_verdict']['approved'] is False, 'false approval remains false')
    for approval in (1, 0, None, 'true', [], {}):
        bad = agf_report(); bad['final_verdict']['approved'] = approval; agf_invalid(api, ledger, bad)
    for root in (None, [], 'report', 1):
        agf_invalid(api, ledger, root); agf_invalid(api, root, agf_report())
    for key in ('final_verdict', *AGF_ARRAYS):
        bad = agf_report(); del bad[key]; agf_invalid(api, ledger, bad)
        for value in (None, 1, 'wrong', [] if key == 'final_verdict' else {}):
            bad = agf_report(); bad[key] = value; agf_invalid(api, ledger, bad)
    bad = agf_report(); del bad['final_verdict']['approved']; agf_invalid(api, ledger, bad)
    for value in (None, {}, 'wrong'):
        bad = agf_report(); bad['required_fixes'] = value; agf_invalid(api, ledger, bad)
    cycle = []; cycle.append(cycle)
    for value in (float('nan'), float('inf'), -float('inf'), (1,), {1}, object(), cycle, {1: 'key'}):
        bad = agf_report(); bad['metadata'] = value; agf_invalid(api, ledger, bad)
        broken = copy.deepcopy(ledger); broken['metadata'] = value; agf_invalid(api, broken, agf_report())
    for key, values in (('expected_repository', (None, 1, '', 'invalid', '../repo', 'other/repo')),
                        ('expected_head_sha', (None, 1, '', '2' * 39, 'A' * 40, 'g' * 40, '3' * 40))):
        for value in values: agf_invalid(api, ledger, agf_report(), **{key: value})
    for key, value in (('counts', {}), ('verdict', 'request_changes'), ('trial_digests', []), ('head_sha', 'bad')):
        bad = copy.deepcopy(ledger); bad[key] = value; agf_invalid(api, bad, agf_report())
    report = agf_report(); report['required_fixes'] = [{'old': ['retained']}]
    require(agf_call(api, ledger, report)['required_fixes'] == report['required_fixes'], 'existing required fixes retained without blocking')


def agf_advisory(api):
    for case in ('02-consensus-blocker', '05-prior-persisting', '08-reopened-finding'):
        ledger = agf_severity(agf_ledger(case), 'minor'); report = agf_report()
        out = agf_call(api, ledger, report)
        require(out['advisory_minor'] == ledger['findings'] and out['issues'] == [] and out['required_fixes'] == [], 'active minor visible separately')
        require(out['final_verdict']['approved'] is True, 'minor alone permits approval')
        for key in AGF_ARRAYS:
            report = agf_report(); report[key] = [{'carried': ['important']}]
            out = agf_call(api, ledger, report)
            require(out[key] == report[key] and out['final_verdict']['approved'] is False, 'minor preserves blocking array ' + key)
    for case in ('06-prior-resolution-two-of-three', '11-authorized-suppression-retained'):
        out = agf_call(api, agf_severity(agf_ledger(case), 'minor'), agf_report())
        require(out['advisory_minor'] == [] and out['final_verdict']['approved'] is True, 'inactive minor excluded')
    cr = load_api(ROOT / 'tools/convergent_review.py'); mixed = agf_severity(agf_ledger('02-consensus-blocker'), 'minor')
    for severity in ('important', 'blocker'):
        f = copy.deepcopy(mixed['findings'][0]); f['severity'] = severity; f['rule'] += severity
        f['fingerprint'] = agf_fingerprint(cr, mixed, f); mixed['findings'].append(f)
    mixed['findings'].sort(key=lambda f: f['fingerprint']); mixed['counts'] = cr.calculate_counts(mixed['findings']); mixed['verdict'] = 'request_changes'
    cr.validate_ledger(mixed); out = agf_call(api, mixed, agf_report())
    require(out['advisory_minor'] == [f for f in mixed['findings'] if f['severity'] == 'minor'], 'mixed minor remains visible')
    require(out['issues'] == [f for f in mixed['findings'] if f['severity'] != 'minor'] and out['final_verdict']['approved'] is False, 'minor never clears important or blocker; ledger order retained')


def agf_block(api):
    for case in ('02-consensus-blocker', '05-prior-persisting', '08-reopened-finding'):
        for severity in ('blocker', 'important'):
            ledger = agf_severity(agf_ledger(case), severity); report = agf_report()
            report['issues'] = [{'old': ['blocking']}]; report['required_fixes'] = [{'old': ['fix']}]
            out = agf_call(api, ledger, report)
            require(out['issues'] == report['issues'] + ledger['findings'], 'active full findings appended in ledger order')
            fixes = [{'fingerprint': f['fingerprint'], 'required_fix': f['title'] + ': ' + f['description']} for f in ledger['findings']]
            require(out['required_fixes'] == report['required_fixes'] + fixes and out['final_verdict']['approved'] is False, 'blocking fixes appended and approval false')
            require(out['advisory_minor'] == [], 'blocking severity is not minor')
            for field, value in (('fingerprint', 'f' * 64), ('lifecycle', 'invalid')):
                bad = copy.deepcopy(ledger); bad['findings'][0][field] = value; agf_invalid(api, bad, agf_report())
            bad = copy.deepcopy(ledger); bad['counts']['active_' + severity] += 1; agf_invalid(api, bad, agf_report())
    for case in ('06-prior-resolution-two-of-three', '11-authorized-suppression-retained'):
        out = agf_call(api, agf_ledger(case), agf_report())
        require(out['issues'] == [] and out['required_fixes'] == [] and out['final_verdict']['approved'] is True, 'resolved and suppressed findings excluded')


def agf_array(api, key):
    ledger = agf_ledger()
    for entries in ([{'severity': 'minor', 'nested': [1]}], [''], [False], [None], [0], [[], {}]):
        report = agf_report(); report[key] = entries; report['required_fixes'] = [{'unrelated': ['explanatory']}]
        out = agf_call(api, ledger, report)
        require(out[key] == entries and out['final_verdict']['approved'] is False, 'nonempty blocking array preserved: ' + key)
        report[key] = []; out = agf_call(api, ledger, report)
        require(out['final_verdict']['approved'] is True, 'restored empty array approves: ' + key)


def run_agf_case(name, api):
    if not callable(getattr(api, 'convergent_agf_verdict', None)):
        print('SETUP_ERROR: missing convergent_agf_verdict API', file=sys.stderr); raise SystemExit(2)
    dispatch = dict(zip(AGF_CASES[:3], (agf_approve, agf_advisory, agf_block)))
    if name in dispatch: dispatch[name](api)
    else: agf_array(api, AGF_ARRAYS[AGF_CASES[3:].index(name)])


RECEIPT_CASES = ('reject-missing-operator', 'reject-wrong-candidate', 'reject-unrun',
    'reject-setup', 'reject-pending', 'reject-running', 'reject-failed',
    'reject-invalidated', 'idempotent-replay', 'reject-double-advance', 'recover-missing-receipt')
RECEIPT_MINIMA = {'contract-approved': ('mode-a', 'contract-review'),
    'source-ready': ('approved-contract', 'provisional-bundle'), 'qa-passed': ('mode-b',),
    'evidence-captured': ('fresh-qa',), 'feature-complete': ('fresh-qa', 'evidence-capture')}


def receipt_ids(value):
    if type(value) not in (dict, list): return set()
    children = value.values() if type(value) is dict else value
    return {id(value)}.union(*(receipt_ids(child) for child in children))


class ReceiptFixture:
    """Synthetic authority/gate fixtures; captures alone describe real local processes."""
    def __init__(self, api, parent, alternate=False):
        self.api = api; self.root = Path(parent) / ('alternate' if alternate else 'receipt')
        self.root.mkdir(); git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.name', 'Receipt Fixture Only')
        git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        self.repository = 'portable/receipt-fixture' if alternate else 'niq-cnr/nizam-framework'
        git(self.root, 'remote', 'add', 'origin', self.repository)
        self.inputs = dict(source=['src/code.py'], contracts=['contract.json'],
            tests=['tests/test.py'], tools=['tools/check.py'], unknown_dependencies=[])
        for path in ('src/code.py', 'tests/test.py', 'tools/check.py'): self.write(path, b'# protected receipt fixture\n')
        self.state = dict(repository=self.repository, current_phase='fixture-phase', current_feature='120',
            status='awaiting-fixture', updated_at='2026-10-14T00:00:00Z',
            scope_budget=dict(original_estimate_lines=44, total_lines_changed=3, per_feature=[]),
            circuit_breaker={'fixture': {'attempts': 1, 'limit': 3}},
            history=[dict(at='earlier', event='fixture-seed', detail='preserve this prefix')],
            authority={'fixture': ['unowned sentinel']})
        self.write('record.json', self.state)
        for name in ('contract', 'contract_review', 'qa_verdict', 'run_state'):
            self.write('schema/' + name + '.schema.json', (ROOT / 'schema' / (name + '.schema.json')).read_bytes())
        proposed = json.loads((ROOT / '.agent/contracts/120.json').read_text())
        proposed['status'] = 'proposed'; proposed['approvals'] = {'validator_mode_a': False, 'evaluator_contract_review': False}
        self.write('contract.json', proposed); proposal_revision = self.commit('fixture proposal')
        proposal_digest = sha(canonical(proposed)); self.gate = agf_report(); del self.gate['extra_metadata']
        mode_a = dict(self.gate, feature='120', reviewed_commit=proposal_revision,
            contract_sha256=proposal_digest, reviewer='fixture-mode-a')
        review = dict(self.gate, review='fixture-only', feature='120', contract_id='120',
            reviewed_revision=proposal_revision, proposal_sha256=proposal_digest, reviewer='fixture-contract-review')
        self.write('proof/mode-a.json', mode_a); self.write('proof/contract-review.json', review)
        approved = copy.deepcopy(proposed); approved['status'] = 'approved'
        approved['approvals'] = {'validator_mode_a': True, 'evaluator_contract_review': True}
        approved['approval_evidence'] = dict(mode_a='proof/mode-a.json', contract_review='proof/contract-review.json', proposal_sha256=proposal_digest)
        self.write('contract.json', approved); approval_revision = self.commit('fixture approved authority')
        self.contract = self.ref('contract.json', approval_revision); digest = self.contract['sha256']
        entries = [self.entry('mode-a', self.ref('proof/mode-a.json', approval_revision), proposal_revision, proposal_digest),
            self.entry('contract-review', self.ref('proof/contract-review.json', approval_revision), proposal_revision, proposal_digest),
            self.entry('approved-contract', self.contract, approval_revision, digest)]
        artifacts = {
            'provisional-bundle': dict(self.gate, feature_id='120', reviewed_revision=approval_revision, approved_contract_sha256=digest, reviewer='fixture-bundle-review'),
            'mode-b': dict(self.gate, feature='120', reviewed_commit=approval_revision, approved_contract_sha256=digest, reviewer='fixture-mode-b'),
            'fresh-qa': dict(self.gate, feature_id='120', reviewed_revision=approval_revision, approved_contract_sha256=digest, reviewer='fixture-qa', qa_pass=True, checks_run=1, checks_passed=1, adversarial={'performed': True}, evidence_files=[], required_fixes=[]),
            'evidence-capture': dict(role='Root', feature='120', revision=approval_revision, approved_contract_sha256=digest, passed=True, actual_exit=0, purpose='synthetic typed parser fixture')}
        for kind, value in artifacts.items(): self.write('proof/' + kind + '.json', value)
        authority = json.loads((ROOT / '.agent/evidence/phase018-preflight/activation-authority.json').read_text())
        if alternate:
            authority.update(owner='fixture-portable-owner', gate='H-FIXTURE-PORTABLE', repository=self.repository,
                operator_instruction_verbatim='Synthetic fixture instruction, not real operator consent.',
                scope=dict(phase='portable-phase', features=['120', 'fixture-next'], original_estimate_lines=33, ceiling_130pct=44))
        self.authority = authority; self.write('proof/standing-authority.json', authority)
        self.candidate_revision = self.commit('fixture protected candidate and typed prerequisite fixtures')
        self.candidate = api.assess_repository(self.root, self.candidate_revision, self.inputs,
            ['NIZAM_WA120_FIXTURE'], {'contract.json': ['/status'], 'record.json': ['/status', '/updated_at', '/history']})
        self.authority_ref = self.ref('proof/standing-authority.json', self.candidate_revision)
        entries += [self.entry(kind, self.ref('proof/' + kind + '.json', self.candidate_revision), approval_revision, digest) for kind in artifacts]
        self.producer = dict(agent_id='fixture-only-capture-producer', session_id='fixture-only-session')
        self.diagnostic = 'PASS receipt fixture actual assertion'
        self.policy = dict(schema_version=1, repository=self.repository, feature_id='120', stage='feature-complete',
            operation_id='fixture-operation-120', candidate=copy.deepcopy(self.candidate), contract=self.contract,
            operator=None, producer=self.producer, prerequisites=entries, commands=[],
            from_status=self.state['status'], to_status='captured-fixture', at='2026-10-14T01:00:00Z', recovery=None)
        self.capture = self.actual_capture('success')
        self.set_capture(self.capture); self.set_stage('feature-complete')

    def write(self, path, value):
        target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if type(value) is bytes else canonical(value))

    def commit(self, message):
        git(self.root, 'add', '.')
        if git(self.root, 'diff', '--cached', '--name-only'):
            git(self.root, 'commit', '-qm', message)
        return git(self.root, 'rev-parse', 'HEAD')

    def ref(self, path, revision=None):
        revision = revision or git(self.root, 'rev-parse', 'HEAD')
        data = subprocess.check_output(['git', '-C', str(self.root), 'show', revision + ':' + path])
        return dict(path=path, sha256=sha(data), revision=revision)

    def pin(self, path, value):
        self.write(path, value); return self.ref(path, self.commit('fixture artifact ' + path))

    def nonregular_artifact(self, reference):
        """Keep identical JSON bytes/path/digest; change only historical Git mode."""
        revision = reference['revision']; path = reference['path']
        data = subprocess.check_output(['git', '-C', str(self.root), 'show', revision + ':' + path])
        oid = subprocess.check_output(['git', '-C', str(self.root), 'hash-object', '-w', '--stdin'], input=data).decode().strip()
        with tempfile.TemporaryDirectory(prefix='receipt-mode-index-', dir=self.root.parent) as directory:
            env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory) / 'index')}
            def index(*args):
                return subprocess.check_output(['git', '-C', str(self.root), *args], env=env).decode().strip()
            index('read-tree', revision)
            index('update-index', '--cacheinfo', '120000', oid, path)
            tree = index('write-tree')
            commit = subprocess.check_output(['git', '-C', str(self.root), 'commit-tree', tree, '-p', revision],
                input=b'Owned nonregular artifact mode fixture\n', env=env).decode().strip()
        row = git(self.root, 'ls-tree', commit, '--', path).split()
        require(row[:3] == ['120000', 'blob', oid], 'nonregular artifact historical mode is isolated')
        require(subprocess.check_output(['git', '-C', str(self.root), 'show', commit + ':' + path]) == data,
            'nonregular artifact retains exact valid bytes')
        return dict(reference, revision=commit)

    def entry(self, kind, artifact, revision, digest):
        return dict(kind=kind, artifact=copy.deepcopy(artifact), feature_id='120', assessed_revision=revision, contract_sha256=digest)

    def actual_capture(self, outcome):
        revision = git(self.root, 'rev-parse', 'HEAD')
        code = "import os,pathlib,sys; assert os.environ['NIZAM_WA120_FIXTURE']=='observed'; pathlib.Path('proof/process-count.txt').open('a').write('executed\\n'); print(%r)" % self.diagnostic
        if outcome == 'semantic-negative': code += '; assert 1 != 2'
        if outcome == 'failed': code += '; sys.exit(7)'
        if outcome == 'setup-error': code += "; print('SETUP_ERROR: fixture dependency missing',file=sys.stderr); sys.exit(2)"
        argv = [sys.executable, '-c', code]
        process = subprocess.run(argv, cwd=self.root, capture_output=True, env=os.environ)
        require(process.returncode == {'failed': 7, 'setup-error': 2}.get(outcome, 0), 'actual fixture process outcome')
        label = outcome.replace('-', '_')
        self.write('proof/' + label + '.stdout', process.stdout); self.write('proof/' + label + '.stderr', process.stderr)
        output_revision = self.commit('actual fixture process outputs ' + outcome)
        capture = dict(schema_version=1, argv=argv, cwd=str(self.root), revision=revision,
            candidate_sha256=sha(canonical(self.candidate)), environment=copy.deepcopy(self.candidate['environment']),
            producer=copy.deepcopy(self.producer), executed=True, outcome=outcome, exit_code=process.returncode,
            stdout=self.ref('proof/' + label + '.stdout', output_revision), stderr=self.ref('proof/' + label + '.stderr', output_revision))
        return capture

    def set_capture(self, capture):
        self.capture_ref = self.pin('proof/capture-' + str(len(git(self.root, 'rev-list', 'HEAD').splitlines())) + '.json', capture)
        self.policy['commands'] = [dict(argv=copy.deepcopy(capture['argv']), expected_exit=0,
            proof_kind='semantic-negative' if capture['outcome'] == 'semantic-negative' else 'success',
            diagnostic=self.diagnostic, capture=self.capture_ref)]
        self.refresh()

    def refresh(self):
        p = self.policy
        self.receipt = {key: copy.deepcopy(p[key]) for key in ('schema_version', 'repository', 'feature_id', 'stage', 'operation_id', 'candidate', 'producer', 'prerequisites')}
        self.receipt.update(status='passed', contract_ref=copy.deepcopy(p['contract']), operator_ref=copy.deepcopy(p['operator']), verdict=copy.deepcopy(self.gate),
            checks=[dict(argv=copy.deepcopy(c['argv']), executed=True, outcome=c['proof_kind'], exit_code=0,
                stdout=copy.deepcopy(self.capture['stdout']), stderr=copy.deepcopy(self.capture['stderr']), capture=copy.deepcopy(c['capture'])) for c in p['commands']])

    def set_stage(self, stage):
        self.policy['stage'] = stage
        scope = {k: copy.deepcopy(self.authority['scope'][k]) for k in ('phase', 'features', 'original_estimate_lines', 'ceiling_130pct')}
        application = dict(schema_version=1, role='Root', repository=self.repository, feature_id='120', stage=stage,
            candidate_sha256=sha(canonical(self.candidate)), approved=True, authority_ref=self.authority_ref,
            owner=self.authority['owner'], gate=self.authority['gate'], scope=scope)
        self.operator = application; self.policy['operator'] = self.pin('proof/operator-' + stage + '.json', application); self.refresh()

    def bad_artifact(self, kind, change):
        entry = next(e for e in self.policy['prerequisites'] if e['kind'] == kind)
        value = json.loads(subprocess.check_output(['git', '-C', str(self.root), 'show', entry['artifact']['revision'] + ':' + entry['artifact']['path']]))
        change(value); entry['artifact'] = self.pin('proof/bad-' + kind + '.json', value); self.refresh()

    def snapshot(self):
        return {str(p.relative_to(self.root)): (sha(p.read_bytes()), p.stat().st_mode) for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}


def receipt_verify(api, f):
    before = copy.deepcopy((f.receipt, f.policy)); files = f.snapshot()
    result = api.verify_stage_receipt(f.root, f.receipt, policy=f.policy)
    require(result == f.receipt and type(result) is dict, 'receipt exact validated copy')
    require(not receipt_ids(result) & receipt_ids([f.receipt, f.policy]), 'receipt deep copy independence')
    require((f.receipt, f.policy) == before and files == f.snapshot(), 'receipt read-only validation, no command reexecution')
    return result


def receipt_reject(api, f, operation=None):
    before = repr((f.receipt, f.policy, f.state)); files = f.snapshot()
    rejected(api, operation or (lambda: api.verify_stage_receipt(f.root, f.receipt, policy=f.policy)), 'receipt invalid input rejected')
    require(before == repr((f.receipt, f.policy, f.state)) and files == f.snapshot(), 'rejected receipt preserves inputs/files')


def receipt_plan(api, f, state=None, receipt='fixture-default'):
    state = f.state if state is None else state
    receipt = f.receipt if receipt == 'fixture-default' else receipt
    before = copy.deepcopy((state, receipt, f.policy)); files = f.snapshot()
    result = api.plan_receipt_transition(f.root, state, receipt, policy=f.policy)
    require(set(result) == {'action', 'state', 'receipt', 'reason'} and type(result['reason']) is str and bool(result['reason']), 'transition exact return shape/reason')
    require(not receipt_ids(result) & receipt_ids([state, receipt, f.policy]), 'transition deep copy independence')
    require((state, receipt, f.policy) == before and files == f.snapshot(), 'transition read-only inputs/files')
    import jsonschema
    jsonschema.validate(result['state'], json.loads((ROOT / 'schema/run_state.schema.json').read_text()))
    return result


def receipt_operator(api, f, parent):
    receipt_verify(api, f); receipt_verify(api, ReceiptFixture(api, parent, alternate=True))
    receipt_artifact_integrity(api, f)
    original = copy.deepcopy(f.policy)
    for value in (None, {}, {'path': '../escape', 'sha256': '0' * 64, 'revision': f.candidate_revision}):
        f.policy = copy.deepcopy(original); f.policy['operator'] = value; f.refresh(); receipt_reject(api, f)
    for key, value in (('approved', 1), ('approved', False), ('feature_id', 'wrong'), ('stage', 'qa-passed'), ('candidate_sha256', 'f' * 64), ('owner', 'wrong'), ('gate', 'wrong')):
        app = copy.deepcopy(f.operator); app[key] = value; f.policy = copy.deepcopy(original)
        f.policy['operator'] = f.pin('proof/bad-operator.json', app); f.refresh(); receipt_reject(api, f)
    for key, value in (('features', ['other']), ('original_estimate_lines', True), ('ceiling_130pct', 1), ('phase', 'wrong')):
        app = copy.deepcopy(f.operator); app['scope'][key] = value; f.policy = copy.deepcopy(original)
        f.policy['operator'] = f.pin('proof/bad-operator-scope.json', app); f.refresh(); receipt_reject(api, f)
    for key, value in (('operator_instruction_verbatim', ''), ('repository', 'foreign/repo'), ('owner', 'unexpected')):
        authority = copy.deepcopy(f.authority); authority[key] = value; app = copy.deepcopy(f.operator)
        app['authority_ref'] = f.pin('proof/bad-authority.json', authority); f.policy = copy.deepcopy(original)
        f.policy['operator'] = f.pin('proof/operator-bad-authority.json', app); f.refresh(); receipt_reject(api, f)
    f.policy = original; f.refresh(); receipt_verify(api, f)


def receipt_artifact_integrity(api, f):
    original = copy.deepcopy(f.policy)
    reference = copy.deepcopy(original['operator'])
    for key, value in (('sha256', 'f' * 64), ('revision', '0' * 40),
                       ('revision', git(f.root, 'hash-object', reference['path'])), ('revision', 'HEAD')):
        require(value != reference[key], 'artifact probe changes selected pin field')
        f.policy = copy.deepcopy(original); f.policy['operator'][key] = value; f.refresh()
        require(f.receipt['operator_ref'] == f.policy['operator'], 'artifact probe synchronizes receipt binding')
        receipt_reject(api, f)
        f.policy = copy.deepcopy(original); f.refresh(); receipt_verify(api, f)
    f.policy['operator'] = f.nonregular_artifact(reference); f.refresh()
    require(f.receipt['operator_ref'] == f.policy['operator'], 'nonregular artifact binding synchronized')
    receipt_reject(api, f)
    f.policy = original; f.refresh(); receipt_verify(api, f)


def receipt_candidate(api, f):
    receipt_verify(api, f); original = copy.deepcopy(f.receipt)
    changed = copy.deepcopy(f.candidate); changed['source_tree'] = 'f' * 40
    changed['identity_sha256'] = sha(canonical({k: v for k, v in changed.items() if k != 'identity_sha256'}))
    f.receipt['candidate'] = changed; receipt_reject(api, f); f.receipt = original
    f.pin('proof/evidence-only.json', {'fixture': True}); receipt_verify(api, f)
    f.write('contract.json', dict(json.loads((f.root / 'contract.json').read_text()), status='complete'))
    f.commit('owned contract metadata completion'); receipt_verify(api, f)
    for path in ('src/code.py', 'tests/test.py', 'tools/check.py'):
        target = f.root / path; data = target.read_bytes(); mode = target.stat().st_mode
        target.write_bytes(data + b'# drift\n'); receipt_reject(api, f); target.write_bytes(data)
        target.chmod(mode ^ 0o111); receipt_reject(api, f); target.chmod(mode)
        target.unlink(); target.symlink_to(f.root / 'contract.json'); receipt_reject(api, f); target.unlink(); target.write_bytes(data); target.chmod(mode)
    previous = os.environ['NIZAM_WA120_FIXTURE']; os.environ['NIZAM_WA120_FIXTURE'] = 'changed'
    try: receipt_reject(api, f)
    finally: os.environ['NIZAM_WA120_FIXTURE'] = previous
    receipt_verify(api, f)


def receipt_unrun(api, f):
    receipt_verify(api, f); original = copy.deepcopy(f.receipt); policy = copy.deepcopy(f.policy)
    for field, value in (('executed', False), ('executed', 1), ('exit_code', None), ('capture', None), ('stdout', None), ('argv', ['wrong'])):
        f.receipt = copy.deepcopy(original); f.receipt['checks'][0][field] = value; receipt_reject(api, f)
    for field, value in (('checks', []), ('checks', original['checks'] * 2), ('producer', {'agent_id': 'wrong', 'session_id': 'wrong'})):
        f.receipt = copy.deepcopy(original); f.receipt[field] = value; receipt_reject(api, f)
    f.receipt = original
    target = f.root / f.capture['stdout']['path']; saved = target.read_bytes(); target.unlink()
    receipt_reject(api, f); target.write_bytes(saved); receipt_verify(api, f)
    alias = f.root / 'proof/current-output-alias'; require(not alias.exists(), 'owned output alias path absent')
    alias.write_bytes(saved); target.unlink(); target.symlink_to(alias)
    try: receipt_reject(api, f)  # Same live bytes/digest; only the output path is a symlink.
    finally:
        target.unlink(); target.write_bytes(saved); alias.unlink()
    receipt_verify(api, f)
    for key, value in (('executed', False), ('exit_code', None), ('outcome', 'unrun'), ('producer', {'agent_id': 'wrong', 'session_id': 'wrong'})):
        capture = copy.deepcopy(f.capture); capture[key] = value; f.set_capture(capture); receipt_reject(api, f)
    f.policy = policy; f.receipt = original; receipt_verify(api, f)


def receipt_setup(api, f):
    receipt_verify(api, f); original = copy.deepcopy(f.policy); good = copy.deepcopy(f.capture)
    bad_capture = f.actual_capture('setup-error'); f.capture = bad_capture; f.set_capture(bad_capture)
    receipt_reject(api, f)  # Independently pinned real exit2/PASS output defeats forged receipt exit0/success.
    for outcome in ('setup-error', 'unsupported', 'transport-error'):
        f.policy = copy.deepcopy(original); f.capture = good; f.refresh()
        f.receipt['checks'][0]['outcome'] = outcome; receipt_reject(api, f)
        capture = copy.deepcopy(good); capture['outcome'] = outcome; f.set_capture(capture); receipt_reject(api, f)
    for value in (1, True, None, -1):
        f.policy = copy.deepcopy(original); f.policy['commands'][0]['expected_exit'] = value; f.refresh(); receipt_reject(api, f)
    f.policy = original; f.capture = good; f.refresh(); receipt_verify(api, f)
    semantic = f.actual_capture('semantic-negative'); f.capture = semantic; f.set_capture(semantic); receipt_verify(api, f)


def receipt_status(api, f, status):
    receipt_verify(api, f); f.receipt['status'] = status; receipt_reject(api, f)
    f.receipt['status'] = 'passed'; receipt_verify(api, f)


def receipt_failed(api, f):
    receipt_status(api, f, 'failed'); original = copy.deepcopy(f.policy); good = copy.deepcopy(f.capture)
    failed = f.actual_capture('failed'); f.capture = failed; f.set_capture(failed)
    receipt_reject(api, f)  # Real trusted exit7 and printed PASS cannot be replaced by receipt's forged exit0.
    f.policy = original; f.capture = good; f.refresh()
    for value in (7, False, True, '0', None):
        f.receipt['checks'][0]['exit_code'] = value; receipt_reject(api, f)
    f.refresh(); receipt_verify(api, f)
    saved = copy.deepcopy(f.receipt)
    for value in (None, [], 1, float('nan'), {'bad': (1,)}):
        f.receipt = value; receipt_reject(api, f)
    f.receipt = saved; cycle = []; cycle.append(cycle); f.receipt['cycle'] = cycle
    receipt_reject(api, f); f.receipt = saved = copy.deepcopy(saved); del f.receipt['cycle']
    for key, value in (('schema_version', True), ('status', 'unknown'), ('unknown', 1)):
        f.receipt = copy.deepcopy(saved); f.receipt[key] = value; receipt_reject(api, f)
    for value in (False, 1, None, 'true'):
        f.receipt = copy.deepcopy(saved); f.receipt['verdict']['final_verdict']['approved'] = value; receipt_reject(api, f)
    for field in AGF_ARRAYS:
        f.receipt = copy.deepcopy(saved); f.receipt['verdict'][field] = [False]; receipt_reject(api, f)
    f.receipt = saved; policy = copy.deepcopy(f.policy)
    for key, value in (('schema_version', True), ('stage', 'invented'), ('from_status', ''), ('unknown', 1)):
        f.policy = copy.deepcopy(policy); f.policy[key] = value; receipt_reject(api, f)
    f.policy = policy; receipt_verify(api, f)


def receipt_prerequisites(api, f):
    receipt_status(api, f, 'invalidated')
    for stage, minima in RECEIPT_MINIMA.items():
        f.set_stage(stage); receipt_verify(api, f); original = copy.deepcopy(f.policy)
        for kind in minima:
            f.policy = copy.deepcopy(original); f.policy['prerequisites'] = [e for e in original['prerequisites'] if e['kind'] != kind]
            f.refresh(); receipt_reject(api, f)
            f.policy = copy.deepcopy(original)
            for e in f.policy['prerequisites']:
                if e['kind'] == kind: e['feature_id'] = 'predecessor'
            f.refresh(); receipt_reject(api, f)
        f.policy = original; f.refresh()
    original = copy.deepcopy(f.policy)
    for kind, field, value in (('mode-a', 'contract_sha256', 'f' * 64), ('contract-review', 'reviewer', ''),
        ('approved-contract', 'status', 'proposed'), ('provisional-bundle', 'approved_contract_sha256', 'f' * 64),
        ('mode-b', 'reviewed_commit', f.candidate_revision), ('fresh-qa', 'qa_pass', 1), ('evidence-capture', 'actual_exit', False)):
        f.policy = copy.deepcopy(original); f.bad_artifact(kind, lambda v, field=field, value=value: v.update({field: value})); receipt_reject(api, f)
    for kind in ('mode-a', 'contract-review', 'provisional-bundle', 'mode-b', 'fresh-qa'):
        for field in AGF_ARRAYS:
            f.policy = copy.deepcopy(original); f.bad_artifact(kind, lambda v, field=field: v.update({field: ['block']})); receipt_reject(api, f)
    f.policy = copy.deepcopy(original); f.policy['prerequisites'].append(copy.deepcopy(original['prerequisites'][0])); f.refresh(); receipt_reject(api, f)
    f.policy = copy.deepcopy(original); f.policy['prerequisites'][0]['kind'] = 'invented'; f.refresh(); receipt_reject(api, f)
    f.policy = original; f.refresh(); receipt_verify(api, f)


def receipt_replay(api, f):
    receipt_verify(api, f); out = receipt_plan(api, f)
    digest = sha(canonical(f.receipt)); event = dict(at=f.policy['at'], event='wa-receipt-transition',
        detail='Receipt ' + f.policy['operation_id'] + ' advanced 120:' + f.policy['stage'] + ' (' + digest + ')',
        operation_id=f.policy['operation_id'], feature_id='120', stage=f.policy['stage'],
        candidate_sha256=sha(canonical(f.candidate)), receipt_sha256=digest)
    expected = copy.deepcopy(f.state); expected.update(status=f.policy['to_status'], updated_at=f.policy['at']); expected['history'].append(event)
    require(out['action'] == 'advance' and out['state'] == expected and out['receipt'] == f.receipt, 'receipt first transition exact owned advance')
    api.verify_record_update(f.state, out['state'], ['/status', '/updated_at', '/history'])
    replay = receipt_plan(api, f, out['state'])
    require(replay['action'] == 'noop' and replay['state'] == out['state'], 'receipt identical replay noop')
    return out['state']


def receipt_double(api, f):
    advanced = receipt_replay(api, f)
    for field, value in (('detail', 'altered'), ('candidate_sha256', 'f' * 64), ('stage', 'qa-passed'), ('receipt_sha256', 'f' * 64)):
        state = copy.deepcopy(advanced); state['history'][-1][field] = value
        receipt_reject(api, f, lambda state=state: api.plan_receipt_transition(f.root, state, f.receipt, policy=f.policy))
    for mutation in ('duplicate', 'status', 'schema', 'history'):
        state = copy.deepcopy(advanced)
        if mutation == 'duplicate': state['history'].append(copy.deepcopy(state['history'][-1]))
        if mutation == 'status': state['status'] = 'incompatible'
        if mutation == 'schema': del state['scope_budget']
        if mutation == 'history': state['history'].append({'event': 'malformed'})
        receipt_reject(api, f, lambda state=state: api.plan_receipt_transition(f.root, state, f.receipt, policy=f.policy))
    original = copy.deepcopy(f.receipt); f.receipt['verdict']['final_verdict']['summary'] = 'different valid receipt'
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, advanced, f.receipt, policy=f.policy)); f.receipt = original
    f.receipt['status'] = 'pending'
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, f.state, f.receipt, policy=f.policy)); f.receipt = original; f.refresh()
    for state in (None, [], {'status': 'arbitrary'}, dict(f.state, repository='wrong')):
        receipt_reject(api, f, lambda state=state: api.plan_receipt_transition(f.root, state, f.receipt, policy=f.policy))
    require(receipt_plan(api, f, advanced)['action'] == 'noop', 'valid replay remains noop after collision probes')
    policy = copy.deepcopy(f.policy); f.set_stage('qa-passed'); receipt_verify(api, f)
    state = copy.deepcopy(advanced); state['status'] = f.policy['from_status']
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, state, f.receipt, policy=f.policy))
    f.policy = policy; f.refresh()
    # A genuinely valid second candidate/capture cannot reuse an operation across candidates.
    revision = git(f.root, 'rev-parse', 'HEAD')
    f.candidate = api.assess_repository(f.root, revision, f.inputs, ['NIZAM_WA120_FIXTURE'],
        {'contract.json': ['/status'], 'record.json': ['/status', '/updated_at', '/history']})
    f.policy['candidate'] = copy.deepcopy(f.candidate); f.capture = f.actual_capture('success')
    f.set_capture(f.capture); f.set_stage('feature-complete'); receipt_verify(api, f)
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, state, f.receipt, policy=f.policy))


def receipt_recovery(api, f):
    out = receipt_plan(api, f, receipt=None)
    require(out['action'] == 'rerun-required' and out['receipt'] is None and out['state'] == f.state, 'missing receipt never advances')
    f.policy['recovery'] = dict(path='proof/missing-receipt.json', sha256=sha(canonical(f.receipt)), revision=git(f.root, 'rev-parse', 'HEAD'))
    require(receipt_plan(api, f, receipt=None)['action'] == 'rerun-required', 'missing recovery artifact requests rerun')
    recovery = f.pin('proof/recovery-receipt.json', f.receipt); f.policy['recovery'] = recovery
    target = f.root / f.capture['stdout']['path']; raw = target.read_bytes(); target.unlink()
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, f.state, None, policy=f.policy)); target.write_bytes(raw)
    out = receipt_plan(api, f, receipt=None)
    require(out['action'] == 'republish' and out['state'] == f.state and out['receipt'] == f.receipt, 'verified recovery only proposes republish')
    published = f.root / 'proof/restored-receipt.json'; require(not published.exists(), 'restore uses new owned fixture path')
    published.write_bytes(canonical(out['receipt'])); restored = api.parse_json(published.read_bytes())
    require(api.verify_stage_receipt(f.root, restored, policy=f.policy) == restored, 'actual owned restore reread revalidates')
    advanced = receipt_plan(api, f, receipt=restored)
    require(advanced['action'] == 'advance' and receipt_plan(api, f, advanced['state'], restored)['action'] == 'noop', 'restored receipt advances exactly once')
    require(receipt_plan(api, f, advanced['state'], None)['action'] == 'republish', 'matching recorded recovery proposes no new transition')
    bad = copy.deepcopy(f.receipt); bad['status'] = 'failed'; f.policy['recovery'] = f.pin('proof/corrupt-recovery.json', bad)
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, f.state, None, policy=f.policy))
    f.policy['recovery'] = recovery; state = copy.deepcopy(advanced['state']); state['history'][-1]['receipt_sha256'] = 'f' * 64
    receipt_reject(api, f, lambda: api.plan_receipt_transition(f.root, state, None, policy=f.policy))


def run_receipt_case(name, api):
    if not all(callable(getattr(api, key, None)) for key in ('verify_stage_receipt', 'plan_receipt_transition')):
        print('SETUP_ERROR: missing receipt APIs', file=sys.stderr); raise SystemExit(2)
    previous = os.environ.get('NIZAM_WA120_FIXTURE'); os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
    try:
        with tempfile.TemporaryDirectory(prefix='nizam120-receipt-') as parent:
            f = ReceiptFixture(api, parent)
            if name == 'reject-missing-operator': receipt_operator(api, f, parent)
            elif name == 'reject-wrong-candidate': receipt_candidate(api, f)
            elif name == 'reject-unrun': receipt_unrun(api, f)
            elif name == 'reject-setup': receipt_setup(api, f)
            elif name == 'reject-failed': receipt_failed(api, f)
            elif name == 'reject-invalidated': receipt_prerequisites(api, f)
            elif name == 'idempotent-replay': receipt_replay(api, f)
            elif name == 'reject-double-advance': receipt_double(api, f)
            elif name == 'recover-missing-receipt': receipt_recovery(api, f)
            else: receipt_status(api, f, name.removeprefix('reject-'))
    finally:
        if previous is None: os.environ.pop('NIZAM_WA120_FIXTURE', None)
        else: os.environ['NIZAM_WA120_FIXTURE'] = previous


LANE_CASES = ('independent-lanes', 'shared-state-serialized', 'reject-terminal-spoof', 'reject-fourth', 'owned-rollback')


class LaneFixture(ReceiptFixture):
    """New owned Git graph; every authority/actor label is a synthetic parser fixture."""
    def __init__(self, parent):
        self.parent = Path(parent).resolve(); self.root = self.parent / 'coordinator'; self.root.mkdir()
        self.attempt_parent = self.parent / 'attempts'; self.attempt_parent.mkdir(); self.roots = []
        git(self.root, 'init', '-q'); git(self.root, 'config', 'user.name', 'Fixture Lanes Only')
        git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        self.repository = 'portable/lanes-fixture'; git(self.root, 'remote', 'add', 'origin', self.repository)
        for name in ('a', 'b', 'staged', 'work'): self.write('src/' + name + '.py', b'# unchanged private base\n')
        self.write('.gitignore', b'ignored/\n'); self.write('proof/prior.txt', b'original external proof\n')
        self.outside = self.parent / 'outside-sentinel'; self.outside.write_bytes(b'outside sentinel\n'); self.outside.chmod(0o600)
        self.sibling = self.parent / 'sibling'; self.sibling.mkdir(); (self.sibling / 'sentinel').write_bytes(b'sibling task sentinel\n')
        for name in ('contract', 'contract_review', 'run_state', 'feature_list'):
            self.write('schema/' + name + '.schema.json', (ROOT / 'schema' / (name + '.schema.json')).read_bytes())
        contract = json.loads((ROOT / '.agent/contracts/121.json').read_text()); contract['status'] = 'proposed'
        contract['approvals'] = dict(validator_mode_a=False, evaluator_contract_review=False)
        self.write('contract.json', contract); proposed = self.commit('fixture proposed121'); digest = sha(canonical(contract))
        gate = dict(final_verdict={'approved': True, 'summary': 'synthetic fixture gate'}, issues=[], missing_acceptance_coverage=[], unsupported_claims=[])
        self.write('proof/mode-a.json', dict(gate, feature='121', reviewed_commit=proposed, contract_sha256=digest, reviewer='fixture-mode-a'))
        self.write('proof/contract-review.json', dict(gate, review='fixture-only', feature='121', contract_id='121', reviewed_revision=proposed, proposal_sha256=digest, reviewer='fixture-contract-review'))
        contract['status'] = 'approved'; contract['approvals'] = dict(validator_mode_a=True, evaluator_contract_review=True)
        contract['approval_evidence'] = dict(mode_a='proof/mode-a.json', contract_review='proof/contract-review.json', proposal_sha256=digest)
        self.write('contract.json', contract)
        self.state = dict(repository=self.repository, current_phase='fixture-lanes', current_feature='121', active_contract_id='121', status='in_progress', updated_at='2026-10-14T00:00:00Z',
            scope_budget=dict(original_estimate_lines=44, total_lines_changed=2, per_feature=[]), circuit_breaker={'lane-step': {'attempts': 1, 'limit': 3}, 'other-step': {'attempts': 1, 'limit': 3}},
            history=[dict(at='earlier', event='fixture-seed', detail='unchanged prefix')], execution_lanes=[])
        feature = lambda id, status, dependencies, passes: dict(id=id, name=id, description='fixture feature', status=status, dependencies=dependencies, passes=passes, acceptance_tests=['fixture only'], estimated_lines=1)
        self.features = dict(phase='fixture-lanes', spec_version='0.1.0', original_estimate_lines=44,
            features=[feature('predecessor', 'complete', [], True), feature('121', 'in_progress', ['predecessor'], False)])
        self.write('coordination.json', self.state); self.write('features.json', self.features)
        self.base = self.commit('fixture approved contract and current coordination'); self.contract_ref = self.ref('contract.json', self.base)
        self.attempt = self.worktree('owned'); self.other = self.worktree('other')
        self.request = dict(operation_id='fixture-operation', feature_id='121', owner={'agent_id': 'fixture-agent', 'session_id': 'fixture-session'},
            agent_role='Generator', step_key='lane-step', attempt=1, base_revision=self.base, attempt_root=str(self.attempt), writes=['src/a.py'], state_fields=['/work/left'])
        self.policy = dict(repository=self.repository, coordination_ref=self.ref('coordination.json'), feature_list_ref=self.ref('features.json'), authority_ref=None, attempt_parent=str(self.attempt_parent), rollback_ref=None)
        self.authorize(); self.proof_captures = []; self.git_probe_log = []

    def worktree(self, name, attached=False):
        path = self.attempt_parent / name
        git(self.root, 'worktree', 'add', *(['-b', 'fixture-' + name] if attached else ['--detach']), str(path), self.base)
        self.roots.append(path); return path

    def close(self):
        for path in self.roots:
            require(path.parent == self.attempt_parent and path != self.root, 'cleanup only owned registered fixture worktree')
            if path.exists():
                if path.name == 'probe-submodule': git(path, 'update-index', '--force-remove', 'owned-gitlink')
                git(self.root, 'worktree', 'remove', '--force', str(path))

    def inventory_probe(self, kind):
        path = self.worktree('probe-' + kind); writes = ['src/a.py']; argv = None
        if kind in ('staged', 'committed', 'unmerged'):
            (path / 'src/b.py').write_bytes(b'ours undeclared change\n'); git(path, 'add', 'src/b.py')
            if kind != 'staged': git(path, 'commit', '-qm', 'owned fixture undeclared commit')
        if kind == 'rename': git(path, 'mv', 'src/a.py', 'src/cross-owner.py')
        if kind == 'mode': (path / 'src/b.py').chmod((path / 'src/b.py').stat().st_mode ^ 0o111)
        if kind == 'symlink': (path / 'src/a.py').unlink(); (path / 'src/a.py').symlink_to(path / 'src/b.py')
        if kind == 'submodule':
            (path / 'owned-gitlink').mkdir(); writes = ['owned-gitlink']
            git(path, 'update-index', '--add', '--cacheinfo', '160000', self.base, 'owned-gitlink')
        if kind == 'unmerged':
            writes = ['src/b.py']
            with tempfile.TemporaryDirectory(prefix='lane-conflict-index-', dir=self.parent) as directory:
                env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory) / 'index'), 'LC_ALL': 'C'}
                command = lambda *args: subprocess.check_output(['git', '-C', str(self.root), *args], env=env).decode().strip()
                command('read-tree', self.base)
                oid = subprocess.check_output(['git', '-C', str(self.root), 'hash-object', '-w', '--stdin'], input=b'theirs undeclared change\n').decode().strip()
                command('update-index', '--cacheinfo', '100644', oid, 'src/b.py'); tree = command('write-tree')
                theirs = subprocess.check_output(['git', '-C', str(self.root), 'commit-tree', tree, '-p', self.base], input=b'Owned fixture conflicting side\n', env=env).decode().strip()
            argv = ['git', '-C', str(path), 'merge', '--no-edit', theirs]
            result = subprocess.run(argv, capture_output=True, env={**os.environ, 'LC_ALL': 'C'})
            self.write('proof/unmerged-setup.stdout', result.stdout); self.write('proof/unmerged-setup.stderr', result.stderr)
            require(result.returncode == 1 and bool(git(path, 'ls-files', '--unmerged')), 'actual expected Git merge conflict setup')
            self.git_probe_log.append(dict(argv=argv, actual_exit=result.returncode, stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr), classification='expected fixture merge conflict, not API semantic red'))
        self.git_probe_log.append(dict(kind=kind, root=str(path), head=git(path, 'rev-parse', 'HEAD'), index=git(path, 'ls-files', '--stage'), status=git(path, 'status', '--porcelain=v1')))
        return path, writes

    def authorize(self, **changes):
        self.request = copy.deepcopy(self.request)
        self.request.update(copy.deepcopy(changes))
        dispatch = dict(schema_version=1, role='Orchestrator', repository=self.repository, approved=True, contract_ref=self.contract_ref, **copy.deepcopy(self.request))
        self.policy['authority_ref'] = self.pin('proof/dispatch.json', dispatch)

    def sync(self):
        self.write('coordination.json', self.state); self.write('features.json', self.features); revision = self.commit('fixture current snapshot')
        self.policy.update(coordination_ref=self.ref('coordination.json', revision), feature_list_ref=self.ref('features.json', revision))

    def lane(self, name='other', status='running', writes=None, fields=None):
        return dict(copy.deepcopy(self.request), operation_id=name, step_key='other-step', attempt_root=str(self.other),
            owner={'agent_id': 'fixture-other-agent', 'session_id': 'fixture-other-session'},
            writes=['src/b.py'] if writes is None else writes, state_fields=['/work/right'] if fields is None else fields, status=status, terminal_ref=None)

    def proof(self, lane, failure=False):
        argv = [sys.executable, '-c', "print('synthetic fixture capture assertion'); raise SystemExit(%d)" % (7 if failure else 0)]
        result = subprocess.run(argv, cwd=self.root, capture_output=True)
        require(result.returncode == (7 if failure else 0), 'actual fixture proof exit')
        name = 'failure' if failure else 'release'; self.write('proof/' + name + '.stdout', result.stdout); self.write('proof/' + name + '.stderr', result.stderr)
        record = {k: copy.deepcopy(lane[k]) for k in ('operation_id', 'feature_id', 'owner', 'attempt', 'base_revision', 'attempt_root')}
        record.update(schema_version=1, role='Orchestrator', actual_exit=result.returncode, **({'captured': True} if failure else {'released': True}))
        reference = self.pin('proof/' + name + '.json', record)
        self.proof_captures.append(dict(argv=argv, cwd=str(self.root), actual_exit=result.returncode, reference=reference,
            stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr), note='synthetic role/binding fixtures; raw process exit observed'))
        return reference

    def attempt_write(self, path, data):
        target = self.attempt / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)

    def all_files(self, exclude_attempt=False):
        result = {}
        for p in self.parent.rglob('*'):
            parts = p.relative_to(self.parent).parts
            if '.git' in parts or (exclude_attempt and (p == self.attempt or self.attempt in p.parents)): continue
            if p.is_symlink(): result[str(p)] = ('symlink', os.readlink(p))
            elif p.is_file(): result[str(p)] = (sha(p.read_bytes()), p.stat().st_mode)
        return result


def lane_call(api, f, method='assess_conflict_lanes'):
    inputs = copy.deepcopy((f.request, f.policy)); files = f.all_files(); registration = git(f.root, 'worktree', 'list', '--porcelain')
    result = getattr(api, method)(f.root, f.request, policy=f.policy)
    require((f.request, f.policy) == inputs and f.all_files() == files and git(f.root, 'worktree', 'list', '--porcelain') == registration, 'lane assessment is read-only')
    require(not receipt_ids(result) & receipt_ids([f.request, f.policy]), 'lane result independent copy')
    if method == 'assess_conflict_lanes':
        require(set(result) == {'eligible', 'conflicts', 'operation_id'} and type(result['eligible']) is bool and result['operation_id'] == f.request['operation_id'], 'lane exact assessment shape')
    else:
        require(result == dict(operation_id=f.request['operation_id'], attempt=f.request['attempt'], base_revision=f.request['base_revision'], attempt_root=f.request['attempt_root'],
            head_revision=git(f.attempt, 'rev-parse', 'HEAD'), owned_changes=result['owned_changes']), 'lane exact isolation identity')
    return result


def lane_reject(api, f, method='assess_conflict_lanes'):
    inputs = repr((f.request, f.policy)); files = f.all_files(); registration = git(f.root, 'worktree', 'list', '--porcelain')
    rejected(api, lambda: getattr(api, method)(f.root, f.request, policy=f.policy), 'lane invalid request rejected')
    require(repr((f.request, f.policy)) == inputs and f.all_files() == files and git(f.root, 'worktree', 'list', '--porcelain') == registration, 'lane denial precedes every side effect')


def lane_independent(api, f):
    f.state['execution_lanes'] = [f.lane()]; f.sync()
    require(lane_call(api, f) == {'eligible': True, 'conflicts': [], 'operation_id': f.request['operation_id']}, 'independent lanes eligible')
    require(lane_call(api, f, 'verify_isolated_attempt')['owned_changes'] == [], 'real detached base worktree accepted')
    for field, value in (('status', 'pending'), ('passes', False)):
        old = copy.deepcopy(f.features); f.features['features'][0][field] = value; f.sync(); lane_reject(api, f); f.features = copy.deepcopy(old); f.sync()
    old = copy.deepcopy(f.features); f.features['features'][0].update(status='cancelled', passes=False); f.sync(); require(lane_call(api, f)['eligible'] is True, 'cancelled predecessor satisfied')
    f.features = copy.deepcopy(old); f.features['features'].append(copy.deepcopy(old['features'][0])); f.sync(); lane_reject(api, f); f.features = copy.deepcopy(old); f.sync()
    f.authorize(writes=['src/a.py', 'src/staged.py', 'src/work.py', 'src/new.py', 'ignored/owned.txt'])
    f.attempt_write('src/a.py', b'owned committed change\n'); git(f.attempt, 'add', 'src/a.py'); git(f.attempt, 'commit', '-qm', 'owned fixture source change')
    f.attempt_write('src/staged.py', b'owned staged change\n'); git(f.attempt, 'add', 'src/staged.py')
    for path in ('src/work.py', 'src/new.py', 'ignored/owned.txt'): f.attempt_write(path, b'owned worktree change\n')
    require(lane_call(api, f, 'verify_isolated_attempt')['owned_changes'] == sorted(f.request['writes']), 'committed staged live untracked ignored ownership')
    original = copy.deepcopy(f.request)
    for path in ('unowned.txt', 'ignored/unowned.txt'):
        f.attempt_write(path, b'keep unowned sentinel\n'); lane_reject(api, f, 'verify_isolated_attempt'); (f.attempt / path).unlink()
    for kind in ('staged', 'committed', 'rename', 'mode', 'symlink', 'unmerged', 'submodule'):
        root, writes = f.inventory_probe(kind); f.authorize(attempt_root=str(root), writes=writes)
        lane_reject(api, f, 'verify_isolated_attempt')
        f.request = copy.deepcopy(original); f.authorize()
        require(lane_call(api, f, 'verify_isolated_attempt')['owned_changes'] == sorted(original['writes']), 'restored valid isolation after ' + kind)
    f.authorize(base_revision='0' * 40); lane_reject(api, f, 'verify_isolated_attempt'); f.request = copy.deepcopy(original); f.authorize()
    fake = f.attempt_parent / 'unregistered'; fake.mkdir(); f.authorize(attempt_root=str(fake)); lane_reject(api, f, 'verify_isolated_attempt'); f.request = copy.deepcopy(original); f.authorize()
    attached = f.worktree('attached', True); f.authorize(attempt_root=str(attached)); lane_reject(api, f, 'verify_isolated_attempt'); f.request = copy.deepcopy(original); f.authorize()
    require(lane_call(api, f, 'verify_isolated_attempt')['owned_changes'] == sorted(original['writes']), 'restored isolated owned positive')


def lane_shared(api, f):
    for status in ('reserved', 'running', 'invalidated'):
        f.state['execution_lanes'] = [f.lane('file-first', status, ['src/a.py'], ['/unrelated']), f.lane('pointer-second', status, ['elsewhere.txt'], ['/work'])]; f.sync()
        require(lane_call(api, f) == dict(eligible=False, conflicts=['file-first', 'pointer-second'], operation_id=f.request['operation_id']), 'same file and pointer prefix conflict in lane order')
    for path in ('src', 'src/a.py/child'):
        f.state['execution_lanes'] = [f.lane(writes=[path], fields=[])]; f.sync(); require(lane_call(api, f)['eligible'] is False, 'file ancestor descendant conflict')
    f.state['execution_lanes'] = [dict(copy.deepcopy(f.request), status='reserved', terminal_ref=None)]; f.sync()
    require(lane_call(api, f)['eligible'] is True, 'same operation exact lane ignored')
    f.state['execution_lanes'][0]['writes'] = ['elsewhere.txt']; f.sync(); lane_reject(api, f)
    f.state['execution_lanes'] = [f.lane(fields=['/work/leftover'])]; f.sync()
    require(lane_call(api, f)['eligible'] is True, 'pointer components disjoint, not string prefix')
    saved = (f.root / 'coordination.json').read_bytes(); f.write('coordination.json', dict(f.state, updated_at='stale')); lane_reject(api, f); f.write('coordination.json', saved)
    target = f.root / 'features.json'; mode = target.stat().st_mode; target.chmod(mode ^ 0o111); lane_reject(api, f); target.chmod(mode)
    require(lane_call(api, f)['eligible'] is True, 'restored current snapshot positive')
    state = copy.deepcopy(f.state); features = copy.deepcopy(f.features)
    for key, value in (('repository', 'foreign/repo'), ('current_feature', 'foreign'), ('active_contract_id', 'foreign'), ('status', 'complete'), ('current_phase', 'foreign-phase')):
        f.state = copy.deepcopy(state); f.state[key] = value; f.sync(); lane_reject(api, f)
        f.state = copy.deepcopy(state); f.sync(); require(lane_call(api, f)['eligible'] is True, 'restored coordination predicate ' + key)
    f.features = copy.deepcopy(features); f.features['phase'] = 'foreign-phase'; f.sync(); lane_reject(api, f)
    f.features = copy.deepcopy(features); f.sync(); require(lane_call(api, f)['eligible'] is True, 'restored feature phase binding')


def lane_spoof(api, f):
    original = copy.deepcopy(f.request)
    for key, value in (('status', 'released'), ('terminal', True), ('approved', True), ('authority_ref', f.policy['authority_ref']),
        ('owner', {'agent_id': 'spoof', 'session_id': 'spoof'}), ('agent_role', 'Orchestrator')):
        f.request = copy.deepcopy(original); f.request[key] = value; lane_reject(api, f)
    f.request = copy.deepcopy(original)
    for key, value in (('attempt', None), ('writes', ['../escape']), ('writes', ['src/../a.py']), ('writes', ['.git/config']), ('writes', ['src/a.py'] * 2), ('state_fields', ['/']), ('state_fields', ['/bad~escape']), ('state_fields', ['/work', '/work/left'])):
        f.request = copy.deepcopy(original); f.authorize(**{key: value}); lane_reject(api, f)
        f.request = copy.deepcopy(original); f.authorize(); require(lane_call(api, f)['eligible'] is True, 'restored bound shape probe ' + key)
    for value in (None, [], float('nan')):
        f.request = value; lane_reject(api, f)
    f.request = copy.deepcopy(original); cycle = []; cycle.append(cycle); f.request['extra'] = cycle; lane_reject(api, f); f.request = copy.deepcopy(original)
    policy = copy.deepcopy(f.policy)
    for key, value in (('sha256', 'f' * 64), ('revision', '0' * 40)):
        f.policy = copy.deepcopy(policy); f.policy['authority_ref'][key] = value; lane_reject(api, f)
    f.policy = copy.deepcopy(policy); dispatch = json.loads((f.root / 'proof/dispatch.json').read_text())
    for key, value in (('approved', 1), ('role', 'Generator')):
        bad = dict(dispatch, **{key: value}); f.policy['authority_ref'] = f.pin('proof/bad-dispatch.json', bad); lane_reject(api, f)
    f.policy = copy.deepcopy(policy); lane = f.lane(status='released', writes=['src/a.py'])
    f.state['execution_lanes'] = [lane]; f.sync(); lane_reject(api, f)
    reference = f.proof(lane); lane['terminal_ref'] = reference; f.sync(); require(lane_call(api, f)['eligible'] is True, 'pinned actual release frees conflicts')
    record = json.loads((f.root / reference['path']).read_text())
    for key, value in (('released', 1), ('actual_exit', False), ('operation_id', 'foreign')):
        lane['terminal_ref'] = f.pin('proof/bad-release.json', dict(record, **{key: value})); f.sync(); lane_reject(api, f)
    lane['terminal_ref'] = reference; f.sync(); require(lane_call(api, f)['eligible'] is True, 'restored exact release positive')


def lane_fourth(api, f):
    for ordinal in (1, 2, 3):
        f.state['circuit_breaker']['lane-step']['attempts'] = ordinal; f.sync(); f.authorize(attempt=ordinal)
        require(lane_call(api, f)['eligible'] is True, 'allocated ordinal accepted: ' + str(ordinal))
    original = copy.deepcopy(f.request); state = copy.deepcopy(f.state)
    for ordinal in (4, 0, True, '3', None):
        f.authorize(attempt=ordinal); lane_reject(api, f)
    f.request = copy.deepcopy(original); f.authorize()
    for key, value in (('attempts', 0), ('attempts', 2), ('attempts', True), ('attempts', '3'), ('limit', 4), ('limit', True)):
        f.state = copy.deepcopy(state); f.state['circuit_breaker']['lane-step'][key] = value; f.sync(); lane_reject(api, f)
    f.state = copy.deepcopy(state); del f.state['circuit_breaker']['lane-step']; f.sync(); lane_reject(api, f)
    f.state = copy.deepcopy(state); f.state['circuit_breaker']['lane-step'] = {'attempts': 3, 'limit': 3}; f.sync()
    require(lane_call(api, f)['eligible'] is True, 'restored original counter allocation accepted')


def lane_rollback(api, f):
    f.attempt_write('src/a.py', b'owned failure change\n'); original = copy.deepcopy(f.request)
    failure = f.proof(f.request, True); f.policy['rollback_ref'] = failure
    f.attempt_write('unowned-sentinel', b'unowned inside blocks removal\n'); lane_reject(api, f, 'rollback_owned_attempt'); (f.attempt / 'unowned-sentinel').unlink()
    policy = copy.deepcopy(f.policy)
    f.policy['rollback_ref'] = None; lane_reject(api, f, 'rollback_owned_attempt'); f.policy = copy.deepcopy(policy)
    record = json.loads((f.root / failure['path']).read_text())
    for key, value in (('captured', 1), ('actual_exit', 0), ('owner', {'agent_id': 'wrong', 'session_id': 'wrong'})):
        f.policy['rollback_ref'] = f.pin('proof/bad-failure.json', dict(record, **{key: value})); lane_reject(api, f, 'rollback_owned_attempt')
    f.policy = copy.deepcopy(policy); saved = (f.root / failure['path']).read_bytes(); (f.root / failure['path']).unlink(); lane_reject(api, f, 'rollback_owned_attempt'); f.write(failure['path'], saved)
    f.request['owner'] = {'agent_id': 'wrong', 'session_id': 'wrong'}; lane_reject(api, f, 'rollback_owned_attempt'); f.request = copy.deepcopy(original)
    nested = f.attempt / 'nested'; nested.mkdir(); alias = f.attempt_parent / 'alias'; alias.symlink_to(f.attempt, target_is_directory=True)
    foreign = f.attempt_parent / 'foreign'; git(f.root, 'init', '-q', str(foreign))
    for changes, parent in (({'attempt_root': str(f.root)}, f.parent), ({'attempt_root': str(f.parent)}, f.parent.parent),
        ({'attempt_root': str(nested)}, f.attempt_parent), ({'attempt_root': str(alias)}, f.attempt_parent),
        ({'attempt_root': str(foreign)}, f.attempt_parent), ({'base_revision': '0' * 40}, f.attempt_parent)):
        f.request = copy.deepcopy(original); f.authorize(**changes); f.policy['attempt_parent'] = str(parent)
        f.policy['rollback_ref'] = f.proof(f.request, True)
        lane_reject(api, f, 'rollback_owned_attempt')
        f.request = copy.deepcopy(original); f.authorize(); f.policy['attempt_parent'] = policy['attempt_parent']
        f.policy['rollback_ref'] = f.proof(f.request, True)
        require(lane_call(api, f, 'verify_isolated_attempt')['owned_changes'] == ['src/a.py'], 'restored valid isolation between unsafe rollback probes')
    alias.unlink(); nested.rmdir()
    outside = f.all_files(exclude_attempt=True); inputs = copy.deepcopy((f.request, f.policy))
    result = api.rollback_owned_attempt(f.root, f.request, policy=f.policy)
    require(result == dict(operation_id=f.request['operation_id'], attempt_root=str(f.attempt), removed=True), 'owned rollback exact removal result')
    require(not f.attempt.exists() and str(f.attempt) not in git(f.root, 'worktree', 'list', '--porcelain'), 'actual owned worktree absent and unregistered')
    require(f.all_files(exclude_attempt=True) == outside and (f.request, f.policy) == inputs, 'outside sibling sentinel coordinator prior proof unchanged')
    require(json.loads((f.root / failure['path']).read_text())['actual_exit'] == 7, 'failure capture remains actual nonzero after rollback')


def run_lane_case(name, api):
    if not all(callable(getattr(api, key, None)) for key in ('assess_conflict_lanes', 'verify_isolated_attempt', 'rollback_owned_attempt')):
        print('SETUP_ERROR: missing lane APIs', file=sys.stderr); raise SystemExit(2)
    with tempfile.TemporaryDirectory(prefix='nizam121-lanes-') as parent:
        f = LaneFixture(parent)
        try: (lane_independent, lane_shared, lane_spoof, lane_fourth, lane_rollback)[LANE_CASES.index(name)](api, f)
        finally: f.close()


FAILURE_CASES = ('infrastructure-failed', 'semantic-failed', 'reject-cause-relabel', 'counter-continuity')


class FailureFixture(ReceiptFixture):
    """Selected Root authority and producer labels are synthetic, never authentication."""
    def __init__(self, api, parent, cause='infrastructure', attempt=1, lanes=None, timestamp=True):
        super().__init__(api, parent)
        self.parent = Path(parent); self.serial = 0
        self.outside = self.parent / 'outside-sentinel'; self.outside.write_bytes(b'outside unchanged\n'); self.outside.chmod(0o600)
        self.write('proof/prior-proof.txt', b'earlier proof stays unchanged\n')
        contract = json.loads((ROOT / '.agent/contracts/122.json').read_text())
        contract.update(status='proposed', approvals=dict(validator_mode_a=False, evaluator_contract_review=False)); contract.pop('approval_evidence', None)
        self.write('contract.json', contract); proposed = self.commit('synthetic proposed122 contract'); digest = sha(canonical(contract))
        self.write('proof/122-mode-a.json', dict(self.gate, feature='122', reviewed_commit=proposed, contract_sha256=digest, reviewer='synthetic-mode-a'))
        self.write('proof/122-review.json', dict(self.gate, review='synthetic-only', feature='122', contract_id='122', reviewed_revision=proposed, proposal_sha256=digest, reviewer='synthetic-review'))
        contract.update(status='approved', approvals=dict(validator_mode_a=True, evaluator_contract_review=True),
            approval_evidence=dict(mode_a='proof/122-mode-a.json', contract_review='proof/122-review.json', proposal_sha256=digest))
        self.write('contract.json', contract); revision = self.commit('synthetic approved122 contract and independent parser gates')
        self.contract = self.ref('contract.json', revision)
        self.state.update(current_feature='122', active_contract_id='122', status='in_progress',
            circuit_breaker={'failure-step': {'attempts': attempt, 'limit': 3}, 'other': {'attempts': 2, 'limit': 3}})
        if lanes is not None: self.state['execution_lanes'] = copy.deepcopy(lanes)
        if not timestamp: del self.state['updated_at']
        self.current(); self.anchor = copy.deepcopy(self.policy['coordination_ref'])
        revision = self.commit('synthetic protected122 candidate')
        self.candidate = api.assess_repository(self.root, revision, self.inputs, ['NIZAM_WA120_FIXTURE'], {'contract.json': ['/status']})
        self.request = dict(operation_id='fixture-failure122', contract_id='122', feature_id='122', step_key='failure-step', attempt=attempt, stage='source-ready', cause=cause)
        self.capture = self.failed_capture(cause)
        self.evidence = dict(schema_version=1, kind=cause, reason='Synthetic independently selected classification of the observed failed wrapper.', capture_ref=None, verdict_ref=None)
        if cause == 'semantic':
            verdict = dict(copy.deepcopy(self.gate), review='synthetic rejection', feature='122'); verdict['final_verdict']['approved'] = False
            self.evidence['verdict_ref'] = self.pin_new('verdict', verdict)
        self.authority = dict(schema_version=1, role='Orchestrator', repository=self.repository, approved=True,
            contract_ref=self.contract, coordination_ref=self.anchor, candidate=self.candidate, producer=self.producer)
        self.bind()

    def commit(self, message):
        if not getattr(self, '_fixture_housekeeping_disabled', False):
            for key, value in (('gc.auto', '0'), ('maintenance.auto', 'false')):
                git(self.root, 'config', '--local', key, value)
            self._fixture_housekeeping_disabled = True
        return super().commit(message)

    def pin_new(self, label, value):
        self.serial += 1
        return self.pin('proof/failure-%d-%s.json' % (self.serial, label), value)

    def current(self):
        self.write('coordination122.json', self.state)
        reference = self.ref('coordination122.json', self.commit('synthetic current122 coordination'))
        self.policy = dict(repository=self.repository, coordination_ref=reference, authority_ref=None)

    def failed_capture(self, cause):
        revision = git(self.root, 'rev-parse', 'HEAD')
        # An expected inner negative succeeds; the outer wrapper still actually exits7.
        code = "import subprocess,sys; p=subprocess.run([sys.executable,'-c','raise SystemExit(9)']); assert p.returncode==9; print('PASS inner expected negative; outer failed'); sys.exit(7)"
        argv = [sys.executable, '-c', code]; result = subprocess.run(argv, cwd=self.root, capture_output=True, env=os.environ)
        require(result.returncode == 7, 'actual failed outer capture7')
        self.write('proof/failed.stdout', result.stdout); self.write('proof/failed.stderr', result.stderr)
        output_revision = self.commit('actual failed outer122 output')
        return dict(schema_version=1, argv=argv, cwd=str(self.root), revision=revision, candidate_sha256=sha(canonical(self.candidate)),
            environment=copy.deepcopy(self.candidate['environment']), producer=copy.deepcopy(self.producer), executed=True,
            outcome=cause + '-failed', exit_code=result.returncode, stdout=self.ref('proof/failed.stdout', output_revision), stderr=self.ref('proof/failed.stderr', output_revision))

    def bind(self):
        capture_ref = self.pin_new('capture', self.capture); self.evidence['capture_ref'] = capture_ref
        self.authority.update(copy.deepcopy(self.request), capture_ref=capture_ref, evidence_ref=self.pin_new('evidence', self.evidence))
        self.policy['authority_ref'] = self.pin_new('authority', self.authority)

    def files(self):
        return {str(p.relative_to(self.parent)): (p.lstat().st_mode, os.readlink(p) if p.is_symlink() else sha(p.read_bytes()) if p.is_file() else 'directory')
            for p in self.parent.rglob('*')}


def failure_call(api, f, deny=False):
    inputs = repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence)); files = f.files()
    try:
        result = api.route_failed_attempt(f.root, f.request, policy=f.policy)
    except api.AssuranceError as exc:
        require(deny and 0 < len(str(exc)) <= 1000, 'failure rejection is bounded AssuranceError')
        result = None
    else:
        require(not deny, 'invalid failure routing input accepted')
        q = f.request; attempt = q['attempt']
        expected = dict(q, outcome='failed', route='halt' if attempt == 3 else q['cause'] + ('-diagnosis' if q['cause'] == 'infrastructure' else '-repair'),
            attempts_used=attempt, limit=3, remaining=3-attempt, capture_ref=f.authority['capture_ref'])
        require(type(result) is dict and result == expected and all(type(result[k]) is int for k in ('attempt','attempts_used','limit','remaining')), 'exact failed routing result and integer counts')
        require(not receipt_ids(result) & receipt_ids([f.request, f.policy, f.state, f.authority, f.capture, f.evidence]), 'failure result never aliases any input')
        result['capture_ref']['path'] = 'returned-copy-only'
    require(inputs == repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence)) and files == f.files(), 'failure routing preserves full modes/bytes, counters, histories, prior proof and outside sentinel')


def failure_probe(api, f, target, field, value, bound=False):
    saved = copy.deepcopy((f.request, f.policy, f.state, f.authority, f.capture, f.evidence))
    getattr(f, target)[field] = value
    if bound: f.bind()
    if target == 'state':
        authority_ref = f.policy['authority_ref']; f.current(); f.policy['authority_ref'] = authority_ref
    failure_call(api, f, True)
    f.request, f.policy, f.state, f.authority, f.capture, f.evidence = saved
    f.write('coordination122.json', f.state)
    failure_call(api, f)


def failure_pinned(api, f, target, value):
    saved = copy.deepcopy((f.authority, f.policy))
    if target == 'authority': f.policy['authority_ref'] = f.pin_new('bad-authority', value)
    else:
        f.authority[target + '_ref'] = f.pin_new('bad-' + target, value)
        f.policy['authority_ref'] = f.pin_new('bad-binding', f.authority)
    failure_call(api, f, True)
    f.authority, f.policy = saved; failure_call(api, f)


def failure_infrastructure(api, f):
    failure_call(api, f)
    if f.request['attempt'] != 1: return
    for field, values in {'executed': [False, 1, None], 'exit_code': [0, True, '7', None],
            'outcome': ['success', 'semantic-negative', 'pending', 'running', 'semantic-failed'],
            'schema_version': [True, '1', 2], 'argv': [[], ['']], 'cwd': ['', None],
            'candidate_sha256': ['f'*64], 'producer': [{'agent_id': 'different', 'session_id': 'other'}],
            'environment': [{}], 'revision': ['0'*40]}.items():
        for value in values: failure_probe(api, f, 'capture', field, value, True)
    for field, values in {'reason': ['', 'x'*401, None], 'schema_version': [True, 2], 'verdict_ref': [f.contract]}.items():
        for value in values: failure_probe(api, f, 'evidence', field, value, True)
    target = f.root / f.capture['stdout']['path']; raw = target.read_bytes(); mode = target.stat().st_mode
    for mutation in ('bytes', 'mode', 'symlink', 'missing'):
        if mutation == 'bytes': target.write_bytes(raw + b'changed')
        elif mutation == 'mode': target.chmod(mode ^ 0o111)
        elif mutation == 'symlink': target.unlink(); target.symlink_to(f.outside)
        else: target.unlink()
        failure_call(api, f, True)
        if target.is_symlink(): target.unlink()
        target.write_bytes(raw); target.chmod(mode); failure_call(api, f)
    for stream in ('stdout', 'stderr'):
        failure_probe(api, f, 'capture', stream, f.pin_new('invalid-utf8-' + stream, b'\xff'), True)


def failure_verdict(f, family, approved, issues):
    verdict = dict(copy.deepcopy(f.gate), feature_id='122', feature='122', review='synthetic review')
    verdict['final_verdict']['approved'] = approved; verdict['issues'] = copy.deepcopy(issues)
    if family == 'qa_verdict': verdict.update(qa_pass=False, checks_run=1, checks_passed=0, adversarial={'performed': True}, evidence_files=[], required_fixes=[])
    return verdict


def failure_legacy_verdicts(f):
    base = dict(feature_id='122', verdict='fail', executed_at='2026-10-15T00:00:00Z',
        checks=[dict(command=' '.join(f.capture['argv']), exit_code=7, evidence=f.capture['stdout']['path'])], required_fixes=[])
    false = dict(approved=False)
    rows = [('legacy-final-false', dict(base, final_verdict=false), False)]
    for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        rows.append(('legacy-' + key, dict(base, **{key: [{'criterion': 'synthetic blocking finding'}]}), False))
        for value in (None, False, {}, 'malformed'):
            rows.append(('legacy-malformed-' + key, dict(base, final_verdict=false, **{key: value}), True))
    rows += [('legacy-no-rejection', base, True), ('legacy-pass-no-rejection', dict(base, verdict='pass'), True),
        ('legacy-final-true-empty', dict(base, final_verdict=dict(approved=True, summary='synthetic passing verdict')), True)]
    for value in (None, False, 'malformed', {'approved': 1}, {'approved': 'false'}):
        rows.append(('legacy-malformed-final', dict(base, issues=[{}], final_verdict=value), True))
    return rows


def failure_semantic(api, f):
    failure_call(api, f)
    if f.request['attempt'] != 1: return
    for value in (None, f.contract): failure_probe(api, f, 'evidence', 'verdict_ref', value, True)
    for approved, arrays in ((True, []), (False, []), (True, [{'criterion': 'blocking synthetic fixture finding'}])):
        for family in ('contract_review', 'qa_verdict'):
            verdict = failure_verdict(f, family, approved, arrays)
            reference = f.pin_new('semantic-' + family, verdict)
            if approved and not arrays: failure_probe(api, f, 'evidence', 'verdict_ref', reference, True)
            else:
                saved = copy.deepcopy((f.evidence, f.authority, f.policy)); f.evidence['verdict_ref'] = reference; f.bind(); failure_call(api, f)
                f.evidence, f.authority, f.policy = saved
    malformed = dict(f.gate, final_verdict={'approved': 'false', 'summary': 'wrong type'})
    failure_probe(api, f, 'evidence', 'verdict_ref', f.pin_new('invalid-verdict', malformed), True)
    failure_probe(api, f, 'capture', 'outcome', 'success', True)
    failure_call(api, f)
    for label, verdict, deny in failure_legacy_verdicts(f):
        saved = copy.deepcopy((f.evidence, f.authority, f.policy)); f.evidence['verdict_ref'] = f.pin_new(label, verdict); f.bind()
        inputs = repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence)); files = f.files()
        try: failure_call(api, f, deny)
        except AssertionError as exc:
            print('SEMANTIC_SCHEMA_CONTEXT ' + label + ': ' + str(exc.__context__), file=sys.stderr); raise
        finally:
            require(inputs == repr((f.request, f.policy, f.state, f.authority, f.capture, f.evidence)) and files == f.files(), 'legacy schema union preserves inputs and fixture bytes/modes')
            f.evidence, f.authority, f.policy = saved
        failure_call(api, f)


def failure_relabel(api, f):
    failure_call(api, f)
    opposite = 'semantic' if f.request['cause'] == 'infrastructure' else 'infrastructure'
    for target, fields in {'request': {'cause': [opposite, 'success', 'probe', None], 'attempt': [0, 4, True, '1', None],
            'authority_ref': [f.policy['authority_ref']], 'capture_ref': [f.authority['capture_ref']], 'producer': [f.producer], 'budget': [99], 'success': [True]},
            'policy': {'repository': ['wrong/repository'], 'extra': [True]},
            'authority': {'role': ['Generator'], 'approved': [False, 1], 'schema_version': [True, 2], 'extra': [0],
                'candidate': [dict(f.candidate, source_commit='0'*40)], 'producer': [{'agent_id':'', 'session_id':'fixture'}]},
            'evidence': {'kind': [opposite, 'probe'], 'extra': [False]}}.items():
        for field, values in fields.items():
            for value in values: failure_probe(api, f, target, field, value, target in ('authority', 'evidence'))
    for field in ('operation_id', 'contract_id', 'feature_id', 'step_key', 'stage', 'cause', 'attempt'):
        saved = f.request.pop(field); failure_call(api, f, True); f.request[field] = saved; failure_call(api, f)
    for field in ('authority_ref', 'coordination_ref'):
        for key, value in (('path', '../outside-sentinel'), ('path', '/tmp/unsafe'), ('sha256', '0'*64), ('revision', 'HEAD'), ('revision', '0'*40), ('extra', 1)):
            reference = dict(f.policy[field]); reference[key] = value; failure_probe(api, f, 'policy', field, reference)
        failure_probe(api, f, 'policy', field, f.nonregular_artifact(f.policy[field]))
    cycle = []; cycle.append(cycle)
    for value in (float('nan'), float('inf'), cycle): failure_probe(api, f, 'request', 'attempt', value)
    for target in ('request', 'policy'):
        original = copy.deepcopy(getattr(f, target))
        for value in (None, True, [], 'invalid-root'):
            setattr(f, target, value); failure_call(api, f, True); setattr(f, target, copy.deepcopy(original)); failure_call(api, f)
    saved = copy.deepcopy(f.policy); f.policy['authority_ref'] = None; failure_call(api, f, True); f.policy = saved
    for target in ('authority', 'capture', 'evidence'):
        original = copy.deepcopy(getattr(f, target))
        for key in original:
            value = copy.deepcopy(original); del value[key]; failure_pinned(api, f, target, value)
        value = dict(original, unknown=True); failure_pinned(api, f, target, value)
    failure_pinned(api, f, 'evidence', dict(f.evidence, capture_ref=f.contract))
    for field in ('coordination_ref', 'authority_ref', 'repository'):
        value = f.policy.pop(field); failure_call(api, f, True); f.policy[field] = value; failure_call(api, f)
    for path in ('src/code.py', 'contract.json'):
        target = f.root / path; raw = target.read_bytes(); mode = target.stat().st_mode
        target.write_bytes(raw + b' changed'); failure_call(api, f, True); target.write_bytes(raw); failure_call(api, f)
        target.chmod(mode ^ 0o111); failure_call(api, f, True); target.chmod(mode); failure_call(api, f)
    failure_call(api, f)


def failure_continuity(api, f):
    failure_call(api, f)
    original = copy.deepcopy(f.state)
    f.state['history'].append(dict(at='later', event='handoff', detail='synthetic agent/session/generation handoff preserves allocated identity'))
    if 'updated_at' in f.state: f.state['updated_at'] = '2026-10-15T03:00:00Z'
    authority_ref = f.policy['authority_ref']; f.current(); f.policy['authority_ref'] = authority_ref; failure_call(api, f)
    for field, values in {'circuit_breaker': [dict(f.state['circuit_breaker'], **{'failure-step': {'attempts': a, 'limit': limit}}) for a, limit in ((0,3),(1,4),(True,3),(4,3))],
            'scope_budget': [dict(f.state['scope_budget'], total_lines_changed=0)], 'authority': [{'fixture': ['renamed']}],
            'current_phase': ['renamed-phase'], 'current_feature': ['123'], 'active_contract_id': ['123'], 'status': ['complete'],
            'history': [[], [dict(original['history'][0], detail='rewritten')]], 'updated_at': [None, 1],
            'execution_lanes': [[], [{'changed': True}]], 'process_id': ['new-authority']}.items():
        for value in values:
            if field == 'execution_lanes' and field in f.state and value == f.state[field]: continue
            failure_probe(api, f, 'state', field, value)
    if 'execution_lanes' in f.state:
        saved_policy = copy.deepcopy(f.policy); saved = f.state.pop('execution_lanes'); authority_ref = f.policy['authority_ref']; f.current(); f.policy['authority_ref'] = authority_ref
        failure_call(api, f, True); f.state['execution_lanes'] = saved; f.write('coordination122.json', f.state); f.policy = saved_policy; failure_call(api, f)
        for value in (list(reversed(saved)), [dict(saved[0], operation_id='renamed'), *saved[1:]]): failure_probe(api, f, 'state', 'execution_lanes', value)
    for field in ('operation_id', 'step_key', 'stage', 'contract_id', 'feature_id'):
        failure_probe(api, f, 'request', field, 'renamed-after-handoff')
    saved = copy.deepcopy((f.state, f.policy, f.authority)); del f.state['updated_at']; f.current()
    f.authority['coordination_ref'] = copy.deepcopy(f.policy['coordination_ref']); f.policy['authority_ref'] = f.pin_new('schema-invalid-anchor', f.authority)
    failure_call(api, f, True)  # Current shipped schema requires updated_at even when both snapshots omit it.
    f.state, f.policy, f.authority = saved; f.write('coordination122.json', f.state)
    failure_call(api, f)


def run_failure_case(name, api):
    if not callable(getattr(api, 'route_failed_attempt', None)):
        print('SETUP_ERROR: missing route_failed_attempt API; not intended behavioral red', file=sys.stderr); raise SystemExit(2)
    previous = os.environ.get('NIZAM_WA120_FIXTURE'); os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
    try:
        configurations = [(1, None, 'semantic' if name == 'semantic-failed' else 'infrastructure')]
        if name in ('infrastructure-failed', 'semantic-failed'): configurations += [(a, None, configurations[0][2]) for a in (2,3)]
        if name == 'reject-cause-relabel': configurations += [(1, None, 'semantic')]
        if name == 'counter-continuity': configurations = [(a, lanes, 'infrastructure') for a in (1,2,3) for lanes in (None, [{'operation_id':'other-a'}, {'operation_id':'other-b'}])]
        for attempt, lanes, cause in configurations:
            with tempfile.TemporaryDirectory(prefix='nizam122-failure-') as parent:
                f = FailureFixture(api, parent, cause, attempt, lanes)
                (failure_infrastructure if name == 'infrastructure-failed' else failure_semantic if name == 'semantic-failed' else failure_relabel if name == 'reject-cause-relabel' else failure_continuity)(api, f)
    finally:
        if previous is None: os.environ.pop('NIZAM_WA120_FIXTURE', None)
        else: os.environ['NIZAM_WA120_FIXTURE'] = previous


CONTROL_CASES = ('ci-candidate-bound', 'ci-blocker-rejected')
CONTROL_ORIGIN = 'https://github.com/niq-cnr/nizam-framework.git'
CONTROL_REPOSITORY = 'niq-cnr/nizam-framework'
CONTROL_PREFIX = '.agent/evidence/123/experiment/'
CONTROL_APPROVAL = '452a5a5f748b5234ce1da3ad765b0da8f622cb53'


class ControlsFixture(FailureFixture):
    """SYNTHETIC parser proof, never an attestation of hosted execution or consent.

    Real Git objects, current convergence and A10 APIs are exercised locally. The
    REST/log/namespace/evaluator attestations below are synthetic discrimination
    inputs. Only the separately selected hosted proof can satisfy controls-ready.
    """
    commit = FailureFixture.commit  # Disable maintenance before our first commit.

    def __init__(self, api, parent, defect=None, seed=None):
        self.api = api; self.parent = Path(parent); self.root = self.parent / 'root'
        self.serial = 0; self.nodes = {}; self.originals = {}; self.payloads = {}; self.defect=defect; self.applied=[]; self.manifests={}; self.synthetic_projection=False; self.namespace=self.parent.name; self.checkouts={}; self._raw_cache={}
        tool_paths = ['tools/workflow_assurance_ci.py', 'tools/convergent_review.py',
            'tools/evaluate_convergent_review_prompt.py', 'tools/linux_trial_sandbox.sh',
            'tools/isolated_trial_adapter.py', 'tools/verify_lib.sh',
            '.github/workflows/compliance.yml', 'tools/fixtures_self_test.sh',
            '.github/scripts/test_sandbox_boundaries.py', 'tools/test_convergent_review.py',
            'templates/convergent-review-prompt.md']
        tool_paths += sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'schema').glob('*.schema.json'))
        source_profile=bool(defect and defect['site']=='source-contract')
        if seed and not source_profile:
            self.root=seed.root;self.source=seed.source
            self.ambient_source=seed.ambient_source;self.packet_base=seed.packet_base;self.fixture_source_path=seed.fixture_source_path
            self._fixture_housekeeping_disabled = True
            self._raw_cache = seed._raw_cache
            require(git(self.root,'remote','get-url','origin')==CONTROL_ORIGIN,'seed actual origin stable')
            git(self.root,'merge-base','--is-ancestor',self.source,'HEAD')
            for path in seed.source_paths:require((self.root/path).is_file() and not (self.root/path).is_symlink(),'seed complete Source remains materialized')
        else:
            subprocess.check_call(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(self.root)])
            git(self.root, 'config', 'user.name', 'SYNTHETIC123 Independent Parser Fixture')
            git(self.root, 'config', 'user.email', 'synthetic123@example.invalid')
            git(self.root, 'config', 'gc.auto', '0')
            git(self.root, 'config', 'maintenance.auto', 'false')
            self._fixture_housekeeping_disabled = True
            git(self.root, 'remote', 'set-url', 'origin', CONTROL_ORIGIN)
            c123_ae = json.loads((ROOT / '.agent/contracts/123.json').read_bytes())['approval_evidence']
            bounded_paths = sorted(set(tool_paths + [
                'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py',
                '.agent/contracts/123.json', c123_ae['mode_a'], c123_ae['contract_review'],
                '.agent/evidence/phase018-preflight/activation-authority.json',
            ]))
            git(self.root, 'checkout', '--quiet', '--orphan', 'synthetic-ambient')
            git(self.root, 'rm', '-rf', '--quiet', '--ignore-unmatch', '.')
            git(self.root, 'checkout', '--quiet', git(ROOT, 'rev-parse', 'HEAD'), '--', *bounded_paths)
            self.ambient_source = self.commit('SYNTHETIC bounded ambient source baseline')
            git(self.root, 'checkout', '--quiet', '--detach', self.ambient_source)
            self.source = self.ambient_source
            self.fixture_source_path='tools/zz_wa123_synthetic_candidate.txt'
            require(not git(self.root,'status','--porcelain=v1'),'full ambient clone is clean before private source anchors')
            require(not git(self.root,'ls-tree',self.ambient_source,'--',self.fixture_source_path),'private synthetic source input is absent from ambient tree')
            target=self.root/self.fixture_source_path
            with target.open('xb') as stream:stream.write(b'SYNTHETIC_INPUT_VERSION = 0\n')
            target.chmod(0o644)
            self.packet_base=self.commit('SYNTHETIC private UTF8 source baseline F0')
            target.write_bytes(b'SYNTHETIC_INPUT_VERSION = 1\n')
            if source_profile:
                value=self.value('source-contract',json.loads((self.root/'.agent/contracts/123.json').read_bytes()))
                self.write('.agent/contracts/123.json',canonical(value)+b'\n')
            self.source=self.commit('SYNTHETIC private meaningful UTF8 source candidate F1')
        require(git(self.root,'show','-s','--format=%P',self.source)==self.packet_base,'private F1 has exactly F0 as parent')
        require(git(self.root,'show','-s','--format=%P',self.packet_base)==self.ambient_source,'private F0 has exactly ambient checkout as parent')
        require(self.fixture_source_path>'tools/workflow_assurance.py','private source input preserves original first Source drift target')
        require(git(self.root,'diff','--name-only',self.ambient_source,self.packet_base)==self.fixture_source_path,'F0 retains every ambient tracked blob and mode')
        changed=sorted([self.fixture_source_path]+(['.agent/contracts/123.json'] if source_profile else []))
        require(git(self.root,'diff','--name-only',self.packet_base,self.source).splitlines()==changed,'F1 changes only meaningful private input and designated contract mutation')
        require(self.ref(self.fixture_source_path,self.packet_base)['sha256']==sha(b'SYNTHETIC_INPUT_VERSION = 0\n'),'F0 contains actual synthetic UTF8 baseline')
        require(self.ref(self.fixture_source_path,self.source)['sha256']==sha(b'SYNTHETIC_INPUT_VERSION = 1\n'),'F1 contains actual changed synthetic UTF8 input')
        self.source_paths = list(seed.source_paths) if seed and not source_profile else git(self.root,'ls-tree','-r','--name-only',self.source).splitlines()
        self.outside = self.parent / 'outside-sentinel'; self.outside.write_bytes(b'SYNTHETIC outside unchanged\n'); self.outside.chmod(0o600)
        self.inputs = copy.deepcopy(seed.inputs) if seed and not source_profile else dict(source=['tools/workflow_assurance.py',self.fixture_source_path], contracts=['.agent/contracts/123.json'],
            tests=['tools/test_workflow_assurance.py'], tools=tool_paths, unknown_dependencies=[])
        self.candidate = copy.deepcopy(seed.candidate) if seed and not source_profile else api.assess_repository(self.root, self.source, self.inputs, ['PYTHONDONTWRITEBYTECODE'], {})
        api.validate_identity(self.candidate)
        require(git(self.root,'rev-parse',self.source+'^{tree}')==self.candidate['source_tree'],'reused actual Source tree identity')
        for category in ('source','tests','tools','contracts'):
            for entry in self.candidate['assessed_inputs'][category]:
                target=self.root/entry['path'];require(sha(target.read_bytes())==entry['sha256'] and bool(target.stat().st_mode&0o111)==entry['executable'],'immutable seed protected bytes/mode stable')
        self.good_contract = copy.deepcopy(seed.good_contract) if seed and not source_profile else self.ref('.agent/contracts/123.json',CONTROL_APPROVAL)
        self.contract = self.ref('.agent/contracts/123.json', self.source if source_profile else CONTROL_APPROVAL)
        gate = dict(final_verdict=dict(approved=True), issues=[], missing_acceptance_coverage=[], unsupported_claims=[])
        if seed and not source_profile and (not defect or defect['site'] not in ('provisional', 'authority')):
            self.prerequisites = copy.deepcopy(seed.prerequisites)
            authority_ref = copy.deepcopy(seed.authority_ref)
            authority = copy.deepcopy(seed.authority)
            scope = copy.deepcopy(seed.scope)
        else:
            approved = self.read(self.good_contract); ae = approved['approval_evidence']
            self.prerequisites = []
            for kind, key, field in (('mode-a', 'mode_a', 'reviewed_commit'), ('contract-review', 'contract_review', 'reviewed_revision')):
                artifact=self.ref(ae[key],self.source); actual=self.read(artifact)
                self.prerequisites.append(dict(kind=kind, artifact=artifact, feature_id='123',
                    assessed_revision=actual[field], contract_sha256=ae['proposal_sha256']))
            self.prerequisites.append(dict(kind='approved-contract', artifact=self.contract, feature_id='123',
                assessed_revision=self.contract['revision'], contract_sha256=self.contract['sha256']))
            provisional = dict(gate, feature_id='123', reviewed_revision=self.contract['revision'],
                approved_contract_sha256=self.contract['sha256'], reviewer='SYNTHETIC-provisional-parser-only')
            provisional_ref = self.put('provisional', provisional)
            self.prerequisites.append(dict(kind='provisional-bundle', artifact=provisional_ref, feature_id='123',
                assessed_revision=self.contract['revision'], contract_sha256=self.contract['sha256']))
            origin_ref = self.ref('.agent/evidence/phase018-preflight/activation-authority.json', self.source)
            original = self.read(origin_ref); scope = {k: original['scope'][k] for k in ('phase','features','original_estimate_lines','ceiling_130pct')}
            authority = dict(schema_version=1, role='Root', purpose='experiment-only', repository=CONTROL_ORIGIN,
                **{k: original[k] for k in ('owner','gate','operator_instruction_verbatim')}, scope=scope,
                source_authority_ref=origin_ref, mapping=dict(repository_origin=CONTROL_ORIGIN, review_repository=CONTROL_REPOSITORY))
            authority_ref = self.put('authority', authority)
            self.authority_ref = authority_ref; self.authority = authority; self.scope = scope
        self.shadow = dict(repository=CONTROL_ORIGIN, current_phase='018-workflow-assurance-controls', current_feature='123',
            status='experiment-pending', updated_at='2026-10-15T00:00:00Z',
            scope_budget=dict(original_estimate_lines=7200,total_lines_changed=4303,per_feature=[]),
            circuit_breaker={},history=[],purpose='experiment-only')
        report = dict(gate, required_fixes=[])
        self.capture_producer = self.value('capture-producer',dict(agent_id='wa123-capable-ci', session_id='123-ci-capture-attempt1'))
        self.verify_producer = self.value('verify-producer',dict(agent_id='wa123-capable-ci', session_id='123-ci-verify-attempt1'))
        prior=self.value('carried-ledger',None)
        if seed and not source_profile and defect and defect['site'] not in ('shadow', 'report', 'carried-ledger'):
            shadow_ref = copy.deepcopy(seed.selection['shadow_state_ref'])
            report_ref = copy.deepcopy(seed.selection['report_ref'])
        else:
            shadow_ref = self.put('shadow', self.shadow)
            report_ref = self.put('report', report)
        self.selection = dict(schema_version=1, mode='capture', repository_origin=CONTROL_ORIGIN,
            review_repository=CONTROL_REPOSITORY, source_commit=self.source, source_tree=self.candidate['source_tree'],
            inputs=self.inputs, contract_ref=self.contract, authority_ref=authority_ref, prerequisites=self.prerequisites,
            producer=self.capture_producer, packet_base=self.packet_base, prior_ledger=self.put('prior-ledger',prior) if prior else None,
            report_ref=report_ref, prompt_ref=self.ref('templates/convergent-review-prompt.md', self.source),
            runner_ref=self.ref('tools/workflow_assurance_ci.py',self.source), adapter_ref=self.ref('tools/linux_trial_sandbox.sh',self.source),
            evaluator_ref=self.ref('tools/evaluate_convergent_review_prompt.py',self.source), shadow_state_ref=shadow_ref,
            candidate=None,a10_policy_ref=None,capture_pack_ref=None)
        self.shadow=self.read(self.selection['shadow_state_ref'])
        self.capture_selection = self.put('selection-capture',self.selection)
        self.checkout=self.stage_checkout('capture',self.capture_selection)
        if seed and not source_profile and getattr(seed, '_shared_exp', None) is not None:
            import shutil
            self.exp = seed._shared_exp
            self._reused_exp = True
            shutil.rmtree(self.exp / CONTROL_PREFIX, ignore_errors=True)
            git(self.exp, 'reset', '--quiet', '--hard', self.source)
        else:
            self.exp = self.parent / 'experiment'
            self._reused_exp = False
            git(self.root,'worktree','add','--quiet','--detach',str(self.exp),self.source)
            if not seed and not defect:
                self._shared_exp = self.exp
        self.exp_write('inputs/selection-capture.json',self.raw(self.capture_selection))
        self.exp_commit('SYNTHETIC capture selected input')
        self.make_evaluation(self.read(self.selection['report_ref']))
        capture_tip = git(self.exp,'rev-parse','HEAD')
        self.capture_host, self.capture_pack = self.host('capture',capture_tip,self.capture_selection,
            [self.candidate_ref,self.capability_ref,self.evaluation_ref,self.replay_ref,self.map_ref,self.map_capture_ref])
        app = dict(schema_version=1,role='Root',repository=CONTROL_ORIGIN,feature_id='123',stage='source-ready',
            candidate_sha256=sha(canonical(self.candidate)),approved=True,authority_ref=authority_ref,
            owner=authority['owner'],gate=authority['gate'],scope=scope)
        self.a10_policy = dict(schema_version=1,repository=CONTROL_ORIGIN,feature_id='123',stage='source-ready',operation_id='123-ci-capture',
            candidate=self.candidate,contract=self.contract,operator=self.put('operator',app),producer=self.capture_producer,
            prerequisites=self.prerequisites,commands=[dict(argv=self.map_capture['argv'],expected_exit=0,proof_kind='success',
                diagnostic='WA123_A11_APPROVED',capture=self.map_capture_ref)],from_status='experiment-pending',
            to_status='experiment-source-ready',at='2026-10-15T00:01:00Z',recovery=None)
        self.receipt = {k:copy.deepcopy(self.a10_policy[k]) for k in ('schema_version','repository','feature_id','stage','operation_id','candidate','producer','prerequisites')}
        self.receipt.update(status='passed',contract_ref=self.contract,operator_ref=self.a10_policy['operator'],verdict=gate,
            checks=[dict(argv=self.map_capture['argv'],executed=True,outcome='success',exit_code=0,
                stdout=self.map_capture['stdout'],stderr=self.map_capture['stderr'],capture=self.map_capture_ref)])
        self.receipt=self.value('receipt-body',self.receipt)
        self.receipt_ref = self.put('receipt',self.receipt)
        self.a10_policy['recovery'] = self.receipt_ref
        self.policy_ref = self.put('a10-policy',self.a10_policy)
        self.verify_selection_value = dict(self.selection,mode='verify',producer=self.verify_producer,
            candidate=self.candidate,a10_policy_ref=self.policy_ref,capture_pack_ref=self.capture_pack)
        self.verify_selection = self.put('selection-verify',self.verify_selection_value)
        self.stage_checkout('verify',self.verify_selection)
        for label,ref in (('selection-verify',self.verify_selection),('policy-verify',self.policy_ref),('receipt-verify',self.receipt_ref)):
            self.exp_write('inputs/'+label+'.json',self.raw(ref))
        self.exp_commit('SYNTHETIC independently selected verify inputs')
        computation_policy=copy.deepcopy(self.a10_policy); computation_receipt=copy.deepcopy(self.receipt)
        if source_profile:
            # Invalid metadata cannot itself pass120. Compute unchanged120 with the
            # genuine approved object, then project only its contract bindings in
            # this explicitly SYNTHETIC invalid123 graph before packing outputs.
            good_prerequisites=copy.deepcopy(self.prerequisites)
            for entry in good_prerequisites:
                if entry['kind']=='approved-contract':entry.update(artifact=self.good_contract,assessed_revision=CONTROL_APPROVAL,contract_sha256=self.good_contract['sha256'])
                if entry['kind']=='provisional-bundle':
                    record=self.read(entry['artifact']);record.update(reviewed_revision=CONTROL_APPROVAL,approved_contract_sha256=self.good_contract['sha256'])
                    entry.update(artifact=self.put('computation-provisional',record),assessed_revision=CONTROL_APPROVAL,contract_sha256=self.good_contract['sha256'])
            computation_policy.update(contract=self.good_contract,prerequisites=good_prerequisites)
            computation_receipt.update(contract_ref=self.good_contract,prerequisites=good_prerequisites)
            computation_policy['recovery']=self.put('computation-receipt',computation_receipt)
            self.synthetic_projection=True
        if defect and defect['site']=='receipt-body':
            computation_receipt['status']='passed'
            computation_policy['recovery']=self.put('computation-receipt',computation_receipt)
            self.synthetic_projection=True
        verified = api.verify_stage_receipt(self.exp,computation_receipt,policy=computation_policy)
        advance = api.plan_receipt_transition(self.exp,self.shadow,computation_receipt,policy=computation_policy)
        noop = api.plan_receipt_transition(self.exp,advance['state'],computation_receipt,policy=computation_policy)
        republish = api.plan_receipt_transition(self.exp,self.shadow,None,policy=computation_policy)
        absent = copy.deepcopy(computation_policy); absent['recovery']['path'] += '.missing-wa123'
        require(not git(self.root,'ls-tree',absent['recovery']['revision'],'--',absent['recovery']['path']), 'synthetic recovery path actually absent')
        rerun = api.plan_receipt_transition(self.exp,self.shadow,None,policy=absent)
        conflicting = copy.deepcopy(advance['state']); conflicting['history'].append(copy.deepcopy(conflicting['history'][-1]))
        rejected(api,lambda:api.plan_receipt_transition(self.exp,conflicting,computation_receipt,policy=computation_policy),'actual duplicate conflict exercise')
        self.a10_result = dict(receipt=verified,advance=advance,noop=noop,republish=republish,rerun_required=rerun,conflict_rejected=True)
        if self.synthetic_projection:
            old_digest=sha(canonical(computation_receipt));new_digest=sha(canonical(self.receipt))
            def project(value):
                if value==computation_receipt:return copy.deepcopy(self.receipt)
                if type(value) is dict:return {k:project(v) for k,v in value.items()}
                if type(value) is list:return [project(v) for v in value]
                if type(value) is str:return value.replace(old_digest,new_digest)
                return value
            self.a10_result=project(self.a10_result)
        require([advance['action'],noop['action'],republish['action'],rerun['action']] == ['advance','noop','republish','rerun-required'],'actual four A10 actions')
        self.exp_write('verify/result.json',self.a10_result); self.exp_write('verify/stdout',self.payloads['verify/result.json']); self.exp_write('verify/stderr',b'')
        outputs = self.exp_commit('SYNTHETIC A10 parser results'+(' with invalid-binding projection' if self.synthetic_projection else ' from actual local APIs')+'; not hosted')
        result_ref = self.exp_ref('verify/result.json',outputs)
        capture = self.capture([sys.executable,'tools/workflow_assurance_ci.py','verify','--selection','.agent/evidence/123/selection.json',
            '--output',str(self.parent/'wa123-verify')],self.checkouts['verify']['sha'],self.verify_producer,self.exp_ref('verify/stdout',outputs),self.exp_ref('verify/stderr',outputs),cwd=self.root)
        self.exp_write('verify/capture.json',capture); tip=self.exp_commit('SYNTHETIC verify capture representation')
        a10_capture_ref=self.exp_ref('verify/capture.json',tip)
        verify_host, pack = self.host('verify',tip,self.verify_selection,[self.receipt_ref,result_ref,a10_capture_ref])
        git(self.root,'checkout',tip,'--',CONTROL_PREFIX);self.materialized_tip=tip
        self.commit_paths('SYNTHETIC materialized immutable experiment outputs', CONTROL_PREFIX)
        self.evidence = dict(schema_version=1,candidate=self.candidate,checkout=self.checkout,
            capture_selection_ref=self.capture_selection,verify_selection_ref=self.verify_selection,evaluation_ref=self.evaluation_ref,
            replay_ref=self.replay_ref,trial_provenance=self.trials,a11_capture_ref=self.map_capture_ref,a11_result_ref=self.map_ref,
            a10_receipt_ref=self.receipt_ref,a10_result_ref=result_ref,a10_capture_ref=a10_capture_ref,capability_ref=self.capability_ref,
            capture_host=self.capture_host,verify_host=verify_host,pack_ref=pack,inventory=self.manifests['verify']['inventory'])
        self.review = dict(schema_version=1,role='Evaluator',reviewer='SYNTHETIC-independent-host-parser-reviewer',source_commit=self.source,
            capture_selection_ref=self.capture_selection,verify_selection_ref=self.verify_selection,evidence_ref=None,
            capture_host=self.capture_host,verify_host=verify_host,**gate,evidence_files=[self.capture_host['metadata_ref']['path'],verify_host['metadata_ref']['path']])
        self.policy = dict(schema_version=1,role='Root',repository_origin=CONTROL_ORIGIN,review_repository=CONTROL_REPOSITORY,
            feature_id='123',selection_ref=self.verify_selection,evidence_ref=None,hosted_review_ref=None,approved=True)
        self.evidence=self.value('evidence-body',self.evidence)
        self.bind()
        self.policy=self.value('policy',self.policy)
        self.evidence,self.policy,self.review=copy.deepcopy((self.evidence,self.policy,self.review))
        require(len(self.applied)==(1 if defect else 0),'exactly one deliberate defect site applied')
        self.assert_bindings()

    def commit_paths(self, message, *paths):
        if not getattr(self, '_fixture_housekeeping_disabled', False):
            for key, value in (('gc.auto', '0'), ('maintenance.auto', 'false')):
                git(self.root, 'config', '--local', key, value)
            self._fixture_housekeeping_disabled = True
        git(self.root, 'add', '--', *(paths or ('.',)))
        if git(self.root, 'diff', '--cached', '--name-only'):
            git(self.root, 'commit', '-qm', message)
        return git(self.root, 'rev-parse', 'HEAD')

    def ref(self, path, revision=None):
        revision = revision or git(self.root, 'rev-parse', 'HEAD')
        key = (revision, path)
        if key not in self._raw_cache:
            self._raw_cache[key] = subprocess.check_output(['git', '-C', str(self.root), 'show', revision + ':' + path])
        return dict(path=path, sha256=sha(self._raw_cache[key]), revision=revision)

    def stage_checkout(self,mode,selection):
        # This outer CLI input belongs to a Root record-only checkout, never the
        # Source-relative output branch. Both historical versions remain in Git.
        path='.agent/evidence/123/selection.json';target=self.root/path
        present=self.value(mode+'-selection-present',True)
        if present:self.write(path,self.value(mode+'-fixed-selection-bytes',self.raw(selection)))
        elif target.exists():target.unlink()
        revision=self.commit_paths('SYNTHETIC '+mode+' fixed CLI selection checkout', path)
        checkout=dict(sha=revision,tree=git(self.root,'rev-parse',revision+'^{tree}'),event='push',
            event_head=revision,event_base=None,parents=git(self.root,'show','-s','--format=%P',revision).split())
        self.checkouts[mode]=self.value(mode+'-checkout',checkout)
        return self.checkouts[mode]

    def raw(self, reference):
        key = (reference['revision'], reference['path'])
        if key not in self._raw_cache:
            self._raw_cache[key] = subprocess.check_output(['git','-C',str(self.root),'show',reference['revision']+':'+reference['path']])
        return self._raw_cache[key]

    def read(self, reference): return json.loads(self.raw(reference))

    def value(self,label,value):
        result=copy.deepcopy(value)
        if self.defect and self.defect['site']==label:
            changed=self.defect['change'](result,self)
            if changed is not None and (type(changed) is bytes or type(value) in (bytes,bool) or value is None):result=changed
            self.applied.append(label)
        return result

    def put(self,label,value):
        self.serial += 1; path='.agent/evidence/123/synthetic-root/%s/%04d-%s' % (self.namespace,self.serial,label)
        value=self.value(label,value); data=value if type(value) is bytes else canonical(value)+b'\n'
        self.write(path,data); rev=self.commit_paths('SYNTHETIC parser record '+label, path)
        self._raw_cache[(rev, path)] = data
        reference=dict(path=path, sha256=sha(data), revision=rev)
        self.nodes[label]=reference; self.originals[label]=copy.deepcopy(value); return reference

    def exp_write(self,path,value):
        target=self.exp/(CONTROL_PREFIX+path); target.parent.mkdir(parents=True,exist_ok=True)
        value=self.value(path,value);data=value if type(value) is bytes else canonical(value)+b'\n'
        self.payloads[path]=data;target.write_bytes(data)

    def exp_commit(self,message):
        git(self.exp,'add','--',CONTROL_PREFIX); git(self.exp,'commit','--quiet','-m',message)
        return git(self.exp,'rev-parse','HEAD')

    def exp_ref(self,path,revision):
        rel = CONTROL_PREFIX + path
        if path in self.payloads:
            self._raw_cache[(revision, rel)] = self.payloads[path]
        return self.ref(rel,revision)

    def capture(self,argv,revision,producer,stdout,stderr,cwd=None):
        return dict(schema_version=1,argv=argv,cwd=str(self.exp if cwd is None else cwd),revision=revision,candidate_sha256=sha(canonical(self.candidate)),
            environment=self.candidate['environment'],producer=producer,executed=True,outcome='success',exit_code=0,stdout=stdout,stderr=stderr)

    def make_evaluation(self,report):
        cr=load_api(ROOT/'tools/convergent_review.py'); ev=load_api(ROOT/'tools/evaluate_convergent_review_prompt.py')
        packet_path=self.exp/(CONTROL_PREFIX+'evaluation/packet.json'); packet_path.parent.mkdir(parents=True,exist_ok=True)
        cr.cmd_build_packet(argparse.Namespace(repo=str(self.exp),repository=CONTROL_REPOSITORY,review_id='wa123-controls',
            mode='ordinary',base=self.selection['packet_base'],head=self.source,output=str(packet_path)))
        packet=cr.parse_json_bytes(packet_path.read_bytes(),'synthetic packet'); digest=sha(packet_path.read_bytes())
        self.exp_write('candidate.json',self.candidate); trial_paths=[]; receipts=[]; paths=[]
        prior=self.selection['prior_ledger'];prior_file=packet_path.parent/'prior-ledger.json' if prior else None
        if prior:prior_file.write_bytes(self.raw(prior))
        runner=str(self.exp/'tools/workflow_assurance_ci.py'); adapter=str(self.exp/'tools/linux_trial_sandbox.sh')
        for n in (1,2,3):
            directory=self.exp/(CONTROL_PREFIX+'evaluation/trial-'+str(n)); directory.mkdir()
            pp=directory/'packet.json'; prompt=directory/'prompt.md'; output=directory/'trial.json'
            pp.write_bytes(packet_path.read_bytes())
            trial_prior=directory/'prior-ledger.json' if prior else None
            if prior:trial_prior.write_bytes(self.raw(prior))
            prompt.write_text(ev.render_prompt(self.raw(self.selection['prompt_ref']).decode(),pp,n,output,trial_prior))
            trial=dict(schema_version=cr.SCHEMA_VERSION,review_id='wa123-controls',head_sha=self.source,packet_digest=digest,trial_number=n,observations=[])
            output.write_bytes(cr.canonical_json_bytes(trial)); (directory/'runner.stdout').write_bytes(b''); (directory/'runner.stderr').write_bytes(b'')
            trial_paths.append(str(output)); paths.append((pp,prompt,output))
            receipts.append(dict(trial_number=n,prompt_digest=sha(prompt.read_bytes()),trial_digest=sha(output.read_bytes()),
                isolated_packet_digest=digest,runner_exit=0,isolation_adapter_digest=self.selection['adapter_ref']['sha256']))
        review_dir=self.exp/(CONTROL_PREFIX+'evaluation/review')
        cr.cmd_converge(argparse.Namespace(packet=str(packet_path),trial=trial_paths,prior_ledger=str(prior_file) if prior else None,suppression=[],output_dir=str(review_dir)))
        ledger=json.loads((review_dir/'ledger.json').read_bytes()); mapped=self.api.convergent_agf_verdict(ledger,report,
            expected_repository=CONTROL_REPOSITORY,expected_head_sha=self.source)
        expected=not bool(self.defect and self.defect.get('gate_rejection'))
        require(mapped['final_verdict']['approved'] is expected,'actual convergent mapping follows explicit clear/blocking variant expectation')
        if prior:
            require(all(json.loads(Path(p).read_bytes())['observations']==[] for p in trial_paths),'carried variants have three empty observation trials')
            require(ledger['findings'] and all(row['lifecycle']=='persisting' for row in ledger['findings']),'actual convergence carries unresolved prior findings')
        evaluation=dict(schema_version=cr.SCHEMA_VERSION,packet_digest=digest,prompt_template_digest=self.selection['prompt_ref']['sha256'],
            runner_digest=self.selection['runner_ref']['sha256'],trials=receipts,review_replay_digest=sha((review_dir/'replay.json').read_bytes()))
        self.exp_write('evaluation/prompt-evaluation.json',evaluation); self.exp_write('map/result.json',mapped)
        for label,data in (('boundary',b'SANDBOX BOUNDARIES PASS: intact 0; isolated omission controls 40/41/42; unexpected execution errors rejected\n'),('isolation',b'SYNTHETIC parser suite output; not executed namespaces\n'),('map',b'WA123_A11_APPROVED\n')):
            self.exp_write(label+'/stdout',data); self.exp_write(label+'/stderr',b'')
        execution=git(self.exp,'rev-parse','HEAD'); outputs=self.exp_commit('SYNTHETIC evaluator and capability parser outputs; no enforced execution')
        process=lambda argv,label:dict(argv=argv,cwd=str(self.exp),revision=execution,executed=True,actual_exit=0,
            stdout=self.exp_ref(label+'/stdout',outputs),stderr=self.exp_ref(label+'/stderr',outputs))
        capability=dict(schema_version=1,source_commit=self.source,checkout_sha=self.checkout['sha'],environment=self.candidate['environment'],
            producer=self.capture_producer,boundary=process([sys.executable,'.github/scripts/test_sandbox_boundaries.py'],'boundary'),
            isolation=process([sys.executable,'tools/test_convergent_review.py'],'isolation'))
        self.map_capture=self.capture([sys.executable,'tools/workflow_assurance_ci.py','map','--selection',CONTROL_PREFIX+'inputs/selection-capture.json',
            '--evaluation',str(packet_path.parent),'--output',str(self.exp/(CONTROL_PREFIX+'map/result.json'))],execution,self.capture_producer,
            self.exp_ref('map/stdout',outputs),self.exp_ref('map/stderr',outputs))
        self.exp_write('capability.json',capability); self.exp_write('map/capture.json',self.map_capture)
        tip=self.exp_commit('SYNTHETIC parser provenance representations')
        self.candidate_ref=self.exp_ref('candidate.json',outputs); self.capability_ref=self.exp_ref('capability.json',tip)
        self.map_ref=self.exp_ref('map/result.json',outputs); self.map_capture_ref=self.exp_ref('map/capture.json',tip)
        self.evaluation_ref=self.exp_ref('evaluation/prompt-evaluation.json',outputs); self.replay_ref=self.exp_ref('evaluation/review/replay.json',outputs)
        self.trials=[]
        for n,(pp,prompt,output) in enumerate(paths,1):
            refs={key:self.ref(str(path.relative_to(self.exp)),outputs) for key,path in
                (('packet_ref',pp),('prompt_ref',prompt),('output_ref',output),('stdout_ref',pp.parent/'runner.stdout'),('stderr_ref',pp.parent/'runner.stderr'))}
            invocation=[adapter,'--root',str(pp.parent),'--runner',runner,'--',runner,'--prompt',str(prompt),'--packet',str(pp),'--trial-number',str(n),'--output',str(output)]
            if prior:invocation+=['--prior-ledger',str(pp.parent/'prior-ledger.json')]
            self.trials.append(dict(number=n,**refs,evaluation_receipt_ref=self.evaluation_ref,invocation=invocation,
                **{k:self.selection[k] for k in ('runner_ref','adapter_ref','evaluator_ref')},boundary_ref=self.capability_ref))

    def inventory(self,tip):
        rows=[]
        for revision in git(self.exp,'rev-list','--reverse',self.source+'..'+tip).splitlines():
            for line in git(self.exp,'diff-tree','--no-commit-id','--raw','-r',revision).splitlines():
                meta, path = line.split('\t', 1)
                parts = meta.lstrip(':').split()
                mode, blob = parts[1], parts[3]
                rows.append(dict(path=path,revision=revision,git_blob=blob,git_mode=mode,sha256=self.ref(path,revision)['sha256']))
        return sorted(rows,key=lambda r:(r['revision'],r['path']))

    def host(self,mode,tip,selection,results):
        import io,zipfile
        checkout=self.checkouts[mode]
        git(self.exp,'update-ref','refs/wa123/proof',tip)
        path=self.parent/(mode+'.bundle')
        git(self.exp,'bundle','create','--version=2',str(path),'refs/wa123/proof','^'+self.source)
        changed=self.value(mode+'-bundle-bytes',path.read_bytes());extra={}
        if type(changed) is tuple:changed,extra=changed
        bundle=changed;pack=self.put(mode+'-bundle',bundle)
        manifest=dict(schema_version=1,mode=mode,source_commit=self.source,output_tip=tip,bundle_sha256=sha(bundle),bundle_size=len(bundle),inventory=self.inventory(tip))
        manifest.update(extra);manifest=self.value(mode+'-manifest',manifest)
        self.manifests[mode]=manifest;producer=self.capture_producer if mode=='capture' else self.verify_producer
        invocation=self.value(mode+'-invocation-body',dict(schema_version=1,mode=mode,producer=producer,selection_ref=selection,
            source_commit=self.source,checkout=checkout,environment=self.candidate['environment'],
            argv=[sys.executable,'tools/workflow_assurance_ci.py',mode,'--selection','.agent/evidence/123/selection.json',
                '--output',str(self.parent/('wa123-'+mode))],cwd=str(self.root),output_tip=manifest['output_tip'],
            bundle_sha256=sha(bundle),manifest_sha256=sha(canonical(manifest)+b'\n'),result_refs=results,actual_exit=0))
        invocation_ref=self.put(mode+'-invocation',canonical(invocation)+b'\n');raw_inv=self.raw(invocation_ref)
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in (('proof.bundle',bundle),('manifest.json',canonical(manifest)+b'\n'),('invocation.json',raw_inv)):
                info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,data)
        archive_bytes=self.value(mode+'-archive-bytes',archive.getvalue());archive_ref=self.put(mode+'-archive',archive_bytes)
        run=101 if mode=='capture' else 102;job=run+100;artifact=run+200
        artifact_name='wa123-'+mode+'-'+producer['session_id']
        run_json=dict(id=run,run_attempt=1,name='compliance',event=checkout['event'],head_sha=checkout['event_head'],status='completed',conclusion='success',repository=dict(full_name=CONTROL_REPOSITORY),unconsumed_fixture='SYNTHETIC ignored external field')
        names=['validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'];jobs=[]
        for index,name in enumerate(names):
            steps=[dict(number=1,name='WA123 '+mode,status='completed',conclusion='success'),
                dict(number=2,name='WA123 '+('verify' if mode=='capture' else 'capture'),status='completed',conclusion='skipped'),
                dict(number=3,name='Run PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/test_sandbox_boundaries.py',status='completed',conclusion='success'),
                dict(number=4,name='Run required isolation suite',status='completed',conclusion='success')] if name=='convergent_review' else []
            jobs.append(dict(id=job if name=='convergent_review' else job+10+index,run_id=run,run_attempt=1,name=name,status='completed',conclusion='success',head_sha=checkout['event_head'],steps=steps))
        raw_jobs=dict(total_count=5,jobs=jobs,unconsumed_fixture='SYNTHETIC ignored');artifacts=dict(total_count=1,artifacts=[dict(id=artifact,name=artifact_name,expired=False,size_in_bytes=len(archive_bytes),unconsumed_fixture='SYNTHETIC ignored')])
        log=b'SYNTHETIC parser log only\tWA123_INVOCATION='+raw_inv
        args=[['gh','api','repos/'+CONTROL_REPOSITORY+'/actions/runs/'+str(run)],
            ['gh','api','repos/'+CONTROL_REPOSITORY+'/actions/runs/%d/attempts/1/jobs?per_page=100'%run],
            ['gh','api','repos/'+CONTROL_REPOSITORY+'/actions/runs/%d/artifacts?per_page=100'%run],
            ['gh','run','view',str(run),'--repo',CONTROL_REPOSITORY,'--job',str(job),'--log'],
            ['gh','api','repos/'+CONTROL_REPOSITORY+'/actions/artifacts/%d/zip'%artifact]]
        fetches=[]
        for kind,argv,data in zip(('run','jobs','artifacts','job-log','archive'),args,(run_json,raw_jobs,artifacts,log,archive_bytes)):
            output=archive_ref if kind=='archive' else self.put(mode+'-'+kind,data)
            fetches.append(self.value(mode+'-fetch-'+kind,dict(kind=kind,argv=argv,cwd=str(self.root),revision=git(self.root,'rev-parse','HEAD'),
                actual_exit=0,stdout=output,stderr=self.put(mode+'-'+kind+'-stderr',b''))))
        metadata=dict(schema_version=1,mode=mode,source_commit=self.source,producer=producer,selection_ref=selection,invocation_ref=invocation_ref,
            run_id=run,attempt=1,job_id=job,artifact_id=artifact,artifact_name=artifact_name,archive_ref=archive_ref,fetches=fetches)
        host=self.value(mode+'-host',dict(repository=CONTROL_REPOSITORY,run_id=run,attempt=1,job_id=job,job='convergent_review',head_sha=checkout['event_head'],
            checkout_sha=checkout['sha'],artifact_name=artifact_name,artifact_sha256=sha(archive_bytes),metadata_ref=self.put(mode+'-metadata',metadata),job_log_ref=fetches[3]['stdout']))
        return host,pack

    def bind(self):
        evidence_ref=self.put('evidence',self.evidence)
        self.review=dict(self.review,evidence_ref=evidence_ref,capture_host=self.evidence['capture_host'],verify_host=self.evidence['verify_host'])
        self.policy=dict(self.policy,evidence_ref=evidence_ref,hosted_review_ref=self.put('hosted-review',self.review))

    def assert_bindings(self):
        """Verify fixture transport companions; skip only a declared target property."""
        import io,zipfile
        waiver=self.defect.get('waiver','') if self.defect else ''
        for ref in self.nodes.values():
            require(sha(self.raw(ref))==ref['sha256'],'fixture immutable node bytes/digest coherent')
        if not(self.defect and self.defect['name']=='evidence-checkout'):
            require(self.evidence['checkout']==self.checkouts['capture'],'fixture Evidence retains capture Checkout')
        for mode in ('capture','verify'):
            host=self.evidence[mode+'_host'];metadata=self.read(host['metadata_ref'])
            fetches={row['kind']:row for row in metadata['fetches']}
            selected=self.capture_selection if mode=='capture' else self.verify_selection
            checkout=self.checkouts[mode]
            frame=not(self.defect and self.defect.get('frame_waiver')==mode+'-checkout')
            if frame:
                require(git(self.root,'rev-parse',checkout['sha']+'^{tree}')==checkout['tree'],'fixture actual stage checkout tree')
                require(git(self.root,'show','-s','--format=%P',checkout['sha']).split()==checkout['parents'],'fixture actual stage checkout parents')
                git(self.root,'merge-base','--is-ancestor',self.source,checkout['sha'])
                tree_entries={}
                for row in git(self.root,'ls-tree','-r',checkout['sha']).splitlines():
                    m_part, p_part = row.split('\t', 1)
                    m_bits, _, m_oid = m_part.split()
                    tree_entries[p_part] = (m_bits, m_oid)
                for category in ('source','tests','tools','contracts'):
                    for entry in self.candidate['assessed_inputs'][category]:
                        raw=self.raw(dict(path=entry['path'], revision=checkout['sha'], sha256=entry['sha256']))
                        mode_bits=tree_entries[entry['path']][0]
                        require(sha(raw)==entry['sha256'] and (mode_bits=='100755') is entry['executable'],'fixture stage checkout preserves protected Source bytes/modes')
                require(checkout['event']=='push' and checkout['event_head']==checkout['sha'] and checkout['event_base'] is None,'fixture actual synthetic push checkout/event')
            fixed=frame and not(self.defect and self.defect.get('frame_waiver')==mode+'-fixed-input')
            if fixed:
                path='.agent/evidence/123/selection.json'
                actual=self.raw(dict(path=path, revision=checkout['sha'], sha256=''))
                require(actual==self.raw(selected),'fixture fixed CLI input equals independently selected immutable JSON')
            archive=self.raw(metadata['archive_ref'])
            require(metadata['archive_ref']==fetches['archive']['stdout'],'fixture raw archive selection coherent')
            if not(mode=='verify' and waiver=='archive-hash'):
                require(host['artifact_sha256']==sha(archive),'fixture Host archive SHA coherent')
            require(host['job_log_ref']==fetches['job-log']['stdout'],'fixture log selection coherent')
            if not(mode=='verify' and waiver=='archive-size'):
                require(self.read(fetches['artifacts']['stdout'])['artifacts'][0]['size_in_bytes']==len(archive),'fixture raw archive size coherent')
            if mode=='verify' and waiver=='archive-structure':continue
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                bundle=z.read('proof.bundle');manifest_raw=z.read('manifest.json');inv_raw=z.read('invocation.json')
            manifest=json.loads(manifest_raw);inv=json.loads(inv_raw)
            require(manifest_raw==canonical(self.manifests[mode])+b'\n','fixture manifest is exact produced object')
            require(inv_raw==self.raw(metadata['invocation_ref']),'fixture archive/Root invocation bytes coherent')
            require(inv['bundle_sha256']==manifest['bundle_sha256']==sha(bundle),'fixture bundle hashes coherent')
            require(inv['manifest_sha256']==sha(manifest_raw),'fixture manifest hash coherent')
            require(manifest['bundle_size']==len(bundle),'fixture bundle length coherent')
            require(inv['output_tip']==manifest['output_tip'],'fixture manifest/invocation tip coherent')
            require(inv['selection_ref']==(self.capture_selection if mode=='capture' else self.verify_selection),'fixture invocation selection coherent')
            require(inv['checkout']==checkout and host['checkout_sha']==checkout['sha'],'fixture per-stage Invocation/Host checkout coherent')
            require(inv['source_commit']==metadata['source_commit']==self.source,'fixture stage source remains immutable assessed anchor')
            run=self.read(fetches['run']['stdout']);jobs=self.read(fetches['jobs']['stdout'])
            if not(self.defect and self.defect['site'] in (mode+'-run',mode+'-jobs')):
                require(run['head_sha']==host['head_sha']==checkout['event_head'] and run['event']==checkout['event'],'fixture raw run/Host stage event head coherent')
                require(all(job['head_sha']==host['head_sha'] for job in jobs['jobs']),'fixture raw jobs stage head coherent')
            require(inv['producer']==(self.capture_producer if mode=='capture' else self.verify_producer),'fixture invocation producer coherent')
            expected_results=([self.candidate_ref,self.capability_ref,self.evaluation_ref,self.replay_ref,self.map_ref,self.map_capture_ref] if mode=='capture'
                else [self.receipt_ref,self.evidence['a10_result_ref'],self.evidence['a10_capture_ref']])
            require(inv['result_refs']==expected_results,'fixture invocation exact result_refs coherent')
            if not(mode=='verify' and waiver=='log-marker'):
                raw_log=self.raw(host['job_log_ref']);require(raw_log.count(b'WA123_INVOCATION=')==1 and raw_log.endswith(b'WA123_INVOCATION='+inv_raw),'fixture unique exact log marker coherent')
            if mode=='verify':
                require(bundle==self.raw(self.evidence['pack_ref']),'fixture selected pack/archive bytes coherent')
                require(manifest['inventory']==self.evidence['inventory'],'fixture selected inventory coherent')
        capture=json.loads(self.payloads['verify/capture.json']);outer=self.read(self.nodes['verify-invocation'])
        name=self.defect['name'] if self.defect else ''
        require(capture['argv']==outer['argv'],'fixture nested A10 Capture exact outer verify argv')
        require(capture['argv'][capture['argv'].index('--selection')+1]=='.agent/evidence/123/selection.json','fixture nested A10 fixed CLI path')
        if name!='a10-capture-wrong-cwd':
            require(capture['cwd']==outer['cwd']==str(self.root),'fixture nested A10 Capture actual Root cwd')
        if name!='a10-capture-preselection-revision':
            require(capture['revision']==outer['checkout']['sha']==self.checkouts['verify']['sha'],'fixture nested A10 Capture actual stage V revision')
        if name not in ('a10-capture-preselection-revision','verify-preselection-checkout','verify-fixed-selection-absent','verify-fixed-selection-substituted'):
            selected=self.raw(dict(path='.agent/evidence/123/selection.json', revision=capture['revision'], sha256=''))
            require(selected==self.raw(self.verify_selection),'fixture nested A10 fixed input equals independently selected verify JSON')
        result=json.loads(self.payloads['verify/result.json']);expected_receipt=self.read(self.receipt_ref)
        require(result['receipt']==expected_receipt,'fixture actual/projected result receipt equals selected immutable receipt')
        for key in ('advance','noop','republish'):
            require(result[key]['receipt']==expected_receipt,'fixture transition receipt projection coherent')
        require(result['rerun_required']['receipt'] is None,'fixture missing-recovery has no receipt')
        for key in ('republish','rerun_required'):
            require(result[key]['state']==self.shadow,'fixture recovery leaves selected initial state unchanged')
        require(result['advance']['state']==result['noop']['state'],'fixture identical replay state retained')
        event=result['advance']['state']['history'][-1];digest=sha(canonical(expected_receipt))
        require(event['receipt_sha256']==digest and event['candidate_sha256']==sha(canonical(self.candidate)),'fixture projected receipt/candidate event digests coherent')
        require(event['operation_id']==self.a10_policy['operation_id'] and event['feature_id']=='123' and event['stage']=='source-ready','fixture projected event operation binding coherent')
        require(event['detail'].endswith('('+digest+')'),'fixture projected event detail digest coherent')
        before=copy.deepcopy(self.shadow);after=copy.deepcopy(result['advance']['state'])
        require(after['history'][:-1]==before['history'] and after['status']==self.a10_policy['to_status'] and after['updated_at']==self.a10_policy['at'],'fixture projected owned transition fields coherent')
        for key in ('history','status','updated_at'):after.pop(key);before.pop(key)
        require(after==before,'fixture unowned shadow fields coherent')
        rev_trees={}
        for row in self.evidence['inventory']:
            ref={k:row[k] for k in ('path','revision','sha256')}
            require(sha(self.raw(ref))==row['sha256'],'fixture inventory bytes coherent')
            if row['revision'] not in rev_trees:
                rev_trees[row['revision']] = {line.split('\t',1)[1]: line.split('\t',1)[0].split()[:3] for line in git(self.root,'ls-tree','-r',row['revision']).splitlines()}
            require(rev_trees[row['revision']].get(row['path'])==[row['git_mode'],'blob',row['git_blob']],'fixture inventory Git mode/blob coherent')


def controls_snapshot(f):
    paths=[]
    anchors=(f.parent,) if f.root.is_relative_to(f.parent) else (f.root,f.parent)
    for anchor in anchors:
        for directory,dirs,files in os.walk(anchor):
            dirs[:]=[d for d in dirs if d not in ('.git', 'synthetic-root')]
            paths.extend(Path(directory)/name for name in files if name!='.git')
    for ref in f.nodes.values():
        p = f.root / ref['path']
        if p.exists() or p.is_symlink():
            paths.append(p)
    return ({str(p):(p.lstat().st_mode,p.lstat().st_nlink,sha(p.read_bytes())) for p in set(paths)},
        f.outside.lstat().st_mode,f.outside.read_bytes(),git(f.root,'status','--porcelain','--untracked-files=all'),
        git(f.root,'rev-parse','HEAD'),git(f.root,'show-ref'))


def controls_call(api,f,deny=False):
    before=repr((f.evidence,f.policy)); files=controls_snapshot(f)
    try:
        if deny:
            try:api.verify_controls_ready(f.root,f.evidence,policy=f.policy)
            except api.AssuranceError as exc:
                diagnostic=str(exc);require(bool(diagnostic),'nonempty targeted rejection')
                require(re.search(f.defect['cause'],diagnostic,re.I) is not None,'rejection must identify intended cause '+f.defect['name']+': '+diagnostic)
                print('EXPECTED_REJECTION '+json.dumps(dict(name=f.defect['name'],site=f.defect['site'],diagnostic=diagnostic),sort_keys=True));return
            require(False,'synthetic invalid controls proof accepted: '+f.defect['name'])
            return
        out=api.verify_controls_ready(f.root,f.evidence,policy=f.policy)
        require(out==dict(schema_version=1,feature_id='123',source_commit=f.source,checkout_sha=f.checkout['sha'],
            candidate_sha256=sha(canonical(f.candidate)),capture_run_id=101,verify_run_id=102,a11_verdict='approve',
            a10_receipt_sha256=f.receipt_ref['sha256'],transition_actions=['advance','noop','republish','rerun-required'],
            hosted_review_sha256=f.policy['hosted_review_ref']['sha256']),'exact synthetic readiness result')
        require(not receipt_ids(out)&receipt_ids([f.evidence,f.policy]),'controls result deep copy')
        return out
    finally:
        require(repr((f.evidence,f.policy))==before,'controls inputs unchanged')
        require(controls_snapshot(f)==files,'controls repository, proof, full modes, origin refs and outside sentinel unchanged')



def controls_foreign_observer(api,f):
    """Selected historical Env is independent of the observer's local runtime."""
    originals={name:getattr(api.platform,name) for name in ('python_implementation','python_version','system','machine')}
    historical={name:getattr(api,name) for name in ('verify_stage_receipt','plan_receipt_transition','assess_repository')}
    captured=copy.deepcopy(f.candidate['environment']);process=subprocess.Popen
    def observe_process(argv,*args,**kwargs):
        tokens=list(argv) if isinstance(argv,(list,tuple)) else [str(argv)]
        if tokens and Path(tokens[0]).name!='git':
            require(not any(name in ' '.join(map(str,tokens)) for name in ('workflow_assurance_ci.py','evaluate_convergent_review_prompt.py','linux_trial_sandbox.sh','isolated_trial_adapter.py','unshare')),'observation launched runner/evaluator/namespace')
        return process(argv,*args,**kwargs)
    def forbidden(*args,**kwargs):raise AssertionError('POLICY_ASSERTION: observer reexecuted historical A10/assessment')
    try:
        subprocess.Popen=observe_process
        for name in originals:setattr(api.platform,name,lambda n=name:'SYNTHETIC-local-observer-'+n)
        for name in historical:setattr(api,name,forbidden)
        require(captured['runtime']['version']!=api.platform.python_version(),'observer runtime discrimination is real')
        controls_call(api,f)
        print('PASS SYNTHETIC foreign-local-runtime observation; historical capture and verify Env unchanged')
    finally:
        subprocess.Popen=process
        for name,value in originals.items():setattr(api.platform,name,value)
        for name,value in historical.items():setattr(api,name,value)
    require(f.candidate['environment']==captured,'historical selected environment unchanged')
    controls_call(api,f)


def controls_prior(f,severity):
    """Actual convergence of an explicitly synthetic prior packet at selected base."""
    cr=load_api(ROOT/'tools/convergent_review.py');directory=ROOT/'tools/fixtures/convergent_review/02-consensus-blocker'
    packet=json.loads((directory/'packet.json').read_bytes());base=git(f.root,'rev-parse',f.source+'^')
    packet.update(repository=CONTROL_REPOSITORY,review_id='wa123-controls',head_sha=base,base_sha=git(f.root,'rev-parse',base+'^'))
    digest=sha(cr.canonical_json_bytes(packet));trials=[]
    for n in (1,2,3):
        trial=json.loads((directory/('trial-%d.json'%n)).read_bytes())
        trial.update(review_id='wa123-controls',head_sha=base,packet_digest=digest)
        for observation in trial['observations']:observation['finding']['severity']=severity
        trials.append(trial)
    return cr.converge_documents(packet,digest,trials,{n:sha(cr.canonical_json_bytes(trials[n-1])) for n in (1,2,3)},None,None,[])


def controls_variant(api,positive,defect):
    """Fresh graph: inject once before downstream commitments; restore chosen good graph."""
    with tempfile.TemporaryDirectory(prefix='nizam123-SYNTHETIC-variant-') as parent:
        bad=controls_construct(api,parent,defect,seed=positive)
        try:controls_call(api,bad,True)
        finally:
            if not getattr(bad, '_reused_exp', False):
                git(bad.root,'worktree','remove','--force',str(bad.exp))
    git(positive.root,'restore','--source='+positive.materialized_tip,'--staged','--worktree','--',CONTROL_PREFIX)
    positive.write('.agent/evidence/123/selection.json',positive.raw(positive.verify_selection))
    positive.commit_paths('SYNTHETIC restored original positive materialization', CONTROL_PREFIX, '.agent/evidence/123/selection.json')
    controls_call(api,positive)
    print('RESTORED '+defect['name'])


def controls_zip(raw,change):
    import io,zipfile
    with zipfile.ZipFile(io.BytesIO(raw)) as z:entries=[(info,z.read(info)) for info in z.infolist()]
    entries=change(entries); output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:
        for info,data in entries:z.writestr(info,data)
    return output.getvalue()


def controls_zip_size(raw,declared):
    """Change only the proof.bundle uncompressed-size declaration, not its bytes."""
    data=bytearray(raw)
    for signature,offset,name_offset in ((b'PK\x03\x04',22,30),(b'PK\x01\x02',24,46)):
        position=data.find(signature)
        require(position>=0,'synthetic ZIP header present')
        require(data[position+name_offset:position+name_offset+12]==b'proof.bundle','synthetic first entry is bundle')
        data[position+offset:position+offset+4]=declared.to_bytes(4,'little')
    return bytes(data)


def controls_zip_symlink(raw):
    def change(entries):
        entries[0][0].create_system=3;entries[0][0].external_attr=0o120777<<16
        return entries
    return controls_zip(raw,change)


def controls_intermediate_bundle(f,hidden=False,mode_only=False):
    """Actual Git objects: scope escape, or protected drift restored before tip."""
    tip=git(f.exp,'rev-parse','HEAD'); source_path='tools/workflow_assurance.py' if hidden or mode_only else 'SYNTHETIC-out-of-scope.txt'
    blob=subprocess.check_output(['git','-C',str(f.exp),'hash-object','-w','--stdin'],input=b'SYNTHETIC forbidden intermediate bytes\n').decode().strip()
    with tempfile.TemporaryDirectory(prefix='SYNTHETIC-index-',dir=f.parent) as name:
        env={**os.environ,'GIT_INDEX_FILE':str(Path(name)/'index')}
        def index(*args):return subprocess.check_output(['git','-C',str(f.exp),*args],env=env).decode().strip()
        mode='100644'
        if mode_only:
            original_mode,kind,blob=git(f.exp,'ls-tree',tip,'--',source_path).split()[:3]
            mode='100644' if original_mode=='100755' else '100755'
        index('read-tree',tip);index('update-index','--add','--cacheinfo',mode,blob,source_path)
        tree=index('write-tree'); bad=git(f.exp,'commit-tree',tree,'-p',tip,'-m','SYNTHETIC forbidden intermediate')
        if hidden:bad=git(f.exp,'commit-tree',git(f.exp,'rev-parse',tip+'^{tree}'),'-p',bad,'-m','SYNTHETIC restore protected tip')
        path=Path(name)/'bad.bundle';git(f.exp,'update-ref','refs/wa123/proof',bad)
        try:git(f.exp,'bundle','create','--version=2',str(path),'refs/wa123/proof','^'+f.source);raw=path.read_bytes()
        finally:git(f.exp,'update-ref','refs/wa123/proof',tip)
    return raw,dict(output_tip=bad,inventory=f.inventory(bad))


def controls_unknown_object(raw,f):
    """Valid Git pack carrying one actual unreferenced object beyond declared graph."""
    tip=git(f.exp,'rev-parse','HEAD')
    extra=subprocess.check_output(['git','-C',str(f.exp),'hash-object','-w','--stdin'],input=b'SYNTHETIC undeclared unreachable object\n').decode().strip()
    objects=git(f.exp,'rev-list','--objects','--no-object-names',f.source+'..'+tip).splitlines()
    packed=subprocess.check_output(['git','-C',str(f.exp),'pack-objects','--stdout'],input=('\n'.join(objects+[extra])+'\n').encode())
    return raw.split(b'\n\n',1)[0]+b'\n\n'+packed


def controls_observer(f):
    """Independently expected bounded rule; actual trusted observer executable."""
    cr=load_api(ROOT/'tools/convergent_review.py'); ev=load_api(ROOT/'tools/evaluate_convergent_review_prompt.py')
    with tempfile.TemporaryDirectory(prefix='SYNTHETIC123-observer-',dir=f.parent) as directory:
        directory=Path(directory); packet_path=directory/'packet.json'; prompt=directory/'prompt.md'; output=directory/'trial.json'
        def exercise(old,content,path,expected):
            packet=dict(schema_version=cr.SCHEMA_VERSION,repository=CONTROL_REPOSITORY,review_id='wa123-controls',
                mode='ordinary',base_sha=f.selection['packet_base'],head_sha=f.source,scope_commitment=None,
                delta=[dict(path=path,old_mode='100644',new_mode='100644',old_digest=sha(old.encode()),new_digest=sha(content.encode()),old_content=old)],
                review_files=[dict(path=path,content=content,content_digest=sha(content.encode()))])
            cr.validate_packet(packet); packet_path.write_bytes(cr.canonical_json_bytes(packet))
            prompt.write_text(ev.render_prompt(f.raw(f.selection['prompt_ref']).decode(),packet_path,1,output,None))
            if output.exists():output.unlink()
            argv=[sys.executable,str(ROOT/'tools/workflow_assurance_ci.py'),'--prompt',str(prompt),'--packet',str(packet_path),'--trial-number','1','--output',str(output)]
            process=subprocess.run(argv,cwd=directory,capture_output=True)
            require(process.returncode==0,'actual deterministic observer command0: '+process.stderr.decode(errors='replace'))
            trial=cr.parse_json_bytes(output.read_bytes(),'synthetic observer trial');cr.validate_trial(trial,packet,sha(packet_path.read_bytes()),'synthetic observer')
            require(len(trial['observations'])==len(expected),'substantive gate-disable observation count')
            evidence=[]
            for observation in trial['observations']:
                require(observation['action']=='active' and observation['finding']['severity']=='important' and observation['finding']['path']==path,
                    'gate-disable is active important finding at authenticated workflow path')
                evidence.extend(observation['evidence'])
            require(sorted((e['start_line'],e['end_line'],e['excerpt'],e['content_digest'],e['path']) for e in evidence)==
                sorted((n,n,content.splitlines()[n-1],sha(content.encode()),path) for n in expected),'exact authenticated offending line evidence')
        path='.github/workflows/compliance.yml'
        for value in ('true','"false"','FALSE','${{ success() }}','',"'false'"):
            content='jobs:\n  check:\n    continue-on-error: '+value+'\n'
            exercise('# base\n',content,path,[3]);exercise('# base\n','jobs:\n  check:\n    continue-on-error: false\n',path,[])
        exercise('# base\n','jobs:\n  a:\n    continue-on-error: true\n  b:\n    continue-on-error: \"false\"\n',path,[3,5])
        exercise('# base\n','jobs:\n  a:\n    continue-on-error: false\n  b:\n    continue-on-error: false\n',path,[])
        for content in ('# continue-on-error: true\n','continue-on-error: false # allowed literal false\n'):
            exercise('# base\n',content,path,[])
        exercise('continue-on-error: true\n# old\n','continue-on-error: true\n# changed only\n',path,[])
        exercise('# base\n','continue-on-error: true\n','tools/unrelated.yml',[])


def controls_defects(blockers=False):
    """Each entry names one producer site, expected cause and permitted audit exception."""
    def row(name,site,change,cause,**extra):return dict(name=name,site=site,change=change,cause=cause,**extra)
    if blockers:
        rows=[row('incoming-'+key,'report',lambda v,f,k=key:v[k].append({'SYNTHETIC':'blocking despite favorable label'}),
            r'AGF|report|blocking|verdict|approval|issues|coverage|unsupported',gate_rejection=True) for key in AGF_ARRAYS]
        rows += [row('carried-'+severity,'carried-ledger',lambda v,f,s=severity:controls_prior(f,s),
            r'AGF|ledger|blocking|verdict|approval|important|blocker',gate_rejection=True) for severity in ('blocker','important')]
        rows += [row('wrong-'+key,'verify/result.json',lambda v,f,k=key:v[k].update(action='noop' if k=='advance' else 'advance'),
            r'A10|transition|action|receipt') for key in ('advance','noop','republish','rerun_required')]
        rows += [row('unexercised-conflict','verify/result.json',lambda v,f:v.update(conflict_rejected=False),r'A10|conflict|receipt|result'),
            row('recovery-policy-removed','a10-policy',lambda v,f:v.update(recovery=None),r'A10|policy|recovery|receipt|transition'),
            row('failed-receipt','receipt-body',lambda v,f:v.update(status='failed'),r'A10|receipt|passed|status')]
        return rows
    rows=[]
    for site in ('capability.json','evaluation/prompt-evaluation.json','verify/capture.json','verify/result.json','capture-metadata','verify-metadata',
        'selection-capture','selection-verify','hosted-review','authority','shadow','a10-policy'):
        rows.append(row('unknown-'+site,site,lambda v,f:v.update(unknown=True),r'keys|closed|object|schema|fields|unexpected'))
    for site in ('capability.json','evaluation/prompt-evaluation.json','verify/capture.json'):
        rows.append(row('missing-version-'+site,site,lambda v,f:v.pop('schema_version'),r'keys|required|schema|version|field|object'))
    rows += [row('bool-version','capability.json',lambda v,f:v.update(schema_version=True),r'version|integer|type|capabil'),
        row('duplicate-key','capability.json',lambda v,f:canonical(v)[:-1]+b',"schema_version":1}\n',r'duplicate|canonical|JSON|json'),
        row('nonfinite-bytes','capability.json',lambda v,f:canonical(v).replace(b'"schema_version":1',b'"schema_version":NaN')+b'\n',r'finite|JSON|json|constant|canonical'),
        row('generic-boundary-label','boundary/stdout',lambda v,f:b'PASS\n',r'boundary|capabil|diagnostic|marker'),
        row('boundary-unsupported','capability.json',lambda v,f:v['boundary'].update(actual_exit=64),r'boundary|capabil|exit|process'),
        row('boundary-process-extra','capability.json',lambda v,f:v['boundary'].update(unknown=True),r'keys|closed|object|fields|process'),
        row('capability-runtime-drift','capability.json',lambda v,f:v['environment']['runtime'].update(version='SYNTHETIC-drift'),r'environment|runtime|capabil'),
        row('fourth-capture-producer','capture-producer',lambda v,f:v.update(session_id='123-ci-capture-attempt4'),r'producer|session|attempt|allocation'),
        row('bool-trial-exit','evaluation/prompt-evaluation.json',lambda v,f:v['trials'][0].update(runner_exit=True),r'trial|exit|integer|receipt|evaluation'),
        row('trial-adapter-substitution','evaluation/prompt-evaluation.json',lambda v,f:v['trials'][1].update(isolation_adapter_digest='0'*64),r'adapter|isolation|digest|trial'),
        row('replay-valid-missing-trials','evidence-body',lambda v,f:v.update(trial_provenance=[]),r'trial|provenance|three|length'),
        row('evidence-unknown','evidence-body',lambda v,f:v.update(unselected_policy={}),r'keys|closed|object|fields'),
        row('policy-unknown','policy',lambda v,f:v.update(unknown=True),r'keys|closed|object|fields|policy'),
        row('policy-bool-version','policy',lambda v,f:v.update(schema_version=True),r'version|integer|type|policy'),
        row('Root-selection-substitution','policy',lambda v,f:v.update(selection_ref=f.capture_selection),r'policy|selection|mode|verify|binding'),
        row('approval-metadata-missing','source-contract',lambda v,f:v.pop('approval_evidence'),r'approval|proposal|contract|prerequisite|metadata'),
        row('approval-proposal-stale','source-contract',lambda v,f:v['approval_evidence'].update(proposal_sha256='0'*64),r'approval|proposal|contract|prerequisite|metadata'),
        row('approval-gate-link-stale','source-contract',lambda v,f:v['approval_evidence'].update(mode_a=v['approval_evidence']['contract_review']),r'approval|proposal|contract|prerequisite|metadata')]
    for field,value in (('executed',False),('exit_code',True),('exit_code',7),('outcome','pending'),('outcome','running'),('outcome','failed'),('outcome','invalidated'),('outcome','setup-error')):
        rows.append(row('capture-'+field+'-'+str(value),'verify/capture.json',lambda v,f,k=field,x=value:v.update({k:x}),r'capture|exit|executed|outcome|success|command'))
    rows += [row('a10-capture-wrong-cwd','verify/capture.json',lambda v,f:v.update(cwd=str(f.exp)),r'capture|cwd|invocation|verify|fixed|input|binding'),
        row('a10-capture-preselection-revision','verify/capture.json',lambda v,f:v.update(revision=f.source),r'capture|revision|checkout|invocation|selection|fixed|input|binding')]
    rows.append(row('capture-forged-producer','verify/capture.json',lambda v,f:v['producer'].update(session_id='123-ci-verify-attempt2'),r'producer|session|capture'))
    for key in ('source_commit','source_tree'):
        rows.append(row('evidence-candidate-'+key,'evidence-body',lambda v,f,k=key:v['candidate'].update({k:'0'*40}),r'candidate|identity|source|tree|selection|binding'))
    rows += [row('evidence-checkout','evidence-body',lambda v,f:v['checkout'].update(sha='0'*40),r'checkout|source|binding'),
        row('evidence-environment','evidence-body',lambda v,f:v['candidate']['environment']['runtime'].update(version='SYNTHETIC-other'),r'candidate|environment|identity|selection|binding'),
        row('evidence-capture-attempt','evidence-body',lambda v,f:v['capture_host'].update(attempt=2),r'host|attempt|metadata|review|binding')]
    for number in range(3):
        for key in ('packet_ref','prompt_ref','output_ref','stdout_ref','stderr_ref','boundary_ref'):
            rows.append(row('trial%d-%s-digest'%(number+1,key),'evidence-body',
                lambda v,f,n=number,k=key:v['trial_provenance'][n][k].update(sha256='0'*64),r'trial|provenance|ref|artifact|digest|boundary|packet|prompt|output'))
        for key in ('packet_ref','prompt_ref','output_ref'):
            rows.append(row('trial%d-%s-valid-swap'%(number+1,key),'evidence-body',
                lambda v,f,n=number,k=key:v['trial_provenance'][n].update({k:copy.deepcopy(v['trial_provenance'][(n+1)%3][k])}),r'trial|provenance|packet|prompt|output|path|receipt|digest|binding'))
        for key,replacement in (('runner_ref','evaluator_ref'),('adapter_ref','runner_ref'),('evaluator_ref','adapter_ref')):
            rows.append(row('trial%d-%s-substitution'%(number+1,key),'evidence-body',
                lambda v,f,n=number,k=key,r=replacement:v['trial_provenance'][n].update({k:f.selection[r]}),r'trial|provenance|runner|adapter|evaluator|selected|binding'))
    for mode in ('capture','verify'):
        rows += [row(mode+'-fixed-selection-absent',mode+'-selection-present',lambda v,f:False,r'checkout|selection|CLI|fixed|input|blob|path|missing',frame_waiver=mode+'-fixed-input'),
            row(mode+'-fixed-selection-substituted',mode+'-fixed-selection-bytes',lambda v,f:canonical(dict(json.loads(v),producer=dict(agent_id='wa123-capable-ci',session_id='123-ci-'+json.loads(v)['mode']+'-attempt2')))+b'\n',r'checkout|selection|CLI|fixed|input|digest|binding',frame_waiver=mode+'-fixed-input'),
            row(mode+'-preselection-checkout',mode+'-checkout',lambda v,f:v.update(sha=f.source),r'checkout|selection|CLI|fixed|input|tree|parent|path',frame_waiver=mode+'-checkout'),
            row(mode+'-wrong-checkout-tree',mode+'-checkout',lambda v,f:v.update(tree='0'*40),r'checkout|tree|object|binding',frame_waiver=mode+'-checkout')]
        rows += [row(mode+'-raw-run-missing',mode+'-run',lambda v,f:v.pop('conclusion'),r'run|required|field|missing|conclusion|metadata'),
            row(mode+'-raw-run-wrong-id',mode+'-run',lambda v,f:v.update(id=v['id']+500),r'run|id|binding|metadata'),
            row(mode+'-raw-head-mismatch',mode+'-run',lambda v,f:v.update(head_sha='0'*40),r'head|source|checkout|metadata|binding'),
            row(mode+'-raw-run-bool',mode+'-run',lambda v,f:v.update(id=True),r'run|integer|metadata|type'),
            row(mode+'-raw-run-unfinished',mode+'-run',lambda v,f:v.update(status='in_progress'),r'run|completed|status|metadata'),
            row(mode+'-missing-job-page',mode+'-jobs',lambda v,f:v.update(total_count=4),r'jobs|count|page|five|metadata'),
            row(mode+'-failed-active-step',mode+'-jobs',lambda v,f:v['jobs'][3]['steps'][0].update(conclusion='failure'),r'step|job|success|conclusion|metadata'),
            row(mode+'-expired-artifact',mode+'-artifacts',lambda v,f:v['artifacts'][0].update(expired=True),r'artifact|expired|metadata'),
            row(mode+'-fetch-nonzero',mode+'-fetch-run',lambda v,f:v.update(actual_exit=7),r'fetch|exit|command|metadata'),
            row(mode+'-fetch-bool-exit',mode+'-fetch-run',lambda v,f:v.update(actual_exit=True),r'fetch|exit|integer|type|metadata')]
    for kind in ('mode-a','contract-review','approved-contract','provisional-bundle'):
        rows.append(row('missing-gate-'+kind,'selection-capture',lambda v,f,k=kind:v.update(prerequisites=[e for e in v['prerequisites'] if e['kind']!=k]),r'prerequisite|approval|gate|contract|selection|binding'))
    rows += [row('hosted-review-not-approved','hosted-review',lambda v,f:v['final_verdict'].update(approved=False),r'review|verdict|approved|gate'),
        row('hosted-review-blocking','hosted-review',lambda v,f:v['issues'].append({'SYNTHETIC':'blocked'}),r'review|issues|gate|blocking|verdict'),
        row('missing-log-marker','verify-job-log',lambda v,f:v.replace(b'WA123_INVOCATION=',b'UNSELECTED='),r'log|marker|invocation',waiver='log-marker'),
        row('duplicate-log-marker','verify-job-log',lambda v,f:v+v,r'log|marker|invocation',waiver='log-marker'),
        row('substituted-log-marker','verify-job-log',lambda v,f:v.replace(b'\"actual_exit\":0',b'\"actual_exit\":7'),r'log|marker|invocation|exit',waiver='log-marker'),
        row('archive-declared-size','verify-artifacts',lambda v,f:v['artifacts'][0].update(size_in_bytes=v['artifacts'][0]['size_in_bytes']+1),r'artifact|archive|size|length',waiver='archive-size'),
        row('archive-hash','verify-host',lambda v,f:v.update(artifact_sha256='0'*64),r'archive|artifact|hash|digest',waiver='archive-hash'),
        row('invocation-extra','verify-invocation-body',lambda v,f:v.update(unknown=True),r'keys|closed|object|fields|invocation'),
        row('manifest-extra','verify-manifest',lambda v,f:v.update(unknown=True),r'keys|closed|object|fields|manifest'),
        row('inventory-duplicate','verify-manifest',lambda v,f:v['inventory'].append(copy.deepcopy(v['inventory'][0])),r'inventory|duplicate|artifact')]
    for name,change in (('v3',lambda b,f:b.replace(b'# v2 git bundle',b'# v3 git bundle',1)),('truncated',lambda b,f:b[:-1]),
        ('trailing',lambda b,f:b+b'trailing junk'),('foreign-base',lambda b,f:b.replace(('-'+f.source).encode(),('-'+'0'*40).encode(),1)),
        ('extra-ref',lambda b,f:b.replace(b' refs/wa123/proof\n',b' refs/wa123/proof\n'+f.source.encode()+b' refs/extra\n',1))):
        rows.append(row('bundle-'+name,'verify-bundle-bytes',change,r'bundle|pack|prerequisite|base|header|trailing|ref'))
    rows += [row('out-of-scope-pack','verify-bundle-bytes',lambda b,f:controls_intermediate_bundle(f,False),r'scope|prefix|path|protected|inventory|add.only'),
        row('restored-tip-hides-source-edit','verify-bundle-bytes',lambda b,f:controls_intermediate_bundle(f,True),r'scope|prefix|path|protected|intermediate|add.only'),
        row('protected-mode-in-pack','verify-bundle-bytes',lambda b,f:controls_intermediate_bundle(f,mode_only=True),r'scope|prefix|path|protected|mode|add.only'),
        row('unreferenced-pack-object','verify-bundle-bytes',controls_unknown_object,r'pack|object|inventory|unreach|undeclared')]
    zip_changes=[('duplicate',lambda entries:entries+entries[:1]),('extra',lambda entries:entries+[('extra.txt',b'extra')]),
        ('traversal',lambda entries:[('../escape',entries[0][1])]+entries[1:]),
        ('manifest-mismatch',lambda entries:[entries[0],(entries[1][0],canonical(dict(json.loads(entries[1][1]),bundle_sha256='0'*64))+b'\n'),entries[2]])]
    for name,change in zip_changes:
        rows.append(row('zip-'+name,'verify-archive-bytes',lambda raw,f,c=change:controls_zip(raw,c),r'ZIP|zip|entry|archive|duplicate|path|travers|manifest|hash|digest',waiver='archive-structure'))
    rows += [row('zip-symlink','verify-archive-bytes',lambda raw,f:controls_zip_symlink(raw),r'ZIP|zip|entry|regular|symlink|mode',waiver='archive-structure'),
        row('zip-entry-bound','verify-archive-bytes',lambda raw,f:controls_zip_size(raw,21*1024*1024),r'size|bound|limit|large|exceed',waiver='archive-structure'),
        row('zip-archive-bound','verify-archive-bytes',lambda raw,f:b'0'*(32*1024*1024+1)+raw,r'size|bound|limit|large|exceed',waiver='archive-structure')]
    # Claimed commitment loops are deliberately invalid immutable Refs, not hash fixed points.
    for name,change in (('future',lambda r,f:r.update(revision=f.nodes['selection-verify']['revision'])),('dangling',lambda r,f:r.update(revision='0'*40)),
        ('self',lambda r,f:r.update(path='.agent/evidence/123/synthetic-root/%s/%04d-evidence'%(f.namespace,f.serial+1),revision=git(f.root,'rev-parse','HEAD'),sha256='0'*64)),
        ('loop',lambda r,f:r.update(path='.agent/evidence/123/synthetic-root/%s/%04d-hosted-review'%(f.namespace,f.serial+2),revision=git(f.root,'rev-parse','HEAD'),sha256='0'*64))):
        rows.append(row('claimed-ref-'+name,'evidence-body',lambda v,f,c=change:c(v['trial_provenance'][0]['evaluation_receipt_ref'],f),r'ref|artifact|commit|digest|path|order|evaluation|trial'))
    return rows


def controls_candidate(api,f):
    controls_call(api,f)
    controls_foreign_observer(api,f)
    for defect in sorted(controls_defects(),key=lambda row:row['name']!='replay-valid-missing-trials'):controls_variant(api,f,defect)
    saved=copy.deepcopy(f.policy)
    for label,value in (('nonfinite',float('nan')),('cycle',None)):
        f.defect=dict(name='policy-'+label,site='in-memory-JSON',cause=r'finite|cycle|JSON|json|serializ')
        try:
            f.policy['unknown']=value
            if label=='cycle':f.policy['unknown']=f.policy
            controls_call(api,f,True)
        finally:f.policy=copy.deepcopy(saved);f.defect=None
        controls_call(api,f)
    protected=[f.candidate['assessed_inputs'][key][0]['path'] for key in ('source','tests','tools','contracts')]
    protected+=['.github/workflows/compliance.yml','schema/contract.schema.json','tools/workflow_assurance_ci.py','tools/verify_lib.sh']
    for path in dict.fromkeys(protected):
        target=f.root/path;data=target.read_bytes();mode=target.stat().st_mode
        f.defect=dict(name='current-protected-'+path,site='materialized-current-input',cause=r'input|source|current|mode|contract|digest|protected')
        try:
            target.write_bytes(data+b'\n# SYNTHETIC protected drift\n');controls_call(api,f,True)
            target.write_bytes(data);target.chmod(mode^0o111);controls_call(api,f,True)
        finally:target.write_bytes(data);target.chmod(mode);f.defect=None
        controls_call(api,f)
    target=f.root/f.candidate['assessed_inputs']['source'][0]['path'];raw=target.read_bytes();mode=target.stat().st_mode;alias=f.parent/'SYNTHETIC-hardlink'
    f.defect=dict(name='current-protected-input-hardlink',site='materialized-current-input',cause=r'link|regular|artifact|file|input')
    try:
        os.link(target,alias);require(target.stat().st_nlink==2,'actual selected artifact hardlink control')
        controls_call(api,f,True)
    finally:
        if alias.exists():alias.unlink()
        require(target.read_bytes()==raw and target.stat().st_mode==mode and target.stat().st_nlink==1,'selected artifact bytes/full modes/link count restore')
        f.defect=None
    controls_call(api,f)
    controls_observer(f)


def controls_blockers(api,f):
    controls_call(api,f)
    for defect in controls_defects(True):controls_variant(api,f,defect)


def controls_construct(api,parent,defect=None,seed=None):
    try:return ControlsFixture(api,parent,defect,seed)
    except Exception as exc:
        print('SETUP_ERROR: synthetic graph constructor '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        raise SystemExit(2) from exc


def run_controls_case(name,api):
    if not callable(getattr(api,'verify_controls_ready',None)):
        print('SETUP_ERROR: missing verify_controls_ready; never intended semantic red',file=sys.stderr);raise SystemExit(2)
    with tempfile.TemporaryDirectory(prefix='nizam123-SYNTHETIC-parser-') as parent:
        f=controls_construct(api,parent)
        (controls_candidate if name=='ci-candidate-bound' else controls_blockers)(api,f)


def run_controls_ready(api):
    """Observe only completed independently selected hosted proof; never execute it."""
    if not callable(getattr(api,'verify_controls_ready',None)):
        print('SETUP_ERROR: missing verify_controls_ready; never intended semantic red',file=sys.stderr);raise SystemExit(2)
    policy_path=ROOT/'tools/fixtures/workflow_assurance/wa123_controls_policy.json'
    policy=api.parse_json(api.regular_file(ROOT,str(policy_path.relative_to(ROOT))).read_bytes())
    reference=policy['evidence_ref']
    evidence=api.parse_json(api._receipt_artifact(ROOT,reference))
    before=copy.deepcopy((policy,evidence)); status=git(ROOT,'status','--porcelain','--untracked-files=all')
    with tempfile.TemporaryDirectory(prefix='nizam123-actual-observation-') as parent:
        scratch=Path(parent)/'repo'; bundle=Path(parent)/'selected.bundle'
        subprocess.check_call(['git','clone','--quiet','--shared','--no-checkout',str(ROOT),str(scratch)])
        git(scratch,'remote','set-url','origin',git(ROOT,'remote','get-url','origin'))
        git(scratch,'checkout','--quiet','--detach',evidence['candidate']['source_commit'])
        payload=api._receipt_artifact(ROOT,evidence['pack_ref']);bundle.write_bytes(payload)
        require(payload.startswith(b'# v2 git bundle\n') and b'\n\n' in payload,'selected bundle v2 preparation')
        pack=payload.split(b'\n\n',1)[1]
        imported=subprocess.run(['git','-C',str(scratch),'index-pack','--strict','--fix-thin','--stdin'],input=pack,capture_output=True)
        require(imported.returncode==0,'selected pack imports into owned observation scratch')
        git(scratch,'bundle','verify',str(bundle))
        git(scratch,'fetch','--no-tags','--no-write-fetch-head',str(bundle),'refs/wa123/proof:refs/wa123/import-verify')
        result=api.verify_controls_ready(scratch,evidence,policy=policy)
        negative=copy.deepcopy(evidence);negative['trial_provenance']=[]
        synthetic_policy=copy.deepcopy(policy)
        synthetic_review=api.parse_json(api._receipt_artifact(scratch,policy['hosted_review_ref']))
        git(scratch,'config','user.name','SYNTHETIC123 private observation control')
        git(scratch,'config','user.email','synthetic123@example.invalid')
        git(scratch,'config','gc.auto','0');git(scratch,'config','maintenance.auto','false')
        def commit_control(label,value):
            path='.agent/evidence/123/synthetic-observation-'+label+'.json';raw=canonical(value)+b'\n'
            target=scratch/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            git(scratch,'add','--',path);git(scratch,'commit','--quiet','-m','SYNTHETIC observation control '+label)
            return dict(path=path,revision=git(scratch,'rev-parse','HEAD'),sha256=sha(raw))
        synthetic_policy['evidence_ref']=commit_control('missing-trials',negative)
        synthetic_review['evidence_ref']=synthetic_policy['evidence_ref']
        synthetic_policy['hosted_review_ref']=commit_control('review-ref-binding',synthetic_review)
        try:api.verify_controls_ready(scratch,negative,policy=synthetic_policy)
        except api.AssuranceError as exc:
            require(re.search(r'trial|provenance|three|length',str(exc),re.I) is not None,'readiness missing-trial cause: '+str(exc))
            print('EXPECTED_REJECTION SYNTHETIC selected missing-trial observation: '+str(exc))
        else:require(False,'synthetic invalid controls proof accepted: readiness missing trials')
        require(api.verify_controls_ready(scratch,evidence,policy=policy)==result,'actual selected hosted proof restores after synthetic discrimination')
    require((policy,evidence)==before and git(ROOT,'status','--porcelain','--untracked-files=all')==status,'actual hosted observation inputs and real checkout unchanged')
    require(result==dict(schema_version=1,feature_id='123',source_commit=evidence['candidate']['source_commit'],checkout_sha=evidence['checkout']['sha'],
        candidate_sha256=sha(canonical(evidence['candidate'])),capture_run_id=evidence['capture_host']['run_id'],verify_run_id=evidence['verify_host']['run_id'],
        a11_verdict='approve',a10_receipt_sha256=evidence['a10_receipt_ref']['sha256'],transition_actions=['advance','noop','republish','rerun-required'],
        hosted_review_sha256=policy['hosted_review_ref']['sha256']),'exact actual selected hosted observation result')
    print('PASS controls-ready observed independently selected actual hosted proof')


PROFILE_CASES = (
    'preregister-before-run',
    'roles-reused',
    'reject-unstable-baseline',
    'same-candidate',
    'missed-baseline-blocker',
    'cost-latency-accounting',
    'no-self-promotion',
)


class ProfileFixture(FailureFixture):
    """Synthetic Phase 019 (124/125) profile preregistration and shadow comparison fixture."""

    def __init__(self, api, parent):
        super().__init__(api, parent)
        self.candidate_digest = sha(canonical(self.candidate))
        self.source_commit = self.candidate['source_commit']
        self.source_tree = self.candidate['source_tree']
        self.profile_authority = dict(
            schema_version=1,
            role='Root',
            repository=self.repository,
            owner='cnr',
            gate='H-PHASE-019',
            approved=True,
            allow_self_promotion=False,
            allow_gate_reduction=False,
        )
        self.profile_authority_ref = self.pin_new('profile-authority', self.profile_authority)
        self.baseline_controls = dict(
            schema_version=1,
            feature_id='123',
            source_commit=self.source_commit,
            candidate_sha256=self.candidate_digest,
            a11_verdict='approve',
            status='stable',
            flaky_runs=0,
            unresolved_blockers=0,
        )
        self.baseline_controls_ref = self.pin_new('baseline-controls', self.baseline_controls)
        self.test_bundle = dict(
            schema_version=1,
            bundle_id='wa019-bundle',
            source_commit=self.source_commit,
            cases=list(PROFILE_CASES),
        )
        self.test_bundle_ref = self.pin_new('test-bundle', self.test_bundle)
        self.preregistration = dict(
            schema_version=1,
            preregistration_id='wa124-generic-profiles',
            repository=self.repository,
            feature_id='124',
            execution_scope='repository-worktree',
            state='preregistered-before-shadow',
            shadow_runs_started=False,
            shadow_run_refs=[],
            candidate=copy.deepcopy(self.candidate),
            test_bundle_ref=copy.deepcopy(self.test_bundle_ref),
            role_bindings=dict(
                Orchestrator='orchestrator-primary',
                Planner='planner-creative',
                Generator='generator-deterministic',
                Validator='validator-structural',
                Evaluator='evaluator-adversarial',
            ),
            tiers={
                'Routine': dict(
                    applicability='Unambiguous trivial and small-change worktree edits with recorded verification.',
                    route_classes=['trivial', 'small-change'],
                    required_roles=['Generator', 'Evaluator'],
                    same_candidate_baseline=True,
                    persistent_runtime_claim=False,
                    max_duration_ms=60000,
                    max_cost_units=100,
                    max_blocker_mismatch=0,
                ),
                'Standard': dict(
                    applicability='Scoped bug fixes and standard single-module features with independent acceptance.',
                    route_classes=['bugfix', 'standard-feature'],
                    required_roles=['Planner', 'Generator', 'Validator', 'Evaluator'],
                    same_candidate_baseline=True,
                    persistent_runtime_claim=False,
                    max_duration_ms=180000,
                    max_cost_units=300,
                    max_blocker_mismatch=0,
                ),
                'High-assurance': dict(
                    applicability='Security, isolation, authority, schema, and cross-module high-risk changes.',
                    route_classes=['high-risk'],
                    required_roles=['Orchestrator', 'Planner', 'Generator', 'Validator', 'Evaluator'],
                    same_candidate_baseline=True,
                    persistent_runtime_claim=False,
                    max_duration_ms=600000,
                    max_cost_units=1000,
                    max_blocker_mismatch=0,
                ),
            },
            thresholds=dict(
                max_missed_baseline_blockers=0,
                max_unexplained_divergences=0,
                max_duration_ms=600000,
                max_cost_units=1000,
                min_comparison_runs=3,
            ),
            operator_decision_policy=dict(
                accountable_role='Root',
                gate='H-PHASE-019',
                self_promotion_allowed=False,
                automatic_gate_reduction_allowed=False,
                authority_ref=copy.deepcopy(self.profile_authority_ref),
            ),
        )
        self.prereg_policy = dict(
            schema_version=1,
            repository=self.repository,
            feature_id='124',
            stage='profile-preregistration',
            baseline_controls_ref=copy.deepcopy(self.baseline_controls_ref),
            authority_ref=copy.deepcopy(self.profile_authority_ref),
            persistent_runtime_ready=False,
        )
        self.sync_preregistration()

    def sync_preregistration(self):
        self.preregistration_ref = self.pin_new('preregistration', self.preregistration)
        self.prereg_policy_ref = self.pin_new('prereg-policy', self.prereg_policy)
        self.comparison_policy = dict(
            schema_version=1,
            repository=self.repository,
            feature_id='125',
            stage='shadow-comparison',
            preregistration_ref=copy.deepcopy(self.preregistration_ref),
            preregistration_policy_ref=copy.deepcopy(self.prereg_policy_ref),
            authority_ref=copy.deepcopy(self.profile_authority_ref),
        )
        self.baseline_run = self.make_run('baseline-125', 'success', 0, [], [], 12000, 80, 6)
        self.shadow_run = self.make_run('shadow-125', 'success', 0, [], ['ADV-001'], 4500, 35, 3)
        self.comparison = dict(
            schema_version=1,
            comparison_id='wa125-routine-comparison',
            repository=self.repository,
            feature_id='125',
            preregistration_ref=copy.deepcopy(self.preregistration_ref),
            profile_tier='Routine',
            route_class='small-change',
            candidate=copy.deepcopy(self.candidate),
            baseline_run=copy.deepcopy(self.baseline_run),
            shadow_run=copy.deepcopy(self.shadow_run),
            operator_decision=dict(
                role='Root',
                owner='cnr',
                gate='H-PHASE-019',
                decision='approve-recommendation-only',
                self_promote=False,
                reduce_active_gates=False,
                authority_ref=copy.deepcopy(self.profile_authority_ref),
            ),
            requested_action='recommend-only',
        )

    def make_run(self, run_id, outcome, exit_code, blocker_ids, advisory_ids, duration_ms, cost_units, command_count):
        self.serial += 1
        out_path = f'proof/profile-{self.serial}-{run_id}.stdout'
        err_path = f'proof/profile-{self.serial}-{run_id}.stderr'
        self.write(out_path, f'PROFILE_RUN {run_id} {outcome}\n'.encode('utf-8'))
        self.write(err_path, b'')
        rev = self.commit(f'profile run output {run_id}')
        stdout_ref = self.ref(out_path, rev)
        stderr_ref = self.ref(err_path, rev)
        cap = dict(
            schema_version=1,
            run_id=run_id,
            candidate_sha256=self.candidate_digest,
            revision=rev,
            executed=True,
            outcome=outcome,
            exit_code=exit_code,
            duration_ms=duration_ms,
            cost_units=cost_units,
            command_count=command_count,
            stdout=stdout_ref,
            stderr=stderr_ref,
        )
        cap_ref = self.pin_new(f'cap-{run_id}', cap)
        approved = (outcome == 'success' and not blocker_ids)
        verdict = dict(
            final_verdict=dict(approved=approved),
            issues=[dict(id=b, description='blocking finding ' + b) for b in blocker_ids],
            missing_acceptance_coverage=[],
            unsupported_claims=[],
        )
        return dict(
            run_id=run_id,
            candidate_sha256=self.candidate_digest,
            source_commit=self.source_commit,
            source_tree=self.source_tree,
            test_bundle_sha256=self.test_bundle_ref['sha256'],
            executed=True,
            outcome=outcome,
            exit_code=exit_code,
            verdict=verdict,
            blocker_ids=list(blocker_ids),
            advisory_ids=list(advisory_ids),
            duration_ms=duration_ms,
            cost_units=cost_units,
            command_count=command_count,
            capture_ref=cap_ref,
        )


def profile_preregister_call(api, f, deny=False):
    before = repr((f.preregistration, f.prereg_policy))
    files = f.files()
    try:
        out = api.preregister_profile_comparison(f.root, f.preregistration, policy=f.prereg_policy)
    except api.AssuranceError as exc:
        require(deny and 0 < len(str(exc)) <= 1000, 'preregistration rejection is bounded AssuranceError')
        out = None
    else:
        require(not deny, 'invalid preregistration input accepted')
        require(
            out
            == dict(
                schema_version=1,
                feature_id='124',
                preregistration_id=f.preregistration['preregistration_id'],
                repository=f.repository,
                execution_scope=f.preregistration['execution_scope'],
                candidate_sha256=f.candidate_digest,
                source_commit=f.source_commit,
                baseline_controls_sha256=f.prereg_policy['baseline_controls_ref']['sha256'],
                test_bundle_sha256=f.preregistration['test_bundle_ref']['sha256'],
                tiers=['Routine', 'Standard', 'High-assurance'],
                roles_reused=True,
                before_shadow_run=True,
                baseline_stable=True,
                self_promotion_allowed=False,
                automatic_gate_reduction_allowed=False,
            ),
            'exact preregistration output',
        )
        require(not receipt_ids(out) & receipt_ids([f.preregistration, f.prereg_policy]), 'preregistration deep copy')
    require(repr((f.preregistration, f.prereg_policy)) == before and f.files() == files, 'preregistration preserves inputs and files')
    return out


def profile_evaluate_call(api, f, deny=False):
    before = repr((f.comparison, f.comparison_policy))
    files = f.files()
    try:
        out = api.evaluate_profile_comparison(f.root, f.comparison, policy=f.comparison_policy)
    except api.AssuranceError as exc:
        require(deny and 0 < len(str(exc)) <= 1000, 'comparison rejection is bounded AssuranceError')
        out = None
    else:
        require(not deny, 'invalid comparison input accepted')
        require(
            out['promoted'] is False
            and out['active_gates_reduced'] is False
            and out['permissions_changed'] is False
            and out['same_candidate'] is True,
            'comparison invariants hold',
        )
        require(not receipt_ids(out) & receipt_ids([f.comparison, f.comparison_policy]), 'comparison deep copy')
    require(repr((f.comparison, f.comparison_policy)) == before and f.files() == files, 'comparison preserves inputs and files')
    return out


def profile_preregister_before_run(api, f):
    profile_preregister_call(api, f)
    saved = copy.deepcopy((f.preregistration, f.prereg_policy))
    for field, values in {
        'state': ['running', 'completed', 'after-shadow-run', '', None],
        'shadow_runs_started': [True, 1, 'false', None],
        'shadow_run_refs': [['shadow-1'], [{}], None, 'none'],
        'execution_scope': ['persistent-runtime-sbcl', 'unknown-scope', ''],
        'feature_id': ['125', '123', ''],
        'repository': ['foreign/repo'],
        'schema_version': [True, 2, '1'],
    }.items():
        for val in values:
            f.preregistration, f.prereg_policy = copy.deepcopy(saved)
            f.preregistration[field] = val
            profile_preregister_call(api, f, True)
    # Persistent-runtime SBCL scope succeeds only when persistent_runtime_ready=True (130-132 qualified)
    f.preregistration, f.prereg_policy = copy.deepcopy(saved)
    f.preregistration['execution_scope'] = 'persistent-runtime-sbcl'
    f.preregistration['tiers']['High-assurance']['persistent_runtime_claim'] = True
    f.prereg_policy['persistent_runtime_ready'] = True
    profile_preregister_call(api, f)
    # Claiming persistent_runtime_claim=True under repository-worktree scope must fail
    f.preregistration, f.prereg_policy = copy.deepcopy(saved)
    f.preregistration['tiers']['Routine']['persistent_runtime_claim'] = True
    profile_preregister_call(api, f, True)
    # Causal commit ordering: committing a shadow run before pinning preregistration must fail
    head_before = git(f.root, 'rev-parse', 'HEAD')
    serial_before = f.serial
    saved_comp = copy.deepcopy((f.comparison, f.comparison_policy))
    try:
        early_shadow = f.make_run('shadow-early-before-prereg', 'success', 0, [], [], 3000, 20, 2)
        late_prereg_ref = f.pin_new('preregistration-after-shadow', f.preregistration)
        profile_preregister_call(api, f, True)
        f.comparison['preregistration_ref'] = copy.deepcopy(late_prereg_ref)
        f.comparison_policy['preregistration_ref'] = copy.deepcopy(late_prereg_ref)
        f.comparison['shadow_run'] = copy.deepcopy(early_shadow)
        profile_evaluate_call(api, f, True)
    finally:
        git(f.root, 'reset', '--hard', '--quiet', head_before)
        f.serial = serial_before
        f.comparison, f.comparison_policy = saved_comp
    f.preregistration, f.prereg_policy = saved
    profile_preregister_call(api, f)


def profile_roles_reused(api, f):
    profile_preregister_call(api, f)
    saved = copy.deepcopy((f.preregistration, f.prereg_policy))
    for bad_roles in (
        dict(f.preregistration['role_bindings'], SuperAgent='super-profile'),
        {k: v for k, v in f.preregistration['role_bindings'].items() if k != 'Evaluator'},
        dict(f.preregistration['role_bindings'], Generator='orchestrator-primary'),
        dict(f.preregistration['role_bindings'], Evaluator='evaluator-v2-custom'),
    ):
        f.preregistration = copy.deepcopy(saved[0])
        f.preregistration['role_bindings'] = bad_roles
        profile_preregister_call(api, f, True)
    for tier in ('Routine', 'Standard', 'High-assurance'):
        for bad_req in (
            ['Generator'],
            ['Evaluator'],
            ['Generator', 'Evaluator', 'Evaluator'],
            ['Generator', 'Evaluator', 'InventedRole'],
        ):
            f.preregistration = copy.deepcopy(saved[0])
            f.preregistration['tiers'][tier]['required_roles'] = bad_req
            profile_preregister_call(api, f, True)
        f.preregistration = copy.deepcopy(saved[0])
        f.preregistration['tiers'][tier]['route_classes'] = ['high-risk', 'trivial']
        profile_preregister_call(api, f, True)
    f.preregistration, f.prereg_policy = saved
    profile_preregister_call(api, f)


def profile_reject_unstable_baseline(api, f):
    profile_preregister_call(api, f)
    saved = copy.deepcopy((f.preregistration, f.prereg_policy, f.baseline_controls))
    for field, values in {
        'status': ['unstable', 'flaky', 'pending', 'failed', ''],
        'a11_verdict': ['reject', 'pending', ''],
        'flaky_runs': [1, 2, -1, True],
        'unresolved_blockers': [1, 3, -1, True],
        'source_commit': ['0' * 40],
        'candidate_sha256': ['f' * 64],
        'feature_id': ['122'],
    }.items():
        for val in values:
            f.preregistration, f.prereg_policy, f.baseline_controls = copy.deepcopy(saved)
            f.baseline_controls[field] = val
            f.prereg_policy['baseline_controls_ref'] = f.pin_new('bad-baseline', f.baseline_controls)
            profile_preregister_call(api, f, True)
    for tier in ('Routine', 'Standard', 'High-assurance'):
        f.preregistration, f.prereg_policy, f.baseline_controls = copy.deepcopy(saved)
        f.preregistration['tiers'][tier]['max_blocker_mismatch'] = 1
        profile_preregister_call(api, f, True)
    for field in ('max_missed_baseline_blockers', 'max_unexplained_divergences'):
        f.preregistration, f.prereg_policy, f.baseline_controls = copy.deepcopy(saved)
        f.preregistration['thresholds'][field] = 1
        profile_preregister_call(api, f, True)
    f.preregistration, f.prereg_policy, f.baseline_controls = saved
    profile_preregister_call(api, f)


def profile_same_candidate(api, f):
    out = profile_evaluate_call(api, f)
    require(out['recommendation'] == 'recommend-for-operator-review', 'clean Routine comparison recommends review')
    saved = copy.deepcopy((f.comparison, f.comparison_policy))
    for tier, route in (('Standard', 'bugfix'), ('High-assurance', 'high-risk')):
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['profile_tier'] = tier
        f.comparison['route_class'] = route
        res = profile_evaluate_call(api, f)
        require(res['profile_tier'] == tier and res['route_class'] == route and res['same_candidate'] is True, 'tier evaluation')
    # Failed outcome on BOTH baseline and shadow for the same blocker on the same candidate is recorded and eligible
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['baseline_run'] = f.make_run('base-fail-same', 'failed', 1, ['BLK-SAME'], [], 10000, 70, 5)
    f.comparison['shadow_run'] = f.make_run('shad-fail-same', 'failed', 1, ['BLK-SAME'], [], 4000, 30, 3)
    res = profile_evaluate_call(api, f)
    require(
        res['baseline_outcome'] == 'failed'
        and res['shadow_outcome'] == 'failed'
        and res['missed_baseline_blockers'] == []
        and res['recommendation'] == 'recommend-for-operator-review',
        'failed outcome captured on both baseline and shadow with matching blocker',
    )
    # Candidate and run mismatches must be rejected
    for run_key in ('baseline_run', 'shadow_run'):
        for field, val in (
            ('candidate_sha256', '0' * 64),
            ('source_commit', '0' * 40),
            ('source_tree', '0' * 40),
            ('test_bundle_sha256', '0' * 64),
            ('executed', False),
            ('outcome', 'pending'),
        ):
            f.comparison = copy.deepcopy(saved[0])
            f.comparison[run_key][field] = val
            profile_evaluate_call(api, f, True)
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['shadow_run']['run_id'] = f.comparison['baseline_run']['run_id']
    profile_evaluate_call(api, f, True)
    # Reusing the identical capture_ref on baseline and shadow must be rejected
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['shadow_run']['capture_ref'] = copy.deepcopy(f.comparison['baseline_run']['capture_ref'])
    profile_evaluate_call(api, f, True)
    # Profile tier, executed_roles, and argv bindings must discriminate reduced tiers from baseline
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['baseline_run']['profile_tier'] = 'Baseline'
    f.comparison['baseline_run']['executed_roles'] = ['Orchestrator', 'Planner', 'Generator', 'Validator', 'Evaluator']
    f.comparison['baseline_run']['argv'] = ['python3', 'tools/start_path.py', '--tier', 'Baseline']
    f.comparison['shadow_run']['profile_tier'] = 'Routine'
    f.comparison['shadow_run']['executed_roles'] = ['Generator', 'Evaluator']
    f.comparison['shadow_run']['argv'] = ['python3', 'tools/start_path.py', '--tier', 'Routine']
    profile_evaluate_call(api, f)
    # Identical argv on Routine tier must be rejected
    f.comparison['shadow_run']['argv'] = ['python3', 'tools/start_path.py', '--tier', 'Baseline']
    profile_evaluate_call(api, f, True)
    # Wrong executed_roles on Routine tier must be rejected
    f.comparison['shadow_run']['argv'] = ['python3', 'tools/start_path.py', '--tier', 'Routine']
    f.comparison['shadow_run']['executed_roles'] = ['Orchestrator', 'Planner', 'Generator', 'Validator', 'Evaluator']
    profile_evaluate_call(api, f, True)
    # Wrong profile_tier on shadow_run must be rejected
    f.comparison['shadow_run']['executed_roles'] = ['Generator', 'Evaluator']
    f.comparison['shadow_run']['profile_tier'] = 'Standard'
    profile_evaluate_call(api, f, True)
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['candidate']['source_tree'] = 'f' * 40
    profile_evaluate_call(api, f, True)
    f.comparison, f.comparison_policy = saved
    profile_evaluate_call(api, f)


def profile_missed_baseline_blocker(api, f):
    saved = copy.deepcopy((f.comparison, f.comparison_policy))
    # Baseline finds BLK-CRIT-1; shadow misses it
    f.comparison['baseline_run'] = f.make_run('base-blk', 'failed', 1, ['BLK-CRIT-1'], [], 12000, 80, 6)
    f.comparison['shadow_run'] = f.make_run('shad-miss', 'success', 0, [], [], 4000, 30, 3)
    # Attempting to approve recommendation when a baseline blocker was missed MUST fail
    f.comparison['operator_decision']['decision'] = 'approve-recommendation-only'
    profile_evaluate_call(api, f, True)
    # Recording the comparison with reject-recommendation succeeds and reports missed_baseline_blockers + reject-promotion
    f.comparison['operator_decision']['decision'] = 'reject-recommendation'
    res = profile_evaluate_call(api, f)
    require(
        res['missed_baseline_blockers'] == ['BLK-CRIT-1']
        and res['recommendation'] == 'reject-promotion'
        and res['promoted'] is False,
        'missed baseline blocker rejects promotion recommendation',
    )
    # Unexplained extra blocker in shadow also rejects approve-recommendation-only
    f.comparison = copy.deepcopy(saved[0])
    f.comparison['shadow_run'] = f.make_run('shad-extra', 'failed', 1, ['BLK-EXTRA'], [], 4000, 30, 3)
    f.comparison['operator_decision']['decision'] = 'approve-recommendation-only'
    profile_evaluate_call(api, f, True)
    f.comparison['operator_decision']['decision'] = 'reject-recommendation'
    res_extra = profile_evaluate_call(api, f)
    require(
        res_extra['unexplained_divergences'] == ['BLK-EXTRA']
        and res_extra['recommendation'] == 'reject-promotion',
        'unexplained divergence rejects promotion recommendation',
    )
    f.comparison, f.comparison_policy = saved
    profile_evaluate_call(api, f)


def profile_cost_latency_accounting(api, f):
    res = profile_evaluate_call(api, f)
    require(
        res['accounting']
        == dict(
            baseline_duration_ms=12000,
            shadow_duration_ms=4500,
            duration_delta_ms=-7500,
            baseline_cost_units=80,
            shadow_cost_units=35,
            cost_delta_units=-45,
            baseline_command_count=6,
            shadow_command_count=3,
            command_delta=-3,
        )
        and res['within_cost_latency_bounds'] is True,
        'exact cost and latency accounting',
    )
    saved = copy.deepcopy((f.comparison, f.comparison_policy))
    # Exceeding Routine max_duration_ms (60000) or max_cost_units (100)
    f.comparison['shadow_run'] = f.make_run('shad-slow', 'success', 0, [], [], 75000, 120, 4)
    f.comparison['operator_decision']['decision'] = 'approve-recommendation-only'
    profile_evaluate_call(api, f, True)
    f.comparison['operator_decision']['decision'] = 'reject-recommendation'
    over = profile_evaluate_call(api, f)
    require(
        over['within_cost_latency_bounds'] is False and over['recommendation'] == 'reject-promotion',
        'exceeding cost/latency bounds rejects recommendation',
    )
    # Tampering with duration_ms / cost_units / command_count relative to pinned capture_ref must fail
    for field in ('duration_ms', 'cost_units', 'command_count'):
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['shadow_run'][field] += 1
        profile_evaluate_call(api, f, True)
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['shadow_run'][field] = 0
        profile_evaluate_call(api, f, True)
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['shadow_run'][field] = True
        profile_evaluate_call(api, f, True)
    f.comparison, f.comparison_policy = saved
    profile_evaluate_call(api, f)


def profile_no_self_promotion(api, f):
    res = profile_evaluate_call(api, f)
    require(
        res['promoted'] is False
        and res['active_gates_reduced'] is False
        and res['permissions_changed'] is False,
        'recommendation never self-promotes or reduces gates',
    )
    saved = copy.deepcopy((f.comparison, f.comparison_policy, f.preregistration, f.prereg_policy, f.profile_authority))
    for action in ('self-promote', 'activate-profile', 'reduce-gates', 'grant-permissions', ''):
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['requested_action'] = action
        profile_evaluate_call(api, f, True)
    for field, val in (
        ('self_promote', True),
        ('reduce_active_gates', True),
        ('role', 'Generator'),
        ('role', 'Evaluator'),
        ('owner', 'wrong-owner'),
        ('gate', 'WRONG-GATE'),
        ('decision', 'auto-promote'),
    ):
        f.comparison = copy.deepcopy(saved[0])
        f.comparison['operator_decision'][field] = val
        profile_evaluate_call(api, f, True)
    for field in ('self_promotion_allowed', 'automatic_gate_reduction_allowed'):
        f.preregistration = copy.deepcopy(saved[2])
        f.preregistration['operator_decision_policy'][field] = True
        profile_preregister_call(api, f, True)
    for field in ('allow_self_promotion', 'allow_gate_reduction'):
        f.profile_authority = copy.deepcopy(saved[4])
        f.profile_authority[field] = True
        bad_auth_ref = f.pin_new('bad-profile-auth', f.profile_authority)
        f.preregistration = copy.deepcopy(saved[2])
        f.prereg_policy = copy.deepcopy(saved[3])
        f.prereg_policy['authority_ref'] = bad_auth_ref
        f.preregistration['operator_decision_policy']['authority_ref'] = bad_auth_ref
        profile_preregister_call(api, f, True)
    f.comparison, f.comparison_policy, f.preregistration, f.prereg_policy, f.profile_authority = saved
    profile_evaluate_call(api, f)


def run_profile_case(name, api):
    if not all(callable(getattr(api, fn, None)) for fn in ('preregister_profile_comparison', 'evaluate_profile_comparison', 'verify_profiles_ready')):
        print('SETUP_ERROR: missing Phase 019 profile APIs; not intended semantic red', file=sys.stderr)
        raise SystemExit(2)
    previous = os.environ.get('NIZAM_WA120_FIXTURE')
    os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
    try:
        with tempfile.TemporaryDirectory(prefix='nizam019-profiles-') as parent:
            f = ProfileFixture(api, parent)
            dispatch = {
                'preregister-before-run': profile_preregister_before_run,
                'roles-reused': profile_roles_reused,
                'reject-unstable-baseline': profile_reject_unstable_baseline,
                'same-candidate': profile_same_candidate,
                'missed-baseline-blocker': profile_missed_baseline_blocker,
                'cost-latency-accounting': profile_cost_latency_accounting,
                'no-self-promotion': profile_no_self_promotion,
            }
            dispatch[name](api, f)
    finally:
        if previous is None:
            os.environ.pop('NIZAM_WA120_FIXTURE', None)
        else:
            os.environ['NIZAM_WA120_FIXTURE'] = previous


def run_profiles_ready(api):
    """Observe committed Phase 019 (124/125) profile readiness bundle and verify negative discrimination."""
    if not callable(getattr(api, 'verify_profiles_ready', None)):
        print('SETUP_ERROR: missing verify_profiles_ready; never intended semantic red', file=sys.stderr)
        raise SystemExit(2)
    policy_path = ROOT / 'tools/fixtures/workflow_assurance/wa125_profiles_policy.json'
    policy = api.parse_json(api.regular_file(ROOT, str(policy_path.relative_to(ROOT))).read_bytes())
    evidence = api.parse_json(api._receipt_artifact(ROOT, policy['evidence_ref']))
    before = copy.deepcopy((policy, evidence))
    status = git(ROOT, 'status', '--porcelain', '--untracked-files=all')
    with tempfile.TemporaryDirectory(prefix='nizam125-profiles-observation-') as parent:
        scratch = Path(parent) / 'repo'
        subprocess.check_call(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(scratch)])
        git(scratch, 'remote', 'set-url', 'origin', git(ROOT, 'remote', 'get-url', 'origin'))
        git(scratch, 'checkout', '--quiet', '--detach', evidence['candidate']['source_commit'])
        result = api.verify_profiles_ready(scratch, evidence, policy=policy)
        # Negative discrimination: remove one comparison row and verify rejection
        negative = copy.deepcopy(evidence)
        negative['comparisons'] = negative['comparisons'][:2]
        synthetic_policy = copy.deepcopy(policy)
        synthetic_review = api.parse_json(api._receipt_artifact(scratch, policy['independent_review_ref']))
        git(scratch, 'config', 'user.name', 'SYNTHETIC125 private observation control')
        git(scratch, 'config', 'user.email', 'synthetic125@example.invalid')
        git(scratch, 'config', 'gc.auto', '0')
        git(scratch, 'config', 'maintenance.auto', 'false')

        def commit_control(label, value):
            path = f'.agent/evidence/125/synthetic-observation-{label}.json'
            raw = canonical(value) + b'\n'
            target = scratch / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            git(scratch, 'add', '--', path)
            git(scratch, 'commit', '--quiet', '-m', 'SYNTHETIC125 observation control ' + label)
            return dict(path=path, revision=git(scratch, 'rev-parse', 'HEAD'), sha256=sha(raw))

        synthetic_policy['evidence_ref'] = commit_control('missing-comparisons', negative)
        synthetic_review['evidence_ref'] = synthetic_policy['evidence_ref']
        synthetic_policy['independent_review_ref'] = commit_control('review-ref-binding', synthetic_review)
        try:
            api.verify_profiles_ready(scratch, negative, policy=synthetic_policy)
        except api.AssuranceError as exc:
            require(re.search(r'comparisons|tiers|Routine|Standard|High-assurance', str(exc), re.I) is not None, 'profiles-ready negative cause: ' + str(exc))
            print('EXPECTED_REJECTION SYNTHETIC125 missing-comparisons observation: ' + str(exc))
        else:
            require(False, 'synthetic invalid profiles-ready proof accepted')
        # Negative discrimination: remove capture_ref from case_proofs
        no_cap_ev = copy.deepcopy(evidence)
        no_cap_ev['case_proofs'][0].pop('capture_ref', None)
        no_cap_policy = copy.deepcopy(policy)
        no_cap_review = api.parse_json(api._receipt_artifact(scratch, policy['independent_review_ref']))
        no_cap_policy['evidence_ref'] = commit_control('missing-case-capture', no_cap_ev)
        no_cap_review['evidence_ref'] = no_cap_policy['evidence_ref']
        no_cap_policy['independent_review_ref'] = commit_control('missing-case-capture-review', no_cap_review)
        try:
            api.verify_profiles_ready(scratch, no_cap_ev, policy=no_cap_policy)
        except api.AssuranceError as exc:
            require(re.search(r'case proof|closed|capture', str(exc), re.I) is not None, 'profiles-ready missing case capture cause: ' + str(exc))
        else:
            require(False, 'synthetic missing case_proof capture_ref accepted')
        # Negative discrimination: independent reviewer identical to authority owner
        self_review_policy = copy.deepcopy(policy)
        self_review = api.parse_json(api._receipt_artifact(scratch, policy['independent_review_ref']))
        self_review['reviewer'] = 'cnr'
        self_review_policy['independent_review_ref'] = commit_control('self-reviewer', self_review)
        try:
            api.verify_profiles_ready(scratch, evidence, policy=self_review_policy)
        except api.AssuranceError as exc:
            require(re.search(r'independent reviewer|distinct|authority|producer', str(exc), re.I) is not None, 'profiles-ready self-reviewer cause: ' + str(exc))
        else:
            require(False, 'synthetic self-reviewer accepted')
        require(api.verify_profiles_ready(scratch, evidence, policy=policy) == result, 'profiles-ready restores after synthetic negative')
    require((policy, evidence) == before and git(ROOT, 'status', '--porcelain', '--untracked-files=all') == status, 'profiles-ready preserves inputs and repo state')
    require(
        result
        == dict(
            schema_version=1,
            feature_id='125',
            phase='019-workflow-assurance-profiles',
            execution_scope='repository-worktree',
            source_commit=evidence['candidate']['source_commit'],
            candidate_sha256=sha(canonical(evidence['candidate'])),
            preregistration_sha256=evidence['preregistration_ref']['sha256'],
            tiers_verified=['Routine', 'Standard', 'High-assurance'],
            cases_verified=list(PROFILE_CASES),
            promoted=False,
            active_gates_reduced=False,
            independent_review_sha256=policy['independent_review_ref']['sha256'],
        ),
        'exact profiles-ready observation result',
    )
    print('PASS profiles-ready observed independently selected Phase 019 proof')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--case', choices=CASES + AGF_CASES + RECEIPT_CASES + LANE_CASES + FAILURE_CASES + CONTROL_CASES + PROFILE_CASES)
    group.add_argument('--scope', action='store_true')
    group.add_argument('--scope-controls', action='store_true')
    group.add_argument('--base-cases', action='store_true')
    group.add_argument('--scope-116', action='store_true')
    group.add_argument('--scope-controls-116', action='store_true')
    group.add_argument('--pre-entry-cases', action='store_true')
    group.add_argument('--check', choices=('foundation-ready', 'controls-ready', 'profiles-ready'))
    group.add_argument('--scope-118', action='store_true')
    group.add_argument('--scope-controls-118', action='store_true')
    group.add_argument('--scope-117', action='store_true')
    group.add_argument('--scope-controls-117', action='store_true')
    parser.add_argument('--base')
    args = parser.parse_args()
    if args.scope_118 or args.scope_controls_118:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / 'tools/fixtures/workflow_assurance/scope_guard_118.py')
        (helper.scope_controls if args.scope_controls_118 else helper.scope)(args.base); return
    if args.check == 'controls-ready':
        if args.base: parser.error('--base requires a scope command')
        run_controls_ready(load_api()); return
    if args.check == 'profiles-ready':
        if args.base: parser.error('--base requires a scope command')
        run_profiles_ready(load_api()); return
    if args.check:
        if args.base: parser.error('--base requires a scope command')
        load_api(ROOT / 'tools/fixtures/workflow_assurance/foundation_fixtures.py').run_foundation(load_api()); return
    if args.scope_117 or args.scope_controls_117:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / 'tools/fixtures/workflow_assurance/scope_guard_117.py')
        (helper.scope_controls if args.scope_controls_117 else helper.scope)(args.base); return
    if args.scope_116 or args.scope_controls_116:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / 'tools/fixtures/workflow_assurance/scope_guard_116.py')
        (helper.scope_controls if args.scope_controls_116 else helper.scope)(args.base); return
    if args.scope or args.scope_controls:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / 'tools/fixtures/workflow_assurance/scope_guard_115.py')
        (helper.scope_controls if args.scope_controls else helper.scope)(args.base); return
    if args.base: parser.error('--base requires a scope command')
    api = load_api()
    for name in ([args.case] if args.case else PRE_ENTRY_CASES if args.pre_entry_cases else BASE_CASES if args.base_cases else CASES + AGF_CASES + RECEIPT_CASES + LANE_CASES + FAILURE_CASES + CONTROL_CASES + PROFILE_CASES):
        (run_profile_case if name in PROFILE_CASES else run_controls_case if name in CONTROL_CASES else run_failure_case if name in FAILURE_CASES else run_lane_case if name in LANE_CASES else run_receipt_case if name in RECEIPT_CASES else run_agf_case if name in AGF_CASES else run_entry_case if name in ENTRY_CASES else run_bundle_case if name in BUNDLE_CASES else run_case)(name, api); print('PASS ' + name)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
