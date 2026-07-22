#!/usr/bin/env bash
#
# tools/e2e_bootstrap_test.sh -- Hermetic end-to-end consumer-bootstrap test
# (R2, phase 004-durable-enforcement, F-029).
#
# Exercises the REAL inject-then-verify adoption path bootstrap.sh implements
# (standard/GIP.md, the Governance Inheritance Protocol) end to end, entirely
# offline: it creates an ephemeral ANNOTATED git tag on the working checkout's
# own HEAD, runs bootstrap.sh against a local `file://` clone of THIS
# checkout at that pinned tag into a throwaway scratch `.nizam` target, and
# asserts (a) the injected payload is present, (b) the injected NIZAM.json is
# independently index-valid, (c) the DOCUMENTED bootstrapped-consumer
# discovery path `<target>/tools/skill.json` resolves -- the exact functional
# adoption bug (H4) that shipped in v0.1.0 and survived untested to phase 003
# (tools/interface.md Sec 2, item 1) -- (d) `bootstrap.sh --verify-only`
# passes against the injected target, and (e) the injected
# `tools/validate.sh --payload` is CWD-INDEPENDENT: it produces identical,
# green results whether invoked from inside the payload root or from the
# consumer repository root above it (issue #18 / NDEBT-012, feature 050).
# No network access ever occurs: the
# `file://` clone reads bootstrap.sh's cloned-from URL directly from this
# checkout's own object store.
#
# bootstrap.sh is NOT modified by this harness (spec Sec 4.2): its existing
# --repo-url/--tag/--target/--verify-only surface is already sufficient for a
# fully hermetic local install. tools/verify_lib.sh is NOT modified either --
# this harness composes its `vlib_path_resolves` primitive for the discovery-
# path assertion only (never for directory-presence checks, which would be
# vacuously exempted by that primitive's documented trailing-slash
# directory-only rule).
#
# Dual-mode, mirroring tools/verify_lib.sh's F-023 sourced-library
# discipline: SOURCING this file defines its functions ONLY, with ZERO side
# effects (no git operation, no trap registration, no stdout/stderr, no
# scratch directory) -- a contract/QA fixture-test can `source` this file and
# call its assertion functions directly against a synthetic target, without
# paying the cost (or risk) of a real clone. DIRECT EXECUTION additionally
# runs main() (see the BASH_SOURCE guard at the very end of this file), which
# performs one full ephemeral-tag + file:// clone + inject + assert cycle.
#
# Usage (MUST be invoked with the current working directory at this
# repository's own root, mirroring bootstrap.sh's own CWD-relative
# convention):
#   bash tools/e2e_bootstrap_test.sh                       positive (happy-path) run
#   bash tools/e2e_bootstrap_test.sh --self-test-negative  negative self-test (H4 guard)
#
# Exit status (direct execution):
#   0   The positive run's full inject-then-verify cycle succeeded.
#   1   Any assertion failed, bootstrap.sh failed, an unrecognized argument
#       was given, or (by explicit design -- see main()'s --self-test-negative
#       branch) the negative self-test completed and correctly proved the H4
#       guard is load-bearing.
#
# Dependencies: bash, git, python3. No network. No vendored dependencies.

# ---------------------------------------------------------------------------
# Assertion functions (sourceable library surface; each is a pure function of
# its <target> argument, actually reading the target directory from disk --
# never keyed off any global/ambient state).
# ---------------------------------------------------------------------------

# assert_payload_present <target>
#
# Confirms the bootstrap.sh-injected payload is present under <target>: the
# four REQUIRED_MODULE_DIRS (standard/, templates/, schema/, tools/) as real
# directories, plus non-empty NIZAM.json and provenance.json files. Uses
# plain `test -d`/`test -s` -- deliberately NEVER tools/verify_lib.sh's
# vlib_path_resolves for the directory checks, since vlib_path_resolves
# trivially returns 0 on any token ending in "/" as its documented
# directory-only exemption, which would make a directory-presence check
# vacuous.
#
# Args:
#   target: repo-relative or absolute path to a bootstrap.sh injection root.
#
# Returns:
#   0 if standard/, templates/, schema/, tools/, methodology/, ecosystem/,
#     NIZAM.json, and provenance.json are all present (dirs real, files
#     non-empty).
#   1 otherwise (the first missing item is named).
assert_payload_present() {
  local target="$1"
  local d f

  for d in standard templates schema tools methodology ecosystem; do
    if [ ! -d "${target}/${d}" ]; then
      echo "assert_payload_present: missing injected module directory: ${target}/${d}"
      return 1
    fi
  done

  for f in NIZAM.json provenance.json; do
    if [ ! -s "${target}/${f}" ]; then
      echo "assert_payload_present: missing or empty: ${target}/${f}"
      return 1
    fi
  done

  echo "assert_payload_present: OK -- standard/, templates/, schema/, tools/, methodology/, ecosystem/, NIZAM.json, provenance.json all present under ${target}"
  return 0
}

