---
id: nizam-product-spec-007
title: "Nizam Framework — Phase 007 Spec (Consumer-Adoption Enablement & First External Pilot) — PROPOSAL"
description: "Phase-007 proposal: close the one foundational gap the shipped ecosystem loop leaves — the Bootstrap stage has no protocol document and its gate H-CONSUMER-UPGRADE is an undefined reserved name — then run the first REAL external-consumer pilot (handover F-016..F-020) to generate non-self-referential friction, and let that evidence prioritise the remaining deferred protocols. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-007) and, for the pilot, access to a consumer repository. Extends product_spec.md..product_spec_006.md; replaces none."
tags: [spec, ecosystem-cycle, consumer-adoption, bootstrap, pilot, phase-007, proposal]
status: draft
last_audited: "2026-07-20"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-20T00:00:00Z"
updated_at: "2026-07-20T00:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-20T00:00:00Z"
    summary: "Initial phase-007 proposal, authored after the Tier-0/Tier-1 ecosystem completion merged (schema/audit_delta.schema.json + tools/ecosystem_audit.py + tools/compare_ecosystem_baselines.py + tools/validate_evidence_freshness.py). Scope sourced from ROADMAP Track 4 (First External Consumer Pilot) and the NIP-0001 successor consumer-adoption programme (handover F-016..F-020). Frontmatter status stays draft until operator activation (gate H-PHASE-007) — the 005 lesson: status must track the decision lifecycle, not anticipate it. No feature may enter contract negotiation before that authorization; current_phase remains 006-enforcement-closure (complete) until then."
---

# Nizam Framework — Phase 007 Spec (Consumer-Adoption Enablement & First External Pilot)

**Status: PROPOSED — awaiting operator authorization.** Phase `007-consumer-adoption`
is NOT activated. Per `methodology/00_planning.md` a phase becomes real only on
operator authorization (gate **H-PHASE-007**); `docs/planning/manifest.json` keeps
`current_phase: 006-enforcement-closure` (complete) and carries this phase as
`status: pending` until that authorization is recorded in `.agent/run_state.json`
(event `phase_activated`), committed before any feature execution per the NDEBT-018
rule. The Planner-produced spec and DAG-validated feature list
(`.agent/feature_list_007.json`) exist at proposal; operator authorization completes
the activation triad.

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

1. **H-PHASE-007 — OUTSTANDING.** Authorize activation of this proposal (required
   before any feature enters contract negotiation) and resolve the consumer-repo
   sourcing question of Section 3.
2. **H-CONSUMER-UPGRADE — OUTSTANDING (to be DEFINED by F-061).** Approve a consumer's
   adoption of a newly released framework tag before the pilot's Bootstrap stage
   proceeds. F-061 defines its semantics; F-063 is the first exercise of it.

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
