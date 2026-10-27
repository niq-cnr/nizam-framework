---
id: nizam-context
title: "Nizam Framework — Context"
description: "Token-efficient architecture and execution-command summary for agents consuming the Nizam framework."
version: 3.1.0
status: active
authoritative_source: CONTEXT.md
change_log:
  - version: "3.1.0"
    date: "2026-10-27"
    summary: "Prepare the v3.1.0 MINOR release (NF-OWNER-2026-10-27): hardened read-only Git identity seam (tools/git_seam.py, NF-R01/F02), reconciled atomic .nizam/ payload installation vs external proportionate activation in standard/GIP.md and finite task-scoped operator_recovery in methodology/03_circuit_breaker.md (NF-R02/F10/F11), versioned 1.1.0 typed binary review packet coverage and magic-byte sniffing in schema/review_packet.schema.json and tools/convergent_review.py (NF-R03/F09), optional generic external evidence admission contract and CLI in schema/external_evidence_admission.schema.json and tools/external_evidence.py (NF-R04), standalone consumer e2e qualification suite (tools/test_nf_ac05_standalone_e2e.py, NF-R05), and the approved API-REF-PILOT backlog plan. All changes are additive and hardening; no shipped schema was narrowed. The local .nizam/ payload is self-installed to the published v3.0.0 release (2b8298ae1d5a41534e00b6710a738b4b181b87fa)."
  - version: "3.0.0"
    date: "2026-10-27"
    summary: "Prepare the NF-22 MAJOR corrective candidate: C13 manifest enforcement, consumer routing and first-contact link coverage. Publication and self-adoption remain pending review and release sign-off."
  - version: "2.0.0"
    date: "2026-10-24"
    summary: "Prepare the v2.0.0 MAJOR release of the completion, structured-QA, canonical receipt replay and finite retry repairs. Existing consumers must migrate verification inventories, assessed proof and recovery authority; docs/migration-v2.0.0.md records the compatibility boundary. Tag publication and official local self-adoption remain separate observed steps; no commissioning or production readiness is asserted."
  - version: "1.11.0"
    date: "2026-10-23"
    summary: "Prepare the v1.11.0 MINOR release: add the provider-neutral semantic observation architecture (Choice/Noul/Score contracts, mode-isolated off-by-default policy, the versioned question/policy catalog, the seven decision families, the optional host-side Jev adapter and provider-attempt usage accounting), the independently-adjudicated evaluation corpus and four-arm harness, and the deterministic governance repairs (strict normalized QA acceptance, complete-delta scope binding, contract-identity consistency, authoritative monotonic attempts, and verified continuation authority); plus the earlier evidence-archive/bounded-preservation, sparse-bootstrap, llms.txt and README/guide refresh work. All new semantic capability is off by default; no shipped schema was narrowed. The installed .nizam/ payload remains pinned to v1.10.1 until the reviewed post-tag re-bootstrap to v1.11.0."
