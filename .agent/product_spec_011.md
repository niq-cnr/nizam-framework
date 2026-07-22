---
id: nizam-product-spec-011
title: "Nizam Framework — Phase 011 Spec (0–n Project Spectrum, Stage 4: n-Coordination Protocols — Dependency Reconciliation & Release-Train Coordination) — PROPOSAL"
description: "Phase-011 proposal: realize NIP-0002 (The 0–n Project Spectrum) Stage 4 — the n-coordination protocols, the final stage of the staged plan. Authors the two deferred ecosystem protocols where cross-repo ordering and release-train entry genuinely live — ecosystem/04_dependency_reconciliation.md (the Plan stage) and ecosystem/05_release_train_coordination.md (the Promote stage) — with their companion schemas, defines the reserved H-PLANNING-AUTHORITY and H-TRAIN-ENTRY gates that map to them, mechanizes each as a stdlib-only tool that consumes the phase-010 ecosystem-level aggregate (schema/ecosystem_membership_result.schema.json / tools/ecosystem_membership_run.py) as its input substrate, adds hermetic Stage-4 coverage, then pilots the coordination layer against a scratch multi-repo ecosystem to PROVE it and prioritise the remaining production-maturity work from that evidence (NDEBT-035). The release cut carrying the whole loop (NDEBT-029), a real non-scratch multi-repo pilot, and the remaining Repeat/GA protocols (06_simplification_review / 08_ga_gate with H-CONSOLIDATION / H-GA) are explicitly OUT OF SCOPE — carried as phase-012 candidate scope. Extends product_spec.md..product_spec_010.md; replaces none. Frontmatter status stays draft until operator activation (gate H-PHASE-011) — the 005 lesson: status tracks the decision lifecycle, not anticipates it."
tags: [spec, ecosystem-cycle, zero-to-n, multi-repo, coordination, dependency-reconciliation, release-train, phase-011, proposal]
status: draft
last_audited: "2026-07-22"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-22T05:00:00Z"
updated_at: "2026-07-22T05:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-22T05:00:00Z"
    summary: "Initial phase-011 proposal, authored after PR #47 merged phase 010 (NIP-0002 Stage 3, the n-case — Multi-Repo Tooling) to main. Scope sourced from NIP-0002's Staged Realization Stage 4 (the n-coordination protocols — 04_dependency_reconciliation + 05_release_train_coordination, with companion schemas, where cross-repo ordering and release-train entry genuinely live) + the phase-010 pilot evidence (feature 079, .agent/evidence/pilot-079/, which validated the ordering: the ecosystem-level aggregate result already records per-member verdicts + a common-pin consistency finding — exactly the substrate a 04 reconciliation pass consumes) + the open debt row NDEBT-035. This is the FINAL stage of NIP-0002, taken one stage at a time as phases 008/009/010 took Stages 1/2/3. Frontmatter status stays draft until operator activation (gate H-PHASE-011) — the 005 lesson: status tracks the decision lifecycle, not anticipates it. No feature may enter contract negotiation before that authorization; current_phase remains 010-multi-repo (complete) until then. The release cut carrying the whole loop (NDEBT-029), a real non-scratch multi-repo pilot, and the remaining Repeat/GA protocols (06/08 with the reserved H-CONSOLIDATION / H-GA gates) are deferred to phase 012, evidence-gated on this phase's Stage-4 pilot."
---

# Nizam Framework — Phase 011 Spec (0–n Project Spectrum, Stage 4: n-Coordination Protocols)

**Status: PROPOSED — awaiting operator activation (gate H-PHASE-011).** This spec and the
DAG-validated feature list (`.agent/feature_list_011.json`) are Planner artifacts; per
`methodology/00_planning.md` a phase becomes the plan of record only on operator authorization
(gate **H-PHASE-011**). Until then `current_phase` remains `010-multi-repo` (complete), `status`
stays `draft` (the 005 lesson — frontmatter tracks the decision lifecycle, it does not anticipate
it), and **no feature enters contract negotiation**. `.agent/run_state.json` is untouched (a
proposal is not an activation). It advances **NIP-0002 (The 0–n Project Spectrum)** to Stage 4 —
the **final** stage of the staged plan. On activation, execution begins with the ungated DAG root
feature 080 (the dependency-reconciliation protocol + its companion schema).

