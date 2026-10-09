#!/usr/bin/env python3
"""ci_synth.py IMPLTREE WORKDIR [ID...] : synthetic CI-evidence scenario for AT5-AT8, S10, S11 plus single-point mutants.
Builds T0 (copy of the contract-faithful implementation, committed as the positive headSha C1; a 'neg' branch commit N1 applies the
contract's two mutation_replacements; a local bare 'origin'), a gh SHIM that serves canned JSON/log fixtures (the 'live' side), and the
seven ci-*.txt captures. Each mutant changes ONE thing in the captures, the live fixtures, or the git objects."""
import json, os, re, shutil, subprocess, sys, pathlib
H = pathlib.Path(__file__).resolve().parent / 'cmds'
impl, work = sys.argv[1], sys.argv[2]
only = sys.argv[3:]
sh = lambda *a, cwd=None, env=None: subprocess.run(a, cwd=cwd, capture_output=True, text=True, env=env)
def git(t, *a):
    r = sh('git', *a, cwd=t); assert r.returncode == 0, (a, r.stderr); return r.stdout.strip()

def build_t0(path):
    shutil.rmtree(path, ignore_errors=True)
    subprocess.run(['cp', '-a', impl, path], check=True)
    git(path, 'config', 'user.name', 'eval'); git(path, 'config', 'user.email', 'eval@example.invalid')
    git(path, 'checkout', '-q', '-b', 'pos')
    git(path, 'add', '-A'); git(path, 'commit', '-q', '-m', 'positive head C1')
    c1 = git(path, 'rev-parse', 'HEAD')
    git(path, 'checkout', '-q', '-b', 'neg')
    c = pathlib.Path(path) / 'tools/linux_trial_sandbox.sh'; s = c.read_text()
    a = 'exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc'; assert s.count(a) == 1
    c.write_text(s.replace(a, 'exec'))
    c = pathlib.Path(path) / 'tools/isolated_trial_adapter.py'; s = c.read_text()
    a = 'syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)'; assert s.count(a) == 1
    c.write_text(s.replace(a, 'pass'))
    git(path, 'commit', '-q', '-am', 'DO NOT MERGE throwaway mutation')
    n1 = git(path, 'rev-parse', 'HEAD')
    git(path, 'checkout', '-q', 'pos')
    o = os.path.join(os.path.dirname(path), 'origin.git')
    shutil.rmtree(o, ignore_errors=True)
    git(path, 'init', '-q', '--bare', o)
    git(path, 'remote', 'set-url', 'origin', o)
    git(path, 'push', '-q', 'origin', 'pos:refs/heads/phase/014-104-sandbox-ci')
    return c1, n1, o

POS_LOG = ['convergent_review\tRun python3 tools/test_convergent_review.py\t2026-10-09T19:00:%02d.0000000Z %s' % (i, l) for i, l in enumerate([
    'test_a (__main__.T.test_a) ... ok', 'test_linux_sandbox_blocks_cross_trial_files_and_network (__main__.S.t) ... ok',
    'Ran 54 tests in 40.1s', 'OK', 'CONFORMANCE: FULL'])]
NEG_LOG = ['convergent_review\tRun python3 tools/test_convergent_review.py\t2026-10-09T19:10:%02d.0000000Z %s' % (i, l) for i, l in enumerate([
    'FAIL: test_linux_sandbox_blocks_cross_trial_files_and_network (__main__.S.t)', 'Traceback (most recent call last):', 'AssertionError: 40 != 0',
    'FAILED (failures=1)', 'CONFORMANCE: NOT FULL (run unsuccessful)'])]

