# Release Readiness — v1.2.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-09-17 on `main` at release
base `c0e0d04` (PR #57, "feat(review): define convergent code review standard"), which
was merged directly to `main` without opening a phase-numbered feature (no
`product_spec_014.md`, `feature_list_014.json`, or `phase_014.yaml` exists) -- this
record and the accompanying version-anchor bump are the release-preparation step alone,
not a retroactive feature-ceremony reconstruction. Target tier: MINOR, because the
Convergent Automated Code Review standard delivers purely additive, new-optional
capability -- nothing that validated under v1.1.0 is invalidated. At preparation time
the pipeline has not created, pushed, or approved `v1.2.0`.

## Automated readiness

1. Framework validator: full default sweep **16/16 PASS** (`bash tools/validate.sh`).
2. Fixture and CLI self-test: **79/79 PASS** (`bash tools/fixtures_self_test.sh`).
3. Convergent-review permanent unittest suite: **54/54 PASS**
   (`python3 tools/test_convergent_review.py`) -- the frozen 12-case corpus plus
   adversarial blocker regressions.
4. Release close-out gate, `--mode pr`, at V=1.2.0: **PASS**
   (`python3 .github/scripts/release_closeout.py --mode pr`).
5. Real repository tag probe: `git rev-parse -q --verify refs/tags/v1.2.0` returns
   non-zero -- **no `v1.2.0` tag exists**.

## Content map (PR #57, already merged)

| Surface | Summary |
|---|---|
| `standard/convergent_code_review.md` | The Convergent Automated Code Review standard: prior-ledger-first, authenticated three-trial review; a model is an observation-only sensor, deterministic code owns lifecycle, verdict, and replay. |
| `schema/review_packet.schema.json`, `review_trial`, `review_ledger`, `review_suppression`, `review_replay` | Five fully closed (`additionalProperties: false`) schemas for the packet, trial, ledger, human suppression, and content-addressed replay artifacts. |
| `templates/convergent-review-prompt.md` | The closed-output, exactly-three-trial prompt template. |
| `tools/convergent_review.py`, `evaluate_convergent_review_prompt.py`, `linux_trial_sandbox.sh`, `isolated_trial_adapter.py`, `test_convergent_review.py` | The dependency-free CLI/library, the prompt evaluator, the Linux reference sandbox adapter, and the permanent unittest suite over the frozen 12-case corpus. |

This release-preparation change itself additionally: bumps `NIZAM.json`'s
`framework.version` to `1.2.0`; adds the dated `[1.2.0]` MINOR CHANGELOG section citing
`methodology/06_release_train.md` Section 3.2; synchronizes the C10 version anchors in
`CONTEXT.md` (frontmatter + `change_log[0]`), `docs/guide/index.html` (meta + footer),
and README.md's four rolling version pins (curl URL, `GOVERNANCE_TAG`, `--tag`, and the
`releases/tag` display link and URL) -- the migration-guide link stays pinned to
`v1.0.0` verbatim, this being a MINOR release under Section 3.2 with no new migration
guide; and rolls `docs/planning/ROADMAP.md`'s Current Position disposition to name
`Release in preparation: v1.2.0` exactly once. While there, it also corrects a
pre-existing drift in that same document: the v1.1.0 post-release refresh (PR #56) had
renamed only the version number on the "Latest released tag" bullet, leaving the tier,
date, PR, commit, CHANGELOG section, and Release URL all still describing v1.0.0; this
change restates that bullet with the genuine v1.1.0 facts (PR #55, merge commit
`a2c15d2`, `release.yml` run `32282540074`, `[1.1.0]` CHANGELOG section) and rolls
"Prior released tag" from the stale v0.9.0 to v1.0.0.

## Gate disposition — H-FRAMEWORK-RELEASE

**v1.2.0 (MINOR) is PREPARED.** CHANGELOG, the C10 version anchors, and this readiness
record are complete. Sign-off and the tag remain **OUTSTANDING** -- no sign-off or tag
is recorded for v1.2.0 anywhere in this repository. Creating and pushing the annotated
`v1.2.0` tag is the operator's `H-FRAMEWORK-RELEASE` act alone, per
`methodology/06_release_train.md` Section 6, entirely outside this pipeline. The
pipeline never creates or pushes a release tag on its own.

No `v1.2.0` git ref of any kind (tag, branch, or otherwise) exists in this repository as
of this record's preparation.
