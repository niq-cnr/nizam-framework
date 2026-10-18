#!/usr/bin/env python3
"""Read-only assessed-source identity and bounded JSON record continuity.

An immutable Git anchor survives later record-only commits. Unknown candidate
changes fail closed; this utility does not authenticate callers or authorize work.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys


class AssuranceError(ValueError):
    """An assessment is incomplete, unsafe, malformed or has changed."""


def require(condition, message):
    if not condition:
        raise AssuranceError(message)


def json_value(value, ancestors=None):
    ancestors = set() if ancestors is None else ancestors
    if type(value) in (dict, list):
        require(id(value) not in ancestors, 'cyclic non-JSON value')
        ancestors.add(id(value))
    if type(value) is dict:
        require(all(type(key) is str for key in value), 'JSON object keys must be strings')
        for child in value.values():
            json_value(child, ancestors)
    elif type(value) is list:
        for child in value:
            json_value(child, ancestors)
    else:
        require(type(value) in (str, int, float, bool, type(None)), 'non-JSON value')
        require(type(value) is not float or math.isfinite(value), 'nonfinite JSON number')
    if type(value) in (dict, list):
        ancestors.remove(id(value))


def canonical(value):
    json_value(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise AssuranceError('nonfinite JSON number: ' + value)
    try:
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
        json_value(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise AssuranceError('invalid JSON: ' + str(exc)) from exc


def pointers(fields):
    require(type(fields) is list and all(type(p) is str for p in fields), 'owned fields must be pointer list')
    require(len(fields) == len(set(fields)), 'duplicate owned pointer')
    result = {}
    for pointer in fields:
        require(pointer.startswith('/') and pointer != '/', 'owned pointer must name a field')
        require(re.search(r'~(?![01])', pointer) is None, 'invalid pointer escape')
        parts = tuple(p.replace('~1', '/').replace('~0', '~') for p in pointer[1:].split('/'))
        require(all(parts), 'empty pointer segment')
        require(not any(parts[:len(old)] == old or old[:len(parts)] == parts for old in result), 'overlapping owned pointers')
        result[parts] = pointer
    return result


def verify_record_update(before, after, owned_fields):
    json_value(before); json_value(after)
    require(type(before) is dict and type(after) is dict, 'record root must be JSON object')
    owned = pointers(owned_fields)
    for parts in owned:
        value = before
        for key in parts:
            require(type(value) is dict and key in value, 'owned pointer is missing or traverses container')
            value = value[key]
        require(type(value) not in (dict, list) or parts == ('history',), 'owned field must be scalar leaf')
        if parts == ('history',):
            require(type(value) is list, 'history must be a list')
    if 'history' in before:
        require(type(before['history']) is list and type(after.get('history')) is list, 'history must remain a list')
        prefix = after['history'][:len(before['history'])]
        require(canonical(prefix) == canonical(before['history']), 'history original prefix changed')

    def compare(left, right, path):
        require(type(left) is type(right), 'record JSON type changed: ' + repr(path))
        if path in owned:
            return
        if type(left) is dict:
            require(set(left) == set(right), 'record key set changed: ' + repr(path))
            for key in left:
                compare(left[key], right[key], path + (key,))
        else:
            require(canonical(left) == canonical(right), 'unowned record value changed: ' + repr(path))
    compare(before, after, ())
    return True


def relative_path(path):
    require(type(path) is str and path and '\\' not in path and '\0' not in path, 'invalid relative path')
    parts = path.split('/')
    require(not path.startswith('/') and all(p not in ('', '.', '..', '.git') for p in parts), 'unsafe or aliased relative path: ' + path)
    return path


def regular_file(root, path):
    relative_path(path)
    target = root
    for part in path.split('/'):
        target = target / part
        require(not target.is_symlink(), 'symlink path component: ' + path)
    require(target.is_file() and stat.S_ISREG(target.stat().st_mode), 'missing/nonregular file: ' + path)
    return target


def git(root, *args):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
        return result.stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        diagnostic = getattr(exc, 'stderr', b'').decode('utf-8', errors='replace').strip()
        raise AssuranceError('Git observation failed: ' + (diagnostic or str(exc))) from exc


def blobs(root, object_ids):
    ids = sorted(set(object_ids))
    try:
        result = subprocess.run(['git', '-C', str(root), 'cat-file', '--batch'],
                                input=('\n'.join(ids) + '\n').encode(), capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AssuranceError('Git blob observation failed') from exc
    output = result.stdout; offset = 0; values = {}
    for oid in ids:
        end = output.find(b'\n', offset)
        header = output[offset:end].decode().split()
        require(end >= offset and len(header) == 3 and header[0] == oid and header[1] == 'blob', 'missing/nonblob Git input')
        size = int(header[2]); offset = end + 1
        require(output[offset + size:offset + size + 1] == b'\n', 'truncated Git blob observation')
        values[oid] = output[offset:offset + size]; offset += size + 1
    require(offset == len(output), 'unexpected Git blob output')
    return values


CATEGORIES = ('source', 'contracts', 'tests', 'tools')


def manifest(inputs):
    require(type(inputs) is dict and set(inputs) == set(CATEGORIES) | {'unknown_dependencies'}, 'unknown/incomplete input manifest')
    require(type(inputs['unknown_dependencies']) is list and not inputs['unknown_dependencies'], 'unknown dependencies invalidate assessment')
    seen = set(); result = {}
    for category in CATEGORIES:
        paths = inputs[category]
        require(type(paths) is list and paths, 'empty/malformed assessed category: ' + category)
        for path in paths:
            relative_path(path)
            require(path not in seen, 'duplicate assessed path: ' + path)
            seen.add(path)
        result[category] = sorted(paths)
    return result


def masks(ownership):
    require(type(ownership) is dict, 'record ownership must be object')
    result = {}
    for path, fields in ownership.items():
        relative_path(path); pointers(fields)
        result[path] = sorted(fields)
    return result


def assess_repository(repo, source_commit, inputs, environment_names, record_ownership=None):
    """Observe complete candidate drift against the explicit immutable anchor."""
    try:
        root = Path(repo)
        require(not root.is_symlink(), 'repository root is symlink')
        root = root.resolve(strict=True)
        require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'repository must be Git toplevel')
        require(type(source_commit) is str and re.fullmatch('[0-9a-f]{40}', source_commit), 'source commit must be explicit full immutable id')
        require(git(root, 'rev-parse', '--verify', source_commit + '^{commit}').decode().strip() == source_commit, 'source anchor is not exact commit')
        source_tree = git(root, 'rev-parse', source_commit + '^{tree}').decode().strip()
        origin = git(root, 'remote', 'get-url', 'origin').decode().strip()
        require(bool(origin), 'missing repository origin')
        selected = manifest(inputs)
        ownership = masks({} if record_ownership is None else record_ownership)
        forbidden = set(selected['source'] + selected['tests'] + selected['tools'])
        require(not forbidden.intersection(ownership), 'source/tests/tools cannot receive record ownership')
        require(type(environment_names) is list and all(type(n) is str and n and '=' not in n and '\0' not in n for n in environment_names), 'invalid environment variable names')
        require(len(environment_names) == len(set(environment_names)), 'duplicate environment variable')
        require(all(n in os.environ for n in environment_names), 'missing assessed environment variable')
        environment = {'runtime': {'implementation': platform.python_implementation(), 'version': platform.python_version(),
                                   'system': platform.system(), 'machine': platform.machine()},
                       'variables': {n: os.environ[n] for n in sorted(environment_names)}}
        baseline = {}
        for entry in git(root, 'ls-tree', '-rz', source_commit).split(b'\0'):
            if not entry: continue
            metadata, name = entry.split(b'\t', 1); mode, kind, oid = metadata.decode().split()
            path = name.decode(); relative_path(path)
            require(mode in ('100644', '100755') and kind == 'blob', 'unsupported anchored file mode: ' + path)
            baseline[path] = (mode, oid)
        index = {}
        for entry in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
            if not entry: continue
            metadata, name = entry.split(b'\t', 1); mode, oid, stage = metadata.decode().split()
            path = name.decode(); relative_path(path)
            require(stage == '0' and mode in ('100644', '100755') and path not in index, 'unmerged/unsafe index input: ' + path)
            index[path] = (mode, oid)
        require(set(index) == set(baseline), 'unknown added/deleted/renamed tracked path')
        require(not git(root, 'ls-files', '--others', '-z'), 'unknown untracked or ignored candidate path')
        all_selected = set(p for paths in selected.values() for p in paths) | set(ownership)
        require(all_selected <= set(baseline), 'assessed/record path missing from immutable anchor')
        objects = blobs(root, [oid for mode, oid in baseline.values()] + [oid for mode, oid in index.values()])
        observed = {}
        # Raw bytes for every tracked path, not Git diff text: attributes/filters
        # cannot hide changes to unknown source/build dependencies.
        for path, (mode, oid) in baseline.items():
            target = regular_file(root, path); current = target.read_bytes()
            require(bool(target.stat().st_mode & 0o111) == (mode == '100755') and index[path][0] == mode, 'executable mode changed: ' + path)
            anchor = objects[oid]; staged = objects[index[path][1]]
            if path in ownership:
                original = parse_json(anchor)
                verify_record_update(original, parse_json(current), ownership[path])
                verify_record_update(original, parse_json(staged), ownership[path])
                digest = sha(canonical(original))
            else:
                require(current == anchor and staged == anchor, 'unknown/assessed bytes changed: ' + path)
                digest = sha(current)
            observed[path] = {'path': path, 'sha256': digest, 'executable': mode == '100755'}
        identity = {'schema_version': 1, 'repository': origin, 'source_commit': source_commit,
                    'source_tree': source_tree, 'assessed_inputs': {c: [observed[p] for p in selected[c]] for c in CATEGORIES},
                    'environment': environment, 'record_ownership': ownership}
        identity['identity_sha256'] = sha(canonical(identity))
        validate_identity(identity)
        return identity
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise AssuranceError('assessment observation failed: ' + str(exc)) from exc


def validate_identity(identity):
    json_value(identity)
    keys = {'schema_version', 'repository', 'source_commit', 'source_tree', 'assessed_inputs', 'environment', 'record_ownership', 'identity_sha256'}
    require(type(identity) is dict and set(identity) == keys, 'unknown/incomplete identity fields')
    require(type(identity['schema_version']) is int and identity['schema_version'] == 1, 'invalid identity schema version')
    require(type(identity['repository']) is str and identity['repository'] and identity['repository'] == identity['repository'].strip(), 'invalid repository identity')
    for key, length in [('source_commit', 40), ('source_tree', 40), ('identity_sha256', 64)]:
        require(type(identity[key]) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', identity[key]), 'invalid identity ' + key)
    assessed = identity['assessed_inputs']
    require(type(assessed) is dict and set(assessed) == set(CATEGORIES), 'invalid assessed identity categories')
    seen = set(); forbidden = set()
    for category in CATEGORIES:
        entries = assessed[category]
        require(type(entries) is list and entries, 'empty assessed identity category')
        names = []
        for item in entries:
            require(type(item) is dict and set(item) == {'path', 'sha256', 'executable'}, 'invalid assessed identity entry')
            path = relative_path(item['path']); names.append(path)
            require(path not in seen, 'duplicate assessed identity path'); seen.add(path)
            require(type(item['executable']) is bool, 'invalid executable identity type')
            require(type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}', item['sha256']), 'invalid assessed digest')
        require(names == sorted(names), 'noncanonical assessed path order')
        if category != 'contracts': forbidden.update(names)
    ownership = masks(identity['record_ownership'])
    require(canonical(ownership) == canonical(identity['record_ownership']) and not forbidden.intersection(ownership), 'invalid record identity ownership')
    environment = identity['environment']
    require(type(environment) is dict and set(environment) == {'runtime', 'variables'}, 'invalid environment identity fields')
    runtime = environment['runtime']; variables = environment['variables']
    require(type(runtime) is dict and set(runtime) == {'implementation', 'version', 'system', 'machine'} and all(type(v) is str for v in runtime.values()), 'invalid runtime identity')
    require(type(variables) is dict and all(type(k) is str and k and '=' not in k and '\0' not in k and type(v) is str for k, v in variables.items()), 'invalid environment variables identity')
    body = {k: v for k, v in identity.items() if k != 'identity_sha256'}
    require(identity['identity_sha256'] == sha(canonical(body)), 'identity digest mismatch')


def compare_identity(before, after):
    validate_identity(before); validate_identity(after)
    return canonical(before) == canonical(after)


def _bundle_object(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), 'invalid closed ' + label)


def _bundle_string(value, label):
    require(type(value) is str and bool(value.strip()), 'invalid ' + label)


def _bundle_hex(value, length, label):
    require(type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'invalid ' + label)


def _bundle_file(root, reference, keys, used):
    _bundle_object(reference, keys, 'file reference')
    path = relative_path(reference['path'])
    require(path not in used, 'duplicate bundle artifact path: ' + path)
    used.add(path)
    _bundle_hex(reference['sha256'], 64, 'artifact digest')
    data = regular_file(root, path).read_bytes()
    require(sha(data) == reference['sha256'], 'actual bundle artifact changed: ' + path)
    return data


def _bundle_proof(root, proof, stage, case, operation, commit, used):
    data = _bundle_file(root, proof, ('path', 'sha256', 'command', 'revision', 'diagnostic'), used)
    for key in ('command', 'revision', 'diagnostic'):
        _bundle_string(proof[key], key)
    require(proof['revision'] == commit, 'proof baseline revision mismatch')
    text = data.decode('utf-8')
    def header(name, expected):
        require(re.findall(r'^' + name + r': (.*)$', text, re.M) == [expected], 'invalid unique proof header: ' + name)
    header('COMMAND', proof['command']); header('REVISION', commit)
    header('EXIT', '1' if stage == 'red' else '0')
    require(text.count('\nSTDOUT:\n') == 1 and text.count('\nSTDERR:\n') == 1, 'proof output sections missing/duplicated')
    stdout = text.split('\nSTDOUT:\n', 1)[1]
    require('\nSTDERR:\n' in stdout, 'proof output sections out of order')
    stdout, stderr = stdout.split('\nSTDERR:\n', 1)
    output = stdout + '\n' + stderr
    # The frozen producer emits success/policy fields, never arbitrary exception
    # output. Classify only output channels: metadata paths are not diagnostics.
    permitted = [re.escape(proof['diagnostic'])]
    if stage == 'setup':
        permitted += [r'EXISTING115_API_HARNESS_CLI: PASS',
                      r'TARGET_CALLABLE: verify_acceptance_bundle PASS']
    else:
        permitted += [r'INPUT_SHA256: [0-9a-f]{64}', r'OPERATION_SHA256: [0-9a-f]{64}',
                      r'FIXTURE_BASELINE: [0-9a-f]{40}', r'FIXTURE_CURRENT_HEAD: [0-9a-f]{40}',
                      r'OBSERVED_RESULT: ' + ('accept' if stage == 'positive' else
                                             'reject' if operation['expected_result'] == 'accept' else 'accept')]
        if stage == 'red':
            permitted += [r'NAIVE_POLICY_DIAGNOSTIC: [^\r\n]+']
    grammar = '(?:' + '|'.join(permitted) + ')'
    require(all(not line.strip() or re.fullmatch(grammar, line) for line in stdout.splitlines()),
            'setup/transport failure cannot satisfy proof')
    require(all(not line.strip() or stage == 'red' and line == proof['diagnostic']
                for line in stderr.splitlines()), 'setup/transport failure cannot satisfy proof')
    # Bare and qualified exception labels are also disallowed inside an otherwise
    # recognized field; namespace-qualified policy text is not an error channel.
    exception_label = (r'\b(?:[A-Za-z_][A-Za-z0-9_.]*)?(?:Error|Exception)\s*:|'
                       r'\b(?:SystemExit|KeyboardInterrupt|GeneratorExit|StopIteration|StopAsyncIteration)\s*:|'
                       r'\bSETUP_OR_UNRELATED_ERROR\s*:|Traceback \(most recent call last\)|command not found')
    require(not re.search(exception_label, output), 'setup/transport failure cannot satisfy proof')
    require(proof['diagnostic'] in (output if stage == 'red' else stdout).splitlines(), 'actual proof diagnostic missing')
    if stage == 'setup':
        require('TARGET_CALLABLE: verify_acceptance_bundle PASS' in stdout.splitlines(), 'callable target setup missing')
        return
    reference = operation['positive_input' if stage == 'positive' else 'case_input']
    header('INPUT_SHA256', reference['sha256']); header('OPERATION_SHA256', sha(canonical(operation)))
    if stage == 'positive':
        require(proof['diagnostic'] == 'POSITIVE_CONTROL: ' + case + ' PASS', 'case-specific positive control missing')
    else:
        require(proof['diagnostic'].startswith('POLICY_ASSERTION: ' + case + ' ') and
                len(proof['diagnostic']) > len('POLICY_ASSERTION: ' + case + ' '), 'case-specific intended assertion missing')
        expected = 'reject' if operation['expected_result'] == 'accept' else 'accept'
        header('OBSERVED_RESULT', expected)
        require(not re.search(r'\b(?:missing|absent|unavailable)\b.*\b(?:API|callable|verify_acceptance_bundle)\b', proof['diagnostic'], re.I), 'absence assertion is not behavioral red')


def verify_acceptance_bundle(repo, bundle, independent_review):
    """Validate observed sealed inputs and independent behavioral proof records.

    Recorded commands are read, never executed. Roles are local recorded identity,
    not authentication. Implementation Source identity is separate from this seal.
    """
    try:
        json_value(bundle); json_value(independent_review)
        _bundle_object(bundle, ('schema_version', 'feature_id', 'baseline', 'inputs', 'environment',
                                'roles', 'required_cases', 'baseline_evidence', 'seal_sha256'), 'bundle')
        require(type(bundle['schema_version']) is int and bundle['schema_version'] == 1, 'invalid bundle schema version')
        _bundle_string(bundle['feature_id'], 'bundle feature')
        _bundle_hex(bundle['seal_sha256'], 64, 'bundle seal')
        body = {k: v for k, v in bundle.items() if k != 'seal_sha256'}
        require(bundle['seal_sha256'] == sha(canonical(body)), 'bundle seal mismatch')
        root = Path(repo)
        require(not root.is_symlink(), 'bundle repository is symlink')
        root = root.resolve(strict=True)
        require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'bundle repository must be Git toplevel')
        baseline = bundle['baseline']; _bundle_object(baseline, ('commit', 'tree'), 'baseline')
        for name in ('commit', 'tree'): _bundle_hex(baseline[name], 40, 'baseline ' + name)
        commit = baseline['commit']
        require(git(root, 'rev-parse', '--verify', commit + '^{commit}').decode().strip() == commit, 'baseline is not exact commit')
        require(git(root, 'rev-parse', commit + '^{tree}').decode().strip() == baseline['tree'], 'baseline actual tree mismatch')
        roles = bundle['roles']; _bundle_object(roles, ('test_author', 'developer', 'acceptance_reviewer'), 'roles')
        for person in roles.values():
            _bundle_object(person, ('agent_id', 'session_id'), 'role identity')
            for value in person.values(): _bundle_string(value, 'role identity')
        for field in ('agent_id', 'session_id'):
            require(len({person[field] for person in roles.values()}) == 3, 'roles must have distinct ' + field)
        review = independent_review
        _bundle_object(review, ('review', 'feature', 'actor', 'reviewer_session_id', 'seal_sha256', 'issues',
                                'missing_acceptance_coverage', 'unsupported_claims', 'final_verdict'), 'independent review')
        reviewer = roles['acceptance_reviewer']
        require(review['review'] == 'validator-test-bundle-review' and review['feature'] == bundle['feature_id'], 'review purpose/feature mismatch')
        require(review['actor'] == reviewer['agent_id'] and review['reviewer_session_id'] == reviewer['session_id'], 'independent reviewer identity mismatch')
        require(review['seal_sha256'] == bundle['seal_sha256'], 'review seal mismatch')
        for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
            require(type(review[key]) is list and not review[key], 'independent review has blockers')
        verdict = review['final_verdict']; _bundle_object(verdict, ('approved', 'summary'), 'review verdict')
        require(verdict['approved'] is True, 'review is not approved boolean'); _bundle_string(verdict['summary'], 'review summary')
        environment = bundle['environment']; _bundle_object(environment, ('runtime', 'variables'), 'environment')
        runtime = {'implementation': platform.python_implementation(), 'version': platform.python_version(),
                   'system': platform.system(), 'machine': platform.machine()}
        require(canonical(environment['runtime']) == canonical(runtime), 'actual bundle runtime changed')
        variables = environment['variables']
        require(type(variables) is dict, 'bundle environment variables must be object')
        for name, value in variables.items():
            require(name and '=' not in name and '\0' not in name and type(value) is str and os.environ.get(name) == value, 'actual bundle environment variable changed')
        items = bundle['inputs']; require(type(items) is list and items, 'bundle sealed inputs missing')
        used = set(); paths = []; kinds = set()
        for item in items:
            data = _bundle_file(root, item, ('kind', 'path', 'sha256', 'executable'), used)
            require(item['kind'] in ('test', 'obligation', 'interface', 'baseline_control') and type(item['kind']) is str, 'unsupported bundle input kind')
            require(type(item['executable']) is bool, 'bundle executable must be boolean')
            path = item['path']; paths.append(path); kinds.add(item['kind'])
            entry = git(root, '--literal-pathspecs', 'ls-tree', '-z', commit, '--', path).split(b'\0')
            require(len(entry) == 2 and entry[1] == b'', 'sealed input missing from baseline Git tree')
            metadata, actual_path = entry[0].split(b'\t', 1); mode, kind, oid = metadata.decode().split()
            require(actual_path.decode() == path and kind == 'blob' and mode in ('100644', '100755'), 'unsafe sealed Git blob/mode')
            require((mode == '100755') is item['executable'] and bool(regular_file(root, path).stat().st_mode & 0o111) is item['executable'], 'sealed executable mode changed')
            require(blobs(root, [oid])[oid] == data, 'sealed input differs from immutable Git blob')
        require(paths == sorted(paths) and kinds == {'test', 'obligation', 'interface', 'baseline_control'}, 'incomplete/noncanonical sealed inputs')
        cases = bundle['required_cases']
        require(type(cases) is list and cases, 'required bundle cases missing')
        for case in cases: _bundle_string(case, 'required case')
        require(cases == sorted(set(cases)), 'duplicate/noncanonical required cases')
        rows = bundle['baseline_evidence']; require(type(rows) is list and len(rows) == len(cases), 'baseline case coverage incomplete')
        seen = set()
        for row in rows:
            _bundle_object(row, ('case', 'operation', 'setup', 'positive', 'red'), 'case proof row')
            case = row['case']; require(type(case) is str and case in cases and case not in seen, 'unknown/duplicate baseline case')
            seen.add(case)
            operation = row['operation']
            _bundle_object(operation, ('target', 'positive_input', 'case_input', 'mutation', 'expected_result'), 'case operation')
            require(operation['target'] == 'verify_acceptance_bundle' and operation['expected_result'] in ('accept', 'reject'), 'unsupported case operation')
            _bundle_string(operation['mutation'], 'case-specific mutation')
            if case == 'independent-handoff': require(operation['expected_result'] == 'accept', 'handoff must expect acceptance')
            if case.startswith('reject-'): require(operation['expected_result'] == 'reject', 'negative case must expect rejection')
            for name in ('positive_input', 'case_input'):
                parse_json(_bundle_file(root, operation[name], ('path', 'sha256'), used))
            require(operation['positive_input']['sha256'] != operation['case_input']['sha256'], 'case input must differ from positive control')
            for stage in ('setup', 'positive', 'red'):
                _bundle_proof(root, row[stage], stage, case, operation, commit, used)
        return True
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, KeyError) as exc:
        raise AssuranceError('bundle observation failed: ' + str(exc)) from exc



def _entry_blob(root, revision, path):
    _bundle_hex(revision, 40, 'entry Git revision'); relative_path(path)
    require(git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip() == revision,
            'entry anchor must be an actual immutable commit')
    rows = git(root, '--literal-pathspecs', 'ls-tree', '-z', revision, '--', path).split(b'\0')
    require(len(rows) == 2 and rows[1] == b'', 'missing entry Git input: ' + path)
    metadata, name = rows[0].split(b'\t', 1); mode, kind, oid = metadata.decode().split()
    require(name.decode() == path and kind == 'blob' and mode in ('100644', '100755'), 'unsafe entry Git input')
    return blobs(root, [oid])[oid], mode == '100755'


def _entry_pinned(root, revision, path, source_path=None):
    data, executable = _entry_blob(root, revision, source_path or path)
    target = regular_file(root, path)
    require(target.read_bytes() == data and bool(target.stat().st_mode & 0o111) == executable,
            'pinned entry bytes/mode changed: ' + path)
    return data


def verify_authorized_entry(repo, entry):
    """Observe approved local active117 authority and exact write intents; never write."""
    try:
        json_value(entry)
        _bundle_object(entry, ('schema_version', 'repository', 'authorization', 'installed', 'contract',
                              'role', 'profile', 'writes'), 'entry')
        require(type(entry['schema_version']) is int and entry['schema_version'] == 1, 'entry schema version')
        supplied = Path(repo); require(not supplied.is_symlink(), 'symlink repository root')
        root = supplied.resolve()
        require(Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() == root, 'entry repository root')
        def read(path): return parse_json(regular_file(root, path).read_bytes())
        ref = entry['contract']; _bundle_object(ref, ('path', 'sha256', 'feature_id'), 'entry contract reference')
        require(ref['path'] == '.agent/contracts/117.json' and ref['feature_id'] == '117', 'canonical entry contract')
        _bundle_hex(ref['sha256'], 64, 'entry contract digest')
        require(sha(regular_file(root, ref['path']).read_bytes()) == ref['sha256'], 'entry contract changed')
        contract = read(ref['path']); approvals = contract['approvals']; policy = contract['gate_reference_policy']
        require(contract['status'] == 'approved' and contract['contract_id'] == contract['feature_id'] == '117', 'active approved117 contract')
        require(approvals['validator_mode_a'] is True and approvals['evaluator_contract_review'] is True, 'dual entry approvals')
        refs = approvals['gate_refs']
        _bundle_object(refs, ('proposal_revision', 'proposal_sha256', 'api_sha256', 'validator_mode_a',
                              'evaluator_contract_review'), 'entry gate references')
        proposal_data, _ = _entry_blob(root, refs['proposal_revision'], ref['path'])
        _bundle_hex(refs['proposal_sha256'], 64, 'proposal digest'); _bundle_hex(refs['api_sha256'], 64, 'API digest')
        require(sha(proposal_data) == refs['proposal_sha256'], 'immutable entry proposal changed')
        proposal = parse_json(proposal_data)
        require(proposal['status'] == 'proposed' and proposal['approvals']['gate_refs'] is None and
                proposal['approvals']['validator_mode_a'] is False and proposal['approvals']['evaluator_contract_review'] is False,
                'entry proposal approval state')
        proposal['status'] = 'approved'
        for key in ('validator_mode_a', 'evaluator_contract_review', 'gate_refs'):
            proposal['approvals'][key] = approvals[key]
        if 'approved_at' in approvals:
            _bundle_string(approvals['approved_at'], 'approval timestamp'); proposal['approvals']['approved_at'] = approvals['approved_at']
        require(canonical(proposal) == canonical(contract), 'unapproved entry obligation change')
        require(type(approvals['revisions']) is int and type(policy['revision']) is int and
                approvals['revisions'] == policy['revision'], 'entry gate revision')
        api_data = _entry_pinned(root, refs['proposal_revision'], contract['api_interface_ref'])
        require(sha(api_data) == refs['api_sha256'], 'entry API proposal binding')
        actors = []
        for role in ('validator_mode_a', 'evaluator_contract_review'):
            gate_ref = refs[role]; _bundle_object(gate_ref, ('path', 'sha256'), 'entry gate reference')
            require(gate_ref['path'] == policy[role]['path'], 'current role gate path')
            _bundle_hex(gate_ref['sha256'], 64, 'gate digest')
            data = regular_file(root, gate_ref['path']).read_bytes(); require(sha(data) == gate_ref['sha256'], 'entry gate changed')
            gate = parse_json(data)
            require(gate['review'] == policy[role]['review'] and gate['feature'] == '117' and
                    type(gate['revision_reviewed']) is int and gate['revision_reviewed'] == approvals['revisions'] and
                    gate['proposal_sha256'] == refs['proposal_sha256'] and gate['api_sha256'] == refs['api_sha256'], 'stale role gate')
            _bundle_string(gate['actor'], 'gate actor'); actors.append(gate['actor'])
            require(gate['final_verdict']['approved'] is True and all(type(gate[k]) is list and not gate[k]
                    for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), 'entry gate blockers')
        require(len(set(actors)) == 2, 'independent entry pre-code gates')
        authority = contract['entry_authority']; auth = entry['authorization']
        _bundle_object(auth, ('path', 'revision', 'sha256'), 'entry authorization')
        require(auth['path'] == authority['authorization_path'] and auth['revision'] == authority['authorization_revision'], 'entry authorization anchor')
        _bundle_hex(auth['sha256'], 64, 'authority digest')
        data = _entry_pinned(root, auth['revision'], auth['path']); require(sha(data) == auth['sha256'], 'entry authority digest changed')
        observed = parse_json(data); _bundle_string(entry['repository'], 'entry project')
        require(entry['repository'] == authority['project'] == observed['project'] and observed['gate'] == 'H-PHASE-017', 'foreign entry authority')
        _bundle_string(observed['operator_text'], 'recorded operator authority')
        require(git(root, 'remote', 'get-url', 'origin').decode().strip() in authority['origins'], 'foreign entry origin')
        pin = authority['installed_pin']; _bundle_object(entry['installed'], ('tag', 'resolved_sha'), 'entry installed pin')
        require(entry['installed'] == {k: pin[k] for k in ('tag', 'resolved_sha')}, 'stale entry pin')
        _bundle_hex(pin['resolved_sha'], 40, 'installed commit')
        require(type(pin['tag']) is str and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', pin['tag']), 'installed tag')
        require(git(root, 'rev-parse', '--verify', 'refs/tags/' + pin['tag'] + '^{commit}').decode().strip() == pin['resolved_sha'], 'actual installed tag changed')
        provenance = read('.nizam/provenance.json')
        _bundle_object(provenance, ('framework_version', 'tag', 'resolved_sha', 'source_url', 'installed_at'), 'bootstrap provenance')
        require(all(provenance[k] == pin[k] for k in ('tag', 'resolved_sha', 'source_url')) and
                provenance['framework_version'] == pin['tag'][1:], 'observed stale installed provenance')
        _bundle_string(provenance['installed_at'], 'installation timestamp')
        critical = ('NIZAM.json', 'tools/SKILL.md', 'standard/AGF.md', 'standard/capability_profiles.md', 'standard/permission_classes.md')
        docs = {path: _entry_pinned(root, pin['resolved_sha'], '.nizam/' + path, path) for path in critical}
        require(parse_json(docs['NIZAM.json'])['framework']['version'] == provenance['framework_version'], 'installed index version')
        pairs = {'Orchestrator': 'orchestrator-primary', 'Planner': 'planner-creative', 'Generator': 'generator-deterministic',
                 'Validator': 'validator-structural', 'Evaluator': 'evaluator-adversarial'}
        for role, profile in pairs.items():
            require(role in docs['standard/AGF.md'].decode() and role in docs['standard/permission_classes.md'].decode() and
                    re.search(r'^\| `' + re.escape(profile) + r'` \|[^\n]*\| ' + role + r' \|', docs['standard/capability_profiles.md'].decode(), re.M), 'installed role/profile routing')
        require(type(entry['role']) is str and entry['role'] in pairs and entry['profile'] == pairs[entry['role']], 'entry role/profile pair')
        state = read('.agent/run_state.json'); features = read('.agent/feature_list_017.json')
        require(state['status'] == 'in_progress' and state['current_feature'] == state['active_contract_id'] == '117' and
                features['phase'] == '017-workflow-assurance-foundation' and features['phase_status'] == 'in_progress', 'entry requires active117')
        selected = [f for f in features['features'] if f['id'] == '117']
        require(len(selected) == 1 and selected[0]['status'] == 'in_progress' and selected[0]['passes'] is False and
                selected[0]['contract_ref'] == ref['path'], 'entry selected117 lifecycle')
        def target(path):
            relative_path(path); result = root
            for index, part in enumerate(path.split('/')):
                result = result / part; require(not result.is_symlink(), 'symlink write-intent path')
                if index < len(path.split('/')) - 1:
                    require(not result.exists() or result.is_dir(), 'non-directory write-intent parent')
            return result
        grants = contract['entry_write_grants']; require(type(grants) is list, 'entry grant list')
        for grant in grants:
            _bundle_object(grant, ('role', 'profile', 'path', 'fields', 'operation', 'full_file', 'create_only'), 'entry write grant')
            require(type(grant['role']) is str and grant['role'] in pairs and grant['profile'] == pairs[grant['role']], 'grant role/profile')
            require(type(grant['full_file']) is bool and type(grant['create_only']) is bool and grant['operation'] in ('write', 'append'), 'grant type/operation')
            path = grant['path']; relative_path(path[:-3] if type(path) is str and path.endswith('/**') else path)
            require('*' not in path or path == '.agent/evidence/117/**', 'unbounded grant path')
            pointers(grant['fields'])
            require((grant['fields'] == [] and grant['operation'] == 'write') if grant['full_file'] else bool(grant['fields']), 'grant field ownership')
        require(type(entry['writes']) is list, 'entry write intents'); seen = set()
        for intent in entry['writes']:
            _bundle_object(intent, ('path', 'fields', 'operation'), 'entry write intent')
            path = intent['path']; destination = target(path); fields = pointers(intent['fields'])
            require(path not in seen and intent['operation'] in ('write', 'append'), 'duplicate/invalid entry write'); seen.add(path)
            matches = []
            for grant in grants:
                pattern = grant['path']; owned = path.startswith(pattern[:-2]) if pattern.endswith('/**') else path == pattern
                if grant['role'] != entry['role'] or grant['profile'] != entry['profile'] or not owned or grant['operation'] != intent['operation']: continue
                if grant['create_only'] and destination.exists(): continue
                if not grant['create_only']: regular_file(root, path)
                if grant['full_file']:
                    if not fields: matches.append(grant)
                elif fields and set(intent['fields']) <= set(grant['fields']): matches.append(grant)
            require(bool(matches), 'unowned entry role/path/field operation')
            if fields:
                record = read(path)
                for parts in fields:
                    value = record
                    for key in parts:
                        require(type(value) is dict and key in value, 'missing owned intent field'); value = value[key]
                    require((parts == ('history',) and intent['operation'] == 'append' and type(value) is list) or
                            (parts != ('history',) and intent['operation'] == 'write' and type(value) not in (dict, list)), 'record intent must name scalar or history append')
        return True
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, KeyError, AttributeError) as exc:
        raise AssuranceError('entry observation failed: ' + str(exc)) from exc


def verify_foundation_ready(repo, prerequisite):
    """Observe candidate-bound current20 proof; readiness never closes a phase."""
    try:
        json_value(prerequisite)
        supplied = Path(repo); require(not supplied.is_symlink(), 'symlink foundation root')
        root = supplied.resolve(strict=True)
        require(Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() == root, 'foundation repository root')
        prefix = '.agent/evidence/118/'
        def read(path): return parse_json(regular_file(root, path).read_bytes())
        candidate = read(prefix + 'source-candidate.json')
        fields = ('revision', 'tree', 'source_sha256', 'runtime_sha256', 'historical_sha256')
        _bundle_object(candidate, fields, 'foundation candidate')
        _bundle_hex(candidate['revision'], 40, 'foundation revision'); _bundle_hex(candidate['tree'], 40, 'foundation tree')
        revision = candidate['revision']
        require(git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip() == revision, 'foundation immutable commit')
        require(git(root, 'rev-parse', revision + '^{tree}').decode().strip() == candidate['tree'], 'foundation actual tree')
        _bundle_object(prerequisite, fields + ('feature', 'actor', 'session_id', 'passed', 'checks_run', 'checks_passed', 'checks'), 'foundation prerequisite')
        require(prerequisite['feature'] == '118' and prerequisite['passed'] is True, 'foundation prerequisite status')
        for key in ('checks_run', 'checks_passed'):
            require(type(prerequisite[key]) is int and prerequisite[key] == 20, 'foundation strict count')
        for key in fields:
            require(canonical(prerequisite[key]) == canonical(candidate[key]), 'foundation candidate binding: ' + key)
        api = read(prefix + 'api-interface.json'); inputs = read(prefix + 'runtime-inputs.json')
        _bundle_object(inputs, ('core_paths', 'runtime_paths', 'roles_ref'), 'foundation runtime manifest')
        core = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', prefix + 'api-interface.json', prefix + 'scope-guard.py']
        require(inputs['core_paths'] == api['core_paths'] == core, 'foundation exact core inputs')
        runtime = inputs['runtime_paths']; require(type(runtime) is list and runtime, 'foundation runtime inputs')
        for path in runtime: relative_path(path)
        require(len(runtime) == len(set(runtime)) and not set(runtime).intersection(core), 'foundation duplicate runtime inputs')
        require(inputs['roles_ref'] == prefix + 'role-sessions.json' and
                {prefix + name for name in ('runtime-inputs.json', 'producer-interface.json', 'historical-runtime-inputs.json', 'role-sessions.json')} <= set(runtime), 'foundation omitted runtime inputs')
        historical = api['historical_paths']
        require(type(historical) is list and len(historical) == len(set(historical)) == 12, 'foundation historical inputs')
        for key, paths, anchor in [('source_sha256', core, revision), ('runtime_sha256', runtime, revision),
                                   ('historical_sha256', historical, api['historical_base'])]:
            _bundle_object(candidate[key], paths, 'foundation digest map')
            for path in paths:
                _bundle_hex(candidate[key][path], 64, 'foundation input digest')
                data = _entry_pinned(root, anchor, path)
                require(sha(data) == candidate[key][path], 'foundation actual input digest: ' + path)
                if key == 'historical_sha256':
                    require(_entry_pinned(root, revision, path) == data, 'foundation historical Source binding')
        ledger = read(prefix + 'historical-runtime-inputs.json')
        _bundle_object(ledger, ('purpose', 'inputs', 'tag', 'tag_revision'), 'foundation historical runtime')
        _bundle_string(ledger['purpose'], 'historical runtime purpose'); _bundle_hex(ledger['tag_revision'], 40, 'historical tag revision')
        require(type(ledger['tag']) is str and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', ledger['tag']), 'historical runtime tag')
        require(git(root, 'rev-parse', '--verify', 'refs/tags/' + ledger['tag'] + '^{commit}').decode().strip() == ledger['tag_revision'], 'historical runtime tag changed')
        require(type(ledger['inputs']) is list and len(ledger['inputs']) == 23, 'historical runtime coverage')
        seen = set()
        for row in ledger['inputs']:
            _bundle_object(row, ('revision', 'path', 'sha256', 'executable'), 'historical runtime input')
            _bundle_hex(row['revision'], 40, 'historical input revision'); relative_path(row['path'])
            identity = (row['revision'], row['path']); require(identity not in seen, 'duplicate historical runtime input'); seen.add(identity)
            _bundle_hex(row['sha256'], 64, 'historical runtime digest')
            data, executable = _entry_blob(root, row['revision'], row['path'])
            require(type(row['executable']) is bool and row['executable'] is executable and sha(data) == row['sha256'], 'historical runtime bytes/mode changed')
        roles = read(inputs['roles_ref']); _bundle_object(roles, ('test_author', 'developer', 'acceptance_reviewer'), 'foundation roles')
        for role in roles.values():
            _bundle_object(role, ('agent_id', 'session_id'), 'foundation role')
            for key in ('agent_id', 'session_id'): _bundle_string(role[key], 'foundation role ' + key)
        for key, supplied_key in [('agent_id', 'actor'), ('session_id', 'session_id')]:
            identities = {role[key] for role in roles.values()}
            _bundle_string(prerequisite[supplied_key], 'foundation prerequisite ' + supplied_key)
            require(len(identities) == 3 and prerequisite[supplied_key] not in identities, 'foundation independent prerequisite identity')
        checks = prerequisite['checks']; cases = api['current_cases']
        require(type(checks) is list and type(cases) is list and len(checks) == len(cases) == 20, 'foundation case coverage')
        used = set(); names = set()
        for row, case in zip(checks, cases):
            _bundle_object(case, ('case', 'command'), 'foundation expected case')
            _bundle_object(row, ('case', 'command', 'exit_code', 'evidence', 'sha256'), 'foundation proof row')
            for key in ('case', 'command'):
                _bundle_string(row[key], 'foundation ' + key); require(row[key] == case[key], 'foundation case/command mismatch')
            require(row['case'] not in names, 'foundation duplicate case'); names.add(row['case'])
            require(type(row['exit_code']) is int and row['exit_code'] == 0, 'foundation strict proof exit')
            path = relative_path(row['evidence']); require(path.startswith(prefix) and path not in used, 'foundation proof path'); used.add(path)
            _bundle_hex(row['sha256'], 64, 'foundation proof digest'); data = regular_file(root, path).read_bytes()
            require(sha(data) == row['sha256'], 'foundation raw proof digest'); text = data.decode('utf-8')
            for name, value in [('COMMAND', row['command']), ('REVISION', revision), ('EXIT', '0')]:
                require(re.findall(r'^' + name + r': (.*)$', text, re.M) == [value], 'foundation unique proof header: ' + name)
            require(text.count('\nSTDOUT:\n') == text.count('\nSTDERR:\n') == 1, 'foundation proof sections')
            output = text.split('\nSTDOUT:\n', 1)[1]
            require('\nSTDERR:\n' in output and bool(output.split('\nSTDERR:\n', 1)[0].strip()), 'foundation stdout diagnostic')
        return True
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, KeyError, AttributeError) as exc:
        raise AssuranceError('foundation observation failed: ' + str(exc)) from exc


def convergent_agf_verdict(ledger, report, *, expected_repository, expected_head_sha):
    """Map a validated converged ledger to a strict AGF verdict without mutation."""
    try:
        import convergent_review as review
    except ModuleNotFoundError as exc:
        if exc.name != 'convergent_review':
            raise
        from tools import convergent_review as review
    try:
        json_value(ledger); json_value(report)
        require(type(ledger) is dict and type(report) is dict, 'AGF inputs must be JSON objects')
        review.validate_ledger(ledger)
        review.validate_repository(expected_repository, 'expected_repository')
        require(type(expected_head_sha) is str and re.fullmatch(r'[0-9a-f]{40}', expected_head_sha),
                'expected_head_sha must be a lowercase forty-hex commit')
        require(ledger['repository'] == expected_repository and ledger['head_sha'] == expected_head_sha,
                'AGF ledger repository/head binding mismatch')
        verdict = report.get('final_verdict')
        require(type(verdict) is dict and type(verdict.get('approved')) is bool,
                'AGF final_verdict.approved must be boolean')
        arrays = ('issues', 'missing_acceptance_coverage', 'unsupported_claims')
        require(all(type(report.get(key)) is list for key in arrays), 'AGF blocking fields must be arrays')
        require('required_fixes' not in report or type(report['required_fixes']) is list,
                'AGF required_fixes must be an array')
        out = {key: copy.deepcopy(report[key]) for key in ('final_verdict',) + arrays}
        out['required_fixes'] = copy.deepcopy(report.get('required_fixes', []))
        out['advisory_minor'] = []
        for finding in ledger['findings']:
            if finding['lifecycle'] not in ('new', 'persisting', 'reopened') or finding['suppression'] is not None:
                continue
            if finding['severity'] == 'minor':
                out['advisory_minor'].append(copy.deepcopy(finding))
            else:
                out['issues'].append(copy.deepcopy(finding))
                out['required_fixes'].append({'fingerprint': finding['fingerprint'],
                    'required_fix': finding['title'] + ': ' + finding['description']})
        out['final_verdict']['approved'] = (verdict['approved'] is True and
            all(not out[key] for key in arrays) and ledger['verdict'] == 'approve')
        return out
    except AssuranceError:
        raise
    except (review.ReviewError, RecursionError) as exc:
        raise AssuranceError('AGF verdict mapping failed: ' + str(exc)) from exc


def _receipt_text(value, label):
    require(type(value) is str and bool(value.strip()), 'receipt nonempty string: ' + label)


def _receipt_ref(root, reference):
    _bundle_object(reference, ('path', 'sha256', 'revision'), 'receipt artifact reference')
    relative_path(reference['path']); _bundle_hex(reference['sha256'], 64, 'receipt artifact digest')
    _bundle_hex(reference['revision'], 40, 'receipt artifact revision')
    require(git(root, 'rev-parse', '--verify', reference['revision'] + '^{commit}').decode().strip() == reference['revision'],
            'receipt artifact exact commit')


def _receipt_artifact(root, reference, live=False):
    _receipt_ref(root, reference)
    data, _ = _entry_blob(root, reference['revision'], reference['path'])
    require(sha(data) == reference['sha256'], 'receipt artifact digest mismatch')
    if live:
        require(regular_file(root, reference['path']).read_bytes() == data, 'receipt current output changed')
    return data


def _receipt_schema(root, value, name):
    import jsonschema
    try:
        jsonschema.Draft202012Validator(parse_json(regular_file(root, 'schema/' + name + '.schema.json').read_bytes())).validate(value)
    except jsonschema.exceptions.ValidationError as exc:
        raise AssuranceError('receipt ' + name + ' schema: ' + exc.message[:240]) from exc


def _receipt_gate(value):
    require(type(value) is dict and type(value.get('final_verdict')) is dict and
            value['final_verdict'].get('approved') is True, 'receipt gate not approved')
    require(all(type(value.get(k)) is list and value[k] == [] for k in
                ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), 'receipt blocking arrays not empty')


def _receipt_producer(value):
    _bundle_object(value, ('agent_id', 'session_id'), 'receipt producer')
    for key in value: _receipt_text(value[key], key)


def _receipt_policy(root, policy):
    json_value(policy)
    _bundle_object(policy, ('schema_version', 'repository', 'feature_id', 'stage', 'operation_id', 'candidate',
        'contract', 'operator', 'producer', 'prerequisites', 'commands', 'from_status', 'to_status', 'at', 'recovery'), 'receipt policy')
    require(type(policy['schema_version']) is int and policy['schema_version'] == 1, 'receipt policy version')
    for key in ('repository', 'feature_id', 'operation_id', 'from_status', 'to_status', 'at'): _receipt_text(policy[key], key)
    minima = {'contract-approved': ('mode-a', 'contract-review'), 'source-ready': ('approved-contract', 'provisional-bundle'),
        'qa-passed': ('mode-b',), 'evidence-captured': ('fresh-qa',), 'feature-complete': ('fresh-qa', 'evidence-capture')}
    require(type(policy['stage']) is str and policy['stage'] in minima, 'receipt unknown stage')
    validate_identity(policy['candidate']); _receipt_producer(policy['producer'])
    for key in ('contract', 'operator'): _receipt_ref(root, policy[key])
    if policy['recovery'] is not None: _receipt_ref(root, policy['recovery'])
    require(type(policy['prerequisites']) is list and type(policy['commands']) is list and policy['commands'], 'receipt required lists')
    return minima[policy['stage']]


def _receipt_candidate(root, candidate, revision=None):
    import errno
    validate_identity(candidate)
    anchor = candidate['source_commit']
    require(git(root, 'rev-parse', '--verify', anchor + '^{commit}').decode().strip() == anchor, 'receipt candidate exact commit')
    require(git(root, 'rev-parse', anchor + '^{tree}').decode().strip() == candidate['source_tree'], 'receipt candidate actual tree')
    revision = revision or git(root, 'rev-parse', 'HEAD').decode().strip()
    _bundle_hex(revision, 40, 'receipt executed revision')
    require(git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip() == revision, 'receipt executed exact commit')
    git(root, 'merge-base', '--is-ancestor', anchor, revision)
    require(git(root, 'remote', 'get-url', 'origin').decode().strip() == candidate['repository'], 'receipt actual repository')
    ownership = candidate['record_ownership']
    protected = [entry for category in ('source', 'tests', 'tools') for entry in candidate['assessed_inputs'][category]]
    paths = {anchor: {entry['path'] for entry in candidate['assessed_inputs']['contracts']} | set(ownership)}
    for commit in (anchor, revision):
        paths.setdefault(commit, set()).update(entry['path'] for entry in protected)
    entries = {}
    for commit, requested in paths.items():
        chunks = []; chunk = []; size = 0
        for path in sorted(requested):
            cost = len(os.fsencode(path)) + 9
            if chunk and size + cost > 32768:
                chunks.append(chunk); chunk = []; size = 0
            chunk.append(path); size += cost
        if chunk: chunks.append(chunk)
        pending = list(reversed(chunks))
        observed = set()
        while pending:
            chunk = pending.pop()
            try:
                rows = git(root, '--literal-pathspecs', 'ls-tree', '-z', commit, '--', *chunk).split(b'\0')
            except AssuranceError as exc:
                if isinstance(exc.__cause__, OSError) and exc.__cause__.errno == errno.E2BIG and len(chunk) > 1:
                    middle = len(chunk) // 2
                    pending.extend((chunk[middle:], chunk[:middle])); continue
                raise
            require(rows[-1] == b'', 'unsafe entry Git input')
            selected = set(chunk)
            for row in rows[:-1]:
                metadata, name = row.split(b'\t', 1); mode, kind, oid = metadata.decode().split()
                path = name.decode()
                require(path in selected and path not in observed and kind == 'blob' and mode in ('100644', '100755'),
                        'unsafe entry Git input')
                observed.add(path); entries[commit, path] = (oid, mode == '100755')
        for path in sorted(requested):
            require(path in observed, 'missing entry Git input: ' + path)
    values = blobs(root, [oid for oid, executable in entries.values()])
    for category in ('source', 'tests', 'tools'):
        for entry in candidate['assessed_inputs'][category]:
            for commit in (anchor, revision):
                oid, executable = entries[commit, entry['path']]; data = values[oid]
                require(sha(data) == entry['sha256'] and executable is entry['executable'], 'receipt protected Git input changed')
            target = regular_file(root, entry['path'])
            require(sha(target.read_bytes()) == entry['sha256'] and bool(target.stat().st_mode & 0o111) is entry['executable'],
                    'receipt protected current input changed')
    for entry in candidate['assessed_inputs']['contracts']:
        oid, executable = entries[anchor, entry['path']]; data = values[oid]
        digest = sha(canonical(parse_json(data))) if entry['path'] in ownership else sha(data)
        require(digest == entry['sha256'] and executable is entry['executable'], 'receipt contract assessed digest')
        if entry['path'] not in ownership:
            require(regular_file(root, entry['path']).read_bytes() == data, 'receipt unowned contract changed')
    for path, fields in ownership.items():
        oid, executable = entries[anchor, path]; data = values[oid]; target = regular_file(root, path)
        require(bool(target.stat().st_mode & 0o111) is executable, 'receipt record mode changed')
        verify_record_update(parse_json(data), parse_json(target.read_bytes()), fields)
    environment = {'runtime': {'implementation': platform.python_implementation(), 'version': platform.python_version(),
        'system': platform.system(), 'machine': platform.machine()},
        'variables': {key: os.environ.get(key) for key in candidate['environment']['variables']}}
    require(canonical(environment) == canonical(candidate['environment']), 'receipt observed environment changed')


def _receipt_contract(root, value, feature):
    _receipt_schema(root, value, 'contract')
    require(value['contract_id'] == value['feature_id'] == feature and value['status'] == 'approved', 'receipt approved contract binding')
    approvals = value.get('approvals', {})
    require(approvals.get('validator_mode_a') is True and approvals.get('evaluator_contract_review') is True, 'receipt dual approvals')


def _receipt_prerequisites(root, policy, minimum):
    entries = policy['prerequisites']; seen = set(); current = set(); records = []
    kinds = ('mode-a', 'contract-review', 'approved-contract', 'provisional-bundle', 'mode-b', 'fresh-qa', 'evidence-capture')
    for entry in entries:
        _bundle_object(entry, ('kind', 'artifact', 'feature_id', 'assessed_revision', 'contract_sha256'), 'receipt prerequisite')
        require(type(entry['kind']) is str and entry['kind'] in kinds, 'receipt prerequisite kind')
        _receipt_text(entry['feature_id'], 'prerequisite feature')
        _bundle_hex(entry['assessed_revision'], 40, 'prerequisite revision'); _bundle_hex(entry['contract_sha256'], 64, 'prerequisite contract')
        require(git(root, 'rev-parse', '--verify', entry['assessed_revision'] + '^{commit}').decode().strip() == entry['assessed_revision'],
                'receipt prerequisite actual revision')
        identity = (entry['kind'], entry['feature_id'])
        require(identity not in seen, 'receipt duplicate prerequisite'); seen.add(identity)
        if entry['feature_id'] == policy['feature_id']: current.add(entry['kind'])
        value = parse_json(_receipt_artifact(root, entry['artifact'])); kind = entry['kind']
        feature, revision, digest = entry['feature_id'], entry['assessed_revision'], entry['contract_sha256']
        if kind == 'approved-contract':
            _receipt_contract(root, value, feature)
            require(entry['artifact']['sha256'] == digest and entry['artifact']['revision'] == revision, 'receipt approved contract entry')
        elif kind == 'evidence-capture':
            require(value.get('role') == 'Root' and value.get('feature') == feature and value.get('revision') == revision and
                value.get('approved_contract_sha256') == digest and value.get('passed') is True and
                type(value.get('actual_exit')) is int and value['actual_exit'] == 0, 'receipt evidence capture predicate')
        else:
            _receipt_gate(value)
            fields = {'mode-a': ('feature', 'reviewed_commit', 'contract_sha256'),
                'contract-review': ('feature', 'reviewed_revision', 'proposal_sha256'),
                'provisional-bundle': ('feature_id', 'reviewed_revision', 'approved_contract_sha256'),
                'mode-b': ('feature', 'reviewed_commit', 'approved_contract_sha256'),
                'fresh-qa': ('feature_id', 'reviewed_revision', 'approved_contract_sha256')}[kind]
            require(tuple(value.get(k) for k in fields) == (feature, revision, digest), 'receipt prerequisite binding')
            if kind == 'contract-review':
                _receipt_schema(root, value, 'contract_review'); require(value.get('contract_id') == feature, 'receipt contract-review identity')
                who = value.get('reviewer', value.get('actor')); _receipt_text(who, 'contract reviewer')
                if 'reviewer' in value and 'actor' in value: require(value['reviewer'] == value['actor'], 'receipt ambiguous reviewer')
            elif kind == 'fresh-qa':
                _receipt_schema(root, value, 'qa_verdict')
                require(value.get('qa_pass') is True and type(value.get('checks_run')) is int and value['checks_run'] > 0 and
                    type(value.get('checks_passed')) is int and value['checks_passed'] == value['checks_run'] and
                    type(value.get('adversarial')) is dict and value['adversarial'].get('performed') is True, 'receipt fresh QA predicate')
            else: _receipt_text(value.get('reviewer'), 'prerequisite reviewer')
        records.append((entry, value))
    require(set(minimum) <= current, 'receipt missing current prerequisite')
    contract = parse_json(_receipt_artifact(root, policy['contract'])); _receipt_contract(root, contract, policy['feature_id'])
    contracts = [(contract, policy['contract'], policy['feature_id'])] + [(v, e['artifact'], e['feature_id']) for e, v in records if e['kind'] == 'approved-contract']
    for value, reference, feature in contracts:
        evidence = value.get('approval_evidence', {}); reviewers = []
        _bundle_hex(evidence.get('proposal_sha256'), 64, 'receipt proposal digest')
        for kind, key in (('mode-a', 'mode_a'), ('contract-review', 'contract_review')):
            matches = [(e, v) for e, v in records if e['kind'] == kind and e['feature_id'] == feature and
                e['artifact']['path'] == evidence.get(key) and e['contract_sha256'] == evidence['proposal_sha256']]
            require(len(matches) == 1, 'receipt missing bound dual approval')
            e, v = matches[0]; reviewers.append(v.get('reviewer', v.get('actor')))
        require(reviewers[0] != reviewers[1], 'receipt independent contract reviewers')


def _receipt_operator(root, policy):
    app = parse_json(_receipt_artifact(root, policy['operator']))
    _bundle_object(app, ('schema_version', 'role', 'repository', 'feature_id', 'stage', 'candidate_sha256',
        'approved', 'authority_ref', 'owner', 'gate', 'scope'), 'receipt operator application')
    require(type(app['schema_version']) is int and app['schema_version'] == 1 and app['role'] == 'Root' and
        app['approved'] is True, 'receipt operator decision')
    for key in ('repository', 'feature_id', 'stage'): require(app[key] == policy[key], 'receipt operator target')
    require(app['candidate_sha256'] == sha(canonical(policy['candidate'])), 'receipt operator candidate')
    authority = parse_json(_receipt_artifact(root, app['authority_ref']))
    for key in ('operator_instruction_verbatim', 'owner', 'gate'): _receipt_text(authority.get(key), 'operator authority ' + key)
    require(app['owner'] == authority['owner'] and app['gate'] == authority['gate'], 'receipt actual operator owner/gate')
    require(authority.get('repository') in (policy['repository'], policy['repository'] + ' only'), 'receipt authority repository')
    scope = app['scope']; keys = ('phase', 'features', 'original_estimate_lines', 'ceiling_130pct')
    _bundle_object(scope, keys, 'receipt operator scope'); _receipt_text(scope['phase'], 'operator phase')
    require(type(scope['features']) is list and scope['features'] and all(type(x) is str and x.strip() for x in scope['features']) and
        len(set(scope['features'])) == len(scope['features']) and policy['feature_id'] in scope['features'], 'receipt scope features')
    require(all(type(scope[k]) is int and scope[k] >= 0 for k in keys[2:]) and
        scope['ceiling_130pct'] >= scope['original_estimate_lines'], 'receipt scope budget')
    require(type(authority.get('scope')) is dict and canonical(scope) == canonical({k: authority['scope'].get(k) for k in keys}),
            'receipt actual authority scope')


def verify_stage_receipt(repo, receipt, *, policy):
    """Validate trusted-policy receipt bindings and actual captures without executing commands."""
    try:
        root = Path(repo); require(not root.is_symlink(), 'receipt symlink repository'); root = root.resolve(strict=True)
        require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'receipt repository toplevel')
        minimum = _receipt_policy(root, policy); json_value(receipt)
        _bundle_object(receipt, ('schema_version', 'repository', 'feature_id', 'stage', 'operation_id', 'status', 'candidate',
            'producer', 'contract_ref', 'operator_ref', 'prerequisites', 'checks', 'verdict'), 'receipt')
        require(type(receipt['schema_version']) is int and receipt['schema_version'] == 1 and receipt['status'] == 'passed', 'receipt not passed')
        for key in ('repository', 'feature_id', 'stage', 'operation_id', 'producer', 'prerequisites'):
            require(canonical(receipt[key]) == canonical(policy[key]), 'receipt expected binding: ' + key)
        require(canonical(receipt['contract_ref']) == canonical(policy['contract']) and
            canonical(receipt['operator_ref']) == canonical(policy['operator']), 'receipt authority refs')
        require(compare_identity(receipt['candidate'], policy['candidate']), 'receipt candidate identity mismatch')
        require(policy['candidate']['repository'] == policy['repository'], 'receipt candidate repository binding')
        _receipt_candidate(root, policy['candidate']); _receipt_operator(root, policy); _receipt_prerequisites(root, policy, minimum)
        _bundle_object(receipt['verdict'], ('final_verdict', 'issues', 'missing_acceptance_coverage', 'unsupported_claims'), 'receipt verdict')
        _receipt_gate(receipt['verdict'])
        require(type(receipt['checks']) is list and len(receipt['checks']) == len(policy['commands']), 'receipt command coverage')
        seen = set()
        for command, check in zip(policy['commands'], receipt['checks']):
            _bundle_object(command, ('argv', 'expected_exit', 'proof_kind', 'diagnostic', 'capture'), 'receipt command policy')
            require(type(command['argv']) is list and command['argv'] and all(type(x) is str and x for x in command['argv']), 'receipt command argv')
            signature = canonical(command['argv']); require(signature not in seen, 'receipt duplicate command'); seen.add(signature)
            require(type(command['expected_exit']) is int and command['expected_exit'] == 0 and
                command['proof_kind'] in ('success', 'semantic-negative'), 'receipt expected success policy')
            _receipt_text(command['diagnostic'], 'receipt diagnostic')
            require('\n' not in command['diagnostic'] and '\r' not in command['diagnostic'], 'receipt diagnostic single line')
            _bundle_object(check, ('argv', 'executed', 'outcome', 'exit_code', 'stdout', 'stderr', 'capture'), 'receipt check')
            require(canonical(check['capture']) == canonical(command['capture']), 'receipt independent capture pin')
            capture = parse_json(_receipt_artifact(root, command['capture']))
            _bundle_object(capture, ('schema_version', 'argv', 'cwd', 'revision', 'candidate_sha256', 'environment', 'producer',
                'executed', 'outcome', 'exit_code', 'stdout', 'stderr'), 'receipt actual capture')
            require(type(capture['schema_version']) is int and capture['schema_version'] == 1, 'receipt capture version')
            _receipt_text(capture['cwd'], 'capture cwd'); _receipt_producer(capture['producer'])
            require(canonical(capture['producer']) == canonical(policy['producer']) and
                capture['candidate_sha256'] == sha(canonical(policy['candidate'])) and
                canonical(capture['environment']) == canonical(policy['candidate']['environment']), 'receipt capture producer/candidate/environment')
            _receipt_candidate(root, policy['candidate'], capture['revision'])
            for actual in (capture, check):
                require(actual['executed'] is True and type(actual['exit_code']) is int and actual['exit_code'] == 0 and
                    actual['outcome'] == command['proof_kind'] and canonical(actual['argv']) == canonical(command['argv']),
                    'receipt actual command did not pass')
            output = []
            for key in ('stdout', 'stderr'):
                require(canonical(check[key]) == canonical(capture[key]), 'receipt actual output reference')
                output.append(_receipt_artifact(root, capture[key], live=True).decode('utf-8'))
            require(command['diagnostic'] in '\n'.join(output).splitlines(), 'receipt expected actual diagnostic missing')
        return copy.deepcopy(receipt)
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise AssuranceError('receipt validation failed: ' + str(exc)[:400]) from exc


def plan_receipt_transition(repo, state, receipt, *, policy):
    """Propose one owned transition, identical replay, or explicit missing-receipt recovery."""
    try:
        root = Path(repo).resolve(strict=True); _receipt_policy(root, policy); json_value(state)
        _receipt_schema(root, state, 'run_state')
        require(state['repository'] == policy['repository'], 'receipt transition repository')
        recovering = receipt is None
        if recovering:
            reference = policy['recovery']
            if reference is None or not git(root, '--literal-pathspecs', 'ls-tree', '-z', reference['revision'], '--', reference['path']):
                return {'action': 'rerun-required', 'state': copy.deepcopy(state), 'receipt': None, 'reason': 'Receipt proof is missing; rerun is required.'}
            receipt = parse_json(_receipt_artifact(root, reference))
        verified = verify_stage_receipt(root, receipt, policy=policy)
        digest = sha(canonical(verified)); operation = policy['operation_id']
        event = {'at': policy['at'], 'event': 'wa-receipt-transition',
            'detail': 'Receipt ' + operation + ' advanced ' + policy['feature_id'] + ':' + policy['stage'] + ' (' + digest + ')',
            'operation_id': operation, 'feature_id': policy['feature_id'], 'stage': policy['stage'],
            'candidate_sha256': sha(canonical(policy['candidate'])), 'receipt_sha256': digest}
        matches = [e for e in state['history'] if e.get('event') == 'wa-receipt-transition' and e.get('operation_id') == operation]
        if matches:
            require(len(matches) == 1 and canonical(matches[0]) == canonical(event) and state['status'] == policy['to_status'],
                    'receipt conflicting or duplicate advancement')
            action, reason = 'noop', 'Identical receipt transition is already recorded.'
            after = copy.deepcopy(state)
        else:
            require(state['status'] == policy['from_status'], 'receipt transition source status')
            action, reason = 'advance', 'Verified receipt proposes one owned transition.'
            after = copy.deepcopy(state)
            if not recovering:
                after['status'] = policy['to_status']; after['updated_at'] = policy['at']; after['history'].append(event)
        if recovering:
            action, reason = 'republish', 'Verified original receipt may be republished; no state transition occurred.'
            after = copy.deepcopy(state)
        verify_record_update(state, after, ['/status', '/updated_at', '/history']); _receipt_schema(root, after, 'run_state')
        return {'action': action, 'state': after, 'receipt': verified, 'reason': reason}
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise AssuranceError('receipt transition failed: ' + str(exc)[:400]) from exc


def _lane_path(value):
    require(type(value) is str and Path(value).is_absolute(), 'lane absolute path required')
    path = Path(value).resolve(strict=True)
    require(str(path) == value and path.is_dir(), 'lane noncanonical or symlink directory')
    return path


def _lane_shape(root, request):
    _bundle_object(request, ('operation_id', 'feature_id', 'owner', 'agent_role', 'step_key', 'attempt',
        'base_revision', 'attempt_root', 'writes', 'state_fields'), 'lane request')
    for key in ('operation_id', 'feature_id', 'agent_role', 'step_key'): _receipt_text(request[key], key)
    _receipt_producer(request['owner'])
    require(type(request['attempt']) is int and 1 <= request['attempt'] <= 3, 'lane attempt outside max3')
    _bundle_hex(request['base_revision'], 40, 'lane immutable base')
    require(git(root, 'rev-parse', '--verify', request['base_revision'] + '^{commit}').decode().strip() == request['base_revision'], 'lane actual base')
    _lane_path(request['attempt_root'])
    writes = request['writes']; require(type(writes) is list and writes, 'lane writes required')
    for path in writes: relative_path(path)
    require(len(set(writes)) == len(writes), 'lane duplicate writes'); pointers(request['state_fields'])


def _lane_file(root, reference, live=False):
    data = _receipt_artifact(root, reference, live=live)
    if live:
        _, executable = _entry_blob(root, reference['revision'], reference['path'])
        require(bool(regular_file(root, reference['path']).stat().st_mode & 0o111) is executable, 'lane snapshot mode changed')
    return parse_json(data)


def _lane_record(root, reference, request, failure=False):
    value = _lane_file(root, reference, live=True); flag = 'captured' if failure else 'released'
    keys = ('operation_id', 'feature_id', 'owner', 'attempt', 'base_revision', 'attempt_root')
    _bundle_object(value, ('schema_version', 'role', *keys, flag, 'actual_exit'), 'lane evidence')
    require(type(value['schema_version']) is int and value['schema_version'] == 1 and value['role'] == 'Orchestrator' and
        value[flag] is True and type(value['actual_exit']) is int and
        (value['actual_exit'] != 0 if failure else value['actual_exit'] == 0), 'lane evidence not verified')
    require(all(canonical(value[k]) == canonical(request[k]) for k in keys), 'lane evidence ownership mismatch')


def _lane_assessment(repo, request, policy):
    json_value(request); json_value(policy); root = _lane_path(str(repo))
    require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'lane coordinator toplevel')
    _bundle_object(policy, ('repository', 'coordination_ref', 'feature_list_ref', 'authority_ref', 'attempt_parent', 'rollback_ref'), 'lane policy')
    require(git(root, 'remote', 'get-url', 'origin').decode().strip() == policy['repository'], 'lane actual repository')
    _lane_shape(root, request); target = _lane_path(request['attempt_root']); parent = _lane_path(policy['attempt_parent'])
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir').decode().strip()).resolve(strict=True)
    require(parent != root and not parent.is_relative_to(root) and not parent.is_relative_to(common), 'lane unsafe attempt parent')
    require(target != parent and target.is_relative_to(parent) and not any(target.is_relative_to(p) or p.is_relative_to(target)
        for p in (root, common)), 'lane unsafe attempt root')
    authority = _lane_file(root, policy['authority_ref'])
    _bundle_object(authority, (*request, 'schema_version', 'role', 'repository', 'approved', 'contract_ref'), 'lane authority')
    require(type(authority['schema_version']) is int and authority['schema_version'] == 1 and authority['role'] == 'Orchestrator' and
        authority['repository'] == policy['repository'] and authority['approved'] is True, 'lane authority not approved')
    require(all(canonical(authority[k]) == canonical(v) for k, v in request.items()), 'lane request outside dispatch')
    _receipt_contract(root, _lane_file(root, authority['contract_ref']), request['feature_id'])
    state = _lane_file(root, policy['coordination_ref'], live=True); features = _lane_file(root, policy['feature_list_ref'], live=True)
    _receipt_schema(root, state, 'run_state'); _receipt_schema(root, features, 'feature_list')
    require(state['repository'] == policy['repository'] and state['current_feature'] == request['feature_id'] and
        state.get('active_contract_id', request['feature_id']) == request['feature_id'] and state['status'] == 'in_progress' and
        features['phase'] == state['current_phase'], 'lane coordination binding')
    rows = features['features']; ids = [r['id'] for r in rows]
    require(len(set(ids)) == len(ids), 'lane duplicate feature'); selected = [r for r in rows if r['id'] == request['feature_id']]
    require(len(selected) == 1 and selected[0]['status'] == 'in_progress', 'lane selected feature inactive')
    for dependency in selected[0]['dependencies']:
        matches = [r for r in rows if r['id'] == dependency]
        require(len(matches) == 1 and (matches[0]['status'] == 'cancelled' or
            (matches[0]['status'] == 'complete' and matches[0]['passes'] is True)), 'lane dependency not satisfied')
    counter = state['circuit_breaker'].get(request['step_key'])
    require(type(counter) is dict and type(counter.get('attempts')) is int and counter['attempts'] == request['attempt'] and
        type(counter.get('limit')) is int and counter['limit'] == 3, 'lane counter allocation mismatch')
    lanes = state.get('execution_lanes'); require(type(lanes) is list, 'lane coordination inventory missing')
    seen = set(); conflicts = []
    for lane in lanes:
        _bundle_object(lane, (*request, 'status', 'terminal_ref'), 'coordinated lane')
        bound = {k: lane[k] for k in request}; _lane_shape(root, bound)
        require(lane['operation_id'] not in seen, 'lane duplicate operation'); seen.add(lane['operation_id'])
        require(lane['status'] in ('reserved', 'running', 'invalidated', 'released'), 'lane invalid status')
        if lane['status'] == 'released': _lane_record(root, lane['terminal_ref'], bound)
        else: require(lane['terminal_ref'] is None, 'lane premature terminal proof')
        if lane['operation_id'] == request['operation_id']:
            require(canonical(bound) == canonical(request), 'lane conflicting operation identity'); continue
        if lane['status'] == 'released': continue
        paths = any(a == b or a.startswith(b + '/') or b.startswith(a + '/') for a in request['writes'] for b in lane['writes'])
        fields = any(a[:len(b)] == b or b[:len(a)] == a for a in pointers(request['state_fields']) for b in pointers(lane['state_fields']))
        if paths or fields: conflicts.append(lane['operation_id'])
    return {'eligible': not conflicts, 'conflicts': conflicts, 'operation_id': request['operation_id']}


def assess_conflict_lanes(repo, request, *, policy):
    """Assess trusted current coordination; this does not reserve a lane."""
    try:
        return _lane_assessment(repo, request, policy)
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        raise AssuranceError('lane assessment failed: ' + str(exc)[:300]) from exc


def _lane_worktrees(root):
    records = []
    for record in git(root, 'worktree', 'list', '--porcelain', '-z').split(b'\0\0'):
        if record:
            records.append(dict(field.decode().partition(' ')[::2] for field in record.split(b'\0') if field))
    return records


def _lane_inventory(target, base, head):
    def tree(revision):
        result = {}
        for row in git(target, 'ls-tree', '-rz', revision).split(b'\0'):
            if row:
                metadata, path = row.split(b'\t', 1); mode, kind, oid = metadata.decode().split(); path = path.decode(); relative_path(path)
                require(kind == 'blob' and mode in ('100644', '100755'), 'lane unsafe tree entry'); result[path] = (mode, oid)
        return result
    original, committed = tree(base), tree(head); staged = {}
    for row in git(target, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            metadata, path = row.split(b'\t', 1); mode, oid, stage = metadata.decode().split(); path = path.decode(); relative_path(path)
            require(stage == '0' and mode in ('100644', '100755') and path not in staged, 'lane unsafe or unmerged index')
            staged[path] = (mode, oid)
    others = git(target, 'ls-files', '--others', '--exclude-standard', '-z') + git(target, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z')
    paths = set(original) | set(committed) | set(staged) | {p.decode() for p in others.split(b'\0') if p}
    objects = blobs(target, [oid for mapping in (original, committed, staged) for mode, oid in mapping.values()])
    changes = []
    for path in sorted(paths):
        relative_path(path); current = target
        for part in path.split('/'):
            current = current / part; require(not current.is_symlink(), 'lane symlink attempt entry')
        value = None
        if current.exists():
            current = regular_file(target, path); value = ('100755' if current.stat().st_mode & 0o111 else '100644', current.read_bytes())
        versions = [None if path not in m else (m[path][0], objects[m[path][1]]) for m in (original, committed, staged)] + [value]
        if any(v != versions[0] for v in versions[1:]): changes.append(path)
    return changes


def verify_isolated_attempt(repo, request, *, policy):
    """Observe a registered detached attempt and every actual changed path."""
    try:
        require(assess_conflict_lanes(repo, request, policy=policy)['eligible'], 'lane ownership conflict')
        root = _lane_path(str(repo)); target = _lane_path(request['attempt_root'])
        records = [r for r in _lane_worktrees(root) if r.get('worktree') == str(target)]
        require(len(records) == 1 and 'detached' in records[0] and 'branch' not in records[0], 'lane detached registration required')
        require(git(target, 'rev-parse', '--show-toplevel').decode().strip() == str(target), 'lane attempt actual toplevel')
        common = lambda p: git(p, 'rev-parse', '--path-format=absolute', '--git-common-dir').decode().strip()
        require(common(root) == common(target), 'lane foreign Git repository')
        head = git(target, 'rev-parse', 'HEAD').decode().strip(); git(target, 'merge-base', '--is-ancestor', request['base_revision'], head)
        changes = _lane_inventory(target, request['base_revision'], head)
        require(set(changes) <= set(request['writes']), 'lane unowned attempt changes')
        return {'operation_id': request['operation_id'], 'attempt': request['attempt'], 'base_revision': request['base_revision'],
            'attempt_root': str(target), 'head_revision': head, 'owned_changes': changes}
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        raise AssuranceError('lane isolation failed: ' + str(exc)[:300]) from exc


def rollback_owned_attempt(repo, request, *, policy):
    """Remove exactly one owned attempt after external failure capture; never terminate processes."""
    try:
        first = verify_isolated_attempt(repo, request, policy=policy); root = _lane_path(str(repo))
        require(policy['rollback_ref'] is not None, 'lane captured failure required')
        _lane_record(root, policy['rollback_ref'], request, failure=True)
        require(first == verify_isolated_attempt(repo, request, policy=policy), 'lane attempt changed before rollback')
        git(root, 'worktree', 'remove', '--force', request['attempt_root'])
        require(not Path(request['attempt_root']).exists() and not any(r.get('worktree') == request['attempt_root'] for r in _lane_worktrees(root)),
                'lane rollback removal incomplete')
        return {'operation_id': request['operation_id'], 'attempt_root': request['attempt_root'], 'removed': True}
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        raise AssuranceError('lane rollback failed: ' + str(exc)[:300]) from exc


def _failure_continuity(root, request, policy, authority):
    anchor = _lane_file(root, authority['coordination_ref'])
    current = _lane_file(root, policy['coordination_ref'], live=True)
    for state in (anchor, current):
        _receipt_schema(root, state, 'run_state')
        require(state['repository'] == policy['repository'] and state['current_feature'] == request['feature_id'] and
            state.get('active_contract_id', request['contract_id']) == request['contract_id'] and
            state['status'] == 'in_progress', 'failure coordination identity')
        require(type(state['history']) is list, 'failure history list')
        if 'execution_lanes' in state:
            require(type(state['execution_lanes']) is list, 'failure lane inventory list')
        counter = state['circuit_breaker'].get(request['step_key'])
        require(type(counter) is dict and type(counter.get('attempts')) is int and
            counter['attempts'] == request['attempt'] and type(counter.get('limit')) is int and
            counter['limit'] == 3, 'failure counter allocation mismatch')
    require(anchor['current_phase'] == current['current_phase'], 'failure phase changed')
    require(('execution_lanes' in anchor) == ('execution_lanes' in current) and
        canonical(anchor.get('execution_lanes')) == canonical(current.get('execution_lanes')), 'failure lanes changed')
    owned = ['/history']
    if 'updated_at' in anchor:
        require(type(anchor['updated_at']) is str and type(current.get('updated_at')) is str, 'failure timestamp type')
        owned.append('/updated_at')
    verify_record_update(anchor, current, owned)


def _failure_rejection(root, reference):
    verdict = _lane_file(root, reference)
    try:
        _receipt_schema(root, verdict, 'contract_review')
    except AssuranceError:
        _receipt_schema(root, verdict, 'qa_verdict')
    arrays = ('issues', 'missing_acceptance_coverage', 'unsupported_claims')
    require(all(type(verdict[key]) is list for key in arrays if key in verdict), 'failure semantic array shape')
    rejected = False
    if 'final_verdict' in verdict:
        require(type(verdict['final_verdict']) is dict and
            type(verdict['final_verdict'].get('approved')) is bool, 'failure semantic approval shape')
        rejected = verdict['final_verdict']['approved'] is False
    require(rejected or any(verdict.get(key, []) for key in arrays), 'failure semantic verdict passed')


def route_failed_attempt(repo, request, *, policy):
    """Propose a cause route from independently selected failed evidence; never retry or write state."""
    try:
        json_value(request); json_value(policy)
        root = _lane_path(str(repo))
        require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'failure repository toplevel')
        keys = ('operation_id', 'contract_id', 'feature_id', 'step_key', 'attempt', 'stage', 'cause')
        _bundle_object(request, keys, 'failure request')
        for key in ('operation_id', 'contract_id', 'feature_id', 'step_key', 'stage'):
            _receipt_text(request[key], 'failure ' + key)
        require(request['contract_id'] == request['feature_id'], 'failure contract identity')
        require(type(request['attempt']) is int and 1 <= request['attempt'] <= 3, 'failure attempt outside max3')
        require(type(request['cause']) is str and request['cause'] in ('infrastructure', 'semantic'), 'failure cause')
        _bundle_object(policy, ('repository', 'coordination_ref', 'authority_ref'), 'failure policy')
        require(git(root, 'remote', 'get-url', 'origin').decode().strip() == policy['repository'], 'failure actual repository')
        authority = _lane_file(root, policy['authority_ref'])
        _bundle_object(authority, (*keys, 'schema_version', 'role', 'repository', 'approved', 'contract_ref',
            'coordination_ref', 'candidate', 'producer', 'capture_ref', 'evidence_ref'), 'failure authority')
        require(type(authority['schema_version']) is int and authority['schema_version'] == 1 and
            authority['role'] == 'Orchestrator' and authority['approved'] is True and
            authority['repository'] == policy['repository'], 'failure authority not approved')
        require(all(canonical(authority[key]) == canonical(request[key]) for key in keys), 'failure request outside authority')
        _receipt_contract(root, _lane_file(root, authority['contract_ref']), request['feature_id'])
        _receipt_producer(authority['producer']); _receipt_candidate(root, authority['candidate'])
        _failure_continuity(root, request, policy, authority)
        capture = _lane_file(root, authority['capture_ref'])
        _bundle_object(capture, ('schema_version', 'argv', 'cwd', 'revision', 'candidate_sha256', 'environment',
            'producer', 'executed', 'outcome', 'exit_code', 'stdout', 'stderr'), 'failure capture')
        require(type(capture['schema_version']) is int and capture['schema_version'] == 1 and
            capture['executed'] is True and type(capture['exit_code']) is int and capture['exit_code'] != 0 and
            capture['outcome'] == request['cause'] + '-failed', 'failure capture is not actual failed outcome')
        require(type(capture['argv']) is list and capture['argv'] and
            all(type(arg) is str and arg for arg in capture['argv']), 'failure capture argv')
        _receipt_text(capture['cwd'], 'failure capture cwd'); _receipt_producer(capture['producer'])
        require(canonical(capture['producer']) == canonical(authority['producer']) and
            capture['candidate_sha256'] == sha(canonical(authority['candidate'])) and
            canonical(capture['environment']) == canonical(authority['candidate']['environment']), 'failure capture bindings')
        _receipt_candidate(root, authority['candidate'], capture['revision'])
        for stream in ('stdout', 'stderr'):
            reference = capture[stream]
            data = _receipt_artifact(root, reference, live=True)
            _, executable = _entry_blob(root, reference['revision'], reference['path'])
            require(bool(regular_file(root, reference['path']).stat().st_mode & 0o111) is executable,
                'failure output mode changed')
            data.decode('utf-8')
        evidence = _lane_file(root, authority['evidence_ref'])
        _bundle_object(evidence, ('schema_version', 'kind', 'reason', 'capture_ref', 'verdict_ref'), 'failure evidence')
        require(type(evidence['schema_version']) is int and evidence['schema_version'] == 1 and
            evidence['kind'] == request['cause'], 'failure evidence classification')
        require(type(evidence['reason']) is str and bool(evidence['reason'].strip()) and
            len(evidence['reason']) <= 400, 'failure evidence reason')
        require(canonical(evidence['capture_ref']) == canonical(authority['capture_ref']), 'failure evidence capture mismatch')
        if request['cause'] == 'infrastructure':
            require(evidence['verdict_ref'] is None, 'failure infrastructure verdict must be null')
        else:
            _failure_rejection(root, evidence['verdict_ref'])
        attempt = request['attempt']
        return copy.deepcopy(dict(request, outcome='failed', route='halt' if attempt == 3 else
            request['cause'] + ('-diagnosis' if request['cause'] == 'infrastructure' else '-repair'),
            attempts_used=attempt, limit=3, remaining=3-attempt, capture_ref=authority['capture_ref']))
    except (AssuranceError, OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        raise AssuranceError('failure routing invalid: ' + str(exc)[:800]) from exc


# Feature123 composes the existing engines; archived hosted validation is read-only.
_WA123_ORIGIN = 'https://github.com/niq-cnr/nizam-framework.git'
_WA123_REPOSITORY = 'niq-cnr/nizam-framework'
_WA123_PREFIX = '.agent/evidence/123/experiment/'
_WA123_SELECTION = '.agent/evidence/123/selection.json'


class _ControlsProof:
    """Validate selected immutable bytes, never execute historical receipt APIs."""
    def __init__(self, repo):
        self.root = Path(repo).resolve(strict=True)
        require(git(self.root, 'rev-parse', '--show-toplevel').decode().strip() == str(self.root), 'controls repository toplevel')
        require(git(self.root, 'remote', 'get-url', 'origin').decode().strip() == _WA123_ORIGIN, 'controls repository origin')
        self.cache = {}; self.bundle_cache = {}; self.commits = set(); self.entries = {}
        self.transport = None; self.observed_outputs = set()

    def obj(self, value, keys, label):
        _bundle_object(value, tuple(keys.split()), label + ' closed keys')
        return value

    def integer(self, value, label, minimum=0):
        require(type(value) is int and value >= minimum, label + ' exact integer')
        return value

    def text(self, value, label):
        require(type(value) is str and 0 < len(value) <= 1024 and '\0' not in value, label + ' string')
        return value

    def version(self, value, label):
        require(type(value) is int and value == 1, label + ' version integer1')

    def same(self, left, right, label):
        require(canonical(left) == canonical(right), label + ' binding mismatch')

    def exact_commit(self, revision):
        _bundle_hex(revision, 40, 'controls immutable revision')
        if revision not in self.commits:
            try:
                observed=git(self.root, 'rev-parse', '--verify', revision+'^{commit}').decode().strip()
            except AssuranceError as exc:
                raise AssuranceError('controls artifact ref commit unavailable '+revision+': '+str(exc)[:600]) from exc
            require(observed==revision, 'controls exact commit')
            self.commits.add(revision)

    def entry(self, revision, path):
        self.exact_commit(revision); relative_path(path)
        key=(revision,path)
        if key not in self.entries:
            rows=git(self.root,'--literal-pathspecs','ls-tree','-z',revision,'--',path).split(b'\0')
            require(len(rows)==2 and rows[1]==b'', 'missing controls artifact path: '+path)
            metadata,name=rows[0].split(b'\t',1);mode,kind,oid=metadata.decode().split()
            require(name.decode()==path and kind=='blob' and mode in ('100644','100755'), 'unsafe controls Git input')
            size=int(git(self.root,'cat-file','-s',oid).decode())
            require(size>=0,'controls blob size')
            self.entries[key]=(oid,mode,size)
        return self.entries[key]

    def transported(self, revision, path):
        if not path.startswith(_WA123_PREFIX):return
        self.observed_outputs.add((revision,path))
        if self.transport is None:return
        lineage,inventory=self.transport
        require(revision in lineage and path in inventory,'experiment ref outside selected transported lineage/inventory')
        oid,mode,_=self.entry(revision,path);row=inventory[path]
        require(oid==row['git_blob'] and mode==row['git_mode'],'transported ref blob/mode binding')
        data=self.cache.get((revision,path))
        if data is not None:require(sha(data)==row['sha256'],'transported ref digest binding')

    def bind_transport(self, source, tip, inventory):
        lineage=set(git(self.root,'rev-list',source+'..'+tip).decode().splitlines())
        by_path={row['path']:row for row in inventory}
        require(len(by_path)==len(inventory),'transported duplicate path inventory')
        self.transport=(lineage,by_path)
        for revision,path in tuple(self.observed_outputs):self.transported(revision,path)

    def raw(self, ref, label='artifact', maximum=2*1024*1024):
        _bundle_object(ref,('path','sha256','revision'),'controls artifact reference')
        relative_path(ref['path']);_bundle_hex(ref['sha256'],64,'controls artifact digest')
        # Physical state is deliberately fresh, even when immutable Git data is cached.
        current=self.root
        parts=ref['path'].split('/')
        for index,part in enumerate(parts):
            current=current/part
            try:physical=current.lstat()
            except FileNotFoundError:break
            require(not stat.S_ISLNK(physical.st_mode),label+' current artifact component symlink')
            if index<len(parts)-1:require(stat.S_ISDIR(physical.st_mode),label+' current artifact parent mode')
            else:require(stat.S_ISREG(physical.st_mode) and physical.st_nlink==1,label+' current artifact regular mode/hardlink')
        data,_=self.at(ref['revision'],ref['path'],maximum)
        require(sha(data)==ref['sha256'],label+' artifact ref digest')
        return data

    def output_ref(self, ref, label):
        require(type(ref) is dict and type(ref.get('path')) is str and ref['path'].startswith(_WA123_PREFIX),
                label+' transported experiment output path')
        return self.raw(ref,label)

    def value(self, ref, label, canonical_bytes=True):
        raw=self.raw(ref,label);value=parse_json(raw)
        if canonical_bytes:require(raw==canonical(value)+b'\n',label+' canonical JSON')
        return value

    def at(self, revision, path, maximum=2*1024*1024):
        oid,mode,size=self.entry(revision,path)
        require(size<=maximum,'controls artifact size bound exceeded before blob read')
        key=(revision,path)
        if key not in self.cache:
            data=git(self.root,'cat-file','blob',oid)
            require(len(data)==size,'controls blob observed size')
            self.cache[key]=data
        self.transported(revision,path)
        return self.cache[key],mode=='100755'

    def environment(self, env):
        self.obj(env, 'runtime variables', 'environment')
        self.obj(env['runtime'], 'implementation version system machine', 'runtime')
        for key, val in env['runtime'].items(): self.text(val, 'runtime ' + key)
        require(env['variables'] == {'PYTHONDONTWRITEBYTECODE': '1'}, 'environment selected variables')

    def producer(self, producer, mode):
        _receipt_producer(producer)
        require(producer['agent_id'] == 'wa123-capable-ci' and re.fullmatch('123-ci-' + mode + '-attempt[1-3]', producer['session_id']), 'producer session allocation attempt')

    def identity(self, candidate, inputs):
        validate_identity(candidate); self.environment(candidate['environment'])
        require(candidate['repository'] == _WA123_ORIGIN and candidate['record_ownership'] == {}, 'candidate origin/record ownership')
        selected = manifest(inputs)
        require(candidate['source_tree'] == git(self.root, 'rev-parse', candidate['source_commit'] + '^{tree}').decode().strip(), 'candidate actual source tree')
        for category in CATEGORIES:
            require([e['path'] for e in candidate['assessed_inputs'][category]] == selected[category], 'candidate assessed inputs manifest')
            for entry in candidate['assessed_inputs'][category]:
                raw, executable = self.at(candidate['source_commit'], entry['path'])
                require(sha(raw) == entry['sha256'] and executable is entry['executable'], 'protected source input digest/mode')
                current = regular_file(self.root, entry['path'])
                require(current.stat().st_nlink == 1 and sha(current.read_bytes()) == entry['sha256'] and bool(current.stat().st_mode & 0o111) is executable, 'protected current input digest/mode/hardlink')

    def checkout(self, value, selection, candidate):
        self.obj(value, 'sha tree event event_head event_base parents', 'checkout')
        for key in ('sha', 'tree', 'event_head'): _bundle_hex(value[key], 40, 'checkout ' + key)
        require(value['event'] in ('push', 'pull_request'), 'checkout event')
        require(type(value['parents']) is list, 'checkout parents')
        require(git(self.root, 'rev-parse', value['sha'] + '^{tree}').decode().strip() == value['tree'], 'checkout tree binding')
        require(git(self.root, 'show', '-s', '--format=%P', value['sha']).decode().split() == value['parents'], 'checkout parents binding')
        git(self.root, 'merge-base', '--is-ancestor', candidate['source_commit'], value['sha'])
        if value['event'] == 'push': require(value['event_head'] == value['sha'] and value['event_base'] is None, 'checkout push head/base')
        else:
            _bundle_hex(value['event_base'], 40, 'checkout base')
            require(value['event_head'] in value['parents'] and value['event_base'] in value['parents'], 'checkout PR merge parents')
        raw, _ = self.at(value['sha'], _WA123_SELECTION)
        require(raw == self.raw(selection, 'fixed CLI selection'), 'checkout fixed CLI selection input binding')
        for category in CATEGORIES:
            for entry in candidate['assessed_inputs'][category]:
                raw, mode = self.at(value['sha'], entry['path'])
                require(sha(raw) == entry['sha256'] and mode is entry['executable'], 'checkout protected input digest/mode')

    def selection(self, reference, mode):
        value = self.value(reference, mode + ' selection')
        self.obj(value, 'schema_version mode repository_origin review_repository source_commit source_tree inputs contract_ref authority_ref prerequisites producer packet_base prior_ledger report_ref prompt_ref runner_ref adapter_ref evaluator_ref shadow_state_ref candidate a10_policy_ref capture_pack_ref', mode + ' selection')
        self.version(value['schema_version'], mode + ' selection')
        require(value['mode'] == mode and value['repository_origin'] == _WA123_ORIGIN and value['review_repository'] == _WA123_REPOSITORY, 'selection mode/repository binding')
        self.producer(value['producer'], mode)
        for key in ('source_commit', 'source_tree', 'packet_base'): _bundle_hex(value[key], 40, 'selection ' + key)
        git(self.root, 'merge-base', '--is-ancestor', value['packet_base'], value['source_commit'])
        for key in ('contract_ref', 'authority_ref', 'report_ref', 'prompt_ref', 'runner_ref', 'adapter_ref', 'evaluator_ref', 'shadow_state_ref'): self.raw(value[key], 'selection ' + key)
        if mode == 'capture': require(all(value[k] is None for k in ('candidate', 'a10_policy_ref', 'capture_pack_ref')), 'capture selection future input')
        else: require(all(value[k] is not None for k in ('candidate', 'a10_policy_ref', 'capture_pack_ref')), 'verify selection missing input')
        paths = {'prompt_ref': 'templates/convergent-review-prompt.md', 'runner_ref': 'tools/workflow_assurance_ci.py', 'adapter_ref': 'tools/linux_trial_sandbox.sh', 'evaluator_ref': 'tools/evaluate_convergent_review_prompt.py'}
        for key, path in paths.items():
            require(value[key]['path'] == path, 'selected runner/adapter/evaluator/prompt path')
            raw, mode_bit = self.at(value['source_commit'], path)
            require(raw == self.raw(value[key], key), 'selected executable/prompt protected source binding')
            if key != 'prompt_ref': require(mode_bit or key == 'evaluator_ref', 'selected runner/adapter executable mode')
        return value

    def authority(self, selection):
        value = self.value(selection['authority_ref'], 'authority')
        self.obj(value, 'schema_version role purpose repository owner gate operator_instruction_verbatim scope source_authority_ref mapping', 'authority')
        self.version(value['schema_version'], 'authority')
        require(value['role'] == 'Root' and value['purpose'] == 'experiment-only' and value['repository'] == _WA123_ORIGIN, 'authority role/repository')
        original = self.value(value['source_authority_ref'], 'original authority', False)
        require(value['source_authority_ref']['path'] == '.agent/evidence/phase018-preflight/activation-authority.json' and original['repository'] == _WA123_REPOSITORY + ' only', 'original authority repository/path')
        for key in ('owner', 'gate', 'operator_instruction_verbatim'):
            self.text(value[key], 'authority ' + key); require(value[key] == original[key], 'authority original instruction/owner/gate')
        self.obj(value['scope'], 'phase features original_estimate_lines ceiling_130pct', 'authority scope')
        self.same(value['scope'], {k: original['scope'][k] for k in value['scope']}, 'original authority scope')
        require(value['scope'] == {'phase':'018-workflow-assurance-controls','features':['119','120','121','122','123'],'original_estimate_lines':7200,'ceiling_130pct':9360}, 'authority original scope constants')
        self.same(value['mapping'], {'repository_origin':_WA123_ORIGIN,'review_repository':_WA123_REPOSITORY}, 'authority selected mapping')
        return value

    def prerequisites(self, selection, candidate):
        contract = self.value(selection['contract_ref'], 'approved contract', False)
        _receipt_contract(self.root, contract, '123')
        anchor, _ = self.at(candidate['source_commit'], '.agent/contracts/123.json')
        require(anchor == self.raw(selection['contract_ref'], 'approved contract'), 'approved contract protected candidate input')
        ae = contract.get('approval_evidence', {})
        self.obj(ae, 'mode_a contract_review proposal_sha256 proposal_revision', 'approval metadata')
        _bundle_hex(ae['proposal_sha256'], 64, 'approval proposal digest'); _bundle_hex(ae['proposal_revision'], 40, 'approval proposal revision')
        proposed, _ = self.at(ae['proposal_revision'], '.agent/contracts/123.json')
        require(sha(proposed) == ae['proposal_sha256'], 'approval proposal digest binding')
        rows = selection['prerequisites']; require(type(rows) is list, 'prerequisite list')
        seen = set(); reviewers = []
        for row in rows:
            self.obj(row, 'kind artifact feature_id assessed_revision contract_sha256', 'prerequisite')
            require(row['kind'] in ('mode-a','contract-review','approved-contract','provisional-bundle') and row['feature_id']=='123' and row['kind'] not in seen, 'prerequisite kind/duplicate')
            seen.add(row['kind']); _bundle_hex(row['assessed_revision'],40,'prerequisite revision'); _bundle_hex(row['contract_sha256'],64,'prerequisite contract')
            value = self.value(row['artifact'], 'prerequisite ' + row['kind'], False)
            if row['kind']=='approved-contract':
                require(row['artifact']==selection['contract_ref'] and row['assessed_revision']==row['artifact']['revision'] and row['contract_sha256']==row['artifact']['sha256'], 'approved-contract prerequisite binding')
            else:
                _receipt_gate(value)
                if row['kind']=='mode-a':
                    require(row['artifact']['path']==ae['mode_a'] and value['feature']=='123' and value['reviewed_commit']==row['assessed_revision'] and value['contract_sha256']==row['contract_sha256']==ae['proposal_sha256'], 'ModeA approval prerequisite binding')
                    reviewers.append(value['reviewer'])
                elif row['kind']=='contract-review':
                    _receipt_schema(self.root,value,'contract_review')
                    require(row['artifact']['path']==ae['contract_review'] and value['feature']=='123' and value['reviewed_revision']==row['assessed_revision'] and value['proposal_sha256']==row['contract_sha256']==ae['proposal_sha256'], 'contract-review approval prerequisite binding')
                    reviewers.append(value.get('reviewer',value.get('actor')))
                else:
                    require(value['feature_id']=='123' and value['reviewed_revision']==row['assessed_revision'] and value['approved_contract_sha256']==row['contract_sha256']==selection['contract_ref']['sha256'], 'provisional-bundle approval prerequisite binding')
                    self.text(value['reviewer'],'provisional reviewer')
        require(seen=={'mode-a','contract-review','approved-contract','provisional-bundle'} and len(set(reviewers))==2, 'missing bound dual approval/provisional prerequisites')
        return contract

    def shadow(self, selection):
        state=self.value(selection['shadow_state_ref'],'shadow')
        self.obj(state,'repository current_phase current_feature status updated_at scope_budget circuit_breaker history purpose','shadow')
        _receipt_schema(self.root,state,'run_state')
        require(state['repository']==_WA123_ORIGIN and state['current_phase']=='018-workflow-assurance-controls' and state['current_feature']=='123' and state['status']=='experiment-pending' and state['purpose']=='experiment-only', 'shadow experiment binding')
        self.same(state['scope_budget'],dict(original_estimate_lines=7200,total_lines_changed=4303,per_feature=[]),'shadow scope')
        require(state['history']==[] and state['circuit_breaker']=={},'shadow new experiment counters/history')
        require(type(state['updated_at']) is str and state['updated_at'].endswith('Z'),'shadow time')
        return state

    def capture(self, reference, candidate, producer, label):
        value=self.value(reference,label+' capture')
        self.obj(value,'schema_version argv cwd revision candidate_sha256 environment producer executed outcome exit_code stdout stderr',label+' capture')
        self.version(value['schema_version'],label+' capture')
        require(type(value['argv']) is list and value['argv'] and all(type(x) is str and x for x in value['argv']),label+' capture argv')
        require(type(value['cwd']) is str and Path(value['cwd']).is_absolute(),label+' capture cwd')
        _bundle_hex(value['revision'],40,label+' capture revision');git(self.root,'merge-base','--is-ancestor',candidate['source_commit'],value['revision'])
        require(value['executed'] is True and type(value['exit_code']) is int and value['exit_code']==0 and value['outcome']=='success',label+' capture executed exit outcome')
        self.same(value['producer'],producer,label+' capture producer');self.same(value['environment'],candidate['environment'],label+' capture environment')
        require(value['candidate_sha256']==sha(canonical(candidate)),label+' capture candidate digest')
        self.output_ref(value['stdout'],label+' capture stdout').decode('utf8');self.output_ref(value['stderr'],label+' capture stderr').decode('utf8')
        return value

    def bundle_header(self, raw, source):
        _bundle_hex(source,40,'bundle source')
        require(type(raw) is bytes and len(raw)<=16*1024*1024,'bundle size limit')
        header,sep,pack=raw.partition(b'\n\n');lines=header.split(b'\n')
        require(sep and len(lines)==3 and lines[0]==b'# v2 git bundle','bundle v2 header/ref count')
        prefix=('-'+source+' ').encode()
        require(lines[1].startswith(prefix),'bundle prerequisite base')
        diagnostic=lines[1][len(prefix):].decode('utf8')
        require(diagnostic and all(ord(c)>=32 and ord(c)!=127 for c in diagnostic),'bundle prerequisite diagnostic')
        match=re.fullmatch(rb'([0-9a-f]{40}) refs/wa123/proof',lines[2])
        require(match is not None,'bundle advertised ref')
        return match[1].decode(),pack

    def pack(self, raw, source):
        import zlib
        key=(sha(raw),source)
        if key in self.bundle_cache:return self.bundle_cache[key]
        tip,pack=self.bundle_header(raw,source)
        require(pack[:4]==b'PACK' and len(pack)>=32,'pack header truncated')
        require(int.from_bytes(pack[4:8],'big') in (2,3),'pack version')
        count=int.from_bytes(pack[8:12],'big');require(count<=100000,'pack object count bound')
        offset=12; entries={}; resolved={}; by_oid={}
        for _ in range(count):
            start=offset;byte=pack[offset];offset+=1;kind=(byte>>4)&7;size=byte&15;shift=4
            while byte&128:
                byte=pack[offset];offset+=1;size|=(byte&127)<<shift;shift+=7;require(shift<=63,'pack size overflow')
            require(size<=20*1024*1024,'pack object size bound')
            base=None
            if kind==6:
                byte=pack[offset];offset+=1;distance=byte&127
                while byte&128:byte=pack[offset];offset+=1;distance=((distance+1)<<7)+(byte&127)
                base=start-distance
            elif kind==7:base=pack[offset:offset+20].hex();offset+=20
            else:require(kind in (1,2,3,4),'pack unknown object type')
            decoder=zlib.decompressobj();data=decoder.decompress(pack[offset:],20*1024*1024+1)
            require(decoder.eof and len(data)==size,'pack compressed size/truncation')
            offset+=len(pack[offset:])-len(decoder.unused_data)
            entries[start]=(kind,base,data)
        require(offset+20==len(pack) and hashlib.sha1(pack[:offset]).digest()==pack[offset:],'pack trailing junk/checksum')
        def delta(base,data):
            cursor=0
            def number():
                nonlocal cursor
                result=shift=0
                while True:
                    byte=data[cursor];cursor+=1;result|=(byte&127)<<shift;shift+=7
                    if not byte&128:return result
                    require(shift<=63,'pack delta varint')
            require(number()==len(base),'pack delta base size');length=number()
            require(length<=20*1024*1024,'pack delta declared output bound');out=bytearray()
            while cursor<len(data):
                op=data[cursor];cursor+=1
                if op&128:
                    at=length_copy=0
                    for bit in range(4):
                        if op&(1<<bit):at|=data[cursor]<<(8*bit);cursor+=1
                    for bit in range(3):
                        if op&(16<<bit):length_copy|=data[cursor]<<(8*bit);cursor+=1
                    length_copy=length_copy or 65536
                    require(at+length_copy<=len(base) and len(out)+length_copy<=length,'pack delta copy/output bound')
                    out.extend(base[at:at+length_copy])
                else:
                    require(op>0 and cursor+op<=len(data) and len(out)+op<=length,'pack delta literal/output bound')
                    out.extend(data[cursor:cursor+op]);cursor+=op
                require(len(out)<=20*1024*1024,'pack delta output bound')
            require(len(out)==length,'pack delta result size');return bytes(out)
        types={1:'commit',2:'tree',3:'blob',4:'tag'}
        pending=set(entries)
        while pending:
            progress=False
            for start in list(pending):
                kind,base,data=entries[start]
                if kind in types:otype=types[kind];body=data
                else:
                    if type(base) is int:
                        if base not in resolved:continue
                        otype,parent=resolved[base]
                    else:
                        if base in by_oid:otype,parent=by_oid[base]
                        else:
                            try:
                                otype=git(self.root,'cat-file','-t',base).decode().strip()
                                require(int(git(self.root,'cat-file','-s',base).decode())<=20*1024*1024,'pack external delta base size bound')
                                parent=git(self.root,'cat-file',otype,base)
                            except AssuranceError:continue
                    body=delta(parent,data)
                oid=hashlib.sha1((otype+' '+str(len(body))+'\0').encode()+body).hexdigest()
                require(oid not in by_oid,'pack duplicate object');resolved[start]=(otype,body);by_oid[oid]=(otype,body);pending.remove(start);progress=True
            require(progress,'pack unresolved delta base')
        expected={line.split()[0] for line in git(self.root,'rev-list','--objects',tip,'^'+source).decode().splitlines()}
        require(set(by_oid)==expected,'pack undeclared/unreachable object inventory')
        git(self.root,'merge-base','--is-ancestor',source,tip)
        inventory=[]; previous=source
        for revision in git(self.root,'rev-list','--reverse',source+'..'+tip).decode().splitlines():
            require(git(self.root,'show','-s','--format=%P',revision).decode().split()==[previous],'bundle output commit ancestry')
            changes=git(self.root,'diff-tree','--no-commit-id','--raw','-r','-z',revision).split(b'\0');changes=[x for x in changes if x]
            require(len(changes)%2==0,'bundle raw tree diff')
            for meta,name in zip(changes[::2],changes[1::2]):
                old_mode,new_mode,old_oid,oid,status=meta.decode().lstrip(':').split();path=name.decode()
                require(status=='A' and path.startswith(_WA123_PREFIX) and new_mode in ('100644','100755'),'bundle add-only prefix/protected intermediate path/mode')
                data,_=self.at(revision,path)
                inventory.append(dict(path=path,revision=revision,git_blob=oid,git_mode=new_mode,sha256=sha(data)))
            previous=revision
        inventory.sort(key=lambda x:(x['revision'],x['path']))
        self.bundle_cache[key]=(tip,inventory)
        return tip,inventory

    def host(self, host, mode, selection_ref, selection, candidate):
        import io
        import zipfile
        self.obj(host,'repository run_id attempt job_id job head_sha checkout_sha artifact_name artifact_sha256 metadata_ref job_log_ref',mode+' host')
        require(host['repository']==_WA123_REPOSITORY and host['job']=='convergent_review','host repository/job')
        for key in ('run_id','attempt','job_id'):self.integer(host[key],'host '+key,1)
        metadata=self.value(host['metadata_ref'],mode+' metadata')
        self.obj(metadata,'schema_version mode source_commit producer selection_ref invocation_ref run_id attempt job_id artifact_id artifact_name archive_ref fetches',mode+' metadata')
        self.version(metadata['schema_version'],mode+' metadata')
        require(metadata['mode']==mode and metadata['source_commit']==candidate['source_commit'],'metadata source/mode')
        self.same(metadata['selection_ref'],selection_ref,'metadata selection');self.same(metadata['producer'],selection['producer'],'metadata producer')
        for key in ('run_id','attempt','job_id','artifact_name'):require(metadata[key]==host[key],'host metadata '+key+' binding')
        self.integer(metadata['artifact_id'],'artifact id',1)
        require(host['artifact_name']=='wa123-'+mode+'-'+selection['producer']['session_id'],'host artifact name')
        rows=metadata['fetches'];require(type(rows) is list and [r.get('kind') for r in rows]==['run','jobs','artifacts','job-log','archive'],'metadata fetch order')
        expected=[['gh','api',f'repos/{_WA123_REPOSITORY}/actions/runs/{host["run_id"]}'],
            ['gh','api',f'repos/{_WA123_REPOSITORY}/actions/runs/{host["run_id"]}/attempts/{host["attempt"]}/jobs?per_page=100'],
            ['gh','api',f'repos/{_WA123_REPOSITORY}/actions/runs/{host["run_id"]}/artifacts?per_page=100'],
            ['gh','run','view',str(host['run_id']),'--repo',_WA123_REPOSITORY,'--job',str(host['job_id']),'--log'],
            ['gh','api',f'repos/{_WA123_REPOSITORY}/actions/artifacts/{metadata["artifact_id"]}/zip']]
        outputs={}
        for row,argv in zip(rows,expected):
            self.obj(row,'kind argv cwd revision actual_exit stdout stderr',mode+' fetch')
            require(type(row['actual_exit']) is int and row['actual_exit']==0,'fetch actual exit integer0')
            self.same(row['argv'],argv,'fetch command argv');require(type(row['cwd']) is str and Path(row['cwd']).is_absolute(),'fetch cwd')
            _bundle_hex(row['revision'],40,'fetch exercised revision')
            outputs[row['kind']]=self.raw(row['stdout'],'raw '+row['kind'],32*1024*1024 if row['kind']=='archive' else 16*1024*1024 if row['kind']=='job-log' else 2*1024*1024)
            self.raw(row['stderr'],'fetch stderr').decode('utf8')
        require(rows[-1]['stdout']==metadata['archive_ref'] and rows[3]['stdout']==host['job_log_ref'],'metadata archive/log ref binding')
        archive=outputs['archive'];require(sha(archive)==host['artifact_sha256'],'archive artifact hash digest')
        require(len(archive)<=32*1024*1024,'archive size limit')
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            infos=z.infolist();require(len(infos)==3 and {i.filename for i in infos}=={'proof.bundle','manifest.json','invocation.json'},'ZIP entry duplicate/extra/path')
            require(sum(i.file_size for i in infos)<=20*1024*1024,'ZIP entry decompression size bound')
            for info in infos:
                mode_bits=info.external_attr>>16
                require(not info.is_dir() and not info.flag_bits&1 and stat.S_IFMT(mode_bits) in (0,stat.S_IFREG),'ZIP entry regular mode/symlink/encryption')
                limit=16*1024*1024 if info.filename=='proof.bundle' else 2*1024*1024
                require(info.file_size<=limit,'ZIP entry size bound')
            bundle=z.read('proof.bundle');manifest_raw=z.read('manifest.json');invocation_raw=z.read('invocation.json')
        manifest_value=parse_json(manifest_raw);require(manifest_raw==canonical(manifest_value)+b'\n','manifest canonical JSON')
        self.obj(manifest_value,'schema_version mode source_commit output_tip bundle_sha256 bundle_size inventory','manifest')
        self.version(manifest_value['schema_version'],'manifest')
        require(manifest_value['mode']==mode and manifest_value['source_commit']==candidate['source_commit'],'manifest source/mode')
        require(type(manifest_value['bundle_size']) is int and manifest_value['bundle_size']==len(bundle) and manifest_value['bundle_sha256']==sha(bundle),'manifest bundle size/hash')
        tip,inventory=self.pack(bundle,candidate['source_commit'])
        require(tip==manifest_value['output_tip'],'manifest bundle output tip')
        self.same(manifest_value['inventory'],inventory,'artifact inventory')
        invocation=self.value(metadata['invocation_ref'],mode+' invocation')
        require(invocation_raw==self.raw(metadata['invocation_ref']),'archive invocation bytes')
        self.obj(invocation,'schema_version mode producer selection_ref source_commit checkout environment argv cwd output_tip bundle_sha256 manifest_sha256 result_refs actual_exit',mode+' invocation')
        self.version(invocation['schema_version'],'invocation')
        require(invocation['mode']==mode and invocation['source_commit']==candidate['source_commit'],'invocation source/mode')
        self.same(invocation['selection_ref'],selection_ref,'invocation selection');self.same(invocation['producer'],selection['producer'],'invocation producer')
        self.same(invocation['environment'],candidate['environment'],'invocation environment')
        require(type(invocation['actual_exit']) is int and invocation['actual_exit']==0,'invocation actual exit')
        require(type(invocation['cwd']) is str and Path(invocation['cwd']).is_absolute(),'invocation cwd')
        require(type(invocation['argv']) is list and len(invocation['argv'])==7 and invocation['argv'][1:6]==['tools/workflow_assurance_ci.py',mode,'--selection',_WA123_SELECTION,'--output'] and Path(invocation['argv'][0]).is_absolute() and Path(invocation['argv'][6]).is_absolute(),'invocation exact argv')
        require(invocation['output_tip']==tip and invocation['bundle_sha256']==sha(bundle) and invocation['manifest_sha256']==sha(manifest_raw),'invocation manifest/hash binding')
        self.checkout(invocation['checkout'],selection_ref,candidate)
        require(invocation['checkout']['sha']==host['checkout_sha'] and invocation['checkout']['event_head']==host['head_sha'],'host checkout/head binding')
        log=outputs['job-log'].decode('utf8');markers=re.findall(r'WA123_INVOCATION=(\{[^\r\n]*\})$',log,re.M)
        require(len(markers)==1 and markers[0].encode()+b'\n'==invocation_raw,'job log unique invocation marker binding')
        run=parse_json(outputs['run']);jobs=parse_json(outputs['jobs']);artifacts=parse_json(outputs['artifacts'])
        require(type(run) is dict,'raw run object')
        for key in ('id','run_attempt'):self.integer(run.get(key),'raw run '+key,1)
        require(run['id']==host['run_id'] and run['run_attempt']==host['attempt'] and run.get('name')=='compliance' and run.get('status')=='completed' and run.get('conclusion')=='success','raw run id/status/conclusion metadata')
        require(run.get('head_sha')==host['head_sha'] and run.get('event')==invocation['checkout']['event'] and type(run.get('repository')) is dict and run['repository'].get('full_name')==_WA123_REPOSITORY,'raw run head/event/repository binding')
        require(type(jobs) is dict and type(jobs.get('total_count')) is int and jobs['total_count']==5 and type(jobs.get('jobs')) is list and len(jobs['jobs'])==5,'raw jobs five/count/page')
        require({j.get('name') for j in jobs['jobs']}=={'validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'} and len({j.get('id') for j in jobs['jobs']})==5,'raw jobs names/id uniqueness')
        selected_job=None
        for job in jobs['jobs']:
            for key in ('id','run_id','run_attempt'):self.integer(job.get(key),'raw job '+key,1)
            require(job['run_id']==host['run_id'] and job['run_attempt']==host['attempt'] and job.get('head_sha')==host['head_sha'] and job.get('status')=='completed' and job.get('conclusion')=='success','raw job run/head/success binding')
            require(type(job.get('steps')) is list,'job steps list')
            numbers=[]
            for step in job['steps']:
                numbers.append(self.integer(step.get('number'),'step number',1));self.text(step.get('name'),'step name')
                require(type(step.get('status')) is str and (step.get('conclusion') is None or type(step.get('conclusion')) is str),'step status/conclusion types')
            require(len(numbers)==len(set(numbers)),'duplicate job step number')
            if job['id']==host['job_id'] and job['name']=='convergent_review':selected_job=job
        require(selected_job is not None,'selected host job id binding')
        for name in ('WA123 '+mode,'Run PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/test_sandbox_boundaries.py','Run required isolation suite'):
            matches=[s for s in selected_job['steps'] if s['name']==name]
            require(len(matches)==1 and matches[0]['status']=='completed' and matches[0]['conclusion']=='success','required job step success: '+name)
        inactive='WA123 '+('verify' if mode=='capture' else 'capture')
        skipped=[s for s in selected_job['steps'] if s['name']==inactive]
        require(len(skipped)==1 and skipped[0]['status']=='completed' and skipped[0]['conclusion']=='skipped','inactive job stage skipped: '+inactive)
        require(type(artifacts) is dict and type(artifacts.get('total_count')) is int and 1<=artifacts['total_count']<=100 and type(artifacts.get('artifacts')) is list and len(artifacts['artifacts'])==artifacts['total_count'],'artifact pagination/count')
        ids=set();matches=[]
        for artifact in artifacts['artifacts']:
            self.integer(artifact.get('id'),'artifact id',1);self.integer(artifact.get('size_in_bytes'),'artifact size',1)
            require(artifact['id'] not in ids and type(artifact.get('expired')) is bool and type(artifact.get('name')) is str,'artifact id/type/duplicate');ids.add(artifact['id'])
            if artifact['name']==host['artifact_name']:matches.append(artifact)
        require(len(matches)==1 and not matches[0]['expired'] and matches[0]['id']==metadata['artifact_id'],'selected artifact expired/id')
        require(matches[0]['size_in_bytes']==len(archive),'artifact archive size length')
        return invocation,bundle,inventory

    def replay(self, evidence, selection):
        try:
            import convergent_review as cr
        except ModuleNotFoundError:
            from tools import convergent_review as cr
        ref=evidence['replay_ref'];replay=self.value(ref,'replay');cr.validate_replay(replay)
        prefix=ref['path'].rsplit('/',1)[0]+'/'
        def read(path):
            relative_path(path);raw,_=self.at(ref['revision'],prefix+path);return raw
        ledger_raw=read('ledger.json');markdown=read('review.md')
        require(sha(ledger_raw)==replay['output_digests']['ledger'] and sha(markdown)==replay['output_digests']['markdown'],'replay output digests')
        ledger=parse_json(ledger_raw);cr.validate_ledger(ledger)
        require(ledger_raw==cr.canonical_json_bytes(ledger) and markdown==cr.render_markdown(ledger).encode() and cr.canonical_json_bytes(cr.extract_embedded_ledger(markdown.decode()))==ledger_raw,'replay canonical ledger/markdown')
        packet=prior=None;pd=prior_digest=None;trials=[];trial_digests={};trial_raw={}
        for artifact in replay['artifacts']:
            raw=read(artifact['path']);require(len(raw)==artifact['bytes'] and sha(raw)==artifact['digest'],'replay retained artifact digest')
            value=parse_json(raw);require(raw==cr.canonical_json_bytes(value),'replay retained canonical JSON')
            if artifact['role']=='packet':packet=value;pd=artifact['digest'];cr.validate_packet(packet)
            elif artifact['role']=='trial':trials.append(value);trial_digests[artifact['trial_number']]=artifact['digest'];trial_raw[artifact['trial_number']]=raw
            elif artifact['role']=='prior_ledger':prior=value;prior_digest=artifact['digest'];cr.validate_ledger(prior)
            else:raise AssuranceError('replay unselected suppression')
        require(packet is not None and packet['repository']==_WA123_REPOSITORY and packet['head_sha']==selection['source_commit'] and packet['base_sha']==selection['packet_base'] and packet['review_id']=='wa123-controls' and packet['mode']=='ordinary','replay packet selected identity/head/base')
        require(replay['repository']==packet['repository'] and replay['head_sha']==packet['head_sha'] and replay['review_id']==packet['review_id'],'replay identity binding')
        if selection['prior_ledger'] is None:require(prior is None,'replay unexpected prior ledger')
        else:require(prior_digest==selection['prior_ledger']['sha256'] and self.raw(selection['prior_ledger'])==cr.canonical_json_bytes(prior),'selected prior ledger digest')
        for trial in trials:cr.validate_trial(trial,packet,pd,'replay trial')
        computed=cr.converge_documents(packet,pd,trials,trial_digests,prior,prior_digest,[])
        require(cr.canonical_json_bytes(computed)==ledger_raw,'replay convergence mismatch')
        evaluation=self.value(evidence['evaluation_ref'],'evaluation receipt')
        self.obj(evaluation,'schema_version packet_digest prompt_template_digest runner_digest trials review_replay_digest','evaluation receipt')
        require(evaluation['schema_version']==cr.SCHEMA_VERSION and evaluation['packet_digest']==pd and evaluation['prompt_template_digest']==selection['prompt_ref']['sha256'] and evaluation['runner_digest']==selection['runner_ref']['sha256'] and evaluation['review_replay_digest']==ref['sha256'],'evaluation selected input/replay digest')
        rows=evidence['trial_provenance'];require(type(rows) is list and len(rows)==3 and [r.get('number') for r in rows]==[1,2,3],'three trial provenance length/order')
        require(type(evaluation['trials']) is list and len(evaluation['trials'])==3,'evaluation three receipts')
        try:
            import evaluate_convergent_review_prompt as evaluator
        except ModuleNotFoundError:
            from tools import evaluate_convergent_review_prompt as evaluator
        for number,(row,receipt) in enumerate(zip(rows,evaluation['trials']),1):
            self.obj(row,'number packet_ref prompt_ref output_ref stdout_ref stderr_ref evaluation_receipt_ref invocation runner_ref adapter_ref evaluator_ref boundary_ref','trial provenance')
            self.obj(receipt,'trial_number prompt_digest trial_digest isolated_packet_digest runner_exit isolation_adapter_digest','trial evaluation receipt')
            require(type(row['number']) is int and type(receipt['trial_number']) is int and receipt['trial_number']==number and type(receipt['runner_exit']) is int and receipt['runner_exit']==0,'trial receipt number/exit integer')
            require(receipt['isolated_packet_digest']==pd and receipt['isolation_adapter_digest']==selection['adapter_ref']['sha256'],'trial adapter/packet digest')
            for key in ('runner_ref','adapter_ref','evaluator_ref'):self.same(row[key],selection[key],'trial selected '+key)
            self.same(row['boundary_ref'],evidence['capability_ref'],'trial boundary provenance');self.same(row['evaluation_receipt_ref'],evidence['evaluation_ref'],'trial evaluation receipt ref')
            for key,suffix in [('packet_ref','packet.json'),('prompt_ref','prompt.md'),('output_ref','trial.json'),('stdout_ref','runner.stdout'),('stderr_ref','runner.stderr')]:
                require(row[key]['path'].endswith('/trial-'+str(number)+'/'+suffix),'trial provenance path binding '+key)
            require(self.raw(row['packet_ref'],'trial packet')==cr.canonical_json_bytes(packet) and self.raw(row['output_ref'],'trial output')==trial_raw[number],'trial retained packet/output bytes')
            require(receipt['trial_digest']==row['output_ref']['sha256'] and receipt['prompt_digest']==row['prompt_ref']['sha256'],'trial output/prompt receipt digest')
            for key in ('packet_ref','prompt_ref','output_ref','stdout_ref','stderr_ref','evaluation_receipt_ref'):self.output_ref(row[key],'trial '+key)
            self.raw(row['stdout_ref'],'trial stdout').decode();self.raw(row['stderr_ref'],'trial stderr').decode()
            argv=row['invocation'];require(type(argv) is list and len(argv) in (15,17),'trial adapter invocation argv')
            require(argv[1]=='--root' and argv[3]=='--runner' and argv[5]=='--' and argv[6]==argv[4] and argv[7]=='--prompt' and argv[9]=='--packet' and argv[11]=='--trial-number' and argv[12]==str(number) and argv[13]=='--output','trial adapter invocation structure')
            require(Path(argv[0]).name=='linux_trial_sandbox.sh' and Path(argv[4]).name=='workflow_assurance_ci.py' and Path(argv[2]).name=='trial-'+str(number),'trial selected adapter/runner/root path')
            require(argv[8]==str(Path(argv[2])/'prompt.md') and argv[10]==str(Path(argv[2])/'packet.json') and argv[14]==str(Path(argv[2])/'trial.json'),'trial invocation input/output paths')
            prior_path=Path(argv[2])/'prior-ledger.json' if prior is not None else None
            require((len(argv)==17 and argv[15:]==['--prior-ledger',str(prior_path)]) if prior is not None else len(argv)==15,'trial prior invocation')
            rendered=evaluator.render_prompt(self.raw(selection['prompt_ref']).decode(),Path(argv[10]),number,Path(argv[14]),prior_path).encode()
            require(self.raw(row['prompt_ref'],'trial prompt')==rendered,'trial rendered prompt binding')
        report=self.value(selection['report_ref'],'report')
        self.obj(report,'final_verdict issues missing_acceptance_coverage unsupported_claims required_fixes','report')
        self.obj(report['final_verdict'],'approved','report verdict')
        require(type(report['final_verdict']['approved']) is bool and all(type(report[k]) is list for k in ('issues','missing_acceptance_coverage','unsupported_claims','required_fixes')),'report boolean/array types')
        mapped=convergent_agf_verdict(ledger,report,expected_repository=_WA123_REPOSITORY,expected_head_sha=selection['source_commit'])
        try:
            _receipt_gate(mapped)
        except AssuranceError as exc:
            raise AssuranceError('A11 AGF report/ledger approval failure: '+str(exc)[:600]) from exc
        self.same(mapped,self.value(evidence['a11_result_ref'],'A11 mapped result'),'A11 report/ledger result')
        return mapped

    def capability(self, evidence, capture_selection, candidate):
        value=self.value(evidence['capability_ref'],'capability')
        self.obj(value,'schema_version source_commit checkout_sha environment producer boundary isolation','capability')
        self.version(value['schema_version'],'capability')
        require(value['source_commit']==candidate['source_commit'] and value['checkout_sha']==evidence['checkout']['sha'],'capability source/checkout')
        self.same(value['environment'],candidate['environment'],'capability environment/runtime');self.same(value['producer'],capture_selection['producer'],'capability producer')
        for key,path in [('boundary','.github/scripts/test_sandbox_boundaries.py'),('isolation','tools/test_convergent_review.py')]:
            process=value[key];self.obj(process,'argv cwd revision executed actual_exit stdout stderr','capability '+key+' process')
            require(process['executed'] is True and type(process['actual_exit']) is int and process['actual_exit']==0,'capability '+key+' process exit')
            require(type(process['argv']) is list and len(process['argv'])==2 and Path(process['argv'][0]).is_absolute() and process['argv'][1]==path,'capability '+key+' argv')
            require(type(process['cwd']) is str and Path(process['cwd']).is_absolute(),'capability process cwd')
            git(self.root,'merge-base','--is-ancestor',candidate['source_commit'],process['revision'])
            stdout=self.output_ref(process['stdout'],'capability '+key+' stdout').decode();self.output_ref(process['stderr'],'capability stderr').decode()
            if key=='boundary':require(stdout.splitlines().count('SANDBOX BOUNDARIES PASS: intact 0; isolated omission controls 40/41/42; unexpected execution errors rejected')==1,'capability boundary diagnostic')
        return value

    def a10(self, evidence, selection, capture_selection, candidate, verify_invocation):
        policy=self.value(selection['a10_policy_ref'],'A10 policy')
        _receipt_policy(self.root,policy)
        require(policy['stage']=='source-ready' and policy['feature_id']=='123' and policy['operation_id']=='123-ci-capture' and policy['repository']==_WA123_ORIGIN,'A10 policy stage/operation')
        self.same(policy['candidate'],candidate,'A10 policy candidate');self.same(policy['producer'],capture_selection['producer'],'A10 captured producer')
        self.same(policy['contract'],capture_selection['contract_ref'],'A10 contract');self.same(policy['prerequisites'],capture_selection['prerequisites'],'A10 prerequisites')
        require(policy['from_status']=='experiment-pending' and policy['to_status']=='experiment-source-ready','A10 transition status')
        require(type(policy['at']) is str and policy['at'].endswith('Z'),'A10 transition time')
        operator=self.value(policy['operator'],'A10 operator')
        self.obj(operator,'schema_version role repository feature_id stage candidate_sha256 approved authority_ref owner gate scope','A10 operator')
        self.version(operator['schema_version'],'A10 operator')
        authority=self.authority(capture_selection)
        require(operator['role']=='Root' and operator['approved'] is True and operator['repository']==_WA123_ORIGIN and operator['feature_id']=='123' and operator['stage']=='source-ready' and operator['candidate_sha256']==sha(canonical(candidate)),'A10 operator binding')
        self.same(operator['authority_ref'],capture_selection['authority_ref'],'A10 operator authority')
        for key in ('owner','gate','scope'):self.same(operator[key],authority[key],'A10 operator '+key)
        receipt=self.value(evidence['a10_receipt_ref'],'A10 receipt')
        self.obj(receipt,'schema_version repository feature_id stage operation_id status candidate producer contract_ref operator_ref prerequisites checks verdict','A10 receipt')
        self.version(receipt['schema_version'],'A10 receipt')
        require(receipt['status']=='passed','A10 receipt passed status')
        for key in ('repository','feature_id','stage','operation_id','candidate','producer','prerequisites'):self.same(receipt[key],policy[key],'A10 receipt '+key)
        self.same(receipt['contract_ref'],policy['contract'],'A10 receipt contract');self.same(receipt['operator_ref'],policy['operator'],'A10 receipt operator')
        self.obj(receipt['verdict'],'final_verdict issues missing_acceptance_coverage unsupported_claims','A10 receipt verdict');_receipt_gate(receipt['verdict'])
        require(type(policy['commands']) is list and len(policy['commands'])==1 and type(receipt['checks']) is list and len(receipt['checks'])==1,'A10 command/check coverage')
        command=policy['commands'][0];check=receipt['checks'][0]
        self.obj(command,'argv expected_exit proof_kind diagnostic capture','A10 command')
        self.obj(check,'argv executed outcome exit_code stdout stderr capture','A10 check')
        require(type(command['expected_exit']) is int and command['expected_exit']==0 and command['proof_kind']=='success' and command['diagnostic']=='WA123_A11_APPROVED','A10 expected command policy')
        self.same(command['capture'],evidence['a11_capture_ref'],'A10 selected actual capture');self.same(check['capture'],command['capture'],'A10 check capture')
        capture=self.capture(evidence['a11_capture_ref'],candidate,capture_selection['producer'],'A11')
        self.same(capture['argv'],command['argv'],'A10 actual argv');self.same(check['argv'],capture['argv'],'A10 check argv')
        require(check['executed'] is True and type(check['exit_code']) is int and check['exit_code']==0 and check['outcome']=='success','A10 check exit/outcome')
        for key in ('stdout','stderr'):self.same(check[key],capture[key],'A10 check '+key)
        require('WA123_A11_APPROVED' in self.raw(capture['stdout']).decode().splitlines(),'A11 actual map diagnostic')
        argv=capture['argv'];require(len(argv)==9 and argv[1:5]==['tools/workflow_assurance_ci.py','map','--selection',_WA123_PREFIX+'inputs/selection-capture.json'] and argv[5]=='--evaluation' and argv[7]=='--output','A11 map command argv')
        copied,_=self.at(capture['revision'],_WA123_PREFIX+'inputs/selection-capture.json')
        require(copied==self.raw(evidence['capture_selection_ref']),'A11 selected input copy')
        require(policy['recovery']==evidence['a10_receipt_ref'],'A10 selected recovery receipt')
        state=self.shadow(capture_selection)
        digest=sha(canonical(receipt));event=dict(at=policy['at'],event='wa-receipt-transition',detail='Receipt '+policy['operation_id']+' advanced 123:source-ready ('+digest+')',operation_id=policy['operation_id'],feature_id='123',stage='source-ready',candidate_sha256=sha(canonical(candidate)),receipt_sha256=digest)
        advanced=copy.deepcopy(state);advanced['status']=policy['to_status'];advanced['updated_at']=policy['at'];advanced['history'].append(event)
        verify_record_update(state,advanced,['/status','/updated_at','/history'])
        result=self.value(evidence['a10_result_ref'],'A10 result')
        self.obj(result,'receipt advance noop republish rerun_required conflict_rejected','A10 result')
        self.same(result['receipt'],receipt,'A10 verified receipt')
        for key,action,expected_state,expected_receipt in [('advance','advance',advanced,receipt),('noop','noop',advanced,receipt),('republish','republish',state,receipt),('rerun_required','rerun-required',state,None)]:
            item=result[key];self.obj(item,'action state receipt reason','A10 transition '+key)
            require(item['action']==action,'A10 transition action '+key);self.same(item['state'],expected_state,'A10 transition state/history '+key);self.same(item['receipt'],expected_receipt,'A10 transition receipt '+key);self.text(item['reason'],'A10 transition reason')
            _receipt_schema(self.root,item['state'],'run_state')
        require(result['conflict_rejected'] is True,'A10 conflict rejection not exercised')
        absent=copy.deepcopy(policy['recovery']);absent['path']+='.missing-wa123'
        require(not git(self.root,'ls-tree',absent['revision'],'--',absent['path']),'A10 recovery missing path actually absent')
        capture=self.capture(evidence['a10_capture_ref'],candidate,selection['producer'],'A10')
        self.same(capture['argv'],verify_invocation['argv'],'A10 capture invocation argv')
        require(capture['cwd']==verify_invocation['cwd'] and capture['revision']==verify_invocation['checkout']['sha'],'A10 capture cwd/revision verify invocation checkout binding')
        require(self.raw(capture['stdout'])==self.raw(evidence['a10_result_ref']),'A10 actual result stdout')

    def verify(self, evidence, policy):
        json_value(policy);json_value(evidence)
        self.obj(policy,'schema_version role repository_origin review_repository feature_id selection_ref evidence_ref hosted_review_ref approved','controls policy')
        self.version(policy['schema_version'],'controls policy')
        require(policy['role']=='Root' and policy['approved'] is True and policy['repository_origin']==_WA123_ORIGIN and policy['review_repository']==_WA123_REPOSITORY and policy['feature_id']=='123','controls selected Root policy')
        self.obj(evidence,'schema_version candidate checkout capture_selection_ref verify_selection_ref evaluation_ref replay_ref trial_provenance a11_capture_ref a11_result_ref a10_receipt_ref a10_result_ref a10_capture_ref capability_ref capture_host verify_host pack_ref inventory','controls evidence')
        self.version(evidence['schema_version'],'controls evidence')
        self.same(evidence,self.value(policy['evidence_ref'],'selected evidence'),'controls selected evidence')
        for key in ('evaluation_ref','replay_ref','a11_capture_ref','a11_result_ref','a10_result_ref','a10_capture_ref','capability_ref'):
            self.output_ref(evidence[key],key)
        self.same(policy['selection_ref'],evidence['verify_selection_ref'],'controls policy verify selection')
        capture_selection=self.selection(evidence['capture_selection_ref'],'capture');selection=self.selection(evidence['verify_selection_ref'],'verify')
        for key in capture_selection:
            if key not in ('mode','candidate','a10_policy_ref','capture_pack_ref','producer'):self.same(capture_selection[key],selection[key],'capture/verify selection '+key)
        candidate=evidence['candidate'];self.identity(candidate,selection['inputs']);self.same(candidate,selection['candidate'],'selected candidate identity')
        require(candidate['source_commit']==selection['source_commit'] and candidate['source_tree']==selection['source_tree'],'candidate selected source/tree')
        self.prerequisites(capture_selection,candidate);self.authority(capture_selection);self.shadow(capture_selection)
        capture_inv,capture_bundle,capture_inventory=self.host(evidence['capture_host'],'capture',evidence['capture_selection_ref'],capture_selection,candidate)
        verify_inv,verify_bundle,verify_inventory=self.host(evidence['verify_host'],'verify',evidence['verify_selection_ref'],selection,candidate)
        self.bind_transport(candidate['source_commit'],verify_inv['output_tip'],verify_inventory)
        self.same(evidence['checkout'],capture_inv['checkout'],'Evidence capture checkout')
        require(self.raw(selection['capture_pack_ref'],'capture bundle',16*1024*1024)==capture_bundle,'selected capture bundle bytes')
        require(self.raw(evidence['pack_ref'],'verify bundle',16*1024*1024)==verify_bundle,'selected final pack bytes')
        self.same(evidence['inventory'],verify_inventory,'evidence artifact inventory')
        git(self.root,'merge-base','--is-ancestor',capture_inv['output_tip'],verify_inv['output_tip'])
        self.same(capture_inv['environment'],verify_inv['environment'],'capture/verify environment')
        self.same(capture_inv['result_refs'],[next(r for r in capture_inv['result_refs'] if r['path'].endswith('/candidate.json')),evidence['capability_ref'],evidence['evaluation_ref'],evidence['replay_ref'],evidence['a11_result_ref'],evidence['a11_capture_ref']],'capture invocation result refs')
        self.output_ref(capture_inv['result_refs'][0],'candidate artifact')
        self.same(self.value(capture_inv['result_refs'][0],'candidate artifact'),candidate,'capture candidate artifact')
        self.same(verify_inv['result_refs'],[evidence['a10_receipt_ref'],evidence['a10_result_ref'],evidence['a10_capture_ref']],'verify invocation result refs')
        self.capability(evidence,capture_selection,candidate);self.replay(evidence,capture_selection)
        self.a10(evidence,selection,capture_selection,candidate,verify_inv)
        review=self.value(policy['hosted_review_ref'],'hosted review')
        self.obj(review,'schema_version role reviewer source_commit capture_selection_ref verify_selection_ref evidence_ref capture_host verify_host final_verdict issues missing_acceptance_coverage unsupported_claims evidence_files','hosted review')
        self.version(review['schema_version'],'hosted review');self.text(review['reviewer'],'hosted reviewer')
        require(review['role']=='Evaluator' and review['source_commit']==candidate['source_commit'],'hosted review role/source')
        self.obj(review['final_verdict'],'approved','hosted review verdict');_receipt_gate(review)
        for key in ('capture_selection_ref','verify_selection_ref','capture_host','verify_host'):self.same(review[key],evidence[key],'hosted review '+key)
        self.same(review['evidence_ref'],policy['evidence_ref'],'hosted review evidence')
        require(type(review['evidence_files']) is list and review['evidence_files'],'hosted review evidence paths')
        for path in review['evidence_files']:relative_path(path)
        return dict(schema_version=1,feature_id='123',source_commit=candidate['source_commit'],checkout_sha=evidence['checkout']['sha'],candidate_sha256=sha(canonical(candidate)),capture_run_id=evidence['capture_host']['run_id'],verify_run_id=evidence['verify_host']['run_id'],a11_verdict='approve',a10_receipt_sha256=evidence['a10_receipt_ref']['sha256'],transition_actions=['advance','noop','republish','rerun-required'],hosted_review_sha256=policy['hosted_review_ref']['sha256'])


def verify_controls_ready(repo, evidence, *, policy):
    """Observe selected hosted A11/A10 proof without running historical commands."""
    try:
        return copy.deepcopy(_ControlsProof(repo).verify(evidence,policy))
    except AssuranceError:
        raise
    except (OSError,ValueError,TypeError,KeyError,AttributeError,IndexError,StopIteration,RecursionError,RuntimeError) as exc:
        raise AssuranceError('controls proof invalid: '+str(exc)[:600]) from exc


_WA_ROLE_PROFILES = {
    'Orchestrator': 'orchestrator-primary',
    'Planner': 'planner-creative',
    'Generator': 'generator-deterministic',
    'Validator': 'validator-structural',
    'Evaluator': 'evaluator-adversarial',
}
_WA_ASSURANCE_TIERS = ('Routine', 'Standard', 'High-assurance')
_WA_TIER_ROUTES = {
    'Routine': ['trivial', 'small-change'],
    'Standard': ['bugfix', 'standard-feature'],
    'High-assurance': ['high-risk'],
}
_WA_PROFILE_CASES = (
    'preregister-before-run',
    'roles-reused',
    'reject-unstable-baseline',
    'same-candidate',
    'missed-baseline-blocker',
    'cost-latency-accounting',
    'no-self-promotion',
)


def _receipt_root(repo):
    root = Path(repo)
    require(not root.is_symlink(), 'receipt symlink repository')
    root = root.resolve(strict=True)
    require(git(root, 'rev-parse', '--show-toplevel').decode().strip() == str(root), 'receipt repository toplevel')
    return root


def _profile_int(value, label, minimum=0):
    require(type(value) is int and value >= minimum, f'profile integer >={minimum}: {label}')
    return value


def _profile_candidate(root, candidate, *, live_env=True):
    if live_env:
        _receipt_candidate(root, candidate)
        return
    validate_identity(candidate)
    anchor = candidate['source_commit']
    require(git(root, 'rev-parse', '--verify', anchor + '^{commit}').decode().strip() == anchor, 'profile candidate exact commit')
    require(git(root, 'rev-parse', anchor + '^{tree}').decode().strip() == candidate['source_tree'], 'profile candidate actual tree')
    require(git(root, 'remote', 'get-url', 'origin').decode().strip() == candidate['repository'], 'profile actual repository')
    env = candidate['environment']
    _bundle_object(env, ('runtime', 'variables'), 'profile candidate environment')
    _bundle_object(env['runtime'], ('implementation', 'version', 'system', 'machine'), 'profile candidate runtime')
    for key, val in env['runtime'].items():
        _receipt_text(val, 'profile runtime ' + key)
    require(type(env['variables']) is dict and env['variables'], 'profile environment variables')
    for category in ('source', 'tests', 'tools', 'contracts'):
        for entry in candidate['assessed_inputs'][category]:
            data, executable = _entry_blob(root, anchor, entry['path'])
            require(sha(data) == entry['sha256'] and executable is entry['executable'], 'profile protected Git input changed')


def _profile_authority(root, reference, repository):
    raw = _receipt_artifact(root, reference)
    authority = parse_json(raw)
    require(raw.rstrip(b'\n') == canonical(authority), 'profile authority canonical JSON')
    _bundle_object(
        authority,
        ('schema_version', 'role', 'repository', 'owner', 'gate', 'approved', 'allow_self_promotion', 'allow_gate_reduction'),
        'profile authority',
    )
    _profile_int(authority['schema_version'], 'authority schema_version', 1)
    require(authority['schema_version'] == 1, 'authority schema_version')
    require(authority['role'] == 'Root' and authority['approved'] is True, 'profile authority Root approval')
    require(authority['repository'] == repository, 'profile authority repository binding')
    _receipt_text(authority['owner'], 'authority owner')
    _receipt_text(authority['gate'], 'authority gate')
    require(
        authority['allow_self_promotion'] is False and authority['allow_gate_reduction'] is False,
        'profile authority forbids self-promotion and gate reduction',
    )
    return authority


def preregister_profile_comparison(repo, preregistration, *, policy, live_env=True):
    """Validate and record a Phase 019 Feature 124 profile comparison preregistration before shadow runs."""
    try:
        json_value(preregistration)
        json_value(policy)
        root = _receipt_root(repo)
        origin = git(root, 'remote', 'get-url', 'origin').decode().strip()
        _bundle_object(
            policy,
            ('schema_version', 'repository', 'feature_id', 'stage', 'baseline_controls_ref', 'authority_ref', 'persistent_runtime_ready'),
            'profile preregistration policy',
        )
        require(type(policy['schema_version']) is int and policy['schema_version'] == 1, 'preregistration policy version')
        require(policy['repository'] == origin, 'preregistration policy repository binding')
        require(
            policy['feature_id'] == '124' and policy['stage'] == 'profile-preregistration',
            'preregistration policy feature/stage',
        )
        require(type(policy['persistent_runtime_ready']) is bool, 'preregistration persistent_runtime_ready boolean')
        authority = _profile_authority(root, policy['authority_ref'], origin)

        baseline_raw = _receipt_artifact(root, policy['baseline_controls_ref'])
        baseline = parse_json(baseline_raw)
        require(baseline_raw.rstrip(b'\n') == canonical(baseline), 'baseline controls canonical JSON')
        _bundle_object(
            baseline,
            ('schema_version', 'feature_id', 'source_commit', 'candidate_sha256', 'a11_verdict', 'status', 'flaky_runs', 'unresolved_blockers'),
            'baseline controls readiness',
        )
        require(
            type(baseline['schema_version']) is int and baseline['schema_version'] == 1 and baseline['feature_id'] == '123',
            'baseline controls feature/version',
        )
        _profile_int(baseline['flaky_runs'], 'baseline flaky_runs', 0)
        _profile_int(baseline['unresolved_blockers'], 'baseline unresolved_blockers', 0)
        require(
            baseline['status'] == 'stable'
            and baseline['a11_verdict'] == 'approve'
            and baseline['flaky_runs'] == 0
            and baseline['unresolved_blockers'] == 0,
            'unstable or unapproved baseline controls rejected',
        )

        _bundle_object(
            preregistration,
            (
                'schema_version',
                'preregistration_id',
                'repository',
                'feature_id',
                'execution_scope',
                'state',
                'shadow_runs_started',
                'shadow_run_refs',
                'candidate',
                'test_bundle_ref',
                'role_bindings',
                'tiers',
                'thresholds',
                'operator_decision_policy',
            ),
            'profile preregistration',
        )
        require(type(preregistration['schema_version']) is int and preregistration['schema_version'] == 1, 'preregistration schema_version')
        _receipt_text(preregistration['preregistration_id'], 'preregistration_id')
        require(
            preregistration['repository'] == origin and preregistration['feature_id'] == '124',
            'preregistration repository/feature_id',
        )
        require(
            preregistration['execution_scope'] in ('repository-worktree', 'persistent-runtime-sbcl'),
            'preregistration execution_scope',
        )
        if preregistration['execution_scope'] == 'persistent-runtime-sbcl':
            require(
                policy['persistent_runtime_ready'] is True,
                'persistent-runtime SBCL profile claims require completed 130-132 qualification',
            )
        require(
            preregistration['state'] == 'preregistered-before-shadow'
            and preregistration['shadow_runs_started'] is False
            and preregistration['shadow_run_refs'] == [],
            'preregistration must occur before any shadow run starts',
        )

        candidate = preregistration['candidate']
        _profile_candidate(root, candidate, live_env=live_env)
        candidate_digest = sha(canonical(candidate))
        require(
            baseline['source_commit'] == candidate['source_commit']
            and baseline['candidate_sha256'] == candidate_digest,
            'baseline controls must bind to the same candidate as preregistration',
        )

        test_bundle_raw = _receipt_artifact(root, preregistration['test_bundle_ref'])
        test_bundle = parse_json(test_bundle_raw)
        require(test_bundle_raw.rstrip(b'\n') == canonical(test_bundle), 'test bundle canonical JSON')
        _bundle_object(test_bundle, ('schema_version', 'bundle_id', 'source_commit', 'cases'), 'profile test bundle')
        require(
            type(test_bundle['schema_version']) is int
            and test_bundle['schema_version'] == 1
            and test_bundle['source_commit'] == candidate['source_commit']
            and type(test_bundle['cases']) is list
            and len(test_bundle['cases']) >= 1
            and all(type(c) is str and bool(c.strip()) for c in test_bundle['cases']),
            'profile test bundle source_commit/cases binding',
        )

        roles = preregistration['role_bindings']
        _bundle_object(roles, tuple(_WA_ROLE_PROFILES.keys()), 'profile role_bindings')
        require(
            roles == _WA_ROLE_PROFILES,
            'profile role_bindings must reuse exact existing AGF role and capability profile IDs',
        )

        tiers = preregistration['tiers']
        _bundle_object(tiers, _WA_ASSURANCE_TIERS, 'profile tiers')
        tier_max_duration = 0
        tier_max_cost = 0
        for tier_name in _WA_ASSURANCE_TIERS:
            spec = tiers[tier_name]
            _bundle_object(
                spec,
                (
                    'applicability',
                    'route_classes',
                    'required_roles',
                    'same_candidate_baseline',
                    'persistent_runtime_claim',
                    'max_duration_ms',
                    'max_cost_units',
                    'max_blocker_mismatch',
                ),
                f'tier {tier_name}',
            )
            _receipt_text(spec['applicability'], f'{tier_name} applicability')
            require(
                spec['route_classes'] == _WA_TIER_ROUTES[tier_name],
                f'{tier_name} route_classes must match canonical tier applicability',
            )
            require(
                type(spec['required_roles']) is list
                and len(spec['required_roles']) >= 2
                and len(spec['required_roles']) == len(set(spec['required_roles']))
                and all(r in _WA_ROLE_PROFILES for r in spec['required_roles'])
                and 'Evaluator' in spec['required_roles']
                and 'Generator' in spec['required_roles'],
                f'{tier_name} required_roles must reuse canonical roles and include Generator and Evaluator',
            )
            require(spec['same_candidate_baseline'] is True, f'{tier_name} requires same_candidate_baseline=True')
            require(type(spec['persistent_runtime_claim']) is bool, f'{tier_name} persistent_runtime_claim boolean')
            if preregistration['execution_scope'] == 'repository-worktree':
                require(
                    spec['persistent_runtime_claim'] is False,
                    f'{tier_name} repository-worktree scope cannot claim persistent-runtime semantics',
                )
            dur = _profile_int(spec['max_duration_ms'], f'{tier_name} max_duration_ms', 1)
            cost = _profile_int(spec['max_cost_units'], f'{tier_name} max_cost_units', 1)
            mismatch = _profile_int(spec['max_blocker_mismatch'], f'{tier_name} max_blocker_mismatch', 0)
            require(mismatch == 0, f'{tier_name} max_blocker_mismatch must be 0')
            tier_max_duration = max(tier_max_duration, dur)
            tier_max_cost = max(tier_max_cost, cost)

        thresholds = preregistration['thresholds']
        _bundle_object(
            thresholds,
            ('max_missed_baseline_blockers', 'max_unexplained_divergences', 'max_duration_ms', 'max_cost_units', 'min_comparison_runs'),
            'profile thresholds',
        )
        require(
            _profile_int(thresholds['max_missed_baseline_blockers'], 'max_missed_baseline_blockers', 0) == 0
            and _profile_int(thresholds['max_unexplained_divergences'], 'max_unexplained_divergences', 0) == 0,
            'profile thresholds must prohibit missed baseline blockers and unexplained divergences',
        )
        require(
            _profile_int(thresholds['max_duration_ms'], 'thresholds max_duration_ms', 1) >= tier_max_duration
            and _profile_int(thresholds['max_cost_units'], 'thresholds max_cost_units', 1) >= tier_max_cost
            and _profile_int(thresholds['min_comparison_runs'], 'thresholds min_comparison_runs', 1) >= 1,
            'profile thresholds must bound tier duration, cost, and comparison runs',
        )

        op_policy = preregistration['operator_decision_policy']
        _bundle_object(
            op_policy,
            ('accountable_role', 'gate', 'self_promotion_allowed', 'automatic_gate_reduction_allowed', 'authority_ref'),
            'operator_decision_policy',
        )
        require(
            op_policy['accountable_role'] == 'Root'
            and op_policy['gate'] == authority['gate']
            and op_policy['self_promotion_allowed'] is False
            and op_policy['automatic_gate_reduction_allowed'] is False
            and op_policy['authority_ref'] == policy['authority_ref'],
            'operator_decision_policy must bind Root authority and forbid self-promotion/gate reduction',
        )

        return copy.deepcopy(
            dict(
                schema_version=1,
                feature_id='124',
                preregistration_id=preregistration['preregistration_id'],
                repository=origin,
                execution_scope=preregistration['execution_scope'],
                candidate_sha256=candidate_digest,
                source_commit=candidate['source_commit'],
                baseline_controls_sha256=policy['baseline_controls_ref']['sha256'],
                test_bundle_sha256=preregistration['test_bundle_ref']['sha256'],
                tiers=list(_WA_ASSURANCE_TIERS),
                roles_reused=True,
                before_shadow_run=True,
                baseline_stable=True,
                self_promotion_allowed=False,
                automatic_gate_reduction_allowed=False,
            )
        )
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as exc:
        raise AssuranceError('profile preregistration invalid: ' + str(exc)[:600]) from exc


def _profile_run_record(root, run, label, expected_candidate_sha, expected_commit, expected_tree, expected_bundle_sha):
    _bundle_object(
        run,
        (
            'run_id',
            'candidate_sha256',
            'source_commit',
            'source_tree',
            'test_bundle_sha256',
            'executed',
            'outcome',
            'exit_code',
            'verdict',
            'blocker_ids',
            'advisory_ids',
            'duration_ms',
            'cost_units',
            'command_count',
            'capture_ref',
        ),
        label,
    )
    _receipt_text(run['run_id'], label + ' run_id')
    require(
        run['candidate_sha256'] == expected_candidate_sha
        and run['source_commit'] == expected_commit
        and run['source_tree'] == expected_tree
        and run['test_bundle_sha256'] == expected_bundle_sha,
        f'same-candidate binding mismatch on {label}',
    )
    require(run['executed'] is True and run['outcome'] in ('success', 'failed'), f'{label} must be an executed run')
    require(type(run['exit_code']) is int, f'{label} exit_code must be integer')
    if run['outcome'] == 'success':
        require(run['exit_code'] == 0, f'{label} success outcome requires exit_code 0')
    else:
        require(run['exit_code'] != 0, f'{label} failed outcome requires nonzero exit_code')

    for field in ('blocker_ids', 'advisory_ids'):
        items = run[field]
        require(
            type(items) is list
            and all(type(x) is str and bool(x.strip()) for x in items)
            and len(items) == len(set(items)),
            f'{label} {field} must be unique non-empty strings',
        )

    verdict = run['verdict']
    _bundle_object(
        verdict,
        ('final_verdict', 'issues', 'missing_acceptance_coverage', 'unsupported_claims'),
        f'{label} verdict',
    )
    _bundle_object(verdict['final_verdict'], ('approved',), f'{label} final_verdict')
    require(type(verdict['final_verdict']['approved']) is bool, f'{label} approved boolean')
    for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'):
        require(type(verdict[k]) is list, f'{label} verdict {k} list')
    if run['blocker_ids'] or run['outcome'] == 'failed':
        require(
            verdict['final_verdict']['approved'] is False
            and bool(verdict['issues'] or verdict['missing_acceptance_coverage'] or verdict['unsupported_claims']),
            f'{label} with blockers or failed outcome must have unapproved verdict and non-empty blocking array',
        )
    else:
        _receipt_gate(verdict)

    dur = _profile_int(run['duration_ms'], f'{label} duration_ms', 1)
    cost = _profile_int(run['cost_units'], f'{label} cost_units', 1)
    cmds = _profile_int(run['command_count'], f'{label} command_count', 1)

    cap_raw = _receipt_artifact(root, run['capture_ref'])
    cap = parse_json(cap_raw)
    require(cap_raw.rstrip(b'\n') == canonical(cap), f'{label} capture canonical JSON')
    _bundle_object(
        cap,
        (
            'schema_version',
            'run_id',
            'candidate_sha256',
            'revision',
            'executed',
            'outcome',
            'exit_code',
            'duration_ms',
            'cost_units',
            'command_count',
            'stdout',
            'stderr',
        ),
        f'{label} capture',
    )
    require(
        type(cap['schema_version']) is int
        and cap['schema_version'] == 1
        and cap['run_id'] == run['run_id']
        and cap['candidate_sha256'] == expected_candidate_sha
        and cap['executed'] is True
        and cap['outcome'] == run['outcome']
        and cap['exit_code'] == run['exit_code']
        and cap['duration_ms'] == dur
        and cap['cost_units'] == cost
        and cap['command_count'] == cmds,
        f'{label} capture accounting/outcome mismatch',
    )
    git(root, 'merge-base', '--is-ancestor', expected_commit, cap['revision'])
    _receipt_artifact(root, cap['stdout']).decode('utf-8')
    _receipt_artifact(root, cap['stderr']).decode('utf-8')


def evaluate_profile_comparison(repo, comparison, *, policy, live_env=True):
    """Evaluate a Phase 019 Feature 125 shadow comparison against its preregistered baseline."""
    try:
        json_value(comparison)
        json_value(policy)
        root = _receipt_root(repo)
        origin = git(root, 'remote', 'get-url', 'origin').decode().strip()
        _bundle_object(
            policy,
            ('schema_version', 'repository', 'feature_id', 'stage', 'preregistration_ref', 'preregistration_policy_ref', 'authority_ref'),
            'profile comparison policy',
        )
        require(type(policy['schema_version']) is int and policy['schema_version'] == 1, 'comparison policy version')
        require(
            policy['repository'] == origin and policy['feature_id'] == '125' and policy['stage'] == 'shadow-comparison',
            'comparison policy repository/feature/stage',
        )
        prereg_raw = _receipt_artifact(root, policy['preregistration_ref'])
        prereg = parse_json(prereg_raw)
        require(prereg_raw.rstrip(b'\n') == canonical(prereg), 'preregistration artifact canonical JSON')
        prereg_policy_raw = _receipt_artifact(root, policy['preregistration_policy_ref'])
        prereg_policy = parse_json(prereg_policy_raw)
        require(prereg_policy_raw.rstrip(b'\n') == canonical(prereg_policy), 'preregistration policy canonical JSON')
        require(policy['authority_ref'] == prereg_policy.get('authority_ref'), 'comparison authority_ref must match preregistration policy')
        prereg_summary = preregister_profile_comparison(root, prereg, policy=prereg_policy, live_env=live_env)
        authority = _profile_authority(root, policy['authority_ref'], origin)

        _bundle_object(
            comparison,
            (
                'schema_version',
                'comparison_id',
                'repository',
                'feature_id',
                'preregistration_ref',
                'profile_tier',
                'route_class',
                'candidate',
                'baseline_run',
                'shadow_run',
                'operator_decision',
                'requested_action',
            ),
            'profile comparison',
        )
        require(type(comparison['schema_version']) is int and comparison['schema_version'] == 1, 'comparison schema_version')
        _receipt_text(comparison['comparison_id'], 'comparison_id')
        require(
            comparison['repository'] == origin
            and comparison['feature_id'] == '125'
            and comparison['preregistration_ref'] == policy['preregistration_ref'],
            'comparison repository/feature/preregistration binding',
        )
        tier = comparison['profile_tier']
        require(tier in _WA_ASSURANCE_TIERS, 'comparison profile_tier')
        tier_spec = prereg['tiers'][tier]
        require(comparison['route_class'] in tier_spec['route_classes'], 'comparison route_class not applicable to tier')

        require(
            canonical(comparison['candidate']) == canonical(prereg['candidate']),
            'same-candidate comparison candidate differs from preregistered candidate',
        )
        _profile_candidate(root, comparison['candidate'], live_env=live_env)
        candidate_digest = prereg_summary['candidate_sha256']
        source_commit = prereg['candidate']['source_commit']
        source_tree = prereg['candidate']['source_tree']
        bundle_digest = prereg_summary['test_bundle_sha256']

        baseline_run = comparison['baseline_run']
        shadow_run = comparison['shadow_run']
        _profile_run_record(root, baseline_run, 'baseline_run', candidate_digest, source_commit, source_tree, bundle_digest)
        _profile_run_record(root, shadow_run, 'shadow_run', candidate_digest, source_commit, source_tree, bundle_digest)
        require(baseline_run['run_id'] != shadow_run['run_id'], 'baseline and shadow run_id must be distinct')

        require(
            comparison['requested_action'] == 'recommend-only',
            'no-self-promotion: profile comparison requested_action must be recommend-only',
        )
        op_decision = comparison['operator_decision']
        _bundle_object(
            op_decision,
            ('role', 'owner', 'gate', 'decision', 'self_promote', 'reduce_active_gates', 'authority_ref'),
            'comparison operator_decision',
        )
        require(
            op_decision['role'] == 'Root'
            and op_decision['owner'] == authority['owner']
            and op_decision['gate'] == authority['gate']
            and op_decision['authority_ref'] == policy['authority_ref'],
            'comparison operator_decision authority binding',
        )
        require(
            op_decision['self_promote'] is False and op_decision['reduce_active_gates'] is False,
            'no-self-promotion: self_promote and reduce_active_gates must be False',
        )
        require(
            op_decision['decision'] in ('pending-operator-review', 'hold', 'reject-recommendation', 'approve-recommendation-only'),
            'comparison operator_decision value',
        )

        missed_blockers = sorted(set(baseline_run['blocker_ids']) - set(shadow_run['blocker_ids']))
        extra_blockers = sorted(set(shadow_run['blocker_ids']) - set(baseline_run['blocker_ids']))
        baseline_approved = baseline_run['verdict']['final_verdict']['approved']
        shadow_approved = shadow_run['verdict']['final_verdict']['approved']
        if not baseline_approved and shadow_approved and not missed_blockers:
            missed_blockers = ['UNIDENTIFIED_BASELINE_REJECTION']

        within_bounds = (
            shadow_run['duration_ms'] <= tier_spec['max_duration_ms']
            and shadow_run['cost_units'] <= tier_spec['max_cost_units']
            and shadow_run['duration_ms'] <= prereg['thresholds']['max_duration_ms']
            and shadow_run['cost_units'] <= prereg['thresholds']['max_cost_units']
        )
        eligible = (
            not missed_blockers
            and not extra_blockers
            and within_bounds
            and baseline_approved == shadow_approved
            and baseline_run['outcome'] == shadow_run['outcome']
        )
        if op_decision['decision'] == 'approve-recommendation-only':
            require(
                eligible,
                'missed baseline blocker, divergence, or cost/latency bound violation rejects recommendation approval',
            )

        return copy.deepcopy(
            dict(
                schema_version=1,
                feature_id='125',
                comparison_id=comparison['comparison_id'],
                preregistration_id=prereg['preregistration_id'],
                repository=origin,
                profile_tier=tier,
                route_class=comparison['route_class'],
                candidate_sha256=candidate_digest,
                source_commit=source_commit,
                same_candidate=True,
                baseline_outcome=baseline_run['outcome'],
                shadow_outcome=shadow_run['outcome'],
                missed_baseline_blockers=missed_blockers,
                unexplained_divergences=extra_blockers,
                within_cost_latency_bounds=within_bounds,
                accounting=dict(
                    baseline_duration_ms=baseline_run['duration_ms'],
                    shadow_duration_ms=shadow_run['duration_ms'],
                    duration_delta_ms=shadow_run['duration_ms'] - baseline_run['duration_ms'],
                    baseline_cost_units=baseline_run['cost_units'],
                    shadow_cost_units=shadow_run['cost_units'],
                    cost_delta_units=shadow_run['cost_units'] - baseline_run['cost_units'],
                    baseline_command_count=baseline_run['command_count'],
                    shadow_command_count=shadow_run['command_count'],
                    command_delta=shadow_run['command_count'] - baseline_run['command_count'],
                ),
                recommendation='recommend-for-operator-review' if eligible else 'reject-promotion',
                operator_decision=op_decision['decision'],
                promoted=False,
                active_gates_reduced=False,
                permissions_changed=False,
            )
        )
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as exc:
        raise AssuranceError('profile comparison invalid: ' + str(exc)[:600]) from exc


def verify_profiles_ready(repo, evidence, *, policy):
    """Observe candidate-bound Phase 019 (124/125) profile preregistration and shadow comparison proof."""
    try:
        json_value(evidence)
        json_value(policy)
        root = _receipt_root(repo)
        origin = git(root, 'remote', 'get-url', 'origin').decode().strip()
        _bundle_object(
            policy,
            ('schema_version', 'role', 'repository', 'feature_id', 'evidence_ref', 'independent_review_ref', 'approved'),
            'profiles-ready policy',
        )
        require(type(policy['schema_version']) is int and policy['schema_version'] == 1, 'profiles-ready policy version')
        require(
            policy['role'] == 'Root'
            and policy['approved'] is True
            and policy['repository'] == origin
            and policy['feature_id'] == '125',
            'profiles-ready Root policy binding',
        )
        evidence_raw = _receipt_artifact(root, policy['evidence_ref'])
        require(evidence_raw.rstrip(b'\n') == canonical(evidence), 'profiles-ready selected evidence bytes mismatch')
        _bundle_object(
            evidence,
            (
                'schema_version',
                'feature_id',
                'phase',
                'execution_scope',
                'candidate',
                'preregistration_ref',
                'preregistration_policy_ref',
                'preregistration_result_ref',
                'comparison_policy_ref',
                'comparisons',
                'case_proofs',
            ),
            'profiles-ready evidence',
        )
        require(
            type(evidence['schema_version']) is int
            and evidence['schema_version'] == 1
            and evidence['feature_id'] == '125'
            and evidence['phase'] == '019-workflow-assurance-profiles'
            and evidence['execution_scope'] == 'repository-worktree',
            'profiles-ready evidence metadata',
        )
        candidate = evidence['candidate']
        _profile_candidate(root, candidate, live_env=False)

        prereg = parse_json(_receipt_artifact(root, evidence['preregistration_ref']))
        prereg_policy = parse_json(_receipt_artifact(root, evidence['preregistration_policy_ref']))
        expected_prereg_result = parse_json(_receipt_artifact(root, evidence['preregistration_result_ref']))
        actual_prereg_result = preregister_profile_comparison(root, prereg, policy=prereg_policy, live_env=False)
        require(actual_prereg_result == expected_prereg_result, 'profiles-ready preregistration result mismatch')
        require(canonical(prereg['candidate']) == canonical(candidate), 'profiles-ready candidate binding')

        comp_policy = parse_json(_receipt_artifact(root, evidence['comparison_policy_ref']))
        require(type(evidence['comparisons']) is list and len(evidence['comparisons']) >= 4, 'profiles-ready comparisons list')
        tiers_recommended = set()
        rejected_blocker_seen = False
        for row in evidence['comparisons']:
            _bundle_object(row, ('comparison_ref', 'result_ref'), 'profiles-ready comparison row')
            comp = parse_json(_receipt_artifact(root, row['comparison_ref']))
            expected_res = parse_json(_receipt_artifact(root, row['result_ref']))
            actual_res = evaluate_profile_comparison(root, comp, policy=comp_policy, live_env=False)
            require(actual_res == expected_res, 'profiles-ready comparison result mismatch')
            require(
                actual_res['promoted'] is False
                and actual_res['active_gates_reduced'] is False
                and actual_res['permissions_changed'] is False,
                'profiles-ready comparison cannot promote or reduce gates',
            )
            if actual_res['recommendation'] == 'recommend-for-operator-review':
                tiers_recommended.add(actual_res['profile_tier'])
            elif actual_res['recommendation'] == 'reject-promotion' and actual_res['missed_baseline_blockers']:
                rejected_blocker_seen = True
        require(
            tiers_recommended == set(_WA_ASSURANCE_TIERS) and rejected_blocker_seen,
            'profiles-ready requires verified Routine/Standard/High-assurance comparisons plus rejected missed-blocker proof',
        )

        case_proofs = evidence['case_proofs']
        require(type(case_proofs) is list and len(case_proofs) == len(_WA_PROFILE_CASES), 'profiles-ready case_proofs count')
        seen_cases = []
        for row in case_proofs:
            _bundle_object(row, ('case', 'feature_id', 'command', 'exit_code'), 'profiles-ready case proof')
            require(
                row['case'] in _WA_PROFILE_CASES
                and row['case'] not in seen_cases
                and row['feature_id'] in ('124', '125')
                and row['command'] == f'PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py --case {row["case"]}'
                and type(row['exit_code']) is int
                and row['exit_code'] == 0,
                'profiles-ready case proof row invalid',
            )
            seen_cases.append(row['case'])
        require(tuple(seen_cases) == _WA_PROFILE_CASES, 'profiles-ready case order/coverage')

        review_raw = _receipt_artifact(root, policy['independent_review_ref'])
        review = parse_json(review_raw)
        require(review_raw.rstrip(b'\n') == canonical(review), 'profiles-ready review canonical JSON')
        _bundle_object(
            review,
            (
                'schema_version',
                'role',
                'reviewer',
                'feature_id',
                'source_commit',
                'evidence_ref',
                'final_verdict',
                'issues',
                'missing_acceptance_coverage',
                'unsupported_claims',
            ),
            'profiles-ready independent review',
        )
        require(
            type(review['schema_version']) is int
            and review['schema_version'] == 1
            and review['role'] == 'Evaluator'
            and review['feature_id'] == '125'
            and review['source_commit'] == candidate['source_commit']
            and review['evidence_ref'] == policy['evidence_ref'],
            'profiles-ready independent review binding',
        )
        _receipt_text(review['reviewer'], 'profiles-ready reviewer')
        _receipt_gate(review)

        return copy.deepcopy(
            dict(
                schema_version=1,
                feature_id='125',
                phase='019-workflow-assurance-profiles',
                execution_scope='repository-worktree',
                source_commit=candidate['source_commit'],
                candidate_sha256=sha(canonical(candidate)),
                preregistration_sha256=evidence['preregistration_ref']['sha256'],
                tiers_verified=list(_WA_ASSURANCE_TIERS),
                cases_verified=list(_WA_PROFILE_CASES),
                promoted=False,
                active_gates_reduced=False,
                independent_review_sha256=policy['independent_review_ref']['sha256'],
            )
        )
    except AssuranceError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as exc:
        raise AssuranceError('profiles proof invalid: ' + str(exc)[:600]) from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    assess = sub.add_parser('assess')
    for name in ('repo', 'source-commit', 'inputs', 'environment-names'):
        assess.add_argument('--' + name, required=True)
    assess.add_argument('--record-ownership')
    bundle = sub.add_parser('bundle')
    for name in ('repo', 'bundle', 'review'):
        bundle.add_argument('--' + name, required=True)
    entry = sub.add_parser('entry')
    entry.add_argument('--repo', required=True); entry.add_argument('--entry', required=True)
    for name in ('compare', 'record'):
        command = sub.add_parser(name)
        command.add_argument('--before', required=True); command.add_argument('--after', required=True)
        if name == 'record': command.add_argument('--owned-fields', required=True)
    vrec = sub.add_parser('verify-receipt')
    for name in ('repo', 'receipt', 'policy'):
        vrec.add_argument('--' + name, required=True)
    ptrans = sub.add_parser('plan-transition')
    for name in ('repo', 'state', 'policy'):
        ptrans.add_argument('--' + name, required=True)
    ptrans.add_argument('--receipt')
    rfail = sub.add_parser('route-failure')
    for name in ('repo', 'request', 'policy'):
        rfail.add_argument('--' + name, required=True)
    pprof = sub.add_parser('preregister-profile')
    for name in ('repo', 'preregistration', 'policy'):
        pprof.add_argument('--' + name, required=True)
    eprof = sub.add_parser('evaluate-profile')
    for name in ('repo', 'comparison', 'policy'):
        eprof.add_argument('--' + name, required=True)
    vprof = sub.add_parser('verify-profiles-ready')
    for name in ('repo', 'evidence', 'policy'):
        vprof.add_argument('--' + name, required=True)
    args = parser.parse_args()
    def read(path): return parse_json(Path(path).read_bytes())
    try:
        if args.command == 'entry':
            verify_authorized_entry(args.repo, read(args.entry))
            print('PASS entry'); return 0
        if args.command == 'bundle':
            verify_acceptance_bundle(args.repo, read(args.bundle), read(args.review))
            print('PASS bundle'); return 0
        if args.command == 'assess':
            result = assess_repository(args.repo, args.source_commit, read(args.inputs), read(args.environment_names),
                                       read(args.record_ownership) if args.record_ownership else None)
            print(canonical(result).decode()); return 0
        if args.command == 'verify-receipt':
            result = verify_stage_receipt(args.repo, read(args.receipt), policy=read(args.policy))
            print(canonical(result).decode()); return 0
        if args.command == 'plan-transition':
            result = plan_receipt_transition(args.repo, read(args.state), read(args.receipt) if args.receipt else None, policy=read(args.policy))
            print(canonical(result).decode()); return 0
        if args.command == 'route-failure':
            result = route_failed_attempt(args.repo, read(args.request), policy=read(args.policy))
            print(canonical(result).decode()); return 0
        if args.command == 'preregister-profile':
            result = preregister_profile_comparison(args.repo, read(args.preregistration), policy=read(args.policy))
            print(canonical(result).decode()); return 0
        if args.command == 'evaluate-profile':
            result = evaluate_profile_comparison(args.repo, read(args.comparison), policy=read(args.policy))
            print(canonical(result).decode()); return 0
        if args.command == 'verify-profiles-ready':
            result = verify_profiles_ready(args.repo, read(args.evidence), policy=read(args.policy))
            print(canonical(result).decode()); return 0
        before, after = read(args.before), read(args.after)
        if args.command == 'compare':
            require(compare_identity(before, after), 'assessed identity changed')
        else:
            verify_record_update(before, after, read(args.owned_fields))
        print('PASS ' + args.command); return 0
    except (AssuranceError, OSError, UnicodeError, RecursionError) as exc:
        print('AssuranceError: ' + str(exc), file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
