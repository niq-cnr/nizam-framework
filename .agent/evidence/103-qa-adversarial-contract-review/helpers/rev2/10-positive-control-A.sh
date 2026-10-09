# Positive control on <A>: contract-faithful minimal implementation (helpers/rev2/implement.py) in an attempt worktree at <B>.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers/rev2
A="$NIZAM_EVAL_SCRATCH/att"
echo "== attempt worktree: HEAD=$(git -C "$A" rev-parse --short HEAD) parent(B)=$(git -C "$A" rev-parse --short HEAD~1) grandparent(<A>)=$(git -C "$A" rev-parse HEAD~2); .git is a $(test -f "$A/.git" && echo FILE || echo DIR); porcelain lines: $(git -C "$A" status --porcelain | wc -l)"
git -C "$A" diff --stat HEAD~1 HEAD
echo "== all 26 verification commands (AT1-AT8, S01-S18), exit status read from each process, attempt commit applied:"
TAIL=3 python3 "$H/runall.py" "$A"
echo
echo "== SIMULATED capable host (PATH shim, not capable-host evidence): AT1, AT2 and the amended AT4 capable branch"
mkdir -p "$NIZAM_EVAL_SCRATCH/capbin"; cp "$H/capable_shim.sh" "$NIZAM_EVAL_SCRATCH/capbin/unshare"; chmod +x "$NIZAM_EVAL_SCRATCH/capbin/unshare"
cd "$A"
PATH="$NIZAM_EVAL_SCRATCH/capbin:$PATH" bash "$H/cmds/AT1.sh"; echo "AT1 capable-sim rc=$?"
PATH="$NIZAM_EVAL_SCRATCH/capbin:$PATH" bash "$H/cmds/AT2.sh"; echo "AT2 capable-sim rc=$?"
PATH="$NIZAM_EVAL_SCRATCH/capbin:$PATH" bash "$H/cmds/AT4.sh" 2>&1 | grep -E "scratch_run: (replaced|command)|AssertionError|^FAIL:|PASS|FAIL |CONFORMANCE|scratch_run: EXP"; echo "AT4 capable-sim rc=${PIPESTATUS[0]}"
