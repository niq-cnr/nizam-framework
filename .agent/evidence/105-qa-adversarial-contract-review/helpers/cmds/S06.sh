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
import hashlib, shutil, stat, tempfile
src = open('tools/fixtures_self_test.sh').read()
# 1. STATIC: the demonstration builds everything under its own scratch directory and nowhere else
if '\n_claim_map_case() (\n' not in src: print('problems: ["_claim_map_case does not exist"]'); sys.exit(1)
def case_body(text):
    i = text.index('\n_claim_map_case() (\n'); return text[i:text.index('\n)\n', i)]
W = re.compile(r'\b(mkdir|rmdir|touch|rm|cp|mv|ln|tee|install|dd|truncate|chmod)\b|:\s*>|(?<![0-9&-])>(?!&)')
body = case_body(src)
live = [l for l in body.splitlines() if not l.lstrip().startswith('#')]
if body.count('scratch_dirs d || return 1') != 1: bad.append('static: _claim_map_case must call scratch_dirs exactly once')
if any(w in '\n'.join(live) for w in ('tools/fixtures', 'REPO', 'TMPDIR', 'pushd')) or re.search(r'(^|[;&|] *)cd ', '\n'.join(live), re.M): bad.append('static: _claim_map_case names the repository, tools/fixtures, TMPDIR or changes directory')
stray = [s.strip() for l in live for s in re.split(r';|&&|\|\|', l) if W.search(s) and '${d}' not in s]
if stray: bad.append('static: a write in _claim_map_case is not rooted at ${d}: ' + repr(stray))
if not body.startswith('\n_claim_map_case() (\n'): bad.append('static: _claim_map_case must be a subshell function so the scratch EXIT trap cannot replace the global one')
# 2. DYNAMIC: a full run on a private copy, fixtures directories made unwritable, must exit 0 and leave the tree byte-identical
def fingerprint(root):
    out = []
    for d, ds, ns in os.walk(root):
        ds[:] = sorted(x for x in ds if x not in ('.git', '__pycache__'))
        out += [(os.path.relpath(os.path.join(d, x), root), 'd', '') for x in ds]
        for n in sorted(ns):
            p = os.path.join(d, n)
            if n == '.git': continue
            out.append((os.path.relpath(p, root), 'l', os.readlink(p)) if os.path.islink(p) else (os.path.relpath(p, root), 'f', hashlib.sha256(open(p, 'rb').read()).hexdigest()))
    return sorted(out)
def set_dirs_writable(path, writable):
    for d, ds, _ in os.walk(path):
        for x in [d] + [os.path.join(d, y) for y in ds]:
            m = os.stat(x).st_mode
            os.chmod(x, (m | stat.S_IWUSR) if writable else (m & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)))
def leak(root):
    p = root + '/tools/fixtures_self_test.sh'; s = open(p).read()
    i = s.index('_claim_map_case() ('); a = 'scratch_dirs d || return 1'; j = s.index(a, i)
    open(p, 'w').write(s[:j] + 'd="${REPO}/tools/fixtures/zz_trip"; mkdir -p "${d}" || return 1' + s[j + len(a):])
def trial(mutate, readonly):
    tmp = tempfile.mkdtemp(prefix='nizam-105-contain-')
    try:
        root = tmp + '/repo'
        shutil.copytree(os.getcwd(), root, symlinks=True)
        if mutate: leak(root)
        before = fingerprint(root)
        fx = root + '/tools/fixtures'
        if readonly:
            set_dirs_writable(fx, False)
            try: os.mkdir(fx + '/zz_precondition'); bad.append('precondition: tools/fixtures is still writable (running as a user that ignores directory permissions?)'); os.rmdir(fx + '/zz_precondition')
            except PermissionError: pass
        p = subprocess.run(['bash', 'tools/fixtures_self_test.sh'], cwd=root, capture_output=True, text=True)
        if readonly: set_dirs_writable(fx, True)
        return p.returncode, p.stdout + p.stderr, fingerprint(root) == before
    finally:
        set_dirs_writable(tmp, True); shutil.rmtree(tmp, ignore_errors=True)
rc, out, same = trial(False, True)
if rc != 0 or not same or not re.search(r'^SELF-TEST OK: (\d+)/\1 fixtures accounted for, 0 failed$', out, re.M) or len(re.findall(r'^OK   claim-map   ', out, re.M)) != 4: bad.append('dynamic A: the unmutated self-test with unwritable fixtures directories must exit 0, print four OK claim-map lines and leave the tree byte-identical (rc=%s, identical=%s)' % (rc, same))
# 3. TRIPWIRE CONTROLS: a version of the demonstration that writes into tools/fixtures is caught by each tripwire
rc, out, same = trial(True, True)
if rc == 0 or not same or re.search(r'^OK   claim-map   ', out, re.M) or len(re.findall(r'^FAIL claim-map   ', out, re.M)) != 4: bad.append('dynamic B: a leaking demonstration must FAIL all four cases under unwritable fixtures directories and write nothing (rc=%s, identical=%s)' % (rc, same))
rc, out, same = trial(True, False)
if same or rc == 0: bad.append('dynamic C: a leaking demonstration with WRITABLE directories must change the fingerprint and fail the run (the fingerprint detector is load-bearing; rc=%s, identical=%s)' % (rc, same))
print('static ok:', not [b for b in bad if b.startswith('static')], 'problems:', bad)
sys.exit(1 if bad else 0)
PY
