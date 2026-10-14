#!/usr/bin/env python3
"""Read-only assessed-source identity and bounded JSON record continuity.

An immutable Git anchor survives later record-only commits. Unknown candidate
changes fail closed; this utility does not authenticate callers or authorize work.
"""
import argparse
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
