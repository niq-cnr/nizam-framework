---
id: nizam-product-spec-005
title: "Nizam Framework — Phase 005 Spec (Ecosystem Engineering Cycle — Framework Side)"
description: "Phase-005 specification: implement and dogfood the framework side of the reusable, schema-governed Ecosystem Engineering Cycle (handover NIP-0001, features F-001..F-015). Adds the ecosystem module protocols, baseline/preflight/finding schemas, capability routing, a deterministic preflight CLI, validator/CI fixtures, and framework self-dogfood evidence, ending at a human-gated framework release. Consumer adoption (handover F-016..F-020) is explicitly deferred to the successor programme phase. Extends product_spec.md..product_spec_004.md; replaces none."
tags: [spec, ecosystem, governance, audit, dogfood, release-train, phase-005]
status: active
last_audited: "2026-07-17"
authoritative_source: NA
version: 1.1.0
spec_version: "1.0.0"
created_at: "2026-07-17T00:00:00Z"
updated_at: "2026-07-17T00:00:00Z"
change_log:
  - version: "1.1.0"
    date: "2026-07-18T00:00:00Z"
    summary: "Feature 046 (PR-stack review response): frontmatter status flipped draft -> active, correcting a truth-sync defect against the body's own Status: ACTIVE declaration and the already-active manifest phase-005 entry (activated 2026-07-17). Body and all other frontmatter fields unchanged."
  - version: "1.0.0"
    date: "2026-07-17T00:00:00Z"
    summary: "Initial phase-005 spec (Ecosystem Engineering Cycle, framework side). Derived from the accepted handover programme definition (NIP-0001, product_spec.md, feature_list.json, implementation_dag.md, work_packets.json, validation_and_dogfood_plan.md, operator_gates.md). ACTIVE plan of record — phase activation authorized by operator 2026-07-17 (\"approved. expedite.\", gate H-NIP)."
---

# Nizam Framework — Phase 005 Spec (Ecosystem Engineering Cycle — Framework Side)

**Status: ACTIVE — plan of record.** Phase `005-ecosystem-cycle` was authorized for
activation by the ecosystem operator on 2026-07-17 via remote-control message
**"approved. expedite."**, satisfying operator gate **H-NIP** (accept NIP-0001
before implementation becomes plan of record). This spec is derived from the accepted
handover programme definition in `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`
and the handover artifacts; it scopes phase 005 to the **framework side only**
(handover features F-001..F-015). It extends `.agent/product_spec.md`,
`.agent/product_spec_002.md`, `.agent/product_spec_003.md`, and
`.agent/product_spec_004.md`; it supersedes none.

## 1. Product Intent

Provide a reusable, framework-native lifecycle that lets an AI agent or engineering
team reconcile and assess a multi-repository ecosystem, coordinate the next
development train, and measure progress toward GA — using short, parameterised
invocations rather than embedding extensive governance instructions in each prompt.

The programme is **framework-first and dogfood-first**: implement in
`nizam-framework`, validate the framework against itself, then (in the successor
phase) release a tagged version and adopt it in `nizamiq-strategy`. Phase 005 covers
the first three of those steps up to — but not through — consumer adoption.

The canonical lifecycle Nizam defines is:

```text
Bootstrap -> Preflight -> Baseline -> Audit -> Plan -> Execute -> Verify -> Promote -> Compare -> Repeat
```

Nizam owns the reusable lifecycle, schemas, validation rules, and capability routing.
Each consumer ecosystem supplies its own registry, scope, architecture, product
slice, release trains, debt, environments, owners, thresholds, and operator gates.

## 2. Scope

### 2.1 In scope (framework side — handover F-001..F-015)

Phase 005 delivers the **minimal viable** ecosystem lifecycle on the framework side,
grouped into four pull requests plus a human-gated release:

- **PR-F1 — NIP and plan of record** (handover F-001): the accepted NIP-0001, the
  phase-005 planning artifacts, manifest activation, and the roadmap update.
- **PR-F2 — Core ecosystem protocols and schemas** (handover F-002..F-010): the
  ecosystem module index, the clean-state preflight / immutable baseline /
  engineering audit / progress comparison protocols, the baseline / preflight-verdict
  / engineering-finding schemas, and capability registration.
- **PR-F3 — Deterministic preflight tooling** (handover F-011..F-012): the minimum
  preflight CLI and the extended validator + CI fixtures.
- **PR-F4 — Framework dogfood evidence** (handover F-013..F-014): running the new
  cycle against `nizam-framework`, recording findings and a baseline delta, and
  updating the roadmap/debt register from evidence.
