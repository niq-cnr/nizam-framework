---
id: nizam-backlog-reconciliation-2026-10-08
title: "Backlog Reconciliation — 2026-10-08 Maintainer Brief, Phase-014 Activation and the Candidate DAG"
description: "Human view of the 2026-10-08 backlog reconciliation: current state, discrepancies and their resolution, the crosswalk from the maintainer brief's aliases A00-A16, scenarios T01-T19 and NIP-0003 cases 1-13 to existing ids, the operator decision record, the candidate DAG view derived from docs/planning/backlog_dag.json, an ordering comparison, the verification matrix, and the outline of a separate Workflow Assurance NIP."
version: 0.1.4
status: active
authoritative_source: docs/planning/backlog_reconciliation.md
last_audited: "2026-10-09"
tags: [planning, backlog, reconciliation, dag, phase-014, nip-0003, workflow-assurance]
change_log:
  - version: "0.1.4"
    date: "2026-10-09"
    summary: "Planner record after feature 105 completed (.agent/qa/105.json pass; .agent/validator/105-mode-b.json approved). Section 5.1: the A07 row is marked delivered by F105, and its next action becomes none. NDEBT-042 is resolved in DEBT.md 0.51.0. Section 5.3 gains one note recording the open NIP3-115/NIP3-116 runtime_session registration question, carried from contract 105 design_notes.orchestrator_followups[2], for the NIP-0003 pre-acceptance revision. No other row changes; the A05 and A06 rows are not updated here."
  - version: "0.1.3"
    date: "2026-10-08"
    summary: "Evaluator follow-up. V11 of the DAG validator now admits exactly .agent/validator/phase-014-activation.json (the Validator's verdict on this package; an exact path, not a .agent/validator/ prefix) beside .agent/run_state.json. The Evaluator's .agent/evidence/phase-014-activation/eval/ files already fall under the package path. dag_negative_controls.py gains four V11 controls (accept the verdict, a later eval/ file and run_state; reject another .agent/validator/*.json, a prefix look-alike, and a payload edit): 14/14. Nit fixed: 'four kinds of test'."
  - version: "0.1.2"
    date: "2026-10-08"
    summary: "Validator round-2 corrections. 102 AT5 (the NDEBT-044 e open-debt roll) is approved-tranche coverage under the 11:21:14Z decision. The remaining Planner hardening (099 AT3/AT6/AT7, 101 AT2, 102 AT2/AT3/AT7) was acknowledged by the operator, verbatim 'acknowledged.' (run_state operator_gate_decision 2026-10-08T13:20:12Z). Spec references updated to 1.1.2. D-20 records the round."
  - version: "0.1.1"
    date: "2026-10-08"
    summary: "Validator round-1 corrections. (1) The run_state position landed at 2026-10-08T12:18:31Z (014-ga-track / 099 / in_progress): ACT-014 is complete, and the ready set is {F099}, the head of the single lane, with F103/F105/F106/F107/F109 dependency-eligible but lane-ordered. (2) The scope budget 6660/8658 is the Planner's activation-time estimate (naive 2890 x the measured 2.3 process weight, NIP-0003:494-495), approved by the operator verbatim 'In approve the increased budget.' (run_state operator_gate_decision 2026-10-08T12:50:31Z). (3) The 102 machine-readable dossier, its DEBT.md cross-check, the open-debt roll and the hash pin are marked as Planner hardening beyond the enumerated approval, pending operator acknowledgment [0.1.2: the open-debt roll reclassified as approved-tranche coverage; the rest acknowledged at 13:20:12Z]. (4) The probes cover every acceptance test (revision 3), and an acceptance-test compile check is added. (5) NDEBT-045 added to the debt table. (6) D-19 records the round."
  - version: "0.1.0"
    date: "2026-10-08"
    summary: "Initial reconciliation package, authored by the Planner in the main working tree (branch phase/014-ga-track, base 02b02c6) after re-checking the stopped agent's unreviewed draft (worktree branch chore/backlog-reconciliation at 9edd5d0; not edited). Records the H-PHASE-014 activation with the approved amendments and the maintenance-tranche fold (features 103-109), the crosswalk, the decision record, the candidate DAG view, an ordering comparison, the T/NIP verification matrix with honest statuses, and the Workflow Assurance NIP outline (not authored; final design waits for feature 101). Machine-readable companion: docs/planning/backlog_dag.json."
---

# Backlog Reconciliation — 2026-10-08

## 1. Purpose and authority

On 2026-10-08 the operator gave a maintainer brief. It asked for the backlog to be
reconciled, for workflow assurance to be designed, for NIP-0003 to be extended rather
than replaced, and for an atomic DAG in the framework's existing formats, executing
only what is authorized. The brief's aliases `A00`–`A16` and scenarios `T01`–`T19` are
planning labels, not feature ids.

