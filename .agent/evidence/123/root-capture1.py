"""Root operational evidence admission; no Source execution or lifecycle writes.

QA-specific admission is completed against the actual returned evidence grammar
before this file is first executed. This module is preparation until released.
"""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

E = Path('.agent/evidence/123')
SOURCE = '9886e5fadad31845349e54235820edac71c7b7fb'
APPROVED = '452a5a5f748b5234ce1da3ad765b0da8f622cb53'
SEAL = '49c35ca9ce43ea3cab9e5c6b26cd305277189697'
BLOCKING = ('issues', 'missing_acceptance_coverage', 'unsupported_claims')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args])


def read(path):
    return json.loads(Path(path).read_bytes())


def strict(value):
    assert value['final_verdict']['approved'] is True
    assert all(type(value[k]) is list and value[k] == [] for k in BLOCKING)


def schema(value, family):
    for prefix in ('', '.nizam/'):
        jsonschema.validate(value, read(prefix + 'schema/' + family + '.schema.json'))


def ref(row):
    path, revision = row['path'], row['revision']
    raw = git('show', revision + ':' + path)
    assert sha(raw) == row['sha256'], (revision, path)
    entry = git('ls-tree', revision, '--', path).decode().split()
    assert len(entry) == 4 and entry[1] == 'blob'
    if 'git_blob' in row:
        assert entry[2] == row['git_blob']
    if 'git_mode' in row:
        assert entry[0] == row['git_mode']
    return raw


def refs(value, found=None):
    if found is None:
        found = {}
    if isinstance(value, dict):
        if {'path', 'revision', 'sha256'} <= value.keys():
            key = (value['revision'], value['path'], value['sha256'])
            if key not in found:
                found[key] = len(ref(value))
        for item in value.values():
            refs(item, found)
    elif isinstance(value, list):
        for item in value:
            refs(item, found)
    return found


def index(path):
    value = read(path)
    total = 0
    for row in value['files']:
        raw = Path(row['path']).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], row['path']
        total += len(raw)
    return {'path': str(path), 'sha256': sha(Path(path).read_bytes()),
            'files_verified': len(value['files']), 'bytes_verified': total}


def current_pin(path, revision, expected):
    raw = git('show', revision + ':' + path)
    assert sha(raw) == expected and Path(path).read_bytes() == raw, path
    return {'path': path, 'revision': revision, 'sha256': expected}
