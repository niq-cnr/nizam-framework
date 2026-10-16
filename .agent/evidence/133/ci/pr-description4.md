## Summary

Receipt validation repeatedly launched Git for individual immutable inputs. Batch those reads per invocation while retaining fresh physical-file checks and exact receipt identity checks. The independent focused readset uses 8 real Git launches versus the unchanged oracle’s 168.

## Changes

- Batch literal paths separately for each revision inside `_receipt_candidate`, with bounded argument chunks and finite splitting on actual `E2BIG` failures.
- Preserve blob type, executable mode, digest, ancestry, origin, ownership and environment checks; add four independent regression checks to the existing fixture suite.
- Preserve the original full AST guard fingerprint across Python versions by explicitly including empty fields on Python 3.13 and later. Product code, the guard mask and all behavioral assertions remain unchanged by this portability repair.
- Update the changelog and planning/handover views; retain failed attempts and the immutable installed v1.5.0 payload.

## Test Plan

- Original implementation: independent Mode B, eight selected local command outcomes and exactly one additional adversarial check passed at their recorded revisions. Nine mandatory attempts preserve the original compliance failure. Those outcomes remain historical for the original runner.
- Original local default suite: 48 ordered cases plus one auxiliary observation. Original local fixture suite: 166 files, two selected WA cases and four new focused checks. Original extra: 9,884 valid paths beyond host argument capacity, late-chunk rejection/restoration and full preservation.
- Hosted run 38831271485 failed the AST serialization guard in both shell jobs on Python 3.14.8. The four new checks were not reached and the separate default-48 step was skipped; this negative evidence is retained.
- Portability repair: distinct combined bundle/Mode B review and fresh targeted QA passed. All four individual selectors passed on actual Python 3.12.3, 3.13.13 and 3.14.3; valid outside-body mutations rejected, body-only mask controls passed, default/payload/self-governance checks passed, and exactly one outside-directory import-decoy extra passed. All full preservation snapshots matched. Unchanged local full suites were not repeated under the explicitly recorded bounded recovery plan.
- [Hosted CI2](https://github.com/niq-cnr/nizam-framework/actions/runs/38842030473) passed all six required PR checks at `19efbca54be6b2d58f637b22ee4b4185cf32b342`. Complete qualified logs verify 48 ordered cases plus one auxiliary, both 166-file fixture inventories, all four new checks in each shell run, two physical source receipts and five cleanup footers. Raw unknown step labels are preserved with command-group/timestamp attribution. Local 3.14.3 remains distinct from hosted 3.14.8.
- After fresh clear feedback, normal merge `bfd15d10eb718d2cf18272b35c1bb5857af71f3f` on 2026-10-16 04:39:19Z retained parents `c8ef3cd4`/`19efbca5` and exactly the tested tree. Matching [main CI](https://github.com/niq-cnr/nizam-framework/actions/runs/38851734070) completed successfully on the exact merge: all five jobs passed. Independently admitted complete logs verify the two physical source receipts, 48 ordered cases plus one auxiliary, both 166-file inventories, all four new checks in each shell run and all five cleanup footers. The original watcher connection failure remains recorded separately from the successful workflow.

Immutable endpoint `462f30f2` records 3,024 conservative authored-change lines against the unchanged 2,600 ceiling. The failed budget and bounded delivery exception remain. A separately captured and independently admitted disjoint supplement adds 3,196 lines through `c3345ff4`, giving 6,220 retained authored-change lines through that endpoint. The original failed budget remains unchanged. Later administrative work, including matching-main proof and this description update, remains separately unmeasured; no fully measured delivery-cost claim is made. No elapsed-time speedup or competitor result is claimed.
