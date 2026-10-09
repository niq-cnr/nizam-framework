"""Feature 103 Evaluator adversarial probe (methodology/02 Sec 8).

Usage: python3 .agent/evidence/103-qa-adversarial-helpers/probe.py <scratch-root>

Builds a clean copy of the repository (git archive HEAD when a .git directory exists, otherwise a
plain copy of this tree) under <scratch-root>, outside the repository, and replays the contract's own
AT1/AT2/AT3/S11/S13/S17 commands (read from .agent/contracts/103.json) against hostile `unshare` shims
and five single-point mutations of tools/test_convergent_review.py. The repository is never modified.
Exit 0 iff every expectation below held; exit 1 otherwise.
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCR = Path(sys.argv[1]).resolve()
if ROOT in SCR.parents or SCR == ROOT:
    sys.exit('scratch root must be outside the repository')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
V = json.load(open(ROOT / '.agent/contracts/103.json'))['verification']
CMD = {os.path.basename(v['evidence_file']).split('-')[0]: v['command'] for v in V}  # at1, s11, ...
BASE = SCR / 'base'
problems = []


def build_base():
    shutil.rmtree(SCR, ignore_errors=True)
    BASE.mkdir(parents=True)
    if (ROOT / '.git').exists():
        arc = subprocess.run(['git', 'archive', 'HEAD'], cwd=ROOT, capture_output=True, check=True).stdout
        subprocess.run(['tar', '-x', '-C', str(BASE)], input=arc, check=True)
    else:
        shutil.copytree(ROOT, BASE, dirs_exist_ok=True)


def fresh(name, git=False):
    d = SCR / name
    shutil.copytree(BASE, d)
    if git:  # scratch_run.py requires a git repository root
        subprocess.run('git init -q && git add -A >/dev/null 2>&1 && git -c user.name=x -c user.email=x@x commit -qm s',
                       shell=True, cwd=d, env=env, check=True)
    return d


def sh(key, cwd, path=None):
    e = dict(env, PATH=path) if path else env
    p = subprocess.run(['bash', '-c', CMD[key]], cwd=cwd, capture_output=True, text=True, env=e)
    return p.returncode, (p.stdout + p.stderr).strip()


def suite(d, path, flag=False):
    p = subprocess.run([sys.executable, 'tools/test_convergent_review.py'] + (['--allow-unsupported-isolation'] if flag else []),
                       cwd=d, capture_output=True, text=True, env=dict(env, PATH=path))
    o = p.stdout + p.stderr
    return p.returncode, len(re.findall(r"skipped 'UNSUPPORTED", o)), re.findall(r'^(?:FAIL|ERROR): (test_\w+)', o, re.M), \
        re.findall(r'^CONFORMANCE:.*$', o, re.M)


def shim(name, body):
    d = SCR / name
    d.mkdir()
    (d / 'unshare').write_text(body)
    (d / 'unshare').chmod(0o755)
    return str(d) + ':' + env['PATH']


def expect(label, ok, detail=''):
    print(('  EXPECTED: ' if ok else '  UNEXPECTED: ') + label + (' ' + detail if detail else ''))
    if not ok:
        problems.append(label)


print('ADVERSARIAL QUESTION (feature 103, HEAD %s): can the suite pass, or the flag mask a failure, while an isolation-dependent test ran unsandboxed or user-namespace isolation was unavailable?'
      % subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip())
print('Host: apparmor_restrict_unprivileged_userns=%s' % (open('/proc/sys/kernel/apparmor_restrict_unprivileged_userns').read().strip()
      if os.path.exists('/proc/sys/kernel/apparmor_restrict_unprivileged_userns') else 'absent'))
build_base()

print('PART 1 hostile unshare shims, unmutated code')
rc, un, bad, conf = suite(fresh('B'), shim('B_bin', '#!/bin/sh\nkill -9 $$\n'))
print('  B shim dies by SIGKILL, required mode: exit %d, UNSUPPORTED lines %d, FAIL/ERROR %s, %s' % (rc, un, bad, conf))
expect('B: exit 1, 5 UNSUPPORTED, no FAIL, NOT FULL', rc == 1 and un == 5 and not bad and conf == ['CONFORMANCE: NOT FULL (UNSUPPORTED isolation-dependent tests: 5)'])
rc, un, bad, conf = suite(fresh('C'), shim('C_bin', '#!/bin/sh\necho ok; echo ok >&2; exit 1\n'), True)
print('  C shim prints success text but exits 1, WITH flag: exit %d, UNSUPPORTED lines %d, FAIL/ERROR %s, %s' % (rc, un, bad, conf))
expect('C: exit 0, 5 UNSUPPORTED, no FAIL, NOT FULL', rc == 0 and un == 5 and not bad and conf == ['CONFORMANCE: NOT FULL (UNSUPPORTED isolation-dependent tests: 5)'])

print('PART 2 single-point mutations of tools/test_convergent_review.py (contract commands replayed in the mutated scratch copy)')
EXITLINE = 'return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation) else 1'
MUTS = [
    ('M1', 'decorator runs the test body when the probe says unavailable (skipTest removed)',
     'self.skipTest(f"{UNSUPPORTED_REASON_PREFIX} ({_PROBE_CACHE[0].detail})")', 'pass', ['at1', 'at2']),
    ('M2', 'probe ignores the unshare exit status', 'if completed.returncode == 0:', 'if True:', ['at1', 'at2']),
    ('M3', 'process exit status ignores UNSUPPORTED', EXITLINE, 'return 0 if successful else 1', ['at1']),
    ('M4', 'flag also forgives real failures', EXITLINE,
     'return 0 if (arguments.allow_unsupported_isolation or (successful and not unsupported)) else 1', ['at3', 's13', 's17']),
    ('M5', 'FileNotFoundError from the probe treated as available',
     'return IsolationProbeResult(False, "unshare executable not found on PATH")', 'return IsolationProbeResult(True, "")', ['s11']),
]
print('  CONTROL (unmutated):')
for key in ['at1', 'at2', 'at3', 's11', 's13', 's17']:
    rc, _ = sh(key, fresh('ctl_' + key, git=key in ('at3', 's13')))
    print('    %s exit %d' % (key.upper(), rc))
    expect('control %s exit 0' % key.upper(), rc == 0)
for tag, label, old, new, killers in MUTS:
    print('  %s %s' % (tag, label))
    detected_by = []
    for key in ['at1', 'at2', 'at3', 's11', 's13', 's17']:
        d = fresh('%s_%s' % (tag, key), git=key in ('at3', 's13'))
        f = d / 'tools/test_convergent_review.py'
        text = f.read_text()
        assert text.count(old) == 1, (tag, text.count(old))
        f.write_text(text.replace(old, new))
        rc, out = sh(key, d)
        print('    %s on mutant: exit %d%s' % (key.upper(), rc, '' if rc == 0 else ' (detected)'))
        if rc != 0:
            detected_by.append(key)
    expect('%s detected by at least one of %s' % (tag, killers), any(k in detected_by for k in killers), 'detected by %s' % detected_by)

print('CONCLUSION: %s' % ('every expectation held; no way found to run an isolation-dependent test unsandboxed or to mask a failure with the flag (restricted host only; capable-host behaviour is feature 104 AT5-AT8)'
                          if not problems else 'UNEXPECTED RESULTS: %s' % problems))
print('Repository working tree was not touched by the probes (scratch copy only).')
sys.exit(1 if problems else 0)
