# Changelog

All notable changes to the Nizam framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Generic optional external evidence admission now requires a trusted host-selected
  candidate digest and revalidates current bindings and artifact bytes on replay.
  Interrupted admission records are preserved and can complete one validated ledger
  transition; unresolved or conflicting records refuse. Permit identifiers are checked
  against existing schema bounds before filesystem writes. Existing callers must supply
  `expected_candidate_sha256` / `--expected-candidate-sha256` when adopting this source.

## [3.1.3] - 2026-10-29

**Patch release** (`methodology/06_release_train.md` Section 3.3).
Preparation only: actual Framework self-install, release and adoption remain pending.

### Fixed

- Review packets preserve supported historical symlink target text from Git as
  inert evidence, including deleted escaping links. Candidate links and artifact
  access retain their existing safety restrictions. Historical text is limited
  to nonempty UTF-8 without ASCII controls; standalone packet formats do not
  authenticate old modes against the base tree.

## [3.1.2] - 2026-10-29

**Patch release** (`methodology/06_release_train.md` Section 3.3).
At preparation on 2026-10-29, source acceptance, actual prepublication Framework
self-install, human merge/sign-off, annotated tag and publication remain pending.
No consumer schema or required-key migration is introduced.

### Fixed

- Framework release preparation now requires actual self-installation of the
  reviewed payload before each release. Existing release gates verify accepted
  controller evidence, real destination readback and final payload equality;
  portable source pins and human release authority remain explicit.

- Assessment and QA/receipt consumption accept unchanged, unselected inherited
  symlink identities without following their targets. Existing non-feature routes
  retain their immutable pre-begin link snapshots; later drift still fails.
  Selected inputs, record paths, symlink ancestors and generic candidate
  link/type/index/revision drift remain closed.

## [3.1.1] - 2026-10-28

**Patch release** (`methodology/06_release_train.md` Section 3.3).
At preparation on 2026-10-28, human merge/sign-off, annotated tag and publication
remain pending. No schema, required-key or consumer runtime changes.

### Fixed

- Promotion retries now refer to the authoritative task-wide stopping policy,
  including immediate hard stops and finite operator recovery. Clarified native
  typed-capture versus external/legacy failure-accounting coverage without
  changing runtime recovery bindings or claiming consumer integration.

- Historical cost-unit comparisons are explicitly qualified; incomplete timing,
  token or billing inputs do not establish measured financial savings.

### Changed

- Internal CI workflows use the operator-directed `ubicloud-standard-8` runner;
  consumer payload execution and contracts are unchanged.

## [3.1.0] - 2026-10-27

**Minor release** (`methodology/06_release_train.md` Section 3.2): adds the
hardened read-only Git identity seam (`NF-R01`), installation and recovery policy
reconciliation (`NF-R02`), versioned `1.1.0` typed binary review packet coverage
(`NF-R03`), optional generic external evidence admission (`NF-R04`), standalone
consumer e2e qualification (`NF-R05`), and the approved `API-REF-PILOT` backlog
plan. No shipped schema was narrowed and no required key was added to existing
consumer records, so a `v3.0.0`-compliant consumer that upgrades by re-bootstrap
remains compliant without remediation.

### Added

- **Hardened read-only Git identity seam (`NF-R01`, `NF-AC01`, `F02`)**:
  Added `tools/git_seam.py` enforcing `--no-replace-objects`,
  `GIT_NO_REPLACE_OBJECTS=1`, `-c core.useReplaceRefs=false`, sanitized `GIT_*`
  environment variables, verified worktree/gitdir boundaries, literal pathspecs,
  and batch blob reads across `tools/workflow_assurance.py`, `tools/start_path.py`,
  `tools/convergent_review.py`, and `tools/payload_integrity.py`.
- **Versioned `1.1.0` binary review packet coverage (`NF-R03`, `NF-AC03`, `F09`)**:
  Extended `schema/review_packet.schema.json` and `tools/convergent_review.py`
  with backward-compatible `1.0.0` support and opt-in `1.1.0` typed binary entries
  (`text`, `opaque_binary`, `absent`), magic-byte media sniffing,
  `integrity_only` vs `trusted_processor_derived` scope enforcement, and binary
  approval invalidation.
- **Generic optional external evidence admission (`NF-R04`, `NF-AC04`)**:
  Added `schema/external_evidence_admission.schema.json`, neutral conformance
  corpus `tools/fixtures/external_evidence/conformance_corpus.json`, and
  `tools/external_evidence.py` (`validate-admission`, `run-corpus`, `bind-summary`)
  with zero Agentic SDLC coupling.
- **Standalone consumer e2e qualification and API reference pilot plan (`NF-R05`, `NF-AC05`)**:
  Added `tools/test_nf_ac05_standalone_e2e.py`, `tools/test_nf_owner_dag_and_backlog.py`,
  `docs/planning/nf-owner-2026-10-27/`, and the approved `API-REF-PILOT` backlog
  plan for a focused three-module Python API reference pilot.

### Fixed

- **Installation and recovery policy reconciliation (`NF-R02`, `NF-AC02`, `F10`, `F11`)**:
  Reconciled atomic 6-module+index `.nizam/` installation vs proportionate external
  consumer workflow activation in `standard/GIP.md` (`v0.7.2`), and routed all
  post-halt continuation through finite task-scoped `operator_recovery` preserving
  attempt history in `methodology/03_circuit_breaker.md` (`v0.6.1`).

## [3.0.0] - 2026-10-27

**Major release** (`methodology/06_release_train.md` Sections 3.1 and 3.4).
At preparation on 2026-10-27 this corrective candidate had not yet been tagged.
The new C13 governance manifest shape narrows previously accepted manifests.
See [v3.0.0 migration](docs/migration-v3.0.0.md) before upgrading.

### Added

- Define optional domain-skill authority and an empty recommendation catalogue.
  The offline resolver uses explicit local inputs; it does not install packages,
  authorize execution or make a recommendation without qualification.
- Publish a generated compliance-control reference and its consistency checks.
  The catalogue contains no qualified or recommended documentation packages.

### Fixed

- Validate typed governance skill identity, capabilities, runtime requirements and
  state interface; reject duplicate capability names and version mismatch for all names.
- Route consumer instructions through the installed index and canonical task classifier.
- Repair first-contact paths and control descriptions; include root README paths in C9.

These corrections have no documentation-skills prerequisite or active recommendation.
Immutable adoption and release sign-off remain separate.

## [2.0.0] - 2026-10-24

**Major release** (`methodology/06_release_train.md` Sections 3.1 and 3.4):
completion now requires a pinned typed verification inventory, assessed candidate
and structured per-check execution proof, and retries have finite task-wide
budgets. Previously accepted consumer records can require a fresh task and new
evidence. Read [Migrating to v2.0.0](docs/migration-v2.0.0.md) before upgrading.

### Fixed

- Preserve approved contract identity and scope through completion, and compare
  inherited index objects/modes and worktree contents, symlink targets and
  endpoints instead of trusting unchanged Git status labels.
- Validate capture contents, exact candidate/command/environment bindings and
  stream bytes through one shared rule for direct completion and receipt QA
  prerequisites. Ordinary failed proof cannot substantiate success; expected
  semantic negatives and zero-byte streams remain supported.
- Preserve canonical receipt replay only for the exact receipt-owned status,
  timestamp and one appended history event, with every Git layer checked.
  Direct completion and unrelated state edits retain their scope refusals.
- Correct installed-consumer bootstrap and historical expected-exit fixtures
  without weakening proof validation or reaching back to framework source.

### Changed

- Require typed verification before a new task begins and bind complete
  authorization records, actual verifier/schema inputs, QA context and original
  execution root to the assessed candidate. Legacy metadata remains readable
  but cannot silently become stronger completion proof.
- Enforce finite retries across task steps, sessions and output directories:
  six failed executions per task and three failures of one signature, together
  with finite configured step limits. Successes, narrative summaries, amended
  scopes and decomposition labels do not reset failures. Reopening requires
  explicit finite task-scoped operator recovery.
- Synchronize release entry points and provide migration guidance. This release
  does not enable semantic providers, qualify persistent SBCL operation, or
  establish consumer commissioning or production readiness.


## [1.11.0] - 2026-10-23

**Minor release** (`methodology/06_release_train.md` Section 3.2): adds the
provider-neutral semantic observation architecture (off by default), the
deterministic governance-close-out repairs, and the earlier evidence-archive,
sparse-bootstrap, `llms.txt` and front-door documentation work. No shipped schema
was narrowed and no required key was added, so a `v1.10.x`-compliant consumer that
upgrades by re-bootstrap remains compliant without remediation.

### Added

- **Provider-neutral semantic observation architecture (Jev-ready foundation, off by default)**:
  Added `tools/semantic_contract.py` (versioned discriminated Choice/Noul/Score
  union, per-primitive validation and the authority-free observation binding),
  `tools/semantic_policy.py` (off-default global/per-family mode state with
  authorized widening and rollback, and veto-first pure deterministic
  composition), `tools/semantic_catalog.py` (the seven decision families
  `DF-01`..`DF-07` and typed question/dependency validation),
  `tools/semantic_families.py` (per-family question definitions, admission gates
  and bounded state projection), `tools/providers/jev.py` (optional host-side Jev
  adapter — exact pinned model, TLS-enforced trusted endpoint, no redirects,
  sealed credentials, one transport attempt, bounded fallbacks),
  `tools/usage_accounting.py` and `tools/cohort_economics.py` (charged-once,
  unknown-not-zero accounting and undefined-zero-denominator economics), and
  `tools/evaluation_corpus.py` / `tools/evaluation_harness.py`
  (independently-adjudicated corpora with leakage-free lineage splits and the
  four-arm A/B/C/D harness with a preregistration contract). Six new JSON schemas
  (`semantic_observation`, `semantic_request`, `semantic_policy_result`,
  `semantic_catalog`, `provider_attempt_event`) are indexed in `NIZAM.json`. No
  semantic mode is active by default; off performs no provider import or call.

- **Historical evidence archive and bounded preservation**: added
  `.agent/evidence-archive/index.json`, `schema/evidence_archive.schema.json` and
  `tools/evidence_archive.py` to bind completed historical evidence tranches to
  Git blobs retained by ordinary history; `tools/evidence_preservation.py` for
  content-addressed input inventories; and canonical-format compatibility vectors
  in `tools/test_canonical_formats.py`.

- **Machine-legible LLM documentation endpoints (`llms.txt` and `llms-full.txt`)**:
  added at the repository root and mirrored under `docs/guide/` for GitHub Pages,
  providing an AI-agent entry protocol, start-path routing matrix, CLI reference,
  role/permission summary and validation check catalog.

### Changed

- **Deterministic governance-close-out repairs**: `tools/start_path.py` now uses
  one strict normalized QA predicate across both verdict shapes (rejecting
  contradictory markers, missing per-check evidence, skipped checks and stale
  candidates), binds completion to the complete committed/staged/unstaged/untracked
  delta from the recorded task base, propagates one validated contract/context end
  to end, allocates authoritative monotonic attempts atomically before dispatch
  (rejecting reuse across sessions or output paths), and requires a verified
  amendment/decomposition/operator record for continuation (a narrative
  `--repair-summary` no longer grants authority).

- **Development tree and consumer installation footprint**: moved completed
  feature evidence out of the active tree into verifiable Git-object archive form;
  `bootstrap.sh` now retrieves the payload with a `blob:none` filter and precise
  sparse checkout, retains only the sparse reference, stages both halves before
  replacement with rollback, and refuses a silently unfiltered download. The
  `v1.11.0` script performs this filtered/sparse retrieval.

- **Developer & AI-agent front-door upgrade (`README.md` and `docs/guide/index.html`)**:
  added release/guide/LLM badges, a dual-persona entry table, a
  failure-to-remediation comparison matrix, an ASCII workspace / execution-loop
  diagram, a 5-route decision matrix, an `llms.txt` quick-load section, a
  `C1`–`C16` compliance summary, and a modern light/dark guide design with copy
  buttons and dual Human/Agent track cards.

## [1.10.1] - 2026-10-19

**Patch release** (`methodology/06_release_train.md` Section 3.3): refreshes the
HTML user guide (`docs/guide/index.html`), `CONTEXT.md`, and residual phase-005 /
phase-015 era prose across the shipped payload (`ecosystem/01_clean_state_preflight.md`,
`methodology/10_live_runtime_sessions.md`, `methodology/11_sbcl_runtime_binding.md`,
`schema/README.md`, `tools/interface.md`, `tools/README.md`, `tools/SKILL.md`,
`tools/skill.json`, and `NIZAM.json`) with zero schema, CLI, or behavioral changes.

### Changed

- **Full documentation and GitHub Pages refresh (`v1.10.1`)**:
  - Updated `docs/guide/index.html` (`1.10.1`) to replace legacy `v0.1.0` pins in `#quickstart` and `#faq` with `v1.10.1` (`--expected-sha`, `--git-repo .nizam-ref/`, and `--require-content-integrity`), list all six injected payload directories (`standard/`, `templates/`, `schema/`, `tools/`, `methodology/`, `ecosystem/`) in `DD-1`, `#quickstart`, and `#adoption-paths`, document `tools/start_path.py` semantic task routing and execution helpers (`classify`, `begin`/`done`, `amend-contract`, `preflight`, `capture`, `publish` default `--mode prepare`, `build-receipt`, `status`, `resume`) under `#start-paths`, refresh `#modules` cards (`standard/`, `methodology/`, `schema/`, `tools/`, `ecosystem/`) to remove stale pre-phase-008/015 claims, and document Section 4.4 external mutation mediation (`NIZAM_MUTATION_ADAPTER`) under `#agent-integration`.
  - Updated `CONTEXT.md` (`1.10.1`), `ecosystem/01_clean_state_preflight.md` (`v0.1.5`), `methodology/10_live_runtime_sessions.md` (`v0.2.1`), `methodology/11_sbcl_runtime_binding.md` (`v0.1.2`), `schema/README.md` (`v0.20.2`), `tools/interface.md` (`v0.5.2`), `tools/README.md` (`v0.37.2`), `tools/SKILL.md` (`v0.8.2`), `tools/skill.json` (`v0.8.2`), and `NIZAM.json` (`1.10.1`) to retire residual `"3-strike attempt limit"`, `"phase016"`, `"Feature 117 entry checks"`, and `"consumer-aspirational"` runtime-protocol labels in favor of the delivered bounded runtime controller (`features 126–129`), work-specific diagnostic stopping policy, and Phase 020 (`features 130–132`) full live SBCL qualification boundary.
  - Added permanent regression checks in `tools/test_public_entry.py` guarding `docs/guide/index.html` and shipped payload documentation against stale `v0.1.0` pins, pre-015/016 placeholder text, and universal 3-strike claims.
- **`v1.10.0` post-release closeout and `.nizam/` self-adoption (`C5`)**:
  Re-bootstrapped `.nizam/` to the released immutable tag `v1.10.0` (`6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7`, annotated tag object `8971603d2091fd5f5602f556b49499a0c8aa7a29`, `278` released files + `provenance.json`, `installed_at` `2026-10-19T07:56:18Z`, evidence `.agent/evidence/release-v1.10.0-closeout/`), updated `.github/scripts/verify_self_governance.py`, `README.md`, `docs/planning/SELF_GOVERNANCE.md` (`v0.6.0`), `docs/planning/ROADMAP.md` (`v0.65.28`), `docs/planning/operator_gates.md` (`v0.49.0`), `docs/planning/manifest.json`, and `docs/planning/REMEDIATION_2026_10_18.md` (`v0.15.0`), and removed the transitional corrective banner in `AGENTS.md` (`v0.4.0`) upon reaching parity between `.nizam/` and the authored framework.

## [1.10.0] - 2026-10-19

**Minor release** (`methodology/06_release_train.md` Section 3.2): the
2026-10-19 `v1.9.0` audit and follow-up execution (`C0–C5`, closing findings
`F1–F3`) lands as additive and hardening capability across `tools/`,
`standard/`, `methodology/`, `ecosystem/`, `schema/`, and `bootstrap.sh`
(`278` released files) with no removed or renamed shipped file and no breaking
governance change; nothing that validated under `v1.9.0` is invalidated.

### Changed

