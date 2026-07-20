---
id: nizam-operator-gates
title: "Operator Gate Registry — nizam-framework"
description: "The single informational registry of every operator (human) gate the framework recognizes, its scope, and its current disposition; authoritative gate definitions live in the phase specifications this registry cites."
version: 0.1.0
status: active
authoritative_source: docs/planning/operator_gates.md
change_log:
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
this registry; where this registry and a phase spec disagree, the phase spec
wins.

## 1. Decided gates (phases 005–006)

Every gate below has been dispositioned. Recurring gates (noted as such) are
re-satisfied each time their trigger recurs — this table records their most
recent disposition, not a claim that they never fire again.

| Gate | Scope — what the operator decides | Introduced | Disposition |
|------|-----------------------------------|------------|-------------|
| `H-NIP` | Accept a NIP (handover proposal) as the plan of record and authorize phase activation. | `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`; `.agent/product_spec_005.md` Sec 8 | SATISFIED 2026-07-17 — operator accepted NIP-0001 ("approved. expedite."), activating phase 005. |
| `H-PHASE-006` | Authorize activation of a proposed phase before any feature starts (the per-phase activation class; `H-NIP` was phase 005's activation gate). | `.agent/product_spec_006.md` gates | SATISFIED 2026-07-19 — operator authorized phase 006 ("Approved. Proceed with the logical next steps."). |
| `H-FRAMEWORK-SCOPE` | Approve the minimum-viable capability of a release; prevent optional tooling/schemas from expanding the first release. | `.agent/product_spec_005.md` Sec 8 | DISPOSITIONED 2026-07-18 — subsumed by the `H-NIP` activation decision rather than taken separately (recorded plainly in `docs/planning/ROADMAP.md`, not backfilled). |
| `H-DOGFOOD-EXCEPTION` | Approve a `PASS_WITH_EXCEPTIONS` framework preflight result before execution continues (recurring, per exception). | `.agent/product_spec_005.md` Sec 8; `ecosystem/01_clean_state_preflight.md` Sec 5 | EXERCISED twice in phase 005, both operator-approved. |
| `H-RISK` | Accept residual P1 engineering risk surfaced by an audit; agents may never accept risk on a human's behalf (recurring, per residual risk). | `.agent/product_spec_005.md` Sec 8; `ecosystem/01_clean_state_preflight.md` Sec 4 | NOT REQUIRED in phase 005 — no residual P1 risk surfaced. |
| `H-PAYLOAD-CONTRACT` | Decide the injected-payload / methodology contract (which directories the bootstrap payload carries). | `.agent/product_spec_006.md` gates (F-051) | SATISFIED in phase 006 (feature 051). |
| `H-CONSTITUTIONAL` | The mechanize-or-descope decision for the constitutional-policy surface (per document: mechanize into a validator check, or mark consumer-aspirational). | `.agent/product_spec_006.md` gates (F-058); `docs/planning/ROADMAP.md` Track 3 | RESOLVED 2026-07-20 — two surfaces mechanized (validate.sh C14/C15), seven marked consumer-aspirational. |
| `H-FRAMEWORK-RELEASE` | Approve the semantic version, changelog, migration notes, and tag creation for a framework release (recurring, per release). | `.agent/product_spec_005.md` Sec 8; `methodology/06_release_train.md` | EXECUTED 2026-07-18 (v0.7.0) and 2026-07-20 (v0.8.0, phase 006 feature 059) — operator-signed tags. |

## 2. Reserved gates (deferred to the successor consumer-adoption phase)

The five gates below are named in `.agent/product_spec_005.md` Sec 8 as belonging
to the successor consumer-adoption programme phase. They are **reserved names
only**: their scope, trigger, and disposition are the successor phase's to
define, and this registry deliberately records no invented semantics for them.
Each is paired below with the lifecycle stage (`ecosystem/README.md`) it is
expected to guard, purely to orient the reader — not as a definition.

| Gate | Expected lifecycle stage | Status |
|------|--------------------------|--------|
| `H-CONSUMER-UPGRADE` | Bootstrap (stage 00) — a consumer repository adopting a newly released framework tag. | RESERVED — definition deferred to the successor consumer-adoption phase. |
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
- `docs/planning/ROADMAP.md` — the durable forward-planning surface recording
  the outstanding and dispositioned human gates.
- `ecosystem/README.md` — the canonical ecosystem lifecycle whose Promote
  stage is the archetypal human-gated step.
- `methodology/06_release_train.md` — the release mechanics `H-FRAMEWORK-RELEASE`
  gates.
