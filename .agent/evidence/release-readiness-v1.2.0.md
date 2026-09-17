# Release Readiness — v1.2.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-09-17 from release-
preparation base `c0e0d04` (`main`, the PR #57 merge commit) on branch
`claude/epic-wozniak-jw1zmo`. Target tier: MINOR, because everything `main` gained
since `v1.1.0` is purely additive, new-optional capability under
`methodology/06_release_train.md` Section 3.2 -- one new standard, five new schemas
that validate only new artifact types, new tools, one new template, and a new
`tools/SKILL.md` section. No previously shipped schema, file, or protocol id is
narrowed, removed, or renamed, so nothing that validated under v1.1.0 is
invalidated and no migration guide is required. At preparation time the pipeline
has not created, pushed, or approved `v1.2.0`.

## Provenance note

The content this release ships landed on `main` via PR #57
(`feat(review): define convergent code review standard`, merged
2026-09-17T06:59:59Z) **outside a numbered phase**: no product specification,
feature list, contract, QA verdict, or Section-5 evidence exists for it under
`.agent/`, so validator check C16 has nothing to police for it. Its verification
rests on the shipped `tools/test_convergent_review.py` suite plus the ordinary CI
sweep. This record states that plainly rather than backfilling phase artifacts;
whether to register a debt row for the out-of-phase landing is the operator's call.

## Automated readiness

Every capture below lives under `.agent/evidence/release-prep-v1.2.0/` in the
`methodology/04_tool_driven_state.md` Section 5 shape (invocation, verbatim output,
`EXIT:<code>`), replayable from the repository root.

1. Framework validator: full default sweep **16/16 PASS**
   (`bash tools/validate.sh`; `validate-full-sweep.txt`).
2. Fixture and CLI self-test: **79/79 PASS**
   (`bash tools/fixtures_self_test.sh`; `fixtures-self-test.txt`).
3. Hermetic bootstrap/genesis/n-case/coordination e2e: **PASS**
   (`bash tools/e2e_bootstrap_test.sh`; `e2e-bootstrap.txt`).
4. Convergent-review test suite: **54 tests OK**
   (`python3 tools/test_convergent_review.py`; `convergent-review-tests.txt`).
   Note: `.github/workflows/compliance.yml` does not run this suite; it was run
   here directly.
5. Release close-out gate, `--mode pr`, at V=1.2.0: **PASS**
   (`python3 .github/scripts/release_closeout.py --mode pr`; `closeout-mode-pr.txt`).
6. Release close-out gate, `--mode tag`, rehearsal: **PASS 9/9**. The seven
   prepared files were committed to a temporary local commit, tagged `v1.2.0`
   locally, checked with `--mode tag --tag v1.2.0`, and the commit and tag were
   then discarded (`git tag -d`, `git reset --soft`); nothing was pushed. The same
   rehearsal ran `release.yml`'s CHANGELOG extraction `awk` against
   `v1.2.0:CHANGELOG.md` and produced a non-empty 93-line notes body. Not retained
   as an evidence file because the rehearsal mutates refs; its output was:

   ```text
   PASS tag shape (vMAJOR.MINOR.PATCH)
   PASS NIZAM.json readable at v1.2.0 (V reference)
   PASS tag v1.2.0 matches NIZAM.json framework.version at tag (1.2.0)
   PASS CONTEXT.md version anchor (frontmatter + change_log[0])
   PASS docs/guide/index.html version anchors (meta + footer)
   PASS README.md version pins (curl URL / GOVERNANCE_TAG / --tag / releases-tag)
   PASS CHANGELOG.md top released section (heading + tier banner)
   PASS ROADMAP.md disposition line (Latest released tag / Release in preparation)
   PASS CHANGELOG.md top section matches tag v1.2.0
   Release close-out: tag v1.2.0's anchors are internally consistent (--mode tag).
   ```

7. Real repository tag probes: `git rev-parse -q --verify refs/tags/v1.2.0`
   returns non-zero and `git ls-remote --tags origin refs/tags/v1.2.0` returns
   nothing -- **no `v1.2.0` tag exists locally or on origin**
   (`no-local-tag-check.txt`, `no-remote-tag-check.txt`).
8. Anchor spot-checks: `version-anchors.txt` (NIZAM.json, CONTEXT.md, guide meta +
   footer all `1.2.0`), `readme-pins.txt` (seven rolling pins at `v1.2.0`, the
   migration link at `v1.0.0`), `changelog-heading-banner.txt`,
   `roadmap-disposition-count.txt` (exactly one body line names `v1.2.0`),
   `operator-gates-disposition.txt`.

## Content map -- what v1.2.0 ships beyond v1.1.0 (all from PR #57)

| Surface | Status | Summary |
|---|---|---|
| `standard/convergent_code_review.md` | READY | Twelve-section runtime-neutral standard: observation-only models, prior-ledger-first review, exactly three sandbox-isolated trials, deterministic fingerprints/lifecycle/verdict, human-authorized suppression, content-addressed replay, transactional publication. |
| `schema/review_packet.schema.json`, `review_trial`, `review_ledger`, `review_suppression`, `review_replay` | READY | Closed Draft 2020-12 artifact family for the review protocol; new artifact types only, no existing schema touched. |
| `tools/convergent_review.py` | READY | Dependency-free reference CLI: `build-packet`, `fingerprint`, `converge`, `render`, `extract-ledger`, `verify-replay`. |
| `tools/evaluate_convergent_review_prompt.py`, `tools/linux_trial_sandbox.sh`, `tools/isolated_trial_adapter.py` | READY | Prompt evaluator requiring a trusted sandbox adapter per trial; the Linux namespaces + Landlock reference adapter. |
| `tools/test_convergent_review.py`, `tools/fixtures/convergent_review/` | READY | Permanent stdlib unittest suite (54 tests) over the frozen twelve-case corpus indexed by `manifest.json`. |
| `templates/convergent-review-prompt.md` | READY | Ninth governed template: the closed-output trial prompt. |
| `tools/SKILL.md` Section 9 (0.5.0) | READY | Routes automated review through the standard and the CLI; References renumbered to Section 10. |
| `NIZAM.json`, `standard/README.md` 0.5.0, `schema/README.md` 0.18.0, `templates/README.md` 0.4.0, `tools/README.md` 0.11.0 | READY | Capability, key_documents, `schemas[]`, and `templates[]` registrations plus module index rows. |

## Release surfaces (this preparation)

- `NIZAM.json` `framework.version`, `CONTEXT.md` (frontmatter + `change_log[0]`),
  and both `docs/guide/index.html` C10 anchors (meta + footer) identify `1.2.0`.
  CONTEXT.md's Module Map `schema/`, `standard/`, and `templates/` bullets now name
  the review schema family, the Convergent Automated Code Review standard, and the
  DoD and convergent-review prompt templates; the guide's `standard/` and `tools/`
  module cards each gain a paragraph describing the new capability.
- README.md's seven rolling version pins (curl URL, `GOVERNANCE_TAG`, `--tag`, the
  `[vX release]` display text and its `releases/tag` URL) all read `v1.2.0`; the
  migration-guide link (path and label) stays pinned to `v1.0.0` verbatim -- a
  MINOR release with no new migration guide. README's `standard/` module row now
  also names the layered Definition of Done and the new standard.