- **Framework release** (handover F-015): a reviewed semantic-version release cut
  after dogfood exit criteria pass — a HUMAN GATE (H-FRAMEWORK-RELEASE), recorded but
  not executed by the pipeline.

### 2.2 Out of scope (successor programme phase — handover F-016..F-020)

Consumer adoption is **explicitly out of scope for phase 005** and is deferred to the
successor programme phase, gated on the framework release:

- F-016 — Adopt released tag in `nizamiq-strategy` (re-bootstrap against the released
  tag).
- F-017 — Simplify NizamIQ governance prompts.
- F-018 — Reconcile NizamIQ planning authority.
- F-019 — Run first NizamIQ ecosystem preflight.
- F-020 — Plan the subsequent automation tranche from real consumer friction.

These features target `nizamiq/nizamiq-strategy` (a different repository) and require a
released, immutable framework tag as their precondition — a released tag cannot exist
until phase 005's H-FRAMEWORK-RELEASE gate is executed. F-020 (a framework-repo
feature) is nonetheless part of the successor programme because it depends on the
consumer preflight F-019 producing real friction evidence. Per the framework's
cross-repository discipline, adoption work does not begin before the framework
capability is implemented, dogfooded, and released.

### 2.3 Deferrable within the minimal viable release

Per the handover product spec, typed dependency extraction, complexity scoring, and
GA evidence packaging (the `04_dependency_reconciliation.md`,
`05_release_train_coordination.md`, `06_simplification_review.md`,
`08_ga_gate.md` protocols and their optional schemas
`dependency_graph`/`audit_delta`/`ecosystem_complexity`/`ga_evidence_index`) MAY be
protocol-only or deferred if they threaten the first release's coherence. The
mandatory first-release surface is the four core protocols
(preflight/baseline/audit/comparison), the three core schemas
(baseline/preflight-verdict/finding), capability routing, one preflight CLI,
fixtures + validation, and framework dogfood evidence. Scope-lock is an operator gate
(H-FRAMEWORK-SCOPE).

## 3. Users

- **Framework Maintainer** — adds or evolves reusable governance capabilities.
- **Ecosystem Operator** — approves scope, exceptions, release trains, risks,
  framework upgrades, and GA decisions.
- **Ecosystem Auditor** — collects evidence, assesses maturity, records findings.
- **Release-Train Planner** — transforms approved findings into dependency-ordered
  work packets.
- **Repository Agent** — executes approved repository-local work under existing Nizam
  controls.

## 4. Functional Requirements (framework side)

Derived from the handover product spec. FR-01..FR-11 are in scope for phase 005;
FR-12 (consumer adoption) is deferred to the successor phase.

| FR | Requirement | Realized by (framework feature) |
|----|-------------|---------------------------------|
| FR-01 | **Capability discovery** — the root capability index exposes ecosystem lifecycle capabilities with authoritative source paths. | 032 (module index), 040 (capability routing) |
| FR-02 | **Clean-state preflight** — a reusable preflight protocol and machine-readable verdict (PASS / PASS_WITH_EXCEPTIONS / FAIL). | 033 (protocol), 038 (verdict schema) |
| FR-03 | **Immutable baseline** — a point-in-time baseline over framework, repository, dependency, CI, planning, and evidence references. | 034 (protocol), 037 (baseline schema) |
| FR-04 | **Engineering findings** — a common schema for repository and ecosystem findings. | 035 (audit protocol), 039 (finding schema) |
| FR-05 | **Typed dependencies** — support dependency types beyond a single generic `depends_on`. | DEFERRABLE (protocol-only / successor; see §2.3) |
| FR-06 | **Audit lifecycle** — an evidence-first engineering audit with maturity states and confidence. | 035 (audit protocol), 039 (finding schema) |
| FR-07 | **Release-train coordination** — connect approved findings to cross-repository work packets and existing release-train controls. | DEFERRABLE (protocol-only / successor; see §2.3) |
| FR-08 | **Simplification review** — a recurring process for identifying duplication/complexity without authorising automatic consolidation. | DEFERRABLE (protocol-only / successor; see §2.3) |
| FR-09 | **Progress comparison** — how two approved baselines or audits are compared. | 036 (comparison protocol) |
| FR-10 | **Operator gates** — preserve explicit human approval for exceptions, release, risk acceptance, consolidation, train closure, and GA declaration. | Cross-cutting; see §8 |
| FR-11 | **Dogfood** — execute the lifecycle against the framework itself before consumer adoption. | 043 (preflight dogfood), 044 (audit + delta dogfood) |
| FR-12 | **Consumer adoption** — a consumer adopts by re-bootstrap against an immutable released tag. | OUT OF SCOPE — successor programme phase (§2.2) |

## 5. Non-Functional Requirements

