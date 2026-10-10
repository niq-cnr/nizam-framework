# v1.5.0 Release-Preparation Plan (MINOR) — Planner output, awaiting @validator Mode A

- Plan author: @planner (Protocol 04). Plan only — no other file is edited by the planner.
- Branch: `chore/v1.5.0-release-prep`, cut from `main` = `312257b` (phase 014 closed by
  PR #77, feature 102).
- Last release: `v1.4.0` (tag object `bb32064` at `9edd5d0`, PR #63; `release.yml` run
  37763448754 succeeded). No `v1.5.0` tag exists (probed below, local and origin).
- Request: the operator's verbatim words, 2026-10-10, in the Orchestrator's session
  (supplied to the planner by the Orchestrator): "ensure the that
  documentation and change notes is updated and ready for relase. You are authorized to
  manage, triage as necessary, your PR's and once clean merge as appropriate. you are
  authorized to tag and pin the release." This is an `H-FRAMEWORK-RELEASE` request,
  recorded as the `methodology/06_release_train.md` Section 2 human sign-off.
- **Tag authorization is INCLUDED this time.** Unlike v1.4.0 — where the sign-off
  ("PR #62 has been merged, cut a new release pin/tag it.") covered the durable
  preparation only and the tag act awaited a separate post-merge authorization
  ("merged — authorized to tag v1.4.0", NDEBT-018) — this authorization names the tag
  act explicitly: "you are authorized to tag and pin the release." No separate
  post-merge tag authorization will be awaited. **But per
  `methodology/06_release_train.md` Section 6, this plan still covers the durable
  preparation only**: the tag act remains a separate Orchestrator mechanic, executed
  AFTER this PR merges, at the reviewed merge commit, with the already-recorded
  authorization. Nothing in this plan creates, pushes or approves a tag; `run_state`
  is not touched (the tag record lands there at the post-release refresh, by the
  Orchestrator).
- Every "current text" block below was re-read from HEAD `312257b` (AH-1). Each anchor's
  uniqueness was checked with `str.count` (= 1 unless noted) and by the in-memory
  simulation in Section 5.

---

## 0. Baseline evidence at HEAD `312257b` (captured by the planner, read-only runs)

Runs were serial — `tools/validate.sh` and `tools/fixtures_self_test.sh` never overlap
(two harnesses over the same fixtures tree). Raw captures:
`.agent/evidence/release-v1.5.0-prep/01-validate-sh.txt` (…/02-…, 03-…, 04-…,
05-…, 06-guide-anchors.txt); each file's line 1 is the invocation, its last line
`EXIT:<code>`.

| Command | Result at HEAD |
|---|---|
| `bash tools/validate.sh` | `SUMMARY: 16 passed, 0 failed`; exit 0 |
| `bash tools/fixtures_self_test.sh` | `SELF-TEST OK: 147/147 fixtures accounted for, 0 failed`; exit 0 |
| `python3 .github/scripts/release_closeout.py --mode pr` | 5 x PASS, `...agree with V=1.4.0 (--mode pr).`, exit 0 — correctly still 1.4.0 BEFORE the edits |
| `bash tools/e2e_bootstrap_test.sh` | exit 0, `e2e_bootstrap_test.sh: PASS` (assert_genesis / assert_multirepo / assert_stage4 OK; `resolved_sha=312257b65573330c5ba6fd5ffb4a3b5a23b3c800`) |
| `git rev-parse -q --verify refs/tags/v1.5.0` | no output, exit 1 |
| `git ls-remote --tags origin v1.5.0` | empty output, exit 0 |
| `git rev-parse -q --verify refs/tags/v1.4.0` | `bb32064472fb71deaba96e134b888c7e9e590d96`, exit 0 (last-release fact) |
| `git status --porcelain` after the runs | `?? .agent/evidence/release-v1.5.0-prep/` (this plan's captures) and `?? .nizam/` (pre-existing — see Hazard H2) |

## 1. Tier re-verification: MINOR, so v1.5.0

Consumer-reaching delta `v1.4.0..HEAD`. `bootstrap.sh` injects `standard/`,
`templates/`, `schema/`, `tools/`, `methodology/`, `ecosystem/` and `NIZAM.json`
(bootstrap.sh lines 12–13; confirmed). The command
`git diff --name-only v1.4.0..HEAD | grep -Ev '^(\.agent/|docs/)'` returns exactly:

- `.github/workflows/compliance.yml` — envelope: **NOT injected** (bootstrap.sh injects
  the seven payload paths only; `.github/` never is). Confirmed.
- `CHANGELOG.md` — envelope (not injected).
- `NIZAM.json` — `framework.version` bump (E2) **plus three additive capability-index
  registrations** (array appends, no removal/rename): `nizam-ecosystem-bootstrap`
  (feature 106), `nizam-ecosystem-simplification-review` and `nizam-ecosystem-ga-gate`
  (feature 099). Consumers loading the index see three new entries.
- `ecosystem/06_simplification_review.md`, `ecosystem/08_ga_gate.md` — the 099
  activation wave: `draft` → `active`, 0.1.0 → 0.2.0, each with a change_log entry;
  the pre-activation "reserved until phase-014 execution" parenthetical removed from
  the Section 5 gate text. **Normative status change** — these two protocols were
  shipped proposal-grade at v1.4.0 and become load-bearing now.
- `ecosystem/README.md` — 0.4.0 → 0.5.0 (module navigation re-synced to the active
  registrations; rows and counts unchanged).
- `schema/README.md` — 0.18.0 → 0.19.0 (feature 104 statement:
  `tools/test_convergent_review.py` is the sole validator of the review schema family).
- `standard/capability_profiles.md` — 0.3.0 → 0.4.0 (feature 109): the Section 2 table
  gains an explicit `Role` column naming each profile's AGF role.
- `standard/definition_of_done.md` — 0.1.0 → 0.2.0 (feature 104): Merge-Done and
  Enforcement name four compliance.yml jobs (the new `convergent_review` job joins
  `validate`, `e2e_bootstrap`, `fixtures_self_test`).
- `tools/README.md` — 0.11.0 → 0.17.0 across the phase (103 required-conformance
  documentation, 104 CI job, 105 claim map, 106 subset rule, 107 C1 row, 109 C15 row).
- `tools/interface.md` — 0.3.0 → 0.3.1 (feature 108): one-token citation correction
  (§5 item 10 cites §2 item 5, not item 4); checklist stays at 10 items.
- `tools/validate.sh` — feature 107 (default-sweep C1/C2 additionally check every
  `docs/nips/*.md`; `--payload` unchanged), feature 109 (C15 calls both
  `vlib_profiles_cover_roles` and the new `vlib_profiles_map_roles`), feature 108
  (`--help` paragraphs for C14–C16, the C5 text, and the payload-doc-set wording
  corrected).
- `tools/verify_lib.sh` — feature 109: new `vlib_profiles_map_roles` primitive.
- `tools/skill.json` — 0.3.0 → 0.4.0 (feature 099/106 registrations:
  `ecosystem_simplification_review`, `ecosystem_ga_gate`; the intentional-subset rule
  itself is enforced by the tightened C13, no new check number).
- `tools/fixtures_self_test.sh`, `tools/fixtures/skill_index_neg_unindexed_capability.json`
  (new), `tools/test_convergent_review.py` — features 103/104/105 (sandbox
  UNSUPPORTED reporting + `--allow-unsupported-isolation`, CI conformance mode, the
  nested-fixture claim map).

Nothing under `templates/`, `methodology/` or `bootstrap.sh` changed. All other
changes are under `.agent/` and `docs/` (envelope).

Reasoning:

- **Not MAJOR (Section 3.1).** No schema narrowed and no required key changed. No
  shipped file, module or protocol id was removed or renamed. The shipped v1.4.0 payload remains valid after re-bootstrap: the shipped
  skill capability modules are indexed, and newly registered modules satisfy C13.
  This does not promise identical validator results for independently modified manifests.
- **Not PATCH (Section 3.3).** A patch "corrects an error without changing the
  shape". This delta adds normative surface (two protocols become active and
  registered), an additive standard-doc column, a new verify_lib primitive, a new
  skill-index registration, and widened default-sweep checks — new surface, not a
  correction.
- **MINOR (Section 3.2).** New, optional capability without invalidating anything
  that previously validated. The per-feature verdicts in the approved contracts
  agree: 099 MINOR, 103 MINOR, 104 MINOR, 106 MINOR, 107 "MINOR at the next release
  (the default-mode sweep scope of shipped tools/validate.sh widens; consumers
  validate with `--payload`, which is unchanged; Section 3.4 rounds up)", 109 MINOR;
  105 and 108 are PATCH. The highest tier governs.
- **Payload compatibility, precisely scoped.** C1/C2 docs/nips scope and C15
  mapping direction are default-sweep only. C13 now enforces the intentional-subset
  rule in BOTH full sweep and `--payload`: each skill capability module must equal
  a NIZAM.json capability authoritative_source. An existing but unindexed module
  that previously passed C13 now fails. Re-bootstrap supplies the compliant shipped
  manifest/index pair; independent additions must register their authoritative source.
  The normative-status flips activate shipped documents. MINOR describes the
  shipped-payload upgrade; no byte-identical validator-behavior claim is made.
- **Section 3.4 (round up).** 105/108 are PATCH; the release straddles PATCH and
  MINOR, so the higher tier governs.

**Verdict: MINOR, so v1.5.0.** The CHANGELOG banner cites
`methodology/06_release_train.md` Section 3.2.

## 2. Edits — exact current text (HEAD `312257b`) → new text

Notation: `~~~text` fences hold literal file text. An edit replaces exactly one
occurrence of "Current" with "New". Line numbers are at HEAD `312257b`.

### E1 — `CHANGELOG.md`: roll `[Unreleased]` into a dated `[1.5.0]` section

Precedent (7441ffa, 2e12225): keep an **empty** `## [Unreleased]` heading directly
above the new dated section. The seven existing `[Unreleased]` bullets (lines
12–92) move **verbatim** — they are the phase-014 record and stay byte-identical,
including their own "(... at the next release ... no release is prepared and no tag
is created)" parentheticals, which were true when written. The banner and the three
new bullets carry the release framing. Two sub-edits: E1a (heading + banner + `### Added`
subhead) and E1b (three new bullets appended after the feature-106 bullet).

