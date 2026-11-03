---
id: nip-0005-executable-claim-binding
title: "NIP-0005 — Executable Claim Binding"
description: "Proposes that every normative claim carry an executable binding, that no artifact define its own expected state, and that a receipt whose expectation is recomputed from the artifact be classified self-certifying rather than satisfying a gate."
version: 0.1.0
status: draft
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

### 1.2 Self-certifying evidence

A second, independent instance of the same defect appeared in the evidence mechanism itself:

- The candidate-freeze step **recomputed the expected candidate from the tree under test**, so
  regeneration was always sufficient to pass. It detected a *forgotten* regeneration, never a *malicious*
  one.
- The frozen file set was **derived from the live tree**, so the set could shrink and still pass.
- The candidate's integrity coverage excluded every architecture, specification, contract and backlog
  artifact — the deliverable itself. A 2.1 MB pinned evidence artifact could be altered and the
  integrity check still exited zero.

An artifact that derives its own expectation cannot detect its own defects. That is not a tuning problem;
it is a category error in the evidence model.

## 2. Proposal

Four amendments. A1–A3 are the mechanism; A4 is the constraint that keeps A1 from producing confident
nonsense.

### A1 — Every normative claim carries an executable binding

A normative claim is any statement that something *must* hold: a contract decision, an acceptance
predicate, an invariant, a required property. Each carries exactly one of:

- `verified_by: <check-id>` — an executable check that fails when the claim does not hold; or
- `unverifiable: {category, reason}` — a typed declaration that the claim cannot be checked
  mechanically, with a category from a closed set and a reason naming what would be needed.

A gate **fails** if any normative claim carries neither. Three states are required, not two:

```
PASS     the check ran and the claim held
FAIL     the check ran and the claim did not hold
UNBOUND  no check exists and no unverifiability is declared  -> GATE FAILURE
```

`UNBOUND` is not a skip. A run containing `UNBOUND` entries may not be cited as coverage evidence, and no
gate may move to pass on the strength of such a run. `UNVERIFIABLE` is a legitimate disposition and is
counted separately, because "we cannot test this and here is why" is an honest engineering position while
"nobody looked" is not.

### A2 — No artifact defines its own expected state

Expected state — file sets, digests, counts, predicate coverage — is authored as an artifact independent
of the thing under test, and pinned outside it.

- Regenerating a derived artifact is **never** verification. A mechanism that recomputes its expectation
  from the tree it is checking is a staleness check, and must be labelled as one rather than as a freeze.
- A set that defines its own membership cannot detect shrinkage. The expected membership is recorded
  externally and a difference is a failure requiring a deliberate update.
- Integrity coverage must include the deliverable. If the artifacts being claimed are outside the
  verified set, the claim is about something else.

### A3 — Receipts bind to an independently authored expectation

A receipt records that a command ran. That is not the same as establishing that the claim holds. A receipt
whose expectation is recomputed from the artifact under test is classified **`SELF_CERTIFYING`** and
cannot satisfy a gate, however green it is. To satisfy a gate, a receipt binds to an expectation authored
independently of the artifact it judges, and names that expectation.

### A4 — A bound check's expectation comes from the same authority as the claim

A1 alone is insufficient and there is direct evidence. A predicate case was authored to expect a refusal
code, `REFUSED:stale_generation`, that **does not exist in the registry that owns the refusal-code
vocabulary** — the registry defines twelve codes and that is not one of them. The case was therefore
unsatisfiable on the authority's own terms, and binding it would have produced a permanently failing check
attributed to the implementation rather than to the expectation.

So: a check's expected value derives from the same authority as the claim it verifies, never from the
artifact's current behaviour and never from the author's recollection of the specification.

## 3. Conformance

A repository conforms when a machine-readable claim-binding artifact exists and a gate check enforces it:

1. Every normative claim is enumerated with a stable ID and its source location.
2. Each carries `verified_by` or `unverifiable`.
3. `UNBOUND` count is zero.
4. Every `verified_by` resolves to a check that exists and can fail — demonstrated by a negative control
   that is executed and observed to report failure.
5. Every candidate/freeze mechanism in the repository carries an external expected-state artifact, and no
   gate accepts a recomputed expectation as verification.

Conformance is a property of a run, not of a document. A claim-binding artifact that has never been
executed against the gate is itself an unbound claim.

## 4. What this does not do

- It does not require every claim to be mechanically checkable. `UNVERIFIABLE` with a category and reason
  is a first-class, acceptable disposition.
- It does not replace human review. It makes review cheaper by removing the class of question that review
  is worst at — whether an executable artifact matches prose — so review can spend its budget on judgement.
- It does not mandate a tool, a schema, or a language. The three-state vocabulary and the independence
  requirement are the substance; the serialisation is an implementation choice.
- It does not assert that a bound check is a *good* check. A4 constrains where its expectation comes from;
  it cannot make a weak test strong.

## 5. Rollout

1. **H-NIP acceptance** of this scope, followed by a versioned release. No gate changes before that.
2. A claim-binding artifact adopted per repository, starting with one repository and one gate, so the
   mechanism is exercised before it is generalised.
3. The three-state reporting vocabulary adopted by any harness that reports coverage, because the
   two-state collapse is what hid 59% of a normative contract in the observation above.
4. Existing `SELF_CERTIFYING` receipts reclassified rather than deleted — they remain true records of
   commands that ran; they simply stop counting as gate evidence.

## 6. Open question

A2 makes the expected state explicit but does not make it *correct*. An externally authored expectation
pinned from today's state is still today's state, reviewed by whoever authored it. Whether a second
independence step is required — the expected state authored by a different actor from the artifact — is
left open, because the observation above had only one actor and cannot answer it.
