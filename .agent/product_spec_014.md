---
id: nizam-product-spec-014
title: "Nizam Framework — Phase 014 Spec: GA Track — the Real Multi-Repo Pilot and the Remaining Lifecycle Protocols (06 Simplification Review, 08 GA Gate)"
description: "Plan-of-record spec for phase 014, activated 2026-10-08 under H-PHASE-014 with the approved amendments: the real non-scratch multi-repo pilot, the Repeat/GA lifecycle protocols with their reserved gates, and the folded enforcement-integrity maintenance tranche (features 103-109) ahead of the GA-readiness assessment."
tags: [spec, ecosystem-cycle, ga, pilot, maintenance, phase-014]
status: active
last_audited: "2026-10-09"
authoritative_source: NA
version: 1.1.3
spec_version: "1.1.3"
created_at: "2026-09-30T10:24:00Z"
updated_at: "2026-10-09T15:52:32Z"
change_log:
  - version: "1.1.3"
    date: "2026-10-09T15:52:32Z"
    summary: "PATCH (no scope change; design intent unchanged; product_spec_013 1.1.2 / 014 1.0.1 precedent: factual correction of acceptance-test commands), routed through the Planner per methodology/00_planning.md Section 9 under operator decision 2026-10-09T15:51:52Z (run_state operator_gate_decision, recorded before this change per NDEBT-018); operator verbatim: 'Approve amendment A1 to the phase-014 acceptance tests (spec 1.1.3): 103 AT4 removes both isolation halves (namespaces and Landlock) and its capable branch requires 'AssertionError: 40 != 0'; 104 AT8 requires the same signature; the 103/104 descriptions and spec bullets are updated as proposed; NDEBT-046 is logged. Approved.' The Evaluator's contract-103 review (.agent/qa/103-contract-review.json issue 1; evidence 05-coverage-gaps.txt F1/F1c) refuted, by execution, the premise that removing the unshare namespaces from tools/linux_trial_sandbox.sh turns test_linux_sandbox_blocks_cross_trial_files_and_network red on a capable host: Landlock alone enforces the file leg and the network leg accepts any OSError, so the suite stays 'Ran 54 tests / OK / CONFORMANCE: FULL'. Applied: 103 AT4's mutation now removes both isolation halves (adds the fail-closed replacement of the adapter's Landlock restrict-self call) and its capable branch also requires 'AssertionError: 40 != 0'; 104 AT8 requires the same breach signature; the 103 and 104 descriptions and this spec's 103/104 bullets name the isolation-removal mutation; the namespace-coverage gap and the vacuous execution test are logged as NDEBT-046 (not in phase-014 scope). Proven in scratch (.agent/evidence/103-qa-adversarial-contract-review/amendment-proposal.md Section 6): red at base on the restricted host, green under a contract-faithful implementation on both branches, and red for each injected defect in the branch that can observe it. feature_list_014 spec_version moves to 1.1.3 in lockstep."
  - version: "1.1.2"
    date: "2026-10-08T13:22:24Z"
    summary: "PATCH (no scope change): Validator round-2 corrections. (B) Feature 102 AT5, the NDEBT-044 (e) open-debt roll, is reclassified from Planner hardening to approved-tranche coverage under the 11:21:14Z decision ('NDEBT-044, split by concern'). The remaining Planner hardening (099 AT3/AT6/AT7, 101 AT2, 102 AT2/AT3/AT7) was ACKNOWLEDGED by the operator, verbatim 'acknowledged.' (run_state operator_gate_decision 2026-10-08T13:20:12Z), so nothing is pending and no decline fallback is defined; the earlier 'revert to the 1.0.1 forms' language is removed. (C) The garbled 102 bullet is repaired, and the unverifiable statement about the Orchestrator's brief is removed. feature_list_014 spec_version moves to 1.1.2 in lockstep."
  - version: "1.1.1"
    date: "2026-10-08T12:50:57Z"
    summary: "PATCH (no scope change): Validator round-1 corrections to 1.1.0. (1) The 1.1.0 coverage claim was an overclaim: its probes covered only 099 AT1/AT5, 100 AT2-4, 101 AT1-3, 102 AT1-5 and 104 AT2. As of 1.1.1, a02_premise_probes.py sweeps EVERY acceptance test on the pre-implementation tree, with declared outcomes and mutation-precondition proof; it adds positive and negative simulations for 099, 103-109, 101 and 102, including mutation controls for 108. (2) The 102 machine-readable dossier (AT2), its DEBT.md cross-check (AT3), the open-debt roll (AT5) and the new hash pin (AT7) are relabelled as Planner hardening beyond the operator's enumerated approval, pending acknowledgment. The recorded decision enumerates only 102 AT1 `import json` and the phase-scoped tag check. Every feature now carries an acceptance_provenance record. (3) The 6660/8658 figure is the Planner's activation-time estimate (naive 2890 x the measured 2.3 process weight, cited to NIP-0003:494-495), not an operator-directed basis. The operator then approved it, verbatim 'In approve the increased budget.' (run_state operator_gate_decision 2026-10-08T12:50:31Z). (4) Whole-file greps are scoped to a section or row (099 AT7, 103 AT6, 104 AT3/AT4, 105 AT4 with its pre-satisfied clause dropped, 107 AT4). 109 AT4 requires a defined primitive, return code 1 and a targeted diagnostic. 104 gains an exact CI-evidence contract (run JSON + job log, bound by job id, name, branch and headSha). 103's capable-host branches are discharged by 104's CI evidence. 107 gains a C2-only control. 101 rejects an empty findings.json unless a zero_findings_justification is stated. 102 AT4 fetches tags first. 102 AT7 pins sha256 of the frozen activation infrastructure. NDEBT-045 is logged (the --payload help paragraph), outside 108's scope. feature_list_014 spec_version moves to 1.1.1 in lockstep. [1.1.2: AT5 reclassified as approved-tranche coverage; the hardening was operator-acknowledged at 13:20:12Z.]"
  - version: "1.1.0"
    date: "2026-10-08T12:05:32Z"
    summary: "ACTIVATED + SUBSTANTIVE RE-PLANNING (MINOR: scope added) under H-PHASE-014, routed through the Planner per methodology/00_planning.md Section 9. Authorization event: .agent/run_state.json operator_gate_decision at 2026-10-08T11:21:14Z, recorded before this change (NDEBT-018); operator verbatim: '- H-PHASE-014. Activate Phase 014 with the proposed amendments, Approved. - Maintenance tranche, fold them into Phase 014, Approved.' Applied: (1) the missing edge 101 -> 099; (2) acceptance-test hardening — an exit-captured validator gate replaces every `validate.sh | grep SUMMARY` pipeline, 099 AT5 asserts a DEFINED row per gate, 100 asserts real members, the v1.4.0 pin and per-member H-CONSUMER-UPGRADE ordering against run_state, 101 asserts a scoped, anchored review artifact, 102 AT1 gains `import json`, 102's dossier tests become machine-readable with an external debt cross-check [corrected in 1.1.1: Planner hardening beyond the enumerated approval; operator-acknowledged 2026-10-08T13:20:12Z, 'acknowledged.' (1.1.2)], and the fixed-version tag-absence test becomes a phase-scoped tag check against the tag set recorded at activation; (3) a clarifying clause for 'run_state untouched until activation'; (4) the maintenance tranche as features 103-109 (NDEBT-043 -> 041, 042, 044 split by concern, 037, 026), each a dependency of 102, with the workflow-change prohibition lifted for them only; (5) the scope re-baseline: naive 2890 x 2.3 measured process weight = 6660 (ceiling 8658), from 2200 [clarified in 1.1.1: the Planner's activation-time estimate; approved by the operator at 2026-10-08T12:50:31Z]. Status draft -> active; .agent/feature_list_014.json spec_version moves to 1.1.0 in lockstep. Every amended or new acceptance test was run against the pre-implementation tree and probed with negative controls (.agent/evidence/backlog-reconciliation-2026-10-08/a02_premise_probes.txt) [corrected in 1.1.1: an overclaim at 1.1.0 — the probes then covered only part of the tests; see the 1.1.1 entry]."
  - version: "1.0.1"
    date: "2026-10-08T10:33:25Z"
    summary: "PLAN AMENDMENT per methodology/00_planning.md Section 9 (factual re-baseline; design intent unchanged), routed through the Planner and applied in the v1.4.0 post-release refresh under operator decision D1 (verbatim 'proceed with the logic next steps to complete the backlog.', 2026-10-08), the authorization event recorded in .agent/run_state.json history (operator_gate_decision at 2026-10-08T10:30:34Z) before the act per NDEBT-018 -- not H-PHASE-014. The operator-authorized out-of-phase v1.4.0 release (tag object bb32064 at 9edd5d0) falsified two premises authored at v1.3.0: (1) the pilot pin -- feature 100 now targets the released immutable tag v1.4.0, the latest, which also carries the draft ecosystem/06 and 08 documents that feature 099 activates; (2) the tag-absence acceptance criterion -- retargeted to v1.5.0, the next MINOR, preserving its meaning (phase 014 cuts no release; the pipeline never self-tags). Scope, features, dependencies, estimates (2200) and status (draft) are unchanged; the 'no release is prepared by phase 014' gate text stays, still true. PATCH per the product_spec_013 1.1.2 precedent (factual correction of acceptance-test commands, design intent unchanged); .agent/feature_list_014.json spec_version moves to 1.0.1 in lockstep."
  - version: "1.0.0"
    date: "2026-09-30T10:24:00Z"
    summary: "Initial phase-014 proposal, authored at v1.3.0 (main 2e122256, tag v1.3.0) realizing the rolled-forward phase-012 candidate scope that stood through phases 012 and 013 (a real non-scratch multi-repo pilot + the remaining lifecycle protocols 06/08 with the reserved H-CONSOLIDATION/H-GA gates). The two protocol documents are authored ahead of activation, proposal-grade (status draft): ecosystem/06_simplification_review.md and ecosystem/08_ga_gate.md. Features 099-102, DAG roots {099, 100}, original_estimate_lines 2200. No feature may enter contract negotiation before activation; current_phase remains 013-definition-of-done (complete) and .agent/run_state.json is untouched until then."
