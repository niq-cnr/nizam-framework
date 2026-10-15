"""Root transport: capture observed hosted run/logs, fetch exact checkout, then parse."""
import datetime
import json
import pathlib
import subprocess

E = pathlib.Path('.agent/evidence/121')
records = []
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
def capture(label, argv):
    run = subprocess.run(argv, capture_output=True)
    out, err = E / ('ci1-' + label + '.stdout.txt'), E / ('ci1-' + label + '.stderr.txt')
    out.write_bytes(run.stdout); err.write_bytes(run.stderr)
    records.append({'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'actual_exit': run.returncode,
        'stdout': str(out), 'stderr': str(err), 'revision': revision,
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (E / 'ci1-fetch-results.json').write_text(json.dumps(records, indent=2) + '\n')
    assert run.returncode == 0, label
    return run.stdout
repo = 'niq-cnr/nizam-framework'
capture('run', ['gh', 'run', 'view', '38655158531', '--repo', repo, '--json', 'databaseId,headSha,status,conclusion,jobs'])
capture('closeout', ['gh', 'run', 'view', '38655158402', '--repo', repo, '--json', 'databaseId,headSha,status,conclusion,jobs'])
capture('job-log', ['gh', 'run', 'view', '38655158531', '--repo', repo, '--job', '116163055103', '--log'])
capture('checkout', ['git', 'fetch', 'origin', 'refs/pull/102/merge'])
parser = ['python3', str(E / 'capture-hosted.py'), 'ci1', 'b8558349bc58bcf75b746cb90e5b8a2de327e08b',
    '38655158531', '38655158402', '116163055103', 'b8558349bc58bcf75b746cb90e5b8a2de327e08b', '102']
run = subprocess.run(parser, capture_output=True)
(E / 'ci1-parser.stdout.txt').write_bytes(run.stdout); (E / 'ci1-parser.stderr.txt').write_bytes(run.stderr)
(E / 'ci1-parser.json').write_text(json.dumps({'argv': parser, 'cwd': str(pathlib.Path.cwd()),
    'actual_exit': run.returncode, 'revision': revision}, indent=2) + '\n')
print(run.stdout.decode(), end=''); print(run.stderr.decode(), end='')
assert run.returncode == 0
