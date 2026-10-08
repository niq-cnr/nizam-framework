# v1.4.0 Release-Preparation Plan (MINOR) — Planner output, awaiting @validator Mode A

- Plan author: @planner (Protocol 04). Plan only — no other file is edited by the planner.
- Branch: `chore/v1.4.0-release-prep`, cut from `main` = `669fb72` (PR #62 merged).
- Last release: `v1.3.0` (tag at `2e122256`, PR #60). No `v1.4.0` tag exists (probed below).
- Request: the operator's verbatim words, 2026-10-08, in the Orchestrator's Claude Code
  session (supplied to the planner by the Orchestrator in amendment 1): "PR #62 has been merged, cut a new release pin/tag it." This is an
  `H-FRAMEWORK-RELEASE` request, recorded (E7) as the Section 2 human sign-off for cutting the
  release preparation only. Per
  `methodology/06_release_train.md` Section 6, this change does the **durable preparation**
  only. The **tag act** is a separate Orchestrator step that happens after merge and awaits
  explicit post-merge authorization recorded in `run_state` before the act (NDEBT-018; the
  v1.1.0 precedent). Nothing in this plan creates, pushes or approves a tag.
- Amendment 1 (2026-10-08, Orchestrator decisions): Q2 accepted (E6 keeps the v1.3.0
  line); Q3 answered with the verbatim quote (E7b/E7c amended); Q4 withdrawn (already
  NDEBT-044(c)); Q1/Q5 acknowledged. Self-check re-run in Section 5.
- Every "current text" block below was re-read from HEAD `669fb72` (AH-1). Each anchor's
  uniqueness was checked with `grep -c` or `str.count` (= 1 unless noted).

---

## 0. Baseline evidence at HEAD `669fb72` (captured by the planner, read-only runs)

| Command | Result at HEAD |
|---|---|
| `bash tools/validate.sh` | `SUMMARY: 16 passed, 0 failed` |
| `bash tools/fixtures_self_test.sh` | `SELF-TEST OK: 79/79 fixtures accounted for, 0 failed` |
| `python3 .github/scripts/release_closeout.py --mode pr` | 5 x PASS, `...agree with V=1.3.0 (--mode pr).`, exit 0 |
| `bash tools/e2e_bootstrap_test.sh` | exit 0, `e2e_bootstrap_test.sh: PASS` (assert_genesis / assert_multirepo / assert_stage4 OK) |
| `git rev-parse -q --verify refs/tags/v1.4.0` | no output, exit 1 |
| `git ls-remote --tags origin v1.4.0` | empty output, exit 0 |
| `git status --porcelain` after the runs | empty (the harnesses leave the tree clean) |

## 1. Tier re-verification: MINOR, so v1.4.0

Consumer-reaching delta `v1.3.0..HEAD`. `bootstrap.sh` injects `standard/`, `templates/`,
`schema/`, `tools/`, `methodology/`, `ecosystem/` and `NIZAM.json`. The command
`git diff --name-only v1.3.0..HEAD | grep -Ev '^(\.agent/|docs/)'` returns exactly:

- `ecosystem/06_simplification_review.md`: **new**, `status: draft`, v0.1.0
- `ecosystem/08_ga_gate.md`: **new**, `status: draft`, v0.1.0
- `ecosystem/README.md`: 0.3.0 → 0.4.0. The two rows flip from Planned to Shipped; prose only.
- `NIZAM.json`: two **added** entries in the ecosystem module's `key_documents`
  (array append; no removal or rename)
- `CHANGELOG.md` (envelope; not injected)

Nothing under `standard/`, `templates/`, `schema/`, `tools/`, `methodology/` or
`bootstrap.sh` changed. All other changes are under `.agent/` and `docs/` (envelope).

Reasoning:

- **Not MAJOR (Section 3.1).** No schema narrowed and no required key changed. No shipped
  file, module or protocol id was removed or renamed. A consumer at v1.3.0 cannot fail by
  upgrading.
- **Not PATCH (Section 3.3).** A patch "corrects an error without changing the shape". This
  change adds two new protocol files and two new index entries to the injected payload. That
  is new surface, not a correction.
- **MINOR (Section 3.2).** Section 3.2's test is "adds new, optional capability without
  invalidating anything that previously validated". Its bullet list says "at minimum", and it
  names "a new protocol document" (under `methodology/`). These two are new protocol
  documents under the injected `ecosystem/` module.
- **Section 3.4 (round up).** Someone could argue that draft, non-normative documents are
  PATCH-like. If the change straddles PATCH and MINOR, Section 3.4 requires the higher tier.

**Verdict: MINOR, so v1.4.0.** The CHANGELOG banner cites
`methodology/06_release_train.md` Section 3.2.

## 2. Edits — exact current text (HEAD) → new text

Notation: `~~~text` fences hold literal file text. An edit replaces exactly one occurrence of
"Current" with "New". Line numbers are at HEAD `669fb72`.

### E1 — `CHANGELOG.md`: roll `[Unreleased]` into a dated `[1.4.0]` section

Precedent (7441ffa, 2e12225): keep an **empty** `## [Unreleased]` heading directly above
the new dated section. The two existing `[Unreleased]` bullets (Phase 014 proposal; NIP-0003
proposal; lines 12–52) move **verbatim** under the new section's `### Added`. Only the text
between them and the headings changes. Because the bullets are unmoved in the file, the
edit is a pure insertion.

Current (lines 8–10; count = 1):
~~~text
## [Unreleased]

### Added
~~~
New:
~~~text
## [Unreleased]

## [1.4.0] - 2026-10-08

**Minor release** (`methodology/06_release_train.md` Section 3.2): consumers receive two
new ecosystem lifecycle protocol documents, `ecosystem/06_simplification_review.md`
(Repeat: recurring simplification review) and `ecosystem/08_ga_gate.md` (Promote/GA:
evidence-gated GA declaration criteria), together with their `ecosystem/README.md` rows
and `NIZAM.json` ecosystem `key_documents` entries. Both documents ship proposal-grade
(`status: draft`) and are **not yet normative**: their activation (the draft → active
flip, capability registration, and the definition of the reserved `H-CONSOLIDATION` /
`H-GA` gates) awaits phase-014 feature 099 under the operator gate `H-PHASE-014`. This is
purely additive, new-optional surface -- nothing that validated under v1.3.0 is
invalidated. Everything else in this release is framework-envelope only (planning
records, the phase-014 Planner artifacts, and the NIP-0003 proposal), none of which
`bootstrap.sh` injects. The NIP-0003 entry below quotes that proposal's own expectation
of v1.4.0 / v1.5.0 for its phases 015/016; because this release takes v1.4.0, those
phases would now release as v1.5.0 / v1.6.0 (the NIP itself stays unedited pending
`H-NIP`).

### Added
~~~

Constraints the generator must preserve:

- The heading literally starts with `## [1.4.0] - `. This is close-out group 4; the date
  is 2026-10-08.
- The section body contains `**Minor release**` and `methodology/06_release_train.md`. The
  tier-banner regex is `\*\*(Major|Minor|Patch) release\*\*`.
- The section must not contain the org-brand token C5 sweeps for (regex `n[i]zamiq`; the bracket keeps this plan's own added lines free of the literal) in any case. Validator C5 sweeps
  `CHANGELOG.md`. The C5 implementation is `grep -InE` (case-sensitive) while its help
  text says case-insensitive -- already logged as `NDEBT-044(c)` (PR #62) -- so treat any
  case as forbidden. It also must not
  contain `.svc` or `cluster.local`.
- The two rolled bullets are not reworded. They are a historical record of what each
  proposal said. The banner sentence above carries the v1.5.0 / v1.6.0 correction.

### E2 — `NIZAM.json`: `framework.version`

Current (line 4; count = 1):
~~~text
    "version": "1.3.0",
~~~
New:
~~~text
    "version": "1.4.0",
~~~

No other version-bearing field exists in `NIZAM.json`; `grep -n '"version"'` returns only
line 4. Precedent 2e12225 also changed the methodology `purpose` string, `key_documents` and
`capabilities`. Those were registration for that release's new methodology document, not
version anchors. This release adds no registration: the ecosystem `key_documents` entries
already landed in PR #61. The `capabilities` array, `tools/skill.json` and the guide card
stay with phase-014 feature 099, so **no other `NIZAM.json` change**.

### E3 — `CONTEXT.md`: frontmatter version and new `change_log[0]`

E3a. Current (line 5; count = 1):
~~~text
version: 1.3.0
status: active
~~~
New:
~~~text
version: 1.4.0
status: active
~~~

E3b. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "1.3.0"
~~~
New:
~~~text
change_log:
  - version: "1.4.0"
    date: "2026-10-08"
    summary: "Prepare the v1.4.0 MINOR release: the two proposal-grade ecosystem lifecycle protocol documents landed with the phase-014 proposal (PR #61) -- `ecosystem/06_simplification_review.md` (Repeat; consolidations only under the reserved H-CONSOLIDATION gate) and `ecosystem/08_ga_gate.md` (Promote/GA; GA declaration operator-only under the reserved H-GA gate), both `status: draft` and not yet normative (activation awaits phase-014 feature 099 under H-PHASE-014) -- plus their `ecosystem/README.md` rows and `NIZAM.json` ecosystem key_documents entries; purely additive, new-optional surface; nothing that validated under v1.3.0 is invalidated. Everything else since v1.3.0 is framework-envelope only (planning records, the phase-014 Planner artifacts, the NIP-0003 proposal). H-FRAMEWORK-RELEASE remains pending; no tag is created by the pipeline."
  - version: "1.3.0"
~~~

Gate notes:

- Close-out group 1 needs the frontmatter `^version:` and `change_log[0].version` both
  equal to 1.4.0.
- C8 needs a `change_log` entry matching the bumped version; E3b provides it.
- The CONTEXT.md body has no version string (`grep -n 'v1\.3\.0'` hits only the
  change_log), so there is no body edit.

### E4 — `README.md`: the four pins (7 occurrences on 4 lines)

E4a. Current (line 22; count = 1):
~~~text
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.3.0/bootstrap.sh -o bootstrap.sh
~~~
New:
~~~text
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.4.0/bootstrap.sh -o bootstrap.sh
~~~

E4b. Current (line 24; count = 1):
~~~text
GOVERNANCE_TAG=v1.3.0 ./bootstrap.sh --tag v1.3.0
~~~
New:
~~~text
GOVERNANCE_TAG=v1.4.0 ./bootstrap.sh --tag v1.4.0
~~~

E4c. Current (line 27; count = 1):
~~~text
`--tag v1.3.0` (equivalently `GOVERNANCE_TAG=v1.3.0`) pins the inheritance to a real
~~~
New:
~~~text
`--tag v1.4.0` (equivalently `GOVERNANCE_TAG=v1.4.0`) pins the inheritance to a real
~~~

E4d. Current (line 44; count = 1):
~~~text
See the [v1.3.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.3.0)
~~~
New:
~~~text
See the [v1.4.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.4.0)
~~~

**Leave unchanged:** line 45,
`and the [v0.9.0 → v1.0.0 migration guide](docs/migration-v1.0.0.md), and run`. Close-out
group 3's docstring (`release_closeout.py` lines 190–194) deliberately excludes the
migration-guide link. That link stays pinned to the last release that shipped a migration
guide, across no-new-migration MINOR releases (contract 097's
`migration_link_exclusion_rationale`). v1.4.0 needs no migration guide. 2e12225 also left
it untouched.

After the edit, `grep -c 'v1\.3\.0' README.md` must be 0 and `grep -o 'v1\.4\.0' README.md | wc -l`
must be 7.

### E5 — `docs/guide/index.html`: meta and footer

E5a. Current (line 6; count = 1):
~~~text
<meta name="framework-version" content="1.3.0">
~~~
New:
~~~text
<meta name="framework-version" content="1.4.0">
~~~

E5b. Current (line 670; count = 1):
~~~text
  <p>Nizam framework version <strong><span id="footer-version">1.3.0</span></strong>.</p>
~~~
New:
~~~text
  <p>Nizam framework version <strong><span id="footer-version">1.4.0</span></strong>.</p>
~~~

Close-out group 2 and C10 sub-check (3) both require these to equal `NIZAM.json`
`framework.version`.

**No guide card edits.** The ecosystem card's 06/08 entries are phase-014 feature 099
scope, per the CHANGELOG `[Unreleased]` text being rolled and the ROADMAP phase-014 banner.

### E6 — `docs/planning/ROADMAP.md`

**Correction to the dispatch brief (AH-2, detect before fix).** The brief says the existing
"Latest released tag: v1.3.0" line "must therefore be rephrased so it no longer matches the
disposition pattern". **That premise is false, so that edit is not planned:**

1. Close-out group 5 builds its pattern from V:
   `rf"Latest released tag: v{re.escape(version)}\b|Release in preparation: v{re.escape(version)}\b"`
   (`release_closeout.py` lines 276–279). At V=1.4.0, the `v1.3.0` line does not match and
   does not count. The required count of exactly 1 comes from the new
   `Release in preparation: v1.4.0` bullet alone. Tag mode at `v1.4.0` uses the same
   V-scoped pattern.
2. Precedent keeps the line unedited. In 7441ffa (v1.2.0 prep), the new "Release in
   preparation: v1.2.0" bullet went **ahead of** "Latest released tag: v1.1.0", which was
   kept as the true latest-released record. In ROADMAP 0.38.0 (v1.1.0 prep, feature 098):
   "inserted ahead of the existing released-tag bullet, which stays unedited". 2e12225
   rewrote the latest-released bullet only to **correct drift**: it was stale, not matching
   the prior release.
3. Until the operator pushes `v1.4.0`, the statement "Latest released tag: v1.3.0" is
   **true**. Rephrasing it would leave the ROADMAP with no latest-released record. The
   post-release refresh is the step that rolls it, as in 0.39.0 and 0.42.0.

So E6 inserts the new disposition bullet and keeps the v1.3.0 bullet byte-identical. This
also satisfies "v1.3.0's released facts are kept". **Orchestrator decision (amendment 1):
ACCEPTED** -- the v1.3.0 line stays unchanged and the "Release in preparation: v1.4.0"
bullet is inserted ahead of it (`release_closeout.py:276-279`; `7441ffa` precedent).

E6a. Frontmatter version. Current (line 5; count = 1):
~~~text
version: 0.43.0
status: active
~~~
New:
~~~text
version: 0.44.0
status: active
~~~

E6b. New `change_log[0]`. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "0.43.0"
~~~
New:
~~~text
change_log:
  - version: "0.44.0"
    date: "2026-10-08"
    summary: "v1.4.0 release preparation (operator-requested 2026-10-08; H-FRAMEWORK-RELEASE sign-off and tag pending): the two proposal-grade ecosystem lifecycle protocol documents landed with the phase-014 proposal (ecosystem/06_simplification_review.md and ecosystem/08_ga_gate.md, status draft, not yet normative -- activation awaits phase-014 feature 099 under H-PHASE-014) are packaged as the next MINOR release; everything else since v1.3.0 is framework-envelope only. Current Position gains the 'Release in preparation: v1.4.0' bullet ahead of the latest-released bullet, which stays unedited -- v1.3.0 remains the latest released tag until the operator tags v1.4.0, and the close-out gate's body pattern is version-scoped, so the v1.3.0 line does not count at V=1.4.0 (the 0.38.0/0.40.0 precedent). The Phase 014 banner gains a dated release-fact paragraph: once v1.4.0 is tagged, feature 102's no-v1.4.0-tag acceptance test, product_spec_014's zero-v1.4.0-refs criterion, and feature 100's v1.3.0 pilot pin are stale, so a Planner re-baseline of the phase-014 artifacts is required before H-PHASE-014 (no phase-014 artifact is edited here). The NIP-0003 queued-candidate section's expected versions roll from v1.4.0 / v1.5.0 to v1.5.0 / v1.6.0 (the NIP itself is unedited pending H-NIP). run_state, manifest and DEBT.md are untouched."
  - version: "0.43.0"
~~~

E6c. Current Position: insert the single disposition line. Current (line 730; count = 1):
~~~text
- **Latest released tag: v1.3.0 (MINOR) — RELEASED 2026-09-30 at `2e122256` (PR #60).**
~~~
New (the new bullet, then the original line **unchanged**; lines 731–741 below it stay
untouched):
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

E6d. Phase-014 banner: append a dated fact paragraph. The phase-014 artifacts are **not**
edited. Current (lines 203–206; count = 1):
~~~text
optimization is revisited only if the real pilot proves the per-member clone cost
load-bearing.

## Queued Candidate — NIP-0003: Live Runtime Sessions (proposed phases 015/016, to follow 014) — PROPOSED, awaiting H-NIP
~~~
New:
~~~text
optimization is revisited only if the real pilot proves the per-member clone cost
load-bearing.

**Release fact for re-baseline (2026-10-08, recorded by the v1.4.0 release preparation;
the banner text above is unedited).** This proposal was authored at v1.3.0, and three of
its premises go stale once the operator tags `v1.4.0`: feature 102's acceptance test
`git rev-parse -q --verify refs/tags/v1.4.0; test $? -eq 1`
(`.agent/feature_list_014.json`) and the phase-level "zero v1.4.0 refs" criterion in
`.agent/product_spec_014.md` both assert that no v1.4.0 tag exists, and feature 100 pins
the real pilot to the released tag `v1.3.0` (`.agent/feature_list_014.json`,
`.agent/product_spec_014.md`, `docs/planning/phase_014.yaml`). A Planner re-baseline of
the phase-014 artifacts is required before `H-PHASE-014` is presented; the release
preparation edits none of them.

## Queued Candidate — NIP-0003: Live Runtime Sessions (proposed phases 015/016, to follow 014) — PROPOSED, awaiting H-NIP
~~~

E6e. NIP-0003 queued-candidate section: a small factual version roll. The NIP is **not**
edited. Current (lines 224–227; count = 1):
~~~text
**Proposed realization, to follow phase 014.** Phase 015 (normative surface, features
103–107, design estimate 5,400 lines) releases as the next MINOR (expected v1.4.0) and
also rolls up phase 014's unreleased changes. Phase 016 (reference controller and live
conformance, features 108–113) releases as the next MINOR (expected v1.5.0); it requires
~~~
New:
~~~text
**Proposed realization, to follow phase 014.** Phase 015 (normative surface, features
103–107, design estimate 5,400 lines) releases as the next MINOR (expected v1.5.0; the
NIP's own text still says v1.4.0, which the 2026-10-08 release preparation takes) and
also rolls up phase 014's unreleased changes. Phase 016 (reference controller and live
conformance, features 108–113) releases as the next MINOR (expected v1.6.0; the NIP says
v1.5.0); it requires
~~~

ROADMAP invariant after E6: exactly one body line, after the second `---`, matches
`Latest released tag: v1\.4\.0\b|Release in preparation: v1\.4\.0\b`. It is the first
line of the E6c bullet. None of the E6d/E6e text contains either phrase.

**Explicitly not done in E6:**

- The `## Current Position (2026-08-15)` heading date and the stale open-debt bullet stay
  unchanged. They are logged as `NDEBT-044(e)` for the next refresh, and no release-prep
  precedent touched them.
- The "Prior released tag: v1.2.1" and "Earlier released tag" bullets stay unchanged.
  Rolling them is the post-release refresh's job.

### E7 — `docs/planning/operator_gates.md`

E7a. Current (line 5; count = 1):
~~~text
version: 0.24.0
status: active
~~~
New:
~~~text
version: 0.25.0
status: active
~~~

E7b. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "0.24.0"
~~~
New:
~~~text
change_log:
  - version: "0.25.0"
    date: "2026-10-08"
    summary: "H-FRAMEWORK-RELEASE row's Disposition cell gains v1.4.0 PREPARED/OUTSTANDING language: the two proposal-grade ecosystem lifecycle protocol documents (ecosystem/06_simplification_review.md, ecosystem/08_ga_gate.md; status draft, not yet normative -- activation awaits phase-014 feature 099 under H-PHASE-014) are packaged as the next MINOR, everything else since v1.3.0 being envelope-only; this release-preparation change bumped CHANGELOG, the C10 version anchors, and the readiness record (`.agent/evidence/release-readiness-v1.4.0.md`) to complete; tag authorization and the tag remain OUTSTANDING. The operator requested this release verbatim ('PR #62 has been merged, cut a new release pin/tag it.', 2026-10-08), recorded here as the Section 2 human sign-off gate for cutting the release preparation; the tag act itself remains the separate Orchestrator mechanic per Section 6 and awaits explicit post-merge authorization, recorded in run_state before the act (the v1.1.0 / NDEBT-018 precedent). Appended to the existing recurring row, not a new row, matching the v0.22.0/v0.23.0 precedent."
  - version: "0.24.0"
~~~

E7c. Row-anchored append to the existing `H-FRAMEWORK-RELEASE` row (line 134; a single
physical line). This is a substring replacement inside that row only. Current substring
(the row's tail; count = 1 in the file):
~~~text
published from the `[1.3.0]` CHANGELOG section at 2026-09-30T10:12:30Z. Recurring: outstanding again at the next release. |
~~~
New substring:
~~~text
published from the `[1.3.0]` CHANGELOG section at 2026-09-30T10:12:30Z. v1.4.0 (MINOR) is PREPARED (`.agent/evidence/release-readiness-v1.4.0.md`), packaging the two proposal-grade ecosystem lifecycle protocol documents landed with the phase-014 proposal (PR #61) — `ecosystem/06_simplification_review.md` and `ecosystem/08_ga_gate.md`, both `status: draft` and not yet normative (activation awaits phase-014 feature 099 under `H-PHASE-014`) — with everything else since v1.3.0 envelope-only. The operator requested this release verbatim ('PR #62 has been merged, cut a new release pin/tag it.', 2026-10-08), recorded here as the Section 2 human sign-off gate for cutting the release preparation; the tag act itself remains the separate Orchestrator mechanic per Section 6 and awaits explicit post-merge authorization, recorded in run_state before the act (the v1.1.0 / NDEBT-018 precedent). CHANGELOG, C10 version anchors, and the readiness record are complete; tag authorization and the tag remain OUTSTANDING -- no tag authorization or tag is recorded for v1.4.0. Recurring: outstanding again at the next release. |
~~~

Verbatim-quote rule (amendment 1). E7b and E7c quote the operator verbatim, as the 0.22.0
precedent did ("The operator requested this release verbatim ('create a new release based on
the lasted code'), recorded here as the Section 2 human sign-off gate for cutting the release
preparation; the tag act itself remains the separate Orchestrator mechanic per Section 6").
The quote, 'PR #62 has been merged, cut a new release pin/tag it.', was supplied by the Orchestrator as the operator's exact in-session words of
2026-10-08. It contains no brand token, no `|` (safe inside the table row) and no `'` (safe
inside the single-quoted span). The quote's "pin/tag it" is **not** recorded as tag
authorization: the tag act awaits explicit post-merge authorization, recorded in
`run_state` before the act (NDEBT-018; the v1.1.0 precedent at `a2c15d2`).

### E8 — `.agent/evidence/release-readiness-v1.4.0.md`: NOT written by the generator

The **@evaluator** writes this file after it independently runs Section 4. Its structure
must mirror `.agent/evidence/release-readiness-v1.3.0.md`:

1. `# Release Readiness — v1.4.0`
2. **Gate paragraph:**
   - Gate: `H-FRAMEWORK-RELEASE` (operator-only).
   - "Prepared 2026-10-08 on the `chore/v1.4.0-release-prep` branch" from `main` `669fb72`.
   - What is packaged: the two draft ecosystem documents, plus their `ecosystem/README.md`
     rows and `NIZAM.json` key_documents entries. State that they are not yet normative,
     with activation via phase-014 feature 099 under `H-PHASE-014`.
   - Target tier: MINOR, per `methodology/06_release_train.md` Section 3.2, with the
     Section 3.4 round-up note.
   - "At preparation time the pipeline has not created, pushed, or approved `v1.4.0`."
3. **Envelope paragraph:**
   - Everything else since v1.3.0 is envelope-only: the phase-014 Planner artifacts,
     `docs/planning/*`, the NIP-0003 proposal, `.agent/*` and `CHANGELOG.md`.
   - Record the phase-014 re-baseline fact (feature 102 / spec criterion / feature 100
     pilot pin).
4. `## Automated readiness`, items 1–5, each with a bold result and its command:
   1. `bash tools/validate.sh`: **16/16 PASS**
   2. `bash tools/fixtures_self_test.sh`: **79/79 PASS**
   3. `python3 .github/scripts/release_closeout.py --mode pr` at V=1.4.0: **PASS**, all
      five anchor groups agree
   4. `bash tools/e2e_bootstrap_test.sh`: **PASS**, including `assert_multirepo` and
      `assert_stage4`
   5. Tag probes: `git rev-parse -q --verify refs/tags/v1.4.0` is non-zero (exit 1) and
      `git ls-remote --tags origin v1.4.0` prints nothing **and exits 0**, so **no `v1.4.0`
      tag exists** (locally or on origin). Empty output with a non-zero exit (for example
      128, a network or auth failure) is **not** evidence of absence. It is an
      inconclusive probe and blocks readiness until it is re-run.
5. **Raw captured outputs line**, pointing at `.agent/evidence/release-v1.4.0-prep/`:
   `01-validate-sh.txt`, `02-fixtures-self-test.txt`, `03-release-closeout-pr.txt`,
   `04-tag-probe-and-sanitization.txt`, `05-e2e-bootstrap.txt`. This mirrors
   `flake-methodology-2026-09-30/`, and this plan is `00-`. File 04 carries:
   - both tag probes, each followed by `echo "exit=$?"`, with the captured exit codes:
     `exit=1` for `rev-parse`, and empty output then `exit=0` for `ls-remote` (§4 #5a/#5b)
   - `git status --porcelain --untracked-files=all` and the §3 untracked-aware scope-guard
     output (`scope_guard_exit=0`), plus the guard's negative-control run (§3)
   - `#13` (the CHANGELOG lines 8–10 check) and its `exit=0`
   - the per-file control-character count
     `LC_ALL=C grep -cP '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r' <file>`, which must be 0 for
     every touched file
   - `grep -inE 'n[i]zamiq|\.svc|cluster\.local'` over every touched file, which must
     return no hits (exit 1), together with the §4 `#10` positive control (exit 0). The
     control proves the pattern can match.

   File 05 must state honestly that `tools/e2e_bootstrap_test.sh` tags and clones the
   checkout's **HEAD commit** (`tools/e2e_bootstrap_test.sh` lines 8–10), not the
   uncommitted working tree. It also records the HEAD SHA the harness exercised (the
   `resolved_sha=` in its `assert_genesis` line). If the release edits are uncommitted
   at run time, file 05 says so. This is acceptable under the 2e12225 precedent, because
   the edits are envelope and version-anchor only and touch nothing `bootstrap.sh`
   injects except the `NIZAM.json` version string.
6. `## Content map` table. Columns: Surface | Summary. Rows:
   - `ecosystem/06_simplification_review.md`
   - `ecosystem/08_ga_gate.md`
   - `ecosystem/README.md` + `NIZAM.json` (key_documents; `framework.version` 1.4.0)
   - `docs/guide/index.html` (meta/footer 1.4.0 only)
   - `CHANGELOG.md` / `README.md` / `CONTEXT.md`
   - `docs/planning/ROADMAP.md`, `docs/planning/operator_gates.md`
7. **Closing line, verbatim form:** "`H-FRAMEWORK-RELEASE` sign-off and the tag remain
   outstanding — this pipeline never self-tags per `methodology/06_release_train.md`
   Section 6."

The record names `.agent/evidence/release-v1.4.0-prep/` files 01–05. These are
evaluator-produced; the generator does not create them.

## 3. Scope: touched files and must-not-touch list

**Generator touches exactly 7 files:** `CHANGELOG.md`, `NIZAM.json`, `CONTEXT.md`,
`README.md`, `docs/guide/index.html`, `docs/planning/ROADMAP.md` and
`docs/planning/operator_gates.md`.

**Evaluator adds:** `.agent/evidence/release-readiness-v1.4.0.md` and
`.agent/evidence/release-v1.4.0-prep/01-…05-*.txt`. This plan, `00-release-prep-plan.md`,
already exists.

The final PR therefore matches the 7441ffa / 2e12225 anchor set (8 files + raw evidence).
The only difference is that no `methodology/` payload edit exists this time.

**MUST NOT TOUCH** (any diff here is a Mode B rejection):

- `.agent/run_state.json`. Precedent release prep never touched it; it is touched only at
  the post-release tag record.
- `docs/planning/manifest.json`
- `docs/planning/DEBT.md`. Precedent release prep (7441ffa, 2e12225) never touched it, and
  no new debt is created by this change.
- All phase-014 artifacts: `.agent/product_spec_014.md`, `.agent/feature_list_014.json`,
  `docs/planning/phase_014.yaml`
- `docs/nips/*` (including `NIP-0003-live-runtime-sessions.md`)
- Everything under `methodology/`, `schema/`, `tools/`, `standard/`, `templates/`,
  `ecosystem/` and `registry/`, plus `bootstrap.sh`
- `.github/` (including `.github/scripts/release_closeout.py`)
- `docs/migration-*.md`, `docs/architecture/*` and every other `.agent/*` file except the
  E8 evaluator outputs

**Mechanical scope guard, part A (tracked edits only; kept from revision 0):**
`git diff --name-only 669fb72 -- . ':!.agent/evidence/release-readiness-v1.4.0.md' ':!.agent/evidence/release-v1.4.0-prep/'`
must list exactly the 7 generator files (§4 #11). It cannot see untracked files.

**Mechanical scope guard, part B (untracked-aware allowlist; authoritative).** This guard
is self-contained. The `scope_guard` function reads change lines on stdin and exits 0 only
if both of these hold:

- every line is on the allowlist;
- all 7 generator files appear as modifications.

Anything else prints `UNEXPECTED:` or `MISSING:` and exits 1. Paths that git quotes (for
example ones with special characters) never match the allowlist, so they also fail
closed.

Input normalization. The guard takes **the union of every tracked change since
`669fb72` (committed or not) and every untracked, non-ignored file**. Without this, its
verdict would depend on whether the generator has committed yet. Tracked changes come from
`git diff --name-status 669fb72`, which is relative to the working tree; untracked files
come from `git ls-files --others --exclude-standard`. Both respect `.gitignore`, as
`git status` does. The ignored classes are OS and editor junk, `*.log`, `node_modules/`,
`__pycache__/`, `*.pyc` and `.venv/`, so no governed path can hide there.

Allowlist:

- `M` on each of the 7 generator files. All 7 are required, and any other status letter
  (A/D/R/T) fails.
- `?? .agent/evidence/release-readiness-v1.4.0.md`
- `?? .agent/evidence/release-v1.4.0-prep/<file>`: plan `00-` and evaluator outputs 01–05.
  The prefix includes the trailing `/`, so a sibling such as `release-v1.4.0-prep-x/` fails.
- `?? .agent/validator/release-v1.4.0-<name>.json`: the validator's own verdict files for
  this review. `.agent/validator/release-v1.4.0-plan.json` already exists untracked, and
  the `.agent/validator/nip-0003-review.json` precedent shipped its verdict in PR #62.
  This entry was **added** to the Orchestrator's example allowlist. Without it, the guard
  would fail on the validator's own artifact.

```sh
scope_guard() {
  awk '
    BEGIN {
      n = split("CHANGELOG.md NIZAM.json CONTEXT.md README.md docs/guide/index.html docs/planning/ROADMAP.md docs/planning/operator_gates.md", g, " ")
      for (i = 1; i <= n; i++) want["M " g[i]] = 1
      bad = 0
    }
    ($0 in want) { seen[$0] = 1; next }
    $0 == "?? .agent/evidence/release-readiness-v1.4.0.md" { next }
    index($0, "?? .agent/evidence/release-v1.4.0-prep/") == 1 && $0 !~ /\.\.|\/$/ { next }
    $0 ~ /^\?\? \.agent\/validator\/release-v1\.4\.0-[A-Za-z0-9._-]+\.json$/ && $0 !~ /\.\./ { next }
    { print "UNEXPECTED: " $0; bad = 1 }
    END {
      for (k in want) if (!(k in seen)) { print "MISSING: " k; bad = 1 }
      exit bad
    }'
}
{ git diff --name-status 669fb72 | awk -F '\t' '{ print $1 " " $2 (NF > 2 ? " -> " $3 : "") }'
  git ls-files --others --exclude-standard | sed 's/^/?? /'
} | scope_guard; echo "scope_guard_exit=$?"
```

Expected (evaluator, after the generator's edits and the evaluator's outputs exist): no
`UNEXPECTED:`/`MISSING:` lines and `scope_guard_exit=0`.

**Negative control** (the evaluator dry-runs it on synthetic lists in the same shell,
after defining `scope_guard`; no repository state is involved):

```sh
OK7='M CHANGELOG.md
M NIZAM.json
M CONTEXT.md
M README.md
M docs/guide/index.html
M docs/planning/ROADMAP.md
M docs/planning/operator_gates.md'
printf '%s\n' "$OK7" '?? .agent/evidence/release-readiness-v1.4.0.md' '?? .agent/evidence/release-v1.4.0-prep/01-validate-sh.txt' '?? .agent/validator/release-v1.4.0-plan.json' | scope_guard; echo "positive_exit=$?"
printf '%s\n' "$OK7" '?? methodology/10_live_runtime_sessions.md' | scope_guard; echo "neg_untracked_forbidden_exit=$?"
printf '%s\n' "$OK7" 'M .agent/run_state.json' | scope_guard; echo "neg_tracked_forbidden_exit=$?"
printf '%s\n' "$OK7" '?? .agent/evidence/release-v1.4.0-prep-x/evil.txt' | scope_guard; echo "neg_sibling_prefix_exit=$?"
printf '%s\n' "$OK7" '?? .agent/validator/release-v1.4.0-../../ecosystem/x.json' | scope_guard; echo "neg_traversal_exit=$?"
printf '%s\n' "$OK7" | grep -v 'NIZAM.json' | scope_guard; echo "neg_missing_generator_file_exit=$?"
printf '%s\n' "$OK7" | sed 's/^M CONTEXT.md$/D CONTEXT.md/' | scope_guard; echo "neg_wrong_status_exit=$?"
```

Expected: `positive_exit=0`, and every `neg_*_exit=1` with the matching `UNEXPECTED:` or
`MISSING:` line printed. Section 5 records the planner's own run of this control.

## 4. Verification commands (evaluator runs; expected results)

Commands that contain a shell pipe or a regex alternation (`#5a`, `#5b`, `#7`, `#8`, `#10`,
`#10-control`, `#12`, `#13`) are **not** in the table. Markdown tables require `\|`, which
would change their meaning. They appear verbatim, with real `|`, in the fenced blocks below
the table, labelled by row number. The table keeps only their expected results.

| # | Command | Expected |
|---|---|---|
| 1 | `bash tools/validate.sh` | last line `SUMMARY: 16 passed, 0 failed`; exit 0 (C5, C8, C10 green) |
| 2 | `bash tools/fixtures_self_test.sh` | `SELF-TEST OK: 79/79 fixtures accounted for, 0 failed`; exit 0 |
| 3 | `python3 .github/scripts/release_closeout.py --mode pr` | 5 x `PASS`, final line `Release close-out: all internal version anchors agree with V=1.4.0 (--mode pr).`; exit 0 |
| 4 | `bash tools/e2e_bootstrap_test.sh` | exit 0; `e2e_bootstrap_test.sh: PASS`. **Exercises HEAD, not the uncommitted tree** (the harness tags the checkout's HEAD, lines 8–10). This is acceptable under the 2e12225 precedent and must be recorded honestly in `05-e2e-bootstrap.txt`, with the exercised SHA (E8 item 5). |
| 5a | fenced block `#5a` | no SHA printed; `exit=1` |
| 5b | fenced block `#5b` | empty output **and** `exit=0`, both captured in `04-tag-probe-and-sanitization.txt`. Empty output with a non-zero exit (for example 128, network or auth) is INCONCLUSIVE, not a pass. |
| 6 | `python3 -c "import json;print(json.load(open('NIZAM.json'))['framework']['version'])"` | `1.4.0` |
| 7 | fenced block `#7` | `0` then `7` |
| 8 | fenced block `#8` | `1` |
| 9 | `grep -c '^- \*\*Latest released tag: v1.3.0 (MINOR) — RELEASED 2026-09-30 at' docs/planning/ROADMAP.md` | `1` (v1.3.0 released record kept byte-identical) |
| 10 | fenced block `#10` | no match lines; `exit=1` |
| 10-control | fenced block `#10-control` | three match lines; `exit=0` (proves `#10` is not vacuous) |
| 11 | §3 scope guard part A | exactly the 7 generator files (tracked edits only) |
| 11b | §3 scope guard part B (untracked-aware) + its negative control | `scope_guard_exit=0`; control: `positive_exit=0`, all `neg_*_exit=1` |
| 12 | fenced block `#12` | `0` (tracked forbidden paths unchanged; part B covers untracked) |
| 13 | fenced block `#13` | `exit=0`. CHANGELOG lines 8–10 are exactly `## [Unreleased]`, an empty line, then `## [1.4.0] - 2026-10-08`. Close-out group 4 does not check that `[Unreleased]` is empty. |

`#5a`
```sh
git rev-parse -q --verify refs/tags/v1.4.0; echo "exit=$?"
```

`#5b`
```sh
git ls-remote --tags origin v1.4.0; echo "exit=$?"
```

`#7`
```sh
grep -c 'v1\.3\.0' README.md; grep -o 'v1\.4\.0' README.md | wc -l
```

`#8`
```sh
python3 -c "import re,sys;sys.path.insert(0,'.github/scripts');import release_closeout as r;b=r.document_body(open('docs/planning/ROADMAP.md').read());print(sum(1 for l in b.splitlines() if re.search(r'Latest released tag: v1\.4\.0\b|Release in preparation: v1\.4\.0\b',l)))"
```

`#10`
```sh
grep -inE 'n[i]zamiq|\.svc|cluster\.local' CHANGELOG.md NIZAM.json README.md CONTEXT.md; echo "exit=$?"
```

`#10-control` (a synthetic positive; the token is assembled at run time, so this plan file
never contains it literally)
```sh
printf '%s\n' "x $(printf 'n%szamiq' i | tr a-z A-Z) y" 'host.svc' 'a.cluster.local' | grep -inE 'n[i]zamiq|\.svc|cluster\.local'; echo "exit=$?"
```

`#12`
```sh
git diff 669fb72 -- .agent/run_state.json docs/planning/manifest.json docs/planning/DEBT.md docs/nips .agent/product_spec_014.md .agent/feature_list_014.json docs/planning/phase_014.yaml methodology schema tools standard templates ecosystem .github bootstrap.sh | wc -c
```

`#13`
```sh
test "$(sed -n '8,10p' CHANGELOG.md)" = "$(printf '## [Unreleased]\n\n## [1.4.0] - 2026-10-08')"; echo "exit=$?"
```

Mode B (validator) note: `git diff HEAD` (or `git diff 669fb72`) must show only the E1–E7
hunks.

## 5. Plan self-check (planner, in-memory, read-only)

The planner parsed this plan's own `~~~text` Current/New pairs and applied them to
**in-memory** copies of the HEAD `669fb72` files. It asserted that every Current block
occurs exactly once, then imported `.github/scripts/release_closeout.py` and ran its
groups. No repository file other than this plan was written. Captured output:

~~~
applied pairs: 18 files: ['CHANGELOG.md', 'CONTEXT.md', 'NIZAM.json', 'README.md', 'docs/guide/index.html', 'docs/planning/ROADMAP.md', 'docs/planning/operator_gates.md']
V = 1.4.0
PASS CONTEXT.md version anchor (frontmatter + change_log[0])
PASS docs/guide/index.html version anchors (meta + footer)
PASS README.md version pins (curl URL / GOVERNANCE_TAG / --tag / releases-tag)
PASS CHANGELOG.md top released section (heading + tier banner)
PASS ROADMAP.md disposition line (Latest released tag / Release in preparation)
PASS ROADMAP.md disposition line (Latest released tag / Release in preparation)   [tag-mode semantics, tag=v1.4.0]
tag-mode (c) heading == tag: True
C5 CHANGELOG.md hits: 0 / NIZAM.json: 0 / README.md: 0 / CONTEXT.md: 0   [case-insensitive]
yaml CONTEXT.md 1.4.0 1.4.0 2026-10-08
yaml docs/planning/ROADMAP.md 0.44.0 0.44.0 2026-10-08
yaml docs/planning/operator_gates.md 0.25.0 0.25.0 2026-10-08
README v1.3.0: 0 v1.4.0: 7
ROADMAP latest v1.3.0 line kept: 1
operator_gates release rows: 1 ends with Recurring: True has v1.4.0 PREPARED: True
CHANGELOG [Unreleased] empty then [1.4.0]: True
exit=0
~~~

Re-run after amendment 1 (same harness, plus four operator_gates and brand-token
assertions). Every line above repeated identically, followed by:

~~~
applied pairs: 18 files: [... same 7 files ...]   (each Current block count == 1)
PASS x5 at V=1.4.0 (+ ROADMAP under tag-mode semantics); tag-mode (c) heading == tag: True
operator_gates quote in row: True | in change_log[0]: True
row cells unchanged (pipe count HEAD vs new): 5 5
post-merge authorization stated in row + change_log: True
brand token in any edited file (case-insensitive): 8   -> all 8 pre-exist at HEAD in docs/planning/ROADMAP.md (not C5-swept); HEAD counts for the other six files are 0, so the plan adds 0
exit=0
~~~

This shows the plan is sufficient and internally consistent. It is not a substitute for the
evaluator's real runs in Section 4, which also cover C8/C10 and the e2e harness.

### 5.1 Revision-1 self-check: fenced commands run verbatim at HEAD `669fb72`

The planner extracted every labelled ```` ```sh ```` block from this file programmatically
(no retyping) and ran them in `bash` against the **current HEAD tree, before any release
edit**. The run set `PYTHONDONTWRITEBYTECODE=1` in the environment only; command text is
unchanged. Captured output:

~~~
===== #5a =====          exit=1
===== #5b =====          (no output) exit=0
===== #7 =====           4 / 0
===== #8 =====           0
===== #10 =====          (no output) exit=1
===== #10-control =====  1:x <TOKEN-UPPERCASE> y / 2:host.svc / 3:a.cluster.local / exit=0
===== #12 =====          0
===== #13 =====          exit=1
===== §3 part B on current tree =====
MISSING: M CONTEXT.md / M NIZAM.json / M docs/planning/ROADMAP.md / M docs/guide/index.html / M CHANGELOG.md / M README.md / M docs/planning/operator_gates.md
scope_guard_exit=1
===== §3 part B negative control =====
positive_exit=0
UNEXPECTED: ?? methodology/10_live_runtime_sessions.md               neg_untracked_forbidden_exit=1
UNEXPECTED: M .agent/run_state.json                                  neg_tracked_forbidden_exit=1
UNEXPECTED: ?? .agent/evidence/release-v1.4.0-prep-x/evil.txt        neg_sibling_prefix_exit=1
UNEXPECTED: ?? .agent/validator/release-v1.4.0-../../ecosystem/x.json neg_traversal_exit=1
MISSING: M NIZAM.json                                                neg_missing_generator_file_exit=1
UNEXPECTED: D CONTEXT.md + MISSING: M CONTEXT.md                     neg_wrong_status_exit=1
#8 variant (demonstration only; V substituted 1.4.0 -> 1.3.0): 1
~~~

`<TOKEN-UPPERCASE>` above stands for the run-time-assembled brand token, which `grep -i`
matched. It is redacted here so this file never carries the literal.

Interpretation, HEAD versus the post-edit expectation:

| # | At HEAD (now) | Expected post-edit | Same? | Why it differs / what the HEAD run proves |
|---|---|---|---|---|
| 5a | `exit=1` | `exit=1` | yes | No local tag; the probe is well-formed. |
| 5b | empty, `exit=0` | empty, `exit=0` | yes | origin reachable (exit 0) **and** no tag: a genuine negative, not a failure. |
| 7 | `4` then `0` | `0` then `7` | no | HEAD still has 4 pin lines at v1.3.0 (`grep -c` counts lines) and no v1.4.0. The second number comes through `\| wc -l`, which proves the pipe works. |
| 8 | `0` | `1` | no | No v1.4.0 disposition exists before E6c. The V=1.3.0 variant prints `1`, which proves the unescaped alternation matches a real disposition line. Escaped, it would count 0. |
| 10 | no hits, `exit=1` | no hits, `exit=1` | yes | `#10-control` shows the identical pattern matching all three alternatives (`exit=0`), so `#10`'s `exit=1` is a real negative, not vacuous. |
| 12 | `0` | `0` | yes | The pipe into `wc -c` works; forbidden tracked paths are unchanged. |
| 13 | `exit=1` | `exit=0` | no | HEAD lines 8–10 are `## [Unreleased]`, an empty line and `### Added`. E1 inserts `## [1.4.0] - 2026-10-08` as line 10. |
| 11b | `scope_guard_exit=1` (7 x MISSING, 0 x UNEXPECTED) | `scope_guard_exit=0` | no | No generator edits exist yet. The two existing untracked files (this plan and `.agent/validator/release-v1.4.0-plan.json`) are correctly **allowed**. |
| 11b control | `positive_exit=0`, all six `neg_*_exit=1` | same | yes | The guard catches untracked forbidden paths, tracked forbidden paths, sibling-prefix and traversal paths, a missing generator file, and a wrong status letter. |

The re-run of the 18-edit in-memory simulation after this revision gave the same results:
18/18 unique, close-out 5/5 PASS at V=1.4.0, `sim_exit=0`. The approved E1–E7 edit
specifications are byte-unchanged.

Side effect disclosed: the planner's revision-0 in-memory simulation imported
`release_closeout`. That wrote `.github/scripts/__pycache__/release_closeout.cpython-312.pyc`
(2026-10-08 09:56Z). It is **gitignored** (`__pycache__/`), so it is invisible to
`git status`, to scope guard part B and to the PR. The evaluator's `#8` will create the
same cache. It is harmless, but the Orchestrator may delete it; the planner may edit only
this file.

## 6. Post-merge (out of scope for this change; recorded for the Orchestrator)

1. The PR merges after review.
2. The operator gives `H-FRAMEWORK-RELEASE` sign-off and authorizes the tag. Record that in
   `run_state` **before** the act (NDEBT-018).
3. The Orchestrator pushes annotated `v1.4.0` at the reviewed merge commit.
4. `release.yml` runs the tag-mode close-out and publishes the Release.
5. The post-release refresh (0.39.0 / 0.42.0 precedent):
   - ROADMAP: remove the Release-in-preparation bullet and roll "Latest released tag" to
     v1.4.0.
   - operator_gates: EXECUTED.
   - run_state: `release_executed`.
   - The phase-014 re-baseline, if the operator decides it (Section 7, Q1: an operator
     decision for the post-release refresh; this prep records the ROADMAP fact-note only).

## 7. Open questions — resolved by Orchestrator amendment 1 (2026-10-08)

- **Q1 — acknowledged.** Whether to re-baseline phase 014 is an operator decision for the
  post-release refresh. Three items would be affected:
  - feature 102's `refs/tags/v1.4.0` absence test;
  - `product_spec_014.md`'s "zero v1.4.0 refs" criterion;
  - optionally, feature 100's `v1.3.0` pilot pin.

  This prep records only the ROADMAP fact-note (E6d) and edits no phase-014 artifact.
- **Q2 — ACCEPTED.** The "Latest released tag: v1.3.0" ROADMAP line stays unchanged, and
  the "Release in preparation: v1.4.0" bullet is inserted ahead of it (E6c).
- **Q3 — ANSWERED.** The operator's verbatim words are quoted in E7b/E7c as the Section 2
  human sign-off for cutting the release preparation. The tag act awaits explicit
  post-merge authorization, recorded in `run_state` before the act.
- **Q4 — WITHDRAWN.** The C5 case-sensitivity drift is already logged as `NDEBT-044(c)`
  (PR #62). The planner's "not logged" claim was wrong; the E1 note now cites the row.
- **Q5 — acknowledged.** The stale `run_state` (`updated_at` 2026-08-19) stays untouched
  by this prep.

No open questions remain. Next: @validator Mode A re-review (revision round 2 of 3) of the verification-plan fixes; the 18 edit specifications were approved in round 1 and are byte-unchanged.

```
[STATE: Phase 013 (complete; release prep has no phase) | STEP: PLAN (revision 1: verification plan fixed) | DEPS: VERIFIED]
plan: .agent/evidence/release-v1.4.0-prep/00-release-prep-plan.md
tier: MINOR -> v1.4.0 (06_release_train.md §3.2, §3.4)
generator_files: 7 (CHANGELOG.md, NIZAM.json, CONTEXT.md, README.md, docs/guide/index.html, docs/planning/ROADMAP.md, docs/planning/operator_gates.md)
evaluator_files: .agent/evidence/release-readiness-v1.4.0.md + release-v1.4.0-prep/01..05
self_check: 18/18 current-text blocks unique; close-out groups 5/5 PASS at V=1.4.0; fenced #5a/#5b/#7/#8/#10/#10-control/#12/#13 run verbatim at HEAD (§5.1); scope_guard negative control 6/6 caught, positive 0
validator_issues_addressed: major-1 untracked-aware guard (§3 part B, #11b); major-2 pipes moved to fenced blocks; minor-3 #5b exit=0 required + captured in 04; optional #13 + e2e-HEAD note
next: @validator Mode A re-review (round 2 of 3)
open_questions: none (Q1/Q5 acknowledged, Q2 accepted, Q3 answered, Q4 withdrawn as NDEBT-044(c))
```
