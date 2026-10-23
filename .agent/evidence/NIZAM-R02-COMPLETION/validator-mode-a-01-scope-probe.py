#!/usr/bin/env python3
"""Pre-code diagnostic of the proposed SCOPE command, not product implementation."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

ROOT = Path('/workspace/scratch/58c4bfe533de/nizam-framework-pr')
EVIDENCE = ROOT / '.agent/evidence/NIZAM-R02-COMPLETION'
CONTRACT = ROOT / '.agent/contracts/NIZAM-R02-COMPLETION.json'
EXPECTED = '023aac22cf2d17f3396c2f2f44fda6e6bff2224d6e59215ed7b9fb672e0af65b'
raw = CONTRACT.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
contract = json.loads(raw)
entry = next(x for x in contract['verification'] if x['id'] == 'SCOPE')
command = shlex.split(entry['command'])
assert command[:3] == ['PYTHONDONTWRITEBYTECODE=1', 'python3', '-c']
source = command[3]
env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')

def git(root, *args):
    return subprocess.check_output(['git', '-c', 'user.name=Nizam review fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=' + os.devnull, *args], cwd=root, env=env)

results = []
for case in ['masked-committed-path', 'official-capture-reservation']:
    with tempfile.TemporaryDirectory(prefix='nizam-mode-a-scope-') as name:
        fixture = Path(name)
        (fixture / 'outside.txt').write_text('base\n')
        git(fixture, 'init', '-q')
        git(fixture, 'add', 'outside.txt')
        git(fixture, 'commit', '-qm', 'fixture base')
        base = git(fixture, 'rev-parse', 'HEAD').decode().strip()
        if case == 'masked-committed-path':
            (fixture / 'outside.txt').write_text('undeclared committed edit\n')
            git(fixture, 'add', 'outside.txt')
            git(fixture, 'commit', '-qm', 'undeclared edit')
            git(fixture, 'restore', '--source', base, '--staged', '--worktree', '--', 'outside.txt')
        else:
            marker = fixture / '.agent/evidence/NIZAM-R02-COMPLETION-scope-attempt1.reservation.json'
            marker.parent.mkdir(parents=True)
            marker.write_text('{}\n')
        # Only the literal baseline commit is substituted for the disposable fixture.
        # All Git queries, allowlists and the actual assertion remain unchanged.
        assert source.count(contract['source_revision']) == 1
        fixture_source = source.replace(contract['source_revision'], base, 1)
        argv = ['python3', '-c', fixture_source]
        started = time.monotonic()
        completed = subprocess.run(argv, cwd=fixture, env=env, capture_output=True)
        stem = 'validator-mode-a-01-' + case
        for stream, body in [('stdout', completed.stdout), ('stderr', completed.stderr)]:
            with (EVIDENCE / (stem + '.' + stream + '.txt')).open('xb') as handle:
                handle.write(body)
        committed = git(fixture, 'diff', '--name-only', '-z', base, 'HEAD', '--').decode().split('\0')
        committed = [p for p in committed if p]
        status = git(fixture, 'status', '--porcelain=v1').decode()
        record = {'case': case, 'argv': argv, 'cwd': str(fixture), 'duration_ms': round((time.monotonic() - started) * 1000), 'exit_code': completed.returncode, 'stdout': stem + '.stdout.txt', 'stderr': stem + '.stderr.txt', 'committed_delta_paths': committed, 'fixture_base': base, 'fixture_head': git(fixture, 'rev-parse', 'HEAD').decode().strip(), 'only_command_substitution': 'Pinned repository base commit replaced by disposable fixture base commit; queries, allowlist and assertion unchanged.'}
        with (EVIDENCE / (stem + '.execution.json')).open('x') as handle:
            json.dump(record, handle, indent=2)
            handle.write('\n')
        if case == 'masked-committed-path':
            assert committed == ['outside.txt']
            assert completed.returncode == 0
            assert json.loads(completed.stdout)['unexpected'] == []
            outcome = 'False pass: undeclared committed path is hidden by staged restoration.'
        else:
            assert completed.returncode != 0
            assert json.loads(completed.stdout)['unexpected'] == ['.agent/evidence/NIZAM-R02-COMPLETION-scope-attempt1.reservation.json']
            outcome = 'False fail: the official task capture reservation is excluded from permitted metadata.'
        results.append({'case': case, 'observed_exit': completed.returncode, 'outcome': outcome, 'record': stem + '.execution.json'})
assert CONTRACT.read_bytes() == raw
summary = {'contract_sha256': EXPECTED, 'purpose': 'Predeclared contract-verifier diagnostic. Both defects are expected observations; no product implementation or acceptance test is executed.', 'results': results, 'product_changed': False, 'contract_changed': False}
with (EVIDENCE / 'validator-mode-a-01-scope-probe-summary.json').open('x') as handle:
    json.dump(summary, handle, indent=2)
    handle.write('\n')
print(json.dumps(summary))
