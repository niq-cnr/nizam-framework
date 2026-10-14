#!/usr/bin/env python3
"""Independent final QA capture; never changes product or sealed tests."""
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / '.agent/evidence/126/final-qa'
SOURCE = 'd965c2ca9dd845f9a094153c7328d90a5398d06f'
TEST = 'd89d79fcdb9c5b3d3098f5ed8162b11467bb3284'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def identities():
    seal = json.loads((ROOT / '.agent/evidence/126/test-seal-b3.json').read_text())
    entries = seal['source_stub_harness_docs'] + [seal['test'], seal['api'], seal['obligation_projection']] + seal['normative_inputs']
    rows = []
    for e in entries:
        data = (ROOT / e['path']).read_bytes()
        blob = git('rev-parse', 'HEAD:' + e['path']).decode().strip()
        assert sha(data) == e['sha256'] and blob == e['git_blob'], e['path']
        assert git('show', 'HEAD:' + e['path']) == data, e['path']
        if 'revision' in e:
            assert git('show', e['revision'] + ':' + e['path']) == data, e['path']
        rows.append({'path': e['path'], 'sha256': sha(data), 'git_blob': blob,
                     'revision': e.get('revision', 'HEAD')})
    contract = (ROOT / '.agent/contracts/126.json').read_bytes()
    assert sha(contract) == '7eed25daca89c13a548976a213ddba6e6837acaee90511f0deff152a60697778'
    assert len((ROOT / seal['test']['path']).read_text().splitlines()) == 795
    for path in ('.agent/validator/126-bundle-review-2.json', '.agent/validator/126-mode-b-2.json'):
        v = json.loads((ROOT / path).read_text())
        assert v['final_verdict']['approved'] is True
        assert all(v[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    return {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'head': git('rev-parse', 'HEAD').decode().strip(),
            'branch': git('branch', '--show-current').decode().strip(),
            'source_revision': SOURCE, 'test_revision': TEST,
            'contract_sha256': sha(contract), 'files': rows,
            'root_run_state_sha256': sha((ROOT / '.agent/run_state.json').read_bytes()),
            'installed_inventory': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted((ROOT / '.nizam').rglob('*')) if p.is_file()}}

def main():
    assert Path.cwd() == ROOT
    assert git('branch', '--show-current').decode().strip() == 'qa/126-final'
    before = identities()
    write('identity-before.json', before)
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    runtime = {'python_argv': shutil.which('python3'), 'python_realpath': str(Path(shutil.which('python3')).resolve()),
        'python_executable_sha256': sha(Path(sys.executable).read_bytes()),
        'python_version': sys.version, 'python_implementation': platform.python_implementation(),
        'packages': {x: importlib.metadata.version(x) for x in ('jsonschema', 'referencing', 'attrs', 'rpds-py', 'jsonschema-specifications')},
        'host': {'hostname': socket.gethostname(), 'platform': platform.platform(), 'uname': list(platform.uname()),
                 'uid': os.getuid(), 'gid': os.getgid()},
        'environment': {k: env.get(k) for k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'PYTHONPATH', 'PYTHONHOME', 'PYTHONDONTWRITEBYTECODE', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME')},
        'fixture_environment': 'Session strips PYTHONPATH/PYTHONHOME/CL_SOURCE_REGISTRY/ASDF_OUTPUT_TRANSLATIONS and uses fresh private HOME/XDG/state per invocation.'}
    write('runtime.json', runtime)
    contract = json.loads((ROOT / '.agent/contracts/126.json').read_text())
    checks = []
    for i, item in enumerate(contract['verification'], 1):
        words = shlex.split(item['command'])
        assert words.pop(0) == 'PYTHONDONTWRITEBYTECODE=1'
        prefix = f'{i:02d}-command'
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        clock = time.monotonic()
        p = subprocess.run(words, cwd=ROOT, env=env, capture_output=True, timeout=180)
        stdout, stderr = OUT / (prefix + '.stdout.txt'), OUT / (prefix + '.stderr.txt')
        stdout.write_bytes(p.stdout); stderr.write_bytes(p.stderr)
        result = {**item, 'argv': words, 'cwd': str(ROOT), 'environment_override': {'PYTHONDONTWRITEBYTECODE': '1'},
            'runtime_ref': '.agent/evidence/126/final-qa/runtime.json',
            'identity_ref': '.agent/evidence/126/final-qa/identity-before.json',
            'started_at': start, 'duration_seconds': time.monotonic() - clock,
            'exit_code': p.returncode, 'stdout': str(stdout.relative_to(ROOT)), 'stderr': str(stderr.relative_to(ROOT)),
            'stdout_sha256': sha(p.stdout), 'stderr_sha256': sha(p.stderr),
            'source_revision': SOURCE, 'source_sha256': before['files'][0]['sha256'],
            'test_revision': TEST, 'test_sha256': '626ff4194baee472d27065906e12a0109f2f9878e326a5d6d2212ad2f584fe88'}
        write(prefix + '.json', result)
        checks.append(result)
        print(f'{i}/9 exit={p.returncode}: {item["command"]}', flush=True)
    after = identities()
    write('identity-after.json', after)
    assert before['files'] == after['files'] and before['installed_inventory'] == after['installed_inventory']
    assert before['root_run_state_sha256'] == after['root_run_state_sha256']
    write('summary.json', {'checks_run': len(checks), 'checks_passed': sum(x['exit_code'] == 0 for x in checks),
        'source_test_installed_and_run_state_unchanged': True,
        'helper_sha256': sha(Path(__file__).read_bytes()), 'checks': checks})
    return 0 if all(x['exit_code'] == 0 for x in checks) else 1

if __name__ == '__main__':
    sys.exit(main())
