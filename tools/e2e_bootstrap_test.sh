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
# (tools/interface.md Sec 2, item 1) -- and (d) `bootstrap.sh --verify-only`
# passes against the injected target. No network access ever occurs: the
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
#   0 if standard/, templates/, schema/, tools/, NIZAM.json, and
#     provenance.json are all present (directories real, files non-empty).
#   1 otherwise (the first missing item is named).
assert_payload_present() {
  local target="$1"
  local d f

  for d in standard templates schema tools; do
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

  echo "assert_payload_present: OK -- standard/, templates/, schema/, tools/, NIZAM.json, provenance.json all present under ${target}"
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

injected_module_paths = {"standard", "templates", "schema", "tools"}


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

  echo "e2e_bootstrap_test.sh: PASS -- hermetic bootstrap inject-then-verify cycle succeeded (tag ${EPHEMERAL_TAG}, target ${target})."
}

# Direct-execution guard: `main "$@"` runs ONLY when this file is executed
# directly (e.g. `bash tools/e2e_bootstrap_test.sh`), never when it is merely
# `source`d -- so sourcing this file for fixture-testing its functions never
# triggers a real clone, tag, or scratch directory.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