def spec_base(c1, n1):
    jobs = lambda ids, concl: [{'completedAt': 'x', 'conclusion': concl.get(n, 'success'), 'databaseId': i, 'name': n, 'startedAt': 'x', 'status': 'completed', 'steps': [], 'url': 'u'} for n, i in ids]
    return {
        'pos': {'id': 1001, 'headSha': c1, 'headBranch': 'phase/014-104-sandbox-ci', 'conclusion': 'success', 'jobs': jobs([('e2e_bootstrap', 2001), ('validate', 2002), ('fixtures_self_test', 2003), ('convergent_review', 2004)], {})},
        'neg': {'id': 1002, 'headSha': n1, 'headBranch': 'throwaway/104-isolation-removal', 'conclusion': 'failure', 'jobs': jobs([('e2e_bootstrap', 3001), ('validate', 3002), ('fixtures_self_test', 3003), ('convergent_review', 3004)], {'convergent_review': 'failure'})},
        'poslog_id': 2004, 'neglog_id': 3004, 'poslog': list(POS_LOG), 'neglog': list(NEG_LOG),
        'live_poslog': None, 'live_neglog': None, 'live_pos': None, 'live_neg': None,
        'mut_base': c1, 'mut_neg': n1, 'mut_lines': None,
        'pr': {'baseRefName': 'main', 'headRefName': 'throwaway/104-isolation-removal', 'mergedAt': None, 'state': 'CLOSED'}, 'live_pr': None, 'pr_n': 77,
        'branch_absent_lines': [], 'tails': {}, 'line1': {}, 'ls_branch': 'throwaway/104-isolation-removal',
    }

def write_all(t, spec):
    D = pathlib.Path(t) / '.agent/evidence/104'; D.mkdir(parents=True, exist_ok=True)
    fx = pathlib.Path(t).parent / (pathlib.Path(t).name + '.fx'); shutil.rmtree(fx, ignore_errors=True); fx.mkdir()
    def run_json(r): return json.dumps({k: r[k] for k in ('conclusion', 'headBranch', 'headSha', 'jobs')}, separators=(',', ':'))
    def put(name, line1, body, tail='EXIT:0'):
        (D / name).write_text('\n'.join([spec['line1'].get(name, line1)] + body + [spec['tails'].get(name, tail)]) + '\n')
    put('ci-positive-run.txt', 'gh run view %d --json headSha,headBranch,conclusion,jobs' % spec['pos']['id'], [run_json(spec['pos'])])
    put('ci-positive-log.txt', 'gh run view --job %d --log' % spec['poslog_id'], spec['poslog'])
    put('ci-negative-run.txt', 'gh run view %d --json headSha,headBranch,conclusion,jobs' % spec['neg']['id'], [run_json(spec['neg'])])
    put('ci-negative-log.txt', 'gh run view --job %d --log' % spec['neglog_id'], spec['neglog'])
    mb, mn = spec['mut_base'], spec['mut_neg']
    live_diff = sh('git', 'diff', '--no-color', spec['pos']['headSha'], spec['neg']['headSha'], cwd=t).stdout.splitlines()
    mut = spec['mut_lines'] if spec['mut_lines'] is not None else live_diff
    put('ci-negative-mutation.txt', 'git diff --no-color %s %s' % (mb, mn), mut)
    put('ci-negative-pr-state.txt', 'gh pr view %d --json state,mergedAt,headRefName,baseRefName' % spec['pr_n'], [json.dumps(spec['pr'], separators=(',', ':'), sort_keys=True)])
    put('ci-negative-branch-absent.txt', 'git ls-remote --heads origin ' + spec['ls_branch'], spec['branch_absent_lines'])
    # live fixtures served by the gh shim
    (fx / ('run-%d.json' % spec['pos']['id'])).write_text(run_json(spec['live_pos'] or spec['pos']) + '\n')
    (fx / ('run-%d.json' % spec['neg']['id'])).write_text(run_json(spec['live_neg'] or spec['neg']) + '\n')
    (fx / ('log-%d.txt' % spec['poslog_id'])).write_text('\n'.join(spec['live_poslog'] if spec['live_poslog'] is not None else spec['poslog']) + '\n')
    (fx / ('log-%d.txt' % spec['neglog_id'])).write_text('\n'.join(spec['live_neglog'] if spec['live_neglog'] is not None else spec['neglog']) + '\n')
    (fx / ('pr-%d.json' % spec['pr_n'])).write_text(json.dumps(spec['live_pr'] or spec['pr'], separators=(',', ':'), sort_keys=True) + '\n')
    bindir = fx / 'bin'; bindir.mkdir()
    (bindir / 'gh').write_text('''#!/bin/bash
# gh SHIM (read-only canned fixtures)
FX="%s"
if [ "$1 $2" = "run view" ]; then
  if [ "$3" = "--job" ]; then cat "$FX/log-$4.txt"; exit 0; fi
  [ -f "$FX/run-$3.json" ] && { cat "$FX/run-$3.json"; exit 0; }
fi
if [ "$1 $2" = "pr view" ]; then cat "$FX/pr-$3.json"; exit 0; fi
echo "gh shim: unsupported: $*" >&2; exit 4
''' % fx)
    os.chmod(bindir / 'gh', 0o755)
    return str(bindir)

