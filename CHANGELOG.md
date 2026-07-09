# Changelog

All notable changes to the Nizam framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
