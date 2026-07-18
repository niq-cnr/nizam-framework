---
id: nip-0001-ecosystem-engineering-cycle
title: "NIP-0001: Ecosystem Engineering Cycle"
description: "Accepted proposal to add a reusable, schema-governed lifecycle for reconciling, auditing, coordinating, simplifying, and promoting multi-repository ecosystems."
version: 1.0.0
status: active
authoritative_source: docs/nips/NIP-0001-ecosystem-engineering-cycle.md
last_audited: "2026-07-17"
tags: [nip, ecosystem, governance, audit, release-train, dogfood]
change_log:
  - version: "1.0.0"
    date: "2026-07-17"
    summary: "Accepted by operator 2026-07-17 (remote-control message: \"approved. expedite.\"), satisfying gate H-NIP. NIP becomes the plan of record for phase 005-ecosystem-cycle. Frontmatter status set to 'active' (the frontmatter schema enum is draft/active/deprecated; the decision-lifecycle state 'Accepted' is carried in the body Status section, matching the docs/architecture/ADR-00N house pattern)."
  - version: "0.1.0"
    date: "2026-07-17"
    summary: "Initial proposal (handover programme definition), status proposed, awaiting operator approval."
---

# NIP-0001: Ecosystem Engineering Cycle

## Status

**Accepted.** Approved by the ecosystem operator on 2026-07-17 via remote-control
message "approved. expedite.", satisfying operator gate **H-NIP** and authorizing
activation of phase `005-ecosystem-cycle` as the framework's plan of record. This
document supersedes the proposal-time wording; the accepted lifecycle below is
implemented through the normal Nizam planning and contract-first execution loop.

### Acceptance Record

| Field | Value |
|-------|-------|
| Decision | ACCEPTED |
| Operator | Ecosystem operator (`rosscn@nizamiq.com`) |
| Date | 2026-07-17 |
| Gate satisfied | H-NIP ("Approve NIP-0001 before implementation becomes plan of record") |
| Authorization (verbatim) | "approved. expedite." |
| Channel | Remote-control message |
| Consequence | Phase `005-ecosystem-cycle` activated; framework-side features (handover F-001..F-015) become the active plan of record. Consumer adoption (handover F-016..F-020) is deferred to a successor programme phase. |
| Outstanding human gates | H-FRAMEWORK-SCOPE (scope-lock), H-DOGFOOD-EXCEPTION, H-FRAMEWORK-RELEASE, H-RISK remain outstanding and are NOT satisfied by this acceptance. |

### Placement note

This is the first Nizam Improvement Proposal (NIP) in this repository. The
pre-existing decision-record pattern is the ADR set under `docs/architecture/`
(`ADR-001`..`ADR-003`). NIPs are framework-capability proposals (broader in scope
than a single architecture decision) and are placed under `docs/nips/`, created by
this record. ADRs remain the home for narrower, single-decision architecture
records; a NIP may spawn one or more ADRs during implementation.

## Problem

Nizam currently provides strong repository-level planning, contract-first execution,
anti-hallucination controls, evidence externalisation, release discipline, and
cross-repository dependency gates.

Multi-repository ecosystems still require long prompts to define:

- clean-state reconciliation;
- immutable audit baselines;
- ecosystem-wide engineering audits;
- typed dependency verification;
- release-train coordination;
- simplification analysis;
- audit-to-audit comparison;
- GA evidence gates.

This duplicates governance outside the framework and allows prompt text, ecosystem
strategy documents, and implementation behaviour to diverge.

## Decision

Add a first-class **Ecosystem Engineering Cycle** to Nizam.

The canonical lifecycle is:

```text
Bootstrap
  -> Preflight
  -> Baseline
  -> Audit
  -> Plan
  -> Execute
  -> Verify
  -> Promote
  -> Compare
  -> Repeat
```

Nizam defines the reusable lifecycle, schemas, validation rules, and capability
routing.

Each consumer ecosystem defines its own:

- repository registry;
- scope;
- architecture;
- product slice;
- release trains;
- debt;
- environments;
- owners;
- thresholds;
- operator gates.

## Goals

1. Reduce ecosystem governance prompts to parameters and objectives.
2. Ensure every audit and train begins from a reconciled state.
3. Provide immutable, machine-readable evidence baselines.
4. Coordinate cross-repository work using typed dependencies.
5. Track maturity, complexity, debt, and engineering progress over time.
6. Make simplification a recurring engineering responsibility.
7. Preserve operator authority for risk and release decisions.
8. Dogfood the capability against `nizam-framework` before consumer adoption.

