---
id: nizam-operator-gates
title: "Operator Gate Registry — nizam-framework"
description: "The single informational registry of every operator (human) gate the framework recognizes, its scope, and its current disposition; authoritative gate definitions live in the phase specifications this registry cites."
version: 0.7.0
status: active
authoritative_source: docs/planning/operator_gates.md
change_log:
  - version: "0.7.0"
    date: "2026-07-21"
    summary: "H-CONSUMER-UPGRADE disposition corrected (PR #45 review): exercise (2), the phase-008 feature-069 re-pilot, is reclassified as a PRE-RELEASE pilot, not a released-tag adoption — it bootstrapped an ephemeral tag on the phase-008 branch HEAD (the fixed 065–068 tools are unreleased), so it exercised the gate's decision mechanics ahead of a release but does not match the gate's defined scope (adoption of a released immutable tag). Only exercise (1), the phase-007 pilot against released tag v0.8.0, is the canonical released-tag case; a released-tag adoption of the fixed framework stays outstanding until the next H-FRAMEWORK-RELEASE."
  - version: "0.6.0"
    date: "2026-07-21"
    summary: "H-CONSUMER-UPGRADE exercised a second time (phase 008 feature 069 re-pilot adoption of the fixed framework, proving pilot findings A/B resolved). The disposition cell now records both exercises (phase-007 pilot v0.8.0; phase-008 re-pilot)."
  - version: "0.5.0"
    date: "2026-07-21"
    summary: "H-PHASE-008 SATISFIED — operator authorized activation of phase 008 (0-n Project Spectrum, Stage 1: Consumer-Readiness) with 'Approved. Please proceed', realizing NIP-0002's Stage-1 selection. Generalized the former single H-PHASE-006 row into the recurring per-phase-activation class H-PHASE-NNN, recording the 006/007/008 dispositions in one row (each recorded in run_state.phase_activated before feature execution, per NDEBT-018) rather than accreting near-duplicate per-phase rows."
  - version: "0.4.0"
    date: "2026-07-21"
    summary: "H-NIP exercised a second time: operator accepted NIP-0002 (The 0–n Project Spectrum, verbatim 'NIP-0002 is accepted'), selecting phase 008 as its realization (the first exercise accepted NIP-0001 -> phase 005 on 2026-07-17). Row reworded to record H-NIP as recurring (once per NIP) and to make explicit that selection is not activation — the selected phase still needs its own H-PHASE-NNN. Recorded alongside .agent/run_state.json (event operator_gate_decision)."
  - version: "0.3.0"
    date: "2026-07-21"
    summary: "Phase-007 feature 063: H-CONSUMER-UPGRADE disposition rolled DEFINED/OUTSTANDING -> EXERCISED. First exercise 2026-07-21 — the operator authorized adopting a scratch/throwaway consumer against released tag v0.8.0 for the first pilot; recorded in .agent/run_state.json (event operator_gate_decision) before the bootstrap ran, per the NDEBT-018 rule. The gate is recurring, so it is outstanding again at the next adoption/upgrade."
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Phase-007 feature 061: H-CONSUMER-UPGRADE is DEFINED and moved from the reserved table (Section 2) into the decided-and-active table (Section 1) with scope, trigger, and disposition semantics — it approves a consumer repository's adoption of, or upgrade to, a newly released immutable framework tag at the Bootstrap stage (ecosystem/00_ecosystem_bootstrap.md), record-but-never-self-execute. Status DEFINED/OUTSTANDING, awaiting its first exercise at the first external-consumer pilot (feature 063). The four sibling gates (H-PLANNING-AUTHORITY, H-TRAIN-ENTRY, H-CONSOLIDATION, H-GA) stay reserved. Section 1 retitled to 'Decided and active gates' since it now carries a defined-but-not-yet-exercised gate."
  - version: "0.1.0"
    date: "2026-07-20"
    summary: "Initial registry. Consolidates the operator (H-) gates that until now lived only inline in the phase specifications (.agent/product_spec_005.md Sec 8, .agent/product_spec_006.md, docs/planning/ROADMAP.md dispositions) into one informational ledger, fulfilling the canonical `operator_gates.md` reference that .agent/product_spec_005.md Sec 8 has pointed at since phase 005. Records the eight decided phase-005/006 gates with their dispositions and lists the five deferred successor-phase gates by name and reserved status only, without inventing semantics the successor consumer-adoption phase has not yet decided. Informational: it records dispositions, it does not define or execute them."
---

# Operator Gate Registry

An **operator gate** (an "H-gate") is a decision the framework reserves for a
human operator: it is never taken by an agent and never self-executed by the
pipeline. As the ecosystem cycle puts it, *the pipeline records but never
self-executes a human gate* (`.agent/product_spec_005.md` Sec 8;
`ecosystem/README.md`'s Promote stage is the canonical example — a human-gated
release step the pipeline records but never performs).