---

# Phase 014 — GA Track: the Real Multi-Repo Pilot and the Remaining Lifecycle Protocols

## Status and authority

**ACTIVATED 2026-10-08 (gate `H-PHASE-014`), with the proposed amendments and the
maintenance-tranche fold.** The operator's words, verbatim:

> - H-PHASE-014. Activate Phase 014 with the proposed amendments, Approved. - Maintenance tranche, fold them into Phase 014, Approved.

The decision is recorded in `.agent/run_state.json` as an `operator_gate_decision` at
2026-10-08T11:21:14Z, before this re-planning and before any activation record
(`NDEBT-018`). This spec and `.agent/feature_list_014.json` are now the plan of record.
Activation is recorded canonical-first: `docs/planning/phase_014.yaml` (`in_progress`)
first, `docs/planning/manifest.json` (`current_phase: 014-ga-track`) second, and the
derived `.agent/run_state.json` position third. The Orchestrator writes the run_state
position, because it owns those fields (`standard/AGF.md` Section 5 rule 4).

**Clarifying clause: "run_state untouched until activation".** Spec 1.0.0 (Safety and
state model) said that `.agent/run_state.json` was untouched until activation. That
meant the proposal advanced none of the phase-execution coordination fields
(`current_phase`, `current_feature`, `status`, `scope_budget`, `circuit_breaker`,
`active_contract_id`). It never forbade the Orchestrator from appending
`operator_gate_decision` history entries that record a decision before the act it
authorizes. NDEBT-018 requires exactly those entries. Two were appended while phase 014
was still proposed: D1 at 2026-10-08T10:30:34Z and `H-PHASE-014` at 11:21:14Z. Both
are consistent with the clause.

