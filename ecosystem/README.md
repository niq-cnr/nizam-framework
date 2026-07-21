---
id: nizam-ecosystem-module
title: "Ecosystem Engineering Cycle"
description: "Reusable governance lifecycle for reconciling, auditing, planning, executing, and improving multi-repository software ecosystems."
version: 0.2.1
status: active
authoritative_source: ecosystem/README.md
change_log:
  - version: "0.2.1"
    date: "2026-07-18"
    summary: "Feature 048 (operator PR #21 review, finding 1): the module-navigation paragraph no longer calls 02/03/07 'Planned' — the four core protocols shipped at features 033-036; the five Planned documents (00/04/05/06/08) are the deferrable set. Prose re-synced with the table the 034-036 row-flips had left contradicting it."
  - version: "0.2.0"
    date: "2026-07-17"
    summary: "Completed the module index (handover F-002, phase 005-ecosystem-cycle): defined the canonical 10-stage lifecycle and added the module-navigation section for the 9 numbered protocol documents."
---

# Ecosystem Engineering Cycle

This module governs ecosystem-scale engineering work. It extends Nizam's repository-
local contract-first execution loop (methodology/01_execution.md) up one level, to the
scale of a multi-repository ecosystem: reconciling where every repository actually
stands, auditing engineering maturity with evidence, coordinating the next
cross-repository release train, and measuring progress over time -- all under the same
operator-gated discipline every other Nizam capability follows (see
docs/nips/NIP-0001-ecosystem-engineering-cycle.md, the accepted handover proposal this
module realizes).

## The Canonical Lifecycle

Every ecosystem engineering cycle moves through the same ten stages, in order, and then
repeats:

```text
Bootstrap -> Preflight -> Baseline -> Audit -> Plan -> Execute -> Verify -> Promote -> Compare -> Repeat
```

- **Bootstrap** -- a consumer repository adopts the framework (governance-inheritance-
  protocol, standard/GIP.md) so it can participate in the ecosystem cycle at all.
- **Preflight** -- before any reconciliation begins, confirm the working state is clean
  and safe to reason about: exactly one machine-readable verdict of PASS,
  PASS_WITH_EXCEPTIONS, or FAIL, with explicit blocking rules and an operator-exception
  rule for the PASS_WITH_EXCEPTIONS case.
- **Baseline** -- capture a point-in-time, immutable snapshot over framework,
  repository, dependency, CI, planning, and evidence references, every fact anchored to
  a stated revision or timestamp.
- **Audit** -- an evidence-first engineering assessment against a maturity model, never
  promoting a claim beyond the evidence that backs it.
- **Plan** -- turn approved audit findings into dependency-ordered, cross-repository
  work packets.
- **Execute** -- each repository agent carries out its share of the plan under its own,
  unmodified repository-local contract-first controls.
- **Verify** -- confirm the executed work actually satisfies its contracts and closes
  the findings it claimed to close.
- **Promote** -- a human-gated release step; the pipeline records but never
  self-executes a promotion or GA decision.
- **Compare** -- measure a new baseline or audit against the prior one, distinguishing
  new, resolved, reopened, and stale findings, with every score movement traceable to
  evidence.
- **Repeat** -- the cycle begins again from Preflight, so engineering progress is a
  continuous, evidence-backed loop rather than a one-time exercise.

## Module Navigation

The module comprises this index plus 9 numbered protocol documents, one per lifecycle
concern. Each is named below by its bare filename (never directory-qualified until it
actually exists in this repository, to avoid a dangling reference); the Shipped/Planned
annotation reflects this repository's actual, current state and is expected to change
as later features land their protocol document.

| # | Bare filename | Lifecycle concern | Status |
|---|----------------|--------------------|--------|
| 00 | `00_ecosystem_bootstrap.md` | Bootstrap | Shipped |
| 01 | `01_clean_state_preflight.md` | Preflight | Shipped |
| 02 | `02_evidence_baseline.md` | Baseline | Shipped |
| 03 | `03_engineering_audit.md` | Audit | Shipped |
| 04 | `04_dependency_reconciliation.md` | Plan (typed dependencies) | Planned |
| 05 | `05_release_train_coordination.md` | Promote (release-train coordination) | Planned |
| 06 | `06_simplification_review.md` | Repeat (recurring simplification) | Planned |
| 07 | `07_progress_comparison.md` | Compare | Shipped |
| 08 | `08_ga_gate.md` | Promote (GA gate) | Planned |

"Shipped" means the document already exists in this repository's `ecosystem/`
directory; "Planned" means it does not yet exist here. Five documents are Shipped.
The mandatory first-release surface's four core protocols
(preflight/baseline/audit/comparison, product_spec_005.md Sec 2.3) landed in phase
005-ecosystem-cycle: `01_clean_state_preflight.md` (feature 033), then
`02_evidence_baseline.md`, `03_engineering_audit.md`, and `07_progress_comparison.md`
(features 034-036). The Bootstrap-stage protocol `00_ecosystem_bootstrap.md` (the
lifecycle's entry stage) landed in phase 007-consumer-adoption (feature 060), wrapping
the Governance Inheritance Protocol (`standard/GIP.md`) and `bootstrap.sh`. The four
still-Planned documents — `04_dependency_reconciliation.md`,
`05_release_train_coordination.md`, `06_simplification_review.md`, and `08_ga_gate.md`
— are deferrable (product_spec_005.md Sec 2.3) and are prioritised from real
consumer-pilot evidence (phase 007) rather than authored speculatively.

## Capability Routing

This module's capabilities are registered in NIZAM.json's root capability index so an
agent can discover them without bulk-reading this directory. The single,
runtime-agnostic skill (tools/SKILL.md, tools/skill.json) remains the router for every
ecosystem capability; no runtime-specific ecosystem skills are introduced.

## Consumer Convention

Every execution of the cycle externalises its evidence by path rather than pasting
terminal output inline, under `.agent/reconciliation/<execution-id>/`,
`.agent/audits/<audit-id>/`, `.agent/trains/<train-id>/`, and
`.agent/evidence/<execution-id>/` in the consuming repository.
