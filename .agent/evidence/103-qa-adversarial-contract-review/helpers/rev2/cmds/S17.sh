python3 - <<'PY'
import json, os, pathlib, re, subprocess, sys, tempfile
FIVE = ['test_linux_sandbox_blocks_cross_trial_files_and_network', 'test_linux_sandbox_blocks_execution_of_runner_generated_trial_file', 'test_prompt_evaluator_rejects_runner_symlink_substitution_for_post_run_files', 'test_prompt_evaluator_runs_three_isolated_validated_trials', 'test_prompt_evaluator_uses_per_trial_packet_copies']
PROBE_ARGS = '--user --map-root-user true'
L = json.load(open('.agent/contracts/103.json'))['design_notes']['output_contract']['lines']
def make_shim(directory, body):
    directory = pathlib.Path(directory); (directory / 'bin').mkdir(parents=True)
    log = directory / 'calls.log'; log.write_text('')
    shim = directory / 'bin' / 'unshare'
    shim.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "' + str(log) + '"\n' + body)
    shim.chmod(0o755)
    return directory / 'bin', log
def run_suite(shim_dir, *args, path=None):
    env = dict(os.environ)
    env['PATH'] = path if path is not None else str(shim_dir) + os.pathsep + os.environ['PATH']
    p = subprocess.run([sys.executable, 'tools/test_convergent_review.py', *args], env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr
def unsupported_lines(out):
    return {t: bool(re.search(r"^" + t + r"\b.*skipped 'UNSUPPORTED: user-namespace isolation unavailable", out, re.M)) for t in FIVE}
def has_line(out, line):
    return re.search(r'^' + re.escape(line) + r'$', out, re.M) is not None
bad = []
with tempfile.TemporaryDirectory() as d:
    shim_dir, log = make_shim(d, 'if [ "$*" = "' + PROBE_ARGS + '" ]; then exit 0; fi\necho "simulated sandbox failure" >&2\nexit 97\n')
    rc, out = run_suite(shim_dir, '--allow-unsupported-isolation')
    calls = log.read_text().splitlines()
fails = sorted(re.findall(r'^FAIL: (test_\w+)', out, re.M))
if fails != sorted(FIVE): bad.append('FAIL lines are not exactly the five isolation-dependent tests: ' + repr(fails))
if re.search(r'^ERROR: test_', out, re.M): bad.append('unexpected ERROR')
if 'UNSUPPORTED' in out or 'skipped' in out: bad.append('a failing sandbox test was reported UNSUPPORTED/skipped under the flag (the flag masked a real failure)')
if rc == 0: bad.append('exit 0 under the flag although five sandbox tests failed')
if L['allow_note'] in out or L['required_note'] in out: bad.append('a note line was printed although no UNSUPPORTED outcome occurred')
if not has_line(out, L['not_full_failing']): bad.append('exact run-unsuccessful NOT FULL line missing')
if 'CONFORMANCE: FULL' in out: bad.append('FULL printed for a failing run')
if calls[:1] != [PROBE_ARGS] or sum(1 for c in calls if c.startswith('--user --map-root-user --net ')) < 5: bad.append('the five tests did not each invoke the sandbox after a successful probe: ' + repr(calls))
print('rc=%d' % rc, 'FAIL lines:', fails, 'unshare calls:', len(calls))
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