The authority for the original scope is the **rolled-forward phase-012 candidate
scope**. It was carried unchanged through the phase-012 close (ROADMAP 0.35.0), the
phase-013 activation (0.37.0) and the phase-013 close (0.39.0): a real non-scratch
multi-repo pilot, plus the lifecycle protocols `ecosystem/06_simplification_review.md`
(Repeat) and `ecosystem/08_ga_gate.md` (Promote/GA) with the reserved `H-CONSOLIDATION`
/ `H-GA` gates. The authority for the maintenance tranche is the operator's fold
decision above. Its rows are re-verified at `02b02c6` in
`.agent/evidence/backlog-reconciliation-2026-10-08/`.

## Scope

Phase 014 delivers eleven features. They are listed in the canonical single-lane order,
which is also the order of `.agent/feature_list_014.json`.

| Order | Feature | Concern | Debt | Depends on |
|-------|---------|---------|------|------------|
| 1 | **099** | GA-track activation wave: 06/08 draft → active and registered; `H-CONSOLIDATION` / `H-GA` defined | — | — |
| 2 | **103** | Sandbox prerequisite: an explicit, non-passing UNSUPPORTED outcome | NDEBT-043 | — |
| 3 | **104** | Convergent-review suite enforced in CI; the review schema family's validator stated | NDEBT-041 | 103 |
| 4 | **105** | Nested-fixture ownership: the NIP-0003 claim map, pulled forward | NDEBT-042 | — |
| 5 | **106** | Capability-index parity: an intentional subset, enforced by C13 | NDEBT-044 (a) | — |
| 6 | **107** | NIP frontmatter under C1/C2; NIP-0002's status corrected | NDEBT-044 (b) | — |
| 7 | **109** | C15 mapping direction: an explicit Role column and a new primitive | NDEBT-026 | — |
| 8 | **108** | Validator help and adapter-reference truth | NDEBT-037; NDEBT-044 (c, d, f) | 106, 107, 109 |
| 9 | **100** | Real, non-scratch multi-repo pilot at the released tag v1.4.0 | — | — |
| 10 | **101** | First real simplification review | — | 099, 100 |
| 11 | **102** | GA-readiness dossier (no declaration), next-candidate refinement, phase close; NDEBT-044 (e) | NDEBT-044 (e) | 099, 100, 101, 103–109 |