**The brief itself is not a repository artifact.** The meaning of each alias below is
carried from the re-checked draft crosswalk, and each scenario is identified by its
proof obligation.

This document is the human view. `docs/planning/backlog_dag.json` is the
machine-readable view, and the two must agree; the DAG validator checks that this file
names every packet, alias and scenario.

**Canonical plans win.** The phase-014 packets mirror `.agent/feature_list_014.json`
(spec 1.1.2) and `docs/planning/phase_014.yaml`. Everything after phase 014 is a
**candidate** until its own `H-NIP` / `H-PHASE-NNN` gate.

## 2. Current state (base `02b02c6`, plus this package)

**The base commit.** `main` is at `02b02c6`; PR #64 merged at 2026-10-08T11:16:42Z.
It holds the v1.4.0 post-release refresh and the D1 re-baseline of the then-pending
phase 014.

**The release.** v1.4.0 is RELEASED. The annotated tag object is `bb32064`, at
`9edd5d0`. Release truth (alias `A02`) was settled by PR #64.

**Re-verified at `02b02c6`** (`.agent/evidence/backlog-reconciliation-2026-10-08/recheck-02b02c6/`):

| Check | Result |
|-------|--------|
| `bash tools/validate.sh` | 16/16, exit 0 |
| `--payload` | 12/12, exit 0 |
| `bash tools/fixtures_self_test.sh` | 79/79, exit 0 |
| `release_closeout.py --mode pr` | exit 0 at V=1.4.0 |
| `python3 tools/test_convergent_review.py` | 54 tests, 5 FAIL, exit 1 |

The convergent-review failures are `NDEBT-043`. This host sets
`kernel.apparmor_restrict_unprivileged_userns = 1`, and `unshare --user` is denied. The
9edd5d0 baseline (`baseline/`, copied from the draft) also records the tag-mode
close-out and the e2e run, both passing.

**CI coverage.** `.github/workflows/compliance.yml` declares the jobs `validate`,
`e2e_bootstrap` and `fixtures_self_test`. None runs the convergent suite
(`NDEBT-041`).

**Phase 014 is ACTIVATED** (`H-PHASE-014`, Section 4):

- `.agent/product_spec_014.md` is 1.1.2 and `active`.
- `.agent/feature_list_014.json` holds eleven features: 099–109, then 100, 101, 102.
- `docs/planning/phase_014.yaml` is `in_progress`.
- The manifest's `current_phase` is `014-ga-track`.
- The derived `.agent/run_state.json` position landed at 2026-10-08T12:18:31Z. It was
  the Orchestrator's third, canonical-first write (`phase_activated`):
  `current_phase` `014-ga-track`, `current_feature` `099`, `status` `in_progress`.
- **The scope budget is approved.** `original_estimate_lines` is 6660 and the ceiling
  is 8658. The figure is the Planner's activation-time estimate: naive 2890 × the
  measured 2.3 process weight (NIP-0003:494-495). The operator approved it verbatim,
  "In approve the increased budget.", recorded as `operator_gate_decision` at
  2026-10-08T12:50:31Z.

**Acceptance infrastructure is frozen** at `.agent/evidence/phase-014-activation/`. It
holds the baselines (tag set, `.agent/audits` listing, validator check ids) and the
gates `validator_gate.py`, `scratch_run.py` and `phase_tag_check.py`. All seven files
are sha256-pinned by feature 102 AT7.

**Acceptance-test provenance.** Each feature's `acceptance_provenance` separates four
kinds of test:

- tests implementing the operator's enumerated amendment list;
- approved-tranche coverage under the same decision: 102 AT5, the NDEBT-044 (e)
  open-debt roll;
- **Planner hardening beyond that list, operator-acknowledged 2026-10-08T13:20:12Z
  ("acknowledged."):**
  - 102's machine-readable GA-readiness dossier (AT2) and its `DEBT.md` cross-check
    (AT3);
  - the hash pin (AT7);
  - 099 AT3/AT6/AT7;
  - 101 AT2;
- new-feature design (103–109).

## 3. Discrepancies and their resolution

