# Positive control: contract-faithful minimal implementation (helpers/implement.py) in an attempt worktree at <B> = approved-contract commit.
set -u
H=.agent/evidence/103-qa-adversarial-contract-review/helpers
A="$NIZAM_EVAL_SCRATCH/att"
echo "== attempt worktree: HEAD=$(git -C "$A" rev-parse --short HEAD) parent(B)=$(git -C "$A" rev-parse --short HEAD~1) base=$(git -C "$A" rev-parse --short HEAD~2); .git is a $(test -f "$A/.git" && echo FILE || echo DIR); porcelain lines: $(git -C "$A" status --porcelain | wc -l)"
git -C "$A" diff --stat HEAD~1 HEAD
echo "== all 24 verification commands, exit status read from each process:"
TAIL=3 python3 "$H/runall.py" "$A"
