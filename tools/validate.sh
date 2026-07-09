#!/usr/bin/env bash
#
# tools/validate.sh -- Nizam repo-local NDS compliance validator.
#
# The runtime-agnostic, repo-local compliance check described in
# docs/architecture/ADR-001-ci-compliance-enforcement.md and
# .agent/product_spec_002.md Sec 4 (F-012). Operates entirely on the
# repository rooted at the current working directory at invocation time --
# it never hardcodes an absolute path back to any particular checkout, so
# `cd <any-repo-copy> && bash tools/validate.sh` always evaluates that
# copy's own tree.
#
# One runtime-agnostic command: `bash tools/validate.sh` exits 0 on a clean
# tree and non-zero on any violation.
#
# Runtime dependencies (fail-closed, see require_command/require_python_module
# below): bash, git, grep, find, awk, python3 (with the `jsonschema` and
# `yaml` (PyYAML) modules importable).
#
# Modes:
#   (default, no args)   Full repo sweep: runs checks C1-C8.
#   --target <file>      Runs only the checks applicable to a single file.
#   --payload            Validates a consumer-injected .nizam/ payload subset.
#   --help / -h           Prints usage and exits 0.
#
# See print_usage() below for the full description of every check and mode.
set -euo pipefail

# ---------------------------------------------------------------------------
# Fail-closed dependency guards (mirrors bootstrap.sh's require_command
# pattern, repo root bootstrap.sh, require_command() function).
# ---------------------------------------------------------------------------

die() {
  echo "FATAL: $*" >&2
  exit 1
}

require_command() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 \
    || die "required command '${cmd}' not found on PATH. tools/validate.sh cannot run without it."
}

