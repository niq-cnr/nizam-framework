# n-case pilot evidence — feature 079 (phase 010 close)

Pilots the **n-case (many associated repositories forming one ecosystem)** end-to-end with the
phase-010 tooling (features 075–078): a scratch **multi-repo** ecosystem of three projects stood
up **from nothing** by `bootstrap.sh --genesis`, declared in a schema-validated membership
registry, then iterated + aggregated with **no hand-applied workaround**. Each member
(`member-alpha`, `member-beta`, `member-gamma`) was created by genesis itself — `git init` + the
deterministic scaffold + the injected `.nizam/` payload — from one ephemeral tag on the phase-010
branch HEAD, so all three carry the **same** framework pin. The members are ephemeral (discarded);
only these framework-side snapshots are committed.

## Outcome — the n-case runs from nothing, consistency enforced

| Step | Result | Evidence |
|---|---|---|
| **Genesis ×3** — three new projects from nothing at one shared pin | all three stood up (scaffold + injected `.nizam/`); each `provenance.json` records the same `resolved_sha` | `pilot_run.txt` |
| **Membership registry** — the artifact that sets `n` | a 3-member `in_scope` registry authored over them | `membership.json` |
| **Registry validation** — required + schema-backed | **PASS** — `validate.sh --target` (C12) accepts the registry shape + exactly-one-list invariant | `registry_validate.txt` |
| **Iteration + aggregation** — the n-case run | `ecosystem_membership_run.py` ran Preflight per member and rolled the verdicts up; **ecosystem_verdict PASS**, exit 0, `framework_pin_consistent true`, `member_count 3`, no findings | `membership_run.json`, `ecosystem_run.txt` |
| **Aggregate validation** — a produced, schema-valid result | **PASS** — `validate.sh --target` (C12) accepts `membership_run.json` as an ecosystem-level result | `result_validate.txt` |
| **Consistency is *enforced*, not silent** (negative) | one member's pin was tampered to diverge → the next run correctly flipped to **ecosystem_verdict FAIL**, exit 1, `framework_pin_consistent false`, with a first-class `consistency_findings` entry naming the divergence | `membership_run_divergent.json`, `ecosystem_run_divergent.txt` |

The n-case that phase 008 recorded as absent (`NDEBT-031`: single-`--repo-root` tools, no required
membership artifact) now runs end-to-end: a schema-validated registry declares the set, the tooling
iterates the `in_scope` repo-roots, and a correct schema-valid aggregate ecosystem-level result is
produced — and a divergent framework pin across members surfaces as a flagged finding that forces
the ecosystem verdict to FAIL, never a silent mismatch. Standing hermetic coverage is
`tools/e2e_bootstrap_test.sh` `assert_multirepo` (feature 078).

## Gate

The `H-CONSUMER-UPGRADE` gate was recorded in `run_state` before any genesis bootstrap ran
(NDEBT-018), covering all three pilot members. As in the phases 007–009 pilots, this is a
**pre-release / branch-HEAD pilot** (the phase-010 tooling is unreleased), exercising the gate's
decision mechanics — **not** a released-immutable-tag adoption.

## Residual friction (new debt)

- **NDEBT-034 (Low)** — the pilot cost scales linearly with member count: `bootstrap.sh --genesis`
  does a full `file://` clone per member, so the 3-member inline run exceeded a 2-minute budget and
  had to be backgrounded. A throughput optimisation (a shared clone cache / lighter re-inject), not
  a correctness gap.

## What this does *not* prove

A **real, non-scratch multi-repo ecosystem** at a **released** tag remains the standing
production-maturity criterion across the 0–n programme (NDEBT-029 — the whole loop is not yet in a
released tag). This pilot exercises the n-case *mechanics* against throwaway members, not real
multi-project maturity. The Stage-4 *coordination* protocols (`04`/`05`) are carried as NDEBT-035 /
phase-011 candidate scope, validated against this evidence.
