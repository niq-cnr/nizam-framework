#!/usr/bin/env python3
"""mutate.py IMPLTREE WORKDIR [ID...] : single-point mutants of the contract-faithful implementation.
Each mutant = a fresh cp -a copy of IMPLTREE with ONE defect; run the contract's pre-CI checks; list which checks catch it.
FAST checks first; the slow ones (S09 validate.sh, AT9, S08, AT10) only if every fast check passed (a survivor)."""
import os, re, shutil, subprocess, sys, time, pathlib
H = pathlib.Path(__file__).resolve().parent / 'cmds'
impl, work = sys.argv[1], sys.argv[2]
only = sys.argv[3:]
FAST = ['AT1', 'AT2', 'AT3', 'AT4', 'S01', 'S03', 'S04', 'S05', 'S06', 'S07']
SLOW = ['S09', 'AT9', 'S08', 'AT10']

def sub(t, path, old, new, count=1, nth=None):
    p = pathlib.Path(t) / path
    s = p.read_text()
    assert s.count(old) >= 1, (path, old)
    if nth == 'last':
        i = s.rindex(old); s = s[:i] + new + s[i + len(old):]
    else:
        s = s.replace(old, new, count)
    p.write_text(s)

WF = '.github/workflows/compliance.yml'
SUITE = '      - run: python3 tools/test_convergent_review.py\n'
GUARD = '''          if [ -e /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
            sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
          fi
'''
DOD = 'standard/definition_of_done.md'
TR = 'tools/README.md'
SR = 'schema/README.md'
M = []
def mut(i, d):
    def deco(f): M.append((i, d, f)); return f
    return deco

# ---------------- workflow ----------------
mut('w01', 'suite step gains -k filter')(lambda t: sub(t, WF, SUITE, '      - run: python3 tools/test_convergent_review.py -k test_a\n'))
mut('w02', 'suite step gains --allow-unsupported-isolation')(lambda t: sub(t, WF, SUITE, '      - run: python3 tools/test_convergent_review.py --allow-unsupported-isolation\n'))
mut('w03', 'suite step gains an env var')(lambda t: sub(t, WF, SUITE, '      - env:\n          CONVERGENT_REVIEW_ALLOW: "1"\n        run: python3 tools/test_convergent_review.py\n'))
mut('w04', 'job-level env var')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    runs-on: ubuntu-latest\n    env:\n      X: "1"\n'))
mut('w05', 'sysctl write masked with || true')(lambda t: sub(t, WF, 'userns=0\n          fi', 'userns=0 || true\n          fi'))
mut('w06', 'guard removed (unconditional sudo sysctl write)')(lambda t: sub(t, WF, GUARD, '          sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0\n'))
mut('w06b', 'guard kept but the whole step masked: || true after fi')(lambda t: sub(t, WF, GUARD, GUARD + '          true\n'))
mut('w07', 'job-level continue-on-error: true')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    runs-on: ubuntu-latest\n    continue-on-error: true\n'))
mut('w08', 'suite step continue-on-error: true')(lambda t: sub(t, WF, SUITE, '      - continue-on-error: true\n        run: python3 tools/test_convergent_review.py\n'))
mut('w09', 'pip install jsonschema removed')(lambda t: sub(t, WF, '      - run: pip install jsonschema\n      - name: Enable', '      - name: Enable'))
mut('w10', 'checkout SHA changed (in the new job only)')(lambda t: sub(t, WF, '11bd71901bbe5b1630ceea73d27597364c9af683', '11bd71901bbe5b1630ceea73d27597364c9af684', nth='last'))
mut('w11', 'setup-python SHA changed (new job only)')(lambda t: sub(t, WF, '0b93645e9fea7318ecaed2b359559ac225c90a2b', '0b93645e9fea7318ecaed2b359559ac225c90a2c', nth='last'))
mut('w11b', 'setup-python unpinned tag @v5 (new job only)')(lambda t: sub(t, WF, 'actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b # v5.3.0', 'actions/setup-python@v5', nth='last'))
def w12(t):
    p = pathlib.Path(t) / WF; s = p.read_text()
    job = s[s.index('  convergent_review:'):]
    p.write_text(s + '\n' + job.replace('convergent_review:', 'convergent_review_two:', 1))
