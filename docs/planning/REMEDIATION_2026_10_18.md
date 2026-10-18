---
id: nizam-remediation-2026-10-18
title: "Critical Quality and Velocity Remediation Brief — 2026-10-18"
description: "Single coordination brief recording the 2026-10-18 operator remediation mandate, live-work reconciliation, CI suite ownership and timing baseline, and reconciled backlog order."
version: 0.8.0
status: active
authoritative_source: docs/planning/REMEDIATION_2026_10_18.md
change_log:
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

## 1. Mandate Adoption & Continuing Follow-Up Authority (R0 & A0)

- **Initial mandate adopted at**: `2026-10-18T04:45:00Z`
- **Follow-up audit & execution mandate (`A0`–`A8`) adopted at**: `2026-10-18T10:10:00Z`
- **Repository**: `niq-cnr/nizam-framework` (`https://github.com/niq-cnr/nizam-framework.git`)
- **Authoritative instructions**: Operator remediation mandate dated 18 October 2026 ("Nizam framework critical quality and velocity remediation prompt") and operator post-remediation audit & follow-up execution mandate dated 18 October 2026 ("Nizam framework: post-remediation audit and follow-up execution prompt", audited source `8815d311ea512d3bbd7dafddfc124a6197b38c72`), recorded in `.agent/run_state.json` and this single brief.
- **Continuing process precedence**: The operator reaffirmed and continued authorization to pragmatically ignore, suspend, simplify, or replace obstructive repository-local Nizam governance (`AGENTS.md`, installed `.nizam/` instructions, authored skills and protocols, phase plans, templates, contracts, line-count gates, 3-strike attempt counters, and historical scope guards) while completing follow-up packets `A0`–`A8`. The previous `v0.5.0` claim that temporary remediation mode had ended is superseded until `A8` re-bootstraps `.nizam/` to the post-follow-up immutable release (`v1.8.0`). During `A0`–`A8`, `AGENTS.md`, this brief, and root `tools/start_path.py` take precedence over conflicting `.nizam/` requirements while strictly preserving:
  1. Independent acceptance of each integrated, publishable remediation slice by a non-authoring reviewer.
  2. Real, accurately captured verification results tied to the committed candidate and execution inputs.
  3. Security and correctness invariants (identity, authorization, isolation, source integrity, claimed vs. authenticated authority).
  4. Ownership of writes, preservation of unrelated work, and recoverability.
  5. Honest lifecycle status across implemented, tested, independently accepted, merged, released, installed, and commissioned states.

## 2. Live-Work Reconciliation (R0 & A0)