change_log:
  - version: "1.10.1"
    date: "2026-10-19"
    summary: "Prepare the v1.10.1 PATCH release: full repository-wide documentation and GitHub Pages accuracy refresh across docs/guide/index.html (retiring all v0.1.0 pins, 4-directory payload enumerations, 'Framework-side only so far', and pre-controller runtime-session prose; adding all 6 injected modules, --git-repo/--expected-sha/--require-content-integrity verification modes, semantic 5-route task routing and capture/publish/build-receipt helpers, and Section 4.4 external mutation mediation), CONTEXT.md (complete Module Map and Execution Commands), ecosystem/01_clean_state_preflight.md (v0.1.5 work-specific diagnostic stopping policy reference), methodology/10_live_runtime_sessions.md (v0.2.1) and methodology/11_sbcl_runtime_binding.md (v0.1.2) and schema/README.md (v0.20.2) (replacing stale phase016 pending prose with delivered features 126-129 bounded runtime controller/SBCL loop and Phase 020 features 130-132 full live SBCL qualification boundary), tools/interface.md (v0.5.2), tools/README.md (v0.37.2), tools/SKILL.md (v0.8.2), tools/skill.json (v0.8.2), NIZAM.json (v1.10.1), and tools/test_public_entry.py regression guards. Pure documentation/prose patch with 278 released files and no schema or behavioral break. The installed .nizam/ payload remains pinned to v1.10.0 until the reviewed post-tag re-bootstrap to v1.10.1. H-FRAMEWORK-RELEASE sign-off, tag, and pin authorization continue under the operator's 2026-10-19 mandate; the annotated tag act remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6)."
  - version: "1.10.0"
    date: "2026-10-19"
    summary: "Prepare the v1.10.0 MINOR release: the 2026-10-19 v1.9.0 audit and follow-up execution (C0-C5, closing findings F1-F3: default noncommitting --mode prepare in tools/start_path.py publish, removal of implicit local Git add/commit fallback from _git_commit_literal_paths, explicit NIZAM_MUTATION_ADAPTER requirement for committing publish/build-receipt, strict rejection of missing/empty/{}/boolean/denied/pending/failed adapter responses, unknown_external_commit_outcome reconciliation against actual repository state without duplicate commits or re-running captured commands, full branch/intended_base/diff-tree delta binding, and GIT_OPTIONAL_LOCKS=0 on read-side Git queries; elimination of ${TARGET_DIR}/tools/payload_integrity.py execution from bootstrap.sh --verify-only, --git-repo DIR support for install-time retained tag repositories and commit-bound content-integrity verification, explicit caller-supplied --expected-sha and --git-repo rules without mutable provenance.json fallback, distinct content_integrity=directory_match_unbound reporting for --source-root, and fail-closed helper exit-code handling; and executable work-specific diagnostic stopping policy in tools/start_path.py classify and capture with continuation_lineage tracking across attempts/splits plus aligned methodology/00_planning.md, methodology/01_execution.md, and schema/run_state.schema.json) lands as additive and hardening capability with 278 released files. The installed .nizam/ payload remains pinned to v1.9.0 until the reviewed post-tag re-bootstrap to v1.10.0. H-FRAMEWORK-RELEASE sign-off, tag, and pin authorization continue under the operator's 2026-10-19 mandate; the annotated tag act remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6)."
  - version: "1.9.0"
    date: "2026-10-18"
    summary: "Prepare the v1.9.0 MINOR release: the 2026-10-18 v1.8.0 rollout corrective execution (B0-B6, closing findings V1-V7: separated noncommitting prepare, externally mediated publish, noncommitting finalize, and strictly noncommitting default build-receipt in tools/start_path.py with literal pathspecs, isolated temporary GIT_INDEX_FILE staging, same-path staged conflict rejection, failed observation rejection, batching, and Stage 1 interruption recovery; strict SemVer release-tag syntax on the public path, explicit refs/tags/<tag> fetch/peel, same-name branch ambiguity rejection, install-time --expected-sha verification before target replacement, and 3-form normal/worktree reproducibility in bootstrap.sh and tools/e2e_bootstrap_test.sh; shared complete file-inventory, byte-content, and executable-mode payload integrity comparator tools/payload_integrity.py wired into verify_self_governance.py and bootstrap.sh --verify-only; non-conflated exercised/not-applicable/skipped/out-of-scope summary in tools/validate.sh --payload; aligned work-specific stopping policy across methodology/03_circuit_breaker.md, standard/acceptance_bars.md, tools/SKILL.md, tools/skill.json, NIZAM.json, methodology/README.md, and README.md; C13 version parity between tools/skill.json and tools/SKILL.md; provenance/capability discovery replacing hardcoded v1.5.0/phase016 claims in tools/SKILL.md and tools/README.md; and clarified release-tag payload vs. repository .nizam/ self-installation in README.md and docs/planning/SELF_GOVERNANCE.md) lands as additive and hardening capability with 278 released files. The installed .nizam/ payload remains pinned to v1.8.0 until the reviewed post-tag re-bootstrap to v1.9.0. H-FRAMEWORK-RELEASE sign-off, tag, and pin authorization continue under the operator's 2026-10-18 mandate; the annotated tag act remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6)."
  - version: "1.8.0"
    date: "2026-10-18"
    summary: "Prepare the v1.8.0 MINOR release: the 2026-10-18 post-remediation audit follow-up (A0-A8, closing F1-F6: unified canonical scope eligibility and non-vacuous QA completion across classify/begin/done/amend-contract; post-execution evidence publication and closed 12-field receipt capture projection in tools/start_path.py publish and build-receipt; live sandbox isolation probe in preflight and PATH sanitization in tools/isolated_trial_adapter.py; causal commit ordering, min_comparison_runs, tier-differentiated run bindings, captured case_proofs, and reviewer/producer provenance checks in verify_profiles_ready; aligned Routine/Standard/High-assurance responsibility tables, diagnostic stopping rules, and AGF verdict shape across standard/ and methodology/; dynamic phase/feature status discovery and contradiction reporting; zero-reach-back disposable consumer lifecycle rehearsal in tools/e2e_bootstrap_test.sh and .nizam/schema fallback in _receipt_schema; and the 12-task preregistered paired baseline-vs-shadow comparison in .agent/evidence/125/) lands as additive and hardening capability with no removed or renamed shipped file and no breaking governance change. The installed .nizam/ payload remains pinned to v1.7.0 until the reviewed post-tag re-bootstrap to v1.8.0. H-FRAMEWORK-RELEASE sign-off, tag, and pin authorization continue under the operator's 2026-10-18 mandate; the annotated tag act remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6)."
  - version: "1.7.0"
    date: "2026-10-18"
    summary: "Prepare the v1.7.0 MINOR release: feature 134 (portable Docker trial-sandbox adapter tools/docker_trial_sandbox.sh and adapter-specific conformance selection), Phase 019 features 124-125 (generic repository/worktree assurance profile preregistration and shadow comparison/recommendation, with persistent-runtime SBCL profile claims remaining gated on Phase 020 features 130-132), and the 2026-10-18 critical quality and velocity remediation (R0-R11: 5-route semantic task classification, trivial start path, lightweight contract amendments, unified stopping rules, capability preflight, exclusive non-overwriting evidence capture, Option A repository-binding migration, operational receipt/resume CLI, concise read-only status views, and deduplicated/bounded CI verification) land as additive, new-optional capability with no schema narrowing, no removed or renamed shipped file, and no breaking governance change; nothing that validated under v1.6.0 is invalidated. The installed .nizam/ payload remains pinned to v1.6.0 until the reviewed post-tag re-bootstrap to v1.7.0. H-FRAMEWORK-RELEASE sign-off, tag, and pin authorization are recorded from the operator's 2026-10-18 instruction; the annotated tag act remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6)."
  - version: "1.6.0"
    date: "2026-10-17"
    summary: "Prepare the v1.6.0 MINOR release: the Workflow Assurance tranche (features 115-119 foundation readiness; 120-123 receipt gates, conflict lanes, cause routing and capable CI controls; 126-128 bounded partial runtime core; 129 SBCL loop and confirmed cancellation, feature-scope complete with full-live qualification deliberately remaining features 131/132; 133 receipt-input batching) plus the start-path gating land as additive, new-optional capability with no schema narrowing, no removed or renamed shipped file and no breaking governance change; nothing that validated under v1.5.0 is invalidated. Everything else since v1.5.0 is framework-envelope only (audit-readiness, planning, maintenance and self-governance records). The installed .nizam/ payload remains the commissioned v1.5.0 pin; it is refreshed only by a reviewed, operator-authorized re-bootstrap AFTER the v1.6.0 tag exists. H-FRAMEWORK-RELEASE preparation is complete; the annotated tag remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6) and no tag is created by the pipeline."
  - version: "1.5.0"
    date: "2026-10-10"
    summary: "General Availability declared by the operator on 2026-10-10. H-GA is EXECUTED; H-CONSOLIDATION remains OUTSTANDING. The declaration proceeds with explicit evidence exceptions: real_production_pilot is not_met; recorded_consumer_adoptions is insufficient_evidence. These gaps remain recorded in the historical readiness dossier; recorded evidence gaps remain unresolved. Prepare the v1.5.0 MINOR release: phase 014 (GA track) and its maintenance tranche -- the ecosystem lifecycle protocols ecosystem/06_simplification_review.md (Repeat) and ecosystem/08_ga_gate.md (Promote/GA) flip draft -> active (0.2.0 each) and are registered as capabilities in NIZAM.json and tools/skill.json (0.4.0), with the operator gates H-CONSOLIDATION and H-GA defined (H-CONSOLIDATION OUTSTANDING; H-GA EXECUTED by the operator 2026-10-10); standard/capability_profiles.md (0.4.0) gains the explicit Role column enforced by the new C15 mapping primitive vlib_profiles_map_roles; the convergent-review suite ships required-conformance mode with UNSUPPORTED reporting and its convergent_review CI job (tools/test_convergent_review.py, tools/README.md 0.17.0); the default sweep checks C1/C2 over docs/nips/ and C13 in both modes enforces the intentional-subset skill-index rule. The shipped manifest/index pair remains compliant after re-bootstrap; C13 now enforces the intentional-subset rule in both full sweep and --payload, so independently added skill modules must be registered in NIZAM.json. Everything else since v1.4.0 is framework-envelope only (the phase-014 close and GA-readiness dossier, amendments, planning records, backlog reconciliation). H-FRAMEWORK-RELEASE sign-off and tag authorization are recorded from the operator's 2026-10-10 request; the tag act itself remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6) and no tag is created by the pipeline."
  - version: "1.4.0"
    date: "2026-10-08"
    summary: "Prepare the v1.4.0 MINOR release: the two proposal-grade ecosystem lifecycle protocol documents landed with the phase-014 proposal (PR #61) -- `ecosystem/06_simplification_review.md` (Repeat; consolidations only under the reserved H-CONSOLIDATION gate) and `ecosystem/08_ga_gate.md` (Promote/GA; GA declaration operator-only under the reserved H-GA gate), both `status: draft` and not yet normative (activation awaits phase-014 feature 099 under H-PHASE-014) -- plus their `ecosystem/README.md` rows and `NIZAM.json` ecosystem key_documents entries; purely additive, new-optional surface; nothing that validated under v1.3.0 is invalidated. Everything else since v1.3.0 is framework-envelope only (planning records, the phase-014 Planner artifacts, the NIP-0003 proposal). H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "1.3.0"
    date: "2026-09-30"
    summary: "Prepare the v1.3.0 MINOR release: the Review-Gate Flake Management methodology (`methodology/09_review_gate_flake_management.md`) -- operational doctrine for infrastructure failures of convergent review gates (fail-closed principles, the open F1-F6 flake-class taxonomy, the bounded retry ladder, protected-repository rules, telemetry, evidence duties, and KPI targets), registered in `NIZAM.json`, `methodology/README.md`, and the HTML guide -- purely additive, new-optional capability; nothing that validated under v1.2.0 is invalidated. H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "1.2.0"
    date: "2026-09-17"
    summary: "Prepare the v1.2.0 MINOR release: the Convergent Automated Code Review standard (`standard/convergent_code_review.md`, PR #57), its five closed review schemas (`schema/review_packet.schema.json`, `review_trial`, `review_ledger`, `review_suppression`, `review_replay`), the `templates/convergent-review-prompt.md` trial prompt, and the dependency-free `tools/convergent_review.py` CLI with its Linux sandbox adapter and permanent unittest suite -- purely additive, new-optional capability; nothing that validated under v1.1.0 is invalidated. H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "1.1.0"
    date: "2026-08-19"
    summary: "Prepare the v1.1.0 MINOR release, phase 013 (Definition of Done): the canonical layered Definition of Done (`standard/definition_of_done.md`), the feature-list lifecycle invariant (validator check C16), the release close-out gate (`.github/scripts/release_closeout.py`), the optional advisory `dod_ref` key on five schemas, and its two consumer projections (`templates/DoD.md`, `.github/PULL_REQUEST_TEMPLATE.md`) -- purely additive, new-optional capability; nothing that validated under v1.0.0 is invalidated. Applies the Module Map's `standard/` bullet edit deferred from feature 093 (this same version bump): the bullet now names the layered Definition of Done alongside the existing constitutional-and-standard document enumeration. H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "1.0.0"
    date: "2026-08-15"
    summary: "Prepare the v1.0.0 MAJOR release for phase 012's full issue-52 consumer-safety remediation: breaking schema invariants with a clean migration guide, correct reopened classification, isolated retry recovery, coherent five-role/lifecycle governance, and consumer-facing documentation aligned to shipped behavior. H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "0.9.0"
    date: "2026-07-22"
    summary: "Bump version for the v0.9.0 MINOR release, the first since v0.8.0, carrying phases 007-011: consumer-adoption enablement (ecosystem/00 Bootstrap protocol + H-CONSUMER-UPGRADE) and the full NIP-0002 realization (0-n Project Spectrum: consumer-readiness, greenfield genesis, the n-case membership registry + multi-repo tooling, and the Stage-4 04/05 coordination protocols), plus the audit/compare tooling now shipped in the tag (NDEBT-029). Module Map's ecosystem/ entry now enumerates the Bootstrap (00) and Stage-4 coordination (04/05) protocols and drops the stale 'framework-side only so far' (consumers now bootstrap and run the full 0–n lifecycle from the injected tools/); all additive, no removal or narrowing. A real non-scratch multi-repo pilot at this tag stays the standing production-maturity criterion."
  - version: "0.7.0"
    date: "2026-07-19"
    summary: "H-PAYLOAD-CONTRACT (phase-006 feature 051): the bootstrap payload sentence now names the SIX injected governance directories (standard/, templates/, schema/, tools/, methodology/, ecosystem/) plus NIZAM.json -- methodology/ and ecosystem/ joined the injected payload, resolving NDEBT-008; registry/ and docs/ remain framework-envelope and are not injected."
  - version: "0.6.0"
    date: "2026-07-17"
    summary: "Add ecosystem/ to the Module Map (the reusable Ecosystem Engineering Cycle module, framework-side only this phase); bump version to reflect the v0.7.0 release state."
  - version: "0.5.0"
    date: "2026-07-13"
    summary: "Bump version for v0.6.0 release (durable enforcement C9-C11, verify_lib, hermetic e2e bootstrap test, schema reconciliation, and the documentation-truth cleanup)."
  - version: "0.4.1"
    date: "2026-07-12"
    summary: "Stale-enumeration cleanup: the Module Map's standard/ entry now names the constitutional policy documents (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance) shipped since v0.4.0, instead of only the four genesis-era core documents."
  - version: "0.4.0"
    date: "2026-07-09"
    summary: "Bump version for v0.5.1 release (payload validation mode)."
  - version: "0.3.0"
    date: "2026-07-09"
    summary: "Add docs/ to Module Map (ADRs and HTML user guide); bump version to reflect v0.5.0 release state."
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Rewrite to reflect the shipped state: NIZAM.json and bootstrap.sh have both shipped (removed stale 'ships in feature 00X' claims); named the phase-002 compliance surfaces (tools/validate.sh, .github/workflows/compliance.yml, docs/architecture/); corrected the bootstrap payload sentence to the 4 injected directories (standard/, templates/, schema/, tools/) plus NIZAM.json; stated the agent entry path (NIZAM.json -> tools/SKILL.md); expanded NDS/AGF/GIP at first use with their verbatim canonical titles."
---