## 1. Purpose

NIP-0002 requires the Ecosystem Engineering Cycle to span an ecosystem of **0 to n projects**,
staged and evidence-led. Phases 008/009/010 delivered the **"1"**, **"0"**, and **"n"** points:
a single existing project runs the loop cleanly, a new project is stood up from nothing, and *many*
associated repositories are declared in a required, schema-validated membership registry, iterated,
and aggregated into one ecosystem-level result with cross-repo consistency enforced. What remains
is the **coordination** layer: with `n` members now enumerated and their verdicts aggregated, the
cycle can *see* the whole ecosystem but cannot yet **coordinate work across it**. NIP-0002 places
the genuine n-repo coordination in two deferred protocols (`ecosystem/04_dependency_reconciliation.md`
and `ecosystem/05_release_train_coordination.md`, both still `Planned` in `ecosystem/README.md`)
— the lifecycle's **Plan** and **Promote** stages, where cross-repository *ordering* and
release-train *entry* live — and reserves the two operator gates that govern them
(`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`). Neither protocol, schema, nor gate is authored today
(`NDEBT-035`).

Phase 011 makes the **coordination layer** first-class: the two protocol documents, their
companion schemas, the two reserved gates *defined*, and a mechanization that consumes the
phase-010 ecosystem-level aggregate as its input substrate — then **pilots it to prove it**. It
deliberately does **not** cut a release (`NDEBT-029`), run a real non-scratch pilot, or author the
remaining Repeat/GA protocols (`06`/`08`): those build *on top of* a coordination layer that does
not yet exist, so per the framework's governing rule (*no claim may be promoted beyond its
evidence*) they are deferred to phase 012 and prioritised from this phase's pilot evidence. This is
the same prove-then-build shape phases 007–010 used. **Completing Stage 4 completes NIP-0002.**

## 2. Scope

### 2.1 In scope (features 080–084)

- **080 — Dependency-reconciliation protocol (`ecosystem/04`) + companion schema** (`NDEBT-035`;
  NIP-0002 Stage 4). Author `ecosystem/04_dependency_reconciliation.md` — the lifecycle's **Plan**
  stage: how approved audit findings and the phase-010 ecosystem-level aggregate (per-member
  verdicts + the common-pin consistency finding) are turned into **typed, dependency-ordered
  cross-repository work packets**. Author a companion JSON schema for a reconciliation-plan
  *instance* (the packet shape, the typed cross-repo dependency edges, the topological-order
  invariant). **Define** the reserved `H-PLANNING-AUTHORITY` gate (move it from the reserved table
  into the decided table with scope/trigger/disposition semantics, as phase 007 did for
  `H-CONSUMER-UPGRADE`). Register the schema in `NIZAM.json` + `schema/README.md`. Flip the
  `ecosystem/README.md` module-navigation row `04 … Planned → Shipped`. **Root (doc + schema).**
- **081 — Release-train coordination protocol (`ecosystem/05`) + companion schema** (`NDEBT-035`).
  Author `ecosystem/05_release_train_coordination.md` — the lifecycle's **Promote** stage: the
  entry conditions under which reconciled work packets are admitted into a **cross-repository
  release train**, the train-manifest shape, and the record-but-never-self-execute promotion rule.
  Author a companion JSON schema for a release-train-manifest *instance*. **Define** the reserved
  `H-TRAIN-ENTRY` gate. Register the schema; flip the `05 … Planned → Shipped` row. **dep 080** (a
  train admits a reconciliation plan).
- **082 — Reconciliation tooling** (`NDEBT-035`). Mechanize the Plan stage: a stdlib-only `tools/`
  script that reads the phase-010 aggregate (`ecosystem_membership_run.py`'s `membership_run.json`,
  `schema/ecosystem_membership_result.schema.json`) plus a set of approved findings and **produces
  a schema-valid, dependency-ordered reconciliation plan** — a produced artifact, not a
  hand-rollup. Enforce the topological-order invariant (a cyclic cross-repo dependency set is a
  first-class flagged finding forcing a non-PASS verdict, never a silent mis-order), mirroring the
  documented exit-code table + stdlib-only style of the existing ecosystem tools. **dep 080.**