The existing `[Unreleased]` set names features 099, 103, 104, 105, 106 plus the two
envelope bullets — but **features 107, 108 and 109 have no `[Unreleased]` bullets**
(verified: `grep -n 'feature 10[789]' CHANGELOG.md` returns nothing). The release
record must name everything consumer-reachable, so E1b adds one bullet each for 107
and 108 and one envelope bullet covering feature 102's phase close; feature 109's
additive surface opens the `### Added` subhead. Nothing consumer-reachable is left
unnamed: 099/103/104/105/106 by the rolled bullets; 107/108/109/102-envelope by the
new ones; every changed payload file appears in at least one bullet.

E1a. Current (lines 8–10; count = 1):
~~~text
## [Unreleased]

### Changed
~~~
New:
~~~text
## [Unreleased]

## [1.5.0] - 2026-10-10

**Minor release** (`methodology/06_release_train.md` Section 3.2): phase 014 (GA track)
and its maintenance tranche land in the injected payload. The two ecosystem lifecycle
protocols are now normative -- `ecosystem/06_simplification_review.md` (Repeat) and
`ecosystem/08_ga_gate.md` (Promote/GA) flip `draft` -> `active` (0.2.0 each) and are
registered as capabilities in `NIZAM.json` and `tools/skill.json` (0.4.0), with the
operator gates `H-CONSOLIDATION` and `H-GA` defined in
`docs/planning/operator_gates.md` -- both DEFINED and OUTSTANDING, neither exercised,
and GA is not declared. `standard/capability_profiles.md` (0.4.0) gains an explicit
`Role` column whose mapping the validator's C15 check now enforces, and the
convergent-review suite ships a required-conformance mode with its own CI job. This is
additive protocol surface with validator enforcement changes. C1/C2 docs/nips and
C15 mapping checks widen the default sweep. C13 enforces the intentional-subset
rule in both full sweep and `--payload`: every skill capability module must equal
a NIZAM.json capability authoritative_source, so an existing but unindexed module
now fails. The shipped manifest/index pair remains compliant; independently added
modules must be registered. The release tier is rounded up per Section 3.4. Upgrade path:
consumers re-bootstrap from the `v1.5.0` tag to inherit the payload
(`methodology/06_release_train.md` Section 5). Everything else in this release is
framework-envelope only (the phase-014 close and GA-readiness dossier, planning
records, and the backlog reconciliation), none of which `bootstrap.sh` injects.

### Added

- **Phase 014 feature 109: C15 mapping direction** (additive; MINOR,
  `methodology/06_release_train.md` Section 3.2). `standard/capability_profiles.md`
  (0.4.0) gains an explicit `Role` column naming each capability profile's AGF role,
  and `tools/verify_lib.sh` gains the `vlib_profiles_map_roles` primitive parsing it:
  validator check C15 (default sweep) now calls both the coverage and the mapping
  primitives, so a swapped profile-to-role mapping fails. Additive and
  compatibility-first: `vlib_profiles_cover_roles` is unchanged. NDEBT-026.

### Changed
~~~

E1b. Current (lines 92–94; count = 1):
~~~text
  by the existing C13 substitution. `tools/README.md` (0.15.0) records the decision. NDEBT-044 (a).

## [1.4.0] - 2026-10-08
~~~
New:
~~~text
  by the existing C13 substitution. `tools/README.md` (0.15.0) records the decision. NDEBT-044 (a).
- **Phase 014 feature 107: docs/nips under C1/C2** (additive; MINOR,
  `methodology/06_release_train.md` Section 3.2). In the default sweep only,
  `tools/validate.sh` checks C1 (frontmatter schema) and C2 (format) over every
  markdown file under `docs/nips/`; those files stay outside the shipped-doc set, so
  C9/C10 do not scan them and `--payload` is unchanged. NIP-0002's frontmatter status
  moves `accepted` -> `active` (0.2.1), the schema enum value for an accepted NIP
  (NDEBT-044 b). `tools/README.md` (0.16.0) names the C1 row change.
- **Phase 014 feature 108: validator help and adapter-reference truth** (PATCH,
  `methodology/06_release_train.md` Section 3.3). `tools/validate.sh --help` is
  corrected: the C14-C16 paragraphs describe the checks as actually implemented (C15
  now names both primitives; C16 names the vetted feature-list primitive), the C5
  branding-sweep text matches its implementation, and the payload-doc-set wording
  matches the shipped file-set builders. `tools/interface.md` (0.3.1) corrects one
  citation (Section 5 item 10 cites Section 2 item 5, not item 4); the checklist stays
  at 10 items, so every adapter remains conformant. NDEBT-037, NDEBT-044 (c/d/f).
- **Phase 014 close and envelope.** Feature 102 assembled the GA-readiness dossier and
  closed the phase canonical-first: `H-GA` is OUTSTANDING and GA is not declared
  (`real_production_pilot` `not_met` per amendment A3). Amendments A1/A2
  (acceptance-test corrections) and A3 (features 100/101 cancelled) are planning
  records, as are the backlog reconciliation (`docs/planning/backlog_reconciliation.md`,
  `backlog_dag.json`) and the phase-014 planning artifacts -- nothing `bootstrap.sh`
  injects changes.

## [1.4.0] - 2026-10-08
~~~

Constraints the generator must preserve:

