#!/usr/bin/env python3
"""Attempt 2: frozen operational controls plus two exact SDK PAX paths only."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / '.agent/evidence/123/gh-collector-repair1-control.py'
BINDINGS = ROOT / '.agent/evidence/123/gh-collector-repair2-preparation/sdk-exact-pax-bindings.json'
ARCHIVE = Path('/home/cnross/.tmp/nizam-gh-collector-repair1-build/go1.24.5.linux-amd64.tar.gz')
BUILD = Path('/home/cnross/.tmp/nizam-gh-collector-repair2-build')


def extract(b, archive):
    assert hashlib.sha256(BINDINGS.read_bytes()).hexdigest() == '1294a2ec56f89c83fc1ee77910c9f8db47b3cdc5e1086d65142103b5b8808743'
    exact = json.loads(BINDINGS.read_bytes())['metadata']
    assert len(exact) == 2
    expected = {x['raw_index']: x for x in exact}
    cfg, tick = b.RELEASE['extraction'], time.monotonic()
    rows, seen, total, raw_index, consumed, pending = [], set(), 0, 0, [], None
    with gzip.open(archive, 'rb') as f:
        while True:
            assert time.monotonic() - tick < cfg['seconds'] and raw_index < cfg['max_entries']
            block = f.read(512)
            if block == bytes(512):
                assert f.read(512) == bytes(512)
                while True:
                    tail = f.read(65536)
                    if not tail:
                        break
                    assert not tail.strip(b'\0') and time.monotonic() - tick < cfg['seconds']
                break
            assert len(block) == 512
            item = tarfile.TarInfo.frombuf(block, 'utf-8', 'strict')
            header_sha = hashlib.sha256(block).hexdigest()
            original_name, name = item.name, item.name.rstrip('/')
            if item.type == b'x':
                assert pending is None and raw_index in expected
                e = expected[raw_index]
                assert item.name == e['name'] and item.size == e['size'] and item.mode == e['mode']
                assert header_sha == e['header_sha256'] and item.size <= 4096
                payload = f.read(item.size)
                assert len(payload) == item.size and hashlib.sha256(payload).hexdigest() == e['payload_sha256']
                assert payload == e['payload_UTF8'].encode('utf-8')
                assert len(f.read((-item.size) % 512)) == (-item.size) % 512
                pending = e
                consumed.append(raw_index)
                raw_index += 1
                continue
            if pending is not None:
                e = pending['next_member']
                assert item.type in (tarfile.REGTYPE, tarfile.AREGTYPE)
                assert (raw_index, item.name, item.type.hex(), item.size, item.mode, header_sha) == (
                    e['raw_index'], e['name'], e['type_hex'], e['size'], e['mode'], e['header_sha256'])
                payload = pending['payload_UTF8'].encode('utf-8')
                assert payload.startswith(str(len(payload)).encode() + b' path=') and payload.endswith(b'\n')
                name = payload.split(b' path=', 1)[1][:-1].decode('utf-8')
                pending = None
            parts = name.split('/')
            assert len(name.encode()) <= cfg['max_path_bytes'] and parts[0] == 'go'
            assert all(x not in ('', '.', '..') for x in parts) and not any(x in name for x in ('\\', '\0', ':'))
            assert name not in seen and item.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
            seen.add(name)
            assert len(seen) <= cfg['max_entries'] and 0 <= item.size <= cfg['max_file_bytes']
            target = Path(b.RELEASE['paths']['sdk']).joinpath(*parts)
            for parent in [Path(b.RELEASE['paths']['sdk'])] + list(target.parents)[:-1][::-1]:
                if parent == Path(b.RELEASE['paths']['sdk']) or Path(b.RELEASE['paths']['sdk']) in parent.parents:
                    parent.mkdir(mode=0o700, exist_ok=True)
                    assert parent.is_dir() and not parent.is_symlink() and stat.S_IMODE(parent.stat().st_mode) == 0o700
            mode, digest = 0o700 if item.isdir() or item.mode & 0o111 else 0o600, None
            if item.isdir():
                assert item.size == 0
                target.mkdir(mode=0o700, exist_ok=True)
                assert target.is_dir() and not target.is_symlink()
            else:
                total += item.size
                assert total <= cfg['max_total_bytes']
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
                h, left = hashlib.sha256(), item.size
                with os.fdopen(fd, 'wb') as dest:
                    while left:
                        assert time.monotonic() - tick < cfg['seconds']
                        data = f.read(min(left, 1024 * 1024))
                        assert data
                        dest.write(data)
                        h.update(data)
                        left -= len(data)
                assert len(f.read((-item.size) % 512)) == (-item.size) % 512
                digest = h.hexdigest()
            os.chmod(target, mode, follow_symlinks=False)
            rows.append({'path': name, 'original_header_name': original_name,
                         'type': 'directory' if item.isdir() else 'file', 'bytes': item.size,
                         'sha256': digest, 'original_mode': item.mode, 'effective_mode': mode})
            raw_index += 1
    assert pending is None and consumed == [13638, 13640] and raw_index == 15737 and len(rows) == 15735
    result = b.write('sdk-members-before-go.json', {'rows': rows, 'total_file_bytes': total,
                     'exact_metadata': exact, 'raw_header_count': raw_index,
                     'elapsed_seconds': time.monotonic() - tick})
    print('SDK member inventory frozen before Go:', len(rows), 'members; exact two PAX paths', flush=True)
    return result


def main():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == '3b22dc9a95b3031c01cc2606e395e64ba0cacfb7e786696377ed68f4c85de667'
    spec = importlib.util.spec_from_file_location('frozen_collector1', OLD)
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    old_release = b.RELEASE
    b.RELEASE_PATH = ROOT / '.agent/evidence/123/root-gh-collector-repair2-execution-release.json'
    b.RELEASE = json.loads(b.RELEASE_PATH.read_bytes())
    assert b.RELEASE['build_root'] == str(BUILD)
    assert b.RELEASE['source'] == old_release['source'] and b.RELEASE['test_pin'] == old_release['test_pin']
    assert b.RELEASE['extraction'] == old_release['extraction']
    substitute = lambda x: x.replace('nizam-gh-collector-repair1-build', 'nizam-gh-collector-repair2-build')
    assert b.RELEASE['environment'] == {k: substitute(v) for k, v in old_release['environment'].items()}
    expected_commands = json.loads(substitute(json.dumps(old_release['commands'])))
    assert b.RELEASE['commands'] == expected_commands
    b.BUILD, b.OUT, b.ENV = BUILD, ROOT / b.RELEASE['paths']['raw_capture'], b.RELEASE['environment'].copy()
    assert b.OUT == ROOT / '.agent/evidence/123/gh-collector-repair2-execution'
    def reuse():
        s = ARCHIVE.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size == 78563580
        assert b.sha(ARCHIVE) == '10ad9e86233e74c0f6590fe5426895de6bf388964210eac34a6d83f38918ecdc'
        b.write('sdk-reuse.json', {'path': str(ARCHIVE), 'bytes': s.st_size,
                                  'sha256': b.sha(ARCHIVE), 'download_executed': False})
        print('Existing SDK archive rehash matched; no download', flush=True)
        return ARCHIVE
    b.download = reuse
    b.extract = lambda archive: extract(b, archive)
    try:
        b.main()
    except BaseException as exc:
        if b.OUT.exists():
            b.write('stopped.json', {'exception': type(exc).__name__, 'diagnostic': str(exc),
                                    'frames': b.RESULTS, 'no_retry': True})
        raise


if __name__ == '__main__':
    main()