- **Initial `main` baseline (`R0`)**: `e3748676f4f12a5a1a10bf1a100869db773b70ee` (PR #114 merge); PR #115 merged Feature 134 (`144e20e09bd17257c34873e1608a24bb6f05248d`), and PR #116 merged `R0`–`R11` at audited source `8815d311ea512d3bbd7dafddfc124a6197b38c72`.
- **Follow-up `main` & release baseline (`A0`)**: PR #117 (`47851d857e0ab879b848610128ee6e9e13368f0d`) released tag `v1.7.0` (annotated tag object `6a4cf599f3850ae31561ba38f9da29237d0a4a53`; `release.yml` run `39116785402` succeeded), and PR #118 (`f64333c203ee4cf3693b32c2bf28735b088ab3f8`) merged the `v1.7.0` closeout and `.nizam/` re-bootstrap (`277` released files + `provenance.json`, `commissioning_performed: false` per `docs/planning/SELF_GOVERNANCE.md`).
- **Active follow-up scope (`A0`–`A8`)**: Closes audit findings `F1`–`F6` across Slice 1 (`A0 + A1 + A2`), Slice 2 (`A3 + A4 + A5`), and Slice 3 (`A6 + A7 + A8`) before releasing and adopting `v1.8.0`.

## 3. Suite Ownership & Timing Baseline (R1 & A0 Audited Hosted Runs)

### 3.1 Pre-Remediation and Post-PR #116 Hosted Timing Baseline

| Source | Job / Suite | Observed Duration | Root Cause / Notes |
|---|---|---|---|
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, `2026-10-18T00:08:23Z`–`01:47:50Z`, total `99m27s`) | `validate` / `e2e_bootstrap` / `self_governance` | `19s` / `54s` / `28s` | Fast jobs on PR #114 head `7c049c8805a5d48a9729f2d80e0a7e4a5086a2cb` (previously mislabeled in v0.1.0–v0.5.1 as `main` `e3748676`) |
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, total `99m27s`) | `fixtures_self_test` | `84m47s` | `fixtures_self_test.sh` (`42m33s`, dominated by `ci-candidate-bound` + `ci-blocker-rejected`) + full `test_workflow_assurance.py` (`41m50s`, running `ci-candidate-bound` + `ci-blocker-rejected` a second time) |
| Hosted Actions run `39064043210` (PR #114 head `7c049c88`, total `99m27s`) | `convergent_review` | `35m40s` | Isolation suite (`8s`) + duplicate `fixtures_self_test.sh` (`35m03s`, running `ci-candidate-bound` + `ci-blocker-rejected` a third time) |
| Hosted Actions run `39075498443` (PR #115 `fe78e4fe`, `2026-10-18T02:23:03Z`–`04:02:30Z`, total `99m27s`) | Full `compliance.yml` | `99m27s` | Immediately preceding successful PR #115 run (`fixtures_self_test` + `convergent_review` with native + Docker isolation suites and duplicate `fixtures_self_test.sh`) |
| Hosted Actions run `39111912990` (PR #116 final candidate `ec70cefb`, total `18m12s`) | Full `compliance.yml` | `18m12s` | **~81.7% reduction** vs. PR #115 (`39075498443`): full Workflow Assurance step `15m06s`, general fixture step `2m37s`, `convergent_review` job `1m11s` |
| Hosted Actions run `39115161856` (merged `main` `8815d311`, `2026-10-18T09:23:47Z`–`09:42:10Z`, total `18m23s`) | Full `compliance.yml` | `18m23s` | **~81.5% reduction** vs. PR #115 (`39075498443`) on the merged candidate (cross-revision hosted observation, not a controlled benchmark or agent active-time measurement) |

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
  - **Audit & Follow-Up Classification (`A0` / `F3`)**: The initial `R9` `.agent/evidence/125/` records are classified as **parser/record-validation smoke evidence** until `A3` strengthens causal commit ordering, minimum comparison run counts, tier-specific run binding, captured `case_proofs`, and reviewer/producer provenance separation, and `A7` records the real paired task evaluation.

### 3.7 Slice 5 Summary (`R10 + R11` — Initial Smoke Rehearsal & Follow-Up Transition)

- **R10 (Initial 15-Task CLI Smoke & Consumer Rehearsal — Reclassified under `A0` / `F4`)**:
  - Recorded in [pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json) (`source_commit: b99041dc948522a52832c8871fc3ec8e3c073091`, `total_duration_ms: 18075`, `evidence_classification: "historical-smoke-and-parser-validation"`).
  - **Audit & Follow-Up Classification**: The initial `R10` record exercised CLI subcommands and `v1.6.0` bootstrap combined with author-checkout `start_path.py` calls, rather than a zero-reach-back consumer checkout and a real paired baseline-vs-proposed task study. It is retained strictly as **historical smoke/CLI validation evidence**; `A6` delivers the zero-reach-back consumer-only rehearsal and `A7` delivers the real paired task evaluation.
- **R11 (Transitional Override Continuation under `A0`–`A8`)**:
  - Rather than exiting temporary remediation override mode prematurely while `.nizam/` lacked the new tools and findings `F1`–`F6` remained open, temporary remediation precedence continues under `A0`–`A8` until `A8` releases `v1.8.0`, re-bootstraps `.nizam/` to `v1.8.0`, and verifies parity between root and `.nizam/`.

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
3. **Follow-Up Slice 3 (`A6` + `A7` → independent acceptance at `345b0c1a81bb6138ca2d2d917af4639cbd93d5c4`; `A8` `v1.8.0` release prepared)**:
   - `A6`: Added `assert_consumer_zero_reachback` in `tools/e2e_bootstrap_test.sh` (and `.nizam/schema/` fallback in `_receipt_schema` in `tools/workflow_assurance.py`) to exercise `classify`, `preflight`, `begin|done trivial`, `amend-contract`, `capture` → `publish` → `build-receipt` → `verify-receipt` → `resume`, `status`, and `validate.sh --payload` in a clean disposable `--genesis` consumer repository using only `.nizam/tools/` with zero reach-back to the author checkout.
   - `A7`: Executed a 12-task preregistered paired baseline-vs-shadow comparison across `Routine` (`trivial`, `small-change`, plus tiny policy-bearing edit and test-oracle weakening under-classification blockers), `Standard` (`bugfix`, `standard-feature`, plus detected seeded blocker and rejected missed-blocker negative control), and `High-assurance` (`high-risk` positive runs and causal/self-review blocker detection), recorded in [pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json) and `.agent/evidence/125/` (`min_comparison_runs: 12`, `0` missed blockers on recommended tiers, `promoted: false`, `active_gates_reduced: false`).
   - `A8`: Prepared `v1.8.0` MINOR release anchors on `feat/remediation-followup-2026-10-18`; upon PR merge, tag and release immutable `v1.8.0`, re-bootstrap `.nizam/` to `v1.8.0`, remove transitional override banner from `AGENTS.md`, and complete final closeout.

