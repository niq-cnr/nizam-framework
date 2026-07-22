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
#   (default, no args)   Full repo sweep: runs checks C1-C15.
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
  (no arguments)      Full repo sweep. Runs all 15 checks (C1-C15) and
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
                          between C4, C11, and C12. If the file carries a
                          top-level `review` key, a `verdict`+`execution_id`
                          pair, a top-level `qa_pass` or `verdict` key, a
                          top-level `contract_id` key, or a top-level
                          `circuit_breaker` or `scope_budget` key (checked in
                          that order), it routes to C12 (ecosystem
                          preflight_verdict) or C11 (dogfood schema
                          validation) against exactly that one file, validated
                          against schema/contract_review.schema.json,
                          schema/preflight_verdict.schema.json,
                          schema/qa_verdict.schema.json,
                          schema/contract.schema.json, or
                          schema/run_state.schema.json respectively. Failing
                          those, an ecosystem_baseline shape (the six
                          `*_references` arrays), an engineering_finding
                          shape (`closure_criteria`), or an audit_delta shape
                          (top-level `earlier`+`later`+`transitions`, matched
                          ahead of the generic `verdict`/`qa_pass` routes so an
                          additive key cannot divert a valid delta) routes to C12
                          against schema/ecosystem_baseline.schema.json,
                          schema/engineering_finding.schema.json, or
                          schema/audit_delta.schema.json (the first three
                          families landed via NDEBT-015, feature 052, which
                          fixed their former misroute to C4/C11 that failed
                          regardless of polarity; audit_delta joined later).
                          C4 does NOT also run in any of these
                          routed cases. Otherwise (no recognized key present
                          -- e.g. NIZAM.json or a Nizam-index-shaped fixture)
                          C4 (schema validation + indexed-path walker) runs
                          against exactly that one file, exactly as before C11
                          existed.
                        - For a `.html` target: C10 (single-source-of-truth
                          consistency) runs against exactly that one file.
                          No other check has a `.html` target case.
                      Checks that are inherently repo-wide (C5 branding
                      sweep, C6 bootstrap.sh sanity, C7 module-README
                      presence, C8 git-history version/changelog diff) do
                      NOT run under --target. Exits non-zero if any
                      applicable check fails. Files in tools/fixtures/ are
                      read only under --target and by the default sweep's
                      C12 ecosystem-fixture check.

  --payload           Consumer-payload mode. Validates only the subset of
                      checks relevant to a `bootstrap.sh`-injected consumer
                      payload (standard/, templates/, schema/, tools/, and
                      NIZAM.json). UNLIKE the default/--target modes (which
                      evaluate the tree at CWD), --payload anchors to its own
                      payload root -- the parent of the tools/ directory this
                      script lives in -- so `bash .nizam/tools/validate.sh
                      --payload` from a consumer repository root behaves
                      identically to `cd .nizam && bash tools/validate.sh
                      --payload` (NDEBT-012 / issue #18, feature 050).
                      Framework-envelope files that are intentionally absent
                      from consumer payloads (CONTEXT.md, README.md,
                      CHANGELOG.md, bootstrap.sh, methodology/, registry/,
                      docs/, ecosystem/) are not required; directory-qualified
                      cross-references into those non-injected paths are
                      carved out of C9 in payload mode (NDEBT-004) exactly as
                      C4 carves them out of the NIZAM.json index.
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
      skipping the literal `NA`) resolves on disk. Indexed paths must be
      repo-relative and stay inside the repo: an absolute path, a path
      whose normalized form escapes the root (leading `..`), or a path
      that resolves through a symlink to outside the repo root FAILs in
      every mode. In --payload mode the registry schema is optional
      (skipped if missing), and paths under the non-injected dirs
      (registry/, docs/) are skipped as expected-absent while paths under
      the injected dirs (standard/, templates/, schema/, tools/,
      methodology/, ecosystem/ -- the last two joined the payload in
      feature 051) are still required to resolve; the carve-out tests the
      NORMALIZED path, so a traversal spelling
      (e.g. `docs/../tools/x.md`) cannot ride a skip.

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
      directory contains such a file). In --payload mode ONLY, a third,
      mode-gated carve-out (NDEBT-004, the C9 analog of C4's payload
      carve-out) additionally skips any directory-qualified token whose
      first segment is NOT an injected-payload dir (standard/, templates/,
      schema/, tools/): a consumer .nizam/ subset legitimately carries
      cross-references into non-injected framework-envelope paths
      (methodology/, ecosystem/, registry/, docs/, .agent/, .github/, ...)
      it reaches via the pinned framework checkout, not via the injected
      subset. The default full sweep applies NO such carve-out, so a stale
      non-injected reference is still caught there. Any remaining token that
      does not resolve is a C9 FAIL, reported as
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

  C12 Ecosystem schema-family fixture validation (are the ecosystem schema
      families' fixtures actually load-bearing, or merely present?). For
      each of the seven families -- the three shipped in features 037-039
      (baseline, preflight-verdict, engineering-finding), plus audit_delta
      (feature 057), ecosystem_membership (feature 075), the
      membership-run aggregate membership_result (feature 077), and the
      reconciliation_plan (feature 080; NIP-0002 Stage 4) --
      validates every matching
      `tools/fixtures/<family>_*.json` fixture, via python3 + jsonschema,
      against its shipped schema (`schema/ecosystem_baseline.schema.json`,
      `schema/preflight_verdict.schema.json`,
      `schema/engineering_finding.schema.json`,
      `schema/audit_delta.schema.json`,
      `schema/ecosystem_membership.schema.json`,
      `schema/ecosystem_membership_result.schema.json`, and
      `schema/reconciliation_plan.schema.json`). A fixture is
      NEGATIVE (MUST fail validation) iff its filename carries the canonical
      delimited-lowercase token `_neg_` or `_invalid_`; every other
      conforming fixture is POSITIVE and MUST validate. A positive fixture
      that fails, or a negative fixture that validates, is a single C12 FAIL
      naming the offending path and schema. NAMING CONFORMANCE (NDEBT-016): a
      basename carrying a case-insensitive `neg`/`invalid` look-alike that is
      NOT the canonical token (uppercase `_NEG_`, full-word `_negative_`) is
      itself a named FAIL, so the polarity classifier cannot be gamed by a
      look-alike name. Each family MUST also contribute at least one POSITIVE
      and one NEGATIVE matched fixture -- a family contributing zero of either
      polarity (e.g. its fixtures were moved, renamed, or deleted) is itself a
      named FAIL, never a silent pass (NDEBT-009's own dormancy-regression
      meta-risk, guarded against structurally). This full-sweep form is
      default-mode only and does not run under `--payload` (no acceptance test
      requires payload-mode fixture coverage; consumer payloads carry no
      governed `.agent/` audit trail for these families to reconcile against).
      Under `--target`, a single ecosystem fixture IS routed to a discriminating
      per-file C12 verdict (NDEBT-015). The standing self-test that exercises
      every negative fixture against its targeted check (closing NDEBT-009's
      dormancy for the non-ecosystem fixtures too) is `tools/fixtures_self_test.sh`.

  C13 Skill-index integrity (does every capability pointer in
      tools/skill.json resolve?). JSON-parses `tools/skill.json` and
      requires the `entry_point` and every `capabilities[].module` path to
      resolve to an existing file; a missing/empty `entry_point` or an
      empty `capabilities` array is itself a FAIL, so the check cannot go
      vacuous. Closes NDEBT-007: the release_train capability shipped a
      retired module pointer from v0.4.0 through v0.5.3 because nothing
      parsed this file's content. Runs in the full sweep AND under
      `--payload`; in payload mode, pointers into the non-injected
      directories (registry/, docs/) are skipped -- the same carve-out
      set and normalized-path discipline C4 uses (absolute or
      root-escaping pointers FAIL in every mode; traversal spellings
      cannot ride the skip); methodology/ and ecosystem/ joined the
      injected payload in feature 051 (NDEBT-008) and are now required to
      resolve. Negative fixture:
      `tools/fixtures/skill_index_neg_dangling_module.json`, exercised as a
      standing test by `tools/fixtures_self_test.sh` (feature 052 / NDEBT-009),
      which substitutes it for tools/skill.json and asserts the `[C13] FAIL`.

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

  # methodology/ and ecosystem/ joined the injected payload in feature 051
  # (H-PAYLOAD-CONTRACT), so their .md files are now part of the payload-doc
  # set that C1/C2/C3/C5/C8/C9/C10 sweep in --payload mode.
  for d in standard templates methodology ecosystem; do
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

# Path hygiene BEFORE any skip/resolve decision (feature 049 review
# hardening): the index must stay inside the repo. A raw prefix test on
# the un-normalized string would let a traversal spelling like
# `ecosystem/../tools/x.md` ride the payload carve-out while really
# pointing into an injected dir, and `os.path.exists` on an absolute
# path like `/etc/hosts` would count host files as resolved index
# content. Absolute and root-escaping entries FAIL in every mode.
root = os.path.realpath(os.getcwd())
normalized = []
out_of_tree = []
for p in paths:
    if p == "NA":
        continue
    norm = os.path.normpath(p)
    if os.path.isabs(p) or norm == ".." or norm.startswith("../"):
        out_of_tree.append(p)
    else:
        normalized.append(norm)

if out_of_tree:
    print(f"{path}: indexed path(s) absolute or escaping the repo root: {out_of_tree}")
    sys.exit(1)

# Symlink-escape check runs on every path that EXISTS on disk, in every
# mode, and BEFORE the payload carve-out (PR #28 review): a present path
# that resolves outside the repo root is rejected even under a carve-out
# dir -- otherwise a symlinked `ecosystem/evil -> /etc` would ride the
# payload skip and defeat the all-mode escape rule. lexists (not exists)
# so a broken symlink escaping the root is still caught; genuinely-absent
# carve-out paths (lexists False) stay allowed as expected-absent.
escaped = []
for p in normalized:
    if os.path.lexists(p):
        real = os.path.realpath(p)
        if real != root and not real.startswith(root + os.sep):
            escaped.append(p)
if escaped:
    print(f"{path}: indexed path(s) resolve outside the repo root (symlink escape): {escaped}")
    sys.exit(1)

if mode == "payload":
    # Non-injected framework-envelope dirs, skipped as expected-absent in a
    # consumer payload. NARROWED in feature 051 (H-PAYLOAD-CONTRACT): only
    # registry/ and docs/ remain non-injected -- methodology/ and ecosystem/
    # joined the bootstrap-injected payload (they were carved out here on an
    # interim basis by F-049/F-050 pending this decision), so NIZAM.json's
    # methodology/ and ecosystem/ paths are now REQUIRED to resolve in a
    # consumer install exactly like the other injected dirs.
    skipped_dirs = {"registry", "docs"}
    normalized = [
        p for p in normalized
        if not any(p == d or p.startswith(d + "/") for d in skipped_dirs)
    ]

missing = [p for p in normalized if not os.path.exists(p)]
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
# extension. Applies C9-specific exemptions (a `.nizam/`-prefix
# bootstrapped-consumer exemption; the two named schema/README.md
# 'Validates'-column singleton-artifact tokens; and -- in --payload mode
# only, NDEBT-004, the C9 analog of C4's payload carve-out -- any reference
# NOT under an injected-payload prefix (standard/, templates/, schema/,
# tools/), since such references are expected-absent in a consumer subset;
# the default full sweep applies no carve-out) BEFORE handing each
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

      # NDEBT-004 (feature 050): the C9 analog of C4's payload carve-out. In
      # --payload mode a directory-qualified reference is only REQUIRED to
      # resolve if its target is part of the bootstrap-injected payload.
      # EXTENDED in feature 051 (H-PAYLOAD-CONTRACT): methodology/ and
      # ecosystem/ joined the injected payload, so references into them are
      # now REQUIRED to resolve (they were skipped here on an interim basis
      # by F-050 pending the decision). References into the still-non-injected
      # framework-envelope paths (registry/, docs/, .agent/, .github/, ...)
      # remain expected-absent in a consumer .nizam/ subset and are skipped.
      # The DEFAULT full sweep applies NO carve-out, so a stale non-injected
      # reference is still caught there.
      if [ "${VALIDATOR_MODE:-default}" = "payload" ]; then
        case "${token}" in
          standard/*|templates/*|schema/*|tools/*|methodology/*|ecosystem/*) ;;
          *) continue ;;
        esac
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
# mode regardless of where CWD is. As of feature 050 (NDEBT-012 / issue
# #18) --payload anchors to its own payload root, so on a real consumer
# install CWD becomes the injected .nizam/ payload itself -- which still
# carries no .agent/, so C11 has nothing to enforce either way (and on the
# framework's own checkout the payload root simply equals the repo root).
# This is a COUNTED pass (unlike C6's
# uncounted SKIP), since C11 genuinely is applicable in concept to payload
# validation (spec Sec 4.1) -- it just resolves to a trivial pass by
# design, not a suppressed check.
check_c11_dogfood_payload_skip() {
  echo "[C11] PASS dogfood (payload mode: .agent/ governance state is not part of the bootstrap.sh payload; passes trivially by design, not a suppressed check)"
  return 0
}

# ---------------------------------------------------------------------------
# C12 -- ecosystem schema-family fixture validation (NDEBT-009 fix, scoped to
# the ecosystem schema families: the three shipped in features 037/038/039
# plus audit_delta -- proves the tools/fixtures/{ecosystem_baseline,
# preflight_verdict,engineering_finding,audit_delta}_*.json fixtures are
# load-bearing, not merely present).
# The full-sweep check_c12_ecosystem_fixtures below is default-mode only
# (mirrors C6/C7's repo-wide-only precedent) and not run under --payload (no
# acceptance test requires payload-mode fixture coverage; see NON-GOALS). As
# of feature 052 (NDEBT-015) a `--target` invocation against a single
# ecosystem fixture IS routed -- to check_c12_target, further below -- so it
# emits a discriminating [C12] verdict instead of misrouting to C4/C11; the
# full-sweep polarity/dormancy guard and the single-file --target validation
# are two distinct entry points that share the family schemas.
# ---------------------------------------------------------------------------

# check_c12_ecosystem_fixtures
#
# For each of the seven families, validates every matching
# tools/fixtures/<family>_*.json fixture against its shipped schema. A
# fixture is NEGATIVE (MUST fail schema validation) iff its filename
# contains the canonical delimited token '_neg_' or '_invalid_' -- checked as
# an explicit NEGATIVE marker, never derived from the ABSENCE of the substring
# 'valid' (which is itself a substring of 'invalid' and would silently
# misclassify negative fixtures as positive; NDEBT-014 defect class 4). Every
# other matching (conforming) fixture is POSITIVE and MUST validate. A positive
# fixture that fails, or a negative fixture that validates, is this check's
# failure.
#
# NAMING CONFORMANCE (NDEBT-016, feature 052): the polarity marker is reserved.
# A basename carrying a case-insensitive `neg`/`invalid` look-alike that is NOT
# the canonical delimited-lowercase token (uppercase `_NEG_`, full-word
# `_negative_`, etc.) is a named FAIL, so the classifier cannot be gamed by a
# look-alike name; the earlier case-sensitive regex tolerated those spellings
# for future fixtures. A schema-valid doc that borrows a canonical negative
# marker is likewise caught (as "negative unexpectedly VALIDATED").
#
# DORMANCY GUARD (this check's own meta-risk, per NDEBT-009's exact failure
# mode -- a fixture-driver check that stops inspecting anything, e.g. because
# its fixtures were moved/renamed/deleted, must NOT silently pass): each
# family MUST contribute at least one POSITIVE and at least one NEGATIVE
# matched fixture. A family contributing zero of either polarity is itself a
# named failure -- MINIMUM_PER_FAMILY is never satisfied by "no files to
# check".
check_c12_ecosystem_fixtures() {
  local py_out
  py_out=$(python3 - <<'PY'
import glob
import json
import re
import sys

import jsonschema

FAMILIES = {
    "ecosystem_baseline": "schema/ecosystem_baseline.schema.json",
    "preflight_verdict": "schema/preflight_verdict.schema.json",
    "engineering_finding": "schema/engineering_finding.schema.json",
    "audit_delta": "schema/audit_delta.schema.json",
    "ecosystem_membership": "schema/ecosystem_membership.schema.json",
    "membership_result": "schema/ecosystem_membership_result.schema.json",
    "reconciliation_plan": "schema/reconciliation_plan.schema.json",
}


def reconciliation_plan_cycles(doc):
    """The topological-order invariant (ecosystem/04_dependency_reconciliation.md
    Section 4): a reconciliation plan's `order` MUST be a valid topological sort of
    an acyclic `depends_on` edge set -- a cyclic dependency set has no valid order
    and forces plan_verdict FAIL. Cycle detection spans the packet graph and is not
    expressible in JSON Schema, so C12 enforces it in code (mirroring
    membership_multilist_entries and repository_revision_inconsistencies): returns
    True iff the packets' depends_on edges contain at least one cycle. Only edges
    referencing a declared packet id participate (a dangling edge is a shape concern,
    not a cycle)."""
    packets = doc.get("packets", [])
    if not isinstance(packets, list):
        return False
    ids = {p["id"] for p in packets if isinstance(p, dict) and isinstance(p.get("id"), str)}
    graph = {}
    for p in packets:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str):
            continue
        deps = p.get("depends_on", [])
        graph[p["id"]] = [d for d in deps if isinstance(d, str) and d in ids] if isinstance(deps, list) else []
    # DFS with a colour marker: WHITE(unseen)/GREY(on stack)/BLACK(done); a GREY
    # revisit is a back edge -> cycle.
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}

    def has_back_edge(node):
        colour[node] = GREY
        for nxt in graph.get(node, []):
            if colour.get(nxt, BLACK) == GREY:
                return True
            if colour.get(nxt, BLACK) == WHITE and has_back_edge(nxt):
                return True
        colour[node] = BLACK
        return False

    return any(colour[node] == WHITE and has_back_edge(node) for node in graph)


def membership_multilist_entries(doc):
    """The exactly-one-list invariant (registry/scope_definition_patterns.md
    Section 2.1 / 2.3): an entry (by `name`) MUST appear in exactly one scope
    list. A name in two lists is drift (Section 5 rule 4) -- a project copied,
    not moved, on promotion. The constraint spans sibling arrays and is not
    expressible in JSON Schema, so C12 enforces it in code, mirroring
    repository_revision_inconsistencies and audit_delta_duplicate_ids."""
    counts = {}
    for scope_list in ("in_scope", "incubating", "reference_archive", "out_of_scope"):
        items = doc.get(scope_list, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    counts[item["name"]] = counts.get(item["name"], 0) + 1
    return sorted(name for name, n in counts.items() if n > 1)


def repository_revision_inconsistencies(doc):
    """NDEBT-023: within repository_references, entries sharing the same
    `repository` MUST share the same `revision`. Revisions are compared only
    among entries KNOWN to be the same repository (by the explicit key), so
    distinct repositories -- and the dependency tool-version "revision" -- never
    false-positive. This relational cross-item rule is not expressible in JSON
    Schema, so C12 enforces it in code, mirroring the capture tool's own
    find_repository_revision_inconsistencies (tools/ecosystem_preflight.py)."""
    by_repo = {}
    refs = doc.get("repository_references", [])
    if isinstance(refs, list):
        for item in refs:
            if not isinstance(item, dict):
                continue
            repo = item.get("repository")
            rev = item.get("revision")
            if not isinstance(repo, str) or not isinstance(rev, str):
                continue
            by_repo.setdefault(repo, set()).add(rev)
    return sorted(r for r, revs in by_repo.items() if len(revs) > 1)


def audit_delta_duplicate_ids(doc):
    """ecosystem/07_progress_comparison.md Sec 3: every finding present in either
    input receives EXACTLY ONE transition class; a finding "assigned to more than
    one class at once, is not a valid comparison result". The same `id` appearing
    in two of the five buckets (or twice within one) is therefore invalid, but the
    constraint spans sibling arrays and is not expressible in JSON Schema, so C12
    enforces it in code -- mirroring repository_revision_inconsistencies above."""
    counts = {}
    transitions = doc.get("transitions", {})
    if isinstance(transitions, dict):
        for bucket in ("new", "resolved", "reopened", "persisting", "stale"):
            items = transitions.get(bucket, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and isinstance(item.get("id"), str):
                        counts[item["id"]] = counts.get(item["id"], 0) + 1
    return sorted(fid for fid, n in counts.items() if n > 1)


# NDEBT-016 (feature 052): the polarity marker is AUTHORITATIVE and RESERVED.
# A fixture is NEGATIVE iff its basename carries the canonical, delimited,
# lowercase token `_neg_`/`_invalid_` (CANONICAL_NEG). To stop the classifier
# being gamed by look-alike names, a CONFORMANCE guard rejects any basename
# carrying a case-insensitive `neg`/`invalid` letter-sequence that is NOT that
# canonical token -- uppercase (`_NEG_`), full-word (`_negative_`), or any
# other non-delimited spelling -- FAILing it by name rather than silently
# (mis)classifying it. The earlier case-sensitive regex left three dodges for
# FUTURE names (none of the shipped fixtures were affected): full-word,
# uppercase, and false-trigger. Full-word/uppercase are now conformance FAILs;
# the false-trigger (a positive "invalid-input-handling" doc borrowing the
# reserved token) is caught by the polarity assertion below -- a schema-VALID
# doc under a canonical negative marker FAILs as "negative unexpectedly
# VALIDATED", so the reserved token cannot be borrowed by a positive fixture.
CANONICAL_NEG = re.compile(r"(?:^|_)(?:neg|invalid)(?:_|\.)")
LOOKALIKE = re.compile(r"neg|invalid", re.IGNORECASE)

failures = []
for family, schema_path in FAMILIES.items():
    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    paths = sorted(glob.glob(f"tools/fixtures/{family}_*.json"))

    # Conformance gate: a basename with a neg/invalid look-alike that is not
    # the canonical delimited-lowercase token is non-conforming; it is removed
    # from classification (its polarity is undefined until renamed) and
    # reported. Conforming names classify by the canonical token alone.
    conforming = []
    for path in paths:
        name = path.rsplit("/", 1)[-1]
        if LOOKALIKE.search(name) and not CANONICAL_NEG.search(name):
            failures.append(
                f"{path}: non-conforming polarity marker -- a negative fixture MUST "
                "use the delimited lowercase token '_neg_' or '_invalid_' (NDEBT-016)"
            )
            continue
        conforming.append(path)

    positive_paths = [p for p in conforming if not CANONICAL_NEG.search(p.rsplit("/", 1)[-1])]
    negative_paths = [p for p in conforming if CANONICAL_NEG.search(p.rsplit("/", 1)[-1])]

    if not positive_paths:
        failures.append(
            f"{family}: zero POSITIVE fixtures matched tools/fixtures/{family}_*.json "
            "-- dormant or missing coverage (NDEBT-009 regression)"
        )
    if not negative_paths:
        failures.append(
            f"{family}: zero NEGATIVE fixtures matched tools/fixtures/{family}_*.json "
            "-- dormant or missing coverage (NDEBT-009 regression)"
        )

    for path in conforming:
        is_negative = path in negative_paths
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        try:
            jsonschema.validate(data, schema)
            is_valid = True
        except jsonschema.ValidationError:
            is_valid = False
        # NDEBT-023: a schema-valid ecosystem_baseline that declares
        # inconsistent same-repository revisions is NOT a valid baseline; the
        # code-level check completes the schema's coverage so the negative
        # fixture is caught by polarity rather than validating unexpectedly.
        if is_valid and family == "ecosystem_baseline" and repository_revision_inconsistencies(data):
            is_valid = False
        # Sec 3: a schema-valid audit_delta that classifies one finding id into
        # more than one transition bucket is NOT a valid comparison; the
        # code-level check completes the schema's coverage.
        if is_valid and family == "audit_delta" and audit_delta_duplicate_ids(data):
            is_valid = False
        # NDEBT-031: a schema-valid membership registry that lists the same entry
        # in two scope lists violates the exactly-one-list invariant; the
        # code-level check completes the schema's coverage so the multilist
        # negative fixture is caught by polarity rather than validating.
        if is_valid and family == "ecosystem_membership" and membership_multilist_entries(data):
            is_valid = False
        # NDEBT-035: a schema-valid reconciliation_plan whose depends_on graph
        # contains a cycle cannot be a PASS plan (no valid topological order
        # exists); the code-level check completes the schema's coverage so the
        # cyclic negative fixture is caught by polarity rather than validating.
        if is_valid and family == "reconciliation_plan" and reconciliation_plan_cycles(data) and data.get("plan_verdict") == "PASS":
            is_valid = False
        if is_negative and is_valid:
            failures.append(f"{path}: negative fixture unexpectedly VALIDATED against {schema_path}")
        elif not is_negative and not is_valid:
            failures.append(f"{path}: positive fixture unexpectedly FAILED to validate against {schema_path}")

for line in failures:
    print(line)
sys.exit(1 if failures else 0)
PY
)
  local rc=$?
  if [ "${rc}" -eq 0 ]; then
    echo "[C12] PASS ecosystem-fixtures"
    return 0
  fi
  echo "[C12] FAIL ecosystem-fixtures"
  echo "${py_out}" | sed 's/^/  /'
  return 1
}

# check_c12_target <file> <family>
#
# NDEBT-015 (feature 052): single-fixture ecosystem-schema validation for the
# `--target` dispatcher. The full-sweep check_c12_ecosystem_fixtures validates
# EVERY fixture of all seven families with a polarity/dormancy guard; this
# variant validates exactly ONE `--target` file against the schema of the
# family the router (check_c11_or_c4_target) identified, emitting a
# discriminating [C12] verdict -- a valid fixture PASSes, a negative fixture
# FAILs. (Before feature 052 these files fell through to C4 or misrouted to
# C11's qa_verdict route and failed regardless of polarity: zero signal.) It
# does NOT apply the naming-polarity/conformance classification -- under
# --target the caller names one file explicitly and the schema verdict IS the
# signal; polarity is the caller's to interpret.
check_c12_target() {
  local target="$1"
  local family="$2"
  local out

  if out=$(python3 - "${target}" "${family}" <<'PY'
import json
import sys

import jsonschema

path, family = sys.argv[1], sys.argv[2]

schema_paths = {
    "ecosystem_baseline": "schema/ecosystem_baseline.schema.json",
    "preflight_verdict": "schema/preflight_verdict.schema.json",
    "engineering_finding": "schema/engineering_finding.schema.json",
    "audit_delta": "schema/audit_delta.schema.json",
    "ecosystem_membership": "schema/ecosystem_membership.schema.json",
    "membership_result": "schema/ecosystem_membership_result.schema.json",
    "reconciliation_plan": "schema/reconciliation_plan.schema.json",
}
schema_path = schema_paths[family]

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
    print(f"{path}: schema violation ({family}): {exc.message}")
    sys.exit(1)

# NDEBT-023: same-repo revision-consistency is a code-level rule the schema
# cannot express; mirror the full-sweep C12 check (and the capture tool's
# find_repository_revision_inconsistencies) so a --target invocation against a
# schema-valid-but-inconsistent baseline is caught, not passed.
if family == "ecosystem_baseline":
    by_repo = {}
    refs = doc.get("repository_references", [])
    if isinstance(refs, list):
        for item in refs:
            if not isinstance(item, dict):
                continue
            repo = item.get("repository")
            rev = item.get("revision")
            if not isinstance(repo, str) or not isinstance(rev, str):
                continue
            by_repo.setdefault(repo, set()).add(rev)
    inconsistent = sorted(r for r, revs in by_repo.items() if len(revs) > 1)
    if inconsistent:
        print(f"{path}: same-repo revision inconsistency ({family}): {inconsistent} (NDEBT-023)")
        sys.exit(1)

# ecosystem/07_progress_comparison.md Sec 3: a finding receives exactly one
# transition class; the same id in two buckets is not expressible in JSON Schema,
# so mirror the full-sweep audit_delta_duplicate_ids check here for --target too.
if family == "audit_delta":
    counts = {}
    transitions = doc.get("transitions", {})
    if isinstance(transitions, dict):
        for bucket in ("new", "resolved", "reopened", "persisting", "stale"):
            items = transitions.get(bucket, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and isinstance(item.get("id"), str):
                        counts[item["id"]] = counts.get(item["id"], 0) + 1
    duplicates = sorted(fid for fid, n in counts.items() if n > 1)
    if duplicates:
        print(f"{path}: finding id in more than one transition class ({family}): {duplicates} (Sec 3)")
        sys.exit(1)

# NDEBT-031: the exactly-one-list invariant (an entry MUST appear in exactly one
# scope list) spans sibling arrays and is not expressible in JSON Schema, so mirror
# the full-sweep membership_multilist_entries check here for --target too.
if family == "ecosystem_membership":
    counts = {}
    for scope_list in ("in_scope", "incubating", "reference_archive", "out_of_scope"):
        items = doc.get(scope_list, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    counts[item["name"]] = counts.get(item["name"], 0) + 1
    multilist = sorted(name for name, n in counts.items() if n > 1)
    if multilist:
        print(f"{path}: entry in more than one scope list ({family}): {multilist} (NDEBT-031, exactly-one-list invariant)")
        sys.exit(1)

# NDEBT-035: the topological-order invariant -- a reconciliation plan whose
# depends_on graph contains a cycle has no valid order and cannot be a PASS plan;
# cycle detection spans the packet graph and is not expressible in JSON Schema, so
# mirror the full-sweep reconciliation_plan_cycles check here for --target too.
if family == "reconciliation_plan":
    packets = doc.get("packets", [])
    ids = {p["id"] for p in packets if isinstance(p, dict) and isinstance(p.get("id"), str)} if isinstance(packets, list) else set()
    graph = {}
    if isinstance(packets, list):
        for p in packets:
            if isinstance(p, dict) and isinstance(p.get("id"), str):
                deps = p.get("depends_on", [])
                graph[p["id"]] = [d for d in deps if isinstance(d, str) and d in ids] if isinstance(deps, list) else []
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    stack = []

    def _has_back_edge(node):
        colour[node] = GREY
        for nxt in graph.get(node, []):
            if colour.get(nxt, BLACK) == GREY:
                return True
            if colour.get(nxt, BLACK) == WHITE and _has_back_edge(nxt):
                return True
        colour[node] = BLACK
        return False

    has_cycle = any(colour[node] == WHITE and _has_back_edge(node) for node in graph)
    if has_cycle and doc.get("plan_verdict") == "PASS":
        print(f"{path}: cyclic dependency set claimed PASS ({family}): no valid topological order (NDEBT-035, ecosystem/04 Section 4)")
        sys.exit(1)

sys.exit(0)
PY
  ); then
    echo "[C12] PASS ecosystem-fixtures --target routed: ${family}"
    return 0
  fi

  echo "[C12] FAIL ecosystem-fixtures --target routed: ${family}"
  printf '%s\n' "${out}" | sed 's/^/  /'
  return 1
}

# C13 -- skill-index integrity (NDEBT-007 fix, feature 049): JSON-parses
# tools/skill.json and resolves its entry_point and every
# capabilities[].module pointer to an existing file. Closes the enforcement
# hole that let the release_train capability ship a retired module pointer
# from v0.4.0 through v0.5.3 undetected (C4 parses only NIZAM.json; C9
# sweeps only .md/.html bodies; the e2e harness asserts only the file's
# existence). In payload mode, pointers into the non-injected directories
# (registry/, docs/) are skipped -- the same carve-out set C4 uses -- because
# bootstrap.sh does not inject them; methodology/ and ecosystem/ joined the
# injected payload in feature 051 (H-PAYLOAD-CONTRACT, NDEBT-008) and are now
# required to resolve. Structural honesty: a missing/empty entry_point or an
# empty capabilities array is itself a FAIL, so the check cannot go vacuous.
#
# check_c13_skill_index [payload]
check_c13_skill_index() {
  local mode="${1:-default}"
  local out
  if out=$(python3 - "${mode}" <<'PY'
import json
import os
import sys

mode = sys.argv[1]
# Non-injected framework-envelope prefixes skipped in --payload mode.
# NARROWED in feature 051 (H-PAYLOAD-CONTRACT): methodology/ and ecosystem/
# joined the injected payload, so a skill.json module pointer into them is
# now REQUIRED to resolve in a consumer install (they were carved out here on
# an interim basis by F-049 pending the decision); only registry/ and docs/
# remain non-injected.
SKIPPED_DIR_PREFIXES = ("registry/", "docs/")

try:
    with open("tools/skill.json", encoding="utf-8") as fh:
        skill = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"tools/skill.json unreadable or not valid JSON: {exc}")
    sys.exit(1)

# Shape/type hardening (PR #28 review): valid JSON that is not the expected
# object -- null, a list, a scalar -- or a truthy non-string entry_point/
# module would otherwise reach .get()/os.path APIs and raise an
# AttributeError/TypeError traceback. Report those as actionable C13
# failures instead (the check still FAILs either way; this makes the
# failure legible rather than a stack trace).
if not isinstance(skill, dict):
    print(f"tools/skill.json must be a JSON object, got {type(skill).__name__}")
    sys.exit(1)

problems = []
paths = []

entry_point = skill.get("entry_point")
if not isinstance(entry_point, str) or not entry_point:
    problems.append("entry_point missing, empty, or not a string")
else:
    paths.append(("entry_point", entry_point))

capabilities = skill.get("capabilities")
if not isinstance(capabilities, list) or not capabilities:
    problems.append("capabilities missing or empty")
    capabilities = []

for index, capability in enumerate(capabilities):
    module = capability.get("module") if isinstance(capability, dict) else None
    label = f"capabilities[{index}] ({capability.get('name', '?') if isinstance(capability, dict) else '?'})"
    if not isinstance(module, str) or not module:
        problems.append(f"{label} has no non-empty string module pointer")
        continue
    paths.append((label, module))

root = os.path.realpath(os.getcwd())
for label, path in paths:
    # Same path hygiene as C4 (feature 049 review hardening): normalize
    # BEFORE the carve-out test so a traversal spelling cannot ride a
    # skip, and reject absolute or root-escaping pointers in every mode.
    norm = os.path.normpath(path)
    if os.path.isabs(path) or norm == ".." or norm.startswith("../"):
        problems.append(f"{label} -> {path} is absolute or escapes the repo root")
        continue
    # Symlink-escape check runs in every mode and BEFORE the payload
    # carve-out (PR #28 review): a present pointer that resolves outside the
    # repo root is rejected even under a carve-out dir. lexists (not
    # isfile) so a broken symlink escaping the root is caught too;
    # genuinely-absent carve-out pointers stay allowed as expected-absent.
    if os.path.lexists(norm):
        real = os.path.realpath(norm)
        if real != root and not real.startswith(root + os.sep):
            problems.append(f"{label} -> {path} resolves outside the repo root (symlink escape)")
            continue
    # entry_point is NEVER carved out (PR #28 review): it is the skill's
    # single load-bearing entry document and must resolve in any payload,
    # so a mis-set entry_point under a non-injected prefix FAILs rather than
    # ride the capability-module carve-out. (In practice entry_point is
    # tools/SKILL.md -- injected -- so this changes nothing for the shipped
    # skill.json; it closes the hole for a misdeclared entry_point.)
    if label != "entry_point" and mode == "payload" and norm.startswith(SKIPPED_DIR_PREFIXES):
        continue
    if not os.path.isfile(norm):
        problems.append(f"{label} -> {path} does not resolve to a file")

for problem in problems:
    print(problem)
sys.exit(1 if problems else 0)
PY
  ); then
    if [ "${mode}" = "payload" ]; then
      echo "[C13] PASS skill-index (payload mode: non-injected dirs registry/ and docs/ skipped; methodology/ and ecosystem/ are injected and required as of feature 051)"
    else
      echo "[C13] PASS skill-index"
    fi
    return 0
  fi
  echo "[C13] FAIL skill-index"
  printf '%s\n' "${out}" | sed 's/^/  /'
  return 1
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

# NDEBT-015 (feature 052): recognize the ecosystem schema families so a
# `--target` invocation against one of their fixtures produces a
# DISCRIMINATING signal instead of misrouting. Before this, an ecosystem
# fixture carried no route discriminator and fell through to C4 (or, for
# preflight_verdict, collided with the qa_verdict route on its top-level
# `verdict` key), so EVERY ecosystem `--target` invocation failed regardless
# of the fixture's polarity. Discriminators (dual-key / required-key
# heuristics): the full audit_delta shape `earlier`+`later`+`transitions` ->
# audit_delta, matched FIRST -- audit_delta declares additionalProperties: true,
# so a delta that also carried a stray `verdict`/`qa_pass`/`closure_criteria` key
# would otherwise be diverted into an earlier family's route; no other family's
# artifact carries all three keys, so matching the whole shape up front never
# steals their fixtures. Then `verdict`+`execution_id` -> preflight_verdict
# (checked BEFORE the generic `verdict`->qa_verdict route so preflight is not
# swallowed; qa_verdict artifacts carry no `execution_id`); the six mandatory
# `*_references` category arrays -> ecosystem_baseline; `closure_criteria` ->
# engineering_finding. These `ecosystem:<family>` routes
# dispatch to check_c12_target (schema validation emitting a [C12] verdict);
# the existing review/qa_verdict/contract/run_state routes and the C4
# fall-through are unchanged.
ECOSYSTEM_BASELINE_KEYS = {
    "framework_references", "repository_references", "dependency_references",
    "ci_references", "planning_references", "evidence_references",
}

if {"earlier", "later", "transitions"} <= doc.keys() and isinstance(doc.get("transitions"), dict):
    # Checked FIRST, and on the full required shape (earlier + later +
    # transitions), not a bare `transitions` key: audit_delta declares
    # additionalProperties: true, so a delta that also carried a stray
    # `verdict`/`qa_pass`/`closure_criteria` key would otherwise be diverted into
    # an earlier family's route. Matching the whole audit_delta shape up front
    # keeps additive keys from misrouting a valid delta. No other family's
    # artifact carries all three of these keys, so this never steals their
    # fixtures.
    print("ecosystem:audit_delta")
elif "ecosystem_verdict" in doc or "framework_pin_consistent" in doc:
    # NDEBT-031: the membership-run AGGREGATE. Either `ecosystem_verdict` or
    # `framework_pin_consistent` is the discriminator (each is unique to this
    # family -- the per-repo preflight_verdict uses `verdict`+`execution_id`,
    # never `ecosystem_verdict`), so an aggregate malformed by OMITTING one still
    # routes here for a clear error. Checked BEFORE the generic single-key routes
    # so an aggregate carrying an extension key never misroutes.
    print("ecosystem:membership_result")
elif {"in_scope", "incubating", "reference_archive", "out_of_scope"} & doc.keys():
    # NDEBT-031: the four scope-list keys are the membership-registry
    # discriminator; ANY one of them triggers it (so a registry malformed by
    # omitting lists still routes here for a clear membership error, not a C4
    # misroute). Checked BEFORE the generic review/verdict/contract_id/run-state
    # routes: the membership schema permits additionalProperties, so a valid
    # registry carrying an extension key (`review`, `verdict`, ...) must still
    # reach C12 rather than being diverted. No other family's artifact carries
    # these scope-list keys, so this never steals their fixtures.
    print("ecosystem:ecosystem_membership")
elif "plan_verdict" in doc or "cycle_findings" in doc:
    # NDEBT-035: the reconciliation PLAN (ecosystem/04 Plan stage). Either
    # `plan_verdict` or `cycle_findings` is the discriminator (each is unique to
    # this family -- the per-repo preflight_verdict uses `verdict`+`execution_id`,
    # the aggregate uses `ecosystem_verdict`), so a plan malformed by OMITTING one
    # still routes here for a clear error. Checked BEFORE the generic single-key
    # routes so a plan carrying an extension key never misroutes.
    print("ecosystem:reconciliation_plan")
elif "review" in doc:
    print("contract_review")
elif "verdict" in doc and "execution_id" in doc:
    print("ecosystem:preflight_verdict")
elif "qa_pass" in doc or "verdict" in doc:
    print("qa_verdict")
elif "contract_id" in doc:
    print("contract")
elif "circuit_breaker" in doc or "scope_budget" in doc:
    print("run_state")
elif ECOSYSTEM_BASELINE_KEYS.issubset(doc):
    print("ecosystem:ecosystem_baseline")
elif "closure_criteria" in doc:
    print("ecosystem:engineering_finding")
else:
    print("none")
PY
)

  case "${route}" in
    none)
      check_c4_index "${target}"
      ;;
    ecosystem:*)
      check_c12_target "${target}" "${route#ecosystem:}"
      ;;
    *)
      check_c11_dogfood_target "${target}" "${route}"
      ;;
  esac
}

# C14 -- workflow SHA-pin integrity (feature 058, Track 3 provenance mechanize).
# Every third-party GitHub Actions `uses:` ref in .github/workflows/ MUST be
# pinned to a full 40-hex commit SHA, not a mutable tag/branch. Mechanizes the
# SHA-pinning requirement of standard/provenance_policy.md via the vetted
# vlib_workflows_sha_pinned primitive (which fails a vanished/empty workflow dir,
# so the check cannot go vacuous). Default-mode only: .github/ is
# framework-envelope, never part of a bootstrap-injected consumer payload.
check_c14_workflow_pins() {
  local out
  if out=$(vlib_workflows_sha_pinned .github/workflows 2>&1); then
    echo "[C14] PASS workflow-sha-pins"
    return 0
  fi
  echo "[C14] FAIL workflow-sha-pins"
  printf '%s\n' "${out}" | sed 's/^/  /'
  return 1
}

# C15 -- capability-profile <-> AGF-role correspondence (feature 058, Track 3
# capability-profile mechanize). Each of the five capability profiles
# (standard/capability_profiles.md) maps to a role defined in standard/AGF.md;
# the vetted vlib_profiles_cover_roles primitive guards the 5<->5 correspondence
# feature 053 made true (NDEBT-010) against drift (a dropped profile or role
# fails it). Default-mode only: a framework-authoring invariant the consumer
# inherits already-verified.
check_c15_capability_profile_roles() {
  local out
  if out=$(vlib_profiles_cover_roles standard/capability_profiles.md standard/AGF.md 2>&1); then
    echo "[C15] PASS capability-profile-roles"
    return 0
  fi
  echo "[C15] FAIL capability-profile-roles"
  printf '%s\n' "${out}" | sed 's/^/  /'
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

  # NDEBT-012 / issue #18 (feature 050): in --payload mode ONLY, anchor to
  # this script's own payload root so a consumer running
  # `bash .nizam/tools/validate.sh --payload` from their repository root
  # behaves identically to `cd .nizam && bash tools/validate.sh --payload`.
  # The validator's payload root is the parent of the tools/ directory this
  # script lives in. Default and --target modes deliberately STAY
  # CWD-anchored -- that is the documented contract (`cd <any-repo-copy> &&
  # bash tools/validate.sh` evaluates that copy's own tree), and in the
  # documented `cd <copy> && bash tools/validate.sh` invocation the script
  # root already equals CWD, so payload-mode anchoring only ever changes the
  # from-a-different-CWD consumer form that issue #18 reported broken.
  if [ "${VALIDATOR_MODE}" = "payload" ]; then
    local script_dir payload_root
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" \
      || die "--payload: cannot resolve the validator's own script directory."
    payload_root="$(dirname -- "${script_dir}")"
    cd -- "${payload_root}" \
      || die "--payload: cannot cd to the payload root '${payload_root}'."
  fi

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
    check_c13_skill_index payload && passed=$((passed + 1)) || failed=$((failed + 1))

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
    check_c12_ecosystem_fixtures && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c13_skill_index && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c14_workflow_pins && passed=$((passed + 1)) || failed=$((failed + 1))
    check_c15_capability_profile_roles && passed=$((passed + 1)) || failed=$((failed + 1))

    echo "SUMMARY: ${passed} passed, ${failed} failed"
  fi

  [ "${failed}" -eq 0 ]
}

main "$@"
