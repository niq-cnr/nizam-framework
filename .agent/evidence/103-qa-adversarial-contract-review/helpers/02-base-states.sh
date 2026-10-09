# Base states: scratch clone at 88959c9 plus the proposed contract (untracked), run AT1-AT8 and S01-S16 sequentially.
set -u
H=.agent/evidence/103-qa-adversarial-contract-review/helpers
echo "== base HEAD: $(git -C "$NIZAM_EVAL_SCRATCH/base" rev-parse --short 88959c9) (clone is on scratch-B only for later steps; checking out 88959c9 detached copy)"
cd "$NIZAM_EVAL_SCRATCH" && git -C base worktree add -q --detach ../basecheck 88959c9 && cp base/.agent/contracts/103.json basecheck/.agent/contracts/103.json && cd - >/dev/null
echo "== worktree HEAD: $(git -C "$NIZAM_EVAL_SCRATCH/basecheck" rev-parse --short HEAD); untracked: $(git -C "$NIZAM_EVAL_SCRATCH/basecheck" status --short)"
echo "== suite at base (exit read from the process):"
( cd "$NIZAM_EVAL_SCRATCH/basecheck" && python3 tools/test_convergent_review.py > "$NIZAM_EVAL_SCRATCH/base_suite.txt" 2>&1; echo "suite rc=$?" ; grep -c ' ... FAIL$' "$NIZAM_EVAL_SCRATCH/base_suite.txt" | sed 's/^/FAIL result lines: /'; grep -E '^(Ran|FAILED|OK)' "$NIZAM_EVAL_SCRATCH/base_suite.txt"; grep -c skipped "$NIZAM_EVAL_SCRATCH/base_suite.txt" | sed 's/^/skipped lines: /' )
echo "== AT/S results at base (rc per check; last lines of output):"
TAIL=6 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/basecheck"
git -C "$NIZAM_EVAL_SCRATCH/base" worktree remove --force ../basecheck
