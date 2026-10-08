# v1.4.0 Post-Release Refresh + Phase-014 Re-baseline (D1) — Planner plan, awaiting @validator Mode A

- Plan author: @planner (Protocol 04). This file is the planner's only write.
- Branch: `chore/v1.4.0-post-release`, cut from `main` = `9edd5d0` (PR #63 merged).
- Base for every diff and guard below: `9edd5d0`. All "Current" blocks were re-read from the
  working tree, which equals `9edd5d0` for every file this plan edits (AH-1). Each Current
  block's uniqueness (count = 1) was asserted by the Section 5 dry-run.
- Revision: 0, amended in-flight by the Orchestrator's D1 instruction (Section 2B). No
  validator round has happened yet.

## 0. Facts and baseline (captured read-only by the planner)

Release facts, from `.agent/evidence/release-v1.4.0-tag/01..06` and re-probed live:

| Fact | Value | Source |
|---|---|---|
| Annotated tag | `v1.4.0`, `git cat-file -t` = `tag` | 01 |
| Tag object | `bb32064472fb71deaba96e134b888c7e9e590d96` | 01, 03 (`git ls-remote`) |
| Tagged commit | `9edd5d0e0d9e0489c961407d306ae30541c27dd5` (PR #63 merge, 2026-10-08T10:24:45Z) | 01 |
| Tagger time | 2026-10-08T10:26:01Z (epoch 1791455161) | 01 |
| `release.yml` run | 37763448754, conclusion `success`, every step success incl. "Verify release close-out" | 04 |
| GitHub Release | "Nizam v1.4.0 — Simplification Review & GA Gate protocols, draft (MINOR)", published 2026-10-08T10:26:22Z, not draft, not prerelease | 05 |
| Consumer quick-start at `v1.4.0` | installed `framework.version` 1.4.0, resolved_sha `9edd5d0`, 82 indexed paths | 06 |
| Tag-act authorization (verbatim) | "merged — authorized to tag v1.4.0" | run_state `operator_gate_decision` 2026-10-08T10:25:50Z |
| Release request (verbatim) | "PR #62 has been merged, cut a new release pin/tag it." | same event; operator_gates v0.25.0 |
| D1 authorization (verbatim) | "proceed with the logic next steps to complete the backlog." | run_state `operator_gate_decision` 2026-10-08T10:30:34Z (verified present, AH-2) |

Baseline at `9edd5d0` + the uncommitted run_state (planner runs, `PYTHONDONTWRITEBYTECODE=1`):

- `bash tools/validate.sh` printed `SUMMARY: 16 passed, 0 failed` (exit 0).
- `bash tools/fixtures_self_test.sh` printed `SELF-TEST OK: 79/79 fixtures accounted for, 0 failed`.
- `python3 .github/scripts/release_closeout.py --mode pr` gave 5 PASS lines at `V=1.4.0`
  (exit 0). It already passes because the prep bullet supplies the one disposition line.
- `python3 .github/scripts/release_closeout.py --mode tag --tag v1.4.0` passed (exit 0). It
  reads every anchor at the tag (`git show v1.4.0:<path>`), so this refresh cannot affect it.
- Feature 102's current test `git rev-parse -q --verify refs/tags/v1.4.0; test $? -eq 1`
  now **exits 1**: the ref resolves to `bb32064`. The assertion is actually false.
- `refs/tags/v1.5.0`: `git for-each-ref` matched 0 refs, and `git ls-remote --tags origin 'v1.5.0*'`
  returned empty output with exit 0. The retargeted test exits 0 today.
- `git status --porcelain` shows only `M .agent/run_state.json` and
  `?? .agent/evidence/release-v1.4.0-tag/`.

## 1. Precedent decisions

**P1: ROADMAP disposition (mirrors `3094223`, the v1.3.0 refresh).** At v1.3.0 the refresh
did three things:

1. It removed the "Release in preparation" bullet.
2. It rewrote the latest-released bullet to name the new tag.
3. It rolled the previous latest line (v1.2.1, carrying v1.2.0 inside it) to
   "**Prior released tag:**". The previous "Prior" (v1.1.0) was demoted to
   "**Earlier released tags:**".

Here, R5 removes the v1.4.0 prep bullet and inserts a new "Latest released tag: v1.4.0"
bullet. R5 also relabels the v1.3.0 bullet's lead line from "Latest released tag" to
"Prior released tag", with the bullet body byte-identical. R6 relabels the v1.2.1 bullet
from "Prior released tag" to "Earlier released tag", matching the existing
"- Earlier released tag: v1.0.0" bullet below it, with the body byte-identical.

Justification:

- Keeping "Latest released tag: v1.3.0" would be false.
- Relabelling rather than deleting keeps every released fact.
- One "Prior" and one "Latest" line keeps the ladder unambiguous.
- The close-out gate counts only V-scoped matches (`release_closeout.py:276-279`). The v1.3.0
  line would not count at V=1.4.0 either way, so the roll is for truth, not for the gate.

After the edit, exactly one body line matches `Latest released tag: v1.4.0` and none
matches `Release in preparation: v1.4.0` (V5).

**P2: operator_gates.** The new text is appended to the existing `H-FRAMEWORK-RELEASE` row
(no new row), following the v0.21.0 (v1.1.0) and v0.24.0 (v1.3.0) precedents. Following
v0.24.0 (`3094223`), the row's own PREPARED clause also changes:

- Current: "remain OUTSTANDING -- no ... is recorded for v1.4.0".
- New: "remained OUTSTANDING at preparation time".

Otherwise the cell would keep a false present-tense "no tag is recorded" claim. The cell
still ends with "Recurring: outstanding again at the next release. |".

**P3: CHANGELOG.** One bullet goes under `[Unreleased]` → `### Changed`. `a063dff` (the
v1.1.0 refresh) did not touch CHANGELOG. `3094223` added its post-release note inside an
`### Added` bullet because it shipped new artifacts. This refresh adds nothing; it updates
records and re-baselines existing artifacts, which Keep a Changelog files under "Changed".
The bullet sits under `[Unreleased]`, so the `[1.4.0]` section, the top released section
that close-out group 4 checks, is unchanged.

**P4: manifest.json.** Releasing alone would not change the manifest:

- `a063dff` touched the manifest only because v1.1.0 was an in-phase release (phase 013's
  note gained "-> RELEASED").
- The out-of-phase releases v1.2.0, v1.2.1 and v1.3.0 never touched it. In `3094223`, the
  manifest edit was the phase-014 proposal entry only.

So **no release-driven manifest edit**. Under D1, the manifest **is** edited, because its
phase-014 note names v1.3.0 as the pilot tag (Section 2B, M1/M2). The note gets an
append-only "-> RE-BASELINED" clause, the house pattern ("-> ACTIVATED", "-> COMPLETE",
"-> RELEASED"). `updated_at` rolls to 2026-10-08, as `3094223` did.

**P5: run_state.** The file is Orchestrator-owned and already carries the two release events
and the D1 event. This plan specifies **no** run_state edit. It is committed as-is (Section 3).

**P6: DEBT.md is untouched.** No new debt is created. NDEBT-044(e) (the stale Current
Position open-debt count) is deliberately **not** rolled here; see Q1.

## 2A. Edits — release records

Notation: a `~~~text` block holds literal file text. Each edit replaces exactly one
occurrence of "Current" with "New". Edits to the same file apply in the order listed.

#### R1 — `docs/planning/ROADMAP.md`
Current:
~~~text
version: 0.44.0
status: active
~~~
New:
~~~text
version: 0.45.0
status: active
~~~

#### R2 — `docs/planning/ROADMAP.md`
Current:
~~~text
change_log:
  - version: "0.44.0"
~~~
New:
~~~text
change_log:
  - version: "0.45.0"
    date: "2026-10-08"
    summary: "v1.4.0 RELEASED (post-release refresh, the 0.39.0/0.42.0 precedent) + the phase-014 re-baseline under operator decision D1. Release: after PR #63 merged at 9edd5d0, the operator authorized the tag act verbatim ('merged — authorized to tag v1.4.0', recorded in run_state before the act per NDEBT-018); the Orchestrator pushed annotated tag v1.4.0 (tag object bb32064) at that reviewed commit; release.yml run 37763448754 succeeded with the blocking tag-mode close-out passing and published GitHub Release 'Nizam v1.4.0 — Simplification Review & GA Gate protocols, draft (MINOR)' from the [1.4.0] CHANGELOG section at 2026-10-08T10:26:22Z. Current Position: the release-preparation bullet is removed and the latest-released disposition rolls to name v1.4.0 -- keeping exactly one body line matching the close-out gate's V-scoped disposition pattern at V=1.4.0 -- with the v1.3.0 bullet relabelled 'Prior released tag' and the v1.2.1 anomaly bullet relabelled 'Earlier released tag' (both bodies unedited). Phase 014: under D1 (operator verbatim 'proceed with the logic next steps to complete the backlog.', 2026-10-08, recorded in run_state before the act; not H-PHASE-014) the factual re-baseline that the 0.44.0 release-fact paragraph called for is APPLIED in this change -- feature 100's pilot pin v1.3.0 -> v1.4.0 and feature 102's tag-absence assertion v1.4.0 -> v1.5.0 (product_spec_014 1.0.1, feature_list_014, phase_014.yaml, the manifest phase-014 note) -- recorded in a dated paragraph below the unedited banner; phase 014 stays pending/proposed, awaiting H-PHASE-014. The NIP-0003 section's release wording moves to past tense (expected v1.5.0 / v1.6.0 unchanged; the NIP is unedited pending H-NIP). DEBT.md is untouched; the stale Current Position open-debt count (NDEBT-044(e)) is not rolled here."
  - version: "0.44.0"
~~~

#### R4 — `docs/planning/ROADMAP.md` (phase-014 note; the banner and the 0.44.0 paragraph stay unedited)
Current:
~~~text
the phase-014 artifacts is required before `H-PHASE-014` is presented; the release
preparation edits none of them.
~~~
New:
~~~text
the phase-014 artifacts is required before `H-PHASE-014` is presented; the release
preparation edits none of them.

**Re-baseline APPLIED (2026-10-08, v1.4.0 post-release refresh; the paragraphs above
are unedited).** `v1.4.0` is released (annotated tag object `bb32064` at `9edd5d0`;
`release.yml` run 37763448754 SUCCESS), so the premises named above became actually
false: feature 102's tag-absence acceptance test fails once the `v1.4.0` ref exists.
Under operator decision D1, given 2026-10-08 with the verbatim words
"proceed with the logic next steps to complete the backlog."
and recorded in `.agent/run_state.json` as an `operator_gate_decision` before the act per
NDEBT-018 (D1 is not `H-PHASE-014`), this change applies the factual re-baseline.
Feature 100's pilot pin moves from `v1.3.0` to `v1.4.0`, the latest released immutable
tag, which also carries the draft `ecosystem/06`/`08` documents that feature 099
activates; this supersedes the `v1.3.0` in item 2 of the scope list above. Feature 102's
tag-absence assertion and the spec's matching criterion move from `v1.4.0` to `v1.5.0`,
the next MINOR, keeping their meaning: phase 014 cuts no release, and the pipeline never
self-tags. Edited: `.agent/product_spec_014.md` (1.0.0 → 1.0.1),
`.agent/feature_list_014.json` (`spec_version` in lockstep),
`docs/planning/phase_014.yaml`, and the manifest's phase-014 note. Scope, dependencies,
estimates (2200) and every status are unchanged. Phase 014 stays `pending` / `proposed`
and is activation-ready, awaiting `H-PHASE-014`.
~~~

#### R7 — `docs/planning/ROADMAP.md` (NIP-0003 section; expected versions already v1.5.0 / v1.6.0; tense only)
Current:
~~~text
NIP's own text still says v1.4.0, which the 2026-10-08 release preparation takes) and
~~~
New:
~~~text
NIP's own text still says v1.4.0, which the 2026-10-08 v1.4.0 release took) and
~~~

#### R5 — `docs/planning/ROADMAP.md` (Current Position: prep bullet out, v1.4.0 in, v1.3.0 relabelled)
Current:
~~~text
- **Release in preparation: v1.4.0 (MINOR) — awaiting `H-FRAMEWORK-RELEASE`.** Requested
  by the operator 2026-10-08. The consumer-reaching content since v1.3.0 is exactly the
  two proposal-grade ecosystem lifecycle protocol documents landed with the phase-014
  proposal (PR #61) — `ecosystem/06_simplification_review.md` (Repeat) and
  `ecosystem/08_ga_gate.md` (Promote/GA), both `status: draft` and not yet normative
  (their activation awaits phase-014 feature 099 under `H-PHASE-014`) — plus their
  `ecosystem/README.md` rows and `NIZAM.json` ecosystem `key_documents` entries.
  Everything else since v1.3.0 (the phase-014 Planner artifacts, these planning
  records, and the NIP-0003 proposal, PR #62) is framework-envelope only. MINOR per
  `methodology/06_release_train.md` Section 3.2 (new optional protocol documents;
  nothing that validated under v1.3.0 is invalidated), rounded up per Section 3.4. This
  release-preparation change synchronizes every C10 version anchor to 1.4.0 and cuts
  the dated `[1.4.0]` CHANGELOG section; the readiness record
  (`.agent/evidence/release-readiness-v1.4.0.md`) is written by the Evaluator after
  independently re-running the checks. The `H-FRAMEWORK-RELEASE` sign-off and tag remain
  outstanding — the pipeline never self-tags.
- **Latest released tag: v1.3.0 (MINOR) — RELEASED 2026-09-30 at `2e122256` (PR #60).**
~~~
New:
~~~text
- **Latest released tag: v1.4.0 (MINOR) — RELEASED 2026-10-08 at `9edd5d0` (PR #63).**
  After PR #63 merged, the operator authorized the tag act with the verbatim words
  "merged — authorized to tag v1.4.0"
  (recorded in `.agent/run_state.json` before the act per NDEBT-018). Under that
  authorization the Orchestrator pushed the annotated tag `v1.4.0` (tag object `bb32064`,
  tagged 2026-10-08T10:26:01Z) at the reviewed merge commit; the pipeline never
  self-tags. `release.yml` run 37763448754 succeeded — the blocking tag-mode close-out
  passed — and published
  [the GitHub Release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.4.0)
  'Nizam v1.4.0 — Simplification Review & GA Gate protocols, draft (MINOR)' from the
  `[1.4.0]` CHANGELOG section at 2026-10-08T10:26:22Z. It packages the proposal-grade
  `ecosystem/06_simplification_review.md` and `ecosystem/08_ga_gate.md` (both
  `status: draft`, not yet normative; activation awaits phase-014 feature 099 under
  `H-PHASE-014`). The README quick-start replayed at `v1.4.0` installed framework
  version 1.4.0 (`.agent/evidence/release-v1.4.0-tag/06-consumer-quickstart.txt`).
- **Prior released tag: v1.3.0 (MINOR) — RELEASED 2026-09-30 at `2e122256` (PR #60).**
~~~

#### R6 — `docs/planning/ROADMAP.md` (v1.2.1 bullet: lead label only; body unchanged)
Current:
~~~text
- **Prior released tag: v1.2.1 (PATCH) — tagged 2026-09-19; the recorded anomaly.** Its
~~~
New:
~~~text
- **Earlier released tag: v1.2.1 (PATCH) — tagged 2026-09-19; the recorded anomaly.** Its
~~~

R3 is intentionally unused. The phase-014 banner (scope item 2 says `v1.3.0`) is **not**
edited. The 0.44.0 paragraph states "the banner text above is unedited", and the house
pattern annotates instead of rewriting. R4 explicitly supersedes item 2.

#### G1 — `docs/planning/operator_gates.md`
Current:
~~~text
version: 0.25.0
status: active
~~~
New:
~~~text
version: 0.26.0
status: active
~~~

#### G2 — `docs/planning/operator_gates.md`
Current:
~~~text
change_log:
  - version: "0.25.0"
~~~
New:
~~~text
change_log:
  - version: "0.26.0"
    date: "2026-10-08"
    summary: "H-FRAMEWORK-RELEASE EXECUTED for v1.4.0: after PR #63 merged at 9edd5d0, the operator authorized the tag act verbatim ('merged — authorized to tag v1.4.0', following the release request 'PR #62 has been merged, cut a new release pin/tag it.'; recorded in run_state before the act per NDEBT-018) and the Orchestrator, as the delegated methodology/06_release_train.md Section 6 mechanic, pushed annotated tag v1.4.0 (tag object bb32064) at that reviewed commit -- the pipeline never self-tags; release.yml run 37763448754 succeeded -- the blocking tag-mode close-out passed -- and published GitHub Release 'Nizam v1.4.0 — Simplification Review & GA Gate protocols, draft (MINOR)' from the [1.4.0] CHANGELOG section at 2026-10-08T10:26:22Z. The row's own v1.4.0 PREPARED clause moves to past tense ('remained OUTSTANDING at preparation time', the v0.24.0 precedent) so the cell no longer claims that no tag is recorded. Appended to the existing recurring row, not a new row. Recurring: outstanding again only for a future release. Operator decision D1 (the phase-014 re-baseline) is not a registered gate; it is recorded in run_state, ROADMAP and the manifest, not here. H-PHASE-014 stays OUTSTANDING."
  - version: "0.25.0"
~~~

#### G3 — `docs/planning/operator_gates.md` (row-anchored tail of the single `H-FRAMEWORK-RELEASE` row; the cell's pipe count is unchanged)
Current:
~~~text
tag authorization and the tag remain OUTSTANDING -- no tag authorization or tag is recorded for v1.4.0. Recurring: outstanding again at the next release. |
~~~
New:
~~~text
tag authorization and the tag remained OUTSTANDING at preparation time. **v1.4.0 EXECUTED 2026-10-08**: operator authorization verbatim 'merged — authorized to tag v1.4.0' (following the release request 'PR #62 has been merged, cut a new release pin/tag it.'; recorded in run_state before the act, NDEBT-018); annotated tag `v1.4.0` (tag object `bb32064`) pushed at `9edd5d0` (PR #63, the reviewed merge commit, tagged 2026-10-08T10:26:01Z) by the Orchestrator as the delegated Section 6 mechanic — the pipeline never self-tags; `release.yml` run 37763448754 SUCCESS (the blocking tag-mode close-out passed); GitHub Release 'Nizam v1.4.0 — Simplification Review & GA Gate protocols, draft (MINOR)' published from the `[1.4.0]` CHANGELOG section at 2026-10-08T10:26:22Z. Recurring: outstanding again at the next release. |
~~~

#### C1 — `CHANGELOG.md`
Current:
~~~text
## [Unreleased]

## [1.4.0] - 2026-10-08
~~~
New:
~~~text
## [Unreleased]

### Changed

- **v1.4.0 post-release refresh and phase-014 re-baseline** (planning records only;
  nothing `bootstrap.sh` injects changes). `docs/planning/ROADMAP.md` (v0.45.0) rolls
  Current Position to name `v1.4.0` as the latest released tag (annotated tag object
  `bb32064` at `9edd5d0`, PR #63; `release.yml` run 37763448754 succeeded with the
  blocking tag-mode close-out passing; Release published 2026-10-08T10:26:22Z) and
  removes the preparation bullet; `docs/planning/operator_gates.md` (v0.26.0) records
  `H-FRAMEWORK-RELEASE` EXECUTED for v1.4.0 on the existing row. Under operator decision
  D1 (recorded in `run_state` before the act; not `H-PHASE-014`), the pending phase-014
  proposal is re-baselined for the facts v1.4.0 made stale: feature 100's pilot pin moves
  from `v1.3.0` to `v1.4.0`, and feature 102's tag-absence assertion moves from `v1.4.0`
  to `v1.5.0`, the next MINOR (`.agent/product_spec_014.md` 1.0.1,
  `.agent/feature_list_014.json`, `docs/planning/phase_014.yaml`, and the manifest's
  phase-014 note). Phase 014 stays `pending` / `proposed`, awaiting `H-PHASE-014`.

## [1.4.0] - 2026-10-08
~~~

## 2B. Edits — phase-014 re-baseline under D1 (Orchestrator amendment, 2026-10-08)

**Authority.** This is a plan amendment under `methodology/00_planning.md` Section 9, routed
through the Planner. It cites the recorded `run_state` history event
(`operator_gate_decision`, `at` 2026-10-08T10:30:34Z, "Decision D1 ... APPROVED", operator
verbatim "proceed with the logic next steps to complete the backlog."). The event exists in
the working-tree run_state (AH-2 verified). It is **not** `H-PHASE-014`. Every status and
`activation_state` stays as it is (V11).

**Pilot tag decision: retarget `v1.3.0` → `v1.4.0`.** One-line justification: v1.4.0 is the
latest released immutable tag, and it is the only tag carrying the `ecosystem/06`/`08`
drafts that phase 014 activates. No reason to keep v1.3.0 was found:

- The v1.3.0 pin was chosen as "a released immutable tag a real consumer can adopt"
  (spec line 36), not for v1.3.0-specific content.
- The v1.4.0 consumer quick-start is proven (evidence 06).
- Nothing in 099–102 depends on v1.3.0 content.

**Tag-absence assertion: retarget `v1.4.0` → `v1.5.0`.** The meaning is preserved: phase 014
cuts no release, and the next MINOR tag must not exist from 014's own act. `v1.5.0` is also
the expected release of the NIP-0003 phase 015 that follows 014.

**Spec version: 1.0.0 → 1.0.1 (PATCH), with `feature_list_014.json` `spec_version` in
lockstep.** This follows the `product_spec_013` 1.1.2 precedent: a "factual correction of
acceptance-test commands; design intent unchanged" was a PATCH, with the feature list
bumped in lockstep. Lockstep keeps the Drift Detection Gate quiet: spec and feature list
both read 1.0.1 (V11).

**Estimate.** `original_estimate_lines` stays 2200 and the per-feature estimates stay
400/900/400/500. The pilot does the same work at a different tag (one bootstrap per
member). No scope-budget re-baseline is needed (Section 9's `rebaseline` record does not
apply).

**Deliberately unedited (AH-2, detect before fix).**

- `product_spec_014.md` lines 161–162: "`H-FRAMEWORK-RELEASE`: not in this phase's scope (no
  release is prepared by phase 014)". This is **still true**. v1.4.0 was cut out-of-phase,
  and the ROADMAP NIP-0003 section has phase 015 roll up 014's unreleased changes.
- Spec lines 4, 16 and 36 and the feature list's "authored 2026-09-30 after the v1.3.0
  release": historical facts, still true.
- The spec's "run_state is untouched until activation" (lines 26–28): see Q3.
- `phase_014.yaml` cannot carry a re-baseline note, because `schema/phase.schema.json` has
  `additionalProperties: false` and no change_log key. Its record is the manifest note and
  the spec change_log.

#### S1 — `.agent/product_spec_014.md`
Current:
~~~text
last_audited: "2026-09-30"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-09-30T10:24:00Z"
updated_at: "2026-09-30T10:24:00Z"
change_log:
~~~
New:
~~~text
last_audited: "2026-10-08"
authoritative_source: NA
version: 1.0.1
spec_version: "1.0.1"
created_at: "2026-09-30T10:24:00Z"
updated_at: "2026-10-08T10:33:25Z"
change_log:
  - version: "1.0.1"
    date: "2026-10-08T10:33:25Z"
    summary: "PLAN AMENDMENT per methodology/00_planning.md Section 9 (factual re-baseline; design intent unchanged), routed through the Planner and applied in the v1.4.0 post-release refresh under operator decision D1 (verbatim 'proceed with the logic next steps to complete the backlog.', 2026-10-08), the authorization event recorded in .agent/run_state.json history (operator_gate_decision at 2026-10-08T10:30:34Z) before the act per NDEBT-018 -- not H-PHASE-014. The operator-authorized out-of-phase v1.4.0 release (tag object bb32064 at 9edd5d0) falsified two premises authored at v1.3.0: (1) the pilot pin -- feature 100 now targets the released immutable tag v1.4.0, the latest, which also carries the draft ecosystem/06 and 08 documents that feature 099 activates; (2) the tag-absence acceptance criterion -- retargeted to v1.5.0, the next MINOR, preserving its meaning (phase 014 cuts no release; the pipeline never self-tags). Scope, features, dependencies, estimates (2200) and status (draft) are unchanged; the 'no release is prepared by phase 014' gate text stays, still true. PATCH per the product_spec_013 1.1.2 precedent (factual correction of acceptance-test commands, design intent unchanged); .agent/feature_list_014.json spec_version moves to 1.0.1 in lockstep."
~~~

#### S2 — `.agent/product_spec_014.md`
Current:
~~~text
2. **100 — the real, non-scratch multi-repo ecosystem pilot at the released immutable
   tag v1.3.0.** The operator-designated real repositories — the framework hardcodes
~~~
New:
~~~text
2. **100 — the real, non-scratch multi-repo ecosystem pilot at the released immutable
   tag v1.4.0.** The operator-designated real repositories — the framework hardcodes
~~~

#### S3 — `.agent/product_spec_014.md`
Current:
~~~text
- **100** — the real, non-scratch multi-repo pilot at tag v1.3.0. Root.
~~~
New:
~~~text
- **100** — the real, non-scratch multi-repo pilot at tag v1.4.0. Root.
~~~

#### S4 — `.agent/product_spec_014.md`
Current:
~~~text
- At proposal time exactly zero v1.4.0 refs exist (no tag, no release prep — the
  pipeline never self-tags): `git rev-parse -q --verify refs/tags/v1.4.0` returns
  non-zero.
~~~
New:
~~~text
- At proposal time exactly zero v1.5.0 refs exist (no tag, no release prep — the
  pipeline never self-tags): `git rev-parse -q --verify refs/tags/v1.5.0` returns
  non-zero. (Re-baselined 2026-10-08 under D1 from the next-MINOR target of the
  v1.3.0 era, which the operator-authorized out-of-phase v1.4.0 release made false.)
~~~

#### F1 — `.agent/feature_list_014.json`
Current:
~~~text
  "spec_version": "1.0.0",
~~~
New:
~~~text
  "spec_version": "1.0.1",
~~~

#### F2 — `.agent/feature_list_014.json` (planning_note tail; within the line-5 JSON string)
Current:
~~~text
no feature enters contract negotiation before that authorization.",
~~~
New:
~~~text
no feature enters contract negotiation before that authorization. RE-BASELINED 2026-10-08 (spec 1.0.1) under operator decision D1, recorded in run_state before the act (not H-PHASE-014): the v1.4.0 release moved feature 100's pilot pin from v1.3.0 to v1.4.0 and feature 102's tag-absence assertion to v1.5.0, the next MINOR; scope, dependencies, estimates and statuses unchanged.",
~~~

#### F3 — `.agent/feature_list_014.json` (feature 100 `name`)
Current:
~~~text
"name": "Real, non-scratch multi-repo ecosystem pilot at the released v1.3.0 tag",
~~~
New:
~~~text
"name": "Real, non-scratch multi-repo ecosystem pilot at the released v1.4.0 tag",
~~~

#### F4 — `.agent/feature_list_014.json` (feature 100 `description`, substring of line 25)
Current:
~~~text
each adopted/upgraded to the released immutable tag v1.3.0 under a recorded per-member
~~~
New:
~~~text
each adopted/upgraded to the released immutable tag v1.4.0 under a recorded per-member
~~~

#### F5 — `.agent/feature_list_014.json` (feature 102 `acceptance_tests[3]`)
Current:
~~~text
"git rev-parse -q --verify refs/tags/v1.4.0; test $? -eq 1",
~~~
New:
~~~text
"git rev-parse -q --verify refs/tags/v1.5.0; test $? -eq 1",
~~~

#### Y1 — `docs/planning/phase_014.yaml` (line 3)
Current:
~~~text
description: Run the real non-scratch multi-repo pilot at the released v1.3.0 tag, activate
~~~
New:
~~~text
description: Run the real non-scratch multi-repo pilot at the released v1.4.0 tag, activate
~~~

#### Y2 — `docs/planning/phase_014.yaml` (line 10)
Current:
~~~text
    description: Real, non-scratch multi-repo ecosystem pilot at the released v1.3.0 tag.
~~~
New:
~~~text
    description: Real, non-scratch multi-repo ecosystem pilot at the released v1.4.0 tag.
~~~

#### M1 — `docs/planning/manifest.json`
Current:
~~~text
  "updated_at": "2026-09-30",
~~~
New:
~~~text
  "updated_at": "2026-10-08",
~~~

#### M2 — `docs/planning/manifest.json` (append-only to the phase-014 `note`; earlier text unchanged)
Current:
~~~text
Awaiting operator gate H-PHASE-014; no feature enters contract negotiation before it. Forward planning: docs/planning/ROADMAP.md."
~~~
New:
~~~text
Awaiting operator gate H-PHASE-014; no feature enters contract negotiation before it. Forward planning: docs/planning/ROADMAP.md. -> RE-BASELINED 2026-10-08 under operator decision D1 (verbatim 'proceed with the logic next steps to complete the backlog.', recorded in .agent/run_state.json as operator_gate_decision before the act per NDEBT-018; NOT H-PHASE-014): the out-of-phase v1.4.0 release (tag at 9edd5d0) falsified two v1.3.0-era premises, so feature 100's pilot pin moves from v1.3.0 to the released immutable tag v1.4.0 and feature 102's tag-absence assertion moves to v1.5.0 (the next MINOR); product_spec_014 1.0.0 -> 1.0.1 with feature_list_014 in lockstep; the phase_014.yaml descriptions follow. Scope, dependencies, estimates (2200) and status/activation_state (pending/proposed) unchanged; still awaiting H-PHASE-014."
~~~

**Total edits: 23 Current/New pairs across 7 generator files.** The pairs are R1, R2, R4,
R5, R6, R7, G1–G3, C1, S1–S4, F1–F5, Y1, Y2, M1 and M2. The 7 files are `CHANGELOG.md`,
`docs/planning/ROADMAP.md`, `docs/planning/operator_gates.md`,
`docs/planning/manifest.json`, `docs/planning/phase_014.yaml`,
`.agent/feature_list_014.json` and `.agent/product_spec_014.md`. `.agent/run_state.json`
is the eighth `M` path in the scope guard; the Orchestrator owns it and the generator
never edits it.

## 3. Scope

**Generator edits exactly 7 files:**

- `CHANGELOG.md`
- `docs/planning/ROADMAP.md`
- `docs/planning/operator_gates.md`
- `docs/planning/manifest.json`
- `docs/planning/phase_014.yaml`
- `.agent/feature_list_014.json`
- `.agent/product_spec_014.md`

**Committed as-is by the Orchestrator (not edited by the generator):**

- `.agent/run_state.json` (`M`). It carries the `operator_gate_decision` and
  `release_executed` events for v1.4.0, plus the D1 `operator_gate_decision`.
- `.agent/evidence/release-v1.4.0-tag/01-tag-object.txt` … `06-consumer-quickstart.txt`
- `.agent/evidence/release-v1.4.0-post-release/` (this plan, `00-refresh-plan.md`, plus the
  evaluator's outputs)
- `.agent/validator/release-v1.4.0-refresh-*.json` (the validator's verdicts)

**MUST NOT TOUCH** (any diff here is a Mode B rejection):

- `docs/nips/*`
- `docs/planning/DEBT.md`
- `README.md`, `CONTEXT.md`, `NIZAM.json`, `docs/guide/`
- `.github/` (including `release_closeout.py`)
- the payload directories `methodology/`, `schema/`, `tools/`, `standard/`, `templates/`,
  `ecosystem/`, `registry/`, and `bootstrap.sh`
- every other `.agent/*` file, including `product_spec_013.md`, `feature_list_013.json`
  and `feature_list.json`

The release anchors stay at 1.4.0, because NIZAM.json, CONTEXT.md, README.md, the guide and
CHANGELOG `[1.4.0]` are all untouched.

**Scope guard (untracked-aware, authoritative), V12 below.**

- Input: the union of `git diff --name-status 9edd5d0` (every tracked change, committed or
  not) and `git ls-files --others --exclude-standard`.
- Change from the prep plan's guard: the evidence, plan and validator entries are allowed
  as `??` **or** `A`. The prep guard allowed only `??`, so it would have failed spuriously
  after the Orchestrator commits.
- Every `M` entry must be present.
- Paths are matched by anchored regex over `[A-Za-z0-9._-]` names, with no `/` inside the
  name. Sub-directories, sibling prefixes and `..` traversal therefore fail closed. Quoted
  paths also fail.

## 4. Verification (evaluator runs; every command fenced, real pipes)

Each block below is labelled `#Vn`. Expected results are stated under each block.

**#V1**
```sh
bash tools/validate.sh 2>&1 | tail -1; echo "exit=${PIPESTATUS[0]}"
```
Expected: `SUMMARY: 16 passed, 0 failed`, then `exit=0`. This includes C5, which sweeps
CHANGELOG, and C16, the feature-list schema plus lifecycle check.

**#V2**
```sh
bash tools/fixtures_self_test.sh 2>&1 | tail -1; echo "exit=${PIPESTATUS[0]}"
```
Expected: `SELF-TEST OK: 79/79 fixtures accounted for, 0 failed`, then `exit=0`.

**#V3**
```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/release_closeout.py --mode pr; echo "exit=$?"
```
Expected: 5 `PASS` lines, then
`Release close-out: all internal version anchors agree with V=1.4.0 (--mode pr).`, then
`exit=0`.

**#V4**
```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/release_closeout.py --mode tag --tag v1.4.0 | grep -c '^PASS'; echo "exit=${PIPESTATUS[0]}"
```
Expected: `9`, then `exit=0`. Tag mode reads the anchors at the tag, not HEAD; this confirms
the refresh cannot disturb it.

**#V5**: ROADMAP body disposition counts.
```sh
PYTHONDONTWRITEBYTECODE=1 python3 -c "import re,sys;sys.path.insert(0,'.github/scripts');import release_closeout as r;b=r.document_body(open('docs/planning/ROADMAP.md').read()).splitlines();c=lambda p:sum(1 for l in b if re.search(p,l));print(c(r'Latest released tag: v1\.4\.0\b'),c(r'Release in preparation: v1\.4\.0\b'),c(r'Latest released tag: v1\.3\.0\b'),c(r'Prior released tag: v1\.3\.0\b'),c(r'Prior released tag:'),c(r'Latest released tag:'),c(r'Release in preparation:'))"
```
Expected: `1 0 0 1 1 1 0`. In order, these are:

1. exactly one `Latest released tag: v1.4.0` line;
2. zero `Release in preparation: v1.4.0` lines;
3. v1.3.0 is no longer "Latest";
4. v1.3.0 is the single "Prior" line;
5. one "Prior" line in total;
6. one "Latest" line in total;
7. no preparation bullet left in the body.

**#V6**: no brand token on any added line in the edited files.
```sh
git diff -U0 9edd5d0 -- CHANGELOG.md docs/planning/ROADMAP.md docs/planning/operator_gates.md docs/planning/manifest.json docs/planning/phase_014.yaml .agent/feature_list_014.json .agent/product_spec_014.md | grep -E '^\+' | grep -vE '^\+\+\+ ' | grep -icE 'n[i]zamiq|\.svc|cluster\.local'
```
Expected: `0`. Grep exits 1 on zero matches, which is expected. CHANGELOG is the only
C5-swept file among the seven; the check covers all seven and is case-insensitive, so it is
stricter than C5.

**#V6-control**: proves #V6's tail is not vacuous. The token is assembled at run time.
```sh
printf '%s\n' '+++ b/x' "+x $(printf 'n%szamiq' i) y" '+host.svc' ' +ctx-line' | grep -E '^\+' | grep -vE '^\+\+\+ ' | grep -icE 'n[i]zamiq|\.svc|cluster\.local'
```
Expected: `2`.

**#V7**: schema validity of the three phase-014-related JSON/YAML files.
```sh
python3 -c "import json,yaml,jsonschema;L=lambda p:json.load(open(p));jsonschema.validate(L('.agent/feature_list_014.json'),L('schema/feature_list.schema.json'));jsonschema.validate(yaml.safe_load(open('docs/planning/phase_014.yaml')),L('schema/phase.schema.json'));jsonschema.validate(L('docs/planning/manifest.json'),L('schema/manifest.schema.json'));print('schemas OK')"; echo "exit=$?"
```
Expected: `schemas OK`, then `exit=0`.

**#V8**: no phase-014 artifact still asserts "no v1.4.0 tag", and the retargets landed.
```sh
grep -cE 'refs/tags/v1\.4\.0|zero v1\.4\.0 refs' .agent/feature_list_014.json .agent/product_spec_014.md docs/planning/phase_014.yaml docs/planning/manifest.json
python3 -c "import json,yaml;f={x['id']:x for x in json.load(open('.agent/feature_list_014.json'))['features']};t=f['102']['acceptance_tests'];print('102_retarget', 'git rev-parse -q --verify refs/tags/v1.5.0; test \$? -eq 1' in t and not any('v1.4.0' in a for a in t));print('100_pin', 'v1.4.0' in f['100']['name'] and 'tag v1.4.0' in f['100']['description'] and 'v1.3.0' not in f['100']['name']+f['100']['description']);y=open('docs/planning/phase_014.yaml').read();print('yaml_pin', y.count('released v1.4.0 tag')==2 and 'v1.3.0' not in y);s=open('.agent/product_spec_014.md').read();print('spec_pin', 'tag v1.4.0.**' in s and 'pilot at tag v1.4.0. Root.' in s and 'refs/tags/v1.5.0' in s)"
bash -c 'git rev-parse -q --verify refs/tags/v1.5.0; test $? -eq 1'; echo "retargeted_102_test_exit=$?"
```
Expected:

1. Four lines, each ending `:0`.
2. `102_retarget True`, `100_pin True`, `yaml_pin True`, `spec_pin True`.
3. `retargeted_102_test_exit=0`, with no SHA printed.

**#V9**: no status or `activation_state` changed, structure is invariant, and the drift gate
stays quiet.
```sh
python3 - <<'PY'
import json, subprocess, yaml
B = "9edd5d0"
show = lambda p: subprocess.run(["git", "show", f"{B}:{p}"], capture_output=True, text=True, check=True).stdout
fo, fn = json.loads(show(".agent/feature_list_014.json")), json.load(open(".agent/feature_list_014.json"))
k = lambda d: [(f["id"], f["status"], f["dependencies"], f["estimated_lines"], len(f["acceptance_tests"])) for f in d["features"]]
print("features_invariant", k(fo) == k(fn) and fo["original_estimate_lines"] == fn["original_estimate_lines"] == 2200 and fo["phase"] == fn["phase"])
po, pn = yaml.safe_load(show("docs/planning/phase_014.yaml")), yaml.safe_load(open("docs/planning/phase_014.yaml"))
print("phase_yaml_invariant", po["status"] == pn["status"] == "pending" and [(s["id"], s["status"]) for s in po["steps"]] == [(s["id"], s["status"]) for s in pn["steps"]])
mo, mn = json.loads(show("docs/planning/manifest.json")), json.load(open("docs/planning/manifest.json"))
sig = lambda m: [(p["id"], p["status"], p.get("activation_state")) for p in m["phases"]]
o14 = [p for p in mo["phases"] if p["id"] == "014-ga-track"][0]; n14 = [p for p in mn["phases"] if p["id"] == "014-ga-track"][0]
rest = lambda m: [p for p in m["phases"] if p["id"] != "014-ga-track"]
print("manifest_invariant", sig(mo) == sig(mn) and (n14["status"], n14["activation_state"]) == ("pending", "proposed") and mo["current_phase"] == mn["current_phase"] == "013-definition-of-done" and rest(mo) == rest(mn) and n14["note"].startswith(o14["note"]) and {k: v for k, v in o14.items() if k != "note"} == {k: v for k, v in n14.items() if k != "note"})
fm = lambda t: yaml.safe_load(t.split("---")[1])
so, sn = fm(show(".agent/product_spec_014.md")), fm(open(".agent/product_spec_014.md").read())
print("spec_status_invariant", so["status"] == sn["status"] == "draft")
print("drift_gate_lockstep", sn["spec_version"] == fn["spec_version"] == "1.0.1" and str(sn["version"]) == "1.0.1" and sn["change_log"][0]["version"] == "1.0.1")
PY
```
Expected: five lines, each ending `True`.

**#V10**: frontmatter versions, the operator_gates row, and the CHANGELOG shape.
```sh
python3 - <<'PY'
import yaml
fm = lambda p: yaml.safe_load(open(p).read().split("---")[1])
r, g = fm("docs/planning/ROADMAP.md"), fm("docs/planning/operator_gates.md")
print("roadmap_fm", r["version"], r["change_log"][0]["version"])
print("gates_fm", g["version"], g["change_log"][0]["version"])
rows = [l for l in open("docs/planning/operator_gates.md").read().splitlines() if l.startswith("| `H-FRAMEWORK-RELEASE`")]
row = rows[0]
need = ["**v1.4.0 EXECUTED 2026-10-08**", "'merged — authorized to tag v1.4.0'", "'PR #62 has been merged, cut a new release pin/tag it.'", "recorded in run_state before the act, NDEBT-018", "`9edd5d0`", "37763448754 SUCCESS", "2026-10-08T10:26:22Z"]
print("gates_row", len(rows) == 1, all(n in row for n in need), row.count("|") == 5, row.endswith("Recurring: outstanding again at the next release. |"), "no tag authorization or tag is recorded for v1.4.0" not in row)
t = open("CHANGELOG.md").read().split("\n"); i = t.index("## [Unreleased]")
print("changelog", t[i + 1:i + 4] == ["", "### Changed", ""], [l for l in t[i + 1:] if l.startswith("## [")][0] == "## [1.4.0] - 2026-10-08")
PY
```
Expected:

1. `roadmap_fm 0.45.0 0.45.0`
2. `gates_fm 0.26.0 0.26.0`
3. `gates_row True True True True True`
4. `changelog True True`

**#V11**: forbidden tracked paths are unchanged (V12 also covers untracked).
```sh
git diff 9edd5d0 -- docs/nips docs/planning/DEBT.md README.md CONTEXT.md NIZAM.json docs/guide .github bootstrap.sh methodology schema tools standard templates ecosystem registry .agent/product_spec_013.md .agent/feature_list_013.json .agent/feature_list.json | wc -c
```
Expected: `0`.

**#V12**: untracked-aware scope guard.
```sh
scope_guard() {
  awk '
    BEGIN {
      n = split("CHANGELOG.md docs/planning/ROADMAP.md docs/planning/operator_gates.md docs/planning/manifest.json docs/planning/phase_014.yaml .agent/feature_list_014.json .agent/product_spec_014.md .agent/run_state.json", g, " ")
      for (i = 1; i <= n; i++) want["M " g[i]] = 1
      bad = 0
    }
    ($0 in want) { seen[$0] = 1; next }
    $0 ~ /^(\?\?|A) \.agent\/evidence\/release-v1\.4\.0-tag\/0[1-6]-[A-Za-z0-9._-]+\.txt$/ && $0 !~ /\.\./ { next }
    $0 ~ /^(\?\?|A) \.agent\/evidence\/release-v1\.4\.0-post-release\/[A-Za-z0-9._-]+$/ && $0 !~ /\.\./ { next }
    $0 ~ /^(\?\?|A) \.agent\/validator\/release-v1\.4\.0-refresh-[A-Za-z0-9._-]+\.json$/ && $0 !~ /\.\./ { next }
    { print "UNEXPECTED: " $0; bad = 1 }
    END {
      for (k in want) if (!(k in seen)) { print "MISSING: " k; bad = 1 }
      exit bad
    }'
}
{ git diff --name-status 9edd5d0 | awk -F '\t' '{ print $1 " " $2 (NF > 2 ? " -> " $3 : "") }'
  git ls-files --others --exclude-standard | sed 's/^/?? /'
} | scope_guard; echo "scope_guard_exit=$?"
```
Expected: no `UNEXPECTED:` and no `MISSING:` lines, then `scope_guard_exit=0`. This holds
both before and after the Orchestrator's commit, because `A` and `??` are treated alike.

**#V12-control** (run in the same shell after defining `scope_guard`; synthetic input only)
```sh
OK8='M CHANGELOG.md
M docs/planning/ROADMAP.md
M docs/planning/operator_gates.md
M docs/planning/manifest.json
M docs/planning/phase_014.yaml
M .agent/feature_list_014.json
M .agent/product_spec_014.md
M .agent/run_state.json'
printf '%s\n' "$OK8" '?? .agent/evidence/release-v1.4.0-tag/01-tag-object.txt' 'A .agent/evidence/release-v1.4.0-tag/06-consumer-quickstart.txt' 'A .agent/evidence/release-v1.4.0-post-release/00-refresh-plan.md' '?? .agent/evidence/release-v1.4.0-post-release/01-validate-sh.txt' '?? .agent/validator/release-v1.4.0-refresh-plan.json' | scope_guard; echo "positive_exit=$?"
printf '%s\n' "$OK8" '?? docs/nips/NIP-0004-x.md' | scope_guard; echo "neg_untracked_forbidden_exit=$?"
printf '%s\n' "$OK8" 'M README.md' | scope_guard; echo "neg_tracked_forbidden_exit=$?"
printf '%s\n' "$OK8" 'M docs/planning/DEBT.md' | scope_guard; echo "neg_debt_exit=$?"
printf '%s\n' "$OK8" 'M .agent/product_spec_013.md' | scope_guard; echo "neg_other_agent_file_exit=$?"
printf '%s\n' "$OK8" '?? .agent/evidence/release-v1.4.0-post-release-x/evil.txt' | scope_guard; echo "neg_sibling_prefix_exit=$?"
printf '%s\n' "$OK8" '?? .agent/evidence/release-v1.4.0-post-release/sub/evil.txt' | scope_guard; echo "neg_subdir_exit=$?"
printf '%s\n' "$OK8" '?? .agent/evidence/release-v1.4.0-tag/07-extra.txt' | scope_guard; echo "neg_tag_dir_extra_exit=$?"
printf '%s\n' "$OK8" '?? .agent/validator/release-v1.4.0-refresh-../../ecosystem/x.json' | scope_guard; echo "neg_traversal_exit=$?"
printf '%s\n' "$OK8" '?? .agent/validator/release-v1.4.0-plan2.json' | scope_guard; echo "neg_validator_name_exit=$?"
printf '%s\n' "$OK8" | grep -v 'phase_014.yaml' | scope_guard; echo "neg_missing_file_exit=$?"
printf '%s\n' "$OK8" | grep -v 'run_state.json' | scope_guard; echo "neg_missing_run_state_exit=$?"
printf '%s\n' "$OK8" | sed 's/^M \.agent\/product_spec_014\.md$/D .agent\/product_spec_014.md/' | scope_guard; echo "neg_wrong_status_exit=$?"
```
Expected: `positive_exit=0`. Every `neg_*_exit=1`, with the matching `UNEXPECTED:` or
`MISSING:` line printed (13 negatives).

Mode B note: `git diff HEAD` (or `git diff 9edd5d0`) must show only the 23 hunks of
Section 2 across the 7 generator files, plus the Orchestrator-owned run_state events.
e2e is not required, because no payload file changes (V11). The v1.1.0/v1.3.0 refreshes
did not run it either.

## 5. Planner self-check

The planner did a dry-run in an isolated scratch clone. It extracted every Current/New pair
from this file programmatically, without retyping, and asserted count = 1 before each
replacement. It then copied in the working-tree run_state, the `release-v1.4.0-tag/`
evidence and this plan, and ran every fenced `#Vn` block verbatim. No file in the real
repository other than this plan was written. Results are recorded in Section 5.1.

### 5.1 Dry-run output

Setup:

- A scratch clone (`git clone --no-checkout` of this repo) was checked out detached at
  `9edd5d0`.
- The working-tree `.agent/run_state.json` was copied in, with the D1 event (231 history
  entries).
- `release-v1.4.0-tag/01..06` and this plan were copied in.
- `PYTHONDONTWRITEBYTECODE=1` was set.

Captured output:

~~~
applied pairs: 23 files: 7 [.agent/feature_list_014.json, .agent/product_spec_014.md, CHANGELOG.md,
  docs/planning/ROADMAP.md, docs/planning/manifest.json, docs/planning/operator_gates.md,
  docs/planning/phase_014.yaml]            (every Current block count == 1)
#V1   SUMMARY: 16 passed, 0 failed / exit=0
#V2   SELF-TEST OK: 79/79 fixtures accounted for, 0 failed / exit=0
#V3   5 x PASS; ...agree with V=1.4.0 (--mode pr). / exit=0
#V4   9 / exit=0
#V5   1 0 0 1 1 1 0
#V6   0
#V6-control  2
#V7   schemas OK / exit=0
#V8   .agent/feature_list_014.json:0  .agent/product_spec_014.md:0  docs/planning/phase_014.yaml:0
      docs/planning/manifest.json:0 / 102_retarget True / 100_pin True / yaml_pin True / spec_pin True
      retargeted_102_test_exit=0
#V9   features_invariant True / phase_yaml_invariant True / manifest_invariant True
      spec_status_invariant True / drift_gate_lockstep True
#V10  roadmap_fm 0.45.0 0.45.0 / gates_fm 0.26.0 0.26.0 / gates_row True True True True True
      changelog True True
#V11  0
#V12  scope_guard_exit=0   (no UNEXPECTED / MISSING)
#V12-control  positive_exit=0; all 13 neg_*_exit=1, each with its UNEXPECTED:/MISSING: line
#V12 after committing everything in the sim (evidence now 'A', 7 A + 8 M): scope_guard_exit=0
~~~

Additional planner checks:

- The first dry-run (revision 0 of the harness) caught a defect in this plan's own #V9:
  the older manifest phase entries have no `activation_state`, which raised `KeyError`. The plan now
  uses `p.get(...)`. The second run above is clean.
- This plan file has a case-insensitive brand-token count of 0, because every regex writes
  it as `n[i]zamiq`.
- #V12 in the **real** repo now, before any generator edit, gives `scope_guard_exit=1`. The
  output has exactly 7 `MISSING:` lines (the generator files) and 0 `UNEXPECTED:` lines.
  `M .agent/run_state.json` and both `??` evidence dirs are already allowed.
- Feature 102's **current** test exits 1 (the v1.4.0 ref resolves). The retargeted v1.5.0
  test exits 0. No `v1.5.0` ref exists, either locally or in `ls-remote` (exit 0, empty
  output).

Side effects: none in the real repository. The sim clones live only in the session
scratchpad, and the only real-repo write is this file.

## 6. Open questions (none blocks this refresh)

- **Q1: NDEBT-044(e) is deferred.** Current Position still says "Open debt (current, at
  DEBT.md v0.40.0): two rows remain Open". NDEBT-044(e) asks for this to be rolled "at the
  next ROADMAP Current Position refresh". This refresh rolls only the disposition ladder,
  as 0.42.0 did. Rolling the count properly also means reconciling the NDEBT-044 bundle row
  in `DEBT.md`, which is out of this PR's scope. Recommendation: fold it into the
  phase-014 101 simplification-review inputs or a small hygiene PR. Orchestrator: accept
  the deferral, or authorize an R8 + DEBT.md edit.
- **Q2: the time-fragility of feature 102's tag-absence test.** The retarget keeps the
  meaning ("phase 014 cuts no release"). But any out-of-phase `v1.5.0` cut before 014
  closes would falsify it again, which is exactly what v1.4.0 did. A phase-scoped
  formulation would be robust: for example, "no tag points at a commit made by a phase-014
  feature". That would change the test's shape, which is outside D1's "factual retargets
  only". Flagged for the planner's activation-time review under `H-PHASE-014`; not done
  here.
- **Q3: spec "run_state untouched until activation".** `product_spec_014` (lines 26–28) and
  the manifest note say run_state is untouched until activation. run_state now carries the
  D1 event, which names phase 014. Its phase position (`current_phase`, `status`) is
  untouched, which is the claim's evident intent, so the text is left as-is. If the
  validator reads it literally, a one-clause PATCH clarification can be added in a later
  revision.
- **Q4: definition of D1.** D1 was defined in the Orchestrator's operator report and in the
  run_state event, which quotes its scope. No repo document previously named "D1". The
  ROADMAP, CHANGELOG, manifest and spec texts in this plan therefore always pair "D1" with
  the verbatim quote and the run_state record, so a reader can resolve it.
