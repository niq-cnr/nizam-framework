"""Root transport only: retain five real fetches, without issuing a verdict.

Run once in a fresh owned Root capture worktree after selecting actual IDs.
No Fetch Ref or HostMetadata is constructed until raw bytes are committed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess


def positive(value):
    parsed = int(value)
    if str(parsed) != value or parsed < 1:
        raise argparse.ArgumentTypeError('expected canonical positive decimal')
    return parsed


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            value.update(block)
    return value.hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode', choices=('capture', 'verify'))
parser.add_argument('operation_attempt', type=int, choices=(1, 2, 3))
for name in ('run_id', 'run_attempt', 'job_id', 'artifact_id'):
    parser.add_argument(name, type=positive)
args = parser.parse_args()
cwd = Path.cwd().resolve(strict=True)
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
origin = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
assert origin == 'https://github.com/niq-cnr/nizam-framework.git'
assert not subprocess.check_output(['git', 'status', '--porcelain'])
state = json.loads(Path('.agent/run_state.json').read_text())
step = state['circuit_breaker']['123-ci-' + args.mode]
assert state['current_feature'] == '123' and step['attempts'] == args.operation_attempt
assert step['limit'] == 3
prefix = Path('.agent/evidence/123') / ('hosted-' + args.mode + str(args.operation_attempt) + '-fetch')
plan = [
    ('run', ['gh', 'api', f'repos/niq-cnr/nizam-framework/actions/runs/{args.run_id}'], 2),
    ('jobs', ['gh', 'api', f'repos/niq-cnr/nizam-framework/actions/runs/{args.run_id}/attempts/{args.run_attempt}/jobs?per_page=100'], 2),
    ('artifacts', ['gh', 'api', f'repos/niq-cnr/nizam-framework/actions/runs/{args.run_id}/artifacts?per_page=100'], 2),
    ('job-log', ['gh', 'run', 'view', str(args.run_id), '--repo', 'niq-cnr/nizam-framework', '--job', str(args.job_id), '--log'], 16),
    ('archive', ['gh', 'api', f'repos/niq-cnr/nizam-framework/actions/artifacts/{args.artifact_id}/zip'], 32),
]
paths = [Path(str(prefix) + '-' + kind + suffix) for kind, _, _ in plan
         for suffix in ('.stdout', '.stderr')]
manifest_path = Path(str(prefix) + '.execution.json')
assert all(not p.exists() and not p.is_symlink() for p in paths + [manifest_path])
records = []
for kind, argv, bound_mib in plan:
    out = Path(str(prefix) + '-' + kind + '.stdout')
    err = Path(str(prefix) + '-' + kind + '.stderr')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with out.open('xb') as stdout, err.open('xb') as stderr:
        process = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    record = {'kind': kind, 'argv': argv, 'cwd': str(cwd), 'revision': revision,
              'actual_exit': process.returncode, 'started_at': started,
              'finished_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'stdout_path': str(out), 'stderr_path': str(err),
              'stdout_bytes': out.stat().st_size,
              'stdout_sha256': digest(out),
              'stderr_sha256': digest(err)}
    record['within_size_bound'] = out.stat().st_size <= bound_mib * 1024 * 1024 and err.stat().st_size <= 2 * 1024 * 1024
    records.append(record)
    manifest_path.write_text(json.dumps({'role': 'Root transport', 'mode': args.mode,
        'operation_attempt': args.operation_attempt, 'records': records,
        'boundary': 'Raw observations only; no normalized facts, Ref admission or success verdict.'}, indent=2) + '\n')
    print(json.dumps({'kind': kind, 'actual_exit': process.returncode,
                      'stdout_bytes': record['stdout_bytes'],
                      'within_size_bound': record['within_size_bound']}), flush=True)
    if process.returncode != 0 or not record['within_size_bound']:
        raise SystemExit(1)
