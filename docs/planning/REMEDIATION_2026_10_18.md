---
id: nizam-remediation-2026-10-18
title: "Critical Quality and Velocity Remediation Brief — 2026-10-18"
description: "Single coordination brief recording the 2026-10-18 operator remediation mandate, live-work reconciliation, CI suite ownership and timing baseline, and reconciled backlog order."
version: 0.1.0
status: active
authoritative_source: docs/planning/REMEDIATION_2026_10_18.md
change_log:
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
| `fixtures_self_test` | (1) `.github/scripts/test_c13_cleanup.py`, (2) `bash tools/fixtures_self_test.sh` (all 166 on-disk fixtures, claim-map completeness guard, 14 `test_runtime_session.py` leaves, and 4 `test_receipt_candidate_batching.py` behavioral checks), (3) `python3 tools/test_workflow_assurance.py` (full Workflow Assurance regression suite, including `ci-candidate-bound` and `ci-blocker-rejected` once) | Removed duplicate `ci-candidate-bound` and `ci-blocker-rejected` loop from `tools/fixtures_self_test.sh` |
| `convergent_review` | (1) `.github/scripts/test_sandbox_boundaries.py` (native + Docker adapter), (2) SBCL smoke verification, (3) `tools/test_convergent_review.py` required full-conformance isolation suite (native + Docker adapter), (4) conditional `WA123 capture` / `WA123 verify` | Removed duplicate `bash tools/fixtures_self_test.sh` step |
| `self_governance` | (1) `.github/scripts/verify_self_governance.py`, (2) `.github/scripts/test_self_governance.py`, (3) `bash .nizam/tools/validate.sh --payload` | None |

### 3.3 Post-R2 Measured Local Verification Timings (Slice 1)

- `bash tools/validate.sh`: **PASS** (`16/16` checks)
- `bash tools/validate.sh --payload`: **PASS** (`12/12` checks)
- `python3 .github/scripts/release_closeout.py --mode pr`: **PASS** (`V=1.6.0`)
- `python3 .github/scripts/verify_self_governance.py` + `test_self_governance.py`: **PASS** (`276` released files + `10` drift negatives)
- `python3 .github/scripts/test_c13_cleanup.py`: **PASS** in `4.16s` (after disabling Git 2.55 background `maintenance.auto` and skipping `.agent/evidence/` in the private C13 scratch copy)
- `bash tools/fixtures_self_test.sh`: **PASS** (`166/166` fixtures accounted for, `14` runtime-session leaves, `4` receipt-candidate-batching checks) in **`1m28.46s`** (down from `42m33s` in `fixtures_self_test` and `35m03s` in `convergent_review` when `ci-candidate-bound` and `ci-blocker-rejected` were duplicated inside `fixtures_self_test.sh`).

## 4. Reconciled Backlog & Dependency Order (R0–R11)

1. **Slice 1 (`R0` → `R1` → `R2` → independent acceptance)**:
   - `R0`: Mandate adoption, PR #115 (`134`) reconciliation, and backlog order adjustment.
   - `R1`: Suite ownership mapping and timing baseline.
   - `R2`: Deduplicate CI (`tools/fixtures_self_test.sh` and `.github/workflows/compliance.yml`) and pin Python (`3.12`) + shared `.github/requirements-ci.txt`.
2. **Slice 2 (`R3` + `R4`)**:
   - `R3`: Bound `ControlsFixture` and `controls_snapshot` in `tools/test_workflow_assurance.py` so synthetic parser tests use a small, deterministic repository tree instead of cloning/walking the entire growing `.agent/evidence/` history and traversing `f.root` twice.
   - `R4`: Retire the default whole-module `MASKED_AST` freeze in `tools/test_receipt_candidate_batching.py` (confining historical AST-freeze checks to an opt-in flag while keeping all four behavioral receipt-batching checks in default execution).
3. **Slice 3 (`R5` + `R6` + `R7` + `R8`)**:
   - `R5`: Task routing (`tools/start_path.py`, schemas, entry docs, `AGENTS.md`, `tools/SKILL.md`, `methodology/01_execution.md`), evidence-based blocking vs. advisory review severity (reusing `convergent_agf_verdict`), lightweight amendments, and unified stopping rules (`standard/acceptance_bars.md` and `methodology/03_circuit_breaker.md`).
   - `R6`: Automated safe evidence capture (exclusive per-execution paths, monotonic elapsed time, no silent overwrite, interrupted vs. completed distinction), capability preflight, and cause-based recovery routing.
   - `R7`: Bounded repository-binding migration (Option A from `.agent/evidence/120/repository-binding-decision-proposal.json`) and operational receipt/resume integration into the start/resume flow.
   - `R8`: Concise generated status/readiness views and thin task entry/status CLI without recursive closeout invalidation.
4. **Slice 4 (`R9` — Phase 019 Features `124` and `125`)**:
   - Reconciled dependency split in `.agent/feature_list_019.json`: generic repository/worktree assurance profile comparison (`124`) and shadow recommendation (`125`) depend on `123` (`123` → `124` → `125`) and execute now; persistent-runtime / SBCL profile qualification remains gated on Phase 020 features `130–132`.
5. **Slice 5 (`R10` + `R11`)**:
   - `R10`: Independent acceptance of integrated slices and representative pilot (10–20 tasks/replays + clean consumer checkout validation).
   - `R11`: Documentation, backlog reconciliation, and clean exit from temporary remediation mode.
