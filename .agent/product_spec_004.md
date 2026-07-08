---
id: nizam-product-spec-004
title: "Nizam Framework — Phase 004 Spec (Durable Enforcement & Dogfooding)"
description: "Phase-004 specification: makes quality DURABLE and self-enforced instead of hand-fixed each phase. Mechanizes the narrative/functional-truth fixes phase 003 applied by hand (path-resolution + single-source-of-truth CI checks), adds a hermetic end-to-end consumer-bootstrap test, ships a vetted verification-helper library plus a verification-authoring standard, and dogfoods the framework's own JSON schemas against its .agent/ audit artifacts (resolving NDEBT-002). Extends product_spec.md, product_spec_002.md, and product_spec_003.md; replaces none."
tags: [spec, governance, enforcement, dogfooding, ci, verification, phase-004]
status: draft
last_audited: "2026-07-08"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-08T12:00:00Z"
updated_at: "2026-07-08T12:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-08T12:00:00Z"
    summary: "Initial phase-004 spec (durable enforcement & dogfooding). PROPOSED — awaiting human authorization."
---

# Nizam Framework — Phase 004 Spec (Durable Enforcement & Dogfooding)

**Status: PROPOSED — awaiting human authorization.** This spec plans phase
`004-durable-enforcement`. It does **not** change `run_state.json`, and the
manifest carries phase 004 as non-active (`status: pending`,
`activation_state: proposed`) until a human authorizes activation — the identical
lifecycle used for phases 002 and 003. It extends `.agent/product_spec.md`,
`.agent/product_spec_002.md`, and `.agent/product_spec_003.md`; it supersedes
none.

## 1. Motivation — Structural Truth Is Enforced; Narrative Truth Is Not

Phases 001–003 built a framework whose **structural** truth is rigorously,
mechanically enforced: `tools/validate.sh` (C1–C8) guards frontmatter schemas
(C1/C2), untagged fences (C3), `NIZAM.json` index integrity with on-disk path
resolution (C4), branding leakage (C5), `bootstrap.sh` sanity (C6), module-README
presence (C7), and version-bump-vs-changelog discipline (C8). CI (`.github/
workflows/compliance.yml`) runs that sweep on every PR.

But the framework's **narrative / functional** truth — do the words in one doc
agree with the words in another, and with what the code actually does? — is
almost entirely un-enforced. Every phase-003 finding (H1–H9) was a
narrative/functional-truth defect that a human or a cold-read agent had to catch
by eye, and that the pipeline then fixed *by hand*:

- **H4** shipped in v0.1.0 and survived untested to phase 003: `tools/interface.md`
  told runtimes to discover `tools/skill.json` at the consumer repo root, but
  `bootstrap.sh` installs the payload under `.nizam/`. A **functional adoption
  bug** no check could see.
- **H1/H5** were doc-vs-code and doc-vs-doc drift (stale "ships in feature 006/007"
  claims; a 3-dir payload description contradicting `bootstrap.sh`'s 4-dir +
  `NIZAM.json` reality). The independent QA adversarial gate — not any validator
  check — caught the residual `GIP.md` §1 stale-payload self-contradiction in the
  F-019 rework.

Separately, the build pipeline's **weakest measured link is
verification-command soundness**: the contract-testability evaluator **rejected 4
of 6 phase-003 contracts** on genuine verification-soundness defects (a
`git diff HEAD` scope guard blind to new files; whole-file greps that vacuously
matched pre-existing text in other sections; a path regex that captured trailing
sentence periods; OR-vs-AND gate logic) — each burning a contract-revision round.
The same anti-patterns recur every phase because nothing captures the hard-won
correct primitives for reuse.

Phase 004 — **Durable Enforcement & Dogfooding** — closes these gaps by making the
manual fixes *mechanical and permanent*, without adding a line of new consumer
runtime behavior. Every check added is verified **non-breaking against the current
tree first** (§3.1): phase 003 already made the docs correct and consistent, so
these checks lock in that state rather than demanding new remediation.

## 2. Recommendations Ledger (R1–R4)