- **2026-10-19 `v1.9.0` audit and follow-up execution (`C0–C5`, closing `F1–F3`).**
  - **Default noncommitting publication, strict adapter mediation, base/delta binding, and index-preserving read queries (`C1`, closes `F1`)**:
    Changed `tools/start_path.py publish` default `--mode` from `publish` to
    `prepare` (noncommitting). Removed the implicit local `git add` /
    `git commit` fallback from `_git_commit_literal_paths`: `--mode publish` and
    `build-receipt --commit` now require `NIZAM_MUTATION_ADAPTER` and fail closed
    (`exit 2`) when unconfigured. Hardened `_invoke_mutation_adapter` to reject
    empty stdout, `{}`, boolean, denied, pending, and failed adapter responses
    without local fallback, and to distinguish explicit denial (`exit 1`) from
    interrupted acknowledgement (`unknown_external_commit_outcome`, `exit 1`),
    reconciling interrupted Stage 1 / Stage 2 commits against actual repository
    state without duplicate commits or re-running captured commands. Enforced
    completion binding to `repository_root`, `repository`, `intended_base`
    (`commit_rev^1 == intended_base`), `intended_branch`/`detached_head`, and
    exact owned file delta (`git diff-tree`). Scoped read-side Git queries with
    `GIT_OPTIONAL_LOCKS=0` (`git --no-optional-locks`) so `mtime`-only changes
    never refresh `.git/index`. Updated `tools/interface.md` (`v0.5.1`),
    `standard/permission_classes.md` (`v0.4.1`), `tools/SKILL.md` (`v0.8.1`),
    `tools/skill.json` (`v0.8.1`), and `tools/test_start_path.py`.
  - **Independent verifier loading, retained `--git-repo` reference support, unbound directory labeling, and fail-closed helper exit codes (`C2`, closes `F2`)**:
    Removed execution of `${TARGET_DIR}/tools/payload_integrity.py` from
    `bootstrap.sh --verify-only`; verifier code is loaded only from an external
    authored script sibling or materialized outside the target from
    `${EXPECTED_SHA}:tools/payload_integrity.py` in `--git-repo`. Added
    `--git-repo DIR` to `bootstrap.sh` so install mode can retain the verified
    shallow tag clone outside `.nizam/` and `--verify-only` can perform
    commit-bound content-integrity verification offline. Forbade deriving
    `--expected-sha` or `--git-repo` from mutable `${TARGET_DIR}/provenance.json`
    or ambient CWD. Updated `tools/payload_integrity.py` and `bootstrap.sh` so
    `--source-root` directory comparisons report
    `content_integrity=directory_match_unbound` and are rejected when
    `--expected-sha` or `--require-content-integrity` is requested. Removed the
    unconditional helper exit-`2` downgrade to `structural_only` pass so invalid
    flags or bad references fail closed (`exit 2`). Updated `README.md`,
    `standard/GIP.md` (`v0.7.1`), `ecosystem/00_ecosystem_bootstrap.md`
    (`v0.8.1`), `tools/README.md` (`v0.37.1`), `tools/test_public_entry.py`, and
    `tools/e2e_bootstrap_test.sh`.
  - **Executable work-specific diagnostic stopping policy and prose/schema alignment (`C3`, closes `F3`)**:
    Replaced unconditional `"max_attempts": 3` in `tools/start_path.py classify`
    and the hard `1 <= attempt <= 3` ceiling in `tools/start_path.py capture`
    with executable work-specific stopping evaluation
    (`_evaluate_attempt_continuation`), permitting attempt `> 3` when invariants
    hold, the failure is localized, and `--Diagnostic-Hypothesis` /
    `--Refined-Scope` (or `--Split-From` with retained `continuation_lineage`)
    are recorded, while halting immediately (`exit 2`, `halted=true`) on
    repeated identical `--Defect-Signature` without new diagnostic progress or
    valid decomposition, exhausted `--Step-Limit`, or `--Failure-Class
    invariant_breach|specification_contradiction|authority_violation`. Aligned
    residual universal "3-strike" summaries in `methodology/00_planning.md`
    (`v0.4.1`), `methodology/01_execution.md` (`v0.4.1`), and
    `schema/run_state.schema.json`.
  - **`v1.9.0` post-release closeout and `.nizam/` self-adoption (`B6`, PR #122)**:
    Re-bootstrapped `.nizam/` to the released immutable tag `v1.9.0` (`0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, annotated tag object `7e721b6e0fb2a0a3014efda388e1097378e3da87`, `278` released files + `provenance.json`, `installed_at` `2026-10-18T22:32:25Z`, evidence `.agent/evidence/release-v1.9.0-closeout/`) and verified `main` (`3efa3e02df56781960dfa8d0ecf143360c617ff8`, `compliance.yml` run `39175072688` in `17m25s`) prior to this `v1.10.0` corrective rollout.

## [1.9.0] - 2026-10-18

**Minor release** (`methodology/06_release_train.md` Section 3.2): the
2026-10-18 `v1.8.0` rollout corrective execution (`B0–B6`, closing findings
`V1–V7`) lands as additive and hardening capability across `tools/`,
`standard/`, `methodology/`, `ecosystem/`, and `bootstrap.sh` (`278` released
files, adding `tools/payload_integrity.py`) with no removed or renamed shipped
file and no breaking governance change; nothing that validated under `v1.8.0`
is invalidated.

### Added

- **Shared complete payload-integrity comparator (`B3`, closes `V3`)**:
  `tools/payload_integrity.py` compares the complete released file inventory,
  exact SHA-256 byte contents, regular-file types (rejecting symlinks), and
  executable modes (`100755`/`100644`) of an installed `.nizam/` directory
  against a trusted release tree (`git:<repo>@<ref>`) or `dir:<path>`, shared by
  `.github/scripts/verify_self_governance.py` and `bootstrap.sh --verify-only`.

### Changed

- **2026-10-18 `v1.8.0` rollout corrective execution (`B0–B6`, closing `V1–V7`).**
  - **Runtime mutation-authority boundary for evidence publication (`B1`, closes `V1`)**:
    Separated `tools/start_path.py publish` into noncommitting `--mode prepare`
    (`prepare-publish`, emitting deterministic `.publish-request.json` records
    without touching Git), externally mediated `--mode publish` (honoring
    `NIZAM_MUTATION_ADAPTER` and `NIZAM_MUTATION_POLICY`, using literal
    `:(literal)` pathspecs, staging in an isolated temporary `GIT_INDEX_FILE`
    without mutating the caller's real index, rejecting same-path staged
    conflicts and failed Git observations, supporting multi-capture batching,
    and recovering cleanly from Stage 1 interruption), and noncommitting
    `--mode finalize` (`finalize-publish`, verifying committed blob SHA-256 and
    `100644` mode before emitting `.published.json`). Removed the hidden
    `_git_ensure_committed` fallback from `build-receipt` when `--commit` is
    omitted so default `build-receipt` is strictly noncommitting. Updated
    `tools/interface.md` (`v0.5.0`), `standard/permission_classes.md` (`v0.4.0`),
    and `tools/test_start_path.py`.
  - **Install-time release-tag and SHA pin enforcement (`B2`, closes `V2` and `V7` regression)**:
    `bootstrap.sh` enforces strict `vMAJOR.MINOR.PATCH` release-tag syntax on
    the public path (with `--allow-fixture-tag` / `ALLOW_FIXTURE_TAG=1` reserved
    for controlled `e2e-*` test tags), fetches explicit `refs/tags/<tag>` via
    `git fetch --depth 1 --no-tags`, rejects branch-only refs and same-name
    branch/tag ambiguity on the source remote, and verifies `--expected-sha`
    against the peeled tag commit before staging or replacing the target
    directory. Added a 3-form normal-clone and linked-worktree reproducibility
    regression to `tools/e2e_bootstrap_test.sh` and updated `standard/GIP.md`
    (`v0.7.0`) and `ecosystem/00_ecosystem_bootstrap.md` (`v0.8.0`).
  - **Content-verified `--verify-only` and non-conflated `--payload` validation summary (`B3`, closes `V3` and `V4`)**:
    `bootstrap.sh --verify-only` runs `tools/payload_integrity.py` against a
    reachable reference repository or `--reference-repo` (reporting
    `content_integrity=verified`), fails closed when `--expected-sha` or
    `--require-content-integrity` lacks a reachable reference tree, and
    explicitly discloses `structural_only; content_integrity=not_checked` when
    operating offline without a reference tree. `tools/validate.sh --payload`
    reports `[C11] NOT_APPLICABLE`, `[C16] NOT_APPLICABLE`, `[C6] SKIP`,
    `[C12]/[C14]/[C15] OUT_OF_SCOPE`, and a non-conflated summary:
    `SUMMARY (payload mode): 10 exercised passed, 0 failed, 2 not-applicable (C11, C16), 1 skipped (C6), 3 out-of-scope (C12, C14, C15); content_integrity=not_checked, operational_acceptance=not_assessed`.
  - **Coherent stopping policy, skill metadata parity, and provenance discovery (`B4`, closes `V5` and `V6`)**:
    Aligned active stopping-policy text across `methodology/03_circuit_breaker.md`
    (`v0.6.0`), `standard/acceptance_bars.md` (`v0.3.0`), `tools/SKILL.md`
    (`v0.8.0`), `tools/skill.json` (`v0.8.0`), `NIZAM.json`,
    `methodology/README.md` (`v0.7.0`), and `README.md`; enforced version parity
    between `tools/skill.json` and `tools/SKILL.md` in `tools/validate.sh` C13;
    replaced hardcoded `v1.5.0` and `phase016` statements in `tools/SKILL.md`
    Section 10 and active `tools/README.md` (`v0.37.0`) sections with provenance
    and `start_path.py preflight` discovery; and documented the distinction
    between a release tag's authored payload and the repository's own `.nizam/`
    directory in `README.md` and `docs/planning/SELF_GOVERNANCE.md` (`v0.4.1`).
  - **v1.8.0 post-release ledger refresh (`PR #120`)**:
    `v1.8.0` is published at `606d11ee84deff0d3b7934cbfd715223d64ac79d`
    (annotated tag `faeb50dfdb055cc4d5018ab8d474979be71f876f`, `release.yml`
    run `39130412824` at `2026-10-18T13:11:05Z`), and `.nizam/` was
    re-bootstrapped to `v1.8.0` in PR #120 (`016a1b79e0be6bc5b7459baae3c67ee99f2803f6`,
    `compliance.yml` run `39133101798` in `13m35s`) prior to this `v1.9.0`
    corrective rollout.

## [1.8.0] - 2026-10-18

**Minor release** (`methodology/06_release_train.md` Section 3.2): the
2026-10-18 post-remediation audit follow-up (`A0–A8`, closing findings `F1–F6`)
lands as additive and hardening capability across `tools/`, `standard/`,
`methodology/`, and `schema/` with no removed or renamed shipped file and no
breaking governance change; nothing that validated under `v1.7.0` is
invalidated.

### Changed

- **2026-10-18 post-remediation follow-up (`A0–A8`, closing `F1–F6`).**
  - **Route eligibility and completion integrity (`A1`, closes `F1` and `F5`)**:
    `tools/start_path.py` unifies task classification, `begin`, `done`, `amend-contract`,
    and route-bound receipt stages on a single canonical scope-eligibility check
    (`verify_route_scope_eligibility`), rejects symlinks and `.nizam/` paths, checks
    actual Git working-tree changes against declared scope (`verify_actual_changed_scope`),
    and enforces non-vacuous QA completion (`>=1` passing check and non-empty evidence).
  - **Producer-to-receipt integration and operational preflight (`A2`, closes `F2` and `F5`)**:
    Added `tools/start_path.py publish` and `tools/start_path.py build-receipt` to commit
    post-execution capture outputs, project closed 12-field receipt captures with valid
    output revisions and full candidate environment bindings, and verify stage receipts
    for `resume` without command re-execution. `preflight` now executes a live sandbox
    isolation probe and separates `installed`, `available`, `operational`, and `qualified`.
  - **Profile readiness causal ordering and empirical binding (`A3`, closes `F3`)**:
    Hardened `preregister_profile_comparison`, `evaluate_profile_comparison`, and
    `verify_profiles_ready` in `tools/workflow_assurance.py` to enforce causal commit
    ordering (preregistration committed strictly before shadow run captures), distinct
    baseline/shadow run bindings and tier-differentiated `argv`/`executed_roles`,
    `min_comparison_runs`, captured `case_proofs`, and independent reviewer provenance.
  - **Canonical protocol alignment and status reconciliation (`A4–A5`, closes `F4` and `F6`)**:
    Aligned `standard/AGF.md` (`v0.4.0`), `tools/SKILL.md` (`v0.7.0`),
    `methodology/00_planning.md` (`v0.4.0`), `methodology/01_execution.md` (`v0.4.0`),
    `methodology/03_circuit_breaker.md` (`v0.5.0`), `standard/acceptance_bars.md`
    (`v0.2.0`), and `standard/definition_of_done.md` (`v0.4.1`) on the three-tier
    responsibility table, diagnostic stopping rules, single AGF verdict shape, and
    structural C16 (`vlib_feature_list_lifecycle`) check; reconciled `.agent/contracts/124.json`,
    `.agent/contracts/125.json`, `.agent/qa/124.json`, `.agent/qa/125.json`, and
    `.agent/feature_list_022.json`, and expanded `generate_status_view` to dynamically
    discover all feature lists, phase YAMLs, and `manifest.json` and report contradictions.
  - **Zero-reach-back consumer rehearsal and 12-task paired evaluation (`A6–A7`)**:
    Added `assert_consumer_zero_reachback` in `tools/e2e_bootstrap_test.sh` and `.nizam/schema/`
    fallback in `tools/workflow_assurance.py::_receipt_schema` to prove end-to-end consumer
    operation using only `.nizam/tools/` with zero reach-back to the author checkout, and
    recorded a 12-task preregistered paired baseline-vs-shadow comparison (`comp-01`–`comp-12`
    across `Routine`, `Standard`, and `High-assurance`) in `.agent/evidence/125/` and
    `.agent/evidence/remediation-2026-10-18/pilot-report.json`.
- **v1.7.0 post-release ledger refresh and self-adoption** (framework-envelope only).
  `v1.7.0` is published: the annotated tag `v1.7.0` (`6a4cf599f3850ae31561ba38f9da29237d0a4a53`)
  points at reviewed PR #117 merge `47851d857e0ab879b848610128ee6e9e13368f0d`;
  `release.yml` run `39116785402` succeeded and published the GitHub Release at
  `2026-10-18T09:48:38Z`. This repository's `.nizam/` installation is re-pinned to
  the `v1.7.0` payload (`277` released files + `provenance.json`, `installed_at: 2026-10-18T09:49:41Z`)
  via the reviewed post-tag re-bootstrap under `H-CONSUMER-UPGRADE`, and the planning
  ledgers (`ROADMAP.md`, `operator_gates.md`, `SELF_GOVERNANCE.md`, `manifest.json`)
  and `.agent/run_state.json` record the observed facts.

## [1.7.0] - 2026-10-18

**Minor release** (`methodology/06_release_train.md` Section 3.2): the portable
Docker trial-sandbox adapter (feature 134), Phase 019 generic repository/worktree
assurance profile preregistration and shadow comparison/recommendation (features
124–125), and the 2026-10-18 critical quality and velocity remediation (`R0–R11`,
including 5-route semantic task classification, `trivial` start path, lightweight
contract amendments, unified stopping rules, `preflight` and exclusive `capture`,
Option A repository-binding migration and operational receipt/resume CLI, and
concise read-only `status` views) land as additive, new-optional capability. There
is no schema narrowing, no removed or renamed shipped file, and no breaking
governance change; nothing that validated under v1.6.0 is invalidated. Persistent-runtime
SBCL profile claims remain explicitly gated on Phase 020 (`130–132`). Upgrade path:
consumers re-bootstrap from the `v1.7.0` tag to inherit the payload
(`methodology/06_release_train.md` Section 5).

### Added

- **Portable Docker trial-sandbox adapter (feature 134).** Added one canonical
  trusted Docker-backed equivalent adapter (`tools/docker_trial_sandbox.sh`)
  implementing the same `ADAPTER --root TRIAL_ROOT --runner RUNNER --
  RUNNER_ARGUMENTS...` protocol as the Linux reference adapter: one fresh
  `--network none --cap-drop ALL --no-new-privileges --read-only` container per
  trial over a digest-pinned `python:3-alpine` image, same-path bind mounts, a
  fixed minimal container environment, and the existing inner Landlock adapter
  with an explicit interpreter allowlist (new repeatable `--interpreter` flag,
  byte-identical native behavior when absent). The adapter fails closed (exit 2
  arguments, 3 daemon/pinned image, 4 inner setup), never auto-pulls, and
  exposes `--probe` and `--print-image`. Sandbox conformance capability
  selection is now adapter-specific: `tools/test_convergent_review.py`
  auto-selects native-first, falls back to the Docker adapter when the native
  probe fails, honors an explicit `--isolation-adapter` override before unittest
  passthrough, and records the selected adapter and its sha256 on stderr; the
  five sandbox-dependent tests execute under the selected adapter with
  adapter-flavored omission controls and, under Docker, live in-sandbox guards
  (zero capabilities, no daemon socket, fresh PID namespace, no ambient
  environment forwarding). `.github/scripts/test_sandbox_boundaries.py` gains
  the same selection with `--adapter`. UNSUPPORTED reason text and the
  required-conformance exit semantics are unchanged; on hosts with neither
  capability the five tests still report UNSUPPORTED, print
  `CONFORMANCE: NOT FULL`, and exit non-zero. The `convergent_review` CI job
  pulls the pinned image and runs the Docker-adapter boundary and conformance
  suites; no evaluator, schema, host-control, or trust-surface change. The
  pinned-image digest re-pin policy is registered as NDEBT-056, and the
  live-model observation gap remains unclaimed.

- **Phase 019 generic repository/worktree assurance profiles (features 124–125) and task-routing/evidence/status CLI (`tools/start_path.py`, `tools/workflow_assurance.py`).** Added `preregister_profile_comparison` (`preregister-profile`), `evaluate_profile_comparison` (`evaluate-profile`), and `verify_profiles_ready` (`verify-profiles-ready`, `--check profiles-ready`) reusing the five canonical AGF roles and capability profiles (`orchestrator-primary`, `planner-creative`, `generator-deterministic`, `validator-structural`, `evaluator-adversarial`), enforcing `Routine` (`trivial`, `small-change`), `Standard` (`bugfix`, `standard-feature`), and `High-assurance` (`high-risk`) applicability, same-candidate baseline stability, zero missed-blocker tolerance, cost/latency accounting, and no self-promotion (`promoted: false`, `active_gates_reduced: false`, `permissions_changed: false`), while keeping persistent-runtime SBCL profile claims gated on Phase 020 (`130–132`). Extended `tools/start_path.py` with semantic 5-route classification (`classify`), the `trivial` route (`begin|done trivial`), lightweight mechanical contract amendments (`amend-contract`), evidence-based vs. `advisory_minor` verdict inspection (`check-verdict` reusing `convergent_agf_verdict`), capability preflight (`preflight`), exclusive non-overwriting evidence capture (`capture`), operational receipt/resume flow (`resume`), and concise read-only status views (`status --format json|markdown`).

### Changed

- **2026-10-18 critical quality and velocity remediation (R0–R11).** Removed duplicate `ci-candidate-bound` and `ci-blocker-rejected` executions from `tools/fixtures_self_test.sh` and the duplicate `fixtures_self_test.sh` invocation from `convergent_review` in `.github/workflows/compliance.yml` so each suite has a single authoritative job owner; bounded `ControlsFixture` and `controls_snapshot` in `tools/test_workflow_assurance.py` (219 files instead of 34,205); retired the default whole-module `MASKED_AST` freeze in `tools/test_receipt_candidate_batching.py` behind `--check-historical-ast-freeze` while retaining all four behavioral receipt-batching checks; unified comparator and circuit-breaker stopping rules (`attempt <= 3` unless operator reset); and completed the Option A repository-binding migration (`https://github.com/niq-cnr/nizam-framework.git`, `.agent/evidence/120/authority-interpretation.json`) and 15-task representative pilot + disposable consumer rehearsal (`.agent/evidence/remediation-2026-10-18/pilot-report.json`).
- **v1.6.0 post-release ledger refresh** (framework-envelope only). v1.6.0 is
  published: the annotated tag `v1.6.0` points at reviewed PR #113 merge
  `4e7db5a47d753555abd4d724c5d16f2b5eb86c3e`; `release.yml` run 39008222975
  succeeded and published the GitHub Release at 2026-10-17T05:59:26Z (marked
  Latest); the tag bootstrap rehearsal passed. This repository's `.nizam/`
  install is re-pinned to the `v1.6.0` payload by the reviewed post-tag
  re-bootstrap, and the planning ledgers (ROADMAP, operator_gates, HANDOVER,
  manifest) and run_state record the observed facts. The self-governance record
  (`docs/planning/SELF_GOVERNANCE.md`, 0.2.0) records the `v1.6.0` installation
  as installed with commissioning not performed and retains the `v1.5.0`
  commissioning as history; README states that commissioning of this release has
  not been performed. The operator_gates `v1.6.0` PREPARED clause is superseded
  by the EXECUTED record, and the only edit to an existing historical ledger
  body is one supersession marker line on the HANDOVER 2026-10-17 preparation
  note. No payload source or version anchor changes; feature 129 remains
  feature-scope complete with full-live qualification remaining features 131/132.

## [1.6.0] - 2026-10-17

**Minor release** (`methodology/06_release_train.md` Section 3.2): the Workflow
Assurance tranche lands as additive, new-optional capability — features 115–119
(foundation readiness), 120–123 (receipt gates, conflict lanes, cause routing and
capable CI controls), 126–128 (bounded partial runtime core) and 129 (SBCL loop and
confirmed cancellation), plus receipt-input batching (feature 133). There is no schema
narrowing, no removed or renamed shipped file and no breaking governance change;
nothing that validated under v1.5.0 is invalidated. Feature 129's entry below states
its explicit boundary: feature-scope complete, with full-live qualification
deliberately remaining features 131/132. Everything else in this release is
framework-envelope only (planning, maintenance and self-governance records), none of
which `bootstrap.sh` injects. Upgrade path: consumers re-bootstrap from the `v1.6.0`
tag to inherit the payload (`methodology/06_release_train.md` Section 5).

### Changed

- **Receipt input batching (feature 133).** Batch immutable candidate Git inputs
  per call while preserving exact revision/path, bytes/mode and ownership checks,
  fresh physical observations and existing trust boundaries. Four independent
  synthetic controls cover real Git launch reduction and retained semantics;
  historical feature 123 proof remains bound to its assessed Source.

- **Capable CI controls (feature 123).** Added selected two-pass A11/A10 dogfood
  in the existing capable job and read-only observation of immutable hosted
  proof, with explicit deterministic and synthetic evidence boundaries.

- **Evidence-based cause routing (feature 122).** Added a read-only failure route
  bound to selected classification, actual captures and continuous counters.
  Infrastructure and semantic outcomes remain failed within the existing max3.

- **Conflict lanes and rollback (feature 121).** Added read-only lane and detached
  attempt checks, with bounded Git-managed removal after captured failure.
  Shared ownership serializes and the existing three-attempt limit remains.

- **Receipt gates and recovery (feature 120).** Added read-only candidate-bound
  validation of operator decisions, prerequisites and pinned actual command
  captures, with idempotent transition proposals and explicit missing-proof
  recovery. Eleven acceptance cases extend the existing twenty-six.
  Repository bindings use literal Git origin strings without alias normalization;
  existing Root records require reviewed compatibility or migration before live use.

- **Convergent AGF verdict (feature 119).** Added a pure, explicitly bound adapter
  that preserves blocking arrays and carried blocker/important findings, exposes
  minor advice and rejects malformed input. Six independent cases extend the
  existing twenty; historical foundation receipts retain their immutable boundary.

- **Bounded partial core (feature 128).** Added independently authored `core-ready`
  over fourteen bounded leaf subprocesses. Hosted CI retains separate fourteen-leaf
  execution; SBCL/full adapter, phase020 fresh acceptance and final CI131 remain pending.

- **SBCL loop and confirmed cancellation (feature 129).** Added the adopted Source5
  SBCL session loop (`tools/sbcl_session_loop.lisp`), merged via PR #109 (`96cd3573`)
  with approved canonical QA; the 129-source circuit reads 5/5 under the recorded
  operator extension. Feature-scope complete only: full-live SBCL/runtime
  qualification deliberately remains features 131/132 and is not claimed here.

- **Stub operation semantics and handoff (feature 127).** Added bounded polling
  that stops waiting only, correlated cooperative cancellation confirmation and
  checked source-bound reattachment snapshots. Replay uses committed templates
  through explicit authorized submits in a fresh development session. Existing
  fixture CI schedules fourteen checks; independent acceptance and capture remain
  required, with SBCL and fresh acceptance infrastructure outside this change.

- **Partial development runtime controller (feature 126).** Added a detached
  supervisor, isolated stub images, ownership/lease/generation admission, atomic
  development records and read-only attempt guards. Existing fixture CI invokes
  nine independently authored checks. Timeout/replay, SBCL and fresh acceptance
  remain later work; candidate validation does not establish live conformance.

- **Controller-core activation planning.** Captured and independently reviewed
  same-host Linux isolation and SBCL capability; selected feature 126 for contract
  preparation within the unchanged 5,650/7,345 budget, including current preparation
  costs. Controller implementation and live acceptance remain pending. Added a
  balanced comparative-performance proposal with pinned primary sources and future
  paired trials; no comparative performance result or superiority is claimed.

- **Foundation readiness (feature 118).** Added candidate-bound observation of
  current twenty-case prerequisite evidence, explicit runtime and historical Git
  inputs, and independent recorded evaluator identity. Readiness supports later
  record-only HEAD advances with unchanged inputs. Canonical phase closure still
  requires Mode B, fresh QA with a separate spot check, and Root capture; the
  installed v1.5.0 payload and proposed later phases remain unchanged.

- **Authorized entry (feature 117).** Added a read-only preflight over actual local
  origin/authority, pinned critical governance bytes, revision-bound independent
  approvals and explicit existing-role path/field intents. Four independent cases
  extend the current suite to twenty. The project check runs only while 117 is
  active; completion still requires Mode B, fresh QA and capture. Historical
  proofs remain unchanged and installed v1.5.0 remains pinned.

- **Independent acceptance bundles (feature 116).** Added read-only sealed-bundle
  verification over actual immutable test/API/obligation/control Git bytes,
  observed environment and distinct recorded author/developer/reviewer identities.
  Each case binds successful setup and positive control to its own intended
  behavioral failure; generic setup or missing-API failures cannot qualify.
  Independent review stays outside its own seal, and later implementation Source
  identity stays separate. Five new cases extend the existing eleven-case suite.
  This candidate requires its own Mode B, fresh QA and capture; entry enforcement
  and foundation closure remain features 117–118. Installed v1.5.0 is unchanged.

- **Workflow Assurance identity (feature 115).** Added a read-only stdlib API/CLI
  binding actual Git source identity, assessed bytes/modes and observed environment.
  Unknown changes invalidate conservatively; declared scalar record updates and
  exact history append can preserve the original assessed anchor across later HEADs.
  Eleven independent cases run in the existing CI fixture job. Phase 017 foundation
  is authorized at 5,400/7,020; this candidate still requires independent Mode B,
  fresh QA and capture. Sealed bundles, authorized entry and foundation closure
  remain features 116–118; installed v1.5.0 is unchanged.

- **WA and controller planning delivery.** Delivered draft plans for five pending phases,
  allocating WA features 115–125 before controller features 126–132 with full budgets and independent
  future acceptance ownership. Recommended foundation 017→core 016→controls 018→
  fresh 020→profiles 019; preserved original backlog edges and recorded explicit
  proposed split-alias bindings. Public projections reference
  [.agent/evidence/workflow-016-planning/plan-validation.json](.agent/evidence/workflow-016-planning/plan-validation.json).
  Planning delivery passed independent Mode B, fresh QA and evidence capture.
  Actual planning acceptance: [QA](.agent/qa/workflow-016-planning.json) and
  [capture](.agent/evidence/workflow-016-planning/evidence-capture.json).
 Future phase/budget
  activation, runtime/live CI acceptance, release/tag and installed upgrade remain
  separately gated; closed phase 015 and published v1.5.0 are preserved.

- **Normative-stage readiness (feature114).** Added a candidate-bound next MINOR
  dossier and narrow current planning projections. Closure requires independent
  Mode B, fresh twelve-command QA, one additional adversarial spot, actual evidence
  capture and Parent canonical completion. Human release/tag and consumer upgrade
  remain separate decisions; published/installed v1.5.0 is unchanged. Schema/C12
  record validity and normative adapter/binding rules establish no executable
  controller, SBCL launcher, capable live CI or thirteen live proofs. WA choices
  remain selected planning inputs without new allocation or gate reduction.

- **Optional runtime-session adapter (feature113).** Published seven optional
  calls and conditional S1–S9 while preserving the original ten mandatory
  adapter items and existing requirements. Added manifest/index/skill routing
  and document crosslinks. Document10 is partially enforced only by existing
  schema/C12 record checks; SBCL binding remains consumer-aspirational.
  Executable controller/adapter/SBCL enforcement and all thirteen live proofs
  remain pending phase016; installed v1.5.0 is unchanged.

- **SBCL reference binding (feature112).** Added the normative consumer-aspirational
  binding with folded toolchain/lock/core profile, condition/restart capture,
  non-atomic load/compile, drift, thread/cancellation hazards and fresh hermetic
  acceptance rules. Registered Document11 and clarified current availability and
  activation-time planning prose. ASDF forms remain illustrative; executable
  adapter/controller enforcement and all thirteen live proofs remain pending.
  Published/installed v1.5.0 and existing historical proofs are unchanged.

- **Runtime provenance records (feature111).** Added two closed Draft2020-12
  schemas with phase016 fields, eighteen top-level discriminating fixtures and
  shared C12 owner/generation/lease/continuity validation in targeted and full
  sweeps. Registered the schemas and fixture completeness rows; corrected the
  neutral protocol's current record-validation boundary. Record validity never
  proves live runtime enforcement or acceptance; binding, adapter, controller
  and all thirteen live cases remain pending. Installed v1.5.0 is unchanged.

- **Authorized phase015 and neutral runtime protocol (feature110).** Added active
  consumer-aspirational live-runtime rules, generic fresh acceptance and attempt
  continuity, narrow session permissions, review denial, durable handoff criteria
  and same-feature source registrations. H-PHASE-015 approved7200/9360 and six
  exact WA design selections are recorded from pre-edit operator events. Current
  lifecycle follows canonical phase/list after independent gates. Future schemas,
  binding, adapter and controller are deferred; WA/016 remain unallocated, all
  live proofs pending, active gates unchanged and installed v1.5.0 immutable.

- **Accepted scopes and pending phase015 plan.** Recorded operator H-NIP acceptance
  of reviewed NIP3v0.2.0/NIP4v0.1.0; both now1.0.0/active preserve the reviewed
  scope, NIP3 cases/choices and six unresolved WA options. Canonical phase015
  spec/list/YAML allocates110–114 as pending chain, proposed7200/9360 budget
  including phase-level costs. H-PHASE-015 and budget approval remain outstanding;
  no runtime/module implementation, WA-choice resolution, active-gate reduction,
  phase016/WA allocation, release or installed upgrade. Manifest appends pending/
  proposed015; current phase014, historical ledgers/evidence and installedv1.5.0
  remain frozen.

- **Pending NIP planning.** NIP-0003 (0.2.0) now uses provisional110–120, actual
  delivered F105 claim-map/required-CI facts, available SBCL2.2.9.debian and current
  historical102/debt/commissioning/maintenance inputs. Its four operator choices
  and thirteen cases remain preserved. Proposed NIP-0004 (0.1.0) extends the
  Workflow Assurance outline with staged owners, acceptance checks, evidence,
  blocking outcomes and unresolved decisions. Only A03-RT/A03-WA-DRAFT/A03-WA-FINAL
  record drafting delivery; H-NIP acceptance, future H-PHASE, implementation and
  release decisions remain pending. Current planning overlays are synchronized;
  historical records and installed v1.5.0 remain frozen.

- **Verified bounded maintenance.** After planning PR81 merged, C13 interruption
  cleanup now composes byte restoration with process-owned scratch cleanup;
  stronger sandbox tests distinguish namespace, filesystem and generated-exec
  omissions without changing the sandbox. Payload help names six injected modules
  and12 checks; Evaluator role text names independent Loop1 review and Loop2 QA.
  NDEBT-047/046/045 are Resolved and A04a complete at fixed source candidate
  `7221cd17a7c2d2188de0094b8ea008e4e192a0c4`, verified by fresh capable
  CI38108704971 attempt2, independent6/6 QA and the evidence gate. Actual receipts
  remain in `.agent/evidence/post-ga-maintenance/`; local unsupported isolation is
  preserved as a limitation. No installed v1.5.0 upgrade or new release.

- **Current post-GA planning view** (planning envelope only). Canonical complete
  and cancelled phase014 statuses match the derived backlog; cancelled100/101 are
  terminal. Planning PR81 merged; current inputs use actual historical102/current
  debt and commissioned local evidence without invented simplification findings.
  The selected maintenance is verified with actual proof. Historical checkers,
  evidence and released sections remain frozen; no NIP/WA acceptance or new phase.

- **Local self-governance adoption** (framework-envelope only). This repository
  installs the public `v1.5.0` payload under `.nizam/` with genuine pinned provenance.
  Root `AGENTS.md` routes local work through the installed index and skill;
  `docs/planning/SELF_GOVERNANCE.md` (0.1.1) records completed commissioning at
  source candidate `bfd475ff670e582cbbfc8f3187ae988dcf3c8baa`: actual successful CI
  `38075479048`, clean installed preflight PASS, an immutable framework/candidate
  baseline, independent 9/9 QA and the evidence-capture gate passed.
  A standing CI job checks complete file-set/byte/Git-mode fidelity, adversarial
  drift failures and installed payload compliance. Authored payload sources,
  released version anchors and historical phase-014 evidence remain unchanged.

- **v1.5.0 post-release records and handover refresh** (framework-envelope only).
  `docs/planning/ROADMAP.md` (0.51.0) records the published GA release at reviewed
  PR #78 merge `f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852`, its annotated tag and green release workflow;
  `docs/planning/operator_gates.md` (0.31.0) records release execution, and
  `docs/planning/HANDOVER.md` (1.0.1) adds current status above its historical snapshot.
  The manifest completion note records the post-phase release. GitHub Latest and
  consumer pins select `v1.5.0`; real public-tag bootstrap and payload12/12 passed.
  The operator's GA decision and explicit historical evidence exceptions remain
  unchanged. No injected payload or completed phase acceptance infrastructure changes.

## [1.5.0] - 2026-10-10

**Minor release** (`methodology/06_release_train.md` Section 3.2): phase 014 (GA track)
and its maintenance tranche land in the injected payload. The two ecosystem lifecycle
protocols are now normative -- `ecosystem/06_simplification_review.md` (Repeat) and
`ecosystem/08_ga_gate.md` (Promote/GA) flip `draft` -> `active` (0.2.0 each) and are
registered as capabilities in `NIZAM.json` and `tools/skill.json` (0.4.0), with the
operator gates `H-CONSOLIDATION` and `H-GA` defined in
`docs/planning/operator_gates.md` -- H-CONSOLIDATION remains OUTSTANDING; H-GA is EXECUTED by the operator
on 2026-10-10. `standard/capability_profiles.md` (0.4.0) gains an explicit
`Role` column whose mapping the validator's C15 check now enforces, and the
convergent-review suite ships a required-conformance mode with its own CI job. This is
additive protocol surface with validator enforcement changes. C1/C2 docs/nips and
C15 mapping checks widen the default sweep. C13 enforces the intentional-subset
rule in both full sweep and `--payload`: every skill capability module must equal
a NIZAM.json capability authoritative_source, so an existing but unindexed module
now fails. The shipped manifest/index pair remains compliant; independently added
modules must be registered. The release tier is rounded up per Section 3.4. Upgrade path:
consumers re-bootstrap from the `v1.5.0` tag to inherit the payload
(`methodology/06_release_train.md` Section 5). Everything else in this release is
framework-envelope only (the phase-014 close and GA-readiness dossier, planning
records, and the backlog reconciliation), none of which `bootstrap.sh` injects.

General Availability declared by the operator on 2026-10-10. H-GA is EXECUTED; H-CONSOLIDATION remains OUTSTANDING. The declaration proceeds with explicit evidence exceptions: `real_production_pilot` is `not_met`; `recorded_consumer_adoptions` is `insufficient_evidence`. These gaps remain recorded in the historical readiness dossier; recorded evidence gaps remain unresolved.

### Added

- **Phase 014 feature 109: C15 mapping direction** (additive; MINOR,
  `methodology/06_release_train.md` Section 3.2). `standard/capability_profiles.md`
  (0.4.0) gains an explicit `Role` column naming each capability profile's AGF role,
  and `tools/verify_lib.sh` gains the `vlib_profiles_map_roles` primitive parsing it:
  validator check C15 (default sweep) now calls both the coverage and the mapping
  primitives, so a swapped profile-to-role mapping fails. Additive and
  compatibility-first: `vlib_profiles_cover_roles` is unchanged. NDEBT-026.

### Changed

- **v1.4.0 post-release refresh and phase-014 re-baseline** (planning records only;
  nothing `bootstrap.sh` injects changes). `docs/planning/ROADMAP.md` (v0.45.0) rolls
  Current Position to name `v1.4.0` as the latest released tag (annotated tag object
  `bb32064` at `9edd5d0`, PR #63; `release.yml` run 37763448754 succeeded with the
  blocking tag-mode close-out passing; Release published 2026-10-08T10:26:22Z) and
  removes the preparation bullet; `docs/planning/operator_gates.md` (v0.26.0) records
  `H-FRAMEWORK-RELEASE` EXECUTED for v1.4.0 on the existing row. Under operator decision
  D1 (recorded in `run_state` before the act; not `H-PHASE-014`), the pending phase-014
  proposal is re-baselined for the facts v1.4.0 made stale: feature 100's pilot pin moves
  from `v1.3.0` to `v1.4.0`, and feature 102's tag-absence assertion moves from `v1.4.0`
  to `v1.5.0`, the next MINOR (`.agent/product_spec_014.md` 1.0.1,
  `.agent/feature_list_014.json`, `docs/planning/phase_014.yaml`, and the manifest's
  phase-014 note). Phase 014 stays `pending` / `proposed`, awaiting `H-PHASE-014`.
- **Phase 014 activated, with its maintenance tranche, and the backlog reconciled**
  (planning records only; nothing `bootstrap.sh` injects changes). The operator exercised
  `H-PHASE-014` with the proposed amendments and folded in the maintenance tranche; the
  decision was recorded in `run_state` before the re-planning.
  `.agent/product_spec_014.md` moves to 1.1.2, `active`, with
  `.agent/feature_list_014.json` in lockstep. Feature 101 now depends on 099. Every
  acceptance test captures exit status and is probed against the pre-implementation tree,
  and a phase-scoped tag check replaces the fixed-version test; tests beyond the operator's
  enumerated amendment list are Planner hardening, which the operator acknowledged. Features 103–109 schedule
  `NDEBT-043`, then `NDEBT-041`, plus `NDEBT-042`, `NDEBT-044` (split by concern),
  `NDEBT-037` and `NDEBT-026`, all ahead of feature 102. The scope is re-baselined from
  2200 to 6660 lines, with a ceiling of 8658: the Planner's estimate (naive 2890 × the
  measured 2.3 process weight), which the operator approved. `docs/planning/phase_014.yaml` is
  `in_progress` and the manifest's `current_phase` is `014-ga-track`;
  `docs/planning/operator_gates.md` (v0.27.0), `docs/planning/ROADMAP.md` (v0.46.0) and
  `docs/planning/DEBT.md` (v0.48.0) record the activation. Two new files,
  `docs/planning/backlog_reconciliation.md` and `docs/planning/backlog_dag.json`, map the
  maintainer brief to existing ids and give the candidate DAG for the work after phase 014.
