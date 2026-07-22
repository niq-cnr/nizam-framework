---
id: nizam-ecosystem-release-train-coordination
title: "Release-Train Coordination Protocol"
description: "The reusable Promote-stage protocol: consumes an operator-authorized reconciliation plan and admits its work packets into a cross-repository release train, recording per-repository train membership and requiring that every admitted packet traces to a plan packet -- an orphan admission is a first-class recorded finding forcing a non-PASS train verdict. The operator gate H-TRAIN-ENTRY authorizes admission; the pipeline records but never self-executes a promotion or the train's departure."
tags: [ecosystem-cycle, promote, release-train, cross-repo, phase-011]
version: 0.1.0
status: active
authoritative_source: ecosystem/05_release_train_coordination.md
change_log:
  - version: "0.1.0"
    date: "2026-07-22"
    summary: "Initial authoring (phase 011 feature 081; NIP-0002 Stage 4, the n-coordination protocols; NDEBT-035). Defines the ecosystem lifecycle's Promote stage -- admitting an authorized reconciliation plan's (ecosystem/04_dependency_reconciliation.md) work packets into a cross-repository release train, under the trace-to-plan invariant, gated by the operator decision H-TRAIN-ENTRY (defined in this feature in docs/planning/operator_gates.md). House structure mirrors ecosystem/03_engineering_audit.md and its Plan-stage sibling ecosystem/04. Names schema/release_train_manifest.schema.json as the machine-readable manifest shape."
---

# Release-Train Coordination Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's
**Promote** step -- the cross-repository release-train coordination an agent or
engineering team performs once a reconciliation plan
(`ecosystem/04_dependency_reconciliation.md`) has been produced and its planning
authority approved. A release train never departs on speculation: every packet
it admits traces to a packet in the reconciliation plan it was built from, and
the train never promotes on the pipeline's own authority -- only a recorded
operator decision (`H-TRAIN-ENTRY`) admits work and lets the train depart.

Consumers extend this protocol with their own train cadence, repository
release-ordering conventions, and versioning policy; they do not redefine its
input contract, its manifest shape, its trace-to-plan invariant, or its operator
gate. Those four mechanics are defined once, here, exactly as
`ecosystem/04_dependency_reconciliation.md` is the single source of truth for the
Plan stage and `ecosystem/03_engineering_audit.md` is the single source of truth
for the audit's evidence hierarchy.

## 2. When to Run

Release-train coordination MUST NOT begin until:

- A reconciliation plan has been produced with a `PASS` plan verdict, per
  `ecosystem/04_dependency_reconciliation.md` Section 4. A train is never built
  from a `FAIL` plan (one containing a dependency cycle) -- an unordered plan has
  no admissible sequence.
- The plan's planning authority has been approved by the operator
  (`H-PLANNING-AUTHORITY`, `ecosystem/04_dependency_reconciliation.md` Section 5).
  A train never admits a plan whose authority no operator has accepted.

The Promote stage consumes the authorized reconciliation plan as its required
input: the plan supplies the ordered work packets, the repositories they target,
and the dependency order the train's admission must respect. This is the train's
entry condition -- a train built without an authorized, `PASS` plan is not a
coordinated release, it is an uncoordinated push.

## 3. The Release-Train Manifest

A release train is recorded as a **manifest** that:

- names the reconciliation plan it was built from (`source_plan`) and carries the
  plan's packet ids (`plan_packets`) as provenance, so admission can be checked
  against them;
- records the **admitted packets** (`admitted_packets`) -- the subset of plan
  packets entering this train -- each naming the repository it targets;
- records **per-repository train membership** (`train_members`) -- the
  repositories participating in this train's departure;
- records whether the operator's admission decision has been captured
  (`entry_gate_recorded`, Section 5) and the single train verdict
  (`train_verdict`).

