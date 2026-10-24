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

  if ! ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}"; then
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
  # (b) correct expected SHA + --git-repo -> PASS (exit 0) and content_integrity=verified
  local vo_out
  if ! vo_out="$(ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity 2>&1)"; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only rejected the correct recorded SHA (${recorded_sha}): ${vo_out}"
    return 1
  fi
  case "${vo_out}" in
    *"content_integrity=verified"*) ;;
    *)
      echo "assert_provenance_sha_pin: FAIL -- --verify-only did not report content_integrity=verified: ${vo_out}"
      return 1
      ;;
  esac
  # (b2) C2: --expected-sha without --git-repo -> FAIL (never derive repo from provenance.json or ambient CWD)
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted --expected-sha without --git-repo"
    return 1
  fi
  # (b3) C2: --source-root with --expected-sha or --require-content-integrity -> FAIL (unbound directory cannot satisfy commit-bound integrity)
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --source-root "$(pwd)" --expected-sha "${recorded_sha}" --require-content-integrity >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only allowed unbound --source-root to satisfy --expected-sha / --require-content-integrity"
    return 1
  fi
  # (b4) C2 downgrade bug: --source-root=--audit-invalid-reference with --expected-sha and --require-content-integrity -> FAIL
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --source-root=--audit-invalid-reference --expected-sha "${recorded_sha}" --require-content-integrity >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only downgraded --source-root=--audit-invalid-reference to pass"
    return 1
  fi
  # (c) wrong expected SHA -> drift FAIL (non-zero)
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --git-repo "$(pwd)" \
      --expected-sha "0000000000000000000000000000000000000000" >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted a WRONG expected SHA (moved-tag drift not detected)"
    return 1
  fi
  # (d) V3 Case 2: harmless comment appended to installed tools/start_path.py -> FAIL
  cp -p "${target}/tools/start_path.py" "${SCRATCH_DIR}/start_path.py.orig"
  printf '\n# harmless audit comment\n' >> "${target}/tools/start_path.py"
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity >/dev/null 2>&1; then
    mv -f "${SCRATCH_DIR}/start_path.py.orig" "${target}/tools/start_path.py"
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted appended comment in tools/start_path.py (V3 content drift missed)"
    return 1
  fi
  mv -f "${SCRATCH_DIR}/start_path.py.orig" "${target}/tools/start_path.py"
  # (e) V3 Case 3: unexpected extra file added under payload -> FAIL
  printf 'unexpected\n' > "${target}/tools/unexpected_audit_file.txt"
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity >/dev/null 2>&1; then
    rm -f -- "${target}/tools/unexpected_audit_file.txt"
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted unexpected extra file under payload (V3 inventory drift missed)"
    return 1
  fi
  rm -f -- "${target}/tools/unexpected_audit_file.txt"
  # (f) V3 mode drift: flipping executable bit on tools/start_path.py -> FAIL
  chmod +x "${target}/tools/start_path.py"
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity >/dev/null 2>&1; then
    chmod -x "${target}/tools/start_path.py"
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted executable mode drift on tools/start_path.py"
    return 1
  fi
  chmod -x "${target}/tools/start_path.py"
  # (g) C2 tampered checker: replacing installed tools/payload_integrity.py with print-only exit-0 stub + extra file -> FAIL
  cp -p "${target}/tools/payload_integrity.py" "${SCRATCH_DIR}/payload_integrity.py.orig"
  printf '#!/usr/bin/env python3\nimport sys\nprint("STUB PASS")\nsys.exit(0)\n' > "${target}/tools/payload_integrity.py"
  printf 'unexpected\n' > "${target}/tools/unexpected_stub_file.txt"
  if ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity >/dev/null 2>&1; then
    mv -f "${SCRATCH_DIR}/payload_integrity.py.orig" "${target}/tools/payload_integrity.py"
    rm -f -- "${target}/tools/unexpected_stub_file.txt"
    echo "assert_provenance_sha_pin: FAIL -- --verify-only accepted tampered installed payload_integrity.py stub"
    return 1
  fi
  mv -f "${SCRATCH_DIR}/payload_integrity.py.orig" "${target}/tools/payload_integrity.py"
  rm -f -- "${target}/tools/unexpected_stub_file.txt"
  # Restore check passes again
  if ! ALLOW_FIXTURE_TAG=1 bash bootstrap.sh --verify-only --tag "${tag}" --target "${target}" --expected-sha "${recorded_sha}" --git-repo "$(pwd)" --require-content-integrity >/dev/null 2>&1; then
    echo "assert_provenance_sha_pin: FAIL -- --verify-only failed after restoring original payload"
    return 1
  fi
  echo "assert_provenance_sha_pin: OK -- resolved_sha recorded (${recorded_sha}) == tag's true commit; --verify-only enforces --git-repo + --expected-sha match, content bytes, file inventory, executable modes, and C2 guards."
  return 0
}

