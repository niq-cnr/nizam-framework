# Findings that the contract's 24 checks do not (or cannot) catch. Scratch tree only.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers
A="$NIZAM_EVAL_SCRATCH/att"; CAP="$NIZAM_EVAL_SCRATCH/capbin"
cp "$H/capable_shim.sh" "$CAP/unshare"; chmod +x "$CAP/unshare"
echo "### F1  AT4 capable-host branch, simulated: PATH shim makes the probe succeed (so AT4's own 'cap' is True); the mutation removes unshare from the sandbox script, so the shim is never consulted"
( cd "$A" && PATH="$CAP:$PATH" bash "$H/cmds/AT4.sh" 2>&1 | grep -v '\.\.\. ok$'; echo "AT4 (capable branch, simulated) rc=${PIPESTATUS[0]}" )
echo
echo "### F1b control: AT1 and AT2 capable branches (CONFORMANCE: FULL, no UNSUPPORTED, no skipped) with the same shim"
( cd "$A" && PATH="$CAP:$PATH" bash "$H/cmds/AT1.sh"; echo "AT1 (capable, simulated) rc=$?"; PATH="$CAP:$PATH" bash "$H/cmds/AT2.sh"; echo "AT2 (capable, simulated) rc=$?" )
echo
echo "### F1c a mutation the cross-trial test DOES detect (Landlock restriction disabled in the adapter), same capable shim"
( cd "$A" && PATH="$CAP:$PATH" python3 .agent/evidence/phase-014-activation/gates/scratch_run.py --replace tools/isolated_trial_adapter.py 'syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)' 'pass' --expect-rc nonzero --expect '^(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network' -- python3 tools/test_convergent_review.py 2>&1 | grep -E '^(FAIL:|AssertionError|Ran |FAILED|CONFORMANCE|PASS|FAIL |scratch_run)'; echo "rc=${PIPESTATUS[0]}" )
echo
echo "### F2  S10 shim: probe passes, full sandbox refused; count of unshare calls (1 probe + one sandbox call per test)"
( cd "$A" && bash "$H/cmds/S10.sh" | cut -c1-900; echo "S10 rc=${PIPESTATUS[0]}" )
echo
echo "### F3  --allow-unsupported-isolation + partial capability (probe ok, sandbox refused): the flag must not convert the five FAILs"
echo "positive control:"; python3 "$H/gap_probes.py" "$A" flag_with_partial_capability
git -C "$NIZAM_EVAL_SCRATCH/base" worktree add -q --detach ../mutwt/g1 cda6778 && python3 "$H/mutate.py" m05c_flag_masks_sandbox_test_failures_when_probe_passes "$NIZAM_EVAL_SCRATCH/mutwt/g1"
echo "mutant m05c (flag masks sandbox-test failures when the probe passed):"; python3 "$H/gap_probes.py" "$NIZAM_EVAL_SCRATCH/mutwt/g1" flag_with_partial_capability
echo "all 24 checks on m05c: see 04-negative-controls.txt (every one exits 0)"
git -C "$NIZAM_EVAL_SCRATCH/base" worktree remove --force ../mutwt/g1
echo
echo "### F4  ordinary (jsonschema-ImportError) skips on a capable host must not count as UNSUPPORTED"
echo "positive control:"; python3 "$H/gap_probes.py" "$A" ordinary_skip_on_capable_host
git -C "$NIZAM_EVAL_SCRATCH/base" worktree add -q --detach ../mutwt/g2 cda6778 && python3 "$H/mutate.py" m18_ordinary_skips_counted_as_unsupported "$NIZAM_EVAL_SCRATCH/mutwt/g2"
echo "mutant m18 (every skip counted as UNSUPPORTED):"; python3 "$H/gap_probes.py" "$NIZAM_EVAL_SCRATCH/mutwt/g2" ordinary_skip_on_capable_host
echo "all 24 checks on m18: see 04-negative-controls.txt (every one exits 0)"
git -C "$NIZAM_EVAL_SCRATCH/base" worktree remove --force ../mutwt/g2