- CHANGELOG.md carries an empty `[Unreleased]` followed by the dated
  `[1.2.0] - 2026-09-17` section, tagged **Minor release**
  (`methodology/06_release_train.md` Section 3.2), with `### Added` bullets for the
  standard, the schema family, the tooling, the template, and the skill routing,
  and a `### Changed` bullet for the anchor roll.
- `docs/planning/ROADMAP.md` (0.40.0): the document body names
  `Release in preparation: v1.2.0` exactly once. The latest-released bullet, which
  the 0.39.0 post-release refresh had rolled by version number only (it still
  described v1.0.0's PR, commit, run, and MAJOR tier under a `v1.1.0` heading),
  now describes v1.1.0 truthfully; the v1.0.0 facts move to the prior-released
  bullet alongside v0.9.0.
- `docs/planning/operator_gates.md` (0.22.0): the `H-FRAMEWORK-RELEASE` row gains
  the v1.2.0 PREPARED/OUTSTANDING disposition, appended row-anchored.
- `.agent/run_state.json`: one `release_prepared` history event (the v0.9.0
  precedent for a release prepared outside a phase feature); `current_phase` stays
  `013-definition-of-done` and `status` stays `complete`. No feature list, contract,
  or QA artifact is touched.
- `docs/planning/DEBT.md` is untouched: `NDEBT-026`, `NDEBT-034`, `NDEBT-037`, and
  `NDEBT-040` stay Open, out of this preparation's scope.

## Gate disposition -- H-FRAMEWORK-RELEASE

**v1.2.0 (MINOR) is PREPARED.** CHANGELOG, the C10 version anchors, and this
readiness record are complete. Sign-off and the tag remain **OUTSTANDING** -- no
sign-off or tag is recorded for v1.2.0 anywhere in this repository. Per
`methodology/06_release_train.md` Sections 2 and 6, the remaining steps are:

1. This preparation merges to `main` through a reviewed pull request (never
   self-merged).
2. The operator exercises `H-FRAMEWORK-RELEASE`, recorded in `run_state.json`
   (`operator_gate_decision`) before the act, per the NDEBT-018 rule.
3. The annotated `v1.2.0` tag is created and pushed at that reviewed merge commit
   -- the one Orchestrator-owned release mechanic, and only on the operator's
   authorization. `release.yml` then runs the blocking tag-mode close-out and
   publishes the GitHub Release from the `[1.2.0]` section.
4. The post-release refresh (the PR #54 / #56 precedent): ROADMAP drops the
   preparation bullet and rolls the latest-released bullet to v1.2.0 (keeping
   exactly one body line naming it), operator_gates records EXECUTED with the
   verbatim authorization, and run_state records `release_executed`.

No `v1.2.0` git ref of any kind (tag, branch, or otherwise) exists in this
repository or on origin as of this record's preparation.