## Non-Goals

- Building a general-purpose project management system.
- Replacing GitHub, CI, GitOps, issue tracking, or deployment platforms.
- Automatically merging code or declaring GA.
- Encoding NizamIQ-specific repository names or product architecture in the framework.
- Replacing repository-local contracts, tests, ADRs, or debt registers.
- Automating architectural consolidation decisions.

## Proposed Framework Surface

### New module

```text
ecosystem/
  README.md
  00_ecosystem_bootstrap.md
  01_clean_state_preflight.md
  02_evidence_baseline.md
  03_engineering_audit.md
  04_dependency_reconciliation.md
  05_release_train_coordination.md
  06_simplification_review.md
  07_progress_comparison.md
  08_ga_gate.md
```

### Initial schemas

```text
schema/ecosystem_baseline.schema.json
schema/preflight_verdict.schema.json
schema/engineering_finding.schema.json
schema/dependency_graph.schema.json
schema/audit_delta.schema.json
schema/ecosystem_complexity.schema.json
schema/ga_evidence_index.schema.json
```

### Capability routing

Add capability entries to:

- `NIZAM.json`
- `tools/skill.json`
- `tools/SKILL.md`

The single runtime-agnostic skill remains the router. No runtime-specific ecosystem
skills are introduced.

### Deterministic tooling

Initial minimum tooling:

```text
tools/ecosystem_preflight.py
tools/compare_ecosystem_baselines.py
tools/validate_evidence_freshness.py
```

Additional tools may follow after dogfood evidence.

## Artifact Locations

Consumer convention:

```text
.agent/reconciliation/<execution-id>/
.agent/audits/<audit-id>/
.agent/trains/<train-id>/
.agent/evidence/<execution-id>/
```

## Preflight Verdict

A preflight must return exactly one:

- `PASS`
- `PASS_WITH_EXCEPTIONS`
- `FAIL`

`PASS_WITH_EXCEPTIONS` requires explicit operator approval before execution
continues.

## Maturity Model

1. Designed
2. Authored
3. Implemented
4. Unit Tested
5. Integrated
6. Rendered
7. Deployed
8. Exercised
9. Observable
10. Production Proven

No claim may be promoted beyond its evidence.

## Compatibility

This is additive and should be released as a MINOR framework version unless
implementation changes existing required schemas, paths, or bootstrap behaviour.

Existing consumers remain compliant without adopting the ecosystem module.

## Dogfood Requirement

Before release:

1. Run preflight against `nizam-framework`.
2. Generate a framework baseline.
3. Produce at least one schema-valid engineering finding.
4. Compare the baseline with a subsequent run.
5. Record friction as debt.
6. Update the framework roadmap from dogfood evidence.
7. Run all existing validators and bootstrap tests.
8. Obtain human release approval.

## Adoption Requirement

NizamIQ may adopt only a released immutable tag.

The consumer adoption PR must:

- re-bootstrap using the released tag;
- validate the payload;
- replace duplicated lifecycle prose with framework capability references;
- preserve NizamIQ-specific scope and GA planning;
- supersede stale planning documents explicitly;
- retain historical evidence without treating it as current authority.

Consumer adoption (handover F-016..F-020) is out of scope for phase
`005-ecosystem-cycle` and is scheduled as the successor programme phase, gated on the
framework release (H-FRAMEWORK-RELEASE) and H-CONSUMER-UPGRADE.

## Risks

- Over-generalising from one ecosystem.
- Creating excessive schemas before real use.
- Expanding the framework faster than deterministic validation.
- Duplicating existing planning or release-train protocols.
- Treating AI-generated audit findings as authoritative without independent evidence.
- Increasing context requirements rather than reducing them.

## Mitigations

- Implement the minimum viable lifecycle first.
- Dogfood before consumer adoption.
- Keep protocols modular and indexed.
- Require schema validation.
- Prefer deterministic collectors.
- Preserve operator gates.
- Record all friction as debt.
- Delay optional complexity and GA packaging features until the initial loop works.

## Acceptance Criteria

- NIP accepted by operator. *(satisfied 2026-07-17)*
- Ecosystem module indexed and path-valid.
- Initial schemas validate positive and negative fixtures.
- Preflight tool generates a schema-valid result.
- Framework dogfood completes with externalised evidence.
- Existing compliance and bootstrap tests remain green.
- Release is tagged and documented.
- NizamIQ adoption uses the released tag. *(successor programme phase)*
