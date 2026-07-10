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
#   (default, no args)   Full repo sweep: runs checks C1-C10.
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
  (no arguments)      Full repo sweep. Runs all 11 checks (C1-C11) and
                      prints one PASS/FAIL line per check plus a final
                      summary line. Exits 0 only if every check passed.

  --target <file>     Runs only the checks applicable to a single named
                      file, printing PASS/FAIL per applicable check.
                        - For a `.md` target: C1 (frontmatter schema), C2
                          (format), C3 (untagged-fence sweep), C9
                          (repo-wide path resolution, scanning only that
                          file's own body), and C10 (single-source-of-truth
                          consistency, scanning only that file's own body)
                          run against exactly that one file.
                        - For a `.json` target: the file is CONTENT-ROUTED
                          between C4 and C11. If the file carries a
                          top-level `review` key, a top-level `qa_pass` or
                          `verdict` key, a top-level `contract_id` key, or a
                          top-level `circuit_breaker` or `scope_budget` key
                          (checked in that order), C11 (dogfood schema
                          validation) runs against exactly that one file,
                          validated against schema/contract_review.schema.json,
                          schema/qa_verdict.schema.json,
                          schema/contract.schema.json, or
                          schema/run_state.schema.json respectively --
                          C4 does NOT also run in this case. Otherwise (no
                          recognized key present -- e.g. NIZAM.json or a
                          Nizam-index-shaped fixture) C4 (schema validation
                          + indexed-path walker) runs against exactly that
                          one file, exactly as before C11 existed.
                        - For a `.html` target: C10 (single-source-of-truth
                          consistency) runs against exactly that one file.
                          No other check has a `.html` target case.
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
                      Runs C1-C5, C7-C11 with payload-appropriate file
                      sets; C6 is skipped. C9 and C10 both sweep only the
                      payload-doc set (standard/, templates/, and tools/
                      excluding tools/fixtures/, plus schema/README.md) --
                      docs/guide/index.html is never swept in --payload
                      mode, so C10's version-anchor sub-check finds no
                      anchor to check there and passes trivially (the
                      framework-version anchor lives only in the guide,
                      which bootstrap.sh does not inject). C11 passes
                      trivially in --payload mode: `.agent/` governance
                      state is never part of the bootstrap.sh payload, so
                      C11 does not inspect the filesystem at all in this
                      mode (see C11 below). Exits 0 only if every
                      applicable check passed.

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

  C9  Repo-wide path resolution (narrative-truth: does every named path
      actually exist?). For the shipped-doc set UNION {docs/guide/index.html}
      (default mode), the payload-doc set (--payload mode, no guide), or a
      single --target `.md` file: strips a leading YAML frontmatter block
      if present and scans only the remaining BODY text -- frontmatter
      content is C1/C2's concern, not C9's -- with the extended regex
      `[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]*\.(md|json|sh|html|yml)`; i.e. only
      directory-qualified ('/'-containing) tokens ending in a shipped
      extension are treated as candidate path references (bare,
      non-'/'-qualified extension-bearing words -- cross-repo terms,
      same-directory markdown-link targets, ASCII tree-diagram leaf
      labels -- are never extracted). Each candidate token is resolved via
      `tools/verify_lib.sh`'s `vlib_path_resolves`, which strips trailing
      sentence punctuation and exempts placeholder/illustrative forms
      (tokens containing `NNN` or `XXX`, matching `step-<digits>`,
      containing the word `placeholder`, or ending in `/`) before testing
      `test -e` against the current working directory. On top of that
      inherited exemption, C9 applies two of its own, narrower exemptions
      before handing a token to `vlib_path_resolves`: any token beginning
      with the literal prefix `.nizam/` (the bootstrap.sh-created,
      consumer-side install root, which structurally never exists in this
      framework's own working tree); and the two literal tokens
      `.agent/capability_profile.json` and `.agent/debt.json` (naming the
      canonical artifact shape a schema/README.md 'Validates' column
      describes, not a claim that this repository's own `.agent/`
      directory contains such a file). Any remaining token that does not
      resolve is a C9 FAIL, reported as
      `<file>: unresolved path reference '<token>'`.

  C10 Single-source-of-truth consistency (narrative-truth: do the docs
      agree with each other and with the framework's own recorded state?).
      Sweeps the SAME set C9 sweeps in each mode (shipped-doc set UNION
      {docs/guide/index.html} by default; the payload-doc set in --payload
      mode; a single --target `.md` or `.html` file). Strips a leading YAML
      frontmatter block first, exactly as C9 does, then runs three
      independent sub-checks against the remaining BODY:
        (1) Payload-set consistency -- the body is made FORMAT-AGNOSTIC
            before checking: every HTML/XML-style tag span (`<...>`) is
            replaced with a single space (so `<code>tools/</code>` becomes
            ` tools/ ` and a `</p><p>` boundary becomes a plain space,
            regardless of whether the two sentences shared one physical
            source line), then every run of whitespace (including all
            newlines) collapses to a single space -- physical line-wrapping
            becomes irrelevant. The normalized text is then split into
            sentence segments wherever a `.`, `!`, or `?` is immediately
            followed by whitespace (never on `;` or `:`, and never inside a
            `.md`/`.json`/`.sh` filename token, since there the `.` is
            followed by a letter, not whitespace). Each segment is checked,
            in isolation, via `tools/verify_lib.sh`'s `vlib_no_stale_payload`
            (F-023): a segment that mentions `standard/`, `templates/`, and
            `schema/` together but omits `tools/` is a stale payload
            enumeration and fails this sub-check.
        (2) Discovery-order (P3-scoped) -- only where a file's BODY
            contains BOTH of the exact canonical labels 'Bootstrapped-
            consumer discovery' and 'Framework-checkout fallback' (the
            structural labels tools/interface.md Section 2 and the guide's
            mirrored discovery list both use verbatim) does this sub-check
            require the former to appear (by line number) before the
            latter -- a file mentioning neither or only one label is not
            describing the bootstrapped-consumer-vs-fallback sequence at
            all, and is therefore not applicable, not vacuously passed.
        (3) Framework-version anchor (External Anchor Rule) -- the
            expected version is read ONCE, directly from `NIZAM.json`'s
            `framework.version` (never re-derived from the doc under
            test); any `<meta name="framework-version" content="X">` or
            `<span id="footer-version">X</span>` value found in the body
            must equal it, or this sub-check fails.
      A file failing any of the three sub-checks is a single C10 FAIL,
      with each offending sub-check's detail tagged `[payload-set]`,
      `[discovery-order]`, or `[version-anchor]` and printed on its own
      indented line beneath. `tools/verify_lib.sh` is sourced once already
      (by C9, above); C10 composes its existing `vlib_no_stale_payload`
      primitive and never modifies the library.

  C11 Dogfood schema validation (does the framework's OWN durable .agent/
      audit trail actually conform to the schemas it ships?). Validates
      exactly three artifact families against the shipped, already-
      reconciled schemas via python3 + jsonschema (the same stack C4
      uses): `.agent/qa/*.json`, `.agent/contracts/*.json`, and
      `.agent/run_state.json`. ENFORCE-IF-PRESENT, SKIP-IF-ABSENT: each
      family is existence-guarded independently -- a family whose
      directory/file does not exist contributes no failure, so a fresh or
      ungoverned bootstrapped consumer with no `.agent/` at all passes
      this check trivially, while the framework's own populated `.agent/`
      is fully enforced. `.agent/qa/*.json` is CONTENT-ROUTED using a
      RESTRICTED rule: a top-level `review` key routes to
      schema/contract_review.schema.json; a top-level `qa_pass` or
      `verdict` key routes to schema/qa_verdict.schema.json; a file with
      NEITHER key is SKIPPED (not schema-validated at all) -- this default
      sweep deliberately never inspects `contract_id`, `circuit_breaker`,
      or `scope_budget`, which is why a circuit-breaker failure-history
      record with no shipped schema (carrying only `circuit_breaker`, not
      `review`/`qa_pass`/`verdict`) is correctly skipped rather than
      misrouted. `.agent/contracts/*.json` and `.agent/run_state.json`
      require no content routing -- each is validated directly, by path,
      against schema/contract.schema.json and schema/run_state.schema.json
      respectively. Under `--target`, a `.json` file is content-routed
      using the FULL rule (adding a top-level `contract_id` key ->
      schema/contract.schema.json, and a top-level `circuit_breaker` or
      `scope_budget` key -> schema/run_state.schema.json) -- this larger
      rule applies ONLY to `--target`, never to the default `.agent/qa/`
      sweep; a `--target` file matching none of the four keys falls
      through to the existing, unmodified C4 instead. Under `--payload`,
      C11 passes trivially without touching the filesystem: `.agent/` is
      never part of a bootstrap.sh-injected payload. `tools/verify_lib.sh`
      is never modified or consulted by C11 (none of its five primitives
      address JSON-Schema validation).

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
# C9 -- repo-wide path resolution (narrative-truth check)
# ---------------------------------------------------------------------------

# check_c9_path_resolution <file> [<file> ...]
#
# For each given file, strips a leading YAML frontmatter block (if present)
# and scans only the remaining body text with an extended regex that
# extracts directory-qualified ('/'-containing) tokens ending in a shipped
# extension. Applies two C9-specific exemptions (a `.nizam/`-prefix
# bootstrapped-consumer exemption, and the two named schema/README.md
# 'Validates'-column singleton-artifact tokens) BEFORE handing each
# remaining token to `vlib_path_resolves` (sourced from tools/verify_lib.sh,
# F-023), which strips trailing sentence punctuation, applies its own
# placeholder/illustrative/directory-only exemption, and tests the token
# against the current working directory. Composes from vlib_path_resolves
# rather than re-implementing path resolution; never modifies
# tools/verify_lib.sh.
check_c9_path_resolution() {
  local files=("$@")
  local errors=()
  local f body token e

  for f in "${files[@]}"; do
    if [ ! -f "${f}" ]; then
      errors+=("${f}: MISSING file")
      continue
    fi

    # Strip a leading YAML frontmatter block (first line '---' through the
    # next bare '---' line) if present; scan only the remaining BODY.
    body=$(awk '
      NR == 1 && $0 == "---" { in_frontmatter = 1; next }
      in_frontmatter && $0 == "---" { in_frontmatter = 0; next }
      in_frontmatter { next }
      { print }
    ' "${f}")

    while IFS= read -r token; do
      [ -z "${token}" ] && continue

      # C9-specific exemptions, applied BEFORE handing the token to
      # vlib_path_resolves (never inside tools/verify_lib.sh itself).
      case "${token}" in
        .nizam/*)
          continue
          ;;
      esac
      if [ "${token}" = ".agent/capability_profile.json" ] \
        || [ "${token}" = ".agent/debt.json" ]; then
        continue
      fi

      if ! vlib_path_resolves "${token}" >/dev/null 2>&1; then
        errors+=("${f}: unresolved path reference '${token}'")
      fi
    done < <(printf '%s\n' "${body}" \
      | grep -oE '[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]*\.(md|json|sh|html|yml)' \
      | LC_ALL=C sort -u)
  done

  if [ "${#errors[@]}" -eq 0 ]; then
    echo "[C9] PASS path-resolution"
    return 0
  fi

  echo "[C9] FAIL path-resolution"
  for e in "${errors[@]}"; do
    echo "  ${e}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# C10 -- single-source-of-truth consistency (payload-set / discovery-order /
# framework-version anchor)
# ---------------------------------------------------------------------------

# check_c10_consistency <file> [<file> ...]
#
# For each given file, strips a leading YAML frontmatter block (if present,
# identical convention to check_c9_path_resolution) and runs three
# independent sub-checks against the remaining BODY:
#
#   (1) payload-set consistency -- the body is normalized (HTML tags
#       replaced with a space, all whitespace collapsed) and split into
#       sentence segments on a `.`/`!`/`?` immediately followed by
#       whitespace (via a single python3 pass); each segment is checked,
#       in isolation, via tools/verify_lib.sh's vlib_no_stale_payload
#       (F-023, composed here, never modified).
#   (2) discovery-order (P3-scoped) -- when the body names BOTH the
#       'Bootstrapped-consumer discovery' and 'Framework-checkout
#       fallback' canonical labels, asserts the former precedes the
#       latter by line number; not applicable (no assertion) if either
#       label is absent.
#   (3) framework-version anchor (External Anchor Rule) -- any
#       <meta name="framework-version"> or <span id="footer-version">
#       value found in the body must equal NIZAM.json's framework.version
#       (read once from NIZAM.json, never re-derived from the doc under
#       test).
#
# Composes from vlib_no_stale_payload rather than re-implementing stale-
# payload detection; never modifies tools/verify_lib.sh.
check_c10_consistency() {
  local files=("$@")
  local errors=()
  local f body_tmp seg_tmp out
  local expected_version

  expected_version=$(python3 -c "import json; print(json.load(open('NIZAM.json'))['framework']['version'])")

  for f in "${files[@]}"; do
    if [ ! -f "${f}" ]; then
      errors+=("${f}: MISSING file")
      continue
    fi

    # Strip a leading YAML frontmatter block (identical convention to
    # check_c9_path_resolution); scan only the remaining BODY.
    body_tmp=$(mktemp)
    awk '
      NR == 1 && $0 == "---" { in_frontmatter = 1; next }
      in_frontmatter && $0 == "---" { in_frontmatter = 0; next }
      in_frontmatter { next }
      { print }
    ' "${f}" > "${body_tmp}"

    # --- sub-check (1): payload-set consistency (normalize -> segment) ---
    seg_tmp=$(mktemp)
    python3 - "${body_tmp}" > "${seg_tmp}" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
# Strip HTML/XML-style tags, replacing each with a space (not deleting) so
# tag-adjacent words are never wrongly concatenated (e.g. `the</code> hosts`).
text = re.sub(r"<[^>]*>", " ", text)
# Collapse every run of whitespace (including newlines) to a single space --
# physical line-wrapping is now irrelevant.
text = re.sub(r"\s+", " ", text).strip()
# Segment on a sentence terminator immediately followed by whitespace (or
# end-of-stream); never splits on `;`/`:`, never splits inside a filename
# token such as `standard/GIP.md` (the `.` there is followed by a letter,
# not whitespace).
for seg in re.split(r"(?<=[.!?])\s+", text):
    seg = seg.strip()
    if seg:
        print(seg)
PY
    if ! out=$(vlib_no_stale_payload "${seg_tmp}" 2>&1); then
      errors+=("${f}: [payload-set] ${out}")
    fi
    rm -f "${seg_tmp}"

    # --- sub-check (2): discovery-order (P3-scoped) ---
    local boot_line fallback_line
    boot_line=$(grep -inE 'bootstrapped-consumer discovery' "${body_tmp}" | head -1 | cut -d: -f1) || true
    fallback_line=$(grep -inE 'framework-checkout fallback' "${body_tmp}" | head -1 | cut -d: -f1) || true
    if [ -n "${boot_line}" ] && [ -n "${fallback_line}" ] && [ "${boot_line}" -gt "${fallback_line}" ]; then
      errors+=("${f}: [discovery-order] 'Framework-checkout fallback' (line ${fallback_line}) precedes 'Bootstrapped-consumer discovery' (line ${boot_line})")
    fi

    # --- sub-check (3): framework-version anchor (External Anchor Rule) ---
    local meta_version footer_version
    meta_version=$(grep -oE 'name="framework-version" content="[0-9]+\.[0-9]+\.[0-9]+"' "${body_tmp}" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
    if [ -n "${meta_version}" ] && [ "${meta_version}" != "${expected_version}" ]; then
      errors+=("${f}: [version-anchor] meta framework-version '${meta_version}' != NIZAM.json framework.version '${expected_version}'")
    fi
    footer_version=$(grep -oE 'id="footer-version">[0-9]+\.[0-9]+\.[0-9]+' "${body_tmp}" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
    if [ -n "${footer_version}" ] && [ "${footer_version}" != "${expected_version}" ]; then
      errors+=("${f}: [version-anchor] footer version '${footer_version}' != NIZAM.json framework.version '${expected_version}'")
    fi

    rm -f "${body_tmp}"
  done

  if [ "${#errors[@]}" -eq 0 ]; then
    echo "[C10] PASS consistency"
    return 0
  fi

  echo "[C10] FAIL consistency"
  local e
  for e in "${errors[@]}"; do
    echo "  ${e}"
  done
  return 1
}

# ---------------------------------------------------------------------------
# C11 -- dogfood schema validation of .agent/ audit artifacts
# ---------------------------------------------------------------------------

# check_c11_dogfood_sweep
#
# Default-mode, no-argument walker (its inputs are fixed, well-known
# repo-relative paths, not a swept doc set). Validates the framework's OWN
# durable .agent/ audit artifacts against the shipped, F-025-reconciled
# schemas, using python3 + jsonschema (the same stack C4 uses). Walks
# exactly three artifact families relative to CWD, each existence-guarded
# independently for consumer-safety (spec Sec 4.1): a family whose
# directory/file does not exist contributes zero errors -- skip-if-absent
# falls out of the same existence-guarded code path as enforce-if-present,
# with no special-cased branch, so a fresh/ungoverned bootstrapped consumer
# with no .agent/ at all passes this check trivially.
#
#   .agent/qa/*.json       -- content-routed using ONLY the RESTRICTED
#                              route universe: (a) a top-level `review` key
#                              -> schema/contract_review.schema.json; (b) a
#                              top-level `qa_pass` or `verdict` key ->
#                              schema/qa_verdict.schema.json; (e) neither ->
#                              SKIP (no schema is consulted at all). This
#                              function deliberately never checks for
#                              `contract_id`, `circuit_breaker`, or
#                              `scope_budget` -- those routes are consulted
#                              ONLY by check_c11_or_c4_target's --target
#                              dispatcher below, never here. This asymmetry
#                              is what keeps `.agent/qa/027_failures.json`
#                              (a circuit-breaker failure-history record
#                              with no shipped schema, carrying only
#                              `circuit_breaker`, not `review`/`qa_pass`/
#                              `verdict`) correctly SKIPPED rather than
#                              misrouted to schema/run_state.schema.json.
#   .agent/contracts/*.json -- validated directly against
#                              schema/contract.schema.json BY PATH (the
#                              directory itself disambiguates -- no content
#                              routing performed or needed).
#   .agent/run_state.json   -- validated directly against
#                              schema/run_state.schema.json BY PATH
#                              (likewise no content routing).
#
# Composes python3 + jsonschema directly (C4's stack); never modifies
# tools/verify_lib.sh (none of its five primitives address JSON-Schema
# validation).
check_c11_dogfood_sweep() {
  local out

  if out=$(python3 - <<'PY'
import glob
import json
import os
import sys

import jsonschema


def load_schema(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


errors = []

if os.path.isdir(".agent/qa"):
    try:
        qa_schema = load_schema("schema/qa_verdict.schema.json")
        cr_schema = load_schema("schema/contract_review.schema.json")
    except OSError as exc:
        print(f".agent/qa: could not read a required schema: {exc}")
        sys.exit(1)

    for f in sorted(glob.glob(".agent/qa/*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{f}: not valid JSON: {exc}")
            continue
        if not isinstance(doc, dict):
            errors.append(f"{f}: does not parse to a JSON object")
            continue

        # RESTRICTED route universe: (a) review, (b) qa_pass|verdict, else
        # (e) skip. Deliberately never consults contract_id/
        # circuit_breaker/scope_budget -- those are --target-only routes.
        if "review" in doc:
            schema = cr_schema
        elif "qa_pass" in doc or "verdict" in doc:
            schema = qa_schema
        else:
            continue

        try:
            jsonschema.validate(instance=doc, schema=schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{f}: schema violation: {exc.message}")

if os.path.isdir(".agent/contracts"):
    try:
        contract_schema = load_schema("schema/contract.schema.json")
    except OSError as exc:
        errors.append(f".agent/contracts: could not read schema/contract.schema.json: {exc}")
        contract_schema = None

    if contract_schema is not None:
        for f in sorted(glob.glob(".agent/contracts/*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{f}: not valid JSON: {exc}")
                continue
            try:
                jsonschema.validate(instance=doc, schema=contract_schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"{f}: schema violation: {exc.message}")

if os.path.isfile(".agent/run_state.json"):
    try:
        rs_schema = load_schema("schema/run_state.schema.json")
        with open(".agent/run_state.json", "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        jsonschema.validate(instance=doc, schema=rs_schema)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f".agent/run_state.json: not valid JSON: {exc}")
    except jsonschema.ValidationError as exc:
        errors.append(f".agent/run_state.json: schema violation: {exc.message}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
sys.exit(0)
PY
  ); then
    echo "[C11] PASS dogfood"
    return 0
  fi

  echo "[C11] FAIL dogfood"
  echo "${out}" | sed 's/^/  /'
  return 1
}

# check_c11_dogfood_target <file> <route>
#
# Validates one file against the schema named by <route> -- one of
# contract_review/qa_verdict/contract/run_state. Used only by
# check_c11_or_c4_target's --target dispatcher, below.
check_c11_dogfood_target() {
  local target="$1"
  local route="$2"
  local out

  if out=$(python3 - "${target}" "${route}" <<'PY'
import json
import sys

import jsonschema

path, route = sys.argv[1], sys.argv[2]

schema_paths = {
    "contract_review": "schema/contract_review.schema.json",
    "qa_verdict": "schema/qa_verdict.schema.json",
    "contract": "schema/contract.schema.json",
    "run_state": "schema/run_state.schema.json",
}
schema_path = schema_paths[route]

try:
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
except OSError as exc:
    print(f"{path}: could not read {schema_path}: {exc}")
    sys.exit(1)

try:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"{path}: not valid JSON: {exc}")
    sys.exit(1)

try:
    jsonschema.validate(instance=doc, schema=schema)
except jsonschema.ValidationError as exc:
    print(f"{path}: schema violation ({route}): {exc.message}")
    sys.exit(1)

sys.exit(0)
PY
  ); then
    echo "[C11] PASS dogfood --target routed: ${route}"
    return 0
  fi

  echo "[C11] FAIL dogfood --target routed: ${route}"
  echo "  ${out}"
  return 1
}

# check_c11_dogfood_payload_skip
#
# --payload mode is a DESIGNED, disk-free trivial pass: .agent/ is
# orchestrator/governance state that bootstrap.sh NEVER injects into a
# consumer payload (the injected set is exactly standard/, templates/,
# schema/, tools/, NIZAM.json), so C11 has nothing to enforce in payload
# mode regardless of whether .agent/ happens to physically exist in CWD
# (which it always does when --payload is invoked from within the
# framework's own checkout -- --payload does not chroot or cd into a
# separately-bootstrapped consumer directory, it only restricts the FILE
# SETS the other checks sweep). This is a COUNTED pass (unlike C6's
# uncounted SKIP), since C11 genuinely is applicable in concept to payload
# validation (spec Sec 4.1) -- it just resolves to a trivial pass by
# design, not a suppressed check.
check_c11_dogfood_payload_skip() {
  echo "[C11] PASS dogfood (payload mode: .agent/ governance state is not part of the bootstrap.sh payload; passes trivially by design, not a suppressed check)"
  return 0
}

# check_c11_or_c4_target <file>
#
# --target dispatcher for a `.json` file: content-routes using the FULL
# route universe -- (a) review, (b) qa_pass|verdict, (c) contract_id, (d)
# circuit_breaker|scope_budget -- to check_c11_dogfood_target when a route
# is found, or falls through to the existing, unmodified check_c4_index
# when none of the four discriminators is present (e.g. NIZAM.json,
# tools/fixtures/broken_index.json). This is the ONLY place in this file
# where routes (c)/(d) are ever evaluated; check_c4_index's own function
# body is never touched.
check_c11_or_c4_target() {
  local target="$1"
  local route

  route=$(python3 - "${target}" <<'PY'
import json
import sys

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
except (OSError, json.JSONDecodeError):
    print("none")
    sys.exit(0)

if not isinstance(doc, dict):
    print("none")
    sys.exit(0)

if "review" in doc:
    print("contract_review")
elif "qa_pass" in doc or "verdict" in doc:
    print("qa_verdict")
elif "contract_id" in doc:
    print("contract")
elif "circuit_breaker" in doc or "scope_budget" in doc:
    print("run_state")
else:
    print("none")
PY
)

  if [ "${route}" = "none" ]; then
    check_c4_index "${target}"
  else
    check_c11_dogfood_target "${target}" "${route}"
  fi
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

  [ -f tools/verify_lib.sh ] \
    || die "required library tools/verify_lib.sh not found. tools/validate.sh's C9 check cannot run without it."
  # shellcheck source=tools/verify_lib.sh
  source tools/verify_lib.sh

  local passed=0
  local failed=0

  if [ "${VALIDATOR_MODE}" = "target" ]; then
    [ -f "${target}" ] || die "--target file '${target}' does not exist."
    case "${target}" in
      *.md)
        check_c1_frontmatter_schema "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c2_format "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c3_fences "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c9_path_resolution "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        check_c10_consistency "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        ;;
      *.json)
        check_c11_or_c4_target "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        ;;
      *.html)
        check_c10_consistency "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))
        ;;
      *)
        die "--target file '${target}' is neither .md, .json, nor .html -- no applicable checks."
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
    check_c9_path_resolution "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c10_consistency "${payload_md[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c11_dogfood_payload_skip && passed=$((passed + 1)) || failed=$((failed + 1))

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

    local c9_default_files=("${shipped_md[@]}")
    if [ -f docs/guide/index.html ]; then
      c9_default_files+=("docs/guide/index.html")
    fi
    check_c9_path_resolution "${c9_default_files[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c10_consistency "${c9_default_files[@]}" && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c11_dogfood_sweep && passed=$((passed + 1)) || failed=$((failed + 1))

    echo "SUMMARY: ${passed} passed, ${failed} failed"
  fi

  [ "${failed}" -eq 0 ]
}

main "$@"
