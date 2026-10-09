# Single-point mutants of the positive-control implementation (workflow, out-of-scope enforcement files, documents). Fast checks first; slow ones only for survivors.
H=$PWD/.agent/evidence/104-qa-adversarial-contract-review/helpers
python3 "$H/mutate.py" "$NIZAM_EVAL_SCRATCH/work/impl" "$NIZAM_EVAL_SCRATCH/mut" | cut -c1-230
