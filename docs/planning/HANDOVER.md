---
id: nizam-handover-2026-10
title: "Developer Handover — nizam-framework, Phase 014 Remaining Backlog (2026-10)"
description: "Onboarding and handover record for an engineer taking over the remaining phase-014 backlog (features 106, 107, 109, 108, 100, 101, 102): reading order, verified state at main e2a50ed, the working method as practised, the remaining features with their gates and hazards, operator authority, environment gotchas, housekeeping inventory, and open tensions."
version: 1.0.0
status: active
authoritative_source: docs/planning/HANDOVER.md
last_audited: "2026-10-10"
tags: [planning, handover, onboarding, phase-014]
change_log:
  - version: "1.0.0"
    date: "2026-10-10"
    summary: "Initial handover record, authored by the Planner on branch chore/handover-2026-10 cut from main e2a50ed (PR #70 merged), after the operator asked for the project to be prepared for a new developer (run_state operator_gate_decision 2026-10-10T02:11:41Z). Every figure was re-verified against the repository; the replayable checks are in .agent/evidence/handover-2026-10/. Revised after Validator round 1, before merge: (b) states how this package's own budget-counted lines are treated (the Planner's phase-level-item interpretation, effective only when the Orchestrator records it), 106's measurement base and measure.py commands, and the budget figures both pre-handover and including the handover; (c) quotes the 19:28:39Z record's 11-step summary of the brief and presents the 12 steps as practised, adds that an Evaluator contract-review rejection also uses up a contract attempt (103 precedent), separates the evidence gate's EXIT:<code> rule from the practised all-EXIT:0 convention, cites the human_authorized_extension as recorded practice under 03 Section 6, and separates routine pushes and PRs from operator-authorized outward acts; (f) adds the local acceptance-gate helpers, the fixture self-test and the four CI jobs; (g) states both V13 conditions and the DAG critical-path artifact; (h) ties the expected v1.5.0 roll-up to H-NIP and H-PHASE-015; (a) item 12 names the Orchestrator and the four execution roles. Revised after Validator round 2, before merge: (c) states that the Validator runs only read-only git commands and file reads and cannot run verification commands (105-mode-b.json prior_rounds[0] MB-1); step 5 states that attempt-base.txt has been used since 103 (099's base only in run_state); steps 7-8 state that 104 and 105 ran Mode B round 1 on the unpromoted attempt commit, and that a post-promotion Mode B round is still needed when the contract has Mode B obligations on the promoted tree (105 MB-1)."
---

# Developer Handover — Phase 014 Remaining Backlog

