#!/usr/bin/env bash
#
# bootstrap.sh -- Nizam Governance Inheritance Protocol (GIP) bootstrap.
#
# The unified clone -> inject -> verify mechanism described in standard/GIP.md.
# This is an evolution of the earlier AGIP (the earlier governance prototype this
# framework evolved from) into a single, reusable, runtime-agnostic script any
# consumer repository can invoke directly instead of hand-reimplementing the
# GIP Section 2 inheritance sequence.
#
# It clones a pinned semantic-version git tag of the nizam-framework
# governance payload, stages it in a temporary directory, injects standard/,
# templates/, schema/, tools/, methodology/, ecosystem/, and NIZAM.json into a consumer-declared target
# directory (".nizam/" by default), verifies the injection before declaring
# success, records provenance, and only then atomically replaces any prior
# target contents.
#
# Usage:
#   ./bootstrap.sh [--repo-url URL] [--tag TAG] [--target DIR]
#   ./bootstrap.sh --verify-only [--tag TAG] [--target DIR]
#   ./bootstrap.sh --genesis --project-root DIR [--project-name NAME] [--tag TAG]
#   ./bootstrap.sh --help
#
# The --genesis mode stands up a NEW project from nothing (the 0-case of the
# 0-to-n project spectrum, ecosystem/00_ecosystem_bootstrap.md Section 8): it
# git-inits an empty --project-root, scaffolds a minimal deterministic skeleton
# (README, a CONTEXT.md consumer-inputs stub, a source placeholder), then runs
# the normal clone -> inject -> verify -> provenance install into
# <project-root>/.nizam. It refuses a non-empty --project-root (that is a
# brownfield adoption, not a genesis).
#
# Configuration (environment variable, overridable by the matching CLI flag):
#   GOVERNANCE_REPO_URL   Source git repository of the governance payload.
#   GOVERNANCE_TAG        Pinned semantic-version git tag to install or verify
#                         against. REQUIRED and never defaulted: "", "main",
#                         "master", "HEAD", and any "refs/heads/*" reference
#                         are all refused, because a floating branch reference
#                         is never an acceptable inheritance pin (GIP Section
#                         2, point 1).
#   NIZAM_TARGET_DIR      Injection target directory. Defaults to ".nizam".
#
set -euo pipefail

readonly SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
readonly DEFAULT_GOVERNANCE_REPO_URL="https://github.com/niq-cnr/nizam-framework.git"
readonly DEFAULT_TARGET_DIR=".nizam"

# The minimum required-file set per standard/GIP.md Section 2.1: the four
# standard/ documents and the schema/frontmatter.schema.json validation
# target, plus the root capability index itself, plus a representative
# document from each of methodology/ and ecosystem/ (which joined the
# injected payload in phase-006 feature 051, the H-PAYLOAD-CONTRACT decision).
readonly REQUIRED_RELATIVE_FILES=(
  "standard/NDS.md"
  "standard/GIP.md"
  "standard/AGF.md"
  "standard/anti_hallucination.md"
  "schema/frontmatter.schema.json"
  "methodology/00_planning.md"
  "ecosystem/README.md"
  "NIZAM.json"
)

# The governance module directories injected as one atomic operation.
# methodology/ and ecosystem/ joined this set in phase-006 feature 051
# (H-PAYLOAD-CONTRACT): consumer payloads previously omitted them, so the
# numerous tools/skill.json + tools/SKILL.md cross-references into
# methodology/ (and the ecosystem/ references added in F-040) dangled in a
# real .nizam/ install (NDEBT-008). registry/ and docs/ remain
# framework-envelope and are NOT injected.
readonly REQUIRED_MODULE_DIRS=(
  "standard"
  "templates"
  "schema"
  "tools"
  "methodology"
  "ecosystem"
)

GOVERNANCE_REPO_URL="${GOVERNANCE_REPO_URL:-${DEFAULT_GOVERNANCE_REPO_URL}}"
GOVERNANCE_TAG="${GOVERNANCE_TAG:-}"
TARGET_DIR="${NIZAM_TARGET_DIR:-${DEFAULT_TARGET_DIR}}"
# Set to 1 by --target/--target= so --genesis knows whether the caller pinned an
# explicit payload location or wants the default <project-root>/.nizam.
TARGET_EXPLICIT=0
VERIFY_ONLY=0
# Greenfield-genesis mode (feature 071, NDEBT-030; ecosystem/00 Section 8): create
# and scaffold a NEW project at --project-root, then inject the payload into it.
GENESIS=0
PROJECT_ROOT=""
PROJECT_NAME=""
# Optional caller-supplied expected commit SHA (feature 067, NDEBT-033). When set,
# both install mode and --verify-only require the resolved/recorded commit SHA to
# equal this 40-hex digest before installing or accepting the payload.
EXPECTED_SHA="${EXPECTED_SHA:-}"
# Controlled test-only fixture tag override (--allow-fixture-tag or ALLOW_FIXTURE_TAG=1)
# permitting ephemeral ^e2e-[0-9A-Za-z._-]+$ tags in tools/e2e_bootstrap_test.sh.
ALLOW_FIXTURE_TAG="${ALLOW_FIXTURE_TAG:-0}"
# Optional unpacked release source root for --verify-only unbound directory comparison.
SOURCE_ROOT="${SOURCE_ROOT:-}"
# Optional local git repository containing the pinned tag/commit for --verify-only
# (or destination to retain the verified shallow tag clone at install time).
GIT_REPO="${GIT_REPO:-}"
# Require a reachable commit-bound reference tree for --verify-only content-integrity verification.
REQUIRE_CONTENT_INTEGRITY=0
# Explicitly request structural-only verification when no reference tree is supplied.
STRUCTURAL_ONLY=0

