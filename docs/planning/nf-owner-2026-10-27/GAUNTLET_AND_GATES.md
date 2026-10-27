---
id: nizam-nf-owner-2026-10-27-gauntlet-gates
title: "NF-OWNER-2026-10-27 — Three-Iteration Hostile Gauntlet, G1–G6 Gate Evaluation & Exit Reports"
description: "Three-iteration hostile review gauntlet across four critic personas, G1–G6 gate evaluation, and individual exit reports for N04, N08, J01, and external gates."
version: 1.0.0
status: active
authoritative_source: docs/planning/nf-owner-2026-10-27/GAUNTLET_AND_GATES.md
change_log:
  - version: "1.0.0"
    date: "2026-10-27"
    summary: "Record the 3-iteration hostile review gauntlet, G1-G6 gate evaluations, and separate exit reports for N04, N08, J01, and external gates."
---

# NF-OWNER-2026-10-27 — Hostile Review Gauntlet & Gate Evaluation

## 1. Three-Iteration Hostile Review Gauntlet

Four adversarial personas evaluated the architecture, implementation, and tests across three iterations:
- **Persona P1 — Hostile Git & Filesystem Attacker:** Hunts ambient Git state leakage, `git replace`, graft/worktree redirection, symlink traversal, and TOCTOU publication flaws.
- **Persona P2 — Standalone Consumer Integrator:** Hunts hidden Agentic SDLC dependencies, broken `.nizam/` relative paths, CWD sensitivity, and Darwin/Linux portability defects.
- **Persona P3 — Assurance & Circuit-Breaker Auditor:** Hunts silent counter resets, forged continuation authority, vacuous binary approvals, and unauthenticated external evidence admission.
- **Persona P4 — Release & Governance Maintainer:** Hunts `.nizam/` vs. root version conflation, undocumented schema changes, C1–C16 compliance regressions, and dropped backlog obligations.

### Iteration 1 — Initial Seam & Schema Defect Hunt

| Finding ID | Persona | Severity | Defect Identified | Resolution Applied | Verification |
| --- | --- | --- | --- | --- | --- |
| `HG-101` | P1 | Blocker | `tools/start_path.py` and `tools/workflow_assurance.py` copied into synthetic temp directories during tests failed when `tools/git_seam.py` was not copied alongside them. | Added a lazy `_GIT_SEAM` loader with a hardened self-contained fallback in `workflow_assurance.py`, `start_path.py`, `convergent_review.py`, and `payload_integrity.py`. | `tools/test_start_path.py` & `tools/test_workflow_assurance.py` |
| `HG-102` | P2 | Important | `tools/convergent_review.py` `_rename_noreplace` only attempted Linux `renameat2(RENAME_NOREPLACE=1)` and failed on macOS Darwin during atomic publication. | Added Darwin libc `renamex_np(src, dst, RENAME_EXCL=4)` support alongside Linux `renameat2` in `_rename_noreplace`. | `tools/test_convergent_review.py` (54 tests) |
| `HG-103` | P3 | Important | `schema/review_packet.schema.json` `"1.1.0"` branch needed to forbid `semantic_inspection_performed: true` on `integrity_only` opaque binary records at both schema and relational layers. | Enforced `const: false` in `schema/review_packet.schema.json` for `integrity_only` and relational check in `convergent_review.py` (`validate_packet_relations`). | `tools/test_nf_ac03_binary_review.py` |

### Iteration 2 — Cross-Suite & Standalone Consumer Stress Hunt

| Finding ID | Persona | Severity | Defect Identified | Resolution Applied | Verification |
| --- | --- | --- | --- | --- | --- |
| `HG-201` | P1 / P2 | Important | `tools/test_start_path.py` injects a temporary `fake_git` wrapper on `PATH` to test `git diff --cached` failure handling; stripping `PATH` in `run_git_completed` bypassed the test's simulated failure. | Preserved `PATH` (`preserve_path=True`) in `git_seam.run_git_completed` while stripping all `GIT_*` redirection variables and enforcing `--no-replace-objects`. | `tools/test_start_path.py` & `tools/test_nf_ac01_git_identity.py` |
| `HG-202` | P1 / P4 | Important | `tools/test_workflow_assurance.py` uses `git clone --shared` for fast scratch repositories, creating regular `.git/objects/info/alternates` files; rejecting all regular `alternates` files broke `test_workflow_assurance.py`. | Updated `git_seam.validate_repo_root` to reject symlinked/non-regular `.git/objects/info/alternates` while stripping `GIT_ALTERNATE_OBJECT_DIRECTORIES` from the environment and blocking `.git/info/grafts`. | `tools/test_workflow_assurance.py` & `tools/test_nf_ac01_git_identity.py` |
| `HG-203` | P4 | Important | New schema `schema/external_evidence_admission.schema.json` and tools `tools/git_seam.py`, `tools/external_evidence.py` must be indexed in `NIZAM.json`, `schema/README.md`, and `tools/README.md` with version/changelog bumps for C4, C8, and C9. | Indexed all new files in `NIZAM.json`, bumped `schema/README.md` (`0.23.0`) and `tools/README.md` (`0.40.0`) with `change_log` entries. | `bash tools/validate.sh` & `bash tools/validate.sh --payload` |

