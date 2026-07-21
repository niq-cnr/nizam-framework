#!/usr/bin/env bash
# tools/fixtures_self_test.sh -- Fixture dormancy self-test (NDEBT-009,
# phase-006 feature 052).
#
# Closes the dormancy gap flagged by NDEBT-009: the negative fixtures under
# tools/fixtures/ are substantive and discriminating, but no CI job ran them,
# so a validator check that regressed to a vacuous pass would not be caught.
# This harness runs EVERY shipped fixture through its TARGETED surface and
# asserts the discriminating verdict, then proves -- via a COMPLETENESS GUARD
# -- that every file under tools/fixtures/ is accounted for, so a newly-added
# fixture cannot silently go dormant.
#
# NON-VACUOUS BY CONSTRUCTION: it asserts the SPECIFIC verdict of the targeted
# check ([C2]/[C9]/[C10]/... or a verify_lib primitive return), never a bare
# non-zero exit. Most .md fixtures already exit non-zero from incidental
# C1/C2 frontmatter failures unrelated to what they test (e.g.
# stale_payload_pass.md exits 1 but its targeted check, C10, correctly
# PASSES), so an exit-code-only self-test would pass vacuously on the wrong
# check -- exactly the failure mode NDEBT-009 exists to prevent.
#
# Three surfaces exercise the fixtures:
#   (1) validate.sh --target   -- check-level fixtures (.md/.html/.json); the
#                                 ecosystem families route via NDEBT-015.
#   (2) verify_lib primitives  -- primitive-level fixtures (source + invoke),
#                                 including two git-scratch primitives.
#   (3) C13 skill-index        -- via tools/skill.json substitution.
#
# Framework-internal (reads tools/fixtures/, which is a development/QA
# concern); run in CI as its own job alongside validate + e2e_bootstrap.
# Exits 0 only if every assertion passed AND every fixture is accounted for.

set -uo pipefail

REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || {
  echo "fixtures_self_test: cannot resolve repo root" >&2
  exit 2
}
cd -- "${REPO}" || exit 2

[ -f tools/verify_lib.sh ] || { echo "fixtures_self_test: tools/verify_lib.sh not found" >&2; exit 2; }
# shellcheck source=tools/verify_lib.sh
source tools/verify_lib.sh

fail=0
COVERED=()
SKILL_BAK=""

# Backstop: if a C13 substitution is interrupted, restore the real skill.json.
cleanup() {
  if [ -n "${SKILL_BAK}" ] && [ -f "${SKILL_BAK}" ]; then
    cp -- "${SKILL_BAK}" tools/skill.json
    rm -f -- "${SKILL_BAK}"
  fi
}
trap cleanup EXIT

note_covered() { COVERED+=("$1"); }

# assert_target <fixture-basename> <check-tag> <PASS|FAIL>
# Runs `validate.sh --target tools/fixtures/<fixture>` and asserts the named
# check emitted the expected verdict line. The fixture is marked covered.
assert_target() {
  local fx="$1" tag="$2" pol="$3"
  note_covered "${fx}"
  local out
  out=$(bash tools/validate.sh --target "tools/fixtures/${fx}" 2>&1)
  if printf '%s\n' "${out}" | grep -Eq "^\[${tag}\] ${pol}( |\$)"; then
    echo "OK   target      ${fx} -> [${tag}] ${pol}"
  else
    echo "FAIL target      ${fx} -> expected [${tag}] ${pol}, got:"
    printf '%s\n' "${out}" | grep -E '^\[C[0-9]+\] ' | sed 's/^/       /'
    fail=1
  fi
}

# assert_rc <label> <expected-rc> <command...>
# Runs the command, captures its return, asserts it equals <expected-rc>.
assert_rc() {
  local label="$1" want="$2"; shift 2
  "$@" >/dev/null 2>&1
  local got=$?
  if [ "${got}" -eq "${want}" ]; then
    echo "OK   ${label} (rc=${got})"
  else
    echo "FAIL ${label}: expected rc=${want}, got rc=${got}"
    fail=1
  fi
}

# ---------------------------------------------------------------------------
# (1) validate.sh --target check-level fixtures
# ---------------------------------------------------------------------------
echo "== check-level fixtures (validate.sh --target) =="

