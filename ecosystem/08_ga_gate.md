---
id: nizam-ecosystem-ga-gate
title: "GA Gate Protocol"
description: "The reusable Promote-stage protocol for declaring general availability: explicit, evidence-gated GA declaration criteria (a real production pilot, a stable release history at immutable tags, recorded consumer adoptions, no open Critical/High debt, and benchmark thresholds treated strictly as acceptance requirements for the evidence dossier — never as claims of achieved results), the gate ceremony, and the operator decision record. GA declaration is an operator-only act under gate H-GA: the framework must never auto-declare GA, and no tool may emit or imply a GA state on the pipeline's own authority."
tags: [ecosystem-cycle, promote, ga, general-availability, phase-014]
version: 0.1.0
status: draft
authoritative_source: ecosystem/08_ga_gate.md
change_log:
  - version: "0.1.0"
    date: "2026-09-30"
    summary: "Initial authoring, PROPOSAL-GRADE (phase-014 proposal, GA track, awaiting activation gate H-PHASE-014): authored ahead of activation as the rolled-forward phase-012 candidate scope's Promote/GA stage. Status draft until phase-014 execution (feature 099) flips it active and registers the capability (NIZAM.json, tools/skill.json, the user guide) — mirroring how the 04/05 protocols shipped at their authoring features (the 0.2.2/0.2.3 ecosystem/README.md precedent). Defines the GA declaration's evidence-gated preconditions, the gate ceremony, and the operator gate H-GA (reserved; defined during phase-014 execution): GA declaration is operator-only and the framework must never auto-declare GA. House structure mirrors ecosystem/03_engineering_audit.md and ecosystem/05_release_train_coordination.md."
---

# GA Gate Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's
**Promote** stage's GA declaration -- the act by which a framework (or a governed
ecosystem member) is declared **generally available**. GA is a claim about
evidence, not a milestone a calendar or a version number reaches: it is declared
only by the operator, only against an assembled dossier, and only once. The
sibling Promote-stage protocol `ecosystem/05_release_train_coordination.md`
governs how coordinated releases are admitted and recorded; this protocol governs
the separate, later question of whether the accumulated release and adoption
evidence supports the GA claim at all.

Consumers extend this protocol with their own benchmark thresholds, pilot shapes,
and dossier layout; they do not redefine its precondition set, its
thresholds-as-acceptance-requirements rule, its gate ceremony, or its operator
gate. Those four mechanics are defined once, here, exactly as
`ecosystem/05_release_train_coordination.md` is the single source of truth for
the release train's trace-to-plan invariant.

## 2. GA Declaration Preconditions

GA declaration preconditions are explicit and evidence-gated. A GA declaration
MUST NOT be made until every precondition carries recorded evidence:

- **A real production pilot.** A real, non-scratch pilot -- real repositories,
  real worktrees, never scratch-harness fabrication -- has completed with a
  recorded evidence pack. A pilot against synthetic members proves loop
  mechanics, not production maturity, and does not satisfy this precondition.
- **A stable release history.** Consecutive releases cut as operator-signed
  annotated tags at reviewed commits, each with a dated CHANGELOG section and a
  green release workflow. A release line with an unrecorded anomaly does not
  count toward stability until the anomaly is honestly recorded and resolved.
- **Recorded consumer adoptions.** Consumers have adopted released immutable
  tags under recorded `H-CONSUMER-UPGRADE` decisions
  (`docs/planning/operator_gates.md`), one record per adoption.
- **No open Critical/High debt.** The governing debt register carries no open
  Critical- or High-severity rows at assessment time.
- **Benchmark thresholds met.** Each threshold is an ACCEPTANCE REQUIREMENT on
  the evidence dossier: the dossier must contain the measured result and its
  provenance. A threshold is never a claim of achieved results; passing it
  asserts the measurement exists and is anchored, and the operator judges the
  result.

## 3. Evidence Requirements

The dossier is one machine-readable GA-readiness artifact plus per-criterion
evidence files under `.agent/evidence/`, externalised by path -- never pasted
inline into the artifact or a chat transcript. Every fact is anchored to both a
stated revision and timestamp, per `ecosystem/02_evidence_baseline.md`'s anchor
discipline. Every threshold measurement carries its command, its captured
output, and its provenance. Unanchored or stale evidence disqualifies the
criterion it backs, per `ecosystem/07_progress_comparison.md`'s stale-evidence
non-reuse rule: a dossier assembled from evidence the cycle itself would call
stale is not a dossier.

## 4. The Gate Ceremony

The ceremony assigns each role its act:

1. The **pipeline** assembles and validates the dossier and presents the
   GA-readiness assessment: one verdict per precondition, each pointing at its
   evidence by path.
2. The **dual validator gate** (`standard/AGF.md`) may review the assessment.
3. The assessment MUST present **H-GA as OUTSTANDING**: it recommends, it never
   concludes. The pipeline never publishes, tags, announces, or flips any GA
   state on its own authority -- no tool may emit a GA verdict.
4. On the **operator's decision**, the declaration is recorded (Section 6). A
   "GA" state can only be entered by the recorded operator decision.

## 5. Operator Gate — H-GA

GA declaration is operator-only. The gate **H-GA**
(`docs/planning/operator_gates.md`; reserved until phase-014 execution defines
it) authorizes the declaration. The framework must never auto-declare GA -- this
is a fail-closed rule, not guidance: absent the recorded operator decision, every
surface continues to present GA as undeclared, whatever the dossier shows. The
pipeline records but never self-executes, and the decision is recorded BEFORE
the declared act, per the framework's gate-decision-before-execution rule
(`NDEBT-018`).

## 6. The Operator Decision Record

The binding record of a GA declaration is:

- a run_state `operator_gate_decision` event carrying the operator's verbatim
  authorization, the dossier's path and digest, the declared version/tag, and
  the timestamp; and
- the dated declaration note in the governing planning surfaces.

A GA declaration without this record does not exist. The record precedes and
authorizes every downstream act (announcement, badge, guide notation); an act
that precedes its record is a governance defect, recorded as such.

## 7. References

- `ecosystem/README.md` -- the module index and canonical lifecycle whose
  Promote stage this protocol serves.
- `ecosystem/05_release_train_coordination.md` -- the sibling Promote-stage
  protocol governing release-train admission; a stable release history (Section
  2) is built from the trains it records.
- `ecosystem/02_evidence_baseline.md` -- the anchor discipline every dossier
  fact follows.
- `ecosystem/03_engineering_audit.md` -- the evidence hierarchy the dossier's
  per-criterion evidence inherits.
- `docs/planning/operator_gates.md` -- the registry recording the H-GA gate this
  protocol's Section 5 names.
- `methodology/06_release_train.md` -- the repository-local release mechanics
  whose annotated-tag discipline the stable-release-history precondition
  consumes.
- `standard/AGF.md` -- the dual validator gate that may review the GA-readiness
  assessment.
