#!/usr/bin/env python3
"""Finite, released external-tool operations; no Nizam product execution."""
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[3]
RELEASE_PATH = ROOT / '.agent/evidence/123/root-gh-collector-repair1-execution-release.json'
RELEASE = json.loads(RELEASE_PATH.read_bytes())
BUILD = Path(RELEASE['build_root'])
OUT = ROOT / RELEASE['paths']['raw_capture']
ENV = RELEASE['environment'].copy()
REV = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
LIMIT = 8 * 1024 * 1024
RESULTS = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write(name, value):
    path = OUT / name
    with path.open('x') as f:
        json.dump(value, f, separators=(',', ':'))
        f.write('\n')
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def cache_size(path):
    total = 0
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            s = os.lstat(Path(parent) / name)
            if stat.S_ISLNK(s.st_mode):
                raise ValueError('unexpected cache symlink')
            if stat.S_ISREG(s.st_mode):
                total += s.st_size
    return total


def run(name, argv, cwd, seconds, expected=0, pass_fds=(), guard=None):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    tick = time.monotonic()
    p = subprocess.Popen(argv, cwd=cwd, env=ENV, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True, pass_fds=pass_fds)
    sel = selectors.DefaultSelector()
    files, counts, hashes = {}, {}, {}
    for label, pipe in [('stdout', p.stdout), ('stderr', p.stderr)]:
        sel.register(pipe, selectors.EVENT_READ, label)
        files[label] = (OUT / (name + '.' + label)).open('xb')
        counts[label], hashes[label] = 0, hashlib.sha256()
    stop, checked = None, tick
    while sel.get_map():
        try:
            if time.monotonic() - tick > seconds:
                raise ValueError('wall limit')
            if guard:
                guard()
            if time.monotonic() - checked > 2:
                for cache in ('gocache', 'gomodcache', 'gopath'):
                    if cache_size(BUILD / cache) > 4 * 1024**3:
                        raise ValueError('cache size limit')
                checked = time.monotonic()
        except Exception as exc:
            if stop is None:
                stop = str(exc)
                os.killpg(p.pid, signal.SIGKILL)
        for key, _ in sel.select(.05):
            b = os.read(key.fd, 65536)
            if not b:
                sel.unregister(key.fileobj)
                key.fileobj.close()
                continue
            label = key.data
            spare = max(0, LIMIT - counts[label])
            kept = b[:spare]
            files[label].write(kept)
            counts[label] += len(kept)
            hashes[label].update(kept)
            if len(kept) != len(b) and stop is None:
                stop = 'stream bound; excess not retained'
                os.killpg(p.pid, signal.SIGKILL)
    code = p.wait()
    for f in files.values():
        f.close()
    frame = {'argv': argv, 'cwd': str(cwd), 'nizam_revision': REV,
             'environment_allowlist': ENV.copy(), 'started_at': started,
             'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
             'elapsed_seconds': time.monotonic() - tick, 'pid': p.pid,
             'actual_exit': code, 'expected_exit': expected, 'stop': stop,
             'streams_complete': stop is None, 'wall_seconds': seconds,
             'stdout_stderr_bound_each': LIMIT}
    for label in counts:
        frame[label] = {'path': str((OUT / (name + '.' + label)).relative_to(ROOT)),
                        'bytes': counts[label], 'sha256': hashes[label].hexdigest()}
    RESULTS.append(write(name + '.execution.json', frame))
    print(name, 'actual_exit', code, 'elapsed', round(frame['elapsed_seconds'], 3), flush=True)
    if stop or code != expected:
        raise RuntimeError('STOP unexpected command result: ' + name)
    return (OUT / (name + '.stdout')).read_bytes()