# Negatives: the targeted check MUST FAIL.
assert_target bad_authoritative_source.md                          C2  FAIL
assert_target bad_discovery_order.md                               C10 FAIL
assert_target untagged_fence.md                                    C3  FAIL
assert_target unresolved_path.md                                   C9  FAIL
assert_target stale_payload.md                                     C10 FAIL
assert_target stale_payload_cosentence.md                          C10 FAIL
assert_target stale_payload_longwrap.md                            C10 FAIL
assert_target stale_payload_semicolon.md                           C10 FAIL
assert_target stale_payload_html.html                              C10 FAIL
assert_target version_drift.html                                   C10 FAIL
assert_target broken_index.json                                    C4  FAIL
assert_target invalid_contract.json                                C11 FAIL
assert_target invalid_qa_verdict.json                              C11 FAIL
assert_target invalid_run_state.json                               C11 FAIL
assert_target ecosystem_baseline_neg_missing_revision.json         C12 FAIL
assert_target ecosystem_baseline_neg_mixed_timestamps.json         C12 FAIL
assert_target ecosystem_baseline_neg_inconsistent_revisions.json   C12 FAIL
assert_target engineering_finding_neg_closure_evidence_incomplete.json C12 FAIL
assert_target engineering_finding_neg_missing_owner.json           C12 FAIL
assert_target engineering_finding_neg_resolved_without_closure_evidence.json C12 FAIL
assert_target preflight_verdict_invalid_approval_incomplete.json   C12 FAIL
assert_target preflight_verdict_invalid_exceptions.json            C12 FAIL
assert_target preflight_verdict_invalid_verdict.json               C12 FAIL
assert_target audit_delta_neg_resolved_without_closure_evidence.json C12 FAIL
assert_target audit_delta_neg_missing_transition_class.json        C12 FAIL
assert_target audit_delta_neg_duplicate_id_across_buckets.json     C12 FAIL

# Positives: the targeted check MUST PASS (proves the negative's signal is
# discriminating, not a check that fails on everything).
assert_target exempt_paths.md                                      C9  PASS
assert_target ecosystem_baseline_valid.json                        C12 PASS
assert_target engineering_finding_valid.json                       C12 PASS
assert_target engineering_finding_valid_resolved.json              C12 PASS
assert_target preflight_verdict_pass.json                          C12 PASS
assert_target preflight_verdict_pass_with_exceptions.json          C12 PASS
assert_target preflight_verdict_fail.json                          C12 PASS
assert_target audit_delta_valid.json                               C12 PASS

# ---------------------------------------------------------------------------
# (2) verify_lib primitive fixtures
# ---------------------------------------------------------------------------
echo "== primitive fixtures (verify_lib) =="

# vlib_no_stale_payload: pass fixture returns 0, fail fixture returns 1.
note_covered stale_payload_pass.md
note_covered stale_payload_fail.md
assert_rc "primitive   vlib_no_stale_payload pass" 0 vlib_no_stale_payload tools/fixtures/stale_payload_pass.md
assert_rc "primitive   vlib_no_stale_payload fail" 1 vlib_no_stale_payload tools/fixtures/stale_payload_fail.md

# vlib_section_grep: marker in the target section returns 0; marker only in a
# non-target section returns 1 (a vacuous whole-file grep would false-pass).
note_covered section_grep_pass.md
note_covered section_grep_fail.md
assert_rc "primitive   vlib_section_grep pass" 0 vlib_section_grep tools/fixtures/section_grep_pass.md '^## Target Section' 'SECTION_GREP_MARKER'
assert_rc "primitive   vlib_section_grep fail" 1 vlib_section_grep tools/fixtures/section_grep_fail.md '^## Target Section' 'SECTION_GREP_MARKER'

# vlib_word_present (F-053): the whole word "new" is a delimited token in the
# pass fixture; in the fail fixture it appears only inside "renewed".
note_covered word_present_pass.md
note_covered word_present_fail.md
assert_rc "primitive   vlib_word_present pass" 0 vlib_word_present tools/fixtures/word_present_pass.md new
assert_rc "primitive   vlib_word_present fail" 1 vlib_word_present tools/fixtures/word_present_fail.md new

# vlib_bare_ref_resolves (F-055, NDEBT-005b): bare '05_gamma.md' in the fail
# fixture is enumerated by no key_document in the canonical index enum_index.json;
# every bare ref in the pass fixture resolves. Sourced from the canonical index,
# not a duplicated list.
note_covered enum_index.json
note_covered bare_ref_pass.md
note_covered bare_ref_fail.md
assert_rc "primitive   vlib_bare_ref_resolves pass" 0 vlib_bare_ref_resolves tools/fixtures/bare_ref_pass.md tools/fixtures/enum_index.json
assert_rc "primitive   vlib_bare_ref_resolves fail" 1 vlib_bare_ref_resolves tools/fixtures/bare_ref_fail.md tools/fixtures/enum_index.json