Each recommendation is grounded in a phase-003 event captured in `run_state.json`
history and in dry-run evidence gathered against the working tree at plan time.

| ID | Recommendation | Grounding evidence | Realized by |
|----|----------------|--------------------|-------------|
| R1 | **Narrative-truth CI enforcement.** New `validate.sh` checks C9 (repo-wide path-resolution) + C10 (single-source-of-truth consistency: payload set, discovery order, framework version). | H4 (functional discovery bug, unseen by C1–C8), H1/H5 (doc drift caught only by humans/QA). Today only the guide has a *one-off* path-resolution acceptance test (F-018) and a *one-off* version anchor. | F-026 (C9), F-027 (C10) |
| R2 | **Live end-to-end consumer-bootstrap test.** A hermetic `tools/` harness + CI job that runs `bootstrap.sh` into a scratch consumer and asserts payload present + index-valid, the DOCUMENTED `.nizam/tools/skill.json` discovery path resolves, and `--verify-only` passes. | H4 was a functional adoption bug that shipped in v0.1.0 and survived untested to phase 003. Nothing exercises the real inject→verify path end to end. | F-029 |
| R3 | **Vetted verification-helper library** (`tools/verify_lib.sh`) + a codified verification-authoring standard. Battle-tested primitives contracts source instead of re-inventing (and re-breaking); the standard forbids the recurring anti-patterns. | The contract-testability gate REJECTED 4 of 6 phase-003 contracts on verification-soundness defects (018: git-diff-blind-to-new-files scope guard + 3 more; 020: vacuous payload + unsound acronym checks; 022: 2 vacuous whole-file greps). | F-023 (library), F-024 (standard) |
| R4 | **Dogfood schema validation on the framework's own `.agent/` artifacts** (resolves NDEBT-002). (a) Reconcile `qa_verdict.schema.json` (and a new `contract_review.schema.json`) to the ACTUAL produced shapes so ALL historical `.agent/qa/*.json` validate WITHOUT edits; confirm `contract.schema.json` and the already-shipped `run_state.schema.json` match reality. (b) Add C11 validating every `.agent/qa/*.json`, `.agent/contracts/*.json`, and `.agent/run_state.json` against the shipped schemas. | NDEBT-002: `qa_verdict.schema.json` requires `verdict`/`executed_at`/`checks[]` that the produced verdicts do not carry; nothing validates `.agent/qa/*.json`. Plan-time dry-run: verdicts **017–022** and the contract-review files in `.agent/qa/` FAIL the current schema; legacy **000–016** pass. | F-025 (R4a), F-028 (R4b / C11) |

### 2.1 R4 drift, measured precisely (plan-time evidence)

`.agent/qa/` currently contains **three** distinct evaluator-artifact shapes, and
they are mutually incompatible on required keys — so a single flat required-key
list cannot cover them:

1. **Legacy QA verdict** (`000–016`): `feature_id`, `verdict` (enum pass/fail),
   `executed_at`, `checks[]`, `required_fixes`. Validates against the *current*
   `qa_verdict.schema.json`.
2. **Evolved QA verdict** (`017`, `018`, `019`, `020`, `021`, `022-qa`):
   `feature_id`, `qa_pass`, `checks_run`/`checks_passed`, `adversarial{}`,
   `evidence_files[]`, `issues[]`, `required_fixes[]`, `unsupported_claims[]`,
   `missing_acceptance_coverage[]`, `observations[]`, `final_verdict{}`. **FAILS**
   the current schema (`'verdict' is a required property`).
3. **Pre-code contract review** (`020-contract-review`, `021-contract-review`,
   `022`): `review`, `feature`, `issues`, `missing_acceptance_coverage`,
   `unsupported_claims`, `final_verdict{}`. **FAILS** the current schema
   (`'feature_id' is a required property`).