The manifest is a *record* of a coordinated promotion, not the promotion itself:
the actual release of each repository is carried out by that repository's own,
unmodified release controls (`methodology/06_release_train.md`), exactly as
`ecosystem/README.md`'s Promote stage describes. This protocol governs how the
train is recorded and gated; it does not itself cut a release.

## 4. The Trace-to-Plan Invariant

Every admitted packet MUST **trace to a plan packet**: each `admitted_packets`
entry's `id` MUST appear in the manifest's `plan_packets` set. An admitted packet
with no plan origin is an **orphan** -- a promotion of work the reconciliation
plan never planned -- and is a first-class recorded finding
(`orphan_findings`) that forces the train verdict to `FAIL`: a manifest that
admits an orphan is not a valid coordinated release and MUST NOT be emitted as
`PASS`. This mirrors the Plan stage's topological-order invariant
(`ecosystem/04_dependency_reconciliation.md` Section 4) at the admission layer --
a coordinator who wants a `PASS` train admits only packets the plan authorized,
never work smuggled in outside it. The train verdict is exactly one of:

- `PASS` -- every admitted packet traces to a plan packet, and the operator's
  admission decision (`H-TRAIN-ENTRY`) is recorded.
- `FAIL` -- at least one admitted packet is an orphan (recorded in
  `orphan_findings`), or the admission decision is not recorded.

## 5. Operator Gate — H-TRAIN-ENTRY

Admitting work into a cross-repository release train is an operator decision, not
a pipeline one. The gate **H-TRAIN-ENTRY** (`docs/planning/operator_gates.md`)
authorizes the admission of reconciled work packets into a train before the train
may depart. The pipeline **records but never self-executes** this authorization:
a tool may build and validate a manifest, but it MUST refuse to emit a `PASS`
train without the recorded operator decision (`entry_gate_recorded`), and it never
itself promotes or departs the train, exactly as `ecosystem/README.md`'s Promote
stage records but never self-executes a promotion or GA decision. The gate is
recorded before the train is admitted, per the framework's
gate-decision-before-execution rule (`NDEBT-018`).

## 6. Release-Train Artifact

Every release-train coordination run MUST emit a schema-valid, machine-readable
manifest artifact at:

```text
.agent/trains/<train-id>/manifest.json
```

where `<train-id>` is the unique identifier of the cross-repository release
train, per `ecosystem/README.md`'s Consumer Convention. The manifest artifact's
shape (the source plan and its packet ids, the admitted packets, the
per-repository train membership, the recorded-admission flag, the train verdict,
and any recorded orphan findings) is defined by
`schema/release_train_manifest.schema.json`. This protocol governs the artifact's
required semantics; it does not itself define the JSON Schema.

Evidence backing the train (the authorized plan consumed, the per-repository
release records) is externalised by path under `.agent/evidence/<execution-id>/`,
per the framework's Evidence Capture Convention
(`methodology/04_tool_driven_state.md` Section 5) -- never pasted inline into the
manifest or a chat transcript.

## 7. References

- `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` -- the accepted NIP whose
  Stage 4 (n-coordination protocols) this document realizes; the Promote stage is
  where release-train entry genuinely lives.
- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is the Promote step of.
- `ecosystem/04_dependency_reconciliation.md` -- the preceding lifecycle step: no
  train is built except from an authorized, `PASS` reconciliation plan.
- `schema/reconciliation_plan.schema.json` -- the schema of the plan this
  protocol admits; the manifest's `plan_packets` trace back to it.
- `schema/release_train_manifest.schema.json` -- the machine-readable schema for
  the manifest artifact this protocol requires.
- `docs/planning/operator_gates.md` -- the registry recording the H-TRAIN-ENTRY
  gate this protocol's Section 5 defines.
- `methodology/06_release_train.md` -- the repository-local release controls the
  actual per-repository promotion follows; this protocol coordinates, it does not
  replace them.
- `methodology/03_circuit_breaker.md` -- the house pattern this document's
  structure, tone, and immutability discipline follow.