CHECKS = ['AT5', 'AT6', 'AT7', 'AT8', 'S10', 'S11']
def run_checks(t, bindir):
    env = dict(os.environ); env['PATH'] = bindir + ':' + env['PATH']
    out = {}
    for n in CHECKS:
        p = subprocess.run(['bash', str(H / (n + '.sh'))], cwd=t, capture_output=True, text=True, env=env)
        out[n] = (p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:] )
    return out

MUT = {}
def m(i, d):
    def deco(f): MUT[i] = (d, f); return f
    return deco

def _setline(spec, fname, line1): spec['line1'][fname] = line1

@m('c01', 'mutation base != positive headSha (diff taken against an older commit)')
def _(t, s, ctx): s['mut_base'] = ctx['A']
@m('c01b', 'mutation diff target != negative run headSha')
def _(t, s, ctx): s['mut_neg'] = ctx['c1']
@m('c02', 'job at the positive headSha is WEAKENED (-k), HEAD has the pinned job')
def _(t, s, ctx):
    # rebuild: commit a weakened-job commit W, make it the positive headSha, make W an ancestor of HEAD (HEAD = new commit restoring the pinned job)
    wf = pathlib.Path(t) / '.github/workflows/compliance.yml'; good = wf.read_text()
    git(t, 'checkout', '-q', '-b', 'weak', ctx['A']) if False else None
    wf.write_text(good.replace('      - run: python3 tools/test_convergent_review.py\n', '      - run: python3 tools/test_convergent_review.py -k test_a\n'))
    git(t, 'commit', '-q', '-am', 'weakened job W'); w = git(t, 'rev-parse', 'HEAD')
    wf.write_text(good); git(t, 'commit', '-q', '-am', 'restore pinned job')
    s['pos']['headSha'] = w; s['mut_base'] = w
    # negative = N1' on top of W: reuse N1 content on W
    git(t, 'checkout', '-q', '-b', 'neg2', w)
    for f, a, b in (('tools/linux_trial_sandbox.sh', 'exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc', 'exec'), ('tools/isolated_trial_adapter.py', 'syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)', 'pass')):
        p = pathlib.Path(t) / f; p.write_text(p.read_text().replace(a, b))
    git(t, 'commit', '-q', '-am', 'neg on W'); n2 = git(t, 'rev-parse', 'HEAD'); git(t, 'checkout', '-q', 'pos')
    git(t, 'checkout', '-q', '-b', 'tip'); wf.write_text(good)
    git(t, 'merge', '-q', '--no-edit', 'pos') if False else None
    s['neg']['headSha'] = n2; s['mut_neg'] = n2