# assert_nizam_index_valid <target>
#
# An INDEPENDENT proof that <target>/NIZAM.json parses as JSON and every path
# it indexes under an injected module (standard/, templates/, schema/,
# tools/) resolves under <target>. Deliberately does NOT source or delegate
# to bootstrap.sh's own check_nizam_index -- bootstrap.sh cannot safely be
# `source`d (its last line unconditionally calls `main "$@"`, and sourcing it
# would re-run install/verify-only with the sourcing script's own argv and
# mutate the sourcing shell's own `set -euo pipefail` options). This is a
# genuine second, independent proof, not a re-use of the thing under test --
# a latent bug in bootstrap.sh's own self-check would not silently pass this
# harness too.
#
# Args:
#   target: repo-relative or absolute path to a bootstrap.sh injection root.
#
# Returns:
#   0 if NIZAM.json parses and every indexed path under an injected module
#     resolves under <target>.
#   1 otherwise (a parse failure or the unresolved path(s) are named).
assert_nizam_index_valid() {
  local target="$1"

  python3 - "${target}" <<'PY'
import json
import os
import sys

root = sys.argv[1]
nizam_path = os.path.join(root, "NIZAM.json")

try:
    with open(nizam_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, json.JSONDecodeError) as exc:
    print(f"assert_nizam_index_valid: NIZAM.json failed to parse under {root}: {exc}", file=sys.stderr)
    sys.exit(1)

injected_module_paths = {"standard", "templates", "schema", "tools", "methodology", "ecosystem"}


def is_injected(rel_path):
    return isinstance(rel_path, str) and rel_path.split("/", 1)[0] in injected_module_paths


indexed_paths = set()
for module in data.get("modules", []):
    if module.get("path") not in injected_module_paths:
        continue
    for doc in module.get("key_documents", []):
        indexed_paths.add(doc)
for schema_path in data.get("schemas", []):
    if is_injected(schema_path):
        indexed_paths.add(schema_path)
for template_path in data.get("templates", []):
    if is_injected(template_path):
        indexed_paths.add(template_path)
self_reference_path = data.get("self_reference", {}).get("path")
if self_reference_path and is_injected(self_reference_path):
    indexed_paths.add(self_reference_path)

missing = sorted(
    rel for rel in indexed_paths
    if not os.path.isfile(os.path.join(root, rel))
)

if missing:
    print(
        "assert_nizam_index_valid: indexed path(s) failed to resolve under "
        + root + ": " + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)

print(
    f"assert_nizam_index_valid: OK -- NIZAM.json parses; "
    f"{len(indexed_paths)} indexed path(s) resolve under {root}."
)
PY
}

# assert_discovery_path <target>
#
# The H4 regression guard: confirms the DOCUMENTED bootstrapped-consumer
# discovery path <target>/tools/skill.json resolves (tools/interface.md
# Sec 2, item 1: "Bootstrapped-consumer discovery" names .nizam/tools/
# skill.json as the first hop). Composes tools/verify_lib.sh's
# vlib_path_resolves directly against a concrete file path with no trailing
# "/", so vlib_path_resolves' directory-only exemption never applies here and
# the call genuinely tests existence. Lazily sources tools/verify_lib.sh if
# it has not already been sourced by the caller, so this function is safe to
# call standalone (e.g. from a fixture test that only sourced this file).
#
# Args:
#   target: repo-relative or absolute path to a bootstrap.sh injection root.
#
# Returns:
#   0 if <target>/tools/skill.json resolves on disk.
#   1 otherwise (the missing path is named).
assert_discovery_path() {
  local target="$1"

  if ! declare -F vlib_path_resolves >/dev/null 2>&1; then
    # shellcheck source=tools/verify_lib.sh
    source "$(dirname -- "${BASH_SOURCE[0]}")/verify_lib.sh"
  fi

  if ! vlib_path_resolves "${target}/tools/skill.json"; then
    echo "assert_discovery_path: H4 regression -- documented discovery path does not resolve: ${target}/tools/skill.json"
    return 1
  fi

  echo "assert_discovery_path: OK -- ${target}/tools/skill.json resolves (H4 regression guard satisfied)"
  return 0
}

# run_bootstrap_verify_only <tag> <target>
#
# Proves bootstrap.sh's OWN --verify-only self-check mechanism also
# functions end-to-end against the real injected target -- a second,
# complementary proof to assert_nizam_index_valid (not a substitute for it),
# since assert_nizam_index_valid protects against a latent bug in
# bootstrap.sh's own verifier that a self-check could not catch on its own.
# MUST be invoked with CWD at this repository's root, where bootstrap.sh
# lives (mirrors bootstrap.sh's own CWD-relative convention).
#
# Args:
#   tag: the pinned tag bootstrap.sh's provenance.json should record.
#   target: the already-injected directory to verify.
#
# Returns:
#   0 if `bootstrap.sh --verify-only --tag <tag> --target <target>` exits 0.
#   1 otherwise.
run_bootstrap_verify_only() {
  local tag="$1"
  local target="$2"

  if ! bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}"; then
    echo "run_bootstrap_verify_only: bootstrap.sh --verify-only FAILED against ${target} (tag ${tag})"
    return 1
  fi

  return 0
}