This record is for a competent engineer who is new to this repository. It states
what is true at `main` `e2a50ed` (PR #70, merged 2026-10-10), how the work has been
done, and what is left. Every claim points to a repository path, commit, PR or CI
run id. The facts are re-checked by
`.agent/evidence/handover-2026-10/verify_handover_facts.py`. Its capture is
`.agent/evidence/handover-2026-10/01-verify-handover-facts.txt`.

This document is a guide. If it disagrees with a canonical file, the canonical file
wins: `docs/planning/phase_014.yaml`, `.agent/feature_list_014.json`,
`.agent/product_spec_014.md`, `.agent/run_state.json` and `docs/planning/DEBT.md`.

## (a) Start here — the 30-minute reading order

Read these in order. Read only the sections named. The framework's own rule is
"query the index, never bulk-read" (`methodology/04_tool_driven_state.md` §2).

1. `NIZAM.json`: the capability index. Find the path for a task here first.
2. `tools/SKILL.md`: the entry point and the obligations that always apply.
3. `CONTEXT.md`: the module map and execution commands.
4. `docs/planning/ROADMAP.md`: "Current Position", then the phase-014
   "Plan of Record" banner.
5. `docs/planning/phase_014.yaml`: the canonical phase document. It has one
   step per feature, in lane order.
6. `.agent/product_spec_014.md` (spec 1.1.6): read "Maintenance tranche — design
   decisions", "Safety and state model", "Execution Order", "Scope budget
   measurement (phase-014 rule)" and "Human gates".
7. `.agent/feature_list_014.json`: the features, dependencies, estimates and
   executable acceptance tests.
8. `.agent/run_state.json`: the position, `scope_budget` and `circuit_breaker`.
   The append-only `history` is the decision log.
9. `docs/planning/DEBT.md`: the Open table.
10. `docs/planning/operator_gates.md`: every human gate and its disposition.
11. `methodology/00_planning.md` to `methodology/04_tool_driven_state.md`:
    planning, the two-loop execution, adversarial TDD, the circuit breaker, and
    durable state with the evidence convention.
12. `standard/AGF.md`: the Orchestrator and the four execution roles (§2), and the
    Dual Validator Gate (§3–§4).

Then read one completed feature end to end, to see the method in practice. Feature
105 is the most recent: `.agent/contracts/105.json`,
`.agent/validator/105-mode-a.json`, `.agent/qa/105-contract-review.json`,
`.agent/validator/105-mode-b.json`, `.agent/qa/105.json` and `.agent/evidence/105/`.

## (b) Current state at handover

**Release.**

- The latest tag is `v1.4.0`. It is an annotated tag object `bb32064` on commit
  `9edd5d0` (PR #63). `.github/workflows/release.yml` run 37763448754 published it. See ROADMAP
  Current Position.
- `main` now carries unreleased changes since then. They are listed under
  `CHANGELOG.md` `[Unreleased]`:
  - the post-release refresh (PR #64, `02b02c6`);
  - the phase-014 activation (PR #65, `483f016`);
  - features 099, 103, 104 and 105 (PRs #66, #67, #68 and #70).
- 099, 103 and 104 declare `MINOR` and 105 declares `PATCH` (`version_impact` in
  `.agent/feature_list_014.json`). So the next release is at least MINOR under
  `methodology/06_release_train.md`.
- That release is an operator `H-FRAMEWORK-RELEASE` decision. Phase 014 prepares
  no release. Read the tag hazard in (h) before any release.

**Phase 014 position.**

- `014-ga-track` is `in_progress` (`docs/planning/phase_014.yaml`;
  `docs/planning/manifest.json` `current_phase`).
- `.agent/run_state.json` reads `current_feature` `106`, `status` `in_progress`,
  `active_contract_id` `null` and `completed_contract_ids` `["099","103","104","105"]`.
  No feature is started.

**Completed features.** Each is `COMPLETED` in `docs/planning/phase_014.yaml` and `complete` in
the feature list.

| Feature | Goal | PR | Merge commit | Debt closed |
|---------|------|----|--------------|-------------|
| 099 | Activates `ecosystem/06_simplification_review.md` and `ecosystem/08_ga_gate.md`, and defines `H-CONSOLIDATION` and `H-GA` | #66 | `88959c9` | — |
| 103 | Explicit `UNSUPPORTED` / `CONFORMANCE: NOT FULL` outcome when user namespaces are unavailable. Includes amendment A1 (spec 1.1.3) and the scope-budget re-baseline (spec 1.1.4). | #67 | `b8ea889` | NDEBT-043 |
| 104 | `convergent_review` CI job in required-conformance mode. Includes amendment A2 (spec 1.1.5). | #68 | `2a53764` | NDEBT-041 |
| 105 | Nested-fixture claim map in `tools/fixtures_self_test.sh` (spec 1.1.6 adds budget-rule row 4a) | #70 | `e2a50ed` | NDEBT-042 |

**104's CI proof.**

- The positive run 37980556248 passed all four jobs, and the suite printed
  `CONFORMANCE: FULL` (`.agent/evidence/104/ci-positive-run.txt`,
  `.agent/evidence/104/ci-positive-log.txt`).
- The negative control 37980776642 failed `convergent_review` with
  `AssertionError: 40 != 0` (`.agent/evidence/104/ci-negative-log.txt`). It ran on
  draft PR #69, which was closed unmerged; its branch was deleted.
- Main is green at `e2a50ed`: `compliance` run 38015931994
  (`.agent/evidence/handover-2026-10/03-main-ci.txt`).

**Scope budget.**

- `original_estimate_lines` is 8600 and the 130 percent ceiling is 11180. The
  operator approved this re-baseline from 6660/8658: "option 1 confirmed." See
  `run_state.scope_budget.rebaseline` and spec 1.1.4.
- 3714 lines are budget-counted so far:

  | Item | Lines |
  |------|-------|
  | 099 | 596 |
  | 103 | 885 |
  | Phase-level re-baseline item | 292 |
  | 104 | 991 |
  | 105 | 950 |

- That leaves 4886 to the estimate and 7466 to the ceiling.
- Evidence lines are tracked separately and never gated (11988 recorded).
- The counting rule is the phase-014 rule only (spec "Scope budget measurement").
  `methodology/00_planning.md` §6 is unchanged.
  - **Budget-counted:** product, contracts, verdicts, audit deliverables and
    planning.
  - **Evidence:** everything under `.agent/evidence/`, plus any non-JSON file under
    `.agent/validator/` (row 4a).
  - **Excluded:** `.agent/run_state.json`.
- Measure with `.agent/evidence/scope-budget-014/measure.py`. It fails closed: an
  unclassified path makes it exit 3.
- The per-feature flag threshold is 3 × the mean of the last three features. For
  106 that is 3 × mean(885, 991, 950) = 2826.
- Re-measuring the squash commits on `main` gives slightly different figures,
  because lines edited twice net out:
  - 104 measures 1000 (`b8ea889..2a53764`), against 991 recorded.
  - The whole range `483f016..e2a50ed` measures 3663.

  The recorded per-range figures (3714) are the governing ones
  (`.agent/evidence/handover-2026-10/02-measure-main.txt`).
- **All the figures above are pre-handover.** They stand at `e2a50ed`, before this
  handover package is merged.

**How this handover's own lines count.**

- Spec 1.1.4 rule row 6 makes everything under `docs/planning/**` budget-counted
  planning. So this package counts: `docs/planning/HANDOVER.md` plus the
  edits to `docs/planning/ROADMAP.md`, `docs/planning/backlog_dag.json` and
  `docs/planning/backlog_reconciliation.md`. Its
  `.agent/evidence/handover-2026-10/` captures are evidence (row 2), and its
  `.agent/run_state.json` edit is excluded (row 1).
- **Measured before commit:** a working-tree measurement taken just before this
  final edit gave 805 budget-counted (all planning) and 9 excluded; the
  evidence total is in the capture
  (`.agent/evidence/handover-2026-10/10-measure-handover.txt`, replay
  `python3 .agent/evidence/scope-budget-014/measure.py --range handover=e2a50ed..`).
  The exact figure is the merged commit's, which the Orchestrator measures.
- **Treatment (the Planner's interpretation; not yet recorded).** The spec's
  "Attribution" rule says a feature's range normally starts at the previous
  feature's completion commit, and it names one exception: the 1.1.4 re-baseline,
  recorded as the phase-level item `rebaseline-1.1.4`. Read literally, 106's range
  would start at `e2a50ed` and absorb this package. The Planner's interpretation is
  that the handover is a second phase-level item, for the same reason the spec
  gives for the re-baseline: its cause is the operator's handover request
  (`operator_gate_decision` 2026-10-10T02:11:41Z), not feature 106. Charging it to
  106 would put 106 near the top of its own range (530–960) on planning lines
  alone.
  - As a phase-level item it would count toward `total_lines_changed` only, not
    toward any per-feature figure or the rolling baseline.
  - The estimate has no allowance for it (the 300 allowance was for the
    re-baseline), so it uses up headroom.
- **Authority.** `run_state.scope_budget` is Orchestrator-owned (`standard/AGF.md`
  §5). The treatment takes effect only when the Orchestrator records it, as it
  recorded `rebaseline-1.1.4` and the attribution of 105's planning record (the
  `planning_record` event for 105). The Orchestrator records:
  - a `phase_level_items` entry `handover-2026-10`, with range `e2a50ed..<H>`,
    where `<H>` is the commit that merges this handover PR into `main`;
  - its measured figure, added to `total_lines_changed`.

  The Orchestrator must record this, or a different stated treatment with its
  authority, before 106 starts. If it is not recorded, the spec's default
  applies: 106's range starts at `e2a50ed` (`--range 106=e2a50ed..`), and 106's
  per-feature figure includes this package.
- **106's measurement range under the recommended treatment.** It starts at `<H>`.
  - While 106 is in progress (working tree):
    `python3 .agent/evidence/scope-budget-014/measure.py --range 106=<H>.. --files`
  - At 106's completion commit `<C>`:
    `python3 .agent/evidence/scope-budget-014/measure.py --range 106=<H>..<C> --files`
  - `<H>` is this handover PR's merge commit on `main`. Find it with
    `git log --first-parent --oneline e2a50ed..main`.
- **Figures including the handover** (pre-commit measurement; replace with the
  Orchestrator's recorded figure):

  | Figure | Pre-handover | Including the handover |
  |--------|--------------|------------------------|
  | Budget-counted | 3714 | about 4519 |
  | Left to the estimate (8600) | 4886 | about 4081 |
  | Left to the ceiling (11180) | 7466 | about 6661 |
  | Projection with the 5350 remaining estimate | 9064 | about 9869 |

  106's rolling threshold stays 2826 under either treatment. It is 3 × the mean
  of the last three features' actuals, and a phase-level item is not a feature.

**Open debt.** At `docs/planning/DEBT.md` 0.51.0 there are eight Open rows, all
Low:

| Row | What it is | Where it is planned |
|-----|------------|---------------------|
| NDEBT-047 | The self-test C13 swap of `tools/skill.json` has no EXIT backstop | Unscheduled |
| NDEBT-046 | The sandbox tests do not discriminate the namespace half | Unscheduled |
| NDEBT-045 | The `--payload` help paragraph misstates the payload | Unscheduled; deliberately not in 108 |
| NDEBT-044 | The drift bundle, items (a) to (f) | (a) 106, (b) 107, (c)(d)(f) 108, (e) 102 |
| NDEBT-040 | SHA-anchored `run_state` byte-guards | Workflow Assurance NIP candidate |
| NDEBT-037 | `--help` stops at C13 | 108 |
| NDEBT-034 | Per-member clone cost | Deferred |
| NDEBT-026 | C15 mapping direction | 109 |

**CI.**

- `.github/workflows/compliance.yml` has four jobs: `validate`, `e2e_bootstrap`,
  `fixtures_self_test` and `convergent_review`.
- It runs on `pull_request` and on `push` to `main`.
- `.github/workflows/release.yml` and `.github/workflows/release_closeout.yml` gate
  tags and releases. `.github/workflows/pages.yml` publishes the guide.

## (c) The working method as practised

The operator set the per-feature workflow in a maintainer brief dated 2026-10-08.
**The brief is held by the operator and is not a repository artifact.**
`docs/planning/backlog_reconciliation.md` §1 records that the brief exists. The only
record of how it is applied is the Orchestrator's `operator_gate_decision` at
2026-10-09T19:28:39Z in `.agent/run_state.json`. That record summarizes the brief's
section 6 as 11 steps:

> the per-feature sequence is section 6's 11 steps (Generator contract -> Validator
> Mode A -> Evaluator contract review -> implement -> identified candidate -> Mode B
> -> Evaluator acceptance incl. the one adversarial check -> Orchestrator evidence
> gate), already followed for 099/103/104

The 12 steps below are the sequence **as practised** for 099, 103, 104 and 105, at
a finer granularity. They are reconstructed from the `run_state` history and the
feature records, not copied from the brief. The features did not all run them
identically; the variations in steps 5, 7 and 8 are stated in those steps. The gates are those of
`methodology/01_execution.md` and `standard/AGF.md`. The same record says its
application changes no active gate.

**Per-feature sequence.** Single lane: one feature at a time, and one writer for
each shared file.

1. **The Orchestrator starts the feature.**
   - It checks the dependency gate (`methodology/00_planning.md` §5).
   - It records `feature_started` in `run_state`.
   - It cuts `phase/014-<id>-<slug>` from `main`.
2. **The Generator proposes `.agent/contracts/<id>.json`.** The contract covers
   scope, the allowed and forbidden paths, verification steps and non-goals.
3. **Validator Mode A** checks the contract against the spec
   (`.agent/validator/<id>-mode-a.json`). If Mode A rejects, the Generator
   revises. Each revision counts as one `<id>-contract` attempt.
4. **The Evaluator reviews the contract** for testability, using mutation testing
   (`.agent/qa/<id>-contract-review.json`). For example, 104's review ran 113
   mutants. The reviewer's evidence goes under
   `.agent/evidence/<id>-qa-adversarial-contract-review/`.
   - **An Evaluator rejection also sends the contract back for revision, and that
     revision also uses up a `<id>-contract` attempt** (`methodology/01_execution.md`
     §2; `methodology/03_circuit_breaker.md` §2). The revised contract then goes
     through Mode A again.
   - Precedent, 103: Mode A rejected rev 0, and the Evaluator rejected rev 1. So the
     final rev 2 was attempt 3 of 3 (`run_state` history, 2026-10-09T14:33:52Z and
     15:28:25Z).
5. **The Orchestrator sets up the attempt.**
   - It commits the approved contract as the attempt base `<B>`.
     `.agent/evidence/<id>/attempt-base.txt` has recorded `<B>` since 103 (103,
     104, 105). For 099 the base `7115dc5` is recorded only in `run_state`
     (`implementation_attempt_started`, 2026-10-09T07:58:38Z).
   - It creates a detached worktree at `<B>`:
     `/home/<user>/workspace02/nizam-wt-<id>-attempt<N>`.
6. **The Generator implements only the contracted scope, inside that worktree.**
   - It makes exactly ONE commit, with its evidence under `.agent/evidence/<id>/`.
   - If it finds the contract is wrong, it stops and the contract goes back
     through Loop 1 (`methodology/01_execution.md` §3).
7. **The Orchestrator promotes the attempt.** It checks the commit is in scope,
   cherry-picks it onto the feature branch and removes the worktree
   (`run_state` `implementation_promoted` events for 099, 103, 104 and 105).
8. **Validator Mode B** checks the implementation against the approved contract
   (`.agent/validator/<id>-mode-b.json`).
   - **Order of steps 7 and 8.** For 099 and 103 the attempt was promoted first and
     Mode B ran on `git diff <B>..HEAD` of the promoted branch (`run_state`
     2026-10-09T08:03:25Z and 17:21:44Z). For 104 and 105 the Orchestrator ran
     Mode B round 1 on the unpromoted attempt commit inside the worktree, and
     promoted afterwards (`run_state` 19:27:22Z and 22:18:49Z). When the contract
     gives Mode B obligations on the promoted tree, a Mode B round after promotion
     is still needed: 105 needed a second Mode B round on the promoted tree
     (`.agent/validator/105-mode-b.json` `prior_rounds[0]` MB-1).
   - The Validator runs only read-only git commands (diff, show, log, status) and
     file reads. It cannot run the contract's verification commands
     (`.agent/validator/105-mode-b.json` `prior_rounds[0]` MB-1).
   - When a contract gives Mode B checks to execute, the Orchestrator runs them
     serially on the promoted tree and Mode B reviews the captures.
   - Precedent: `.agent/validator/105-mode-b-rerun/`.
9. **Evaluator QA** re-runs every check, plus exactly one adversarial check of its
   own design (`.agent/qa/<id>.json`, `.agent/evidence/<id>-qa-adversarial.txt`).
10. **The Orchestrator runs the evidence gate** (`methodology/01_execution.md` §3).
    The gate's rule is that every `*.txt` evidence file has the invocation on line 1
    and the actual exit status, `EXIT:<code>`, as its last line, and that every path
    the verdict cites exists.
    - **Practised convention:** every capture in a feature's own evidence
      directory (`.agent/evidence/<id>/` for 099, 103, 104 and 105) ends `EXIT:0`.
      See the `run_state` `feature_complete` event for 099 ("all EXIT:0").
      Negative controls keep this convention by capturing a command that succeeds:
      106 AT4 wraps a failing validator in
      `.agent/evidence/phase-014-activation/gates/scratch_run.py` with
      `--expect-rc 1`, and 104's negative-control capture is a successful
      `gh run view` of the failed run (`.agent/evidence/104/ci-negative-run.txt`).
    - Reviewer evidence does record non-zero statuses where a probe is meant to
      fail. Example:
      `.agent/evidence/099-qa-adversarial-contract-review/05-s3-reviewer-evidence-trap.txt`.
11. **Completion is canonical-first:**
    1. the `docs/planning/phase_014.yaml` step becomes `COMPLETED`;
    2. the feature-list entry becomes `complete`;
    3. the `run_state` position advances (the Orchestrator writes it).

    `tools/validate.sh` C16 enforces the verdict-before-complete invariant
    (`standard/definition_of_done.md`).
12. **The Orchestrator opens a PR, and the operator merges it.** No one else
    merges.

**Rules that bind every step.**

- **Circuit breaker (`methodology/03_circuit_breaker.md`).**
  - Each named step allows at most 3 attempts. Attempt 4 is forbidden outright
    (§3–§4). After the 3rd failure the step is `BLOCKED` and escalates to the
    operator. Only the operator can unblock it (§6): with a corrected approach, after
    which the step is attempted fresh, or by cancelling or descoping the feature.
  - **Recorded practice, not a rule in `03`:** when the operator authorizes one
    more round under §6, the Orchestrator records the operator's verbatim decision
    as a `human_authorized_extension` in `run_state.circuit_breaker`, with its exact
    scope. Precedents: `027-contract` (2026-07-10, limit raised for a redesign),
    `097-contract` (2026-08-18, one final revision) and `104-contract` (2026-10-09,
    contingent, not used).
  - Note: the `099-contract`, `103-contract`, `104-contract` and `105-contract`
    entries in `run_state.circuit_breaker` each record 3 attempts. Budget for this.
- **Durable state only (`methodology/04_tool_driven_state.md` §4;
  `standard/AGF.md` §5).** Results live in `.agent/`, never in chat.
- **`run_state` history is append-only.** It is Orchestrator-owned. The Planner,
  Generator, Validator and Evaluator never write it.
- **Record before act (NDEBT-018).** An operator decision is written to `run_state`
  as `operator_gate_decision`, with the operator's verbatim words, before the act
  it authorizes. It is committed first when a gated tool reads the tree
  (`ecosystem/01_clean_state_preflight.md` §4.1).
- **Evidence shape (`methodology/04_tool_driven_state.md` §5).**
  - Line 1 is the exact invocation, which must be replayable from the repo root
    with no session-absolute paths.
  - Then the raw output.
  - The last line is `EXIT:<code>`.
  - Timestamps are read from the clock (§5.1).
- **Attempt isolation and scope guards.**
  - The Generator works only in the attempt worktree.
  - The contract's allowed and forbidden paths are checked by the contract's own
    scope steps. Examples: `.agent/evidence/105/s02-attempt-root-delta.txt` and
    `.agent/evidence/105/s03-scope-boundary.txt`.
  - `.agent/evidence/phase-014-activation/` is frozen. No contract may touch it,
    and 102 AT7 pins its sha256 hashes.
- **JSON verdict parse rule (`standard/AGF.md` §4).** A gate passes only when
  `final_verdict.approved === true` and the `issues`,
  `missing_acceptance_coverage` and `unsupported_claims` arrays are all empty.
  Prose never counts.
- **Planner only for substantive change.** Use the Planner for requirement,
  architecture, dependency or acceptance-test changes, and for planning records:
  the A1/A2 amendments, spec PATCHes and DEBT records. Any acceptance-test change
  is a recorded amendment (`methodology/00_planning.md` §9).
- **Orchestration tooling.** The Orchestrator drove the agent stages with Claude
  Code Workflow-tool scripts. These are session-local and not in the repository.
  You may use any harness, provided every gate and record above is produced.
- **Outward acts are the Orchestrator's alone.** No other role pushes, opens a PR
  or touches a remote.
  - **Routine practice, with no per-act operator record:** pushing the feature
    branch and opening its PR (for example #68 and #70). These follow the
    contract's own steps. For example, the 2026-10-09T19:28:39Z record says "Push
    of the 104 feature branch ... now resumes per contract step 5".
  - **Recorded operator authorization, before the act (NDEBT-018):** throwaway or
    destructive acts and tags. For example, 104's throwaway branch push
    (`run_state` 2026-10-09T18:20:09Z), its never-merged draft PR #69 and its
    deletion (18:20:44Z), and the `v1.4.0` tag (ROADMAP change_log 0.45.0).
  - **Merges are the operator's own act.** The operator performs every merge.

**Not authorized (proposals only).** Reduced review profiles (backlog alias
`A15`), combined or parallel gates, and replacing an agent gate with a
deterministic one (alias `A10`) are all ideas for the Workflow Assurance NIP. That
NIP is outlined in `docs/planning/backlog_reconciliation.md` §7 but not authored.
None of them applies until an `H-NIP` and an `H-PHASE-NNN` decision exist.

## (d) Remaining backlog

The single lane is the canonical list order
(`.agent/product_spec_014.md` "Execution Order"):
**106 → 107 → 109 → 108 → 100 → 101 → 102**. The `estimated_lines` figures below
use the spec 1.1.4 budget-counted basis.

| Id | Goal (one line) | Depends on | Estimate | Gate / decision needed | Known hazards |
|----|-----------------|-----------|----------|------------------------|---------------|
| 106 | `tools/skill.json` is a documented *intentional subset* of `NIZAM.json`, enforced by extending C13. `ecosystem/00_ecosystem_bootstrap.md` gains its missing `NIZAM.json` capability. (NDEBT-044 a) | — | 750 (530–960) | None beyond H-PHASE-014 (satisfied) | No new check number (C17 is earmarked by NIP-0003). The new negative fixture must be exercised in the same change, or the self-test completeness guard (105) fails. The C13 substitution is the swap window of NDEBT-047. |
| 107 | NIP-0002's status `accepted` → `active`; every `docs/nips/*.md` under C1/C2 (NDEBT-044 b) | — | 680 (510–850) | None | `docs/nips/` must NOT join `build_shipped_md_set`, because C9/C10 would then fail on paths that proposals cite but that do not exist yet. Add the files to the C1/C2 inputs only. |
| 109 | An explicit `Role` column in `standard/capability_profiles.md` §2, a new `vlib_profiles_map_roles` primitive, and C15 calling both primitives (NDEBT-026) | — | 710 (520–890) | None | Compatibility-first. The existing `vlib_profiles_cover_roles` stays unchanged. It is a shipped-standard edit (version bump plus change_log). |
| 108 | Validator help and adapter-reference truth: the C14–C16 `--help` paragraphs, C5 "case-sensitive", the payload-doc set, and the `tools/interface.md` §5 item 10 reference (NDEBT-037, NDEBT-044 c/d/f) | 106, 107, 109 | 690 (510–860) | None | Runs last of the tranche, so it documents the final C1/C13/C15 behavior. NDEBT-045 is deliberately out of scope. `tools/interface.md` ships to consumers. |
| 100 | A real, non-scratch multi-repo pilot at `v1.4.0`, each member in an isolated worktree: Preflight → Baseline → Audit, then the membership-run aggregate. Evidence goes to `.agent/evidence/pilot-100/`. | — | 780 (550–1000) | **BLOCKED on the operator:** the member set, then a recorded `H-CONSUMER-UPGRADE` per member before its re-bootstrap. `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` only if a real plan or train is built. | No synthetic members. `aggregate.framework_pin` is the peeled commit `9edd5d0`, not the tag object `bb32064`. Each `gates-record.json` `decided_at` must equal a `run_state` event's `at`. Never work on a member's `main`. NDEBT-034 makes each member a full clone. |
| 101 | The first real simplification review (`ecosystem/06_simplification_review.md`) over the pilot evidence and the maintained surface. Candidates only. | 099, 100 | 890 (580–1200) | `H-CONSOLIDATION` only for an actual consolidation, which is out of this feature | Exactly one new `.agent/audits/*simplification*` directory relative to `.agent/evidence/phase-014-activation/audits-baseline.txt`. `review.json` must cite `.agent/evidence/pilot-100/aggregate.json`. |
| 102 | The GA-readiness dossier with **no** GA declaration, next-candidate refinement, and the canonical-first phase close | 099, 100, 101, 103–109 | 850 (600–1100) | `H-GA` stays OUTSTANDING (operator-only) | AT4 fails if any tag was created during the phase (see (h)). AT5 re-rolls the ROADMAP open-debt bullet to the live Open set. AT7 is the frozen-infrastructure hash pin. AT10 runs the self-test, so do not run it at the same time as the validator. |

The remaining estimate is 5350. With the 3714 counted before this handover, the
projection is 9064. Including this handover as a phase-level item (see (b)), it is
about 9869. Both are under the 11180 ceiling.

**What is blocked on the operator.**

1. **Feature 100.** It needs the real member repositories (and access to them).
   Then each member needs a recorded `H-CONSUMER-UPGRADE`. `H-PHASE-014` named no
   member (`.agent/product_spec_014.md` "Human gates").
   - Feature 101 cannot start until 100 is done, and 102 cannot start until 101
     is done.
   - If the operator names the members early, 100 may move up the lane by a
     recorded amendment (spec "Execution Order").
2. **`H-CONSOLIDATION` / `H-GA` semantics.** They are DEFINED and OUTSTANDING
   (`docs/planning/operator_gates.md` §1). Phase 014 never exercises either.
3. **`H-NIP` for NIP-0003.** `docs/nips/NIP-0003-live-runtime-sessions.md` is
   `draft` (merged as a proposal in PR #62). It is queued after phase 014 as
   phases 015/016. Its ids shift to about 110–120
   (`docs/planning/backlog_reconciliation.md` §5.3).
4. **The next `H-FRAMEWORK-RELEASE`.** Its timing interacts with 102 AT4; see (h).

## (e) Operator gates and authority

- **The operator (the human) decides:**
  - activation (`H-PHASE-NNN`) and NIP acceptance (`H-NIP`);
  - releases and tags (`H-FRAMEWORK-RELEASE`);
  - consumer adoption (`H-CONSUMER-UPGRADE`);
  - cross-repo plans and trains (`H-PLANNING-AUTHORITY`, `H-TRAIN-ENTRY`);
  - consolidation (`H-CONSOLIDATION`) and GA (`H-GA`);
  - accepting residual risk (`H-RISK`);
  - circuit-breaker extensions;
  - every PR merge.

  The registry is `docs/planning/operator_gates.md`.
- **Agents never** self-merge, self-tag, self-activate a phase, declare GA,
  consolidate, or accept risk on the operator's behalf.
- **How a decision is recorded.**
  1. The operator's words are quoted verbatim in a `run_state`
     `operator_gate_decision` event, before the act (NDEBT-018).
  2. The decision is then reflected in the gate registry row and in the spec or
     feature list when it changes the plan. Amendment A2 is an example:
     "B. Amend AT5" became spec 1.1.5.
  3. An ambiguous or truncated instruction is applied only as far as its text
     goes, and the interpretation is disclosed. See the 1.1.4 re-baseline record:
     the operator's message was truncated, and confirmation was sought and given.

## (f) Environment and gotchas

**Prerequisites.**

- `python3` with `jsonschema` and `PyYAML`.
- `git`, with worktree support.
- `gh`, for PR and run evidence.
- `bash`.
- SBCL only for NIP-0003 work (phases 015/016), not for phase 014.

**Required checks.** Run everything from the repo root, one command at a time
(see "Never run ... at the same time" below).

- **The validator:** `bash tools/validate.sh` must print
  `SUMMARY: 16 passed, 0 failed` and exit 0. `bash tools/validate.sh --payload` is
  the consumer view.
- **The phase-014 acceptance gate helpers** that the acceptance tests call. They are
  in the frozen tree, so run them but never edit them.
  - `python3 .agent/evidence/phase-014-activation/gates/validator_gate.py` and the
    same with `--payload` (106 AT6 and AT7, and others). The gate exits 0 only if
    the validator exits 0, prints one SUMMARY line with 0 failed and no `FAIL` line,
    and every check id that passed at activation still passes.
  - `python3 .agent/evidence/phase-014-activation/gates/scratch_run.py [--replace PATH OLD NEW]... --expect-rc N|nonzero [--expect REGEX]... -- CMD...`
    runs CMD in a mutated private copy of the repository and never writes the real
    tree (106 AT4). Its exit codes are 0 when the expectations hold, 1 when one
    fails, 2 for a usage error and 3 when a mutation precondition fails.
  - `python3 .agent/evidence/phase-014-activation/gates/phase_tag_check.py` (102
    AT4; see (h)).
- **The fixture self-test:** `bash tools/fixtures_self_test.sh` must exit 0 and end
  with `SELF-TEST OK: N/N fixtures accounted for, 0 failed`. N was 146 at
  `e2a50ed`, and it grows with each fixture a feature adds (106 plans one new
  negative fixture). 106 AT3 and AT8 run it.
- **The four CI jobs, locally** (`.github/workflows/compliance.yml`):
  - `validate`: `bash tools/validate.sh`
  - `e2e_bootstrap`: `bash tools/e2e_bootstrap_test.sh`. It creates an ephemeral
    `e2e-*` tag on the local `HEAD`, bootstraps a file:// clone of that commit into
    a scratch target, and deletes the tag. It exercises committed `HEAD` only, so
    commit before you rely on it. The `e2e-*` tags are the ones
    `.agent/evidence/phase-014-activation/gates/phase_tag_check.py` exempts.
  - `fixtures_self_test`: `bash tools/fixtures_self_test.sh`
  - `convergent_review`: `python3 tools/test_convergent_review.py` (see
    "User-namespace isolation" below).

**User-namespace isolation.**

- Some hosts set `kernel.apparmor_restrict_unprivileged_userns=1`. Ubuntu
  24.04-style defaults do, and so does the previous maintainer's workstation.
- On those hosts, `python3 tools/test_convergent_review.py` reports the five
  sandbox tests `UNSUPPORTED` and prints `CONFORMANCE: NOT FULL`, exiting 1.
  **This is by design (103).**
- Use `--allow-unsupported-isolation` ONLY locally. CI runs in required mode and
  passes on GitHub-hosted Ubuntu runners (run 37980556248).

**Never run `tools/validate.sh` and `tools/fixtures_self_test.sh` at the same
time.** The self-test's C13 probe temporarily swaps `tools/skill.json`, so a
validator run during that swap sees the wrong file. Run them serially. This is why
Mode B re-runs are serialized.

**NDEBT-047 recovery.**

- If the self-test is interrupted, `tools/skill.json` can be left swapped.
- The symptom: `git status` shows ` M tools/skill.json`, and validate reports
  `[C13] FAIL`.
- The fix: `git checkout -- tools/skill.json`.

**CI cancellation.** `.github/workflows/compliance.yml` sets
`concurrency: cancel-in-progress: true`, keyed on workflow and ref. A new push to
the same PR branch cancels the run in progress. So capture run ids only from the
final push.

**Budget measurement.** `measure.py` fails closed. A new file family outside the
rule's classes makes it exit 3 (this happened in 105 and led to row 4a). Classify
the path through a Planner PATCH; never by hand.

**Pre-existing failures that are not your regression.**

- `.agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py`
  fails V7 and V13 at `e2a50ed`. See (g).

## (g) Housekeeping inventory

**Recommendations only. Nothing here was deleted.** Captured in
`.agent/evidence/handover-2026-10/04-branch-inventory.txt`.

**Local branches whose PR is merged.** Their squash merges mean `git branch
--merged` does not list them.

| Branch | PR |
|--------|----|
| `chore/nip-0003-live-runtime-sessions` | #62 |
| `chore/v1.1.0-post-release` | #56 |
| `chore/v1.4.0-post-release` | #64 |
| `chore/v1.4.0-release-prep` | #63 |
| `phase/013-definition-of-done` | #55 |
| `phase/014-099-ga-activation-wave` | #66 |
| `phase/014-103-sandbox-prereq` | #67 |
| `phase/014-104-sandbox-ci` | #68 |
| `phase/014-105-nested-fixture-ownership` | #70 |
| `phase/014-ga-track` | #65 |

These are safe to delete after the operator confirms.

**Local branch with no PR.**

- `chore/backlog-reconciliation` sits at `9edd5d0`, an ancestor of `main`, with no
  commits of its own.
- Its worktree `nizam-framework-wt-reconcile` holds two untracked draft paths. The
  draft was re-checked and superseded by the PR #65 package
  (`docs/planning/backlog_reconciliation.md` change_log 0.1.0).
- Recommend `git worktree remove --force` on it, then delete the branch.

**Remote branches whose PR is merged.**

| Branch | PR |
|--------|----|
| `chore/scrub-coderabbit-example` | #59 |
| `chore/v1.0.0-post-release` | #54 |
| `chore/v1.4.0-post-release` | #64 |
| `claude/nizam-framework-agent-personas-9lraqo` | #42–#51 |
| `claude/nizam-framework-agent-personas-9lraqo-tier0` | #40 |
| `claude/nizam-framework-agent-personas-9lraqo-tier1` | #41 |
| `claude/upbeat-cray-4mtqm9` | #58 |
| `feat/methodology-review-gate-flake-management` | #60 |
| `feat/phase-014-ga-track-proposal` | #61 |
| `phase/012-v1-consumer-safety` | #53 |
| `phase/013-definition-of-done` | #55 |
| `phase/014-099-ga-activation-wave` | #66 |
| `phase/014-103-sandbox-prereq` | #67 |
| `phase/014-104-sandbox-ci` | #68 |
| `phase/014-105-nested-fixture-ownership` | #70 |
| `phase/014-ga-track` | #65 |

Note that `origin/phase/014-ga-track` is the stale head `c061b31`. That is why
amendment A2 re-pointed 104 AT5.

**Remote branch with no PR.**

- `origin/claude/epic-wozniak-jw1zmo` (`7e4c5b2`, "release: prepare v1.2.0") is
  1 commit ahead of `main`. v1.2.0 shipped through PR #58.
- Recommend the operator reviews it before deleting it.

**Worktrees.** Besides the main tree, there are:

- `nizam-framework-wt-reconcile`, described above;
- a detached session-scratch worktree at `9edd5d0` under the previous session's
  temporary directory, which is safe to `git worktree remove`.

No `nizam-wt-*` attempt worktree remains.

**Stale records not fixed here.**

- `.agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py`
  V7 still fails: the packets for F099, F103, F104 and
  F105 still read `pending`.
  - This refresh synced only the budget figures and the spec version in
    `docs/planning/backlog_dag.json`: `activated_phase` is now 8600/11180 at spec
    `1.1.6`, and the packets' weighted estimates now match the canonical
    `estimated_lines`. Before the refresh, V7 also failed on those estimates.
  - Packet statuses mirror feature statuses, so this record does not change them.
  - The Orchestrator should refresh them, or 102's close should.
  - In an uncommitted working tree, V11 also fails on any path outside the
    reconciliation package (this handover's files included). After commit it
    passes (`.agent/evidence/handover-2026-10/05-backlog-dag.txt`).
- V13 still fails. It checks two things
  (`.agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py`):
  1. **Spec-version lockstep.** The product spec, the feature list and the DAG's
     `activated_phase.spec_version` must agree. At `e2a50ed` the DAG still read
     `1.1.2` against `1.1.6`. This refresh sets it to `1.1.6`, and also restates
     the DAG's `plan_status_note` and `estimate_weighting.basis`, so this part now
     passes. The change is recorded in `docs/planning/backlog_reconciliation.md`
     change_log 0.1.5.
  2. **Estimate reconciliation.** The `.agent/feature_list_014.json` per-feature
     estimates must sum to its `original_estimate_lines`, and the DAG must carry
     the same figure. They sum to 7980, against 8600. This gap is by design and
     disclosed in spec 1.1.4: 099 and 103 keep their old all-paths estimates (920
     and 280), and 8600 also holds the 300 re-baseline allowance. This part fails.
     It can pass only after a canonical change, which is a Planner spec PATCH: the
     feature-list estimates or `original_estimate_lines` would have to change. The
     DAG then mirrors the result.
- The DAG's derived critical path currently runs through `F099`, not `F100`,
  because the stale `pending` statuses leave `F099` weighted at 920. With the
  statuses refreshed it runs through `F100` again. See
  `docs/planning/backlog_reconciliation.md` §6 and
  `.agent/evidence/handover-2026-10/09-dag-critical-path.txt`.
- 104's recorded 991 against the 1000 re-measured on `main` is left as recorded.
  The pre-existing gap is noted in the 105 `planning_record`.
- `docs/planning/manifest.json` `updated_at` and the phase-014 note were last
  touched at activation. They are history and still true, so they are unchanged.

## (h) Open questions and known tensions

1. **The NIP-0003 runtime_session claim.**
   - NIP-0003 feature 108 (now about 115) creates
     `tools/fixtures/runtime_session/`.
   - The NIP's own text has its feature 109 (now about 116) register that
     subdirectory in 105's claim map.
   - An unclaimed subdirectory fails the self-test. So the claim row must land in
     the same change that creates the directory.
   - This is open for the NIP's pre-acceptance revision
     (`docs/planning/backlog_reconciliation.md` §5.3).
2. **102's open-debt roll versus this refresh.**
   - This handover rolled the ROADMAP Current Position open-debt bullet to the
     eight Open ids at DEBT 0.51.0, as NDEBT-044 (e) asks "at the next Current
     Position refresh".
   - 102 AT5 still re-rolls it at phase close, against whatever is Open then.
   - NDEBT-044 stays Open until (a)–(d) and (f) land.
3. **Release timing versus 102 AT4.**
   - 102 AT4 runs
     `.agent/evidence/phase-014-activation/gates/phase_tag_check.py`, which fails
     if any tag (other than the ephemeral `e2e-*`) was created after activation.
   - So releasing the unreleased 099–105 changes before phase 014 closes would
     break 102 AT4, unless the Planner records an amendment first. The gate script
     itself is frozen; only the acceptance test could change.
   - The ROADMAP's NIP-0003 section (`docs/planning/ROADMAP.md`, "Proposed
     realization, to follow phase 014") says phase 015, the NIP-0003 normative
     surface, "releases as the next MINOR (expected v1.5.0) ... and also rolls up
     phase 014's unreleased changes". That expectation depends on `H-NIP` for
     NIP-0003 and then `H-PHASE-015`, neither of which exists yet. If they do not
     happen, when phase 014's changes are released is an open
     `H-FRAMEWORK-RELEASE` question.
4. **Every contract so far needed all three rounds** (`run_state.circuit_breaker`).
   - Plan contract authoring carefully.
   - There is no 4th round by right. One happens only if the operator authorizes
     it under `methodology/03_circuit_breaker.md` §6 and the Orchestrator records
     the decision as a `human_authorized_extension` before it starts (see (c)).
