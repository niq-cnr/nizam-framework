---
id: nizam-product-spec-009
title: "Nizam Framework — Phase 009 Spec (0–n Project Spectrum, Stage 2: Greenfield Genesis) — PROPOSAL"
description: "Phase-009 proposal: realize NIP-0002 (The 0–n Project Spectrum) Stage 2 — the 0-case (greenfield genesis). Stands up a NEW project from nothing and bootstraps the framework into it (NDEBT-030): authors the greenfield-genesis protocol, mechanizes a create-and-scaffold capability, models the incubating→in_scope (count-0→1) transition on the scope registry, adds hermetic e2e coverage, then pilots the 0-case against a scratch greenfield project to PROVE it and prioritise the n-case/04-05 stages from that evidence. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-009). The n-case (multi-repo tooling + membership registry, NDEBT-031), the 04/05 coordination protocols, and the release cut carrying audit/compare (NDEBT-029) are explicitly OUT OF SCOPE — carried as phase-010 candidate scope. Extends product_spec.md..product_spec_008.md; replaces none."
tags: [spec, ecosystem-cycle, zero-to-n, greenfield-genesis, bootstrap, scaffold, phase-009, proposal]
status: active
last_audited: "2026-07-22"
authoritative_source: NA
version: 1.1.0
spec_version: "1.0.0"
created_at: "2026-07-22T00:00:00Z"
updated_at: "2026-07-22T00:10:00Z"
change_log:
  - version: "1.1.0"
    date: "2026-07-22T00:10:00Z"
    summary: "Phase activated: frontmatter status draft -> active on operator authorization 2026-07-22 (verbatim: 'Activate phase 009', gate H-PHASE-009, recorded in .agent/run_state.json event phase_activated before any feature execution per the NDEBT-018 rule). current_phase advanced 008-consumer-readiness -> 009-greenfield-genesis; scope budget reset (1000 est, phase-008 final archived). Body Status banner updated PROPOSED -> ACTIVE plan of record; no scope change. The draft status was the designed proposal state, flipped only now that the decision lifecycle reached activation (the 005 lesson applied as intended)."
  - version: "1.0.0"
    date: "2026-07-22T00:00:00Z"
    summary: "Initial phase-009 proposal, authored after PR #45 merged phase 008 (NIP-0002 Stage 1, Consumer-Readiness) to main. Scope sourced from NIP-0002's Staged Realization Stage 2 (the 0-case — greenfield genesis) + the phase-008 re-pilot evidence + the open debt row NDEBT-030. The operator directed taking Stage 2 next, one stage at a time (as phase 008 took Stage 1). Frontmatter status stays draft until operator activation (gate H-PHASE-009) — the 005 lesson: status tracks the decision lifecycle, not anticipates it. No feature may enter contract negotiation before that authorization; current_phase remains 008-consumer-readiness (complete) until then. NIP-0002 Stages 3–4 (n-case multi-repo tooling + membership registry NDEBT-031, 04/05 coordination protocols) plus the release cut carrying the audit/compare tools (NDEBT-029) are deferred to phase 010, evidence-gated on this phase's 0-case pilot."
---

# Nizam Framework — Phase 009 Spec (0–n Project Spectrum, Stage 2: Greenfield Genesis)

**Status: ACTIVE — plan of record.** Phase `009-greenfield-genesis` was authorized for
activation by the operator on 2026-07-22 (verbatim: **"Activate phase 009"**, satisfying gate
**H-PHASE-009**; recorded in `.agent/run_state.json` event `phase_activated` before any feature
execution, per the NDEBT-018 rule). It advances **NIP-0002 (The 0–n Project Spectrum)** to
Stage 2 (the 0-case). Per `methodology/00_planning.md`, the Planner-produced spec and the
DAG-validated feature list (`.agent/feature_list_009.json`) existed at proposal; the operator
authorization completed the activation triad. `docs/planning/manifest.json` carries
`current_phase: 009-greenfield-genesis` with the phase-009 entry `status: in_progress`.
Execution begins with the ungated DAG root feature 070 (the greenfield-genesis protocol).

## 1. Purpose

