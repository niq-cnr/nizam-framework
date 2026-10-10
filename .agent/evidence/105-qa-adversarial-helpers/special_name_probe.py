#!/usr/bin/env python3
"""special_name_probe.py [--keep] : Evaluator adversarial check for feature 105 (methodology/02 Section 8).

Question: can an UNCLAIMED subdirectory of tools/fixtures/ evade the claim map / completeness guard because of its NAME?
The guard is bash and keys an associative array by directory name (claim_count["${entry}"], claimed_dir["${f%%/*}"]).
In bash the subscripts '@' and '*' are special even for associative arrays (they expand to ALL values), so a directory
literally named '@' or '*' could be read as 'claimed' when any real claim exists. This is a name-driven bypass class that
none of the contract's 14 checks nor the 92 contract-review mutants exercise (they use ordinary names).

Method: for each hostile name, copy the repository (tracked + untracked, symlinks preserved) into a private directory
OUTSIDE the repository, create tools/fixtures/<name>/probe.json there, run `bash tools/fixtures_self_test.sh` in the copy and
require: exit status 1, a final 'SELF-TEST FAILED' line, and the hostile name reported (claim-map 'unclaimed subdirectory'
or completeness 'below an unclaimed subdirectory'). Ordinary names are included as controls (they must fail the same way), and
the unmodified copy is the positive control (must exit 0, 'SELF-TEST OK'). Sequential: never two self-tests at once.
Nothing in the real repository is written."""
import os, re, shutil, subprocess, sys, tempfile
REPO = os.getcwd()
assert subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip() == REPO, 'run from repo root'
SCRATCH_PARENT = os.environ.get('PROBE_SCRATCH') or tempfile.gettempdir()
assert not os.path.realpath(SCRATCH_PARENT).startswith(os.path.realpath(REPO) + os.sep)
NAMES = [('control: ordinary name', 'zz_unclaimed_probe'),
         ('hidden directory', '.zz_hidden'),
         ('name with a space', 'zz probe dir'),
         ('leading dash', '-zz'),
         ('glob star', '*'),
         ('subscript at-sign', '@'),
         ('subscript at-sign inside brackets', 'a]b'),
         ('arithmetic-looking', '$(echo hi)')]
problems = []
def run_case(label, name):
    parent = tempfile.mkdtemp(prefix='p105-', dir=SCRATCH_PARENT)
    try:
        root = os.path.join(parent, 'repo')
        shutil.copytree(REPO, root, symlinks=True)
        if name is not None:
            d = os.path.join(root, 'tools', 'fixtures', name)
            os.makedirs(d); open(os.path.join(d, 'probe.json'), 'w').write('{}\n')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run(['bash', 'tools/fixtures_self_test.sh'], cwd=root, capture_output=True, text=True, env=env)
        out = p.stdout + p.stderr
        lines = out.splitlines()
        last = lines[-1] if lines else ''
        if name is None:
            ok = p.returncode == 0 and re.search(r'^SELF-TEST OK: (\d+)/\1 fixtures accounted for, 0 failed', out, re.M)
            print('%-40s rc=%d last=%r %s' % (label, p.returncode, last[:70], 'PASS' if ok else 'FAIL'))
            if not ok: problems.append('positive control failed: rc=%d' % p.returncode)
            return
        named = name in out
        flagged = ('unclaimed subdirectory' in out) or ('below an unclaimed subdirectory' in out)
        ok = p.returncode == 1 and 'SELF-TEST FAILED' in out and flagged and named
        print('%-40s name=%r rc=%d SELF-TEST FAILED=%s flagged-unclaimed=%s name-reported=%s -> %s' % (
            label, name, p.returncode, 'SELF-TEST FAILED' in out, flagged, named, 'GUARD HELD' if ok else 'GUARD EVADED OR MISREPORTED'))
        if not ok:
            problems.append('%s (%r): rc=%d flagged=%s named=%s' % (label, name, p.returncode, flagged, named))
            for l in [l for l in lines if 'claim-map' in l or 'completeness' in l or 'SELF-TEST' in l][:8]: print('      | ' + l)
    finally:
        shutil.rmtree(parent, ignore_errors=True)
run_case('positive control: unmodified copy', None)
for label, name in NAMES: run_case(label, name)
print('problems:', problems)
sys.exit(0 if not problems else 1)