# Tracked temp/backup paths for the cleanup trap. Cleared once ownership of a
# directory transfers away from the tracker (e.g. after a successful atomic
# move), so cleanup never deletes something it no longer owns.
CLONE_DIR=""
STAGE_DIR=""
REPLACED_OLD_DIR=""
TEMP_VERIFIER=""
# A --project-root this run created (genesis mode). Removed by cleanup if a
# genesis fails partway, so a failed genesis never leaves a half-built project
# behind; cleared on success once the project owns itself. A pre-existing empty
# --project-root is never tracked here (we did not create it, so we never delete it).
CREATED_PROJECT_ROOT=""

print_usage() {
  cat <<'USAGE'
Usage: bootstrap.sh [OPTIONS]

Inherit, or verify inheritance of, the Nizam governance payload (standard/,
templates/, schema/, tools/, methodology/, ecosystem/, NIZAM.json) into this
repository, per standard/GIP.md (Governance Inheritance Protocol).

Modes:
  (default)         Fetch the pinned refs/tags/<GOVERNANCE_TAG>, verify any
                     supplied --expected-sha before staging, stage the
                     governance payload in a temp directory, verify it, record
                     provenance, and atomically install it under the target
                     directory (optionally retaining the verified tag clone at
                     --git-repo DIR).
  --verify-only      Drift and content-integrity check against an already-injected
                     target directory: confirms the target exists, its
                     NIZAM.json parses, every path it indexes resolves on
                     disk, its recorded provenance tag matches the expected
                     pinned tag, its recorded commit SHA is present (and,
                     with --expected-sha, matches), and:
                       - with --git-repo DIR and --expected-sha SHA (and
                         optional --require-content-integrity), loads the
                         trusted verifier outside the target and verifies the
                         full released file inventory, blob digests, and
                         executable modes against that commit tree
                         (content_integrity=verified);
                       - with --source-root DIR alone, compares inventory,
                         modes, and bytes against an unbound directory
                         (content_integrity=directory_match_unbound);
                       - with neither reference flag (or --structural-only),
                         reports structural_only (content_integrity=not_checked).
  --genesis          Greenfield genesis (the 0-case, ecosystem/00 Section 8):
                     stand up a NEW project from nothing. git-inits an empty
                     --project-root, scaffolds a minimal deterministic skeleton
                     (README, a CONTEXT.md consumer-inputs stub, a source
                     placeholder), then performs the normal install into
                     <project-root>/.nizam. Refuses a non-empty --project-root
                     (a brownfield adoption, not a genesis). Requires
                     --project-root; mutually exclusive with --verify-only.
  --help, -h         Print this usage text and exit 0. Network-free.

Options:
  --repo-url URL     Override GOVERNANCE_REPO_URL for this invocation.
  --tag TAG          Override GOVERNANCE_TAG for this invocation. Must be a
                     pinned semantic-version release tag (vMAJOR.MINOR.PATCH)
                     resolved strictly via refs/tags/<TAG>. Floating branches
                     ("", "main", "master", "HEAD", "refs/heads/*", or any
                     branch-only ref) are refused.
  --target DIR       Override the injection target directory (default: .nizam,
                     or <project-root>/.nizam in --genesis mode).
  --project-root DIR (--genesis only) The new project's root to create and
                     scaffold. Must not already exist as a non-empty directory.
  --project-name NAME (--genesis only) Name used in the scaffold (default: the
                     basename of --project-root).
  --expected-sha SHA The 40-hex commit SHA the pinned tag must resolve to.
                     Enforced at install time BEFORE staging or replacing the
                     target directory, and in --verify-only (with --git-repo)
                     against recorded provenance and the reference commit tree.
  --git-repo DIR     In install mode, retain the verified tag repository clone
                     at DIR (outside --target). In --verify-only mode (required
                     with --expected-sha / --require-content-integrity), local
                     Git repository outside --target containing the expected
                     tag/commit object.
  --source-root DIR  (--verify-only) Unpacked directory outside --target to
                     compare installed file inventory, modes, and bytes against
                     (reports content_integrity=directory_match_unbound; cannot
                     satisfy --expected-sha or --require-content-integrity).
  --require-content-integrity
                     (--verify-only) Require commit-bound content-integrity
                     verification via --git-repo DIR and --expected-sha SHA.
  --structural-only  (--verify-only) Perform structural/provenance checks only
                     without claiming content-integrity verification; incompatible
                     with --expected-sha, --require-content-integrity, --git-repo,
                     and --source-root.

Environment variables (overridden by the matching flag above when both are given):
  GOVERNANCE_REPO_URL   Source repository of the governance payload.
  GOVERNANCE_TAG        Pinned tag to install or to verify against.
  NIZAM_TARGET_DIR      Injection target directory.
  EXPECTED_SHA          Expected 40-hex commit SHA for install and --verify-only.
  GIT_REPO              Local Git repository path for install retention or --verify-only.

Exit status:
  0   Success (including --help and a passing --verify-only run).
  1   Configuration error, verification failure, or clone/injection failure.
USAGE
}

