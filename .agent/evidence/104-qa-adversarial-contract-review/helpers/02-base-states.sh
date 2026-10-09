# Base states at <A> + the proposed contract (scratch clone, nothing implemented): every declared state_at_base_A is reproduced.
set -u
H=$PWD/.agent/evidence/104-qa-adversarial-contract-review/helpers
bash "$H/setup_scratch.sh" "$NIZAM_EVAL_SCRATCH/work" 2>&1 | head -3
echo "== declared: AT1=1 AT2=0 AT3=1 AT4=1 AT5-AT8=1 AT9=0 AT10=0 S01=0 S02=1 S03=1 S04=1 S05=1 S06=1 S07=1 S08=0 S09=0 S10=1 S11=1"
TAIL=2 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/work/base" AT1 AT2 AT3 AT4 AT5 AT6 AT7 AT8 AT9 AT10 S01 S02 S03 S04 S05 S06 S07 S08 S09 S10 S11 | cut -c1-210
