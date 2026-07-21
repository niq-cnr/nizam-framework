---
id: nizam-product-spec-007
title: "Nizam Framework — Phase 007 Spec (Consumer-Adoption Enablement & First External Pilot) — PROPOSAL"
description: "Phase-007 proposal: close the one foundational gap the shipped ecosystem loop leaves — the Bootstrap stage has no protocol document and its gate H-CONSUMER-UPGRADE is an undefined reserved name — then run the first REAL external-consumer pilot (handover F-016..F-020) to generate non-self-referential friction, and let that evidence prioritise the remaining deferred protocols. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-007) and, for the pilot, access to a consumer repository. Extends product_spec.md..product_spec_006.md; replaces none."
tags: [spec, ecosystem-cycle, consumer-adoption, bootstrap, pilot, phase-007, proposal]
status: active
last_audited: "2026-07-20"
authoritative_source: NA
version: 1.3.0
spec_version: "1.0.0"
created_at: "2026-07-20T00:00:00Z"
updated_at: "2026-07-21T00:00:00Z"
change_log:
  - version: "1.3.0"
    date: "2026-07-21T00:00:00Z"
    summary: "Planning-surface reconciliation after phase close (PR #42 review): Section 5 gate dispositions rolled to their exercised state (H-PHASE-007 EXERCISED 2026-07-20; H-CONSUMER-UPGRADE DEFINED+EXERCISED 2026-07-21), and the Status banner's stale 'pilot deferred' line replaced with the phase-COMPLETE record (features 060/061/063/064 complete, 062 cancelled). Mirrors the completion state already in .agent/run_state.json, .agent/feature_list_007.json, and docs/planning/manifest.json. No scope change."
  - version: "1.2.0"
    date: "2026-07-21T00:00:00Z"
    summary: "Phase-close amendment: records the operator's 2026-07-21 design requirement that the system span an ecosystem of 0-to-n projects, and cross-references the two governed docs authored to capture it — docs/nips/NIP-0002-zero-to-n-project-spectrum.md (the capability proposal, status Proposed, whose acceptance would make it phase 008's plan of record) and docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md (the pilot-proven single-project fixes, Accepted). No scope change to phase 007's shipped features 060-064; the pilot (063) executed against a scratch consumer (operator option c) and its friction is recorded as NDEBT-027..032. Section 3's consumer-repo question was resolved as the scratch-consumer path."
  - version: "1.1.0"
    date: "2026-07-20T00:00:00Z"
    summary: "Phase activated: frontmatter status draft -> active on operator authorization 2026-07-20 (verbatim: 'Authorized to activate now', gate H-PHASE-007, recorded in .agent/run_state.json event phase_activated before any feature execution per the NDEBT-018 rule). current_phase advanced 006-enforcement-closure -> 007-consumer-adoption; scope budget reset (870 est, phase-006 final archived). Body Status banner updated to ACTIVE plan of record; no scope change. The draft status was the designed proposal state, flipped only now that the decision lifecycle reached activation (the 005 lesson applied as intended)."
  - version: "1.0.0"
    date: "2026-07-20T00:00:00Z"
    summary: "Initial phase-007 proposal, authored after the Tier-0/Tier-1 ecosystem completion merged (schema/audit_delta.schema.json + tools/ecosystem_audit.py + tools/compare_ecosystem_baselines.py + tools/validate_evidence_freshness.py). Scope sourced from ROADMAP Track 4 (First External Consumer Pilot) and the NIP-0001 successor consumer-adoption programme (handover F-016..F-020). Frontmatter status stays draft until operator activation (gate H-PHASE-007) — the 005 lesson: status must track the decision lifecycle, not anticipate it. No feature may enter contract negotiation before that authorization; current_phase remains 006-enforcement-closure (complete) until then."
---

# Nizam Framework — Phase 007 Spec (Consumer-Adoption Enablement & First External Pilot)

**Status: ACTIVE — plan of record.** Phase `007-consumer-adoption` was authorized for
activation by the operator on 2026-07-20 (verbatim: **"Authorized to activate now"**,
satisfying gate **H-PHASE-007**; recorded in `.agent/run_state.json` event
`phase_activated` before any feature execution, per the NDEBT-018 rule).
`docs/planning/manifest.json` carries `current_phase: 007-consumer-adoption` with the
phase-007 entry `status: in_progress`. Per `methodology/00_planning.md`, the
Planner-produced spec and DAG-validated feature list (`.agent/feature_list_007.json`)
existed at proposal; the operator authorization completed the activation triad.
**Phase 007 is COMPLETE (2026-07-21).** Features 060, 061, 063, 064 landed; the
conditional 062 was cancelled (no brownfield collision to force GIP §5.1, carried as
NDEBT-032). The pilot (063–064) ran against a scratch/throwaway consumer (Section 3
resolved as option c).