require_python_module() {
  local module="$1"
  python3 -c "import ${module}" >/dev/null 2>&1 \
    || die "required python3 module '${module}' is not importable by python3. tools/validate.sh does not vendor or install its own dependencies -- install '${module}' (e.g. 'pip install ${module}' or 'pip install PyYAML' for the 'yaml' module) before running tools/validate.sh."
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

print_usage() {
  cat <<'USAGE'
Usage: tools/validate.sh [--help]
       tools/validate.sh
       tools/validate.sh --target <file>

tools/validate.sh is the repo-local NDS compliance validator. It ALWAYS
operates on the repository rooted at the current working directory at
invocation time (never a hardcoded absolute path back to any particular
checkout) -- so `cd <any-repo-copy> && bash tools/validate.sh` always
evaluates that copy's own tree.

Runtime dependencies (checked up front, fails closed with a named diagnostic
if any is missing): bash, git, grep, find, awk, python3 -- with python3's
`jsonschema` and `yaml` (PyYAML) modules importable. This script never
installs or vendors these dependencies itself.

Modes:
  (no arguments)      Full repo sweep. Runs all 8 checks (C1-C8) and prints
                      one PASS/FAIL line per check plus a final summary
                      line. Exits 0 only if every check passed.

  --target <file>     Runs only the checks applicable to a single named
                      file, printing PASS/FAIL per applicable check.
                        - For a `.md` target: C1 (frontmatter schema), C2
                          (format), and C3 (untagged-fence sweep) run
                          against exactly that one file.
                        - For a `.json` target shaped like a Nizam index
                          file: C4 (schema validation + indexed-path
                          walker) runs against exactly that one file.
                      Checks that are inherently repo-wide (C5 branding
                      sweep, C6 bootstrap.sh sanity, C7 module-README
                      presence, C8 git-history version/changelog diff) do
                      NOT run under --target. Exits non-zero if any
                      applicable check fails. --target is the only mode
                      under which files in tools/fixtures/ are ever read.

  --payload           Consumer-payload mode. Validates only the subset of
                      checks relevant to a `bootstrap.sh`-injected consumer
                      payload (standard/, templates/, schema/, tools/, and
                      NIZAM.json). Framework-envelope files that are
                      intentionally absent from consumer payloads
                      (CONTEXT.md, README.md, CHANGELOG.md, bootstrap.sh,
                      methodology/, registry/, docs/) are not required.
                      Runs C1-C5, C7-C8 with payload-appropriate file sets;
                      C6 is skipped. Exits 0 only if every applicable check
                      passed.

  --help, -h          Prints this usage and exits 0.

Checks (each check function emits exactly one line matching
`[C<N>] PASS <name>` or `[C<N>] FAIL <name>`, with any offending
file(s)/detail(s) printed on the following indented line(s)):

  C1  Frontmatter schema. Every file in the "shipped-doc set" (see below)
      begins with a YAML frontmatter block (first content in the file,
      opened and closed by a bare `---` line) that schema-validates via
      python3 + jsonschema against schema/frontmatter.schema.json.

  C2  Format (belt-and-braces beyond schema). For the same shipped-doc
      set: `authoritative_source` equals the file's own repository-relative
      path exactly, or the literal string `NA`; `status` is one of
      draft/active/deprecated; `version` matches semver MAJOR.MINOR.PATCH.

  C3  Untagged fence sweep (NDS Sec 6.2). For the same shipped-doc set:
      zero fenced code blocks opened with a bare ``` (no language tag).

  C4  NIZAM.json index integrity. NIZAM.json parses as JSON and validates
      via python3 + jsonschema against registry/nizam-index.schema.json,
      AND every repository-relative path indexed anywhere within it (every
      string under a `path` or `authoritative_source` key, plus every
      string item of any `key_documents`/`schemas`/`templates` list,
      skipping the literal `NA`) resolves on disk. In --payload mode the
      registry schema is optional (skipped if missing), and paths under
      non-injected dirs (methodology/, registry/, docs/) are skipped as
      expected-absent while paths under injected dirs (standard/,
      templates/, schema/, tools/) are still required to resolve.

  C5  Branding/endpoint leakage. Zero case-insensitive occurrences of
      `nizamiq`, `.svc`, or `cluster.local` anywhere in shipped content:
      the shipped-doc set, plus NIZAM.json, CHANGELOG.md, root README.md,
      and bootstrap.sh. Repo-wide only; does not run under --target. In
      --payload mode the extra targets are swept only when present; missing
      envelope files do not cause a failure.

  C6  bootstrap.sh sanity. `bash -n ./bootstrap.sh` (syntax check) AND
      `timeout 5 ./bootstrap.sh --help` exits 0. Repo-wide only; does not
      run under --target or --payload. Note: bootstrap.sh lives at the REPO
      ROOT (./bootstrap.sh), not under tools/.

  C7  Module README presence (NDS Sec 5.3). Each of standard/, methodology/,
      registry/, templates/, schema/, tools/ contains a README.md.
      Repo-wide only; does not run under --target. In --payload mode only
      the injected module READMEs (standard/, templates/, schema/, tools/)
      are required.

  C8  Version-bump-vs-changelog (NDS Sec 4). For each file in the
      shipped-doc set: compares the working tree's frontmatter `version`
      against the same file's frontmatter `version` at `git show
      HEAD:<file>`. This comparison is only meaningful in CI on a PR diff
      against HEAD. If the file did not exist at HEAD (new file), it is
      skipped -- no prior version to compare against, no change record
      required. If the file is unchanged vs HEAD, it passes trivially. If
      the version differs, a change record is required: either a
      `change_log` frontmatter entry on the file whose `version` matches
      the new version, or a line in root CHANGELOG.md naming the file's
      path. Repo-wide only; does not run under --target.

Shipped-doc set (the file set C1, C2, C3, C5, and C8 all operate over,
consistently): CONTEXT.md; every .md under docs/architecture/; every .md
under standard/, methodology/, registry/, and templates/; every .md under
tools/ EXCLUDING tools/fixtures/ (which is never part of the default sweep
and is reachable only via --target); and schema/README.md (the only .md
under schema/). Root README.md and docs/planning/* carry no frontmatter
contract and are NOT part of this set (root README.md and bootstrap.sh are
still covered by C5's separately-listed extra targets).

Payload-doc set (the --payload mode file set, used by C1, C2, C3, C5, and
C8): every .md under standard/, templates/, and tools/ EXCLUDING
tools/fixtures/; and schema/README.md. CONTEXT.md, docs/architecture/,
methodology/, and registry/ are intentionally excluded because they are not
injected into consumer repositories by bootstrap.sh.

Exit code: 0 only when every check that ran passed (0 failed).
USAGE
}

# ---------------------------------------------------------------------------
# Shared file-set builder (used consistently by C1, C2, C3, C5, C8)
# ---------------------------------------------------------------------------

build_shipped_md_set() {
  local files=()
  files+=("CONTEXT.md")

  local f
  if [ -d docs/architecture ]; then
    while IFS= read -r f; do
      files+=("${f}")
    done < <(find docs/architecture -type f -name '*.md' | LC_ALL=C sort)
  fi

  local d
  for d in standard methodology registry templates; do
    if [ -d "${d}" ]; then
      while IFS= read -r f; do
        files+=("${f}")
      done < <(find "${d}" -type f -name '*.md' | LC_ALL=C sort)
    fi
  done

  if [ -d tools ]; then
    while IFS= read -r f; do
      files+=("${f}")
    done < <(find tools -type f -name '*.md' -not -path 'tools/fixtures/*' | LC_ALL=C sort)
  fi

  if [ -f schema/README.md ]; then
    files+=("schema/README.md")
  fi

  printf '%s\n' "${files[@]}"
}

# ---------------------------------------------------------------------------
# Payload file-set builder (used by C1, C2, C3, C5, C8 in --payload mode)
# ---------------------------------------------------------------------------

build_payload_md_set() {
  local files=()
  local f
  local d

  for d in standard templates; do
    if [ -d "${d}" ]; then
      while IFS= read -r f; do
        files+=("${f}")
      done < <(find "${d}" -type f -name '*.md' | LC_ALL=C sort)
    fi
  done

  if [ -d tools ]; then
    while IFS= read -r f; do
      files+=("${f}")
    done < <(find tools -type f -name '*.md' -not -path 'tools/fixtures/*' | LC_ALL=C sort)
  fi

  if [ -f schema/README.md ]; then
    files+=("schema/README.md")
  fi

  printf '%s\n' "${files[@]}"
}

# ---------------------------------------------------------------------------
# Shared frontmatter parser/validator (python3 + PyYAML + jsonschema)
# ---------------------------------------------------------------------------

# frontmatter_python <schema|format> <file>
# Prints an error description on failure; exit 0 on success, 1 on failure.
frontmatter_python() {
  local mode="$1"
  local path="$2"
  python3 - "${mode}" "${path}" <<'PY'
import re
import sys

import yaml
import jsonschema

mode, path = sys.argv[1], sys.argv[2]

try:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
except OSError as exc:
    print(f"{path}: could not be read: {exc}")
    sys.exit(1)

lines = text.splitlines()

# A single leading HTML comment line (`<!-- ... -->`) is tolerated ONLY for
# paths under tools/fixtures/ -- the intentional-negative-fixture marker
# documented in .agent/contracts/012.json. Any shipped (non-fixtures) `.md`
# with a leading HTML comment before its frontmatter fails C1 below with the
# "does not begin with a '---' frontmatter delimiter" message, same as any
# other missing-frontmatter file.
start = 0
if (
    path.startswith("tools/fixtures/")
    and lines
    and lines[0].strip().startswith("<!--")
    and lines[0].strip().endswith("-->")
):
    start = 1

if start >= len(lines) or lines[start].strip() != "---":
    print(f"{path}: does not begin with a '---' frontmatter delimiter")
    sys.exit(1)

end_idx = None
for i in range(start + 1, len(lines)):
    if lines[i].strip() == "---":
        end_idx = i
        break

if end_idx is None:
    print(f"{path}: frontmatter opened with '---' but never closed")
    sys.exit(1)

fm_text = "\n".join(lines[start + 1:end_idx])
try:
    frontmatter = yaml.safe_load(fm_text)
except yaml.YAMLError as exc:
    print(f"{path}: frontmatter is not valid YAML: {exc}")
    sys.exit(1)

if not isinstance(frontmatter, dict):
    print(f"{path}: frontmatter did not parse to a mapping")
    sys.exit(1)

if mode == "schema":
    try:
        with open("schema/frontmatter.schema.json", "r", encoding="utf-8") as fh:
            schema = __import__("json").load(fh)
    except OSError as exc:
        print(f"{path}: could not read schema/frontmatter.schema.json: {exc}")
        sys.exit(1)
    try:
        jsonschema.validate(instance=frontmatter, schema=schema)
    except jsonschema.ValidationError as exc:
        print(f"{path}: frontmatter schema violation: {exc.message}")
        sys.exit(1)
    sys.exit(0)

if mode == "format":
    errors = []
    authoritative_source = frontmatter.get("authoritative_source")
    if authoritative_source != path and authoritative_source != "NA":
        errors.append(
            f"authoritative_source '{authoritative_source}' != own path '{path}' and != 'NA'"
        )
    status = frontmatter.get("status")
    if status not in ("draft", "active", "deprecated"):
        errors.append(f"status '{status}' is not one of draft/active/deprecated")
    version = frontmatter.get("version")
    if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+$", version):
        errors.append(f"version '{version}' does not match semver MAJOR.MINOR.PATCH")
    if errors:
        print(f"{path}: " + "; ".join(errors))
        sys.exit(1)
    sys.exit(0)

print(f"{path}: unknown frontmatter_python mode '{mode}'")
sys.exit(2)
PY
}

# ---------------------------------------------------------------------------
# C1 -- frontmatter schema
# ---------------------------------------------------------------------------

check_c1_frontmatter_schema() {
  local files=("$@")
  local errors=()
  local f out

  for f in "${files[@]}"; do
    if ! out=$(frontmatter_python schema "${f}" 2>&1); then
      errors+=("${out}")
    fi
  done

  if [ "${#errors[@]}" -eq 0 ]; then
    echo "[C1] PASS frontmatter-schema"
    return 0
  fi

  echo "[C1] FAIL frontmatter-schema"
  for out in "${errors[@]}"; do
    echo "  ${out}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# C2 -- format (authoritative_source / status / version)
# ---------------------------------------------------------------------------

check_c2_format() {
  local files=("$@")
  local errors=()
  local f out

  for f in "${files[@]}"; do
    if ! out=$(frontmatter_python format "${f}" 2>&1); then
      errors+=("${out}")
    fi
  done

  if [ "${#errors[@]}" -eq 0 ]; then
    echo "[C2] PASS format"
    return 0
  fi

  echo "[C2] FAIL format"
  for out in "${errors[@]}"; do
    echo "  ${out}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# C3 -- untagged fence sweep (NDS Sec 6.2)
# ---------------------------------------------------------------------------

check_c3_fences() {
  local files=("$@")
  local offenders=()
  local f hits

  for f in "${files[@]}"; do
    hits=$(awk -v f="${f}" '
      BEGIN { in_fence = 0 }
      /^```/ {
        if (in_fence == 0) {
          tag = $0
          sub(/^```/, "", tag)
          if (tag == "") { print f ":" NR }
          in_fence = 1
        } else {
          in_fence = 0
        }
        next
      }
    ' "${f}")
    if [ -n "${hits}" ]; then
      offenders+=("${hits}")
    fi
  done

  if [ "${#offenders[@]}" -eq 0 ]; then
    echo "[C3] PASS untagged-fence-sweep"
    return 0
  fi

  echo "[C3] FAIL untagged-fence-sweep"
  local o
  for o in "${offenders[@]}"; do
    echo "${o}" | sed 's/^/  /'
  done
  return 1
}

# ---------------------------------------------------------------------------
# C4 -- index integrity (schema validation + indexed-path walker)
# ---------------------------------------------------------------------------

check_c4_index() {
  local target="$1"
  local out

  if out=$(python3 - "${target}" "${VALIDATOR_MODE}" <<'PY'
import json
import os
import sys

import jsonschema

path = sys.argv[1]
mode = sys.argv[2]

try:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"{path}: not valid JSON: {exc}")
    sys.exit(1)

if mode != "payload":
    try:
        with open("registry/nizam-index.schema.json", "r", encoding="utf-8") as fh:
            schema = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: could not read registry/nizam-index.schema.json: {exc}")
        sys.exit(1)

    try:
        jsonschema.validate(instance=doc, schema=schema)
    except jsonschema.ValidationError as exc:
        print(f"{path}: schema violation: {exc.message}")
        sys.exit(1)

path_keys = ("path", "authoritative_source")
list_path_keys = ("key_documents", "schemas", "templates")
paths = []


def walk(node, key=None):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, k)
    elif isinstance(node, list):
        if key in list_path_keys:
            for item in node:
                if isinstance(item, str):
                    paths.append(item)
                else:
                    walk(item, key)
        else:
            for item in node:
                walk(item, key)
    elif isinstance(node, str):
        if key in path_keys:
            paths.append(node)


walk(doc)

if not paths:
    print(f"{path}: no paths discovered by walker -- index appears empty")
    sys.exit(1)

if mode == "payload":
    skipped_dirs = {"methodology", "registry", "docs"}
    paths = [
        p for p in paths
        if p != "NA"
        and not any(p == d or p.startswith(d + "/") for d in skipped_dirs)
    ]

missing = [p for p in paths if p != "NA" and not os.path.exists(p)]
if missing:
    print(f"{path}: indexed path(s) do not resolve on disk: {missing}")
    sys.exit(1)

sys.exit(0)
PY
  ); then
    echo "[C4] PASS index-integrity"
    return 0
  fi

  echo "[C4] FAIL index-integrity"
  echo "  ${out}"
  return 1
}

# ---------------------------------------------------------------------------
# C5 -- branding/endpoint leakage
# ---------------------------------------------------------------------------

check_c5_branding() {
  local shipped=("$@")
  local extra=(NIZAM.json CHANGELOG.md README.md bootstrap.sh)
  local f
  local all=()

  if [ "${VALIDATOR_MODE}" = "payload" ]; then
    for f in "${shipped[@]}"; do
      [ -f "${f}" ] && all+=("${f}")
    done
    for f in "${extra[@]}"; do
      [ -f "${f}" ] && all+=("${f}")
    done
    if [ "${#all[@]}" -eq 0 ]; then
      echo "[C5] PASS branding-leakage"
      return 0
    fi
  else
    all=("${shipped[@]}" "${extra[@]}")
    local missing=()
    for f in "${all[@]}"; do
      [ -f "${f}" ] || missing+=("${f}")
    done

    if [ "${#missing[@]}" -gt 0 ]; then
      echo "[C5] FAIL branding-leakage"
      echo "  sweep target(s) missing: ${missing[*]} -- refusing to trust an absence-of-match result (skipping grep sweep for this invocation)."
      return 1
    fi
  fi

  local hits
  if hits=$(grep -InE 'nizamiq|\.svc|cluster\.local' "${all[@]}" 2>/dev/null); then
    echo "[C5] FAIL branding-leakage"
    echo "${hits}" | sed 's/^/  /'
    return 1
  fi

  echo "[C5] PASS branding-leakage"
  return 0
}

# ---------------------------------------------------------------------------
# C6 -- bootstrap.sh sanity
# ---------------------------------------------------------------------------

check_c6_bootstrap() {
  if [ ! -f ./bootstrap.sh ]; then
    echo "[C6] FAIL bootstrap-sanity"
    echo "  MISSING ./bootstrap.sh"
    return 1
  fi

  local out
  if ! out=$(bash -n ./bootstrap.sh 2>&1); then
    echo "[C6] FAIL bootstrap-sanity"
    echo "  bash -n ./bootstrap.sh failed: ${out}"
    return 1
  fi

  if ! out=$(timeout 5 ./bootstrap.sh --help 2>&1); then
    echo "[C6] FAIL bootstrap-sanity"
    echo "  timeout 5 ./bootstrap.sh --help failed: ${out}"
    return 1
  fi

  echo "[C6] PASS bootstrap-sanity"
  return 0
}

# ---------------------------------------------------------------------------
# C7 -- module README presence (NDS Sec 5.3)
# ---------------------------------------------------------------------------

check_c7_module_readmes() {
  local modules=()
  if [ "${VALIDATOR_MODE}" = "payload" ]; then
    modules=(standard templates schema tools)
  else
    modules=(standard methodology registry templates schema tools)
  fi
  local missing=()
  local m

  for m in "${modules[@]}"; do
    [ -f "${m}/README.md" ] || missing+=("${m}/README.md")
  done

  if [ "${#missing[@]}" -eq 0 ]; then
    echo "[C7] PASS module-readme-presence"
    return 0
  fi

  echo "[C7] FAIL module-readme-presence"
  for m in "${missing[@]}"; do
    echo "  missing ${m}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# C8 -- version-bump-vs-changelog (NDS Sec 4)
# ---------------------------------------------------------------------------

check_c8_version_changelog() {
  local files=("$@")
  local errors=()
  local f head_content head_tmp out

  # Compute the repo-root-relative prefix (empty when CWD is the repo root).
  local git_prefix
  git_prefix=$(git rev-parse --show-prefix 2>/dev/null || echo "")

  for f in "${files[@]}"; do
    if ! head_content=$(git show "HEAD:${git_prefix}${f}" 2>/dev/null); then
      # File is new at HEAD (did not exist there) -- no prior version to
      # compare against, no change record required.
      continue
    fi

    head_tmp=$(mktemp)
    printf '%s' "${head_content}" > "${head_tmp}"

    if ! out=$(python3 - "${f}" "${head_tmp}" <<'PY'
import re
import sys

import yaml

path, head_path = sys.argv[1], sys.argv[2]


def extract_frontmatter(text):
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
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


current_text = open(path, "r", encoding="utf-8").read()
head_text = open(head_path, "r", encoding="utf-8").read()

current_fm = extract_frontmatter(current_text)
head_fm = extract_frontmatter(head_text)

if current_fm is None or head_fm is None:
    # Frontmatter presence/shape is C1's concern, not this check's.
    sys.exit(0)

current_version = current_fm.get("version")
head_version = head_fm.get("version")

if not isinstance(current_version, str) or not isinstance(head_version, str):
    sys.exit(0)

if current_version == head_version:
    sys.exit(0)

change_log_versions = {
    str(entry.get("version"))
    for entry in (current_fm.get("change_log") or [])
    if isinstance(entry, dict)
}
if current_version in change_log_versions:
    sys.exit(0)

try:
    with open("CHANGELOG.md", "r", encoding="utf-8") as fh:
        changelog_text = fh.read()
except OSError:
    changelog_text = ""

if path in changelog_text:
    sys.exit(0)

print(
    f"{path}: version bumped {head_version} -> {current_version} with no matching "
    f"change_log entry for {current_version} and no CHANGELOG.md line naming {path}"
)
sys.exit(1)
PY
    ); then
      errors+=("${out}")
    fi
    rm -f "${head_tmp}"
  done

  if [ "${#errors[@]}" -eq 0 ]; then
    echo "[C8] PASS version-bump-vs-changelog"
    return 0
  fi

  echo "[C8] FAIL version-bump-vs-changelog"
  for out in "${errors[@]}"; do
    echo "  ${out}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
  VALIDATOR_MODE="default"
  local target=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --help|-h)
        print_usage
        exit 0
        ;;
      --payload)
        VALIDATOR_MODE="payload"
        shift
        ;;
      --target)
        [ "$#" -ge 2 ] || die "--target requires a file argument. See --help."
        VALIDATOR_MODE="target"
        target="$2"
        shift 2
        ;;
      --target=*)
        VALIDATOR_MODE="target"
        target="${1#--target=}"
        shift
        ;;
      *)
        die "unknown argument '$1'. See --help."
        ;;
    esac
  done

  require_command bash
  require_command git
  require_command grep
  require_command find
  require_command awk
  require_command python3
  require_python_module jsonschema
  require_python_module yaml

  local passed=0
  local failed=0

  if [ "${VALIDATOR_MODE}" = "target" ]; then
    [ -f "${target}" ] || die "--target file '${target}' does not exist."
    case "${target}" in
      *.md)
        check_c1_frontmatter_schema "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c2_format "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c3_fences "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        ;;
      *.json)
        check_c4_index "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        ;;
      *)
        die "--target file '${target}' is neither .md nor .json -- no applicable checks."
        ;;
    esac
  elif [ "${VALIDATOR_MODE}" = "payload" ]; then
    echo "MODE: payload (validating consumer-injected subset; framework-envelope checks skipped)"

    local payload_md=()
    local f
    while IFS= read -r f; do
      payload_md+=("${f}")
    done < <(build_payload_md_set)

    check_c1_frontmatter_schema "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c2_format "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c3_fences "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c4_index "NIZAM.json" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c5_branding "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    echo "[C6] SKIP bootstrap-sanity (payload mode)"
    check_c7_module_readmes && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c8_version_changelog "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))

    echo "SUMMARY (payload mode): ${passed} passed, ${failed} failed"
  else
    local shipped_md=()
    local f
    while IFS= read -r f; do
      shipped_md+=("${f}")
    done < <(build_shipped_md_set)

    check_c1_frontmatter_schema "${shipped_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c2_format "${shipped_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c3_fences "${shipped_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c4_index "NIZAM.json" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c5_branding "${shipped_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c6_bootstrap && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c7_module_readmes && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c8_version_changelog "${shipped_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))

    echo "SUMMARY: ${passed} passed, ${failed} failed"
  fi

  [ "${failed}" -eq 0 ]
}

main "$@"