| # | Discrepancy (verified) | Resolution |
|---|------------------------|------------|
| D-01 | The draft DAG sat in a worktree at `9edd5d0`, but its wrapper already claimed base `02b02c6`, and it was unreviewed. | RESOLVED. Re-checked and rebuilt in the main tree; the worktree is untouched (`.agent/evidence/backlog-reconciliation-2026-10-08/dag_recheck.md`). |
| D-02 | Draft probes: 2 of 48 rows stale after PR #64. P5 expected the pre-D1 `v1.4.0` literal to be current, and expected the v1.4.0 release decision to be unmerged. | CORRECTED. The probes are rewritten to read the written acceptance tests from the feature list and the old forms from git (revision 2: 88/88 rows; revision 3 covers every test). |
| D-03 | Draft validator V10 crashed (`FileNotFoundError`) when the human view was missing, instead of failing. | CORRECTED (V10 now FAILs). |
| D-04 | Draft V11 asserted that "no existing file modified", which the approved amendment necessarily violates. | CORRECTED. V11 now confines the package to its declared paths. |
| D-05 | Draft V7 accepted declared *proposed* edges; after activation the DAG must *mirror* the canonical plan. | CORRECTED. V7 now requires equality of dependencies, status and estimate; V12 and V13 are new. |
| D-06 | T06 and T18 cited `a02_premise_probes.txt`, which was never captured. | RESOLVED (captured, §5 shape). |
| D-07 | V9: `docs/planning/ROADMAP.md` writers A03-RT and F102 were unordered. Later, `tools/validate.sh` writers NIP3-119, A11-D and A10 were unordered as well. | RESOLVED. A03-RT now follows F102; WA implementation (A09) follows NIP3-120 as the candidate order. |
| D-08 | The draft's proposed tag check permitted "authorized" new tags. The approved amendment says no tag is created during the phase. | CORRECTED. `phase_tag_check.py` compares against the activation tag set and allows only the harness's ephemeral `e2e-*` namespace. |
| D-09 | 102 AT1 called `json.load` without `import json` (`NameError` on every input). | FIXED in spec 1.1.0 (probe P4). |
| D-10 | The old 099 AT5 OR-grep is satisfied by a mere *mention*. It false-passes on the real file now that Section 1 of `operator_gates.md` mentions both gates in the H-PHASE-014 record. | FIXED. Per-gate DEFINED row plus removal from Section 2 (probe P3). |
| D-11 | `ecosystem/00_ecosystem_bootstrap.md` is a `tools/skill.json` capability (since feature 060) with no `NIZAM.json` capability entry. | SCHEDULED: F106 (NDEBT-044 a). |
| D-12 | `standard/capability_profiles.md` §2 has no Role column, so NDEBT-026's "parse the mapping" has nothing to parse. | DESIGNED: F109 (an additive column and a new primitive; the old primitive is unchanged). |
| D-13 | NIP-0001 and NIP-0003 fail C9 under `--target`, because proposals cite future paths. Adding `docs/nips/` to the shipped-doc set would break C9/C10. | CONSTRAINT recorded on F107 (C1/C2 only). |
| D-14 | Several NIP-0003 premises are stale: provisional ids 103–113 collide with phase 014; feature 109's claim map is pulled forward; "four jobs" becomes five after F104; the `--require-isolation` polarity diverges from F103; it cites `.agent/product_spec_014.md:82-83` "excludes schema and workflow changes"; its release expectations say "v1.4.0/v1.5.0"; it says SBCL is "not installed" (now `/usr/bin/sbcl`, 2.2.9.debian). | QUEUED: A03-RT, after F102. ROADMAP note added; the NIP is not edited. |
| D-15 | The ROADMAP Current Position open-debt bullet says "two rows", at DEBT.md v0.40.0; eight rows are Open (NDEBT-044 e). | SCHEDULED: F102 AT5 (a derived check against the DEBT.md Open table). |
| D-16 | `schema/phase.schema.json` steps are closed (`id`, `description`, `status`, `evidence`, `docs_updated`, `changelog_entry`). The Planner template's per-step `title` / `verification_method` cannot be added. | RESOLVED. Schema-valid steps; per-feature verification lives in the feature list's executable tests. |
| D-17 | Spec 1.0.x said run_state is "untouched until activation", while the D1 and H-PHASE-014 decisions were appended before activation. | CLARIFIED in spec 1.1.0 (coordination fields untouched; decision records required by NDEBT-018). |
| D-18 | The NDEBT-042 row's facts (line 949, `-maxdepth 1`; 79 top-level files, 67 nested). | VERIFIED true at `02b02c6`; no discrepancy. |
| D-19 | Validator round 1 rejected the 1.1.0 package. Its findings: an overclaimed probe coverage; the 102 dossier labelled as approved; the ×2.3 basis called "operator-directed"; stale run_state records; whole-file greps; a bare-rc 109 test; unspecified CI evidence; no capable-host obligation for 103; no C2 control for 107; an empty-findings pass for 101; and no guard for the frozen infrastructure. | CORRECTED in spec 1.1.1. Each item maps to its fix in the Planner's round-1 report. |
| D-20 | Validator round 2 found three issues. 102 AT5 was mislabelled as Planner hardening, although it implements approved tranche scope. The spec's 102 bullet was garbled and carried an unverifiable statement about the Orchestrator's brief. Some "spec 1.1.0" references were stale. | CORRECTED in spec 1.1.2. AT5 is approved-tranche coverage. The rest of the hardening was operator-acknowledged at 13:20:12Z, so no decline fallback is needed. |

