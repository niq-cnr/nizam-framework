python3 - <<'PY'
import json, os, re, subprocess, sys, yaml
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
import fcntl
def serial_guard():
    ancestors, p = set(), os.getpid()
    while p > 1:
        ancestors.add(p)
        try: p = int(open('/proc/%d/stat' % p).read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError): break
    for q in filter(str.isdigit, os.listdir('/proc')):
        if int(q) in ancestors: continue
        try:
            argv = [a.decode() for a in open('/proc/%s/cmdline' % q, 'rb').read().split(b'\0')]
            cwd = os.readlink('/proc/%s/cwd' % q)
        except OSError: continue
        if cwd == os.getcwd() and len(argv) > 1 and os.path.basename(argv[0]) in ('bash', 'sh') and argv[1].endswith(('tools/fixtures_self_test.sh', 'tools/validate.sh')):
            print('REFUSED (exit 4): process %s is already running %s in this tree (C13 race: the self-test swaps tools/skill.json while validate.sh reads it)' % (q, argv[1])); sys.exit(4)
    lock = open(run('git', 'rev-parse', '--absolute-git-dir').strip() + '/nizam-105-serial.lock', 'w')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: print('REFUSED (exit 4): another serial-guarded 105 check holds the lock'); sys.exit(4)
    return lock
LOCK = serial_guard()
p = subprocess.run(['bash', 'tools/validate.sh'], capture_output=True, text=True)
o = p.stdout + p.stderr
summary = re.findall(r'^SUMMARY: (\d+) passed, (\d+) failed$', o, re.M)
passes = len(re.findall(r'^\[C\d+\] PASS\b', o, re.M))
baseline = len(re.findall(r'^\[C\d+\] PASS\b', open('.agent/evidence/phase-014-activation/validate.txt').read(), re.M))
if p.returncode != 0 or len(summary) != 1 or summary[0][1] != '0' or int(summary[0][0]) != passes or passes != baseline or re.search(r'^\[C\d+\] FAIL\b', o, re.M): bad.append('default mode: rc=%s summary=%r PASS lines=%d baseline=%d' % (p.returncode, summary, passes, baseline))
g = subprocess.run([sys.executable, '.agent/evidence/phase-014-activation/gates/validator_gate.py', '--payload'], capture_output=True, text=True)
if g.returncode != 0 or 'GATE: PASS' not in g.stdout: bad.append('payload gate: rc=%s' % g.returncode)
print('validate.sh summary:', summary, 'PASS lines:', passes, 'baseline:', baseline, 'payload gate rc:', g.returncode, 'problems:', bad)
sys.exit(1 if bad else 0)
PY
