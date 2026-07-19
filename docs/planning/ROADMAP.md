---
id: nizam-roadmap
title: "Forward Roadmap — nizam-framework"
description: "The durable forward-planning surface: outstanding human gates, the candidate scope for the next phase, and the strategic decisions the next planning cycle must resolve."
version: 0.7.0
status: active
authoritative_source: docs/planning/ROADMAP.md
change_log:
  - version: "0.7.0"
    date: "2026-07-18"
    summary: "Post-v0.7.0 actions (operator-directed): added the Proposed Next Phase section — phase 006 (Enforcement Closure & Hardening, features 049-059, est 1720 lines) PROPOSED and awaiting operator authorization (gate H-PHASE-006); Track 1 item 3 (v0.7.0 Release title) marked executed via the NDEBT-025 workflow fix + live retitle; Track 1 item 2 (GitHub Pages) marked mechanized via the new pages.yml workflow, publishing on merge."
  - version: "0.6.0"
    date: "2026-07-18"
    summary: "Phase-005 completion refresh: v0.7.0 released (annotated tag pushed by the operator at merge commit 4833322 after the recorded H-FRAMEWORK-RELEASE sign-off; Release page auto-published by release.yml, title defect NDEBT-025). Current Position updated to 2026-07-18 (phases 001-005 complete, C1-C12 sweep, open-debt roll refreshed through NDEBT-025); Plan of Record banner marked complete; Track 1 gains the v0.6.0-Release-page execution record and the v0.7.0 title-fix action."
  - version: "0.5.0"
    date: "2026-07-18"
    summary: "Feature 046 (PR-stack review response): rewrote the stale Sequencing Recommendation sentence (which had wrongly continued to call Track 2 the phase-005 selection) to correctly frame Track 2 as candidate scope for a subsequent phase, consistent with the existing Track 2 supersession note. No other content changed."
  - version: "0.4.0"
    date: "2026-07-17"
    summary: "Added a Dogfood Audit + Delta subsection (feature 044, audit-id audit-2026-07-17-cba6422): 2 new findings (NDEBT-017/018), 1 stale (NDEBT-016), 0 in-window resolved (NDEBT-002 previously resolved (pre-baseline-1))."
  - version: "0.3.0"
    date: "2026-07-17"
    summary: "Phase 005 activated as the Ecosystem Engineering Cycle (framework side). Operator accepted NIP-0001 on 2026-07-17 ('approved. expedite.', gate H-NIP), which selects phase 005's scope. Added a 'Plan of Record' banner recording the activation and marked the former Track 2 candidate ('Consumer Reality & Enforcement Closure') as superseded-as-the-phase-005-selection: its enforcement-closure debt items (NDEBT-007/008/009/010/011/012/005) remain candidate scope for a subsequent phase and are partly exercisable by the framework self-dogfood (features 043-044). Prior content preserved."
  - version: "0.2.0"
    date: "2026-07-15"
    summary: "Post-release refresh after the 2026-07-15 release-readiness audit: v0.6.0 annotated tag cut (Track 1 gate 1 executed; residual GitHub Release publication recorded), Current Position updated from v0.5.3 to v0.6.0, NDEBT-012 (payload-validator CWD sensitivity, issue #18) added to the open-debt roll and the phase 005 candidate scope."
  - version: "0.1.0"
    date: "2026-07-12"
    summary: "Initial roadmap, created during the 2026-07-12 external project review: records the v0.6.0 and GitHub Pages human gates, a debt-driven phase 005 candidate scope, and the mechanize-or-descope decision for the constitutional policy surface."
---

# Forward Roadmap

## Proposed Next Phase (2026-07-18) — 006 Enforcement Closure & Hardening [AWAITING OPERATOR AUTHORIZATION]

