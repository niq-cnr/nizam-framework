# (1) the verdict validates against schema/contract_review.schema.json (what 103 used); (2) S03 verbatim in the SHARED tree: 'extra' must be [] (this review's files are on the allowlist;
# rc 1 is expected only because the six files_modify paths are not implemented there); (3) the .txt evidence shape; (4) the verdict plus evidence do not break validate.sh (scratch clone of HEAD + these files);
# (5) no tracked file and not the contract was modified by this review.
set -u
NS="$NIZAM_EVAL_SCRATCH"
python3 -I -c "
import json, jsonschema
v=json.load(open('.agent/qa/104-contract-review.json')); jsonschema.validate(v, json.load(open('schema/contract_review.schema.json')))
print('contract_review schema: VALID; approved =', v['final_verdict']['approved'], '; revision_reviewed =', v['revision_reviewed'], '; issues/missing/unsupported =', len(v['issues']), len(v['missing_acceptance_coverage']), len(v['unsupported_claims']))"
echo "schema rc=$?"
bash .agent/evidence/104-qa-adversarial-contract-review/helpers/cmds/S03.sh
echo "S03 (shared tree) rc=$?"
echo "== evidence shape: every .txt in this directory (helpers/ excluded): command on line 1, EXIT:<code> last"
for f in .agent/evidence/104-qa-adversarial-contract-review/*.txt; do
  case "$f" in *08-schema-and-s03-allowlist.txt) echo "$(basename "$f"): (this file, being written)"; continue;; esac
  l1=$(head -n 1 "$f"); last=$(tail -n 1 "$f"); case "$last" in EXIT:[0-9]*) e=ok;; *) e=BAD;; esac; case "$l1" in EXIT:*|"") a=BAD;; *) a=ok;; esac
  echo "$(basename "$f"): line1=$a last=[$last] $e"
done
echo "== git status (tracked-file changes other than run_state.json must be none)"
git status --short
git diff --name-only | sort
echo "== contract unchanged"
sha256sum .agent/contracts/104.json
echo "== validate.sh on a scratch clone of HEAD + the untracked/new review files"
T=$(mktemp -d -p "$NS"); git clone -q "$PWD" "$T/c"
mkdir -p "$T/c/.agent/contracts" "$T/c/.agent/validator" "$T/c/.agent/qa"
cp .agent/contracts/104.json "$T/c/.agent/contracts/"; cp .agent/validator/104-mode-a.json "$T/c/.agent/validator/"; cp .agent/qa/104-contract-review.json "$T/c/.agent/qa/"
mkdir -p "$T/c/.agent/evidence"; cp -a .agent/evidence/104-qa-adversarial-contract-review "$T/c/.agent/evidence/"
(cd "$T/c" && bash tools/validate.sh > "$T/validate.out" 2>&1; echo "validate rc=$?"; grep -E "^SUMMARY|FAIL" "$T/validate.out")