# assert_provenance_sha_pin <tag> <target>
# --------------------------------------------------------------------------
# Feature 067 (NDEBT-033): install records the tag's resolved commit SHA in
# provenance.json, and --verify-only with --expected-sha asserts it -- so a moved
# tag replaying a different commit is rejected even when the tag name matches.
# Proves: (a) a non-empty resolved_sha was recorded; (a2) the recorded SHA equals
# the tag's AUTHORITATIVE commit (`git rev-parse <tag>^{commit}`), so the check is
# not self-referential -- it confirms bootstrap resolved and recorded the right
# commit, not merely some SHA the verify step then echoes back; (b) --verify-only
# with the correct --expected-sha PASSES; (c) with a wrong --expected-sha it FAILS.
# The harness tags HEAD in this repo, so the tag's commit is authoritative here.
#
# Returns 0 if all four hold; non-zero otherwise.
assert_provenance_sha_pin() {
  local tag="$1" target="$2" recorded_sha true_sha rc
  recorded_sha="$(python3 -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle).get("resolved_sha", ""))
' "${target}/provenance.json")" || { echo "assert_provenance_sha_pin: FAIL -- provenance.json unreadable under ${target}"; return 1; }
  if [ -z "${recorded_sha}" ]; then
    echo "assert_provenance_sha_pin: FAIL -- bootstrap recorded no resolved_sha in provenance.json (feature 067 regression)"
    return 1
  fi
  # (a2) the recorded SHA must equal the tag's true commit -- an independent,
  # non-self-referential anchor (bootstrap resolved it inside its own clone; this
  # resolves it here from the tag directly).
  if ! true_sha="$(git rev-parse "${tag}^{commit}" 2>/dev/null)"; then
    echo "assert_provenance_sha_pin: FAIL -- cannot resolve tag '${tag}' to a commit for the cross-check"
    return 1
  fi
  if [ "${recorded_sha}" != "${true_sha}" ]; then
    echo "assert_provenance_sha_pin: FAIL -- recorded resolved_sha (${recorded_sha}) != the tag's authoritative commit (${true_sha})"
    return 1
  fi
  # (b) correct expected SHA -> PASS (exit 0)
  if ! bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only rejected the correct recorded SHA (${recorded_sha})"
    return 1
  fi
  # (c) wrong expected SHA -> drift FAIL (non-zero)
  if bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" \
      --expected-sha "0000000000000000000000000000000000000000" >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted a WRONG expected SHA (moved-tag drift not detected)"
    return 1
  fi
  echo "assert_provenance_sha_pin: OK -- resolved_sha recorded (${recorded_sha}) == tag's true commit; --expected-sha PASSES on match, FAILS on mismatch (moved-tag drift detected)."
  return 0
}

# assert_payload_validate_cwd_independent <target>
#
# Feature 050 (NDEBT-012 / issue #18): proves the injected validator's
# `--payload` mode is CWD-INDEPENDENT -- it produces identical, green results
# whether invoked from inside the payload root or from the consumer
# repository root above it. This closes the regression class from the first
# real external-consumer bug report (issue #18: from a consumer repo root,
# `bash .nizam/tools/validate.sh --payload` used to fail because CWD-relative
# resolution could not find the payload's own files).
#
# Runs BOTH documented invocation forms against the just-injected payload and
# asserts (a) both exit 0 and (b) their `[C*]` per-check verdict lines are
# byte-identical. Each `bash tools/validate.sh --payload` exit status is
# captured via an `if` so this function observes a real non-zero rc without
# main()'s `set -e` aborting the harness before the diagnostic is printed.
#
# Args:
#   target: repo-relative or absolute path to a bootstrap.sh injection root
#           (its parent directory is treated as the consumer repository root).
#
# Returns:
#   0 if both invocation forms exit 0 with identical [C*] verdicts.
#   1 otherwise (the failing form and its output tail, or the verdict diff).
assert_payload_validate_cwd_independent() {
  local target="$1"
  local consumer_root payload_rel a_out b_out a_rc b_rc

  consumer_root="$(cd -- "$(dirname -- "${target}")" && pwd)"
  payload_rel="$(basename -- "${target}")"

  # Form A: from inside the payload root (the always-worked form).
  if a_out="$(cd -- "${target}" && bash tools/validate.sh --payload 2>&1)"; then
    a_rc=0
  else
    a_rc=$?
  fi
  # Form B: from the consumer repository root, via the payload path (the
  # form issue #18 reported broken).
  if b_out="$(cd -- "${consumer_root}" && bash "${payload_rel}/tools/validate.sh" --payload 2>&1)"; then
    b_rc=0
  else
    b_rc=$?
  fi

  if [ "${a_rc}" -ne 0 ]; then
    echo "assert_payload_validate_cwd_independent: FORM A (from payload root) failed (rc=${a_rc}):"
    printf '%s\n' "${a_out}" | tail -20
    return 1
  fi
  if [ "${b_rc}" -ne 0 ]; then
    echo "assert_payload_validate_cwd_independent: FORM B (issue #18, from consumer repo root) failed (rc=${b_rc}):"
    printf '%s\n' "${b_out}" | tail -20
    return 1
  fi
  if ! diff <(printf '%s\n' "${a_out}" | grep '^\[C') <(printf '%s\n' "${b_out}" | grep '^\[C') >/dev/null 2>&1; then
    echo "assert_payload_validate_cwd_independent: the two --payload invocation forms produced DIFFERENT [C*] verdicts:"
    diff <(printf '%s\n' "${a_out}" | grep '^\[C') <(printf '%s\n' "${b_out}" | grep '^\[C') || true
    return 1
  fi

  echo "assert_payload_validate_cwd_independent: OK -- --payload is CWD-independent (both invocation forms green with identical [C*] verdicts under ${target})"
  return 0
}

