python3 - <<'PY'
import os, subprocess, sys, tempfile, yaml
bad = []
J = yaml.safe_load(open('.github/workflows/compliance.yml'))['jobs'].get('convergent_review') or {}
found = [s for s in J.get('steps', []) if 'sysctl' in (s.get('run') or '')]
script = found[0]['run'] if len(found) == 1 else ''
if len(found) != 1: bad.append('expected exactly one guarded sysctl step, got %d' % len(found))
KEY = '/proc/sys/kernel/apparmor_restrict_unprivileged_userns'
if script.count(KEY) != 1 or script.count('sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0') != 1: bad.append('the guard path and the single sudo sysctl write are not each present exactly once')
with tempfile.TemporaryDirectory() as t:
    shim = os.path.join(t, 'shim'); os.mkdir(shim); log = os.path.join(t, 'calls.log')
    for name, body in (('sudo', '#!/bin/sh\necho "$*" >> "$SHIM_LOG"\nexit "${SHIM_SUDO_RC:-0}"\n'), ('sysctl', '#!/bin/sh\necho REAL-SYSCTL-REACHED >> "$SHIM_LOG"\nexit 99\n')):
        open(os.path.join(shim, name), 'w').write(body); os.chmod(os.path.join(shim, name), 0o755)
    present = os.path.join(t, 'present'); open(present, 'w').close()
    def case(keypath, sudo_rc):
        if os.path.exists(log): os.remove(log)
        env = {'PATH': shim + ':/usr/bin:/bin', 'SHIM_LOG': log, 'SHIM_SUDO_RC': str(sudo_rc), 'HOME': t}
        r = subprocess.run(['bash', '-e', '-c', script.replace(KEY, keypath)], capture_output=True, text=True, env=env)
        return r.returncode, (open(log).read() if os.path.exists(log) else '')
    a, b, c = case(os.path.join(t, 'absent'), 0), case(present, 0), case(present, 1)
if a != (0, ''): bad.append('absent key must be a silent no-op, got %r' % (a,))
if b != (0, 'sysctl -w kernel.apparmor_restrict_unprivileged_userns=0\n'): bad.append('present key must run exactly the one shimmed sudo write, got %r' % (b,))
if c[0] == 0: bad.append('a failed write must fail the step, got %r' % (c,))
print('absent:', a, 'present:', b, 'present+write-fails:', c, 'problems:', bad)
sys.exit(1 if bad else 0)
PY
