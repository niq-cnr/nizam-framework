---
id: nizam-remediation-2026-10-18
title: "Critical Quality and Velocity Remediation Brief — 2026-10-18"
description: "Single coordination brief recording the 2026-10-18 operator remediation mandate, live-work reconciliation, CI suite ownership and timing baseline, and reconciled backlog order."
version: 0.18.1
status: active
authoritative_source: docs/planning/REMEDIATION_2026_10_18.md
change_log:
  - version: "0.18.1"
    date: "2026-10-28"
    summary: "Qualify historical A7 cost-unit reductions as uncalibrated proxies; preserve completion records and source captures."
  - version: "0.18.0"
    date: "2026-10-22"
    summary: "Mark the remediation mandate COMPLETE as a predecessor and superseded for active direction by mandate NIZAM-JEV-OWNER-2026-10-22 (docs/planning/jev-readiness/PROGRAM.md). All dated R/A/B/C execution facts, evidence paths and release records remain historical and unchanged; no missing remediation work is implied."
  - version: "0.17.0"
    date: "2026-10-19"
    summary: "Complete v1.10.1 release, GitHub Pages deployment, and .nizam/ self-adoption: PR #125 merged at 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd (compliance.yml run 39239133568 succeeded in 17m16s); annotated tag v1.10.1 (5b6fdb64a5bc3bf1def755b8269696d9e95b3a41) published via release.yml run 39241606087 at 2026-10-19T11:01:33Z and GitHub Pages deployed via pages.yml run 39241597482; and .nizam/ re-bootstrapped to v1.10.1 (278 released files + provenance.json, installed_at 2026-10-19T11:03:39Z, evidence .agent/evidence/release-v1.10.1-closeout/)."
  - version: "0.16.0"
    date: "2026-10-19"
    summary: "Prepare v1.10.1 PATCH release packaging the operator-requested full documentation and GitHub Pages refresh across docs/guide/index.html, CONTEXT.md, ecosystem/01_clean_state_preflight.md (v0.1.5), methodology/10_live_runtime_sessions.md (v0.2.1), methodology/11_sbcl_runtime_binding.md (v0.1.2), schema/README.md (v0.20.2), tools/interface.md (v0.5.2), tools/README.md (v0.37.2), tools/SKILL.md (v0.8.2), tools/skill.json (v0.8.2), NIZAM.json (1.10.1), and tools/test_public_entry.py."
  - version: "0.15.0"
    date: "2026-10-19"
    summary: "Complete packet C5 and exit temporary corrective override mode: PR #123 merged at 6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7 (compliance.yml run 39216541409 succeeded in 17m19s); annotated tag v1.10.0 (8971603d2091fd5f5602f556b49499a0c8aa7a29) published via release.yml run 39218964275 at 2026-10-19T07:54:01Z; .nizam/ re-bootstrapped to v1.10.0 (278 released files + provenance.json, installed_at 2026-10-19T07:56:18Z, evidence .agent/evidence/release-v1.10.0-closeout/ including standalone strict consumer --verify-only rehearsal); and AGENTS.md (v0.4.0) transitional corrective banner removed."
  - version: "0.14.0"
    date: "2026-10-19"
    summary: "Complete packet C4 independent acceptance (.agent/evidence/remediation-2026-10-18/c4-independent-acceptance.json) against immutable candidate 29ab5689652866cbb51c2f16b2911874ec591c19 across all 8 rows of the Section 8 acceptance matrix (C1 mediation/binding/recovery/observations, C2 trust/result-handling/ordinary-consumer, C3 continuation, and integrated entry) and proceed to C5 PR delivery, v1.10.0 release, and .nizam/ re-bootstrap."
  - version: "0.13.1"
    date: "2026-10-19"
    summary: "Complete packets C1, C2, and C3 implementation and local verification (closing F1-F3 across tools/start_path.py, tools/payload_integrity.py, bootstrap.sh, methodology/00_planning.md, methodology/01_execution.md, schema/run_state.schema.json, standard/GIP.md, standard/permission_classes.md, ecosystem/00_ecosystem_bootstrap.md, tools/interface.md, tools/SKILL.md, tools/skill.json, tools/README.md, and test suites) and prepare the v1.10.0 MINOR release anchors (NIZAM.json, CONTEXT.md, README.md, docs/guide/index.html, CHANGELOG.md, docs/planning/ROADMAP.md, docs/planning/operator_gates.md) for C4 independent acceptance and C5 delivery."
  - version: "0.13.0"
    date: "2026-10-19"
    summary: "Adopt the v1.9.0 audit and follow-up execution mandate (C0-C5, closing F1-F3 against audited release v1.9.0 at 0c9b1c5979a922c75499e0bfe4d9dbf9524f717d and compared main 3efa3e02df56781960dfa8d0ecf143360c617ff8, compliance run 39175072688 in 17m25s): record continuing operator process-override authority, reconcile Issue #107 against completed Feature 134 and residual NDEBT-056, record one-shot C0 baseline probes (.agent/evidence/remediation-2026-10-18/c0-baseline-probes.json), and define packets C0-C5."
  - version: "0.12.0"
    date: "2026-10-18"
    summary: "Complete packet B6 and exit temporary corrective override mode: Corrective Slice 3 (B5 + B6 pre-tag at 40372780b328359fb4757651640920f11f14a23f) independently accepted and merged via PR #121 at 0c9b1c5979a922c75499e0bfe4d9dbf9524f717d (compliance.yml run 39171134860 succeeded); annotated tag v1.9.0 (7e721b6e0fb2a0a3014efda388e1097378e3da87) published via release.yml run 39172587918 at 2026-10-18T22:31:27Z; .nizam/ re-bootstrapped to v1.9.0 (278 released files + provenance.json, installed_at 2026-10-18T22:32:25Z); and AGENTS.md (v0.3.0) transitional corrective banner removed."
  - version: "0.11.0"
    date: "2026-10-18"
    summary: "Record independent acceptance of Corrective Slice 1 (B0-B2 at 9cc9547ffc09694cea324bb009916811d786d2c5, closing V1, V2, and V7 regression) and Corrective Slice 2 (B3-B4 at f825908e80100a2e13b9157b6a4f72908dd26a24, closing V3, V4, V5, and V6), complete packet B5 end-to-end consumer discrimination in tools/e2e_bootstrap_test.sh, and prepare the v1.9.0 MINOR release anchors (NIZAM.json, CONTEXT.md, README.md, docs/guide/index.html, CHANGELOG.md, docs/planning/ROADMAP.md, docs/planning/manifest.json, docs/planning/operator_gates.md) for integrated PR delivery, tag creation, and post-tag .nizam/ re-bootstrap (B6)."
  - version: "0.10.0"
    date: "2026-10-18"
    summary: "Adopt the v1.8.0 rollout corrective execution mandate (B0-B6, closing V1-V7 against audited release v1.8.0 at 606d11ee84deff0d3b7934cbfd715223d64ac79d and compared main 016a1b79e0be6bc5b7459baae3c67ee99f2803f6, compliance run 39133101798 in 13m35s): record continuing operator process-override authority, backlog mapping, and B0-B6 execution DAG."
  - version: "0.9.0"
    date: "2026-10-18"
    summary: "Complete packet A8 and exit temporary remediation override mode: PR #119 merged at 606d11ee84deff0d3b7934cbfd715223d64ac79d (compliance.yml run 39128908966 succeeded in 18m23s); annotated tag v1.8.0 (faeb50dfdb055cc4d5018ab8d474979be71f876f) published via release.yml run 39130412824 at 2026-10-18T13:11:05Z; .nizam/ re-bootstrapped to v1.8.0 (277 released files + provenance.json, installed_at 2026-10-18T13:12:27Z); and AGENTS.md (v0.2.0) transitional remediation banner removed."
  - version: "0.8.0"
    date: "2026-10-18"
    summary: "Record independent acceptance of Follow-Up Slice 3 packets A6-A7 (345b0c1a81bb6138ca2d2d917af4639cbd93d5c4) and prepare the v1.8.0 MINOR release anchors (NIZAM.json, CONTEXT.md, README.md, docs/guide/index.html, CHANGELOG.md, docs/planning/ROADMAP.md, docs/planning/manifest.json, docs/planning/operator_gates.md) for integrated PR delivery, tag creation, and post-tag .nizam/ re-bootstrap (A8)."
  - version: "0.7.0"
    date: "2026-10-18"
    summary: "Record independent acceptance of Follow-Up Slice 1 (8c7d50a9a712f4fd9a29e160c422f9465e40b226, closing F1, F2, F5) and Follow-Up Slice 2 (149d7d6647cbcccab853f02ce37fc00f1e4e8605, closing F3, F4, F6), and complete Follow-Up Slice 3 packets A6 (disposable consumer zero-reach-back lifecycle rehearsal in tools/e2e_bootstrap_test.sh and .nizam/schema fallback in _receipt_schema) and A7 (12-task preregistered paired baseline-vs-shadow comparison in .agent/evidence/125/ and .agent/evidence/remediation-2026-10-18/pilot-report.json)."
  - version: "0.6.0"
    date: "2026-10-18"
    summary: "Adopt the 2026-10-18 post-remediation audit and follow-up execution mandate (A0-A8) at 2026-10-18T10:10:00Z: reassert continuing operator authority over obstructive repository-local governance until A8 completes; correct run 39064043210 attribution to PR #114 head 7c049c88 and record PR #115 (39075498443, 99m27s), PR #116 (39111912990, 18m12s), and merged main (39115161856, 18m23s) hosted CI facts; reclassify R9/R10 profile and pilot records (.agent/evidence/125/ and .agent/evidence/remediation-2026-10-18/pilot-report.json) as historical smoke/parser/record-validation evidence pending A3/A6/A7/A8; and restore explicit transitional entry precedence in AGENTS.md."
  - version: "0.5.1"
    date: "2026-10-18"
    summary: "Align CI Python minor pin to 3.14 (avoiding /opt/hostedtoolcache 3.12 stdlib landmark collision inside native Landlock sandbox on Ubuntu 24.04) and normalize .git suffix matching in tools/start_path.py for GitHub Actions checkouts."
  - version: "0.5.0"
    date: "2026-10-18"
    summary: "Record Slice 4 independent acceptance (b99041dc948522a52832c8871fc3ec8e3c073091), Slice 5 (R10 + R11) 15-task representative pilot across all five routes and clean disposable consumer checkout rehearsal (.agent/evidence/remediation-2026-10-18/pilot-report.json), and clean exit from temporary remediation mode."
  - version: "0.4.0"
    date: "2026-10-18"
    summary: "Record Slice 3 independent acceptance (14ae992fed5217f016e8ee7edb542c67725d9e48) and Slice 4 (R9) Phase 019 generic repository/worktree assurance profile preregistration (124) and shadow comparison/recommendation (125)."
  - version: "0.3.0"
    date: "2026-10-18"
    summary: "Record Slice 2 independent acceptance (3132337b1a46132a573a854a2db835b84081cc68) and Slice 3 (R5 + R6 + R7 + R8) implementation: 5-route task classification, trivial path, lightweight contract amendments, unified stopping rules, exclusive evidence capture, Option A repository-binding migration, receipt/resume CLI, and concise status view."
  - version: "0.2.0"
    date: "2026-10-18"
    summary: "Record Slice 2 (R3 + R4) bounded ControlsFixture/controls_snapshot timings and retirement of the default whole-module MASKED_AST freeze."
  - version: "0.1.0"
    date: "2026-10-18"
    summary: "Adopt the 2026-10-18 critical quality and velocity remediation mandate (R0), record the CI suite ownership and timing baseline (R1), and reconcile the R0-R11 backlog order."
