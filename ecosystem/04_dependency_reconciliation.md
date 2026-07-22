---
id: nizam-ecosystem-dependency-reconciliation
title: "Dependency Reconciliation Protocol"
description: "The reusable Plan-stage protocol: consumes the current execution's approved engineering-audit findings and the ecosystem-level membership-run aggregate, turns them into typed, dependency-ordered cross-repository work packets, and enforces that the ordered packet sequence is a valid topological sort of the packet dependency edges -- a cyclic dependency set is a first-class recorded finding forcing a non-PASS plan verdict, never a silent mis-order. The operator gate H-PLANNING-AUTHORITY authorizes the planning authority the plan asserts across repositories before it is admitted downstream; the pipeline records but never self-executes that authorization."
tags: [ecosystem-cycle, plan, dependency-reconciliation, cross-repo, topological-order, phase-011]
version: 0.1.0
status: active
authoritative_source: ecosystem/04_dependency_reconciliation.md
change_log:
  - version: "0.1.0"
    date: "2026-07-22"
    summary: "Initial authoring (phase 011 feature 080; NIP-0002 Stage 4, the n-coordination protocols; NDEBT-035). Defines the ecosystem lifecycle's Plan stage -- turning approved audit findings plus the phase-010 ecosystem-level membership-run aggregate into typed, dependency-ordered cross-repository work packets, under the topological-order invariant. Names schema/reconciliation_plan.schema.json as the machine-readable plan shape and the operator gate H-PLANNING-AUTHORITY (defined in this feature in docs/planning/operator_gates.md). House structure mirrors ecosystem/03_engineering_audit.md; the release-train Promote stage that consumes this plan is ecosystem/05_release_train_coordination.md (feature 081)."
---

# Dependency Reconciliation Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's **Plan**
step -- the cross-repository planning an agent or engineering team performs
once an evidence-first engineering audit (`ecosystem/03_engineering_audit.md`)
has produced approved findings, and the ecosystem-membership set has been
iterated into an aggregate result (`ecosystem/README.md` Compare/Audit inputs;
the membership-run aggregate of NIP-0002 Stage 3). Reconciliation never plans in
a vacuum: every work packet it produces closes one or more approved audit
findings against a named repository, and the order it emits is capped by the
dependency edges between those packets, never by the order the planner would
prefer.

Consumers extend this protocol with their own packet categories, sizing, and
repository-specific ownership conventions; they do not redefine its input
contract, its work-packet shape, its topological-order invariant, or its
operator gate. Those four mechanics are defined once, here, exactly as
`ecosystem/03_engineering_audit.md` is the single source of truth for the
audit's evidence hierarchy and maturity model, and
`ecosystem/01_clean_state_preflight.md` is the single source of truth for the
preflight verdict vocabulary.

## 2. When to Run

Reconciliation MUST NOT begin until:

- An engineering audit has produced findings the operator has approved for
  planning, per `ecosystem/03_engineering_audit.md` Section 7. A packet that
  closes no approved finding has no reason to exist; reconciliation plans the
  approved findings, it does not invent work.
- The ecosystem-membership set has been iterated into an aggregate result for
  the current execution -- the machine-readable roll-up of every `in_scope`
  member's per-repository verdict and the cross-repository framework-pin
  consistency finding (`schema/ecosystem_membership_result.schema.json`, the
  artifact `tools/ecosystem_membership_run.py` emits; NIP-0002 Stage 3). A
  reconciliation with no aggregate has no enumerated set of repositories to
  plan across and is not a valid reconciliation.

The Plan stage consumes both the approved findings and the membership-run
aggregate as its required inputs: the findings supply *what* must change and in
*which* repository, and the aggregate supplies the authoritative `in_scope` set
those repositories are drawn from plus the pin-consistency state a plan must not
silently paper over. This is reconciliation's entry condition -- a plan that
begins without both inputs is not evidence-first, it is speculative.

A reconciliation run is deterministic in the sense that re-running it against
the same approved findings and the same unchanged aggregate produces the same
packets and the same order; it is not repeatable across different inputs, which
is precisely why every plan records the aggregate result and the finding set it
was reconciled from.

## 3. Work Packets

A **work packet** is the unit of cross-repository plan. Each packet:

- targets exactly one repository (`repo`), drawn from the aggregate's `in_scope`
  set -- a packet never spans two repositories; cross-repository coupling is
  expressed as a dependency edge (Section 4), not as a shared packet;
- names the approved audit findings it closes (`closes_findings`) -- a packet
  that closes no finding is not recorded, per Section 2;
- carries an identifying `id` unique across the plan, so dependency edges and
  the emitted order can reference it unambiguously.