# assert_install_tag_and_sha_pin_and_worktree_reproducibility <tag>
# --------------------------------------------------------------------------
# Corrective B2 (V2 + V7 regression guard):
#   1. Public path (ALLOW_FIXTURE_TAG=0) rejects fixture tag names (`e2e-*`),
#      floating branch names (`audit-floating-branch`), release-shaped branch
#      names without a matching tag (`refs/heads/v99.9.9`), and same-name
#      branch/tag ambiguity (`refs/heads/v99.8.8` + `refs/tags/v99.8.8`).
#   2. Install-time `--expected-sha` succeeds when `refs/tags/<tag>^{commit}`
#      matches `--expected-sha`, and fails non-zero BEFORE replacing an existing
#      target when `--expected-sha` mismatches or is malformed.
#   3. Both annotated (`v99.1.0`) and lightweight (`v99.2.0`) SemVer release
#      tags resolve via `refs/tags/<tag>^{commit}` on the public path.
#   4. Linked `git worktree` reproducibility (V7): normal clone invocation,
#      invocation from inside a linked git worktree, and `file://` source
#      pointing at a linked git worktree produce identical file inventories,
#      executable modes, and SHA-256 digests.
assert_install_tag_and_sha_pin_and_worktree_reproducibility() {
  local fixture_tag="$1"
  local b2_dir="${SCRATCH_DIR}/b2-pin-and-wt"
  local src_repo="${b2_dir}/src-repo"
  local head_sha

  mkdir -p "${b2_dir}"

  # (1a) Public path must reject e2e-* fixture tag when ALLOW_FIXTURE_TAG=0
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${E2E_SOURCE}" --tag "${fixture_tag}" --target "${b2_dir}/reject-fixture" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- public path accepted non-SemVer fixture tag '${fixture_tag}'"
    return 1
  fi

  # Prepare a disposable source repository cloned from this checkout
  git clone --quiet "file://${E2E_SOURCE}" "${src_repo}"
  git -C "${src_repo}" config user.email "b2-test@nizam.local"
  git -C "${src_repo}" config user.name "B2 Pin Test"
  git -C "${src_repo}" config uploadpack.allowFilter true
  head_sha="$(git -C "${src_repo}" rev-parse HEAD)"

  # Create branch-only ref, release-shaped branch ref, ambiguous branch+tag,
  # annotated SemVer tag, and lightweight SemVer tag.
  git -C "${src_repo}" branch audit-floating-branch HEAD
  git -C "${src_repo}" branch v99.9.9 HEAD
  git -C "${src_repo}" branch v99.8.8 HEAD
  git -C "${src_repo}" tag -a v99.8.8 -m "ambiguous tag" HEAD
  git -C "${src_repo}" tag -a v99.1.0 -m "annotated release tag" HEAD
  git -C "${src_repo}" tag v99.2.0 HEAD

  # (1b) Reject arbitrary branch name
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag audit-floating-branch --target "${b2_dir}/reject-branch" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- accepted floating branch 'audit-floating-branch'"
    return 1
  fi
  # (1c) Reject release-shaped branch without refs/tags/<tag>
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.9.9 --target "${b2_dir}/reject-rel-branch" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- accepted release-shaped branch 'v99.9.9' without refs/tags/v99.9.9"
    return 1
  fi
  # (1d) Reject same-name branch and tag ambiguity
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.8.8 --target "${b2_dir}/reject-ambig" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- accepted ambiguous same-name branch/tag 'v99.8.8'"
    return 1
  fi

  # (2a & 3a) Annotated release tag v99.1.0 with matching --expected-sha succeeds on public path
  if ! ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.1.0 \
      --expected-sha "${head_sha}" --target "${b2_dir}/ok-annotated/.nizam" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- install of annotated tag v99.1.0 with matching --expected-sha failed"
    return 1
  fi

  # Plant a sentinel in the existing target, then verify mismatched --expected-sha fails BEFORE replacing target
  printf 'keep-existing-target\n' > "${b2_dir}/ok-annotated/.nizam/sentinel.keep"
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.1.0 \
      --expected-sha "0000000000000000000000000000000000000000" --target "${b2_dir}/ok-annotated/.nizam" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- install accepted mismatched --expected-sha"
    return 1
  fi
  if [ ! -f "${b2_dir}/ok-annotated/.nizam/sentinel.keep" ]; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- failed install with mismatched --expected-sha replaced or deleted existing target"
    return 1
  fi
  rm -f -- "${b2_dir}/ok-annotated/.nizam/sentinel.keep"

  # Reject malformed --expected-sha
  if ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.1.0 \
      --expected-sha "not-a-40-hex-sha" --target "${b2_dir}/reject-malformed-sha/.nizam" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- install accepted malformed --expected-sha"
    return 1
  fi

  # (3b) Lightweight release tag v99.2.0 with matching --expected-sha succeeds on public path
  if ! ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.2.0 \
      --expected-sha "${head_sha}" --target "${b2_dir}/ok-lightweight/.nizam" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- install of lightweight tag v99.2.0 with matching --expected-sha failed"
    return 1
  fi

  # (3c) --git-repo install retention (regression guard): a successful install
  # retains the verified sparse reference, and a subsequent --verify-only
  # --git-repo content-integrity check passes against it.
  local ref_target="${b2_dir}/ok-ref/.nizam"
  local ref_repo="${b2_dir}/ok-ref/reference"
  if ! ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" --tag v99.1.0 \
      --expected-sha "${head_sha}" --target "${ref_target}" --git-repo "${ref_repo}" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- --git-repo install retention failed"
    return 1
  fi
  if [ ! -d "${ref_repo}/.git" ]; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- --git-repo install did not retain the verified reference"
    return 1
  fi
  if ! ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --verify-only --tag v99.1.0 --expected-sha "${head_sha}" \
      --target "${ref_target}" --git-repo "${ref_repo}" --require-content-integrity >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- --verify-only --git-repo content integrity failed after install retention"
    return 1
  fi

  # (4) Worktree reproducibility (V7 regression guard):
  # Compare normal clone install (ok-annotated/.nizam), invocation from inside a linked git worktree,
  # and file:// source pointing at a linked git worktree.
  local linked_wt="${b2_dir}/linked-worktree"
  git -C "${src_repo}" worktree add --quiet --detach "${linked_wt}" v99.1.0

  if ! (cd -- "${linked_wt}" && ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${src_repo}" \
      --tag v99.1.0 --expected-sha "${head_sha}" --target "${b2_dir}/wt-cwd/.nizam" >/dev/null 2>&1); then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- bootstrap invocation from linked git worktree CWD failed"
    return 1
  fi

  if ! ALLOW_FIXTURE_TAG=0 bash bootstrap.sh --repo-url "file://${linked_wt}" \
      --tag v99.1.0 --expected-sha "${head_sha}" --target "${b2_dir}/wt-source/.nizam" >/dev/null 2>&1; then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- bootstrap invocation from linked git worktree file:// source failed"
    return 1
  fi

  if ! PYTHONDONTWRITEBYTECODE=1 python3 - "${b2_dir}/ok-annotated/.nizam" "${b2_dir}/wt-cwd/.nizam" "${b2_dir}/wt-source/.nizam" <<'PY'
import hashlib
import json
import pathlib
import sys

roots = [pathlib.Path(p).resolve() for p in sys.argv[1:4]]

def snapshot(root: pathlib.Path) -> dict:
    snap = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        mode = bool(p.stat().st_mode & 0o111)
        if rel == "provenance.json":
            doc = json.loads(p.read_text(encoding="utf-8"))
            snap[rel] = {
                "mode": mode,
                "framework_version": doc.get("framework_version"),
                "tag": doc.get("tag"),
                "resolved_sha": doc.get("resolved_sha"),
            }
        else:
            snap[rel] = {
                "mode": mode,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
    return snap

base = snapshot(roots[0])
if len(base) < 270:
    print(f"unexpected file count in installed payload: {len(base)}", file=sys.stderr)
    sys.exit(1)
for other_root in roots[1:]:
    other = snapshot(other_root)
    if other != base:
        print(f"worktree reproducibility mismatch between {roots[0]} and {other_root}", file=sys.stderr)
        sys.exit(1)
PY
  then
    echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: FAIL -- worktree installs produced differing inventories, modes, or digests"
    return 1
  fi

  git -C "${src_repo}" worktree remove --force "${linked_wt}" >/dev/null 2>&1 || true
  rm -rf -- "${b2_dir}"

  echo "assert_install_tag_and_sha_pin_and_worktree_reproducibility: OK -- public SemVer tag gate, install-time --expected-sha match/mismatch, annotated+lightweight tags, and 3-form linked-worktree reproducibility verified."
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
  local expected_summary="SUMMARY (payload mode): 10 exercised passed, 0 failed, 2 not-applicable (C11, C16), 1 skipped (C6), 3 out-of-scope (C12, C14, C15); content_integrity=not_checked, operational_acceptance=not_assessed"
  case "${a_out}" in
    *"${expected_summary}"*) ;;
    *)
      echo "assert_payload_validate_cwd_independent: FORM A missing non-conflated payload summary line (V4 regression)"
      return 1
      ;;
  esac
  case "${b_out}" in
    *"${expected_summary}"*) ;;
    *)
      echo "assert_payload_validate_cwd_independent: FORM B missing non-conflated payload summary line (V4 regression)"
      return 1
      ;;
  esac

  echo "assert_payload_validate_cwd_independent: OK -- --payload is CWD-independent and reports non-conflated summary (both invocation forms green with identical [C*] verdicts under ${target})"
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

  if [ -n "${E2E_SOURCE_DIR:-}" ] && [ -d "${E2E_SOURCE_DIR}" ]; then
    rm -rf -- "${E2E_SOURCE_DIR}"
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

  # Controlled local transport: file:// upload-pack does not advertise blob
  # filters unless the source repository opts in. Use a disposable full mirror
  # so the installer exercises the real filtered/sparse path without mutating
  # this checkout's local Git configuration.
  E2E_SOURCE_DIR="$(mktemp -d)"
  E2E_SOURCE="${E2E_SOURCE_DIR}/source-repo"
  git clone --quiet "file://$(pwd)" "${E2E_SOURCE}"
  git -C "${E2E_SOURCE}" config uploadpack.allowFilter true

  # Explicitly opt in to controlled e2e-* fixture tags for the hermetic harness;
  # assert_install_tag_and_sha_pin_and_worktree_reproducibility tests the public
  # path with ALLOW_FIXTURE_TAG=0.
  export ALLOW_FIXTURE_TAG=1

  echo "e2e_bootstrap_test.sh: installing pinned tag '${EPHEMERAL_TAG}' from 'file://$(pwd)' into '${target}' (hermetic -- local file:// clone, no network)..."
  bash bootstrap.sh --repo-url "file://${E2E_SOURCE}" --tag "${EPHEMERAL_TAG}" --target "${target}"

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
  assert_install_tag_and_sha_pin_and_worktree_reproducibility "${EPHEMERAL_TAG}"
  assert_payload_validate_cwd_independent "${target}"
  assert_preflight_governance_root "${SCRATCH_DIR}"
  assert_genesis "${EPHEMERAL_TAG}"
  assert_multirepo "${EPHEMERAL_TAG}"
  assert_stage4
  assert_consumer_zero_reachback "${EPHEMERAL_TAG}"

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
      --tag "${tag}" --repo-url "file://${E2E_SOURCE}" >/dev/null 2>&1; then
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
      --tag "${tag}" --repo-url "file://${E2E_SOURCE}" >/dev/null 2>&1; then
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
        --tag "${tag}" --repo-url "file://${E2E_SOURCE}" >/dev/null 2>&1; then
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

