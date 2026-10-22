---
id: nizam-jev-readiness-program
title: "Comprehensive Jev Readiness Program"
description: "Execution record for mandate NIZAM-JEV-OWNER-2026-10-22: baseline, backlog reconciliation, execution DAG, deterministic repairs, semantic architecture, qualification and rollout."
version: 0.6.0
status: active
authoritative_source: docs/planning/jev-readiness/PROGRAM.md
change_log:
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

**Program status: IN PROGRESS — deterministic repairs landed locally;
independent verification and the semantic program remain open.**

- The baseline is refreshed and reconciled (JR-00).
- JR-02/JR-03/JR-04 are implemented in the working tree and covered by the
  standalone regression control; full-suite and independent review remain open
  (see §8).
- JR-05 authoritative monotonic attempt allocation is implemented in the working
  tree and covered by its own standalone regression control; the full suite and
  independent review remain open (see §8).
- JR-06 continuation-authority verification is implemented in the working tree
  and covered by its own standalone regression control; the full suite and
  independent review remain open (see §8).
- JR-12 typed semantic contracts (Choice/Noul/Score discriminated union,
  validation and observation binding) are implemented offline and covered by
  `tools/test_semantic_contract.py`; feature contract approval, integration and
  independent review remain open (see §8).
- JR-13 mode isolation and pure policy composition are implemented offline and
  covered by `tools/test_semantic_policy.py`; the live adapters (JR-14) and
  integration remain open (see §8).
- ROADMAP, DEBT, README and the 2026-10-18 remediation record now point at this
  record; the remediation is a completed predecessor, not the active directive
  (see §7).
- No Jev/semantic implementation, live call, release, consumer upgrade,
  operational comparison or independent program acceptance has occurred.
- Off mode remains the only supported semantic mode by default.

No statement in this record is an independent acceptance verdict or an
Operator acceptance decision.

### Immediate next action

1. Obtain independent review of the JR-02/JR-03/JR-04/JR-05/JR-06 diff and run the full
   `tools/test_start_path.py` suite on a Landlock-qualified Linux host
   (`tools/validate.sh` already passes 16/16 locally but should be re-run with
   the review). Do not mark these controls accepted from the macOS standalone
   run alone.
2. If accepted, integrate the repairs through the repository's normal review
   and merge path. The working tree is intentionally uncommitted until that
   review.
3. Then resume the ready frontier in order: JR-01/JR-25 inventory, JR-18/JR-19
   measurement/reproduction, JR-12/JR-27 typed semantic contracts.
4. Stop at the external gates in §5 and `AUTHORITY.md`; none of them are
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

1. **Complete:** JR-00 baseline/reconciliation and the documentation
   reconciliation recorded in §8.
2. **Landed locally, review required:** JR-02 strict QA predicate, JR-03
   complete-delta scope binding, and JR-04 contract consistency, all covered by
   `test_jev_readiness_controls`.
3. **Landed locally, review required:** JR-05 authoritative monotonic attempt
   allocation (reuse rejection + atomic reservation), covered by
   `test_jev_readiness_attempts`.
4. **Landed locally, review required:** JR-06 continuation-authority
   verification, covered by `test_jev_readiness_authority`.
5. **Landed locally, review required:** JR-12 typed semantic contracts,
   covered by `tools/test_semantic_contract.py`; feature contract approval and
   integration still open.
6. **Landed locally, review required:** JR-13 mode isolation and pure policy
   composition, covered by `tools/test_semantic_policy.py`.
7. **Next safe work:** independent review and a Landlock-qualified full-suite
   run of the JR-02/JR-03/JR-04/JR-05/JR-06 diff.
8. **Then:** JR-01/JR-25 architecture inventory, then JR-27 versioned
   question/policy catalog, then JR-15 first family (DF-01) and JR-14 adapter.
6. **Then:** JR-18 CI profiling and JR-19 prerequisite reproduction (offline, no
   spend).
7. **Then:** JR-12/JR-27 typed semantic contracts and catalog
   (design/implementation against a pinned contract; no live calls).
4. **Then:** JR-01/JR-25 architecture inventory and shared-predicate contracts
   (read-only discovery + additive planning).
5. **Then:** JR-18 CI profiling and JR-19 prerequisite reproduction (offline, no
   spend).
6. **Then:** JR-12/JR-27 typed semantic contracts and catalog
   (design/implementation against a pinned contract; no live calls).

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
- The documentation reconciliation (`docs-reconcile-2026-10-22`, small-change)
  is intentionally left uncommitted and not marked `done`: independent QA is
  open, and the recorded task base predates the uncommitted JR-02/JR-03/JR-04
  tool diff, so a `done` call would also correctly flag that out-of-scope
  delta until the control repairs are reviewed separately.
