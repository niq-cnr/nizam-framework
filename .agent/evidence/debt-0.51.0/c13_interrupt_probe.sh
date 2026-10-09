#!/usr/bin/env bash
# DEBT.md 0.51.0 probe (Planner, 2026-10-09): re-verifies the NDEBT-042 remedy
# and demonstrates the NDEBT-047 defect, entirely inside a private export.
#
# Usage (from the repository root): bash .agent/evidence/debt-0.51.0/c13_interrupt_probe.sh [REV]
#
# The real working tree is never written: REV (default HEAD) is exported with
# `git archive` into a mktemp directory outside the repository, committed there
# so that `git status` and `git checkout` work, and every step runs in that copy
# with TMPDIR pointed at a second private directory (so a leaked C13 backup is
# contained and observable). Both directories are removed on exit.
#
# Steps:
#   1. clean run of tools/fixtures_self_test.sh: exit code, the claim-map
#      demonstration lines and the SELF-TEST summary line (NDEBT-042);
#   2. trap probe: print the EXIT trap that is active inside test_c13
#      (one echo line inserted into the private copy, then reverted);
#   3. interrupt probe: start the self-test in its own process group, wait until
#      tools/skill.json differs from REV (the C13 swap window), send SIGTERM to
#      the group, then report git status, whether tools/skill.json is the
#      dangling-module fixture, the leaked backup, and validate.sh C13/SUMMARY;
#   4. recovery: `git checkout -- tools/skill.json`, then validate.sh again.
#
# Exit 0 only if every expectation holds; 1 otherwise; 2 on setup failure.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
rev=${1:-HEAD}
sha=$(git -C "${repo}" rev-parse --verify "${rev}^{commit}") || exit 2
work=$(mktemp -d) || exit 2
tmp_root=$(mktemp -d) || { rm -rf -- "${work}"; exit 2; }
trap 'rm -rf -- "${work}" "${tmp_root}"' EXIT
git -C "${repo}" archive "${sha}" | tar -x -C "${work}" || exit 2
cd -- "${work}" || exit 2
git init -q && git add -A && git -c user.name=probe -c user.email=probe@invalid commit -qm base || exit 2
export TMPDIR="${tmp_root}"
echo "== exported ${sha} to a private copy (outside the repository)"
bad=0
expect() { if eval "$2"; then echo "PASS ${1}"; else echo "FAIL ${1}"; bad=1; fi; }

echo "== 1. clean run"
out=$(bash tools/fixtures_self_test.sh 2>&1); rc=$?
printf '%s\n' "${out}" | grep -E '^(OK|FAIL) +claim-map|^SELF-TEST'
echo "rc=${rc}"
expect "clean self-test exits 0" '[ "${rc}" -eq 0 ]'
expect "four claim-map demonstrations print OK" '[ "$(printf "%s\n" "${out}" | grep -c "^OK   claim-map   .* -> FAIL$")" -eq 4 ]'
expect "SELF-TEST OK N/N equals the any-depth file count" \
  '[ "$(printf "%s\n" "${out}" | grep -c "^SELF-TEST OK: $(find tools/fixtures ! -type d | wc -l)/$(find tools/fixtures ! -type d | wc -l) fixtures accounted for, 0 failed$")" -eq 1 ]'

echo "== 2. EXIT trap active inside test_c13"
grep -n '^trap cleanup EXIT$\|^  trap "\${cleanup}" EXIT$\|^if scratch_dirs fll_scratch; then$\|^test_c13() {$\|^test_c13$' tools/fixtures_self_test.sh
sed -i '/^test_c13() {$/a\  echo "PROBE-TRAP: $(trap -p EXIT)"' tools/fixtures_self_test.sh
trap_line=$(bash tools/fixtures_self_test.sh 2>&1 | grep '^PROBE-TRAP:' | sed "s#${tmp_root}#\$TMPDIR#g")
git checkout -q -- tools/fixtures_self_test.sh
echo "${trap_line}"
expect "the active EXIT trap is cleanup_scratch_dirs, not cleanup" \
  '[[ "${trap_line}" == "PROBE-TRAP: trap -- '"'"'cleanup_scratch_dirs "* ]]'

echo "== 3. interrupt during the C13 swap window"
setsid bash tools/fixtures_self_test.sh > "${tmp_root}/interrupted.out" 2>&1 &
pid=$!
git show HEAD:tools/skill.json > "${tmp_root}/skill.head" || exit 2  # the copy's own HEAD (= REV's tree)
swapped=0
for _ in $(seq 1 12000); do
  if ! cmp -s tools/skill.json "${tmp_root}/skill.head"; then swapped=1; break; fi
  kill -0 "${pid}" 2>/dev/null || break
  sleep 0.05
done
if [ "${swapped}" -eq 1 ]; then kill -TERM -- "-${pid}" 2>/dev/null; echo "sent SIGTERM to process group ${pid} during the swap"; fi
wait "${pid}"; echo "self-test rc=$?"
sleep 3
echo "-- last lines of the interrupted run"; tail -2 "${tmp_root}/interrupted.out"
echo "-- git status --short"; git status --short
expect "the swap window was observed" '[ "${swapped}" -eq 1 ]'
expect "tools/skill.json is left as the dangling-module fixture" \
  'cmp -s tools/skill.json tools/fixtures/skill_index_neg_dangling_module.json'
leaked=$(find "${tmp_root}" -maxdepth 1 -name "tmp.*" -type f | wc -l)
echo "leaked backup files under TMPDIR: ${leaked}"
expect "the C13 backup (SKILL_BAK) is leaked" '[ "${leaked}" -ge 1 ]'
v=$(bash tools/validate.sh 2>&1); vrc=$?
printf '%s\n' "${v}" | grep -E '^\[C13\]|^SUMMARY'; echo "validate rc=${vrc}"
expect "validate.sh C13 fails while swapped" '[ "${vrc}" -ne 0 ] && printf "%s\n" "${v}" | grep -q "^\[C13\] FAIL"'

echo "== 4. recovery: git checkout -- tools/skill.json"
git checkout -q -- tools/skill.json
git status --short
v=$(bash tools/validate.sh 2>&1); vrc=$?
printf '%s\n' "${v}" | grep -E '^\[C13\]|^SUMMARY'; echo "validate rc=${vrc}"
expect "validate.sh passes after recovery" '[ "${vrc}" -eq 0 ]'

echo "RESULT: $([ "${bad}" -eq 0 ] && echo 'all expectations hold' || echo 'an expectation FAILED')"
exit "${bad}"