# ---------------------------------------------------------------------------
# cleanup -- registered as `trap cleanup EXIT` by main() (never at top level,
# so sourcing this file never registers a trap in the sourcing shell).
# Follows bootstrap.sh's own cleanup() idiom exactly: capture the real exit
# code FIRST, do best-effort teardown, then return that exit code so the
# trap never masks the invocation's true result. Idempotent and safe even if
# EPHEMERAL_TAG/SCRATCH_DIR were never set (an early failure before either
# resource was created).
# ---------------------------------------------------------------------------

cleanup() {
  local exit_code=$?

  if [ -n "${SCRATCH_DIR:-}" ] && [ -d "${SCRATCH_DIR}" ]; then
    rm -rf -- "${SCRATCH_DIR}"
  fi

  if [ -n "${EPHEMERAL_TAG:-}" ] && git rev-parse -q --verify "refs/tags/${EPHEMERAL_TAG}" >/dev/null 2>&1; then
    git tag -d "${EPHEMERAL_TAG}" >/dev/null 2>&1 || true
  fi

  return "${exit_code}"
}

# ---------------------------------------------------------------------------
# main -- the entry point, executed ONLY when this file is run directly (see
# the BASH_SOURCE guard at the bottom of this file), never when merely
# sourced. `set -euo pipefail` is scoped to this function body, so sourcing
# this file never mutates the sourcing shell's own options.
# ---------------------------------------------------------------------------

main() {
  set -euo pipefail

  local mode="positive"
  case "${1:-}" in
    "") ;;
    --self-test-negative) mode="negative" ;;
    *)
      echo "e2e_bootstrap_test.sh: unrecognized argument: ${1}" >&2
      echo "usage: bash tools/e2e_bootstrap_test.sh [--self-test-negative]" >&2
      exit 1
      ;;
  esac

  command -v git >/dev/null 2>&1 || { echo "e2e_bootstrap_test.sh: required command 'git' not found on PATH." >&2; exit 1; }
  command -v python3 >/dev/null 2>&1 || { echo "e2e_bootstrap_test.sh: required command 'python3' not found on PATH." >&2; exit 1; }
  [ -f bootstrap.sh ] || { echo "e2e_bootstrap_test.sh: bootstrap.sh not found -- must be run with CWD at the repository root." >&2; exit 1; }

  # shellcheck source=tools/verify_lib.sh
  source "$(dirname -- "${BASH_SOURCE[0]}")/verify_lib.sh"

  EPHEMERAL_TAG=""
  SCRATCH_DIR=""
  trap cleanup EXIT

  EPHEMERAL_TAG="e2e-$(date -u +%s)-$$"
  # Scoped (-c) git identity: annotated tags record a tagger, but CI runners
  # have no ambient user.name/user.email configured, which fails this single
  # invocation with "empty ident name ... not allowed" (exit 128). Supplying
  # the identity inline keeps the harness hermetic and self-contained in any
  # environment without mutating global/repo git config via `git config`.
  git -c user.name='nizam-e2e-bootstrap' -c user.email='e2e-bootstrap@nizam.local' \
    tag -a "${EPHEMERAL_TAG}" -m "ephemeral e2e-bootstrap-test tag (tools/e2e_bootstrap_test.sh) -- auto-deleted on exit" HEAD

  SCRATCH_DIR="$(mktemp -d)"
  local target="${SCRATCH_DIR}/.nizam"

  echo "e2e_bootstrap_test.sh: installing pinned tag '${EPHEMERAL_TAG}' from 'file://$(pwd)' into '${target}' (hermetic -- local file:// clone, no network)..."
  bash bootstrap.sh --repo-url "file://$(pwd)" --tag "${EPHEMERAL_TAG}" --target "${target}"

  assert_payload_present "${target}"
  assert_nizam_index_valid "${target}"

  if [ "${mode}" = "negative" ]; then
    echo "e2e_bootstrap_test.sh: --self-test-negative -- deliberately removing ${target}/tools/skill.json to prove the H4 discovery-path guard is load-bearing, not tautological..."
    rm -f "${target}/tools/skill.json"

    if assert_discovery_path "${target}"; then
      echo "e2e_bootstrap_test.sh: H4 REGRESSION: discovery-path guard did NOT detect the deliberately broken payload (tools/skill.json missing) -- guard is NOT load-bearing" >&2
      exit 1
    fi

    echo "e2e_bootstrap_test.sh: H4 GUARD CONFIRMED LOAD-BEARING: broken payload (missing tools/skill.json) correctly rejected by the discovery-path assertion."
    # --self-test-negative's job is to PROVE a failure detection; completing
    # that job successfully is itself signalled by a non-zero exit (the
    # common negative-test-harness convention), distinguished from an
    # unexpected script crash only by the message above.
    exit 1
  fi

  assert_discovery_path "${target}"
  run_bootstrap_verify_only "${EPHEMERAL_TAG}" "${target}"
  assert_provenance_sha_pin "${EPHEMERAL_TAG}" "${target}"
  assert_payload_validate_cwd_independent "${target}"
  assert_preflight_governance_root "${SCRATCH_DIR}"
  assert_genesis "${EPHEMERAL_TAG}"
  assert_multirepo "${EPHEMERAL_TAG}"
  assert_stage4

  echo "e2e_bootstrap_test.sh: PASS -- hermetic bootstrap inject-then-verify cycle succeeded (tag ${EPHEMERAL_TAG}, target ${target})."
}

