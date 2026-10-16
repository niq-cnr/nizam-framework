"""Two separately invoked bounded primitive probes; no controller imports."""
import array
import errno
import fcntl
import json
import mmap
import os
from pathlib import Path
import signal
import socket
import sys
import tempfile
import time

signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('25s work bound')))
signal.alarm(25)
signal.signal(signal.SIGIO, signal.SIG_IGN)
started = time.monotonic()

def emit(name, **values):
    print(json.dumps(dict(probe=name, pid=os.getpid(), **values), sort_keys=True), flush=True)

def attempt(fn):
    try:
        return dict(ok=True, result=fn())
    except OSError as error:
        return dict(ok=False, errno=error.errno, name=errno.errorcode.get(error.errno))

if sys.argv[1] == 'leases':
    with tempfile.TemporaryDirectory(prefix='nizam-readlease-') as temporary:
        path = Path(temporary) / 'authority.json'
        path.write_bytes(b'{"attempt":1}\n')
        writer = os.open(path, os.O_RDWR)
        reader = os.open(path, os.O_RDONLY)
        mapping = mmap.mmap(writer, 0, access=mmap.ACCESS_WRITE)
        with_writer = attempt(lambda: fcntl.fcntl(reader, fcntl.F_SETLEASE, fcntl.F_RDLCK))
        assert not with_writer['ok'] and with_writer['errno'] == errno.EAGAIN
        os.close(writer)
        with_mapping = attempt(lambda: fcntl.fcntl(reader, fcntl.F_SETLEASE, fcntl.F_RDLCK))
        assert not with_mapping['ok'] and with_mapping['errno'] == errno.EAGAIN
        mapping[11:12] = b'2'
        assert os.pread(reader, 100, 0) == b'{"attempt":2}\n'
        mapping.close()
        acquired = attempt(lambda: fcntl.fcntl(reader, fcntl.F_SETLEASE, fcntl.F_RDLCK))
        assert acquired['ok']
        duplicate = os.dup(reader)
        os.close(reader)
        assert fcntl.fcntl(duplicate, fcntl.F_GETLEASE) == fcntl.F_RDLCK
        replacement = Path(temporary) / 'replacement'
        replacement.write_bytes(b'{"attempt":3}\n')
        os.replace(replacement, path)
        current = path.read_bytes().decode()
        retained = os.pread(duplicate, 100, 0).decode()
        lease_after_replace = fcntl.fcntl(duplicate, fcntl.F_GETLEASE)
        assert current != retained and lease_after_replace == fcntl.F_RDLCK
        directory_fd = os.open(temporary, os.O_RDONLY | os.O_DIRECTORY)
        directory_lease = attempt(lambda: fcntl.fcntl(directory_fd, fcntl.F_SETLEASE, fcntl.F_RDLCK))
        assert not directory_lease['ok'] and directory_lease['errno'] == errno.EINVAL
        os.close(directory_fd)
        fcntl.fcntl(duplicate, fcntl.F_SETLEASE, fcntl.F_UNLCK)
        os.close(duplicate)
        emit('leases', existing_writer=with_writer, existing_mapping_after_writer_close=with_mapping,
             acquired_after_unmap=acquired, retained_fd_bytes=retained, pathname_bytes=current,
             lease_after_namespace_replace=lease_after_replace, directory_lease=directory_lease,
             host_lease_break_seconds=Path('/proc/sys/fs/lease-break-time').read_text().strip(),
             limit='No timer expiry, global namespace exclusion or complete event protocol tested')
elif sys.argv[1] == 'seals':
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    child_pid = os.fork()
    if child_pid == 0:
        parent.close()
        try:
            fd = os.memfd_create('nizam-immutable-input', os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
            os.write(fd, b'{"attempt":1}\n')
            writer_fd = os.dup(fd)
            mapping = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)
            with_mapping = attempt(lambda: fcntl.fcntl(fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE))
            assert not with_mapping['ok'] and with_mapping['errno'] == errno.EBUSY
            mapping.close()
            seals = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
            fcntl.fcntl(fd, fcntl.F_ADD_SEALS, seals)
            old_writer = attempt(lambda: os.pwrite(writer_fd, b'2', 11))
            new_mapping = attempt(lambda: mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE))
            assert not old_writer['ok'] and old_writer['errno'] == errno.EPERM
            assert not new_mapping['ok'] and new_mapping['errno'] == errno.EPERM
            data = json.dumps(dict(existing_mapping=with_mapping, already_open_writer=old_writer,
                                   new_shared_mapping=new_mapping, seals=seals)).encode()
            child.sendmsg([data], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd]))])
            os.close(writer_fd)
            os.close(fd)
        except BaseException as error:
            child.send(json.dumps(dict(error=repr(error))).encode())
            os._exit(2)
        os._exit(0)
    child.close()
    parent.settimeout(5)
    try:
        data, ancillary, flags, _ = parent.recvmsg(4096, socket.CMSG_SPACE(array.array('i').itemsize))
        assert flags == 0 and len(ancillary) == 1
        level, kind, rights = ancillary[0]
        assert (level, kind) == (socket.SOL_SOCKET, socket.SCM_RIGHTS)
        descriptors = array.array('i')
        descriptors.frombytes(rights[:array.array('i').itemsize])
        fd = descriptors[0]
        pid, status = os.waitpid(child_pid, 0)
        assert pid == child_pid and os.waitstatus_to_exitcode(status) == 0
        content = os.pread(fd, 100, 0).decode()
        metadata = json.loads(data)
        assert fcntl.fcntl(fd, fcntl.F_GET_SEALS) == metadata['seals']
        after_helper_death = attempt(lambda: os.pwrite(fd, b'2', 11))
        assert not after_helper_death['ok'] and after_helper_death['errno'] == errno.EPERM
        os.close(fd)
        emit('seals', helper_pid=pid, helper_exit=0, content_after_helper_death=content,
             after_helper_death_write=after_helper_death, **metadata,
             limit='Seals bind copied input bytes only; they neither freeze nor certify current original paths')
    finally:
        parent.close()
        try:
            pid, _ = os.waitpid(child_pid, os.WNOHANG)
            if not pid:
                os.kill(child_pid, signal.SIGKILL)
                os.waitpid(child_pid, 0)
        except ChildProcessError:
            pass
else:
    raise SystemExit('unknown probe')
emit('complete', elapsed_seconds=time.monotonic()-started)