All three carry a `final_verdict{}` except the legacy shape (which carries
`verdict`/`checks[]`). R4a therefore reconciles by **union**, not by loosening a
flat schema (§5, F-025). `.agent/contracts/*.json` ALL validate against the
current `contract.schema.json` today (the `amendments[]` array on `001`/`016`/`019`
and `approvals.revisions` are tolerated by `additionalProperties: true`);
`.agent/run_state.json` already validates against the already-shipped
`schema/run_state.schema.json`. Per **AH-2 (detect before fix)**: R4a does **not**
recreate `run_state.schema.json` (it exists and passes) — it *confirms* it and
makes `amendments[]` an explicit, documented property of `contract.schema.json`.

## 3. Cross-Cutting Constraints

### 3.1 Current-tree-compliance Findings Ledger (checks must be non-breaking)

The governing constraint on R1: **verify the current tree already PASSES each new
check before adding it** — phase 003 made the docs correct, so these checks lock
in that state. Plan-time dry-runs surfaced the exact edge cases each check must
accommodate to stay non-breaking WITHOUT editing any shipped doc:

| ID | Finding (plan-time dry-run) | Consequence for the check design |
|----|-----------------------------|----------------------------------|
| P1 | A naive "every repo-relative path resolves" check **FAILS** the current tree: shipped docs legitimately name **placeholder** paths — `.agent/contracts/NNN.json`, `.agent/qa/NNN.json` (`methodology/04_tool_driven_state.md`, `schema/README.md`), `.agent/evidence/step-01.txt` — and **illustrative, intentionally-absent** per-runtime example dirs `tools/.claude/`, `tools/.codex/` (`tools/README.md`; DD-4 declares these deliberately do not ship). | **C9 (F-026) MUST encode a documented placeholder/illustrative exemption**: enforce resolution only for references that name a concrete file with a shipped extension (`.md`/`.json`/`.sh`/`.html`/`.yml`) AND contain no placeholder token (`NNN`/`XXX`/`\bstep-\d+\b`/an all-caps ≥3-char segment). Directory references and placeholder/example paths are documented-exempt. Verified: with this exemption the current tree passes. |
| P2 | The stale-3-dir payload enumeration (`standard/`+`templates/`+`schema/` without `tools/`) is **clean repo-wide** at plan time (F-019 fixed it). The framework-version anchor is **consistent** now: `NIZAM.json` `framework.version` = `0.1.0` == the guide's `<meta framework-version>` = `0.1.0`. | **C10 (F-027)** generalizes F-019's stale-enumeration guard + the guide's version anchor repo-wide; both pass on the current tree. |
| P3 | `CONTEXT.md:44` legitimately says "`NIZAM.json` first, then `tools/skill.json`" — describing the **framework checkout's own** (repo-root) agent path, which is the documented *fallback* case, not the bootstrapped-consumer case. A naive "every `skill.json` mention must put `.nizam/` first" check would **false-flag** it. | **C10's discovery-order clause MUST be scoped**: assert `.nizam/`-first only where a doc describes the *bootstrapped-consumer* discovery (the `.nizam/tools/skill.json` sequence), not on every `skill.json` mention. Verified against `tools/interface.md` §2 and the guide. |

These findings are the phase's central design risk and the reason R1 is decomposed
into precisely-scoped checks rather than blunt greps — the same
verification-soundness discipline R3 codifies, applied to the checks themselves.

### 3.2 SUMMARY-count migration (critical)

