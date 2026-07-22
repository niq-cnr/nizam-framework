---
id: nizam-product-spec-010
title: "Nizam Framework — Phase 010 Spec (0–n Project Spectrum, Stage 3: The n-case — Multi-Repo Tooling) — PROPOSAL"
description: "Phase-010 proposal: realize NIP-0002 (The 0–n Project Spectrum) Stage 3 — the n-case (many associated repositories forming one ecosystem). Promotes registry/scope_definition_patterns.md from a draft pattern to a required, schema-validated ecosystem-membership artifact that sets n (NDEBT-031), extends the ecosystem tooling to iterate that membership set of repo-roots instead of one --repo-root, mechanizes the cross-repository aggregation + consistency the shipped tools guard only as a 'future extension', adds hermetic n-case coverage, then pilots the n-case against a scratch multi-repo ecosystem to PROVE it and prioritise the Stage-4 coordination protocols from that evidence. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-010). Stage 4 (the 04/05 dependency-reconciliation / release-train coordination protocols + companion schemas, activating the reserved H-PLANNING-AUTHORITY / H-TRAIN-ENTRY gates), the release cut carrying the whole loop (NDEBT-029), and a real, non-scratch multi-repo pilot are explicitly OUT OF SCOPE — carried as phase-011 candidate scope. Extends product_spec.md..product_spec_009.md; replaces none."
tags: [spec, ecosystem-cycle, zero-to-n, multi-repo, membership-registry, phase-010, proposal]
status: active
last_audited: "2026-07-22"
authoritative_source: NA
version: 1.1.0
spec_version: "1.0.0"
created_at: "2026-07-22T02:00:00Z"
updated_at: "2026-07-22T02:15:00Z"
change_log:
  - version: "1.1.0"
    date: "2026-07-22T02:15:00Z"
    summary: "Phase activated: frontmatter status draft -> active on operator authorization 2026-07-22 (verbatim: 'Approved. Proceed with the phase-010 proposal + activation', gate H-PHASE-010, recorded in .agent/run_state.json event phase_activated before any feature execution per the NDEBT-018 rule). current_phase advanced 009-greenfield-genesis -> 010-multi-repo; scope budget reset (1160 est, phase-009 final archived). Body Status banner updated PROPOSED -> ACTIVE plan of record; no scope change. The proposal and activation were done in the same cycle per the operator's instruction; the draft status was the designed proposal state, flipped as the decision lifecycle reached activation (the 005 lesson applied as intended)."
  - version: "1.0.0"
    date: "2026-07-22T02:00:00Z"
    summary: "Initial phase-010 proposal, authored after PR #46 merged phase 009 (NIP-0002 Stage 2, Greenfield Genesis) to main. Scope sourced from NIP-0002's Staged Realization Stage 3 (the n-case — multi-repo tooling + the required membership registry) + the phase-009 pilot evidence (which validated the ordering: the n-case builds on the incubating partition phase 009 populated) + the open debt row NDEBT-031. Taken one stage at a time, as phases 008/009 took Stages 1/2. Frontmatter status stays draft until operator activation (gate H-PHASE-010) — the 005 lesson: status tracks the decision lifecycle, not anticipates it. No feature may enter contract negotiation before that authorization; current_phase remains 009-greenfield-genesis (complete) until then. Stage 4 (04/05 coordination protocols) plus the release cut carrying the whole loop (NDEBT-029) and a real, non-scratch multi-repo pilot are deferred to phase 011, evidence-gated on this phase's n-case pilot."
---

# Nizam Framework — Phase 010 Spec (0–n Project Spectrum, Stage 3: The n-case — Multi-Repo Tooling)

**Status: ACTIVE — plan of record.** Phase `010-multi-repo` was authorized for activation by the
operator on 2026-07-22 (verbatim: **"Approved. Proceed with the phase-010 proposal + activation"**,
satisfying gate **H-PHASE-010**; recorded in `.agent/run_state.json` event `phase_activated`
before any feature execution, per the NDEBT-018 rule). It advances **NIP-0002 (The 0–n Project
Spectrum)** to Stage 3 (the n-case). Per `methodology/00_planning.md`, the Planner-produced spec
and the DAG-validated feature list (`.agent/feature_list_010.json`) existed at proposal; the
operator authorization completed the activation triad. `docs/planning/manifest.json` carries
`current_phase: 010-multi-repo` with the phase-010 entry `status: in_progress`. Execution begins
with the ungated DAG root feature 075 (the ecosystem-membership registry schema).

