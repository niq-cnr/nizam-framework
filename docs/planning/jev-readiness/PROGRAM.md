---
id: nizam-jev-readiness-program
title: "Comprehensive Jev Readiness Program"
description: "Execution record for mandate NIZAM-JEV-OWNER-2026-10-22: baseline, backlog reconciliation, execution DAG, deterministic repairs, semantic architecture, qualification and rollout."
version: 0.9.0
status: active
authoritative_source: docs/planning/jev-readiness/PROGRAM.md
change_log:
  - version: "0.9.0"
    date: "2026-10-22"
    summary: "Land the semantic foundation and accounting/evaluation wave on branch feat/jev-readiness-2026-10-22 (PR #131): JR-07 provider-attempt accounting, JR-08 cohort economics, JR-14 optional Jev adapter (mock transport), JR-27 catalog, JR-15/JR-28..33 seven-family question definitions, JR-16/JR-17 evaluation corpora and four-arm harness. Offline, tested; independent review, JR-34 integration, the remaining operational packages and all gated live/migration/rollout/acceptance work remain open."
  - version: "0.6.0"
    date: "2026-10-22"
    summary: "Implement JR-13 mode isolation and pure deterministic policy composition: tools/semantic_policy.py (off-default global/per-family ModeState with authorized widening and rollback, veto-first compose_policy bounded by mode) and tools/test_semantic_policy.py adversarial tests. Off/mock/replay/shadow never influence the baseline."
  - version: "0.5.0"
    date: "2026-10-22"
    summary: "Implement JR-12 provider-neutral Choice/Noul/Score contracts: tools/semantic_contract.py (discriminated union + pure validation + observation binding), three JSON schemas (indexed in NIZAM.json and schema/README.md), and tools/test_semantic_contract.py adversarial tests. Pure offline preparation against a pinned contract; feature integration and independent review remain open."
  - version: "0.4.0"
    date: "2026-10-22"
    summary: "Implement JR-06 continuation-authority tightening locally: narrative --repair-summary no longer satisfies bounded-amendment, verified-decomposition, or operator-reset; each requires its verified authority reference. Add the standalone regression control."
  - version: "0.3.0"
    date: "2026-10-22"
    summary: "Implement JR-05 authoritative monotonic attempt allocation locally (reuse rejection + atomic reservation), add the standalone regression control, and record it with independent verification open."
  - version: "0.2.0"
    date: "2026-10-22"
    summary: "Record the local completion of the JR-02/JR-03/JR-04 control repairs, reconcile ROADMAP/DEBT/README and the supersession notes with this program, and state the ordered next action and document map. No independent acceptance, release, live execution or Operator closure is claimed."
  - version: "0.1.0"
    date: "2026-10-22"
    summary: "Refresh the mandate baseline at 3b94a9e5, record the reconciled backlog disposition and reference execution DAG, and start the deterministic control repairs (JR-02/JR-03/JR-04) with local evidence."
---

# Comprehensive Jev Readiness Program

This is the durable execution record for mandate
`NIZAM-JEV-OWNER-2026-10-22`. It is additive planning; it does not replace the
repository's contracts, QA records, `run_state.json`, debt register or roadmap.
Where this record and a governed artifact disagree, the governed artifact and
the current source win.

## 1. Current claim

**Program status: IN PROGRESS — the deterministic repairs, provider-neutral
semantic architecture and the accounting/evaluation foundation are implemented
offline and under review; integration, the remaining operational packages and
every live/migration/rollout/acceptance gate remain open. The program is not
complete.**

- Baseline refreshed and reconciled (JR-00).
- Deterministic governance (JR-02/JR-03/JR-04/JR-05/JR-06) implemented and
  covered by standalone regressions.
- Typed contracts (JR-12), mode-isolated policy (JR-13), the versioned catalog
  and the seven family question definitions (JR-27, JR-15, JR-28..JR-33), the
  optional Jev adapter with mock transport (JR-14), provider accounting
  (JR-07), cohort economics (JR-08), and the evaluation corpus/harness
  (JR-16/JR-17) are implemented offline and covered by adversarial tests.
