#!/usr/bin/env python3
"""Bounded native Linux inotify/SCM_RIGHTS mechanism qualification, not product QA."""
import array
import ctypes
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import time

libc = ctypes.CDLL(None, use_errno=True)
libc.inotify_init1.argtypes = [ctypes.c_int]
libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
MASK = 0x2 | 0x4 | 0x8 | 0x40 | 0x80 | 0x100 | 0x200 | 0x400 | 0x800

def watch(fd, path):
    value = libc.inotify_add_watch(fd, os.fsencode(path), MASK | 0x02000000)
    assert value >= 0, (path, ctypes.get_errno())
    return value

def fresh():
    value = libc.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK)
    assert value >= 0, ctypes.get_errno()
    return value

def drain(fd):
    rows = []
    while True:
        try:
            raw = os.read(fd, 65536)
        except BlockingIOError:
            return rows
        at = 0
        while at < len(raw):
            wd, mask, cookie, count = struct.unpack_from('iIII', raw, at)
            rows.append([wd, mask, cookie, os.fsdecode(raw[at+16:at+16+count].rstrip(b'\0'))])
            at += 16 + count
        assert at == len(raw)

start = time.monotonic()
checks = {}
with tempfile.TemporaryDirectory(prefix='nizam-monitor-qualification-') as tmp:
    root = Path(tmp)
    parent = root / 'parent'
    parent.mkdir()
    sub = parent / 'records'
    sub.mkdir()
    file = sub / 'attempt.json'
    file.write_text('original')
    fd = fresh()
    ancestor = watch(fd, root)
    directory = watch(fd, parent)
    leaf = watch(fd, sub)
    # Monitoring is installed before snapshot; every post-install mutation is visible.
    file.write_text('during-collection')
    rows = drain(fd)
    assert any(wd == leaf and name == file.name and mask & 0xa for wd, mask, _, name in rows)
    checks['mutation_during_collection'] = rows
    temporary = sub / 'replacement'
    temporary.write_text('replacement')
    os.replace(temporary, file)
    rows = drain(fd)
    assert any(wd == leaf and name == file.name and mask & 0x80 for wd, mask, _, name in rows)
    checks['atomic_path_replacement'] = rows
    os.rename(sub, parent / 'moved-records')
    rows = drain(fd)
    assert any(wd == directory and name == 'records' and mask & 0x40 for wd, mask, _, name in rows)
    assert any(wd == leaf and mask & 0x800 for wd, mask, _, _ in rows)
    checks['directory_rename_and_ancestor_coverage'] = rows
    os.rename(parent, root / 'moved-parent')
    rows = drain(fd)
    assert any(wd == ancestor and name == 'parent' and mask & 0x40 for wd, mask, _, name in rows)
    checks['ancestor_replacement_visible'] = rows
    lost = root / 'lost'
    lost.mkdir()
    wd = watch(fd, lost)
    lost.rmdir()
    rows = drain(fd)
    assert any(w == wd and mask & 0x400 for w, mask, _, _ in rows)
    assert any(w == wd and mask & 0x8000 for w, mask, _, _ in rows)
    checks['lost_watch_delete_and_ignored'] = rows
    os.close(fd)
    # Descriptor transferred from a helper remains a live monitor after that helper exits.
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    pid = os.fork()
    if pid == 0:
        left.close()
        child_fd = fresh()
        child_wd = watch(child_fd, root)
        right.sendmsg([json.dumps({'wd': child_wd}).encode()],
                      [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [child_fd]))])
        os.close(child_fd)
        os._exit(0)
    right.close()
    raw, anc, flags, _ = left.recvmsg(1024, socket.CMSG_SPACE(array.array('i').itemsize))
    assert not flags
    received = array.array('i')
    for level, kind, data in anc:
        assert level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS
        received.frombytes(data)
    assert len(received) == 1
    moved_fd = received[0]
    assert os.waitpid(pid, 0)[1] == 0
    (root / 'after-helper-death').write_text('visible')
    rows = drain(moved_fd)
    assert any(wd == json.loads(raw)['wd'] and name == 'after-helper-death'
               and mask & 0x100 for wd, mask, _, name in rows)
    checks['fd_handoff_and_post_death_lifetime'] = {'pid': pid, 'events': rows}
    os.close(moved_fd)
    left.close()
    maximum = int(Path('/proc/sys/fs/inotify/max_queued_events').read_text())
    assert 0 < maximum <= 131072, maximum
    fd = fresh()
    watch(fd, root)
    for i in range(maximum // 2 + 10):
        path = root / ('overflow-' + str(i))
        path.touch()
        path.unlink()
    rows = drain(fd)
    assert any(wd == -1 and mask & 0x4000 for wd, mask, _, _ in rows)
    checks['native_queue_overflow_fail_closed_signal'] = {'maximum': maximum, 'events': len(rows),
        'overflow_rows': [r for r in rows if r[1] & 0x4000]}
    os.close(fd)
assert time.monotonic() - start < 45
print(json.dumps({'checks': checks, 'elapsed_seconds': time.monotonic()-start,
    'scope': 'Native mechanism primitives only. Product watch coverage and semantic binding still require implementation and independent review.'}, sort_keys=True))