- **Phase 014 feature 099: GA-track activation wave** (additive; MINOR at the next release,
  `methodology/06_release_train.md` Section 3.2; no release is prepared and no tag is
  created). `ecosystem/06_simplification_review.md` (Repeat) and `ecosystem/08_ga_gate.md`
  (Promote/GA) move from `draft` to `active` (0.2.0 each) and are registered as capabilities
  in `NIZAM.json` and `tools/skill.json` (0.4.0); the ecosystem card in the user guide lists
  every ecosystem document (00-08); `ecosystem/README.md` (0.5.0) is re-synced. The operator
  gates `H-CONSOLIDATION` and `H-GA` are defined in `docs/planning/operator_gates.md`
  (0.28.0) as DEFINED and OUTSTANDING: neither is exercised, no operator decision is
  recorded for either, and GA is not declared.
- **Phase 014 feature 103: Sandbox prerequisite handling** (additive; MINOR at the next release,
  `methodology/06_release_train.md` Section 3.2; no release is prepared and no tag is created).
  `tools/test_convergent_review.py` now probes the host's user-namespace capability directly. When
  isolation is unavailable it reports each of the five sandbox-dependent tests as `UNSUPPORTED`,
  prints `CONFORMANCE: NOT FULL` and exits non-zero (required-conformance mode is the default);
  the new local-development flag `--allow-unsupported-isolation` turns that same outcome into
  exit 0 without masking any other failure, and a capable host prints `CONFORMANCE: FULL`.
  `tools/linux_trial_sandbox.sh` and `tools/isolated_trial_adapter.py` are unchanged (still fail
  closed) and `tools/README.md` (0.12.0) documents both outcomes. NDEBT-043; the capable-host
  evidence is to be provided by feature 104 (not exercised by this feature).
- **Phase 014 feature 104: Convergent-review suite enforced in CI** (additive; MINOR at the next release,
  `methodology/06_release_train.md` Section 3.2; no release is prepared and no tag is created).
  `.github/workflows/compliance.yml` gains one job, `convergent_review`, that runs
  `tools/test_convergent_review.py` in required-conformance mode (never with
  `--allow-unsupported-isolation`) after a guarded step that enables unprivileged user namespaces
  only where the kernel exposes the AppArmor restriction key; the already-pinned action SHAs are
  reused, so C14 stays PASS. `standard/definition_of_done.md` (0.2.0) Sections 8 and 11 now name four
  jobs, `tools/README.md` (0.13.0) names the job in Machine Validation, and `schema/README.md`
  (0.19.0) states that the suite is the sole validator of the review schema family (C12 coverage
  of that family is left to the phase-014 simplification review). NDEBT-041; the CI evidence, a
  green run and a throwaway-branch negative control that also supplies the capable-host evidence
  for feature 103, is recorded under `.agent/evidence/104/`.
- **Phase 014 feature 105: Nested-fixture ownership** (framework-internal; PATCH at the next release,
  `methodology/06_release_train.md` Section 3.3; no release is prepared and no tag is created).
  `tools/fixtures_self_test.sh` gains a fixture-subdirectory claim map (the NIP-0003 feature-109
  design, pulled forward): every subdirectory of `tools/fixtures/` is claimed by exactly one owning
  suite, and the completeness guard now accounts for every file at any depth, where it previously
  accounted for the top-level files only and was blind to the 67 files below
  `tools/fixtures/convergent_review/`. It fails on an unclaimed subdirectory, a doubly-claimed one,
  a claim naming a suite file that does not exist and a claim naming an absent subdirectory, and the
  self-test demonstrates those cases itself in a private scratch area. A claim proves ownership, not
  execution. `tools/README.md` (0.14.0) describes the claim map. No fixture moves. NDEBT-042.