# assert_preflight_governance_root <consumer_root>
# --------------------------------------------------------------------------
# Feature 065 (ADR-004 decision 1; NDEBT-027): a real bootstrapped consumer holds
# the governance payload under .nizam/, NOT at the repo root. ecosystem_preflight.py
# must discover that governance-root so its required references resolve there, and
# must treat the injected (untracked) .nizam/ as an expected exception rather than
# a blocking finding -- so a clean Preflight against a real consumer is a
# PASS_WITH_EXCEPTIONS, never the pre-065 hard FAIL(1). This closes phase-007 pilot
# finding A against a genuinely bootstrapped payload (not a hand-built fixture).
#
# Returns:
#   0 if ecosystem_preflight.py does NOT hard-FAIL(1) against the bootstrapped
#     consumer (exit 2 pending / 3 approved, carrying only the injected-payload
#     exception, are the acceptable clean outcomes); non-zero otherwise.
assert_preflight_governance_root() {
  local consumer_root="$1" out rc
  out="$(mktemp -d)"
  # The bootstrap target is a bare injected .nizam/ payload; ecosystem_preflight.py
  # needs a git working tree with a resolvable HEAD, so stand a minimal consumer
  # repo around it (.nizam/ deliberately left untracked -- the injected payload).
  git -C "${consumer_root}" init -q
  git -C "${consumer_root}" config user.email t@example.invalid
  git -C "${consumer_root}" config user.name tester
  printf '# consumer\n' > "${consumer_root}/README.md"
  git -C "${consumer_root}" add README.md
  git -C "${consumer_root}" commit -qm init
  # Capture the exit code without tripping main()'s `set -e`: a PASS_WITH_EXCEPTIONS
  # verdict legitimately returns non-zero (2 pending / 3 approved), which is the
  # expected clean outcome here, not a harness error.
  if python3 tools/ecosystem_preflight.py --execution-id e2e-preflight \
      --output-dir "${out}" --repo-root "${consumer_root}" >/dev/null 2>&1; then
    rc=0
  else
    rc=$?
  fi
  rm -rf -- "${out}"
  # The injected (untracked) .nizam/ must always surface as an expected exception,
  # so the ONLY valid outcomes are PASS_WITH_EXCEPTIONS -- exit 2 (pending) or 3
  # (operator-approved). Anything else is a regression: 1 = the pre-065 hard FAIL,
  # 0 = the injected payload was NOT surfaced as an exception, 64 = a CLI usage
  # error from a future change, etc. -- all must fail this, the only assertion that
  # exercises ecosystem_preflight.py against a genuinely bootstrap-produced .nizam/.
  if [ "${rc}" -ne 2 ] && [ "${rc}" -ne 3 ]; then
    echo "assert_preflight_governance_root: FAIL -- expected exit 2 (pending) or 3 (approved) against a bootstrapped consumer, got ${rc}; governance-root discovery did not resolve the injected .nizam/ as an expected exception (feature 065 / ADR-004 regression)"
    return 1
  fi
  echo "assert_preflight_governance_root: OK -- ecosystem_preflight.py discovered the injected .nizam/ governance-root (exit ${rc}: PASS_WITH_EXCEPTIONS; the injected payload is an expected exception, required references resolve under .nizam/)."
  return 0
}

