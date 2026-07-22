---
id: nizam-registry-scope-patterns
title: "Ecosystem Registry & Scope-Definition Patterns"
description: "Generalised patterns for a consumer repository that maintains its own ecosystem-level registry of repositories, services, or modules on top of the Nizam framework: the scope-list shape, dependency-map conventions, phase-progress tracking, and drift rules."
version: 0.3.0
status: active
authoritative_source: registry/scope_definition_patterns.md
change_log:
  - version: "0.3.0"
    date: "2026-07-22"
    summary: "Phase-010 feature 075 (NDEBT-031; NIP-0002 Stage 3): promoted from a draft pattern to a required, SCHEMA-BACKED artifact -- status draft -> active. A membership-registry instance now validates against schema/ecosystem_membership.schema.json (registered in NIZAM.json + schema/README.md), which enforces the Section 2 shape (the four scope lists exist as arrays of entries, every entry has an identifying name, out_of_scope entries record a reason). The exactly-one-list invariant (Section 2.1: no name appears in two lists) is a relational cross-array constraint JSON Schema cannot express, so it is enforced in code by validate.sh C12 (mirroring the ecosystem_baseline same-repo-revision rule, NDEBT-023), with positive + schema-invalid + multilist negative fixtures. Section 2 gains the schema/validator cross-reference. This is the artifact that sets n for the 0-to-n spectrum; the multi-repo TOOLING that iterates it is features 076-077."
  - version: "0.2.0"
    date: "2026-07-22"
    summary: "Phase-009 feature 072 (NDEBT-030; NIP-0002 Stage 2): new Section 2.3 models the incubating -> in_scope promotion as the count-0->1 transition of the 0-to-n spectrum. A greenfield-genesis project (ecosystem/00 Section 8; bootstrap.sh --genesis) enters the registry in `incubating` and is promoted to `in_scope` once it clears its first clean Preflight/Baseline, as an explicit recorded edit that MOVES the entry (preserving the Section 2.1 exactly-one-list invariant); demotion is symmetric. Scoped to the single-project count-0->1 case only -- promoting the registry to a required, validated ecosystem-membership artifact the tools iterate to set n (count-1->n) stays NDEBT-031 / NIP-0002 Stage 3, deferred to phase 010. Status stays draft. A tools/fixtures_self_test.sh scratch probe asserts the transition shape (promotion moves the entry; a two-list entry is detected)."
  - version: "0.1.0"
    date: "2026-07-20"
    summary: "Initial ecosystem registry & scope-definition patterns (the list-partition shape, entry shape, dependency-map conventions, phase-progress tracking, and drift rules). Consumer-level pattern doc; ships no project-specific data."
---

# Ecosystem Registry & Scope-Definition Patterns

## 1. Overview

Some consumer repositories are not just a single codebase — they are the strategy or
platform repository for a whole ecosystem of other repositories, services, or modules.
That repository needs its own machine-readable registry describing what is in scope,
what depends on what, and how far along each piece is. This document generalises the
registry shape observed across such deployments into a reusable pattern. It ships no
project-specific data: no repository names, no infrastructure endpoints, no filled-in
scope lists. A consumer repository authors its own instance of this shape.

This pattern is a *consumer-level* concern. It sits above the Nizam framework itself:
Nizam's own `NIZAM.json` (validated by `registry/nizam-index.schema.json`) indexes
Nizam's own modules and capabilities; an ecosystem registry built with the patterns
below indexes a *consumer's* fleet of repositories or services and is a separate,
project-specific artifact.

## 2. The Ecosystem Registry JSON Shape

A single JSON document, versioned and timestamped, with a top-level `schema_version`
(or equivalent) and `last_updated` field, plus a small number of named lists that
partition every tracked entity by scope status:

```text
{
  "schema_version": "<semver>",
  "last_updated": "<ISO 8601 timestamp>",
  "authoritative_source": "<repository-relative path to this document>",
  "dependency_map": "<link or path to a human-readable dependency document, if maintained separately>",
  "phase_progress": { ... },
  "in_scope": [ { ...entry... }, ... ],
  "incubating": [ { ...entry... }, ... ],
  "reference_archive": [ { ...entry... }, ... ],
  "out_of_scope": [ { ...entry... }, ... ]
}
```