- Runtime agnostic.
- Backwards compatible for non-adopting consumers.
- Schema validated (positive AND negative fixtures).
- Evidence externalised by path (never pasted terminal output).
- Minimal context loading.
- Deterministic collection where possible.
- No direct-`main` mutation; no autonomous merge or GA declaration.
- No framework-specific hardcoding of NizamIQ repository names or product
  architecture.
- Clear failure and rollback paths (revert the feature PR; never hand-edit consumer
  payloads or bypass tagged release discipline).

## 6. Feature Breakdown and PR Grouping

Phase 005 continues the framework's feature numbering (phase 004 ended at feature
030) at **031**. Each framework feature maps 1:1 to a handover feature ID to preserve
the accepted DAG and traceability; the `handover_feature_ids` field on each feature in
`.agent/feature_list_005.json` records the mapping.

| Framework | Handover | PR | Title | Operator gate |
|-----------|----------|----|-------|---------------|
| 031 | F-001 | PR-F1 | NIP-0001 acceptance + plan of record | H-NIP (satisfied) |
| 032 | F-002 | PR-F2 | Ecosystem module index | — |
| 033 | F-003 | PR-F2 | Clean-state preflight protocol | — |
| 034 | F-004 | PR-F2 | Immutable baseline protocol | — |
| 035 | F-005 | PR-F2 | Engineering audit protocol | — |
| 036 | F-006 | PR-F2 | Progress comparison protocol | — |
| 037 | F-007 | PR-F2 | Baseline schema + fixtures | — |
| 038 | F-008 | PR-F2 | Preflight verdict schema + fixtures | — |
| 039 | F-009 | PR-F2 | Engineering finding schema + fixtures | — |
| 040 | F-010 | PR-F2 | Register ecosystem capabilities | — |
| 041 | F-011 | PR-F3 | Minimum preflight CLI | — |
| 042 | F-012 | PR-F3 | Extend validator + CI fixtures | — |
| 043 | F-013 | PR-F4 | Dogfood framework preflight | H-DOGFOOD-EXCEPTION (if PASS_WITH_EXCEPTIONS) |
| 044 | F-014 | PR-F4 | Dogfood framework audit + delta | — |
| 045 | F-015 | Release | Release framework capability | H-FRAMEWORK-RELEASE |

Detailed acceptance criteria (including the handover acceptance criteria verbatim)
live in `.agent/feature_list_005.json`.

## 7. Execution Order (topological)

The DAG mirrors the accepted handover `implementation_dag.md`, re-expressed in
framework feature IDs. Validated: every dependency target exists (031..044), there
are no cycles, and a topological ordering exists.

```text
Parallel Group 1: 031 (F-001 NIP + plan of record — no dependencies)
Parallel Group 2: 032 (F-002 module index — dep 031)
                  033 (F-003 preflight protocol — dep 031)
Parallel Group 3: 034 (F-004 baseline protocol — dep 033)
                  038 (F-008 preflight verdict schema — dep 033)
Parallel Group 4: 035 (F-005 audit protocol — dep 034)
                  036 (F-006 comparison protocol — dep 034)
                  037 (F-007 baseline schema — dep 034)
Parallel Group 5: 039 (F-009 finding schema — dep 035)
                  040 (F-010 capability routing — dep 032,033,034,035,036)
                  041 (F-011 preflight CLI — dep 037,038)
Parallel Group 6: 042 (F-012 validator + CI fixtures — dep 037,038,039,041)
Sequential:       043 (F-013 preflight dogfood — dep 042)
                  044 (F-014 audit + delta dogfood — dep 043)
                  045 (F-015 release — dep 044; HUMAN GATE)
```

**Critical path** (from the handover, in framework IDs):
`031 -> 033 -> 034 -> 037/038 -> 041 -> 042 -> 043 -> 044 -> 045`.

**Safe parallelism** (from the handover): 032 and 033 can proceed after NIP
acceptance; 035 and 036 in parallel after the baseline protocol; the three schemas in
parallel after their protocols. Consumer adoption is not implemented before the
framework release.

## 8. Human Gates

Recorded per `operator_gates.md`. The pipeline records but never self-executes a
human gate.

