---
id: nizam-roadmap
title: "Forward Roadmap — nizam-framework"
description: "The durable forward-planning surface: outstanding human gates, the candidate scope for the next phase, and the strategic decisions the next planning cycle must resolve."
version: 0.31.0
status: active
authoritative_source: docs/planning/ROADMAP.md
change_log:
  - version: "0.31.0"
    date: "2026-07-22"
    summary: "PR #50 review (release-ledger reconciliation): the Current Position 'Open debt' summary was phase-008-era stale -- it still listed NDEBT-030 (the 0-case, resolved by phase 009) and NDEBT-031 (the n-case, resolved by phase 010) as open. Rewritten to the real current Open set (only NDEBT-029 release-timing + NDEBT-026 + NDEBT-034, none blocking) and to list the 0-n scope rows all Resolved (027/028/032/033 phase 008, 030 phase 009, 031 phase 010, 035 phase 011). Paired with docs/planning/DEBT.md v0.36.0, which moves NDEBT-030 Open -> Resolved (it was left stale in Open at phase-009 close). No plan-of-record change."
  - version: "0.30.0"
    date: "2026-07-22"
    summary: "Release-in-preparation: v0.9.0 (MINOR), the first release since v0.8.0, carrying phases 007-011 (consumer-adoption enablement + the full NIP-0002 0-n realization + the audit/compare tooling). Current Position gains a 'Release in preparation: v0.9.0 -- awaiting H-FRAMEWORK-RELEASE' entry recording the prepared release surface (CHANGELOG [0.9.0] section, version bumps in C10 lockstep across NIZAM.json/docs/guide/CONTEXT.md/README.md, readiness checklist .agent/evidence/release-readiness-v0.9.0.md) on the release base 1dd4971 (phase-011 merge, PR #49). The pipeline never self-tags: the operator signs off + pushes the annotated v0.9.0 tag, release.yml publishes. NDEBT-029 (audit/compare not in a released tag) stays Open until the tag exists carrying the whole 0-n loop; on the tag it resolves and the standing real non-scratch multi-repo pilot becomes runnable. v0.8.0 remains the latest RELEASED tag until then."
  - version: "0.29.0"
    date: "2026-07-22"
    summary: "Phase 011 (0-n Project Spectrum, Stage 4: n-Coordination Protocols, features 080-084) COMPLETE -- so NIP-0002's staged plan is now complete. The phase-011 Plan-of-Record banner carries the completion record (080 ecosystem/04 Plan stage + reconciliation_plan schema + H-PLANNING-AUTHORITY defined; 081 ecosystem/05 Promote stage + release_train_manifest schema + H-TRAIN-ENTRY defined; 082 ecosystem_reconcile.py; 083 ecosystem_release_train.py + assert_stage4 e2e; 084 pilot proved the layer end-to-end across a scratch 2-member ecosystem -- PASS aggregate -> PASS plan -> PASS train, both negatives enforced (cyclic -> FAIL, ungated -> FAIL), evidence .agent/evidence/pilot-084/). NDEBT-035 resolved. Current Position rolled to phases 001-011 complete. The phase-012 candidate scope (NDEBT-029 release cut carrying the whole 0-n loop + a real non-scratch multi-repo pilot + the remaining 06/08 Repeat/GA protocols with H-CONSOLIDATION/H-GA) is refined and validated against the pilot evidence -- confirmed, not re-ordered (the release cut is the natural next step). manifest + run_state reflect phase-011 completion. A real, non-scratch multi-repo pilot at a released tag remains the open production-maturity criterion."
  - version: "0.28.0"
    date: "2026-07-22"
    summary: "Phase 011 ACTIVATED (operator verbatim: 'Approved. Please proceed', gate H-PHASE-011, 2026-07-22, given after PR #48 merged the phase-011 proposal to main at 44a91fc): the 'Proposed Next Phase — Phase 011' banner becomes the Plan of Record banner. current_phase advanced 010-multi-repo -> 011-coordination-protocols in manifest + run_state (event phase_activated, recorded before any feature execution per NDEBT-018); product_spec_011 flipped draft -> active (1.1.0); scope budget reset to 1330 (phase-010 final already archived at phase-010 close). Execution begins with the ungated DAG root feature 080 (author ecosystem/04_dependency_reconciliation.md + schema/reconciliation_plan.schema.json + define the reserved H-PLANNING-AUTHORITY gate; NDEBT-035). The reserved gates H-PLANNING-AUTHORITY / H-TRAIN-ENTRY are DEFINED at features 080/081 and first exercised at the 084 pilot; H-CONSOLIDATION / H-GA (06/08 Repeat/GA) stay reserved. The release cut carrying the whole loop (NDEBT-029), a real non-scratch multi-repo pilot, and the 06/08 protocols stay phase-012 candidate scope."
  - version: "0.27.0"
    date: "2026-07-22"
    summary: "Phase 011 PROPOSED (authored after PR #47 merged phase 010). A new 'Proposed Next Phase — Phase 011' banner tops the roadmap: NIP-0002 Stage 4 — the n-coordination protocols (ecosystem/04_dependency_reconciliation + ecosystem/05_release_train_coordination, with companion schemas, where cross-repo ordering and release-train entry genuinely live; NDEBT-035), the FINAL stage of the 0-n staged plan (completing it completes NIP-0002). Features 080-084 (DAG root {080}, est 1330), realized by the Planner artifacts .agent/product_spec_011.md (status draft) + .agent/feature_list_011.json, awaiting activation gate H-PHASE-011. Scoped to NIP-0002 Stage 4 only (one stage at a time, as phases 008/009/010 took Stages 1/2/3): 080 the reconciliation protocol + schema + defining the reserved H-PLANNING-AUTHORITY gate; 081 the release-train protocol + schema + defining the reserved H-TRAIN-ENTRY gate; 082 the reconciliation tool (consuming the phase-010 aggregate); 083 the release-train tool + Stage-4 e2e coverage; 084 the pilot + phase close. The former phase-010 banner's 'Deferred -> Phase-011 candidate scope' subsection is annotated as now-authored; the release cut carrying the whole loop (NDEBT-029), a real non-scratch multi-repo pilot, and the remaining Repeat/GA protocols (06_simplification_review / 08_ga_gate with the reserved H-CONSOLIDATION / H-GA gates) are carried forward as phase-012 candidate scope. current_phase stays 010-multi-repo until activation; run_state untouched (a proposal is not an activation)."
  - version: "0.26.0"
    date: "2026-07-22"
    summary: "Phase 010 (0-n Project Spectrum, Stage 3: the n-case, features 075-079) COMPLETE. The phase-010 Plan-of-Record banner carries the completion record (075 required+validated membership registry; 076 ecosystem_membership_run.py iteration; 077 cross-repo aggregation + common-pin consistency into a schema-valid ecosystem-level result; 078 assert_multirepo hermetic n-case e2e; 079 pilot proved the n-case end-to-end across a scratch 3-member ecosystem, PASS aggregate + divergent-pin FAIL, evidence .agent/evidence/pilot-079/). NDEBT-031 resolved; Stage-4 coordination residue carved into NDEBT-035 (phase-011 candidate), per-member clone-cost friction into NDEBT-034. The phase-011 candidate scope (NIP-0002 Stage 4 + NDEBT-029 release + real pilot) is refined and VALIDATED against the pilot evidence -- confirmed, not re-ordered (the aggregate is the 04-reconciliation substrate). manifest + run_state reflect phase-010 completion. A real, non-scratch multi-repo pilot remains the open production-maturity criterion."
  - version: "0.25.0"
    date: "2026-07-22"
    summary: "Records-sync from the PR #47 CodeRabbit review: two prior deferred-scope annotations pointed readers to a 'Proposed Next Phase' banner at the top, but those banners have since become Plan-of-Record banners (phase 010 activated, phase 009 complete). Re-pointed the phase-009 banner's Phase-010 candidate-scope note to the 'Plan of Record — Phase 010 Activated' banner, and the phase-008 banner's Phase-009 candidate-scope note to the phase-009 'Plan of Record … COMPLETE' banner. No plan-of-record change; annotation truth-roll only."
  - version: "0.24.0"
    date: "2026-07-22"
    summary: "Phase 010 ACTIVATED (operator verbatim: 'Approved. Proceed with the phase-010 proposal + activation', gate H-PHASE-010, 2026-07-22): the 'Proposed Next Phase — Phase 010' banner becomes the Plan of Record banner (Activated). current_phase advanced 009-greenfield-genesis -> 010-multi-repo in manifest + run_state (event phase_activated, recorded before any feature execution per NDEBT-018); product_spec_010 flipped draft -> active (1.1.0); scope budget reset to 1160 (phase-009 final archived). operator_gates.md records H-PHASE-010 SATISFIED. Execution begins with the ungated DAG root feature 075 (the ecosystem-membership registry schema; NDEBT-031) — the first change of the n-case."
  - version: "0.23.0"
    date: "2026-07-22"
    summary: "Phase 010 PROPOSED (operator 'Approved. Proceed with the phase-010 proposal + activation'). A new 'Proposed Next Phase — Phase 010' banner tops the roadmap: the n-case (multi-repo tooling + the required, schema-validated ecosystem-membership registry, NDEBT-031), features 075-079 (DAG root {075}, est 1160), realized by the Planner artifacts .agent/product_spec_010.md (status draft) + .agent/feature_list_010.json, awaiting activation gate H-PHASE-010. Scoped to NIP-0002 Stage 3 only (one stage at a time, as phases 008/009 took Stages 1/2). The former phase-009 banner's 'Deferred -> Phase-010 candidate scope (Stages 3-4)' subsection is annotated as now-authored; NIP-0002 Stage 4 (04/05 coordination protocols, activating the reserved H-PLANNING-AUTHORITY / H-TRAIN-ENTRY gates), the release cut carrying the whole loop (NDEBT-029), and a real non-scratch multi-repo pilot are carried forward as phase-011 candidate scope. current_phase stays 009-greenfield-genesis until activation; run_state untouched (a proposal is not an activation)."
  - version: "0.22.0"
    date: "2026-07-22"
    summary: "Phase 009 (0-n Project Spectrum, Stage 2: Greenfield Genesis, features 070-074) COMPLETE. The phase-009 Plan-of-Record banner carries the completion record (070 protocol ecosystem/00 Section 8; 071 bootstrap.sh --genesis; 072 incubating->in_scope count-0->1 in scope_definition_patterns.md Section 2.3; 073 assert_genesis e2e; 074 pilot proved the 0-case, PASS_WITH_EXCEPTIONS, evidence .agent/evidence/pilot-074/). Current Position rolled to phases 001-009 complete. The phase-010 candidate scope (NIP-0002 Stages 3-4: n-case multi-repo tooling + membership registry NDEBT-031, 04/05 coordination protocols, NDEBT-029 release cut) is validated by the pilot (ordering confirmed -- the n-case builds on the incubating partition this phase populated) and carried forward; a real non-scratch greenfield pilot remains the open production-maturity criterion, and the genesis capability is not yet in a released tag (NDEBT-029). Awaiting operator: PR #46 merge + phase-010 planning."
  - version: "0.21.0"
    date: "2026-07-22"
    summary: "Phase 009 ACTIVATED (operator verbatim: 'Activate phase 009', gate H-PHASE-009, 2026-07-22): the 'Proposed Next Phase — Phase 009' banner becomes the Plan of Record banner (Activated). current_phase advanced 008-consumer-readiness -> 009-greenfield-genesis in manifest + run_state (event phase_activated, recorded before any feature execution per NDEBT-018); product_spec_009 flipped draft -> active (1.1.0); scope budget reset to 1000 (phase-008 final archived). operator_gates.md records H-PHASE-009 SATISFIED. Execution begins with the ungated DAG root feature 070 (the greenfield-genesis protocol; NDEBT-030) — the first code change of the 0-case."
  - version: "0.20.0"
    date: "2026-07-22"
    summary: "Phase 009 PROPOSED (operator 'Go', taking NIP-0002 Stage 2 next — one stage at a time as phase 008 took Stage 1). A new 'Proposed Next Phase — Phase 009' banner tops the roadmap: the 0-case (greenfield genesis, NDEBT-030), features 070-074 (DAG root {070}, est 1000), realized by the Planner artifacts .agent/product_spec_009.md (status draft) + .agent/feature_list_009.json, awaiting activation gate H-PHASE-009. The former 'Deferred -> Phase-009 candidate scope' subsection in the phase-008 banner is annotated as now-authored; NIP-0002 Stages 3-4 (n-case multi-repo tooling + membership registry NDEBT-031, 04/05 coordination protocols, NDEBT-029 release cut) are carried forward as phase-010 candidate scope. current_phase stays 008-consumer-readiness until activation; run_state untouched (a proposal is not an activation)."
  - version: "0.19.0"
    date: "2026-07-21"
    summary: "PR #45 review corrections (phase-close accuracy): the feature-069 re-pilot is described honestly as a SCRATCH/THROWAWAY consumer (a loop-mechanics proof), not a 'real' consumer — a real non-scratch consumer pilot stays the open production-maturity criterion. The open-debt roll is reconciled to the phase-008 close: NDEBT-027/028 (ADR-004, features 065/066) + NDEBT-032 (068) + NDEBT-033 (067) moved to RESOLVED; only NDEBT-026 + NDEBT-029/030/031 remain open (carried into phase-009 scope). No plan-of-record change."
  - version: "0.18.0"
    date: "2026-07-21"
    summary: "Phase 008 (0-n Project Spectrum, Stage 1: Consumer-Readiness, features 065-069) COMPLETE. The phase-008 Plan-of-Record banner carries the completion record (065/066 ADR-004 findings A/B; 067 SHA pin; 068 resolved-by-design Option A; 069 re-pilot proved A/B resolved against a freshly bootstrapped scratch consumer, evidence .agent/evidence/pilot-069/). Current Position rolled to phases 001-008 complete. The phase-009 candidate scope (NIP-0002 Stages 2-4: 0-case genesis, n-case multi-repo tooling + membership registry, 04/05 protocols) is validated by the re-pilot and carried forward; a real non-scratch consumer pilot remains the open production-maturity criterion. Awaiting operator: the 067-069 PR + phase-009 planning."
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

