---
id: nizam-ecosystem-progress-comparison
title: "Progress Comparison Protocol"
description: "The reusable protocol for comparing two approved baselines or audits: distinguishing new, resolved, reopened, and stale findings, closing a resolved finding only with closure evidence, refusing to silently reuse stale evidence, and making every score movement traceable to evidence."
version: 0.1.1
status: active
authoritative_source: ecosystem/07_progress_comparison.md
change_log:
  - version: "0.1.1"
    date: "2026-07-18"
    summary: "Feature 048 (operator PR #21 review, finding 4): both references to the deferred delta schema now use the module's bare-filename convention (audit_delta.schema.json, planned under schema/) instead of a directory-qualified path that dangles until the schema ships."
---

# Progress Comparison Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's
Compare step -- how an agent or engineering team measures progress between
two points in the ecosystem engineering cycle. A comparison never operates
on a single snapshot: it takes two already-approved reference points and
produces a classified, evidence-anchored account of what changed between
them, so engineering progress is a continuous, evidence-backed loop
(`ecosystem/README.md`'s canonical lifecycle) rather than a one-time
exercise.

Consumers extend this protocol with their own repository- and
ecosystem-specific finding categories, scoring weights, and thresholds; they
do not redefine its four finding-state transition classes, its
closure-only-with-evidence rule, its stale-evidence non-reuse rule, or its
score-movement traceability requirement. Those four mechanics are defined
once, here, exactly as `ecosystem/01_clean_state_preflight.md` is the single
source of truth for the preflight verdict vocabulary and
`ecosystem/02_evidence_baseline.md` is the single source of truth for the six
baseline field categories.

## 2. Inputs

A comparison requires exactly two approved baselines or audits as its
inputs: an earlier reference point and a later one, each itself the product
of `ecosystem/02_evidence_baseline.md`'s Baseline step or
`ecosystem/03_engineering_audit.md`'s Audit step for its own execution. A
comparison with no baseline or audit on one or both sides is not a valid
comparison, and MUST NOT be run: there is nothing yet to measure progress
against.

Both inputs MUST already be captured and approved before the comparison
begins -- a comparison never captures a baseline or runs an audit itself,
and never substitutes an in-progress or unapproved execution for either
side. The earlier and later inputs need not be adjacent executions of the
cycle; a comparison MAY span any two approved reference points, provided
both sides are unambiguously identified per their own artifact's revision
and timestamp anchors (`ecosystem/02_evidence_baseline.md` Section 4).

## 3. Finding-State Transitions

Every finding tracked across the two compared executions is classified into
exactly one of four transition classes, and every finding present in either
input MUST receive exactly one of them:

- `new` -- present in the later execution's findings, absent from the
  earlier one. A finding not seen before this comparison's later side.
- `resolved` -- present in the earlier execution, absent from the later one,
  and closed per the closure-only-with-evidence rule (Section 4).
- `reopened` -- previously classified `resolved` in an earlier comparison,
  now present again in the later execution's findings.
- `stale` -- present in both executions, but the evidence backing it is no
  longer current per the stale-evidence non-reuse rule (Section 5).

The comparison distinguishes these four classes explicitly and reports each
finding under exactly one of them; a finding left unclassified, or assigned
to more than one class at once, is not a valid comparison result.

## 4. Closure-Only-With-Evidence Rule

A finding is classified `resolved` (Section 3) only with closure evidence:
a dated, path-referenced artifact demonstrating that the underlying
condition the finding described no longer holds. A finding MUST NOT be
classified `resolved` on the basis of its mere absence from the later
execution's scan alone -- absence from a later scan is consistent with the
condition being fixed, but is equally consistent with the later scan simply
not having looked, and closure evidence is what distinguishes the two.

This mirrors the framework's evidence-first discipline
(`ecosystem/03_engineering_audit.md` Section 3's evidence hierarchy): a
comparison tool MUST refuse to emit a `resolved` classification for any
finding whose closure evidence path is missing, unreadable, or does not
resolve to an existing artifact.

## 5. Stale-Evidence Non-Reuse Rule

Evidence backing a finding still present in the later execution
MUST NOT be silently reused as current evidence in this comparison once
that evidence is genuinely stale relative to the later execution's own
revision and timestamp anchors (`ecosystem/02_evidence_baseline.md` Section
4). A finding whose only backing evidence predates the later execution's
baseline or audit, with no fresh confirmation captured at or after that
execution, is flagged `stale` (Section 3) rather than silently carried
forward as if it had been freshly re-confirmed.

A comparison tool MUST NOT treat a finding's continued absence of contrary
evidence as confirmation that its prior evidence still holds; the `stale`
classification exists precisely so that gap is reported, not papered over.

## 6. Score-Movement Traceability

Every score movement between the two compared executions is traceable to
evidence: any change in an aggregate engineering score cites the specific
`new`, `resolved`, `reopened`, and `stale` findings responsible for the
movement, each in turn citing its own evidence per
`ecosystem/03_engineering_audit.md` Section 3's evidence hierarchy. A score
movement with no cited findings, or citing findings with no evidence of
their own, is not traceable and MUST NOT be reported as if it were.

This traceability requirement exists so a later reviewer can always answer
"why did the score move" by following the chain from the score, to the
findings, to the evidence -- never by trusting an aggregate number in
isolation.

## 7. Comparison Artifact

Every comparison run MUST emit a schema-valid, machine-readable delta
artifact at:

```text
.agent/audits/<audit-id>/delta.json
```

where `<audit-id>` is the unique identifier of the ecosystem-cycle audit or
comparison execution, per the framework's Artifact Locations convention
(`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`). The artifact's shape
(the four finding-state transition classes of Section 3, the closure
evidence and stale-evidence references of Sections 4-5, and the
score-movement citations of Section 6) is defined by an optional
`audit_delta.schema.json` (planned under `schema/`); per
`product_spec_005.md` Section 2.3, this schema is deferrable within the
minimal-viable release and is not yet present in this repository. This protocol governs the artifact's required
semantics regardless of whether that schema has landed; it does not itself
define the JSON Schema.

Evidence backing the comparison (raw tool output, logs, or intermediate
collection results) is externalised by path under
`.agent/evidence/<execution-id>/`, per the framework's Evidence Capture
Convention (`methodology/04_tool_driven_state.md` Section 5) -- never
pasted inline into the delta artifact or into a chat transcript.

## 8. References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` -- the accepted NIP
  defining the Compare stage, the Artifact Locations, and the Dogfood
  Requirement this protocol implements.
- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is one step of.
- `ecosystem/02_evidence_baseline.md` -- one of the two protocols a
  comparison's inputs may be drawn from; also the source of the revision
  and timestamp anchoring rule Section 5 relies on.
- `ecosystem/03_engineering_audit.md` -- the other protocol a comparison's
  inputs may be drawn from; also the source of the evidence hierarchy
  Sections 4 and 6 cite.
- `methodology/04_tool_driven_state.md` -- the Evidence Capture Convention
  this protocol's evidence externalisation follows.
- `methodology/03_circuit_breaker.md` -- the house pattern this document's
  structure, tone, and immutability discipline follow.
- `audit_delta.schema.json` -- the optional, deferrable machine-readable
  schema for the delta artifact this protocol describes (planned under
  `schema/`; per `product_spec_005.md` Section 2.3, not scheduled in this
  phase's execution order; not yet present at the time this protocol was
  authored).
