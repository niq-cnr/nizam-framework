"""Valid-interface, deliberately nonconservative behavioral baseline; NOT shipped product."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

class AssuranceError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)

def digest(value):
    return hashlib.sha256(value).hexdigest()

def assess_repository(repo, source_commit, inputs, environment_names, record_ownership=None):
    root = Path(repo)
    observed = {}
    for category in ('source', 'contracts', 'tests', 'tools'):
        observed[category] = []
        for path in sorted(inputs[category]):
            # Deliberate defect: trusts the anchor without checking actual candidate mutation.
            blob = git(root, 'show', source_commit + ':' + path)
            mode = git(root, 'ls-tree', source_commit, path).decode().split()[0]
            observed[category].append(dict(path=path, sha256=digest(blob), executable=mode == '100755'))
    identity = dict(schema_version=1, repository=git(root, 'remote', 'get-url', 'origin').decode().strip(),
                    source_commit=source_commit, source_tree=git(root, 'rev-parse', source_commit + '^{tree}').decode().strip(),
                    assessed_inputs=observed,
                    environment=dict(python_implementation=platform.python_implementation(), python_version=platform.python_version(),
                                     platform_system=platform.system(), platform_machine=platform.machine(),
                                     variables={name: os.environ[name] for name in sorted(environment_names)}),
                    record_ownership=record_ownership or {})
    identity['identity_sha256'] = digest(canonical(identity))
    return identity

def compare_identity(before, after):
    expected = {'schema_version', 'repository', 'source_commit', 'source_tree', 'assessed_inputs', 'environment', 'record_ownership', 'identity_sha256'}
    for value in (before, after):
        if set(value) != expected or type(value['schema_version']) is not int or value['schema_version'] != 1:
            raise AssuranceError('malformed identity')
        if value['identity_sha256'] != digest(canonical({k:v for k,v in value.items() if k != 'identity_sha256'})):
            raise AssuranceError('identity hash mismatch')
    return canonical(before) == canonical(after)

def verify_record_update(before, after, owned_fields):
    # Deliberate defect: accepts all records, omitting owned-field/history policy.
    return True
