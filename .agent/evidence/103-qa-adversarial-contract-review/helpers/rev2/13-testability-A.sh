# Testability on <A>: static section-10 scan of the 26 commands (rev-2 command files), determinism (3 passes), worktree facts.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers/rev2
A="$NIZAM_EVAL_SCRATCH/att"
echo "### section-10 static scan of the 26 contract commands (read from .agent/contracts/103.json rev 2)"
python3 -I "$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers/anti_patterns.py"
echo
echo "### attempt worktree: .git is a $(test -f "$A/.git" && echo FILE || echo DIR)"
for i in 1 2 3; do echo "### determinism pass $i (AT1-AT4, S09-S14, S17, S18 in the attempt worktree)"; TAIL=1 python3 "$H/runall.py" "$A" AT1 AT2 AT3 AT4 S09 S10 S11 S12 S13 S14 S17 S18 | grep '^###'; done
