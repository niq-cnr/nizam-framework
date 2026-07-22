# Release-Readiness Checklist — v0.9.0

Gate **H-FRAMEWORK-RELEASE**. Prepared on the feature-045/059 pattern; the pipeline
never self-tags. Release base: `1dd4971` (the phase-011 merge, PR #49) — the mainline
tip carrying phases 007–011. MINOR release per `methodology/06_release_train.md` §3.2.

1. **All framework validation green:** `SUMMARY: 15 passed, 0 failed` (default sweep,
   C1–C15) / `tools/fixtures_self_test.sh` 65/65 (+ 7 CLI-probe groups) /
   `tools/e2e_bootstrap_test.sh` PASS (`assert_genesis` + `assert_multirepo` +
   `assert_stage4`).
2. **Version surfaces bumped 0.8.0 → 0.9.0 in C10 lockstep** — `NIZAM.json`
   `framework.version` (the External-Anchor Rule source), `docs/guide/index.html`
   `<meta name="framework-version">` + `#footer-version`, and `CONTEXT.md` frontmatter
   `version` + a dated `0.9.0` change_log entry. C10's version-anchor sub-check green.
3. **README.md fully re-pinned to v0.9.0**, zero `v0.8.0` remaining (install `curl`,
   `GOVERNANCE_TAG`, `--tag`, and the Release-page link). Historical `v0.8.0` references
   in `.agent/` records, prior-phase specs, and `docs/planning/*` change_logs are left
   immutable (they record what actually happened at v0.8.0).
4. **CHANGELOG rolled up to a dated `[0.9.0] - 2026-07-22` MINOR section** with a
   release lead classifying the change as MINOR (`methodology/06_release_train.md` §3.2):
   the new schemas validate *new* artifact types (no previously-shipped schema narrowed),
   the existing C12 check (which predates v0.9.0) gains four new schema families
   (`ecosystem_membership`, `ecosystem_membership_result`, `reconciliation_plan`,
   `release_train_manifest`) guarding those new types — the C1–C15 check set is unchanged —
   and the payload additions (`ecosystem/00`, `04`, `05`; the
   membership/reconciliation/release-train + audit/compare tools) are new-optional capability.
   A fresh empty `[Unreleased]` sits on top. `release.yml` will find the matching
   `## [0.9.0]` section at tag-publish time.
5. **The whole 0–n loop is in the tag** (`NDEBT-029`): `tools/ecosystem_audit.py`,
   `tools/compare_ecosystem_baselines.py`, `tools/validate_evidence_freshness.py`,
   `tools/ecosystem_membership_run.py`, `tools/ecosystem_reconcile.py`, and
   `tools/ecosystem_release_train.py` are all present on the release base — a consumer on
   the `v0.9.0` pin can run Preflight → Baseline → Audit → Plan → Promote → Compare
   without pointing at the framework working tree.
6. **No unresolved P0/P1 defect:** `docs/planning/DEBT.md` Open section carries only
   Low/Medium enhancement candidates (`NDEBT-026` C15 mapping-direction; `NDEBT-034`
   per-member clone cost) plus `NDEBT-029` (resolved *by* this release, on the tag push).
   No High/blocking item.
7. **Human sign-off complete:** DONE 2026-07-22 -- the operator signed off release-readiness and merged PR #50 (`H-FRAMEWORK-RELEASE`).
8. **Immutable tag published:** DONE 2026-07-22 -- the operator pushed the annotated tag `v0.9.0` at merge commit `5b19b85`; `release.yml` auto-published the GitHub Release page from the `[0.9.0]` CHANGELOG section (<https://github.com/niq-cnr/nizam-framework/releases/tag/v0.9.0>). `NDEBT-029` resolved.

Items 7–8 are the operator's, executed after PR review per the recorded two-part gate —
the v0.7.0 / v0.8.0 precedent was operator sign-off followed by the operator-pushed
annotated tag (v0.8.0 at `183e468`), after which `release.yml` published the GitHub
Release page from the matching CHANGELOG section. **No `v0.9.0` tag exists at prep time;
the pipeline never self-tags.** On the tag push, `NDEBT-029` moves Open → Resolved and
the first **real, non-scratch multi-repo pilot** at the released tag becomes runnable —
the standing production-maturity criterion this release unblocks.