def download():
    pin = RELEASE['sdk_download']
    url, tick = pin['url'], time.monotonic()
    chain = []
    for hop in range(pin['max_redirects'] + 1):
        u = urllib.parse.urlsplit(url)
        assert u.scheme == 'https' and u.hostname in pin['allowed_https_hosts']
        assert not u.username and not u.password and not u.fragment and u.port in (None, 443)
        body = BUILD / ('sdk-hop' + str(hop) + '.body')
        fd = os.open(body, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        headers = OUT / ('sdk-hop' + str(hop) + '.headers')
        headers.open('xb').close()
        remaining = pin['timeout_seconds'] - (time.monotonic() - tick)
        assert remaining > 0
        argv = ['/usr/bin/curl', '-q', '--proto', '=https', '--http1.1',
                '--max-redirs', '0', '--retry', '0', '--connect-timeout', '10',
                '--max-time', str(remaining), '--max-filesize', str(pin['size']),
                '--silent', '--show-error', '--fail-with-body', '--dump-header', str(headers),
                '--output', '/proc/self/fd/' + str(fd), '--url', url]
        def guard():
            assert time.monotonic() - tick <= pin['timeout_seconds']
            assert os.fstat(fd).st_size <= pin['size'] and headers.stat().st_size <= 65536
        try:
            run('sdk-hop' + str(hop), argv, ROOT, remaining, pass_fds=(fd,), guard=guard)
        finally:
            os.close(fd)
        blocks = [b for b in headers.read_bytes().split(b'\r\n\r\n') if b.startswith(b'HTTP/')]
        lines = blocks[-1].split(b'\r\n')
        status = int(lines[0].split()[1])
        chain.append({'url': url, 'status': status, 'body_path': str(body),
                      'body_bytes': body.stat().st_size, 'body_sha256': sha(body),
                      'headers_path': str(headers.relative_to(ROOT)), 'headers_sha256': sha(headers)})
        write('sdk-hop' + str(hop) + '.http.json', chain[-1])
        if status in (301, 302, 303, 307, 308):
            locations = [l.split(b':', 1)[1].strip().decode('ascii') for l in lines[1:]
                         if l.lower().startswith(b'location:')]
            assert len(locations) == 1 and hop < pin['max_redirects']
            url = urllib.parse.urljoin(url, locations[0])
            continue
        assert status == 200 and body.stat().st_size == pin['size'] and sha(body) == pin['sha256']
        target = Path(pin['destination'])
        assert not target.exists()
        body.rename(target)
        write('sdk-download.json', {'chain': chain, 'archive': str(target), 'bytes': pin['size'],
                                    'sha256': pin['sha256'], 'elapsed_seconds': time.monotonic() - tick})
        print('SDK exact size and checksum matched', flush=True)
        return target
    raise ValueError('redirect bound')


def extract(archive):
    cfg, tick = RELEASE['extraction'], time.monotonic()
    rows, seen, total = [], set(), 0
    with gzip.open(archive, 'rb') as f:
        while True:
            assert time.monotonic() - tick < cfg['seconds']
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
            name = item.name.rstrip('/')
            parts = name.split('/')
            assert len(name.encode()) <= cfg['max_path_bytes'] and parts[0] == 'go'
            assert all(x not in ('', '.', '..') for x in parts) and not any(x in name for x in ('\\', '\0', ':'))
            assert name not in seen and item.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
            seen.add(name)
            assert len(seen) <= cfg['max_entries'] and 0 <= item.size <= cfg['max_file_bytes']
            target = Path(RELEASE['paths']['sdk']).joinpath(*parts)
            for parent in [Path(RELEASE['paths']['sdk'])] + list(target.parents)[:-1][::-1]:
                if parent == Path(RELEASE['paths']['sdk']) or Path(RELEASE['paths']['sdk']) in parent.parents:
                    parent.mkdir(mode=0o700, exist_ok=True)
                    assert parent.is_dir() and not parent.is_symlink()
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
                        b = f.read(min(left, 1024 * 1024))
                        assert b
                        dest.write(b)
                        h.update(b)
                        left -= len(b)
                assert len(f.read((-item.size) % 512)) == (-item.size) % 512
                digest = h.hexdigest()
            os.chmod(target, mode, follow_symlinks=False)
            rows.append({'path': name, 'type': 'directory' if item.isdir() else 'file',
                         'bytes': item.size, 'sha256': digest, 'original_mode': item.mode,
                         'effective_mode': mode})
    result = write('sdk-members-before-go.json', {'rows': rows, 'total_file_bytes': total,
                                                  'elapsed_seconds': time.monotonic() - tick})
    print('SDK member inventory frozen before Go:', len(rows), 'entries', flush=True)
    return result


def manifest():
    rows = []
    for label in ('gomodcache', 'gopath'):
        start = BUILD / label
        for parent, dirs, files in os.walk(start, followlinks=False):
            for name in sorted(dirs + files):
                path = Path(parent) / name
                s = path.lstat()
                assert stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)
                rows.append([str(path.relative_to(BUILD)), s.st_mode, s.st_nlink,
                             s.st_size if stat.S_ISREG(s.st_mode) else None,
                             sha(path) if stat.S_ISREG(s.st_mode) else None])
                assert len(rows) <= 200000
    rows.sort()
    return rows


