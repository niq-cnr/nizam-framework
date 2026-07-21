---
id: nizam-roadmap
title: "Forward Roadmap — nizam-framework"
description: "The durable forward-planning surface: outstanding human gates, the candidate scope for the next phase, and the strategic decisions the next planning cycle must resolve."
version: 0.17.0
status: active
authoritative_source: docs/planning/ROADMAP.md
change_log:
  - version: "0.17.0"
    date: "2026-07-21"
    summary: "Phase 008 ACTIVATED (operator verbatim: 'Approved. Please proceed', gate H-PHASE-008, 2026-07-21): the Proposed Next Phase — Phase 008 section becomes the Plan of Record banner. current_phase advanced 007-consumer-adoption -> 008-consumer-readiness in manifest + run_state (event phase_activated, recorded before any feature execution per NDEBT-018); product_spec_008 flipped draft -> active (1.1.0); scope budget reset to 1010 (phase-007 final archived). operator_gates.md records H-PHASE-008 SATISFIED. Execution begins with the ungated DAG root feature 065 (governance-root resolution in tools/ecosystem_preflight.py; ADR-004 decision 1 / NDEBT-027) — the first real code change of the 0-n programme."
  - version: "0.16.0"
    date: "2026-07-21"
    summary: "Phase 008 PROPOSED (operator 'open phase 008'). The phase-008 section rolls from Authorized-candidate to a proposal-authored banner: the Planner artifacts .agent/product_spec_008.md (status draft) and .agent/feature_list_008.json (features 065-069, DAG-validated acyclic, est 1010) now exist, awaiting activation gate H-PHASE-008. Scope narrowed to NIP-0002 Stage 1 (consumer-readiness — the prerequisite for every larger project count): ADR-004's governance-root resolution (NDEBT-027) + provenance-pin anchoring (NDEBT-028), bootstrap commit-SHA pinning (NDEBT-033), GIP Sec 5.1 brownfield reconciliation (NDEBT-032), then a re-pilot to prove the fixed single-project loop. NIP-0002 Stages 2-4 (0-case greenfield genesis NDEBT-030, n-case multi-repo tooling + membership registry NDEBT-031, 04/05 coordination protocols, NDEBT-029) are carried as phase-009 candidate scope, evidence-gated on the phase-008 re-pilot. manifest.json gains the phase-008 entry (pending/proposed); current_phase stays 007-consumer-adoption until activation."
  - version: "0.15.0"
    date: "2026-07-21"
    summary: "PR #42 review corrections: fixed two stale 'NIP-0002 (Proposed — awaiting H-NIP)' references (completion banner + Current Position) to Accepted/phase-008-selected; corrected the open-debt count from 'seven' to 'six' phase-007 pilot rows (NDEBT-027..032); and added NDEBT-033 (bootstrap provenance pins tag name not resolved commit SHA, deferred to phase 008) to the open-debt roll. No plan-of-record change."
  - version: "0.14.0"
    date: "2026-07-21"
    summary: "NIP-0002 (The 0–n Project Spectrum) ACCEPTED by the operator via gate H-NIP (verbatim 'NIP-0002 is accepted'), selecting phase 008 as its realization. The 'Proposed Next Phase — Phase 008 (Candidate)' section rolled to 'Next Phase — Phase 008 (Authorized)', recording the acceptance and that selection is not activation (phase 008 still needs product_spec_008 + feature_list_008 + H-PHASE-008, the next planning cycle). Recorded alongside .agent/run_state.json (operator_gate_decision) and docs/planning/operator_gates.md (H-NIP second exercise, v0.4.0)."
  - version: "0.13.0"
    date: "2026-07-21"
    summary: "Phase-007 completion refresh + phase-008 candidate scope. Phase 007 (Consumer-Adoption Enablement & First External Pilot, features 060-064) marked COMPLETE 2026-07-21: the phase-007 Plan-of-Record banner carries the completion record; Current Position rolled to 2026-07-21 (phases 001-007 complete); Track 4 marked EXERCISED against a scratch consumer (feature 063 — adoption held, friction NDEBT-027..032, ADR-004 + NIP-0002), with a real-consumer pilot still open. Added the Proposed Next Phase — Phase 008 (Candidate): The 0-n Project Spectrum section, awaiting operator acceptance of NIP-0002 (gate H-NIP): an evidence-prioritized staged plan (consumer-readiness ADR-004 fixes first, then the 0 greenfield-genesis capability, the n multi-repo tooling + membership registry, then the deferred 04/05 coordination protocols). Open-debt roll updated with NDEBT-027..032. (Also corrected the frontmatter version field, which had drifted behind its own change_log at 0.10.0 vs 0.12.0.)"
  - version: "0.12.0"
    date: "2026-07-20"
    summary: "Phase 007 activated (operator verbatim: 'Authorized to activate now', gate H-PHASE-007, 2026-07-20): the Proposed Next Phase section becomes the Plan of Record banner. current_phase advanced 006-enforcement-closure -> 007-consumer-adoption in manifest + run_state (event phase_activated); product_spec_007 flipped draft -> active (1.1.0); scope budget reset to 870 (phase-006 final archived). Execution begins with the framework-internal features 060 (author ecosystem/00_ecosystem_bootstrap.md) then 061 (define H-CONSUMER-UPGRADE); the pilot (063-064) stays deferred pending operator-authorized consumer-repo access."
  - version: "0.11.0"
    date: "2026-07-20"
    summary: "Added the Proposed Next Phase section — phase 007 (Consumer-Adoption Enablement & First External Pilot, features 060-064, est 870 lines) PROPOSED and awaiting operator authorization (gate H-PHASE-007). Scope: author the missing Bootstrap-stage protocol (ecosystem/00_ecosystem_bootstrap.md) + define the reserved gate H-CONSUMER-UPGRADE, then run the first REAL external-consumer pilot (Track 4 / handover F-016..F-020) and prioritise the deferred protocols from real friction — NOT speculative authoring of 04/05/06/08. Planner artifacts .agent/product_spec_007.md (status draft) + .agent/feature_list_007.json (DAG-validated acyclic) exist; current_phase stays 006-enforcement-closure until activation. The pilot (features 063-064) additionally requires operator-authorized access to a consumer repository — the canonical target nizamiq/nizamiq-strategy is outside this session's scope."
  - version: "0.10.0"
    date: "2026-07-20"
    summary: "Phase-006 completion refresh: phase 006 (Enforcement Closure & Hardening, features 049-059) COMPLETE and v0.8.0 released 2026-07-20 (operator sign-off via the PR #38 merge + operator-pushed annotated tag v0.8.0 at 183e468; release.yml published the GitHub Release page from the [0.8.0] CHANGELOG section, run 29717579479 success). The Plan of Record banner is marked complete and Current Position rolled to 2026-07-20 (phases 001-006 complete, validator 15/15 C1-C15, payload 11/11, self-test 47/47). The enforcement-closure debt backlog (NDEBT-004/005/007-024) is fully Resolved; one new Low item NDEBT-026 (validator C15 is coverage-only, not a mapping-direction validator) was surfaced in the PR #38 review and registered."
  - version: "0.9.0"
    date: "2026-07-20"
    summary: "Track 3 (mechanize-or-descope the constitutional layer) RESOLVED by phase-006 feature 058 (gate H-CONSTITUTIONAL, operator decision authorized verbatim): two surfaces mechanized (standard/provenance_policy.md SHA-pinned-Actions via validate.sh check C14; standard/capability_profiles.md 5-profile-to-5-role correspondence via check C15), the remaining seven marked consumer-aspirational, and docs/guide/index.html refreshed to reflect the outcome. Track 3's section now carries the resolution banner."
  - version: "0.8.0"
    date: "2026-07-19"
    summary: "Phase 006 activated (operator verbatim: 'Approved. Proceed with the logical next steps.', gate H-PHASE-006, 2026-07-19): the Proposed Next Phase section becomes the Plan of Record banner. Track 1 item 2 truth-rolled to EXECUTED — the user guide is live on GitHub Pages (first deploy succeeded 2026-07-19 00:23 UTC after the one-time enable; verified serving the v0.7.0 guide), closing the last gate inherited from phase 003."
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