# assert_consumer_zero_reachback <tag>
#
# Proves that a bootstrapped consumer repository can execute the full Nizam
# operational workflow (classify, preflight, trivial/small-change/bugfix
# begin+done, amend-contract, capture -> publish -> build-receipt ->
# verify-receipt -> resume, status, and validate.sh --payload) using ONLY its
# installed `.nizam/` payload, with zero reach-back to the framework source
# repository (A6 + B5).
assert_consumer_zero_reachback() {
  local tag="$1"
  local consumer="${SCRATCH_DIR}/zero-reachback-consumer"

  if ! bash bootstrap.sh --genesis --project-root "${consumer}" --project-name zero-reachback \
      --tag "${tag}" --repo-url "file://${E2E_SOURCE}" >/dev/null 2>&1; then
    echo "assert_consumer_zero_reachback: FAIL -- bootstrap.sh --genesis failed for '${consumer}'."
    return 1
  fi

  if ! PYTHONDONTWRITEBYTECODE=1 python3 - "${consumer}" <<'PY'
import hashlib
import json
import os
import pathlib
import subprocess
import sys

consumer = pathlib.Path(sys.argv[1]).resolve()
sp = consumer / ".nizam" / "tools" / "start_path.py"
wa = consumer / ".nizam" / "tools" / "workflow_assurance.py"
val = consumer / ".nizam" / "tools" / "validate.sh"

assert sp.is_file() and wa.is_file() and val.is_file(), "missing .nizam/tools entrypoints"

env = dict(os.environ)
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["NIZAM_CONSUMER_TEST"] = "1"


def git(*args: str) -> str:
    res = subprocess.run(["git", "-C", str(consumer), *args], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def run_sp(*args: str, expected_rc: int = 0, extra_env: dict | None = None) -> subprocess.CompletedProcess[str]:
    call_env = dict(env)
    if extra_env:
        call_env.update(extra_env)
    res = subprocess.run(
        [sys.executable, str(sp), *args],
        cwd=str(consumer),
        env=call_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != expected_rc:
        raise AssertionError(f"start_path {args} exited {res.returncode} (expected {expected_rc}): {res.stdout}\n{res.stderr}")
    return res


git("config", "user.email", "consumer@example.invalid")
git("config", "user.name", "Consumer Bot")
git("config", "gc.auto", "0")
git("config", "maintenance.auto", "false")
git("remote", "add", "origin", "https://example.invalid/org/zero-reachback.git")

(consumer / ".agent" / "contracts").mkdir(parents=True, exist_ok=True)
(consumer / ".agent" / "qa").mkdir(parents=True, exist_ok=True)
(consumer / ".agent" / "evidence").mkdir(parents=True, exist_ok=True)
(consumer / "docs" / "planning").mkdir(parents=True, exist_ok=True)

run_state = {
    "repository": "https://example.invalid/org/zero-reachback.git",
    "current_phase": "001-init",
    "current_feature": "triv1",
    "status": "in_progress",
    "updated_at": "2026-10-18T11:45:00Z",
    "scope_budget": {
        "original_estimate_lines": 50,
        "total_lines_changed": 0,
        "per_feature": [{"id": "001", "estimated": 50, "actual": 0}],
    },
    "circuit_breaker": {},
    "history": [{"at": "2026-10-18T11:45:00Z", "event": "genesis", "detail": "Initialized consumer repository"}],
}
(consumer / ".agent" / "run_state.json").write_text(json.dumps(run_state, indent=2) + "\n", encoding="utf-8")

(consumer / "src" / "main.py").write_text("print('main')\n", encoding="utf-8")

contract_001 = {
    "contract_id": "001",
    "feature_id": "001",
    "name": "Initial consumer feature",
    "status": "approved",
    "spec_ref": "CONTEXT.md",
    "scope": {
        "files_create": [],
        "files_modify": [
            {"path": "README.md", "purpose": "Update consumer README"},
            {"path": "src/main.py", "purpose": "Main consumer module"},
        ],
    },
    "non_goals": ["No external dependencies"],
    "verification": [
        {"acceptance_test": "test -f README.md", "command": "test -f README.md"}
    ],
    "estimated_lines": 50,
    "evidence_dir": ".agent/evidence/001/",
    "evidence_convention": ".agent/evidence/001/check.txt",
    "approvals": {
        "validator_mode_a": True,
        "evaluator_contract_review": True,
        "approved_at": "2026-10-18T11:45:00Z",
        "revisions": 1,
    },
    "dod_ref": ".nizam/standard/definition_of_done.md",
}
(consumer / ".agent" / "contracts" / "001.json").write_text(json.dumps(contract_001, indent=2) + "\n", encoding="utf-8")

feature_list = {
    "phase": "001-init",
    "spec_version": "0.1.0",
    "phase_status": "in_progress",
    "original_estimate_lines": 50,
    "features": [
        {
            "id": "001",
            "name": "Initial consumer feature",
            "description": "Initial governed consumer feature.",
            "status": "in_progress",
            "passes": False,
            "dependencies": [],
            "acceptance_tests": ["test -f README.md"],
            "estimated_lines": 50,
        }
    ],
}
(consumer / ".agent" / "feature_list.json").write_text(json.dumps(feature_list, indent=2) + "\n", encoding="utf-8")

manifest = {
    "schema_version": 1,
    "updated_at": "2026-10-18T11:45:00Z",
    "current_phase": "001-init",
    "phases": [
        {
            "id": "001-init",
            "title": "Initial Consumer Phase",
            "feature_list": ".agent/feature_list.json",
            "status": "in_progress",
        }
    ],
}
(consumer / "docs" / "planning" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

git("add", ".")
git("commit", "-qm", "initial governed consumer state")

# 1. Classify
c_triv = json.loads(run_sp("classify", "--editorial", "--files", "README.md").stdout)
assert c_triv["route"] == "trivial"
c_feat = json.loads(run_sp("classify", "--needs-new-contract", "--files", "src/PLACEHOLDER.md").stdout)
assert c_feat["route"] == "standard-feature"

# 2. Preflight
pf = json.loads(run_sp("preflight").stdout)
assert pf["ok"] is True and pf["status"] == "ready"
assert pf["capabilities"]["installed"] is True and pf["capabilities"]["operational"] is True

# 3. Trivial begin + done (plus negative rejection of .nizam/ modification)
bad_intent = {
    "id": "trivbad",
    "path": "trivial",
    "summary": "Illegal attempt to touch .nizam/",
    "needs_new_contract": False,
    "files": [".nizam/tools/start_path.py"],
}
(consumer / ".agent" / "evidence" / "trivbad-intent.json").write_text(json.dumps(bad_intent), encoding="utf-8")
run_sp("begin", "trivial", "--id", "trivbad", expected_rc=1)

# Load the consumer's installed verifier directly; no framework checkout imports.
import importlib.util
wa_spec = importlib.util.spec_from_file_location("installed_consumer_assurance", wa)
wa_api = importlib.util.module_from_spec(wa_spec)
wa_spec.loader.exec_module(wa_api)


def structured_route_proof(task_id: str) -> tuple[dict, pathlib.Path, dict]:
    check = {
        "id": "readme-exists",
        "argv": [sys.executable, "-c", "from pathlib import Path; assert Path('README.md').is_file()"],
        "expected_exit": 0,
        "proof_kind": "success",
        "diagnostic": None,
    }
    intent = {
        "id": task_id,
        "path": "trivial",
        "summary": "Verify a bounded README edit using installed tools",
        "needs_new_contract": False,
        "files": ["README.md"],
        "verification": [check],
    }
    intent_rel = f".agent/evidence/{task_id}-intent.json"
    (consumer / intent_rel).write_bytes(wa_api.canonical(intent))
    git("add", intent_rel)
    git("commit", "--only", "-qm", f"pin {task_id} verification inventory", "--", intent_rel)
    run_sp("begin", "trivial", "--id", task_id)
    readme = consumer / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + f"\nConsumer proof: {task_id}.\n", encoding="utf-8")
    base_rel = f".agent/evidence/{task_id}-base.json"
    git("add", "README.md", base_rel)
    git("commit", "--only", "-qm", f"assess {task_id} declared edit and immutable base", "--", "README.md", base_rel)
    authorization_paths = wa_api.qa_authorization_paths(consumer, task_id)
    context = wa_api.qa_context_sha256(consumer, task_id, authorization_paths, [check])
    for name, value in {
        wa_api.QA_CONTEXT_VARIABLE: context,
        wa_api.QA_EXECUTION_ROOT_VARIABLE: str(consumer),
        "NIZAM_CONSUMER_TEST": "1",
    }.items():
        os.environ[name] = value
        env[name] = value
    inputs = {
        "source": ["README.md"],
        "tests": ["src/PLACEHOLDER.md"],
        "contracts": authorization_paths,
        "tools": [
            ".nizam/tools/start_path.py",
            ".nizam/tools/workflow_assurance.py",
            ".nizam/schema/qa_verdict.schema.json",
            ".nizam/schema/contract.schema.json",
            ".nizam/schema/small_change_intent.schema.json",
        ],
        "unknown_dependencies": [],
    }
    candidate = wa_api.assess_route_candidate(
        consumer, task_id, git("rev-parse", "HEAD"), inputs,
        [wa_api.QA_CONTEXT_VARIABLE, wa_api.QA_EXECUTION_ROOT_VARIABLE, "NIZAM_CONSUMER_TEST"],
    )
    output_dir = consumer / ".agent" / "evidence" / task_id
    output_dir.mkdir()
    candidate_path = output_dir / "candidate.json"
    candidate_path.write_bytes(wa_api.canonical(candidate))
    capture = json.loads(run_sp(
        "capture", "--id", task_id, "--step", "qa", "--attempt", "1",
        "--output-dir", output_dir.relative_to(consumer).as_posix(),
        "--candidate", str(candidate_path), "--proof-kind", check["proof_kind"],
        "--agent-id", "consumer-evaluator", "--session-id", "consumer-qa-session",
        "--", *check["argv"],
    ).stdout)
    assert capture["executed"] is True and capture["exit_code"] == 0
    assert (consumer / capture["stdout"]["path"]).read_bytes() == b""
    assert (consumer / capture["stderr"]["path"]).read_bytes() == b""
    capture_ref = {
        "path": capture["capture_path"],
        "sha256": hashlib.sha256((consumer / capture["capture_path"]).read_bytes()).hexdigest(),
    }
    verdict = {
        "proof_version": 2,
        "feature_id": task_id,
        "candidate_ref": {
            "path": candidate_path.relative_to(consumer).as_posix(),
            "sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        },
        "qa_pass": True,
        "checks_run": 1,
        "checks_passed": 1,
        "checks": [{"id": check["id"], "capture": capture_ref}],
        "adversarial": {"performed": True},
        "evidence_files": [capture["capture_path"]],
        "issues": [],
        "unsupported_claims": [],
        "missing_acceptance_coverage": [],
        "required_fixes": [],
        "final_verdict": {"approved": True, "summary": "Executed installed consumer verification."},
    }
    qa_path = consumer / ".agent" / "qa" / f"{task_id}.json"
    qa_path.write_bytes(wa_api.canonical(verdict))
    # An explicitly failing declaration cannot override otherwise captured proof.
    bad = dict(verdict, qa_pass=False)
    qa_path.write_bytes(wa_api.canonical(bad))
    run_sp("done", "trivial", "--id", task_id, expected_rc=1)
    qa_path.write_bytes(wa_api.canonical(verdict))
    run_sp("done", "trivial", "--id", task_id)
    return candidate, candidate_path, intent


structured_route_proof("triv1")

# 4. Amend contract
(consumer / "src" / "helper.py").write_text("print('helper')\n", encoding="utf-8")
amend_req = {
    "contract_id": "001",
    "summary": "Add helper.py to mechanical scope",
    "invariants_preserved": True,
    "files_modify_add": [{"path": "src/helper.py", "purpose": "Helper script"}],
}
(consumer / ".agent" / "evidence" / "001-amendment.json").write_text(json.dumps(amend_req), encoding="utf-8")
git("add", "src/helper.py", ".agent")
git("commit", "-qm", "add helper and trivial records")
amend_doc = json.loads(
    run_sp(
        "amend-contract",
        "--contract",
        "001",
        "--amendment",
        ".agent/evidence/001-amendment.json",
        "--apply",
    ).stdout
)
assert amend_doc["applied"] is True and amend_doc["re_approval_required"] is False
git("add", ".agent/contracts/001.json")
git("commit", "-qm", "commit amended contract 001")

# 5. Start a fresh route after the unrelated feature amendment, then use the
# same installed, assessed candidate for actual QA and the receipt's own command.
run_state["current_feature"] = "trivreceipt"
(consumer / ".agent/run_state.json").write_bytes(wa_api.canonical(run_state))
git("add", ".agent/run_state.json")
git("commit", "-qm", "select independent receipt route")
cand_body, candidate_path, good_intent = structured_route_proof("trivreceipt")
cap_out = json.loads(
    run_sp(
        "capture", "--id", "trivreceipt", "--step", "verify", "--attempt", "1",
        "--output-dir", ".agent/evidence/trivreceipt", "--candidate", str(candidate_path),
        "--agent-id", "consumer-generator", "--session-id", "consumer-sess-1",
        "--", sys.executable, "-c", "print('CONSUMER_RECEIPT_OK')",
    ).stdout
)

# C1 & V1 check (a): default publish (no --mode) defaults to noncommitting prepare and leaves HEAD unchanged
pre_pub_head = git("rev-parse", "HEAD")
prep_out = json.loads(
    run_sp(
        "publish",
        "--capture",
        cap_out["capture_path"],
    ).stdout
)
assert prep_out["status"] == "pending_external_commit" and prep_out["stage"] == "outputs_pending"
assert git("rev-parse", "HEAD") == pre_pub_head

# C1 & V1 check (b): publish --mode publish rejects missing adapter, empty stdout, {}, and NIZAM_MUTATION_POLICY=deny without committing
run_sp(
    "publish",
    "--mode",
    "publish",
    "--capture",
    cap_out["capture_path"],
    expected_rc=1,
)
assert git("rev-parse", "HEAD") == pre_pub_head

run_sp(
    "publish",
    "--mode",
    "publish",
    "--capture",
    cap_out["capture_path"],
    expected_rc=1,
    extra_env={"NIZAM_MUTATION_ADAPTER": f"{sys.executable} -c 'pass'"},
)
assert git("rev-parse", "HEAD") == pre_pub_head

run_sp(
    "publish",
    "--mode",
    "publish",
    "--capture",
    cap_out["capture_path"],
    expected_rc=1,
    extra_env={"NIZAM_MUTATION_ADAPTER": f"{sys.executable} -c 'print(\"{{}}\")'"},
)
assert git("rev-parse", "HEAD") == pre_pub_head

run_sp(
    "publish",
    "--mode",
    "publish",
    "--capture",
    cap_out["capture_path"],
    expected_rc=1,
    extra_env={"NIZAM_MUTATION_POLICY": "deny"},
)
assert git("rev-parse", "HEAD") == pre_pub_head

# Write a consumer-local runtime mutation adapter outside the tracked consumer tree
adapter_script = consumer.parent / "consumer_mutation_adapter.py"
adapter_script.write_text(
    "import json, os, shutil, subprocess, sys, tempfile\n"
    "req = json.load(sys.stdin)\n"
    "repo = req['repository_root']\n"
    "specs = [f':(literal){f[\"path\"]}' for f in req['files']]\n"
    "git_dir = subprocess.run(['git', '-C', repo, 'rev-parse', '--absolute-git-dir'], capture_output=True, text=True, check=True).stdout.strip()\n"
    "real_idx = os.path.join(git_dir, 'index')\n"
    "fd, tmp_idx = tempfile.mkstemp(prefix='adapter-idx-')\n"
    "os.close(fd)\n"
    "os.unlink(tmp_idx)\n"
    "if os.path.exists(real_idx):\n"
    "    shutil.copy2(real_idx, tmp_idx)\n"
    "env = dict(os.environ, GIT_INDEX_FILE=tmp_idx)\n"
    "subprocess.run(['git', '-C', repo, 'read-tree', 'HEAD'], env=env, check=True)\n"
    "subprocess.run(['git', '-C', repo, 'add', '--', *specs], env=env, check=True)\n"
    "subprocess.run(['git', '-C', repo, 'commit', '-q', '-m', req['commit_message'], '--', *specs], env=env, check=True)\n"
    "subprocess.run(['git', '-C', repo, 'reset', '-q', 'HEAD', '--', *specs], check=True)\n"
    "os.unlink(tmp_idx)\n"
    "rev = subprocess.run(['git', '--no-optional-locks', '-C', repo, 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()\n"
    "print(json.dumps({'approved': True, 'status': 'committed', 'committed': True, 'revision': rev, 'commit_rev': rev}))\n",
    encoding="utf-8",
)
adapter_env = {"NIZAM_MUTATION_ADAPTER": f"{sys.executable} {adapter_script}"}

pub_out = json.loads(
    run_sp(
        "publish",
        "--mode",
        "publish",
        "--capture",
        cap_out["capture_path"],
        extra_env=adapter_env,
    ).stdout
)
assert set(pub_out["receipt_capture"].keys()) == {
    "schema_version",
    "argv",
    "cwd",
    "revision",
    "candidate_sha256",
    "environment",
    "producer",
    "executed",
    "outcome",
    "exit_code",
    "stdout",
    "stderr",
}

pin_rev = cand_body["source_commit"]
intent_ref = {
    "path": ".agent/evidence/trivreceipt-intent.json",
    "sha256": hashlib.sha256((consumer / ".agent" / "evidence" / "trivreceipt-intent.json").read_bytes()).hexdigest(),
    "revision": pin_rev,
}
qa_triv_doc = json.loads((consumer / ".agent" / "qa" / "trivreceipt.json").read_text(encoding="utf-8"))
qa_triv_doc["reviewed_revision"] = pin_rev
qa_triv_doc["intent_sha256"] = intent_ref["sha256"]
qa_triv_doc["reviewer"] = "consumer-evaluator"
(consumer / ".agent" / "qa" / "trivreceipt.json").write_text(
    json.dumps(qa_triv_doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
)
git("add", ".agent/qa/trivreceipt.json")
git("commit", "-qm", "pin trivial qa with exact intent revision")
qa_rev = git("rev-parse", "HEAD")
qa_ref = {
    "path": ".agent/qa/trivreceipt.json",
    "sha256": hashlib.sha256((consumer / ".agent" / "qa" / "trivreceipt.json").read_bytes()).hexdigest(),
    "revision": qa_rev,
}

policy_doc = {
    "schema_version": 1,
    "repository": "https://example.invalid/org/zero-reachback.git",
    "feature_id": "trivreceipt",
    "stage": "trivial-complete",
    "operation_id": "consumer-op-trivreceipt",
    "candidate": cand_body,
    "producer": {"agent_id": "consumer-generator", "session_id": "consumer-sess-1"},
    "contract": intent_ref,
    "operator": intent_ref,
    "prerequisites": [
        {
            "kind": "route-intent",
            "artifact": intent_ref,
            "feature_id": "trivreceipt",
            "assessed_revision": pin_rev,
            "contract_sha256": intent_ref["sha256"],
        },
        {
            "kind": "route-qa",
            "artifact": qa_ref,
            "feature_id": "trivreceipt",
            "assessed_revision": pin_rev,
            "contract_sha256": intent_ref["sha256"],
        },
    ],
    "commands": [
        {
            "argv": [sys.executable, "-c", "print('CONSUMER_RECEIPT_OK')"],
            "expected_exit": 0,
            "proof_kind": "success",
            "diagnostic": "CONSUMER_RECEIPT_OK",
            "capture": pub_out["receipt_capture_ref"],
        }
    ],
    "from_status": "in_progress",
    "to_status": "complete",
    "at": "2026-10-18T11:50:00Z",
    "recovery": None,
}
policy_path = consumer / ".agent" / "evidence" / "trivreceipt" / "policy.json"
policy_path.write_text(json.dumps(policy_doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
git("add", ".agent/evidence/trivreceipt/policy.json")
git("commit", "-qm", "commit consumer receipt policy")

# V1 check (c): build-receipt without --commit rejects uncommitted 12-field closed capture without committing
pre_br_head = git("rev-parse", "HEAD")
receipt_path = consumer / ".agent" / "evidence" / "trivreceipt" / "receipt.json"
uncommitted_closed = consumer / ".agent" / "evidence" / "trivreceipt" / "uncommitted.receipt-capture.json"
uncommitted_closed.write_text(
    json.dumps(pub_out["receipt_capture"], sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
run_sp(
    "build-receipt",
    "--policy",
    str(policy_path),
    "--published",
    str(uncommitted_closed),
    "--output",
    str(receipt_path),
    expected_rc=1,
)
assert git("rev-parse", "HEAD") == pre_br_head
uncommitted_closed.unlink()

build_res = json.loads(
    run_sp(
        "build-receipt",
        "--policy",
        str(policy_path),
        "--published",
        pub_out["published_path"],
        "--output",
        str(receipt_path),
        "--commit",
        extra_env=adapter_env,
    ).stdout
)
assert build_res["verified"] is True

wa_verify = subprocess.run(
    [
        sys.executable,
        str(wa),
        "verify-receipt",
        "--root",
        str(consumer),
        "--policy",
        str(policy_path),
        "--receipt",
        str(receipt_path),
    ],
    cwd=str(consumer),
    env=env,
    capture_output=True,
    text=True,
    check=False,
)
assert wa_verify.returncode == 0, f"verify-receipt failed: {wa_verify.stdout}\n{wa_verify.stderr}"

# Canonical default state advances once and replays without any scope exemption
# for unrelated edits. The supported explicit task-owned state is exercised too.
canonical_before = (consumer / ".agent/run_state.json").read_bytes()
res1 = json.loads(run_sp("resume", "--policy", str(policy_path), "--receipt", str(receipt_path), "--apply").stdout)
assert res1["action"] == "advance" and res1["applied"] is True
res2 = json.loads(run_sp("resume", "--policy", str(policy_path), "--receipt", str(receipt_path), "--apply").stdout)
assert res2["action"] == "noop" and res2["applied"] is False
canonical_after = (consumer / ".agent/run_state.json").read_bytes()
assert json.loads(canonical_after)["status"] == "complete"
run_sp("done", "trivial", "--id", "trivreceipt", expected_rc=1)
runtime_state = consumer / ".agent/evidence/trivreceipt/runtime-state.json"
runtime_state.write_bytes(canonical_before)
explicit1 = json.loads(run_sp("resume", "--policy", str(policy_path), "--receipt", str(receipt_path), "--state", str(runtime_state), "--apply").stdout)
assert explicit1["action"] == "advance" and explicit1["applied"] is True
explicit2 = json.loads(run_sp("resume", "--policy", str(policy_path), "--receipt", str(receipt_path), "--state", str(runtime_state), "--apply").stdout)
assert explicit2["action"] == "noop"
assert (consumer / ".agent/run_state.json").read_bytes() == canonical_after

# 6. Status view
st = json.loads(run_sp("status", "--format", "json").stdout)
assert st["reconciled"] is True and st["contradictions"] == []

# 7. Payload validation from consumer root (including V4 non-conflated summary check)
val_res = subprocess.run(["bash", ".nizam/tools/validate.sh", "--payload"], cwd=str(consumer), env=env, capture_output=True, text=True, check=False)
assert val_res.returncode == 0, f"validate.sh --payload failed: {val_res.stdout}\n{val_res.stderr}"
assert "SUMMARY (payload mode): 10 exercised passed, 0 failed, 2 not-applicable (C11, C16), 1 skipped (C6), 3 out-of-scope (C12, C14, C15); content_integrity=not_checked, operational_acceptance=not_assessed" in val_res.stdout
PY
  then
    echo "assert_consumer_zero_reachback: FAIL -- consumer zero-reach-back lifecycle exercise failed."
    return 1
  fi

  echo "assert_consumer_zero_reachback: OK -- consumer project executed classify, preflight, trivial begin/done, amend-contract, capture/publish(prepare+deny+publish)/build-receipt/verify-receipt/resume, status, and validate.sh --payload using only .nizam/ with zero reach-back."
  return 0
}

# Direct-execution guard: `main "$@"` runs ONLY when this file is executed
# directly (e.g. `bash tools/e2e_bootstrap_test.sh`), never when it is merely
# `source`d -- so sourcing this file for fixture-testing its functions never
# triggers a real clone, tag, or scratch directory.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