def main():
    assert not BUILD.exists() and not OUT.exists()
    BUILD.mkdir(mode=0o700)
    OUT.mkdir()
    state_pin = sha(ROOT / '.agent/run_state.json')
    test = subprocess.check_output(['git', 'show', RELEASE['test_pin']['revision'] + ':' + RELEASE['test_pin']['path']], cwd=ROOT)
    assert hashlib.sha256(test).hexdigest() == RELEASE['test_pin']['sha256']
    for folder in ('sdk', 'home', 'tmp', 'gocache', 'gomodcache', 'gopath', 'bin'):
        (BUILD / folder).mkdir(mode=0o700)
    archive = download()
    sdk_pin = extract(archive)
    modules = {}
    for label, commit in [('baseline', RELEASE['source']['baseline']), ('patched', RELEASE['source']['patched'])]:
        path = BUILD / label
        run(label + '-clone', ['/usr/bin/git', 'clone', '--no-hardlinks', '--no-checkout', RELEASE['source']['upstream_owned_clone'], str(path)], BUILD, 60)
        path.chmod(0o700)
        run(label + '-checkout', ['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', commit], path, 30)
        assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip() == commit
        dest = path / RELEASE['test_pin']['destination']
        with dest.open('xb') as f:
            f.write(test)
        modules[label] = {name: sha(path / name) for name in ('go.mod', 'go.sum')}
    assert modules['baseline'] == modules['patched']
    write('source-test-pins.json', {'source': RELEASE['source'], 'test_sha256': RELEASE['test_pin']['sha256'], 'module_hashes': modules})
    commands = RELEASE['commands']
    for i in range(3):
        c = commands[i]
        run('command' + str(i), c['argv'], Path(c['cwd']), c['seconds'], c['expected_exit'])
    frozen = manifest()
    frozen_pin = write('module-cache-before-offline.json', {'rows': frozen})
    for label in modules:
        assert modules[label] == {name: sha(BUILD / label / name) for name in ('go.mod', 'go.sum')}
    print('Dependency download and go mod verify completed; module manifest frozen', flush=True)
    ENV.update(GOPROXY='off', GOSUMDB='off')
    for i in range(3, len(commands)):
        c = commands[i]
        data = run('command' + str(i), c['argv'], Path(c['cwd']), c['seconds'], c['expected_exit'])
        if i == 3:
            names = set(re.findall(rb'^--- FAIL: (TestWA123CollectorRepair\w+)', data, re.M))
            wanted = {b'TestWA123CollectorRepair' + x for x in (b'LongLineThenMarker', b'FiniteLineBoundary', b'OverLimitReturnsError', b'ReaderError', b'WriterError')}
            assert names == wanted and b'[build failed]' not in data and b'undefined:' not in data
        if i == 6:
            assert b'2.76.2+nizam-logfix.1' in data
        assert manifest() == frozen
        for label in modules:
            assert modules[label] == {name: sha(BUILD / label / name) for name in ('go.mod', 'go.sum')}
        print('Pinned module content preserved after command', i, flush=True)
    sdk = json.loads((ROOT / sdk_pin['path']).read_bytes())
    for row in sdk['rows']:
        path = Path(RELEASE['paths']['sdk']) / row['path']
        assert stat.S_IMODE(path.lstat().st_mode) == row['effective_mode']
        if row['type'] == 'file':
            assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    assert sha(ROOT / '.agent/run_state.json') == state_pin
    binary = Path(RELEASE['paths']['binary'])
    write('execution-result.json', {'status': 'actual outcomes only; no passing verdict',
          'release': str(RELEASE_PATH.relative_to(ROOT)), 'revision': REV,
          'sdk_inventory': sdk_pin, 'module_inventory': frozen_pin,
          'binary': {'path': str(binary), 'bytes': binary.stat().st_size,
                     'sha256': sha(binary), 'mode': stat.S_IMODE(binary.stat().st_mode)},
          'frames': RESULTS, 'baseline_expected_assertions_observed': True,
          'module_content_and_go_mod_sum_unchanged': True, 'sdk_unchanged': True,
          'root_state_unchanged': True, 'real_log_or_five_fetch': False})
    print('Released stages complete; private binary hash', sha(binary), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        if OUT.exists():
            write('stopped.json', {'exception': type(exc).__name__, 'diagnostic': str(exc),
                                 'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'frames': RESULTS,
                                 'no_retry': True})
        print('STOP:', type(exc).__name__, str(exc), file=sys.stderr, flush=True)
        raise
