# Base states at <A> (64444289) + contract rev 2 (tracked file, modified in the working tree), AT1-AT8 and S01-S18 sequentially.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers/rev2
T="$NIZAM_EVAL_SCRATCH/basecheck"
echo "== tree: HEAD=$(git -C "$T" rev-parse HEAD) ; status: $(git -C "$T" status --short | tr '\n' ' ')"
( cd "$T" && python3 tools/test_convergent_review.py > "$NIZAM_EVAL_SCRATCH/base_suite.txt" 2>&1; echo "suite rc=$?"; grep -E '^(Ran|FAILED|OK)' "$NIZAM_EVAL_SCRATCH/base_suite.txt"; grep -c ' ... FAIL$' "$NIZAM_EVAL_SCRATCH/base_suite.txt" | sed 's/^/FAIL result lines: /'; grep -c skipped "$NIZAM_EVAL_SCRATCH/base_suite.txt" | sed 's/^/skipped lines: /' )
echo "== AT4 base detail (amended AT4: both mutations must be applied, mutated suite fails with 40 != 0, no UNSUPPORTED line):"
( cd "$T" && TAIL=14 python3 "$H/runall.py" . AT4 )
echo "== all checks:"
TAIL=5 python3 "$H/runall.py" "$T"