# assert_genesis <tag>
# --------------------------------------------------------------------------
# Feature 073 (NDEBT-030; NIP-0002 Stage 2): proves the 0-case end-to-end --
# `bootstrap.sh --genesis` stands up a NEW project FROM NOTHING (git init +
# the deterministic scaffold of ecosystem/00 Section 8), injects the payload,
# and the result is a clean cycle participant that Preflight accepts as
# PASS_WITH_EXCEPTIONS (the injected, untracked .nizam/ the only exception).
# Also proves genesis REFUSES a non-empty --project-root (a brownfield adoption,
# not a genesis). Hermetic: clones file://$(pwd) at the ephemeral tag; everything
# lives under SCRATCH_DIR so cleanup removes it. Each bootstrap/preflight exit is
# captured via an `if` so main()'s `set -e` never aborts before a diagnostic.
#
# Returns 0 if genesis stands up a scaffolded, provenance-pinned, Preflight-clean
# project AND refuses a non-empty target; non-zero (with a diagnostic) otherwise.
assert_genesis() {
  local tag="$1"
  local proj="${SCRATCH_DIR}/genesis-proj"
  local nonempty="${SCRATCH_DIR}/genesis-nonempty"
  local out rc recorded_sha f

  # (a) genesis-from-nothing: create + scaffold + inject in one command.
  if ! bash bootstrap.sh --genesis --project-root "${proj}" --project-name e2e-demo \
      --tag "${tag}" --repo-url "file://$(pwd)" >/dev/null 2>&1; then
    echo "assert_genesis: FAIL -- bootstrap.sh --genesis did not stand up a new project at '${proj}'."
    return 1
  fi

  # (b) the deterministic scaffold is present and non-empty.
  for f in README.md CONTEXT.md src/PLACEHOLDER.md; do
    if [ ! -s "${proj}/${f}" ]; then
      echo "assert_genesis: FAIL -- expected scaffold file missing or empty: ${f}"
      return 1
    fi
  done

  # (c) the injected payload carries provenance with a recorded resolved_sha.
  recorded_sha="$(python3 -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle).get("resolved_sha", ""))
' "${proj}/.nizam/provenance.json")" || { echo "assert_genesis: FAIL -- genesis payload provenance.json unreadable under '${proj}/.nizam'."; return 1; }
  if [ -z "${recorded_sha}" ]; then
    echo "assert_genesis: FAIL -- genesis payload recorded no resolved_sha (feature 067/071 regression)."
    return 1
  fi

  # (d) commit the scaffold so the working tree is clean except the injected,
  # untracked .nizam/; Preflight must then accept it as PASS_WITH_EXCEPTIONS.
  git -C "${proj}" config user.email t@example.invalid
  git -C "${proj}" config user.name tester
  git -C "${proj}" add README.md CONTEXT.md src
  git -C "${proj}" commit -qm "genesis scaffold"
  out="$(mktemp -d)"
  if python3 tools/ecosystem_preflight.py --execution-id e2e-genesis \
      --output-dir "${out}" --repo-root "${proj}" >/dev/null 2>&1; then
    rc=0
  else
    rc=$?
  fi
  rm -rf -- "${out}"
  if [ "${rc}" -ne 2 ] && [ "${rc}" -ne 3 ]; then
    echo "assert_genesis: FAIL -- Preflight against the genesis'd project expected exit 2/3 (PASS_WITH_EXCEPTIONS), got ${rc}."
    return 1
  fi

  # (e) genesis refuses a non-empty --project-root (a brownfield adoption).
  mkdir -p "${nonempty}"
  printf 'existing\n' > "${nonempty}/existing.txt"
  if bash bootstrap.sh --genesis --project-root "${nonempty}" \
      --tag "${tag}" --repo-url "file://$(pwd)" >/dev/null 2>&1; then
    echo "assert_genesis: FAIL -- genesis did NOT refuse a non-empty --project-root '${nonempty}'."
    return 1
  fi

  echo "assert_genesis: OK -- genesis stood up a new project from nothing (scaffold present; provenance resolved_sha=${recorded_sha}); Preflight accepts it (exit ${rc}: PASS_WITH_EXCEPTIONS); a non-empty --project-root is refused."
  return 0
}