### Iteration 3 — Final Adversarial Convergence Check

- **P1 (Git/FS Attacker):** 0 open blocker or important findings. `NF-AC01` and `test_receipt_candidate_batching.py` pass with zero ambient Git leakage.
- **P2 (Standalone Integrator):** 0 open blocker or important findings. `NF-AC05` proves `v2.0.0` install, `e2e-3.0.0-rc1` upgrade, task routing, `"1.0.0"`/`"1.1.0"` review, and optional external evidence admission in a clean offline consumer.
- **P3 (Assurance Auditor):** 0 open blocker or important findings. `NF-AC02`, `NF-AC03`, and `NF-AC04` pass all positive and adversarial negative controls.
- **P4 (Release/Governance Maintainer):** 0 open blocker or important findings. `.nizam/` (`v2.0.0`) and `.agent/run_state.json` remain untouched; `N04`, `N08`, `J01`, and external gates are reported separately below.

---

## 2. Gate Evaluation (`G1`–`G6`)

| Gate | Scope & Criteria | Verdict | Evidence |
| --- | --- | --- | --- |
| `G1` — Baseline & Authority Separation | `origin/main` (`2b8298ae1d5a41534e00b6710a738b4b181b87fa`) reconstructed; isolated worktree created; `.nizam/` (`v2.0.0`) and `.agent/run_state.json` preserved untouched; `A`/`O`/`T` separated. | **PASS** | `docs/planning/nf-owner-2026-10-27/INTAKE_AND_BACKLOG_CROSSWALK.md`, `git status`, `.nizam/provenance.json` |
| `G2` — Full Backlog & DAG Integrity | Jev `JR-00`–`JR-46` (36 reqs / 239 ACs), Phase 020 (`130`–`132`), `#107`/`134`/`NDEBT-056`, `NDEBT-034`/`040`, `API-REF-PILOT`, `NF-01`–`NF-22`, and `NF-R01`–`NF-R05` reconciled in acyclic DAG (`N00`–`N08`, `J01`). | **PASS** | `docs/planning/nf-owner-2026-10-27/execution-dag.json`, `tools/test_nf_owner_dag_and_backlog.py` |
| `G3` — Core Assurance & Policy Repairs (`NF-R01`, `NF-R02`) | Finding F02 (`git replace` & Git redirection) closed across all read-only helpers and receipt consumers; Findings F10 & F11 closed across `standard/GIP.md`, `methodology/03_circuit_breaker.md`, and runtime enforcement. | **PASS** | `tools/test_nf_ac01_git_identity.py`, `tools/test_receipt_candidate_batching.py`, `tools/test_nf_ac02_policy_reconciliation.py` |
| `G4` — Typed Binary Coverage & Generic External Evidence (`NF-R03`, `NF-R04`) | Finding F09 closed via `"1.1.0"` typed binary packet contract (`opaque_binary`, `integrity_only` vs. `trusted_processor_derived`, approval invalidation); generic external evidence schema, corpus, and `tools/external_evidence.py` verified without Agentic SDLC. | **PASS** | `tools/test_nf_ac03_binary_review.py`, `tools/test_nf_ac04_generic_admission.py`, `tools/test_convergent_review.py` |
| `G5` — Standalone E2E Qualification & Compliance (`NF-R05`) | Standalone consumer `v2.0.0` install, `e2e-3.0.0-rc1` upgrade, `start_path.py`, `"1.0.0"`/`"1.1.0"` review, and `external_evidence.py` verified; `validate.sh` (16/16), `validate.sh --payload` (10/10), `fixtures_self_test.sh`, `test_start_path.py`, and `test_workflow_assurance.py` green. | **PASS** | `tools/test_nf_ac05_standalone_e2e.py`, `tools/validate.sh`, `tools/fixtures_self_test.sh` |
| `G6` — External & Operational Boundaries (`J01`) | External release tagging (`H-RELEASE-CUT`), consumer upgrade (`H-CONSUMER-UPGRADE`), live provider budget, and Linux userns/Docker daemon host conformance explicitly separated and never faked locally. | **PASS (BOUNDED / EXTERNALLY GATED)** | Section 3 Exit Reports below |