Phase `006-enforcement-closure` is **PROPOSED, not activated**: the planner artifacts
exist (`.agent/product_spec_006.md`, `.agent/feature_list_006.json` — 11 features
049-059, DAG-validated acyclic, `original_estimate_lines` 1720), the manifest carries
the phase as `status: pending`, and per `methodology/00_planning.md` execution begins
only when the operator authorizes activation (gate **H-PHASE-006**). Scope: the
debt-driven enforcement closure (Track 2's revived candidates NDEBT-004/005/007/008/
009/010/011/012 plus the phase-005 additions NDEBT-013..024), codification of the
incident-proven operational rules, the Track 3 constitutional mechanize-or-descope
decision (operator gate H-CONSTITUTIONAL), the injected-payload contract decision
(H-PAYLOAD-CONTRACT), and a v0.8.0 release gate (H-FRAMEWORK-RELEASE). Consumer
adoption (handover F-016..F-020, `nizamiq/nizamiq-strategy`) is a separate
cross-repository successor programme phase, not part of this proposal.

## Plan of Record (2026-07-17) — Phase 005 Activated: Ecosystem Engineering Cycle

Phase `005-ecosystem-cycle` — activated as the plan of record on 2026-07-17 — is
now **COMPLETE** (v0.7.0 released 2026-07-18; see Current Position below). On
2026-07-17 the ecosystem operator accepted **NIP-0001 — Ecosystem Engineering
Cycle** (`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`) via the remote-control
message **"approved. expedite."**, satisfying gate **H-NIP** and authorizing phase
activation. The Planner produced the phase-005 spec (`.agent/product_spec_005.md`)
and a DAG-validated feature list (`.agent/feature_list_005.json`, 15 features
031-045, `original_estimate_lines` 2300); `docs/planning/manifest.json` now carries
phase 005 as `status: in_progress`, `activation_state: active`, `current_phase:
005-ecosystem-cycle`.

**Scope:** framework side only (handover F-001..F-015) — the ecosystem module
protocols, the baseline / preflight-verdict / engineering-finding schemas, capability
routing, a deterministic preflight CLI, a validator + CI fixtures extension, and
framework self-dogfood evidence, ending at a human-gated framework release
(H-FRAMEWORK-RELEASE). Consumer adoption (handover F-016..F-020, targeting
`nizamiq/nizamiq-strategy`) is deferred to the successor programme phase, gated on
that release.

**Phase-005 human gates — final disposition (2026-07-18):** H-NIP satisfied
2026-07-17; H-DOGFOOD-EXCEPTION exercised twice, both operator-approved with
recorded verbatim authorizations; the scope re-baseline 2300→3500 was
operator-authorized (H-FRAMEWORK-SCOPE was subsumed by the activation
authorization and that re-baseline — no standalone scope-lock event was executed,
stated plainly rather than backfilled); H-FRAMEWORK-RELEASE executed 2026-07-18
(operator sign-off recorded at 31f3fff before the tag, per the NDEBT-018 rule,
then the operator-pushed annotated tag v0.7.0 at 4833322); H-RISK not required
(the DEBT Open register carries zero High/Critical rows at close).

**Relationship to the prior candidate scope:** the former "Track 2 — Phase 005
Candidate Scope: Consumer Reality & Enforcement Closure" (below) is **superseded as
the phase-005 selection** by the operator-accepted NIP-0001. Its enforcement-closure
debt items (NDEBT-007/008/009/010/011/012 and NDEBT-005) remain candidate scope for a
subsequent phase; several are directly exercised as friction evidence by the
framework self-dogfood (features 043-044) and by the successor consumer-adoption
phase. The Track 1 human gates and Tracks 3-4 below remain valid forward intent.

## Purpose and Authority

This document is the durable forward-planning surface for the framework. It is
**pre-planning intent, not a plan of record**: under `methodology/00_planning.md`, a
phase becomes real only when a Planner produces a product spec and a DAG-validated
feature list and a human authorizes activation. Until then, everything below is
candidate scope. `docs/planning/manifest.json` points here via its `forward_planning`
key; this file MUST be updated at each phase close so the repository always states
what comes next (the gap this file closes: phases 001–004 completed with no recorded
successor, leaving open debt deferred to unscoped "future phases").

## Current Position (2026-07-18)

