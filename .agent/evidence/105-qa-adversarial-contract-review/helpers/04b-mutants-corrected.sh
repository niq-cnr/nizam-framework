# Re-run of the mutants whose first-run mutation site was mis-aimed by MY harness (d01 e02 e03 e04 e09 hit the first 'scratch_dirs d || return 1' at line 128, an earlier probe,
# so their 04-mutants.txt outcomes are superseded; d10 was a no-op as written and is redefined). Anchors now include the preceding 'local -a rows=' line of _claim_map_case.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
JOBS=6 python3 "$H/mutate.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/s105/impl /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/mutwork2 d01 d10 e02 e03 e04 e09
