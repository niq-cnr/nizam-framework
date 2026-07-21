---
id: nizam-product-spec-008
title: "Nizam Framework — Phase 008 Spec (0–n Project Spectrum, Stage 1: Consumer-Readiness) — PROPOSAL"
description: "Phase-008 proposal: realize NIP-0002 (The 0–n Project Spectrum) Stage 1 — make the single-project (count-1) case genuinely consumer-ready. Implements ADR-004 (governance-root resolution + provenance-pin anchoring, NDEBT-027/028), hardens bootstrap provenance to a resolved commit SHA (NDEBT-033), mechanizes GIP §5.1 brownfield reconciliation (NDEBT-032), then re-pilots to PROVE the fixed single-project loop against a real bootstrapped consumer and prioritises the 0-case/n-case/04-05 stages from that evidence. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-008). The 0-case (greenfield genesis, NDEBT-030), the n-case (multi-repo tooling + membership registry, NDEBT-031), and the 04/05 coordination protocols are explicitly OUT OF SCOPE — carried as phase-009 candidate scope. Extends product_spec.md..product_spec_007.md; replaces none."
tags: [spec, ecosystem-cycle, consumer-readiness, zero-to-n, bootstrap, provenance, phase-008, proposal]
status: active
last_audited: "2026-07-21"
authoritative_source: NA
version: 1.1.0
spec_version: "1.0.0"
created_at: "2026-07-21T00:00:00Z"
updated_at: "2026-07-21T11:00:00Z"
change_log:
  - version: "1.1.0"
    date: "2026-07-21T11:00:00Z"
    summary: "Phase activated: frontmatter status draft -> active on operator authorization 2026-07-21 (verbatim: 'Approved. Please proceed', gate H-PHASE-008, recorded in .agent/run_state.json event phase_activated before any feature execution per the NDEBT-018 rule). current_phase advanced 007-consumer-adoption -> 008-consumer-readiness; scope budget reset (1010 est, phase-007 final archived). Body Status banner updated PROPOSED -> ACTIVE plan of record; no scope change. The draft status was the designed proposal state, flipped only now that the decision lifecycle reached activation (the 005 lesson applied as intended)."
  - version: "1.0.1"
    date: "2026-07-21T00:00:00Z"
    summary: "PR #43 review corrections (proposal still draft, no scope change): F-069 and the Sequencing section reworded from 'author the phase-009 candidate scope' to 'refine/validate' the candidate scope this proposal already wrote into docs/planning/ROADMAP.md; the F-068 brownfield contract sharpened to distinguish file preservation (intact original + deterministic collision-safe renamed copy, per GIP Sec 5.1) from CI merging (added, never replaced); and the FR table header spelling normalised to 'Realized by' to match the document's American 'realize/realization' prose. The mirrored feature_list_008.json acceptance criteria and CHANGELOG NIP-0002 entry were reconciled in the same change."
  - version: "1.0.0"
    date: "2026-07-21T00:00:00Z"
    summary: "Initial phase-008 proposal, authored after PR #42 merged phase 007 to main and the operator accepted NIP-0002 (gate H-NIP, 'NIP-0002 is accepted') — which SELECTS phase 008 as the NIP's realization. Scope sourced from NIP-0002's Staged Realization Stage 1 (Consumer-readiness, the prerequisite for every larger project count) + ADR-004's two accepted decisions + the phase-007 pilot debt (NDEBT-027/028/032/033). Frontmatter status stays draft until operator activation (gate H-PHASE-008) — the 005 lesson: status tracks the decision lifecycle, not anticipates it. No feature may enter contract negotiation before that authorization; current_phase remains 007-consumer-adoption (complete) until then. NIP-0002 Stages 2–4 (0-case greenfield genesis, n-case multi-repo tooling + membership registry, 04/05 coordination protocols) are deferred to phase 009, evidence-gated on this phase's re-pilot."
---

# Nizam Framework — Phase 008 Spec (0–n Project Spectrum, Stage 1: Consumer-Readiness)