- Phases 001–005 are complete. Phase 005 (Ecosystem Engineering Cycle, framework
  side) landed on `main` via the re-landing PR #25 (merge commit 4833322) after the
  2026-07-18 stack collapse; the validator runs green at `SUMMARY: 12 passed, 0
  failed` (C1–C12), payload mode at `10 passed, 0 failed`, and the hermetic e2e
  bootstrap harness passes in CI.
- Latest released tag: v0.7.0 — the annotated tag was pushed by the operator
  2026-07-18 at the phase merge commit 4833322, executing H-FRAMEWORK-RELEASE after
  the recorded sign-off; `release.yml` auto-published the GitHub Release page from
  the `[0.7.0]` CHANGELOG section (its title defect is NDEBT-025, Track 1 item 3).
  The successor consumer-adoption phase (handover F-016..F-020) is now unblocked.
- Open debt: NDEBT-004, NDEBT-005, NDEBT-007 through NDEBT-024 (20 Open rows, all
  Low or Medium; NDEBT-001/002/003/006/025 are Resolved — 025 on 2026-07-18 via the
  release.yml title fix and live retitle; see `docs/planning/DEBT.md`).

## Track 1 — Outstanding Human Gates (no planning required)

These are recorded decisions awaiting execution by a human with release authority;
they need no new phase.

1. **Cut v0.6.0 — EXECUTED 2026-07-15.** The annotated tag `v0.6.0` was pushed at
   commit 955c1d7 per `methodology/06_release_train.md` (MINOR: additive, no breaking
   runtime change, `bootstrap.sh` unmodified). Residual: **publish the v0.6.0 GitHub
   Release page — EXECUTED 2026-07-15** (the page exists, published 05:53 UTC;
   every tag v0.1.0–v0.6.0 now has a published Release page).
2. **Publish the user guide to GitHub Pages — MECHANIZED 2026-07-18.** Outstanding
   since phase 003; `.github/workflows/pages.yml` now publishes `docs/guide/` on
   every merge to `main` touching the guide (and on dispatch). One-time
   prerequisite for the operator: enable Pages with Source "GitHub Actions"
   (Settings → Pages) — the default GITHUB_TOKEN cannot create the Pages site, so
   the job fails loudly at the configure step until that one-click enable is done,
   after which publication is fully automatic.
3. **Fix the v0.7.0 GitHub Release page title — EXECUTED 2026-07-18.** The title
   now reads `v0.7.0 — Ecosystem Engineering Cycle` (corrected by a branch-scoped
   one-shot applying the fixed `release.yml` extraction logic; body untouched).
   NDEBT-025 is Resolved: the workflow now derives the title from the genuine tag
   object's real type and fails loudly on a remote/local type disagreement.

## Track 2 — [SUPERSEDED as the phase-005 selection, 2026-07-17] Candidate Scope: Consumer Reality & Enforcement Closure

> **Superseded 2026-07-17:** phase 005 was activated as the Ecosystem Engineering
> Cycle (see the Plan of Record banner above) on the operator-accepted NIP-0001. The
> enforcement-closure items below are NOT the phase-005 scope; they remain candidate
> scope for a subsequent phase and are partly exercised as friction evidence by the
> phase-005 framework self-dogfood (features 043-044). Retained verbatim as the
> durable candidate-scope record.

The highest-leverage next phase closes the gap between what the framework enforces on
itself and what a real consumer experiences. Candidate features, sourced from the open
debt register (IDs refer to `docs/planning/DEBT.md`):

1. **Gate `tools/skill.json` content** (NDEBT-007): JSON-parse it, resolve every
   capability `module` path and the `entry_point` in default and `--payload` modes,
   with a negative fixture. This closes the enforcement hole that let a broken module
   pointer ship from v0.4.0 to v0.5.3.
2. **Resolve the injected-payload/methodology contradiction** (NDEBT-008, with
   NDEBT-004): decide whether `methodology/` joins the injected payload or
   pinned-checkout resolution becomes the stated contract for consumer installs, then
   align `bootstrap.sh`, `standard/GIP.md`, `tools/interface.md`, the payload-mode
   validator rules, and the e2e assertions with that single decision.