Features 099–102 keep the scope of spec 1.0.1:

- **099 — the activation wave.** Flip `ecosystem/06` and `ecosystem/08` draft → active.
  Register them in `NIZAM.json` (ecosystem `key_documents` plus `capabilities`),
  `tools/skill.json` and `docs/guide/index.html`; the guide's ecosystem card is
  re-synced to every on-disk `ecosystem/0*.md`. **Define** `H-CONSOLIDATION` and `H-GA`
  (reserved → DEFINED/OUTSTANDING in `docs/planning/operator_gates.md`), mirroring
  features 061/080/081.
- **100 — the real pilot at the released immutable tag v1.4.0.** The members are
  operator-designated real repositories. **H-PHASE-014 designates none: the member set
  is an operator decision not yet made.** Each member is adopted under its own
  `H-CONSUMER-UPGRADE`, recorded before its re-bootstrap (`NDEBT-018`). Each runs in an
  isolated worktree, never on its main branch. The stages are Preflight → Baseline →
  Audit → the membership-run aggregate. A plan or train is built only under recorded
  `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY`. There is no scratch-harness fabrication.
  The evidence contract is fixed in the feature list.
- **101 — the first real simplification review.** It runs `ecosystem/06` over the
  pilot evidence and the accumulated surface, including what 103–109 changed.
  Candidates are evidence-backed findings, and every consolidation is reserved behind
  `H-CONSOLIDATION`. It now depends on 099, which activates 06 and defines that gate.
