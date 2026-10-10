---
id: nizam-context
title: "Nizam Framework — Context"
description: "Token-efficient architecture and execution-command summary for agents consuming the Nizam framework."
version: 1.5.0
status: active
authoritative_source: CONTEXT.md
change_log:
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

- `schema/` — JSON Schemas for every machine-readable artifact (frontmatter, manifest, phase, feature list, contract, QA verdict, run state).
- `standard/` — The Nizam Documentation Standard (NDS), the Agent Governance Framework (AGF), the Governance Inheritance Protocol (GIP), the anti-hallucination constraints, the constitutional policy set (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance), and the layered Definition of Done.
- `methodology/` — Planning, execution, adversarial TDD, circuit breaker, tool-driven state, release train protocols.
- `templates/` — Consumer-repo templates (CONTEXT, AGENTS, DEBT, ADR, work-packet, phase, manifest).
- `tools/` — The single runtime-agnostic skill payload (no per-runtime forks), entered via `tools/SKILL.md`.
- `registry/` — The `NIZAM.json` index schema and scope-definition patterns.
- `docs/` — Architecture Decision Records (`docs/architecture/`) and the self-contained HTML user guide (`docs/guide/index.html`).
- `ecosystem/` — The reusable, schema-governed Ecosystem Engineering Cycle protocols: Bootstrap (`00`), clean-state preflight (`01`), evidence baseline (`02`), engineering audit (`03`), dependency reconciliation (`04`, the Plan stage), release-train coordination (`05`, the Promote stage), and progress comparison (`07`) — now consumer-adoptable (a consumer bootstraps the framework and runs the full 0–n lifecycle), not framework-side only.

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

- Bootstrap a consumer repo: `bootstrap.sh` clones a pinned framework tag, injects the
  six governance directories `standard/`, `templates/`, `schema/`, `tools/`,
  `methodology/`, and `ecosystem/` plus the root `NIZAM.json` capability index, and
  verifies compliance before declaring success.
- Validate framework artifacts against their schemas using any standard JSON Schema
  validator against the files under `schema/`, or run `tools/validate.sh` for the
  repo-local compliance check that `.github/workflows/compliance.yml` runs in CI.

## Out of Scope

Nizam never modifies consumer deployments — it only ships governance payload that a
consumer repo ingests. Nizam is not a runtime: it contains no application code and no
infrastructure or hosted services. Nizam ships exactly one skill payload; no per-runtime
skill forks (e.g. `.claude/`, `.codex/`) are permitted anywhere in the repo.
