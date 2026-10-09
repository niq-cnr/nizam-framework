# Testability: section-10 static scan, determinism (3 repetitions), cwd dependence, attempt-worktree execution.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers
A="$NIZAM_EVAL_SCRATCH/att"
echo "### static scan of the 24 commands (pipeline-swallowed exits, || true, network, wall clock, absolute paths, chdir, bare except-pass)"
python3 -I "$H/anti_patterns.py"
echo
echo "### attempt worktree facts: .git is a $(test -f "$A/.git" && echo FILE || echo DIR) -> $(cat "$A/.git")"
echo
for i in 1 2 3; do echo "### determinism pass $i (AT1-AT4, S09-S13 in the attempt worktree)"; TAIL=0 python3 "$H/runall.py" "$A" AT1 AT2 AT3 AT4 S09 S10 S11 S12 S13; done
echo
echo "### cwd dependence: AT6 and S04 run from a directory that is NOT the repo root (expected to fail: commands are root-relative, as the contract's evidence_convention states)"
( cd "$NIZAM_EVAL_SCRATCH" && bash "$H/cmds/AT6.sh" 2>&1 | tail -1; echo "AT6 from non-root rc=${PIPESTATUS[0]}" )
( cd "$A" && bash "$H/cmds/AT6.sh"; echo "AT6 from attempt-worktree root rc=$?" )