mut('w12', 'second job added (copy)')(w12)
mut('w12b', 'second trivial job added')(lambda t: pathlib.Path(t, WF).write_text(pathlib.Path(t, WF).read_text() + '\n  extra:\n    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n'))
mut('w13', 'permissions contents: write')(lambda t: sub(t, WF, 'permissions:\n  contents: read', 'permissions:\n  contents: write'))
mut('w13b', 'job-level permissions added')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    runs-on: ubuntu-latest\n    permissions:\n      contents: write\n'))
mut('w14', 'suite step guarded by if: false')(lambda t: sub(t, WF, SUITE, '      - if: false\n        run: python3 tools/test_convergent_review.py\n'))
mut('w15', 'job gains a name')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    name: Convergent review\n    runs-on: ubuntu-latest\n'))
def w16(t):
    sub(t, WF, SUITE, '')
    p = pathlib.Path(t) / WF; s = p.read_text()
    i = s.index('      - name: Enable unprivileged')
    p.write_text(s[:i] + SUITE + s[i:])
mut('w16', 'suite step moved before pip and guard')(w16)
mut('w17', 'suite step masked with || true')(lambda t: sub(t, WF, SUITE, '      - run: python3 tools/test_convergent_review.py || true\n'))
mut('w18', 'suite step piped through tee (no pipefail)')(lambda t: sub(t, WF, SUITE, '      - run: python3 tools/test_convergent_review.py 2>&1 | tee suite.log\n'))
mut('w19', 'persist-credentials removed from the new job')(lambda t: sub(t, WF, '        with:\n          persist-credentials: false\n      - uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b # v5.3.0\n        with:\n          python-version: "3.x"\n      - run: pip install jsonschema\n', '      - uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b # v5.3.0\n        with:\n          python-version: "3.x"\n      - run: pip install jsonschema\n'))
mut('w20', 'workflow_dispatch trigger added')(lambda t: sub(t, WF, 'on:\n  pull_request:\n', 'on:\n  workflow_dispatch:\n  pull_request:\n'))
mut('w21', 'concurrency cancel-in-progress changed')(lambda t: sub(t, WF, 'cancel-in-progress: true', 'cancel-in-progress: false'))
mut('w22', 'existing validate job step neutered')(lambda t: sub(t, WF, '      - run: bash tools/validate.sh', '      - run: "true"'))
mut('w23', 'suite step replaced by echo (job exists but never runs the suite)')(lambda t: sub(t, WF, SUITE, '      - run: echo python3 tools/test_convergent_review.py\n'))
mut('w24', 'runs-on self-hosted')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    runs-on: self-hosted\n'))
mut('w25', 'python-version pinned 3.9 (new job)')(lambda t: sub(t, WF, 'python-version: "3.x"', 'python-version: "3.9"', nth='last'))
mut('w26', 'timeout-minutes: 1 added to the new job')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    runs-on: ubuntu-latest\n    timeout-minutes: 1\n'))
mut('w27', 'guard condition inverted-to-vacuous: -e -> -d')(lambda t: sub(t, WF, 'if [ -e /proc', 'if [ -d /proc'))
mut('w28', 'sysctl value 1 instead of 0')(lambda t: sub(t, WF, 'userns=0\n          fi', 'userns=1\n          fi'))
mut('w29', 'guard step gains continue-on-error')(lambda t: sub(t, WF, '      - name: Enable unprivileged user namespaces where the kernel restricts them\n', '      - name: Enable unprivileged user namespaces where the kernel restricts them\n        continue-on-error: true\n'))
mut('w30', 'new job step name contains UNSUPPORTED (AT6 word)')(lambda t: sub(t, WF, 'Enable unprivileged user namespaces where', 'Enable unprivileged UNSUPPORTED user namespaces where'))
mut('w31', 'pull_request trigger removed (on: push only)')(lambda t: sub(t, WF, 'on:\n  pull_request:\n  push:', 'on:\n  push:'))
mut('w32', 'extra third-party action step in the new job')(lambda t: sub(t, WF, '      - run: pip install jsonschema\n      - name: Enable', '      - uses: actions/cache@v4\n      - run: pip install jsonschema\n      - name: Enable'))
mut('w33', 'matrix strategy added to the new job')(lambda t: sub(t, WF, '  convergent_review:\n    runs-on: ubuntu-latest\n', '  convergent_review:\n    strategy:\n      matrix:\n        x: [1]\n    runs-on: ubuntu-latest\n'))
mut('w34', 'guard step gets shell: bash {0} (drops -e)')(lambda t: sub(t, WF, '      - name: Enable unprivileged user namespaces where the kernel restricts them\n', '      - name: Enable unprivileged user namespaces where the kernel restricts them\n        shell: bash {0}\n'))
mut('w35', 'trailing YAML comment mentioning the flag in the new job (no semantic change)')(lambda t: sub(t, WF, '      - run: python3 tools/test_convergent_review.py\n', '      - run: python3 tools/test_convergent_review.py # not --allow-unsupported-isolation\n'))
mut('w36', 'whole new job appended with CRLF-free extra trailing blank lines (no semantic change; control for false-fail)')(lambda t: pathlib.Path(t, WF).write_text(pathlib.Path(t, WF).read_text() + '\n\n'))
mut('w37', 'comment-only edit inside the new job (allowed by workflow_job_notes; control for false-fail)')(lambda t: sub(t, WF, '      - run: pip install jsonschema\n', '      # jsonschema is installed so that no ordinary test is skipped\n      - run: pip install jsonschema\n'))
mut('w38', 'comment inside the guard script mentioning the word skipped (allowed? YAML comment inside run: block reaches the log)')(lambda t: sub(t, WF, '          if [ -e /proc', '          # skipped on kernels without the key\n          if [ -e /proc'))
# ---------------- out-of-scope enforcement edits ----------------
mut('o01', 'suite edited: required mode weakened (main returns 0)')(lambda t: sub(t, 'tools/test_convergent_review.py', 'return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation) else 1', 'return 0'))
mut('o02', 'sandbox script edited')(lambda t: pathlib.Path(t, 'tools/linux_trial_sandbox.sh').write_text(pathlib.Path(t, 'tools/linux_trial_sandbox.sh').read_text() + '\n# x\n'))
mut('o03', 'pages.yml edited')(lambda t: pathlib.Path(t, '.github/workflows/pages.yml').write_text(pathlib.Path(t, '.github/workflows/pages.yml').read_text() + '\n# x\n'))
mut('o04', 'DEBT.md edited')(lambda t: pathlib.Path(t, 'docs/planning/DEBT.md').write_text(pathlib.Path(t, 'docs/planning/DEBT.md').read_text() + '\n# x\n'))
mut('o05', 'validate.sh edited')(lambda t: pathlib.Path(t, 'tools/validate.sh').write_text(pathlib.Path(t, 'tools/validate.sh').read_text() + '\n# x\n'))
# ---------------- documents ----------------
mut('d01', 'DoD: "all three" left unsynced')(lambda t: sub(t, DOD, 'all four, plus', 'all three, plus'))
mut('d02', 'DoD: "three-job" left unsynced')(lambda t: sub(t, DOD, 'four-job workflow', 'three-job workflow'))
mut('d03', 'DoD Section 11: "three jobs" left unsynced')(lambda t: sub(t, DOD, 'four jobs `.github', 'three jobs `.github'))
mut('d04', 'DoD Section 8: job list does not name convergent_review')(lambda t: sub(t, DOD, ', and `convergent_review` (the convergent review suite in required-conformance mode) -- passes', ' -- passes') if False else sub(t, DOD, '`convergent_review` (the convergent review suite in required-conformance mode)', '`fixtures_self_test` again'))
mut('d05', 'DoD: version not bumped')(lambda t: sub(t, DOD, 'version: 0.2.0\n', 'version: 0.1.0\n'))
mut('d06', 'DoD: counts say five')(lambda t: sub(t, DOD, 'own four-job workflow', 'own five-job workflow'))
mut('d07', 'DoD: change_log head entry missing')(lambda t: pathlib.Path(t, DOD).write_text(re.sub(r'  - version: "0.2.0"\n    date: "[^"]+"\n    summary: .*\n', '', pathlib.Path(t, DOD).read_text(), count=1)))
mut('d08', 'tools/README paragraph removed')(lambda t: pathlib.Path(t, TR).write_text(re.sub(r'CI runs this suite as the `convergent_review` job.*?job log must show `CONFORMANCE: FULL`\.\n\n', '', pathlib.Path(t, TR).read_text(), flags=re.S)))
def d09(t):
    q = pathlib.Path(t) / TR; x = q.read_text()
    m = re.search(r'CI runs this suite as the `convergent_review`.*?`CONFORMANCE: FULL`\.\n\n', x, re.S); assert m
    para = m.group(0)
    x = x.replace(para, '', 1)
    h = '## Compliance Coverage \u2014 C1\u2013C16\n\n'; assert h in x
    q.write_text(x.replace(h, h + para, 1))
