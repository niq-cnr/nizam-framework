#!/usr/bin/env python3
"""Offline, observational Nizam host API. No DS package format is implemented.

Only application code can install HostVerifier. The CLI has no verifier and can
never make a compatible offer. Package text is hashed, never interpreted.
"""
from abc import ABC, abstractmethod
from contextlib import ExitStack
from dataclasses import dataclass
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

FORMAT = 'nizam-local-observation/1'
_NOFOLLOW_SUPPORTED = (hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY') and
    os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd and
    os.stat in os.supports_follow_symlinks and os.scandir in os.supports_fd)
ROUTES = {'readme': 'readme-docs', 'tutorial': 'tutorial-docs',
          'documentation-architecture': 'software-docs', 'reference': 'software-docs',
          'operations': 'software-docs'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def host_digest(records):
    return digest({'version': FORMAT, 'files': sorted(records, key=lambda item: item['path'])})


def route(task_kind):
    return ROUTES.get(task_kind) if type(task_kind) is str else None


@dataclass(frozen=True)
class Limits:
    configuration_bytes: int = 1048576
    inventory_files: int = 4096
    individual_file_bytes: int = 16777216
    aggregate_file_bytes: int = 67108864
    relative_path_bytes: int = 1024
    path_component_bytes: int = 255
    directory_depth: int = 16
    entrypoint_bytes: int = 1048576
    total_visited_entries: int = 16384
    total_visited_directories: int = 4096

    def __post_init__(self):
        # Host code may tighten operational bounds, never silently widen v1.
        for name, field in self.__dataclass_fields__.items():
            value = getattr(self, name)
            if type(value) is not int or value < 0 or value > field.default:
                raise ValueError('invalid-observation-bound')


@dataclass(frozen=True)
class FrameworkIdentity:
    source_commit: str
    payload_sha256: str
    compatibility_surface_sha256: str

    def data(self):
        return dict(source_commit=self.source_commit, payload_sha256=self.payload_sha256,
                    compatibility_surface_sha256=self.compatibility_surface_sha256)


@dataclass(frozen=True)
class VerifiedQualification:
    binding_sha256: str
    proof_sha256: str
    producer: str
    released: bool
    supported_mapping: bool
    limitations: tuple = ()


class HostVerifier(ABC):
    """Trusted application extension, never constructed or selected by input data.

    Implementations must check pre-established producer/signature/store trust,
    released activation, expiry, accepted DS mapping and exact-pair scope. No
    real implementation or DS mapping ships here. Synthetic test subclasses
    establish only Nizam API control flow, never package qualification.
    """
    @abstractmethod
    def verify(self, binding):
        """Return VerifiedQualification or None, without network or mutation."""


def qualification_binding(catalogue, entry, framework, observation_sha256, entrypoint):
    return {'mapping': FORMAT, 'catalogue_sha256': digest(catalogue),
            'catalogue_source_commit': framework.source_commit,
            'entry_sha256': digest(entry), 'package': {'skill': entry['skill'],
            'version': entry['package_version'], 'origin': entry['origin'],
            'identity': entry['identity']}, 'contracts': entry['supported_contracts'],
            'framework': framework.data(), 'qualification': entry['qualification'],
            'host_observation_sha256': observation_sha256, 'entrypoint': entrypoint}


class ObservationError(Exception):
    """Fixed diagnostic codes only; no submitted paths or package text in logs."""


class InputNodes:
    """One operation-wide input budget, including the early header scan."""
    def __init__(self):
        self.remaining = 65536

    def visit(self):
        self.remaining -= 1
        if self.remaining < 0:
            raise ObservationError('configuration-too-many-items')


def bounded_snapshot(value, byte_limit, *, _nodes=None):
    """Copy plain JSON incrementally before encoding any untrusted large value.

    Count exact ensure_ascii JSON bytes without allocating escaped strings.
    Copy containers under a shared node/byte/depth budget so later serialization
    cannot race a mutation of the caller's containers. Strings are immutable.
    """
    remaining, active = byte_limit, set()
    nodes = InputNodes() if _nodes is None else _nodes

    def consume(amount):
        nonlocal remaining
        remaining -= amount
        if remaining < 0:
            raise ObservationError('configuration-too-large')

    def copy_json(item, depth):
        nodes.visit()
        if depth > 32:
            raise ObservationError('configuration-too-deep')
        kind = type(item)
        if kind is str:
            if len(item) > remaining:
                raise ObservationError('configuration-too-large')
            consume(2)
            for char in item:
                code = ord(char)
                consume(2 if char in '"\\\b\f\n\r\t' else
                        1 if 32 <= code <= 126 else 6 if code <= 65535 else 12)
            return item
        if item is None:
            consume(4)
            return None
        if kind is bool:
            consume(4 if item else 5)
            return item
        if kind is int:
            if item.bit_length() > 4096:
                raise ObservationError('invalid-configuration-number')
            consume(len(str(item)))
            return item
        if kind is float:
            if not math.isfinite(item):
                raise ObservationError('invalid-configuration-number')
            consume(len(repr(item)))
            return item
        # Never compare user-defined classes: metaclass __eq__ is executable.
        if kind is not dict and kind is not list:
            raise ObservationError('invalid-configuration-type')
        if len(item) * (2 if kind is dict else 1) > nodes.remaining:
            raise ObservationError('configuration-too-many-items')
        if id(item) in active:
            raise ObservationError('cyclic-configuration')
        active.add(id(item))
        try:
            consume(2)
            result = {} if kind is dict else []
            iterator = item.items() if kind is dict else item
            for index, child in enumerate(iterator):
                if index:
                    consume(1)
                if kind is dict:
                    key, child = child
                    if type(key) is not str:
                        raise ObservationError('invalid-configuration-type')
                    key = copy_json(key, depth + 1)
                    consume(1)
                    result[key] = copy_json(child, depth + 1)
                else:
                    result.append(copy_json(child, depth + 1))
            return result
        finally:
            active.remove(id(item))

    return copy_json(value, 0)


class MissingPackage(ObservationError):
    pass


class UnsupportedHost(ObservationError):
    pass


def nofollow_supported():
    return _NOFOLLOW_SUPPORTED


def relative_path(value, limits):
    if (not isinstance(value, str) or not value or len(value) > limits.relative_path_bytes or
            not re.fullmatch(r'[A-Za-z0-9._/-]+', value) or value.startswith('/')):
        raise ObservationError('invalid-relative-path')
    parts = value.split('/')
    if any(part in ('', '.', '..') or len(part) > limits.path_component_bytes for part in parts):
        raise ObservationError('invalid-relative-path')
    return parts


def expected_records(records, entrypoint, limits):
    relative_path(entrypoint, limits)
    if not isinstance(records, list) or not records or len(records) > limits.inventory_files:
        raise ObservationError('invalid-inventory')
    result = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {'path', 'size', 'sha256'}:
            raise ObservationError('invalid-inventory')
        relative_path(record['path'], limits)
        if (type(record['size']) is not int or record['size'] < 0 or
                record['size'] > limits.individual_file_bytes or
                not isinstance(record['sha256'], str) or
                not re.fullmatch('[0-9a-f]{64}', record['sha256']) or record['path'] in result):
            raise ObservationError('invalid-inventory')
        result[record['path']] = record
    if entrypoint not in result or result[entrypoint]['size'] > limits.entrypoint_bytes:
        raise ObservationError('invalid-entrypoint')
    return result


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class Budget:
    def __init__(self, limits):
        self.limits = limits
        self.entries = self.directories = self.files = self.bytes = 0

    def entry(self):
        self.entries += 1
        if self.entries > self.limits.total_visited_entries:
            raise ObservationError('entry-budget-exceeded')

    def directory(self):
        self.directories += 1
        if self.directories > self.limits.total_visited_directories:
            raise ObservationError('directory-budget-exceeded')


class AnchoredTree:
    def __init__(self, root, package, limits):
        self.root, self.package, self.limits = root, package, limits
        self.stack = ExitStack()
        self.links = []
        self.budget = Budget(limits)

    def __enter__(self):
        try:
            if not nofollow_supported():
                raise UnsupportedHost('nofollow-unsupported')
            if (not isinstance(self.root, str) or not self.root.startswith('/') or
                    self.root != os.path.normpath(self.root) or '\x00' in self.root or
                    self.root.startswith('//')):
                raise ObservationError('invalid-root')
            package_parts = relative_path(self.package, self.limits)
            root_fd = self.open_dir('/', None)
            for part in [p for p in self.root.split('/') if p] + package_parts:
                self.budget.entry()
                before = os.stat(part, dir_fd=root_fd, follow_symlinks=False)
                next_fd = self.open_dir(part, root_fd)
                if not stat.S_ISDIR(before.st_mode) or identity(before) != identity(os.fstat(next_fd)):
                    raise ObservationError('directory-changed')
                self.links.append((root_fd, part, next_fd))
                root_fd = next_fd
            self.fd = root_fd
            self.verify_links()
            return self
        except FileNotFoundError:
            self.stack.close()
            raise MissingPackage('package-missing') from None
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        self.stack.close()

    def open_dir(self, path, parent):
        self.budget.directory()
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        self.stack.callback(os.close, fd)
        return fd

    def verify_links(self):
        for parent, name, child in self.links:
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            actual = os.fstat(child)
            if (not stat.S_ISDIR(current.st_mode) or
                    (current.st_dev, current.st_ino) != (actual.st_dev, actual.st_ino)):
                raise ObservationError('ancestor-changed')

    def read_file(self, fd, name, before):
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ObservationError('nonregular-or-linked-file')
        self.budget.files += 1
        if self.budget.files > self.limits.inventory_files or before.st_size > self.limits.individual_file_bytes:
            raise ObservationError('file-budget-exceeded')
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            opened = os.fstat(file_fd)
            if identity(before) != identity(opened) or not stat.S_ISREG(opened.st_mode):
                raise ObservationError('file-changed')
            hasher, size = hashlib.sha256(), 0
            while True:
                chunk = os.read(file_fd, min(65536, self.limits.individual_file_bytes + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                self.budget.bytes += len(chunk)
                if size > self.limits.individual_file_bytes or self.budget.bytes > self.limits.aggregate_file_bytes:
                    raise ObservationError('byte-budget-exceeded')
                hasher.update(chunk)
            if size != opened.st_size or identity(opened) != identity(os.fstat(file_fd)):
                raise ObservationError('file-changed')
            return size, hasher.hexdigest()
        finally:
            os.close(file_fd)

    def walk(self, fd, prefix='', depth=0, *, read=False):
        self.budget.directory()
        if depth > self.limits.directory_depth:
            raise ObservationError('depth-exceeded')
        before = os.fstat(fd)
        result, records = {}, []
        with os.scandir(fd) as entries:
            for entry in entries:
                # Budget BEFORE storing/sorting/recursing. All repeated walks
                # share this counter; empty directories consume it too.
                self.budget.entry()
                path = prefix + entry.name
                relative_path(path, self.limits)
                info = os.stat(entry.name, dir_fd=fd, follow_symlinks=False)
                result[path] = identity(info)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        if identity(info) != identity(os.fstat(child)):
                            raise ObservationError('directory-changed')
                        nested, child_records = self.walk(child, path + '/', depth + 1, read=read)
                        result.update(nested)
                        records.extend(child_records)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    if read:
                        size, sha = self.read_file(fd, entry.name, info)
                        records.append(dict(path=path, size=size, sha256=sha))
                else:
                    raise ObservationError('nonregular-or-linked-file')
        if identity(before) != identity(os.fstat(fd)):
            raise ObservationError('directory-changed')
        return result, records


def observe(root, package, inventory, entrypoint, limits):
    expected = expected_records(inventory, entrypoint, limits)
    with AnchoredTree(root, package, limits) as tree:
        first, records = tree.walk(tree.fd, read=True)
        second, _ = tree.walk(tree.fd)
        tree.verify_links()
        if first != second or {r['path']: r for r in records} != expected:
            raise ObservationError('inventory-mismatch')
        return host_digest(records)


def validate_catalogue(catalogue):
    # Canonical Nizam schema only; it has no remote refs. No DS lookup occurs.
    from jsonschema import Draft202012Validator
    schema = json.loads((Path(__file__).resolve().parent.parent / 'schema/recommended_skills.schema.json').read_bytes())
    if (type(catalogue) is not dict or type(catalogue.get('entries')) is not list or
            len(catalogue['entries']) > 3 or
            next(Draft202012Validator(schema).iter_errors(catalogue), None) is not None):
        raise ObservationError('invalid-catalogue')
    names = [e['skill'] for e in catalogue['entries']]
    if len(names) != len(set(names)):
        raise ObservationError('duplicate-catalogue-skill')


def resolve(config, catalogue, *, framework=None, verifier=None, required_checks=(), limits=None):
    """Read-only advisory result. Host-owned requirements are passed separately.

    Caller must supply current measured framework identity and an independently
    trusted verifier. Configuration is untrusted data; accepted/verifier/command
    fields in it are never evaluated or used to select trusted code.
    """
    result = dict(local_state='unverified', reason='disabled', offer=None,
                  required_checks=list(required_checks), assurance='unassessed',
                  execution_authorized=False, governance_adopted=False)
    try:
        if type(config) is not dict:
            return result
        nodes = InputNodes()
        if len(config) + 1 > nodes.remaining:
            raise ObservationError('configuration-too-many-items')
        nodes.visit()
        enabled = declined = authoring = None
        # Do not perform lookups on the original dictionary. A colliding opaque
        # key can execute __eq__ during .get(), even when config is an exact dict.
        # Only references to the three flags are retained; unknown values are
        # neither inspected nor snapshotted on disabled/declined paths.
        for key, value in config.items():
            nodes.visit()
            if type(key) is not str:
                raise ObservationError('invalid-configuration-type')
            if key == 'enabled':
                nodes.visit()
                enabled = value
            elif key == 'declined':
                nodes.visit()
                declined = value
            elif key == 'authoring_method':
                nodes.visit()
                authoring = value
        if enabled is not True:
            return result
        if declined is True:
            return result | {'reason': 'declined'}
        if authoring is not None and type(authoring) is not str:
            raise ObservationError('invalid-configuration-type')
        if type(authoring) is str and authoring in ('direct', 'alternate'):
            return result | {'reason': 'declined'}
        if limits is None:
            limits = Limits()
        elif type(limits) is not Limits:
            raise ObservationError('invalid-observation-bound')
        config = bounded_snapshot(config, limits.configuration_bytes, _nodes=nodes)
        catalogue = bounded_snapshot(catalogue, limits.configuration_bytes, _nodes=nodes)
        validate_catalogue(catalogue)
        skill = route(config.get('task_kind'))
        if skill is None or config.get('selected_skill') != skill:
            return result | {'reason': 'no-selected-contextual-route'}
        selected = [e for e in catalogue['entries'] if e['skill'] == skill and
                    config.get('task_kind') in e['task_applicability']]
        if not selected:
            return result | {'reason': 'no-catalogue-entry'}
        entry = selected[0]
        if entry['status'] == 'withdrawn':
            return result | {'local_state': 'withdrawn', 'reason': 'withdrawn'}
        if entry['status'] != 'recommended':
            return result | {'reason': 'preactivation'}
        if config.get('format_version') != FORMAT:
            return result | {'reason': 'unsupported-observation-format'}
        if not isinstance(framework, FrameworkIdentity):
            return result | {'reason': 'framework-identity-unavailable'}
        if framework.data() != entry['tested_framework']:
            return result | {'local_state': 'incompatible', 'reason': 'framework-pair-mismatch'}
        observation = observe(config.get('root'), config.get('package'),
                              config.get('inventory'), config.get('entrypoint'), limits)
        if not isinstance(verifier, HostVerifier):
            return result | {'reason': 'qualification-verifier-unavailable'}
        binding = qualification_binding(catalogue, entry, framework, observation, config['entrypoint'])
        proof = verifier.verify(binding)
        if (not isinstance(proof, VerifiedQualification) or proof.binding_sha256 != digest(binding) or
                proof.proof_sha256 != entry['qualification']['sha256'] or
                proof.producer != entry['qualification']['producer'] or
                proof.released is not True or proof.supported_mapping is not True):
            return result | {'reason': 'qualification-not-accepted'}
        return result | {'local_state': 'compatible', 'reason': 'trusted-exact-released-pair',
                         'offer': {'skill': skill, 'entrypoint': os.path.join(config['root'], config['package'], config['entrypoint']),
                                   'host_observation_sha256': observation},
                         'limitations': list(proof.limitations)}
    except MissingPackage:
        return result | {'local_state': 'missing', 'reason': 'package-missing'}
    except UnsupportedHost:
        return result | {'reason': 'nofollow-unsupported'}
    except ObservationError as exc:
        return result | {'local_state': 'incompatible', 'reason': str(exc)}
    except Exception:
        # A failing host adapter cannot turn an advisory lookup into core failure.
        # Diagnostics never disclose an adapter exception or package value.
        return result | {'reason': 'local-observation-unavailable'}


def read_json(path, limit):
    # Configuration/catalogue bytes only. No package body or command is parsed.
    with open(path, 'rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('configuration-too-large')
    def unique(pairs):
        value = {}
        for key, child in pairs:
            if key in value:
                raise ValueError('duplicate-json-key')
            value[key] = child
        return value
    return json.loads(raw, object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--catalogue', default=str(Path(__file__).with_name('recommended_skills.json')))
    args = parser.parse_args()
    try:
        config = read_json(args.config, Limits().configuration_bytes)
        catalogue = read_json(args.catalogue, Limits().configuration_bytes)
        result = resolve(config, catalogue)  # No CLI-selected trusted code.
    except (OSError, ValueError, TypeError, RecursionError):
        result = {'local_state': 'unverified', 'reason': 'invalid-local-configuration', 'offer': None}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