- All of the above was merged to `main` via PR #131 (merge `86d467ef`) with all
  six CI checks green. It is CI-verified offline evidence, not independent
  acceptance, not release, and not live qualification.
- Not yet implemented: wiring the families into the supported routes and roles
  (JR-34), architecture inventory (JR-01/JR-25), authority-boundary fixtures
  (JR-26), review-slot persistence (JR-09/JR-10), entry context (JR-11), CI
  profiling (JR-18), reproducible prerequisites (JR-19), budgets/cancellation
  (JR-35), isolation-host qualification (JR-36), operations/drift (JR-37),
  external-data hardening beyond the adapter (JR-38), documentation (JR-40),
  packaging decision (JR-20/JR-45), reviewer binding (JR-46), release candidate
  (JR-21) and migration rehearsal (JR-39).
- Every gated live package remains open: shadow/advisory (JR-23/JR-24), live
  review qualification (JR-41), pilot release/upgrade (JR-42), staged rollout
  (JR-43), and independent acceptance and Operator closure (JR-22/JR-44).
- Off mode remains the only supported semantic mode by default.

No statement in this record is an independent acceptance verdict or an
Operator acceptance decision.

### Immediate next action

1. Let PR #131 CI run clean and obtain independent review of the JR-02..06 diff,
   then run the full `tools/test_start_path.py` suite on a Landlock-qualified
   Linux host. Do not mark the controls accepted from the macOS standalone run
   alone.
2. Implement the remaining offline packages in dependency order: JR-34 family
   integration, JR-26 authority boundary, JR-09/JR-10 review-slot recovery,
   JR-35 budgets, JR-11/JR-18/JR-19/JR-40 consumer/CI/onboarding, JR-21/JR-39
   release candidate and migration, then JR-36/JR-37/JR-45/JR-46.
3. Stop at the external gates in §5 and `AUTHORITY.md`; none of them are
   unlocked by this program record.

## 2. Refreshed baseline (2026-10-22)

| Item | Observed value |
| --- | --- |
| Repository | `https://github.com/niq-cnr/nizam-framework.git` |
| Inspected commit | `3b94a9e5fc2bd7a21d8cdee2246f958d310d52a3` |
| Branch / worktree | `main`, clean (`## main...origin/main`) |
| Source `NIZAM.json` version | `1.10.1` |
| Installed provenance | `v1.10.1` / `2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd` |
| Open PRs | none |
| Open issues | #107 (portable sandbox adapter / live-model gap) |
| Current-main CI | run `39795674036`, **completed / success**, 33m16s |
| Active lifecycle state | phase `020-sbcl-fresh-acceptance`, feature `130`, `in_progress` |
| Acquisition | existing local clone; `git status`, `git log`, `gh`, source reads |
| Host | Darwin arm64, Python 3.14.6, Bash 5.3.15 |
| Host sandbox | `sandbox_available=false`; Landlock probe exits 1 (`OSError 14`) |
| `tools/test_start_path.py` | exits 1 at the preflight step on this host (host-specific sandbox probe), not at a control assertion |
| `tools/validate.sh` | did not complete within the 180s local timeout; NOT_RUN on this host |

Post-baseline re-run after the documentation edits:
`PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh` passed 16/16; the full
`tools/test_start_path.py` suite remains blocked by the host sandbox probe. The
baseline table below records the start-of-program observations.

The clean-worktree observation is the baseline at program start. After the
JR-02/JR-03/JR-04 wave the working tree intentionally contains uncommitted
changes in `tools/start_path.py`, `tools/test_start_path.py` and this planning
directory; that is not a release or acceptance state. The installed `.nizam/`
payload is unchanged.

Landed cleanup work at this commit is an ancestor and is reused, not
reimplemented: PR #128 (archive/fixture relocation), PR #129
(preservation/canonical byte vectors), PR #130 (sparse bootstrap).

Historical facts preserved without rewriting: the original audit baseline
`c5297f6a`; the 12 paired / 24 captured pilot records; the seeded blockers; the
Linux-only tests that were NOT_RUN on the earlier host; the cleanup record's
`H-CONSOLIDATION` outstanding status.