- **083 — Release-train tooling + Stage-4 coverage** (`NDEBT-035`). Mechanize the Promote-entry
  check: a stdlib-only `tools/` script that reads a reconciliation plan (082) and **produces a
  schema-valid release-train manifest**, gated on `H-TRAIN-ENTRY` (recorded, never self-executed).
  Add hermetic e2e + self-test coverage: stand up a scratch **multi-repo** ecosystem (reusing the
  phase-010 `assert_multirepo` scaffolding), run the aggregate → reconciliation → train chain
  across it, and prove each stage produces a schema-valid artifact. The single-repo and phase-010
  n-case paths stay green (regression-guarded). **dep 081, 082.**
- **084 — Pilot Stage 4, prove, prioritise + phase close.** Run the coordination layer across a
  scratch multi-repo ecosystem with the fixed tooling: the phase-010 aggregate feeds a produced,
  schema-valid reconciliation plan, which feeds a produced, schema-valid release-train manifest,
  with the dependency-ordering + train-entry invariants enforced and **no hand-applied workaround**.
  Record the `H-PLANNING-AUTHORITY` and `H-TRAIN-ENTRY` gate exercises before the acts they govern
  (the NDEBT-018 rule), and any residual friction as `NDEBT-*` rows with evidence under
  `.agent/evidence/<execution-id>/`. Then **refine and validate** the phase-012 candidate scope
  (`NDEBT-029` release cut + the real pilot + the remaining `06`/`08` protocols) *this proposal
  already authored in `docs/planning/ROADMAP.md`* against the pilot evidence, and close phase 011.
  **Completing this feature completes NIP-0002's staged plan.**

### 2.2 Out of scope (→ phase-012 candidate scope)

The production-maturity and Repeat/GA neighbours, deferred until the coordination layer is *proven*
against real evidence:

- Cutting a framework release that carries the whole loop — genesis + audit/compare + the n-case
  tooling + the new coordination layer (`NDEBT-029`) — a release-train action, and a prerequisite
  for the standing real-consumer pilot.
- A **real, non-scratch multi-repo ecosystem pilot** — the standing production-maturity criterion
  across the whole 0–n programme (a scratch ecosystem exercises mechanics, not real multi-project
  maturity).
- The remaining lifecycle protocols `ecosystem/06_simplification_review.md` (Repeat) and
  `ecosystem/08_ga_gate.md` (Promote/GA), with the reserved `H-CONSOLIDATION` and `H-GA` gates —
  outside NIP-0002's 0–n staged plan (they govern the recurring-improvement and GA concerns, not
  project count), prioritised separately from real evidence rather than authored speculatively.

## 3. Preconditions

All five features are executable without any external repo. Features 080–083 are
framework-internal (two protocols + two schemas + two tools + tests). Feature 084's pilot uses the
same **scratch/throwaway** path phases 007–010 established (operator option c) — a scratch
multi-repo ecosystem stood up *from nothing* by `bootstrap.sh --genesis` (phase 009) and declared
in a scratch membership registry (phase 010) — and needs no external repo access. The phase-010
ecosystem-level aggregate (`membership_run.json`) is the coordination layer's input substrate and
already exists (proven by feature 079). The `H-PLANNING-AUTHORITY` and `H-TRAIN-ENTRY` gates are
exercised in the pilot, recorded before the acts they govern (the NDEBT-018 rule). A **real,
non-scratch multi-repo ecosystem** remains a standing production-maturity criterion, carried across
the programme.

## 4. Functional Requirements