**0–n design requirement (operator, 2026-07-21).** During execution the operator set a
first-class requirement that the system handle an ecosystem of **0 to n projects** — 0
(bootstrapping a new project from nothing / greenfield genesis), 1 (a single project,
greenfield or brownfield), and n (many associated projects forming a complex ecosystem).
This phase does **not** build the greenfield-genesis or multi-repo tooling speculatively
(no claim beyond evidence); it (a) makes the spectrum first-class in the Bootstrap
protocol (`ecosystem/00_ecosystem_bootstrap.md` §3, v0.2.0) and (b) captures the decisions
formally: `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` (the capability proposal that
becomes phase 008's plan of record on operator acceptance, gate H-NIP) and
`docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md` (the two pilot-proven
single-project fixes, Accepted). The 0–n build is the evidence-prioritized candidate scope
for phase 008 (`docs/planning/ROADMAP.md`).

## 1. Purpose

Phases 005–006 shipped and hardened the Ecosystem Engineering Cycle's core loop —
Preflight → Baseline → Audit → Compare — as four protocols, four schemas, and four
deterministic tools, dogfooded against this repository and released at v0.8.0. Two
things remain true and unaddressed:

1. **The lifecycle's entry stage has no protocol.** The canonical lifecycle
   (`ecosystem/README.md`) begins at **Bootstrap**, yet `ecosystem/00_ecosystem_bootstrap.md`
   was never written (it is marked *Planned*), and its operator gate
   `H-CONSUMER-UPGRADE` is a reserved name with no defined semantics
   (`docs/planning/operator_gates.md` §2). A consumer cannot formally enter the cycle
   because the stage that admits it is unspecified.
2. **All adoption evidence is self-referential.** Every bootstrap run to date injects
   the framework into a scratch copy of *itself* (`tools/e2e_bootstrap_test.sh`).
   ROADMAP Track 4 is explicit: *bootstrap a real second repository against a released
   tag, run `tools/validate.sh --payload` in it, and feed every friction point back as
   debt* — and it must complete *before any phase that expands cross-repo or
   constitutional scope*.

Phase 007 closes gap (1) with the minimum authoring needed, then executes gap (2) as
the first real pilot. It deliberately does **not** author the remaining deferred
protocols speculatively: the framework's governing rule is *no claim may be promoted
beyond its evidence*, and the pilot is what produces the evidence to prioritise them.

## 2. Scope

### 2.1 In scope (features 060–064)

- **060 — Bootstrap-stage protocol.** Author `ecosystem/00_ecosystem_bootstrap.md`,
  wrapping the existing Governance Inheritance Protocol (`standard/GIP.md`) and
  `bootstrap.sh`; flip its `ecosystem/README.md` status row Planned→Shipped.
- **061 — Define `H-CONSUMER-UPGRADE`.** Move it from RESERVED to a defined,
  dispositionable gate in `docs/planning/operator_gates.md`.
- **062 — (conditional) Real-consumer bootstrap reconciliation.** Implement GIP §5.1
  rename-and-diff in `bootstrap.sh` for a consumer with pre-existing root-level
  `CONTEXT.md`/`AGENTS.md`/CI. Executed only if the pilot (063) surfaces the need.
- **063 — First external-consumer pilot (realises handover F-016/F-019).** Bootstrap
  a released framework tag into a real consumer repository; run `tools/validate.sh
  --payload` there; drive Preflight → Baseline → Audit → Compare against it; capture
  every friction point as a `docs/planning/DEBT.md` (`NDEBT-*`) row. Gate:
  `H-CONSUMER-UPGRADE` + operator-provided consumer-repo access.
- **064 — Plan the next automation tranche (realises handover F-020).** From the
  pilot's recorded friction, prioritise which of the deferred protocols
  (`04_dependency_reconciliation`, `05_release_train_coordination`,
  `06_simplification_review`, `08_ga_gate`) and their companion schemas to author in a
  subsequent phase — evidence-driven, not speculative — and close phase 007.

### 2.2 Out of scope

- **Speculative authoring of `04/05/06/08`** and their companion schemas
  (`dependency_graph`, `ecosystem_complexity`, `ga_evidence_index`), and defining the
  other four reserved gates (`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`,
  `H-CONSOLIDATION`, `H-GA`). These remain deferred until pilot friction justifies each
  (NIP-0001 mitigation ordering: "delay optional complexity and GA packaging features
  until the initial loop works").
- **The full consumer-side programme** beyond the first preflight/adoption evidence.
  Handover F-017 (simplify NizamIQ prompts) and F-018 (reconcile planning authority)
  are consumer-repo-internal work that belongs to the consumer's own governance, not
  to this framework phase.

## 3. Preconditions and dependency on consumer-repo access

The pilot features (063–064) **require a consumer repository the operator authorizes
and this session can reach.** The canonical target named throughout the planning
record is `nizamiq/nizamiq-strategy` (`NIP-0001`, `product_spec_005.md` §2.2), a
*different organization* outside this session's GitHub scope; `product_spec_006.md`
§2.2 already flags that the successor phase "requires … access to the consumer
repository." Activation must therefore also resolve **which** consumer repo the pilot
runs against (the canonical target added via `add_repo` subject to org authorization;
a different operator-provided repo; or a scratch consumer to exercise loop mechanics).
Features 060–061 (and 062) are framework-internal and executable without any external
repo.

## 4. Functional Requirements

| FR | Requirement | Realised by |
|----|-------------|-------------|
| FR-01 | The Bootstrap lifecycle stage has a single-source-of-truth protocol document defining its precondition (pinned immutable tag), the injected payload, verification/provenance drift, the consumer-supplied inputs each ecosystem must provide, and the entry condition into Preflight. | F-060 |
| FR-02 | `H-CONSUMER-UPGRADE` is a defined operator gate with scope, trigger, and disposition semantics — no longer a reserved name. | F-061 |
| FR-03 | Bootstrapping into a consumer that already has root-level `CONTEXT.md`/`AGENTS.md`/CI never silently overwrites them (GIP §5.1 rename-and-diff). | F-062 (conditional) |
| FR-04 | The core loop runs end-to-end against a real, non-self repository and produces schema-valid artifacts, with every friction point recorded as debt. | F-063 |
| FR-05 | The next tranche of deferred-protocol work is prioritised from recorded pilot evidence, not from speculation. | F-064 |

## 5. Human Gates

Recorded per `docs/planning/operator_gates.md`. The pipeline records but never
self-executes a human gate.

1. **H-PHASE-007 — EXERCISED 2026-07-20.** Operator authorized activation (verbatim
   "Authorized to activate now"); the consumer-repo sourcing question of Section 3 was
   resolved as the scratch-consumer path (option c).
2. **H-CONSUMER-UPGRADE — DEFINED (F-061) and EXERCISED 2026-07-21 (F-063).** Defined in
   `docs/planning/operator_gates.md`; first exercised when the operator authorized
   adopting the scratch consumer against released tag v0.8.0 for the pilot (recorded in
   `.agent/run_state.json` before the bootstrap ran, per the NDEBT-018 rule). Recurring.

The other four reserved gates (`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`,
`H-CONSOLIDATION`, `H-GA`) stay reserved — their deferred protocols are out of scope
(Section 2.2).

## 6. Dogfood and Validation Plan

- **Framework-internal (060–062):** `bash tools/validate.sh` stays green (15/15) with
  the new protocol document passing C1 (frontmatter), C8 (version-bump-vs-changelog),
  C9 (path-resolution), C10 (single-source-of-truth consistency), and — if a capability
  entry is added — C13 (skill-index); `ecosystem/README.md`'s status table is flipped
  in the same change so C10 stays consistent; `tools/e2e_bootstrap_test.sh` continues
  to pass and, for F-062, gains coverage of the rename-and-diff path.
- **Pilot (063):** inside the bootstrapped consumer, `tools/validate.sh --payload` is
  green; `ecosystem_preflight.py --repo-root <consumer>` → `ecosystem_audit.py` →
  `compare_ecosystem_baselines.py` run end-to-end; evidence is externalised under the
  consumer's `.agent/reconciliation|audits|evidence/`; each friction point is a new
  `NDEBT-*` row. Success = the loop produces schema-valid artifacts against a non-self
  repo.

## 7. Sequencing

`060 → 061` (the gate guards the bootstrap the protocol defines) → **operator resolves
consumer access** → `063` (first pilot) → `064` (plan next tranche); `062` is inserted
before `063` only if a real consumer with pre-existing root files makes it necessary.
Features 060–061 can land as a framework-internal PR immediately on activation; the
pilot (063–064) follows once a consumer repository is available.