## Plan of Record (2026-07-22) — Phase 011: 0–n Project Spectrum, Stage 4 — n-Coordination Protocols (Dependency Reconciliation & Release-Train Coordination) — **COMPLETE 2026-07-22**

**Phase `011-coordination-protocols` is COMPLETE** (2026-07-22). It realized **NIP-0002 Stage 4 —
the n-coordination protocols**, the **final** stage of the 0–n staged plan — **so NIP-0002's staged
plan is now complete**. Activation was on 2026-07-22 (operator verbatim **"Approved. Please
proceed"**, gate **H-PHASE-011**, given after PR #48 merged the phase-011 proposal to `main` at
`44a91fc`; recorded in `.agent/run_state.json` event `phase_activated` before any feature execution,
per the NDEBT-018 rule). **080** authored `ecosystem/04` (the Plan stage) + `reconciliation_plan`
schema (topological-order invariant, C12) and defined `H-PLANNING-AUTHORITY`; **081** authored
`ecosystem/05` (the Promote stage) + `release_train_manifest` schema (trace-to-plan invariant, C12)
and defined `H-TRAIN-ENTRY`; **082** added `tools/ecosystem_reconcile.py` (aggregate + findings → a
schema-valid dependency-ordered plan; a cycle forces FAIL); **083** added
`tools/ecosystem_release_train.py` (plan → a schema-valid train manifest, refusing a PASS without
the recorded `H-TRAIN-ENTRY` decision) + hermetic `assert_stage4` e2e; **084** piloted the layer
end-to-end across a scratch 2-member ecosystem — validated registry, PASS aggregate → PASS plan →
PASS train (all C12-valid), and both negatives enforced (a cyclic plan → FAIL, an ungated train →
FAIL) — with no hand-applied workaround (evidence `.agent/evidence/pilot-084/`; `NDEBT-035`
resolved). `manifest.json` carries phase-011 `status: complete`; both Stage-4 gates were exercised
in the pilot, recorded before the acts they govern (NDEBT-018). A **real, non-scratch multi-repo
ecosystem at a released tag** remains the standing production-maturity criterion (carried to phase
012, `NDEBT-029`).