Adding C9, C10, C11 changes `validate.sh`'s output from `SUMMARY: 8 passed, 0
failed` to `SUMMARY: 11 passed, 0 failed`. Many phase-001..003 contracts and
evidence files hardcode "8 passed" — those are **immutable historical records**,
never re-run, and stay as-is. Phase-004's OWN features and any updated docs MUST
use the new running count. Because three features each edit `validate.sh`'s
`main()` + `print_usage()` + the emergent count, they are **serialized**
(F-026 → F-027 → F-028) so the count increments deterministically: **C9 8→9, C10
9→10, C11 10→11**. Each check feature updates `validate.sh`'s in-script
`print_usage()` self-description and the `Checks (…)` block to name its new check
and the new total; the phase-close feature (F-030) performs the single
`tools/README.md` + `CHANGELOG.md` sync to the final `C1–C11` / "11 passed" state.
`print_usage()` lives inside `validate.sh` (a `.sh`, not in the shipped-doc set),
so updating it carries no C1/C8 obligation; `tools/README.md` is shipped-doc, so
F-030's edit bumps its frontmatter `version` with a `change_log` entry (C8).

### 3.3 Dogfood every new check/script

Per the F-012 fixtures precedent, every new check and script MUST be
**fixture-tested for each failure mode** under `tools/fixtures/` (reachable only
via `validate.sh --target`, never in the default sweep). Phase-004's own
contracts SHOULD compose their verification from `tools/verify_lib.sh` (R3) once
it lands — which is why R3 (F-023) is sequenced first, as a dependency of every
downstream feature.

### 3.4 Branch / merge dependency

Phase 004 builds on phase 003 (**PR #5, unmerged**). Execution MUST begin **after
PR #5 merges**, rebasing the phase-004 branch onto `main`. C9/C10 assume the
phase-003 docs (corrected `tools/interface.md`, `standard/GIP.md`, `CONTEXT.md`,
`README.md`, `docs/guide/index.html`) are present — they are the surfaces the new
checks guard. The upstream v0.2.0 roll-up (PR #4) and the phase-003 v0.3.0 /
GitHub Pages gates remain outstanding human decisions unrelated to this phase's
execution.

## 4. Design Notes That Bind Multiple Features

### 4.1 R4b (C11) must be safe in a bootstrapped consumer

`validate.sh` is injected into consumers (it lives under `tools/`) and is
runtime-agnostic. C11 reads `.agent/` — which in the *framework* repo holds the
audit artifacts, and in a *consumer* repo holds that consumer's own governed
state. C11 MUST therefore **enforce-if-present and skip-if-absent**: when
`.agent/qa/`, `.agent/contracts/`, or `.agent/run_state.json` do not exist (a
fresh or ungoverned consumer), C11 passes trivially rather than failing. Where the
artifacts exist, they are validated against the shipped (reconciled, permissive-
union) schemas, so a conformant consumer passes and the framework's own
historical artifacts pass (guaranteed by F-025 landing strictly first).

### 4.2 R2 requires NO runtime addition to `bootstrap.sh` (justified)

The prompt authorizes one small runtime addition if `bootstrap.sh` lacks a local
mode. Study of `bootstrap.sh` shows it already supports a fully hermetic local
source: `--repo-url` accepts any URL including `file://<path>`, and `--tag`
accepts any pinned semantic-version tag (only `""`/`main`/`master`/`HEAD`/
`refs/heads/*` are refused). The F-029 harness therefore, entirely offline:
creates an **ephemeral annotated tag** on the working checkout HEAD, runs
`bootstrap.sh --repo-url "file://$(pwd)" --tag <ephemeral> --target <scratch>/.nizam`
(a local `git clone` over the `file://` transport, no network), asserts the
payload + index + documented `.nizam/tools/skill.json` discovery path + a
`--verify-only` pass, and deletes the ephemeral tag. **No `bootstrap.sh`
modification is needed or made** — honoring the phase's "no new consumer runtime
behavior" principle. If, during implementation, a local clone proves infeasible
under CI's git configuration, the *minimal* fallback is a `--repo-url` pointing at
the checkout with an ephemeral tag; adding a bespoke local-path mode to
`bootstrap.sh` is a last resort requiring an explicit, human-authorized amendment
(and would be additive/MINOR, not breaking).

## 5. Remediation Design (per feature)

