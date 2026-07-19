---
id: nizam-product-spec-006
title: "Nizam Framework — Phase 006 Spec (Enforcement Closure & Hardening) — PROPOSAL"
description: "Phase-006 proposal: close the enforcement gaps and consumer-reality defects accumulated in the open debt register (NDEBT-004..024; NDEBT-025 was resolved pre-phase), codify the operational rules phase 005 proved by incident, and take the deferred constitutional-layer mechanize-or-descope decision — ending at a v0.8.0 release gate. PROPOSED, not activated: execution requires operator authorization (gate H-PHASE-006). Extends product_spec.md..product_spec_005.md; replaces none."
tags: [spec, self-compliance, enforcement, hardening, debt, phase-006, proposal]
status: draft
last_audited: "2026-07-18"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-18T00:00:00Z"
updated_at: "2026-07-18T00:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-18T00:00:00Z"
    summary: "Initial phase-006 proposal, authored on operator direction ('Please action items 1-3', item 3) immediately after the phase-005 close and the v0.7.0 release. Scope sourced from ROADMAP Track 2 (the pre-005 candidate scope), Track 3 (the constitutional-layer decision), and the 21-row open debt register. Frontmatter status stays draft until operator activation (gate H-PHASE-006) — the 005 lesson: status must track the decision lifecycle, not anticipate it."
---

# Nizam Framework — Phase 006 Spec (Enforcement Closure & Hardening)

**Status: PROPOSED — awaiting operator authorization (gate H-PHASE-006).** This
document becomes the plan of record only when the operator authorizes activation;
until then `docs/planning/manifest.json` carries phase 006 as `status: pending` and
`current_phase` remains `005-ecosystem-cycle` (complete). Per
`methodology/00_planning.md`, a phase becomes real only when a Planner-produced spec
and a DAG-validated feature list exist AND a human authorizes activation — this
proposal supplies the first two.

## 1. Purpose

Phase 005 shipped the Ecosystem Engineering Cycle and dogfooded it against this
repository; in doing so it grew the open debt register to 21 rows and proved several
operational rules only by incident (probe isolation, gate-decision-before-execution,
verification-authoring anti-patterns). Phase 006 closes the loop: mechanize the
enforcement the register says is missing, fix the defects real consumers reported,
codify the incident-proven rules into the standards that bind by document, and take
the one strategic decision the roadmap has carried since 2026-07-12 (Track 3:
mechanize or descope the constitutional layer).

## 2. Scope

### 2.1 In scope (features 049-059)

Debt-driven enforcement closure and hardening, framework side only — see the feature
summary (Section 4) and `.agent/feature_list_006.json` (11 features, DAG-validated
acyclic, original_estimate_lines 1720).

### 2.2 Out of scope

- **Consumer adoption** (handover F-016..F-020, targeting `nizamiq/nizamiq-strategy`):
  a separate, cross-repository successor programme phase, unblocked by the v0.7.0 tag
  but not part of this proposal — it requires its own operator authorization and
  access to the consumer repository.
- New ecosystem-module capability surface (protocol documents 00/04/05/06/08 and
  their optional schemas remain deferrable per NIP-0001 / product_spec_005 Sec 2.3).
- Any edit to committed `.agent/` evidence or audit artifacts (immutable).

## 3. Requirements — debt-register mapping

| Req | Debt rows | Closure |
|-----|-----------|---------|
| R1 Consumer-reality fixes | NDEBT-012 (issue #18), NDEBT-008 + NDEBT-004 | F-050, F-051 |
| R2 Enforcement gaps mechanized | NDEBT-007, NDEBT-009, NDEBT-015, NDEBT-016, NDEBT-005 | F-049, F-052, F-055 |
| R3 Roles & authoring standards codified | NDEBT-010, NDEBT-013, NDEBT-014, NDEBT-019, NDEBT-020 | F-053 |
| R4 Template/schema truth | NDEBT-011 | F-054 |
| R5 Ecosystem-tooling hardening | NDEBT-021, NDEBT-017, NDEBT-018, NDEBT-023, NDEBT-024 | F-056 |
| R6 Protocol completeness | NDEBT-022 | F-057 |
| R7 Constitutional-layer decision (Track 3) | — (strategic, not a debt row) | F-058 |
| R8 Release closure | — | F-059 (v0.8.0, H-FRAMEWORK-RELEASE) |

NDEBT-025 is excluded: remediated pre-phase (release.yml fix + live retitle,
2026-07-18). NDEBT-006, -001, -002, -003 are already Resolved.

## 4. Feature summary and DAG

Features 049-059 (numbering continues the repo-global sequence; 048 was the last
executed feature). Dependency DAG: 049, 050, 051, 053, 054, 056, 057, 058 are
independent roots; 052 depends on 049 (its self-test mode exercises the new skill.json
check); 055 depends on 052 (guards ride the same self-test surface); 059 (phase close
+ release prep) depends on all of 049-058. Topological order exists; no cycles.

Planner's note, learned from PR #20's review round: the per-feature
`acceptance_tests` in the feature list are forward-looking planning summaries; the
load-bearing verification is negotiated per-feature in each contract at execution
time, with exact-text pinning per the verification-authoring standard (whose
mechanization is itself F-053's deliverable).

## 5. Operator gates

- **H-PHASE-006** — activation of this proposal (required before any feature starts).
- **H-PAYLOAD-CONTRACT** (F-051) — the injected-payload/methodology contract decision
  (add `methodology/` to the payload vs. declare pinned-checkout resolution
  canonical): a standards decision the operator takes; the feature implements
  whichever branch is chosen.
- **H-CONSTITUTIONAL** (F-058) — the Track 3 mechanize-or-descope decision, taken per
  constitutional document; the feature implements the recorded decisions.
- **H-FRAMEWORK-RELEASE** (F-059) — v0.8.0 sign-off + tag, operator-executed, with
  the release-readiness checklist pattern proven in 045.

## 6. Scope budget

original_estimate_lines 1720 (sum of per-feature estimates; 130% ceiling 2236).
Docs/standards edits dominate (F-053, F-058); the largest code deltas are the
validator extensions (F-049, F-052, F-055) and the preflight hardening (F-056).
Re-baseline through the operator per `methodology/00_planning.md` Section 9 if
breached — the 005 precedent applies.
