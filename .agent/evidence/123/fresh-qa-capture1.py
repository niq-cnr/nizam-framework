#!/usr/bin/env python3
"""Evaluator operational capture only; execution needs a separate Root release."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def json_file(path, value):
    write(path, json.dumps(value, indent=2, sort_keys=True).encode() + b'\n')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def inventory(root, sentinel):
    tracked = git(root, 'ls-files', '-z').split(b'\0')[:-1]
    untracked = git(root, 'ls-files', '--others', '-z').split(b'\0')[:-1]
    rows = []
    directories = {}
    for relative in sorted(set(tracked + untracked)):
        name = os.fsdecode(relative)
        target = root / name
        current = root
        for component in Path(name).parts[:-1]:
            current = current / component
            info = current.lstat()
            assert stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), str(current)
            directories[str(current.relative_to(root))] = dict(mode=info.st_mode, symlink=stat.S_ISLNK(info.st_mode))
        info = target.lstat()
        row = dict(path=name, mode=info.st_mode, nlink=info.st_nlink, size=info.st_size)
        if stat.S_ISREG(info.st_mode):
            row['sha256'] = sha(target.read_bytes())
        elif stat.S_ISLNK(info.st_mode):
            row['symlink'] = os.readlink(target)
        else:
            raise RuntimeError('nonregular tracked/untracked path: ' + name)
        rows.append(row)
    info = sentinel.lstat()
    return dict(rows=rows, directories=directories, tracked=[os.fsdecode(p) for p in tracked],
                untracked=[os.fsdecode(p) for p in untracked],
                head=git(root, 'rev-parse', 'HEAD').decode().strip(),
                tree=git(root, 'rev-parse', 'HEAD^{tree}').decode().strip(),
                origin=git(root, 'remote', 'get-url', 'origin').decode().strip(),
                refs=git(root, 'show-ref').decode(),
                status=git(root, 'status', '--porcelain', '--untracked-files=all').decode(),
                sentinel=dict(path=str(sentinel), mode=info.st_mode, nlink=info.st_nlink,
                              size=info.st_size, sha256=sha(sentinel.read_bytes())))


def saved_inventory(directory, name, value):
    raw = canonical(value)
    path = directory / (name + '.json.gz')
    write(path, gzip.compress(raw, mtime=0))
    return dict(path=str(path), sha256=sha(path.read_bytes()), inventory_sha256=sha(raw),
                rows=len(value['rows']), installed=sum(r['path'].startswith('.nizam/') for r in value['rows']))


def execute(root, directory, name, argv, timeout, input_bytes=None):
    started = now()
    monotonic = time.monotonic()
    stdout = directory / (name + '.stdout.txt')
    stderr = directory / (name + '.stderr.txt')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    input_path = None
    if input_bytes is not None:
        input_path = directory / (name + '.stdin')
        write(input_path, input_bytes)
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(argv, cwd=root, env=environment, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                                 stdout=out, stderr=err, start_new_session=True)
        json_file(directory / (name + '.started.json'), dict(argv=argv, cwd=str(root), started_at=started,
                  child_pid=child.pid, exercised_revision=git(root, 'rev-parse', 'HEAD').decode().strip()))
        timed_out = False
        try:
            child.communicate(input=input_bytes, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    result = dict(argv=argv, cwd=str(root), exercised_revision=git(root, 'rev-parse', 'HEAD').decode().strip(),
                  checkout_tree=git(root, 'rev-parse', 'HEAD^{tree}').decode().strip(),
                  started_at=started, ended_at=now(), elapsed_seconds=time.monotonic()-monotonic,
                  child_pid=child.pid, actual_exit=child.returncode, timed_out=timed_out,
                  environment=dict(variables={'PYTHONDONTWRITEBYTECODE':'1'}, runtime=dict(implementation=platform.python_implementation(),
                  version=platform.python_version(), system=platform.system(), machine=platform.machine())),
                  runtime_scope='Actual capture interpreter and inherited environment; command argv retained, no hosted runtime impersonation.',
                  stdin=None if input_path is None else dict(path=str(input_path), sha256=sha(input_bytes), bytes=len(input_bytes)))
    for stream, path in [('stdout', stdout), ('stderr', stderr)]:
        raw = path.read_bytes()
        result[stream] = dict(path=str(path), sha256=sha(raw), bytes=len(raw))
    json_file(directory / (name + '.execution.json'), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--sentinel', type=Path, required=True)
    parser.add_argument('--expected-exit', type=int, default=0)
    parser.add_argument('--timeout', type=int, default=7200)
    parser.add_argument('--stdin', type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.repo.resolve(strict=True)
    directory = args.output.resolve(strict=True)
    assert directory != root and root not in directory.parents
    assert args.sentinel.is_file() and root not in args.sentinel.resolve().parents
    argv = args.command[1:] if args.command[:1] == ['--'] else args.command
    assert argv and '/' not in args.name and '..' not in args.name
    before = inventory(root, args.sentinel)
    before_ref = saved_inventory(directory, args.name + '.preservation-before', before)
    result = execute(root, directory, args.name, argv, args.timeout,
                     None if args.stdin is None else args.stdin.read_bytes())
    after = inventory(root, args.sentinel)
    after_ref = saved_inventory(directory, args.name + '.preservation-after', after)
    summary = dict(command_execution=str(directory / (args.name+'.execution.json')),
                   expected_exit=args.expected_exit, actual_exit=result['actual_exit'],
                   before=before_ref, after=after_ref, preservation_equal=before == after,
                   capture_driver_sha256=sha(Path(__file__).read_bytes()),
                   source_bindings={p:sha((root/p).read_bytes()) for p in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py')},
                   success=(result['actual_exit']==args.expected_exit and not result['timed_out'] and before==after))
    json_file(directory / (args.name+'.capture-summary.json'), summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
