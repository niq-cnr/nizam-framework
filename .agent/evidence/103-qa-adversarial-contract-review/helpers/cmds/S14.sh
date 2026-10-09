python3 - <<'PY'
import json, os, pathlib, re, subprocess, sys, tempfile
import ast, re
BASE = '88959c9'
PATH = 'tools/test_convergent_review.py'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
old_src, new_src = run('git', 'show', BASE + ':' + PATH), open(PATH).read()
bad = []
SPAWN = {'run', 'Popen', 'call', 'check_call', 'check_output'}
def spawns(tree):
    out = []
    def visit(node, in_class, fn):
        if isinstance(node, ast.ClassDef): in_class = True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): fn = node.name
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess' and node.func.attr in SPAWN and not in_class:
            out.append((fn, node))
        for child in ast.iter_child_nodes(node): visit(child, in_class, fn)
    visit(tree, False, None)
    return out
old_spawns, new_spawns = spawns(ast.parse(old_src)), spawns(ast.parse(new_src))
if len(new_spawns) != len(old_spawns) + 1: bad.append('module-level subprocess calls: base %d, now %d (exactly one new call, the probe, is allowed)' % (len(old_spawns), len(new_spawns)))
probe = [n for f, n in new_spawns if f == 'probe_user_namespace_isolation']
if len(probe) != 1: bad.append('the single new subprocess call must be inside probe_user_namespace_isolation')
else:
    kw = {k.arg: k.value for k in probe[0].keywords}
    if 'shell' in kw: bad.append('probe passes shell=')
    if 'timeout' not in kw: bad.append('probe has no timeout')
    if ast.unparse(kw.get('stdin', ast.Constant(None))) != 'subprocess.DEVNULL': bad.append('probe stdin is not subprocess.DEVNULL')
assigned = {t.id: n.value for n in ast.parse(new_src).body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
if ast.literal_eval(assigned['ISOLATION_PROBE_COMMAND']) not in (('unshare', '--user', '--map-root-user', 'true'), ['unshare', '--user', '--map-root-user', 'true']): bad.append('ISOLATION_PROBE_COMMAND is not the fixed probe argv')
if ast.literal_eval(assigned['UNSUPPORTED_REASON_PREFIX']) != 'UNSUPPORTED: user-namespace isolation unavailable': bad.append('UNSUPPORTED_REASON_PREFIX is not the pinned prefix')
added = [l[1:] for l in run('git', 'diff', '-U0', BASE, '--', PATH).splitlines() if l.startswith('+') and not l.startswith('+++')]
if not added: bad.append('no added lines (vacuous)')
forbidden = re.compile(r'sudo|setcap|sysctl\s+-w|/proc/sys|--isolation-adapter|--no-sandbox|os\.system|shell\s*=\s*True|\bos\.environ\b|\benviron\b|getenv|putenv|chmod')
hits = [l.strip() for l in added if forbidden.search(l)]
if hits: bad.append('forbidden constructs in added lines: ' + repr(hits))
for p in ('tools/linux_trial_sandbox.sh', 'tools/isolated_trial_adapter.py', 'tools/evaluate_convergent_review_prompt.py'):
    if subprocess.run(['git', 'diff', '--quiet', BASE, '--', p]).returncode != 0: bad.append(p + ' changed')
print('base spawns:', len(old_spawns), 'now:', len(new_spawns), 'added lines:', len(added), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
