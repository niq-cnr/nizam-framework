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
import subprocess
import sys
import tempfile

BASE = '9ebfd03883486a205ac8c3a211f0cac0af5fddba'
APPROVED = '6af2a8b4ed54c09830acb2033f9c5c0d053263df'
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
        for path, data in {'src/code.py': 'value = 1\n', 'contract.json': '{"revision":1}',
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
        require(actual['assessed_inputs'][category] == expected, 'observed ' + category + ' bytes/mode')
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
    git(f.root, 'remote', 'remove', 'origin')
    rejected(api, lambda: f.assess(api), 'missing origin is not identity')


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
    rejected(api, lambda: f.assess(api, mask={'src/code.py': ['/value']}), 'source cannot receive record mask')


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


def read_at(revision, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + path], stderr=subprocess.PIPE)


def parsed_at(revision, path):
    return json.loads(read_at(revision, path))


def same(a, b, message):
    require(canonical(a) == canonical(b), message)


def scope(base):
    require(base == BASE, 'scope requires approved immutable base')
    contract = json.loads((ROOT / '.agent/contracts/115.json').read_text())
    approved = parsed_at(APPROVED, '.agent/contracts/115.json')
    before_contract = copy.deepcopy(approved); after_contract = copy.deepcopy(contract)
    for value in (before_contract, after_contract):
        value.pop('status', None); value.pop('approvals', None)
    same(before_contract, after_contract, 'approved contract obligations unchanged')
    allowed = {x['path'] for family in ('files_create', 'files_modify') for x in approved['scope'][family] if not x['path'].endswith('/**')}
    changed = set(subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--name-only', '-z', base], stderr=subprocess.PIPE).decode().split('\0')) - {''}
    unknown = set(subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--others', '-z'], stderr=subprocess.PIPE).decode().split('\0')) - {''}
    # Git ignores no unknown paths here: ignored artifacts also receive scope scrutiny.
    changed |= unknown
    for path in changed:
        require(path in allowed or path.startswith(('.agent/evidence/115/', '.agent/evidence/phase017-activation/')), 'unknown scope path ' + path)
    prior = git(ROOT, 'ls-tree', '-r', '--name-only', APPROVED).splitlines()
    for path in prior:
        if path.startswith(('.agent/evidence/', '.nizam/')) or path in ('.agent/qa/115-contract-review.json', '.agent/validator/115-mode-a.json'):
            require((ROOT / path).is_file() and not (ROOT / path).is_symlink(), 'protected file type ' + path)
            require((ROOT / path).read_bytes() == read_at(APPROVED, path), 'protected immutable bytes ' + path)
    # All nonauthorized files are byte-exact by the path delta guard above.
    index = json.loads((ROOT / 'NIZAM.json').read_text()); oldindex = parsed_at(base, 'NIZAM.json')
    for item in index['modules']:
        if item['path'] == 'tools':
            for addition in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py'):
                if addition in item['key_documents']: item['key_documents'].remove(addition)
    same(index, oldindex, 'index only appends two tool documents')
    before = parsed_at(base, '.agent/run_state.json'); after = json.loads((ROOT / '.agent/run_state.json').read_text())
    require(canonical(after['history'][:len(before['history'])]) == canonical(before['history']), 'prior history exact prefix')
    same(after['phase_015_scope_budget_final'], before['scope_budget'], 'phase015 full final budget preserved')
    mutable = {'current_phase', 'current_feature', 'status', 'updated_at', 'last_action', 'active_contract_id', 'pending_operator_gate', 'history', 'scope_budget', 'circuit_breaker', 'phase_015_scope_budget_final'}
    same({k:v for k,v in after.items() if k not in mutable}, {k:v for k,v in before.items() if k not in mutable}, 'all unowned coordination fields')
    require(after['current_phase'] == '017-workflow-assurance-foundation' and after['current_feature'] in ('115', '116', None), 'only authorized017/115 progression')
    budget = after['scope_budget']; require(budget['original_estimate_lines'] == 5400 and budget['ceiling_130pct'] == 7020, 'authorized017 allowance unchanged')
    require(all(str(x['id']) == '115' for x in budget['per_feature']), 'only115 budget measured')
    for key, value in before['circuit_breaker'].items(): same(after['circuit_breaker'][key], value, 'old counter ' + key)
    for key in set(after['circuit_breaker']) - set(before['circuit_breaker']):
        require(key.startswith(('115-', 'phase017-')) and after['circuit_breaker'][key]['limit'] == 3 and 0 <= after['circuit_breaker'][key]['attempts'] <= 3, 'bounded new counter ' + key)
    features = json.loads((ROOT / '.agent/feature_list_017.json').read_text()); oldfeatures = parsed_at(base, '.agent/feature_list_017.json')
    for key in set(features) | set(oldfeatures):
        if key not in ('features', 'spec_version', 'phase_status'): same(features.get(key), oldfeatures.get(key), 'phase017 list ' + key)
    require(features['spec_version'] == '0.2.0' and features['phase_status'] in ('in_progress', 'complete'), 'activated list version/status')
    require(len(features['features']) == len(oldfeatures['features']), 'no added feature')
    for actual, original in zip(features['features'], oldfeatures['features']):
        if original['id'] != '115': same(actual, original, 'uncontracted feature ' + original['id'])
        else:
            metadata = {'status', 'passes', 'contract', 'qa', 'evidence', 'completed_at', 'contract_ref', 'qa_ref', 'evidence_ref'}
            same({k:v for k,v in actual.items() if k not in metadata}, {k:v for k,v in original.items() if k not in metadata}, '115 obligations/estimate frozen')
    manifest = json.loads((ROOT / 'docs/planning/manifest.json').read_text()); oldmanifest = parsed_at(base, 'docs/planning/manifest.json')
    require(manifest['current_phase'] == '017-workflow-assurance-foundation', 'only017 current manifest')
    for actual, original in zip(manifest['phases'], oldmanifest['phases']):
        if original['id'] != '017-workflow-assurance-foundation': same(actual, original, 'other manifest row')
        else:
            fields = {'activation_state', 'status', 'note', 'notes', 'updated_at'}
            same({k:v for k,v in actual.items() if k not in fields}, {k:v for k,v in original.items() if k not in fields}, '017 manifest immutable fields')
    require(len(manifest['phases']) == len(oldmanifest['phases']), 'manifest row count')
    for key in set(manifest) | set(oldmanifest):
        if key not in ('phases', 'current_phase', 'updated_at'): same(manifest.get(key), oldmanifest.get(key), 'manifest root ' + key)
    dag = json.loads((ROOT / 'docs/planning/backlog_dag.json').read_text()); anchor = parsed_at(APPROVED, 'docs/planning/backlog_dag.json')
    for key in set(dag) | set(anchor):
        if key not in ('generated_at', 'activated_phase', 'phase017_execution', 'packets'): same(dag.get(key), anchor.get(key), 'DAG preserved ' + key)
    require(len(dag['packets']) == len(anchor['packets']), 'DAG packet count')
    for actual, original in zip(dag['packets'], anchor['packets']):
        if original.get('id') != 'A09': same(actual, original, 'other DAG packet')
        else:
            fields = {'status', 'prerequisites_satisfied', 'completion_evidence', 'evidence', 'qa', 'progress', 'closure', 'completed_at', 'prerequisites'}
            same({k:v for k,v in actual.items() if k not in fields}, {k:v for k,v in original.items() if k not in fields}, 'A09 adopted edges/obligations')
    phase_text = (ROOT / 'docs/planning/phase_017.yaml').read_text()
    phase_anchor = read_at(APPROVED, 'docs/planning/phase_017.yaml').decode()
    require(phase_anchor[phase_anchor.index("- id: '116'"):] == phase_text[phase_text.index("- id: '116'"):], 'uncontracted phase steps exact')
    # Doc edits remain bounded by independent ModeB review; immutable historical suffix is mechanical.
    for path, heading in [('docs/planning/HANDOVER.md', '## Historical handover snapshot')]:
        old = read_at(base, path).decode(); actual = (ROOT / path).read_text()
        oldbody = old[old.find('\n# '):]
        require('\n' + heading in oldbody, 'nonempty historical anchor ' + path)
        suffix = oldbody[oldbody.index('\n' + heading):]
        require(len(suffix) > 1000, 'substantive historical suffix ' + path)
        require(suffix in actual, 'historical document body preserved ' + path)
    workflow = (ROOT / '.github/workflows/compliance.yml').read_text(); old = read_at(base, '.github/workflows/compliance.yml').decode()
    lines = workflow.splitlines(True)
    lines = [line for line in lines if 'python3 tools/test_workflow_assurance.py' not in line]
    require(''.join(lines) == old, 'workflow one additive test command only')
    print('PASS scope: actual delta, immutable proof, owned fields and prior history')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--case', choices=CASES)
    group.add_argument('--scope', action='store_true')
    parser.add_argument('--base')
    args = parser.parse_args()
    if args.scope:
        if not args.base: parser.error('--scope requires --base')
        scope(args.base); return
    if args.base: parser.error('--base requires --scope')
    api = load_api()
    for name in ([args.case] if args.case else CASES):
        run_case(name, api); print('PASS ' + name)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