## 1. Purpose

NIP-0002 requires the Ecosystem Engineering Cycle to span an ecosystem of **0 to n projects**,
staged and evidence-led. Phase 008 delivered the **"1"** point (a single, already-existing
project runs the loop cleanly) and phase 009 the **"0"** point (a new project stood up from
nothing). The **"n"** point — *many* associated repositories forming one ecosystem — remains:
the shipped ecosystem tools derive one `repository_name` and take a single `--repo-root`, their
multi-repository consistency guard is annotated a "defensive invariant for a future extension",
and the ecosystem-membership set that *sets* `n` has no required, validated artifact
(`registry/scope_definition_patterns.md` is a draft pattern; `NDEBT-031`). A consumer running
the cycle over more than one repository today runs it once per repository and aggregates by hand.

Phase 010 makes the **n-case** first-class: a required, schema-validated membership registry that
declares the set, tooling that iterates that set, and a mechanized cross-repo aggregation — then
**pilots it to prove it**. It deliberately does **not** author the `04`/`05` coordination
protocols (Stage 4) or cut a release (`NDEBT-029`): those build *on top of* an n-case iteration
that does not yet exist, so per the framework's governing rule (*no claim may be promoted beyond
its evidence*) they are deferred to phase 011 and prioritised from this phase's pilot evidence.
This is the same prove-then-build shape phases 007–009 used.

## 2. Scope

### 2.1 In scope (features 075–079)

- **075 — Ecosystem-membership registry schema** (`NDEBT-031`; NIP-0002 Stage 3). Author a JSON
  schema for a membership-registry *instance* — the list-partition shape
  (`in_scope`/`incubating`/`reference_archive`/`out_of_scope`), the entry shape, and the
  exactly-one-list invariant of `registry/scope_definition_patterns.md` §2 — and promote that
  pattern doc from a draft to a **required, schema-backed** artifact that sets `n`. Validate a
  membership registry (a validator check and/or dogfood check) with covering fixtures.
- **076 — Multi-repo iteration** (`NDEBT-031`). Extend the ecosystem tooling to read the
  membership registry and iterate its `in_scope` set of repo-roots — running the per-repository
  stage across the set — instead of assuming a single `--repo-root` (as a new mode on an
  existing tool or a companion orchestrator, decided at contract time). The single-`--repo-root`
  path stays unchanged (regression-guarded); the count-1 case is the degenerate single-member set.
- **077 — Cross-repo aggregation + consistency** (`NDEBT-031`). Mechanize the multi-repository
  consistency the shipped tools guard only as a "future extension": aggregate the per-repository
  verdicts into one ecosystem-level result, and enforce cross-repo consistency (e.g. every member
  ran under the same framework pin). What today is a hand-aggregation becomes a produced,
  schema-valid ecosystem-level artifact.