### F-023 — `tools/verify_lib.sh`: vetted verification-helper library + fixtures (R3)
Create `tools/verify_lib.sh` exposing reusable, individually-testable shell
functions that contracts and `validate.sh` checks source instead of re-inventing:
(1) **section-scoped grep** (assert a token appears within a named doc section
span, not vacuously anywhere in the file); (2) the **untracked-aware scope
guard** (`git status --porcelain --untracked-files=all -- . ':(exclude).agent'`
— sees NEW files a `git diff HEAD` scope guard is blind to; the exact
018/021-precedent defect); (3) **strict-version-increase-vs-HEAD** (parse
frontmatter `version` at working tree vs `git show HEAD:<file>`, assert a strict
semver increase); (4) **punctuation-stripped path resolution** (resolve a
repo-relative path reference after stripping trailing sentence punctuation — the
018 false-fail defect — honoring the P1 placeholder exemption); (5) the
**generalized stale-enumeration guard** (no single-line `standard/`+`templates/`+
`schema/` payload enumeration omits `tools/` — the F-019 rework guard). Each
function is a library primitive (sourced, not executed standalone) and is
**fixture-tested for each pass and fail mode** under `tools/fixtures/`. This is
the phase's foundational feature — every downstream feature depends on it so their
contracts compose verification from these primitives. `tools/verify_lib.sh` is a
`.sh` (not shipped-doc), so it carries no frontmatter/C8 obligation; `validate.sh`
stays green (`SUMMARY: 8 passed, 0 failed` — no new check yet).

### F-024 — Verification-authoring standard (R3 methodology) — depends on F-023
Extend `methodology/02_adversarial_tdd.md` with a new section codifying the
**verification-authoring standard**: the anti-patterns a contract's verification
suite MUST NOT use — (a) whole-file greps that vacuously match text elsewhere in
the file (use section-scoped grep); (b) `git diff HEAD` scope guards blind to new
untracked files (use the untracked-aware guard); (c) bare-adjacency / parenthetical
"appears near" checks; (d) literal-substring checks that don't require real
content (a substring that false-passes on unrelated text). The section points at
`tools/verify_lib.sh` (F-023) as the canonical, fixture-tested implementations.
`methodology/02_adversarial_tdd.md` is in the shipped-doc set — its `version` bump
carries a `change_log` entry (NDS §4 / C8); `validate.sh` stays green (still 8).

### F-025 — R4a: reconcile schemas to the ACTUAL artifact shapes (resolves NDEBT-002 part a) — depends on F-023
- **Reconcile `schema/qa_verdict.schema.json`** to an `anyOf` **union** of the two
  QA-verdict shapes (§2.1): the *legacy* shape (`feature_id`+`verdict`+`checks[]`)
  and the *evolved* shape (`feature_id`+`qa_pass`+`final_verdict{}`+…). Add a new
  **`schema/contract_review.schema.json`** describing the *pre-code contract
  review* shape (`review`+`feature`+`final_verdict{}`+`issues[]`+
  `missing_acceptance_coverage[]`+`unsupported_claims[]`). Goal: **every** historical
  `.agent/qa/*.json` validates against `qa_verdict.schema.json` OR
  `contract_review.schema.json` **WITHOUT any edit** to those immutable audit records.
- **Confirm `schema/contract.schema.json`** matches the produced contract shape and
  make `amendments[]` (carried by `001`/`016`/`019`) and `approvals.revisions` an
  explicit, documented property (they validate today via `additionalProperties`;
  this makes the contract self-documenting).
- **Confirm** `schema/run_state.schema.json` already exists and
  `.agent/run_state.json` already validates against it (AH-2 — do not recreate).
- Index the new `contract_review.schema.json` in `NIZAM.json` `schemas[]` and add
  a `schema/README.md` entry; keep `NIZAM.json` schema-valid with every indexed
  path resolving (C4). Bump `schema/README.md` `version` with a `change_log` entry
  (C8). **No `validate.sh` check is added here** (that is F-028), so `validate.sh`
  stays green at 8. **Strictly precedes F-028** so C11 never fails on a historical
  artifact.

### F-026 — R1: C9 repo-wide path-resolution check + fixtures (R1) — depends on F-023
Add **C9** to `validate.sh`: every concrete repo-relative *file* path named in any
shipped `.md` (the C1/C3 shipped-doc set) AND in `docs/guide/index.html` resolves
on disk, applying the **P1 placeholder/illustrative exemption** (§3.1): enforce
only references naming a file with a shipped extension and containing no
placeholder token; directory refs and placeholder/example paths (`NNN`, `step-NN`,
`tools/.claude/`, `tools/.codex/`) are documented-exempt. Compose from
`verify_lib.sh`'s punctuation-stripped path resolution (F-023). Update
`print_usage()` (in-script) to describe C9 and the new total; **SUMMARY 8→9**.
Fixture-test both modes under `tools/fixtures/`: a `.md` naming a real nonexistent
file → C9 FAILs (`--target`); a `.md` naming only resolving + exempt-placeholder
paths → C9 PASSes. **Acceptance gate: the current tree passes C9** (proven
non-breaking by the P1 dry-run). `validate.sh` exits 0 with `SUMMARY: 9 passed, 0
failed`.