---

## 3. Individual Exit Reports (`N04`, `N08`, `J01`, and External Gates)

### 3.1 Node `N04` Exit Report — Core Standalone Qualification & `v2.0.0` Compatibility

- **Status:** `COMPLETED` (Verified Locally)
- **What Was Proven:**
  1. A clean standalone consumer repository with zero Agentic SDLC files, imports, or environment variables installs released `v2.0.0` (`603afc7b17919334a6a01df1e39e63798d9d0acd`) offline via `bootstrap.sh`, passes `--verify-only --require-content-integrity` (`content_integrity=verified`), and passes `.nizam/tools/validate.sh --payload` (`10 exercised passed, 0 failed`).
  2. Upgrading that consumer to the candidate snapshot via an explicit fixture tag (`e2e-3.0.0-rc1`) requires `--allow-fixture-tag` (refused without it) and passes `--verify-only --require-content-integrity` and `.nizam/tools/validate.sh --payload`.
  3. Standalone consumer task classification (`classify`), capability check (`preflight`), trivial route (`begin` -> `capture` -> `done`), `"1.0.0"` text-only `convergent_review.py` (`build-packet` -> `converge`), and negative tamper/scope controls all succeed using only `.nizam/`.
- **Verification Command:** `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 python3 tools/test_nf_ac05_standalone_e2e.py -v -k test_n04`

### 3.2 Node `N08` Exit Report — Extended Standalone Qualification (Binary Review & Generic External Evidence)

- **Status:** `COMPLETED` (Verified Locally)
- **What Was Proven:**
  1. Standalone consumer repositories operate normally (`start_path.py status --format json` reconciled with zero contradictions) when external evidence integration is completely absent.
  2. Committing binary assets (`assets/logo.png`) alongside source changes (`src/app.py`) in a standalone consumer builds a valid `"1.1.0"` review packet (`opaque_binary` with `image/png` and `integrity_only`, plus `text`), converges 3 trials, and passes `verify-replay`.
  3. Standalone consumer execution of `.nizam/tools/external_evidence.py` (`allocate-attempt`, `admit-evidence`, idempotent duplicate delivery, unknown profile rejection, and `reconcile`) succeeds end-to-end without Agentic SDLC.
- **Verification Command:** `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 python3 tools/test_nf_ac05_standalone_e2e.py -v -k test_n08`

### 3.3 Node `J01` & External Gates Exit Report

- **Status:** `EXTERNALLY_GATED` (Not Executed Locally; Preserved for Authorized Operator / Host Execution)
- **Blocked External Gates & Required Authority:**
  1. **`H-RELEASE-CUT` (Public Tag Release):** Cutting and pushing a public `v3.0.0` Git tag on `https://github.com/niq-cnr/nizam-framework.git` requires operator release authority. Candidate qualification used disposable local tag `e2e-3.0.0-rc1` with `--allow-fixture-tag`.
  2. **`H-CONSUMER-UPGRADE` (Self-Governance `.nizam/` Re-Bootstrap):** Updating this repository's own `.nizam/` from `v2.0.0` (`603afc7b17919334a6a01df1e39e63798d9d0acd`) requires an immutable released tag and explicit operator authorization.
  3. **`LINUX-USERNS-OR-DOCKER-HOST` (`NDEBT-040` / `NDEBT-056`):** The local macOS Darwin host (`arm64`) does not provide Linux `unshare --user` or Landlock syscall 444, and the local Docker daemon is not running (`tools/docker_trial_sandbox.sh --probe` exits 3). Full 5-test sandbox isolation conformance (`CONFORMANCE: FULL` without `--allow-unsupported-isolation`) and container boundary omission controls execute in hosted Linux CI (`.github/workflows/compliance.yml` `convergent_review` job).
  4. **`LIVE-PROVIDER-BUDGET` & Downstream Adapter Verification (`JR-00`–`JR-46` Live Nodes & Phase 020 `130`–`132`):** Live paid model provider calls, live SBCL process acceptance (Phase 020 features `130`–`132`), and downstream external producer rollout remain gated on operator budget/authority and are preserved in `docs/planning/nf-owner-2026-10-27/execution-dag.json`.