| FR | Requirement | Realized by |
|----|-------------|-------------|
| FR-01 | The Plan stage is authored as `ecosystem/04_dependency_reconciliation.md` with a companion schema for a reconciliation-plan instance (typed cross-repo dependency edges + topological-order invariant); the reserved `H-PLANNING-AUTHORITY` gate is defined; the module-navigation `04` row flips Planned → Shipped. | F-080 |
| FR-02 | The Promote stage is authored as `ecosystem/05_release_train_coordination.md` with a companion schema for a release-train-manifest instance; the reserved `H-TRAIN-ENTRY` gate is defined; the `05` row flips Planned → Shipped. | F-081 |
| FR-03 | A stdlib-only tool consumes the phase-010 ecosystem-level aggregate + approved findings and produces a schema-valid, dependency-ordered reconciliation plan; a cyclic cross-repo dependency set is a flagged finding forcing a non-PASS verdict, not a silent mis-order. | F-082 |
| FR-04 | A stdlib-only tool consumes a reconciliation plan and produces a schema-valid release-train manifest gated on `H-TRAIN-ENTRY` (recorded, never self-executed); hermetic e2e + self-test coverage proves the aggregate → reconciliation → train chain across a scratch multi-repo ecosystem; prior paths stay green. | F-083 |
| FR-05 | The coordination layer is proven end-to-end against a scratch multi-repo ecosystem, the two Stage-4 gates are exercised before the acts they govern, and the next tranche (`NDEBT-029` release cut + the real pilot + the `06`/`08` protocols) is prioritised from that evidence. | F-084 |

## 5. Human Gates

Recorded per `docs/planning/operator_gates.md`. The pipeline records but never self-executes
a human gate.

1. **H-PHASE-011 — OUTSTANDING.** Authorizes activation of this proposal (required before any
   feature enters contract negotiation); its acceptance advances NIP-0002 to Stage 4 and will be
   recorded in `.agent/run_state.json` (event `phase_activated`) before any feature runs, per the
   NDEBT-018 rule.
2. **H-PLANNING-AUTHORITY — defined at F-080, first exercised at F-084.** Approves the planning
   authority a reconciliation plan asserts across repositories before it is admitted downstream;
   record-but-never-self-execute. Moved from the reserved table into the decided table at F-080
   (as phase 007 did for `H-CONSUMER-UPGRADE`); recorded in `run_state` before the pilot's plan is
   promoted (the NDEBT-018 rule).
3. **H-TRAIN-ENTRY — defined at F-081, first exercised at F-084.** Admits reconciled work into a
   cross-repository release train; record-but-never-self-execute. Recorded in `run_state` before
   the pilot's train manifest is produced.

The reserved gates `H-CONSOLIDATION` (Repeat/stage 06) and `H-GA` (Promote/stage 08) map to the
`06`/`08` protocols and **stay reserved** — those protocols are phase-012 candidate scope, outside
NIP-0002's 0–n staged plan.

## 6. Dogfood and Validation Plan

- **Framework-internal (080–083):** `bash tools/validate.sh` stays green (15/15, or grows by
  reconciliation-plan / release-train-manifest checks — likely extending the C12 schema-family
  router with two new families) with the schema/tooling changes; `tools/fixtures_self_test.sh`
  gains reconciliation-plan and release-train-manifest positive/negative fixtures (including a
  cyclic-dependency negative that must FAIL and an ungated-train-entry negative);
  `tools/e2e_bootstrap_test.sh` gains the Stage-4 coordination case chained onto `assert_multirepo`.
  `NIZAM.json` / `schema/README.md` / `tools/skill.json` / `ecosystem/README.md` are updated in
  lockstep for the two new schemas + two new protocols + two new capabilities so C9/C10/C13 stay
  consistent.
- **Pilot (084):** stand up a scratch multi-repo ecosystem, run the aggregate → reconciliation →
  train chain end-to-end producing schema-valid reconciliation-plan and release-train-manifest
  artifacts, with the two Stage-4 gates exercised and recorded before the acts they govern; every
  residual friction point is a new `NDEBT-*` row. Success = the coordination layer runs across the
  set with no hand-applied workaround.

## 7. Sequencing

`080` (the reconciliation protocol + schema, the Plan stage) is the DAG root; `081` (the
release-train protocol + schema, the Promote stage) depends on it (a train admits a reconciliation
plan); `082` (reconciliation tooling) depends on `080`; `083` (release-train tooling + coverage)
depends on `081` and `082`; `084` depends on all four and proves them. Features 080–083 can land as
a framework-internal PR on activation; 084 pilots and closes the phase — **and with it, NIP-0002's
staged plan**. The release/real-pilot/06-08 work (Section 2.2) is **already authored** as
phase-012 candidate scope in `docs/planning/ROADMAP.md` by this proposal; F-084 **refines and
validates** that existing candidate against the pilot evidence (it does not re-author it), and no
phase-012 work is begun in this phase.