### F-027 — R1: C10 single-source-of-truth consistency check + fixtures (R1) — depends on F-023, F-026
Add **C10** to `validate.sh` generalizing three proven one-offs repo-wide:
(1) **payload-set consistency** — the injected payload is uniformly described as
`standard/`+`templates/`+`schema/`+`tools/`+`NIZAM.json`; no stale 3-dir
enumeration survives anywhere (the F-019 rework guard, via `verify_lib.sh`);
(2) **discovery-order consistency** — where a doc describes the *bootstrapped-
consumer* discovery, `.nizam/tools/skill.json` precedes the repo-root fallback
(scoped per **P3** so `CONTEXT.md:44`'s framework-checkout description is not
false-flagged); (3) **framework-version anchor** — every doc that embeds the
framework version (today: the guide's `<meta framework-version>` + footer) equals
`NIZAM.json` `framework.version`, generalizing the F-018 guide anchor (**External
Anchor Rule**: the expected value is read from `NIZAM.json`, never re-derived from
the doc under test). Update `print_usage()`; **SUMMARY 9→10**. Fixture-test each
of the three sub-checks' fail modes under `tools/fixtures/`. **Acceptance gate: the
current tree passes C10** (proven by the P2/P3 dry-runs). Serialized after F-026
for deterministic count.

### F-028 — R4b: C11 dogfood schema validation on `.agent/` artifacts + fixtures (resolves NDEBT-002 part b) — depends on F-025, F-027
Add **C11** to `validate.sh`: validate every `.agent/qa/*.json` (against
`qa_verdict.schema.json` OR `contract_review.schema.json`), every
`.agent/contracts/*.json` (against `contract.schema.json`), and
`.agent/run_state.json` (against `run_state.schema.json`) — using python3 +
jsonschema, the same stack C4 uses. **Enforce-if-present, skip-if-absent** (§4.1)
so a fresh/ungoverned consumer stays green. Update `print_usage()`; **SUMMARY
10→11**. Fixture-test under `tools/fixtures/`: a deliberately schema-invalid
verdict/contract/run_state artifact → C11 FAILs (`--target`-style, against a
fixture path), satisfying the `02_adversarial_tdd.md` §5 schema-rejection
requirement (a schema fed only valid input has constrained nothing). **Depends on
F-025** (schemas reconciled first) so C11 passes over ALL historical `.agent/*`
artifacts; **and on F-027** for the deterministic count. `validate.sh` exits 0 with
`SUMMARY: 11 passed, 0 failed`.

### F-029 — R2: hermetic end-to-end consumer-bootstrap test + CI job (R2) — depends on F-023
Create `tools/e2e_bootstrap_test.sh`, a **hermetic** (network-free) harness (§4.2)
that: creates an ephemeral annotated tag on the working checkout; runs
`bootstrap.sh --repo-url "file://$(pwd)" --tag <ephemeral> --target
<scratch>/.nizam` into a `mktemp` scratch consumer directory; asserts (a) the
injected payload (`standard/`, `templates/`, `schema/`, `tools/`, `NIZAM.json`,
`provenance.json`) is present and (b) `NIZAM.json` under the target is index-valid,
(c) the **documented** discovery path `<scratch>/.nizam/tools/skill.json` resolves
(the H4 regression guard — per `tools/interface.md` §2 item 1), and (d)
`bootstrap.sh --verify-only --tag <ephemeral> --target <scratch>/.nizam` exits 0;
then deletes the ephemeral tag and scratch dir (trap-based cleanup, even on
failure). Add a **CI job** to `.github/workflows/compliance.yml` (a second job
alongside `validate`) that runs the harness. Composes assertions from
`verify_lib.sh` where applicable. The harness carries a **negative-mode** self-test
(dogfood): invoked against a deliberately-broken payload (e.g. a removed
`.nizam/tools/skill.json`), it MUST exit non-zero — proving the H4 guard is
load-bearing, not tautological. `bootstrap.sh` is **not modified**; `validate.sh`
count is unaffected (this is a CI job + harness, not a `validate.sh` check).

### F-030 — Phase close: docs/count sync, CHANGELOG, green validator, v0.4.0 release gate — depends on F-024, F-025, F-026, F-027, F-028, F-029
Sync `tools/README.md` to describe the new `C1–C11` check set and the
`SUMMARY: 11 passed, 0 failed` total (single doc bump; `version` + `change_log`,
C8). Add `CHANGELOG.md [Unreleased]` entries for the phase-004 deliverables
(`verify_lib.sh` + the verification-authoring standard; C9/C10/C11; the reconciled
schemas + new `contract_review.schema.json` resolving NDEBT-002; the e2e harness +
CI job). Confirm `tools/validate.sh` exits 0 with `SUMMARY: 11 passed, 0 failed` on
the final tree, and that the new CI job passes. Move **NDEBT-002 to Resolved** in
`docs/planning/DEBT.md`. Record the **v0.4.0 release human gate** — **MINOR** per
`methodology/05_release_train.md` (additive validator checks C9–C11 + `verify_lib`
+ e2e harness + CI job + permissive schema reconciliation; no breaking runtime
change, and no `bootstrap.sh` modification) — and note the still-outstanding
upstream phase-003 gates (v0.3.0, GitHub Pages, PR #5 merge). The pipeline records
but does **not** execute any release/publishing gate.

## 6. Acceptance Criteria (phase-level)

1. `tools/verify_lib.sh` exists, is `bash -n`-clean, exposes the five named
   primitives, and each is fixture-tested for pass AND fail under `tools/fixtures/`.
2. `methodology/02_adversarial_tdd.md` carries a verification-authoring-standard
   section naming the four forbidden anti-patterns and pointing at
   `tools/verify_lib.sh`; its `version` bumped with a matching `change_log` entry;
   `validate.sh` still green.
3. `schema/qa_verdict.schema.json` (union) + the new
   `schema/contract_review.schema.json` validate **every** historical
   `.agent/qa/*.json` with **zero edits** to those files; every
   `.agent/contracts/*.json` validates against `contract.schema.json` (with
   `amendments[]` explicit); `.agent/run_state.json` validates against the existing
   `run_state.schema.json`; `NIZAM.json` indexes the new schema and stays C4-green.
4. `validate.sh` gains C9 and the current tree PASSES it (P1 placeholder exemption
   applied); C9 is fixture-tested (a nonexistent-file reference FAILs). SUMMARY is
   `9 passed` after F-026.
5. `validate.sh` gains C10 and the current tree PASSES it (payload/discovery/version
   consistency, P2/P3 scoping applied); C10 sub-checks are fixture-tested. SUMMARY
   is `10 passed` after F-027.
6. `validate.sh` gains C11; it validates all `.agent/qa|contracts` + `run_state`
   against the reconciled schemas, PASSES on the current tree, SKIPS gracefully when
   `.agent/` is absent, and is fixture-tested (a schema-invalid artifact FAILs).
   SUMMARY is `11 passed` after F-028.
7. `tools/e2e_bootstrap_test.sh` runs `bootstrap.sh` hermetically (local `file://`
   + ephemeral tag, no network, no `bootstrap.sh` edit) and asserts payload +
   index + `.nizam/tools/skill.json` discovery + `--verify-only`; a CI job runs it;
   its negative self-test FAILs on a broken payload.
8. `tools/README.md` + `CHANGELOG.md [Unreleased]` name the phase-004 deliverables
   and the `SUMMARY: 11 passed, 0 failed` migration; NDEBT-002 moved to Resolved;
   `validate.sh` exits 0 on the final tree; no `v0.4.0` tag is auto-cut.
9. No edit touches any immutable artifact (completed `.agent/contracts/*.json`,
   `.agent/evidence/*`, `.agent/qa/*.json`, or any prior-phase feature list);
   `bootstrap.sh` is unmodified.

## 7. Constraints

- Immutable artifacts are off-limits: prior-phase contracts, evidence, and QA
  verdicts are audit records and MUST NOT be edited. R4a proves the reconciled
  schemas accept them *as-is*.
- **R4a (F-025) strictly precedes R4b (F-028)**; the three `validate.sh`-editing
  features are serialized (F-026 → F-027 → F-028) for a deterministic SUMMARY count.
- Every new check/script is fixture-tested for each failure mode; phase-004
  contracts compose verification from `tools/verify_lib.sh` (F-023 lands first).
- Every new/edited JSON schema keeps `NIZAM.json` C4-green; every edited shipped
  `.md` carries its NDS §4 change record (C8).
- No new consumer runtime behavior; `bootstrap.sh` is not modified. Checks are
  proven non-breaking against the current tree before landing.
- Atomic features, clean acyclic DAG, per-feature + total `estimated_lines`,
  evidence per `methodology/04_tool_driven_state.md` §5, External Anchor Rule.

## 8. Execution Order (topological)

```text
Parallel Group 1: F-023 (verify_lib.sh + fixtures — no dependencies; foundational)
Parallel Group 2: F-024 (verification-authoring standard — depends F-023)
                  F-025 (R4a schema reconciliation — depends F-023; MUST precede F-028)
                  F-026 (C9 path-resolution, SUMMARY 8->9 — depends F-023)
                  F-029 (e2e bootstrap harness + CI job — depends F-023)
Parallel Group 3: F-027 (C10 consistency, SUMMARY 9->10 — depends F-023, F-026)
Parallel Group 4: F-028 (C11 dogfood, SUMMARY 10->11 — depends F-025, F-027)
Sequential (last): F-030 (phase close — depends F-024, F-025, F-026, F-027, F-028, F-029)
```

Dependency graph validated: all dependency targets exist (F-023..F-029), no cycles,
a topological ordering exists. The three `validate.sh`-editing features
(F-026 → F-027 → F-028) form the load-bearing serial spine (SUMMARY-count
migration §3.2); F-025 joins that spine before F-028 (R4a-before-R4b). F-024 and
F-029 are independent leaves off F-023 and may run any time before F-030.

## 9. Human Gates

1. **Phase activation** — a human authorizes activation before any execution
   (manifest flips `activation_state: proposed → active`, `current_phase → 004`);
   the pipeline does not self-activate. Execution begins **after PR #5 merges**
   (§3.4), rebased onto `main`.
2. **v0.4.0 release** (F-030) — **MINOR** per `methodology/05_release_train.md`
   (additive checks + tooling + CI + permissive schema reconciliation; no breaking
   runtime change; `bootstrap.sh` unmodified). Recorded, not executed.
3. **Outstanding upstream (not phase-004 gates, noted for the human):** the v0.2.0
   roll-up PR #4, and the phase-003 v0.3.0 release + GitHub Pages publishing +
   PR #5 merge.
4. **Bootstrap local-mode runtime addition** — NOT required (§4.2). If
   implementation proves a local clone infeasible, adding a bespoke local-path mode
   to `bootstrap.sh` would be a human-authorized, additive/MINOR amendment.

## 10. Feature ↔ Recommendation Traceability

| Feature | Realizes |
|---------|----------|
| F-023 | R3 (verification-helper library) |
| F-024 | R3 (verification-authoring standard) |
| F-025 | R4a (schema reconciliation — NDEBT-002 part a) |
| F-026 | R1 (C9 path-resolution) |
| F-027 | R1 (C10 single-source-of-truth consistency) |
| F-028 | R4b (C11 dogfood schema validation — NDEBT-002 part b) |
| F-029 | R2 (hermetic e2e consumer-bootstrap test) |
| F-030 | phase close: docs/count sync, CHANGELOG, NDEBT-002 resolved, v0.4.0 gate |
</content>
</invoke>