## Plan of Record (2026-07-21) — Phase 008 Activated: 0–n Project Spectrum, Stage 1 — Consumer-Readiness

**Phase `008-consumer-readiness` is ACTIVE — plan of record.** On 2026-07-21 the operator
authorized activation (verbatim: **"Approved. Please proceed"**, satisfying gate
**H-PHASE-008**; recorded in `.agent/run_state.json` event `phase_activated` before any
feature execution, per the NDEBT-018 rule). It realizes `NIP-0002` (accepted via gate H-NIP).
`docs/planning/manifest.json` carries `current_phase: 008-consumer-readiness` with the
phase-008 entry `status: in_progress`; `.agent/product_spec_008.md` is active (1.1.0); the
scope budget was reset to 1010 (phase-007 final archived). The planner artifacts
(`.agent/feature_list_008.json` — features 065–069, DAG-validated acyclic, roots {065, 068})
are the plan of record. Execution begins with the ungated DAG root feature **065**
(governance-root resolution) — the first real *code* change of the 0–n programme.

**Scope — NIP-0002 Stage 1 only (prove-then-build).** NIP-0002's Staged Realization is
explicitly *evidence-led — no stage claimed working until proven against real evidence* — and
its **Stage 1 (consumer-readiness) is the prerequisite for every larger project count**. The
phase-007 pilot proved even the single-project (count-1) case is not consumer-ready, so phase
008 makes that case genuinely work and completes the "1" point of the spectrum, then re-pilots
to prove it. Features (evidence-prioritized from the pilot debt `NDEBT-027/028/032/033`):

