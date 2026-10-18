---
id: nizam-remediation-2026-10-18
title: "Critical Quality and Velocity Remediation Brief — 2026-10-18"
description: "Single coordination brief recording the 2026-10-18 operator remediation mandate, live-work reconciliation, CI suite ownership and timing baseline, and reconciled backlog order."
version: 0.5.1
status: active
authoritative_source: docs/planning/REMEDIATION_2026_10_18.md
change_log:
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

## 1. Mandate Adoption & Authority (R0)

- **Adopted at**: `2026-10-18T04:45:00Z`
- **Repository**: `niq-cnr/nizam-framework` (`https://github.com/niq-cnr/nizam-framework.git`)
- **Authoritative instruction**: Operator remediation mandate dated 18 October 2026 ("Nizam framework critical quality and velocity remediation prompt"), recorded in `.agent/run_state.json` and this single brief.
- **Process precedence**: Prospectively suspends obstructive repository-local self-governance ceremony (repeated per-edit contracts, dual pre-code approval rounds, automatic halt solely from old 3-attempt counter exhaustion, historical line-count ceilings, whole-module AST freezes outside target functions, and recursive closeout invalidation) while strictly preserving:
  1. Independent acceptance of each integrated, publishable remediation slice by a non-authoring reviewer.
  2. Real, accurately captured verification results tied to the committed candidate and execution inputs.
  3. Security and correctness invariants (identity, authorization, isolation, source integrity, claimed vs. authenticated authority).
  4. Ownership of writes, preservation of unrelated work, and recoverability.
  5. Honest lifecycle status across implemented, tested, independently accepted, merged, released, installed, and commissioned states.

## 2. Live-Work Reconciliation (R0)

