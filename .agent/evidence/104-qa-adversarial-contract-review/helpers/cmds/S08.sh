python3 - <<'PY'
import os, re, subprocess, sys, tempfile
bad = []
env0 = dict(os.environ)
def suite(cwd, env):
    p = subprocess.run([sys.executable, 'tools/test_convergent_review.py', '--allow-unsupported-isolation'], cwd=cwd, env=env, capture_output=True, text=True)
    o = p.stdout + p.stderr
    m = re.search(r'^Ran (\d+) tests', o, re.M)
    return p.returncode, (int(m.group(1)) if m else None), bool(re.search(r'^(FAIL|ERROR): test_', o, re.M)), re.search(r'^OK\b', o, re.M) is not None
root = suite(os.getcwd(), env0)
with tempfile.TemporaryDirectory() as t:
    dest = os.path.join(t, 'clone')
    subprocess.run(['git', 'clone', '-q', '--depth', '1', 'file://' + os.getcwd(), dest], check=True)
    depth = int(subprocess.run(['git', '-C', dest, 'rev-list', '--count', 'HEAD'], capture_output=True, text=True, check=True).stdout)
    env = {k: v for k, v in env0.items() if not k.startswith('GIT_')}
    env.update({'HOME': t, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})
    clone = suite(dest, env)
if depth != 1: bad.append('clone is not depth 1')
if root[0] != 0 or root[2] or not root[3] or root[1] is None: bad.append('working-tree run (flag used for LOCAL development only): %r' % (root,))
if clone != root: bad.append('shallow identity-less clone differs from the working-tree run: %r vs %r' % (clone, root))
print('depth:', depth, 'working tree (rc, tests, fail/error line, OK):', root, 'shallow clone:', clone, 'problems:', bad)
sys.exit(1 if bad else 0)
PY