**Scope — NIP-0002 Stage 4 only (prove-then-build).** Phases 008/009/010 delivered the "1", "0",
and "n" points; the membership set is enumerated and its verdicts aggregated. What remained was the
**coordination** layer — with `n` members visible, the cycle could *see* the ecosystem but could
not yet **coordinate work across it**. NIP-0002 placed the genuine n-repo coordination in two
protocols that were `Planned` (now Shipped in `ecosystem/README.md`) — the lifecycle's **Plan** and
**Promote** stages — and reserved the two gates that govern them (`NDEBT-035`). Phase 011 authored
and mechanized them, then piloted the layer. Features:

1. **080 — Dependency-reconciliation protocol (`ecosystem/04`) + companion schema** (`NDEBT-035`) —
   author the Plan stage (approved findings + the phase-010 aggregate → typed, dependency-ordered
   cross-repo work packets), a reconciliation-plan schema (topological-order invariant), and
   **define** the reserved `H-PLANNING-AUTHORITY` gate.
2. **081 — Release-train coordination protocol (`ecosystem/05`) + companion schema** (`NDEBT-035`) —
   author the Promote stage (admitting reconciled packets into a cross-repo release train, entry
   conditions, record-but-never-self-execute), a release-train-manifest schema, and **define** the
   reserved `H-TRAIN-ENTRY` gate.
