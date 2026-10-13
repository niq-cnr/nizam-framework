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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    assess = sub.add_parser('assess')
    for name in ('repo', 'source-commit', 'inputs', 'environment-names'):
        assess.add_argument('--' + name, required=True)
    assess.add_argument('--record-ownership')
    for name in ('compare', 'record'):
        command = sub.add_parser(name)
        command.add_argument('--before', required=True); command.add_argument('--after', required=True)
        if name == 'record': command.add_argument('--owned-fields', required=True)
    args = parser.parse_args()
    def read(path): return parse_json(Path(path).read_bytes())
    try:
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