1. **065 — Governance-root resolution** (`ADR-004` decision 1, `NDEBT-027`) — tools locate the
   injected `.nizam/` payload instead of assuming the framework-root layout.
2. **066 — Provenance-pin anchoring** (`ADR-004` decision 2, `NDEBT-028`) — a Baseline's
   `framework_references` names the injected pin, not the consumer HEAD.
3. **067 — Bootstrap commit-SHA pinning** (`NDEBT-033`) — provenance records tag + resolved
   SHA; `--verify-only` rejects a moved tag.
4. **068 — Brownfield bootstrap reconciliation** (GIP §5.1, `NDEBT-032`) — `bootstrap.sh`
   preserves colliding pre-existing root files; completes the 1-brownfield point.
5. **069 — Re-pilot, prove, prioritize + phase close** — run the *fixed* loop against a real
   bootstrapped scratch consumer (clean Preflight PASS, correctly-anchored baseline, no
   workaround), then author the phase-009 candidate scope below and close the phase.

**Deferred → Phase-009 candidate scope (NIP-0002 Stages 2–4).** Held until Stage 1 is *proven*,
because each builds on single-project tools that must work first:
- **The 0-case — greenfield genesis** (`NDEBT-030`): create-and-scaffold a *new* project and
  bootstrap into it; the scope registry's `incubating` partition models the count-0→1 transition.
- **The n-case — multi-repo tooling** (`NDEBT-031`): iterate an ecosystem-membership registry
  (a set of repo-roots) instead of one `--repo-root`; promote
  `registry/scope_definition_patterns.md` to a required, validated membership artifact that sets `n`.
- **n-coordination protocols**: author `04_dependency_reconciliation.md` and
  `05_release_train_coordination.md` with companion schemas — where cross-repo ordering and
  release-train entry live.
- Cut a framework release carrying the audit/compare tools (`NDEBT-029`) — a release-train action.

A **real, non-scratch consumer pilot** remains an open acceptance criterion across the whole
0–n programme (the scratch pilot exercises loop *mechanics*, not product maturity).

## Plan of Record (2026-07-20) — Phase 007 Activated: Consumer-Adoption Enablement & First External Pilot — **COMPLETE 2026-07-21**

Phase `007-consumer-adoption` is **COMPLETE** (2026-07-21). It shipped the Bootstrap-stage
protocol (feature 060, amended to v0.2.0 to make the 0–n spectrum first-class), defined and
first-exercised the `H-CONSUMER-UPGRADE` gate (061, 063), ran the first non-self
ecosystem-cycle pilot against a scratch consumer (063 — adoption held: bootstrap + verify +
`validate.sh --payload` 11/11; friction recorded as `NDEBT-027`…`NDEBT-032`), and authored
the evidence-prioritized phase-008 candidate scope (064, above). The decisions were captured
formally as `NIP-0002` (Accepted 2026-07-21, gate H-NIP — selecting phase 008) and `ADR-004`
(Accepted). The conditional feature 062 was
intentionally not run (the scratch consumer had no colliding root files; carried as
`NDEBT-032`). On 2026-07-20 the operator authorized activation (verbatim: **"Authorized to
activate now"**, satisfying gate **H-PHASE-007**; recorded in `.agent/run_state.json` event
`phase_activated` before any feature execution). `docs/planning/manifest.json` carries
`current_phase: 007-consumer-adoption` with the phase-007 entry `status: in_progress`;
`.agent/product_spec_007.md` is active (1.1.0); the scope budget was reset to 870
(phase-006 final archived). The planner artifacts (`.agent/feature_list_007.json` —
5 features 060-064, DAG-validated acyclic, `original_estimate_lines` 870) are the plan
of record. Execution begins with the framework-internal features **060** (author the
Bootstrap-stage protocol) then **061** (define `H-CONSUMER-UPGRADE`); the pilot
(063-064) stays deferred pending operator-authorized consumer-repo access (below).

