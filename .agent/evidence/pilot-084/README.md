# Stage-4 coordination pilot evidence — feature 084 (phase 011 close)

Pilots the **NIP-0002 Stage 4 n-coordination layer** end-to-end with the phase-011 tooling
(features 080–083): a scratch **multi-repo** ecosystem of two projects stood up **from nothing**
by `bootstrap.sh --genesis` at one shared pin, iterated into an ecosystem-level aggregate, then
run through the **Plan → Promote** coordination chain — reconciliation to a dependency-ordered
plan, then admission into a release train — with **no hand-applied workaround**. Both members
(`member-alpha`, `member-beta`) were created by genesis itself from one ephemeral tag on the
phase-011 branch HEAD, so both carry the **same** framework pin. The members are ephemeral
(discarded); only these framework-side snapshots are committed.

## Outcome — the coordination layer runs from nothing; both gates enforced

| Step | Result | Evidence |
|---|---|---|
| **Genesis ×2** — two new projects from nothing at one shared pin | both stood up; each `provenance.json` records the same `resolved_sha` | `pilot_run.txt` |
| **Membership registry** — sets `n` | a 2-member `in_scope` registry authored over them; **validates** (`validate.sh --target`, C12) | `membership.json`, `registry_validate.txt` |
| **Aggregate** — the Stage-4 input substrate | `ecosystem_membership_run.py` iterated the set → **ecosystem_verdict PASS**, exit 0, `framework_pin_consistent true`, `member_count 2` | `membership_run.json`, `aggregate_run.txt` |
| **Plan stage (`H-PLANNING-AUTHORITY`)** — reconciliation | `ecosystem_reconcile.py` turned a packets input (with a cross-repo `depends_on` edge) into **plan_verdict PASS**, exit 0, topological `order` `[pkt-beta, pkt-alpha]`; **validates** as `reconciliation_plan` (C12) | `plan.json`, `reconcile_run.txt`, `plan_validate.txt` |
| **Promote stage (`H-TRAIN-ENTRY`)** — release train | `ecosystem_release_train.py --entry-gate-recorded` admitted the plan → **train_verdict PASS**, exit 0, `entry_gate_recorded true`, `train_members [member-alpha, member-beta]`; **validates** as `release_train_manifest` (C12) | `manifest.json`, `train_run.txt`, `manifest_validate.txt` |
| **Negative A — topological order *enforced*** | a cyclic packet set → reconcile correctly flipped to **plan_verdict FAIL**, exit 1, with a `cycle_findings` entry | `plan_cycle.json`, `reconcile_cycle_run.txt` |
| **Negative B — `H-TRAIN-ENTRY` *enforced*** | admitting the PASS plan **without** the recorded gate → release-train correctly refused a PASS: **train_verdict FAIL**, exit 1, `entry_gate_recorded false` | `manifest_ungated.json`, `train_ungated_run.txt` |

The coordination layer that phase 010 recorded as absent (`NDEBT-035`: the `04`/`05` protocols +
gates unauthored) now runs end-to-end: the phase-010 aggregate feeds a schema-valid,
dependency-ordered reconciliation plan, which feeds a schema-valid release-train manifest — and
the two load-bearing invariants are *enforced*, not cosmetic: a cyclic dependency set forces a
non-PASS plan (never a silent mis-order), and an ungated admission is refused a PASS train (the
`H-TRAIN-ENTRY` operator decision is required, never self-executed). Standing hermetic coverage is
`tools/e2e_bootstrap_test.sh` `assert_stage4` (feature 083).

## Gates

Both Stage-4 operator gates were recorded in `run_state` (event `operator_gate_decision`) **before
the acts they govern** (NDEBT-018): `H-PLANNING-AUTHORITY` before the reconciliation plan was
produced, `H-TRAIN-ENTRY` before the (gated) train manifest was emitted. As in the phases 007–010
pilots, this is a **pre-release / branch-HEAD pilot** (the phase-011 tooling is unreleased),
exercising each gate's decision mechanics against a **scratch** plan/train — **not** a real
cross-repository release. The negatives above prove the gates are enforced rather than assumed.

## What this does *not* prove

A **real, non-scratch multi-repo ecosystem** running the coordination layer at a **released** tag
remains the standing production-maturity criterion across the 0–n programme (`NDEBT-029` — the whole
loop is not yet in a released tag). This pilot exercises the Stage-4 *mechanics* against throwaway
members, not real multi-project maturity. The release cut, that real pilot, and the remaining
Repeat/GA protocols (`06`/`08`) are carried as phase-012 candidate scope in `docs/planning/ROADMAP.md`,
validated against this evidence.