## 4. Decision record (verbatim)

1. **Operator gate decision, 2026-10-08.** Recorded by the Orchestrator in
   `.agent/run_state.json` as `operator_gate_decision` at 2026-10-08T11:21:14Z,
   before the re-planning:

   > - H-PHASE-014. Activate Phase 014 with the proposed amendments, Approved. - Maintenance tranche, fold them into Phase 014, Approved.

2. **Operator instruction about prior work:**

   > reuse the partial DAG only after re-checking it.

   Honoured as recorded in
   `.agent/evidence/backlog-reconciliation-2026-10-08/dag_recheck.md`: what was kept,
   corrected or dropped, with the draft's own re-run outputs.

**What these decisions do not authorize:**

- `H-CONSUMER-UPGRADE` for any real consumer. Feature 100's member set is still an
  operator decision.
- `H-NIP` (NIP-0003, or the future Workflow Assurance NIP).
- `H-CONSOLIDATION`, `H-GA`, or any release.

## 5. Crosswalk

### 5.1 Aliases A00–A16

| Alias | Meaning (brief) | Maps to | Disposition | Required authority | Depends on | Owner | Next action |
|-------|-----------------|---------|-------------|--------------------|------------|-------|-------------|
| `A00` | Baseline and authority inventory | `A00` | Satisfied (captured at 9edd5d0, re-verified at 02b02c6) | none | — | Orchestrator | none |
| `A01` | Crosswalk + candidate DAG | `A01` (this package) | Satisfied | Orchestrator delegation | `A00` | Planner | Review by Validator/Evaluator |
| `A02` | Release truth + phase-014 amendment | `R3` (PR #64, D1), `A02-AMEND` | Satisfied | H-FRAMEWORK-RELEASE (executed), D1, H-PHASE-014 | `A01`, `R3` | Orchestrator / Planner | none |
| `A03` | Design split: NIP-0003 extension vs separate proposal | `A03-SCOPE`, `A03-RT`, `A03-WA-DRAFT`, `A03-WA-FINAL`, `PLAN-WA` | New gap, split (§7) | Planner drafting; H-NIP to accept | `A01`; F101 for the final | Planner | Draft the WA NIP (parallel-safe); revise NIP-0003 after F102 |
| `A04` | Role/test ownership, Evaluator acceptance bundle | `A04a` (text), `A04b` (behavior) | Extend existing (01_execution already has Loop-1 Evaluator review) | A04a: phase selection; A04b: WA H-NIP + H-PHASE-NNN | `PLAN-NEXT`; `PLAN-WA` + `A09` | Generator | none until selected |
| `A05` | Sandbox prerequisites | `F103` (NDEBT-043) | Scheduled, phase 014 | H-PHASE-014 (satisfied) | `ACT-014` | Generator | Contract after 099 |
| `A06` | Convergent suite enforced in CI | `F104` (NDEBT-041) | Scheduled, phase 014 | H-PHASE-014 (satisfied) | `F103` | Generator | Contract after 103 |
| `A07` | Nested fixture ownership | `F105` (NDEBT-042; NIP-0003 109 claim map pulled forward) | Delivered (105), phase 014; NDEBT-042 resolved (DEBT.md 0.51.0) | H-PHASE-014 (satisfied) | `ACT-014` | Generator | none |
| `A08` | Drift bundle | `F106` (044a), `F107` (044b), `F108` (037 + 044c/d/f), `F109` (026), `F102` (044e) | Scheduled, phase 014, split by concern | H-PHASE-014 (satisfied) | 108 after 106, 107, 109 | Generator | Contracts in lane order |
| `A09` | Candidate/contract/verification identity (+ NDEBT-040) | `A09` | New gap (WA NIP) | WA H-NIP + H-PHASE-NNN | `PLAN-WA` | Generator | Outline only (§7) |
| `A10` | Deterministic gate enforcement, idempotent recovery | `A10` | New gap (WA NIP) | WA H-NIP + H-PHASE-NNN | `A09` | Generator | Outline only |
| `A11` | Convergent finding → AGF verdict mapping | `A11-D`, `A11-CI` | New gap (WA NIP) | WA H-NIP + H-PHASE-NNN | `A09`; `F104` | Generator | Outline only |
| `A12` | NIP-0003 normative surface | `NIP3-110`..`NIP3-114` (provisional; were 103–107), `PLAN-NEXT`, `A03-RT` | Extend existing | H-NIP, then H-PHASE-015 | `F102` | Planner / Generator | Wait for phase-014 close |
| `A13` | NIP-0003 runtime controller + live conformance | `NIP3-115`..`NIP3-120` (were 108–113), `PLAN-016` | Extend existing | H-NIP, then H-PHASE-016 | `NIP3-114` | Planner / Generator | Wait |
| `A14` | Cause-based failure routing | `A14` | New gap (WA NIP; needs NIP3-110's attempt definition) | WA H-NIP + H-PHASE-NNN | `PLAN-WA`, `NIP3-110` | Generator | Outline only |
| `A15` | Risk profiles with preregistered evaluation | `A15` | Deferred until the gates are trusted | WA H-NIP + H-PHASE-NNN | `A10`, `A11-CI` | Generator | Outline only |
| `A16` | Dogfood, documentation truth, readiness | `F102`, `NIP3-114`, `NIP3-120`, `A16-WA` | Extend existing | per owning phase | per packet | Generator | F102 in phase 014 |

### 5.2 Debt rows

| Row | Severity | Disposition (DEBT.md v0.48.0) |
|-----|----------|-------------------------------|
| NDEBT-043 | Low | F103 |
| NDEBT-041 | Medium | F104, after F103 |
| NDEBT-042 | Low | F105 (claim map reused from the NIP-0003 design) |
| NDEBT-044 | Low | Split: F106 (a), F107 (b), F108 (c, d, f), F102 (e) |
| NDEBT-037 | Low | F108 |
| NDEBT-026 | Low | F109 |
| NDEBT-040 | Low | Annotated as a WA NIP candidate (A09); stays Open |
| NDEBT-034 | Low | Deferred (phase-014 non-goal) |
| NDEBT-045 | Low | New 2026-10-08: the `--payload` help paragraph misstates the payload. Not scheduled; outside 108's scope. |

### 5.3 NIP-0003 features (provisional ids shift by seven)

Phase 014 allocated 103–109. NIP-0003's provisional features therefore shift. The
new numbers are confirmed only at phase-015 planning (`PLAN-NEXT`).

| NIP-0003 id | Shifted to | Packet | Phase |
|-------------|------------|--------|-------|
| 103 | 110 | `NIP3-110` | 015 |
| 104 | 111 | `NIP3-111` | 015 |
| 105 | 112 | `NIP3-112` | 015 |
| 106 | 113 | `NIP3-113` | 015 |
| 107 | 114 | `NIP3-114` | 015 |
| 108 | 115 | `NIP3-115` | 016 |
| 109 | 116 | `NIP3-116` | 016 |
| 110 | 117 | `NIP3-117` | 016 |
| 111 | 118 | `NIP3-118` | 016 |
| 112 | 119 | `NIP3-119` | 016 |
| 113 | 120 | `NIP3-120` | 016 |

Notes on individual features:

- **NIP3-113** (was 106) no longer carries the NDEBT-044 (d) fix; that moves to F108.
- **NIP3-116** (was 109) reuses F105's claim map and F104's CI job.
- **NIP3-115 / NIP3-116 registration (open; for the NIP-0003 pre-acceptance revision).** The runtime_session fixture subdirectory first appears in NIP3-115 (was 108), but the spec has NIP3-116 (was 109) register it in F105's claim map; because an unclaimed subdirectory fails the self-test, the revision must put the registration row in the same change that creates the directory (contract 105 `design_notes.orchestrator_followups[2]`).

NIP-0003 acceptance cases 1–13 map to these packets in §8.

### 5.4 Gates

| Gate | State | Bound to |
|------|-------|----------|
| `H-PHASE-014` | SATISFIED 2026-10-08 | `ACT-014` |
| `H-CONSUMER-UPGRADE` | OUTSTANDING, per real member | `F100` |
| `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` | Only if F100 builds a plan or train | `F100` |
| `H-CONSOLIDATION` / `H-GA` | Defined by F099; never exercised in phase 014 | `F099`, `F101`, `F102` |
| `H-NIP` | NIP-0003 outstanding; WA NIP not yet authored | `PLAN-NEXT`, `PLAN-016`, `PLAN-WA` |
| `H-PHASE-015` / `H-PHASE-016` | Future | `NIP3-110`..`NIP3-120` |
| `H-FRAMEWORK-RELEASE` | Not in phase-014 scope | — |

## 6. Candidate DAG view (derived from `backlog_dag.json`)

**The DAG.** 43 packets. It is acyclic over `depends_on` plus `serialize_after`.
Every phase-014 packet mirrors the canonical feature list.

**Complete.** `ACT-014`: the run_state position landed at 2026-10-08T12:18:31Z.

**Ready set: {`F099`}.** All its prerequisites are met, its dependencies are complete,
and it heads the single lane.

**Dependency-eligible, waiting only on lane order** (`serialize_after`): `F103`, `F105`,
`F106`, `F107`, `F109`.

- `F103`'s tests are host-conditional. This host proves the UNSUPPORTED half; the
  capable-host half is discharged by 104's CI evidence.

**Near-ready** (authorized; waiting only on in-flight technical or evidence events):

- `F108`: waits on `F106`, `F107` and `F109`.
- `F101`: waits on `F099`, `F100` and the pilot evidence.
- `F102`: waits on all of 099–101 and 103–109.
- `A03-WA-DRAFT`: needs Orchestrator review of this package.
- `A03-WA-FINAL`: waits on `F101`'s findings.

**Blocked, with causes:**

| Packet(s) | Cause |
|-----------|-------|
| `F100` | **Authority:** per-member `H-CONSUMER-UPGRADE` is OUTSTANDING. **Environment:** the operator has not designated the real member repositories. |
| `F104` | **Environment:** UNVERIFIED whether hosted ubuntu runners permit the guarded userns step. It is also technically behind `F103`. A required-mode failure escalates; it never weakens the mode. |
| `A03-RT` | Proposal. Orchestrator scheduling after `F102`; this package was forbidden to edit the NIP. |
| `PLAN-NEXT`, `PLAN-016`, `PLAN-WA` | `H-NIP` |
| `NIP3-110`..`NIP3-114` | `H-PHASE-015` |
| `NIP3-115`..`NIP3-120` | `H-PHASE-016`. `NIP3-116`..`NIP3-118` also have environment items: the CI userns step, and SBCL in CI. |
| `A04a` | Phase selection at `PLAN-NEXT` |
| `A09`, `A10`, `A11-D`, `A11-CI`, `A04b`, `A14`, `A15`, `A16-WA` | WA NIP acceptance plus phase activation |

**Critical paths:**

- **Phase 014** (canonical dependencies): `ACT-014` → `F100` → `F101` → `F102`.
  Its pace is set by the operator's member designation and the `H-CONSUMER-UPGRADE`
  decisions, not by line counts.
- **Whole backlog** (technical; weighted-line midpoint; gate turnaround excluded,
  because it is unknown): `A00` → `A01` → `A02-AMEND` → `ACT-014` → `F100` → `F101` →
  `F102` → `PLAN-NEXT` → `NIP3-110` → … → `NIP3-114` → `PLAN-016` → `NIP3-115` → … →
  `NIP3-120`. That is about 21,250–27,560 weighted lines.

**Phase-014 single-lane order** (the canonical list order, and the Dependency
Enforcement Rule's selection order): `F099` → `F103` → `F104` → `F105` → `F106` →
`F107` → `F109` → `F108` → `F100` → `F101` → `F102`. **The first eligible feature is
099.**

**After phase 014** (single writer, candidate): `A03-RT` → `PLAN-NEXT` → `A04a` →
`NIP3-110`..`NIP3-114` → `PLAN-WA` → `PLAN-016` → `NIP3-115`..`NIP3-120` → `A09` →
`A11-D` → `A10` → `A11-CI` → `A04b` → `A14` → `A16-WA` → `A15`.

- **The parallel-safe lane:** `A03-WA-DRAFT` (new files only).
- **Open, non-blocking question:** whether WA implementation (`A09`…) precedes
  NIP-0003 phase 016 or follows it. The candidate encodes "follows", matching the
  operator's sequencing of NIP-0003 directly after phase 014.

**Scope budget** (phase 014, canonical):

- the Planner's activation-time estimate, naive 2890 × the measured 2.3 process weight
  (NIP-0003:494-495) = `original_estimate_lines` **6660**;
- approved by the operator, verbatim "In approve the increased budget."
  (`operator_gate_decision` 2026-10-08T12:50:31Z);
- 130 percent ceiling **8658**;
- at phase 013's realized 2.89× the projection is about 8352, under the ceiling.

### 6.1 Ordering comparison

| | **Recommended:** 099 → 103–109 → 100 → 101 → 102 | **Alternative:** 099 → 100 → 101 → 103–109 → 102 |
|---|---|---|
| Lane utilization | Starts with seven features that need no outstanding operator decision. The lane never idles while members are designated. | Stalls at 100 until the operator designates members and records each `H-CONSUMER-UPGRADE`. |
| Real-pilot evidence | Arrives later. | Arrives earliest, and the long pole starts first. |
| 101 review subject | Reviews the surface after the tranche, including the new CI job, claim map and C13/C15 changes. | Reviews a surface that 103–109 then change; part of the review is stale on arrival (the `ecosystem/06` §2 "moving surface" concern). |
| Enforcement debt | NDEBT-041 (Medium) is closed early, so later phase-014 merges run the convergent gate in CI. | NDEBT-041 stays open through the pilot and the review. |
| Flexibility | If members are designated early, 100 can be moved up by a recorded amendment, because 100's dependencies allow it. | — |

**Recommendation: the first order**, now encoded as the canonical list order. The
alternative wins only if real-pilot evidence is wanted before anything else, and
neither decision record says it is.

## 7. Outline — a separate Workflow Assurance NIP (not authored)

**Status: an outline only.** No NIP file is created by this package. The final design
waits for feature 101's simplification-review findings and any `H-CONSOLIDATION`
decision (`A03-WA-FINAL`). Provisional label: NIP-0004. Owner: Planner (`A03-WA-DRAFT`
to draft; `H-NIP` to accept; `PLAN-WA` to plan).

**Why it is separate from NIP-0003.** NIP-0003 governs live runtime sessions: one
worktree, one runtime image. The items below govern the workflow itself: identity,
gates, verdicts, routing and risk. They apply with or without a runtime session.
Extending NIP-0003 with them would couple two acceptance decisions.

Each A03-family item has exactly one owner:

| Item | Owner proposal | Content (outline) |
|------|----------------|-------------------|
| `A09` | WA NIP | Candidate / contract / verification / policy / environment identity; owned-field (parsed-JSON) comparison for coordination files, generalizing the NDEBT-040 adjudication; explicit invalidation rules; trusted-runner assumptions; non-circular candidate identity. |
| `A10` | WA NIP | Deterministic gate enforcement and idempotent recovery, reusing `tools/validate.sh`, `tools/verify_lib.sh` and the schemas; no second scheduler. Phase 014's frozen `validator_gate.py` / `scratch_run.py` are a working precedent to evaluate. |
| `A11` | WA NIP | Convergent finding → AGF verdict mapping: blocking vs advisory minor, preserving the empty-array rule of the JSON Verdict Parse Rule; CI acceptance inside F104's job. |
| `A04` (b) | WA NIP | Development vs acceptance test ownership; a frozen Evaluator acceptance bundle; bounded handoff records. `A04a` (role-text fix) is not WA-owned; it is a doc fix for the next selected phase. |
| `A14` | WA NIP | Cause-based diagnostic routing replacing the forced `methodology/03_circuit_breaker.md` §2 strategy ladder, after authorized activation; depends on NIP-0003's attempt definition (`NIP3-110`). |
| `A15` | WA NIP | Routine / Standard / High-assurance profiles: applicability checks, a preregistered shadow comparison, outcome records, and a promotion recommendation (never activation). Deferred until A10/A11 are trusted. |
| NIP-0003 extensions | NIP-0003 (A03-RT) | Attempt continuity (declared-negative outcomes; probe vs governed attempt; cross-stage budget) in `NIP3-110`; the id shift; claim-map reuse; the job count; isolation-flag polarity; stale citations. |

**Every changed rule in the WA NIP must carry** an owner, a rationale, a transition
plan, acceptance evidence (the T-scenarios in §8), and an activation boundary (never
active before its versioned authorization). **Release impact:** MINOR or MAJOR,
depending on whether any required field changes. The NIP itself must assess this,
under `methodology/06_release_train.md` §3.

## 8. Verification matrix (honest statuses)

Statuses are `pending` (no evidence yet), `partially-evidenced` (some evidence exists,
and the remaining proof is named) or `satisfied`. **None is `satisfied` today.**

| Scenario | Proof obligation | Owners | Status | Evidence / remaining |
|----------|------------------|--------|--------|----------------------|
| `T01` | `validate.sh --payload` + e2e + `interface.md` §5 item count | `F104`, `NIP3-111`, `NIP3-113`, `A16-WA` | partially-evidenced | 9edd5d0 payload 12/12 and e2e PASS; the combined-candidate run remains. |
| `T02` | A proposed phase/NIP stays pending/draft; activation is recorded before any contract | `ACT-014`, `A10` | partially-evidenced | The H-PHASE-014 event (11:21:14Z) precedes every phase-014 contract (none exists). A mechanized check (A10) remains. |
| `T03` | Invalidation-matrix tests | `A09`, `A10` | pending | — |
| `T04` | Cross-candidate evidence replay rejected | `A09`, `A10` | pending | — |
| `T05` | Parsed-JSON owned-field comparison; NDEBT-040 controls | `A09` | partially-evidenced | One manual positive adjudication (feature 093 QA). No mechanized negative control. |
| `T06` | Exit-captured checks; synthetic optimistic-report control | `A02-AMEND`, `A10`, `F103` | partially-evidenced | `a02_premise_probes.txt` P2: the gate rejects a validator that prints 16/16 but exits 1. Generalization (A10) remains. |
| `T07` | External-anchor acceptance vs stubbed behavior | `A04b`, `A10` | pending | — |
| `T08` | Unsupported-not-passing on a restricted host; executes on an available host | `F103`, `NIP3-116` | partially-evidenced | Today the restricted host is non-passing (5 FAIL), but it is misreported as FAIL, not UNSUPPORTED. F103 fixes this; F104 supplies the available-host run. |
| `T09` | CI job + deliberate regression fails it; nested claim map | `F104`, `F105` | pending | — |
| `T10` | An advisory minor stays visible; blockers cannot be outvoted | `A11-D`, `A11-CI` | pending | — |
| `T11` | Route-per-cause tests | `A14`, `A04b` | pending | — |
| `T12` | Attempt continuity across restart/rename/stage (NIP case 9) | `NIP3-110`, `NIP3-115`, `A14` | pending | — |
| `T13` | NIP cases 1, 3, 8, 13 live | `NIP3-111`, `NIP3-115` | pending | — |
| `T14` | NIP cases 4, 5, 6 live | `NIP3-115`, `NIP3-117` | pending | — |
| `T15` | NIP cases 7, 11, 12 live + ASDF no-op/failing controls | `NIP3-118` | pending | — |
| `T16` | Misclassification controls | `A15` | pending | — |
| `T17` | Integration on the combined candidate | `A16-WA`, `NIP3-119`, `F102` | partially-evidenced | 9edd5d0 e2e chain PASS; the combined run remains. |
| `T18` | Real-member + per-member gate ordering; release vs activation vs GA | `F100`, `F102`, `A02-AMEND` | partially-evidenced | Probes P5, P6 and P8 prove the tests discriminate; no real pilot evidence yet. |
| `T19` | Frozen acceptance-bundle identity vs candidate identity | `A04b`, `A09`, `NIP3-118` | pending | — |

**NIP-0003 cases.** Each case needs a phase-015 schema fixture where possible, and a
phase-016 live proof in CI. All are pending.

| Case | Owners | Status |
|------|--------|--------|
| `NIP-1` | `NIP3-111`, `NIP3-115` | pending |
| `NIP-2` | `NIP3-115` | pending |
| `NIP-3` | `NIP3-111`, `NIP3-115` | pending |
| `NIP-4` | `NIP3-111`, `NIP3-117` | pending |
| `NIP-5` | `NIP3-111`, `NIP3-115`, `NIP3-117` | pending |
| `NIP-6` | `NIP3-111`, `NIP3-115`, `NIP3-117` | pending |
| `NIP-7` | `NIP3-111`, `NIP3-118` | pending |
| `NIP-8` | `NIP3-111`, `NIP3-115`, `NIP3-116` | pending |
| `NIP-9` | `NIP3-110`, `NIP3-115` | pending |
| `NIP-10` | `NIP3-111`, `NIP3-115`, `NIP3-117` | pending |
| `NIP-11` | `NIP3-111`, `NIP3-118` | pending |
| `NIP-12` | `NIP3-118` | pending |
| `NIP-13` | `NIP3-111`, `NIP3-115` | pending |

## 9. Evidence and replay

All evidence lives under `.agent/evidence/backlog-reconciliation-2026-10-08/`. Every
command below is replayable from the repository root.

| Path | Content |
|------|---------|
| `baseline/*.txt` | 9edd5d0 captures, copied verbatim from the draft. |
| `recheck-02b02c6/*.txt` | Fresh captures in a clean clone at `02b02c6`. |
| `dag_recheck.md` | What was kept, corrected or dropped from the draft, with the draft scripts' own re-run outputs. |
| `tools/validate_backlog_dag.py` | DAG validator, revision 2. |
| `tools/a02_premise_probes.py` | Probes, revision 2. |
| `dag_validation.txt` | DAG validation, in the `04` §5 shape. |
| `tools/dag_negative_controls.py` + `dag_negative_controls.txt` | Fourteen controls. Ten mutated DAGs each fail their targeted check. Four V11 confinement controls feed a recorded git-status text: one is accepted (the Validator's exact verdict path, a later `eval/` file and run_state); three are rejected (another `.agent/validator/*.json`, a prefix look-alike, a payload edit). The unmutated copy passes. |
| `a02_premise_probes.txt` | Revision 3: a sweep of every acceptance test against the pre-implementation tree, plus P1–P20 discriminating controls; 255/255 rows; `04` §5 shape. |
| `tools/at_compile_check.py` + `at_compile_check.txt` | `bash -n` of every acceptance test, plus `compile()` of every embedded Python body. |

Activation baselines and gates are in `.agent/evidence/phase-014-activation/`.
