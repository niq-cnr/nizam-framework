# tools/verify_lib.sh -- Vetted Verification-Helper Library (R3, phase
# 004-durable-enforcement, F-023).
#
# A SOURCED bash library -- it defines functions ONLY. Sourcing this file
# has NO side effect beyond those definitions: no stdout, no stderr, no
# state mutation, no `set -x`, no top-level work of any kind. This is a
# hard requirement (see .agent/contracts/023.json verification entry 2) so
# that any contract or `tools/validate.sh` check can `source
# tools/verify_lib.sh` unconditionally without perturbing its own shell
# options, output streams, or exit status.
#
# Exposes five vetted, individually fixture-tested primitives that
# contracts (F-024..F-029) and future `tools/validate.sh` checks should
# compose their verification from, instead of re-inventing (and
# re-breaking) the historical anti-patterns this library exists to fix:
# vacuous whole-file greps, `git diff HEAD` scope guards blind to new
# untracked files, equal-or-decreasing version "increases", punctuation-
# mangled path resolution, and stale multi-directory payload enumerations.
#
# Dependency-light: bash + coreutils + git + python3 (with PyYAML, already
# required by tools/validate.sh). No network access, no vendored
# dependencies.
#
# Each function below is a library primitive only: it is never executed as
# a standalone script, and it produces no output or side effect purely
# from being sourced -- only when explicitly invoked.

# ---------------------------------------------------------------------------
# Internal helper (not one of the five named primitives): strips one or
# more trailing sentence-punctuation characters from a token. Used by
# vlib_path_resolves. Kept private (leading underscore) to keep the
# library's public surface to exactly the five documented primitives.
# ---------------------------------------------------------------------------

_vlib_strip_trailing_punct() {
  local s="$1"
  local c
  while [ -n "${s}" ]; do
    c="${s: -1}"
    case "${c}" in
      .|,|\;|:|\!|\?|\)|\]|\}|\"|\')
        s="${s%?}"
        ;;
      *)
        break
        ;;
    esac
  done
  printf '%s' "${s}"
}

# ---------------------------------------------------------------------------
# vlib_section_grep <file> <heading-regex> <token-regex>
#
# Asserts that <token-regex> is found strictly within the span starting at
# the first line matching <heading-regex> and running up to (but not
# including) the next markdown heading line (a line beginning with one or
# more `#` characters) or EOF. Returns 1 if the heading itself is never
# found, OR if the token is absent from that span -- even when the token
# appears elsewhere in the file. This is the section-scoped counterpart to
# a vacuous whole-file grep, which would false-pass on a token that merely
# appears in some unrelated section.
#
# Args:
#   file: path to a text file. Actually read from disk (never keyed off
#     the filename itself).
#   heading-regex: an extended regex matched against each line, e.g.
#     '^## Target Section'.
#   token-regex: an extended regex searched for within the heading's span.
#
# Returns:
#   0 if the heading is found and the token occurs within its span.
#   1 otherwise (heading not found, or token absent from the span).
# ---------------------------------------------------------------------------

vlib_section_grep() {
  local file="$1"
  local heading_re="$2"
  local token_re="$3"

  [ -f "${file}" ] || return 1

  awk -v h="${heading_re}" -v t="${token_re}" '
    BEGIN { started = 0; in_span = 0; matched = 0 }
    {
      if (!started) {
        if ($0 ~ h) {
          started = 1
          in_span = 1
        }
      } else if ($0 ~ /^#+/) {
        in_span = 0
      }
      if (in_span && $0 ~ t) {
        matched = 1
      }
    }
    END { exit(matched ? 0 : 1) }
  ' "${file}"
}

# ---------------------------------------------------------------------------
# vlib_scope_guard <allowed-path-or-prefix> [<allowed-path-or-prefix> ...]
#
# MUST be invoked with CWD at a git repository root. Runs
# `git status --porcelain --untracked-files=all -- . ':(exclude).agent'`
# (the untracked-aware form -- unlike a plain `git diff HEAD` guard, this
# SEES brand-new untracked files; the exact 018/021-precedent defect this
# primitive exists to fix), strips each line's 3-character status prefix,
# and checks every remaining changed path against the given allow-list:
# a path is allowed if it exactly equals, or is prefixed by, one of the
# given patterns.
#
# Args:
#   One or more allowed repo-relative paths or path prefixes.
#
# Returns:
#   0 if every changed path (or there are none) is allowed.
#   1 if any changed path is not allowed (the offending path(s) are
#     printed).
# ---------------------------------------------------------------------------

vlib_scope_guard() {
  local allowed=("$@")
  local changed
  changed=$(git status --porcelain --untracked-files=all -- . ':(exclude).agent') || return 1

  local line path allow ok bad
  bad=0
  while IFS= read -r line; do
    [ -z "${line}" ] && continue
    path="${line:3}"
    ok=0
    for allow in "${allowed[@]}"; do
      if [ "${path}" = "${allow}" ] || [[ "${path}" == "${allow}"* ]]; then
        ok=1
        break
      fi
    done
    if [ "${ok}" -eq 0 ]; then
      echo "vlib_scope_guard: out-of-scope changed path: ${path}"
      bad=1
    fi
  done <<< "${changed}"

  [ "${bad}" -eq 0 ]
}

