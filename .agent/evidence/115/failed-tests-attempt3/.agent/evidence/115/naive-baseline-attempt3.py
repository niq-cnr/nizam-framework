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

def _assess(repo, source_commit, inputs, environment_names, record_ownership=None):
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
                    source_commit=source_commit, source_tree='0' * 40,
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
    return canonical({k:v for k,v in before.items() if k not in ('environment','identity_sha256')}) == canonical({k:v for k,v in after.items() if k not in ('environment','identity_sha256')})

def verify_record_update(before, after, owned_fields):
    # Deliberate defect: accepts all records, omitting owned-field/history policy.
    return True


def assess_repository(repo, source_commit, inputs, environment_names, record_ownership=None):
    try:
        return _assess(repo, source_commit, inputs, environment_names, record_ownership)
    except (subprocess.CalledProcessError, KeyError) as exc:
        raise AssuranceError("Incomplete observed input: " + str(exc)) from exc


def main():
    import argparse
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    assess = commands.add_parser('assess')
    for name in ('repo','source-commit','inputs','environment-names'): assess.add_argument('--'+name, required=True)
    assess.add_argument('--record-ownership')
    compare = commands.add_parser('compare'); compare.add_argument('--before', required=True); compare.add_argument('--after', required=True)
    record = commands.add_parser('record'); record.add_argument('--before', required=True); record.add_argument('--after', required=True); record.add_argument('--owned-fields', required=True)
    args = parser.parse_args()
    def read(path): return json.loads(Path(path).read_text())
    try:
        if args.command == 'assess':
            result = assess_repository(args.repo,args.source_commit,read(args.inputs),read(args.environment_names),read(args.record_ownership) if args.record_ownership else None)
            print(json.dumps(result)); return 0
        if args.command == 'compare': return 0 if compare_identity(read(args.before),read(args.after)) else 1
        return 0 if verify_record_update(read(args.before),read(args.after),read(args.owned_fields)) else 1
    except (AssuranceError, OSError, ValueError) as exc:
        import sys
        print(str(exc), file=sys.stderr); return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
