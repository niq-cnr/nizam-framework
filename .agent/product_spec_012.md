---
id: nizam-product-spec-012
title: "Nizam Framework — Phase 012 Spec: v1.0.0 Consumer-Safety Remediation"
description: "Resolve every v0.9.0 consumer-adoption finding in issue #52, tighten invalid schema states, remove destructive recovery guidance, correct runtime classification, align the five-role model, and prepare the breaking v1.0.0 release."
tags: [spec, consumer-safety, remediation, breaking-release, phase-012]
status: active
last_audited: "2026-08-15"
authoritative_source: NA
version: 1.1.0
spec_version: "1.1.0"
created_at: "2026-08-15T18:03:31Z"
updated_at: "2026-08-15T18:35:11Z"
change_log:
  - version: "1.1.0"
    date: "2026-08-15T18:35:11Z"
    summary: "Names docs/planning/phase_012.yaml as the canonical structured lifecycle document required by the approved phase-state model; run_state remains derived coordination state."
  - version: "1.0.0"
    date: "2026-08-15T18:03:31Z"
    summary: "Initial active phase-012 plan, authorized by the operator with the verbatim instruction 'approved. please proceed.' after approving the full issue-52 major-release boundary, a clean-break migration guide, and isolated-worktree failure recovery."
---

# Phase 012 — v1.0.0 Consumer-Safety Remediation

## Status and authority

**ACTIVE plan of record.** The operator authorized this phase on 2026-08-15 with
the verbatim instruction **"approved. please proceed."** (`H-PHASE-012`). The
authorization follows explicit operator decisions to resolve the full issue #52
batch in one v1.0.0 release, enforce a clean schema break with a migration guide,
and standardize isolated worktrees for retry cleanup.

Issue #52 was raised from a real v0.9.0 consumer adoption. Its highest-risk
claims were reproduced before planning: the circuit-breaker protocol prescribes
repository-wide destructive cleanup, the preflight schema accepts blocking
findings on successful verdicts, and the comparison tool misclassifies an
earlier-resolved/later-open finding. Schema tightening is breaking under
`methodology/06_release_train.md` Section 3.1, so the release target is v1.0.0.

## Scope

Phase 012 resolves every issue #52 bullet as one consumer-visible release:

1. Tighten the five reported schema families and add discriminating fixtures.
2. Correct reopened-finding classification and consolidate fixture scratch setup.
3. Replace destructive shared-tree recovery, define repairable derived state,
   restore the five-role model, and correct planning/execution/release/eval rules.
4. Reconcile ecosystem lifecycle and consumer-inheritance documentation.
5. Ship a clean-break v1.0.0 migration guide and rehearse an upgrade.
6. Prepare the release; the pipeline records but never self-executes the final tag.

Every reported finding receives a row in the issue matrix embedded in the
feature contracts and PR body. A finding is closed only by a reproduced failing
probe plus a passing regression, or by evidence proving that the report does not
apply. No finding is silently dropped because it was labelled Minor or Trivial.

## Public contract changes

- Successful preflight verdicts reject `blocking_findings`; failed verdicts
  require a non-empty list.
- Pin-consistent membership results require a non-empty `framework_pin`.
- Failed reconciliation plans require non-empty `cycle_findings` and empty
  `order`.
- Membership `schema_version` uses strict SemVer 2.0 syntax.
- Evidence paths require a file/path segment after `.agent/evidence/`.
- Compare classifies resolved-then-open findings as `reopened`.
- No shipped path or capability identifier is removed or renamed.

These changes intentionally invalidate some v0.9.0 artifacts. There is no dual
validation window. The migration guide supplies exact before/after examples and
the sanctioned re-bootstrap workflow.

## Safety and state model

Each retryable implementation attempt runs in an isolated worktree created from
the last approved base. On the third failed attempt, the agent captures evidence,
marks the canonical phase step blocked, removes only that exact attempt worktree,
and stops. Repository-wide `git reset --hard` and `git clean -fd` are forbidden.

The phase document is the canonical lifecycle state. `.agent/run_state.json` is
derived coordination state updated idempotently after the canonical write. If a
mismatch is detected, execution halts and rebuilds the derived entry; no protocol
claims a multi-file atomic write.

For this phase, that canonical structured document is
`docs/planning/phase_012.yaml`, registered from `docs/planning/manifest.json`.

## Feature DAG

- **085** — issue intake plus failing regression tests. Root.
- **086** — schema invariants and migration examples. Depends on 085.
- **087** — comparison correctness and fixture-harness refactor. Depends on 085.
- **088** — governance and methodology safety. Depends on 085.
- **089** — ecosystem and consumer documentation truth. Depends on 086–088.
- **090** — full validation and disposable consumer upgrade rehearsal. Depends on 086–089.
- **091** — v1.0.0 release preparation and human gate. Depends on 090.

The DAG is acyclic and has one root (`085`). Consumers remain pinned to v0.9.0
until feature 091 passes and the operator separately executes
`H-FRAMEWORK-RELEASE`.

## Acceptance

- Every issue #52 bullet is mapped to changed behavior and evidence.
- New regressions fail against the v0.9.0 behavior and pass after remediation.
- `tools/validate.sh`, `tools/fixtures_self_test.sh`, and
  `tools/e2e_bootstrap_test.sh` pass with their real exit codes asserted.
- Python and shell syntax checks pass.
- A disposable consumer re-bootstrap against a local v1.0.0 candidate passes;
  deliberately incompatible legacy artifacts fail with actionable diagnostics.
- Documentation metadata, capability indexes, changelog, and version anchors are
  consistent.
- Automated review has no unresolved blocking finding.

## Out of scope

- Bulk upgrades of NizamIQ or other consumers; those are separate release trains.
- The deferred real non-scratch multi-repo pilot and lifecycle stages 06/08.
- Compatibility shims that continue accepting semantically invalid v0.9.0 artifacts.
- Unrelated open Low debt (`NDEBT-026`, `NDEBT-034`).

The prior phase-012 candidate scope (real pilot plus stages 06/08) is deferred
unchanged to the next planning cycle because the confirmed Critical consumer-
safety intake takes precedence.

## Human gates

- `H-PHASE-012`: **SATISFIED 2026-08-15** — "approved. please proceed."
- `H-FRAMEWORK-RELEASE`: **OUTSTANDING** — after feature 090, the operator must
  approve the v1.0.0 version, changelog, migration notes, and annotated tag.