A conforming registry instance validates against **`schema/ecosystem_membership.schema.json`**
(registered in `NIZAM.json` and `schema/README.md`): the schema enforces the shape below — the
four scope lists exist as arrays of entries, every entry carries an identifying `name`, and
`out_of_scope` entries record a `reason`. The **exactly-one-list invariant** (§2.1: no `name`
appears in two lists) is a relational cross-array constraint JSON Schema cannot express, so
`tools/validate.sh` C12 enforces it in code alongside the schema (the same split the
`ecosystem_baseline` same-repo-revision rule uses). This makes the registry a *required, validated*
artifact — the one that sets `n` for the 0-to-n spectrum — not merely a documented pattern.

### 2.1 The list-partition pattern

Every tracked entity appears in **exactly one** list, chosen by its current
relationship to the ecosystem, not by its perceived importance:

| List | Meaning |
|---|---|
| `in_scope` | Actively maintained and part of the current masterplan or roadmap. |
| `incubating` | Exists, is tracked, but has not yet met the bar for full `in_scope` status (e.g. governance not yet bootstrapped, concept-stage, or pre-implementation). |
| `reference_archive` | No longer independently maintained, but retained as a reference for one or more `in_scope` entries (e.g. a predecessor implementation, a migration source). |
| `out_of_scope` | Explicitly excluded, with a `reason` field so the exclusion is a recorded decision rather than an omission. |

An entity's list membership, not a status string alone, is the authoritative signal for
whether it currently receives ecosystem-level governance, resourcing, or dependency
guarantees.

### 2.2 The entry shape

Each entry in any list is an object. A minimal entry needs only an identifying key and
enough context to explain why it is in that list (`out_of_scope` entries in particular
may be nothing more than a name and a `reason`). A fuller entry, typical of `in_scope`,
commonly carries:

- An identifying key (a name) and a link to its canonical location.
- A one-line `role` or `description` — what this entity is *for*, in business terms.
- A `status` field describing operational state (e.g. `active`, `IN_DEVELOPMENT`,
  `deprecated`) — kept distinct from the list it lives in, since a `deprecated` entity
  can still be `in_scope` during a wind-down window.
- A `depends_on` array (Section 3).
- An `exposes` array — the interfaces, packages, or endpoints this entity provides to
  the rest of the ecosystem, so a consumer can reason about impact without cloning it.
- A free-text `note` capturing the latest material fact about the entity, dated
  implicitly by the registry's own `last_updated`/`last_audited` fields.
- A `last_audited` timestamp, so registry consumers can distinguish a freshly verified
  entry from a stale one.

Optional enrichment fields (a maturity or health score, a tier/grouping label, a
superseding-entity pointer) may be layered on top without changing the base shape,
provided they do not replace the required identifying and scope-list fields above.

### 2.3 The `incubating -> in_scope` promotion (the count-0->1 transition)

The `incubating` partition is where a project lives while it is *tracked but not yet a full
member* -- the **count-0->1 state** of the 0-to-n spectrum
(`ecosystem/00_ecosystem_bootstrap.md` Section 3). A project created by greenfield genesis
(`ecosystem/00_ecosystem_bootstrap.md` Section 8; `bootstrap.sh --genesis`) enters the registry
here: it exists and is bootstrapped, but has not yet earned `in_scope` governance, resourcing, or
dependency guarantees.

Promotion `incubating -> in_scope` is an explicit, recorded registry edit, never an implicit side
effect:

- **Entry.** A genesis'd project is added to `incubating` at creation, carrying at least its
  identifying key and a `note` recording that it is a freshly stood-up project awaiting its first
  clean cycle run.
- **Promotion criterion.** It is promoted to `in_scope` once it has cleared its first clean
  Preflight and Baseline (`ecosystem/01_clean_state_preflight.md`,
  `ecosystem/02_evidence_baseline.md`) at the pinned framework tag -- i.e. it is demonstrably a
  working cycle participant, not merely a scaffolded shell.
- **The move preserves the exactly-one-list invariant** (Section 2.1): promotion *moves* the
  entry from `incubating` to `in_scope` in the same edit; an entry must never appear in both.
  Leaving a promoted project in `incubating`, or copying rather than moving it, is drift
  (Section 5, rule 4).
