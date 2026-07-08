# Changelog

All notable changes to the Nizam framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes._

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

### Fixed

- `tools/validate.sh`: a missing C5 sweep target now emits `[C5] FAIL` and
  continues to the `SUMMARY` line instead of aborting the whole run; the
  leading-HTML-comment frontmatter tolerance is now scoped to
  `tools/fixtures/` only, so a shipped document cannot evade the C1 check.

### Security

- `.github/workflows/compliance.yml`: actions pinned to source-verified
  commit SHAs (`actions/checkout` v4.2.2, `actions/setup-python` v5.3.0),
  least-privilege `permissions: contents: read`, `persist-credentials: false`
  on checkout, and a `concurrency` group with `cancel-in-progress`.

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
  mechanism (the evolution of the earlier AGIP prototype) — clones a pinned
  `GOVERNANCE_TAG`, stages and injects `standard/`, `templates/`, `schema/`,
  `tools/`, and `NIZAM.json` into a consumer repository's `.nizam/`
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