# Nizam Framework — CONTEXT

## Identity

Nizam is a generalised, AI-legible, versioned governance framework. It ships standards,
protocols, schemas, and templates as a single portable payload any AI agent or engineering
team can consume, in any runtime, for any project. Nizam is not application code, not
infrastructure, and not a runtime service.

## Module Map (Hybrid Mono-Repo)

- `schema/` — JSON Schemas for every machine-readable artifact (frontmatter, manifest, phase, feature list, contract, contract review, QA verdict, bug-fix cause/scope, small-change intent, run state, work packet, debt, capability profile, ecosystem preflight/baseline/finding/delta/membership/reconciliation/release-train, runtime session/operation, and convergent review packet/trial/ledger/suppression/replay).
- `standard/` — The Nizam Documentation Standard (NDS), the Agent Governance Framework (AGF), the Governance Inheritance Protocol (GIP), the anti-hallucination constraints, the constitutional policy set (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance), the layered Definition of Done, Convergent Automated Code Review, and Acceptance Bars.
- `methodology/` — Planning, contract-first execution, adversarial TDD, work-specific diagnostic stopping and circuit breaker, tool-driven durable state, eval and trace, release train, eval-gated promotion, cross-repo dependency gate, review-gate flake management, live runtime sessions, and SBCL runtime binding protocols.
- `templates/` — Consumer-repo templates (CONTEXT, AGENTS, DEBT, ADR, DoD, convergent-review prompt, work-packet, phase, manifest).
- `tools/` — The single runtime-agnostic skill payload (no per-runtime forks), entered via `tools/SKILL.md` and `tools/skill.json`, together with `tools/interface.md`, `tools/validate.sh`, `tools/payload_integrity.py`, `tools/start_path.py`, `tools/convergent_review.py`, `tools/workflow_assurance.py`, and `tools/runtime_session.py`.
- `registry/` — The `NIZAM.json` index schema and scope-definition patterns.
- `docs/` — Architecture Decision Records (`docs/architecture/`), migration guidance (`docs/migration-v1.0.0.md`), and the self-contained HTML user guide (`docs/guide/index.html`).
- `ecosystem/` — The reusable, schema-governed Ecosystem Engineering Cycle protocols: Bootstrap (`00`), clean-state preflight (`01`), evidence baseline (`02`), engineering audit (`03`), dependency reconciliation (`04`, the Plan stage), release-train coordination (`05`, the Promote stage), simplification review (`06`, the Repeat stage), progress comparison (`07`), and GA gate (`08`, the Promote-stage GA declaration) — consumer-adoptable across the full 0–n repository spectrum.