# Writes a clearly labelled error message to stderr and exits non-zero. Every
# failure path in this script routes through here so no failure is silent.
die() {
  echo "${SCRIPT_NAME}: error: $*" >&2
  exit 1
}

log() {
  echo "${SCRIPT_NAME}: $*"
}

# Removes every temp/backup directory this run still owns. Registered against
# EXIT and ERR so a failed run -- at any step -- never leaves a partial stage
# or an orphaned clone behind, and never leaves the target directory missing
# if a prior copy had to be moved aside to make room for a new one.
cleanup() {
  local exit_code=$?
  if [ -n "${TEMP_VERIFIER}" ] && [ -f "${TEMP_VERIFIER}" ]; then
    rm -f -- "${TEMP_VERIFIER}"
  fi
  if [ -n "${STAGE_DIR}" ] && [ -d "${STAGE_DIR}" ]; then
    rm -rf -- "${STAGE_DIR}"
  fi
  if [ -n "${CLONE_DIR}" ] && [ -d "${CLONE_DIR}" ]; then
    rm -rf -- "${CLONE_DIR}"
  fi
  if [ -n "${REPLACED_OLD_DIR}" ] && [ -d "${REPLACED_OLD_DIR}" ]; then
    if [ ! -d "${TARGET_DIR}" ]; then
      # The previous target was moved aside but the new stage never took its
      # place: restore it so a failed run never leaves zero governance
      # directories in place.
      mv -- "${REPLACED_OLD_DIR}" "${TARGET_DIR}"
    else
      rm -rf -- "${REPLACED_OLD_DIR}"
    fi
  fi
  if [ -n "${CREATED_PROJECT_ROOT}" ] && [ -d "${CREATED_PROJECT_ROOT}" ]; then
    # A genesis created this project root and then failed before completing:
    # remove it so a failed genesis leaves nothing half-built. Only ever set
    # for a root THIS run created (never a pre-existing directory).
    rm -rf -- "${CREATED_PROJECT_ROOT}"
  fi
  return "${exit_code}"
}

trap cleanup EXIT ERR

