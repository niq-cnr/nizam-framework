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
# Exposes eight vetted, individually fixture-tested primitives that
# contracts (F-024..F-029, F-053, F-055) and future `tools/validate.sh` checks
# should compose their verification from, instead of re-inventing (and
# re-breaking) the historical anti-patterns this library exists to fix:
# vacuous whole-file greps, `git diff HEAD` scope guards blind to new
# untracked files, equal-or-decreasing version "increases", punctuation-
# mangled path resolution, stale multi-directory payload enumerations,
# bare-substring matches that false-pass on a containing word, hand-maintained
# document enumerations that silently omit a shipped file, and bare (non-`/`-
# qualified) numbered-document cross-references left stale by a renumbering.
#
# Dependency-light: bash + coreutils + git + python3 (with PyYAML, already
# required by tools/validate.sh). No network access, no vendored
# dependencies.
#
# Each function below is a library primitive only: it is never executed as
# a standalone script, and it produces no output or side effect purely
# from being sourced -- only when explicitly invoked.

# ---------------------------------------------------------------------------
# Internal helper (not one of the eight named primitives): strips one or
# more trailing sentence-punctuation characters from a token. Used by
# vlib_path_resolves. Kept private (leading underscore) to keep the
# library's public surface to exactly the eight documented primitives.
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

# ---------------------------------------------------------------------------
# vlib_word_present <file> <word>
#
# Returns 0 iff <word> occurs in <file> as a whole, delimited word — not as a
# substring of a longer word. This is the vetted replacement for a bare
# substring check that false-passes on a containing word (the NDEBT-014
# defect-class-4 catalogue in methodology/02_adversarial_tdd.md: `renewed`
# contains `new`, `stalemate` contains `stale`, `invalid` contains `valid`),
# where the acceptance criterion is the presence of the word itself, not any
# word that happens to contain its letters. <word> is matched as a fixed
# string (never a regex), bounded by grep's word-boundary (`-w`) semantics.
#
# Args:
#   file: path to a text file. Actually read from disk (never keyed off the
#     filename itself).
#   word: the literal word whose whole-word presence is asserted.
#
# Returns:
#   0 if <word> occurs as a whole word in <file>.
#   1 otherwise (file missing, or the token appears only inside longer words).
# ---------------------------------------------------------------------------

vlib_word_present() {
  local file="$1"
  local word="$2"

  [ -f "${file}" ] || return 1

  grep -qwF -- "${word}" "${file}"
}

# ---------------------------------------------------------------------------
# vlib_enumeration_complete <index-json> <module-key> <dir> [glob]
#
# Sources the canonical index <index-json> (a nizam-index-shaped JSON with a
# top-level "modules" array of {"path", "key_documents": [...]}), selects the
# module whose "path" equals <module-key>, and asserts that EVERY file in <dir>
# matching [glob] (default '*.md') is enumerated -- by basename -- in that
# module's key_documents list. This is the disk->index (completeness)
# direction that tools/validate.sh C4 does NOT cover: C4 checks index->disk
# (every listed doc resolves on disk -- no dangling entry), while this checks
# the reverse (no on-disk document is silently OMITTED from the canonical
# index). The NDEBT-005 recurrence guard for the enumeration-completeness
# defect class F-027 fixed by hand (NDEBT-003a: a key-documents list dropping
# a shipped file) -- resolution sourced from the single canonical index, never
# a re-derived or duplicated list.
#
# Args:
#   index-json: path to the canonical index JSON.
#   module-key: the module's "path" value to select within the index.
#   dir:        the on-disk directory whose files are checked for enumeration.
#   glob:       optional filename glob (default '*.md').
#
# Returns:
#   0 if every matching on-disk file is enumerated in the index for the module.
#   1 otherwise (index/dir unreadable, index unpariseable, module absent, or an
#     on-disk file is missing from key_documents -- the omission(s) printed).
# ---------------------------------------------------------------------------

