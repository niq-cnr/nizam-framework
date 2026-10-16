## Summary

Receipt validation repeatedly launched Git for individual immutable inputs. Batch those reads per invocation while retaining fresh physical-file checks and exact receipt identity checks. The independent focused readset now uses 8 real Git launches versus the unchanged oracle’s 168.

## Changes

- Batch literal paths separately for each revision inside `_receipt_candidate`, with bounded argument chunks and finite splitting on actual `E2BIG` failures.
- Preserve blob type, executable mode, digest, ancestry, origin, ownership and environment checks; add four independent regression checks to the existing fixture suite.
- Update the changelog and current planning/handover views; retain original failures and the immutable installed v1.5.0 payload.

## Test Plan

- Independent Mode B, eight selected local command outcomes, and exactly one additional adversarial check passed. Original failed compliance attempt remains recorded among nine actual mandatory attempts.
- Default suite: 48 ordered cases plus one auxiliary observation. Fixture suite: 166 files, two selected WA cases and four new focused checks.
- Extra check: valid 9,884-path repository beyond host argument capacity, late-chunk rejection and restoration; full checkout/payload preservation passed.
- Previous PR #104 main CI: all five jobs verified successful. This PR requires its own exact-head checks, normal merge and successful main CI.

Final accounting at immutable endpoint `462f30f2` records 3,024 conservative authored-change lines against the unchanged 2,600 ceiling. The failed budget and bounded delivery exception under standing delegated authority are retained; subsequent integration administration remains separately recorded. No elapsed-time speedup or competitor benchmark result is claimed.