3. **082 — Reconciliation tooling** (`NDEBT-035`) — a stdlib-only tool consuming the phase-010
   aggregate + approved findings → a schema-valid, dependency-ordered reconciliation plan; a cyclic
   dependency set is a flagged finding forcing a non-PASS verdict.
4. **083 — Release-train tooling + Stage-4 coverage** (`NDEBT-035`) — a stdlib-only tool consuming a
   reconciliation plan → a schema-valid release-train manifest gated on `H-TRAIN-ENTRY`; hermetic
   e2e over the aggregate → reconciliation → train chain (reusing `assert_multirepo`); prior paths
   regression-guarded.
5. **084 — Pilot, prove, prioritize + phase close** — run the coordination layer across a scratch
   multi-repo ecosystem, exercise the two Stage-4 gates before the acts they govern, then
   refine/validate the phase-012 candidate scope below and close the phase (**completing NIP-0002**).

**Deferred → Phase-012 candidate scope (release + real pilot + Repeat/GA protocols).** *(Refined and
validated against the feature-084 pilot evidence, `.agent/evidence/pilot-084/`: the pilot proved the
coordination layer runs end-to-end with both gates enforced, so the candidate below is **confirmed,
not re-ordered**. With NIP-0002's staged plan now complete, the release cut is the natural next step
— it carries the whole 0–n loop into a tag a real consumer can adopt, which the standing real
multi-repo pilot then requires.)* The production-maturity and Repeat/GA neighbours, outside
NIP-0002's 0–n staged plan:
- Cut a framework release carrying the whole loop — genesis + audit/compare + n-case tooling + the
  new coordination layer (`NDEBT-029`) — a release-train action, and a prerequisite for the real pilot.
- A **real, non-scratch multi-repo ecosystem pilot** — the standing production-maturity criterion
  across the whole 0–n programme.
- The remaining lifecycle protocols `ecosystem/06_simplification_review.md` (Repeat) and
  `ecosystem/08_ga_gate.md` (Promote/GA), with the reserved `H-CONSOLIDATION` / `H-GA` gates —
  prioritised separately from real evidence rather than authored speculatively.