mut('d09', 'tools/README paragraph moved below the Compliance Coverage heading (outside Machine Validation)')(d09)
mut('d10', 'tools/README paragraph names the job without backticks')(lambda t: sub(t, TR, 'CI runs this suite as the `convergent_review` job', 'CI runs this suite as the convergent_review job'))
mut('d11', 'tools/README paragraph says the flag is used in CI (meaning flipped)')(lambda t: sub(t, TR, 'in required-conformance mode and never with `--allow-unsupported-isolation`', 'in required-conformance mode and always with `--allow-unsupported-isolation`'))
mut('d12', 'tools/README version not bumped')(lambda t: sub(t, TR, 'version: 0.13.0\n', 'version: 0.12.0\n'))
LINE = '`tools/test_convergent_review.py` is the sole validator of the review schema family (`review_packet`, `review_trial`, `review_ledger`, `review_suppression`, `review_replay`): `tools/validate.sh` check C12 does not cover this family, and extending C12 to it is left to the phase-014 simplification review and `H-CONSOLIDATION`.'
mut('d13', 'schema README sole-validator line hard-wrapped across two lines')(lambda t: sub(t, SR, 'is the sole validator of the review schema family (`review_packet`', 'is the sole validator\nof the review schema family (`review_packet`'))
mut('d14', 'schema README sole-validator line wrapped so that file name and "sole validator" split')(lambda t: sub(t, SR, 'is the sole validator of', 'is the\nsole validator of', nth='last'))
mut('d15', 'schema README sole-validator line missing')(lambda t: sub(t, SR, LINE + '\n\n', ''))
mut('d16', 'schema README line moved after DD-3 heading (outside ## Schemas)')(lambda t: (sub(t, SR, LINE + '\n\n', ''), sub(t, SR, '## DD-3 — Evidence Externalisation\n', '## DD-3 — Evidence Externalisation\n\n' + LINE + '\n'))[0])
mut('d17', 'schema README line says "a validator" (sole dropped)')(lambda t: sub(t, SR, 'is the sole validator of the review', 'is a validator of the review', nth='last'))
mut('d18', 'schema README line names a different file')(lambda t: sub(t, SR, '`tools/test_convergent_review.py` is the sole validator', '`tools/convergent_review.py` is the sole validator', nth='last'))
mut('d19', 'schema README version not bumped')(lambda t: sub(t, SR, 'version: 0.19.0\n', 'version: 0.18.0\n'))
mut('d20', 'schema README older change_log entry altered')(lambda t: sub(t, SR, 'Reconcile review and Git modes', 'Reconcile review and Git MODES'))
mut('d21', 'CHANGELOG bullet missing')(lambda t: pathlib.Path(t, 'CHANGELOG.md').write_text(re.sub(r'- \*\*Phase 014 feature 104:.*?`\.agent/evidence/104/`\.\n', '', pathlib.Path(t, 'CHANGELOG.md').read_text(), flags=re.S)))
mut('d22', 'CHANGELOG bullet altered')(lambda t: sub(t, 'CHANGELOG.md', 'reused, so C14 stays PASS', 'reused, so C14 stays green'))
mut('d23', 'phase yaml: evidence key missing')(lambda t: sub(t, 'docs/planning/phase_014.yaml', '    evidence: .agent/evidence/104/at1-single-job.txt\n', ''))
def d24(t):
    q = pathlib.Path(t) / 'docs/planning/phase_014.yaml'; x = q.read_text()
    old = '(NDEBT-041); depends on 103.\n    status: PENDING'
    assert old in x
    q.write_text(x.replace(old, '(NDEBT-041); depends on 103.\n    status: BLOCKED', 1))