**Status: ACTIVE — plan of record.** Phase `008-consumer-readiness` was authorized for
activation by the operator on 2026-07-21 (verbatim: **"Approved. Please proceed"**,
satisfying gate **H-PHASE-008**; recorded in `.agent/run_state.json` event `phase_activated`
before any feature execution, per the NDEBT-018 rule). It realizes **NIP-0002 (The 0–n
Project Spectrum)**, which the operator accepted on 2026-07-21 (gate **H-NIP**). Per
`methodology/00_planning.md`, the Planner-produced spec and the DAG-validated feature list
(`.agent/feature_list_008.json`) existed at proposal; the operator authorization completed the
activation triad. `docs/planning/manifest.json` carries `current_phase: 008-consumer-readiness`
with the phase-008 entry `status: in_progress`. Execution begins with the ungated DAG root
feature 065 (governance-root resolution).

## 1. Purpose

NIP-0002 requires the Ecosystem Engineering Cycle to span an ecosystem of **0 to n
projects**, and lays out a **staged, evidence-led** realization whose **Stage 1 is
"Consumer-readiness (the prerequisite)"** — the gate for every larger project count. The
phase-007 scratch-consumer pilot proved that even the **single-project (count-1)** case is
not yet consumer-ready: a clean Preflight against a real bootstrapped consumer is a hard
FAIL, and a baseline mislabels which framework it ran under (`ADR-004`; `NDEBT-027`/`-028`).

Phase 008 makes the single-project case genuinely consumer-ready and completes the "1" point
of the spectrum (greenfield *and* brownfield), then **re-pilots to prove it**. It deliberately
does **not** build the 0-case (greenfield genesis) or the n-case (multi-repo tooling) or the
`04`/`05` coordination protocols — those build *on top of* single-project tools that do not
yet work, so per the framework's governing rule (*no claim may be promoted beyond its
evidence*) they are deferred to phase 009 and prioritised from this phase's re-pilot evidence.
This is the same prove-then-build shape phase 007 used.

## 2. Scope

### 2.1 In scope (features 065–069)

- **065 — Governance-root resolution** (ADR-004 decision 1; `NDEBT-027`). Give the ecosystem
  tools a governance-root distinct from the repository root so they locate the injected
  `.nizam/` payload instead of assuming the framework-root layout, and treat that injected
  payload as expected rather than an untracked blocking finding. `--self-fixture`
  (governance-root == repo-root) stays the degenerate case, unchanged.
- **066 — Provenance-pin anchoring** (ADR-004 decision 2; `NDEBT-028`). A Baseline anchors
  `framework_references` to the injected provenance pin (`.nizam/provenance.json`
  `framework_version`/`tag`), not the consumer's HEAD; `repository_references` continues to
  anchor to the consumer HEAD, so the two categories record two distinct correct facts.
- **067 — Bootstrap commit-SHA pinning** (`NDEBT-033`). `bootstrap.sh` resolves the release
  tag to its commit SHA, persists both the tag and the resolved SHA in `provenance.json`, and
  `--verify-only` compares the SHA as well as the tag (rejecting a tag that has been moved),
  preserving the existing immutable-ref validation.
- **068 — Brownfield bootstrap reconciliation** (GIP §5.1; `NDEBT-032`, ex-conditional
  feature 062). Two distinct behaviours per GIP §5.1: (a) *file preservation* — a
  pre-existing root-level file that collides with an injected artifact (`CONTEXT.md`,
  `AGENTS.md`) is left intact and also copied to a deterministic, collision-safe renamed
  destination for hand reconciliation, never overwritten in place; (b) *CI merging* — a
  consumer's own CI configuration is added to, never replaced. This replaces the current
  atomic `.nizam/`-only replace and completes the 1-brownfield point of the spectrum.
- **069 — Re-pilot, prove, refine + phase close.** Re-run the full loop against a real,
  bootstrapped consumer with the fixed tools: a clean Preflight PASS, a correctly
  provenance-anchored baseline, SHA-verified provenance. Record residual friction as
  `NDEBT-*`, **refine and validate** the phase-009 candidate scope (NIP-0002 Stages 2–4)
  *this proposal already authored in `docs/planning/ROADMAP.md`* against the re-pilot
  evidence — confirming or re-ordering it, not re-authoring it — and close phase 008.

### 2.2 Out of scope (→ phase-009 candidate scope)

NIP-0002 Stages 2–4, deferred until Stage 1 is *proven* against real evidence:

- **The 0-case — greenfield genesis** (`NDEBT-030`): standing up a *new* project from nothing
  and bootstrapping the framework into it, with the scope registry's `incubating` partition
  modelling the count-0→1 transition.