## 3. Authority and gates

- Source work follows the repository's own route and contract mechanisms.
  `docs/planning/jev-readiness/*` and the deterministic tool changes classify
  as `small-change`; feature-level semantic architecture needs an approved
  feature contract.
- Installed `.nizam/` is not edited. It changes only through an authorized
  immutable release and supported upgrade.
- The following require separate concrete authorization that this mandate does
  not confer: spending money, sending repository data to a provider, merging,
  publishing a release, upgrading real consumers, production influence.
- The historical USD 100 smoke ceiling is **not** authorization for this
  program.
- Implementer agents do not self-certify independent acceptance or Operator
  closure.

## 4. Ready frontier (safe now)

1. **Complete / under review:** JR-00 baseline, JR-02..JR-06 deterministic
   repairs, JR-07/JR-08 accounting and economics, JR-12/JR-13 semantic
   contracts and policy, JR-14 mock adapter, JR-27 catalog, JR-15/JR-28..JR-33
   family definitions, JR-16/JR-17 evaluation foundation (PR #131).
2. **Next safe offline work:** JR-34 family integration, JR-26 authority
   boundary, JR-09/JR-10 review-slot recovery, JR-35 budgets/cancellation,
   JR-11/JR-18/JR-19/JR-40 context/CI/onboarding/docs, JR-21/JR-39 release
   candidate and migration rehearsal, then JR-36/JR-37/JR-45/JR-46.
3. **Blocked by the review host:** a Landlock-qualified full-suite run of
   `tools/test_start_path.py` (macOS cannot run the native sandbox probe).

## 5. Gated / blocked frontier

- JR-14 live adapter dispatch: needs provider account, permitted data, exact
  model, budget and deadline.
- JR-23/JR-24 shadow and advisory execution: needs the above plus an approved
  evaluation plan and frozen corpus.
- JR-41/JR-42/JR-43 live review, release, consumer migration and rollout: need
  Operator/release/consumer authority.
- JR-22/JR-44 independent offline acceptance and final closure: need an
  independent assurance reviewer and the Operator.

## 6. Definition of done (unchanged)

All 36 F/J/X/C entries and all 239 AC IDs must be reconciled to verified
completion or a specific permitted, evidence-backed Operator disposition.
Deterministic counterexamples must fail safely; legitimate workflows must pass.
All three primitives and seven families must be implemented, integrated and
evaluated. Actual live qualification, migration, release, operational
comparison and independent closure remain required for the claimed support.

## 7. Canonical companion artifacts

- `baseline.json` — machine-readable refreshed baseline.
- `backlog-map.md` — requirement/AC/JR reconciliation and dispositions.
- `execution-dag.json` — versioned reference graph with typed edges/status.
- `support-matrix.json` — supported/held/unsupported cells for the primitive/family/mode/role surface.
- `measurement-policy.md` — evidence classes and economics definitions.
- `AUTHORITY.md` — concrete external gates and what each one unlocks.

### Where current status lives

- This file is the durable program record and ordered next action.
- [ROADMAP.md](/docs/planning/ROADMAP.md) is the live project-position summary; its
  "Current position" section points here and carries the release facts.
- [DEBT.md](/docs/planning/DEBT.md) is the only open-debt register; this program does not
  create debt rows and does not close them.
- [SELF_GOVERNANCE.md](/docs/planning/SELF_GOVERNANCE.md) owns installation/commissioning
  state. This program changes source and planning only; the installed `v1.10.1`
  payload and its commissioning stage are unchanged.
- [REMEDIATION_2026_10_18.md](/docs/planning/REMEDIATION_2026_10_18.md) and the handover
  packets are dated historical records. They are not current directives.
- `.agent/run_state.json` remains lifecycle authority; this record does not
  replace or mutate it.

## 8. Execution log (2026-10-22 wave)

### Completed in source

- **JR-02** — `tools/start_path.py:qa_passes` is now one strict normalized
  predicate for both historical QA shapes. It rejects contradictory
  `qa_pass`/`verdict` markers, non-passing checks (including legacy checks that
  omit `status` but carry a non-zero exit), missing per-check evidence, short
  `evidence_files`, blocking arrays, and `final_verdict.approved is not True`.
- **JR-03** — `tools/start_path.py:verify_actual_changed_scope` binds `done` to
  the complete delta from the task base recorded at `begin`
  (`.agent/evidence/<id>-base.json`): committed, staged, unstaged, untracked,
  rename/copy endpoints, and explicit task-owned `.agent` outputs. Git
  inspection failures and wrong worktree roots fail closed. A genuinely
  non-Git project retains the historical local-only behavior.
- **JR-04** — `tools/start_path.py:require_inside_contract` rejects a contract
  record whose `contract_id`/`feature_id` disagree with each other or with the
  requested contract.
- **JR-05** — `tools/start_path.py:_authoritative_consumed_attempts` derives the
  authoritative next attempt from the durable circuit-breaker counter plus every
  prior capture/reservation marker under `.agent/evidence/` regardless of output
  directory or session. `_evaluate_attempt_continuation` rejects a requested
  attempt that reuses a consumed number, and `_reserve_attempt` atomically
  reserves the number (exclusive create) before dispatch. The reuse check runs
  after the invariant-breach halt so safety halts are never shadowed.
- **JR-06** — `tools/start_path.py:_evaluate_attempt_continuation` no longer
  accepts a narrative `--repair-summary` as continuation authority. `bounded-
  amendment` requires a recorded contract amendment, `verified-decomposition`
  requires `--decomposition-of`, and `operator-reset` requires recorded operator
  authorization in `.agent/run_state.json`. `--repair-summary` remains
  explanatory only.
- **JR-12** — `tools/semantic_contract.py` defines the versioned discriminated
  union for Choice/Noul/Score with pure per-primitive validation, the full
  observation binding (task/operation/attempt, base/candidate, requirement and
  contract refs, question family/version with ordered options/rubric/polarity,
  exact requested/resolved model with mismatch rejection, transport body/response
  digests, and the six execution statuses plus reason codes). `answer` is
  non-authoritative and separate from execution status; a missing Noul
  probability is unknown, never false; option order participates in identity;
  confidence is rejected rather than relabeled. Three JSON schemas
  (`semantic_observation`, `semantic_request`, `semantic_policy_result`) are
  indexed in `NIZAM.json` and `schema/README.md`.
- **JR-13** — `tools/semantic_policy.py` implements the six modes (off/mock/
  replay/shadow/advisory/governed) with off as the immutable default. `ModeState`
  resolves a global mode with per-family overrides; `authorize_transition`
  requires a non-empty authorization record to widen influence and `disable`
  always rolls back to off. `compose_policy` is pure and veto-first:
  `HardVeto` predicates over verified facts trigger the ``veto`` outcome in any
  mode, non-succeeded observations fall back to ``no_effect``, and the remaining
  disposition stays inside the mode's bounded set (off/mock/replay/shadow never
  influence the baseline).