- **078 — n-case coverage** (`NDEBT-031`). Add hermetic e2e + self-test coverage: stand up a
  scratch **multi-repo** ecosystem (two or more genesis'd repos, reusing `bootstrap.sh
  --genesis` from phase 009), author a membership registry over them, and prove the iteration +
  aggregation runs across the set. The single-repo paths stay green (regression-guarded).
- **079 — Pilot the n-case, prove, refine + phase close.** Run the loop across a scratch
  multi-repo ecosystem with the fixed tooling: a validated membership registry, the tools
  iterating the set, and a correct aggregate result, with no hand-applied workaround. Record
  residual friction as `NDEBT-*`, **refine and validate** the phase-011 candidate scope (NIP-0002
  Stage 4 + `NDEBT-029` + the real pilot) *this proposal already authored in
  `docs/planning/ROADMAP.md`* against the pilot evidence, and close phase 010.

### 2.2 Out of scope (→ phase-011 candidate scope)

NIP-0002 Stage 4 and its neighbours, deferred until the n-case is *proven* against real evidence:

- **n-coordination protocols** (Stage 4): authoring `ecosystem/04_dependency_reconciliation.md`
  and `ecosystem/05_release_train_coordination.md` with their companion schemas — where
  cross-repo *ordering* and release-train *entry* genuinely live, activating the reserved
  `H-PLANNING-AUTHORITY` (Plan) and `H-TRAIN-ENTRY` (Promote) gates.
- Cutting a framework release that carries the whole loop — the genesis capability, the
  audit/compare tools, and the n-case tooling (`NDEBT-029`) — a release-train action.
- A **real, non-scratch multi-repo ecosystem pilot** — the standing production-maturity
  criterion across the whole 0–n programme (a scratch ecosystem exercises mechanics, not real
  multi-project maturity).

## 3. Preconditions

All five features are executable without any external repo. Features 075–078 are
framework-internal (schema + tooling + registry promotion + tests). Feature 079's pilot uses the
same **scratch/throwaway** path phases 007–009 established (operator option c) — two or more
fresh projects stood up *from nothing* by `bootstrap.sh --genesis` (phase 009) and declared in a
scratch membership registry — and needs no external repo access. The `H-CONSUMER-UPGRADE` gate is
exercised per member for those genesis adoptions, recorded before each bootstrap (the NDEBT-018
rule). A **real, non-scratch multi-repo ecosystem** remains a standing production-maturity
criterion, carried across the programme.

## 4. Functional Requirements

| FR | Requirement | Realized by |
|----|-------------|-------------|
| FR-01 | A membership-registry *instance* is validated against a shipped JSON schema encoding the list-partition shape, the entry shape, and the exactly-one-list invariant; `scope_definition_patterns.md` is a required, schema-backed artifact that sets `n`. | F-075 |
| FR-02 | The ecosystem tooling reads a membership registry and iterates its `in_scope` set of repo-roots, running the per-repository stage across the set; the single-`--repo-root` path is unchanged. | F-076 |
| FR-03 | Per-repository verdicts are aggregated into one schema-valid ecosystem-level result, and cross-repo consistency (e.g. a common framework pin) is enforced rather than hand-checked. | F-077 |
| FR-04 | Hermetic e2e + self-test coverage proves the iteration + aggregation across a scratch multi-repo ecosystem; the single-repo paths stay green. | F-078 |
| FR-05 | The n-case is proven end-to-end against a scratch multi-repo ecosystem, and the next tranche (NIP-0002 Stage 4 + `NDEBT-029` + the real pilot) is prioritised from that evidence. | F-079 |

## 5. Human Gates

Recorded per `docs/planning/operator_gates.md`. The pipeline records but never self-executes
a human gate.

1. **H-PHASE-010 — OUTSTANDING.** Authorize activation of this proposal (required before any
   feature enters contract negotiation). Its acceptance advances NIP-0002 to Stage 3.
2. **H-CONSUMER-UPGRADE — recurring, exercised per member at F-079.** Approve each genesis'd
   member's adoption of the framework tag before its Bootstrap proceeds; recorded in `run_state`
   before each bootstrap runs (the NDEBT-018 rule), as in phases 007–009.

The reserved gates `H-PLANNING-AUTHORITY` (Plan) and `H-TRAIN-ENTRY` (Promote) map to the Stage-4
`04`/`05` coordination protocols and **stay reserved** — those protocols are phase-011 scope.
`H-CONSOLIDATION` and `H-GA` (Repeat/Promote stages 06/08) also stay reserved.

## 6. Dogfood and Validation Plan

- **Framework-internal (075–078):** `bash tools/validate.sh` stays green (15/15, or grows by a
  membership-registry check) with the schema/tooling changes; `tools/fixtures_self_test.sh` gains
  membership-registry positive/negative fixtures and iteration/aggregation probes;
  `tools/e2e_bootstrap_test.sh` (or a companion) gains the multi-repo case. `NIZAM.json` /
  `schema/README.md` / `tools/skill.json` are updated in lockstep for any new schema or capability
  so C10/C13 stay consistent.
- **Pilot (079):** stand up a scratch multi-repo ecosystem (≥2 genesis'd repos), author a
  membership registry over them, and run the iteration + aggregation end-to-end producing
  schema-valid per-repo and ecosystem-level artifacts; every residual friction point is a new
  `NDEBT-*` row. Success = the n-case runs across the set with no hand-applied workaround.

## 7. Sequencing

`075` (the membership-registry schema) is the DAG root; `076` (multi-repo iteration) depends on
it; `077` (aggregation + consistency) depends on `076`; `078` (coverage) depends on `076` and
`077`; `079` depends on all four and proves them. Features 075–078 can land as a
framework-internal PR on activation; 079 pilots and closes the phase. The Stage-4/release work
(Section 2.2) is **already authored** as phase-011 candidate scope in `docs/planning/ROADMAP.md`
by this proposal; F-079 **refines and validates** that existing candidate against the pilot
evidence (it does not re-author it), and no Stage-4 work is begun in this phase.
