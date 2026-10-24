# Local PR preparation

## PR 1: Preserve task authorization and inherited work at completion

Base: `00e0bcb1bd16ba2ddaf5774153bbf2c1e05244a6`  
Branch: `fix/r02-completion`  
Accepted tip: `02c54239af1e646d79f344ffd0ff2ae64f51905b`

- Carry the task contract into completion and revalidate approval and allowed scope.
- Record separate versioned index and no-follow worktree observations, including rename/copy endpoints.
- Refuse an inherited-work exemption when legacy records cannot establish preservation.
- Account for committed, staged, unstaged and untracked scope changes.

Verification: independent baseline reproductions, 22 regression scenarios, independent post-code review and fresh QA; compliance 16/0; isolation conformance 54 tests with no skips. See `.agent/evidence/r02-completion/root-completion-gate.json`.

## PR 2: Validate structured QA proof for completion and receipt prerequisites

Base: `02c54239af1e646d79f344ffd0ff2ae64f51905b`  
Branch: `fix/r02-proof-validation`

- Share structured QA validation across direct completion and both receipt prerequisite paths.
- Bind exact typed check inventory, assessed candidate, consumed authorization, active verifier/schema inputs, producer context and execution root.
- Verify actual captures and both output streams; preserve intentional negative-test and zero-byte-stream semantics.
- Support equivalent-checkout proof consumption and inherited unrelated work without weakening generic assessment.
- Keep historical evidence readable; require fresh complete proof where older forms cannot establish the claimed result.

Final independent review and immutable-candidate QA are pending in this preparation record. The delivery index records the final result.

## Delivery boundary

These branches are prepared locally. No upstream PR, merge, release, deployment or installed `.nizam/` upgrade is performed. Isolation policy simplification is tracked separately in `.agent/evidence/r02/isolation-simplification.json`.