NIP-0002 requires the Ecosystem Engineering Cycle to span an ecosystem of **0 to n projects**,
staged and evidence-led. Phase 008 realized **Stage 1 (consumer-readiness)** — the "1" point of
the spectrum (a single, already-existing project) now runs the loop cleanly. The **"0" point
remains absent**: standing up a *new* project from nothing and bootstrapping the framework into
it has no protocol, tooling, or vocabulary ("genesis"/"scaffold" refer only to the framework
building itself in phase 001), and `ecosystem/00_ecosystem_bootstrap.md` presupposes a target
repo that already exists (`NDEBT-030`).

Phase 009 makes the **0-case (greenfield genesis)** first-class and mechanized, then
**pilots it to prove it**. It deliberately does **not** build the n-case (multi-repo tooling)
or the `04`/`05` coordination protocols — those are Stages 3–4, which build on a membership
registry the 0-case only begins to populate, so per the framework's governing rule (*no claim
may be promoted beyond its evidence*) they are deferred to phase 010 and prioritised from this
phase's pilot evidence. This is the same prove-then-build shape phases 007 and 008 used.

## 2. Scope

### 2.1 In scope (features 070–074)

- **070 — Greenfield-genesis protocol** (`NDEBT-030`; NIP-0002 Stage 2). Author the genesis
  stage semantics: the precondition (no repo / an empty project), the create-and-scaffold
  steps, the minimal project skeleton, the consumer-supplied inputs each new ecosystem must
  provide (`ecosystem/00` §5), and the entry condition into Bootstrap → Preflight. Establish
  "genesis"/"scaffold" vocabulary distinct from the framework's own phase-001 genesis.
  Authored as an `ecosystem/00_ecosystem_bootstrap.md` amendment or a dedicated sub-protocol
  (decided at contract time), house structure matching `ecosystem/00`/`01`.
- **071 — Genesis scaffold capability** (`NDEBT-030`). Mechanize standing up a new project from
  nothing — `git init` + a minimal, deterministic project skeleton (a README, a source
  placeholder, and the consumer inputs `ecosystem/00` §5 names) + injecting the pinned `.nizam/`
  payload — as a `--genesis` mode on `bootstrap.sh` or a companion `tools/` script (decided at
  contract time), reusing the existing pinned-tag inject + provenance path unchanged. The
  existing inject-into-existing-repo path stays unchanged (regression-guarded).
- **072 — Incubating→in_scope transition** (`NDEBT-030`, the count-0→1 rung). Model the scope
  registry's `incubating` partition as the tracked 0→1 state: a genesis'd project starts
  `incubating` (tracked but not yet a full member) and is promoted to `in_scope`. A *scoped
  slice* of `registry/scope_definition_patterns.md` covering the incubating case only — NOT the
  full membership-registry promotion (that is Stage 3 / `NDEBT-031`, phase 010).
- **073 — Genesis e2e coverage** (`NDEBT-030`). Extend `tools/e2e_bootstrap_test.sh` (or a
  companion hermetic test) to prove genesis creates a new project from nothing, scaffolds it,
  injects the payload, and yields a clean Preflight (`PASS`, or an operator-approved
  `PASS_WITH_EXCEPTIONS` whose only exception is the injected `.nizam/`). The existing
  inject-into-existing-repo path stays green (regression-guarded).
- **074 — Pilot the 0-case, prove, refine + phase close.** Stand up a scratch/throwaway
  **greenfield** project via genesis (operator option c, as in phases 007/008 — needs no
  external repo), run the loop end-to-end, and prove the 0-case with no hand-applied workaround.
  Record residual friction as `NDEBT-*`, **refine and validate** the phase-010 candidate scope
  (NIP-0002 Stages 3–4) *this proposal already authored in `docs/planning/ROADMAP.md`* against
  the pilot evidence — confirming or re-ordering it, not re-authoring it — and close phase 009.

### 2.2 Out of scope (→ phase-010 candidate scope)

NIP-0002 Stages 3–4, deferred until the 0-case is *proven* against real evidence:

- **The n-case — multi-repo tooling** (`NDEBT-031`): extending the ecosystem tools to iterate an
  ecosystem-membership registry (a set of repo-roots) instead of one `--repo-root`, and
  promoting `registry/scope_definition_patterns.md` from draft patterns to a required, validated
  membership artifact that sets `n`.
- **n-coordination protocols**: authoring `04_dependency_reconciliation.md` and
  `05_release_train_coordination.md` with their companion schemas — where cross-repo ordering
  and release-train entry genuinely live (activating the reserved `H-PLANNING-AUTHORITY` /
  `H-TRAIN-ENTRY` gates).
