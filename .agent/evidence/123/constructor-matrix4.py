#!/usr/bin/env python3
"""Root-released engineering supplement only; never a selector, gate or hosted proof.

Preparation is inert. Execution requires the exact frozen helper and a later Root
release. Each child imports the actual test checkout; ROOT is never reassigned.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time
import traceback

# Actual committed author4 checkpoint; never substituted by ambient HEAD.
CHECKPOINT = 'd1fd767bca33f7e54486ebc8542811315fe48bde'
TEST_SHA256 = '06eba273dbfd615df7f0ea3b6b52592ed208f9ec267b52a1e06996488b850f13'
MAIN = '79811ef76df950b8151e2af62637ab7d1df34305'
PINS = {
    'tools/workflow_assurance.py': '2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8',
    'tools/workflow_assurance_ci.py': '7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905',
    '.agent/contracts/123.json': '64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5',
    '.agent/evidence/123/author3-controls.py': '79352536f9db966c73d7552dc5112db08a4fa356d507bf9c6482aef27f06e8bd',
}
PHASES = ('K-baseline', 'M-baseline', 'replay-valid-missing-trials',
    'approval-metadata-missing', 'approval-proposal-stale', 'approval-gate-link-stale',
    'carried-blocker', 'carried-important', 'observer')
GZIP_PATHS = tuple('.agent/evidence/123/source3-controls-' + group + '1.' + stage +
    '.preservation-before.json.gz' for group in ('blocker', 'candidate')
    for stage in ('positive', 'semantic-negative'))
STREAM_LIMIT = 2 * 1024 * 1024
TOTAL_SECONDS = 1800
PHASE_SECONDS = 300


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def worker(repo, scratch, phase):
    """Exact existing functions only; every negative retains its frozen restore."""
    check(Path.cwd() == repo, 'worker actual cwd must equal exercised checkout')
    check(os.environ.get('PYTHONDONTWRITEBYTECODE') == '1', 'explicit bytecode env required')
    for relative, expected in {**PINS, 'tools/test_workflow_assurance.py': TEST_SHA256}.items():
        check(file_sha(repo / relative) == expected, 'worker pin mismatch: ' + relative)
    sys.path.insert(0, str(repo / 'tools'))
    spec = importlib.util.spec_from_file_location('matrix4_actual_frozen_tests', repo / 'tools/test_workflow_assurance.py')
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    check(tests.ROOT == repo, 'test module must derive ROOT from its actual checkout')
    api = tests.load_api()
    check(callable(getattr(api, 'verify_controls_ready', None)), 'executable API required')
    scratch.mkdir()
    fixture = tests.controls_construct(api, scratch)
    tests.controls_call(api, fixture)
    print('ENGINEERING genuine baseline0 ' + phase, flush=True)
    if phase in ('K-baseline', 'M-baseline'):
        return
    if phase == 'observer':
        tests.controls_observer(fixture)
    else:
        rows = tests.controls_defects(phase.startswith('carried-'))
        selected = [row for row in rows if row['name'] == phase]
        check(len(selected) == 1, 'one unchanged named frozen defect required')
        tests.controls_variant(api, fixture, selected[0])
    print('ENGINEERING unchanged assertion and restoration completed ' + phase, flush=True)


class Recorder:
    """Bound child pipes before retention; no capture_output or unbounded reads."""
    def __init__(self, output, deadline):
        self.output = output
        self.deadline = deadline
        self.serial = 0
        self.revisions = {}
        self.outcomes = []

    def command(self, argv, cwd, label, env=None):
        self.serial += 1
        stem = self.output / ('%02d-' % self.serial + label)
        start = time.monotonic()
        start_at = datetime.now(timezone.utc).isoformat()
        reserve = 60 if label in PHASES else 0
        timeout = min(PHASE_SECONDS, self.deadline - start - reserve - 2)
        check(timeout > 0, 'whole operation 1800s bound exhausted')
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True)
        paths = {name: Path(str(stem) + '.' + name) for name in ('stdout', 'stderr')}
        counts = dict(stdout=0, stderr=0)
        eof = set()
        exceeded = None
        cleanup_deadline = None
        interrupted = None

        def stop(reason):
            nonlocal exceeded, cleanup_deadline
            if cleanup_deadline is None:
                exceeded = reason
                cleanup_deadline = min(time.monotonic()+2, self.deadline)
                # The process-group may survive its direct child and hold pipes open.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        with paths['stdout'].open('xb') as out, paths['stderr'].open('xb') as err:
            handles = dict(stdout=out, stderr=err)
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
                selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
                try:
                    while selector.get_map():
                        if time.monotonic() - start >= timeout:
                            stop('timeout')
                        if cleanup_deadline is not None and time.monotonic() >= cleanup_deadline:
                            break
                        drain_wait = 0.1 if cleanup_deadline is None else min(0.1,max(0,cleanup_deadline-time.monotonic()))
                        for key, _ in selector.select(timeout=drain_wait):
                            name = key.data
                            block = os.read(key.fileobj.fileno(), min(65536, max(1, STREAM_LIMIT - counts[name] + 1)))
                            if not block:
                                eof.add(name)
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                                continue
                            available = max(0, STREAM_LIMIT - counts[name])
                            handles[name].write(block[:available])
                            counts[name] += len(block)
                            if counts[name] > STREAM_LIMIT:
                                stop(name+'-oversize')
                except BaseException as exc:
                    interrupted = exc
                    stop('interrupted: '+type(exc).__name__)
                finally:
                    # Unclosed descendant pipes are explicitly incomplete, never awaited forever.
                    for key in list(selector.get_map().values()):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
        try:
            actual_exit = process.wait(timeout=max(0, (cleanup_deadline if cleanup_deadline is not None
                else min(start+timeout,self.deadline))-time.monotonic()))
        except subprocess.TimeoutExpired:
            stop('timeout')
            try:
                actual_exit = process.wait(timeout=max(0,cleanup_deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                actual_exit = None  # No fabricated exit when the killed child is not reaped in bound.
        except BaseException as exc:
            interrupted = exc
            stop('interrupted: '+type(exc).__name__)
            try:
                actual_exit = process.wait(timeout=max(0,cleanup_deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                actual_exit = None
        record = dict(argv=argv, cwd=str(cwd), environment={'PYTHONDONTWRITEBYTECODE': '1'},
            actual_exit=actual_exit, start_at=start_at, finish_at=datetime.now(timezone.utc).isoformat(),
            exercised_revision=self.revisions.get(str(cwd)), input_sha256={**PINS,'tools/test_workflow_assurance.py':TEST_SHA256},
            elapsed_seconds=time.monotonic()-start,
            effective_timeout_seconds=timeout, stop_reason=exceeded,
            streams={name:dict(path=str(path), retained_bytes=path.stat().st_size,
                observed_bytes=counts[name], sha256=file_sha(path), complete=name in eof and counts[name] <= STREAM_LIMIT)
                for name, path in paths.items()})
        self.outcomes.append(dict(label=label,actual_exit=actual_exit,stop_reason=exceeded,
            execution_path=str(stem)+'.execution.json'))
        Path(str(stem)+'.execution.json').write_bytes(canonical(record))
        if interrupted is not None:
            raise interrupted
        check(exceeded is None and actual_exit == 0, 'first unexpected child failure: ' + label)
        return paths['stdout'].read_bytes()


def snapshot(recorder, repo, label):
    names = recorder.command(['git', 'ls-files', '-z'], repo, label+'-paths').split(b'\0')
    rows = []
    for name in filter(None, names):
        check(time.monotonic() < recorder.deadline, 'whole operation bound during preservation')
        relative = os.fsdecode(name)
        path = repo / relative
        info = path.lstat()
        value = os.readlink(path) if stat.S_ISLNK(info.st_mode) else file_sha(path)
        rows.append((relative, info.st_mode, info.st_nlink, value))
    origin = recorder.command(['git', 'remote', 'get-url', 'origin'], repo, label+'-origin').decode().strip()
    status = recorder.command(['git', 'status', '--porcelain=v1', '--untracked-files=all'], repo, label+'-status')
    check(not status, 'owned exercised checkout must remain completely clean')
    installed = sum(relative.startswith('.nizam/') and stat.S_ISREG(mode) for relative,mode,links,value in rows)
    check(installed == 239, 'installed inventory must remain 239 regular files')
    head = recorder.command(['git','rev-parse','HEAD'],repo,label+'-head').decode().strip()
    refs = recorder.command(['git','show-ref'],repo,label+'-refs')
    return dict(rows=rows, origin=origin, head=head, refs_sha256=sha(refs), installed_regular_files=installed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', choices=PHASES)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    check(CHECKPOINT is not None and TEST_SHA256 is not None, 'unfrozen author checkpoint pins; execution forbidden')
    check(os.environ.get('PYTHONDONTWRITEBYTECODE') == '1', 'explicit bytecode env required')
    if args.worker:
        worker(args.repo.resolve(), args.scratch.resolve(), args.worker)
        return 0
    check(all(value is not None and value.is_absolute() for value in (args.repository,args.workspace,args.output)), 'explicit absolute paths required')
    check(not args.workspace.exists() and not args.output.exists(), 'exclusive new owned paths required')
    args.workspace.mkdir()
    args.output.mkdir()
    started = time.monotonic()
    recorder = Recorder(args.output, started + TOTAL_SECONDS)
    def interrupt(signum, _frame):
        raise InterruptedError('engineering driver received signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupt)
    signal.signal(signal.SIGINT,interrupt)
    snapshots = {}
    result = 1
    failure = None
    try:
        for name in ('K', 'M'):
            recorder.command(['git','clone','--quiet','--shared','--no-checkout',str(args.repository),str(args.workspace/name)], args.workspace, 'clone-'+name)
        k, m = args.workspace/'K', args.workspace/'M'
        recorder.command(['git','checkout','--quiet','--detach',CHECKPOINT], k, 'checkout-K')
        tree = recorder.command(['git','rev-parse',CHECKPOINT+'^{tree}'], m, 'K-tree').decode().strip()
        merge = recorder.command(['git','-c','user.name=SYNTHETIC engineering matrix4',
            '-c','user.email=synthetic-matrix4@example.invalid','commit-tree',tree,'-p',MAIN,'-p',CHECKPOINT,
            '-m','SYNTHETIC engineering matrix4 treeK main-first-parent; not a hosted merge'], m, 'make-M').decode().strip()
        recorder.command(['git','checkout','--quiet','--detach',merge], m, 'checkout-M')
        shape = recorder.command(['git','show','-s','--format=%H %T %P',merge], m, 'M-actual-shape').decode().split()
        check(shape == [merge,tree,MAIN,CHECKPOINT], 'actual synthetic M tree/ordered parents mismatch')
        changed = recorder.command(['git','diff','--name-only',merge+'^',merge,'--','*.gz'], m, 'old-M-parent-gzip-delta').decode().splitlines()
        check(set(GZIP_PATHS) <= set(changed), 'synthetic old-parent delta must actually contain retained gzip')
        for number, relative in enumerate(GZIP_PATHS):
            raw = recorder.command(['git','show',merge+':'+relative], m, 'gzip-materialization-'+str(number))
            check(raw[:2] == b'\x1f\x8b' and raw == (m/relative).read_bytes(), 'retained binary materialization mismatch')
        recorder.revisions = {str(k):CHECKPOINT,str(m):merge}
        for name, repo in (('K',k), ('M',m)):
            for relative, expected in {**PINS,'tools/test_workflow_assurance.py':TEST_SHA256}.items():
                check(file_sha(repo/relative) == expected, 'pre-import pin mismatch: '+relative)
            snapshots[name] = snapshot(recorder, repo, name+'-before')
        (args.output/'preconditions.json').write_bytes(canonical(dict(checkpoint=CHECKPOINT,synthetic_merge=merge,
            tree=tree,parents=[MAIN,CHECKPOINT], retained_binary_paths=GZIP_PATHS,
            pins={**PINS,'tools/test_workflow_assurance.py':TEST_SHA256}, helper_sha256=file_sha(Path(__file__)),
            scope='SYNTHETIC engineering input portability only; no actual GitHub identity or gate verdict')))
        for phase in PHASES:
            repo = k if phase == 'K-baseline' else m
            recorder.command([sys.executable,str(Path(__file__).resolve()),'--worker',phase,'--repo',str(repo),
                '--scratch',str(args.workspace/('fixture-'+phase))], repo, phase,
                {**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        result = 0
    except (Exception, KeyboardInterrupt) as exc:
        failure = type(exc).__name__+': '+str(exc)
        traceback.print_exc()
    finally:
        preservation = {}
        for name, before in snapshots.items():
            try:
                # Preservation still runs after a phase failure; no further product behavior follows it.
                after = snapshot(recorder,args.workspace/name,name+'-after')
                same = before == after
                preservation[name] = dict(equal=same,tracked_paths=len(before['rows']),installed_regular_files=before['installed_regular_files'],
                    before_sha256=sha(canonical(before)),after_sha256=sha(canonical(after)))
                if not same: result = 1
            except (Exception, KeyboardInterrupt):
                traceback.print_exc();result = 1
        (args.output/'summary.json').write_bytes(canonical(dict(actual_exit=result,failure=failure,
            command_outcomes=recorder.outcomes,preservation=preservation,
            elapsed_seconds=time.monotonic()-started,full_bank=False,hosted_proof=False,gate_verdict=False)))
    return result


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
