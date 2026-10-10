# Base states at <A> + contract (scratch clone): every verification entry's declared state_at_base_A. Sequential.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
TAIL=3 python3 "$H/runall.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/s105/base AT1 AT2 AT3 AT4 AT5 S01 S02 S03 S04 S05 S06 S07 S08 S09