- Cutting a framework release that carries the audit/compare tools (`NDEBT-029`) — a
  release-train action, handled when a release is next cut, and a prerequisite for the standing
  **real, non-scratch consumer pilot**.

## 3. Preconditions

All five features are executable without any external repo. Features 070–073 are
framework-internal (protocol/doc + bootstrap/tool code + registry + tests). Feature 074's pilot
uses the same **scratch/throwaway** path phases 007/008 established (operator option c) — a
fresh, empty directory stood up *from nothing* by the genesis capability itself and bootstrapped
from an ephemeral/pre-release tag — and needs no external repo access. The `H-CONSUMER-UPGRADE`
gate (defined in phase 007) is exercised again for that genesis adoption, recorded before the
bootstrap runs (the NDEBT-018 rule). A **real, non-scratch greenfield project** remains a
standing production-maturity criterion, carried across the programme.

## 4. Functional Requirements

| FR | Requirement | Realized by |
|----|-------------|-------------|
| FR-01 | The greenfield-genesis stage is a documented first-class protocol: precondition (no/empty repo), create-and-scaffold steps, the minimal skeleton + consumer-supplied inputs, and the entry into Bootstrap → Preflight — distinct from the framework's own phase-001 genesis. | F-070 |
| FR-02 | A single command stands up a new project from nothing: `git init` + a minimal deterministic skeleton + injection of the pinned `.nizam/` payload, reusing the existing provenance path; the inject-into-existing-repo path is unchanged. | F-071 |
| FR-03 | A genesis'd project is tracked in the scope registry's `incubating` partition and can be promoted `incubating → in_scope`, mechanizing the count-0→1 transition. | F-072 |
| FR-04 | Hermetic e2e coverage proves genesis-from-nothing → scaffold → inject → clean Preflight, with the existing bootstrap path regression-guarded. | F-073 |
| FR-05 | The 0-case loop is proven end-to-end against a scratch greenfield project, and the next tranche (NIP-0002 Stages 3–4) is prioritised from that evidence. | F-074 |

## 5. Human Gates

Recorded per `docs/planning/operator_gates.md`. The pipeline records but never self-executes
a human gate.

1. **H-PHASE-009 — OUTSTANDING.** Authorize activation of this proposal (required before any
   feature enters contract negotiation). Its acceptance advances NIP-0002 to Stage 2.
2. **H-CONSUMER-UPGRADE — recurring, exercised again at F-074.** Approve the genesis'd project's
   adoption of the framework tag before the Bootstrap stage proceeds; recorded in `run_state`
   before the bootstrap runs (the NDEBT-018 rule), as in phases 007/008.

The four reserved gates (`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`, `H-CONSOLIDATION`, `H-GA`)
stay reserved — their protocols (the n-case coordination stages) remain out of scope, deferred
to phase 010.

## 6. Dogfood and Validation Plan

- **Framework-internal (070–073):** `bash tools/validate.sh` stays green (15/15) with the
  protocol/registry/tool changes; `tools/fixtures_self_test.sh` gains coverage of the
  incubating-partition model; `tools/e2e_bootstrap_test.sh` continues to pass and gains the
  genesis-from-nothing case. `ecosystem/00_ecosystem_bootstrap.md` and any companion doc are
  updated in lockstep so C10 stays consistent, and `ecosystem/README.md` / `tools/skill.json` /
  `NIZAM.json` are updated if a new capability entry is warranted.
- **Pilot (074):** the genesis capability stands up a scratch greenfield project from nothing;
  inside it, `ecosystem_preflight.py` produces a clean Preflight and a correctly-anchored
  baseline; the loop (Preflight → Baseline → Audit → Compare) runs end-to-end producing
  schema-valid artifacts; every residual friction point is a new `NDEBT-*` row. Success = the
  0-case runs from nothing with no hand-applied workaround.

## 7. Sequencing

`070` (the protocol) is the DAG root; `071` (scaffold capability) and `072` (incubating
transition) depend on it; `073` (e2e) depends on `071` and `072`; `074` depends on all four and
proves them. Features 070–073 can land as a framework-internal PR on activation; 074 pilots and
closes the phase. The n-case/04-05 work (Section 2.2) is **already authored** as phase-010
candidate scope in `docs/planning/ROADMAP.md` by this proposal; F-074 **refines and validates**
that existing candidate against the pilot evidence (it does not re-author it), and no Stage-3–4
work is begun in this phase.