This document is **informational**. It is the single place to see every gate
the framework recognizes and where each one currently stands. It does **not**
define gates or grant authority: the authoritative definition of each gate
lives in the phase specification that introduced it (cited per row), and the
authoritative record of a gate *decision or disposition* is the operator's own
recorded decision. For an **approval**, that is typically a `run_state.json`
`operator_gate_decision` event, verbatim operator text, or a signed release tag.
For a **non-approval outcome** — a gate recorded `NOT REQUIRED` because its
trigger never arose, or one subsumed by a broader operator decision — the
binding record is the disposition written into the cited phase specification's
change_log or `docs/planning/ROADMAP.md`. Either way the record lives outside
this registry.

A phase specification is authoritative for a gate's **definition and scope**; a
gate's **current disposition**, however, follows the *latest* recorded operator
decision, which supersedes any earlier point-in-time status. This distinction
matters because `.agent/product_spec_005.md` Sec 8 records `H-FRAMEWORK-SCOPE`,
`H-DOGFOOD-EXCEPTION`, `H-FRAMEWORK-RELEASE`, and `H-RISK` as `OUTSTANDING` — that
is their status *as of phase-005 activation*, not a standing claim. The final
dispositions in Section 1 below (subsumed / exercised / executed / not required)
are the *later* operator records that superseded that activation-time snapshot:
the v0.7.0 and v0.8.0 release tags and `docs/planning/ROADMAP.md`'s phase-005/006
completion entries. So where this registry and a phase spec disagree on a gate's
**definition**, the phase spec wins; where they differ on a gate's **status**,
the later operator record (cited in the Disposition column) is current.

## 1. Decided and active gates

Every gate below has been dispositioned, or — for a newly defined gate not yet
exercised — has a defined scope and a stated current status. Recurring gates
(noted as such) are re-satisfied each time their trigger recurs; this table records
their most recent disposition, not a claim that they never fire again.

| Gate | Scope — what the operator decides | Introduced | Disposition |
|------|-----------------------------------|------------|-------------|
| `H-NIP` | Accept a NIP (handover proposal) as the plan of record and **select** the phase that realizes it (recurring, once per NIP; selection is not activation — the selected phase still needs its own `H-PHASE-NNN`). | `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`; `docs/nips/NIP-0002-zero-to-n-project-spectrum.md`; `.agent/product_spec_005.md` Sec 8 | SATISFIED 2026-07-17 — operator accepted NIP-0001 ("approved. expedite."), selecting phase 005. EXERCISED AGAIN 2026-07-21 — operator accepted NIP-0002 ("NIP-0002 is accepted"), selecting phase 008 (The 0–n Project Spectrum); phase-008 authoring + activation (`H-PHASE-008`) is the next cycle. |
| `H-PHASE-NNN` | Authorize activation of a proposed phase before any feature starts (the recurring per-phase activation class; `H-NIP` was phase 005's activation gate). | `.agent/product_spec_006.md`..`product_spec_008.md` gates | SATISFIED per phase: **006** 2026-07-19 ("Approved. Proceed with the logical next steps."); **007** 2026-07-20 ("Authorized to activate now"); **008** 2026-07-21 ("Approved. Please proceed", gate H-PHASE-008 — activates NIP-0002's Stage 1). Each recorded in `.agent/run_state.json` (`phase_activated`) before any feature execution, per NDEBT-018. |
| `H-FRAMEWORK-SCOPE` | Approve the minimum-viable capability of a release; prevent optional tooling/schemas from expanding the first release. | `.agent/product_spec_005.md` Sec 8 | DISPOSITIONED 2026-07-18 — subsumed by the `H-NIP` activation decision rather than taken separately (recorded plainly in `docs/planning/ROADMAP.md`, not backfilled). |
| `H-DOGFOOD-EXCEPTION` | Approve a `PASS_WITH_EXCEPTIONS` framework preflight result before execution continues (recurring, per exception). | `.agent/product_spec_005.md` Sec 8; `ecosystem/01_clean_state_preflight.md` Sec 5 | EXERCISED twice in phase 005, both operator-approved. |
| `H-RISK` | Accept residual P1 engineering risk surfaced by an audit; agents may never accept risk on a human's behalf (recurring, per residual risk). | `.agent/product_spec_005.md` Sec 8; `ecosystem/01_clean_state_preflight.md` Sec 4 | NOT REQUIRED in phase 005 — no residual P1 risk surfaced. |
| `H-PAYLOAD-CONTRACT` | Decide the injected-payload / methodology contract (which directories the bootstrap payload carries). | `.agent/product_spec_006.md` gates (F-051) | SATISFIED in phase 006 (feature 051). |
| `H-CONSTITUTIONAL` | The mechanize-or-descope decision for the constitutional-policy surface (per document: mechanize into a validator check, or mark consumer-aspirational). | `.agent/product_spec_006.md` gates (F-058); `docs/planning/ROADMAP.md` Track 3 | RESOLVED 2026-07-20 — two surfaces mechanized (validate.sh C14/C15), seven marked consumer-aspirational. |
| `H-FRAMEWORK-RELEASE` | Approve the semantic version, changelog, migration notes, and tag creation for a framework release (recurring, per release). | `.agent/product_spec_005.md` Sec 8; `methodology/06_release_train.md` | EXECUTED 2026-07-18 (v0.7.0) and 2026-07-20 (v0.8.0, phase 006 feature 059) — operator-signed tags. |
| `H-CONSUMER-UPGRADE` | Approve a consumer repository's adoption of, or upgrade to, a newly released **immutable framework tag** at the Bootstrap stage — the pinned tag the consumer will inherit and run the cycle under. The pipeline records the adoption decision; it never adopts on a human's behalf (recurring, per adoption/upgrade). | `.agent/product_spec_007.md`; `ecosystem/00_ecosystem_bootstrap.md` Sec 2 | DEFINED 2026-07-20 (phase 007, feature 061). EXERCISED once against a released tag and once as a pre-release pilot: (1) 2026-07-21 (phase 007, feature 063) — the **canonical case** matching this gate's defined scope: a scratch/throwaway consumer adopting the **released immutable tag** `v0.8.0`; (2) 2026-07-21 (phase 008, feature 069) — a **pre-release pilot, NOT a released-tag adoption**: the re-pilot bootstrapped an *ephemeral tag on the phase-008 branch HEAD* (the fixed 065–068 tools are unreleased), exercising the same operator-decision mechanics ahead of a release to prove findings A/B resolved. A released-tag adoption of the *fixed* framework remains outstanding until the next `H-FRAMEWORK-RELEASE` cuts a tag carrying the fixes. Each recorded in `.agent/run_state.json` (event `operator_gate_decision`) before the bootstrap ran, per the NDEBT-018 rule. Recurring: outstanding again at the next adoption/upgrade. |

