#!/usr/bin/env python3
"""Exercise the real fixture harness in a private copy; never swap the source tree."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
MARKER = 'if TMPDIR="${REPO}" scratch_dirs should_not_exist; then'


def run(args, cwd, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, **kwargs)


def private_source(destination, source_ref):
    if source_ref:
        archive = run(['git', 'archive', source_ref], REPO).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            files.extractall(destination, filter='data')
    else:
        paths = run(['git', 'ls-files', '-z'], REPO).stdout.decode().split('\0')
        for name in paths:
            if not name:
                continue
            src, dst = REPO / name, destination / name
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    run(['git', 'init', '-q'], destination)
    run(['git', 'config', 'user.email', 'cleanup-test@example.test'], destination)
    run(['git', 'config', 'user.name', 'C13 cleanup regression'], destination)
    run(['git', 'add', '-A'], destination)
    run(['git', 'commit', '-qm', 'private actual source'], destination)


def exercise(source_ref):
    with tempfile.TemporaryDirectory(prefix='nizam-c13-regression-') as name:
        scratch = Path(name)
        private = scratch / 'repo'
        private.mkdir()
        private_source(private, source_ref)
        temporary = scratch / 'owned-temporary'
        temporary.mkdir()
        sentinel = temporary / 'unrelated-sentinel'
        sentinel.write_bytes(b'preserve unrelated data\n')
        original = (private / 'tools/skill.json').read_bytes()
        fixture = (private / 'tools/fixtures/skill_index_neg_dangling_module.json').read_bytes()
        ready, ledger = scratch / 'swapped.json', scratch / 'created-paths.txt'
        binary = scratch / 'bin'
        binary.mkdir()
        mktemp = shutil.which('mktemp')
        if not mktemp:
            raise RuntimeError('mktemp is unavailable')
        (binary / 'mktemp').write_text(
            '#!/usr/bin/env python3\nimport subprocess,sys\n'
            f'r=subprocess.run([{mktemp!r},*sys.argv[1:]],text=True,capture_output=True)\n'
            f'if r.returncode==0:\n with open({str(ledger)!r},"a") as f:f.write(r.stdout)\n'
            'sys.stdout.write(r.stdout);sys.stderr.write(r.stderr);raise SystemExit(r.returncode)\n')
        (binary / 'mktemp').chmod(0o755)
        # Validation is a transport double. The real top-level harness and traps run.
        validator = private / 'tools/validate.sh'
        validator.write_text(
            '#!/usr/bin/env python3\nimport hashlib,json,pathlib,signal\n'
            f'p=pathlib.Path({str(private / "tools/skill.json")!r})\n'
            f'if hashlib.sha256(p.read_bytes()).hexdigest()=={hashlib.sha256(fixture).hexdigest()!r}:\n'
            f' pathlib.Path({str(ready)!r}).write_text(json.dumps({{"swapped_sha256": hashlib.sha256(p.read_bytes()).hexdigest()}}))\n'
            ' while True:signal.pause()\n'
            'print("transport double before C13")\n')
        validator.chmod(0o755)
        # validate.sh is invoked through bash by the actual fixture harness.
        validator_py = private / 'tools/cleanup_validator_double.py'
        validator_py.write_text(validator.read_text())
        validator.write_text('#!/usr/bin/env bash\nexec python3 "$(dirname "$0")/cleanup_validator_double.py" "$@"\n')
        env = os.environ.copy()
        env.update(TMPDIR=str(temporary), PATH=str(binary) + os.pathsep + env['PATH'], PYTHONDONTWRITEBYTECODE='1')
        output = scratch / 'harness.txt'
        with output.open('w') as stream:
            process = subprocess.Popen(['bash', 'tools/fixtures_self_test.sh'], cwd=private, env=env,
                                       stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                deadline = time.monotonic() + 60
                while not ready.exists():
                    if process.poll() is not None:
                        raise RuntimeError('real harness exited before actual C13 swap: ' + output.read_text()[-2000:])
                    if time.monotonic() > deadline:
                        raise RuntimeError('actual C13 swap barrier timed out')
                    time.sleep(0.02)
                if (private / 'tools/skill.json').read_bytes() != fixture:
                    raise RuntimeError('barrier did not observe actual substituted fixture bytes')
                print('ACTUAL SWAP BARRIER: exact dangling fixture bytes observed', flush=True)
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        failures = []
        if (private / 'tools/skill.json').read_bytes() != original:
            failures.append('original skill.json bytes were not restored')
        created = ledger.read_text().splitlines() if ledger.exists() else []
        if not created:
            raise RuntimeError('real harness produced no observed mktemp paths')
        remaining = [p for p in created if Path(p).exists()]
        if remaining:
            failures.append('owned backup/scratch paths remain: ' + repr(remaining))
        if not sentinel.is_file() or sentinel.read_bytes() != b'preserve unrelated data\n':
            failures.append('unrelated sentinel was removed or changed')
        # Load the actual helper definitions, preserving their real trap setup.
        text = (private / 'tools/fixtures_self_test.sh').read_text()
        if MARKER not in text:
            raise RuntimeError('actual scratch-helper boundary not found')
        prefix = private / 'tools/cleanup_actual_prefix.sh'
        prefix.write_text(text.split(MARKER, 1)[0])
        ownership = subprocess.run(['bash', '-c',
            'source tools/cleanup_actual_prefix.sh; scratch_dirs parent_path || exit 2; '
            'scratch_dirs second_path || exit 2; '
            'SKILL_BAK=$(mktemp); SKILL_BAK_OWNER=$BASHPID; '
            'cp tools/skill.json "$SKILL_BAK" || exit 2; '
            'cp tools/fixtures/skill_index_neg_dangling_module.json tools/skill.json || exit 2; '
            '(cleanup; cmp -s tools/skill.json tools/fixtures/skill_index_neg_dangling_module.json || exit 46; '
            'test -f "$SKILL_BAK" && test -d "$parent_path" && test -d "$second_path" || exit 47; '
            'if cleanup_scratch_dirs "$parent_path"; then exit 41; fi; '
            'test -d "$parent_path" || exit 42); child=$?; '
            'test "$child" -eq 0 && test -d "$parent_path" || exit 43; '
            'cleanup || exit 44; '
            'test ! -e "$parent_path" && test ! -e "$second_path" && test ! -e "$SKILL_BAK" || exit 45'],
            cwd=private, env=env, text=True, capture_output=True)
        if (private / 'tools/skill.json').read_bytes() != original:
            failures.append('parent-owned backup did not restore original bytes after child cleanup')
        if ownership.returncode:
            failures.append('child/parent scratch ownership not preserved: code ' + str(ownership.returncode))
        if failures:
            print('C13 RESTORATION FAIL: ' + '; '.join(failures), flush=True)
            return 1
        print('C13 RESTORATION PASS: exact bytes restored; all owned resources removed; unrelated sentinel and parent ownership preserved')
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-ref', help='Immutable actual source tree; default uses current working-tree bytes')
    args = parser.parse_args()
    try:
        return exercise(args.source_ref)
    except (OSError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as error:
        print('C13 SETUP FAIL: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
