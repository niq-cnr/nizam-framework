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
import concurrent.futures
SR = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py']
CMD = ['--', 'bash', 'tools/fixtures_self_test.sh']
SCRIPT = 'tools/fixtures_self_test.sh'
ROW = '  "convergent_review|tools/test_convergent_review.py"'
OK4 = ['^OK   claim-map   unclaimed subdirectory -> FAIL$', '^OK   claim-map   doubly-claimed subdirectory -> FAIL$', '^OK   claim-map   claim naming a missing suite -> FAIL$', '^OK   claim-map   claim naming an absent subdirectory -> FAIL$']
DEMO_FAIL = ['^FAIL claim-map   unclaimed subdirectory: ', '^FAIL claim-map   doubly-claimed subdirectory: ', '^FAIL claim-map   claim naming a missing suite: ', '^FAIL claim-map   claim naming an absent subdirectory: ']
HEAD = 'claim_map_check() {\n'
def insert_after_header(line): return "p = root / 'tools/fixtures_self_test.sh'; t = p.read_text(); h = %r; assert t.count(h) == 1; p.write_text(t.replace(h, h + %r))" % (HEAD, line)
# (name, mutation argv, expected rc, --expect regexes, --forbid regexes)
CASES = [
 ('control: unmutated tree passes with 146/146 and the four OK lines', [], 0, ['^SELF-TEST OK: 146/146 fixtures accounted for, 0 failed$'] + OK4, ['^FAIL ']),
 ('any depth: a dotfile 6 path components deep (4 directories below the claimed subdirectory) is counted (147/147)', ['--write', 'tools/fixtures/convergent_review/01-no-findings/d1/d2/d3/.deep.json', '{}'], 0, ['^SELF-TEST OK: 147/147 fixtures accounted for, 0 failed$'], ['^FAIL ']),
 ('any depth: an unclaimed subdirectory whose only file is 6 path components deep is named and its file counted', ['--write', 'tools/fixtures/zz_deep/a/b/c/d/x.json', '{}'], 1, ['^FAIL claim-map: unclaimed subdirectory: zz_deep$', '^       zz_deep/a/b/c/d/x\\.json$', '^SELF-TEST FAILED: \\d+/147 '], ['^FAIL claim-map: doubly-claimed subdirectory: ']),
 ('top-level behaviour kept: an unlisted top-level file fails through its row set, not the claim map', ['--write', 'tools/fixtures/zz_top.json', '{}'], 1, ['^       zz_top\\.json$', '^SELF-TEST FAILED: \\d+/147 '], ['^FAIL claim-map: ']),
 ('exact-name claim: convergent_review_x/ is not covered by the convergent_review claim', ['--write', 'tools/fixtures/convergent_review_x/a.json', '{}'], 1, ['^FAIL claim-map: unclaimed subdirectory: convergent_review_x$'], ['^FAIL claim-map: doubly-claimed subdirectory: ']),
 ('an EMPTY unclaimed subdirectory fails (the check enumerates directories, not only files)', ['--py-mutate', "(root / 'tools/fixtures/zz_empty').mkdir()"], 1, ['^FAIL claim-map: unclaimed subdirectory: zz_empty$', '^SELF-TEST FAILED: \\d+/146 '], []),
 ('the map is CONSULTED: deleting the real claim row makes the real subdirectory unclaimed', ['--replace', SCRIPT, ROW, ''], 1, ['^FAIL claim-map: unclaimed subdirectory: convergent_review$', '^SELF-TEST FAILED: \\d+/146 '], ['^FAIL claim-map: .*does not exist']),
 ('a claim naming a missing suite file fails (and is not also reported unclaimed)', ['--replace', SCRIPT, ROW, '  "convergent_review|tools/no_such_suite.py"'], 1, ['^FAIL claim-map: claim for convergent_review names a suite file that does not exist: tools/no_such_suite\\.py$'], ['^FAIL claim-map: unclaimed subdirectory: ', '^FAIL claim-map: doubly-claimed subdirectory: ']),
 ('a doubly-claimed subdirectory fails even when both suites exist', ['--replace', SCRIPT, ROW, ROW + '\n  "convergent_review|tools/convergent_review.py"'], 1, ['^FAIL claim-map: doubly-claimed subdirectory: convergent_review$'], ['^FAIL claim-map: .*does not exist', '^FAIL claim-map: unclaimed subdirectory: ']),
 ('a claim naming a subdirectory that is not on disk fails', ['--replace', SCRIPT, ROW, ROW + '\n  "zz_ghost|tools/test_convergent_review.py"'], 1, ['^FAIL claim-map: claim names a subdirectory that is not on disk: zz_ghost$'], ['^FAIL claim-map: unclaimed subdirectory: ']),
 ('a malformed claim row fails', ['--replace', SCRIPT, ROW, '  "convergent_review"'], 1, ['^FAIL claim-map: malformed claim row: convergent_review$'], []),
 ('demonstrations are real: a claim_map_check that always passes cannot print the OK lines', ['--py-mutate', insert_after_header('  return 0\n')], 1, DEMO_FAIL + ['^SELF-TEST FAILED: '], ['^OK   claim-map']),
 ('demonstrations are real: a claim_map_check that always fails cannot print the OK lines (the positive control is load-bearing)', ['--py-mutate', insert_after_header('  echo "FAIL claim-map: constant"; return 1\n')], 1, DEMO_FAIL + ['^FAIL claim-map: constant$'], ['^OK   claim-map']),
]
LABELS = ['unclaimed subdirectory', 'doubly-claimed subdirectory', 'claim naming a missing suite', 'claim naming an absent subdirectory']
FRAGMENTS = ['unclaimed subdirectory: ', 'doubly-claimed subdirectory: ', 'names a suite file that does not exist: ', 'names a subdirectory that is not on disk: ']
def ablate_detection(fragment):
    # replace the ONE line of claim_map_check that holds this mode's message fragment (and its bad=1) with ':'
    return "p = root / 'tools/fixtures_self_test.sh'; t = p.read_text(); assert t.count(%r) == 1; s = t.index(%r); e = t.index('\\n}\\n', s); lines = t[s:e].split('\\n'); hits = [i for i, l in enumerate(lines) if %r in l]; assert len(hits) == 1, hits; assert 'bad=1' in lines[hits[0]]; lines[hits[0]] = ':'; p.write_text(t[:s] + '\\n'.join(lines) + t[e:])" % (HEAD, HEAD, fragment)
for i in range(4):
    CASES.append(('ablation: disabling only the %s detection line removes only its own OK line (the label tests its own mode)' % LABELS[i], ['--py-mutate', ablate_detection(FRAGMENTS[i])], 1, [DEMO_FAIL[i]] + [OK4[j] for j in range(4) if j != i], [OK4[i]]))
def one(case):
    name, mut, rc, exp, forb = case
    argv = SR + mut + ['--expect-rc', str(rc)] + [a for e in exp for a in ('--expect', e)] + [a for e in forb for a in ('--forbid', e)] + CMD
    p = subprocess.run(argv, capture_output=True, text=True)
    return name, p.returncode, (p.stdout + p.stderr)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(one, CASES))
for name, rc, out in results:
    print(('PASS ' if rc == 0 else 'FAIL ') + name + ('' if rc == 0 else ' (scratch_run exit %d)' % rc))
    if rc != 0: print('\n'.join('    ' + l for l in out.splitlines()[-25:])); bad.append(name)
print('cases:', len(CASES), 'problems:', bad)
sys.exit(1 if bad else 0)
PY