## 2. Reserved gates (deferred to the successor consumer-adoption phase)

The four gates below are named in `.agent/product_spec_005.md` Sec 8 as belonging
to the successor consumer-adoption programme phase (a fifth, `H-CONSUMER-UPGRADE`,
was defined in phase 007 and now lives in Section 1). They are **reserved names
only**: their scope, trigger, and disposition are a later phase's to define, and
this registry deliberately records no invented semantics for them. Each is paired
below with the lifecycle stage (`ecosystem/README.md`) it is expected to guard,
purely to orient the reader — not as a definition.

| Gate | Expected lifecycle stage | Status |
|------|--------------------------|--------|
| `H-PLANNING-AUTHORITY` | Plan (stage 04) — reconciling planning authority across repositories. | RESERVED — definition deferred to the successor consumer-adoption phase. |
| `H-TRAIN-ENTRY` | Promote (stage 05) — admitting work into a cross-repository release train. | RESERVED — definition deferred to the successor consumer-adoption phase. |
| `H-CONSOLIDATION` | Repeat (stage 06) — authorizing an actual simplification/consolidation (the simplification review never consolidates automatically). | RESERVED — definition deferred to the successor consumer-adoption phase. |
| `H-GA` | Promote (stage 08) — declaring general availability; the framework must never auto-declare GA. | RESERVED — definition deferred to the successor consumer-adoption phase. |

## 3. Notes

- **Recurring vs one-shot.** `H-NIP` / `H-PHASE-NNN` (activation), `H-FRAMEWORK-RELEASE`
  (release), `H-DOGFOOD-EXCEPTION` (per `PASS_WITH_EXCEPTIONS`), and `H-RISK`
  (per residual risk) are recurring classes — they fire again whenever their
  trigger recurs. The table records each one's latest disposition.
- **This registry is not a gate.** Adding, editing, or reconciling a row here
  records an already-taken operator decision; it never constitutes one.
- **Provenance of a disposition.** The binding record for any row above is the
  operator's own recorded decision — for an approval, a `run_state.json`
  `operator_gate_decision` event, verbatim operator text in the cited spec's
  change_log, or a signed release tag; for a non-approval outcome (a `NOT
  REQUIRED` gate that never fired, or one subsumed by a broader decision), the
  disposition recorded in the cited phase spec or `docs/planning/ROADMAP.md` —
  never this summary row.

## 4. References

- `.agent/product_spec_005.md` Sec 8 — the phase-005 human-gate list this
  registry consolidates, and the canonical `operator_gates.md` reference it
  fulfills.
- `.agent/product_spec_006.md` — the phase-006 gates (`H-PHASE-006`,
  `H-PAYLOAD-CONTRACT`, `H-CONSTITUTIONAL`, `H-FRAMEWORK-RELEASE`).
- `.agent/product_spec_007.md` — the phase-007 gates (`H-PHASE-007` and the
  now-defined `H-CONSUMER-UPGRADE`, guarding the Bootstrap stage
  `ecosystem/00_ecosystem_bootstrap.md`).
- `docs/planning/ROADMAP.md` — the durable forward-planning surface recording
  the outstanding and dispositioned human gates.
- `ecosystem/README.md` — the canonical ecosystem lifecycle whose Promote
  stage is the archetypal human-gated step.
- `methodology/06_release_train.md` — the release mechanics `H-FRAMEWORK-RELEASE`
  gates.
