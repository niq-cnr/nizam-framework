# Positive control: implement.py applies the contract's pinned texts exactly as the Generator would. All pre-CI checks exit 0:
# (a) uncommitted working tree on <A>+contract, (b) a faithful Generator attempt (B = approved contract commit, attempt-base.txt, 16 captured evidence files, ONE commit),
# before and after the attempt commit, including S02. No sysctl or sudo is executed (S05 uses shims only).
set -u
H=$PWD/.agent/evidence/104-qa-adversarial-contract-review/helpers
echo "== sysctl before: $(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns)"
echo "== (a) pinned texts applied in the scratch clone"
TAIL=1 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/work/impl" | cut -c1-210
echo "== (b) Generator-attempt simulation"
python3 "$H/gen_attempt.py" "$NIZAM_EVAL_SCRATCH/gen" 2>&1 | cut -c1-210
echo "== (b') after the attempt commit: AT1-AT4 AT9 AT10 S01 S02 S03-S09 (sequential)"
TAIL=1 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/gen/att" AT1 AT2 AT3 AT4 AT9 AT10 S01 S02 S03 S04 S05 S06 S07 S08 S09 | cut -c1-210
echo "== evidence-shape check of the 16 captured Generator files (line 1 = invocation, last line EXIT:<code>)"
for f in "$NIZAM_EVAL_SCRATCH"/gen/att/.agent/evidence/104/*.txt; do echo "$(basename "$f"): line1=[$(head -n 1 "$f" | cut -c1-48)] last=[$(tail -n 1 "$f")]"; done
echo "== sysctl after: $(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns)"
