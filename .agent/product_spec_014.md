---
id: nizam-product-spec-014
title: "Nizam Framework — Phase 014 Spec: GA Track — the Real Multi-Repo Pilot and the Remaining Lifecycle Protocols (06 Simplification Review, 08 GA Gate)"
description: "Proposal-grade spec for the rolled-forward phase-012 candidate scope — the real non-scratch multi-repo pilot plus the Repeat/GA lifecycle protocols with their reserved gates, authored 2026-09-30 after the v1.3.0 release; awaiting activation gate H-PHASE-014."
tags: [spec, ecosystem-cycle, ga, pilot, phase-014]
status: draft
last_audited: "2026-09-30"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-09-30T10:24:00Z"
updated_at: "2026-09-30T10:24:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-09-30T10:24:00Z"
    summary: "Initial phase-014 proposal, authored at v1.3.0 (main 2e122256, tag v1.3.0) realizing the rolled-forward phase-012 candidate scope that stood through phases 012 and 013 (a real non-scratch multi-repo pilot + the remaining lifecycle protocols 06/08 with the reserved H-CONSOLIDATION/H-GA gates). The two protocol documents are authored ahead of activation, proposal-grade (status draft): ecosystem/06_simplification_review.md and ecosystem/08_ga_gate.md. Features 099-102, DAG roots {099, 100}, original_estimate_lines 2200. No feature may enter contract negotiation before activation; current_phase remains 013-definition-of-done (complete) and .agent/run_state.json is untouched until then."
---

# Phase 014 — GA Track: the Real Multi-Repo Pilot and the Remaining Lifecycle Protocols

## Status and authority

**PROPOSED 2026-09-30 — awaiting operator activation (gate `H-PHASE-014`).** This
spec and the DAG-validated feature list (`.agent/feature_list_014.json`) are Planner
artifacts; per `methodology/00_planning.md` a phase becomes the plan of record only on
operator authorization, so `current_phase` stays `013-definition-of-done` (complete)
and `.agent/run_state.json` is untouched until activation (a proposal is not an
activation).

The authority for this scope is the **rolled-forward phase-012 candidate scope**,
carried unchanged through the phase-012 close (ROADMAP 0.35.0), the phase-013
activation decision (ROADMAP 0.37.0: "moves to phase 014"), and the phase-013 close
(ROADMAP 0.39.0: "stands for phase 014"): a real, non-scratch multi-repo pilot plus
the remaining lifecycle protocols `ecosystem/06_simplification_review.md` (Repeat) and
`ecosystem/08_ga_gate.md` (Promote/GA) with the reserved `H-CONSOLIDATION` / `H-GA`
gates. What was blocked is now unblocked: v1.3.0 is a released immutable tag a real
consumer can adopt.

The two protocol documents are authored **ahead of activation**, proposal-grade
(status `draft`): their activation flip and capability registration are feature 099's
work, mirroring how `04`/`05` shipped at their authoring features. Neither document
can fire a gate at proposal time: `H-CONSOLIDATION` and `H-GA` stay reserved until 099
defines them.

## Scope

Phase 014 delivers four features:

1. **099 — the GA-track activation wave.** Flip `ecosystem/06_simplification_review.md`
   and `ecosystem/08_ga_gate.md` draft → active and register them in NIZAM.json
   (ecosystem module `key_documents` + `capabilities`),
   `tools/skill.json`, and `docs/guide/index.html` — including re-syncing the guide's
   ecosystem card key-documents list, which still omits the shipped 00/04/05
   (pre-existing drift) — and **define** the reserved gates `H-CONSOLIDATION` / `H-GA`
   by moving them reserved → decided (DEFINED/OUTSTANDING) in
   `docs/planning/operator_gates.md`, mirroring features 061/080/081.
2. **100 — the real, non-scratch multi-repo ecosystem pilot at the released immutable
   tag v1.3.0.** The operator-designated real repositories — the framework hardcodes
   none; each member adopted/upgraded under a recorded per-member `H-CONSUMER-UPGRADE`
   decision BEFORE its re-bootstrap, per `NDEBT-018`; each member operates in its own
   isolated worktree, never on a member's main branch; Preflight → Baseline → Audit
   per member, then the membership-run aggregate. Real repositories, real worktrees,
   no scratch-harness fabrication. A real reconciliation plan / release train is built
   ONLY under recorded `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` decisions if the
   operator authorizes them. Findings land in the members' and the framework's debt
   registers; evidence under `.agent/evidence/pilot-100/`.
3. **101 — the first real simplification review.** Run `ecosystem/06` over the real
   pilot evidence plus the accumulated framework surface; candidates are recorded as
   evidence-backed findings; any actual consolidation is reserved behind
   `H-CONSOLIDATION` — never auto-applied.