- The heading literally starts with `## [1.5.0] - `. Close-out group 4; date 2026-10-10.
- The section body contains `**Minor release**` and `methodology/06_release_train.md`
  (tier-banner regex `\*\*(Major|Minor|Patch) release\*\*`).
- The section must not contain the brand token C5 sweeps for (regex `n[i]zamiq`, any
  case — C5's implementation is case-sensitive `grep -InE` while its help says
  case-insensitive, NDEBT-044(c)) or `.svc` / `cluster.local`. Verified in simulation:
  0 brand lines added.
- The seven rolled bullets are not reworded.
- Keep-a-Changelog: the link lines at file top (`[Keep a Changelog]`, `[Semantic
  Versioning]`) and all older sections' dates are untouched.

### E2 — `NIZAM.json`: `framework.version`

Current (line 4; count = 1):
~~~text
    "version": "1.4.0",
~~~
New:
~~~text
    "version": "1.5.0",
~~~

`grep -n '"version"' NIZAM.json` returns only line 4 — the string `"1.4.0"` occurs
nowhere else in the file, so this edit touches the version field and nothing else.
No registration edits: the three phase-014 capability entries landed with features
099/106 (PRs #66/#72). The `capabilities` array, `key_documents` and the guide card
stay as HEAD.

### E3 — `CONTEXT.md`: frontmatter version and new `change_log[0]`

E3a. Current (lines 5–6; count = 1):
~~~text
version: 1.4.0
status: active
~~~
New:
~~~text
version: 1.5.0
status: active
~~~

E3b. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "1.4.0"
~~~
New:
~~~text
change_log:
  - version: "1.5.0"
    date: "2026-10-10"
    summary: "Prepare the v1.5.0 MINOR release: phase 014 (GA track) and its maintenance tranche -- the ecosystem lifecycle protocols ecosystem/06_simplification_review.md (Repeat) and ecosystem/08_ga_gate.md (Promote/GA) flip draft -> active (0.2.0 each) and are registered as capabilities in NIZAM.json and tools/skill.json (0.4.0), with the operator gates H-CONSOLIDATION and H-GA defined (both OUTSTANDING; GA not declared); standard/capability_profiles.md (0.4.0) gains the explicit Role column enforced by the new C15 mapping primitive vlib_profiles_map_roles; the convergent-review suite ships required-conformance mode with UNSUPPORTED reporting and its convergent_review CI job (tools/test_convergent_review.py, tools/README.md 0.17.0); the default sweep checks C1/C2 over docs/nips/ and C13 in both modes enforces the intentional-subset skill-index rule. The shipped manifest/index pair remains compliant after re-bootstrap; C13 now enforces the intentional-subset rule in both full sweep and --payload, so independently added skill modules must be registered in NIZAM.json. Everything else since v1.4.0 is framework-envelope only (the phase-014 close and GA-readiness dossier, amendments, planning records, backlog reconciliation). H-FRAMEWORK-RELEASE sign-off and tag authorization are recorded from the operator's 2026-10-10 request; the tag act itself remains the separate post-merge Orchestrator mechanic (methodology/06_release_train.md Section 6) and no tag is created by the pipeline."
  - version: "1.4.0"
~~~

Gate notes:

- Close-out group 1 needs the frontmatter `^version:` and `change_log[0].version` both
  equal to 1.5.0.
- C8 (version-bump-vs-changelog, NDS Sec 4) sweeps only frontmatter'd **.md** files in
  the shipped/payload sets (`build_shipped_md_set` / `build_payload_md_set`,
  validate.sh lines 478–530). `NIZAM.json` is JSON — never in the set — so the E2
  bump cannot trip C8. `CONTEXT.md` IS in the set; E3b provides the matching
  `change_log` entry, so C8 passes.
- The CONTEXT.md body has one `v1.4.0` mention (the historical change_log summary
  inside E3b's retained line) — it stays.

### E4 — `README.md`: the four pins (7 occurrences on 4 lines)

E4a. Current (line 22; count = 1):
~~~text
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.4.0/bootstrap.sh -o bootstrap.sh
~~~
New:
~~~text
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.5.0/bootstrap.sh -o bootstrap.sh
~~~

E4b. Current (line 24; count = 1):
~~~text
GOVERNANCE_TAG=v1.4.0 ./bootstrap.sh --tag v1.4.0
~~~
New:
~~~text
GOVERNANCE_TAG=v1.5.0 ./bootstrap.sh --tag v1.5.0
~~~

E4c. Current (line 27; count = 1):
~~~text
`--tag v1.4.0` (equivalently `GOVERNANCE_TAG=v1.4.0`) pins the inheritance to a real
~~~
New:
~~~text
`--tag v1.5.0` (equivalently `GOVERNANCE_TAG=v1.5.0`) pins the inheritance to a real
~~~

E4d. Current (line 44; count = 1):
~~~text
See the [v1.4.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.4.0)
~~~
New:
~~~text
See the [v1.5.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.5.0)
~~~

**Leave unchanged:** line 45, the `v0.9.0 → v1.0.0` migration-guide link. Close-out
group 3's docstring (`release_closeout.py` lines 189–195) deliberately excludes it;
it stays pinned to the last release that shipped a migration guide (contract 097's
`migration_link_exclusion_rationale`). v1.5.0 needs no migration guide (upgrade path
is re-bootstrap); 2e12225 left it untouched too.

After the edit, `grep -c 'v1\.4\.0' README.md` must be 0 and
`grep -o 'v1\.5\.0' README.md | wc -l` must be 7 (verified in simulation).

### E5 — `docs/guide/index.html`: meta and footer

E5a. Current (line 6; count = 1):
~~~text
<meta name="framework-version" content="1.4.0">
~~~
New:
~~~text
<meta name="framework-version" content="1.5.0">
~~~

E5b. Current (line 675; count = 1):
~~~text
  <p>Nizam framework version <strong><span id="footer-version">1.4.0</span></strong>.</p>
~~~
New:
~~~text
  <p>Nizam framework version <strong><span id="footer-version">1.5.0</span></strong>.</p>
~~~

Close-out group 2 (`group_guide`, release_closeout.py lines 172–186) checks the two
anchors with **literal substring** matches — `<meta name="framework-version"
content="{V}">` and `<span id="footer-version">{V}</span>`; the guide's ecosystem
card (updated by feature 099) carries no version string. At HEAD, `1.4.0` occurs
exactly twice in the file (both anchors — capture `06-guide-anchors.txt`), so the
post-edit state is exactly 2 x `1.5.0` and 0 x `1.4.0`. C10 sub-check (3) also reads
both anchors against `NIZAM.json` — E2 and E5 must land together (they do).

**No guide card edits.** The card's 06/08 rows and ecosystem document list landed
with feature 099 (PR #66).

### E6 — `docs/planning/ROADMAP.md`

Precedent (0.38.0 / 0.44.0, accepted as Q2 in the v1.4.0 plan): insert the
disposition bullet ahead of the latest-released bullet, which stays byte-identical —
the close-out gate's body pattern is version-scoped
(`release_closeout.py:276-279`), so at V=1.5.0 the v1.4.0 line does not count, and
until the authorized tag act is executed, "Latest released tag: v1.4.0" is the true
latest-released record. The released-record roll (with the tag object id) is the
post-release refresh's job (0.45.0 precedent), stated in the bullet.

E6a. Frontmatter version. Current (line 5; count = 1):
~~~text
version: 0.49.0
status: active
~~~
New:
~~~text
version: 0.50.0
status: active
~~~

E6b. New `change_log[0]`. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "0.49.0"
~~~
New:
~~~text
change_log:
  - version: "0.50.0"
    date: "2026-10-10"
    summary: "v1.5.0 release preparation (operator-requested 2026-10-10; H-FRAMEWORK-RELEASE Section 2 sign-off given, and this time the tag authorization is INCLUDED in the same sentence): phase 014 (GA track) and its maintenance tranche are packaged as the next MINOR release. Current Position gains the 'Release in preparation: v1.5.0' bullet ahead of the latest-released bullet, which stays unedited -- v1.4.0 remains the latest released tag until the authorized tag act is executed after this PR merges, and the close-out gate's body pattern is version-scoped, so the v1.4.0 line does not count at V=1.5.0 (the 0.38.0/0.44.0 precedent). Release fact for the post-release refresh: once v1.5.0 is tagged, feature 102's no-v1.5.0-tag acceptance test and product_spec_014's phase-scoped criterion go stale, so the phase-014 artifacts are re-baselined again at that time (no phase-014 artifact is edited here). run_state, manifest and DEBT.md are untouched."
  - version: "0.49.0"
~~~

E6c. Current Position: insert the single disposition line. Current (line 849;
count = 1):
~~~text
- **Latest released tag: v1.4.0 (MINOR) — RELEASED 2026-10-08 at `9edd5d0` (PR #63).**
~~~
New (the new bullet, then the original line **unchanged**; the body lines below it
stay untouched):
~~~text
- **Release in preparation: v1.5.0 (MINOR) — PREPARED 2026-10-10; tag act AUTHORIZED, awaits merge.**
  Requested by the operator 2026-10-10, verbatim: "ensure the that
  documentation and change notes is updated and ready for relase. You are authorized
  to manage, triage as necessary, your PR's and once clean merge as appropriate. you
  are authorized to tag and pin the release." — the `H-FRAMEWORK-RELEASE` Section 2
  human sign-off, and, unlike v1.4.0, the tag authorization is included in the same
  sentence ("you are authorized to tag and pin the release"), so no separate
  post-merge tag authorization is awaited. Per `methodology/06_release_train.md`
  Section 6 this change is the durable preparation only; the tag act remains the
  separate Orchestrator mechanic, executed after this PR merges — the pipeline never
  self-tags. The consumer-reaching content since v1.4.0 is exactly the phase-014
  (GA track) surface and its maintenance tranche (PRs #64–#77): the ecosystem
  lifecycle protocols flip `draft` -> `active` and are registered (`NIZAM.json`,
  `tools/skill.json`), the operator gates `H-CONSOLIDATION` / `H-GA` are defined (both
  OUTSTANDING), the convergent-review suite ships required-conformance mode with its
  CI job, `standard/capability_profiles.md` gains the C15-enforced `Role` column, the
  default sweep widens (docs/nips under C1/C2 and the C15 mapping), C13 enforces
  the skill-index subset rule in both full sweep and `--payload`,
  and `tools/interface.md` plus the validator help texts are corrected. Everything
  else (the GA-readiness dossier, amendments, planning records, backlog
  reconciliation) is framework-envelope only. MINOR per
  `methodology/06_release_train.md` Section 3.2, rounded up per Section 3.4. This
  release-preparation change synchronizes every version anchor to 1.5.0 and cuts the
  dated `[1.5.0]` CHANGELOG section; the readiness record
  (`.agent/evidence/release-readiness-v1.5.0.md`) is written by the Evaluator after
  independently re-running the checks. Post-release fact: once the authorized tag is
  pushed, feature 102's no-`v1.5.0`-tag acceptance test and the spec's phase-scoped
  criterion go stale — the post-release refresh rolls this bullet to the released
  record with the tag object id and re-baselines the phase-014 artifacts.
- **Latest released tag: v1.4.0 (MINOR) — RELEASED 2026-10-08 at `9edd5d0` (PR #63).**
~~~

ROADMAP invariant after E6: exactly one body line, after the second `---`, matches
`Latest released tag: v1\.5\.0\b|Release in preparation: v1\.5\.0\b` — the first
line of the E6c bullet. Checked in simulation: count = 1. The NIP-0003
queued-candidate section's "expected v1.5.0 / v1.6.0" wording (lines 325–328) names
no disposition phrase and is untouched, as is every older released record.

**Explicitly not done in E6:** the `## Current Position` heading date and the
open-debt bullet stay unchanged (NDEBT-044(e) precedent); the "Prior released tag"
and "Earlier released tag" bullets stay unchanged; the first (phase-status) bullet
stays unchanged. No phase-014 artifact is edited.

### E7 — `docs/planning/operator_gates.md`

E7a. Current (line 5; count = 1):
~~~text
version: 0.29.0
status: active
~~~
New:
~~~text
version: 0.30.0
status: active
~~~

E7b. Current (lines 8–9; count = 1):
~~~text
change_log:
  - version: "0.29.0"
~~~
New:
~~~text
change_log:
  - version: "0.30.0"
    date: "2026-10-10"
    summary: "H-FRAMEWORK-RELEASE row's Disposition cell gains the v1.5.0 PREPARED clause: phase 014 (GA track) and its maintenance tranche are packaged as the next MINOR; this release-preparation change bumps CHANGELOG, the C10 version anchors, and the readiness record (.agent/evidence/release-readiness-v1.5.0.md) to completion. Unlike v1.4.0, the operator's 2026-10-10 authorization includes the tag act verbatim ('you are authorized to tag and pin the release'), so no separate post-merge tag authorization is awaited; per methodology/06_release_train.md Section 6 the tag act itself remains the separate Orchestrator mechanic, executed after this PR merges, and the tag remains OUTSTANDING until then. The operator's full request is quoted verbatim in the row. Appended to the existing recurring row, not a new row, matching the v0.25.0 precedent."
  - version: "0.29.0"
~~~

E7c. Row-anchored append to the existing `H-FRAMEWORK-RELEASE` row (line 149; a
single physical line). Substring replacement inside that row only. Current substring
(the row's tail; count = 1 in the file):
~~~text
published from the `[1.4.0]` CHANGELOG section at 2026-10-08T10:26:22Z. Recurring: outstanding again at the next release. |
~~~
New substring:
~~~text
published from the `[1.4.0]` CHANGELOG section at 2026-10-08T10:26:22Z. v1.5.0 (MINOR) is PREPARED (`.agent/evidence/release-readiness-v1.5.0.md`), packaging phase 014 (GA track) and its maintenance tranche (PRs #64-#77): the ecosystem protocols 06_simplification_review / 08_ga_gate flip draft -> active with capability registration (NIZAM.json, tools/skill.json), H-CONSOLIDATION / H-GA are defined (both OUTSTANDING; GA not declared), the convergent-review suite gains required-conformance mode and its CI job, capability_profiles.md gains the C15-enforced Role column, and the default sweep widens (docs/nips under C1/C2 and the C15 mapping), and C13 enforces the skill-index subset rule in both full sweep and --payload. The shipped manifest/index pair is compliant; independently added skill modules must be registered. CHANGELOG, C10 version anchors, and the readiness record are complete. The operator requested this release verbatim ('ensure the that documentation and change notes is updated and ready for relase. You are authorized to manage, triage as necessary, your PR's and once clean merge as appropriate. you are authorized to tag and pin the release.', 2026-10-10), recorded here as the Section 2 human sign-off for cutting the release preparation; unlike v1.4.0 the same authorization includes the tag act ('you are authorized to tag and pin the release'), so no separate post-merge tag authorization is awaited -- while per Section 6 the tag act itself remains the separate Orchestrator mechanic, executed after this PR merges; the tag remains OUTSTANDING until then. Recurring: outstanding again at the next release. |
~~~

Verbatim-quote rule. E6c, E7b and E7c quote the operator verbatim, per the
v0.22.0/v0.25.0 precedent — including the typo "relase" (reproduced as-is, as the
v1.1.0 row reproduced "The pR #55" unmarked; see Hazard H1). The quote contains no
`|` and no brand token; its single `'` (in "PR's") is ordinary prose inside the
table cell. The row's cell count is preserved: pipe count 5 before and after
(verified in simulation).

### E8 — `.agent/evidence/release-readiness-v1.5.0.md`: NOT written by the generator

The **@evaluator** writes this file after it independently runs Section 4. Its
structure mirrors `.agent/evidence/release-readiness-v1.4.0.md` with these
release-specific changes:

1. `# Release Readiness — v1.5.0`.
2. **Gate paragraph:**
   - Gate: `H-FRAMEWORK-RELEASE` (operator-only); prepared 2026-10-10 on the
     `chore/v1.5.0-release-prep` branch from `main` `312257b` (phase 014 complete,
     PR #77).
   - What is packaged: the phase-014 (GA track) surface and maintenance tranche —
     the 06/08 activation wave with capability registrations, the
     required-conformance convergent-review suite + CI job, the capability-profile
     Role column with the C15 mapping primitive, the default-sweep widenings, and
     the interface.md / help-text corrections. Target tier: MINOR per
     `methodology/06_release_train.md` Section 3.2, round-up per Section 3.4.
   - **The distinction from v1.4.0, stated plainly:** the operator's 2026-10-10
     authorization includes the tag act ("you are authorized to tag and pin the
     release"), so the readiness record does NOT say tag authorization is
     outstanding; it says the tag ACT remains the separate Section 6 Orchestrator
     mechanic, executed after this PR merges. "At preparation time the pipeline has
     not created, pushed, or executed `v1.5.0`."
3. **Envelope paragraph:** everything else since v1.4.0 is envelope-only (phase-014
   close and GA-readiness dossier with H-GA OUTSTANDING and GA undeclared,
   amendments A1/A2/A3, planning records, backlog reconciliation, `docs/planning/*`,
   `.agent/*`, `CHANGELOG.md` as envelope). Record the post-release re-baseline fact:
   once v1.5.0 is tagged, feature 102's no-`v1.5.0`-tag acceptance test and the
   spec's phase-scoped criterion go stale.
4. `## Automated readiness`, items 1–5, each with a bold result and its command:
   1. `bash tools/validate.sh`: **16/16 PASS**
   2. `bash tools/fixtures_self_test.sh`: **147/147 PASS**
   3. `python3 .github/scripts/release_closeout.py --mode pr` at V=1.5.0: **PASS**,
      all five anchor groups
   4. `bash tools/e2e_bootstrap_test.sh`: **PASS** (note honestly that the harness
      exercises the checkout's HEAD commit, and record the exercised
      `resolved_sha=`).
   5. Tag probes: `git rev-parse -q --verify refs/tags/v1.5.0` non-zero (exit 1) and
      `git ls-remote --tags origin v1.5.0` empty **and exit 0** — plus a control
      probe (`git ls-remote --tags origin v1.4.0`) proving origin was reachable and
      answering. Empty output with a non-zero exit is INCONCLUSIVE, not a pass.
5. **Raw captured outputs** under `.agent/evidence/release-v1.5.0-prep/`:
   `01-validate-sh.txt`, `02-fixtures-self-test.txt`, `03-release-closeout-pr.txt`,
   `04-e2e-bootstrap.txt`, `05-tag-probe-and-sanitization.txt` (05 carries both tag
   probes with exit codes, `git status --porcelain --untracked-files=all`, the §3
   scope-guard output, check #13, per-file control-character counts, and the
   brand-token sweep with its positive control), `06-guide-anchors.txt`. This plan
   is `00-`.
6. `## Content map` table (Surface | Summary) naming: the 06/08 protocols +
   registrations; `standard/capability_profiles.md` + `tools/verify_lib.sh`;
   `tools/test_convergent_review.py` + `.github/workflows/compliance.yml` (envelope
   note); `tools/validate.sh` sweep widenings; `tools/interface.md`; `NIZAM.json`
   (`framework.version` 1.5.0); `docs/guide/index.html` (meta/footer only);
   `CHANGELOG.md` / `README.md` / `CONTEXT.md`; `docs/planning/ROADMAP.md` /
   `docs/planning/operator_gates.md`.
7. **Closing line, verbatim form:** "`H-FRAMEWORK-RELEASE` sign-off and tag
   authorization are recorded; the tag act itself remains the separate
   Orchestrator mechanic executed after this PR merges — this pipeline never
   self-tags per `methodology/06_release_train.md` Section 6."

**Non-edits (named):** `.agent/run_state.json` — the tag act records there AFTER
the tag, by the Orchestrator at the post-release refresh (NDEBT-018); the
CHANGELOG dates of all older sections; and every file not listed in E1–E8.

## 3. Scope: touched files and must-not-touch list

**Generator touches exactly 7 files:** `CHANGELOG.md`, `NIZAM.json`, `CONTEXT.md`,
`README.md`, `docs/guide/index.html`, `docs/planning/ROADMAP.md` and
`docs/planning/operator_gates.md` — the same anchor set as 7441ffa / 2e12225.

**Evaluator adds:** `.agent/evidence/release-readiness-v1.5.0.md` and
`.agent/evidence/release-v1.5.0-prep/01-…06-*.txt`. This plan,
`00-release-prep-plan.md`, already exists (planner output).

**Precondition H-0 (`.nizam/` sandbox, see Hazard H2).** The working tree at HEAD
carries a pre-existing untracked `.nizam/` directory — a consumer-bootstrap artifact
created 2026-10-10 03:08 by an earlier run, ~190 files, none created by this prep.
`git status --porcelain` collapses it to `?? .nizam/`, but
`git ls-files --others --exclude-standard` lists every file, and the part-B guard
correctly fails closed on each one (verified, §5.1). It is not a governed path and
no generator or evaluator edit may touch it; the **Orchestrator removes it before
the generator runs** (or points the generator at a clean checkout). The planner may
edit only this plan and the capture files.

**MUST NOT TOUCH** (any diff here is a Mode B rejection):

- `.agent/run_state.json` — touched only at the post-release tag record, by the
  Orchestrator.
- `docs/planning/manifest.json`, `docs/planning/DEBT.md`,
  `docs/planning/HANDOVER.md`, `docs/planning/backlog_reconciliation.md`,
  `docs/planning/backlog_dag.json`
- All phase-014 artifacts: `.agent/product_spec_014.md`,
  `.agent/feature_list_014.json`, `docs/planning/phase_014.yaml`
- `docs/nips/*` (NIP-0002 stays 0.2.1; NIP-0003 unedited pending `H-NIP`)
- Everything under `methodology/`, `schema/`, `tools/`, `standard/`, `templates/`,
  `ecosystem/` and `registry/`, plus `bootstrap.sh`
- `.github/` (including `.github/workflows/compliance.yml` and
  `.github/scripts/release_closeout.py`)
- `docs/migration-*.md`, `docs/architecture/*` and every other `.agent/*` file
  except the E8 evaluator outputs

**Mechanical scope guard, part A (tracked edits only):**
`git diff --name-only 312257b -- . ':!.agent/evidence/release-readiness-v1.5.0.md' ':!.agent/evidence/release-v1.5.0-prep/'`
must list exactly the 7 generator files (§4 #11). It cannot see untracked files.

**Mechanical scope guard, part B (untracked-aware allowlist; authoritative).**
Self-contained; exits 0 only if every changed path is on the allowlist AND all 7
generator files appear as `M`. Anything else prints `UNEXPECTED:` or `MISSING:` and
exits 1. Quoted paths never match and fail closed.

Input: the union of `git diff --name-status 312257b` (tracked, committed or not)
and `git ls-files --others --exclude-standard` (untracked, gitignore-respecting).
The ignored classes (OS/editor junk, `*.log`, `node_modules/`, `__pycache__/`,
`*.pyc`, `.venv/`) cannot hide a governed path.

Allowlist:

- `M` on each of the 7 generator files — all 7 required; any other status letter
  (A/D/R/T) fails.
- `?? .agent/evidence/release-readiness-v1.5.0.md`
- `?? .agent/evidence/release-v1.5.0-prep/<file>` — the prefix includes the
  trailing `/`; a sibling like `release-v1.5.0-prep-x/` fails.
- `?? .agent/validator/release-v1.5.0-<name>.json` — the validator's own verdict
  files (precedent: `.agent/validator/release-v1.4.0-*.json`, `.agent/validator/nip-0003-review.json`).
  Narrow regex, no subdirectories or traversal.

```sh
scope_guard() {
  awk '
    BEGIN {
      n = split("CHANGELOG.md NIZAM.json CONTEXT.md README.md docs/guide/index.html docs/planning/ROADMAP.md docs/planning/operator_gates.md", g, " ")
      for (i = 1; i <= n; i++) want["M " g[i]] = 1
      bad = 0
    }
    ($0 in want) { seen[$0] = 1; next }
    $0 == "?? .agent/evidence/release-readiness-v1.5.0.md" { next }
    index($0, "?? .agent/evidence/release-v1.5.0-prep/") == 1 && $0 !~ /\.\.|\/$/ { next }
    $0 ~ /^\?\? \.agent\/validator\/release-v1\.5\.0-[A-Za-z0-9._-]+\.json$/ && $0 !~ /\.\./ { next }
    { print "UNEXPECTED: " $0; bad = 1 }
    END {
      for (k in want) if (!(k in seen)) { print "MISSING: " k; bad = 1 }
      exit bad
    }'
}
{ git diff --name-status 312257b | awk -F '\t' '{ print $1 " " $2 (NF > 2 ? " -> " $3 : "") }'
  git ls-files --others --exclude-standard | sed 's/^/?? /'
} | scope_guard; echo "scope_guard_exit=$?"
```

Expected (evaluator, after the generator's edits and the evaluator's outputs
exist): no `UNEXPECTED:`/`MISSING:` lines and `scope_guard_exit=0`.

**Negative control** (evaluator dry-runs it in the same shell after defining
`scope_guard`; no repository state involved):

```sh
OK7='M CHANGELOG.md
M NIZAM.json
M CONTEXT.md
M README.md
M docs/guide/index.html
M docs/planning/ROADMAP.md
M docs/planning/operator_gates.md'
printf '%s\n' "$OK7" '?? .agent/evidence/release-readiness-v1.5.0.md' '?? .agent/evidence/release-v1.5.0-prep/01-validate-sh.txt' '?? .agent/validator/release-v1.5.0-plan.json' | scope_guard; echo "positive_exit=$?"
printf '%s\n' "$OK7" '?? methodology/10_live_runtime_sessions.md' | scope_guard; echo "neg_untracked_forbidden_exit=$?"
printf '%s\n' "$OK7" 'M .agent/run_state.json' | scope_guard; echo "neg_tracked_forbidden_exit=$?"
printf '%s\n' "$OK7" '?? .agent/evidence/release-v1.5.0-prep-x/evil.txt' | scope_guard; echo "neg_sibling_prefix_exit=$?"
printf '%s\n' "$OK7" '?? .agent/validator/release-v1.5.0-../../ecosystem/x.json' | scope_guard; echo "neg_traversal_exit=$?"
printf '%s\n' "$OK7" | grep -v 'NIZAM.json' | scope_guard; echo "neg_missing_generator_file_exit=$?"
printf '%s\n' "$OK7" | sed 's/^M CONTEXT.md$/D CONTEXT.md/' | scope_guard; echo "neg_wrong_status_exit=$?"
printf '%s\n' "$OK7" '?? .nizam/' | scope_guard; echo "neg_nizam_sandbox_exit=$?"
```

Expected: `positive_exit=0`; every `neg_*_exit=1` with the matching
`UNEXPECTED:`/`MISSING:` line. The last control pins Hazard H2: a `.nizam/`
sandbox in the tree fails the guard, so H-0 must hold before the generator runs.

## 4. Verification commands (evaluator runs; expected results)

Commands containing a pipe or regex alternation (`#5a`, `#5b`, `#7`, `#8`, `#10`,
`#10-control`, `#12`, `#13`, `#14`) are **not** in the table — table cells would
need `\|`, changing their meaning. They appear verbatim, with real `|`, in the
fenced blocks below the table.

| # | Command | Expected |
|---|---|---|
| 1 | `bash tools/validate.sh` | last line `SUMMARY: 16 passed, 0 failed`; exit 0 (C5, C8, C10 green) |
| 2 | `bash tools/fixtures_self_test.sh` | `SELF-TEST OK: 147/147 fixtures accounted for, 0 failed`; exit 0 |
| 3 | `python3 .github/scripts/release_closeout.py --mode pr` | 5 x `PASS`, final line `Release close-out: all internal version anchors agree with V=1.5.0 (--mode pr).`; exit 0 |
| 4 | `bash tools/e2e_bootstrap_test.sh` | exit 0; `e2e_bootstrap_test.sh: PASS`. Exercises HEAD, not the uncommitted tree — record the exercised `resolved_sha=` honestly in the capture |
| 5a | fenced block `#5a` | no SHA printed; `exit=1` |
| 5b | fenced block `#5b` | empty output **and** `exit=0`, both captured. Empty output with a non-zero exit (e.g. 128, network/auth) is INCONCLUSIVE, not a pass |
| 6 | `python3 -c "import json;print(json.load(open('NIZAM.json'))['framework']['version'])"` | `1.5.0` |
| 7 | fenced block `#7` | `0` then `7` |
| 8 | fenced block `#8` | `1` |
| 9 | `grep -c '^- \*\*Latest released tag: v1.4.0 (MINOR) — RELEASED 2026-10-08 at' docs/planning/ROADMAP.md` | `1` (v1.4.0 released record kept byte-identical) |
| 10 | fenced block `#10` | no match lines; `exit=1` |
| 10-control | fenced block `#10-control` | three match lines; `exit=0` (proves `#10` is not vacuous) |
| 11 | §3 scope guard part A | exactly the 7 generator files (tracked edits only) |
| 11b | §3 scope guard part B + negative control | `scope_guard_exit=0`; control: `positive_exit=0`, all `neg_*_exit=1` |
| 12 | fenced block `#12` | `0` (tracked forbidden paths unchanged; part B covers untracked) |
| 13 | fenced block `#13` | `exit=0`. CHANGELOG lines 8–10 are exactly `## [Unreleased]`, an empty line, `## [1.5.0] - 2026-10-10` |
| 14 | fenced block `#14` | `0` then `2` |

`#5a`
```sh
git rev-parse -q --verify refs/tags/v1.5.0; echo "exit=$?"
```

`#5b`
```sh
git ls-remote --tags origin v1.5.0; echo "exit=$?"
```

`#7`
```sh
grep -c 'v1\.4\.0' README.md; grep -o 'v1\.5\.0' README.md | wc -l
```

`#8`
```sh
python3 -c "import re,sys;sys.path.insert(0,'.github/scripts');import release_closeout as r;b=r.document_body(open('docs/planning/ROADMAP.md').read());print(sum(1 for l in b.splitlines() if re.search(r'Latest released tag: v1\.5\.0\b|Release in preparation: v1\.5\.0\b',l)))"
```

`#10`
```sh
git diff 312257b -- CHANGELOG.md NIZAM.json README.md CONTEXT.md docs/guide/index.html docs/planning/ROADMAP.md docs/planning/operator_gates.md | sed -n '/^+[^+]/s/^+//p' | grep -inE 'n[i]zamiq|\.svc|cluster\.local'; echo "exit=$?"
```

`#10-control` (a synthetic positive; the token is assembled at run time, so this
plan file never contains it literally)
```sh
printf '%s\n' "x $(printf 'n%szamiq' i | tr a-z A-Z) y" 'host.svc' 'a.cluster.local' | grep -inE 'n[i]zamiq|\.svc|cluster\.local'; echo "exit=$?"
```

`#12`
```sh
git diff 312257b -- .agent/run_state.json docs/planning/manifest.json docs/planning/DEBT.md docs/planning/HANDOVER.md docs/planning/backlog_reconciliation.md docs/planning/backlog_dag.json docs/nips .agent/product_spec_014.md .agent/feature_list_014.json docs/planning/phase_014.yaml methodology schema tools standard templates ecosystem registry .github bootstrap.sh | wc -c
```

`#13`
```sh
test "$(sed -n '8,10p' CHANGELOG.md)" = "$(printf '## [Unreleased]\n\n## [1.5.0] - 2026-10-10')"; echo "exit=$?"
```

`#14`
```sh
grep -c '1\.4\.0' docs/guide/index.html; grep -o '1\.5\.0' docs/guide/index.html | wc -l
```

Mode B (validator) note: `git diff HEAD` (or `git diff 312257b`) must show only
the E1–E7 hunks.

### 4.1 Hazards

- **H1 — the operator's typo "relase".** The verbatim quote contains "ready for
  relase" (and "ensure the that"). It is reproduced **as-is**, matching the
  v1.1.0-row precedent ("The pR #55 is merged." kept unmarked). No `[sic]`, no
  silent correction — the records quote the operator's exact words.
- **H2 — the pre-existing `.nizam/` untracked sandbox** (~190 files, created
  2026-10-10 03:08). The part-B guard fails closed on it (§5.1 captured this);
  Precondition H-0 requires the Orchestrator to remove it (or use a clean
  checkout) before the generator runs. It is not evidence, not governed, and no
  generator/evaluator step may edit it.
- **H3 — tag probe fail-closed.** `#5b` requires empty output AND exit 0. A
  network/auth failure exits 128 — inconclusive, blocks readiness. The evaluator
  should also run the control probe `git ls-remote --tags origin v1.4.0` in the
  same session (expected: the v1.4.0 ref, exit 0) to prove origin was answering.
- **H4 — Keep-a-Changelog link lines.** The `[Keep a Changelog]` / `[Semantic
  Versioning]` link lines at the top of CHANGELOG.md and every older section's
  dates are untouched; only the heading/banner insert and the three-bullet append
  change the file.
- **H5 — guide anchor format.** `group_guide` matches literal substrings
  (`release_closeout.py:184-185`): `<meta name="framework-version"
  content="{V}">` and `<span id="footer-version">{V}</span>`. The two anchors at
  HEAD are the file's only `1.4.0` strings (capture 06); the edit rewrites both
  digits and nothing else — no reformatting, no card edits.
- **H6 — C8 vs the NIZAM.json bump.** C8 only sweeps frontmatter'd .md files
  (§E3 note); the JSON bump cannot trip it. CONTEXT.md's bump is covered by the
  E3b change_log entry.
- **H7 — tag authorization ≠ tag act.** Every record (E6c, E7b, E7c, E3b, E8)
  states both halves: the authorization INCLUDES the tag act, and per Section 6
  the act itself is executed by the Orchestrator only after this PR merges. No
  record may read as if the tag exists or as if the pipeline self-tags.

### 4.2 Rollback

Every edit is a text insertion/replacement in seven tracked files; rollback is
`git checkout -- <file>` (or reverting the single release-prep commit before
merge). No schema, tool, migration or state change is involved. If the PR is
abandoned, no anchor file is left at 1.5.0 and no tag exists — the tree returns
to the HEAD `312257b` state byte-identically.

## 5. Plan self-check (planner, in-memory, read-only)

The planner parsed this plan's own `~~~text` Current/New pairs and applied them
to **in-memory** copies of the HEAD `312257b` files (harness
`/tmp/v150-selfcheck.py`, run with `PYTHONDONTWRITEBYTECODE=1`). It asserted that
every Current block occurs exactly once, then imported
`.github/scripts/release_closeout.py` and ran its groups at V=1.5.0. No
repository file other than this plan and the capture files was written.
Captured output:

~~~
applied pairs: 17; all unique
PASS CONTEXT.md version anchor (frontmatter + change_log[0])
PASS docs/guide/index.html version anchors (meta + footer)
PASS README.md version pins (curl URL / GOVERNANCE_TAG / --tag / releases-tag)
PASS CHANGELOG.md top released section (heading + tier banner)
PASS ROADMAP.md disposition line (Latest released tag / Release in preparation)
PASS x4 [tag-mode semantics, tag=v1.5.0]
tag-mode (c) heading == tag: True
ROADMAP disposition count: 1
v1.4.0 released line kept: 1
yaml CONTEXT.md 1.5.0 1.5.0 2026-10-10
yaml docs/planning/ROADMAP.md 0.50.0 0.50.0 2026-10-10
yaml docs/planning/operator_gates.md 0.30.0 0.30.0 2026-10-10
README v1.4.0 lines: 0 | v1.5.0 occurrences: 7
guide 1.4.0: 0 | 1.5.0: 2
NIZAM version: 1.5.0
CHANGELOG 8-10: '## [Unreleased]' '' '## [1.5.0] - 2026-10-10'
brand lines: CHANGELOG 0->0, NIZAM.json 0->0, CONTEXT.md 0->0, README.md 0->0,
  guide 0->0, ROADMAP.md 4->4 (pre-existing, not C5-swept), operator_gates 0->0
operator_gates row cells (pipe count): 5 -> 5
quote in row: True | tag-auth phrase in row: True | tag-auth phrase in ROADMAP bullet: True
sim_exit=0
~~~

### 5.1 Fenced commands run verbatim at HEAD `312257b`

The planner ran every labelled ```` ```sh ```` block of Section 4 (and the §3
guard) against the **current HEAD tree, before any release edit**. Captured
output:

~~~
===== #5a =====          (no output) exit=1
===== #5b =====          (no output) exit=0
===== #7 =====           4 / 0
===== #8 =====           0   [V=1.4.0 variant, demonstration only: 1]
===== #9 =====           1
===== #10 =====          (no output) exit=1
===== #10-control =====  1:x <TOKEN-UPPERCASE> y / 2:host.svc / 3:a.cluster.local / exit=0
===== #12 =====          0
===== #13 =====          exit=1
===== §3 part B on current tree =====
UNEXPECTED: ?? .nizam/<190 files, one line each>
MISSING: M <all 7 generator files>
scope_guard_exit=1
===== §3 part B negative control =====
positive_exit=0
UNEXPECTED: ?? methodology/10_live_runtime_sessions.md    neg_untracked_forbidden_exit=1
UNEXPECTED: M .agent/run_state.json                       neg_tracked_forbidden_exit=1
UNEXPECTED: ?? .agent/evidence/release-v1.5.0-prep-x/evil.txt  neg_sibling_prefix_exit=1
UNEXPECTED: ?? .agent/validator/release-v1.5.0-../../ecosystem/x.json  neg_traversal_exit=1
MISSING: M NIZAM.json                                     neg_missing_generator_file_exit=1
UNEXPECTED: D CONTEXT.md + MISSING: M CONTEXT.md          neg_wrong_status_exit=1
UNEXPECTED: ?? .nizam/                                    neg_nizam_sandbox_exit=1
~~~

`<TOKEN-UPPERCASE>` is the run-time-assembled brand token, redacted here so this
file never carries the literal. Interpretation, HEAD versus post-edit:

| # | At HEAD (now) | Expected post-edit | Same? | Why it differs / what the HEAD run proves |
|---|---|---|---|---|
| 5a | `exit=1` | `exit=1` | yes | No local tag; probe well-formed |
| 5b | empty, `exit=0` | empty, `exit=0` | yes | Origin reachable AND no tag: a genuine negative |
| 7 | `4` then `0` | `0` then `7` | no | HEAD still pins v1.4.0 on 4 lines; the `wc -l` pipe proves the second number works |
| 8 | `0` | `1` | no | No v1.5.0 disposition before E6c; the V=1.4.0 variant prints `1`, proving the pattern matches a real disposition line |
| 9 | `1` | `1` | yes | The v1.4.0 released record exists now and is kept byte-identical |
| 10 | no hits, `exit=1` | same | yes | `#10-control` proves the pattern matches all three alternatives |
| 12 | `0` | `0` | yes | Forbidden tracked paths unchanged; the pipe works |
| 13 | `exit=1` | `exit=0` | no | HEAD line 10 is `### Changed`; E1a inserts the dated heading there |
| 11b | `scope_guard_exit=1` (7 x MISSING; UNEXPECTED only for the pre-existing `.nizam/` files) | `scope_guard_exit=0` | no | No generator edits exist yet; the two existing untracked prep files (this plan, the validator verdict when it lands) are correctly allowed |
| 11b control | `positive_exit=0`, all seven `neg_*_exit=1` | same | yes | The guard catches untracked/tracked forbidden paths, sibling-prefix and traversal paths, a missing generator file, a wrong status letter, and the `.nizam/` sandbox |

The simulation above was captured before the accuracy corrections below; the
Generator must repeat the simulation against the corrected E1/E3/E6/E7 text. It is not a
substitute for the evaluator's real runs in Section 4, which also cover C8/C10
and the e2e harness.

## 6. Post-merge (out of scope for this change; recorded for the Orchestrator)

1. The PR merges after review (the operator authorized managing/triage/merge of
   this PR in the same 2026-10-10 sentence).
2. **The tag act — already authorized** ("you are authorized to tag and pin the
   release"), unlike v1.4.0: no further authorization is awaited. The
   Orchestrator, as the delegated `methodology/06_release_train.md` Section 6
   mechanic, pushes annotated `v1.5.0` at the reviewed merge commit. The
   decision is recorded in `run_state` (NDEBT-018) as at every release.
3. `release.yml` runs the tag-mode close-out (tag shape; tag vs NIZAM.json at
   the tag; all six anchor groups; CHANGELOG top section vs the tag) and
   publishes the Release from the `[1.5.0]` section.
4. The post-release refresh (0.39.0 / 0.42.0 / 0.45.0 precedent):
   - ROADMAP: remove the Release-in-preparation bullet and roll "Latest
     released tag" to v1.5.0 with the tag object id; the released-record roll.
   - operator_gates: EXECUTED clause for v1.5.0.
   - run_state: `release_executed`.
   - Phase-014 re-baseline: feature 102's no-`v1.5.0`-tag acceptance test and
     the spec's phase-scoped criterion go stale once the tag exists — the
     refresh re-baselines them (the E6b/E6c fact-notes record this in advance).

## 7. Planner's own scope guard

The planner wrote exactly: this plan
(`.agent/evidence/release-v1.5.0-prep/00-release-prep-plan.md`) and the capture
files `01-validate-sh.txt`, `02-fixtures-self-test.txt`,
`03-release-closeout-pr.txt`, `04-e2e-bootstrap.txt`,
`05-tag-probe-and-sanitization.txt`, `06-guide-anchors.txt` in the same
directory. No tracked file was edited; nothing was committed. The planner did
not touch `.nizam/` (H-0 is the Orchestrator's precondition), did not create or
probe-push any tag beyond the read-only probes captured in 05, and did not edit
`run_state.json`.

```
[STATE: Phase 014 (complete; release prep has no phase) | STEP: PLAN (revision 0) | DEPS: VERIFIED]
plan: .agent/evidence/release-v1.5.0-prep/00-release-prep-plan.md
tier: MINOR -> v1.5.0 (06_release_train.md §3.2, §3.4; per-feature contracts 099/103/104/106/107/109 MINOR, 105/108 PATCH)
generator_files: 7 (CHANGELOG.md, NIZAM.json, CONTEXT.md, README.md, docs/guide/index.html, docs/planning/ROADMAP.md, docs/planning/operator_gates.md)
evaluator_files: .agent/evidence/release-readiness-v1.5.0.md + release-v1.5.0-prep/01..06
sign-off: operator verbatim 2026-10-10 (H-FRAMEWORK-RELEASE Section 2); TAG AUTHORIZATION INCLUDED ("you are authorized to tag and pin the release") -- tag act still the separate post-merge Section 6 Orchestrator mechanic
self_check: 17/17 current-text blocks unique; close-out groups 5/5 PASS at V=1.5.0 (pr + tag semantics); fenced #5a/#5b/#7/#8/#9/#10/#10-control/#12/#13 run verbatim at HEAD (§5.1); scope_guard negative control 7/7 caught, positive 0
precondition: H-0 -- Orchestrator removes pre-existing untracked .nizam/ sandbox before the generator runs
next: @validator Mode A review
open_questions: none
```

## 8. Generator accuracy corrections (2026-10-10; proposal only)

Read tools/validate.sh lines 2153-2186 and 2576: C13 subset enforcement applies
to payload mode too. E1/E3/E6/E7 now describe that requirement without promising
unchanged validator behavior. The shipped manifest/index pair remains compliant.
The operator quote starts with "ensure the that"; the unsupported "great work."
prefix was removed. Section 4 #10 now checks added lines because ROADMAP contains
historical brand mentions, which must remain untouched. The old Section 5 simulation
is retained as historical evidence, not proof of the corrected proposal.
Contract metadata and QA/verdict artifacts are permitted by the formal contract
scope guard; the original §3 plan guard predates that metadata and is superseded
by the contract verification guard. No product file was edited for these corrections.

## 9. Current GA amendment — supersedes proposal text above (2026-10-10)

The operator subsequently stated verbatim: "GA is declared." The Orchestrator
recorded this decision BEFORE documentation at commit
`14e632fa04242aaf56eedc15eab377c03ba87511`, 2026-10-10T16:32:48Z. This is the
implementation diff base. The original Current blocks and historical phase dossier
remain unchanged. This amendment supersedes every proposal statement that H-GA
is outstanding or GA is undeclared; it does not rewrite the historical evidence.

- E1/E3: record operator-declared General Availability on 2026-10-10, H-GA
  EXECUTED, H-CONSOLIDATION still OUTSTANDING. State explicit evidence exceptions:
  `real_production_pilot` is `not_met`; `recorded_consumer_adoptions` is
  `insufficient_evidence`. Do not imply all GA prerequisites passed.
- E4: after the opening overview, add a concise GA declaration note dated
  2026-10-10 with a relative link to `docs/planning/operator_gates.md`. No numeric
  release-version string in that note: the seven existing version pins are retained.
- E5: inside the hero header after its tagline, add a concise GA declaration note
  dated 2026-10-10 linking `../planning/operator_gates.md`. Keep two numeric version
  anchors only; the note says General Availability without another version number.
- E6: update the first Current Position phase-014 bullet to distinguish feature
  102's historical no-declaration dossier from this current operator decision;
  record the final scope budget 8705 of 8600 (within 11180 ceiling). Update only
  this current phase bullet, proposed preparation bullet and top changelog entry;
  preserve long historical phase and released-tag records.
- E7: replace only the H-GA row's current Disposition clause with EXECUTED
  2026-10-10, operator verbatim "GA is declared.", the recorded decision time and
  commit `14e632f`, dossier `.agent/evidence/102/ga-readiness.json` SHA256
  `d98ccec0f3c57cda51876db3286b57005143ef771b88b4c92f36748de4c0f590`, and the two
  explicit exceptions above. Preserve its definition/scope, other gate rows and
  table cell count. H-FRAMEWORK-RELEASE append describes GA declared with these
  exceptions; tag authorization is satisfied, tag act awaits post-merge execution.
- E8: evaluator readiness report names this current decision and exceptions,
  references independently captured checks and preserves the frozen dossier digest.

Formal scope/verification authority: `.agent/contracts/release-v1.5.0.json`.
Contract remains proposed until both independent pre-code verdicts approve.
Only E1-E7 product paths and the contract-authorized release metadata/evidence
paths may change against the post-decision base. The contract's AT7 guard
supersedes the old Section 3 guard that did not anticipate contract metadata.
