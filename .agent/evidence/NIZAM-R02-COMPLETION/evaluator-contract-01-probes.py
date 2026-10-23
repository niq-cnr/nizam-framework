#!/usr/bin/env python3
"""Read-only contract inspection plus disposable-clone scope-verifier controls."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / '.agent/contracts/NIZAM-R02-COMPLETION.json'
OUT = Path(__file__).parent / 'evaluator-contract-01-probes'


def identity(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    OUT.mkdir(exist_ok=False)
    contract = json.loads(CONTRACT.read_text())
    assert identity(CONTRACT)['sha256'] == '023aac22cf2d17f3396c2f2f44fda6e6bff2224d6e59215ed7b9fb672e0af65b'
    validator = Draft202012Validator(json.loads((ROOT / '.nizam/schema/contract.schema.json').read_text()))
    validator.validate(contract)
    before = {p: identity(ROOT / p) for p in ('tools/start_path.py', 'tools/test_start_path.py')}
    command = next(v['command'] for v in contract['verification'] if v['id'] == 'SCOPE')
    tokens = shlex.split(command)
    assert tokens[0] == 'PYTHONDONTWRITEBYTECODE=1'
    argv = [sys.executable, *tokens[2:]]
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM='1',
               GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    events = []
    for name in ('clean-control', 'rename-outside-into-evidence', 'allowed-versioned-review'):
        case = OUT / name
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix='nizam-contract-review-') as temp:
            scratch = Path(temp).resolve()
            clone = scratch / 'repo'
            subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(ROOT), str(clone)],
                           check=True, capture_output=True, env=env)
            subprocess.run(['git', '-C', str(clone), 'checkout', '--detach', contract['source_revision']],
                           check=True, capture_output=True, env=env)
            if name == 'rename-outside-into-evidence':
                target = clone / '.agent/evidence/NIZAM-R02-COMPLETION/borrowed-readme.md'
                target.parent.mkdir(parents=True)
                subprocess.run(['git', '-C', str(clone), 'mv', 'README.md', str(target.relative_to(clone))],
                               check=True, capture_output=True, env=env)
                expected = 'nonzero: source README is outside allowed scope'
            elif name == 'allowed-versioned-review':
                target = clone / '.agent/qa/NIZAM-R02-COMPLETION-contract-review-01.json'
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{}\n')
                expected = 'zero: parent-authorized versioned independent review output'
            else:
                expected = 'zero: clean source control'
            status = subprocess.run(['git', 'status', '--porcelain=v1', '--untracked-files=all'],
                                    cwd=clone, env=env, capture_output=True)
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            result = subprocess.run(argv, cwd=clone, env=env, capture_output=True, check=False)
            ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for label, raw in (('stdout.txt', result.stdout), ('stderr.txt', result.stderr),
                               ('status.txt', status.stdout)):
                with (case / label).open('xb') as stream:
                    stream.write(raw)
            row = {'case': name, 'expected': expected, 'argv': argv, 'cwd': str(clone),
                   'started_at': started, 'completed_at': ended, 'exit_code': result.returncode,
                   'stdout': {'path': str((case/'stdout.txt').relative_to(ROOT)), **identity(case/'stdout.txt')},
                   'stderr': {'path': str((case/'stderr.txt').relative_to(ROOT)), **identity(case/'stderr.txt')},
                   'status': {'path': str((case/'status.txt').relative_to(ROOT)), **identity(case/'status.txt')}}
            save(case / 'execution.json', row)
            events.append(row)
            print(json.dumps({'case': name, 'exit_code': result.returncode, 'expected': expected}), flush=True)
    assert events[0]['exit_code'] == 0
    assert events[1]['exit_code'] == 0, 'rename false-pass did not reproduce'
    assert events[2]['exit_code'] == 1, 'review-path false-fail did not reproduce'
    after = {p: identity(ROOT / p) for p in before}
    assert before == after
    assert identity(CONTRACT)['sha256'] == '023aac22cf2d17f3396c2f2f44fda6e6bff2224d6e59215ed7b9fb672e0af65b'
    save(OUT / 'summary.json', {'reviewed_contract': identity(CONTRACT), 'schema_valid': True,
         'scope_command': command, 'cases': events, 'source_before': before, 'source_after': after,
         'qualification': 'Both verifier defects reproduced. Diagnostic wrapper success is not contract approval or implementation acceptance.'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