## Plan of Record (2026-07-22) — Phase 010: 0–n Project Spectrum, Stage 3 — The n-case (Multi-Repo Tooling) — **COMPLETE 2026-07-22**

**Phase `010-multi-repo` is COMPLETE** (2026-07-22). It realized **NIP-0002 Stage 3 — the n-case
(many associated repositories forming one ecosystem)**, taken one stage at a time as phases
008/009 took Stages 1/2. Activation was on 2026-07-22 (operator verbatim: **"Approved. Proceed
with the phase-010 proposal + activation"**, gate **H-PHASE-010**, recorded in
`.agent/run_state.json` event `phase_activated` before any feature execution, per the NDEBT-018
rule). **075** made the membership registry a required, schema-validated artifact that sets `n`;
**076** added `ecosystem_membership_run.py` iterating the `in_scope` set (the stage tool
unchanged); **077** mechanized the cross-repo aggregation + a common-framework-pin consistency
check into a schema-valid ecosystem-level result; **078** added hermetic n-case e2e coverage
(`assert_multirepo`); **079** piloted the n-case end-to-end across a scratch 3-member ecosystem
stood up from nothing — validated registry, PASS aggregate, and a divergent-pin negative correctly
flipping to FAIL — with no hand-applied workaround (evidence `.agent/evidence/pilot-079/`;
`NDEBT-031` resolved). `manifest.json` carries phase-010 `status: complete`; features 075–078
landed with the phase-010 branch PR, 079 closes it.

**Scope — NIP-0002 Stage 3 only (prove-then-build).** Phases 008/009 delivered the "1" and "0"
points. The **"n" point remains**: the shipped tools take a single `--repo-root`, their
multi-repository consistency guard is a "defensive invariant for a future extension", and the
membership set that *sets* `n` has no required, validated artifact (`NDEBT-031`). Phase 010 makes
the n-case first-class, then pilots it. Features:

1. **075 — Ecosystem-membership registry schema** (`NDEBT-031`) — a JSON schema for a membership
   registry instance (the list-partition shape + exactly-one-list invariant); promote
   `scope_definition_patterns.md` from a draft pattern to a required, schema-backed artifact that
   sets `n`.
2. **076 — Multi-repo iteration** (`NDEBT-031`) — the tooling reads the registry and iterates its
   `in_scope` set of repo-roots; the single-`--repo-root` path stays unchanged.
3. **077 — Cross-repo aggregation + consistency** (`NDEBT-031`) — aggregate per-repo verdicts into
   one ecosystem-level result; enforce a common framework pin across members.
