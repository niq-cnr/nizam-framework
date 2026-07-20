---
id: nizam-ecosystem-evidence-baseline
title: "Immutable Evidence Baseline Protocol"
description: "The reusable protocol for capturing a point-in-time, immutable baseline over framework, repository, dependency, CI, planning, and evidence references, with explicit baseline fields and the revision/timestamp anchoring rule that a baseline MUST NOT mix evidence from unspecified revisions."
version: 0.1.1
status: active
authoritative_source: ecosystem/02_evidence_baseline.md
change_log:
  - version: "0.1.1"
    date: "2026-07-20"
    summary: "Tier-0 doc-truth: Section 7's References entry for schema/ecosystem_baseline.schema.json retires the stale parenthetical 'added by a later feature in this phase; not yet present at the time this protocol was authored' -- the schema shipped in feature 037 and has been present under schema/ since (and its same-repo revision-consistency FAIL condition is now mechanized at both levels per NDEBT-023). This is the document's first change_log entry; no semantic change to the protocol."
---

# Immutable Evidence Baseline Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's
Baseline step -- the point-in-time, immutable snapshot an agent or
engineering team captures once a clean-state preflight
(`ecosystem/01_clean_state_preflight.md`) has returned a verdict the
execution is authorized to proceed from. A baseline is the fixed reference
point every later Audit, Plan, and Compare step in the lifecycle measures
against; nothing about a baseline is mutated after it is captured, and no
later step may silently substitute a different baseline for the one it was
given.

Consumers extend this protocol with their own repository- and
ecosystem-specific reference lists (which repositories, which CI systems,
which planning documents); they do not redefine its six baseline field
categories, its immutability semantics, or its revision-and-timestamp
anchoring rule. Those three mechanics are defined once, here, exactly as
`ecosystem/01_clean_state_preflight.md` is the single source of truth for the
preflight verdict vocabulary and blocking discipline.

## 2. When to Capture

A baseline MUST be captured:

- Immediately after a clean-state preflight run has returned `PASS`, or a
  `PASS_WITH_EXCEPTIONS` verdict an operator has explicitly approved, per
  `ecosystem/01_clean_state_preflight.md` Sections 3 and 5. A baseline is
  never captured against a `FAIL` verdict or an unresolved
  `PASS_WITH_EXCEPTIONS`.
- Before the first Audit of a new ecosystem-cycle execution, so the audit has
  a fixed reference point to measure evidence against.
- Before any Compare step that measures progress against a prior execution --
  a Compare with no baseline on one or both sides is not a valid comparison.

A baseline capture is deterministic and repeatable in the sense that
re-running it against the same, unchanged revisions and evidence produces the
same field values; it is not repeatable across different revisions, which is
precisely why every field is anchored (Section 4).

## 3. Baseline Fields

A baseline defines fields across six reference categories. Every baseline
artifact (Section 6) states, at minimum, one reference entry per category
that applies to the execution:

- **Framework references** -- the released framework version or tag the
  ecosystem cycle is currently governed by.
- **Repository references** -- every in-scope repository, each pinned to a
  specific revision (Section 4).
- **Dependency references** -- the cross-repository dependencies the
  execution is reconciling against, however they are typed (see the
  framework's typed-dependency work, deferred per
  `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`).
- **CI references** -- the CI run(s) whose results back any claim in the
  baseline; a claim with no CI reference is not CI-verified.
- **Planning references** -- the planning documents (roadmaps, manifests,
  debt registers) current at the moment of capture.
- **Evidence references** -- externalised evidence paths (never inline
  terminal output) backing every other field, per the framework's Evidence
  Capture Convention (`methodology/04_tool_driven_state.md` Section 5).

Baseline fields and evidence rules are defined by this section and Section 4
together: this section states what a baseline records; Section 4 states how
every recorded fact is anchored so it cannot be misattributed to the wrong
point in time.

## 4. Revision and Timestamp Anchoring Rule

Every evidence item in a baseline is anchored to a declared repository
revision (a commit SHA, or an equivalent immutable revision identifier) and
a timestamp. An evidence item with no declared revision, or no timestamp, is
not a valid baseline entry.

A baseline MUST NOT mix evidence from unspecified revisions: every fact the
baseline records must be traceable to one, explicitly stated revision and
timestamp, and a baseline that combines evidence collected against two or
more different, unstated, or ambiguous revisions of the same repository is
invalid. This is a defined FAIL condition for baseline capture, exactly as a
blocking condition is a defined FAIL condition for preflight
(`ecosystem/01_clean_state_preflight.md` Section 4): a baseline capture tool
MUST refuse to emit a baseline artifact (Section 6) whose evidence items do
not each carry their own revision and timestamp, or whose declared revisions
for the same repository are inconsistent across the baseline's fields.

This rule exists so a later Audit or Compare step can trust that "the
baseline" means one specific, nameable point in time across every repository
and reference it covers -- never a blend of states that never coexisted.

## 5. Immutability Rule

A baseline is a point-in-time, immutable snapshot. Once captured, a baseline
artifact (Section 6) is never edited in place: no field is corrected,
appended to, or removed after the artifact is written. If a captured
baseline is later found to be wrong or incomplete, the correction is a new
baseline, superseding the old one; the old baseline artifact is retained
unchanged as the historical record it always was, not rewritten to look
correct in hindsight.

This mirrors the framework's Circuit Breaker discipline
(`methodology/03_circuit_breaker.md`): a completed audit trail is not
retouched to hide what actually happened; the correction is a new, later
entry, not an edit to the old one.

## 6. Baseline Artifact

Every baseline capture MUST emit a schema-valid, machine-readable artifact
at:

```text
.agent/reconciliation/<execution-id>/baseline.json
```

where `<execution-id>` is the unique identifier of the ecosystem-cycle
execution the baseline belongs to, per the framework's Artifact Locations
convention (`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`). The
artifact's shape (the six baseline field categories of Section 3 and the
per-item revision/timestamp anchor of Section 4) is defined by
`schema/ecosystem_baseline.schema.json`. This protocol governs the
artifact's required semantics; it does not itself define the JSON Schema.

Evidence backing the baseline (raw tool output, logs, or intermediate
collection results) is externalised by path under
`.agent/evidence/<execution-id>/`, per the framework's Evidence Capture
Convention (`methodology/04_tool_driven_state.md` Section 5) -- never pasted
inline into the baseline artifact or into a chat transcript.

## 7. References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` -- the accepted NIP
  defining the Baseline goal, Artifact Locations, and Dogfood Requirement
  this protocol implements.
- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is one step of.
- `ecosystem/01_clean_state_preflight.md` -- the preceding lifecycle step: no
  baseline is captured except from a `PASS` or approved
  `PASS_WITH_EXCEPTIONS` preflight verdict.
- `methodology/04_tool_driven_state.md` -- the Evidence Capture Convention
  this protocol's evidence externalisation follows.
- `methodology/03_circuit_breaker.md` -- the house pattern this document's
  structure, tone, and immutability discipline follow.
- `schema/ecosystem_baseline.schema.json` -- the machine-readable schema for
  the baseline artifact this protocol requires.