3. **Wire the negative fixtures into CI** (NDEBT-009): a fixtures job asserting each
   fixture fails its targeted check, so the validator's own checks cannot silently go
   vacuous.
4. **Define the Orchestrator role in the AGF** (NDEBT-010): the role is load-bearing
   across capability profiles, permission classes, MCP policy, the release train, and
   the framework's entire run history, yet undefined in the authoritative role
   registry.
5. **Recurrence guards for enumeration drift** (NDEBT-005): mechanize
   enumeration-completeness and bare-cross-reference checks, ideally sourced from a
   canonical index rather than hand-maintained lists.
6. **Align the work-packet template with its schema** (NDEBT-011).
7. **Fix the payload validator's CWD sensitivity** (NDEBT-012): anchor
   `tools/validate.sh --payload` path resolution to the script/payload root so
   `bash .nizam/tools/validate.sh --payload` from a consumer repository root behaves
   identically to invocation from inside `.nizam/`. Sourced from the first real
   external-consumer bug report (issue #18) — the exact consumer-reality evidence
   this phase exists to generate.

## Track 3 — Strategic Decision: Mechanize or Descope the Constitutional Layer

The v0.4.0 NMF hybrid shipped a constitutional policy surface (capability profiles,
the MERGE_READY CI-gate formula, eval-and-trace, eval-gated promotion, MCP policy,
failure modes, provenance, permission classes, cross-repo governance) that is
documentation-only: none of it is enforced by this repository's CI, none of it is
exercised by a consumer, and it entered the repository outside the framework's own
planning pipeline (recorded honestly in
`docs/architecture/ADR-003-vibe-coding-manifesto-hybrid.md`).

The next planning cycle MUST resolve, per constitutional document, one of:

- **Mechanize** — give it an enforcement or verification surface in this repository
  (the way NDS Section 7 got `tools/validate.sh`), or a conformance checklist a
  consumer can actually run; or
- **Descope explicitly** — mark it consumer-aspirational in its own frontmatter/body
  so the framework's first-contact surfaces stop implying enforcement that does not
  exist.

Either resolution also requires refreshing `docs/guide/index.html`, which still
narrates the phase-003 world and does not mention the constitutional layer at all.

## Track 4 — First External Consumer Pilot

All bootstrap evidence to date is self-referential: the e2e harness bootstraps the
framework into a scratch copy of itself. Before the constitutional layer grows
further, bootstrap a real second repository against a released tag, run
`tools/validate.sh --payload` in it, and feed every friction point back as debt.
This directly tests the NDEBT-004 and NDEBT-008 concerns in the environment they
actually describe, and produces the first non-self-referential adoption evidence.

## Sequencing Recommendation

Track 1 is immediate (minutes of human effort). Track 2 was superseded as the phase-005 selection by NIP-0001 (see the
supersession note above) and remains candidate scope for a subsequent phase. Track 3's decision should be taken
during phase 005 planning — its outcome determines whether a phase 006 is an
enforcement phase or a documentation-truth phase. Track 4 can run in parallel with
phase 005 and should complete before any phase that expands cross-repo or
constitutional scope.

## Dogfood Audit + Delta (2026-07-17) -- Phase 005 Feature 044

Audit `audit-2026-07-17-cba6422` compares baseline `dogfood-2026-07-17-28c8253` (revision `e73cd04bad78c696c815bf253fb627a93f20c9c0`) against baseline `dogfood-2026-07-17-6d7a47b` (revision `cba6422c01ee024cd3c597adaed977590f6373ef`).

- new: 2 (F-audit044-ndebt-017, F-audit044-ndebt-018)
- resolved: 0 (NDEBT-002 previously resolved (pre-baseline-1), not an in-window transition)
- reopened: 0
- stale: 1 (F-audit044-ndebt-016)

NDEBT-015 remains the highest-value next self-compliance candidate, corroborating Track 2 item 1's existing NDEBT-007 pairing.
