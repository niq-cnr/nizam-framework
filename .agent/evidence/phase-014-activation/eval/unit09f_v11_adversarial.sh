#!/bin/bash
# Adversarial review of the V11 allowlist (validate_backlog_dag.py rev 2.1). Works on a COPY; nothing in the repo is written.
set -u
export PYTHONDONTWRITEBYTECODE=1
SRC="$(pwd)"; COPY="$(mktemp -d "${TMPDIR:-/tmp}/eval-v11adv.XXXXXX")"; OUT="$(mktemp -d "${TMPDIR:-/tmp}/eval-v11adv-out.XXXXXX")"
cp -a "$SRC/." "$COPY/"; cd "$COPY" || exit 3
V=.agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py
fail=0
v11() { grep -E "^(PASS|FAIL) V11" "$OUT/o.txt" | cut -c1-110; }
case_flag() { # label, want_rc, status lines...
  local label="$1" want="$2"; shift 2
  git status --porcelain --untracked-files=all > "$OUT/st.txt"; printf '%s\n' "$@" >> "$OUT/st.txt"
  python3 $V --git-status "$OUT/st.txt" > "$OUT/o.txt" 2>&1; rc=$?
  local res=OK; [ "$rc" = "$want" ] || { res=BAD; fail=1; }
  echo "$res flag-case: $label rc=$rc want=$want :: $(v11)"
}
echo "== A. exact-equality semantics via --git-status (real status + extra lines)"
case_flag "exact verdict path (untracked)"                 0 "?? .agent/validator/phase-014-activation.json"
case_flag "exact verdict path with modified flag"          0 " M .agent/validator/phase-014-activation.json"
case_flag "suffix look-alike .json.bak"                    1 "?? .agent/validator/phase-014-activation.json.bak"
case_flag "prefix look-alike (.json without trailing)"     1 "?? .agent/validator/phase-014-activation.js"
case_flag "sibling verdict phase-014-other.json"           1 "?? .agent/validator/phase-014-other.json"
case_flag "verdict path as a directory component"          1 "?? .agent/validator/phase-014-activation.json/x.json"
case_flag "subdirectory path of validator dir"             1 "?? .agent/validator/sub/phase-014-activation.json"
case_flag "case-variant verdict path"                      1 "?? .agent/validator/Phase-014-activation.json"
case_flag "payload edit tools/validate.sh"                 1 " M tools/validate.sh"
case_flag "stray .agent/run_state.json.bak"                1 "?? .agent/run_state.json.bak"
case_flag "stray outside package: bootstrap.sh"            1 " M bootstrap.sh"
echo "== B. normal invocation (no flag) must still call git status"
touch tools/ZZ_planted_stray.txt
python3 $V > "$OUT/o.txt" 2>&1; rc=$?
res=OK; [ "$rc" = 1 ] || { res=BAD; fail=1; }
echo "$res default run with a planted untracked tools/ file: rc=$rc want=1 :: $(v11)"
grep -n "ZZ_planted_stray" "$OUT/o.txt" | head -1 | cut -c1-140
rm -f tools/ZZ_planted_stray.txt
python3 $V > "$OUT/o.txt" 2>&1; rc=$?
res=OK; [ "$rc" = 0 ] || { res=BAD; fail=1; }
echo "$res default run after removing the stray: rc=$rc want=0 :: $(v11)"
echo "== C. source facts"
grep -n 'ORCHESTRATOR_OWNED = ' $V
grep -n 'in ORCHESTRATOR_OWNED' $V
echo "non-membership (startswith/endswith/in-string) uses of ORCHESTRATOR_OWNED:"; grep -nE "ORCHESTRATOR_OWNED.*(startswith|endswith|\.find|re\.)|startswith\(ORCHESTRATOR_OWNED" $V || echo "  none"
echo "callers passing --git-status outside the negative-controls tool:"; grep -rln -e "--git-status" "$SRC/.agent" "$SRC/tools" "$SRC/.github" 2>/dev/null | sed "s#$SRC/##" | grep -v "/eval/" || echo "  none"
cd "$SRC"; rm -rf "$COPY" "$OUT"
echo "RESULT: $([ $fail = 0 ] && echo all-ok || echo failures)"
exit $fail
