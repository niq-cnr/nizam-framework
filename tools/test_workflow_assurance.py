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


BundleFixture = load_api(ROOT / '.agent/evidence/116/bundle-fixtures.py').BundleFixture


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
    helper = load_api(ROOT / '.agent/evidence/117/entry-fixtures.py')
    helper.run_case(name, api)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--case', choices=CASES)
    group.add_argument('--scope', action='store_true')
    group.add_argument('--scope-controls', action='store_true')
    group.add_argument('--base-cases', action='store_true')
    group.add_argument('--scope-116', action='store_true')
    group.add_argument('--scope-controls-116', action='store_true')
    group.add_argument('--pre-entry-cases', action='store_true')
    group.add_argument('--check', choices=('foundation-ready',))
    group.add_argument('--scope-118', action='store_true')
    group.add_argument('--scope-controls-118', action='store_true')
    group.add_argument('--scope-117', action='store_true')
    group.add_argument('--scope-controls-117', action='store_true')
    parser.add_argument('--base')
    args = parser.parse_args()
    if args.scope_118 or args.scope_controls_118:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / '.agent/evidence/118/scope-guard.py')
        (helper.scope_controls if args.scope_controls_118 else helper.scope)(args.base); return
    if args.check:
        if args.base: parser.error('--base requires a scope command')
        load_api(ROOT / '.agent/evidence/118/foundation-fixtures.py').run_foundation(load_api()); return
    if args.scope_117 or args.scope_controls_117:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / '.agent/evidence/117/scope-guard.py')
        (helper.scope_controls if args.scope_controls_117 else helper.scope)(args.base); return
    if args.scope_116 or args.scope_controls_116:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / '.agent/evidence/116/scope-guard.py')
        (helper.scope_controls if args.scope_controls_116 else helper.scope)(args.base); return
    if args.scope or args.scope_controls:
        if not args.base: parser.error('scope commands require --base')
        helper = load_api(ROOT / '.agent/evidence/115/recovery-scope-guard.py')
        (helper.scope_controls if args.scope_controls else helper.scope)(args.base); return
    if args.base: parser.error('--base requires a scope command')
    api = load_api()
    for name in ([args.case] if args.case else PRE_ENTRY_CASES if args.pre_entry_cases else BASE_CASES if args.base_cases else CASES):
        (run_entry_case if name in ENTRY_CASES else run_bundle_case if name in BUNDLE_CASES else run_case)(name, api); print('PASS ' + name)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