# vlib_enumeration_complete (F-055, NDEBT-005a): the guard enumerates a
# DIRECTORY, so its seeded omission is built in a scratch dir (mktemp + EXIT
# trap -- Section 11 probe isolation), the same git-scratch pattern the two
# primitives below use. A dir whose files are all enumerated by enum_index.json
# passes; adding one on-disk file the index omits must fail.
_enumeration_complete_scratch() (
  local d; d=$(mktemp -d) || return 1
  trap 'rm -rf "${d}"' EXIT
  mkdir -p "${d}/m1"
  : > "${d}/m1/00_alpha.md"
  : > "${d}/m1/01_beta.md"
  vlib_enumeration_complete tools/fixtures/enum_index.json m1 "${d}/m1" '*.md' >/dev/null 2>&1 || return 1
  : > "${d}/m1/02_gamma.md"   # seeded omission: on disk, absent from the index
  vlib_enumeration_complete tools/fixtures/enum_index.json m1 "${d}/m1" '*.md' >/dev/null 2>&1 && return 1
  return 0
)
if _enumeration_complete_scratch; then
  echo "OK   primitive   vlib_enumeration_complete (complete pass / seeded-omission fail)"
else
  echo "FAIL primitive   vlib_enumeration_complete: a scratch assertion did not hold"
  fail=1
fi

