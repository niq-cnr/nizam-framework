#!/usr/bin/env bash
# Disposable live probes for framework-integrity findings SQA-integrity-003 and -004
# (audit c905615d; findings sha256 82d4df0b34fc4235...). Writes only mktemp fixtures;
# the checkout is read-only input. Each case prints one "CASE <id> rc=<n> <verdict>" line.
# Usage: bash tools/probes/s003004_integrity_probe.sh [REPO_ROOT]
set -uo pipefail
REPO="$(cd "${1:-$(dirname "$0")/../..}" && pwd)"
W="$(mktemp -d "${TMPDIR:-/tmp}/s003004-probe.XXXXXX")"
export PYTHONDONTWRITEBYTECODE=1
say() { printf '%s\n' "$*"; }

# ---- 003: C11 schema check + C16 completion check on one contradictory QA record ----
P003="${W}/p003"; mkdir -p "${P003}/.agent/contracts" "${P003}/.agent/qa" "${P003}/.agent/evidence/900" "${P003}/schema"
cp "${REPO}/schema/feature_list.schema.json" "${REPO}/schema/qa_verdict.schema.json" "${P003}/schema/"
printf 'proof\n' > "${P003}/.agent/evidence/900/proof.txt"
cat > "${P003}/.agent/feature_list_900.json" <<'JSON'
{"phase":"900-scratch","spec_version":"1.0.0","original_estimate_lines":10,
 "features":[{"id":"900","name":"S","description":"S","status":"complete","dependencies":[],
 "acceptance_tests":["a"],"estimated_lines":10,"passes":true}]}
JSON
printf '{"contract_id":"900","status":"complete"}\n' > "${P003}/.agent/contracts/900.json"
# Contradictory: rejected (qa_pass=false, checks_passed=0) yet final_verdict.approved=true, nonempty issues.
cat > "${P003}/.agent/qa/900.json" <<'JSON'
{"feature_id":"900","qa_pass":false,"checks_run":2,"checks_passed":0,
 "adversarial":{"performed":true},"evidence_files":[".agent/evidence/900/proof.txt"],
 "issues":["blocking defect: acceptance not met"],"unsupported_claims":[],
 "missing_acceptance_coverage":[],"required_fixes":["fix defect"],
 "final_verdict":{"approved":true,"summary":"contradictory fixture"}}
JSON
# C11 analogue: validate.sh C11 applies this exact jsonschema call to .agent/qa/*.json
(cd "${P003}" && python3 -c '
import json,sys,jsonschema
s=json.load(open("schema/qa_verdict.schema.json")); d=json.load(open(".agent/qa/900.json"))
jsonschema.validate(instance=d, schema=s)' >/dev/null 2>&1)
c11=$?
# C16 analogue: vlib_feature_list_lifecycle sourced from verify_lib.sh, run in the scratch root
(cd "${P003}" && source "${REPO}/tools/verify_lib.sh" && vlib_feature_list_lifecycle >/dev/null 2>&1)
c16=$?
say "CASE 003-contradictory-qa C11_schema_rc=${c11} C16_completion_rc=${c16} (accept = rc 0; required after fix: both nonzero)"

# Clean (genuinely passing) record must keep passing after the fix.
cat > "${P003}/.agent/qa/900.json" <<'JSON'
{"feature_id":"900","qa_pass":true,"checks_run":2,"checks_passed":2,
 "adversarial":{"performed":true},"evidence_files":[".agent/evidence/900/proof.txt"],
 "issues":[],"unsupported_claims":[],"missing_acceptance_coverage":[],"required_fixes":[],
 "final_verdict":{"approved":true,"summary":"clean"}}
JSON
(cd "${P003}" && python3 -c '
import json,jsonschema
jsonschema.validate(instance=json.load(open(".agent/qa/900.json")), schema=json.load(open("schema/qa_verdict.schema.json")))' >/dev/null 2>&1)
c11c=$?
(cd "${P003}" && source "${REPO}/tools/verify_lib.sh" && vlib_feature_list_lifecycle >/dev/null 2>&1)
c16c=$?
say "CASE 003-clean-qa C11_schema_rc=${c11c} C16_completion_rc=${c16c} (required: both 0)"

# ---- 004: ecosystem_audit.py entry gate ----
P004="${W}/p004"; mkdir -p "${P004}"
printf '[{"id":"F1","severity":"low","confidence":"Confirmed","evidence":[{"path":".agent/evidence/e1/x.txt","revision":"abc123"}],"impact":"i","owner":"o","status":"open","closure_criteria":"c"}]' > "${P004}/findings.json"
printf '{"verdict":"PASS","execution_id":"e1","generated_at":"t"}' > "${P004}/pf-ok.json"
printf '{"execution_id":"e1"}' > "${P004}/baseline-minimal.json"
printf '{"verdict":"PASS","execution_id":"e1","generated_at":"t","blocking_findings":["unresolved blocker"]}' > "${P004}/pf-blocking.json"
printf '{"verdict":"PASS","generated_at":"t"}' > "${P004}/pf-noexec.json"
printf '{"verdict":"PASS","execution_id":"e2","generated_at":"t"}' > "${P004}/pf-mismatch.json"
run004() { # $1=case $2=preflight $3=baseline
  python3 "${REPO}/tools/ecosystem_audit.py" --audit-id a --output-dir "${W}/out-$1" \
    --findings-input "${P004}/findings.json" --preflight "$2" --baseline "$3" >/dev/null 2>&1
  local rc=$?
  if [ "${rc}" -eq 0 ]; then say "CASE $1 rc=${rc} ASSEMBLED (accepted)"; else say "CASE $1 rc=${rc} REFUSED"; fi
}
run004 004-minimal-baseline-clean-preflight "${P004}/pf-ok.json" "${P004}/baseline-minimal.json"
run004 004-pass-with-blocking-findings "${P004}/pf-blocking.json" "${P004}/baseline-minimal.json"
run004 004-preflight-missing-execution-id "${P004}/pf-noexec.json" "${P004}/baseline-minimal.json"
run004 004-execution-id-mismatch "${P004}/pf-mismatch.json" "${P004}/baseline-minimal.json"

# Weakened permanent fixture: fixtures_self_test.sh encodes the incomplete baseline as a positive case.
say "FIXTURE tools/fixtures_self_test.sh:858-859 baseline='$(grep -o "printf '{\"execution_id\":\"e1\"}' > \"\${d}/baseline.json\"" "${REPO}/tools/fixtures_self_test.sh" | head -1)'"
rm -rf "${W}"
