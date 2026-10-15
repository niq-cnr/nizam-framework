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


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        assert key not in value, ('duplicate JSON key', key)
        value[key] = item
    return value


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


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


def admit_completed_inputs():
    gates = {
        '.agent/validator/123-mode-a-rev2.json': 'contract_review',
        '.agent/qa/123-contract-review-rev2.json': 'contract_review',
        '.agent/qa/123-provisional-bundle-review-rev3.json': 'contract_review',
        '.agent/validator/123-mode-b.json': 'contract_review',
        '.agent/qa/123.json': 'qa_verdict',
    }
    for path, family in gates.items():
        value = read(path)
        strict(value)
        schema(value, family)
    for path in (E/'hosted-review1.json', '.agent/qa/123-final-executable-seal1.json'):
        strict(read(path))
    pins = []
    for path, revision, expected in (
        ('.agent/contracts/123.json', APPROVED, '64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'),
        ('tools/workflow_assurance.py', SOURCE, '2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8'),
        ('tools/test_workflow_assurance.py', SOURCE, '06eba273dbfd615df7f0ea3b6b52592ed208f9ec267b52a1e06996488b850f13'),
        ('tools/workflow_assurance_ci.py', SOURCE, '7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905'),
        ('.agent/evidence/123/author3-controls.py', SOURCE, '79352536f9db966c73d7552dc5112db08a4fa356d507bf9c6482aef27f06e8bd'),
        ('.agent/qa/123-final-executable-seal1.json', SEAL, '4617136ca05064bc99458ef6e0000566a4282e3b06b785751e7cdb25a2886c79'),
        ('.agent/evidence/123/final-executable-seal1-report.json', SEAL, 'a0604f3ad3f05aa6553003e7aa0a02edc9e1ad1ec7338f4957100ca431512a11'),
        ('.agent/evidence/123/controls-policy.json', 'a8b7b902177edc8f7aead70c74bdcb574714c727', 'cc1ee6cde9faa0f6aaaab3cf2647fb509c04c8644fdca37fea9347e1ba52b53e'),
        ('.agent/evidence/123/controls-evidence.json', 'cfb84f1d559a585bbadf8957d80fd54010ad2f8e', 'd28ccd80b8c68d28d5b519a009b3da19365f5997dc7a97152952e8c107772a77'),
    ):
        pins.append(current_pin(path, revision, expected))
    evidence, policy = read(E/'controls-evidence.json'), read(E/'controls-policy.json')
    assert read('.agent/contracts/123.json')['status'] == 'approved'
    immutable_refs = refs(evidence)
    refs(policy, immutable_refs)
    candidate = evidence['candidate']
    assert candidate['source_commit'] == SOURCE
    protected = [row for rows in candidate['assessed_inputs'].values() for row in rows]
    for row in protected:
        raw = Path(row['path']).read_bytes()
        assert sha(raw) == row['sha256']
        assert bool(Path(row['path']).stat().st_mode & 0o111) == row['executable']
    report = read(E/'final-executable-seal1-report.json')
    assert len(report['payload_catalog']) == 31
    readiness = []
    for path, expected in zip(report['readiness_execution_frames'], [0, 1, 0]):
        value = read(path)
        assert value['actual_exit'] == expected and value['accepted'] and value['preservation_equal']
        assert value['installed_count'] == 239 and value['exercised_revision'] == report['release_revision']
        inventories = []
        for key in ('before', 'after'):
            row = value[key]
            raw = (E/'final-seal1'/row['path']).read_bytes()
            assert sha(raw) == row['sha256']
            inventories.append(json.loads(gzip.decompress(raw)))
        assert inventories[0] == inventories[1]
        for row in value['streams'].values():
            raw = (E/'final-seal1'/row['path']).read_bytes()
            assert sha(raw) == row['sha256'] and len(raw) == row['bytes'] == row['observed_bytes'] and row['complete']
        readiness.append({'path': path, 'actual_exit': expected})
    for path in report['strict_import_execution_frames']:
        assert read(path)['actual_exit'] == 0
    assert read(report['static_execution_frames'][-1])['actual_exit'] == 0
    adjacent = read(E/'source-prerequisite.json')['adjacent_prior_feature_evidence']
    assert len(adjacent) == 28
    for row in adjacent:
        assert Path(row['path']).read_bytes() == ref(row)
    installed = git('ls-files', '.nizam').decode().splitlines()
    assert len(installed) == 239 and git('diff', '--name-only', 'HEAD', '--', '.nizam') == b''
    return dict(strict_schema_gates=list(gates), pins=pins,
                immutable_ref_projections_verified=len(immutable_refs),
                protected_inputs_verified=len(protected), installed_regular_files=239,
                raw_indexes=[index(E/'final-seal1/capture-index.json'), index(E/'hosted-review1/capture-index.json')],
                original_readiness=readiness, adjacent_prior122_refs_verified=len(adjacent),
                initial_static_limitations_preserved=report['prior_static_control_flow'])