Compliance surfaces, added in phase 002-self-compliance, keep the shipped payload honest:
`tools/validate.sh` (the repo-local compliance validator), `.github/workflows/compliance.yml`
(the CI workflow that runs it on every push and pull request), and `docs/architecture/`
(where Architecture Decision Records such as ADR-001 and ADR-002 are recorded).

## How Agents Consume the Framework

Agents route through the root `NIZAM.json` capability index rather than bulk-reading
governance directories. The index resolves the minimal set of files a task requires
(protocol, schema, or template path) so context stays engineered, not exhausted.
`NIZAM.json` is the shipped root capability index; it indexes `tools/skill.json`, whose
`entry_point` field names `tools/SKILL.md` as the agent entry path. An agent resolves
`NIZAM.json` first, then `tools/skill.json`, then loads `tools/SKILL.md` to learn how to
plan, execute, gate, and durably record work.

## Execution Commands

- Bootstrap a consumer repo: `bootstrap.sh` clones a pinned framework tag, verifies
  `--expected-sha` before staging, injects the six governance directories `standard/`,
  `templates/`, `schema/`, `tools/`, `methodology/`, and `ecosystem/` plus the root
  `NIZAM.json` capability index (optionally retaining the verified tag repository at
  `--git-repo .nizam-ref/`), and verifies compliance before declaring success.
- Re-verify an installed payload offline without executing code from inside `.nizam/`:
  `./bootstrap.sh --verify-only --tag <vX.Y.Z> --expected-sha <40-hex-sha> --git-repo .nizam-ref/ --require-content-integrity`
  (or `--source-root <dir>` for `content_integrity=directory_match_unbound`, or
  `--structural-only` for `content_integrity=not_checked`).
- Route, capture, publish, and verify governed task state via `tools/start_path.py`
  (`classify`, `begin`, `done`, `amend-contract`, `preflight`, `capture`, `publish`
  defaulting to `--mode prepare`, `build-receipt`, `verify-receipt`, `resume`, `status`).
- Validate framework artifacts against their schemas using any standard JSON Schema
  validator against the files under `schema/`, or run `tools/validate.sh` for the
  repo-local compliance check that `.github/workflows/compliance.yml` runs in CI.

## Out of Scope

Nizam never modifies consumer deployments — it only ships governance payload that a
consumer repo ingests. Nizam is not a runtime: it contains no application code and no
infrastructure or hosted services. Nizam ships exactly one skill payload; no per-runtime
skill forks (e.g. `.claude/`, `.codex/`) are permitted anywhere in the repo.