- **Phase 014 feature 106: Capability-index parity** (MINOR at the next release,
  `methodology/06_release_train.md` Section 3.2; no release is prepared and no tag is created).
  Parity between `tools/skill.json` and `NIZAM.json` is an intentional subset, not equality:
  every skill-module path must be the authoritative_source of some NIZAM.json capability, and
  NIZAM.json-only entries stay allowed. C13 enforces that rule in the full sweep and under
  `--payload`. No new check number is added (C17 stays earmarked by NIP-0003). `NIZAM.json`
  gains capability `nizam-ecosystem-bootstrap` (`ecosystem/00_ecosystem_bootstrap.md`).
  The negative fixture `tools/fixtures/skill_index_neg_unindexed_capability.json` is exercised
  by the existing C13 substitution. `tools/README.md` (0.15.0) records the decision. NDEBT-044 (a).
- **Phase 014 feature 107: docs/nips under C1/C2** (additive; MINOR,
  `methodology/06_release_train.md` Section 3.2). In the default sweep only,
  `tools/validate.sh` checks C1 (frontmatter schema) and C2 (format) over every
  markdown file under `docs/nips/`; those files stay outside the shipped-doc set, so
  C9/C10 do not scan them and `--payload` is unchanged. NIP-0002's frontmatter status
  moves `accepted` -> `active` (0.2.1), the schema enum value for an accepted NIP
  (NDEBT-044 b). `tools/README.md` (0.16.0) names the C1 row change.
- **Phase 014 feature 108: validator help and adapter-reference truth** (PATCH,
  `methodology/06_release_train.md` Section 3.3). `tools/validate.sh --help` is
  corrected: the C14-C16 paragraphs describe the checks as actually implemented (C15
  now names both primitives; C16 names the vetted feature-list primitive), the C5
  branding-sweep text matches its implementation, and the payload-doc-set wording
  matches the shipped file-set builders. `tools/interface.md` (0.3.1) corrects one
  citation (Section 5 item 10 cites Section 2 item 5, not item 4); the checklist stays
  at 10 items, so every adapter remains conformant. NDEBT-037, NDEBT-044 (c/d/f).
- **Phase 014 close and envelope.** Feature 102 assembled the GA-readiness dossier and
  closed the phase canonical-first; its historical dossier recorded no GA declaration
  and `real_production_pilot` `not_met` per amendment A3. The operator declaration
  above is the subsequent decision. Amendments A1/A2
  (acceptance-test corrections) and A3 (features 100/101 cancelled) are planning
  records, as are the backlog reconciliation (`docs/planning/backlog_reconciliation.md`,
  `backlog_dag.json`) and the phase-014 planning artifacts -- nothing `bootstrap.sh`
  injects changes.

## [1.4.0] - 2026-10-08

**Minor release** (`methodology/06_release_train.md` Section 3.2): consumers receive two
new ecosystem lifecycle protocol documents, `ecosystem/06_simplification_review.md`
(Repeat: recurring simplification review) and `ecosystem/08_ga_gate.md` (Promote/GA:
evidence-gated GA declaration criteria), together with their `ecosystem/README.md` rows
and `NIZAM.json` ecosystem `key_documents` entries. Both documents ship proposal-grade
(`status: draft`) and are **not yet normative**: their activation (the draft → active
flip, capability registration, and the definition of the reserved `H-CONSOLIDATION` /
`H-GA` gates) awaits phase-014 feature 099 under the operator gate `H-PHASE-014`. This is
purely additive, new-optional surface -- nothing that validated under v1.3.0 is
invalidated. Everything else in this release is framework-envelope only (planning
records, the phase-014 Planner artifacts, and the NIP-0003 proposal), none of which
`bootstrap.sh` injects. The NIP-0003 entry below quotes that proposal's own expectation
of v1.4.0 / v1.5.0 for its phases 015/016; because this release takes v1.4.0, those
phases would now release as v1.5.0 / v1.6.0 (the NIP itself stays unedited pending
`H-NIP`).

### Added

- **Phase 014 proposal (GA track — the real multi-repo pilot and the remaining
  lifecycle protocols)** (the rolled-forward phase-012 candidate scope). Authored the
  Planner artifacts `.agent/product_spec_014.md` (status `draft`),
  `.agent/feature_list_014.json` (features 099–102, DAG-validated acyclic, roots
  `{099, 100}`, est 2200), and the canonical pending `docs/planning/phase_014.yaml`,
  plus the two lifecycle protocol documents proposal-grade (`status: draft`):
  `ecosystem/06_simplification_review.md` (Repeat — recurring simplification;
  consolidations only under the reserved `H-CONSOLIDATION` gate) and
  `ecosystem/08_ga_gate.md` (Promote/GA — evidence-gated declaration criteria under
  the reserved `H-GA` gate; benchmark thresholds are acceptance requirements, never
  claims of achieved results; GA declaration is operator-only — the framework must
  never auto-declare GA). `docs/planning/ROADMAP.md` (v0.42.0) also rolls the v1.3.0
  released record (post-release refresh) and tops with the phase-014 proposal banner;
  `docs/planning/manifest.json` gains the phase-014 entry (`pending`/`proposed`);
  `docs/planning/operator_gates.md` (v0.24.0) records the executed v1.3.0 release and
  names phase 014 as the reserved gates' definition site; `ecosystem/README.md`
  (v0.4.0) flips the `06`/`08` rows to Shipped; `NIZAM.json`'s ecosystem
  `key_documents` enumerates both documents (the NDEBT-005 disk-to-index
  completeness guard requires an on-disk `ecosystem/*.md` to be indexed in the
  same change it lands — the `capabilities` array, `tools/skill.json`, and the
  guide card stay with phase-014 feature 099). Awaiting activation gate
  `H-PHASE-014`; `current_phase` stays `013-definition-of-done` and `run_state` is
  untouched (a proposal is not an activation).
- **NIP-0003 proposal (Live Runtime Sessions)** —
  `docs/nips/NIP-0003-live-runtime-sessions.md` (v0.1.0, `draft`; PROPOSED, awaiting
  `H-NIP`). Records the read-only validation of a third-party Agent–REPL Execution
  Protocol (adopt with corrections) and the operator's four decisions of 2026-10-08,
  and proposes a language-neutral live-runtime-session protocol with an SBCL reference
  binding, generic definitions of "attempt" and "own execution context", an optional
  adapter capability (`tools/interface.md` §5 stays at 10 items), session schemas
  under an extended C12, and a reference controller with a live CI conformance job —
  realized as phases 015 (features 103–107) and 016 (108–113) to follow phase 014,
  each releasing as the next MINOR (expected v1.4.0 / v1.5.0). Acceptance would
  select, not activate. `docs/planning/DEBT.md` (v0.47.0) logs four re-verified Open
  rows: `NDEBT-041` (the convergent review suite runs in no CI job), `NDEBT-042` (the
  fixtures completeness guard skips subdirectories), `NDEBT-043` (sandbox tests fail
  instead of skipping when user namespaces are restricted) and `NDEBT-044` (index and
  documentation drift). `docs/planning/ROADMAP.md` (v0.43.0) gains a "Queued
  Candidate — NIP-0003" section below the unedited phase-014 banner. `run_state`,
  `docs/planning/manifest.json` and `docs/planning/operator_gates.md` are untouched
  (a proposal is not an activation).

## [1.3.0] - 2026-09-30

**Minor release** (`methodology/06_release_train.md` Section 3.2): Review-Gate
Flake Management delivers the operational doctrine for infrastructure failures
of convergent review gates as purely additive, new-optional capability --
nothing that validated under v1.2.0 is invalidated.

### Added

- **Review-Gate Flake Management methodology, `methodology/09_review_gate_flake_management.md`.**
  Operational doctrine for the failure family where a convergent review gate
  ends red for infrastructure reasons distinct from any review verdict:
  five fail-closed principles (fail-closed is correct; red is non-terminal;
  never fake green; flake is not a verdict; a green claim requires the gate's
  own output), the open F1–F6 flake-class taxonomy (no-output; hang/timeout;
  behavior/mis-tie; large-packet zero-write; posting/API failure;
  provider-degradation windows — new classes require evidence plus a versioned
  doc revision), the bounded retry ladder (initial attempt with bounded
  trial-local retry, ONE re-dispatch, then class-exception or honest re-run —
  never both, never a third dispatch), protected-repository rules (flakes are
  never merged around; disposition is re-run patience plus the upstream fix),
  telemetry duties (per-run outcome/class/attempt artifacts, a central ledger
  rollup, optional synthetic probes), evidence duties (artifact naming,
  post-merge evidence races, canonical-vs-vendored resync in one wave — drift
  is a defect class of its own), and KPI targets (flake-rate per run,
  exception-merges to zero, mean-time-to-green) measured by the ledger.
  Cross-references `methodology/03_circuit_breaker.md` for attempt counters
  without duplicating its mechanics. Registered in `NIZAM.json` (capability
  index and methodology module key_documents), `methodology/README.md`, and
  `docs/guide/index.html`'s methodology module card.

### Fixed