@m('c03', 'positive log tampered: an UNSUPPORTED line removed from the capture (live log still has it)')
def _(t, s, ctx):
    live = list(s['poslog']) + ['convergent_review\tRun\t2026-10-09T19:00:59.0000000Z test_x ... skipped \'UNSUPPORTED: user-namespace isolation unavailable\'']
    s['live_poslog'] = live
@m('c03b', 'positive log tampered: capture has extra FULL line not in live')
def _(t, s, ctx): s['live_poslog'] = s['poslog'][:-1]
@m('c04', 'positive run cancelled (concurrency cancel-in-progress)')
def _(t, s, ctx): s['pos']['conclusion'] = 'cancelled'; s['pos']['jobs'][3]['conclusion'] = 'cancelled'
@m('c04b', 'positive run success but one sibling job cancelled')
def _(t, s, ctx): s['pos']['jobs'][0]['conclusion'] = 'cancelled'
@m('c04c', 'positive run success but convergent_review job conclusion skipped')
def _(t, s, ctx): s['pos']['jobs'][3]['conclusion'] = 'skipped'
@m('c05', 'positive headBranch is phase/014-ga-track (stale merged head)')
def _(t, s, ctx): s['pos']['headBranch'] = 'phase/014-ga-track'
@m('c05b', 'positive headBranch is main')
def _(t, s, ctx): s['pos']['headBranch'] = 'main'
@m('c06', 'negative log lacks AssertionError: 40 != 0')
def _(t, s, ctx): s['neglog'] = [l for l in s['neglog'] if '40 != 0' not in l]
@m('c06b', 'negative log has AssertionError: 41 != 0')
def _(t, s, ctx): s['neglog'] = [l.replace('40 != 0', '41 != 0') for l in s['neglog']]
@m('c07', 'negative log fails a DIFFERENT test (no cross-trial FAIL line)')
def _(t, s, ctx): s['neglog'] = [l.replace('test_linux_sandbox_blocks_cross_trial_files_and_network', 'test_other') for l in s['neglog']]
@m('c08', 'negative run headBranch not throwaway/104-')
def _(t, s, ctx): s['neg']['headBranch'] = 'phase/014-104-sandbox-ci'
@m('c09', 'negative job conclusion success')
def _(t, s, ctx): s['neg']['jobs'][3]['conclusion'] = 'success'; s['neg']['conclusion'] = 'success'
@m('c10', 'negative PR merged')
def _(t, s, ctx): s['pr']['state'] = 'MERGED'; s['pr']['mergedAt'] = '2026-10-09T20:00:00Z'
@m('c10b', 'negative PR still OPEN')
def _(t, s, ctx): s['pr']['state'] = 'OPEN'
@m('c11', 'throwaway remote branch still exists')
def _(t, s, ctx): git(t, 'push', '-q', 'origin', 'neg:refs/heads/throwaway/104-isolation-removal')
@m('c12', 'mutation touches only the sandbox script (namespace-only, NDEBT-046 shape)')
def _(t, s, ctx):
    git(t, 'checkout', '-q', '-b', 'nsonly', 'pos')
    p = pathlib.Path(t) / 'tools/linux_trial_sandbox.sh'; p.write_text(p.read_text().replace('exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc', 'exec'))
    git(t, 'commit', '-q', '-am', 'ns only'); n = git(t, 'rev-parse', 'HEAD'); git(t, 'checkout', '-q', 'pos')
    s['neg']['headSha'] = n; s['mut_neg'] = n
@m('c12b', 'mutation touches only the adapter (Landlock-only)')
def _(t, s, ctx):
    git(t, 'checkout', '-q', '-b', 'llonly', 'pos')
    p = pathlib.Path(t) / 'tools/isolated_trial_adapter.py'; p.write_text(p.read_text().replace('syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)', 'pass'))
    git(t, 'commit', '-q', '-am', 'll only'); n = git(t, 'rev-parse', 'HEAD'); git(t, 'checkout', '-q', 'pos')
    s['neg']['headSha'] = n; s['mut_neg'] = n