- **The n-case — multi-repo tooling** (`NDEBT-031`): extending the ecosystem tools to iterate
  an ecosystem-membership registry (a set of repo-roots) instead of one `--repo-root`, and
  promoting `registry/scope_definition_patterns.md` to a required, validated membership
  artifact that sets `n`.
- **n-coordination protocols**: authoring `04_dependency_reconciliation.md` and
  `05_release_train_coordination.md` with their companion schemas.
- Cutting a framework release that carries the audit/compare tools (`NDEBT-029`) — a
  release-train action, handled when a release is next cut.

## 3. Preconditions

Features 065–068 are framework-internal (tool + bootstrap code + protocol/doc updates) and
executable without any external repo. Feature 069's re-pilot uses the same **scratch/
throwaway consumer** path phase 007 established (operator option c) — a fresh, minimal git
repo bootstrapped from a released tag — and needs no external repo access. The
`H-CONSUMER-UPGRADE` gate (defined in phase 007) is exercised again for that re-pilot
adoption, recorded before the bootstrap runs (the NDEBT-018 rule).

## 4. Functional Requirements

| FR | Requirement | Realized by |
|----|-------------|-------------|
| FR-01 | The ecosystem tools resolve a governance-root and run cleanly against a real bootstrapped consumer: a correct Preflight verdict (not a spurious FAIL from the injected `.nizam/` or framework-root-relative reference paths). | F-065 |
| FR-02 | A Baseline's `framework_references` records the injected framework pin (from `provenance.json`), not the consumer's HEAD; `repository_references` records the consumer HEAD. | F-066 |
| FR-03 | Bootstrap provenance records the release tag *and* its resolved commit SHA, and `--verify-only` rejects a tag that later resolves to a different commit. | F-067 |
| FR-04 | Bootstrapping into a consumer with pre-existing root-level `CONTEXT.md`/`AGENTS.md`/CI never silently overwrites them (GIP §5.1 rename-and-diff). | F-068 |
| FR-05 | The fixed single-project loop is proven end-to-end against a real bootstrapped consumer, and the next tranche (NIP-0002 Stages 2–4) is prioritised from that evidence. | F-069 |

## 5. Human Gates

Recorded per `docs/planning/operator_gates.md`. The pipeline records but never self-executes
a human gate.

1. **H-PHASE-008 — OUTSTANDING.** Authorize activation of this proposal (required before any
   feature enters contract negotiation). Its acceptance realizes the NIP-0002 selection.
2. **H-CONSUMER-UPGRADE — recurring, exercised again at F-069.** Approve the re-pilot
   consumer's adoption of the framework tag before the Bootstrap stage proceeds; recorded in
   `run_state` before the bootstrap runs (the NDEBT-018 rule), as in phase 007.

The four reserved gates (`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`, `H-CONSOLIDATION`, `H-GA`)
stay reserved — their protocols remain out of scope.

## 6. Dogfood and Validation Plan

- **Framework-internal (065–068):** `bash tools/validate.sh` stays green (15/15) with the
  tool/bootstrap changes; `tools/fixtures_self_test.sh` gains coverage of the governance-root
  option, the provenance-pin anchoring, the SHA-pinned provenance, and the rename-and-diff
  path; `tools/e2e_bootstrap_test.sh` continues to pass and gains the brownfield and
  SHA-verification cases. `ecosystem/00_ecosystem_bootstrap.md` §7 and `standard/GIP.md` §4
  are updated in lockstep with the provenance-shape change so C10 stays consistent.
- **Re-pilot (069):** inside a freshly bootstrapped scratch consumer, `ecosystem_preflight.py`
  now produces a clean Preflight PASS and a correctly-anchored baseline; the loop
  (Preflight → Baseline → Audit → Compare) runs end-to-end producing schema-valid artifacts;
  every residual friction point is a new `NDEBT-*` row. Success = the *fixed* single-project
  tools run against a real bootstrapped consumer with no hand-applied workaround.

## 7. Sequencing

`065 → 066 → 067` (the provenance-shape change in 066/067 is coordinated) and `068`
(independent bootstrap.sh work) run toward `069`, which depends on all four and proves them.
Features 065–068 can land as a framework-internal PR on activation; 069 re-pilots and closes
the phase. The 0-case/n-case/04-05 work (Section 2.2) is **already authored** as phase-009
candidate scope in `docs/planning/ROADMAP.md` by this proposal; F-069 **refines and validates**
that existing candidate against the re-pilot evidence (it does not re-author it), and no
Stage-2–4 work is begun in this phase.