- **JR-27/JR-15/JR-28..33** — `tools/semantic_catalog.py` defines the seven
  families with typed questions and dependency/cycle validation;
  `tools/semantic_families.py` defines every family's question, admission gate and
  bounded state projection, with DF-01 fixtures covering all four categories.
- **JR-14** — `tools/providers/jev.py` is the optional host-side adapter: exact
  pinned model (no floating alias), TLS-enforced trusted endpoint, no redirects,
  sealed credential, one transport attempt, and the Jev SystemOne wire format
  translated into provider-neutral observations. 429/5xx/timeout/malformed/
  model-mismatch/missing-answer/lost-response return bounded fallbacks.
- **JR-07/JR-08** — `tools/usage_accounting.py` records and reconciles
  provider-attempt events (charged-once, unknown-not-zero, append-only);
  `tools/cohort_economics.py` computes cost per accepted change with an undefined
  zero-denominator and keeps corrected historical measurement labels.
- **JR-16/JR-17** — `tools/evaluation_corpus.py` freezes independently
  adjudicated corpora and splits by lineage group without leakage;
  `tools/evaluation_harness.py` validates the A/B/C/D arms, matched inputs,
  arm-D applicability and the preregistration contract.

### Documentation reconciliation

- `ROADMAP.md` now names this program as the active position, states the
  blocked/ready frontier, and reconciles open debt to NDEBT-034, NDEBT-040 and
  NDEBT-056 (NDEBT-055 is resolved).