@m('c13', 'mutation also edits the test suite (extra file)')
def _(t, s, ctx):
    git(t, 'checkout', '-q', 'neg')
    p = pathlib.Path(t) / 'tools/test_convergent_review.py'; p.write_text(p.read_text() + '\n# weaken\n')
    git(t, 'commit', '-q', '-am', 'extra'); n = git(t, 'rev-parse', 'HEAD'); git(t, 'checkout', '-q', 'pos')
    s['neg']['headSha'] = n; s['mut_neg'] = n
@m('c13b', 'mutation also edits the workflow job on the throwaway branch')
def _(t, s, ctx):
    git(t, 'checkout', '-q', 'neg')
    p = pathlib.Path(t) / '.github/workflows/compliance.yml'; p.write_text(p.read_text().replace('      - run: python3 tools/test_convergent_review.py\n', '      - run: python3 tools/test_convergent_review.py -k test_a\n'))
    git(t, 'commit', '-q', '-am', 'weak wf'); n = git(t, 'rev-parse', 'HEAD'); git(t, 'checkout', '-q', 'pos')
    s['neg']['headSha'] = n; s['mut_neg'] = n
@m('c14', 'positive log is the log of another job (validate, id 2002) not convergent_review')
def _(t, s, ctx): s['poslog_id'] = 2002
@m('c15', 'positive run capture differs from live (capture says success, live says failure)')
def _(t, s, ctx):
    import copy
    lv = copy.deepcopy(s['pos']); lv['conclusion'] = 'failure'; lv['jobs'][3]['conclusion'] = 'failure'; s['live_pos'] = lv
@m('c16', 'negative run capture differs from live (job ids shuffled)')
def _(t, s, ctx):
    import copy
    lv = copy.deepcopy(s['neg']); lv['jobs'][3]['databaseId'] = 9999; s['live_neg'] = lv
@m('c17', 'positive run has no convergent_review job')
def _(t, s, ctx): s['pos']['jobs'] = s['pos']['jobs'][:3]
@m('c18', 'positive EXIT trailer EXIT:1')
def _(t, s, ctx): s['tails']['ci-positive-run.txt'] = 'EXIT:1'
@m('c19', 'positive headSha is not an ancestor of HEAD')
def _(t, s, ctx): s['pos']['headSha'] = git(t, 'rev-parse', 'neg')
@m('c20', 'positive log lacks CONFORMANCE: FULL')
def _(t, s, ctx): s['poslog'] = [l for l in s['poslog'] if 'CONFORMANCE' not in l]
@m('c21', 'positive log contains skipped')
def _(t, s, ctx): s['poslog'] = s['poslog'] + ['convergent_review\tRun\t2026-10-09T19:00:59.0000000Z OK (skipped=1)']
@m('c22', 'positive log shows CONFORMANCE: NOT FULL only (substring trap)')
def _(t, s, ctx): s['poslog'] = [l.replace('CONFORMANCE: FULL', 'CONFORMANCE: NOT FULL') for l in s['poslog']]
@m('c23', 'run view invocation line carries --exit-status')
def _(t, s, ctx): s['line1']['ci-positive-run.txt'] = 'gh run view 1001 --json headSha,headBranch,conclusion,jobs --exit-status'
@m('c24', 'negative run uses a different job set than positive')
def _(t, s, ctx): s['neg']['jobs'] = [j for j in s['neg']['jobs'] if j['name'] == 'convergent_review']
@m('c25', 'positive log truncated in the capture (live has more lines)')
def _(t, s, ctx):
    s['live_poslog'] = list(s['poslog']); s['poslog'] = s['poslog'][:-2] + [s['poslog'][-1]]
