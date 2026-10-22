---
id: nizam-jev-readiness-backlog-map
title: "Jev Readiness Backlog Reconciliation"
description: "Requirement, acceptance-criterion and JR-package reconciliation for mandate NIZAM-JEV-OWNER-2026-10-22."
version: 0.1.0
status: active
authoritative_source: docs/planning/jev-readiness/backlog-map.md
change_log:
  - version: "0.1.0"
    date: "2026-10-22"
    summary: "Reconcile the 36 requirements, 239 acceptance criteria and JR packages at baseline 3b94a9e5; record reproduced counterexamples and the locally landed control repairs with independent verification open."
---

# Backlog reconciliation — Jev readiness

Reconciled at `3b94a9e5fc2bd7a21d8cdee2246f958d310d52a3` against the current
source, installed provenance, remote state, debt register, roadmap and the
landed cleanup work. Dispositions use the mandate vocabulary. "Planned" means
the obligation is real and unstarted; it is not a completion claim.

## 1. Requirement register (36 entries)

| ID | Target requirement (short) | Canonical JR | Current implementation / evidence | Disposition |
| --- | --- | --- | --- | --- |
| F01 | Relabel efficiency claims; retain captures | JR-08 | `cohort_economics.py` encodes corrected labels and separations; historical text still needs the final sweep | partially implemented; label sweep open |
| F02 | Comprehensive provider usage capture | JR-07 | `usage_accounting.py` event contract + charged-once/unknown accounting implemented | **partially implemented; live boundary instrumentation open** |
| F03 | One strict normalized completion predicate | JR-02 | `qa_passes` has legacy-shape gaps (missing status accepted; no capture binding) | **implemented locally; independent verification open** |
| F04 | Bind complete delta to immutable base; no fail-open | JR-03 | `verify_actual_changed_scope` ignores committed changes, blanket-skips `.agent/`, returns on Git error | **implemented locally; independent verification open** |
| F05 | Validated contract context end to end | JR-04 | `done` re-loads the bugfix scope/contract but lacks contract consistency checks | **implemented locally; independent verification open** |
| F06 | Monotonic authoritative attempts | JR-05 | Attempt number was caller-supplied (`--attempt`); no authoritative ledger | **implemented locally; independent verification open** |
| F07 | Continuation requires scoped unspent authority | JR-06 | `--repair-summary` alone satisfied some continuation bases | **implemented locally; independent verification open** |
| F08 | Retain/recover only eligible review slots | JR-09 | Feature 134 delivered host capability; live-model gap open (NDEBT-056) | extend existing work |
| F09 | Bound projections without losing evidence | JR-10 | No bounded projection/verified-retrieval contract found | planned |
| F10 | Compact transition inspection | JR-11 | `status` already compact | preserve-and-extend |
| F11 | Reprofile CI before optimizing | JR-18 | Cleanup merged; run 39795674036 took 33m16s | planned measurement |
| F12 | Separate offline/host/live/quality evidence | JR-08/JR-18/JR-22 | Partially separated in remediation records | extend |
| F13 | Small shared pure predicates, byte identity | JR-01/JR-04 | Canonical vectors landed in PR #129; shared policy module absent | extend |
| F14 | Truthful Bash/Python prerequisites | JR-19 | README/bootstrap partially document; clean-env rehearsal unproven | planned |
| F15 | Move history out of repeatedly loaded instructions | JR-11 | `AGENTS.md` carries a long change log | planned |
| F16 | Justified payload split or accepted non-adoption | JR-20/JR-45 | Sparse bootstrap landed (PR #130); split decision open | decide-and-deliver |
| F17 | Qualify supported hosts; retain live gap | JR-00/JR-09/JR-14/JR-22 | macOS Landlock probe fails; issue #107/NDEBT-056 open | reconcile-and-qualify |
| F18 | Version new writes; keep old records readable | JR-01/JR-21 | Canonical vectors exist; no versioned semantic/attempt state | planned |
| J01 | Facts/judgment/authority separated | JR-12/JR-13 | Typed contracts + veto-first policy composition landed offline; no authority fields present | **partially implemented; integration pending** |
| J02 | Start with component→requirement Choice | JR-15/JR-16 | DF-01 question + fixtures + admission/projection implemented | **partially implemented; live dispatch open** |
| J03 | Validate distributions/abstention; calibrate | JR-12/JR-17 | Choice/Noul/Score validation + abstention/tie semantics implemented; held-out calibration pending | **partially implemented; evaluation pending** |
| J04 | Batch only independent questions over same state | JR-10/JR-15 | None | planned |
| J05 | Implement/qualify all seven families | JR-28…JR-33, JR-23/24 | Seven family question definitions + mandatory sources implemented; qualification open | **partially implemented; qualification gated** |
| J06 | Off default; optional provider | JR-12/13/14 | Off-default modes + mock/replay/shadow isolation + optional Jev adapter (mock transport) implemented | **partially implemented; live transport gated** |
| J07 | Pin model, bind observation, explicit replay | JR-12/13/14 | Observation binding (requested/resolved model, digests) implemented; adapter/dispatch/replay pending | **partially implemented; adapter pending** |
| J08 | Explicit external-processing boundary | JR-14/JR-15 | Review sandbox boundary exists; no provider egress policy | planned |
| J09 | Four-arm, held-out, all-in economics | JR-07/08/16/17/23/24 | Accounting, economics, corpus split and four-arm harness implemented; live arms gated | **partially implemented; live comparison gated** |
| J10 | Readiness is not savings or promotion | JR-22/23/24/41/42/43/44 | None | planned + gated |
| X01 | Reconcile cleanup; do not duplicate/delete | JR-00 | PRs 128–130 merged and ancestors of HEAD; archive resolver/vectors present | **reconciled, reuse** |
| C01 | Complete control-surface coverage | JR-25/34/40/44 | Partial map implied by `start_path` routes; no full matrix | planned |
| C02 | Full typed architecture and policy ownership | JR-12/26/27/34 | Contracts, policy, catalog implemented; JR-34 integration and JR-26 boundary open | **partially implemented** |
| C03 | All material semantic families | JR-15/28…33 + evaluation | All seven family definitions implemented; DF-01 fixtures; evaluation corpus/harness landed | **partially implemented; qualification gated** |
| C04 | Operational resilience and data control | JR-14/35/36/37/38 | Attempt/capture primitives exist; no budgets/provider controls | planned |
| C05 | Actual independent-review qualification | JR-09/36/41/46 | Issue #107 + NDEBT-056; no live model observations | planned + gated |
| C06 | Migration and supported release | JR-19/21/39/40/42/43/45 | Bootstrap sparse/rollback work landed; active-state migration not rehearsed for Jev | planned |
| C07 | Full-program closure | JR-22/23/24/41/42/43/44 | None | planned + gated |

## 2. Issue #107 reconciliation

- Feature 134 removed the host-capability blocker by landing the Docker trial
  sandbox adapter. It explicitly did **not** close the live-model observation
  gap (NDEBT-056) and did not qualify an actual review.
- Issue #107's older "add a portable adapter" proposal must not be reimplemented
  by title. The remaining obligation is adapter-specific conformance plus the
  actual live-model/trusted-release proof, owned by JR-09/JR-36/JR-41/JR-46.
- Current host: macOS cannot run the native Landlock path. No Docker daemon
  qualification was performed in this session. The adapter therefore remains
  **unsupported/uncertain** on this host, not qualified.

## 3. Cleanup residuals (preserved, not re-scoped)

| Residual | Status in this program |
| --- | --- |
| Sparse target/reference rollback NOT_RUN failure injection | JR-19 acceptance check; must be reproduced, not assumed |
| Host-specific start-path/Landlock failures | Preserved; this host reproduces the failure |
| `publish_captured_evidence` decomposition | Still deferred; not smuggled into Jev work |
| `H-CONSOLIDATION` | Out of scope for a single Jev program step; remains an outstanding Operator gate |
| Main CI run 39795674036 | Refreshed: completed/success at the inspected main |

## 4. Acceptance-criteria coverage

The 239 AC IDs remain binding. Mapping by parent package:

| Packages | AC IDs | Count |
| --- | --- | --- |
| JR-00 | AC-00-01 … AC-00-04 | 4 |
| JR-01 | AC-01-01 … AC-01-04 | 4 |
| JR-02 | AC-02-01 … AC-02-05 | 5 |
| JR-03 | AC-03-01 … AC-03-05 | 5 |
| JR-04 | AC-04-01 … AC-04-04 | 4 |
| JR-05 | AC-05-01 … AC-05-05 | 5 |
| JR-06 | AC-06-01 … AC-06-05 | 5 |
| JR-07 | AC-07-01 … AC-07-05 | 5 |
| JR-08 | AC-08-01 … AC-08-05 | 5 |
| JR-09 | AC-09-01 … AC-09-05 | 5 |
| JR-10 | AC-10-01 … AC-10-05 | 5 |
| JR-11 | AC-11-01 … AC-11-04 | 4 |
| JR-12 | AC-12-01 … AC-12-08 | 8 |
| JR-13 | AC-13-01 … AC-13-06 | 6 |
| JR-14 | AC-14-01 … AC-14-05 | 5 |
| JR-15 | AC-15-01 … AC-15-06 | 6 |
| JR-16 | AC-16-01 … AC-16-06 | 6 |
| JR-17 | AC-17-01 … AC-17-06 | 6 |
| JR-18 | AC-18-01 … AC-18-05 | 5 |
| JR-19 | AC-19-01 … AC-19-05 | 5 |
| JR-20 | AC-20-01 … AC-20-04 | 4 |
| JR-21 | AC-21-01 … AC-21-05 | 5 |
| JR-22 | AC-22-01 … AC-22-05 | 5 |
| JR-23 | AC-23-01 … AC-23-06 | 6 |
| JR-24 | AC-24-01 … AC-24-06 | 6 |
| JR-25 | AC-25-01 … AC-25-05 | 5 |
| JR-26 | AC-26-01 … AC-26-05 | 5 |
| JR-27 | AC-27-01 … AC-27-05 | 5 |
| JR-28 | AC-28-01 … AC-28-05 | 5 |
| JR-29 | AC-29-01 … AC-29-05 | 5 |
| JR-30 | AC-30-01 … AC-30-05 | 5 |
| JR-31 | AC-31-01 … AC-31-05 | 5 |
| JR-32 | AC-32-01 … AC-32-05 | 5 |
| JR-33 | AC-33-01 … AC-33-05 | 5 |
| JR-34 | AC-34-01 … AC-34-05 | 5 |
| JR-35 | AC-35-01 … AC-35-05 | 5 |
| JR-36 | AC-36-01 … AC-36-05 | 5 |
| JR-37 | AC-37-01 … AC-37-05 | 5 |
| JR-38 | AC-38-01 … AC-38-05 | 5 |
| JR-39 | AC-39-01 … AC-39-05 | 5 |
| JR-40 | AC-40-01 … AC-40-05 | 5 |
| JR-41 | AC-41-01 … AC-41-05 | 5 |
| JR-42 | AC-42-01 … AC-42-05 | 5 |
| JR-43 | AC-43-01 … AC-43-05 | 5 |
| JR-44 | AC-44-01 … AC-44-05 | 5 |
| JR-45 | AC-45-01 … AC-45-05 | 5 |
| JR-46 | AC-46-01 … AC-46-05 | 5 |
| **Total** | | **239** |

Status rule: an AC is complete only with candidate-bound evidence and the
required independent verdict. Planning text, merged PR titles and green
unrelated checks are not completion evidence.

## 5. Reproduced counterexamples (this session)

| Counterexample | Where | Result |
| --- | --- | --- |
| Legacy QA shape accepts a check with no `status` and only `required_fixes` as a blocker | `tools/start_path.py:qa_passes` | Regression control reproduces the weak branch and asserts rejection; independent review open |
| Scope check returns success when Git inspection fails | `tools/start_path.py:verify_actual_changed_scope` | Regression control asserts fail-closed Git errors; independent review open |
| Scope check skips every `.agent/` change | same | Regression control asserts only task-owned `.agent` outputs pass; independent review open |
| Committed changes are invisible to completion | same | Regression control asserts committed/staged/untracked deltas are all checked; independent review open |
| Contract can be reused without task/contract consistency | `tools/start_path.py:require_inside_contract` | Regression control asserts mismatched contract identity is rejected; independent review open |
| Caller can reset attempt history with a reused/lower `--attempt` or a fresh `--output-dir` | `tools/start_path.py:_evaluate_attempt_continuation` / `_reserve_attempt` | Regression control asserts reuse is rejected and the reservation is atomic; independent review open |
| Narrative `--repair-summary` can grant continuation authority | `tools/start_path.py:_evaluate_attempt_continuation` | Regression control asserts each base requires its verified authority reference; independent review open |
| Host cannot run the Landlock sandbox | `tools/isolated_trial_adapter.py` | Reproduced: exit 1, `OSError 14` |

Corrected-behavior evidence is captured by the new regression test added in
this wave; it is local conformance evidence, not independent acceptance.
