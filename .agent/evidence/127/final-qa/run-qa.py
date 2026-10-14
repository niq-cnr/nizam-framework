#!/usr/bin/env python3
"""Fresh Evaluator capture for feature127; sealed product is read-only."""
import datetime, hashlib, importlib.metadata, json, os, platform, shlex, shutil, socket, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
C1 = '88996ee9405f9467ff2debd6e3115b34d064019a'
RELEASE = '4ad36b310de9611128c023c8e810eb08a12110e4'
REL = '.agent/evidence/127/final-qa/'
def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads((ROOT / path).read_text())
def write(name, data): (OUT / name).write_text(json.dumps(data, indent=2) + '\n')
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)
def strict(v): return v['final_verdict']['approved'] is True and all(v[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def inventory(paths):
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(set(paths)) if p.is_file()}
def identities():
    seal = load('.agent/evidence/127/semantic1-test-seal.json')
    entries = seal['source_stub_harness_docs'] + [seal[k] for k in ('test', 'API', 'obligations', 'approved_contract')]
    rows = []
    for e in entries:
        raw = (ROOT / e['path']).read_bytes()
        assert sha(raw) == e['sha256'] and git('show', C1 + ':' + e['path']) == raw, e['path']
        assert git('show', 'HEAD:' + e['path']) == raw, e['path']
        blob = git('rev-parse', 'HEAD:' + e['path']).decode().strip()
        assert blob == e['git_blob'], e['path']
        rows.append(dict(path=e['path'], sha256=sha(raw), git_blob=blob, source_revision=C1))
    paths = git('ls-files', '-z', '--', 'tools', 'schema', 'methodology/10_live_runtime_sessions.md', 'methodology/11_sbcl_runtime_binding.md').decode().split('\0')
    return {'at': now(), 'head': git('rev-parse', 'HEAD').decode().strip(), 'source_revision': C1,
        'files': rows, 'installed_inventory': inventory((ROOT / '.nizam').rglob('*')),
        'runtime_schema_tools_fixture_inventory': inventory(ROOT / p for p in paths if p),
        'run_state_sha256': sha((ROOT / '.agent/run_state.json').read_bytes())}
def stable(identity): return {k: v for k, v in identity.items() if k not in ('at', 'head')}
def main():
    assert Path.cwd() == ROOT and git('branch', '--show-current').decode().strip() == 'qa/127-final'
    assert git('rev-parse', 'HEAD').decode().strip() == RELEASE
    release = load('.agent/evidence/127/qa1-modeb-release.json')
    modeb = load('.agent/validator/127-mode-b.json')
    assert release['strict_approved'] is True and strict(modeb)
    assert sha((ROOT / release['ModeB_ref']).read_bytes()) == release['ModeB_sha256']
    assert strict(load('.agent/validator/127-executable-bundle-review.json'))
    before = identities(); write('identity-before.json', before)
    commands = load('.agent/evidence/127/acceptance1-obligations.json')['fourteen_commands']
    inherited = [x['command'] for x in load('.agent/evidence/126/ci-c3-receipt.json')['commands']]
    new = [x['command'] for x in load('.agent/contracts/127.json')['verification']]
    assert len(commands) == 14 and commands == inherited + new
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    selected = ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'PYTHONPATH', 'PYTHONHOME', 'PYTHONDONTWRITEBYTECODE', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME')
    runtime = {'python_executable': sys.executable, 'python_realpath': str(Path(sys.executable).resolve()),
        'python_sha256': sha(Path(sys.executable).read_bytes()), 'python_version': sys.version,
        'python3_resolved': shutil.which('python3'), 'host': {'hostname': socket.gethostname(), 'platform': platform.platform(), 'uname': list(platform.uname()), 'uid': os.getuid(), 'gid': os.getgid()},
        'packages': {x: importlib.metadata.version(x) for x in ('jsonschema', 'PyYAML', 'referencing', 'attrs', 'rpds-py', 'jsonschema-specifications')},
        'environment': {k: env.get(k) for k in selected}, 'environment_value_sha256': {k: sha(v.encode()) for k, v in sorted(env.items())},
        'fixture_environment': 'Sealed Session supplies private HOME/XDG/state and strips PYTHONPATH/PYTHONHOME/CL_SOURCE_REGISTRY/ASDF_OUTPUT_TRANSLATIONS. No external resources.'}
    write('runtime.json', runtime)
    checks = []
    plan = [(c, 240, None) for c in commands] + [('PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh', 600, None),
        ('PYTHONDONTWRITEBYTECODE=1 bash tools/fixtures_self_test.sh', 1200, None),
        ('PYTHONDONTWRITEBYTECODE=1 python3 ' + REL + 'adversarial.py', 180, '.agent/evidence/127-qa-adversarial.txt')]
    for i, (command, timeout, output_override) in enumerate(plan, 1):
        words = shlex.split(command); assert words.pop(0) == 'PYTHONDONTWRITEBYTECODE=1'
        prefix = f'{i:02d}-command'; pre = identities(); assert stable(pre) == stable(before)
        write(prefix + '-before.json', pre)
        stdout = ROOT / (output_override or REL + prefix + '.stdout.txt'); stderr = OUT / (prefix + '.stderr.txt')
        started, clock = now(), time.monotonic()
        # Streams go directly to files, including on timeout; no pipelines swallow exits.
        with stdout.open('wb') as out, stderr.open('wb') as err:
            p = subprocess.Popen(words, cwd=ROOT, env=env, stdout=out, stderr=err)
            token = Path(f'/proc/{p.pid}/stat').read_text().split(') ', 1)[1].split()[19]
            timed_out = False
            try: exit_code = p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                if p.poll() is None and Path(f'/proc/{p.pid}/stat').read_text().split(') ', 1)[1].split()[19] == token:
                    p.terminate()
                try: exit_code = p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    p.kill(); exit_code = p.wait(timeout=10)
        post = identities(); write(prefix + '-after.json', post)
        row = {'command': command, 'argv': words, 'cwd': str(ROOT), 'environment_override': {'PYTHONDONTWRITEBYTECODE': '1'},
            'runtime_ref': REL + 'runtime.json', 'identity_before': REL + prefix + '-before.json', 'identity_after': REL + prefix + '-after.json',
            'started_at': started, 'duration_seconds': time.monotonic() - clock, 'exit_code': exit_code, 'timed_out': timed_out,
            'stdout': str(stdout.relative_to(ROOT)), 'stderr': str(stderr.relative_to(ROOT)), 'stdout_sha256': sha(stdout.read_bytes()), 'stderr_sha256': sha(stderr.read_bytes()),
            'source_revision': C1, 'test_sha256': seal_test_hash(before), 'preserved_inputs': stable(pre) == stable(post)}
        write(prefix + '.json', row); checks.append(row)
        write('summary.json', {'checks': checks, 'helper_sha256': sha(Path(__file__).read_bytes())})
        print(f'{i}/17 exit={exit_code} timeout={timed_out}: {command}', flush=True)
        if exit_code != 0 or timed_out or not row['preserved_inputs']: return 1
    write('identity-after.json', identities())
    return 0
def seal_test_hash(identity): return next(x['sha256'] for x in identity['files'] if x['path'] == 'tools/test_runtime_session.py')
if __name__ == '__main__': sys.exit(main())