- `DEBT.md` moves NDEBT-055 to the Resolved table and links NDEBT-056 to issue
  #107 and the completed feature 134 without claiming live-model coverage.
- `README.md` points readers at this record for current status.
- `REMEDIATION_2026_10_18.md` records that its active mandate is superseded for
  direction by this program while its dated execution facts remain historical.
- No `.nizam/`, `run_state.json`, contract, QA or release record was changed.

Documentation checks run locally: all `jev-readiness/*.json` parse; the edited
frontmatter parses with monotonic version/change-log entries; `git diff --check`
is clean; and `PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh` completed
**16/16 checks passed, 0 failed** after these edits. `--target` mode is not used
as the acceptance signal because it applies file-relative C9 resolution
differently from the full sweep. These are editorial checks, not independent
acceptance.

### Verification actually run on this host

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile tools/start_path.py tools/test_start_path.py` | PASS |
| standalone `test_jev_readiness_controls()` | PASS — strict QA, complete-delta scope, contract identity |
| standalone `test_jev_readiness_attempts()` | PASS — reuse rejection, cross-output-dir authority, atomic reservation |
| standalone `test_jev_readiness_authority()` | PASS — narrative summary cannot grant the three continuation bases |
| `python3 tools/test_semantic_contract.py` | PASS — Choice/Noul/Score validation + observation binding adversarial cases |
| `python3 tools/test_semantic_policy.py` | PASS — off-default modes, veto-first composition, authorized transitions |
| `python3 tools/test_semantic_catalog.py` | PASS — seven-family registry and question-dependency validation |
| `python3 tools/test_semantic_families.py` | PASS — DF-01 admission/projection and four-category fixtures |
| `python3 tools/test_jev_adapter.py` | PASS — trust boundary, bounded fallbacks, secret isolation (mock transport) |
| `python3 tools/test_usage_accounting.py` | PASS — charged-once, unknown-not-zero, append-only reconciliation |
| `python3 tools/test_cohort_economics.py` | PASS — undefined zero denominator, dedup, unknown/shadow separation |
| `python3 tools/test_evaluation.py` | PASS — leakage-free split, matched arms, preregistration |
| `PYTHONDONTWRITEBYTECODE=1 python3 tools/test_start_path.py` | NOT_COMPLETED — host sandbox probe fails before the suite (`OSError: [Errno 14] Bad address`) |
| `PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh` (after documentation edits) | PASS — 16/16 checks, 0 failed |

The standalone control is runnable independently of the host preflight and
covers: legacy non-zero exit with no `status`; legacy blocking `issues`;
evolved `qa_pass`/`final_verdict` contradiction; evolved evidence-count
shortfall; uncommitted undeclared file; declared-plus-task-owned positive
completion; committed undeclared file; both rename endpoints; non-task
`.agent/run_state.json`; contract identity disagreement. The attempts control
covers: attempt-1 reuse rejection; reuse across a different output directory;
authoritative next attempt success; reservation markers for both attempts; and
the invariant-breach halt ordering relative to the reuse check.

### Still open in this wave

- The full `tools/test_start_path.py` suite remains NOT_COMPLETED on macOS
  because the native Landlock sandbox probe is unqualified there. This is a host
  limitation, not a control assertion failure. `tools/validate.sh` was re-run
  after the documentation edits and passed 16/16 on this host; it is not a
  substitute for the control regression suite or independent review.
- Independent acceptance, merge, release, consumer upgrade, live provider
  execution, and Operator closure remain gated. Nothing in this wave
  self-certifies those.
- Proof is merged to `main` via PR #131 (merge `86d467ef`) with all six CI
  checks green, including `test_start_path.py` on Linux (landlock-qualified)
  and `tools/validate.sh` 16/16. This is CI-verified offline evidence, not
  independent acceptance; the live/migration/rollout/Operator gates remain.