vlib_enumeration_complete() {
  local index="$1"
  local module_key="$2"
  local dir="$3"
  local glob="${4:-*.md}"

  [ -f "${index}" ] || { echo "vlib_enumeration_complete: index not found: ${index}"; return 1; }
  [ -d "${dir}" ] || { echo "vlib_enumeration_complete: dir not found: ${dir}"; return 1; }

  python3 - "${index}" "${module_key}" "${dir}" "${glob}" <<'PY'
import glob as globmod
import json
import os
import sys

index_path, module_key, directory, pattern = sys.argv[1:5]

try:
    with open(index_path, encoding="utf-8") as fh:
        index = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"vlib_enumeration_complete: cannot read index {index_path}: {exc}")
    sys.exit(1)

modules = index.get("modules")
if not isinstance(modules, list):
    print(f"vlib_enumeration_complete: index {index_path} has no 'modules' array")
    sys.exit(1)

listed = None
for module in modules:
    if isinstance(module, dict) and module.get("path") == module_key:
        listed = module.get("key_documents", [])
        break
if listed is None:
    print(f"vlib_enumeration_complete: module '{module_key}' not present in index {index_path}")
    sys.exit(1)

listed_basenames = {os.path.basename(p) for p in listed if isinstance(p, str)}
on_disk = sorted(
    os.path.basename(p)
    for p in globmod.glob(os.path.join(directory, pattern))
    if os.path.isfile(p)
)
omitted = [b for b in on_disk if b not in listed_basenames]
if omitted:
    print(
        f"vlib_enumeration_complete: {directory} file(s) omitted from '{module_key}' "
        f"key_documents in {index_path}: {omitted}"
    )
    sys.exit(1)
sys.exit(0)
PY
}

# ---------------------------------------------------------------------------
# vlib_bare_ref_resolves <file> <index-json>
#
# Scans <file> for BARE numbered-document references -- a 'NN_name.md' token
# (two digits, an underscore, a name, then '.md') that is NOT '/'-qualified
# (carries no directory prefix). For each bare token, asserts its basename
# appears among the basenames of the canonical index <index-json>'s
# key_documents. tools/validate.sh C9 resolves only '/'-qualified path tokens
# and C10's three sub-checks never inspect a bare filename, so a bare
# 'NN_name.md' left stale by a renumbering (the NDEBT-003b defect: a bare
# '05_release_train.md' surviving after the file became '06_release_train.md')
# slips past both. The NDEBT-005 recurrence guard for that class -- resolution
# sourced from the canonical index, not a re-derived list.
#
# Args:
#   file:       path to the text file to scan.
#   index-json: path to the canonical index JSON supplying the valid basenames.
#
# Returns:
#   0 if every bare NN_name.md token resolves to an indexed basename (or the
#     file contains no bare tokens at all).
#   1 otherwise (file/index unreadable, index unparseable, or a bare token does
#     not resolve -- the unresolved token(s) are printed).
# ---------------------------------------------------------------------------

vlib_bare_ref_resolves() {
  local file="$1"
  local index="$2"

  [ -f "${file}" ] || { echo "vlib_bare_ref_resolves: file not found: ${file}"; return 1; }
  [ -f "${index}" ] || { echo "vlib_bare_ref_resolves: index not found: ${index}"; return 1; }

  python3 - "${file}" "${index}" <<'PY'
import json
import os
import re
import sys

file_path, index_path = sys.argv[1:3]

try:
    with open(index_path, encoding="utf-8") as fh:
        index = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"vlib_bare_ref_resolves: cannot read index {index_path}: {exc}")
    sys.exit(1)

basenames = set()
for module in index.get("modules", []):
    if isinstance(module, dict):
        for kd in module.get("key_documents", []):
            if isinstance(kd, str):
                basenames.add(os.path.basename(kd))

try:
    with open(file_path, encoding="utf-8") as fh:
        text = fh.read()
except OSError as exc:
    print(f"vlib_bare_ref_resolves: cannot read {file_path}: {exc}")
    sys.exit(1)

# Bare NN_name.md: two digits, '_', word chars, '.md'; NOT preceded by '/' or a
# word char, so 'dir/05_x.md' (qualified) and 'a05_x.md' (embedded) never match.
bare = re.compile(r"(?<![/\w])([0-9]{2}_[A-Za-z0-9_]+\.md)\b")
unresolved = sorted({m.group(1) for m in bare.finditer(text) if m.group(1) not in basenames})
if unresolved:
    print(f"vlib_bare_ref_resolves: {file_path}: unresolved bare reference(s): {unresolved}")
    sys.exit(1)
sys.exit(0)
PY
}