@m('c26', 'FAIL line present in the POSITIVE log')
def _(t, s, ctx): s['poslog'] = s['poslog'] + ['convergent_review\tRun\t2026-10-09T19:00:59.0000000Z FAIL: test_x (a.b)']
@m('c27', 'negative log contains UNSUPPORTED besides the FAIL and 40 != 0 lines (capability + finding)')
def _(t, s, ctx): s['neglog'] = s['neglog'] + ['convergent_review\tRun\tz test_y ... skipped \'UNSUPPORTED: user-namespace isolation unavailable\'']
@m('c28', 'negative mutation capture altered (live git diff differs)')
def _(t, s, ctx):
    live = sh('git', 'diff', '--no-color', s['pos']['headSha'], s['neg']['headSha'], cwd=t).stdout.splitlines()
    s['mut_lines'] = [l for l in live if not l.startswith('index ')]
@m('c29', 'negative branch-absent capture records a result line (branch exists) with EXIT:0')
def _(t, s, ctx): s['branch_absent_lines'] = ['abc123\trefs/heads/throwaway/104-isolation-removal']
@m('c30', 'negative PR is for a non-throwaway headRefName')
def _(t, s, ctx): s['pr']['headRefName'] = 'phase/014-104-sandbox-ci'

@m('real', 'CONTROL with a REAL gh run JSON (run 37967901131, shape as emitted by gh 2.76.2) re-labelled: job fixtures_self_test -> convergent_review, headSha/headBranch rewritten')
def _(t, s, ctx):
    real = json.load(open(os.environ['REAL_RUN_JSON']))   # captured with: gh run view 37967901131 --json headSha,headBranch,conclusion,jobs
    for j in real['jobs']:
        if j['name'] == 'fixtures_self_test': j['name'] = 'convergent_review'; s['poslog_id'] = j['databaseId']
    real['headSha'] = ctx['c1']; real['headBranch'] = 'phase/014-104-sandbox-ci'; real['id'] = 37967901131
    s['pos'] = real
    s['neg']['jobs'] = [j for j in s['neg']['jobs'] if j['name'] != 'fixtures_self_test']

def main():
    base = os.path.join(work, 'T0'); os.makedirs(work, exist_ok=True)
    c1, n1, o = build_t0(base)
    A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
    print('C1 (positive headSha) =', c1[:12], 'N1 (throwaway) =', n1[:12])
    tally = {'caught': 0, 'survived': 0}
    for mid in ['control'] + list(MUT):
        if mid == 'real' and not os.environ.get('REAL_RUN_JSON'): continue
        if only and mid not in only: continue
        t = os.path.join(work, 'run_' + mid)
        shutil.rmtree(t, ignore_errors=True); shutil.rmtree(t + '.fx', ignore_errors=True)
        subprocess.run(['cp', '-a', base, t], check=True)
        # per-mutant private bare origin
        o2 = t + '.origin.git'; shutil.rmtree(o2, ignore_errors=True); shutil.copytree(o, o2)
        git(t, 'remote', 'set-url', 'origin', o2)
        spec = spec_base(c1, n1)
        if mid != 'control':
            MUT[mid][1](t, spec, {'A': A, 'c1': c1, 'n1': n1})
        bindir = write_all(t, spec)
        res = run_checks(t, bindir)
        rcs = {k: v[0] for k, v in res.items()}
        bad = [k for k, v in rcs.items() if v != 0]
        if mid in ('control', 'real'):
            print('%-8s CONTROL all rc=0? %s %s' % (mid, not bad, rcs))
            if bad:
                for k in bad: print('   ', k, res[k][1])
            continue
        tally['caught' if bad else 'survived'] += 1
        print('%-8s %-8s %s :: caught by %s  %s' % (mid, 'CAUGHT' if bad else 'SURVIVED', MUT[mid][0], ','.join(bad) or '-', ''))
        sys.stdout.flush()
        shutil.rmtree(t, ignore_errors=True); shutil.rmtree(t + '.fx', ignore_errors=True); shutil.rmtree(o2, ignore_errors=True)
    print('TALLY', tally)
main()