# assert_multirepo <tag>
# --------------------------------------------------------------------------
# Feature 078 (NDEBT-031; NIP-0002 Stage 3): proves the n-case end-to-end --
# stand up a scratch MULTI-repo ecosystem (>=2 projects created FROM NOTHING by
# bootstrap.sh --genesis, phase 009), author a membership registry over them,
# and prove the iteration (feature 076) + aggregation (feature 077) run across
# the set producing a schema-valid ecosystem-level result. This is the multi-
# member generalisation of assert_genesis's single count-1 project: two members
# genesis'd at the SAME ephemeral tag share one framework pin, so a correct
# ecosystem run is PASS with framework_pin_consistent true. Hermetic: everything
# lives under SCRATCH_DIR (cleanup removes it); the ephemeral tag is the same one
# main() already created. Each tool exit is captured via an `if` so main()'s
# `set -e` never aborts before a diagnostic is printed.
#
# Asserts, in order:
#   (a) two projects genesis from nothing (member-a, member-b), each scaffolded +
#       provenance-pinned, and each is committed so its working tree is clean
#       except the injected untracked .nizam/;
#   (b) the authored membership registry validates against
#       schema/ecosystem_membership.schema.json via `validate.sh --target` (C12);
#   (c) ecosystem_membership_run.py iterates the in_scope set and returns
#       ecosystem PASS (exit 0) -- both members Preflight-acceptable, pins agree;
#   (d) the produced <out>/membership_run.json is a schema-valid ecosystem-level
#       result (validate.sh --target, C12) with ecosystem_verdict PASS,
#       framework_pin_consistent true, and member_count 2.
#
# Returns 0 if all four hold; non-zero (with a diagnostic) otherwise.
assert_multirepo() {
  local tag="$1"
  local eco="${SCRATCH_DIR}/multirepo"
  local registry="${eco}/membership.json"
  local out="${eco}/out"
  local member rc verdict consistent count
  local -a members=("member-a" "member-b")

  mkdir -p "${eco}"

  # (a) genesis each member FROM NOTHING at the shared ephemeral tag, then commit
  # its scaffold so only the injected untracked .nizam/ remains (Preflight-clean).
  for member in "${members[@]}"; do
    if ! bash bootstrap.sh --genesis --project-root "${eco}/${member}" --project-name "${member}" \
        --tag "${tag}" --repo-url "file://$(pwd)" >/dev/null 2>&1; then
      echo "assert_multirepo: FAIL -- bootstrap.sh --genesis did not stand up member '${member}'."
      return 1
    fi
    git -C "${eco}/${member}" config user.email t@example.invalid
    git -C "${eco}/${member}" config user.name tester
    git -C "${eco}/${member}" add README.md CONTEXT.md src
    git -C "${eco}/${member}" commit -qm "genesis scaffold" >/dev/null 2>&1
  done

  # Author a membership registry over the two members (absolute repo_root each).
  python3 - "${registry}" "${eco}/member-a" "${eco}/member-b" <<'PY'
import json, sys
registry, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
doc = {
    "schema_version": "1.0.0",
    "last_updated": "2026-07-22",
    "in_scope": [
        {"name": "member-a", "repo_root": a, "note": "scratch genesis'd member (e2e n-case)"},
        {"name": "member-b", "repo_root": b, "note": "scratch genesis'd member (e2e n-case)"},
    ],
    "incubating": [],
    "reference_archive": [],
    "out_of_scope": [],
}
with open(registry, "w", encoding="utf-8") as handle:
    json.dump(doc, handle, indent=2)
    handle.write("\n")
PY

  # (b) the registry validates against its schema (C12 --target router).
  if ! bash tools/validate.sh --target "${registry}" >/dev/null 2>&1; then
    echo "assert_multirepo: FAIL -- the authored membership registry did not validate (validate.sh --target, C12)."
    return 1
  fi

  # (c) iterate + aggregate across the set; a pin-consistent, all-acceptable
  # ecosystem is PASS (exit 0).
  if python3 tools/ecosystem_membership_run.py --membership-registry "${registry}" \
      --output-dir "${out}" --repo-roots-base "${eco}" >/dev/null 2>&1; then
    rc=0
  else
    rc=$?
  fi
  if [ "${rc}" -ne 0 ]; then
    echo "assert_multirepo: FAIL -- ecosystem run over the 2-member set expected exit 0 (PASS), got ${rc}."
    return 1
  fi
  if [ ! -s "${out}/membership_run.json" ]; then
    echo "assert_multirepo: FAIL -- no aggregate result written at ${out}/membership_run.json."
    return 1
  fi

  # (d) the produced aggregate is a schema-valid ecosystem-level result (C12) and
  # records the expected PASS / pin-consistent / 2-member verdict.
  if ! bash tools/validate.sh --target "${out}/membership_run.json" >/dev/null 2>&1; then
    echo "assert_multirepo: FAIL -- the produced membership_run.json did not validate as an ecosystem-level result (validate.sh --target, C12)."
    return 1
  fi
  verdict="$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(d.get("ecosystem_verdict", ""))
' "${out}/membership_run.json")"
  consistent="$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print("true" if d.get("framework_pin_consistent") is True else "false")
' "${out}/membership_run.json")"
  count="$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(d.get("member_count", -1))
' "${out}/membership_run.json")"
  if [ "${verdict}" != "PASS" ] || [ "${consistent}" != "true" ] || [ "${count}" != "2" ]; then
    echo "assert_multirepo: FAIL -- aggregate result mismatch: ecosystem_verdict=${verdict} (expect PASS), framework_pin_consistent=${consistent} (expect true), member_count=${count} (expect 2)."
    return 1
  fi

  echo "assert_multirepo: OK -- a scratch 2-member ecosystem (both genesis'd from nothing at one pin) iterates + aggregates to a schema-valid ecosystem-level result (ecosystem_verdict PASS, framework_pin_consistent true, member_count 2)."
  return 0
}