# Real-tree recurrence guards (the actual NDEBT-005 mechanization, not just
# fixture discrimination): the canonical index NIZAM.json must enumerate every
# on-disk governed doc, and no methodology/ or standard/ doc may carry an
# unresolved bare NN_name.md reference. ecosystem/, registers, and NIPs are
# out of the bare-ref sweep by design -- they legitimately carry forward-refs
# to planned-but-unshipped stages and quoted historical defects, the exact
# false-positive risk NDEBT-005 was deferred over; methodology/ + standard/ are
# the stable, fully-shipped modules where NDEBT-003b actually occurred.
_f055_real_tree() {
  local m f bad=0
  for m in standard methodology registry ecosystem; do
    vlib_enumeration_complete NIZAM.json "${m}" "${m}" '*.md' >/dev/null 2>&1 \
      || { echo "FAIL guard       enumeration real-tree: NIZAM.json omits an on-disk ${m}/ doc"; bad=1; }
  done
  [ "${bad}" -eq 0 ] \
    && echo "OK   guard       vlib_enumeration_complete real-tree (NIZAM.json complete vs disk)" \
    || fail=1
  bad=0
  for f in methodology/*.md standard/*.md; do
    vlib_bare_ref_resolves "${f}" NIZAM.json >/dev/null 2>&1 \
      || { echo "FAIL guard       bare-ref real-tree: ${f} carries an unresolved bare reference"; bad=1; }
  done
  [ "${bad}" -eq 0 ] \
    && echo "OK   guard       vlib_bare_ref_resolves real-tree (methodology/ + standard/ clean)" \
    || fail=1
}
_f055_real_tree

# vlib_workflows_sha_pinned (F-058, C14): a scratch workflow dir with a
# tag-pinned ref fails; a SHA-pinned ref (+ an exempt local ./ action) passes;
# and this repo's real .github/workflows passes (all refs pinned). Scratch via
# mktemp + trap (Section 11 probe isolation), like the git-scratch primitives.
_workflow_pins_scratch() (
  local d; d=$(mktemp -d) || return 1
  trap 'rm -rf -- "${d}"' EXIT
  mkdir -p "${d}/wf"
  printf 'jobs:\n  x:\n    steps:\n      - uses: actions/checkout@v4\n' > "${d}/wf/bad.yml"
  vlib_workflows_sha_pinned "${d}/wf" >/dev/null 2>&1 && return 1   # tag ref must fail
  printf 'jobs:\n  x:\n    steps:\n      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n      - uses: ./.github/actions/local\n' > "${d}/wf/bad.yml"
  vlib_workflows_sha_pinned "${d}/wf" >/dev/null 2>&1 || return 1   # sha + local must pass
  return 0
)
if _workflow_pins_scratch && vlib_workflows_sha_pinned .github/workflows >/dev/null 2>&1; then
  echo "OK   primitive   vlib_workflows_sha_pinned (tag fail / sha+local pass / real-tree pass)"
else
  echo "FAIL primitive   vlib_workflows_sha_pinned: a scratch or real-tree assertion did not hold"
  fail=1
fi

# vlib_profiles_cover_roles (F-058, C15): the real capability_profiles.md + AGF.md
# pair passes; a scratch profiles doc omitting a profile identifier fails.
_profiles_roles_scratch() (
  local d; d=$(mktemp -d) || return 1
  trap 'rm -rf -- "${d}"' EXIT
  printf 'orchestrator-primary planner-creative generator-deterministic validator-structural\n' > "${d}/prof.md"
  cp -- standard/AGF.md "${d}/agf.md"
  vlib_profiles_cover_roles "${d}/prof.md" "${d}/agf.md" >/dev/null 2>&1 && return 1   # missing profile must fail
  return 0
)
if vlib_profiles_cover_roles standard/capability_profiles.md standard/AGF.md >/dev/null 2>&1 && _profiles_roles_scratch; then
  echo "OK   primitive   vlib_profiles_cover_roles (real pair pass / missing-profile fail)"
else
  echo "FAIL primitive   vlib_profiles_cover_roles: a real-pair or scratch assertion did not hold"
  fail=1
fi

# vlib_path_resolves: every token line in the pass fixture resolves/exempts
# (rc 0); the fail fixture's token does not (rc 1). Tokens resolve relative to
# the repo root (this script's CWD).
test_path_resolves() {
  note_covered path_resolves_pass.txt
  note_covered path_resolves_fail.txt
  local line ok=1
  while IFS= read -r line || [ -n "${line}" ]; do
    [ -z "${line}" ] && continue
    vlib_path_resolves "${line}" >/dev/null 2>&1 || ok=0
  done < tools/fixtures/path_resolves_pass.txt
  if [ "${ok}" -eq 1 ]; then echo "OK   primitive   vlib_path_resolves pass (all tokens resolve/exempt)"
  else echo "FAIL primitive   vlib_path_resolves pass: a token failed to resolve"; fail=1; fi
  ok=1
  while IFS= read -r line || [ -n "${line}" ]; do
    [ -z "${line}" ] && continue
    vlib_path_resolves "${line}" >/dev/null 2>&1 && ok=0
  done < tools/fixtures/path_resolves_fail.txt
  if [ "${ok}" -eq 1 ]; then echo "OK   primitive   vlib_path_resolves fail (token does not resolve)"
  else echo "FAIL primitive   vlib_path_resolves fail: a token unexpectedly resolved"; fail=1; fi
}
test_path_resolves

# vlib_version_increased (git-scratch): old.md is the HEAD baseline (0.1.0);
# new_pass (0.2.0) is a strict increase (rc 0); new_fail (0.1.0, equal) and
# new_fail_decrease (0.0.9, lower) are not (rc 1).
test_version_increased() {
  note_covered version_increased_old.md
  note_covered version_increased_new_pass.md
  note_covered version_increased_new_fail.md
  note_covered version_increased_new_fail_decrease.md
  if _version_increased_scratch; then
    echo "OK   primitive   vlib_version_increased (pass / equal-fail / decrease-fail)"
  else
    echo "FAIL primitive   vlib_version_increased: a scratch assertion did not hold"
    fail=1
  fi
}
_version_increased_scratch() (
  local d; d=$(mktemp -d) || return 1
  trap 'rm -rf "${d}"' EXIT
  cd -- "${d}" || return 1
  git init -q . || return 1
  git config user.email self-test@nizam.local
  git config user.name fixtures-self-test
  cp -- "${REPO}/tools/fixtures/version_increased_old.md" f.md
  git add f.md && git commit -qm baseline || return 1
  cp -- "${REPO}/tools/fixtures/version_increased_new_pass.md" f.md
  vlib_version_increased f.md >/dev/null 2>&1 || return 1
  cp -- "${REPO}/tools/fixtures/version_increased_new_fail.md" f.md
  vlib_version_increased f.md >/dev/null 2>&1 && return 1
  cp -- "${REPO}/tools/fixtures/version_increased_new_fail_decrease.md" f.md
  vlib_version_increased f.md >/dev/null 2>&1 && return 1
  return 0
)
test_version_increased

# vlib_scope_guard (git-scratch): a change to an allow-listed path passes; an
# out-of-scope change fails. The allow-list is the fixture's contents.
test_scope_guard() {
  note_covered scope_guard_allowlist.txt
  if _scope_guard_scratch; then
    echo "OK   primitive   vlib_scope_guard (allowed pass / out-of-scope fail)"
  else
    echo "FAIL primitive   vlib_scope_guard: a scratch assertion did not hold"
    fail=1
  fi
}
_scope_guard_scratch() (
  local d; d=$(mktemp -d) || return 1
  trap 'rm -rf "${d}"' EXIT
  local allow=()
  local a
  while IFS= read -r a || [ -n "${a}" ]; do
    [ -z "${a}" ] && continue
    allow+=("${a}")
  done < "${REPO}/tools/fixtures/scope_guard_allowlist.txt"
  cd -- "${d}" || return 1
  git init -q . || return 1
  git config user.email self-test@nizam.local
  git config user.name fixtures-self-test
  mkdir -p tools/fixtures
  printf 'seed\n' > tools/verify_lib.sh
  git add -A && git commit -qm baseline || return 1
  # Allowed change only (tools/verify_lib.sh is in the allow-list): passes.
  printf 'change\n' >> tools/verify_lib.sh
  vlib_scope_guard "${allow[@]}" >/dev/null 2>&1 || return 1
  # Add an out-of-scope path (README.md is not allow-listed): fails.
  printf 'oops\n' > README.md
  vlib_scope_guard "${allow[@]}" >/dev/null 2>&1 && return 1
  return 0
)
test_scope_guard

# ---------------------------------------------------------------------------
# (3) C13 skill-index negative fixture (substitution)
# ---------------------------------------------------------------------------
echo "== C13 skill-index negative fixture (substitution) =="
test_c13() {
  note_covered skill_index_neg_dangling_module.json
  SKILL_BAK=$(mktemp)
  cp -- tools/skill.json "${SKILL_BAK}"
  cp -- tools/fixtures/skill_index_neg_dangling_module.json tools/skill.json
  local out; out=$(bash tools/validate.sh 2>&1)
  cp -- "${SKILL_BAK}" tools/skill.json
  rm -f -- "${SKILL_BAK}"; SKILL_BAK=""
  if printf '%s\n' "${out}" | grep -Eq "^\[C13\] FAIL"; then
    echo "OK   c13-substitute skill_index_neg_dangling_module.json -> [C13] FAIL"
  else
    echo "FAIL c13-substitute: substituting the dangling-module fixture did not yield [C13] FAIL"
    fail=1
  fi
}
test_c13

# ---------------------------------------------------------------------------
# TEMPLATE-SCHEMA CONFORMANCE (F-054, NDEBT-011): the shipped
# templates/work-packet.template.json must validate end-to-end against
# schema/work-packet.schema.json. The schema's own `description` claims it
# validates the template; F-054 made that claim true by omitting the three
# optional enum/integer dispatch fields (tier/blast_radius/merge_order), which
# cannot hold a {{...}} placeholder, from the starter template, and this guard
# keeps it true so the template can never silently drift back to non-conformance
# -- the mechanical assertion of the template's contract NDEBT-011 required.
# ---------------------------------------------------------------------------
echo "== template-schema conformance (F-054) =="
if python3 - <<'PY'
import json
import sys

import jsonschema

template = json.load(open("templates/work-packet.template.json"))
schema = json.load(open("schema/work-packet.schema.json"))
try:
    jsonschema.validate(instance=template, schema=schema)
except jsonschema.ValidationError as exc:
    print(f"work-packet.template.json does not validate: {exc.message}")
    sys.exit(1)
sys.exit(0)
PY
then
  echo "OK   guard       work-packet.template.json validates end-to-end against work-packet.schema.json"
else
  echo "FAIL guard       work-packet.template.json does NOT validate against schema/work-packet.schema.json"
  fail=1
fi

# ---------------------------------------------------------------------------
# (4) ecosystem_preflight.py CLI behavior probes (F-056, NDEBT-021.5/-018.1)
# ---------------------------------------------------------------------------
# tools/ecosystem_preflight.py is NOT covered by validate.sh (only its OUTPUT
# schemas are, via C12), so these standing git-scratch probes are its permanent
# regression guard. They assert the load-bearing clean-state polarity: an
# untracked-not-tolerated file FAILs (exit 1); the exact --tolerate-untracked
# and the additive --tolerate-untracked-prefix each downgrade it to a pending
# PASS_WITH_EXCEPTIONS (exit 2). Probe isolation per methodology/02 Sec 11: a
# mktemp -d scratch repo, cleaned via a trap with rm -rf -- on the scratch dirs
# only (never a real path). These are behavior probes, not fixtures, so they add
# nothing to the completeness manifest.
echo "== preflight CLI behavior probes (F-056) =="
_preflight_cli_probes() (
  local sb out rc
  sb=$(mktemp -d) || return 1
  out=$(mktemp -d) || { rm -rf -- "${sb}"; return 1; }
  trap 'rm -rf -- "${sb}" "${out}"' EXIT
  git -C "${sb}" init -q
  git -C "${sb}" config user.email t@example.invalid
  git -C "${sb}" config user.name tester
  mkdir -p "${sb}/schema"
  printf '{}' > "${sb}/schema/preflight_verdict.schema.json"
  printf '{}' > "${sb}/schema/ecosystem_baseline.schema.json"
  git -C "${sb}" add -A
  git -C "${sb}" commit -qm init
  # (a0) a clean framework-root-layout tree (schema/ at the repo root, no .nizam/)
  #      -> PASS (exit 0): governance-root discovery falls back to the repo-root and
  #      the required references resolve there, unchanged by feature 065.
  python3 tools/ecosystem_preflight.py --execution-id p --output-dir "${out}" --repo-root "${sb}" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 0 ] || { echo "  clean framework-root: expected exit 0, got ${rc}"; return 1; }
  printf x > "${sb}/dirty.txt"
  # (a) an untracked-not-tolerated file -> FAIL (exit 1) [the NDEBT-021.5 probe]
  python3 tools/ecosystem_preflight.py --execution-id p --output-dir "${out}" --repo-root "${sb}" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 1 ] || { echo "  untracked-not-tolerated: expected exit 1, got ${rc}"; return 1; }
  # (b) exact --tolerate-untracked downgrades it to pending PASS_WITH_EXCEPTIONS (exit 2)
  python3 tools/ecosystem_preflight.py --execution-id p --output-dir "${out}" --repo-root "${sb}" --tolerate-untracked dirty.txt >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 2 ] || { echo "  exact tolerate: expected exit 2, got ${rc}"; return 1; }
  # (c) additive --tolerate-untracked-prefix also downgrades it (exit 2) [NDEBT-018.1]
  python3 tools/ecosystem_preflight.py --execution-id p --output-dir "${out}" --repo-root "${sb}" --tolerate-untracked-prefix dirty >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 2 ] || { echo "  prefix tolerate: expected exit 2, got ${rc}"; return 1; }
  return 0
)
# feature 065 (ADR-004 decision 1; NDEBT-027): a bootstrapped-consumer layout has
# the governance payload under .nizam/, NOT at the repo root. The tool must (i)
# resolve the required references against that governance-root and (ii) treat the
# injected .nizam/ as an expected 'injected_governance_payload' exception, so a
# clean Preflight against a real consumer is a PASS_WITH_EXCEPTIONS, never the
# pre-065 hard FAIL(1) on missing references + the untracked .nizam/.
_preflight_governance_root_probes() (
  local sb out rc
  sb=$(mktemp -d) || return 1
  out=$(mktemp -d) || { rm -rf -- "${sb}"; return 1; }
  trap 'rm -rf -- "${sb}" "${out}"' EXIT
  git -C "${sb}" init -q
  git -C "${sb}" config user.email t@example.invalid
  git -C "${sb}" config user.name tester
  mkdir -p "${sb}/src" "${sb}/.nizam/schema"
  printf 'x' > "${sb}/src/app.txt"
  printf '{}' > "${sb}/.nizam/schema/preflight_verdict.schema.json"
  printf '{}' > "${sb}/.nizam/schema/ecosystem_baseline.schema.json"
  printf '{}' > "${sb}/.nizam/NIZAM.json"
  git -C "${sb}" add src
  git -C "${sb}" commit -qm init   # .nizam/ left untracked (the injected payload)
  # (d) discovery: refs resolve under the discovered .nizam/ and the injected
  #     payload is an expected exception -> PASS_WITH_EXCEPTIONS pending (2), not FAIL(1).
  python3 tools/ecosystem_preflight.py --execution-id g --output-dir "${out}" --repo-root "${sb}" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 2 ] || { echo "  gov-root discovery: expected exit 2 (not FAIL), got ${rc}"; return 1; }
  python3 - "${out}/preflight.pending.json" <<'PY' || { echo "  gov-root exception kind wrong"; return 1; }
import json, sys
kinds = [e.get("kind") for e in json.load(open(sys.argv[1])).get("exceptions", [])]
raise SystemExit(0 if kinds == ["injected_governance_payload"] else 1)
PY
  # (e) an explicit --governance-root at the payload behaves the same.
  python3 tools/ecosystem_preflight.py --execution-id g --output-dir "${out}" --repo-root "${sb}" --governance-root "${sb}/.nizam" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 2 ] || { echo "  explicit gov-root: expected exit 2, got ${rc}"; return 1; }
  return 0
)
if _preflight_governance_root_probes; then
  echo "OK   preflight   gov-root: injected .nizam/ discovered -> refs resolve + expected exception -> pending(2), not FAIL"
else
  echo "FAIL preflight   a governance-root behavior probe did not hold"
  fail=1
fi

if _preflight_cli_probes; then
  echo "OK   preflight   clean framework-root -> PASS(0); untracked-not-tolerated -> FAIL(1); exact + prefix tolerate -> pending(2)"
else
  echo "FAIL preflight   a CLI behavior probe did not hold"
  fail=1
fi

# ---------------------------------------------------------------------------
# (5) ecosystem_audit.py CLI behavior probes (Tier-1 audit tool)
# ---------------------------------------------------------------------------
# tools/ecosystem_audit.py is NOT covered by validate.sh (only its OUTPUT
# schema is, via C12's engineering_finding family), so these standing probes
# are its permanent regression guard. They assert the load-bearing polarity:
# a valid audit is ASSEMBLED (exit 0, findings.json + report.md written); a
# resolved finding with no closure evidence is INVALID (exit 1, no artifact);
# a FAIL preflight verdict is REFUSED at the Sec 2 entry gate (exit 2). Inputs
# are built inline in a mktemp -d scratch dir, cleaned via an EXIT-trap rm -rf
# on the scratch dir only. Behavior probes, not fixtures -- they add nothing to
# the completeness manifest.
echo "== ecosystem_audit CLI behavior probes =="
_audit_cli_probes() (
  local d rc
  d=$(mktemp -d) || return 1
  trap 'rm -rf -- "${d}"' EXIT
  printf '{"verdict":"PASS","execution_id":"e1","generated_at":"t"}' > "${d}/preflight.json"
  printf '{"execution_id":"e1"}' > "${d}/baseline.json"
  printf '[{"id":"F1","severity":"low","confidence":"Confirmed","evidence":[{"path":".agent/evidence/e1/x.txt","revision":"abc123"}],"impact":"i","owner":"o","status":"open","closure_criteria":"c"}]' > "${d}/findings.json"
  # (a) a valid audit -> ASSEMBLED (exit 0), both artifacts written
  python3 tools/ecosystem_audit.py --audit-id a --output-dir "${d}/out" --findings-input "${d}/findings.json" --preflight "${d}/preflight.json" --baseline "${d}/baseline.json" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 0 ] || { echo "  valid audit: expected exit 0, got ${rc}"; return 1; }
  [ -f "${d}/out/findings.json" ] && [ -f "${d}/out/report.md" ] || { echo "  valid audit: expected findings.json + report.md"; return 1; }
  # (b) a resolved finding with no closure evidence -> FINDINGS_INVALID (exit 1)
  printf '[{"id":"F1","severity":"low","confidence":"Confirmed","evidence":[{"path":".agent/evidence/e1/x.txt","revision":"abc123"}],"impact":"i","owner":"o","status":"resolved","closure_criteria":"c"}]' > "${d}/bad.json"
  python3 tools/ecosystem_audit.py --audit-id a --output-dir "${d}/o2" --findings-input "${d}/bad.json" --preflight "${d}/preflight.json" --baseline "${d}/baseline.json" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 1 ] || { echo "  resolved-without-closure: expected exit 1, got ${rc}"; return 1; }
  # (c) a FAIL preflight verdict -> ENTRY_CONDITION_UNMET (exit 2)
  printf '{"verdict":"FAIL","execution_id":"e1","generated_at":"t","blocking_findings":["x"]}' > "${d}/pf-fail.json"
  python3 tools/ecosystem_audit.py --audit-id a --output-dir "${d}/o3" --findings-input "${d}/findings.json" --preflight "${d}/pf-fail.json" --baseline "${d}/baseline.json" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 2 ] || { echo "  fail-preflight: expected exit 2, got ${rc}"; return 1; }
  return 0
)
if _audit_cli_probes; then
  echo "OK   audit       valid -> ASSEMBLED(0); resolved-without-closure -> INVALID(1); FAIL preflight -> refused(2)"
else
  echo "FAIL audit       a CLI behavior probe did not hold"
  fail=1
fi

# ---------------------------------------------------------------------------
# (6) compare_ecosystem_baselines.py + validate_evidence_freshness.py probes
# ---------------------------------------------------------------------------
# The Compare-stage tools' OUTPUT (delta.json) is C12-covered via the
# audit_delta family, but their CLI behavior is not, so these standing probes
# guard it. They assert: a valid comparison emits a delta (exit 0); an
# earlier-open finding gone from the later audit with no closure evidence is
# UNCLASSIFIABLE (exit 1, Sec 4); freshness reports STALE (exit 1) for old
# evidence and FRESH (exit 0) for evidence at the later anchor revision.
echo "== compare + freshness CLI behavior probes =="
_compare_cli_probes() (
  local d rc
  d=$(mktemp -d) || return 1
  trap 'rm -rf -- "${d}"' EXIT
  printf '{"execution_id":"eA","captured_at":"2026-07-01T00:00:00Z","repository_references":[{"revision":"aaa","timestamp":"t","repository":"r"}]}' > "${d}/baseA.json"
  printf '{"execution_id":"eB","captured_at":"2026-07-20T00:00:00Z","repository_references":[{"revision":"bbb","timestamp":"t","repository":"r"}]}' > "${d}/baseB.json"
  printf '[{"id":"F1","severity":"low","confidence":"Confirmed","evidence":[{"path":".agent/evidence/eA/x.txt","revision":"aaa"}],"impact":"i","owner":"o","status":"open","closure_criteria":"c"}]' > "${d}/findA.json"
  printf '[{"id":"F1","severity":"low","confidence":"Confirmed","evidence":[{"path":".agent/evidence/eB/x.txt","revision":"bbb"}],"impact":"i","owner":"o","status":"open","closure_criteria":"c"}]' > "${d}/findB.json"
  printf '[]' > "${d}/findEmpty.json"
  # (a) a valid comparison -> delta emitted (exit 0), delta.json present
  python3 tools/compare_ecosystem_baselines.py --audit-id c --output-dir "${d}/out" --earlier-findings "${d}/findA.json" --later-findings "${d}/findB.json" --earlier-baseline "${d}/baseA.json" --later-baseline "${d}/baseB.json" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 0 ] || { echo "  valid compare: expected exit 0, got ${rc}"; return 1; }
  [ -f "${d}/out/delta.json" ] || { echo "  valid compare: expected delta.json"; return 1; }
  # (b) earlier-open finding gone from later, no closure -> UNCLASSIFIABLE (exit 1)
  python3 tools/compare_ecosystem_baselines.py --audit-id c --output-dir "${d}/o2" --earlier-findings "${d}/findA.json" --later-findings "${d}/findEmpty.json" --earlier-baseline "${d}/baseA.json" --later-baseline "${d}/baseB.json" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 1 ] || { echo "  gone-without-closure: expected exit 1, got ${rc}"; return 1; }
  # (c) freshness: old evidence (rev aaa) vs later anchor bbb -> STALE (exit 1)
  python3 tools/validate_evidence_freshness.py --findings "${d}/findA.json" --anchor-revision bbb --anchor-timestamp "2026-07-20T00:00:00Z" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 1 ] || { echo "  stale evidence: expected exit 1, got ${rc}"; return 1; }
  # (d) freshness: evidence at the anchor revision bbb -> FRESH (exit 0)
  python3 tools/validate_evidence_freshness.py --findings "${d}/findB.json" --anchor-revision bbb --anchor-timestamp "2026-07-20T00:00:00Z" >/dev/null 2>&1
  rc=$?; [ "${rc}" -eq 0 ] || { echo "  fresh evidence: expected exit 0, got ${rc}"; return 1; }
  return 0
)
if _compare_cli_probes; then
  echo "OK   compare     valid -> delta(0); gone-without-closure -> INVALID(1); freshness stale(1)/fresh(0)"
else
  echo "FAIL compare     a CLI behavior probe did not hold"
  fail=1
fi

# ---------------------------------------------------------------------------
# COMPLETENESS GUARD: every file under tools/fixtures/ must be accounted for
# by exactly one row above; an unlisted fixture (a newly-added dormant
# negative) or a manifest row naming an absent fixture is a FAIL.
# ---------------------------------------------------------------------------
echo "== completeness guard =="
ondisk=()
# find (not `ls -1 -- *`): a glob skips dot-prefixed entries and, if a
# subdirectory ever appears under tools/fixtures/, expands to that dir's
# CONTENTS -- either would let a fixture escape the on-disk set and defeat the
# guard's sole purpose (PR #31 review). -maxdepth 1 -type f lists only the
# immediate regular files, dotfiles included; the leading './' is stripped so
# the names match the bare basenames in COVERED. (No -printf: portable to
# non-GNU find.)
while IFS= read -r f; do ondisk+=("${f}"); done \
  < <(cd tools/fixtures && find . -maxdepth 1 -type f | sed 's#^\./##' | LC_ALL=C sort)
covered_sorted=()
while IFS= read -r f; do covered_sorted+=("${f}"); done \
  < <(printf '%s\n' "${COVERED[@]}" | LC_ALL=C sort -u)

unaccounted=$(comm -23 <(printf '%s\n' "${ondisk[@]}") <(printf '%s\n' "${covered_sorted[@]}"))
phantom=$(comm -13 <(printf '%s\n' "${ondisk[@]}") <(printf '%s\n' "${covered_sorted[@]}"))

if [ -n "${unaccounted}" ]; then
  echo "FAIL completeness: fixture(s) on disk not accounted for by any manifest row (dormant):"
  printf '%s\n' "${unaccounted}" | sed 's/^/       /'
  fail=1
fi
if [ -n "${phantom}" ]; then
  echo "FAIL completeness: manifest row(s) name a fixture that is not on disk:"
  printf '%s\n' "${phantom}" | sed 's/^/       /'
  fail=1
fi

total=${#ondisk[@]}
accounted=${#covered_sorted[@]}
echo "---"
if [ "${fail}" -eq 0 ]; then
  echo "SELF-TEST OK: ${accounted}/${total} fixtures accounted for, 0 failed"
  exit 0
fi
echo "SELF-TEST FAILED: ${accounted}/${total} fixtures accounted for (see FAIL lines above)"
exit 1
