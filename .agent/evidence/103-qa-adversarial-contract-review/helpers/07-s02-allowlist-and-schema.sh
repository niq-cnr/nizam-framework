# (1) verdict validates against schema/contract_review.schema.json; (2) S02's scope/allowlist logic, run verbatim in the SHARED repo,
# must list none of this review's files under 'extra:' (expected overall rc=1 only because the four files_modify paths are not yet implemented).
python3 -I -c "
import json, jsonschema
v=json.load(open('.agent/qa/103-contract-review.json')); jsonschema.validate(v, json.load(open('schema/contract_review.schema.json')))
print('contract_review schema: VALID; approved =', v['final_verdict']['approved'], '; issues =', len(v['issues']))"
echo "schema rc=$?"
bash .agent/evidence/103-qa-adversarial-contract-review/helpers/cmds/S02.sh
echo "S02 rc=$? (1 expected at this stage: only 'modify paths not changed' may be non-empty; 'extra' must be [])"
git status --short
git diff --stat HEAD -- . ':!.agent/run_state.json' | tail -3