- **`main` baseline**: `e3748676f4f12a5a1a10bf1a100869db773b70ee` (PR #114 merge).
- **Installed payload**: `.nizam/` pinned at released tag `v1.6.0` (`4e7db5a47d753555abd4d724c5d16f2b5eb86c3e`, 276 released files + `provenance.json`, `commissioning_performed: false` per `docs/planning/SELF_GOVERNANCE.md`).
- **Active open work reconciled**: PR #115 (`feat/portable-review-sandbox-2026-10-16` at `fe78e4fe538c28420f7ce9ff2bfb460b44e93a4a`, superseding closed PR #108) delivers Feature 134 (`tools/docker_trial_sandbox.sh` and adapter-specific conformance selection in `tools/test_convergent_review.py` and `.github/scripts/test_sandbox_boundaries.py`). This remediation branch (`feat/quality-velocity-remediation-2026-10-18`) builds directly on `fe78e4fe538c28420f7ce9ff2bfb460b44e93a4a` so all Feature 134 work is preserved intact.

## 3. Suite Ownership & Timing Baseline (R1)

### 3.1 Pre-Remediation Timing Baseline

| Source | Job / Suite | Observed Duration | Root Cause / Notes |
|---|---|---|---|
| Hosted Actions run `39064043210` (`main` `e3748676`) | `validate` | `19s` | `tools/validate.sh` (C1–C16) |
| Hosted Actions run `39064043210` (`main` `e3748676`) | `e2e_bootstrap` | `54s` | `tools/e2e_bootstrap_test.sh` |
| Hosted Actions run `39064043210` (`main` `e3748676`) | `self_governance` | `28s` | `verify_self_governance.py`, `test_self_governance.py`, `.nizam/tools/validate.sh --payload` |
| Hosted Actions run `39064043210` (`main` `e3748676`) | `fixtures_self_test` | `84m47s` | `fixtures_self_test.sh` (`42m33s`, dominated by `ci-candidate-bound` + `ci-blocker-rejected`) + full `test_workflow_assurance.py` (`41m50s`, running `ci-candidate-bound` + `ci-blocker-rejected` a second time) |
| Hosted Actions run `39064043210` (`main` `e3748676`) | `convergent_review` | `35m40s` | Isolation suite (`8s`) + duplicate `fixtures_self_test.sh` (`35m03s`, running `ci-candidate-bound` + `ci-blocker-rejected` a third time) |
| Hosted Actions run `39095406918` (PR #115 `fe78e4fe`) | `convergent_review` | `51m07s` | Native + Docker isolation suites + duplicate `fixtures_self_test.sh` |

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

### 3.6 Slice 4 Summary (`R9` — Phase 019 Generic Assurance Profiles `124` and `125` — Accepted at `b99041dc948522a52832c8871fc3ec8e3c073091`)

- **Feature 124 (`preregister_profile_comparison` / `preregister-profile`)**:
  - Reuses the exact five canonical AGF roles and capability profile identifiers (`Orchestrator` → `orchestrator-primary`, `Planner` → `planner-creative`, `Generator` → `generator-deterministic`, `Validator` → `validator-structural`, `Evaluator` → `evaluator-adversarial`).
  - Preregisters `Routine` (`trivial`, `small-change`), `Standard` (`bugfix`, `standard-feature`), and `High-assurance` (`high-risk`) applicability, same-candidate full baseline controls (`status == "stable"`, `a11_verdict == "approve"`, `flaky_runs == 0`, `unresolved_blockers == 0`), candidate/test-bundle digests, zero missed-blocker tolerance, cost/latency limits, and accountable `Root` operator gate before any shadow run starts (`state == "preregistered-before-shadow"`, `shadow_runs_started is False`).
  - Enforces the `execution_scope` boundary: generic `repository-worktree` profiles forbid `persistent_runtime_claim: true`, while `persistent-runtime-sbcl` profile claims require `persistent_runtime_ready: true` (gated on Phase 020 features `130–132`).
- **Feature 125 (`evaluate_profile_comparison` / `evaluate-profile` and `verify_profiles_ready` / `verify-profiles-ready`)**:
  - Evaluates same-candidate baseline vs. shadow runs with candidate-bound capture artifacts (`stdout`, `stderr`, `duration_ms`, `cost_units`, `command_count`), records both `success` and `failed` outcomes, rejects promotion recommendations whenever any baseline blocker is missed or cost/latency bounds are exceeded, and enforces `promoted: false`, `active_gates_reduced: false`, and `permissions_changed: false` (no self-promotion).
  - Verified by the 7 permanent `PROFILE_CASES` (`preregister-before-run`, `roles-reused`, `reject-unstable-baseline`, `same-candidate`, `missed-baseline-blocker`, `cost-latency-accounting`, `no-self-promotion`) and `--check profiles-ready` against `.agent/evidence/125/profiles-policy.json`.

### 3.7 Slice 5 Summary (`R10 + R11` — Representative 15-Task Pilot, Consumer Rehearsal, and Clean Exit)

- **R10 (Representative 15-Task Pilot & Disposable Consumer Rehearsal)**:
  - Recorded in [pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json) (`source_commit: b99041dc948522a52832c8871fc3ec8e3c073091`, `total_duration_ms: 18075`):
  - **15 tasks across all 5 routes** (`3 trivial`, `3 bugfix`, `3 small-change`, `3 standard-feature`, `3 high-risk`):
    - `trivial` (`Routine`): `3` tasks, avg `6.0` commands, avg `484.3ms`, `1` review round/task.
    - `bugfix` (`Standard`): `3` tasks, avg `5.7` commands, avg `453.3ms`, `1` review round/task (`pilot-06-bugfix-seeded-blocker` seeded blocker caught).
    - `small-change` (`Routine`): `3` tasks, avg `6.0` commands, avg `483.7ms`, `1` review round/task (`pilot-07-small-status-flag` advisory-only verdict non-blocking).
    - `standard-feature` (`Standard`): `3` tasks, avg `4.3` commands, avg `360.3ms`, `1` review round/task (`pilot-10-feature-124-prereg` mechanical contract amendment via `amend-contract --apply` without full pre-code re-entry; `pilot-12-feature-seeded-blocker` seeded blocker caught).
    - `high-risk` (`High-assurance`): `3` tasks, avg `4.0` commands, avg `333.0ms`, `1` review round/task (`pilot-15-highrisk-seeded-blocker` seeded blocker caught).
  - **Defect & Evidence Integrity**: `seeded_blockers: 3`, `blockers_caught: 3`, `missed_baseline_blockers: 0`, `silent_evidence_overwrites: 0` (exclusive capture overwrite prevention verified on every task).
  - **Disposable Consumer Checkout Rehearsal**:
    - `bootstrap.sh --repo-url <repo> --tag v1.6.0 --target <consumer>/.nizam`: **PASS** (`1685ms`)
    - `bash .nizam/tools/validate.sh --payload`: **PASS** (`12 passed, 0 failed`, `9645ms`)
    - `python3 tools/start_path.py classify` and `python3 tools/start_path.py status` on consumer checkout: **PASS**.
- **R11 (Backlog Reconciliation & Clean Exit from Temporary Remediation Mode)**:
  - All R0–R11 remediation items are implemented, verified, independently accepted across slices, and reconciled in `AGENTS.md`, `tools/SKILL.md`, `tools/README.md`, `standard/acceptance_bars.md`, `methodology/01_execution.md`, `methodology/03_circuit_breaker.md`, `docs/planning/ROADMAP.md`, `docs/planning/manifest.json`, `docs/planning/phase_019.yaml`, `.agent/feature_list_019.json`, and `.agent/run_state.json`.
  - Temporary remediation override mode exits cleanly with this integrated delivery: ordinary development uses the reconciled five-route workflow (`tools/start_path.py classify`, `begin|done`, `amend-contract`, `preflight`, `capture`, `check-verdict`, `resume`, `status`) and the Phase 019 (`124–125`) generic repository/worktree assurance profile tools (`preregister-profile`, `evaluate-profile`, `verify-profiles-ready`), while Phase 020 (`130–132`) resumes as the active persistent-runtime SBCL track.

## 4. Reconciled Backlog & Dependency Order (R0–R11)

1. **Slice 1 (`R0` → `R1` → `R2` → independent acceptance at `30243037a4e8b085aa2ef8f493a3e93c56977f80`)**:
   - `R0`: Mandate adoption, PR #115 (`134`) reconciliation, and backlog order adjustment.
   - `R1`: Suite ownership mapping and timing baseline.
   - `R2`: Deduplicate CI (`tools/fixtures_self_test.sh` and `.github/workflows/compliance.yml`) and pin Python (`3.14`) + shared `.github/requirements-ci.txt`.
2. **Slice 2 (`R3` + `R4` → independent acceptance at `3132337b1a46132a573a854a2db835b84081cc68`)**:
   - `R3`: Bound `ControlsFixture` and `controls_snapshot` in `tools/test_workflow_assurance.py` so synthetic parser tests use a small, deterministic repository tree instead of cloning/walking the entire growing `.agent/evidence/` history and traversing `f.root` twice.
   - `R4`: Retire the default whole-module `MASKED_AST` freeze in `tools/test_receipt_candidate_batching.py` (confining historical AST-freeze checks to an opt-in flag while keeping all four behavioral receipt-batching checks in default execution).
3. **Slice 3 (`R5` + `R6` + `R7` + `R8` → independent acceptance at `14ae992fed5217f016e8ee7edb542c67725d9e48`)**:
   - `R5`: Task routing (`tools/start_path.py`, schemas, entry docs, `AGENTS.md`, `tools/SKILL.md`, `methodology/01_execution.md`), evidence-based blocking vs. advisory review severity (reusing `convergent_agf_verdict`), lightweight amendments, and unified stopping rules (`standard/acceptance_bars.md` and `methodology/03_circuit_breaker.md`).
   - `R6`: Automated safe evidence capture (exclusive per-execution paths, monotonic elapsed time, no silent overwrite, interrupted vs. completed distinction), capability preflight, and cause-based recovery routing.
   - `R7`: Bounded repository-binding migration (Option A from `.agent/evidence/120/repository-binding-decision-proposal.json`) and operational receipt/resume integration into the start/resume flow.
   - `R8`: Concise generated status/readiness views and thin task entry/status CLI without recursive closeout invalidation.
4. **Slice 4 (`R9` — Phase 019 Features `124` and `125` → independent acceptance at `b99041dc948522a52832c8871fc3ec8e3c073091`)**:
   - Reconciled dependency split in `.agent/feature_list_019.json`: generic repository/worktree assurance profile comparison (`124`) and shadow recommendation (`125`) depend on `123` (`123` → `124` → `125`) and are complete; persistent-runtime / SBCL profile qualification remains gated on Phase 020 features `130–132`.
5. **Slice 5 (`R10` + `R11` → final independent acceptance & PR delivery)**:
   - `R10`: Independent acceptance of integrated slices and representative 15-task pilot + clean consumer checkout validation ([pilot-report.json](../../.agent/evidence/remediation-2026-10-18/pilot-report.json)).
   - `R11`: Documentation, backlog reconciliation, and clean exit from temporary remediation mode.
