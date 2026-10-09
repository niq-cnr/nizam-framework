# Positive control (a): the contract's reference_implementation.text and pinned_texts applied by helpers/implement.py to a scratch clone at <A>;
# every check executable pre-implementation-commit (AT1-AT5, S01, S03-S09). Sequential.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
echo "== sysctl key: $(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>&1)"
git -C /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/s105/impl diff --stat
TAIL=2 python3 "$H/runall.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/s105/impl
