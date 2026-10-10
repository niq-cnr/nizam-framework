# Mutation testing: single-point mutants of the contract-faithful implementation (see helpers/mutate.py). 4 mutants at a time, each in its own tree.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
JOBS=4 python3 "$H/mutate.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/s105/impl /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/mutwork
