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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--case', choices=CASES + AGF_CASES + RECEIPT_CASES + LANE_CASES + FAILURE_CASES)
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
    for name in ([args.case] if args.case else PRE_ENTRY_CASES if args.pre_entry_cases else BASE_CASES if args.base_cases else CASES + AGF_CASES + RECEIPT_CASES + LANE_CASES + FAILURE_CASES):
        (run_failure_case if name in FAILURE_CASES else run_lane_case if name in LANE_CASES else run_receipt_case if name in RECEIPT_CASES else run_agf_case if name in AGF_CASES else run_entry_case if name in ENTRY_CASES else run_bundle_case if name in BUNDLE_CASES else run_case)(name, api); print('PASS ' + name)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