# assert_stage4
#
# The NIP-0002 Stage 4 (n-coordination) hermetic case, chained onto the aggregate
# assert_multirepo produced (${SCRATCH_DIR}/multirepo/out/membership_run.json) --
# no fresh genesis clone (the per-member clone cost is NDEBT-034). It runs the
# aggregate -> reconciliation -> release-train chain across the 2-member set and
# asserts each stage produces a schema-valid artifact with the correct verdict:
#   (a) ecosystem_reconcile.py turns a packets input (over the aggregate's in_scope
#       members, with a cross-repo depends_on edge) into a PASS reconciliation plan
#       (exit 0) that validates against schema/reconciliation_plan.schema.json (C12);
#   (b) ecosystem_release_train.py admits that plan into a release train WITH the
#       H-TRAIN-ENTRY decision recorded -> a PASS manifest (exit 0) that validates
#       against schema/release_train_manifest.schema.json (C12);
#   (c) the same admission WITHOUT --entry-gate-recorded is refused a PASS -> FAIL
#       (exit 1), proving the gate is load-bearing, not cosmetic.
assert_stage4() {
  local eco="${SCRATCH_DIR}/multirepo"
  local agg="${eco}/out/membership_run.json"
  local pk="${eco}/packets.json"
  local plan_dir="${eco}/plan" train_dir="${eco}/train" ungated_dir="${eco}/train_ungated"
  local rc verdict

  if [ ! -s "${agg}" ]; then
    echo "assert_stage4: FAIL -- no aggregate at ${agg} (assert_multirepo must run first)."
    return 1
  fi

  # A packets input over the aggregate's members, with a cross-repo depends_on edge
  # (member-a's packet depends on member-b's) so the topological order is non-trivial.
  cat > "${pk}" <<'PY'
{
  "packets": [
    {"id": "pkt-a", "repo": "member-a", "closes_findings": ["F-A1"], "depends_on": ["pkt-b"]},
    {"id": "pkt-b", "repo": "member-b", "closes_findings": ["F-B1"], "depends_on": []}
  ]
}
PY

  # (a) reconcile -> a PASS plan that validates as reconciliation_plan (C12).
  if python3 tools/ecosystem_reconcile.py --source-result "${agg}" --packets "${pk}" \
      --output-dir "${plan_dir}" >/dev/null 2>&1; then rc=0; else rc=$?; fi
  if [ "${rc}" -ne 0 ]; then
    echo "assert_stage4: FAIL -- reconcile over the 2-member aggregate expected exit 0 (PASS plan), got ${rc}."
    return 1
  fi
  if ! bash tools/validate.sh --target "${plan_dir}/plan.json" >/dev/null 2>&1; then
    echo "assert_stage4: FAIL -- the produced plan.json did not validate as a reconciliation_plan (validate.sh --target, C12)."
    return 1
  fi

  # (b) release-train WITH the H-TRAIN-ENTRY decision recorded -> a PASS manifest
  # that validates as release_train_manifest (C12).
  if python3 tools/ecosystem_release_train.py --plan "${plan_dir}/plan.json" \
      --output-dir "${train_dir}" --entry-gate-recorded >/dev/null 2>&1; then rc=0; else rc=$?; fi
  if [ "${rc}" -ne 0 ]; then
    echo "assert_stage4: FAIL -- gated release-train expected exit 0 (PASS train), got ${rc}."
    return 1
  fi
  if ! bash tools/validate.sh --target "${train_dir}/manifest.json" >/dev/null 2>&1; then
    echo "assert_stage4: FAIL -- the produced manifest.json did not validate as a release_train_manifest (validate.sh --target, C12)."
    return 1
  fi
  verdict="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("train_verdict",""))' "${train_dir}/manifest.json")"
  if [ "${verdict}" != "PASS" ]; then
    echo "assert_stage4: FAIL -- gated train manifest expected train_verdict PASS, got ${verdict}."
    return 1
  fi

  # (c) the SAME admission WITHOUT --entry-gate-recorded is refused a PASS (exit 1),
  # proving the gate is load-bearing.
  if python3 tools/ecosystem_release_train.py --plan "${plan_dir}/plan.json" \
      --output-dir "${ungated_dir}" >/dev/null 2>&1; then rc=0; else rc=$?; fi
  if [ "${rc}" -ne 1 ]; then
    echo "assert_stage4: FAIL -- ungated release-train expected exit 1 (FAIL, H-TRAIN-ENTRY not recorded), got ${rc}."
    return 1
  fi

  echo "assert_stage4: OK -- the aggregate -> reconciliation -> release-train chain runs across the 2-member set: a PASS plan + a PASS train manifest (both C12-valid), and an ungated admission is correctly refused a PASS (FAIL)."
  return 0
}

# Direct-execution guard: `main "$@"` runs ONLY when this file is executed
# directly (e.g. `bash tools/e2e_bootstrap_test.sh`), never when it is merely
# `source`d -- so sourcing this file for fixture-testing its functions never
# triggers a real clone, tag, or scratch directory.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
