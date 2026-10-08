# Release Readiness — v1.4.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-10-08 on the
`chore/v1.4.0-release-prep` branch, cut from `main` at `669fb72` (PR #62
merged). Packaged: the two proposal-grade ecosystem lifecycle protocol documents
that landed with the phase-014 proposal (PR #61) --
`ecosystem/06_simplification_review.md` (Repeat: recurring simplification
review) and `ecosystem/08_ga_gate.md` (Promote/GA: evidence-gated GA
declaration criteria) -- together with their `ecosystem/README.md` rows and
their `NIZAM.json` ecosystem `key_documents` entries. Both documents are
`status: draft` and are **not yet normative**: their activation (the draft →
active flip, capability registration, and the definition of the reserved
`H-CONSOLIDATION` / `H-GA` gates) awaits phase-014 feature 099 under the
operator gate `H-PHASE-014`. Target tier: MINOR, per
`methodology/06_release_train.md` Section 3.2 -- new, optional protocol
documents added to the injected `ecosystem/` module, purely additive; nothing
that validated under v1.3.0 is invalidated. Section 3.4 (round up) applies: an
argument that draft, non-normative documents are PATCH-like straddles the
PATCH/MINOR line, and the higher tier governs. At preparation time the
pipeline has not created, pushed, or approved `v1.4.0`.

Preparation context. The operator's verbatim request, in the Orchestrator's
session on 2026-10-08, was: "PR #62 has been merged, cut a new release pin/tag
it." It is recorded as the Section 2 human sign-off for cutting the release
*preparation* only. The words "pin/tag it" are **not** recorded as tag
authorization: the tag act is a separate Orchestrator step after merge that
awaits explicit post-merge authorization recorded in `run_state` before the
act (NDEBT-018; the v1.1.0 precedent).

Everything else since v1.3.0 is envelope-only (none of it is injected by
`bootstrap.sh`): the phase-014 Planner artifacts, `docs/planning/*`, the
NIP-0003 proposal, `.agent/*`, and `CHANGELOG.md`. Release-fact for a later
Planner re-baseline of phase 014 (no phase-014 artifact is edited here): once
`v1.4.0` is tagged, feature 102's no-`v1.4.0`-tag acceptance test, the
`product_spec_014.md` zero-`v1.4.0`-refs criterion, and feature 100's `v1.3.0`
pilot pin are stale. This is recorded in `docs/planning/ROADMAP.md`.

## Automated readiness

Every result below was produced by the Evaluator's own re-run on the
uncommitted release-preparation tree (HEAD `669fb72`) and not taken from any
prior agent's pasted output.

1. Framework validator: full default sweep **16/16 PASS**
   (`bash tools/validate.sh`; last line `SUMMARY: 16 passed, 0 failed`, exit 0;
   C5, C8, C10 all PASS).
2. Fixture and CLI self-test: **79/79 PASS**
   (`bash tools/fixtures_self_test.sh`; `SELF-TEST OK: 79/79 fixtures accounted
   for, 0 failed`, exit 0; recorded un-tailed, all 104 lines).
3. Release close-out gate, `--mode pr`, at V=1.4.0: **PASS** -- all five anchor
   groups agree (`python3 .github/scripts/release_closeout.py --mode pr`; 5 x
   `PASS`, then `Release close-out: all internal version anchors agree with
   V=1.4.0 (--mode pr).`, exit 0).
4. Hermetic e2e bootstrap harness: **PASS** (`bash tools/e2e_bootstrap_test.sh`,
   exit 0, including `assert_genesis`, `assert_multirepo` and `assert_stage4`).
   Caveat, stated honestly: the harness tags and clones the checkout's HEAD
   **commit**, not the working tree. At run time the release edits were
   uncommitted, so it exercised committed HEAD
   `669fb7251bf45a30fea3fa3f520b23640695131b` (its own `resolved_sha=` line)
   and not the edited tree. This is acceptable under the 2e12225 precedent:
   the edits are envelope and version-anchor only, and touch nothing
   `bootstrap.sh` injects except the `NIZAM.json` `framework.version` string.
5. Tag probes: `git rev-parse -q --verify refs/tags/v1.4.0` prints nothing and
   exits **1**; `git ls-remote --tags origin v1.4.0` prints nothing **and
   exits 0** -- so **no `v1.4.0` tag exists**, locally or on origin. The
   remote probe is not fail-open: a control probe,
   `git ls-remote --tags origin v1.3.0`, returned the `v1.3.0` ref with exit 0
   in the same session, showing that origin was reachable and answering.

Further checks run from the plan's section 4 and recorded in the raw outputs:
`framework.version` reads `1.4.0`; README has 0 `v1.3.0` and 7 `v1.4.0`
occurrences; the ROADMAP body has exactly 1 disposition line at V=1.4.0 and
the `Latest released tag: v1.3.0` record is kept byte-identical; the tracked
diff since `669fb72` names exactly the 7 generator files; the untracked-aware
scope guard exits 0 (before and after the Evaluator's files were written) and
its negative control catches all six synthetic violations; 0 bytes of diff
across all forbidden paths; CHANGELOG lines 8-10 are `## [Unreleased]`, an
empty line, `## [1.4.0] - 2026-10-08`; no control characters in any touched
file; no brand/endpoint token in any added line.

Raw captured outputs: `.agent/evidence/release-v1.4.0-prep/`
(01-validate-sh.txt, 02-fixtures-self-test.txt, 03-release-closeout-pr.txt,
04-tag-probe-and-sanitization.txt, 05-e2e-bootstrap.txt); the approved plan is
`00-release-prep-plan.md` in the same directory.

## Content map

| Surface | Summary |
|---|---|
| `ecosystem/06_simplification_review.md` | Repeat-stage protocol: recurring simplification review; consolidations only under the reserved `H-CONSOLIDATION` gate. New, `status: draft` (v0.1.0), not yet normative. |
| `ecosystem/08_ga_gate.md` | Promote/GA protocol: evidence-gated GA declaration criteria; GA declaration operator-only under the reserved `H-GA` gate. New, `status: draft` (v0.1.0), not yet normative. |
| `ecosystem/README.md` + `NIZAM.json` | README 0.3.0 → 0.4.0 (two rows Planned → Shipped, prose only); `NIZAM.json` ecosystem `key_documents` gains two entries (landed in PR #61); `framework.version` 1.4.0. |
| `docs/guide/index.html` | `framework-version` meta and footer 1.4.0 only; no guide-card edits (phase-014 feature 099 scope). |
| `CHANGELOG.md` / `README.md` / `CONTEXT.md` | Dated `[1.4.0]` MINOR section above the retained `[Unreleased]` heading; four rolling pins (7 occurrences) to v1.4.0; CONTEXT frontmatter + `change_log[0]` at 1.4.0. |
| `docs/planning/ROADMAP.md`, `docs/planning/operator_gates.md` | `Release in preparation: v1.4.0` disposition bullet ahead of the unchanged `Latest released tag: v1.3.0` record; phase-014 release-fact note; NIP-0003 expected-version roll (v1.5.0 / v1.6.0); `H-FRAMEWORK-RELEASE` row appended with v1.4.0 PREPARED / tag OUTSTANDING language. |

`H-FRAMEWORK-RELEASE` sign-off and the tag remain outstanding — this pipeline
never self-tags per `methodology/06_release_train.md` Section 6.
