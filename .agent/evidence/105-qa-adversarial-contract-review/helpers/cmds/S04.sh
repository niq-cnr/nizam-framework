python3 - <<'PY'
import json, os, re, subprocess, sys, yaml
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
norm = lambda x: ' '.join(x.split())
bad = []
P = json.load(open('.agent/contracts/105.json'))['design_notes']
T, K = P['current_tree'], P['pinned_interface']
fx = 'tools/fixtures'
files = sorted(os.path.relpath(os.path.join(d, n), fx) for d, _, ns in os.walk(fx) for n in ns)
dirs = sorted(os.path.relpath(os.path.join(d, n), fx) for d, ds, _ in os.walk(fx) for n in ds)
links = [os.path.join(d, n) for d, ds, ns in os.walk(fx) for n in ds + ns if os.path.islink(os.path.join(d, n))]
top = [x for x in files if '/' not in x]
topdirs = [x for x in dirs if '/' not in x]
# 1. the CURRENT tree equals the pinned enumeration, which is also the tree at <A> (no fixture moved)
if len(files) != T['total_files'] or len(top) != T['top_level_files'] or links: bad.append('tree totals differ from the pinned enumeration: %d files, %d top-level, symlinks %r' % (len(files), len(top), links))
if topdirs != sorted(T['top_level_subdirectories']): bad.append('top-level subdirectories %r differ from the pinned %r' % (topdirs, sorted(T['top_level_subdirectories'])))
for name, spec in T['top_level_subdirectories'].items():
    if len([x for x in files if x.startswith(name + '/')]) != spec['files'] or len([x for x in dirs if x.startswith(name + '/')]) != spec['directories']: bad.append(name + ': file or directory count differs from the pinned enumeration')
    if not os.path.isfile(spec['owner_suite']): bad.append(name + ': the owning suite file does not exist: ' + spec['owner_suite'])
if {'tools/fixtures/' + x for x in files} != set(run('git', 'ls-tree', '-r', '--name-only', A, 'tools/fixtures').split('\n')) - {''}: bad.append('the fixture file set differs from <A> (a fixture was added, moved, renamed or removed)')
if sh('git', 'diff', '--quiet', A, '--', 'tools/fixtures', 'tools/test_convergent_review.py', 'tools/skill.json', 'tools/validate.sh', 'tools/verify_lib.sh').returncode != 0 or run('git', 'status', '--porcelain', '--untracked-files=all', '--', 'tools/fixtures').strip(): bad.append('a fixture, the owning suite, skill.json, validate.sh or verify_lib.sh differs from <A>')
# 2. the claim map: one pinned row, the NIP slot is a comment only and nothing is created for it
src = open('tools/fixtures_self_test.sh').read()
m = re.search(r'^FIXTURE_CLAIMS=\(\n(.*?)^\)\n', src, re.M | re.S)
rows = [l.strip() for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith('#')] if m else None
if rows != ['"' + K['claim_row'] + '"']: bad.append('FIXTURE_CLAIMS rows are %r, expected exactly the pinned row' % (rows,))
if src.count('\n  "' + K['claim_row'] + '"\n') != 1: bad.append('the pinned claim row line does not occur exactly once as a two-space-indented line')
if src.splitlines().count(K['slot_comment_line']) != 1: bad.append('the NIP-0003 slot comment line does not occur exactly once')
if [l for l in src.splitlines() if 'runtime_session' in l and not l.lstrip().startswith('#')]: bad.append('runtime_session appears outside a comment (a claim row for it must not exist)')
if os.path.exists('tools/fixtures/runtime_session') or os.path.exists('tools/test_runtime_session.py') or os.path.exists('tools/runtime_session.py'): bad.append('a NIP-0003 runtime_session artifact was created')
# 3. pinned structure of the script
for token in K['unique_tokens']:
    if src.count(token) != 1: bad.append('token not exactly once: ' + repr(token))
if len(re.findall(r'if _claim_map_case [^\n]*\n\s*echo "OK   claim-map   ', src)) != 1: bad.append('the OK claim-map line is not printed only inside `if _claim_map_case ...`')
for label in K['demonstration_labels']:
    if src.count(label) < 1: bad.append('demonstration label absent: ' + label)
for msg in K['message_fragments']:
    if src.count(msg) != 1: bad.append('message fragment not exactly once: ' + repr(msg))
base = run('git', 'show', A + ':tools/fixtures_self_test.sh')
cut = base.index('# ---------------------------------------------------------------------------\n# COMPLETENESS GUARD')
if not src.startswith(base[:cut]): bad.append('the script before the completeness-guard separator differs from <A> (every earlier probe and row must be byte-identical)')
new_noncomment = [l for l in src[cut:].splitlines() if not l.lstrip().startswith('#')]
if any(re.search(r'(?<![\w./-])(79|146|67|12)(?![\w./-])', l) for l in new_noncomment): bad.append('a fixture count literal appears in the new guard code')
cm = src.find('\nclaim_map_check() {\n')
body = src[cm:src.index('\n}\n', cm)] if cm >= 0 else ''
if cm < 0: bad.append('claim_map_check is absent')
W = re.compile(r'\b(mkdir|rmdir|touch|rm|cp|mv|ln|tee|install|dd|truncate|chmod)\b|:\s*>|(?<![0-9&-])>(?!&)')
if [l for l in body.splitlines() if not l.lstrip().startswith('#') and W.search(l)]: bad.append('claim_map_check is not a pure read (a write verb or redirection appears)')
# 4. no second registry
reg = {l for l in run('git', 'grep', '-l', '--untracked', '-e', 'FIXTURE_CLAIMS', '--', '.', ':!.agent').split('\n') if l}
if not reg <= {'tools/fixtures_self_test.sh', 'tools/README.md'}: bad.append('FIXTURE_CLAIMS appears outside the script and tools/README.md: ' + repr(sorted(reg)))
print('files:', len(files), 'top-level:', len(top), 'subdirectories:', topdirs, 'claim rows:', rows, 'problems:', bad)
sys.exit(1 if bad else 0)
PY
