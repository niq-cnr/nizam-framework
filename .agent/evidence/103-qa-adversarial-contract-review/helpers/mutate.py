#!/usr/bin/env python3
"""mutate.py NAME TREE : inject ONE named defect into a scratch worktree of the positive-control attempt commit."""
import json, pathlib, re, subprocess, sys
name, tree = sys.argv[1], pathlib.Path(sys.argv[2])
T = tree / 'tools/test_convergent_review.py'

def sub(path, old, new, count=1):
    text = path.read_text()
    assert text.count(old) == count, (name, old[:60], text.count(old))
    path.write_text(text.replace(old, new))

RET = 'return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation) else 1'
M = {}
def m(f): M[f.__name__] = f; return f

@m
def m01_required_exits_zero_when_unsupported(): sub(T, RET, 'return 0 if successful else 1')
@m
def m02a_probe_uses_shell():
    sub(T, 'list(ISOLATION_PROBE_COMMAND), stdin=subprocess.DEVNULL', '" ".join(ISOLATION_PROBE_COMMAND), shell=True, stdin=subprocess.DEVNULL')
@m
def m02b_probe_runs_repo_code_instead():
    sub(T, 'list(ISOLATION_PROBE_COMMAND), stdin=subprocess.DEVNULL', '[sys.executable, str(CLI), "--help"], stdin=subprocess.DEVNULL')
@m
def m02c_probe_also_runs_repo_code():
    sub(T, '    try:\n        completed = subprocess.run(\n            list(ISOLATION_PROBE_COMMAND)', '    subprocess.run([sys.executable, str(CLI), "--help"], capture_output=True, check=False)\n    try:\n        completed = subprocess.run(\n            list(ISOLATION_PROBE_COMMAND)')
@m
def m03a_fallback_in_sandbox_script():
    p = tree / 'tools/linux_trial_sandbox.sh'
    sub(p, 'exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc \\\n  "$SELF_DIR/isolated_trial_adapter.py" --root "$ROOT" --runner "$RUNNER" -- "$@"',
        'unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc \\\n  "$SELF_DIR/isolated_trial_adapter.py" --root "$ROOT" --runner "$RUNNER" -- "$@" || exec "$SELF_DIR/isolated_trial_adapter.py" --root "$ROOT" --runner "$RUNNER" -- "$@"')
@m
def m03b_unsandboxed_fallback_in_wrapper():
    sub(T, '            self.skipTest(f"{UNSUPPORTED_REASON_PREFIX} ({_PROBE_CACHE[0].detail})")\n',
        '            globals()["LINUX_SANDBOX"] = ROOT / "tools/isolated_trial_adapter.py"\n')
@m
def m04a_env_var_relaxes_mode(): sub(T, RET, 'return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation or os.getenv("ALLOW_UNSUPPORTED_ISOLATION")) else 1')
@m
def m04b_env_var_relaxes_mode_obfuscated(): sub(T, RET, 'return 0 if successful and (not unsupported or arguments.allow_unsupported_isolation or vars(os)["env" + "iron"].get("ALLOW_UNSUPPORTED_ISOLATION")) else 1')
@m
def m05a_flag_masks_every_failure(): sub(T, RET, 'return 0 if arguments.allow_unsupported_isolation or (successful and not unsupported) else 1')
@m
def m05b_flag_masks_failures_only_when_unsupported_present(): sub(T, RET, 'return 0 if (arguments.allow_unsupported_isolation and unsupported) or (successful and not unsupported) else 1')
@m
def m05c_flag_masks_sandbox_test_failures_when_probe_passes():
    sub(T, 'def probe_user_namespace_isolation()', '_ALLOW: list[bool] = []\n\n\ndef probe_user_namespace_isolation()')
    sub(T, '        return test_function(self, *args, **kwargs)\n', '        if not (_ALLOW and _ALLOW[0]):\n            return test_function(self, *args, **kwargs)\n        try:\n            return test_function(self, *args, **kwargs)\n        except AssertionError as exc:\n            self.skipTest(f"{UNSUPPORTED_REASON_PREFIX} (masked: {exc})")\n')
    sub(T, '    program = unittest.main(', '    _ALLOW.append(arguments.allow_unsupported_isolation)\n    program = unittest.main(')
@m
def m06_sandbox_script_modified_comment_only():
    p = tree / 'tools/linux_trial_sandbox.sh'; p.write_text(p.read_text() + '# harmless comment\n')
@m
def m07_test_body_changed():
    sub(T, '        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)\n\n\n    def _git_repo', '        self.assertIn(result.returncode, (0, 40, 41), result.stdout + result.stderr)\n\n\n    def _git_repo')
@m
def m08a_second_module_level_subprocess_call():
    sub(T, '\n\ndef requires_user_namespace_isolation', '\n\ndef _extra_probe() -> int:\n    return subprocess.run(["true"], check=False).returncode\n\n\ndef requires_user_namespace_isolation')
@m
def m08b_second_subprocess_call_inside_new_class():
    sub(T, '\n\ndef requires_user_namespace_isolation', '\n\nclass _Helper:\n    def go(self) -> int:\n        return subprocess.run(["true"], check=False).returncode\n\n\ndef requires_user_namespace_isolation')
