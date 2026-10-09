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
import importlib.util
bad = []
keys = []
for t in FIVE:
    keys += ['-k', t]
with tempfile.TemporaryDirectory() as d:
    empty = pathlib.Path(d) / 'empty'; empty.mkdir()
    for label, extra in (('required', []), ('allow', ['--allow-unsupported-isolation'])):
        rc, out = run_suite(None, *extra, *keys, path=str(empty))
        if 'Ran 5 tests' not in out or [t for t, ok in unsupported_lines(out).items() if not ok]: bad.append(label + ': five UNSUPPORTED lines not produced with unshare absent')
        if 'unshare executable not found on PATH' not in out: bad.append(label + ': detail does not say unshare is missing')
        if (rc == 0) == (label == 'required'): bad.append(label + ': wrong exit status %d' % rc)
        print(label, 'rc=%d' % rc)
    shim_dir, log = make_shim(pathlib.Path(d) / 'slow', 'exec sleep 30\n')
    saved = os.environ['PATH']; os.environ['PATH'] = str(shim_dir) + os.pathsep + saved
    spec = importlib.util.spec_from_file_location('ncr_under_test', 'tools/test_convergent_review.py'); mod = importlib.util.module_from_spec(spec); sys.modules['ncr_under_test'] = mod; spec.loader.exec_module(mod)
    mod.ISOLATION_PROBE_TIMEOUT_SECONDS = 1
    slow = mod.probe_user_namespace_isolation()
    os.environ['PATH'] = saved
    if slow.available or 'timed out' not in slow.detail: bad.append('a hanging probe was not reported unavailable with a timeout detail: ' + repr(slow))
    shim_dir, log = make_shim(pathlib.Path(d) / 'ok', 'exit 0\n')
    os.environ['PATH'] = str(shim_dir) + os.pathsep + saved
    good = mod.probe_user_namespace_isolation()
    os.environ['PATH'] = saved
    if not good.available or log.read_text().splitlines() != [PROBE_ARGS]: bad.append('probe success path wrong: ' + repr(good) + repr(log.read_text()))
    if sorted(mod.ISOLATION_DEPENDENT_TESTS) != sorted(FIVE): bad.append('decorator registry != the five tests: ' + repr(mod.ISOLATION_DEPENDENT_TESTS))
    print('timeout probe:', slow, 'success probe:', good, 'registry:', sorted(mod.ISOLATION_DEPENDENT_TESTS) == sorted(FIVE))
print('problems:', bad)
sys.exit(1 if bad else 0)
PY