# ---------------------------------------------------------------------------
# vlib_version_increased <file>
#
# MUST be invoked with CWD at a git repository root where <file> exists in
# the working tree. Parses the YAML frontmatter `version` field of the
# working-tree copy and of `git show HEAD:<file>` (via python3 + PyYAML),
# and returns 0 only if the HEAD copy exists, both values parse as
# MAJOR.MINOR.PATCH, and the working-tree version is a STRICT semver
# increase over the HEAD version (proper tuple ordering -- rejects both an
# equal version and a decreased version, not merely a `!=` check).
#
# Args:
#   file: repo-relative path to a file with YAML frontmatter.
#
# Returns:
#   0 if the working-tree version is a strict semver increase over HEAD.
#   1 otherwise (HEAD copy missing, either version fails to parse, or the
#     working-tree version is equal to or less than the HEAD version --
#     a diagnostic is printed).
# ---------------------------------------------------------------------------

vlib_version_increased() {
  local file="$1"

  [ -f "${file}" ] || { echo "vlib_version_increased: MISSING working-tree file ${file}"; return 1; }

  python3 - "${file}" <<'PY'
import re
import subprocess
import sys

import yaml

path = sys.argv[1]


def extract_version(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    fm_text = "\n".join(lines[1:end_idx])
    try:
        frontmatter = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None
    if not isinstance(frontmatter, dict):
        return None
    version = frontmatter.get("version")
    return version if isinstance(version, str) else None


def parse_semver(version):
    if not isinstance(version, str):
        return None
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


try:
    with open(path, "r", encoding="utf-8") as fh:
        working_text = fh.read()
except OSError as exc:
    print(f"vlib_version_increased: could not read working-tree file {path}: {exc}")
    sys.exit(1)

result = subprocess.run(
    ["git", "show", f"HEAD:{path}"],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print(f"vlib_version_increased: no HEAD copy of {path} (git show HEAD:{path} failed)")
    sys.exit(1)
head_text = result.stdout

working_version = extract_version(working_text)
head_version = extract_version(head_text)

working_tuple = parse_semver(working_version)
head_tuple = parse_semver(head_version)

if working_tuple is None or head_tuple is None:
    print(
        f"vlib_version_increased: {path}: version(s) failed to parse as semver "
        f"MAJOR.MINOR.PATCH (working={working_version!r}, head={head_version!r})"
    )
    sys.exit(1)

if working_tuple > head_tuple:
    sys.exit(0)

print(
    f"vlib_version_increased: {path}: working-tree version {working_version} is not "
    f"a strict increase over HEAD version {head_version}"
)
sys.exit(1)
PY
}

# ---------------------------------------------------------------------------
# vlib_path_resolves <path-token>
#
# Strips one or more trailing sentence-punctuation characters
# (`.,;:!?)]}"'`) from the end of <path-token>. If the stripped token
# matches the placeholder/illustrative exemption -- it contains the
# literal substring `NNN` or `XXX`, matches a `step-<digits>` pattern,
# contains the word `placeholder`, or ends in `/` (a directory-only
# reference) -- returns 0 trivially without touching disk. Otherwise tests
# whether the stripped token resolves as a path relative to the current
# working directory (`test -e`).
#
# Args:
#   path-token: a raw path reference, possibly with trailing sentence
#     punctuation attached (e.g. copied verbatim out of prose).
#
# Returns:
#   0 if the token is exempt (placeholder/illustrative/directory-only) or
#     resolves on disk after stripping trailing punctuation.
#   1 if the stripped token is a concrete, non-exempt reference that does
#     not resolve (the offending token is printed).
# ---------------------------------------------------------------------------

vlib_path_resolves() {
  local raw_token="$1"
  local stripped
  stripped=$(_vlib_strip_trailing_punct "${raw_token}")

  if [[ "${stripped}" == *NNN* ]] \
    || [[ "${stripped}" == *XXX* ]] \
    || [[ "${stripped}" =~ step-[0-9]+ ]] \
    || [[ "${stripped}" == *placeholder* ]] \
    || [[ "${stripped}" == */ ]]; then
    return 0
  fi

  if [ -e "${stripped}" ]; then
    return 0
  fi

  echo "vlib_path_resolves: path does not resolve: '${raw_token}' (stripped: '${stripped}')"
  return 1
}

# ---------------------------------------------------------------------------
# vlib_no_stale_payload <file>
#
# Scans <file> line by line. For any single line that mentions `standard/`,
# `templates/`, AND `schema/` together but OMITS `tools/` -- the exact
# F-019 rework defect: a stale 3-directory payload enumeration that should
# have been a 4-directory enumeration -- returns 1 (printing the offending
# line). Returns 0 if no such stale line exists anywhere in the file.
#
# Args:
#   file: path to a text file. Actually read from disk (never keyed off
#     the filename itself).
#
# Returns:
#   0 if the file contains no stale 3-directory payload line.
#   1 if a stale line is found (the offending line is printed).
# ---------------------------------------------------------------------------

vlib_no_stale_payload() {
  local file="$1"

  [ -f "${file}" ] || return 1

  local line
  while IFS= read -r line || [ -n "${line}" ]; do
    if [[ "${line}" == *"standard/"* ]] \
      && [[ "${line}" == *"templates/"* ]] \
      && [[ "${line}" == *"schema/"* ]] \
      && [[ "${line}" != *"tools/"* ]]; then
      echo "vlib_no_stale_payload: stale payload enumeration (omits tools/): ${line}"
      return 1
    fi
  done < "${file}"

  return 0
}