@m
def m08c_second_spawn_via_from_import_alias():
    sub(T, 'import tempfile\n', 'import tempfile\nfrom subprocess import run as _run\n')
    sub(T, '\n\ndef requires_user_namespace_isolation', '\n\ndef _extra_probe() -> int:\n    return _run(["true"], check=False).returncode\n\n\ndef requires_user_namespace_isolation')
@m
def m09a_out_of_scope_file_added_untracked(): (tree / 'docs').joinpath('extra_notes.md').write_text('x\n')
@m
def m09b_out_of_scope_file_added_in_fixtures(): (tree / 'tools/fixtures/convergent_review/extra.txt').write_text('x\n')
@m
def m10a_status_flip_on_other_feature():
    p = tree / '.agent/feature_list_014.json'; d = json.loads(p.read_text())
    f = next(x for x in d['features'] if x['id'] == '104'); f['status'] = 'in_progress'; p.write_text(json.dumps(d, indent=2) + '\n')
@m
def m10b_legit_status_flip_on_103_only():
    p = tree / '.agent/feature_list_014.json'; d = json.loads(p.read_text())
    f = next(x for x in d['features'] if x['id'] == '103'); f['status'] = 'in_progress'; p.write_text(json.dumps(d, indent=2) + '\n')
@m
def m11a_extra_phase_yaml_key_on_103(): sub(tree / 'docs/planning/phase_014.yaml', '    evidence: .agent/evidence/103/at1-required-mode.txt\n', '    evidence: .agent/evidence/103/at1-required-mode.txt\n    notes: extra\n')
@m
def m11b_phase_yaml_step_104_edited(): sub(tree / 'docs/planning/phase_014.yaml', '    description: Convergent-review suite enforced in CI', '    description: Convergent-review suite is enforced in CI')
@m
def m12a_readme_paragraph_word_altered(): sub(tree / 'tools/README.md', 'the required gate never passes on a host', 'the required gate rarely passes on a host')
@m
def m12b_readme_paragraph_extra_sentence(): sub(tree / 'tools/README.md', 'the suite never runs a trial outside the sandbox.', 'the suite never runs a trial outside the sandbox. Extra sentence.')
@m
def m12c_readme_changelog_summary_altered(): sub(tree / 'tools/README.md', 'Document required-conformance mode', 'Describe required-conformance mode')
@m
def m12d_readme_version_not_bumped(): sub(tree / 'tools/README.md', 'version: 0.12.0\n', 'version: 0.11.0\n')
@m
def m12e_changelog_bullet_altered(): sub(tree / 'CHANGELOG.md', 'turns that same outcome into\n  exit 0', 'turns that same outcome into\n  exit 1')
@m
def m12f_changelog_bullet_under_wrong_heading():
    p = tree / 'CHANGELOG.md'; t = p.read_text()
    i = t.index('- **Phase 014 feature 103'); j = t.index('\n\n## [1.4.0]'); bullet = t[i:j]
    t = t[:i].rstrip('\n') + '\n' + t[j:]
    k = t.index('\n## [1.3.0]'); t = t[:k] + '\n' + bullet + '\n' + t[k:]; p.write_text(t)
@m
def m13_docstring_added_to_isolation_test(): sub(T, '    @requires_user_namespace_isolation\n    def test_linux_sandbox_blocks_cross_trial_files_and_network(self) -> None:\n', '    @requires_user_namespace_isolation\n    def test_linux_sandbox_blocks_cross_trial_files_and_network(self) -> None:\n        """Doc."""\n')
@m
def m14_decorator_without_wraps(): sub(T, '    @functools.wraps(test_function)\n', '')
@m
def m15_probe_runs_eagerly_at_import(): sub(T, '\n\ndef main(', '\n\n_PROBE_CACHE.append(probe_user_namespace_isolation())\n\n\ndef main(')
@m
def m16_unsupported_silently_returns_instead_of_skip(): sub(T, '            self.skipTest(f"{UNSUPPORTED_REASON_PREFIX} ({_PROBE_CACHE[0].detail})")\n', '            return None\n')
@m
def m17_sixth_test_decorated(): sub(T, '    def test_every_object_schema_is_closed(self) -> None:', '    @requires_user_namespace_isolation\n    def test_every_object_schema_is_closed(self) -> None:')
@m
def m18_ordinary_skips_counted_as_unsupported(): sub(T, 'reason.startswith(UNSUPPORTED_REASON_PREFIX)', 'True')
@m
def m19_full_printed_despite_unsupported(): sub(T, 'elif unsupported and successful:', 'elif False:')
@m
def m20_probe_failure_means_available():
    sub(T, '    except FileNotFoundError:\n        return IsolationProbeResult(False, "unshare executable not found on PATH")', '    except FileNotFoundError:\n        return IsolationProbeResult(True, "")')
@m
def m21_abbreviation_accepted_for_flag(): sub(T, 'argparse.ArgumentParser(allow_abbrev=False,', 'argparse.ArgumentParser(allow_abbrev=True,')
@m
def m22_baseline_sandbox_flags_exec_removed_in_tree():
    sub(tree / 'tools/linux_trial_sandbox.sh', 'exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc', 'exec')

if name == 'list': print('\n'.join(M)); sys.exit(0)
M[name]()