4. **078 — n-case coverage** (`NDEBT-031`) — hermetic e2e + self-test over a scratch multi-repo
   ecosystem (≥2 genesis'd repos), single-repo paths regression-guarded.
5. **079 — Pilot, prove, prioritize + phase close** — run the loop across a scratch multi-repo
   ecosystem, then refine/validate the phase-011 candidate scope below and close the phase.

**Deferred → Phase-011 candidate scope (NIP-0002 Stage 4 + release + real pilot).** *(Now authored
as a proposal — see the "Proposed Next Phase — Phase 011" banner at the top: NIP-0002 Stage 4 (the
`04`/`05` coordination protocols) is phase 011, and the release cut, real pilot, and the remaining
`06`/`08` Repeat/GA protocols are carried forward as phase-012 candidate scope. Refined and
validated against the feature-079 pilot evidence, `.agent/evidence/pilot-079/`: the pilot confirmed
the ordering — the aggregate ecosystem-level result already records per-member verdicts + a
common-pin consistency finding, exactly the substrate a `04` reconciliation pass consumes — so the
candidate is **confirmed, not re-ordered**. `NDEBT-031` is resolved; its Stage-4 residue is
carved into `NDEBT-035`, and the pilot's per-member clone-cost friction into `NDEBT-034`.)* Held
until the n-case is *proven* — now it is:
- **n-coordination protocols** (Stage 4, `NDEBT-035`): author `ecosystem/04_dependency_reconciliation.md`
  and `ecosystem/05_release_train_coordination.md` with companion schemas — cross-repo *ordering*
  and release-train *entry* — activating the reserved `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates.
  The feature-079 aggregate is their input substrate. **→ phase-011 proposal scope (features 080–084).**
- Cut a framework release carrying the whole loop — genesis + audit/compare + n-case tooling
  (`NDEBT-029`). **→ phase-012 candidate scope.**
- A **real, non-scratch multi-repo ecosystem pilot** — the standing production-maturity criterion
  (the feature-079 pilot exercised mechanics against scratch members, not real multi-project
  maturity). **→ phase-012 candidate scope.**
- *(Optional, `NDEBT-034`)* a throughput optimisation for repeated genesis (shared clone cache /
  lighter re-inject) if a larger pilot makes the per-member clone cost load-bearing.

## Plan of Record (2026-07-22) — Phase 009: 0–n Project Spectrum, Stage 2 — Greenfield Genesis — **COMPLETE 2026-07-22**

**Phase `009-greenfield-genesis` is COMPLETE** (2026-07-22). It realized **NIP-0002 Stage 2 —
the 0-case (greenfield genesis)**: standing up a *new* project from nothing is now first-class
and mechanized. **070** authored the greenfield-genesis protocol (`ecosystem/00` §8); **071**
mechanized it as `bootstrap.sh --genesis` (`git init` + deterministic scaffold + reuse of the
inject/verify/provenance install); **072** modelled the `incubating→in_scope` count-0→1
transition on the scope registry (`scope_definition_patterns.md` §2.3); **073** added hermetic
genesis e2e coverage (`assert_genesis`); **074** piloted the 0-case against a scratch greenfield
project and proved it (a clean Preflight `PASS_WITH_EXCEPTIONS`, evidence
`.agent/evidence/pilot-074/`). Activation was on 2026-07-22 (operator verbatim **"Activate phase
009"**, gate **H-PHASE-009**, recorded before feature execution per NDEBT-018). Landing on `main`
via PR #46; `manifest.json` carries phase-009 `status: complete`. A **real, non-scratch
greenfield project** remains the open production-maturity criterion (carried to phase 010).

**Scope — NIP-0002 Stage 2 only (prove-then-build).** Phase 008 proved the "1" point (a single,
already-existing consumer). The **"0" point remains absent**: standing up a *new* project from
nothing and bootstrapping into it has no protocol, tooling, or vocabulary, and
`ecosystem/00_ecosystem_bootstrap.md` presupposes a repo that already exists (`NDEBT-030`).
Phase 009 makes the 0-case first-class and mechanized, then pilots it. Features:

1. **070 — Greenfield-genesis protocol** (`NDEBT-030`) — author the genesis stage (precondition,
   create-and-scaffold steps, minimal skeleton + consumer inputs, entry into Bootstrap →
   Preflight); "genesis"/"scaffold" vocabulary distinct from the framework's phase-001 genesis.
2. **071 — Genesis scaffold capability** (`NDEBT-030`) — a single command stands up a new
   project from nothing (`git init` + minimal skeleton + inject the pinned `.nizam/` payload),
   reusing the existing provenance path; the inject-into-existing-repo path stays unchanged.
3. **072 — Incubating→in_scope transition** (`NDEBT-030`) — model the scope registry's
   `incubating` partition as the count-0→1 state; a genesis'd project starts `incubating` and is
   promoted `in_scope`. A scoped slice only — *not* the full membership-registry promotion.
4. **073 — Genesis e2e coverage** (`NDEBT-030`) — hermetic test: genesis-from-nothing → scaffold
   → inject → clean Preflight, with the existing bootstrap path regression-guarded.
5. **074 — Pilot, prove, prioritize + phase close** — run the 0-case against a scratch greenfield
   project stood up from nothing (no workaround), then refine/validate the phase-010 candidate
   scope below and close the phase.

**Deferred → Phase-010 candidate scope (NIP-0002 Stages 3–4).** *(Now realized as phase 010,
authored as a proposal and since activated — see the "Plan of Record — Phase 010 Activated"
banner at the top: Stage 3 (the n-case) is phase 010; Stage 4 (the 04/05 coordination protocols)
is carried forward as phase-011 candidate scope.
Validated by the feature-074 0-case pilot: the n-case membership-registry work (`NDEBT-031`)
builds directly on the `incubating` partition this phase populated, so the ordering is confirmed,
not re-ordered.)* Held
until the 0-case is *proven*, because each builds on a membership registry the 0-case only begins
to populate:
- **The n-case — multi-repo tooling** (`NDEBT-031`): iterate an ecosystem-membership registry
  (a set of repo-roots) instead of one `--repo-root`; promote
  `registry/scope_definition_patterns.md` to a required, validated membership artifact that sets `n`.
- **n-coordination protocols**: author `04_dependency_reconciliation.md` and
  `05_release_train_coordination.md` with companion schemas (activating the reserved
  `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates) — where cross-repo ordering and release-train
  entry live.
- Cut a framework release carrying the audit/compare tools (`NDEBT-029`) — a release-train
  action, and a prerequisite for the standing **real, non-scratch consumer pilot**.

A **real, non-scratch consumer/greenfield pilot** remains an open acceptance criterion across
the whole 0–n programme (a scratch pilot exercises loop *mechanics*, not product maturity).

## Plan of Record (2026-07-21) — Phase 008 Activated: 0–n Project Spectrum, Stage 1 — Consumer-Readiness — **COMPLETE 2026-07-21**

**Phase `008-consumer-readiness` is COMPLETE** (2026-07-21). It realized `NIP-0002` Stage 1
(consumer-readiness): **065** governance-root resolution + **066** provenance-pin anchoring
(ADR-004, pilot findings A/B) made the single-project case genuinely consumer-ready; **067**
bootstrap commit-SHA pinning (`NDEBT-033`) hardened the pin against a moved tag; **068**
brownfield coexistence was resolved-by-design (operator Option A — no code; the `.nizam/`-only
inject already satisfies GIP §5.1 by construction); **069** re-piloted the fixed loop against a
freshly bootstrapped **scratch/throwaway** consumer (a loop-mechanics proof, not a real
production project) and proved findings A/B resolved with no hand-applied workaround
(evidence `.agent/evidence/pilot-069/`). A real, non-scratch consumer pilot remains the open
production-maturity criterion (carried into the phase-009 candidate scope). Activation was on 2026-07-21 (operator verbatim
**"Approved. Please proceed"**, gate **H-PHASE-008**, recorded before feature execution per
NDEBT-018). 065/066 landed on `main` via PR #44; 067–069 are on the phase-008 branch for a
second PR. `manifest.json` carries phase-008 `status: complete`.

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
4. **068 — Brownfield coexistence** (GIP §5.1, `NDEBT-032`) — *resolved by design* (operator
   Option A, no `bootstrap.sh` change): the atomic inject writes only `.nizam/` and never
   touches a consumer's root files, so coexistence is safe by construction; reconciling a
   consumer's own root files remains a consumer-side manual step (proposal-time "preserve
   colliding root files in `bootstrap.sh`" wording superseded).
5. **069 — Re-pilot, prove, prioritize + phase close** — run the *fixed* loop against a
   freshly bootstrapped scratch/throwaway consumer (Preflight `PASS_WITH_EXCEPTIONS` whose
   only exception is the injected `.nizam/`, correctly-anchored baseline, no workaround),
   then author the phase-009 candidate scope below and close the phase.

**Deferred → Phase-009 candidate scope (NIP-0002 Stages 2–4).** *(Now realized as phase 009
(complete) — see its "Plan of Record … COMPLETE" banner above: Stage 2 (the 0-case) was phase 009;
Stages 3–4 are carried forward, Stage 3 now realized as the activated phase 010.)* Held until Stage 1 is *proven*,
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

## Current Position (2026-07-22)

- Phases 001–011 are complete. **Phase 011 (0–n Project Spectrum, Stage 4: n-Coordination
  Protocols, features 080–084) is COMPLETE** (2026-07-22) — **so NIP-0002's staged plan is now
  complete**: the coordination layer is first-class and mechanized. `ecosystem/04` is the Plan stage
  (080, `schema/reconciliation_plan.schema.json` + `validate.sh` C12's topological-order invariant;
  `H-PLANNING-AUTHORITY` defined), `ecosystem/05` is the Promote stage (081,
  `schema/release_train_manifest.schema.json` + C12's trace-to-plan invariant; `H-TRAIN-ENTRY`
  defined), `tools/ecosystem_reconcile.py` turns the phase-010 aggregate + findings into a
  schema-valid dependency-ordered plan (082, a cycle forces FAIL), `tools/ecosystem_release_train.py`
  admits a plan into a release train refusing a PASS without the recorded gate (083), with
  `assert_stage4` hermetic e2e; a scratch 2-member pilot proved the layer end-to-end — PASS aggregate
  → PASS plan → PASS train (all C12-valid) + both negatives enforced (cyclic → FAIL, ungated → FAIL) —
  with no workaround (084, evidence `.agent/evidence/pilot-084/`; `NDEBT-035` resolved). A real,
  non-scratch multi-repo pilot at a released tag stays outstanding for production maturity
  (`NDEBT-029`); the release cut carrying the whole 0–n loop, that real pilot, and the remaining
  `06`/`08` Repeat/GA protocols are phase-012 candidate scope. **Phase 010 (0–n Project Spectrum,
  Stage 3: The n-case — Multi-Repo Tooling, features 075–079) is COMPLETE** (2026-07-22): the n-case is now first-class
  and mechanized — `scope_definition_patterns.md` is a required, schema-validated membership
  registry that sets `n` (075, `schema/ecosystem_membership.schema.json` + `validate.sh` C12),
  `ecosystem_membership_run.py` iterates the `in_scope` set instead of one `--repo-root` (076),
  the per-member verdicts aggregate into a schema-valid ecosystem-level result with a
  common-framework-pin consistency check (077, `schema/ecosystem_membership_result.schema.json`),
  `assert_multirepo` gives hermetic n-case e2e coverage (078), and a scratch 3-member pilot proved
  the n-case end-to-end — validated registry, PASS aggregate, divergent-pin FAIL — with no
  workaround (079, evidence `.agent/evidence/pilot-079/`; `NDEBT-031` resolved). A real,
  non-scratch multi-repo pilot stays outstanding for production maturity (`NDEBT-029`: the loop is
  not yet in a released tag); Stage-4 coordination (`04`/`05`) is phase-011 candidate scope
  (`NDEBT-035`). Landing on the phase-010 branch (PR #47). **Phase 009 (0–n Project Spectrum,
  Stage 2: Greenfield Genesis, features 070–074) is COMPLETE** (2026-07-22): the 0-case is now first-class and
  mechanized — `ecosystem/00` §8 defines the greenfield-genesis protocol (070), `bootstrap.sh
  --genesis` stands up a new project from nothing (`git init` + deterministic scaffold + inject,
  071), `scope_definition_patterns.md` §2.3 models the `incubating→in_scope` count-0→1 transition
  (072), `assert_genesis` gives hermetic e2e coverage (073), and a scratch-greenfield pilot proved
  the 0-case end-to-end (074, Preflight `PASS_WITH_EXCEPTIONS`, evidence
  `.agent/evidence/pilot-074/`) — a loop-mechanics proof; a real, non-scratch greenfield pilot
  stays outstanding for production maturity, and the genesis capability is not yet in a released
  tag (`NDEBT-029`). Landing on `main` via PR #46. **Phase 008 (0–n Project Spectrum, Stage 1:
  Consumer-Readiness, features 065–069) is COMPLETE** (2026-07-21): the ecosystem loop is
  now genuinely consumer-ready — `ecosystem_preflight.py` resolves a governance-root (065)
  and anchors a baseline to the injected framework pin (066), so a freshly bootstrapped
  scratch/throwaway consumer gets a clean Preflight + honest baseline (ADR-004, pilot findings
  A/B); `bootstrap.sh` records a commit-SHA pin (067, `NDEBT-033`); brownfield coexistence was
  resolved-by-design (068); and a re-pilot proved findings A/B resolved against a
  scratch/throwaway consumer with no workaround (069, evidence `.agent/evidence/pilot-069/`) —
  a loop-mechanics proof; a real, non-scratch consumer pilot stays outstanding for
  production maturity. 065/066 are on
  `main` (PR #44); 067–069 are on the phase-008 branch (second PR pending). **Phase 007**
  (Consumer-Adoption Enablement & First External Pilot, features 060–064) is on `main`: the
  Bootstrap-stage protocol, the `H-CONSUMER-UPGRADE` gate, the first scratch-consumer pilot,
  and `NIP-0002` (0–n spectrum, Accepted via H-NIP) + `ADR-004` (Accepted). The validator
  runs green at `SUMMARY: 15 passed, 0 failed` (C1–C15), the fixtures self-test at 57/57,
  and the hermetic e2e bootstrap harness passes in CI (now including the n-case `assert_multirepo`).
- Latest released tag: v0.8.0 — the annotated tag was pushed by the operator
  2026-07-20 at the phase merge commit 183e468, executing H-FRAMEWORK-RELEASE after
  the recorded sign-off; `release.yml` auto-published the GitHub Release page from
  the `[0.8.0]` CHANGELOG section (run 29717579479, success). A MINOR release per
  `methodology/06_release_train.md` §3.2. The successor consumer-adoption phase
  (handover F-016..F-020) remains unblocked.
- **Release in preparation: v0.9.0 (MINOR) — awaiting `H-FRAMEWORK-RELEASE`.** The first
  release since v0.8.0, carrying phases 007–011 (consumer-adoption enablement + the full
  NIP-0002 0–n realization + the audit/compare tooling), cutting a tag that finally carries
  the whole 0–n loop into a consumable pin (`NDEBT-029`). Prepared on the release base
  `1dd4971` (phase-011 merge, PR #49): the `CHANGELOG [0.9.0]` section, version bumps in
  C10 lockstep (`NIZAM.json` / `docs/guide/index.html` / `CONTEXT.md` / `README.md`), and
  the readiness checklist `.agent/evidence/release-readiness-v0.9.0.md`. The pipeline never
  self-tags: the operator signs off and pushes the annotated `v0.9.0` tag, then `release.yml`
  publishes the Release page from the `[0.9.0]` section. On the tag, `NDEBT-029` resolves and
  the standing **real, non-scratch multi-repo pilot** becomes runnable at the released tag.
- Open debt (current, at DEBT.md v0.36.0): only three rows remain Open, none blocking —
  `NDEBT-029` (Medium, release-timing: the audit/compare tools are not yet in a released tag;
  **resolves on the operator-pushed `v0.9.0` tag** this release prepares), `NDEBT-026` (Low,
  pre-existing: C15 is a coverage check, not a mapping-direction validator), and `NDEBT-034`
  (Low: the n-case pilot's per-member clone cost, a throughput enhancement). The 0–n programme's
  scope rows are all **Resolved**: `NDEBT-027`/`NDEBT-028` (consumer-readiness, phase 008),
  `NDEBT-032`/`NDEBT-033` (brownfield + bootstrap SHA pin, phase 008), `NDEBT-030` (the 0-case,
  phase 009), `NDEBT-031` (the n-case, phase 010), and `NDEBT-035` (the Stage-4 coordination
  protocols, phase 011). Phase 006 resolved the entire enforcement-closure backlog it inherited
  (NDEBT-004, -005, -007 through -024; NDEBT-001/002/003/006/025 were already Resolved). See
  `docs/planning/DEBT.md`.

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
