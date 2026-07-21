# Re-pilot evidence — feature 069 (phase 008 close)

Re-runs the ecosystem loop against a real, freshly bootstrapped scratch consumer using the
**fixed** tools (features 065–068), proving the phase-007 pilot findings are resolved
**with no hand-applied workaround**. The consumer (a fresh `git init` with `src/calc.py` +
`README.md`) was bootstrapped from an ephemeral tag on the phase-008 branch HEAD, so its
injected `.nizam/` carries the fixed `ecosystem_preflight.py`, the audit/compare tools, and
a `provenance.json` with `resolved_sha` (feature 067). The consumer is ephemeral (discarded);
only these framework-side snapshots are committed.

## Outcome — findings A, B, and the SHA pin all resolved

| Was (phase-007 pilot) | Now (phase-008 re-pilot) | Evidence |
|---|---|---|
| **A.** Clean Preflight against a real consumer was a hard **FAIL** (3 blocking: injected `.nizam/` untracked + refs unresolved at repo-root) | **PASS_WITH_EXCEPTIONS** — the injected `.nizam/` is a single expected `injected_governance_payload` exception; required refs resolve under the governance-root | `preflight_PASS_WITH_EXCEPTIONS.json` |
| **B.** Baseline `framework_references` mis-anchored to the consumer HEAD | `framework_references` = the **injected pin** (the tag); `repository_references` = the consumer HEAD — two distinct correct facts | `baseline_framework_pin_anchored.json` |
| **(067)** provenance pinned only the tag *name* | `provenance.json` records `resolved_sha`; `--verify-only --expected-sha` holds (moved-tag drift detectable) | `provenance_with_resolved_sha.json` |

The fixed single-project loop (Preflight → Baseline, with the injected `.nizam/tools/` now
carrying Audit/Compare) runs end-to-end against a real bootstrapped consumer with no manual
bridge. This is the acceptance criterion phase-007 finding A/B left open.

## Residual

- `NDEBT-029` (audit/compare tools not in a *released* tag) remains open — the branch HEAD
  carries them, but they are proven released only when the next framework tag is cut.
- A **real, non-scratch consumer pilot** remains the open production-maturity criterion across
  the whole 0–n programme (a scratch consumer exercises mechanics, not real project maturity).
  Carried into the phase-009 candidate scope.