- **Release-state drift in `docs/planning/ROADMAP.md` and
  `docs/planning/operator_gates.md`.** The v1.2.0 preparation bullets were
  stale: v1.2.0 was in fact released (2026-09-17, tag at `7441ffa`, `release.yml`
  run 35232527341) and a v1.2.1 PATCH tag exists (2026-09-19, `250fdd9`, PR #59)
  whose `release.yml` run 35456401143 failed the tag-mode close-out
  (`tag v1.2.1` vs anchors still at `1.2.0`; no `[1.2.1]` CHANGELOG section was
  cut). Both docs now record the genuine release facts; this v1.3.0 preparation
  rolls every version anchor forward together, superseding the anomaly.

## [1.2.0] - 2026-09-17

**Minor release** (`methodology/06_release_train.md` Section 3.2): the Convergent
Automated Code Review standard (PR #57) delivers a runtime-neutral, prior-ledger-first,
authenticated three-trial review protocol as purely additive, new-optional capability --
nothing that validated under v1.1.0 is invalidated.

### Added

- **Convergent Automated Code Review standard, `standard/convergent_code_review.md`.**
  Defines a review protocol usable with any model or review agent, without delegating
  review state or merge authority to that model: a model is an observation-only sensor
  that MUST NOT assign trusted finding identifiers, lifecycle states, counts,
  suppressions, or verdicts; deterministic code owns semantic fingerprints, lifecycle
  transitions, counts, the final verdict, Markdown rendering, the embedded ledger, and
  replay verification. Covers authenticated, full-tree packet scope built from immutable
  Git objects, prior-ledger-first ordinary review plus a full-audit mode, sandboxed
  trial isolation, human suppression, and content-addressed replay.

- **Five closed review schemas.** `schema/review_packet.schema.json` (authenticated
  old/current bytes, Git mode deltas, and the mode-dependent full-audit commit/tree
  manifest), `schema/review_trial.schema.json` (one observation-only trial output bound
  to the packet digest), `schema/review_ledger.schema.json` (the deterministic finding
  ledger: semantic fingerprints, `new`/`persisting`/`resolved`/`reopened`/`suppressed`
  lifecycle, consensus, counts, and verdict), `schema/review_suppression.schema.json`
  (human suppression authorization records), and `schema/review_replay.schema.json`
  (content-addressed replay manifests). All five are fully closed
  (`additionalProperties: false`); registered in `schema/README.md`.

- **Convergent-review prompt template, `templates/convergent-review-prompt.md`.** A
  runtime-neutral, closed-output trial prompt for exactly three independent
  observation-only reviews over an authenticated packet, rendered by
  `tools/evaluate_convergent_review_prompt.py` inside the mandatory per-trial sandbox.
  Registered in `templates/README.md` as the module's ninth governed template.

- **Convergent-review tooling, `tools/`.** `convergent_review.py` (the dependency-free
  deterministic library and CLI: trusted no-replace Git-object packet construction,
  authenticated content/mode deltas, structural-plus-relational validation, semantic
  fingerprints, three-trial convergence, lifecycle and verdicts, canonical JSON and
  embedded-ledger Markdown, trust-anchored no-follow replay, and atomic no-replace
  publication), `evaluate_convergent_review_prompt.py` (the prompt evaluator),
  `linux_trial_sandbox.sh` and `isolated_trial_adapter.py` (the Linux reference sandbox
  adapter: user/network/IPC/UTS/PID namespaces plus Landlock filesystem confinement,
  execute permission limited to the trusted runner and runtime), and
  `test_convergent_review.py` (a permanent stdlib `unittest` suite over a frozen
  12-case corpus, indexed by `tools/fixtures/convergent_review/manifest.json`, plus
  adversarial blocker regressions). Registered in `tools/README.md` and `tools/SKILL.md`.

## [1.1.0] - 2026-08-19

**Minor release** (`methodology/06_release_train.md` Section 3.2): phase 013 (Definition
of Done) delivers six purely additive, new-optional features -- the canonical layered
Definition of Done (`standard/definition_of_done.md`, feature 093), the feature-list
lifecycle invariant as validator check C16 (feature 092), the release close-out gate
(`.github/scripts/release_closeout.py`, feature 097), the optional advisory `dod_ref`
key on five schemas (feature 094), and its two consumer projections
(`templates/DoD.md`, feature 095; `.github/PULL_REQUEST_TEMPLATE.md`, feature 096) --
nothing that validated under v1.0.0 is invalidated.

### Added

- **Feature-list lifecycle invariant, validator check C16 (phase 013, feature
  092).** `tools/validate.sh` mechanizes "complete implies approved contract
  and passing QA verdict and evidence on disk" over every
  `.agent/feature_list*.json`: schema validation against
  `schema/feature_list.schema.json`, plus an era-safe referential rule --
  for every `status: "complete"` feature, IF `.agent/contracts/<id>.json`
  exists THEN `.agent/qa/<id>.json` must also exist, and any `evidence_files`
  it lists must resolve on disk. Wired into the default sweep (after C15),
  `--target` (schema-only, via a new `features`+`original_estimate_lines`
  route on `check_c11_or_c4_target`), and `--payload` (a counted trivial
  pass, mirroring C11's precedent) modes, with new positive/negative
  fixtures and `tools/fixtures_self_test.sh` coverage. Also corrects
  `schema/README.md`'s `feature_list.schema.json` row, which previously
  named no enforcing check.

- **Canonical Definition of Done, `standard/definition_of_done.md` (phase
  013, feature 093).** The framework's layered Definition of Done: 13
  numbered sections aggregating the eight done-layers (Step, Handoff, Gate,
  Feature, Plan, Merge, Release, Ecosystem) by citing each layer's existing
  authority rather than restating its mechanics. Defines `complete` over
  the existing five-value `schema/feature_list.schema.json` enum, with no
  `done` state added anywhere. Feature-Done is verified by check C16;
  Merge-Done and Release-Done by the phase-013 feature-097 release
  close-out gate; every other layer is consumer-aspirational. Registered
  in `NIZAM.json` (capability index and `standard` module key_documents),
  `standard/README.md` (index row, version 0.2.1 -> 0.3.0), and
  `docs/guide/index.html`'s `standard/` module card.

- **Release close-out gate, `.github/scripts/release_closeout.py` (phase
  013, feature 097).** A stdlib-only, network-free script mechanizing
  internal version-anchor consistency across the release surface
  (NIZAM.json's `framework.version` as the single reference, compared
  against CONTEXT.md frontmatter + `change_log[0]`, `docs/guide/index.html`'s
  meta/footer spans, README.md's four version pins, CHANGELOG.md's top
  released section heading + tier banner, and `docs/planning/ROADMAP.md`'s
  body-scoped disposition line), generalizing the
  `require(label, condition)` style of
  `.agent/evidence/091/verify_release_prep.py`. Two modes: `--mode pr`
  asserts the working tree's anchors against each other, wired as a new
  paths-filtered pull-request workflow,
  `.github/workflows/release_closeout.yml`; `--mode tag --tag vX.Y.Z`
  reads every anchor as it existed AT THE TAG via `git show`, plus three
  tag-specific checks (tag shape, tag-vs-anchor, CHANGELOG-vs-tag), wired
  as a new blocking step in `.github/workflows/release.yml` between tag
  resolution and CHANGELOG extraction so a version-inconsistent tree can
  never reach GitHub Release publication. Era-safe by construction:
  file-level anchor absence and pre-convention ROADMAP dispositions SKIP
  rather than fail or crash, while a present-but-incomplete anchor (e.g.
  CONTEXT.md with no `change_log` key) emits a named FAIL. The script
  never invokes `git tag` or `git push` -- read-only comparison only.

- **Optional advisory `dod_ref` key, five schemas (phase 013, feature
  094).** Adds an identically worded, optional, advisory `dod_ref` string
  property to `schema/contract.schema.json`, `schema/qa_verdict.schema.json`
  (both `anyOf` branches), `schema/feature_list.schema.json` (top level),
  `schema/work-packet.schema.json`, and
  `schema/engineering_finding.schema.json`, naming
  `standard/definition_of_done.md` as the artifact's governing Definition of
  Done. Touches no `required` array anywhere, a pure loosening per
  `methodology/06_release_train.md` Sec 3.2: every previously-valid artifact
  remains valid. Proved with a positive fixture
  (`tools/fixtures/feature_list_valid.json` gains a `dod_ref`) that still
  validates and still passes the C16 `--target` sweep, plus the full default
  `tools/validate.sh` sweep's existing dogfood coverage. Pairs a
  `schema/README.md` conventions-list sentence and a version bump
  (0.14.0 -> 0.15.0) with a matching change_log entry.

- **Pull-request checklist, `.github/PULL_REQUEST_TEMPLATE.md` (phase 013,
  feature 096).** A plain-markdown PR template naming
  `standard/definition_of_done.md` as the canonical Definition of Done and
  projecting its Merge-Done layer into nine reviewer-facing checkboxes: the
  full `tools/validate.sh` sweep, `tools/fixtures_self_test.sh`,
  `tools/e2e_bootstrap_test.sh`, check C8's version/change_log pairing,
  the check C16 contract-QA-evidence chain, the
  `methodology/04_tool_driven_state.md` Section 5 evidence shape, a
  `CHANGELOG.md` `[Unreleased]` entry, the phase-013 feature-097 release
  close-out gate, and the never-self-merge / operator-only-tag rule. Not a
  governed doc under NDS.md: carries no frontmatter and rides outside
  every check's shipped/payload document sweep by design.

- **Consumer Definition of Done checklist, `templates/DoD.md` (phase 013,
  feature 095).** The copy-and-fill projection of
  `standard/definition_of_done.md` onto a per-project checklist: seven
  Section-N-cited checklist blocks (Step through Release), a non-checklist
  Ecosystem-Done pointer paragraph citing Section 10, a
  `{{PROJECT_SPECIFIC_DONE_CRITERIA}}` extension block, a floor-not-guarantee
  closing note citing Section 12, and a `dod_ref` linking note pointing at
  the optional advisory key phase 013, feature 094 added to several Nizam
  schemas. Registered in `NIZAM.json` (both the top-level `templates[]`
  array and `modules[path=="templates"].key_documents`) and
  `templates/README.md` (new index row, `## Frontmatter Convention`
  parenthetical, description enumeration, version 0.2.2 -> 0.3.0).

## [1.0.0] - 2026-08-15

**Major release** (`methodology/06_release_train.md` §3.1): phase 012 resolves the
complete consumer-safety audit in issue #52. This release deliberately tightens
previously shipped schema contracts, so consumers must re-bootstrap from the immutable
`v1.0.0` tag and repair consumer-owned artifacts with
[`docs/migration-v1.0.0.md`](docs/migration-v1.0.0.md). There is no compatibility mode.

Release preparation is complete, but publication remains gated by
`H-FRAMEWORK-RELEASE`; the pipeline does not create or push the tag.

### Breaking

- **v1.0.0 schema invariant repair (phase 012, feature 086; issue #52).** Evidence
  paths now name an artifact below `.agent/evidence/`; membership registry versions
  use canonical SemVer 2.0.0; successful preflight verdicts reject
  `blocking_findings`; pin-consistent membership results require a non-empty common
  `framework_pin`; and failed reconciliation plans require non-empty
  `cycle_findings` with an empty `order`. These intentionally narrow v0.9.0
  contracts and therefore require the clean-break steps in
  `docs/migration-v1.0.0.md`.

### Fixed

- **Compare reopened classification (phase 012, feature 087; issue #52).** A
  finding that was resolved in the earlier audit and is open again in the later
  audit is now emitted only as `reopened`, with its later evidence preserved,
  rather than being misrouted to `persisting` or `stale`.

### Changed

- **Consumer-facing protocol truth (phase 012, feature 089; issue #52).** Genesis
  is explicitly scaffold-and-inject automation, with consumer decisions, registry
  enrollment, and Preflight/Baseline still required; ecosystem lifecycle summaries,
  reconciliation membership invariants, reopened semantics, validator enforcement
  claims, brownfield responsibility, and all eight C12 fixture families now match the
  shipped schemas and tools.
- **Fixture scratch isolation (phase 012, feature 087; issue #52).** The fixture
  harness now creates and cleans exact temporary roots through one guarded helper;
  all eleven scratch probes reject repository paths and retain their existing
  behavior.
- **Methodology safety reconciliation (phase 012, feature 088; issue #52).**
  Retry attempts now run in isolated worktrees/snapshots and remove only the
  exact failed attempt root after evidence capture; canonical phase state is
  written before idempotently repaired derived run state. The five-role model,
  prior-only scope baseline, evidence-before-completion gate, release-preparation
  validation, three-attempt eval behavior, gated fallback repinning, and
  Orchestrator routing/authorship boundary are now consistent across the shipped
  methodology.

## [0.9.0] - 2026-07-22

**Minor release** (`methodology/06_release_train.md` §3.2): the first release since
`v0.8.0`, carrying **five phases (007–011)** of purely additive, new-optional
capability — nothing that previously validated or worked is invalidated. It cuts a
tag that finally carries the **whole 0–n loop** into a consumable pin (`NDEBT-029`):

- **Consumer-adoption enablement** (phase 007) — the Bootstrap-stage protocol
  `ecosystem/00_ecosystem_bootstrap.md` + the `H-CONSUMER-UPGRADE` gate.
- **NIP-0002 (The 0–n Project Spectrum), fully realized** across phases 008–011 —
  consumer-readiness (ADR-004 governance-root resolution + provenance-pin anchoring +
  SHA-pinned bootstrap), the 0-case (greenfield genesis, `bootstrap.sh --genesis`),
  the n-case (a required, schema-validated ecosystem-membership registry + multi-repo
  iteration/aggregation), and the Stage-4 coordination protocols (`ecosystem/04`
  dependency reconciliation + `ecosystem/05` release-train coordination, with the
  `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates).
- **The ecosystem tooling** — `tools/ecosystem_audit.py`,
  `tools/compare_ecosystem_baselines.py`, `tools/validate_evidence_freshness.py`,
  `tools/ecosystem_membership_run.py`, `tools/ecosystem_reconcile.py`, and
  `tools/ecosystem_release_train.py` — all now shipped in the tag, so a consumer on the
  released pin can run the full lifecycle without pointing at the framework working tree.
  The existing **C12** validator check (which predates v0.9.0) gained four new schema
  families — `ecosystem_membership`, `ecosystem_membership_result`, `reconciliation_plan`,
  and `release_train_manifest` — guarding the new artifact types.

Additive by construction: the new schemas validate *new* artifact types (they do not
narrow any previously-shipped schema), and the new C12 families guard *new* fixture
families (the C1–C15 check set is unchanged). A consumer upgrades by re-running
`bootstrap.sh` against `v0.9.0`
(`methodology/06_release_train.md` §5). A **real, non-scratch multi-repo pilot** at this
released tag remains the standing production-maturity criterion — this release *enables*
it rather than declaring it.

### Added

- **Phase 011 (0–n Project Spectrum, Stage 4: n-Coordination Protocols) complete — NIP-0002's staged
  plan is complete** (feature 084; `NDEBT-035`). Piloted the coordination layer end-to-end against a
  scratch **2-member** ecosystem stood up **from nothing** at one shared pin, using the fixed tooling
  (080–083): a schema-validated membership registry → a **PASS** aggregate → a **PASS** reconciliation
  plan (topologically ordered) → a **PASS** release-train manifest — all C12-valid — with both
  Stage-4 gates exercised and recorded before the acts they govern (`H-PLANNING-AUTHORITY` before the
  plan, `H-TRAIN-ENTRY` before the train; NDEBT-018), and both invariants proven load-bearing by
  negatives (a cyclic plan → `FAIL`, an ungated train → `FAIL`) — with no hand-applied workaround
  (evidence `.agent/evidence/pilot-084/`). `NDEBT-035` resolved; `manifest.json` + `run_state` reflect
  phase-011 completion; ROADMAP (v0.29.0) rolls Current Position to phases 001–011 complete and validates
  the phase-012 candidate scope (the `NDEBT-029` release cut carrying the whole 0–n loop, a real
  non-scratch multi-repo pilot, and the remaining `06`/`08` Repeat/GA protocols). A real, non-scratch
  multi-repo pilot at a released tag remains the open production-maturity criterion.
- **`tools/ecosystem_release_train.py` + Stage-4 e2e coverage** (phase 011 feature 083; `NDEBT-035`;
  NIP-0002 Stage 4). A stdlib-only Promote-stage tool that reads a reconciliation plan (feature 082) and
  **produces** a schema-valid release-train manifest at `<output-dir>/manifest.json`
  (`schema/release_train_manifest.schema.json`), admitting the plan's packets into a cross-repository
  release train. The **`H-TRAIN-ENTRY`** gate is load-bearing: the tool **refuses to emit a `PASS` train**
  without the recorded admission decision (`--entry-gate-recorded`), and it never itself promotes — a
  record-but-never-self-execute Promote. An orphan admission (an `--admit` id with no plan origin) is a
  recorded finding forcing `train_verdict` `FAIL`; a non-`PASS` source plan is a usage error. Exit table
  `0`/`1`/`64`. Extended `tools/e2e_bootstrap_test.sh` with **`assert_stage4`**, chained onto the
  phase-010 `assert_multirepo` aggregate (no fresh genesis clone — the per-member cost is `NDEBT-034`):
  it runs the **aggregate → reconciliation → release-train** chain across the 2-member set, asserting a
  `PASS` plan + a `PASS` train manifest (both C12-valid) and that an **ungated** admission is correctly
  refused a `PASS`. The single-repo + n-case paths stay green.
- **`tools/ecosystem_reconcile.py` — the Plan-stage tool** (phase 011 feature 082; `NDEBT-035`;
  NIP-0002 Stage 4). A stdlib-only tool that reads the phase-010 ecosystem-level membership-run
  aggregate (`schema/ecosystem_membership_result.schema.json`) for the authoritative `in_scope` set plus
  a packets-input file, and **produces** a schema-valid, dependency-ordered reconciliation plan at
  `<output-dir>/plan.json` — the hand-aggregation made a produced artifact. It computes the topological
  order via Kahn's algorithm; a **cyclic** cross-repo dependency set is a first-class recorded finding
  (`cycle_findings`) forcing `plan_verdict` `FAIL` and a non-zero exit, never a silent mis-order. Exit
  table mirrors the sibling tools: `0` PASS plan, `1` FAIL plan (cycle), `64` usage error (unknown target
  repo, dangling edge, malformed input). A standing `fixtures_self_test.sh` CLI probe guards the polarity
  (acyclic → PASS + a C12-valid plan; cyclic → FAIL(1); unknown repo → usage(64)). `self-test` 63/63 + 7 probe groups.
- **`ecosystem/05_release_train_coordination.md` + `schema/release_train_manifest.schema.json` — the
  Promote stage** (phase 011 feature 081; `NDEBT-035`; NIP-0002 Stage 4). Authored the lifecycle's
  Promote-stage protocol: an operator-authorized reconciliation plan's work packets are admitted into a
  **cross-repository release train**, under the **trace-to-plan invariant** — every admitted packet
  traces to a plan packet, and an orphan admission is a first-class recorded finding forcing a
  non-`PASS` `train_verdict`. The companion schema validates the manifest shape (`source_plan` + its
  `plan_packets`, `admitted_packets`, `train_members`, the `entry_gate_recorded` flag, the verdict)
  with one in-schema `if/then` (a `PASS` train requires the admission recorded); the trace-to-plan
  invariant is enforced in code by `validate.sh` C12 as the **eighth** ecosystem schema family (both
  entry points, discriminated by `train_verdict`/`admitted_packets`), with one positive and two negative
  fixtures (schema-invalid ungated-`PASS` + a trace-to-plan-violating orphan + a repo-mismatch; the
  manifest's `plan_packets` carries the plan's `(id, repo)` mapping so the trace-to-plan check binds
  both fields). The reserved gate
  **`H-TRAIN-ENTRY`** is now **defined** (moved `operator_gates.md` Section 2 → Section 1; v0.13.0).
  Registered in `NIZAM.json`, `schema/README.md` (v0.12.0), `tools/skill.json`; the `ecosystem/README.md`
  (v0.2.3) module-nav `05` row flips Planned → Shipped (seven documents Shipped; with `04` + `05` both
  shipped, NIP-0002 Stage 4's coordination protocols are complete). `self-test` 63/63.
- **`ecosystem/04_dependency_reconciliation.md` + `schema/reconciliation_plan.schema.json` — the Plan
  stage** (phase 011 feature 080; `NDEBT-035`; NIP-0002 Stage 4). Authored the lifecycle's Plan-stage
  protocol: approved engineering-audit findings plus the phase-010 ecosystem-level membership-run
  aggregate become **typed, dependency-ordered cross-repository work packets**, under the
  topological-order invariant — a cyclic `depends_on` set is a first-class recorded finding forcing a
  non-`PASS` `plan_verdict`, never a silent mis-order. The companion schema validates the plan shape
  (per-repo packets, typed edges, the emitted order, the verdict); the cycle invariant is enforced in
  code by `validate.sh` C12 as the **seventh** ecosystem schema family (both entry points, discriminated
  by `plan_verdict`/`cycle_findings`), with one positive and two negative fixtures (schema-invalid
  missing-verdict + a cyclic-but-`PASS` + a bad-`order`-but-`PASS`; C12 verifies `order` is a full
  topological permutation of the packet ids, not merely acyclic). The reserved gate **`H-PLANNING-AUTHORITY`** is now **defined**
  (moved `docs/planning/operator_gates.md` Section 2 → Section 1). Registered in `NIZAM.json`,
  `schema/README.md` (v0.11.0), and `tools/skill.json`; the `ecosystem/README.md` (v0.2.2) module-nav
  `04` row flips Planned → Shipped (six documents now Shipped). `self-test` 60/60.
- **Phase 011 proposal (0–n Project Spectrum, Stage 4: n-Coordination Protocols)** (`NDEBT-035`;
  NIP-0002 Stage 4 — the **final** stage). Authored the Planner artifacts `.agent/product_spec_011.md`
  (status `draft`) and `.agent/feature_list_011.json` (features 080–084, DAG-validated acyclic, root
  `{080}`, est 1330) for the deferred n-repo **coordination** layer: `ecosystem/04_dependency_reconciliation.md`
  (Plan) and `ecosystem/05_release_train_coordination.md` (Promote), with companion schemas, the
  reserved `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates defined, tooling that consumes the phase-010
  ecosystem-level aggregate, and a proving multi-repo pilot. `docs/planning/ROADMAP.md` (v0.27.0) tops
  with a phase-011 proposal banner and carries the release cut (`NDEBT-029`), a real non-scratch pilot,
  and the `06`/`08` Repeat/GA protocols forward as phase-012 candidate scope; `docs/planning/manifest.json`
  gains the phase-011 entry (`pending`/`proposed`). Awaiting activation gate `H-PHASE-011`; `current_phase`
  stays `010-multi-repo` and `run_state` is untouched (a proposal is not an activation).
- **Phase 010 (0–n Project Spectrum, Stage 3: The n-case) complete** (feature 079; `NDEBT-031`).
  The n-case was piloted end-to-end against a scratch **3-member** ecosystem stood up **from
  nothing** by `bootstrap.sh --genesis` at one shared pin, using the fixed tooling (075–078): a
  schema-validated membership registry declared the set, `ecosystem_membership_run.py` iterated the
  `in_scope` repo-roots, and a correct schema-valid aggregate ecosystem-level result was produced
  (`ecosystem_verdict` PASS, `framework_pin_consistent` true, `member_count` 3) — with **no
  hand-applied workaround**. A divergent-pin negative correctly flipped the ecosystem to FAIL with a
  first-class `consistency_findings` entry, proving cross-repo consistency is *enforced*, not silent.
  Evidence under `.agent/evidence/pilot-079/`; `H-CONSUMER-UPGRADE` exercised a fourth time (a
  pre-release/branch pilot, recorded before the genesis bootstraps per NDEBT-018). `NDEBT-031` is
  **resolved**; its Stage-4 coordination residue is carved into `NDEBT-035` (phase-011 candidate)
  and the pilot's per-member clone-cost friction into `NDEBT-034`. The phase-011 candidate scope
  (NIP-0002 Stage 4 `04`/`05` protocols + `NDEBT-029` release + a real, non-scratch multi-repo
  pilot) is refined and **validated** against the pilot evidence — confirmed, not re-ordered.
  `manifest.json` → phase-010 `complete`; a real, non-scratch multi-repo pilot remains the open
  production-maturity criterion.

- **Hermetic n-case e2e coverage** (phase 010 feature 078; `NDEBT-031`; NIP-0002 Stage 3).
  `tools/e2e_bootstrap_test.sh` gains `assert_multirepo`: it stands up a scratch **multi-repo**
  ecosystem — two projects created *from nothing* by `bootstrap.sh --genesis` at one shared
  ephemeral tag (so they share a framework pin) — authors a membership registry over them,
  validates that registry (`validate.sh --target`, C12), runs `ecosystem_membership_run.py`
  across the `in_scope` set, and proves the produced `membership_run.json` is a schema-valid
  ecosystem-level result (`ecosystem_verdict` PASS, `framework_pin_consistent` true,
  `member_count` 2). This exercises the iteration (076) + aggregation (077) at *runtime* across
  genuinely genesis'd repos, generalising the single-member `assert_genesis` to the n-case; the
  single-repo bootstrap/genesis paths stay green (each tool exit captured via an `if` so `set -e`
  never aborts before a diagnostic). `ecosystem_membership_run.py` also gains docstrings on its
  `main`/`die_usage` entry points.

- **`schema/ecosystem_membership_result.schema.json` + cross-repo aggregation & consistency**
  (phase 010 feature 077; `NDEBT-031`; NIP-0002 Stage 3). Mechanizes the multi-repository
  aggregation the shipped tools guarded only as a "future extension": `tools/ecosystem_membership_run.py`
  now rolls the per-member verdicts (feature 076) into one **schema-valid ecosystem-level result**
  — `ecosystem_verdict` (`PASS`/`FAIL`), `framework_pin_consistent`, `member_count`, and the
  per-member `members[]` — and **enforces cross-repo consistency**: it reads each member's
  `.nizam/provenance.json` `resolved_sha` and flags a divergent framework pin as a first-class
  `consistency_finding`, not a silent mismatch. The new companion schema encodes an `allOf`
  invariant (if `framework_pin_consistent` is `false` the `ecosystem_verdict` MUST be `FAIL`),
  registered in `NIZAM.json` + `schema/README.md` (v0.10.0) and validated by `tools/validate.sh`
  **C12** as a sixth ecosystem schema-family (`membership_result`), with positive, missing-verdict,
  and inconsistent-`PASS` fixtures. The membership schema's `schema_version`/`last_updated` metadata
  is hardened (required, pattern-checked), and the tool refuses a registry whose entry name appears
  in more than one scope list (the exactly-one-list invariant, checked in-tool before iteration).
  Hermetic n-case coverage is feature 078.

- **`tools/ecosystem_membership_run.py` — multi-repo iteration** (phase 010 feature 076;
  `NDEBT-031`; NIP-0002 Stage 3). Where the shipped ecosystem tools take a single `--repo-root`,
  this reads the membership registry that sets `n` (feature 075) and runs the Preflight stage once
  per `in_scope` member — resolving each member's repo-root (an explicit `repo_root` entry field,
  else `<repo-roots-base>/<name>`), invoking `ecosystem_preflight.py` unchanged per member, and
  collecting a per-member result index at `<output-dir>/membership_run.json`. The tool's own exit
  is an ecosystem rollup — 0 when every `in_scope` member returned an acceptable verdict
  (`PASS`/`PASS_WITH_EXCEPTIONS`), 1 when any member hard-FAILed or its repo-root was missing, 64
  on usage error — while each member's raw per-member stage exit is preserved per-entry in the
  `membership_run.json` index. The count-1 case is a single-member registry, and
  `ecosystem_preflight.py` is byte-for-byte unchanged (regression-guarded). Cross-repo *aggregation*
  into one schema-valid ecosystem-level result and the common-framework-pin *consistency* check are
  feature 077; standing hermetic multi-repo coverage is feature 078.

- **`schema/ecosystem_membership.schema.json` — the required, validated membership registry**
  (phase 010 feature 075; `NDEBT-031`; NIP-0002 Stage 3). The artifact that sets `n` for the 0–n
  spectrum: a JSON schema validating a consumer's ecosystem-membership registry — the four scope
  lists (`in_scope`/`incubating`/`reference_archive`/`out_of_scope`) as arrays of entries, every
  entry with an identifying `name`, and `out_of_scope` entries recording a `reason`. The
  **exactly-one-list invariant** (no `name` in two lists) is a relational cross-array constraint
  JSON Schema cannot express, so `tools/validate.sh` **C12** enforces it in code (mirroring the
  `ecosystem_baseline` same-repo-revision split), wired at both entry points (full-sweep +
  `--target` router, discriminated by ≥2 of the four scope-list keys) with a positive fixture, a
  schema-invalid negative, and a schema-valid-but-multilist negative caught by the code check.
  `registry/scope_definition_patterns.md` → v0.3.0 is **promoted from a draft pattern to a
  required, schema-backed active artifact**; the schema is registered in `NIZAM.json` and
  `schema/README.md` (v0.9.0). The multi-repo *tooling* that iterates this registry is features
  076–077.

- **Phase 010 proposed, then activated** — `.agent/product_spec_010.md` (authored draft,
  subsequently flipped to `status: active` on activation) and
  `.agent/feature_list_010.json` (features 075–079, DAG-validated acyclic, root {075}, est 1160
  lines) propose **0–n Project Spectrum, Stage 3: The n-case (Multi-Repo Tooling)**, the
  realization of `NIP-0002` Stage 3. Scope: a JSON schema for an ecosystem-membership registry
  promoting `registry/scope_definition_patterns.md` from a draft pattern to a required, validated
  artifact that sets `n` (`NDEBT-031`); multi-repo iteration over the `in_scope` set of repo-roots;
  cross-repo aggregation + a common-framework-pin consistency check; hermetic n-case coverage; then
  a pilot proving the n-case against a scratch multi-repo ecosystem. NIP-0002 Stage 4 (the `04`/`05`
  coordination protocols, activating the reserved `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates),
  the release cut carrying the whole loop (`NDEBT-029`), and a real non-scratch multi-repo pilot are
  carried as phase-011 candidate scope. `docs/planning/ROADMAP.md` (v0.23.0) and
  `docs/planning/manifest.json` recorded the proposal (pending/proposed); the operator then
  authorized activation (gate `H-PHASE-010` SATISFIED, 2026-07-22), recorded in
  `.agent/run_state.json` (event `phase_activated`) before any feature execution, advancing
  `current_phase` to `010-multi-repo` and the phase-010 manifest entry to `in_progress`.

- **Phase 009 (0–n Project Spectrum, Stage 2: Greenfield Genesis) complete** (feature 074;
  `NDEBT-030`). The 0-case was piloted end-to-end against a scratch greenfield project stood up
  **from nothing** by `bootstrap.sh --genesis` using the fixed tools (070–073): genesis created
  the project (`git init` + deterministic scaffold + injected `.nizam/` with `tag` + `resolved_sha`
  provenance), and Preflight returned `PASS_WITH_EXCEPTIONS` with the injected `.nizam/` the single
  expected exception — the same clean outcome ADR-004 gave the count-1 case, with no hand-applied
  workaround. Evidence under `.agent/evidence/pilot-074/`; `H-CONSUMER-UPGRADE` exercised a third
  time (a pre-release/branch pilot). `manifest.json` phase-009 → complete. The phase-010 candidate
  scope (NIP-0002 Stages 3–4) is validated by the pilot (the n-case `NDEBT-031` builds on the
  `incubating` partition this phase populated). A real, non-scratch greenfield pilot and a released
  tag carrying the genesis capability (`NDEBT-029`) remain outstanding.

- **Genesis e2e coverage** (phase 009 feature 073; `NDEBT-030`; NIP-0002 Stage 2).
  `tools/e2e_bootstrap_test.sh` gains `assert_genesis`: a hermetic case proving the 0-case
  end-to-end — `bootstrap.sh --genesis` stands up a new project from nothing, the deterministic
  scaffold (README + CONTEXT + `src/` placeholder) and a `resolved_sha`-pinned provenance are
  present, the committed project passes Preflight as `PASS_WITH_EXCEPTIONS` (the injected `.nizam/`
  the only exception), and a non-empty `--project-root` is refused. The existing
  inject-into-an-existing-repo path stays green (regression-guarded).

- **`incubating → in_scope` promotion — the count-0→1 transition** (phase 009 feature 072;
  `NDEBT-030`; NIP-0002 Stage 2). `registry/scope_definition_patterns.md` → v0.2.0 gains
  **Section 2.3** modelling the scope registry's `incubating` partition as the count-0→1 state: a
  greenfield-genesis project (`bootstrap.sh --genesis`) enters the registry in `incubating` and is
  promoted to `in_scope` once it clears its first clean Preflight/Baseline, as an explicit recorded
  edit that **moves** the entry (preserving the Section 2.1 exactly-one-list invariant); demotion
  is symmetric. Scoped to the single-project count-0→1 case only — promoting the registry to a
  required, validated ecosystem-membership artifact the tools iterate to set `n` (count-1→n) stays
  `NDEBT-031`/phase 010. A `tools/fixtures_self_test.sh` scratch probe asserts the transition shape
  (promotion moves the entry; a two-list "copied-not-moved" entry is detected).

- **`bootstrap.sh --genesis` — greenfield-genesis capability** (phase 009 feature 071;
  `NDEBT-030`; NIP-0002 Stage 2). Mechanizes standing up a *new* project from nothing (the
  0-case): `bootstrap.sh --genesis --project-root DIR [--project-name NAME]` `git init`s an empty
  project root, scaffolds a minimal deterministic skeleton (a `README`, a `CONTEXT.md`
  consumer-inputs stub naming the `ecosystem/00` §6 inputs, and a `src/` source placeholder),
  then reuses the normal clone → inject → verify → provenance install (recording `tag` +
  `resolved_sha`) into `<project-root>/.nizam`. It **refuses a non-empty `--project-root`** (a
  brownfield adoption, not a genesis), and a genesis that fails partway removes a project root it
  created (nothing half-built is left behind). The existing inject-into-an-existing-repo path and
  `--verify-only` are unchanged (regression-guarded). `ecosystem/00_ecosystem_bootstrap.md` →
  v0.6.0: §8's mechanization note now names `bootstrap.sh --genesis`, the §3 spectrum table's
  0-case row rolls to "Covered (Section 8 + `bootstrap.sh --genesis`)", and the "two honest
  limits" prose to "protocol + capability exist but not yet in a released tag" (the `NDEBT-029`
  release gap).

- **Greenfield-genesis protocol** (phase 009 feature 070; `NDEBT-030`; NIP-0002 Stage 2). The
  0-case of the 0–n spectrum — standing up a *new* project from nothing — becomes a first-class
  protocol: `ecosystem/00_ecosystem_bootstrap.md` → v0.5.0 gains **Section 8 (Greenfield
  Genesis)** defining the create-and-scaffold entry path (create the repository → scaffold a
  minimal deterministic skeleton + the consumer-supplied inputs of Section 6 → the normal inject
  + verify of Section 5 recording provenance (Section 7) → register the project `incubating` for
  promotion `incubating → in_scope`, the count-0→1 transition). Establishes "genesis"/"scaffold"
  vocabulary for a new *consumer* project, distinct from the framework's own phase-001 genesis.
  The Section 3 spectrum table's 0-case row and the "two honest limits" prose are corrected from
  "no protocol or tooling yet" to "protocol defined (Section 8); create-and-scaffold capability +
  `incubating→in_scope` transition mechanized in NIP-0002 Stage 2". References renumbered to
  Section 9; Sections 4–7 (and every cross-reference to the Section 7 provenance shape) unchanged.

- **Phase 009 proposed** — `.agent/product_spec_009.md` (status draft) and
  `.agent/feature_list_009.json` (features 070–074, DAG-validated acyclic, root {070}, est 1000
  lines) propose **0–n Project Spectrum, Stage 2: Greenfield Genesis**, the realization of
  `NIP-0002` Stage 2 (the 0-case). Scope: the greenfield-genesis protocol (`NDEBT-030`), a
  create-and-scaffold-from-nothing capability, the `incubating→in_scope` (count-0→1) transition
  on the scope registry, hermetic e2e coverage, then a pilot proving the 0-case. NIP-0002
  Stages 3–4 (n-case multi-repo tooling + membership registry `NDEBT-031`, `04`/`05` protocols)
  and the release cut carrying audit/compare (`NDEBT-029`) are carried as phase-010 candidate
  scope. `docs/planning/ROADMAP.md` and `docs/planning/manifest.json` recorded the proposal
  (pending/proposed). **Subsequently activated 2026-07-22** (gate `H-PHASE-009`, operator
  "Activate phase 009"): `.agent/run_state.json` records `phase_activated`, `current_phase` →
  `009-greenfield-genesis`, `product_spec_009` → active, scope budget reset (phase-008 archived);
  ROADMAP → v0.21.0 (Plan of Record banner) and `operator_gates.md` → v0.8.0 record the
  disposition.
- **`bootstrap.sh` commit-SHA pinning** (phase 008 feature 067; `NDEBT-033`). The Bootstrap
  provenance now records the **resolved commit SHA** the pinned tag pointed at (`resolved_sha`
  in `provenance.json`), making the pin an immutable commit rather than just a tag *name* — a
  tag can be moved on the remote to replay a different payload. `bootstrap.sh --verify-only`
  requires the recorded commit to be present (a payload predating this feature is rejected as
  drift) and, given a caller-supplied `--expected-sha` (resolved out-of-band from the authentic
  tag), rejects a recorded commit that differs — catching a moved tag even when the tag string
  matches. `--verify-only` stays network-free (it never re-resolves the tag). Documented in
  lockstep in `ecosystem/00_ecosystem_bootstrap.md` §7 and `standard/GIP.md` §4; covered by a
  new `tools/e2e_bootstrap_test.sh` `assert_provenance_sha_pin` case (record + correct/wrong
  `--expected-sha`).

- **`ecosystem_preflight.py` baseline provenance-pin anchoring** (phase 008 feature 066;
  ADR-004 decision 2, `NDEBT-028`). A Baseline's `framework_references` now anchors to the
  **injected framework pin** recorded in the governance-root's `provenance.json` (its `tag` /
  `framework_version`) rather than the consumer's own git HEAD, so a real bootstrapped
  consumer's baseline names *which framework* it ran under; `repository_references` continues
  to anchor to the consumer HEAD (*which consumer revision*). When there is no distinct injected
  payload (`--self-fixture` / framework-root layout, or no readable pin) it falls back to the
  historical HEAD-anchored self-referential default, unchanged. Closes phase-007 pilot finding B;
  guarded by a `tools/fixtures_self_test.sh` probe asserting the framework pin (`v0.8.0`) and the
  consumer HEAD are distinct and each correct.
- **`ecosystem_preflight.py` governance-root resolution** (phase 008 feature 065; ADR-004
  decision 1, `NDEBT-027`). The Preflight tool now resolves its required schema references
  against a **governance-root** distinct from the repository root, so a real bootstrapped
  consumer — whose payload lives under `.nizam/` — no longer hard-FAILs on missing references.
  A new `--governance-root` option sets it explicitly; otherwise it is discovered (the injected
  `.nizam/` payload, identified by its `NIZAM.json` + `schema/` markers) under `--repo-root`,
  falling back to the repo-root for the framework-root/`--self-fixture` layout (unchanged). The
  injected payload directory is surfaced as an expected `injected_governance_payload` exception
  rather than a blocking untracked finding, so a clean Preflight against a real consumer is a
  `PASS_WITH_EXCEPTIONS`, not the phase-007 pilot's hard FAIL (finding A). Guarded by new
  `tools/fixtures_self_test.sh` probes (discovery, explicit governance-root, clean framework-root
  regression) and a `tools/e2e_bootstrap_test.sh` assertion that runs the fixed Preflight against
  a genuinely bootstrapped `.nizam/` consumer.

- **Phase 008 proposed** — `.agent/product_spec_008.md` (status draft) and
  `.agent/feature_list_008.json` (features 065–069, DAG-validated acyclic, est 1010 lines)
  propose **0–n Project Spectrum, Stage 1: Consumer-Readiness**, the realization of the
  accepted `NIP-0002` Stage 1. Scope: `ADR-004` governance-root resolution (`NDEBT-027`) +
  provenance-pin anchoring (`NDEBT-028`), bootstrap commit-SHA pinning (`NDEBT-033`), GIP §5.1
  brownfield reconciliation (`NDEBT-032`), then a re-pilot proving the fixed single-project
  loop. NIP-0002 Stages 2–4 (0-case greenfield genesis, n-case multi-repo tooling + membership
  registry, `04`/`05` protocols) are carried as phase-009 candidate scope. **Historical
  proposal-time state:** this entry recorded the proposal at status draft (pending/proposed,
  awaiting gate `H-PHASE-008`); phase 008 was **subsequently activated (H-PHASE-008) and
  completed** — see the "Phase 008 … complete" entry under Changed below for the current
  lifecycle state.
- **`docs/nips/NIP-0002-zero-to-n-project-spectrum.md`** — a framework-capability
  proposal (added at status Proposed; subsequently **Accepted** via gate H-NIP — see
  the Changed entry below) that the Ecosystem Engineering Cycle explicitly span an
  ecosystem of **0 to n projects**: 0 (greenfield genesis — a new project from nothing),
  1 (a single project, greenfield or brownfield), and n (many associated repositories).
  Defines the ecosystem-membership/scope registry (reusing
  `registry/scope_definition_patterns.md`'s `in_scope`/`incubating` partitions) as the
  artifact that sets `n`, refines NIP-0001's "multi-repository" framing to be explicit
  about project count, and lays out a staged, evidence-led realization. On its acceptance
  it became the plan-of-record selection for phase 008. Authored on the operator's
  2026-07-21 design requirement and the phase-007 pilot evidence.
- **`docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`** — the two narrower,
  pilot-proven architecture decisions NIP-0002 spawns (status **Accepted**, implementation
  sequenced into phase 008): the ecosystem tools must (1) resolve a **governance-root** so
  they locate the injected `.nizam/` payload rather than assuming the framework-root
  layout, and (2) anchor a Baseline's `framework_references` to the injected **provenance
  pin** (`.nizam/provenance.json`), not the consumer's HEAD. Records the phase-007
  scratch-consumer pilot findings A and B.
- **`ecosystem/00_ecosystem_bootstrap.md`** — the Bootstrap-stage protocol (phase 007
  feature 060), the lifecycle's entry stage, which had no protocol document until now.
  It wraps (does not restate) `standard/GIP.md` and `bootstrap.sh`: the
  pinned-immutable-tag precondition (floating refs refused), the injected six-module
  payload + `NIZAM.json`, verification and provenance/drift, coexistence with a
  non-empty consumer (GIP §5 rename-and-diff + adoption tiers), the consumer-supplied
  inputs each ecosystem must provide, and the entry condition into Preflight. The
  `ecosystem/README.md` Module Navigation status for `00` is flipped Planned→Shipped
  (five of nine protocols now shipped); the capability is registered in `tools/skill.json`
  and `NIZAM.json`. Authored under the operator-activated phase 007 (gate H-PHASE-007);
  the still-Planned `04/05/06/08` protocols remain deferred until real consumer-pilot
  evidence prioritises them.
- **`tools/compare_ecosystem_baselines.py`** + **`tools/validate_evidence_freshness.py`**
  — the deterministic Compare stage (the two NIP-0001-named tools), making Compare
  tool-driven (previously prose-only). `compare_ecosystem_baselines.py` classifies
  every finding across two audits into the closed five-class taxonomy of
  `ecosystem/07_progress_comparison.md` (`new`/`resolved`/`reopened`/`persisting`/`stale`)
  plus `pre_window_resolved`, and emits a schema-valid `delta.json`
  (`schema/audit_delta.schema.json`). It enforces the protocol's rules mechanically:
  closure-only-with-evidence (§4 — a finding merely absent from the later audit is
  reported UNCLASSIFIABLE, never auto-resolved), stale-evidence non-reuse (§5, via
  the shared freshness rule), the open-findings-only score (§6.1), and the
  first-comparison rule (§3.2 — `reopened` empty without `--prior-delta`).
  `validate_evidence_freshness.py` defines and exposes that freshness rule (evidence
  is current iff re-confirmed at or after the later anchor) as both a library
  (imported by the Compare tool) and a CLI. Both mirror `ecosystem_preflight.py`
  (stdlib-only, documented exit tables, `_UsageErrorArgumentParser`→64) and are
  guarded by standing CLI behavior probes in `tools/fixtures_self_test.sh`.
- **`tools/ecosystem_audit.py`** — a deterministic Audit-stage CLI, making the
  Audit stage tool-driven (previously prose-only; its dogfood artifacts were
  hand-authored). It mechanizes `ecosystem/03_engineering_audit.md`'s **entry
  condition** (§2 — refuses to assemble an audit unless the preflight verdict is
  `PASS` or an operator-approved `PASS_WITH_EXCEPTIONS` and a baseline exists for
  the *same* execution) and **artifact production** (§7 — validates
  auditor-authored findings against `schema/engineering_finding.schema.json`'s
  shape and the no-promotion-beyond-evidence closure rule, then emits the
  canonical `findings.json` top-level array + a rendered `report.md`, evidence
  externalised by path). It makes no engineering judgement — findings come from
  the auditor via `--findings-input`. Stdlib-only, mirroring
  `ecosystem_preflight.py` (documented exit-code table 0/1/2/64,
  `_UsageErrorArgumentParser`→64, single clock read); guarded by standing CLI
  behavior probes in `tools/fixtures_self_test.sh`.
- **`schema/audit_delta.schema.json`** — the fourth core ecosystem-cycle schema,
  validating the progress-comparison delta artifact
  (`ecosystem/07_progress_comparison.md` §7): the two revision/timestamp-anchored
  reference points and the closed five-class transition taxonomy
  (`new`/`resolved`/`reopened`/`persisting`/`stale` — all five buckets present, no
  sixth class admitted). Enforces the protocol's invariants: the
  closure-only-with-evidence rule (§4 — non-empty `closure_evidence` on every
  `resolved` and pre-window-resolved finding), fresh evidence required on
  `persisting` findings (§3), both `open_findings_count` endpoints present, and —
  since JSON Schema cannot express a constraint spanning sibling arrays — a
  code-level check in **both** C12 entry points rejecting a finding id classified
  into more than one transition class (§3 "exactly one class", mirroring the
  NDEBT-023 same-repo-revision check). Wired into `tools/validate.sh` **C12** as
  the fourth ecosystem family at both entry points (full-sweep and `--target`
  router, discriminated by its full `earlier`/`later`/`transitions` shape matched
  ahead of the generic key routes so an additive property cannot divert a valid
  delta), with one positive and three negative fixtures under `tools/fixtures/`,
  registered in `NIZAM.json`,
  indexed in `schema/README.md`, and covered by `tools/fixtures_self_test.sh`.
  Completes the four core ecosystem-cycle schemas
  (baseline / preflight-verdict / engineering-finding / audit-delta).

### Changed

- **Phase 008 (0–n Project Spectrum, Stage 1: Consumer-Readiness) complete** (feature 069).
  The fixed loop (065–068) was re-piloted against a freshly bootstrapped **scratch/throwaway**
  consumer (a loop-mechanics proof, not a real production project) and proved the phase-007
  pilot findings resolved **with no hand-applied workaround**: Preflight =
  `PASS_WITH_EXCEPTIONS` (the injected `.nizam/` is a single expected exception, not a hard
  FAIL — finding A); the baseline `framework_references` names the injected pin while
  `repository_references` names the consumer HEAD (finding B); provenance carries
  `resolved_sha` and `--verify-only --expected-sha` holds (067). Evidence under
  `.agent/evidence/pilot-069/`; `docs/planning/manifest.json` phase-008 → complete;
  `H-CONSUMER-UPGRADE` exercised a second time (a pre-release/branch pilot — a released-tag
  adoption of the fixed framework stays outstanding until the next release). NIP-0002 Stages
  2–4 remain the phase-009 candidate scope, validated by this re-pilot; a real, non-scratch
  consumer pilot remains the open production-maturity criterion.

- **Brownfield coexistence clarified as covered-by-construction** (phase 008 feature 068;
  `NDEBT-032`, resolved-by-design). Investigation showed the premise "mechanize GIP §5.1
  rename-and-diff in `bootstrap.sh`" contradicts **GIP §5.1 point 3**: `bootstrap.sh` injects
  only the `.nizam/` payload and never writes to a consumer's root `CONTEXT.md`/`AGENTS.md`/CI,
  so it *cannot* silently overwrite them — the coexistence safety is guaranteed by construction,
  and reconciling a consumer's own root files against `.nizam/templates/` is inherently a
  consumer-side manual step. `ecosystem/00_ecosystem_bootstrap.md` §3 + §5.1 (v0.4.0) corrected
  from "not yet mechanized" to "covered by construction"; `NDEBT-032` moved to Resolved
  (`docs/planning/DEBT.md` v0.31.0). No `bootstrap.sh` change.

- **`NIP-0002` accepted (gate H-NIP) → phase 008 selected.** The operator accepted
  `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` (status proposed → **accepted**, v0.2.0),
  selecting **phase 008 (The 0–n Project Spectrum)** as its realization — the way NIP-0001's
  acceptance selected phase 005. Selection is not activation: phase 008 still needs its own
  `product_spec_008` + `feature_list_008` + `H-PHASE-008`. Recorded in `.agent/run_state.json`
  (`operator_gate_decision`), `docs/planning/operator_gates.md` (H-NIP second exercise,
  v0.4.0), and `docs/planning/ROADMAP.md` (phase-008 section rolled candidate → authorized,
  v0.14.0).
- **`ecosystem/00_ecosystem_bootstrap.md` → v0.2.0** — made the **0-to-n project
  spectrum** first-class (new Section 3), on the operator's 2026-07-21 design
  requirement: the Bootstrap stage now names and scopes the 0 (greenfield genesis),
  1-greenfield, 1-brownfield, and n (multi-repository) cases and states honestly which
  are mechanized today versus delegated to the GIP tiers, the scope-membership registry,
  or the deferred `04`/`05` coordination protocols. Cross-references NIP-0002 (the
  capability framing) and ADR-004 (the single-project consumer-readiness fixes).
- **`docs/planning/DEBT.md` → v0.30.0** — recorded the phase-007 scratch-consumer pilot
  friction and the 0-to-n gaps as `NDEBT-027`…`NDEBT-032`: preflight governance-root
  assumption (A), baseline framework-pin mis-anchoring (B), audit/compare not yet in a
  released tag (C), the absent 0-case (D), single-`--repo-root` tools versus multi-repo
  prose (E), and `bootstrap.sh` lacking GIP §5.1 brownfield reconciliation (F). Each
  cross-references ADR-004 or NIP-0002 and is sequenced into phase 008. Plus `NDEBT-033`
  (from the PR #42 review): bootstrap provenance pins the tag name but not its resolved
  commit SHA — hardening deferred to phase 008.

### Fixed

- **Doc-truth in the ecosystem protocols** — retired the stale "schema … not yet
  present at the time this protocol was authored" parentheticals in
  `ecosystem/01_clean_state_preflight.md`, `ecosystem/02_evidence_baseline.md`, and
  `ecosystem/03_engineering_audit.md` (their schemas shipped in features 037–039 and
  have been present under `schema/` since), and updated
  `ecosystem/07_progress_comparison.md` from its "optional / deferrable / not yet
  present" bare-filename reference to the now-present, directory-qualified
  `schema/audit_delta.schema.json`. No protocol semantics changed.

## [0.8.0] - 2026-07-20

**Minor release** (`methodology/06_release_train.md` §3.2): phase 006
(Enforcement Closure & Hardening, features 049–059) adds new *optional*
capability — validator checks C13/C14/C15, new `tools/verify_lib.sh`
primitives, additional `tools/ecosystem_preflight.py` options, an additive
`enforcement:` frontmatter field (rides `additionalProperties: true`), and
documentation-honesty markings — without invalidating any consumer content
that previously validated. One schema narrowing is disclosed per §4 and
classified minor-not-breaking: `schema/preflight_verdict.schema.json` now
requires `blocking_findings` when `verdict` is `FAIL` (feature 056), but a
preflight verdict is tool output regenerated each run by the same-release
`tools/ecosystem_preflight.py`, not durable consumer-authored content, so
upgrading invalidates no consumer document.

### Added

- **Constitutional-layer mechanize-or-descope decision** (phase 006 feature 058,
  gate **H-CONSTITUTIONAL**, Track 3): the operator's per-document decision on the
  v0.4.0 NMF-hybrid constitutional policy surface, so every consumer first-contact
  surface is honest about what the framework enforces. **Mechanized (2):**
  `standard/provenance_policy.md`'s SHA-pinned-Actions rule is now verified by
  `tools/validate.sh` check **C14** (a new `vlib_workflows_sha_pinned` primitive over
  the workflows directory), and `standard/capability_profiles.md`'s five-profile ↔
  five-AGF-role correspondence by check **C15** (a new `vlib_profiles_cover_roles`
  primitive) — the default sweep is now 15 checks, both dogfooded green.
  **Descoped consumer-aspirational (7):** `standard/ci_gates.md`,
  `methodology/05_eval_and_trace.md`, `methodology/07_eval_gated_promotion.md`,
  `standard/mcp_policy.md`, `standard/permission_classes.md`,
  `standard/failure_modes.md`, and `standard/cross_repo_governance.md` gain an
  `enforcement: consumer-aspirational` frontmatter field and a body banner, and
  `tools/SKILL.md`'s cross-repo directive is softened to match. `docs/guide/index.html`
  is refreshed to name the constitutional documents and reflect each decision;
  ROADMAP Track 3 is marked resolved. The two mechanized docs are marked
  `enforcement: partially-enforced`.
- **Preflight + ecosystem-schema hardening bundle** (phase 006 feature 056,
  resolving **NDEBT-021, -023, -024, -017, -018**): the deferred
  `tools/ecosystem_preflight.py` hardening backlog, each item carrying a
  discriminating executed probe (the CLI is not CI-covered, so the
  untracked-not-tolerated and tolerate-polarity probes are now standing guards in
  `tools/fixtures_self_test.sh`). **NDEBT-021** — NUL-delimited
  `git status --porcelain=v1 -z` parsing that preserves the directory-prefix
  tolerate semantics the 043/044 approved runs depend on; readable-regular-file
  reference checks (`os.path.isfile` + `os.access`, rejecting a directory at the
  path) and an unresolved-HEAD blocking finding; `--repo-root` defaulting to
  `None` so an explicit `.` is honored under `--self-fixture`; and an output-dir
  pre-clean so a reused directory never mixes contradictory verdicts.
  **NDEBT-018** — an additive `--tolerate-untracked-prefix` option (tolerate a
  whole in-flight artifact directory by one declared prefix, preserving the exact
  043/044 dir-collapse semantics) and `ecosystem/01_clean_state_preflight.md`
  (0.1.2) §4.1 codifying that an orchestrator gate-decision tracked-state write
  must be committed before the gated preflight invocation. **NDEBT-017** — a
  pluggable, offline `--ci-run-file` that anchors `ci_references` to a
  caller-resolved CI run (no in-tool network call). **NDEBT-023** — same-repo
  revision-consistency mechanized in the capture tool and validator `C12` (a new
  schema-valid but rule-violating
  `ecosystem_baseline_neg_inconsistent_revisions.json` fixture is caught by the
  code-level check). **NDEBT-024** — a `blocking_findings` array required when
  `verdict` is `FAIL` in `schema/preflight_verdict.schema.json`, with
  `preflight_verdict_fail.json` rebuilt on it. The five documented exit codes
  (0/1/2/3/64) are unchanged; sweeps 13/13 and 11/11, self-test 47/47, e2e green.
- **Progress-comparison taxonomy completion** (phase 006 feature 057, resolving
  **NDEBT-022**): `ecosystem/07_progress_comparison.md` (0.2.0) completes its
  finding-state taxonomy so a real corpus classifies without workarounds.
  Section 3 adds the fifth transition class **`persisting`** (present on both
  sides with freshly re-confirmed, current evidence — the exact opposite of
  `stale`), a **pre-window-resolved** recording rule (§3.1: a finding resolved
  before the earlier input's reference point is recorded but is not a
  cross-execution transition and is excluded from the open-findings score), and
  a **first-comparison** rule (§3.2: an empty `reopened` bucket on a first
  comparison is correct). Section 6.1 fixes the score-count semantics — the
  open-findings score counts `open` findings only, never resolved or
  pre-window-resolved recorded findings. The audit-044 corpus now classifies
  directly (015 persisting, 002 pre-window-resolved, 016 stale, 017/018 new;
  open-only 2→4); the committed `audit-2026-07-17-cba6422` artifacts stay
  immutable.
- **Work-packet template ↔ schema alignment** (phase 006 feature 054, resolving
  **NDEBT-011**): `templates/work-packet.template.json` now validates end-to-end
  against `schema/work-packet.schema.json` — the three enum/integer dispatch
  fields that held the `{{TIER}}`/`{{BLAST_RADIUS}}`/`{{MERGE_ORDER}}`
  placeholders are omitted from the starter template (they cannot be
  schema-valid, and shipping literal defaults would let a copied packet silently
  carry a wrong tier / blast-radius / merge-order) and are documented in the
  schema for consumers that need cross-repo dispatch, so the schema's own
  `description` claim to validate the template is now true. The parse-validity-only caveat is
  retired from `templates/README.md` (0.2.2) and `schema/README.md` (0.7.1), and
  a `tools/fixtures_self_test.sh` guard mechanically asserts the conformance in
  CI (`jsonschema.validate` of the template against its schema) so it cannot
  silently drift back to non-conformance.
- **Enumeration/bare-ref recurrence guards** (phase 006 feature 055, resolving
  **NDEBT-005**): two vetted `tools/verify_lib.sh` primitives — the library's
  seventh and eighth — mechanize the two NDEBT-003 defect classes F-027 had
  fixed by hand, both sourced from the single canonical index `NIZAM.json`
  rather than re-derived lists. `vlib_enumeration_complete` asserts the
  disk→index (completeness) direction `C4` does not cover: every on-disk
  governed document under a module directory must be enumerated in that
  module's `key_documents`. `vlib_bare_ref_resolves` flags a bare,
  non-`/`-qualified `NN_name.md` reference whose basename matches no
  `key_document` — the shape `C9` and `C10` both miss. Both ride the F-052
  self-test surface with seeded-omission and seeded-bare-stale-reference
  fixtures plus a real-tree recurrence sweep (enumeration over all four
  documentation modules; bare-ref over `methodology/` + `standard/`, the
  stable modules where the defect occurred, excluding the still-evolving
  `ecosystem/` and quoting registers to avoid false positives).
  `fixtures_self_test` now accounts for 46 fixtures (was 43).
- `tools/validate.sh` check **C13** (skill-index integrity; phase 006 feature
  049, resolving NDEBT-007): `tools/skill.json` is JSON-parsed and its
  `entry_point` plus every `capabilities[].module` pointer must resolve to an
  existing file — the enforcement hole that let the `release_train` capability
  ship a retired module pointer from v0.4.0 through v0.5.3 undetected is
  closed. Runs in the full sweep (SUMMARY migrates `12 passed` → `13 passed`)
  and in `--payload` mode (`10 passed` → `11 passed`), where pointers into the
  non-injected directories are skipped pending the F-051 payload-contract
  decision. Negative fixture
  `tools/fixtures/skill_index_neg_dangling_module.json` reproduces the defect
  class; `tools/README.md` (0.4.0) and the `NIZAM.json` validator capability
  summary document the C1–C13 set.
- **Fixtures self-test** `tools/fixtures_self_test.sh` and a `fixtures_self_test`
  CI job (phase 006 feature 052, resolving **NDEBT-009**): every shipped
  `tools/fixtures/` fixture is run through its targeted surface —
  `validate.sh --target` for check-level fixtures, the `verify_lib.sh`
  primitives for primitive-level ones, and a `tools/skill.json` substitution
  for the C13 negative fixture — asserting the **specific** verdict (not a
  bare non-zero exit, which most `.md` fixtures already return from incidental
  C1/C2 failures), with a completeness guard that fails on any unaccounted
  fixture. Closes the dormancy gap where a check regressing to a vacuous pass
  would not have been caught.
- `tools/validate.sh` **C12 `--target` routing** (feature 052, resolving
  **NDEBT-015**): a `--target` invocation against an `ecosystem_baseline`,
  `preflight_verdict`, or `engineering_finding` fixture now content-routes to
  its shipped schema and emits a discriminating `[C12]` verdict, instead of
  misrouting to C4/C11 and failing regardless of polarity.
- `tools/validate.sh` **C12 naming-conformance guard** (feature 052, resolving
  **NDEBT-016**): the fixture-polarity classifier is case-insensitive and a
  basename carrying a `neg`/`invalid` look-alike that is not the canonical
  delimited-lowercase token (uppercase `_NEG_`, full-word `_negative_`) is a
  named FAIL, so the classifier cannot be gamed by a look-alike name.
- **Orchestrator role + operational-rule codification** (phase 006 feature
  053): `standard/AGF.md` (0.2.0) now defines the **Orchestrator** in Section 2
  — the coordination/state-ownership role that sequences the four execution
  roles, parses each gate verdict, owns `run_state.json`'s run-position and
  coordination fields (Section 5 rule 4), and enforces the circuit breaker —
  resolving **NDEBT-010**, the load-bearing-but-undefined role that
  `capability_profiles.md`, `permission_classes.md`, `mcp_policy.md`, and
  `methodology/06_release_train.md` (0.3.1) all already referenced.
  `methodology/02_adversarial_tdd.md` (0.4.0) gains Section 10 anti-pattern (e)
  (explicit exit-code assertion — **NDEBT-019**), Section 11 Probe Isolation
  (**NDEBT-013/020**), and Section 12, the five-class verification-authoring
  defect catalogue (**NDEBT-014**). `tools/verify_lib.sh` gains a sixth vetted
  primitive, `vlib_word_present` (whole-word match, fixing the
  substring-on-containing-word false-pass), fixture-tested via
  `tools/fixtures_self_test.sh`. Three stale "four agent roles" descriptions of
  AGF were corrected in-scope (`standard/README.md`,
  `methodology/01_execution.md`, `methodology/00_planning.md`).

### Changed

- **Bootstrap payload enlarged to six directories** (phase 006 feature 051,
  the H-PAYLOAD-CONTRACT decision, resolving **NDEBT-008**): `bootstrap.sh`
  now injects `methodology/` and `ecosystem/` alongside `standard/`,
  `templates/`, `schema/`, and `tools/` (plus `NIZAM.json`). Consumer
  `.nizam/` installs previously omitted these two directories, so the many
  `tools/skill.json` and `tools/SKILL.md` cross-references into `methodology/`
  (and the `ecosystem/` references added in feature 040) dangled in a real
  install. `standard/GIP.md` (0.4.0 — Sections 1, 2, 2.1, 4, 5.1) and
  `CONTEXT.md` (0.7.0) now name the six-directory payload authoritatively; the
  C4/C9/C13 `--payload` carve-outs for `methodology/`+`ecosystem/` are retired
  (those paths are now required to resolve), leaving only the still-non-injected
  `registry/` and `docs/` carved out; `tools/e2e_bootstrap_test.sh` asserts the
  enlarged payload. Verified load-bearing: a payload missing the two dirs now
  FAILs both `validate.sh --payload` and `bootstrap.sh --verify-only`. This
  enlarges what consumers receive on their next re-bootstrap; `registry/` and
  `docs/` remain framework-envelope and are still never injected.

### Fixed

- `tools/validate.sh` self-description drift left by feature 051 (found and
  corrected in-scope during feature 052): the C4/C13 `--help` text, the C13
  function comment, and the C13 payload-mode PASS message still named
  `methodology/`+`ecosystem/` among the payload-skipped directories and said
  the carve-out was "pending the F-051 payload-contract decision" — but
  feature 051 already made those two directories injected/required, narrowing
  the skip set to `registry/`+`docs/`. The code (`skipped_dirs`,
  `SKIPPED_DIR_PREFIXES`, the C9 allow-list) was already correct; only the
  human-readable descriptions lagged. An NDEBT-005-class enumeration-
  completeness miss.
- `tools/validate.sh` C4 payload mode: `ecosystem` joined the non-injected
  carve-out set (`methodology`, `registry`, `docs`). NIZAM.json has indexed
  `ecosystem/` paths since feature 040, but `bootstrap.sh` does not inject the
  directory, so a real consumer v0.7.0 payload would have false-failed C4 —
  masked in the framework's own payload-mode runs because the directory exists
  on disk here. Registered as an NDEBT-008 broadening; the carve-out narrows
  again when F-051 decides the payload contract.
- `tools/validate.sh` C4 + C13 path hygiene (feature-049 review round, PR
  #28): indexed paths and skill-module pointers are normalized before the
  payload carve-out test, so a traversal spelling
  (`ecosystem/../tools/x.md`) can no longer ride a non-injected-dir skip;
  absolute paths and paths escaping the repo root now FAIL in every mode
  instead of matching host files. The repo-containment check runs on every
  present path *before* the carve-out, so a symlinked carve-out path
  (`ecosystem/evil -> /etc`) is rejected in payload mode too rather than
  riding the skip; genuinely-absent carve-out paths stay allowed. C13 also
  never carves out the `entry_point` in payload mode — the skill's single
  entry document must resolve in any payload, so a mis-declared
  `entry_point` under a non-injected prefix FAILs rather than ride the
  capability-module carve-out. The `--help` payload descriptions now name
  the full carve-out set including `ecosystem/`.
- `tools/validate.sh --payload` is now **CWD-independent** (phase 006 feature
  050, resolving **NDEBT-012** / the first external-consumer bug report,
  issue #18): in `--payload` mode the validator anchors to its own payload
  root (the parent of its `tools/` directory), so
  `bash .nizam/tools/validate.sh --payload` run from a consumer repository
  root now behaves identically to `cd .nizam && bash tools/validate.sh
  --payload` instead of failing to find the payload's own files. Default and
  `--target` modes stay CWD-anchored (unchanged documented contract).
- `tools/validate.sh` check **C9** payload carve-out (feature 050, resolving
  **NDEBT-004**): in `--payload` mode a directory-qualified cross-reference is
  only required to resolve if its target is under an injected-payload prefix
  (`standard/`, `templates/`, `schema/`, `tools/`); references into
  non-injected framework-envelope paths (`methodology/`, `ecosystem/`,
  `registry/`, `docs/`, `.agent/`, `.github/`, …) are expected-absent in a
  consumer subset and are skipped — the C9 analog of C4's existing carve-out.
  A real bootstrapped payload previously false-failed C9 on 26 such
  references even from the payload root; both `--payload` invocation forms now
  pass green. The default full sweep applies no carve-out, so stale
  non-injected references are still caught. `tools/e2e_bootstrap_test.sh`
  gains a from-consumer-repo-root `--payload` assertion so the regression
  class stays closed. (The NDEBT-004 fix is landed and verified; resolving it
  *within* feature 050 rather than its own feature is an operator scope call
  disclosed as pending ratification — see the PR #29 description — and
  finalized on merge.)

## [0.7.0] - 2026-07-17

### Added

- `.github/workflows/release.yml`: mechanizes GitHub Release publication.
  On every `vMAJOR.MINOR.PATCH` tag push (or manual dispatch for a
  pre-existing tag), it extracts the tag's own `## [X.Y.Z]` CHANGELOG
  section (read at the tag, not at `main`), titles the Release from the
  annotated tag's subject line, and creates-or-updates the Release page
  idempotently. A tag whose at-tag CHANGELOG carries no matching section
  fails loudly, enforcing `methodology/06_release_train.md` Section 2's
  changelog discipline at publication time — the failure class of the
  v0.5.2/v0.5.3 cycle (tagged without CHANGELOG entries) and of v0.6.0
  (tagged without a Release page). The logic is inline in the workflow, not
  under `tools/`, because `tools/` is bootstrap-injected consumer payload
  and Release publication is a framework-envelope concern.
- `ecosystem/README.md` plus 4 new protocol documents
  (`ecosystem/01_clean_state_preflight.md`, `ecosystem/02_evidence_baseline.md`,
  `ecosystem/03_engineering_audit.md`, `ecosystem/07_progress_comparison.md`):
  the reusable, schema-governed Ecosystem Engineering Cycle (handover
  NIP-0001), extending Nizam's repository-local contract-first loop to
  ecosystem scale. Framework-side only this phase; consumer adoption is
  deferred to a successor programme phase.
- `schema/preflight_verdict.schema.json`, `schema/ecosystem_baseline.schema.json`,
  `schema/engineering_finding.schema.json`, plus matching positive/negative
  `tools/fixtures/` fixtures for all three schema families.
- `tools/ecosystem_preflight.py`: a deterministic, self-fixture-capable CLI
  implementing the clean-state preflight protocol (three-verdict vocabulary,
  operator-exception rule).
- `tools/validate.sh` check **C12** (ecosystem schema-family fixture
  validation). The default sweep's `SUMMARY` migrates from `11 passed, 0
  failed` to `12 passed, 0 failed`; `--payload` mode is unaffected (still
  `10 passed, 0 failed`), since C12 is deliberately full-sweep-only.
- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`: the accepted NIP
  recording the Ecosystem Engineering Cycle's scope and rationale.
- The framework's first self-dogfood evidence cycle: two gated preflight +
  baseline runs (`.agent/reconciliation/dogfood-2026-07-17-28c8253/`,
  `.agent/reconciliation/dogfood-2026-07-17-6d7a47b/`) and a first
  engineering audit + progress comparison
  (`.agent/audits/audit-2026-07-17-cba6422/`), registering NDEBT-013 through
  NDEBT-018.

### Changed

- `docs/planning/ROADMAP.md` (0.2.0): Current Position refreshed after the
  2026-07-15 release-readiness audit — the v0.6.0 annotated tag was cut and
  pushed 2026-07-15 at the release commit (955c1d7), executing Track 1's first
  human gate; the residual v0.6.0 GitHub Release publication and the GitHub
  Pages gate remain recorded, and the phase-005 candidate scope gains the
  NDEBT-012 payload-validator fix.
- `docs/planning/DEBT.md` (0.8.0): registered NDEBT-012 — `tools/validate.sh
  --payload` is CWD-sensitive and fails when invoked from a consumer
  repository root instead of inside `.nizam/` (GitHub issue #18, the first
  bug report from a real external consumer; corroborates NDEBT-004 and
  NDEBT-008's consumer-context concerns).
- Release metadata: `NIZAM.json` `framework.version` and the
  `docs/guide/index.html` version anchors bumped to `0.7.0`; the `README.md`
  quickstart re-pinned to `v0.7.0`; `CONTEXT.md` bumped to 0.6.0 for the
  release state.
- `NIZAM.json`: the `nizam-compliance-validator` capability summary now
  describes the full C1-C12 check set — it had continued to enumerate only
  the eleven v0.6.0-era check domains after C12 (ecosystem schema-family
  fixture validation) shipped in this release.

## [0.6.0] - 2026-07-13

### Added

- `tools/verify_lib.sh`: a vetted, sourced verification-helper library exposing
  five fixture-tested primitives contracts and `validate.sh` checks compose
  instead of re-inventing — section-scoped grep, the untracked-aware scope
  guard, strict-version-increase-vs-HEAD, punctuation-stripped path
  resolution, and the generalized stale-payload-enumeration guard. A matching
  verification-authoring standard section was added to
  `methodology/02_adversarial_tdd.md`, codifying the anti-patterns a
  contract's verification suite must not use (whole-file vacuous greps,
  `git diff HEAD` scope guards blind to new untracked files, bare-adjacency
  checks, and content-free substring checks).
- `tools/validate.sh` checks **C9** (repo-wide path-resolution), **C10**
  (single-source-of-truth consistency: payload-set enumeration, bootstrapped-
  consumer discovery order, framework-version anchor), and **C11** (dogfood
  schema validation of `.agent/qa/*.json`, `.agent/contracts/*.json`, and
  `.agent/run_state.json` against the shipped schemas, enforce-if-present /
  skip-if-absent). The full sweep's `SUMMARY` migrated from `8 passed, 0
  failed` to `11 passed, 0 failed`.
- `schema/contract_review.schema.json`, describing the pre-code
  contract-review artifact shape, and a reconciled `schema/qa_verdict.schema.json`
  (`anyOf` union of the legacy and evolved QA-verdict shapes) so every
  historical `.agent/qa/*.json` validates without edits; `schema/contract.schema.json`
  now documents `amendments[]` as an explicit property. Resolves NDEBT-002.
- `tools/e2e_bootstrap_test.sh`: a hermetic (network-free), dual-mode
  end-to-end harness that exercises the real `bootstrap.sh` inject → verify
  adoption path via a local `file://` clone and an ephemeral annotated tag —
  asserting the injected payload, `NIZAM.json` index integrity, the
  documented `.nizam/tools/skill.json` discovery path, and a `--verify-only`
  pass — plus a `--self-test-negative` mode proving the discovery-path guard
  is load-bearing. A second CI job in `.github/workflows/compliance.yml`
  (`e2e_bootstrap`, alongside the existing `validate` job) runs it on every
  PR and push to `main`. `bootstrap.sh` itself is unmodified.
- `docs/planning/ROADMAP.md`: a forward roadmap naming the outstanding human
  gates (the v0.6.0 release cut, GitHub Pages publishing for `docs/guide/`),
  the candidate scope for a phase 005 sourced from the open debt register,
  and the mechanize-or-descope decision required for the constitutional
  policy surface shipped in v0.4.0.

### Fixed

- `tools/skill.json`: the `release_train` capability's `module` pointer now
  names `methodology/06_release_train.md`; it had pointed at
  `methodology/05_release_train.md`, a path retired by the v0.4.0 methodology
  renumbering that inserted `05_eval_and_trace.md`. The identical stale
  pointer in `tools/interface.md` was fixed during the v0.5.x cycle, but
  `skill.json` — whose content no validator check sweeps (C4 parses only
  `NIZAM.json`; C9 sweeps only `.md`/`.html` bodies) — was missed and shipped
  broken from v0.4.0 through v0.5.3. `skill.json` `version` bumped
  0.1.0 → 0.1.1; the enforcement gap is registered as NDEBT-007.
- `standard/AGF.md` (0.1.1): Section 6's circuit-breaker cross-reference no
  longer calls `methodology/03_circuit_breaker.md` "forthcoming" (it shipped
  at genesis), and the Section 4 verdict rule's dropped word is restored
  ("a single non-empty entry in any of the three arrays blocks advancement").
- `standard/GIP.md` (0.3.1): Section 2.1's verification minimum no longer
  hard-codes "the four `standard/` documents" — the module has shipped eleven
  governance documents since v0.4.0.
- `registry/README.md` (0.2.1): removed the stale "13 capability entries"
  hard count (the root index now carries 24 capability entries).
- `schema/README.md` (0.4.0): added the missing `work-packet.schema.json` row
  to the Schemas table — the schema shipped in v0.5.0 but was never indexed
  in its own module README.
- `NIZAM.json`: the `schema` module's `key_documents` list now includes
  `schema/contract_review.schema.json`, which was present in the top-level
  `schemas[]` array but missing from the module index.
- `CONTEXT.md` (0.4.1) and root `README.md`: the `standard/` module
  descriptions now name the constitutional policy documents shipped since
  v0.4.0 instead of only the four genesis-era core documents; the README
  quickstart is re-pinned from v0.5.1 to v0.5.3 (the latest released tag).
- `docs/planning/manifest.json`: phase `004-durable-enforcement` status
  corrected from the stale `in_progress` to `complete` — run_state recorded
  `phase_complete` on 2026-07-10 and the phase PR merged — with a lifecycle
  note recording the outstanding v0.6.0 human release gate.
- `docs/planning/DEBT.md` (0.7.0): NDEBT-003 moved to Resolved (both of its
  defects were fixed by F-027 and verified in-tree, but the register was
  never updated); new entries NDEBT-007 through NDEBT-011 registered from
  the 2026-07-12 external project review.
- `NIZAM.json` `framework.version` and the `docs/guide/index.html` version
  anchors (meta `framework-version` and the footer version span) reconciled
  from the stale `0.5.1` to `0.5.3`: the v0.5.2 and v0.5.3 hotfix releases
  were tagged without bumping the root capability index, leaving agents that
  discover the framework through `NIZAM.json` a conflicting release identity
  (PR #16 review finding).

### Changed

- Release metadata: `NIZAM.json` `framework.version` and the
  `docs/guide/index.html` version anchors bumped to `0.6.0`; the `README.md`
  quickstart re-pinned to `v0.6.0`; `CONTEXT.md` bumped to 0.5.0 for the
  release state.
- `NIZAM.json`: the `nizam-compliance-validator` capability summary now
  describes the full C1–C11 check set — it had continued to enumerate only
  the eight v0.2.0-era check domains after C9 (repo-wide path resolution),
  C10 (single-source-of-truth consistency), and C11 (dogfood schema
  validation) shipped in this release.

## [0.5.3] - 2026-07-09

### Fixed

- Stripped trailing whitespace from `standard/failure_modes.md` in the
  governance payload, which caused CI failures on consumer repos.
  *(Backfilled 2026-07-12: v0.5.3 was tagged and released on GitHub without a
  CHANGELOG entry, violating `methodology/06_release_train.md`'s changelog
  discipline; this entry restores the record. See the v0.5.3 GitHub Release.)*

## [0.5.2] - 2026-07-09

### Fixed

- `tools/validate.sh` C8 (`check_c8_version_changelog`) path resolution in
  payload mode: `git show HEAD:<path>` now prepends
  `git rev-parse --show-prefix`, so in payload mode (CWD = `.nizam/`) it
  correctly resolves `.nizam/`-relative paths instead of repo-root paths,
  eliminating false "version downgrade" failures on consumer repos that have
  their own `tools/` or `templates/` directories at the repo root. (PR #14)
  *(Backfilled 2026-07-12: v0.5.2 was tagged and released on GitHub without a
  CHANGELOG entry; this entry restores the record. See the v0.5.2 GitHub
  Release.)*

## [0.5.1] - 2026-07-09

### Added

- `tools/validate.sh --payload` mode: validates the `bootstrap.sh`-injected
  consumer payload subset (`standard/`, `templates/`, `schema/`, `tools/`,
  `NIZAM.json`) without requiring framework-envelope files (`CONTEXT.md`,
  `README.md`, `CHANGELOG.md`, `bootstrap.sh`, `methodology/`, `registry/`,
  `docs/`). C4 skips registry schema validation when absent and filters
  non-injected dir paths; C5 sweeps only existing files; C6 is skipped;
  C7 checks only injected module READMEs. Default and `--target` modes are
  unchanged (8/8 pass, no regression). (PR #12)

### Fixed

- ADR-001 follow-up note documenting the `--payload` validation path.

## [0.5.0] - 2026-07-09

### Added

- `schema/work-packet.schema.json`: JSON Schema for the work-packet artifact
  (`templates/work-packet.template.json`). Requires the historical minimal set
  (`id`, `objective`, `scope`, `acceptance`, `evidence`, `non_goals`) so every
  pre-existing packet stays valid, and adds optional linking/dispatch fields an
  execution ledger (for example a Kanban dispatcher) needs to bind a packet to a
  plan of record: `repo`, `tier` (seven-tier model of
  `standard/cross_repo_governance.md`), `blast_radius` (local/cluster/ecosystem),
  `concurrency_lane`, `dependency_edges` (`depends_on`/`consumed_by`) and
  `merge_order` (upstream-before-downstream ordering of
  `methodology/08_cross_repo_dependency_gate.md`), and the foreign keys
  `contract_id`, `phase_id`, `feature_id`, and `train_id`. `templates/work-packet.template.json`
  gains the matching optional placeholder fields and corrects the `merge_order`
  placeholder to an unquoted integer (`0`) matching the integer schema. `NIZAM.json`
  indexes the new schema.

### Fixed

- Compliance hotfix restoring `tools/validate.sh` to green (the v0.4.0/v0.4.1
  releases had shipped a tree failing the framework's own validator): removed
  vendor-specific org branding — a stray org name in
  `standard/cross_repo_governance.md` (C5 branding sweep) and the `$id` URLs of
  `schema/debt.schema.json` and `schema/capability_profile.schema.json`, now in
  the vendor-neutral `urn:nizam-framework:schema:*` form matching the other
  shipped schemas; corrected `methodology/06_release_train.md`'s
  `authoritative_source` to its own path after the `05` -> `06` rename (C2 format);
  and synced `docs/guide/index.html`'s embedded framework-version anchor to `0.4.1`
  to match `NIZAM.json` `framework.version`.
- Schema hardening: clamped `qa_verdict.schema.json` `exit_code` to `0..255`
  (POSIX range); enforced `minimum: 0` on `run_state.schema.json` per-feature
  line count fields; enforced `maximum: 3` on circuit breaker `limit` (aligning
  with the documented mandatory 3-strike rule).
- Documentation drift: updated `README.md` quickstart tag from `v0.1.0` to
  `v0.5.0`; added `docs/` to the `README.md` Modules table and `CONTEXT.md`
  Module Map; bumped `CONTEXT.md` version from `0.2.0` to `0.3.0`; bumped
  `tools/SKILL.md` version from `0.1.0` to `0.2.0` to reflect the Cross-Repo
  Intelligence, Eval-Gated Promotion, and Cross-Repo Dependency Gate additions
  that landed in `v0.4.0` but were not versioned; synced `docs/guide/index.html`
  and `NIZAM.json` `framework.version` to `0.5.0`.

## [0.4.1] - 2026-07-08

### Changed

- **Tool-agnostic automated-review gate**: Renamed the `MERGE_READY` formula
  factor `CODERABBIT_CLEAN` to `AUTOMATED_REVIEW_CLEAN` in `standard/ci_gates.md`
  and generalized the corresponding gate description. The framework now MANDATES
  a blocking, deny-by-default automated code-review gate (a conformant tool must
  have run on the latest relevant SHA with no unresolved blocking findings) but
  no longer dictates the specific tool — the consumer declares it (e.g. in its
  `NIZAM.json` / governance config). `methodology/05_eval_and_trace.md` L8 is
  likewise generalized from a CodeRabbit-specific reference to a tool-agnostic
  automated code-review gate. The attributed 10-gate enforcement table is unchanged.

## [0.4.0] - 2026-07-08

### Added

- **Nizam Manifesto Framework (NMF) Hybrid**: Integrated the constitutional breadth of the Vibe Coding Manifesto into the installable, schema-driven Nizam Framework format (ADR-003).
- `standard/capability_profiles.md` and `schema/capability_profile.schema.json`: Capability Profile Model binding roles to task types and safety classes, not specific models.
- `standard/ci_gates.md`: The mandatory 10-gate `MERGE_READY` formula.
- `standard/mcp_policy.md`: MCP Security Policy for namespace rules and surface allocations.
- `standard/failure_modes.md`: The seven canonical failure modes and detection/response protocols.
- `standard/provenance_policy.md`: Supply-Chain Provenance Policy for artifact attestations and audit envelopes.
- `standard/permission_classes.md`: Permission and Sandbox Policy defining deny-by-default RBAC and Kubernetes allocations.
- `standard/cross_repo_governance.md`: Cross-Repository Intelligence rules, executable truth layer, and seven-tier architecture model.
- `methodology/05_eval_and_trace.md`: Eval and Trace Infrastructure defining the verification hierarchy and role-specific eval suites.
- `methodology/07_eval_gated_promotion.md`: Eval-Gated Model Promotion Protocol treating model changes as code changes.
- `methodology/08_cross_repo_dependency_gate.md`: Cross-Repo Dependency Gate requiring upstream contract delta approval before downstream execution.
- `templates/DEBT.md` and `schema/debt.schema.json`: Circuit Breaker Debt Log for recording circuit breaker trips and architectural debt.

### Changed

- Renamed `methodology/05_release_train.md` to `methodology/06_release_train.md` to maintain ordering.
- Updated `NIZAM.json` to index all new capabilities, modules, schemas, and templates.
- Updated `standard/README.md` and `methodology/README.md` to reflect new protocol documents.
- Updated `tools/SKILL.md` to mandate Cross-Repo Intelligence queries before action, and to acknowledge Eval-Gated Promotion and Cross-Repo Dependency Gates.

## [0.3.0] - 2026-07-08

### Added

- `docs/guide/index.html`, a self-contained, dependency-free HTML user guide
  covering discovery, adoption, the contract-first execution loop, and the
  circuit breaker; and `docs/architecture/ADR-002-html-user-guide.md`,
  recording the decision to ship it. `NIZAM.json` gains a `docs` module
  indexing both Architecture Decision Records (`ADR-001`, `ADR-002`) and the
  guide.
- `LICENSE`, the MIT license (copyright held by "The Nizam Framework
  Authors"), with a corresponding license notice added to `README.md`.

### Changed

- `CONTEXT.md`: rewritten to be current — stale forward-references removed,
  the phase-002 compliance-validator and CI-gate surfaces added, the
  injected payload corrected to the actual four directories plus
  `NIZAM.json`, the `.agent/` path documented, and `status` flipped to
  `active`.
- `README.md`: given a quickstart, a two-audience (framework-maintainer
  vs. consumer-repo) split, links to the HTML guide and the GitHub Release,
  and mentions of the compliance validator, the CI gate, and the
  Architecture Decision Records.

### Fixed

- `tools/interface.md`: corrected the runtime-adapter discovery order so a
  bootstrapped consumer's `.nizam/tools/skill.json` is checked first, with
  the repository-root `tools/skill.json` retained as an explicitly labeled
  framework-checkout fallback.
- `standard/GIP.md`: corrected the injected-payload description (previously
  stale at three directories) to the actual four directories plus
  `NIZAM.json` everywhere it is enumerated, and added an Adopting in an
  Existing Repository section defining incremental adoption tiers.

## [0.2.0] - 2026-07-08

### Added

- `docs/architecture/ADR-001-ci-compliance-enforcement.md`: records the
  decision to adopt CI enforcement of `standard/NDS.md` §7 via a repo-local,
  runtime-agnostic compliance validator invoked by a GitHub Actions workflow
  on every pull request and every push to `main`, closing the gap between
  the framework's prescribed enforcement and its previously-unenforced
  shipped state.
- `tools/validate.sh`, the repo-local NDS compliance validator: eight checks
  (C1-C8) — frontmatter schema, format, untagged-fence sweep, `NIZAM.json`
  index integrity, branding/endpoint leakage, `bootstrap.sh` sanity, module
  README presence, and version-bump-vs-changelog — plus `tools/fixtures/`
  negative fixtures exercising each failure mode, and a `nizam-compliance-validator`
  capability entry indexing it in `NIZAM.json`.
- `.github/workflows/compliance.yml`, the CI gate running `tools/validate.sh`
  on `pull_request` and on `push` to `main` (full-history checkout, so the
  C8 version-bump-vs-changelog check's `git show HEAD:<path>` lookups
  resolve correctly).

### Changed

- `.agent/product_spec.md` §2.1 (Hybrid Mono-Repo Layout): amended to add
  `.github/workflows/` and `tools/validate.sh` to the architecture diagram;
  `spec_version` bumped 1.0.0 → 1.1.0.
- `methodology/02_adversarial_tdd.md` (0.2.0): adds the External Anchor Rule
  (Section 7) and the Mandatory Adversarial Evidence requirement (Section 8).
- `methodology/04_tool_driven_state.md` (0.2.0): adds the Evidence Capture
  Convention and the Clock-Read Timestamps rule (Section 5).
- `methodology/00_planning.md` (0.2.0): adds the Plan Amendment Rule
  (Section 9), covering orchestrator-registrable amendments, Planner-routed
  re-planning, and scope-budget re-baselines.
- `methodology/05_release_train.md` (0.2.0): adds Release Mechanics
  Ownership (Section 6), assigning changelog roll-up, date-stamping, and tag
  creation to the release-manager/orchestrator role.

## [0.1.0] - 2026-07-08

### Added

- Framework genesis: the Nizam hybrid mono-repo, shipping six governance
  modules as a single portable payload — `standard/` (documentation standard,
  governance inheritance protocol, agent governance framework, universal
  anti-hallucination constraints), `methodology/` (planning enforcement,
  contract-first execution harness, adversarial TDD, circuit breaker,
  tool-driven state, release train), `registry/` (the `NIZAM.json` index
  schema and scope-definition patterns), `templates/` (consumer-repo
  CONTEXT/AGENTS/DEBT/ADR/work-packet/phase/manifest templates), `schema/`
  (JSON Schemas for every machine-readable framework artifact), and `tools/`
  (the single, unified, runtime-agnostic skill payload).
- `NIZAM.json`, the root machine-readable capability index and context
  router, validating against `registry/nizam-index.schema.json`.
- `bootstrap.sh`, the unified clone → inject → verify governance inheritance
  mechanism (the evolution of the earlier AGIP (a predecessor prototype)) —
  clones a pinned `GOVERNANCE_TAG`, stages and injects `standard/`,
  `templates/`, `schema/`, `tools/`, and `NIZAM.json` into a consumer
  repository's `.nizam/`
  directory, verifies the injection, and records provenance. Supports a
  network-free `--verify-only` drift-detection mode and a `--help` mode.

### Changed

- `methodology/00_planning.md`: the Scope Budget Protocol's per-feature check
  now defines the rolling-average bootstrap rule for when fewer than three
  features have completed.
- `methodology/03_circuit_breaker.md`: Section 4's breach procedure now
  requires discarding untracked/generated artifacts (not just a
  `git reset --hard`) on circuit-breaker trip, and merges the prior two
  separate BLOCKED-state writes into one atomic write single-sourced from the
  phase document's step-level status.
- `standard/AGF.md`: the JSON Verdict Parse Rule now includes a parse-valid
  example verdict block alongside the existing gate-rule fragment.
- `templates/ADR_TEMPLATE.md`, `templates/AGENTS.md`, `templates/README.md`,
  `tools/interface.md`: documentation corrections (PROPOSED default status,
  single-token session-start placeholder, disambiguated `product_spec.md`
  path, corrected checklist section citations).

### Fixed

- `bootstrap.sh`: `--verify-only` now checks for `python3` up front (via
  `require_command python3`), so a python3-less machine gets the clear
  "required command not found" diagnostic instead of a misleading generic
  failure from `check_nizam_index()`/`check_provenance_tag()`.
- NDS compliance: `authoritative_source` frontmatter values across all shipped
  governance `.md` files are now repo-relative (the stale `nizam-framework/`
  prefix is stripped), matching `NIZAM.json`'s existing repo-relative
  precedent.
- NDS compliance: every previously-untagged fenced code block across the
  shipped docs (`standard/AGF.md`, `standard/NDS.md`,
  `methodology/00_planning.md`, `methodology/01_execution.md`,
  `registry/scope_definition_patterns.md`) now carries an honest ```text``` or
  ```json``` language tag per NDS Sec 6.2.
- `.agent/product_spec.md`: `status` corrected from `DRAFT` to the schema-valid
  lowercase `draft`.
- Verdict-shape canonicalization: the JSON verdict shape is now consistent
  across `standard/AGF.md`, `methodology/01_execution.md`, and
  `tools/SKILL.md` on the sibling-array form (`final_verdict` holds only
  `approved`; `issues`, `missing_acceptance_coverage`, and
  `unsupported_claims` are top-level siblings of `final_verdict`, matching
  actual pipeline practice).