1. **H-NIP — SATISFIED 2026-07-17.** Operator approved NIP-0001 ("approved.
   expedite."), making the ecosystem cycle the plan of record and authorizing phase
   activation.
2. **H-FRAMEWORK-SCOPE — OUTSTANDING.** Approve the minimum viable v1 capability
   (§2.3); prevent optional tooling/schemas from expanding the first release.
3. **H-DOGFOOD-EXCEPTION — OUTSTANDING.** Approve any `PASS_WITH_EXCEPTIONS` framework
   preflight result (feature 043) before execution continues.
4. **H-FRAMEWORK-RELEASE — OUTSTANDING.** Approve the semantic version, changelog,
   migration notes, and tag creation (feature 045). Expected classification: MINOR
   (additive module + schemas + tooling; no breaking runtime change) per
   `methodology/06_release_train.md`, subject to human confirmation.
5. **H-RISK — OUTSTANDING.** Accept any residual P1 engineering risk surfaced by the
   dogfood audit. Agents may not accept risk.

The remaining operator gates from `operator_gates.md` — H-CONSUMER-UPGRADE,
H-PLANNING-AUTHORITY, H-TRAIN-ENTRY, H-CONSOLIDATION, H-GA — belong to the successor
consumer-adoption programme phase and are not in scope for phase 005.

## 9. Dogfood and Validation Plan

Treat `nizam-framework` as a one-repository ecosystem (per the handover
`validation_and_dogfood_plan.md`).

**Validation hierarchy:** schema validation -> static path/index validation ->
positive fixtures -> negative fixtures -> unit tests for deterministic tooling ->
existing framework validator (`tools/validate.sh`, C1-C11) -> existing bootstrap
end-to-end test -> framework self-preflight -> framework self-audit ->
baseline-to-baseline comparison. (Consumer re-bootstrap and consumer preflight are
successor-phase steps.)

**Required first-run outputs** (feature 043):
`.agent/reconciliation/<id>/preflight.json`,
`.agent/reconciliation/<id>/baseline.json`, `.agent/evidence/<id>/`.

**Required second-run outputs** (feature 044): a second baseline plus an audit delta
proving unchanged facts remain stable, a deliberately changed fixture is detected,
resolved findings close only with evidence, and stale evidence is not silently
reused; `.agent/audits/<id>/findings.json` and `.agent/audits/<id>/report.md`.

**Negative test cases** (must be rejected): unsupported preflight verdict; missing
strategy/repository SHA; missing evidence path; finding marked resolved without
closure evidence; baseline mixing repository states without timestamps; PASS verdict
with blocking findings; PASS_WITH_EXCEPTIONS without operator-approval metadata;
capability path pointing at a missing protocol.

**Release exit criteria** (feature 045, human-gated): all existing framework
validation green; new schema fixtures green; dogfood preflight + audit + delta
completed; open dogfood defects recorded as debt; documentation reflects actual
implemented behaviour; no unresolved P0/P1 defect in the new capability; human
release approval obtained.

## 10. Constraints

- **No direct-`main` mutation; reviewed PRs only; no autonomous merge or GA
  declaration.** Rollback for any feature is to revert its PR — never hand-edit
  consumer payloads or bypass tagged release discipline.
- **Preserve the capability-router design.** `tools/SKILL.md` remains a router, not a
  mirror; no runtime-specific ecosystem skills are introduced (single
  runtime-agnostic skill).
- **Prefer schema-governed artifacts and deterministic tools over long prompts.**
- **Every new schema keeps `NIZAM.json` C4-green;** every new/edited shipped `.md`
  carries its NDS change record (C8); every new check/script is fixture-tested for
  each failure mode under `tools/fixtures/` (the C-check dogfood precedent).
- **Existing C1-C11 and bootstrap tests must stay green;** any new ecosystem
  validator check migrates the `SUMMARY:` count deterministically and is proven
  non-breaking against the current tree before landing.
- **No framework-specific hardcoding of NizamIQ repositories or architecture.**
- **Evidence externalised by path;** completion is never declared from authored files
  alone.
- **Three-strike circuit breaker** applies to every feature.
- **Immutable artifacts are off-limits** (prior-phase contracts, evidence, QA
  verdicts, and feature lists are audit records and MUST NOT be edited).

## 11. Success Metrics

- Short consumer invocation under 250 words (measured in the successor phase; the
  framework surface is designed for it here).
- 100% path-valid ecosystem capability entries (`NIZAM.json` C4-green).
- Positive and negative schema fixtures for every new schema.
- Framework self-preflight PASS, or an operator-approved PASS_WITH_EXCEPTIONS.
- No regression in existing validation (C1-C11 + bootstrap e2e stay green).
- A framework release is cut from a reviewed, human-approved, immutable tag
  (H-FRAMEWORK-RELEASE).

## 12. Traceability

Each framework feature (031..045) references its handover feature ID(s) via the
`handover_feature_ids` field in `.agent/feature_list_005.json` and carries the
handover acceptance criteria verbatim within its `acceptance_tests`. The accepted NIP
lives at `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`; the phase entry and
activation record live in `docs/planning/manifest.json`; the forward-planning context
and dogfood-driven roadmap updates live in `docs/planning/ROADMAP.md`.
