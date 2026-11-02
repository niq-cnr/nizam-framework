---
id: nip-0005-executable-claim-binding
title: "NIP-0005 — Executable Claim Binding"
description: "Proposes that every normative claim carry an executable binding, that no artifact define its own expected state, and that a receipt whose expectation is recomputed from the artifact be classified self-certifying rather than satisfying a gate."
version: 0.1.0
status: proposed
authoritative_source: docs/nips/NIP-0005-executable-claim-binding.md
change_log:
  - version: "0.1.0"
    date: "2026-11-02"
    summary: "Propose three amendments plus one constraint, derived from measured defects in a live Mandate 1 preparation where five document-review rounds did not converge and the first execution pass found eight blocking defects."
---

# NIP-0005 — Executable Claim Binding

## Status

**Proposed — awaiting H-NIP acceptance.** This document does not change any gate, does not reduce any
existing requirement, and is not active. It records a defect class observed in practice and a bounded
proposal for closing it. Nothing here is implemented in `.nizam/`; adoption requires operator acceptance
under H-NIP followed by a versioned release.

The author is an owner of this repository. That is not acceptance authority for a governance change, and
this NIP does not treat it as such.

## 1. The defect class

Nizam's gates are reviews of documents. Contracts, verdicts and receipts are the artifacts of record, and
Mode A, Mode B and QA judge those artifacts. No gate confronts a normative claim with an executable check
of the artifact that is supposed to satisfy it.

That leaves one defect class structurally undetectable: **the prose asserts a property, the executable
artifact does not implement it, and every gate passes because every gate read the prose.**

### 1.1 Measured evidence

Observed on a live preparation (a Rust-first execution kernel with a registry, DDL and five
specifications), not constructed for this NIP:

| Observation | Result |
| --- | --- |
| Independent document-review rounds before execution | 5 rounds, **non-converging** — 2, then 7, then 7 blocking findings; at round 3, **0 of 7** prior blockers were closed outright |
| First review that read the executable artifacts against the prose | **8 BLOCKING + 12 IMPORTANT** in a single pass |
| First run of a predicate harness over the normative acceptance predicates | **4 failures immediately**; 2 were genuine unmet predicates every prior round had asserted held |
| Normative predicates accounted for | **23 of 56**; **33 (59%)** were neither tested nor declared untestable, and the harness reported all of them as `SKIPPED` |

The third and fourth rows are the important ones. Coverage *appeared* measured: the harness printed a
result for every predicate. In fact the reporting conflated three different states — passed, failed, and
never considered — into two, and the third state was invisible.

The blocking findings were of one shape. A specification claimed that all external effects pass through a
governed gateway; the slice's only effect class ran in the least-trusted component with a standing
credential outside that gateway. A specification claimed a witness-backed projection; no code anywhere
wrote a witness record, so the projection read a permanent sentinel. A three-credential privilege model
was described in prose; the DDL contained no `GRANT`, no `REVOKE` and no roles.