**Why now.** The core ecosystem loop (Preflight → Baseline → Audit → Compare) is
shipped, dogfooded, and released (v0.8.0). Two gaps remain: the lifecycle's **Bootstrap**
entry stage has no protocol document (`00_ecosystem_bootstrap.md`, still *Planned*
under `ecosystem/`) and its gate `H-CONSUMER-UPGRADE` is an undefined reserved name; and all
adoption evidence is still self-referential (Track 4, below). Phase 007 closes the
Bootstrap gap with the minimum authoring needed, then runs the first real pilot and
lets that evidence prioritise the remaining deferred protocols — it does **not** author
`04/05/06/08` speculatively (the framework's "no claim beyond evidence" rule).

**Scope (features 060-064).** 060 — author the Bootstrap-stage protocol
`00_ecosystem_bootstrap.md` (under `ecosystem/`, wrapping `standard/GIP.md` +
`bootstrap.sh`; flip its `ecosystem/README.md` status row Planned→Shipped); 061 — define the reserved gate `H-CONSUMER-UPGRADE` in
`docs/planning/operator_gates.md`; 062 (conditional) — implement GIP §5.1
rename-and-diff in `bootstrap.sh` for a consumer with pre-existing root files; 063 —
first external-consumer pilot (handover F-016/F-019: bootstrap a released tag into a
real consumer, run `tools/validate.sh --payload`, drive the core loop, record friction
as `NDEBT-*`); 064 — plan the next automation tranche from that friction (handover
F-020) and close the phase.

**Precondition for the pilot.** Features 060-062 are framework-internal and executable
immediately on activation. The pilot (063-064) additionally **requires
operator-authorized access to a consumer repository.** The canonical target
`nizamiq/nizamiq-strategy` is a different organization outside this session's GitHub
scope; activation must resolve which consumer repo the pilot runs against (the
canonical target via `add_repo` subject to org authorization, another operator-provided
repo, or a scratch consumer to exercise loop mechanics). This directly executes Track 4
below.

## Plan of Record (2026-07-19) — Phase 006 Activated: Enforcement Closure & Hardening

Phase `006-enforcement-closure` is now **COMPLETE** — all 11 features (049–059) shipped via PRs #28–#38 and v0.8.0 was released 2026-07-20 (see Current Position below); it was the current plan of record through phase close. On
2026-07-19 the operator authorized activation (verbatim: **"Approved. Proceed with
the logical next steps."**, satisfying gate **H-PHASE-006**; recorded in
`run_state` event `phase_activated` before any feature execution). The planner
artifacts (`.agent/product_spec_006.md`, now active 1.1.0;
`.agent/feature_list_006.json` — 11 features 049-059, DAG-validated acyclic,
`original_estimate_lines` 1720) are the plan of record; the manifest carries the
phase as `status: in_progress`, `current_phase: 006-enforcement-closure`.
Execution runs on the single branch `phase/006-enforcement-closure` with
sequential PRs into `main` (the stacked-PR pattern is retired after the
2026-07-18 collapse). Scope: the
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

## Current Position (2026-07-21)

- Phases 001–007 are complete. **Phase 007 (Consumer-Adoption Enablement & First
  External Pilot, features 060–064) is COMPLETE** (2026-07-21, on the phase-007 branch,
  not yet released): the Bootstrap-stage protocol shipped (feature 060; amended to
  v0.2.0 for the 0–n project spectrum), the `H-CONSUMER-UPGRADE` gate is defined (061)
  and first-exercised (063), the first non-self ecosystem-cycle pilot ran against a
  scratch consumer (063 — adoption held; friction recorded as `NDEBT-027`…`NDEBT-032`),
  and the evidence-prioritized phase-008 candidate scope is authored (064). Two governed
  docs capture the decisions: `NIP-0002` (0–n spectrum, Accepted 2026-07-21 via H-NIP — phase 008 selected) and
  `ADR-004` (consumer-readiness, Accepted). Phase 006 (features 049–059) landed
  on `main` via eleven sequential PRs #28–#38; the validator runs
  green at `SUMMARY: 15 passed, 0 failed` (C1–C15), payload mode at `11 passed, 0
  failed`, the fixtures self-test green, and the hermetic e2e bootstrap harness
  passes in CI.
- Latest released tag: v0.8.0 — the annotated tag was pushed by the operator
  2026-07-20 at the phase merge commit 183e468, executing H-FRAMEWORK-RELEASE after
  the recorded sign-off; `release.yml` auto-published the GitHub Release page from
  the `[0.8.0]` CHANGELOG section (run 29717579479, success). A MINOR release per
  `methodology/06_release_train.md` §3.2. The successor consumer-adoption phase
  (handover F-016..F-020) remains unblocked.
- Open debt: NDEBT-026 (Low, pre-existing) plus the six phase-007 pilot rows
  `NDEBT-027`…`NDEBT-032` — the consumer-readiness and 0–n-spectrum gaps the scratch
  pilot surfaced (governance-root assumption, framework-pin mis-anchoring, audit/compare
  not yet in a released tag, the absent 0-case, single-`--repo-root` tools, and the
  brownfield `bootstrap.sh` gap), each cross-referencing `ADR-004`/`NIP-0002` and
  sequenced into the phase-008 candidate scope above; plus `NDEBT-033` (Medium) — bootstrap
  provenance pins the tag name but not its resolved commit SHA (surfaced in the PR #42
  review), also deferred to phase 008. Phase 006 resolved the entire
  enforcement-closure backlog it inherited (NDEBT-004, -005, -007 through -024;
  NDEBT-001/002/003/006/025 were already Resolved). See `docs/planning/DEBT.md`.

## Track 1 — Outstanding Human Gates (no planning required)

These are recorded decisions awaiting execution by a human with release authority;
they need no new phase.

1. **Cut v0.6.0 — EXECUTED 2026-07-15.** The annotated tag `v0.6.0` was pushed at
   commit 955c1d7 per `methodology/06_release_train.md` (MINOR: additive, no breaking
   runtime change, `bootstrap.sh` unmodified). Residual: **publish the v0.6.0 GitHub
   Release page — EXECUTED 2026-07-15** (the page exists, published 05:53 UTC;
   every tag v0.1.0–v0.6.0 now has a published Release page).
2. **Publish the user guide to GitHub Pages — EXECUTED 2026-07-19.** Outstanding
   since phase 003, now closed: the operator performed the one-time Pages enable
   (Source: GitHub Actions) and the first `.github/workflows/pages.yml` deploy
   succeeded (run attempt 2, 2026-07-19 00:23 UTC). The guide is live at
   https://niq-cnr.github.io/nizam-framework/ — verified serving the v0.7.0
   content including the ecosystem module reference — and republishes
   automatically on every merge to `main` touching `docs/guide/`.
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

> **RESOLVED 2026-07-20 by phase-006 feature 058 (gate H-CONSTITUTIONAL).** The operator's per-document
> decision, authorized verbatim and recorded in `.agent/run_state.json`: **mechanize two** surfaces —
> `standard/provenance_policy.md`'s SHA-pinned-Actions rule (`tools/validate.sh` check C14) and
> `standard/capability_profiles.md`'s five-profile-to-five-role correspondence (check C15) — and **mark the
> remaining seven consumer-aspirational** (`standard/ci_gates.md`, `methodology/05_eval_and_trace.md`,
> `methodology/07_eval_gated_promotion.md`, `standard/mcp_policy.md`, `standard/permission_classes.md`,
> `standard/failure_modes.md`, `standard/cross_repo_governance.md`), with `docs/guide/index.html` refreshed to
> reflect the outcome. Each document now carries its decided enforcement state in frontmatter and a body
> banner. The problem statement below is retained for provenance.

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

## Track 4 — First External Consumer Pilot — **EXERCISED (scratch consumer) 2026-07-21**

All bootstrap evidence to date is self-referential: the e2e harness bootstraps the
framework into a scratch copy of itself. Before the constitutional layer grows
further, bootstrap a real second repository against a released tag, run
`tools/validate.sh --payload` in it, and feed every friction point back as debt.
This directly tests the NDEBT-004 and NDEBT-008 concerns in the environment they
actually describe, and produces the first non-self-referential adoption evidence.

**Exercised in phase 007 (feature 063) against a scratch/throwaway consumer** — a fresh
`git init` repo with genuinely foreign content (`src/calc.py` + `README`), bootstrapped
from the released `v0.8.0` tag (the first time the ecosystem tools ran against non-self
content). Adoption held: bootstrap clone→inject→verify PASS and `tools/validate.sh
--payload` green (11/11) inside the consumer. The core loop (Preflight → Baseline →
Audit → Compare) then surfaced real friction, recorded as `NDEBT-027`…`NDEBT-032`
(evidence `.agent/evidence/pilot-063/`) and captured as `ADR-004` + `NIP-0002`. **Still
open:** a **real, non-scratch consumer pilot** — a scratch repo exercises loop
*mechanics*, not a real project's engineering maturity, so the production-proven adoption
criterion carries forward to a future real-repo pilot (phase 008 candidate scope above).

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
