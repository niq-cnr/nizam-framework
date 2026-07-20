# Release-Readiness Checklist — v0.8.0

Feature 059 (phase 006 close), gate **H-FRAMEWORK-RELEASE**. Prepared on the
feature-045 pattern; the pipeline never self-tags. SHA pins — phase base
`707a3f5` (the F-058 merge, PR #37); coordination `67a0be3`; deliverable
`b79b263`.

1. All framework validation green: `SUMMARY: 15 passed, 0 failed` (default sweep) / `SUMMARY (payload mode): 11 passed, 0 failed` / fixtures self-test 47/47 / e2e bootstrap PASS — evidence `.agent/evidence/059-verify-10.txt`.
2. Version surfaces bumped 0.7.0 → 0.8.0 in C10 lockstep — NIZAM.json `framework.version`, docs/guide/index.html meta + footer, CONTEXT.md frontmatter + change_log — evidence `.agent/evidence/059-verify-04.txt`, `.agent/evidence/059-verify-05.txt`, `.agent/evidence/059-verify-06.txt`.
3. README.md fully re-pinned to v0.8.0, zero v0.7.0 remaining — evidence `.agent/evidence/059-verify-07.txt`.
4. CHANGELOG rolled up to a dated `[0.8.0] - 2026-07-20` MINOR section, with the `blocking_findings` schema narrowing (feature 056) disclosed minor-not-breaking per `06_release_train.md` §4 — evidence `.agent/evidence/059-verify-02.txt`, `.agent/evidence/059-verify-03.txt`.
5. Check-count synced 12 → 15 (C1-C15) across NIZAM.json, tools/README.md, tools/validate.sh — evidence `.agent/evidence/059-verify-12.txt`.
6. No unresolved P0/P1 defect: docs/planning/DEBT.md Open section carries no open item (feature 056 resolved the last five NDEBT rows; all Resolved) — evidence `.agent/evidence/059/verification.txt`.
7. Human sign-off complete: PENDING -- human-gated (H-FRAMEWORK-RELEASE)
8. Immutable tag published: PENDING -- human-gated (H-FRAMEWORK-RELEASE)

Items 7-8 are the operator's, executed after PR review per the recorded
two-part gate — the v0.7.0 precedent was operator sign-off ("I Sign off
release-readiness", recorded at `31f3fff`) followed by the operator-pushed
annotated tag at `4833322`. No v0.8.0 tag exists at close; contract 059 E09
asserts the no-self-tag invariant.