- **102 — the GA-readiness dossier.** It is organised by the five `ecosystem/08`
  Section 2 preconditions. `H-GA` stays OUTSTANDING and nothing is declared. The
  approved amendments for 102 are the `import json` fix (AT1) and the phase-scoped tag
  check (AT4).
  - **Approved-tranche coverage** (the same 11:21:14Z decision, "NDEBT-044, split by
    concern"): the NDEBT-044 (e) open-debt roll (AT5).
  - **Planner hardening, operator-acknowledged 2026-10-08T13:20:12Z
    ("acknowledged."):** the machine-readable dossier contract (AT2), its external
    `DEBT.md` cross-check (AT3) and the frozen-infrastructure hash pin (AT7).
  - After the dossier, 102 does the next-candidate refinement and the canonical-first
    close.

## Maintenance tranche — design decisions (features 103–109)

The tranche exists because GA readiness requires enforcement integrity. A
"required" gate that no CI job runs (NDEBT-041) cannot back a readiness claim. Neither
can a completeness guard that misses 67 files (NDEBT-042), or a check whose
documentation overstates it (NDEBT-026/037/044). Every row was re-verified at `02b02c6`
before it was scheduled (AH-2).

- **103 (NDEBT-043): required by default.** On a host that restricts unprivileged
  user namespaces, the documented command `python3 tools/test_convergent_review.py`
  behaves as follows:
  - each of the five sandbox tests is reported UNSUPPORTED;
  - it prints `CONFORMANCE: NOT FULL`;
  - it exits **non-zero**.

  `--allow-unsupported-isolation` turns the same report into exit 0, for local
  development only; CI never passes it. On a capable host the run prints
  `CONFORMANCE: FULL`. The capability probe is the host's `unshare`, independent of
  the sandbox script. The sandbox script and the trial adapter are not modified.

  Capable-host proof (103 AT4's capable branch, discharged in CI by 104's negative
  control): with *both* isolation halves removed in a scratch copy — the `unshare`
  namespace line of the sandbox script and the adapter's Landlock restrict-self call —
  the run fails on `test_linux_sandbox_blocks_cross_trial_files_and_network` with
  `AssertionError: 40 != 0` (the cross-trial secret was read). Removing the namespaces
  alone is detected by no test in the suite: Landlock still enforces the file leg and
  the network leg accepts any `OSError`. That gap is `NDEBT-046`, outside 103's scope.

  This is the opposite polarity to the `--require-isolation` opt-in that NIP-0003
  sketches for its own future suite. The divergence is recorded for the NIP's
  pre-acceptance revision.
- **104 (NDEBT-041): one new CI job.** It runs the suite in required mode, after a
  guarded step that enables user namespaces where the sysctl key exists. The pinned
  action SHAs are reused, so C14 stays PASS. Every job-count statement is derived from
  the workflow (`standard/definition_of_done.md` §8 and §11, and `tools/README.md`).
  `schema/README.md` states that the suite is the review schema family's **sole
  validator**; C12 coverage of that family is left to 101 / `H-CONSOLIDATION`. CI
  evidence is a green run plus a throwaway-branch negative control. The throwaway
  branch is never merged; its only change is 103 AT4's isolation-removal mutation
  (both halves removed), and the job must fail on
  `test_linux_sandbox_blocks_cross_trial_files_and_network` with
  `AssertionError: 40 != 0`.

  If hosted runners cannot enable namespaces, the required-mode job fails by design.
  The Generator escalates; it never weakens the mode.
- **105 (NDEBT-042): reuse, not reinvention.** This is NIP-0003's feature-109 design
  (a fixture-subdirectory claim map in `tools/fixtures_self_test.sh`, each
  subdirectory claimed by exactly one owning suite), **pulled forward** into phase
  014. NIP-0003's feature (provisionally renumbered 116) then *registers*
  `tools/fixtures/runtime_session/` in this same map. There is no second registry.
- **106 (NDEBT-044 a): the decision, made before anything is asserted, is an
  intentional subset, not equality.**
  - `tools/skill.json` lists the protocols the runtime skill routes to and loads on
    demand.
  - `NIZAM.json` also indexes artifacts that are not routable, such as
    `tools/validate.sh`, `tools/skill.json` itself, `tools/SKILL.md`,
    `tools/interface.md` and the CI/MCP policy standards. Equality would be wrong.
  - The rule: every `tools/skill.json` `capabilities[].module` is the
    `authoritative_source` of some `NIZAM.json` capability.
  - Re-verified at `02b02c6`, the rule is **violated today** by
    `ecosystem/00_ecosystem_bootstrap.md`, which has been a skill capability since
    feature 060 without a `NIZAM.json` capability entry. 106 adds that entry
    (`nizam-ecosystem-bootstrap`).
  - Enforcement extends C13 and adds no check number, because C17 is earmarked by
    NIP-0003.
- **107 (NDEBT-044 b): C1/C2 only.** NIP-0002's `status: accepted` becomes `active`,
  the NIP-0001 precedent. `docs/nips/*.md` join the C1 and C2 inputs, but **not**
  `build_shipped_md_set`. C9 and C10 sweep that same set, and proposals legitimately
  cite paths that do not exist yet: NIP-0001 and NIP-0003 fail C9 under `--target`
  at `02b02c6`.
- **109 (NDEBT-026): compatibility-first.**
  - The capability-profile table has no role column today, so there is nothing to
    parse.
  - 109 adds an explicit `Role` column to `standard/capability_profiles.md` §2, and a
    **new** primitive `vlib_profiles_map_roles` that parses it.
  - C15 calls both primitives, and `vlib_profiles_cover_roles` is unchanged.
    Tightening it in place would narrow behavior that direct callers rely on, a
    MAJOR-class change under `methodology/06_release_train.md` §3.1.
  - C15 is default-mode only, so `--payload` validation does not change.
- **108 (NDEBT-037 + 044 c, d, f): one concern, reference-text truth.** It runs after
  106, 107 and 109, so it documents their final semantics:
  - C14–C16 `--help` paragraphs (every check the validator prints has one);
  - the C5 text is corrected to "case-sensitive", because the sweep is
    `grep -InE`; the text changes, not the behavior;
  - the payload-doc set paragraph now includes `methodology/` and `ecosystem/`;
  - `tools/interface.md` §5 item 10 cites Item 5, not Item 4 (§5 stays at 10 items).

  NDEBT-044 (e), the ROADMAP open-debt count, belongs to 102's phase-close refresh,
  because the Open set changes as this tranche lands.

## Public contract changes

- **Two governed documents become normative** (099): `ecosystem/06` and `ecosystem/08`.
- **Workflow changes are allowed for the maintenance features only.** The 1.0.x
  "no workflow changes" non-goal still binds 099–102. Of the tranche, only **104**
  is planned to touch `.github/` (`compliance.yml`). 103 and 105–109 do not.
- **Schema changes are allowed only where a maintenance contract requires one.** None
  is planned: 106 extends C13, 109 adds a table column and a primitive, and 107
  changes a sweep. If a contract finds that a schema change is required, it must
  first assess the version impact (loosening or optional-only ⇒ MINOR). Any narrowing
  escalates to the operator.
- **Version impact.** Phase 014 prepares no release. The next release is at least
  MINOR, and no planned change is MAJOR.

  | Feature | Impact |
  |---------|--------|
  | 099 | MINOR |
  | 103 | MINOR (a new optional flag; nothing that passed fails) |
  | 104 | MINOR (a `definition_of_done.md` job statement) |
  | 105 | PATCH |
  | 106 | MINOR (C13 tightened, but its inputs ship together) |
  | 107 | MINOR (the default-mode sweep scope widens) |
  | 108 | PATCH |
  | 109 | MINOR (additive column and primitive) |
  | 100–102 | None |

  Each assessment is recorded on the feature as `version_impact`.
- **No consumer contract narrows.** `--payload` validation changes only through C13
  (106), whose inputs ship together, so no consumer sees a new failure.

## Safety and state model

- Activation is canonical-first, and closure is too: the canonical phase document
  first, the manifest second, and the derived run_state third, written by the
  Orchestrator.
- **No `H-GA` act, no `H-CONSOLIDATION` act, no release and no tag.**
- The pilot's per-member adoption decisions are per-consumer `H-CONSUMER-UPGRADE`
  records, kept in each member's own governance state. 100's evidence must also tie
  each of them to a framework run_state event.
- **Acceptance infrastructure is frozen at activation**, under
  `.agent/evidence/phase-014-activation/`:
  - the baselines: `validate.txt`, `validate_payload.txt`, `tag-baseline.txt` and
    `audits-baseline.txt`, all in the `04` §5 shape;
  - the Planner-authored helpers `gates/validator_gate.py`, `gates/scratch_run.py`
    and `gates/phase_tag_check.py` (the `.agent/evidence/098/verify_release_prep.py`
    precedent).

  No feature contract may modify that directory; 102 AT7 pins the sha256 of all seven
  files (three gates, four baselines) and fails if any changed during the phase.
  Every feature's acceptance tests
  capture exit status directly (no pipeline swallows it), and none hard-codes a check
  count. The gate asserts exit 0, `0 failed`, a passed-count equal to the `PASS`
  lines, and that every baseline check still passes.

## Feature DAG

The DAG is acyclic. Its roots are 099, 103, 105, 106, 107, 109 and 100. Its edges are
104 → 103; 108 → 106, 107, 109; 101 → 099, 100; and 102 → 099, 100, 101, 103–109.

## Execution Order

```text
Parallel Group 1: 099, 103, 105, 106, 107, 109, 100 (no dependencies)
Parallel Group 2: 104 (depends on 103), 108 (depends on 106, 107, 109), 101 (depends on 099, 100)
Sequential:       102 (depends on 099, 100, 101, 103-109)
```

**Recommended single lane** (the canonical list order; the Dependency Enforcement Rule
picks the first pending feature whose dependencies are satisfied):

`099 → 103 → 104 → 105 → 106 → 107 → 109 → 108 → 100 → 101 → 102`.

- **The first eligible feature is 099.**
- **The pilot comes late on purpose.** 100 depends on operator decisions that have not
  been made (the member set and each member's `H-CONSUMER-UPGRADE`). Work that is
  ready now goes first, so the lane is not stalled while those decisions are
  outstanding.
- **101 reviews the maintained surface.** It reviews the surface after the tranche
  changes it, not before.
- **Moving the pilot up is possible.** If the operator designates the members earlier,
  100 may be moved up by a recorded amendment. Its dependencies allow that.

The critical path is 100 → 101 → 102.

## Scope budget re-baseline

The 1.0.x estimates (2200) were naive implementation lines, as was phase 013's 2150,
which realized 6212 (2.89×). **The figure below is the Planner's activation-time
estimate under the approved fold. The operator APPROVED it on 2026-10-08, verbatim
"In approve the increased budget." (`.agent/run_state.json` `operator_gate_decision`
at 2026-10-08T12:50:31Z).** Its basis is the **measured ×2.3
process weight**, the figure NIP-0003 applies
(`docs/nips/NIP-0003-live-runtime-sessions.md:494-495`, 2330 naive → 5400), and it
covers multi-round contracts, two QA artifacts and the per-feature §5 evidence.

| Feature | Naive | ×2.3 (rounded to 10) |
|---------|------:|---------------------:|
| 099 | 400 | 920 |
| 103 | 120 | 280 |
| 104 | 100 | 230 |
| 105 | 110 | 250 |
| 106 | 160 | 370 |
| 107 | 50 | 120 |
| 109 | 90 | 210 |
| 108 | 60 | 140 |
| 100 | 900 | 2070 |
| 101 | 400 | 920 |
| 102 | 500 | 1150 |
| **Total** | **2890** | **6660** |

- `original_estimate_lines` is **6660**. It was 2200 and covered four features.
- The 130 percent cumulative ceiling is **8658**.
- At phase 013's realized 2.89× the phase would land near 8352, under the ceiling.
- The per-feature `estimated_lines` sum exactly to 6660.
- The Orchestrator records the re-baseline structurally in `scope_budget`
  (`methodology/00_planning.md` Section 9): from 2200, to 6660, at
  2026-10-08T11:21:14Z.
  - `authorized_by` names the Planner's estimate, made under the operator's fold
    authorization. The operator approved the figure at 2026-10-08T12:50:31Z.

## Acceptance

Phase-level acceptance is the union of every feature's acceptance tests in
`.agent/feature_list_014.json`, plus the following:

- `python3 .agent/evidence/phase-014-activation/gates/validator_gate.py` exits 0. Its
  `--payload` form exits 0 as well.
- `bash tools/fixtures_self_test.sh` exits 0. The test checks the exit status only,
  never a fixture count, because 105 changes that count.
- `python3 .github/scripts/release_closeout.py --mode pr` exits 0.
- The phase-014 feature DAG validates: no dangling dependencies, and the list order is
  topological.
- `docs/planning/phase_014.yaml` validates against `schema/phase.schema.json`. Its
  status is `in_progress` while the phase runs, and `complete` at close.
- `git fetch --tags --quiet origin && python3 .agent/evidence/phase-014-activation/gates/phase_tag_check.py`
  exits 0 (tags are fetched first: an unfetched remote tag is invisible). No
  tag is created during the phase; the pipeline never self-tags. This replaces the
  fixed-version test. That test was retargeted from `v1.4.0` to `v1.5.0` under D1, and
  it was blind to any other tag.

## Acceptance-test provenance and probe coverage

Every feature in `.agent/feature_list_014.json` carries an `acceptance_provenance`
record, which separates four kinds of test:

- **approved_amendment** — tests that implement the operator's enumerated list:
  - 099 AT1/AT5;
  - 100 AT1–AT5;
  - 101 AT1/AT3;
  - 102 AT1/AT4.
- **approved_tranche_scope** — 102 AT5, the NDEBT-044 (e) open-debt roll, which
  implements the approved maintenance fold (same 11:21:14Z decision).
- **planner_hardening_operator_acknowledged** — tests that go beyond the enumerated
  list. They are Planner hardening, operator-acknowledged 2026-10-08T13:20:12Z
  ("acknowledged."), and part of the approved acceptance set:
  - 099 AT3/AT6/AT7;
  - 101 AT2;
  - 102 AT2/AT3/AT7.
- **new_feature_design** — all tests of 103–109 (the fold was approved; their tests are
  Planner design).
- **operator_approved_amendment_1_1_3** — 103 AT4 and 104 AT8, rewritten after the
  Evaluator refuted their capable-host premise (`.agent/qa/103-contract-review.json`
  issue 1); operator decision 2026-10-09T15:51:52Z. Planner design in origin.

The remaining 099/101/102 tests are carried from 1.0.x.

`.agent/evidence/backlog-reconciliation-2026-10-08/tools/a02_premise_probes.py`
(revision 3) runs **every** acceptance test against the pre-implementation tree, with a
declared outcome. The outcomes are:

- `fail`;
- `fail-mut` (a scratch-run control whose mutation precondition held);
- `inapplicable` (109 AT2, which needs the Role column);
- `guard`;
- `gate`.

It also runs positive and negative simulations for each feature. The record is in
`a02_premise_probes.txt`. Positive controls that would require the feature's own code
are deferred to implementation; Part A of the probes names them. They are 103 AT3,
105 AT1–AT3, 106 AT3–AT4 and 107 AT2–AT3.

## Out of scope

- **The `NDEBT-034` clone-throughput optimization.** It stays deferred and is not
  load-bearing at pilot scale; revisit it only if the pilot proves otherwise.
- **`NDEBT-040`** (SHA-anchored byte-guards). It stays Open, annotated as a candidate
  for a future **Workflow Assurance NIP** (candidate/contract identity and
  invalidation). The NIP's outline is in `docs/planning/backlog_reconciliation.md`;
  it is not authored in this phase.
- **NIP-0003.** Its acceptance (`H-NIP`), its phases 015/016 and its pre-acceptance
  revision are all out of scope.
- **The GA declaration itself.** `H-GA` remains outstanding at the close.
- **Bulk consumer upgrades.** They remain separate release trains.
- **Any release preparation or tag.**

## Human gates

- `H-PHASE-014`: **SATISFIED 2026-10-08** (verbatim above; run_state 11:21:14Z).
- `H-CONSUMER-UPGRADE`: **OUTSTANDING**, recurring, once per real member of feature
  100, before that member's re-bootstrap. The member set itself is still to be
  designated by the operator.
- `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY`: only if 100 builds a real plan or train,
  recorded before each act.
- `H-CONSOLIDATION`: defined by 099, and exercised only for an actual consolidation
  chosen from 101's candidates.
- `H-GA`: defined by 099 and never exercised by this phase.
- `H-FRAMEWORK-RELEASE`: not in scope. No release is prepared by phase 014.
