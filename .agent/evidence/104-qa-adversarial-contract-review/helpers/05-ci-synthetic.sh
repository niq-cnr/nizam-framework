# AT5-AT8, S10, S11 against synthetic captures + a gh SHIM (canned live fixtures; git is real, origin is a local bare repo).
# 'control' and 'real' (a REAL gh run JSON re-labelled) must be all-0; every mutant must fail >= 1 of the six.
H=$PWD/.agent/evidence/104-qa-adversarial-contract-review/helpers
python3 "$H/ci_synth.py" "$NIZAM_EVAL_SCRATCH/work/impl" "$NIZAM_EVAL_SCRATCH/ci" | cut -c1-240
echo "== real gh-shape control"
REAL_RUN_JSON="$NIZAM_EVAL_SCRATCH/real_run_103pr.json" python3 "$H/ci_synth.py" "$NIZAM_EVAL_SCRATCH/work/impl" "$NIZAM_EVAL_SCRATCH/ci2" real | cut -c1-240
