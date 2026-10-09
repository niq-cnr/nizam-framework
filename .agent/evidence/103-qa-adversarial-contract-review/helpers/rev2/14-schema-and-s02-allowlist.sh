# (1) verdict validates against schema/contract_review.schema.json (empty issue arrays, approved); (2) S02 verbatim in the SHARED tree (BASE=<A>):
# 'extra' must be [] (this review's files are on the allowlist); rc 1 is expected only because the four files_modify paths are not implemented there.
python3 -I -c "
import json, jsonschema
v=json.load(open('.agent/qa/103-contract-review.json')); jsonschema.validate(v, json.load(open('schema/contract_review.schema.json')))
print('contract_review schema: VALID; approved =', v['final_verdict']['approved'], '; revision_reviewed =', v['revision_reviewed'], '; issues/missing/unsupported =', len(v['issues']), len(v['missing_acceptance_coverage']), len(v['unsupported_claims']), '; history entries =', len(v['history']), '(rev-1 approved =', v['history'][0]['approved'], ', rev-1 issues =', len(v['history'][0]['issues']), ')')"
echo "schema rc=$?"
bash .agent/evidence/103-qa-adversarial-contract-review/helpers/rev2/cmds/S02.sh
echo "S02 (shared tree) rc=$?"
git status --short
git diff --name-only | sort