---

# Critical Quality and Velocity Remediation — 2026-10-18

> **Status (2026-10-22):** this remediation and its A/B/C follow-ups are
> **COMPLETE as historical records**. The active engineering direction is
> mandate `NIZAM-JEV-OWNER-2026-10-22`, recorded in
> [/docs/planning/jev-readiness/PROGRAM.md](/docs/planning/jev-readiness/PROGRAM.md). Nothing below is a
> current directive or a request for new remediation work.

## 1. Mandate Adoption & Continuing Follow-Up Authority (R0, A0, B0 & C0)

- **Initial mandate adopted at**: `2026-10-18T04:45:00Z`
- **Follow-up audit & execution mandate (`A0`–`A8`) adopted at**: `2026-10-18T10:10:00Z`
- **Completed `A8` & `v1.8.0` self-adoption at**: `2026-10-18T13:15:00Z` (PR #120 merged at `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`, `compliance.yml` run `39133101798` succeeded in `13m35s`)
- **`v1.8.0` rollout corrective mandate (`B0`–`B6`) adopted at**: `2026-10-18T14:55:00Z`
- **Completed `B6` & `v1.9.0` self-adoption at**: `2026-10-18T23:06:00Z` (PR #121 merged at `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, `compliance.yml` run `39171134860` succeeded; annotated tag `v1.9.0` `7e721b6e0fb2a0a3014efda388e1097378e3da87` published via `release.yml` run `39172587918` at `2026-10-18T22:31:27Z`; PR #122 merged `.nizam/` `v1.9.0` self-adoption at `3efa3e02df56781960dfa8d0ecf143360c617ff8`, `compliance.yml` run `39175072688` succeeded in `17m25s`)
- **`v1.9.0` audit & follow-up mandate (`C0`–`C5`) adopted at**: `2026-10-19T05:50:00Z` (closing `F1`–`F3` against audited release `v1.9.0` `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d` and compared `main` `3efa3e02df56781960dfa8d0ecf143360c617ff8`)
- **Completed `C5` & `v1.10.0` self-adoption at**: `2026-10-19T07:58:00Z` (PR #123 merged at `6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7`, `compliance.yml` run `39216541409` succeeded in `17m19s`; annotated tag `v1.10.0` `8971603d2091fd5f5602f556b49499a0c8aa7a29` published via `release.yml` run `39218964275` at `2026-10-19T07:54:01Z`; `.nizam/` re-bootstrapped to `v1.10.0` at `2026-10-19T07:56:18Z`, `278` released files + `provenance.json`, evidence `.agent/evidence/release-v1.10.0-closeout/`)
- **Repository**: `niq-cnr/nizam-framework` (`https://github.com/niq-cnr/nizam-framework.git`)
- **Authoritative instructions**: Operator remediation mandate dated 18 October 2026 ("Nizam framework critical quality and velocity remediation prompt"), operator post-remediation audit & follow-up execution mandate dated 18 October 2026 ("Nizam framework: post-remediation audit and follow-up execution prompt", audited source `8815d311ea512d3bbd7dafddfc124a6197b38c72`), operator `v1.8.0` rollout corrective execution mandate dated 18 October 2026 ("Nizam framework v1.8.0 rollout corrective execution prompt", audited release `v1.8.0` at `606d11ee84deff0d3b7934cbfd715223d64ac79d`), and operator `v1.9.0` audit and follow-up execution mandate dated 19 October 2026 ("Nizam framework v1.9.0 audit and follow-up execution prompt", audited release `v1.9.0` at `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, compared `main` `3efa3e02df56781960dfa8d0ecf143360c617ff8`), recorded in `.agent/run_state.json` and this single brief.
- **Process precedence (`C0`–`C5` Completed & Override Exited)**: Temporary corrective override mode exited cleanly upon re-bootstrapping `.nizam/` to the released `v1.10.0` tag (`6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7`) and removing the transitional override banner in `AGENTS.md` (`v0.4.0`). All packets preserved:
  1. Independent acceptance of the integrated candidate by a non-authoring reviewer (`C4`).
  2. Real, accurately captured verification results tied to the committed candidate and execution inputs.
  3. Security and correctness invariants (identity, authorization, isolation, source integrity, claimed vs. authenticated authority, and externally mediated Git commit boundaries).
  4. Ownership of writes, preservation of unrelated work, and recoverability.
  5. Honest lifecycle status across implemented, tested, independently accepted, merged, released, installed, and commissioned states.

## 2. Live-Work Reconciliation (R0, A0, B0 & C0)

- **Initial `main` baseline (`R0`)**: `e3748676f4f12a5a1a10bf1a100869db773b70ee` (PR #114 merge); PR #115 merged Feature 134 (`144e20e09bd17257c34873e1608a24bb6f05248d`), and PR #116 merged `R0`–`R11` at audited source `8815d311ea512d3bbd7dafddfc124a6197b38c72`.
- **Follow-up `main` & release baseline (`A0`)**: PR #117 (`47851d857e0ab879b848610128ee6e9e13368f0d`) released tag `v1.7.0` (annotated tag object `6a4cf599f3850ae31561ba38f9da29237d0a4a53`; `release.yml` run `39116785402` succeeded), and PR #118 (`f64333c203ee4cf3693b32c2bf28735b088ab3f8`) merged the `v1.7.0` closeout and `.nizam/` re-bootstrap (`277` released files + `provenance.json`, `commissioning_performed: false` per `docs/planning/SELF_GOVERNANCE.md`).
- **Completed follow-up delivery (`A0`–`A8`) & `B0`–`B6` baseline**: Closed audit findings `F1`–`F6` (`A0`–`A8`, `v1.8.0` at `606d11ee84deff0d3b7934cbfd715223d64ac79d`, PR #120 at `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`), and closed `V1`–`V7` (`B0`–`B6`, PR #121 at `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, tag `v1.9.0` `7e721b6e0fb2a0a3014efda388e1097378e3da87`, PR #122 at `3efa3e02df56781960dfa8d0ecf143360c617ff8`, `compliance.yml` run `39175072688` in `17m25s`).
- **`C0` Backlog & Issue `#107` Reconciliation**:
  - `.agent/feature_list_019.json` (`124`, `125`), `.agent/feature_list_020.json` (`129`), `.agent/feature_list_021.json` (`133`), and `.agent/feature_list_022.json` (`134`) remain `complete`. Phase 020 features `130`–`132` (persistent SBCL runtime qualification) remain `pending` and off the critical path for `C0`–`C5`.
  - GitHub Issue `#107` ("Docker sandbox adapter & live-model observation qualification (NDEBT-056)") was inspected against completed Feature `134` (PR #115 `144e20e09bd17257c34873e1608a24bb6f05248d`) and `docs/planning/DEBT.md` (`NDEBT-056`). Feature `134` delivered the Docker container sandbox adapter (`--sandbox-adapter=docker`) and adapter-specific conformance selection, while `NDEBT-056` and Issue `#107` explicitly retain the residual requirement for no-network live-model observation qualification and digest re-pin policy. Issue `#107` therefore remains open for that distinct residual debt item and does not conflict with or block `C0`–`C5`.

## 3. Suite Ownership & Timing Baseline (R1, A0, B0 & C0 Audited Hosted Runs)

### 3.1 Pre-Remediation and Post-PR #116 Hosted Timing Baseline

| Source | Job / Suite | Observed Duration | Root Cause / Notes |
|---|---|---|---|
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, `2026-10-18T00:08:23Z`–`01:47:50Z`, total `99m27s`) | `validate` / `e2e_bootstrap` / `self_governance` | `19s` / `54s` / `28s` | Fast jobs on PR #114 head `7c049c8805a5d48a9729f2d80e0a7e4a5086a2cb` (previously mislabeled in v0.1.0–v0.5.1 as `main` `e3748676`) |
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, total `99m27s`) | `fixtures_self_test` | `84m47s` | `fixtures_self_test.sh` (`42m33s`, dominated by `ci-candidate-bound` + `ci-blocker-rejected`) + full `test_workflow_assurance.py` (`41m50s`, running `ci-candidate-bound` + `ci-blocker-rejected` a second time) |
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, total `99m27s`) | `convergent_review` | `35m40s` | Isolation suite (`8s`) + duplicate `fixtures_self_test.sh` (`35m03s`, running `ci-candidate-bound` + `ci-blocker-rejected` a third time) |
| Hosted Actions run `39075498443` (PR #115 `fe78e4fe`, `2026-10-18T02:23:03Z`–`04:02:30Z`, total `99m27s`) | Full `compliance.yml` | `99m27s` | Immediately preceding successful PR #115 run (`fixtures_self_test` + `convergent_review` with native + Docker isolation suites and duplicate `fixtures_self_test.sh`) |
| Hosted Actions run `39111912990` (PR #116 final candidate `ec70cefb`, total `18m12s`) | Full `compliance.yml` | `18m12s` | **~81.7% reduction** vs. PR #115 (`39075498443`): full Workflow Assurance step `15m06s`, general fixture step `2m37s`, `convergent_review` job `1m11s` |
| Hosted Actions run `39115161856` (merged `main` `8815d311`, `2026-10-18T09:23:47Z`–`09:42:10Z`, total `18m23s`) | Full `compliance.yml` | `18m23s` | **~81.5% reduction** vs. PR #115 (`39075498443`) on the merged candidate (cross-revision hosted observation, not a controlled benchmark or agent active-time measurement) |
| Hosted Actions run `39128908966` (PR #119 follow-up candidate `bbe5b415`, `2026-10-18T12:49:37Z`–`13:08:00Z`, total `18m23s`) | Full `compliance.yml` | `18m23s` | Preserves the **~81.5% reduction** vs. PR #115 (`39075498443`) while adding `assert_consumer_zero_reachback` (`e2e_bootstrap` `1m16s`) and the 12-task `profiles-ready` verification |
| Hosted Actions run `39133101798` (merged `main` `016a1b79`, PR #120 `v1.8.0` self-adoption) | Full `compliance.yml` | `13m35s` | **~86.3% reduction** vs. PR #115 (`39075498443`) on the `v1.8.0` self-adopted `main` commit `016a1b79e0be6bc5b7459baae3c67ee99f2803f6` |
| Hosted Actions run `39175072688` (merged `main` `3efa3e02`, PR #122 `v1.9.0` self-adoption) | Full `compliance.yml` | `17m25s` | Delivery evidence on the `v1.9.0` self-adopted `main` commit `3efa3e02df56781960dfa8d0ecf143360c617ff8` (not a controlled performance comparison) |

### 3.2 Authoritative Five-Job Suite Ownership (`compliance.yml`)

Each check family has exactly one authoritative CI job owner inside the existing five-job topology (`validate`, `e2e_bootstrap`, `fixtures_self_test`, `convergent_review`, `self_governance`):

| CI Job | Authoritative Suite Ownership | Duplication Removed in R2 |
|---|---|---|
| `validate` | `bash tools/validate.sh` (full C1–C16 compliance sweep) | None |
| `e2e_bootstrap` | `bash tools/e2e_bootstrap_test.sh` (end-to-end bootstrap, `--genesis`, multi-repo, stage-4, and `--payload` CWD-independence) | None |
| `fixtures_self_test` | (1) `.github/scripts/test_c13_cleanup.py`, (2) `bash tools/fixtures_self_test.sh` (all 166 on-disk fixtures, claim-map completeness guard, 14 `test_runtime_session.py` leaves, 4 `test_receipt_candidate_batching.py` behavioral checks, `test_start_path.py`, and `test_public_entry.py`), (3) `python3 tools/test_workflow_assurance.py` (full Workflow Assurance regression suite, including `ci-candidate-bound` and `ci-blocker-rejected` once) | Removed duplicate `ci-candidate-bound` and `ci-blocker-rejected` loop from `tools/fixtures_self_test.sh` |
| `convergent_review` | (1) `.github/scripts/test_sandbox_boundaries.py` (native + Docker adapter), (2) SBCL smoke verification, (3) `tools/test_convergent_review.py` required full-conformance isolation suite (native + Docker adapter), (4) conditional `WA123 capture` / `WA123 verify` | Removed duplicate `bash tools/fixtures_self_test.sh` step |
| `self_governance` | (1) `.github/scripts/verify_self_governance.py`, (2) `.github/scripts/test_self_governance.py`, (3) `bash .nizam/tools/validate.sh --payload` | None |

### 3.3 Post-R2 Measured Local Verification Timings (Slice 1 — Accepted at `30243037a4e8b085aa2ef8f493a3e93c56977f80`)

- `bash tools/validate.sh`: **PASS** (`16/16` checks)
- `bash tools/validate.sh --payload`: **PASS** (`12/12` checks)
- `python3 .github/scripts/release_closeout.py --mode pr`: **PASS** (`V=1.6.0`)
- `python3 .github/scripts/verify_self_governance.py` + `test_self_governance.py`: **PASS** (`276` released files + `10` drift negatives)
- `python3 .github/scripts/test_c13_cleanup.py`: **PASS** in `4.16s` (after disabling Git 2.55 background `maintenance.auto` and skipping `.agent/evidence/` in the private C13 scratch copy)
- `bash tools/fixtures_self_test.sh`: **PASS** (`166/166` fixtures accounted for, `14` runtime-session leaves, `4` receipt-candidate-batching checks) in **`1m28.46s`** (down from `42m33s` in `fixtures_self_test` and `35m03s` in `convergent_review` when `ci-candidate-bound` and `ci-blocker-rejected` were duplicated inside `fixtures_self_test.sh`).

### 3.4 Post-R3/R4 Measured Local Verification Timings (Slice 2 — Accepted at `3132337b1a46132a573a854a2db835b84081cc68`)

- `ControlsFixture` index and working tree bounded (`git rm -rf --quiet --ignore-unmatch .` on orphan `synthetic-ambient` before checking out the 40 required tool/schema/contract/authority files), reducing `controls_snapshot` from **34,205 files** to **219 files** and single `controls_variant` execution from `13.34s` to `4.28s` while preserving every positive and negative assertion:
  - `python3 tools/test_workflow_assurance.py --case ci-blocker-rejected`: **PASS** (`12/12` negative variants + positive restorations) in **`57.36s`**
  - `python3 tools/test_workflow_assurance.py --case ci-candidate-bound`: **PASS** (`106/106` negative variants + foreign-observer + deterministic observer + positive restorations) in **`11m22.64s`** (down from **`41m50s`** in baseline run `39064043210`)
  - Remaining 46 cases in `tools/test_workflow_assurance.py`: **PASS** (`46/46`) in **`~25s`**
  - `python3 tools/test_workflow_assurance.py --check controls-ready`: **PASS** in **`2.05s`** (with scratch clone detached at `evidence['candidate']['source_commit']`)
  - `python3 tools/test_workflow_assurance.py`: **PASS** (`48/48` cases)
  - `python3 tools/test_receipt_candidate_batching.py`: **PASS** (`4/4` behavioral checks: `real-git-count-reduction`, `semantic-equivalence`, `fresh-mutations`, `literal-paths-and-modes`; historical whole-module `MASKED_AST` check gated behind `--check-historical-ast-freeze`) in **`1.91s`**

### 3.5 Slice 3 Summary (`R5 + R6 + R7 + R8` — Accepted at `14ae992fed5217f016e8ee7edb542c67725d9e48`)

- **R5 (Task Routing, Blocking vs. Advisory Review Severity, Lightweight Amendments, and Unified Stopping Rules)**:
  - Extended `tools/start_path.py` with semantic 5-route classification (`classify` across `trivial`, `bugfix`, `small-change`, `standard-feature`, `high-risk`), `trivial` start path (`begin|done trivial`), lightweight contract amendments (`amend-contract` with `--apply` for mechanical scope extensions and `"re_approval_required": true` for semantic scope changes), and `check-verdict` (reusing `convergent_agf_verdict` for convergent ledgers/reports and enforcing evidence-based blocking vs. `advisory_minor` separation).
  - Updated `standard/acceptance_bars.md` (`v0.1.2`), `methodology/01_execution.md` (`v0.3.0`), `methodology/03_circuit_breaker.md` (`v0.4.1`), `tools/SKILL.md` (`v0.6.2`), and `AGENTS.md` (`v0.1.1`) so comparator rounds remain inside the 3-attempt breaker (`attempt <= 3`) unless an operator reset is recorded.
- **R6 (Automated Safe Evidence Capture, Capability Preflight, and Failure Routing)**:
  - Added `tools/start_path.py preflight` (inspecting Python/Git/pytest/SBCL/userns/Docker capabilities) and `tools/start_path.py capture` (exclusive `"xb"` file creation under `.agent/evidence/<task-id>/<run-id>/`, refusing silent overwrites, recording monotonic `duration_ms`, and distinguishing `completed` vs. `interrupted` runs).
- **R7 (Repository-Binding Migration Option A and Operational Receipt/Resume Flow)**:
  - Executed Option A from `.agent/evidence/120/repository-binding-decision-proposal.json`: created `.agent/evidence/120/authority-interpretation.json`, migrated `.agent/run_state.json` `repository` to `"https://github.com/niq-cnr/nizam-framework.git"` with append-only history event `wa120_repository_binding_migration_option_a`, and added `verify-receipt`, `plan-transition`, and `route-failure` CLI subcommands to `tools/workflow_assurance.py` plus `resume` to `tools/start_path.py`.
- **R8 (Concise Generated Status / Readiness Views)**:
  - Added `tools/start_path.py status --format json|markdown` reporting implemented, verified, independently accepted, merged, released, installed, and commissioned states without mutating repository files, and updated `tools/test_public_entry.py` to derive the expected `--tag v<framework_version>` dynamically from `NIZAM.json`.

### 3.6 Slice 4 Summary (`R9` — Phase 019 Generic Assurance Profiles `124` and `125` — Accepted at `b99041dc948522a52832c8871fc3ec8e3c073091`, Hardened in `A3` & `A7`)

- **Feature 124 (`preregister_profile_comparison` / `preregister-profile`)**:
  - Reuses the exact five canonical AGF roles and capability profile identifiers (`Orchestrator` → `orchestrator-primary`, `Planner` → `planner-creative`, `Generator` → `generator-deterministic`, `Validator` → `validator-structural`, `Evaluator` → `evaluator-adversarial`).
  - Preregisters `Routine` (`trivial`, `small-change`), `Standard` (`bugfix`, `standard-feature`), and `High-assurance` (`high-risk`) applicability, same-candidate full baseline controls (`status == "stable"`, `a11_verdict == "approve"`, `flaky_runs == 0`, `unresolved_blockers == 0`), candidate/test-bundle digests, zero missed-blocker tolerance, cost/latency limits, and accountable `Root` operator gate before any shadow run starts (`state == "preregistered-before-shadow"`, `shadow_runs_started is False`).
  - Enforces the `execution_scope` boundary: generic `repository-worktree` profiles forbid `persistent_runtime_claim: true`, while `persistent-runtime-sbcl` profile claims require `persistent_runtime_ready: true` (gated on Phase 020 features `130–132`).
- **Feature 125 (`evaluate_profile_comparison` / `evaluate-profile` and `verify_profiles_ready` / `verify-profiles-ready`)**:
  - Evaluates same-candidate baseline vs. shadow runs with candidate-bound capture artifacts (`stdout`, `stderr`, `duration_ms`, `cost_units`, `command_count`), records both `success` and `failed` outcomes, rejects promotion recommendations whenever any baseline blocker is missed or cost/latency bounds are exceeded, and enforces `promoted: false`, `active_gates_reduced: false`, and `permissions_changed: false` (no self-promotion).
  - **Audit & Follow-Up Classification (`A0` / `F3`)**: The initial `R9` `.agent/evidence/125/` records are classified as **parser/record-validation smoke evidence**; `A3` strengthened causal commit ordering, minimum comparison run counts, tier-specific run binding, captured `case_proofs`, and reviewer/producer provenance separation, and `A7` recorded the 12-task preregistered paired baseline-vs-shadow evaluation.

### 3.7 Slice 5 Summary (`R10 + R11` — Initial Smoke Rehearsal & Follow-Up Transition)

- **R10 (Initial 15-Task CLI Smoke & Consumer Rehearsal — Reclassified under `A0` / `F4`)**:
  - Recorded in [pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json) (`source_commit: b99041dc948522a52832c8871fc3ec8e3c073091`, `total_duration_ms: 18075`, `evidence_classification: "historical-smoke-and-parser-validation"`).
  - **Audit & Follow-Up Classification**: The initial `R10` record exercised CLI subcommands and `v1.6.0` bootstrap combined with author-checkout `start_path.py` calls, rather than a zero-reach-back consumer checkout and a real paired baseline-vs-proposed task study. It is retained strictly as **historical smoke/CLI validation evidence**; `A6` delivered the zero-reach-back consumer-only rehearsal and `A7` delivered the 12-task paired task evaluation.
- **R11 & A8 (Clean Exit from Temporary Override Mode upon `v1.8.0` Self-Adoption)**:
  - Temporary remediation precedence continued under `A0`–`A8` until `A8` released `v1.8.0` (`606d11ee84deff0d3b7934cbfd715223d64ac79d`), re-bootstrapped `.nizam/` to `v1.8.0` (PR #120 merged at `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`), and verified parity between root and `.nizam/`.

## 4. Initial Backlog & Dependency Order (`R0`–`R11`)

1. **Slice 1 (`R0` → `R1` → `R2` → independent acceptance at `30243037a4e8b085aa2ef8f493a3e93c56977f80`)**:
   - `R0`: Mandate adoption, PR #115 (`134`) reconciliation, and backlog order adjustment.
   - `R1`: Suite ownership mapping and timing baseline.
   - `R2`: Deduplicate CI (`tools/fixtures_self_test.sh` and `.github/workflows/compliance.yml`) and pin Python + shared `.github/requirements-ci.txt`.
2. **Slice 2 (`R3` + `R4` → independent acceptance at `3132337b1a46132a573a854a2db835b84081cc68`)**:
   - `R3`: Bound `ControlsFixture` and `controls_snapshot` in `tools/test_workflow_assurance.py`.
   - `R4`: Retire the default whole-module `MASKED_AST` freeze in `tools/test_receipt_candidate_batching.py` behind `--check-historical-ast-freeze`.
3. **Slice 3 (`R5` + `R6` + `R7` + `R8` → independent acceptance at `14ae992fed5217f016e8ee7edb542c67725d9e48`)**:
   - `R5`: Task routing, blocking vs. advisory review severity, lightweight amendments, and stopping rules.
   - `R6`: Automated safe evidence capture, capability preflight, and cause-based recovery routing.
   - `R7`: Bounded repository-binding migration (Option A) and operational receipt/resume CLI.
   - `R8`: Concise generated status/readiness views.
4. **Slice 4 (`R9` — Phase 019 Features `124` and `125` → independent acceptance at `b99041dc948522a52832c8871fc3ec8e3c073091`)**:
   - Reconciled dependency split in `.agent/feature_list_019.json` (`123` → `124` → `125`) separated from persistent-runtime SBCL (`130`–`132`).
5. **Slice 5 (`R10` + `R11` → merged in PR #116 at `8815d311ea512d3bbd7dafddfc124a6197b38c72`)**:
   - Initial smoke pilot and `v1.7.0` release (`47851d857e0ab879b848610128ee6e9e13368f0d`).

## 5. Post-Remediation Audit Follow-Up Packets (`A0`–`A8`)

1. **Follow-Up Slice 1 (`A0` + `A1` + `A2` → independent acceptance at `8c7d50a9a712f4fd9a29e160c422f9465e40b226`)**:
   - `A0`: Re-resolved baseline (`v1.7.0` / `47851d857e0ab879b848610128ee6e9e13368f0d` + PR #118 `f64333c203ee4cf3693b32c2bf28735b088ab3f8`), recorded continuing follow-up authority (`2026-10-18T10:10:00Z`), corrected run `39064043210` attribution and reclassified `R9`/`R10` records as smoke/parser validation, and restored visible transitional entry precedence in `AGENTS.md`.
   - `A1` (Closes `F1` & `F5` amendment part): Shared canonical path normalization and route-eligibility decision across `classify`, `begin`, `done`, and `amend-contract`; working-tree/commit diff scope verification and task-bound substantive QA/evidence validation in `done`; strict field validation, path normalization, vacuous-command rejection, semantic scope-expansion detection, and approval hash binding in `amend-contract`.
   - `A2` (Closes `F2`, `F5` preflight part, & native Python runtime layout): Explicit 3-stage evidence model (`capture` → `publish` → `build-receipt`/`verify-receipt`/`resume`) with unbound candidate representation (`binding_state: "unbound"`, `candidate_sha256: null`), multi-variable environment capture, post-execution `output_revision` publication, route-aware receipt stages (`trivial-complete`, `bugfix-complete`, `small-change-complete`), operational sandbox adapter probe in `preflight`, and `PATH` sanitization in `tools/isolated_trial_adapter.py` so Python 3.12+ never stats unmounted `/opt/hostedtoolcache` entries under Landlock.
2. **Follow-Up Slice 2 (`A3` + `A4` + `A5` → independent acceptance at `149d7d6647cbcccab853f02ce37fc00f1e4e8605`)**:
   - `A3` (Closes `F3`): Hardened `preregister_profile_comparison`, `evaluate_profile_comparison`, and `verify_profiles_ready` with causal commit ordering (`git merge-base --is-ancestor`), `min_comparison_runs` enforcement, distinct tier/profile-config run bindings, captured `case_proofs`, and distinct reviewer/producer provenance checks.
   - `A4` (Closes `F4`): Aligned `AGENTS.md`, `tools/SKILL.md`, `NIZAM.json`, `standard/AGF.md`, `methodology/00_planning.md`, `methodology/01_execution.md`, `methodology/03_circuit_breaker.md`, and `standard/acceptance_bars.md` on the `Routine` / `Standard` / `High-assurance` responsibility table, work-specific diagnostic stopping policy (repeated identical deterministic failure triggers diagnosis; attempt counter and line counts are telemetry rather than hard blockers), and single authoritative AGF verdict shape.
   - `A5` (Closes `F6`): Dynamic phase/feature discovery and contradiction reporting in `tools/start_path.py status`, reconciliation of `.agent/feature_list_022.json` and `docs/planning/phase_022.yaml`, and C16 (`vlib_feature_list_lifecycle`) historical-exemption tightening and truthful structural-check labeling.
3. **Follow-Up Slice 3 (`A6` + `A7` + `A8` → independent acceptance at `345b0c1a81bb6138ca2d2d917af4639cbd93d5c4` and `bbe5b415727eff608077b3404f2e6376b2b64808`, merged in PR #119 at `606d11ee84deff0d3b7934cbfd715223d64ac79d`, released as `v1.8.0`, self-adopted in PR #120 at `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`)**:
   - `A6`: Added `assert_consumer_zero_reachback` in `tools/e2e_bootstrap_test.sh` (and `.nizam/schema/` fallback in `_receipt_schema` in `tools/workflow_assurance.py`).
   - `A7`: Executed a 12-task preregistered paired baseline-vs-shadow comparison recorded in [pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json) and `.agent/evidence/125/`.
   - `A8`: Released `v1.8.0` (`faeb50dfdb055cc4d5018ab8d474979be71f876f`) and re-bootstrapped `.nizam/` to `v1.8.0` (PR #120 `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`).

## 6. `v1.8.0` Rollout Corrective Execution (`B0`–`B6` Closing `V1`–`V7`)

### 6.1 Audited Findings & Backlog Mapping

| Finding | Severity | Existing Capability Mapping | Corrective Action & Ownership |
|---|---|---|---|
| `V1` | P1 | `120` / `121` / `122` & `A2` (`tools/start_path.py`, `tools/interface.md`, `standard/permission_classes.md`, `tools/test_start_path.py`) | Separate publication into noncommitting `prepare` (`--mode prepare` / `prepare-publish`), externally mediated `publish` (`--mode publish`, honoring `NIZAM_MUTATION_ADAPTER` and normal Git hooks, literal pathspecs `:(literal)`, same-path staged conflict rejection, failed-observation rejection, batching, and stage-interruption recovery), noncommitting `finalize` (`--mode finalize` / `finalize-publish`, verifying committed blob SHA-256 and `100644` mode before writing references), and strictly noncommitting `build-receipt` (removing raw-capture fallback commits and `--commit` direct mutation). |
| `V2` | P1 | `007` / `029` / `050` / `051` / `066` / `067` & `NDEBT-033` (`bootstrap.sh`, `standard/GIP.md`, `ecosystem/00_ecosystem_bootstrap.md`, `tools/e2e_bootstrap_test.sh`) | Enforce strict release-tag syntax (`vMAJOR.MINOR.PATCH` on the public path; explicit `--allow-fixture-tag` for controlled `e2e-*` test tags), fetch and peel `refs/tags/<tag>` explicitly (`git fetch --depth 1 --no-tags <url> refs/tags/<tag>:refs/tags/<tag>`, rejecting branch-only refs, release-shaped branches, and same-name branch ambiguity), and validate `--expected-sha` before staging or replacing the target directory. |
| `V3` | P1 | `066` / `067` & `.github/scripts/verify_self_governance.py` (`tools/payload_integrity.py`, `bootstrap.sh`, `.github/scripts/verify_self_governance.py`, `.github/scripts/test_self_governance.py`) | Extract reusable trusted payload-integrity verification (`tools/payload_integrity.py`) shared by `verify_self_governance.py` and `bootstrap.sh --verify-only`: when a trusted reference (`--reference-repo` or `--reference-manifest` bound to `--expected-sha`) is supplied, verify the complete 277+ released file inventory, byte-for-byte contents, regular-file types (no symlinks), executable modes (`100644`/`100755`), and provenance fields; when only structural/provenance checks run (`--structural-only` or without a trusted reference), report `STRUCTURAL PASS (content_integrity=not_checked)` and fail closed if `--require-integrity` is requested without trusted reference material. |
| `V4` | P2 | `097` / `106` / `108` (`tools/validate.sh`) | Report `validate.sh --payload` results by actual scope: `10` exercised structural checks (`C1`–`C5`, `C7`–`C10`, `C13`), `2` not-applicable checks (`C11`, `C16` — emitted as `[C11] N/A` and `[C16] N/A`, not counted as exercised passes), `1` skipped check (`C6`), `3` out-of-scope checks (`C12`, `C14`, `C15`), and explicit `content_integrity=not_checked, operational_acceptance=not_assessed` disclosure. |
| `V5` | P1 / P2 | `005` / `049` & `A4` (`methodology/03_circuit_breaker.md`, `standard/acceptance_bars.md`, `tools/SKILL.md`, `tools/skill.json`, `NIZAM.json`, `methodology/README.md`, `tools/start_path.py`, `tools/validate.sh` C13) | Align active stopping-policy text across `03_circuit_breaker.md` frontmatter/body, `standard/acceptance_bars.md`, `tools/SKILL.md`, `tools/skill.json`, `NIZAM.json`, `methodology/README.md`, and `tools/start_path.py` (permitting bounded diagnostic continuation when authorized and within budget while halting on invariant/authority denial or repeated identical failure without new information); synchronize `tools/skill.json` `version` (`0.8.0`) with `tools/SKILL.md` frontmatter `version` (`0.8.0`) and enforce parity in `validate.sh` C13; replace hardcoded `v1.5.0` and blanket `phase016` claims in `tools/SKILL.md` with provenance/capability discovery. |
| `V6` | Clarified | `bootstrap.sh`, `tools/SKILL.md`, `standard/GIP.md`, `README.md` | Document clearly at the installation/discovery entry that the canonical installable source at tag `vX.Y.Z` is the declared six authored root modules plus root `NIZAM.json` (whereas the framework repository's own `.nizam/` at a release tag holds the prior self-adopted release until post-release self-adoption). |
| `V7` | Unreproduced | `bootstrap.sh`, `tools/e2e_bootstrap_test.sh` | Retain the worktree rollout report as unreproduced under tested forms and add a permanent 3-form regression in `tools/e2e_bootstrap_test.sh` comparing normal-clone invocation, linked-worktree invocation, and linked-worktree-as-source installation (verifying identical released file set, bytes, types, modes, and `framework_version`/`tag`/`resolved_sha`, with only `installed_at` and explicitly selected `source_url` differing in `provenance.json`). |

### 6.2 Execution DAG & Slice Plan (`B0`–`B6`)

1. **Corrective Slice 1 (`B0 + B1 + B2` → independent acceptance at `9cc9547ffc09694cea324bb009916811d786d2c5`)**:
   - `B0`: Baseline reconciliation (`v1.8.0` at `606d11ee84deff0d3b7934cbfd715223d64ac79d`, `main` at `016a1b79e0be6bc5b7459baae3c67ee99f2803f6`), single brief update (`v0.10.0`), transitional precedence in `AGENTS.md` (`v0.2.1`), and `.agent/run_state.json` record.
   - `B1` (Closes `V1`): Noncommitting `prepare`, externally mediated `publish`, noncommitting `finalize`, and strictly noncommitting default `build-receipt` in `tools/start_path.py`, consumer integration documentation in `tools/interface.md` and `standard/permission_classes.md`, and comprehensive unit/denial/conflict/recovery tests in `tools/test_start_path.py`.
   - `B2` (Closes `V2` & `V7` regression): Explicit `refs/tags/<tag>` fetch/peel, release-tag syntax enforcement, install-time `--expected-sha` verification before target replacement, and 3-form normal/worktree reproducibility regression in `bootstrap.sh`, `standard/GIP.md`, `ecosystem/00_ecosystem_bootstrap.md`, and `tools/e2e_bootstrap_test.sh`.
2. **Corrective Slice 2 (`B3 + B4` → independent acceptance at `f825908e80100a2e13b9157b6a4f72908dd26a24`)**:
   - `B3` (Closes `V3` & `V4`): Shared trusted payload-integrity verifier (`tools/payload_integrity.py`) wired into `bootstrap.sh --verify-only` and `.github/scripts/verify_self_governance.py`, truthful `validate.sh --payload` scope/summary reporting (`10 exercised passed, 0 failed, 2 not-applicable, 1 skipped, 3 out-of-scope`), and updated tests.
   - `B4` (Closes `V5` & `V6`): Coherent work-specific stopping policy across active docs/metadata/tools, `SKILL.md`/`skill.json` version parity enforced in C13, portable provenance/capability discovery in `tools/SKILL.md` and `tools/README.md`, and clear explanation of authored release payload vs. repository self-installed `.nizam/` in `README.md` and `docs/planning/SELF_GOVERNANCE.md`.
3. **Corrective Slice 3 (`B5 + B6` → independent acceptance at `40372780b328359fb4757651640920f11f14a23f`, merged in PR #121 at `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, released as `v1.9.0`, and re-bootstrapped under `.nizam/`)**:
   - `B5`: Clean disposable consumer end-to-end acceptance (`tools/e2e_bootstrap_test.sh` + independent reviewer acceptance at `40372780b328359fb4757651640920f11f14a23f`) covering all 10 discrimination areas in Section 10 (`V1`–`V7`).
   - `B6`: Released `v1.9.0` (`278` released files, annotated tag object `7e721b6e0fb2a0a3014efda388e1097378e3da87` at `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, `release.yml` run `39172587918` published at `2026-10-18T22:31:27Z`), re-bootstrapped `.nizam/` to `v1.9.0` (`installed_at: 2026-10-18T22:32:25Z`, evidence `.agent/evidence/release-v1.9.0-closeout/`), verified installed payload integrity against the trusted `v1.9.0` tag tree, and exited temporary override mode cleanly (`AGENTS.md` `v0.3.0`).

## 7. `v1.9.0` Audit Follow-Up Execution (`C0`–`C5` Closing `F1`–`F3`)

### 7.1 Audited Findings, One-Shot Baseline Reproduction (`C0`), and Packet Mapping

One-shot baseline reproduction probes were executed once against unmodified `3efa3e02df56781960dfa8d0ecf143360c617ff8` and recorded in [c0-baseline-probes.json](../../.agent/evidence/remediation-2026-10-18/c0-baseline-probes.json).

| Finding | Severity | Packet | Scope & Ownership | Acceptance Obligation |
|---|---|---|---|---|
| `F1` | P1 (`+` P2 index mtime) | `C1` | `tools/start_path.py`, `tools/interface.md`, `standard/permission_classes.md`, `tools/SKILL.md`, `AGENTS.md`, `tools/test_start_path.py` | Make `prepare` the default mode of `publish`; remove the implicit local `git add`/`git commit` fallback from `_git_commit_literal_paths`; reject missing/empty/`{}`/boolean-only/denied/pending/failed adapter outcomes without local fallback; distinguish explicit denial from interrupted acknowledgement (`unknown_external_commit_outcome`) and reconcile/recover completed stages against actual repository state without duplicate commits or re-running captured commands; bind completion to repository/worktree, `intended_base`, branch/detached state, and exact owned stage file delta; prevent read-side `.git/index` refreshes via `GIT_OPTIONAL_LOCKS=0` / `--no-optional-locks`. |
| `F2` | P1 | `C2` | `bootstrap.sh`, `tools/payload_integrity.py`, `README.md`, `tools/SKILL.md`, `tools/interface.md`, `standard/GIP.md`, `tools/README.md`, `.github/scripts/test_self_governance.py`, `tools/test_public_entry.py`, `tools/e2e_bootstrap_test.sh` | Never execute `${TARGET_DIR}/tools/payload_integrity.py`; expose `--git-repo DIR` through `bootstrap.sh` (loading verifier code and reference blobs from the verified immutable commit `<expected_sha>` in `--git-repo`, with optional install-time reference retention at `--git-repo DIR`); never derive expected SHA or reference repository from mutable `provenance.json` or ambient CWD; label unbound `--source-root` equality distinctly (`directory_match_unbound`) and forbid it from satisfying `--expected-sha` or `--require-content-integrity`; never downgrade helper exit `2` / parser / reference errors to `structural_only` pass. |
| `F3` | P1 / P2 | `C3` | `tools/start_path.py`, `methodology/00_planning.md`, `methodology/01_execution.md`, `schema/run_state.schema.json`, `tools/test_start_path.py` | Replace unconditional `"max_attempts": 3` in `classify` and hard `attempt <= 3` in `capture` with executable work-specific stopping rules: allow continuation beyond attempt 3 when invariant/authority bounds hold and a bounded amendment, verified decomposition, or extended `circuit_breaker[<step_key>].limit` applies (retaining parent/repair history), while halting on a repeated unresolved defect signature without progress/decomposition, exhausted budget/limit, or invariant/authority breach; align the three residual universal "3-strike" summaries in `00_planning.md`, `01_execution.md`, and `run_state.schema.json`. |

### 7.2 Execution DAG & Dependencies (`C0`–`C5`)

1. **`C0` (Baseline refresh, backlog/Issue `#107` reconciliation, one-shot reproduction probes, and brief update — Complete)**:
   - Recorded in this brief (`v0.13.0`), `AGENTS.md` (`v0.3.1`), `.agent/run_state.json`, and [c0-baseline-probes.json](../../.agent/evidence/remediation-2026-10-18/c0-baseline-probes.json).
2. **`C1` (`F1` — Publication default `prepare`, strict external mediation, base/delta binding, and index lock preservation)**, **`C2` (`F2` — Trusted consumer integrity verification & `--git-repo` binding)**, and **`C3` (`F3` — Executable stopping policy & residual doc/schema alignment) — Complete (`29ab5689652866cbb51c2f16b2911874ec591c19`)**:
   - Implemented across the authored source modules and verified by `tools/test_start_path.py`, `tools/test_public_entry.py`, `.github/scripts/test_self_governance.py`, `tools/validate.sh`, `tools/fixtures_self_test.sh`, and `tools/e2e_bootstrap_test.sh`.
3. **`C4` (Independent Acceptance against the Integrated Candidate — Complete)**:
   - Independently accepted (`APPROVE`, `0` blocking findings, `8/8` matrix rows `PASS`) by non-authoring Evaluator (`evaluator-adversarial`, subagent `a0777e6d-6905-46c4-be69-30965eea63eb`) against immutable candidate `29ab5689652866cbb51c2f16b2911874ec591c19`, recorded in [c4-independent-acceptance.json](../../.agent/evidence/remediation-2026-10-18/c4-independent-acceptance.json).
4. **`C5` (Release, Post-Release `.nizam/` Self-Adoption, and Override Exit — Complete)**:
   - Merged the accepted candidate via PR #123 at `6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7` (`compliance.yml` run `39216541409` green in `17m19s`), published annotated tag `v1.10.0` (`8971603d2091fd5f5602f556b49499a0c8aa7a29`, `release.yml` run `39218964275` succeeded at `2026-10-19T07:54:01Z`), re-bootstrapped `.nizam/` to `v1.10.0` (`278` released files + `provenance.json`, `installed_at: 2026-10-19T07:56:18Z`), verified self-governance and standalone strict consumer verification (`--verify-only --git-repo .nizam-ref/ --expected-sha 6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7 --require-content-integrity`, captured in `.agent/evidence/release-v1.10.0-closeout/`), and removed the transitional override banner in `AGENTS.md` (`v0.4.0`).


## 8. Cost-unit study qualification (2026-10-28)

This qualification narrows interpretation of the historical A7 study; it does
not change the recorded R/A/B/C completion status, captures or pilot report.
The pilot report's Routine 61.1% and Standard 45.1% reductions describe its
declared cost-unit proxies. They are not calibrated measurements of model
usage, token consumption, charges or completed delivery, and cannot support a
claim of measured ecosystem productivity savings.

For the Routine README pair, the historical capture records declare baseline
five roles, six commands and 45 cost units (87 ms), versus shadow two roles,
three commands and 18 cost units (80 ms). Both recorded argv values execute
`start_path.py classify --editorial --files README.md` (the shadow also supplies
`--root .`), and the captured stdout contains route-classification results.
These artifacts do not demonstrate a completed README edit or execution
transcripts for the declared roles. The durations measure the captured command,
not end-to-end delivery time. The declared roles and command counts therefore
remain proxy inputs rather than independently observed task execution.

Sources: the paired [baseline capture](https://github.com/niq-cnr/nizam-framework/blob/606d11ee84deff0d3b7934cbfd715223d64ac79d/.agent/evidence/125/captures/comp-01-routine-trivial-readme-base.json)
and [shadow capture](https://github.com/niq-cnr/nizam-framework/blob/606d11ee84deff0d3b7934cbfd715223d64ac79d/.agent/evidence/125/captures/comp-01-routine-trivial-readme-shad.json)
at the historical v1.8.0 baseline, their referenced stdout records, and
[pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json)
as inspected at `99ef862d6be14c539b36e10acd140e880f78b035`.
Parser, routing, negative-control and consumer-rehearsal evidence retains its
stated scope; this qualification does not revoke those results or infer the
same command limitation for every other paired case. A productivity or monetary
saving claim needs a separately calibrated study of completed comparable tasks,
observed role execution and actual usage/charge records.