# Refuses any tag value that is empty, a floating branch reference, or not a
# pinned semantic-version release tag (unless --allow-fixture-tag / ALLOW_FIXTURE_TAG=1
# is explicitly set for a controlled ^e2e-* test tag).
require_pinned_tag() {
  local tag="$1"
  case "${tag}" in
    ''|main|master|HEAD|refs/heads/*|refs/tags/*)
      die "GOVERNANCE_TAG must be a pinned semantic-version tag name (e.g. v1.8.0), not '${tag}'. A floating branch reference (main, master, HEAD, refs/heads/*) is never accepted (standard/GIP.md Section 2, point 1). Pass --tag <tag> or set GOVERNANCE_TAG."
      ;;
  esac
  if [ "${ALLOW_FIXTURE_TAG}" = "1" ] && [[ "${tag}" =~ ^e2e-[0-9A-Za-z._-]+$ ]]; then
    return 0
  fi
  if [[ ! "${tag}" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$ ]]; then
    die "GOVERNANCE_TAG '${tag}' is not a valid pinned semantic-version release tag (expected vMAJOR.MINOR.PATCH, standard/GIP.md Section 2, point 1)."
  fi
}

require_valid_expected_sha() {
  local sha="$1"
  if [ -n "${sha}" ] && [[ ! "${sha}" =~ ^[0-9a-f]{40}$ ]]; then
    die "--expected-sha must be a 40-character lowercase hexadecimal commit SHA, got '${sha}'."
  fi
}

require_command() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || die "required command '${cmd}' not found on PATH."
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --help|-h)
        print_usage
        exit 0
        ;;
      --verify-only)
        VERIFY_ONLY=1
        shift
        ;;
      --genesis)
        GENESIS=1
        shift
        ;;
      --allow-fixture-tag)
        ALLOW_FIXTURE_TAG=1
        shift
        ;;
      --require-content-integrity)
        REQUIRE_CONTENT_INTEGRITY=1
        shift
        ;;
      --structural-only)
        STRUCTURAL_ONLY=1
        shift
        ;;
      --source-root)
        [ "$#" -ge 2 ] || die "--source-root requires an argument."
        SOURCE_ROOT="$2"
        shift 2
        ;;
      --source-root=*)
        SOURCE_ROOT="${1#--source-root=}"
        shift
        ;;
      --git-repo)
        [ "$#" -ge 2 ] || die "--git-repo requires an argument."
        GIT_REPO="$2"
        shift 2
        ;;
      --git-repo=*)
        GIT_REPO="${1#--git-repo=}"
        shift
        ;;
      --project-root)
        [ "$#" -ge 2 ] || die "--project-root requires an argument."
        PROJECT_ROOT="$2"
        shift 2
        ;;
      --project-root=*)
        PROJECT_ROOT="${1#--project-root=}"
        shift
        ;;
      --project-name)
        [ "$#" -ge 2 ] || die "--project-name requires an argument."
        PROJECT_NAME="$2"
        shift 2
        ;;
      --project-name=*)
        PROJECT_NAME="${1#--project-name=}"
        shift
        ;;
      --repo-url)
        [ "$#" -ge 2 ] || die "--repo-url requires an argument."
        GOVERNANCE_REPO_URL="$2"
        shift 2
        ;;
      --repo-url=*)
        GOVERNANCE_REPO_URL="${1#--repo-url=}"
        shift
        ;;
      --tag)
        [ "$#" -ge 2 ] || die "--tag requires an argument."
        GOVERNANCE_TAG="$2"
        shift 2
        ;;
      --tag=*)
        GOVERNANCE_TAG="${1#--tag=}"
        shift
        ;;
      --target)
        [ "$#" -ge 2 ] || die "--target requires an argument."
        TARGET_DIR="$2"
        TARGET_EXPLICIT=1
        shift 2
        ;;
      --target=*)
        TARGET_DIR="${1#--target=}"
        TARGET_EXPLICIT=1
        shift
        ;;
      --expected-sha)
        [ "$#" -ge 2 ] || die "--expected-sha requires an argument."
        EXPECTED_SHA="$2"
        shift 2
        ;;
      --expected-sha=*)
        EXPECTED_SHA="${1#--expected-sha=}"
        shift
        ;;
      *)
        die "unrecognized argument: $1 (see --help)"
        ;;
    esac
  done
}

# Confirms candidate path $1 is NOT equal to or inside root path $2.
assert_outside_target() {
  local candidate="$1"
  local target_root="$2"
  local label="$3"
  if ! python3 - "${candidate}" "${target_root}" <<'PYEOF'
import os
import sys

cand = os.path.realpath(sys.argv[1])
targ = os.path.realpath(sys.argv[2])
if cand == targ or cand.startswith(targ + os.sep):
    sys.exit(1)
sys.exit(0)
PYEOF
  then
    die "${label} '${candidate}' must be outside target directory '${target_root}'."
  fi
}

# Confirms the minimum required-file set (standard/GIP.md Section 2.1) is
# present and non-empty under the given root (a stage directory pre-move, or
# the live target directory in --verify-only mode).
check_required_files() {
  local root="$1"
  local rel
  for rel in "${REQUIRED_RELATIVE_FILES[@]}"; do
    if [ ! -s "${root}/${rel}" ]; then
      die "required governance file missing or empty under '${root}': ${rel}"
    fi
  done
}

# Confirms NIZAM.json parses as valid JSON and every path it indexes that
# falls under an actually-injected module (standard/, templates/, schema/,
# tools/, methodology/, ecosystem/ -- see REQUIRED_MODULE_DIRS) resolves to a
# real, non-empty file under the given root. NIZAM.json also indexes the
# framework-envelope-only registry/ and docs/ modules, which this script
# deliberately does not inject into consumers (product_spec.md Section 5;
# methodology/ and ecosystem/ joined the injected payload in feature 051);
# paths under those two non-injected modules are excluded from this check.
check_nizam_index() {
  local root="$1"
  if ! python3 - "${root}" <<'PYEOF'
import json
import os
import sys

root = sys.argv[1]
nizam_path = os.path.join(root, "NIZAM.json")

try:
    with open(nizam_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, json.JSONDecodeError) as exc:
    print(f"NIZAM.json failed to parse under {root}: {exc}", file=sys.stderr)
    sys.exit(1)

injected_module_paths = {"standard", "templates", "schema", "tools", "methodology", "ecosystem"}


def is_injected(rel_path):
    return rel_path.split("/", 1)[0] in injected_module_paths


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
if self_reference_path:
    indexed_paths.add(self_reference_path)

missing = [
    rel for rel in sorted(indexed_paths)
    if not os.path.isfile(os.path.join(root, rel))
]

if missing:
    print(
        "indexed path(s) failed to resolve under " + root + ": " + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)

print(f"NIZAM.json parses; {len(indexed_paths)} indexed path(s) resolve under {root}.")
PYEOF
  then
    die "NIZAM.json parse or indexed-path verification failed under '${root}' (see stderr above)."
  fi
}

# Compares provenance.json's recorded tag (and its recorded resolved commit SHA)
# against the expected pinned tag and, when supplied, an expected commit SHA. A
# mismatch is drift (standard/GIP.md Section 4): the correct remediation is
# re-running this script against the expected tag, never hand-patching.
#
# resolved_sha (feature 067, NDEBT-033) makes the pin an immutable commit, not just
# a tag NAME: the SHA is always required present (a payload predating this feature
# has none and is correctly rejected as drift, prompting a re-bootstrap), and when
# the caller passes an expected SHA (--expected-sha, resolved out-of-band from the
# authentic tag) it MUST equal the recorded one -- so a moved remote tag replaying a
# different commit under the same tag name is rejected even though the tag string
# matches. --verify-only stays network-free: it never re-resolves the tag itself.
check_provenance_pin() {
  local root="$1"
  local expected_tag="$2"
  local expected_sha="$3"
  local provenance_path="${root}/provenance.json"
  [ -s "${provenance_path}" ] || die "provenance.json missing or empty under '${root}' -- cannot verify the recorded framework tag."
  local recorded_tag recorded_sha
  recorded_tag="$(python3 -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle).get("tag", ""))
' "${provenance_path}")" || die "provenance.json failed to parse under '${root}'."
  recorded_sha="$(python3 -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle).get("resolved_sha", ""))
' "${provenance_path}")" || die "provenance.json failed to parse under '${root}'."
  if [ "${recorded_tag}" != "${expected_tag}" ]; then
    die "drift detected: provenance.json under '${root}' records tag '${recorded_tag}' but the expected pinned tag is '${expected_tag}' (standard/GIP.md Section 4 -- re-bootstrap against the expected tag; do not hand-patch)."
  fi
  if [ -z "${recorded_sha}" ]; then
    die "provenance.json under '${root}' records no resolved_sha -- it predates the commit-SHA pin (NDEBT-033). Re-bootstrap against tag '${expected_tag}' to record an immutable commit pin (standard/GIP.md Section 4)."
  fi
  if [ -n "${expected_sha}" ] && [ "${recorded_sha}" != "${expected_sha}" ]; then
    die "drift detected: provenance.json under '${root}' records resolved_sha '${recorded_sha}' but the expected commit SHA is '${expected_sha}' -- the tag '${expected_tag}' resolved to a DIFFERENT commit at install time than the one expected now (a moved tag). Re-bootstrap against the authentic tag (standard/GIP.md Section 4)."
  fi
}

# --verify-only: a pure, network-free drift and content-integrity check against an
# already-injected target directory. Clones nothing and writes nothing inside the target.
run_verify_only() {
  require_pinned_tag "${GOVERNANCE_TAG}"
  require_valid_expected_sha "${EXPECTED_SHA}"
  require_command python3
  if [ "${STRUCTURAL_ONLY}" -eq 1 ] && { [ -n "${EXPECTED_SHA}" ] || [ "${REQUIRE_CONTENT_INTEGRITY}" -eq 1 ] || [ -n "${GIT_REPO}" ] || [ -n "${SOURCE_ROOT}" ]; }; then
    die "--structural-only cannot be combined with --expected-sha, --require-content-integrity, --git-repo, or --source-root."
  fi
  if [ -n "${SOURCE_ROOT}" ] && { [ -n "${EXPECTED_SHA}" ] || [ "${REQUIRE_CONTENT_INTEGRITY}" -eq 1 ] || [ -n "${GIT_REPO}" ]; }; then
    die "--source-root performs an unbound directory comparison (directory_match_unbound) and cannot satisfy --expected-sha, --require-content-integrity, or --git-repo; supply --git-repo DIR and --expected-sha SHA for commit-bound verification."
  fi
  if { [ -n "${GIT_REPO}" ] || [ -n "${EXPECTED_SHA}" ] || [ "${REQUIRE_CONTENT_INTEGRITY}" -eq 1 ]; } && { [ -z "${GIT_REPO}" ] || [ -z "${EXPECTED_SHA}" ]; }; then
    die "--verify-only content-integrity verification requires both --git-repo DIR and --expected-sha SHA (never derived solely from mutable provenance.json or ambient working directory)."
  fi

  [ -d "${TARGET_DIR}" ] || die "--verify-only: target directory '${TARGET_DIR}' does not exist -- nothing to verify. Run bootstrap.sh in default (install) mode first."
  log "verify-only: checking '${TARGET_DIR}' against pinned tag '${GOVERNANCE_TAG}' (no clone, no network)..."
  check_required_files "${TARGET_DIR}"
  check_nizam_index "${TARGET_DIR}"
  check_provenance_pin "${TARGET_DIR}" "${GOVERNANCE_TAG}" "${EXPECTED_SHA}"

  if [ "${STRUCTURAL_ONLY}" -eq 1 ] || { [ -z "${GIT_REPO}" ] && [ -z "${SOURCE_ROOT}" ]; }; then
    log "verify-only: PASS (structural_only; content_integrity=not_checked) -- '${TARGET_DIR}' required files, index paths, and recorded provenance tag '${GOVERNANCE_TAG}' verified; file bytes and complete inventory were not compared against a reference tree."
    return 0
  fi

  local -a integrity_args=(
    "--payload-dir=${TARGET_DIR}"
    "--expected-tag=${GOVERNANCE_TAG}"
  )

  if [ -n "${GIT_REPO}" ]; then
    require_command git
    if [ -L "${GIT_REPO}" ] || [ ! -d "${GIT_REPO}" ]; then
      die "--verify-only: --git-repo '${GIT_REPO}' does not exist as a real directory."
    fi
    assert_outside_target "${GIT_REPO}" "${TARGET_DIR}" "--git-repo"
    if ! git -C "${GIT_REPO}" cat-file -e "${EXPECTED_SHA}^{commit}" 2>/dev/null; then
      die "--verify-only: expected commit '${EXPECTED_SHA}' is not present in --git-repo '${GIT_REPO}'."
    fi
    integrity_args+=(
      "--git-repo=${GIT_REPO}"
      "--expected-sha=${EXPECTED_SHA}"
      "--require-reference-tree"
    )
  elif [ -n "${SOURCE_ROOT}" ]; then
    if [ -L "${SOURCE_ROOT}" ] || [ ! -d "${SOURCE_ROOT}" ]; then
      die "--verify-only: --source-root '${SOURCE_ROOT}' does not exist as a real directory."
    fi
    assert_outside_target "${SOURCE_ROOT}" "${TARGET_DIR}" "--source-root"
    integrity_args+=("--source-root=${SOURCE_ROOT}")
  fi

  # Never execute code inside ${TARGET_DIR} to decide whether ${TARGET_DIR} is genuine.
  # Load verifier logic from an independently trusted source outside ${TARGET_DIR}
  # or from the verified Git object ${EXPECTED_SHA}:tools/payload_integrity.py in --git-repo.
  local integrity_script=""
  local script_root
  script_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  if [ -f "${script_root}/tools/payload_integrity.py" ] && python3 - "${script_root}" "${TARGET_DIR}" <<'PYEOF'
import os
import sys

sr = os.path.realpath(sys.argv[1])
td = os.path.realpath(sys.argv[2])
sys.exit(1 if (sr == td or sr.startswith(td + os.sep)) else 0)
PYEOF
  then
    integrity_script="${script_root}/tools/payload_integrity.py"
  elif [ -n "${GIT_REPO}" ]; then
    TEMP_VERIFIER="$(mktemp "${TMPDIR:-/tmp}/nizam-payload-integrity.XXXXXX")"
    if ! git -C "${GIT_REPO}" show "${EXPECTED_SHA}:tools/payload_integrity.py" > "${TEMP_VERIFIER}" 2>/dev/null || [ ! -s "${TEMP_VERIFIER}" ]; then
      die "--verify-only: unable to load trusted tools/payload_integrity.py from commit '${EXPECTED_SHA}' in --git-repo '${GIT_REPO}'."
    fi
    integrity_script="${TEMP_VERIFIER}"
  elif [ -n "${SOURCE_ROOT}" ] && [ -f "${SOURCE_ROOT}/tools/payload_integrity.py" ]; then
    integrity_script="${SOURCE_ROOT}/tools/payload_integrity.py"
  else
    die "--verify-only: no trusted tools/payload_integrity.py available outside '${TARGET_DIR}'."
  fi

  local pi_out pi_rc
  if pi_out="$(PYTHONDONTWRITEBYTECODE=1 python3 "${integrity_script}" "${integrity_args[@]}" 2>&1)"; then
    pi_rc=0
  else
    pi_rc=$?
  fi

  if [ "${pi_rc}" -ne 0 ]; then
    die "verify-only content-integrity check failed for '${TARGET_DIR}': ${pi_out}"
  fi

  if [ -n "${SOURCE_ROOT}" ]; then
    log "verify-only: PASS (directory_match_unbound; content_integrity=directory_match_unbound) -- '${TARGET_DIR}' matches unbound directory '${SOURCE_ROOT}'; commit tree not verified (${pi_out})."
    return 0
  fi

  log "verify-only: PASS (content_integrity=verified) -- '${TARGET_DIR}' matches pinned tag '${GOVERNANCE_TAG}' at '${EXPECTED_SHA}' (${pi_out})."
  return 0
}

# Default mode: fetch the explicit refs/tags/<GOVERNANCE_TAG> ref, verify
# --expected-sha before staging, stage, inject, verify, record provenance,
# then atomically install -- as one operation, per standard/GIP.md Section 2.1.
run_install() {
  require_pinned_tag "${GOVERNANCE_TAG}"
  require_valid_expected_sha "${EXPECTED_SHA}"
  require_command git
  require_command python3
  if [ -n "${GIT_REPO}" ]; then
    assert_outside_target "${GIT_REPO}" "${TARGET_DIR}" "--git-repo"
  fi

  local remote_refs
  remote_refs="$(git ls-remote "${GOVERNANCE_REPO_URL}" "refs/tags/${GOVERNANCE_TAG}" "refs/tags/${GOVERNANCE_TAG}^{}" "refs/heads/${GOVERNANCE_TAG}" 2>/dev/null)" \
    || die "unable to query refs from '${GOVERNANCE_REPO_URL}'. Confirm the repository URL is reachable."
  if ! printf '%s\n' "${remote_refs}" | grep -q "	refs/tags/${GOVERNANCE_TAG}$"; then
    die "pinned tag 'refs/tags/${GOVERNANCE_TAG}' does not exist in '${GOVERNANCE_REPO_URL}'. Branch-only or untagged refs are never accepted (standard/GIP.md Section 2, point 1)."
  fi
  if printf '%s\n' "${remote_refs}" | grep -q "	refs/heads/${GOVERNANCE_TAG}$"; then
    die "ambiguous ref '${GOVERNANCE_TAG}' in '${GOVERNANCE_REPO_URL}': branch 'refs/heads/${GOVERNANCE_TAG}' collides with tag 'refs/tags/${GOVERNANCE_TAG}'. Refusing ambiguous tag/branch resolution."
  fi

  CLONE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/nizam-bootstrap-clone.XXXXXX")"
  log "fetching ${GOVERNANCE_REPO_URL} at explicit tag ref refs/tags/${GOVERNANCE_TAG} (--depth 1)..."
  git -C "${CLONE_DIR}" init -q \
    || die "git init failed in temporary clone directory '${CLONE_DIR}'."
  git -C "${CLONE_DIR}" fetch --depth 1 --no-tags "${GOVERNANCE_REPO_URL}" "refs/tags/${GOVERNANCE_TAG}:refs/tags/${GOVERNANCE_TAG}" >/dev/null 2>&1 \
    || die "git fetch of 'refs/tags/${GOVERNANCE_TAG}' from '${GOVERNANCE_REPO_URL}' failed."
  git -C "${CLONE_DIR}" checkout -q --detach "refs/tags/${GOVERNANCE_TAG}" \
    || die "git checkout of 'refs/tags/${GOVERNANCE_TAG}' failed."

  # Resolve the pinned tag to the exact commit SHA it points at via refs/tags/<tag>^{commit}.
  local resolved_sha
  resolved_sha="$(git -C "${CLONE_DIR}" rev-parse --verify "refs/tags/${GOVERNANCE_TAG}^{commit}")" \
    || die "unable to resolve commit SHA for 'refs/tags/${GOVERNANCE_TAG}'."
  [ -n "${resolved_sha}" ] || die "resolved an empty commit SHA for tag '${GOVERNANCE_TAG}' -- refusing to record incomplete provenance."

  if [ -n "${EXPECTED_SHA}" ] && [ "${resolved_sha}" != "${EXPECTED_SHA}" ]; then
    die "expected-sha mismatch at install time: tag 'refs/tags/${GOVERNANCE_TAG}' resolved to '${resolved_sha}' but --expected-sha required '${EXPECTED_SHA}' -- refusing to stage or replace '${TARGET_DIR}'."
  fi

  local parent_dir
  parent_dir="$(dirname -- "${TARGET_DIR}")"
  mkdir -p -- "${parent_dir}"
  # Staged in a mktemp directory alongside the eventual target (same
  # filesystem) so the later install move is a single atomic rename, never
  # a cross-filesystem copy.
  STAGE_DIR="$(mktemp -d "${parent_dir}/.nizam-stage.XXXXXX")"

  log "staging governance payload in ${STAGE_DIR}..."
  local module
  for module in "${REQUIRED_MODULE_DIRS[@]}"; do
    [ -d "${CLONE_DIR}/${module}" ] || die "cloned tag '${GOVERNANCE_TAG}' is missing expected module directory '${module}'."
    cp -r -- "${CLONE_DIR}/${module}" "${STAGE_DIR}/${module}"
  done
  [ -s "${CLONE_DIR}/NIZAM.json" ] || die "cloned tag '${GOVERNANCE_TAG}' is missing a non-empty NIZAM.json at its root."
  cp -- "${CLONE_DIR}/NIZAM.json" "${STAGE_DIR}/NIZAM.json"

  log "verifying staged injection before declaring success..."
  check_required_files "${STAGE_DIR}"
  check_nizam_index "${STAGE_DIR}"

  local framework_version
  framework_version="$(python3 -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    print(json.load(handle).get("framework", {}).get("version", ""))
' "${STAGE_DIR}/NIZAM.json")" || die "unable to read framework.version from the staged NIZAM.json."
  [ -n "${framework_version}" ] || die "staged NIZAM.json has no framework.version -- refusing to record incomplete provenance."

  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  log "recording provenance (framework_version=${framework_version}, tag=${GOVERNANCE_TAG}, resolved_sha=${resolved_sha})..."
  python3 -c '
import json, sys
path, version, tag, resolved_sha, source_url, installed_at = sys.argv[1:7]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "framework_version": version,
            "tag": tag,
            "resolved_sha": resolved_sha,
            "source_url": source_url,
            "installed_at": installed_at,
        },
        handle,
        indent=2,
    )
    handle.write("\n")
' "${STAGE_DIR}/provenance.json" "${framework_version}" "${GOVERNANCE_TAG}" "${resolved_sha}" "${GOVERNANCE_REPO_URL}" "${installed_at}" \
    || die "failed to write provenance.json into the staged payload."

  if [ -d "${TARGET_DIR}" ]; then
    REPLACED_OLD_DIR="${TARGET_DIR}.old.$$"
    mv -- "${TARGET_DIR}" "${REPLACED_OLD_DIR}"
  fi
  mv -- "${STAGE_DIR}" "${TARGET_DIR}"
  # Ownership of the staged directory has transferred to TARGET_DIR: clear
  # the tracker so cleanup does not attempt to remove the (now relocated)
  # path a second time.
  STAGE_DIR=""
  if [ -n "${REPLACED_OLD_DIR}" ]; then
    rm -rf -- "${REPLACED_OLD_DIR}"
    REPLACED_OLD_DIR=""
  fi

  if [ -n "${GIT_REPO}" ]; then
    rm -rf -- "${GIT_REPO}"
    mkdir -p -- "$(dirname -- "${GIT_REPO}")"
    cp -R -- "${CLONE_DIR}" "${GIT_REPO}"
    log "retained verified reference repository at '${GIT_REPO}' (commit ${resolved_sha})."
  fi

  log "install complete. Governance payload version ${framework_version} (tag ${GOVERNANCE_TAG}) is now at '${TARGET_DIR}'."
}

# Writes the minimal, deterministic project skeleton a greenfield genesis stands
# up (ecosystem/00_ecosystem_bootstrap.md Section 8, step 2): a project README, a
# CONTEXT.md stub enumerating the consumer-supplied inputs the later stages consume
# (that protocol's Section 6), and a source placeholder the Audit stage can measure.
# Deterministic: only the project name varies, so the same genesis inputs reproduce
# the same scaffold. The title lines are written with printf (name interpolation);
# the bodies come from quoted heredocs so their literal backticked paths are never
# evaluated as command substitutions.
scaffold_project() {
  local root="$1"
  local name="$2"
  log "genesis: scaffolding a minimal deterministic skeleton under '${root}'..."
  mkdir -p -- "${root}/src"

  {
    printf '# %s\n\n' "${name}"
    cat <<'EOF'
A project bootstrapped into the Nizam ecosystem via greenfield genesis
(`.nizam/ecosystem/00_ecosystem_bootstrap.md` Section 8). The governance payload
is injected under `.nizam/`; enter the ecosystem cycle at Preflight
(`.nizam/ecosystem/01_clean_state_preflight.md`).
EOF
  } > "${root}/README.md"

  {
    printf '# %s -- Ecosystem Context\n\n' "${name}"
    cat <<'EOF'
This project participates in the Nizam Ecosystem Engineering Cycle. Before running
the full cycle, supply the consumer-specific inputs the later stages consume
(`.nizam/ecosystem/00_ecosystem_bootstrap.md` Section 6):

- **In-scope repositories** (the ecosystem-membership registry that sets `n`): TODO
- **Scope boundaries**: TODO
- **Scoring thresholds**: TODO
- **Finding owners**: TODO
- **Operator gates**: TODO

Until these are supplied this is a valid `docs-standard-only`/`templates` tier
adoption (`.nizam/standard/GIP.md` Section 5.2), not yet a full-loop consumer. This
project is tracked `incubating` (the count-0->1 state) until it clears its first
clean Preflight/Baseline and is promoted `in_scope`.
EOF
  } > "${root}/CONTEXT.md"

  {
    printf '# %s -- source placeholder\n\n' "${name}"
    cat <<'EOF'
Replace this with the project's first real source. It exists so the Audit stage
(`.nizam/ecosystem/03_engineering_audit.md`) has a real tree to measure from the
project's first cycle run.
EOF
  } > "${root}/src/PLACEHOLDER.md"
}

# --genesis: stand up a NEW project from nothing (the 0-case, ecosystem/00
# Section 8). Creates and git-inits an empty --project-root, scaffolds the minimal
# skeleton, then reuses run_install unchanged to clone -> inject -> verify ->
# provenance the payload into <project-root>/.nizam. Refuses a non-empty
# --project-root (a brownfield adoption, not a genesis).
run_genesis() {
  require_pinned_tag "${GOVERNANCE_TAG}"
  require_command git
  require_command python3
  [ -n "${PROJECT_ROOT}" ] || die "--genesis requires --project-root DIR (the new project's root to create and scaffold)."

  if [ -e "${PROJECT_ROOT}" ]; then
    [ -d "${PROJECT_ROOT}" ] || die "--project-root '${PROJECT_ROOT}' exists and is not a directory."
    if [ -n "$(ls -A -- "${PROJECT_ROOT}" 2>/dev/null)" ]; then
      die "--genesis refuses a non-empty --project-root '${PROJECT_ROOT}': standing up a new project over existing content is a brownfield adoption (ecosystem/00_ecosystem_bootstrap.md Section 5.1), not a greenfield genesis. Bootstrap into it directly (default mode) instead."
    fi
  else
    mkdir -p -- "${PROJECT_ROOT}" || die "unable to create --project-root '${PROJECT_ROOT}'."
    CREATED_PROJECT_ROOT="${PROJECT_ROOT}"
  fi

  local project_name="${PROJECT_NAME:-$(basename -- "${PROJECT_ROOT}")}"

  log "genesis: initializing a new project at '${PROJECT_ROOT}' (name: ${project_name})..."
  git init -q -- "${PROJECT_ROOT}" || die "git init failed for '${PROJECT_ROOT}'."

  scaffold_project "${PROJECT_ROOT}" "${project_name}"

  # Default the payload location to <project-root>/.nizam unless the caller pinned
  # an explicit --target. Then reuse the normal install (clone -> inject -> verify
  # -> provenance) unchanged -- genesis defines no second inheritance mechanism.
  if [ "${TARGET_EXPLICIT}" -eq 0 ]; then
    TARGET_DIR="${PROJECT_ROOT}/${DEFAULT_TARGET_DIR}"
  fi
  log "genesis: injecting the governance payload into '${TARGET_DIR}'..."
  run_install

  # The project stood up successfully and now owns itself: clear the created-root
  # tracker so cleanup never removes it.
  CREATED_PROJECT_ROOT=""
  log "genesis complete: new project '${project_name}' created at '${PROJECT_ROOT}'; governance payload at '${TARGET_DIR}'. Enter the cycle at Preflight (${TARGET_DIR}/ecosystem/01_clean_state_preflight.md)."
}

main() {
  parse_args "$@"
  if [ "${GENESIS}" -eq 1 ]; then
    [ "${VERIFY_ONLY}" -eq 0 ] || die "--genesis and --verify-only are mutually exclusive."
    run_genesis
  elif [ "${VERIFY_ONLY}" -eq 1 ]; then
    run_verify_only
  else
    run_install
  fi
}

main "$@"
