## Summary

Adds `route_failed_attempt`, a read-only routing proposal based on independently selected, committed failure evidence. Failed wrappers retain their failed outcome; attempts one and two route to diagnosis or repair, and attempt three halts without allocating a retry.

## Changes

- Bind authority, capture, classification, candidate and coordination references; preserve counters, budgets, history and optional lane inventories.
- Accept rejecting semantic verdicts across the supported legacy and evolved QA schemas. Preserve the independently discovered false-rejection evidence and its regression.
- Add four independently authored cases, extending the default suite from 42 to 46; update circuit-breaker guidance, tools documentation and the unreleased change notes.

## Test Plan

- [x] Independent pre-code gates and renewed acceptance-bundle review.
- [x] Genuine legacy-verdict failure captured before Source repair.
- [x] Repaired original compatibility check and updated default46 each exited 0; preservation checks passed.
- [ ] Private positive/semantic-negative/restored controls and independent executable seal.
- [ ] Post-code review, fresh QA, one additional adversarial check and compliance checks.
- [ ] Exact-head hosted CI, evidence capture and canonical completion.

Installed v1.5.0 stays pinned. Live Root repository-binding migration, feature123 controls readiness, runtime benchmarks and comparative results remain outside this change. The PR remains draft until the remaining gates pass.