mut('d24', 'phase yaml: step 104 marked BLOCKED')(d24)
mut('d25', 'phase yaml: extra key on step 104')(lambda t: sub(t, 'docs/planning/phase_014.yaml', '    evidence: .agent/evidence/104/at1-single-job.txt\n', '    evidence: .agent/evidence/104/at1-single-job.txt\n    notes: x\n'))
mut('d26', 'phase yaml: a different step edited')(lambda t: sub(t, 'docs/planning/phase_014.yaml', 'description: Nested-fixture ownership', 'description: Nested fixture ownership'))
def d27(t):
    import json
    q = pathlib.Path(t) / '.agent/feature_list_014.json'; d = json.load(open(q))
    for f in d['features']:
        if f['id'] == '105': f['status'] = 'complete'
    json.dump(d, open(q, 'w'), indent=2)
mut('d27', 'feature list: another feature status flipped')(d27)

def run_check(tree, n):
    p = subprocess.run(['bash', str(H / (n + '.sh'))], cwd=tree, capture_output=True, text=True)
    return p.returncode

tally = {'caught': 0, 'survived': 0}
os.makedirs(work, exist_ok=True)
for mid, desc, fn in M:
    if only and mid not in only: continue
    d = os.path.join(work, mid)
    shutil.rmtree(d, ignore_errors=True)
    subprocess.run(['cp', '-a', impl, d], check=True)
    try:
        fn(d)
    except AssertionError as e:
        print('%-5s MUTATION-PRECONDITION-FAILED %s (%s)' % (mid, desc, e)); shutil.rmtree(d, ignore_errors=True); continue
    diff = subprocess.run(['git', 'diff', '--stat', '--', '.'], cwd=d, capture_output=True, text=True).stdout
    res = {n: run_check(d, n) for n in FAST}
    killed = [n for n, r in res.items() if r != 0]
    if not killed:
        for n in SLOW:
            r = run_check(d, n); res[n] = r
            if r != 0: killed.append(n)
    tally['caught' if killed else 'survived'] += 1
    print('%-5s %-8s %s :: caught by %s' % (mid, 'CAUGHT' if killed else 'SURVIVED', desc, ','.join(killed) or '-'))
    sys.stdout.flush()
    if not os.environ.get('KEEP'): shutil.rmtree(d, ignore_errors=True)
print('TALLY', tally)
