---
id: nizam-ecosystem-simplification-review
title: "Simplification Review Protocol"
description: "The reusable Repeat-stage protocol: a recurring, evidence-first simplification review over the ecosystem's accumulated governance surface (protocols, schemas, tooling, standards), recording consolidation candidates with evidence and never applying one automatically — an actual simplification or consolidation is executed only under the operator gate H-CONSOLIDATION, which the pipeline records but never self-executes."
tags: [ecosystem-cycle, repeat, simplification, consolidation, phase-014]
version: 0.1.0
status: draft
authoritative_source: ecosystem/06_simplification_review.md
change_log:
  - version: "0.1.0"
    date: "2026-09-30"
    summary: "Initial authoring, PROPOSAL-GRADE (phase-014 proposal, GA track, awaiting activation gate H-PHASE-014): authored ahead of activation as the rolled-forward phase-012 candidate scope's Repeat stage. Status draft until phase-014 execution (feature 099) flips it active and registers the capability (NIZAM.json, tools/skill.json, the user guide) — mirroring how the 04/05 protocols shipped at their authoring features (the 0.2.2/0.2.3 ecosystem/README.md precedent). Defines the ecosystem lifecycle's Repeat stage: the recurring simplification review, its evidence duties, and the operator gate H-CONSOLIDATION (reserved; defined during phase-014 execution). House structure mirrors ecosystem/03_engineering_audit.md and ecosystem/07_progress_comparison.md."
---

# Simplification Review Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's **Repeat**
step -- the recurring, evidence-first simplification review an agent or engineering
team performs over the ecosystem's accumulated governance surface. The cycle's
engine is a loop (`ecosystem/README.md`): after Compare
(`ecosystem/07_progress_comparison.md`), the cycle does not merely accumulate -- it
periodically asks what should shrink. Simpler is a property that must be reviewed
into existence, never assumed.

Consumers extend this protocol with their own surface inventory conventions,
complexity metrics, and review cadence; they do not redefine its input contract,
its finding discipline, its no-auto-consolidation rule, or its operator gate.
Those four mechanics are defined once, here, exactly as
`ecosystem/03_engineering_audit.md` is the single source of truth for the audit's
evidence hierarchy and `ecosystem/07_progress_comparison.md` is the single source
of truth for the Compare step that feeds this review.

## 2. When to Run

A simplification review MUST NOT begin until:

- An approved comparison or at least two approved baselines/audits exist for the
  window under review (`ecosystem/07_progress_comparison.md` over
  `ecosystem/02_evidence_baseline.md` and `ecosystem/03_engineering_audit.md`
  outputs). A review with no approved evidence base has nothing to reason from.
- The current cycle's execution and verification have completed. A review run
  mid-cycle reasons over a moving surface and its findings are stale on arrival.
- The operator has initiated the review cycle. A simplification review is never
  self-triggered by the pipeline: it is a recurring act the operator starts, not
  a job the tooling schedules for itself.

Cadence guidance: at minimum once per full cycle completion, or when the
accumulated-surface metrics cross a consumer-declared threshold. A threshold
crossing is a prompt for the operator to consider initiating a review, never an
automatic trigger.

## 3. The Simplification Review

The review examines an **inventory of the governed surface** -- the protocols,
schemas, tools, standards, templates, and registry artifacts the ecosystem
accumulates -- with per-item usage and complexity evidence. It hunts:

- **duplication** -- two surfaces stating the same rule, where a change to one
  can silently drift from the other;
- **dead weight** -- shipped but unreferenced or unexercised surface: a schema no
  artifact validates against, a tool no cycle stage invokes, a protocol section
  nothing cites;
- **over-mechanization** -- enforcement whose carrying cost exceeds its defect
  class: a check that has never caught a real defect but runs on every change;
- **consolidation candidates** -- N documents, keys, or tools that should be one.

Every candidate is a **typed finding with evidence**, mirroring
`ecosystem/03_engineering_audit.md`'s finding discipline: a candidate without
evidence does not exist, and the review never promotes a suspicion to a finding
without the artifact, reference, or measurement that backs it.

## 4. Candidate Findings and the No-Auto-Consolidation Rule

Findings are **recorded, never applied**. The review NEVER edits, merges,
deletes, or restructures any governed surface on its own authority; it emits a
candidate list ordered by evidence-backed leverage -- the consolidation that
removes the most surface per unit of risk first. Benchmarks and thresholds used
in the review (a usage floor, a complexity ceiling, a duplication count) are
acceptance requirements for the evidence, not claims of achieved simplicity:
meeting a threshold asserts the measurement exists and is anchored, never that
the surface is now simple.

## 5. Operator Gate — H-CONSOLIDATION

Authorizing an actual simplification or consolidation is an operator decision,
not a pipeline one. The gate **H-CONSOLIDATION**
(`docs/planning/operator_gates.md`; reserved until phase-014 execution defines
it) authorizes the act. The pipeline **records but never self-executes**: a
consolidation runs only after the recorded operator decision, and the decision
is recorded BEFORE the act per the framework's gate-decision-before-execution
rule (`NDEBT-018`). Each consolidation is itself planned work under
`methodology/00_planning.md` -- a feature with a contract -- not a side-effect
of the review.

## 6. Review Artifact

Every simplification review run MUST emit a machine-readable review artifact
plus its evidence under:

```text
.agent/audits/<simplification-review-id>/
```

in the consuming repository, where `<simplification-review-id>` is the unique
identifier of the review run. Every fact in the artifact is anchored to both a
stated revision and timestamp, per the baseline discipline of
`ecosystem/02_evidence_baseline.md`. Evidence is externalised by path -- never
pasted inline into the artifact or a chat transcript -- and each candidate
finding reuses the engineering_finding schema shape
(`schema/engineering_finding.schema.json`) so consolidation candidates flow
through the same finding lifecycle as audit findings.

## 7. References

- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is the Repeat step of.
- `ecosystem/03_engineering_audit.md` -- the finding discipline this protocol's
  candidate findings mirror.
- `ecosystem/07_progress_comparison.md` -- the Compare step whose approved
  outputs feed this review.
- `ecosystem/02_evidence_baseline.md` -- the revision-plus-timestamp anchor
  discipline every review fact follows.
- `docs/planning/operator_gates.md` -- the registry recording the
  H-CONSOLIDATION gate this protocol's Section 5 names.
- `methodology/00_planning.md` -- the planned-work discipline under which an
  authorized consolidation is executed.