4. **102 — the GA-readiness assessment and phase close.** Assemble the evidence
   dossier per `ecosystem/08`'s preconditions, with every threshold an acceptance
   requirement carrying a measured, anchored result. The assessment explicitly does
   NOT declare GA: `H-GA` remains outstanding, the operator's future act alone. Then
   refine the next-candidate scope and close the phase.

## Public contract changes

- **Two new governed documents** under `ecosystem/`
  (`06_simplification_review.md`, `08_ga_gate.md`), additive; status `draft` until
  feature 099 flips them active.
- **No schema changes.** The phase authors no new schema and changes none.
- **No workflow changes.** `.github/` is untouched.
- **Index enumeration, not capability registration.** The two documents join
  `NIZAM.json`'s ecosystem module `key_documents` the moment they land — the
  NDEBT-005 disk-to-index completeness guard (enforced by
  `tools/fixtures_self_test.sh`'s real-tree enumeration check) requires every
  on-disk `ecosystem/*.md` to be indexed in the same change that lands it. The
  `capabilities` array, `tools/skill.json`, and the user guide are deferred to
  099 by design, so the capability index never over-claims an unactivated
  (status `draft`) doctrine.
- **No consumer contract change.** The two documents are framework doctrine; nothing a
  consumer validates against changes at proposal time.

## Safety and state model

A proposal writes no execution state: `.agent/run_state.json` is untouched; the
manifest gains a pending/proposed entry only; `docs/planning/phase_014.yaml` is the
canonical pending lifecycle document (the canonical-first rule applies at execution:
canonical phase document first, manifest second, derived run_state third). The 06/08
documents cannot fire any gate — both gates stay reserved until 099 defines them. The
pilot's per-member adoption decisions are per-consumer `H-CONSUMER-UPGRADE` records in
each member's own governance state, not framework state.

## Feature DAG

- **099** — the activation wave (06/08 active + registration + gate definitions). Root.
- **100** — the real, non-scratch multi-repo pilot at tag v1.3.0. Root.
- **101** — the first real simplification review. Depends on 100.
- **102** — GA-readiness assessment (no declaration), next-candidate refinement, and
  phase close. Depends on 099, 100, 101.

The DAG is acyclic with two roots (`099` and `100`), which may proceed in parallel
(mirroring phase 013's `{092, 097}`). The topological execution order is:
`[099, 100]` → `[101]` → `[102]`. `original_estimate_lines` is 2200
(099: 400, 100: 900, 101: 400, 102: 500); the 130 percent cumulative ceiling is 2860.

## Acceptance

Phase-level acceptance is the union of every feature's acceptance tests in
`.agent/feature_list_014.json` plus the following:

- `bash tools/validate.sh` reports `SUMMARY: 16 passed, 0 failed`.
- `bash tools/fixtures_self_test.sh` exits 0 (79/79).
- `python3 .github/scripts/release_closeout.py --mode pr` exits 0.
- The phase-014 feature DAG validates acyclic.
- `docs/planning/phase_014.yaml` validates against `schema/phase.schema.json` at
  status `pending`.
- At proposal time exactly zero v1.4.0 refs exist (no tag, no release prep — the
  pipeline never self-tags): `git rev-parse -q --verify refs/tags/v1.4.0` returns
  non-zero.

## Out of scope

- **The `NDEBT-034` clone-throughput optimization** (a shared clone cache / lighter
  re-inject / `--reference` clone): explicitly deferred — NOT load-bearing at pilot
  scale (each member bootstraps exactly once to the pinned tag; the linear cost bites
  only on repeated re-bootstrapping sweeps, which the pilot does not perform);
  revisit only if the pilot proves otherwise.
- **Open debt `NDEBT-040`/`037`/`034`/`026`** stays open (all Low, enhancement
  candidates — candidate inputs to the 101 simplification review's evidence, not
  phase prework).
- **The GA declaration itself.** Even at phase close `H-GA` remains outstanding — the
  phase produces the dossier, never the declaration.
- **Bulk consumer upgrades.** They remain separate release trains (the phase-012
  boundary).

## Human gates

- `H-PHASE-014`: **OUTSTANDING** — the operator authorizes activation before any
  feature enters contract negotiation; recorded in run_state before feature execution
  per `NDEBT-018`.
- `H-CONSUMER-UPGRADE`: recurring, per member, BEFORE each member's re-bootstrap
  during feature 100.
- `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY`: only if a real reconciliation plan /
  release train is built in feature 100, recorded before each act.
- `H-CONSOLIDATION`: only for an actual consolidation chosen from feature 101's
  candidates.
- `H-GA`: never exercised by this phase; the GA declaration is the operator's future
  act alone.
- `H-FRAMEWORK-RELEASE`: not in this phase's scope (no release is prepared by phase
  014); recurring at whatever future release proposes one.
