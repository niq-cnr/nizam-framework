#!/usr/bin/env python3
"""Native coverage counterexample; no controller import or execution."""
import ctypes
import json
import mmap
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

start = time.monotonic()
libc = ctypes.CDLL(None, use_errno=True)
libc.inotify_init1.argtypes = [ctypes.c_int]
libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
mask = 0x2 | 0x4 | 0x8 | 0x40 | 0x80 | 0x100 | 0x200 | 0x400 | 0x800
with tempfile.TemporaryDirectory(prefix='nizam-monitor-coverage-') as temporary:
    directory = Path(temporary)
    path = directory / 'attempt.json'
    before = b'{"attempts":1}\n'
    after = b'{"attempts":2}\n'
    path.write_bytes(before)
    writer = os.open(path, os.O_RDWR)
    mapping = mmap.mmap(writer, 0, access=mmap.ACCESS_WRITE)
    fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    assert fd >= 0
    watches = {}
    for label, target in [('directory', directory), ('inode', path)]:
        wd = libc.inotify_add_watch(fd, os.fsencode(target), mask | 0x02000000)
        assert wd >= 0
        watches[label] = wd
    # A regular working-path write reports an event on these very watches.
    path.write_bytes(before)
    positive = os.read(fd, 65536)
    assert positive
    snapshot = path.read_bytes()
    assert snapshot == before
    stamp_before = path.stat()
    mapping[:] = after
    mapping.flush()
    observed = path.read_bytes()
    stamp_after = path.stat()
    rows = []
    try:
        raw = os.read(fd, 65536)
    except BlockingIOError:
        raw = b''
    at = 0
    while at < len(raw):
        wd, event, cookie, count = struct.unpack_from('iIII', raw, at)
        rows.append({'wd': wd, 'mask': event, 'cookie': cookie,
                     'name': os.fsdecode(raw[at+16:at+16+count].rstrip(b'\0'))})
        at += 16 + count
    hidden = observed == after and observed != snapshot and not rows
    # Observe while the proven writer and mapping remain open; their later
    # close cannot retroactively make a publication-time epoch check current.
    print(json.dumps({'scope': 'Native primitive coverage, no product/runtime/acceptance execution',
        'positive_event_bytes': len(positive), 'watches': watches,
        'snapshot_hex': snapshot.hex(), 'current_hex': observed.hex(),
        'writer_still_open': os.fstat(writer).st_ino == path.stat().st_ino,
        'mapping_still_open': not mapping.closed,
        'events_after_shared_mapping_write': rows,
        'mtime_ns': [stamp_before.st_mtime_ns, stamp_after.st_mtime_ns],
        'ctime_ns': [stamp_before.st_ctime_ns, stamp_after.st_ctime_ns],
        'unobserved_authoritative_mutation': hidden,
        'elapsed_seconds': time.monotonic()-start}, sort_keys=True), flush=True)
    mapping.close()
    os.close(writer)
    os.close(fd)
    if hidden:
        print('MONITOR_COVERAGE_UNSOUND: shared mmap changed certified bytes while both directory and inode watches remained silent', file=sys.stderr)
        sys.exit(1)
    if observed != after:
        print('UNEXPECTED_NATIVE_WRITE_FAILURE', file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