- **Demotion is symmetric.** A project that regresses (stops sustaining a clean cycle) moves back
  to `incubating`, or to `reference_archive`/`out_of_scope` with a `reason`, by the same
  explicit-edit rule -- never by silent deletion (Section 5, rule 3).

This subsection scopes only the count-0->1 transition for a single genesis'd project. Making the
registry a *required, validated* ecosystem-membership artifact that the tools iterate to set `n`
(the count-1->n work) is a separate, larger change (`NDEBT-031`, NIP-0002 Stage 3), deliberately
not undertaken here.

## 3. Dependency-Map Conventions

Two complementary mechanisms, not one, are used to express dependency:

1. **Inline `depends_on` arrays.** Each entry lists the identifying keys of the other
   entries it depends on. This is the machine-checkable form: a validator can confirm
   every name in a `depends_on` array resolves to another entry somewhere in the
   registry (in any list — a dependency on a `reference_archive` entry is a signal
   worth flagging, not silently ignored).
2. **A separate human-readable dependency map.** A prose or diagram document
   (referenced from the registry's top-level `dependency_map` field) that explains the
   *shape* of the dependency graph — tiers, layers, or waves — in a way a flat list of
   `depends_on` arrays cannot convey on its own. The registry points to this document;
   it does not inline it, keeping the JSON registry itself lint-friendly and diffable.

Both mechanisms describe the same underlying graph and should agree; a registry
validator should be able to detect drift between the two.

## 4. Phase-Progress Tracking

A registry commonly tracks not just *what* is in scope but *how far along* a shared,
ecosystem-wide effort is, via a single `phase_progress` block distinct from any one
entry's own `status`:

- One status field per named phase or workstream (e.g. `phase_NN_status`), using a
  small closed vocabulary (`COMPLETE`, `IN_PROGRESS`, `NOT_STARTED`, `BLOCKED`).
  Ecosystem-specific milestones (a particular gap-closure effort, a particular
  cross-cutting initiative) may get their own named status field alongside the
  numbered phases.
  These phase records exist independently of a project's own internal phase runner state
  (of the kind produced by `methodology/00_planning.md` / `.agent/run_state.json`);
  `phase_progress` is the ecosystem's outside view, not a project's own execution state.
- A `last_assessment` timestamp recording when the whole block was last reviewed as a
  unit, distinct from any single entry's own `last_audited` field.
- A free-text `notes` field summarising the current cross-entity narrative — what
  unblocked what, what is now sequenced after what — so a reader gets the *story*, not
  just a table of independent statuses.
- A readiness or blocking-items field for whatever the ecosystem's next major
  milestone is, so "are we ready to ship/launch/cut over" has one authoritative,
  queryable answer instead of being re-derived from prose scattered across entries.

## 5. Drift Rules

1. **The registry is authoritative, not any individual entity's own self-description.**
   If an entity's own repository claims a status, role, or dependency set that conflicts
   with the ecosystem registry, the registry wins until a registry update reconciles
   the two. Individual repositories describe themselves for their own contributors;
   the registry describes them for the rest of the ecosystem.
2. **Consumers verify against a pinned reference, not a moving target.** Any process
   that reads the registry to make a decision (a dependency check, a scope check, a
   release gate) should read it at a specific, addressable revision (a commit, tag, or
   timestamped snapshot) — the same discipline `standard/GIP.md` requires for
   inheriting the framework itself via a pinned tag rather than a floating branch.
   A consumer that silently tracks a moving `main` risks acting on a registry state
   that changed mid-decision.
3. **Every exclusion is recorded, not implied.** An entity absent from every list is a
   gap, not a decision. Deliberate exclusions belong in `out_of_scope` with a `reason`;
   an entity that stops being tracked should move to `reference_archive` or
   `out_of_scope` explicitly rather than simply being deleted from the document.
4. **Drift is a first-class, loggable condition.** When a registry consumer detects
   that live state (a dependency that no longer resolves, a status that has silently
   gone stale past some staleness threshold, an entry in two lists at once) disagrees
   with the registry, that disagreement is logged as debt against the registry itself,
   not quietly patched over by the consumer.