A packet is a *plan* of work, not the work itself: execution of a packet is
carried out by the target repository's own, unmodified repository-local
contract-first controls (`methodology/01_execution.md`), exactly as
`ecosystem/README.md`'s Execute stage describes. This protocol governs how the
packets are shaped and ordered; it does not itself execute them.

## 4. Typed Dependency Edges and the Topological-Order Invariant

Cross-repository coupling is expressed as **typed dependency edges** between
packets: a packet's `depends_on` names the packet ids that MUST complete before
it may begin. An edge is *typed* in that it records a cross-repository ordering
constraint discovered from the findings (an API a downstream repository
consumes, a shared contract, a released artifact), not a mere preference.

The plan emits an **order**: an explicit sequence of every packet id. That
sequence MUST be a valid **topological sort** of the dependency edges -- for
every edge `A depends_on B`, `B` appears before `A` in the order. This is the
topological-order invariant, and it is the plan's core guarantee: an ecosystem
consuming the plan can execute the packets in the emitted order and never begin
a packet before its dependencies are done.

A **cyclic dependency set** -- packets whose `depends_on` edges form a cycle --
has no valid topological sort. A cycle is therefore a first-class recorded
finding (`cycle_findings`), and it forces the plan's verdict to `FAIL`: a plan
that contains a cycle is not a valid dependency-ordered plan, and MUST NOT be
emitted as `PASS`. This mirrors the audit's no-promotion-beyond-evidence rule
(`ecosystem/03_engineering_audit.md` Section 4) at the ordering layer -- a
planner who wants a `PASS` plan must break the cycle, not silently pick an
order that violates one of its edges. The plan verdict is exactly one of:

- `PASS` -- every packet closes an approved finding, and the emitted order is a
  valid topological sort of an acyclic dependency set.
- `FAIL` -- the dependency set contains at least one cycle (recorded in
  `cycle_findings`), so no valid order exists.

## 5. Operator Gate — H-PLANNING-AUTHORITY

A reconciliation plan asserts **planning authority** across repositories: it
declares which repositories change, in which order, to close which findings.
That authority is an operator decision, not a pipeline one. The gate
**H-PLANNING-AUTHORITY** (`docs/planning/operator_gates.md`) authorizes a
`PASS` plan's planning authority before the plan is admitted into a release
train (`ecosystem/05_release_train_coordination.md`). The pipeline **records but
never self-executes** this authorization: a tool may produce and validate a
plan, but only a recorded operator decision advances it downstream, exactly as
the Promote stage records but never self-executes a promotion
(`ecosystem/README.md`). The gate is recorded before the plan is admitted, per
the framework's gate-decision-before-execution rule (`NDEBT-018`).

## 6. Reconciliation Artifact

Every reconciliation run MUST emit a schema-valid, machine-readable plan
artifact at:

```text
.agent/reconciliation/<execution-id>/plan.json
```

where `<execution-id>` is the unique identifier of the ecosystem-cycle
execution, per `ecosystem/README.md`'s Consumer Convention. The plan artifact's
shape (the source aggregate it reconciled, the work-packet set, the typed
dependency edges, the emitted order, the plan verdict, and any recorded cycle
findings) is defined by `schema/reconciliation_plan.schema.json`. This protocol
governs the artifact's required semantics; it does not itself define the JSON
Schema.

Evidence backing the plan (the approved findings consumed, the aggregate result,
intermediate ordering output) is externalised by path under
`.agent/evidence/<execution-id>/`, per the framework's Evidence Capture
Convention (`methodology/04_tool_driven_state.md` Section 5) -- never pasted
inline into the plan artifact or a chat transcript.

## 7. References

- `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` -- the accepted NIP whose
  Stage 4 (n-coordination protocols) this document realizes; the Plan stage is
  where cross-repository ordering genuinely lives.
- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is the Plan step of.
- `ecosystem/03_engineering_audit.md` -- the preceding lifecycle step: no
  reconciliation is run except from approved audit findings.
- `schema/ecosystem_membership_result.schema.json` -- the ecosystem-level
  membership-run aggregate this protocol consumes as its enumerated `in_scope`
  set and pin-consistency input (NIP-0002 Stage 3).
- `ecosystem/05_release_train_coordination.md` -- the following lifecycle step:
  the Promote stage that admits an authorized reconciliation plan into a
  cross-repository release train.
- `schema/reconciliation_plan.schema.json` -- the machine-readable schema for
  the plan artifact this protocol requires.
- `docs/planning/operator_gates.md` -- the registry recording the
  H-PLANNING-AUTHORITY gate this protocol's Section 5 defines.
- `methodology/04_tool_driven_state.md` -- the Evidence Capture Convention this
  protocol's evidence externalisation follows.
- `methodology/03_circuit_breaker.md` -- the house pattern this document's
  structure, tone, and immutability discipline follow.
