---
id: nizam-product-spec-003
title: "Nizam Framework — Phase 003 Spec (Communication & User Guide)"
description: "Phase-003 specification: remediates a human-directed documentation-clarity audit (H1-H9) of the framework's first-contact surfaces by shipping a self-contained HTML user guide, correcting stale/incorrect adoption-contract documentation, expanding first-contact jargon, and adding a LICENSE. Extends product_spec.md and product_spec_002.md; replaces neither."
tags: [spec, governance, communication, user-guide, documentation, phase-003]
status: draft
last_audited: "2026-07-08"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-08T05:05:03Z"
updated_at: "2026-07-08T05:05:03Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-08T05:05:03Z"
    summary: "Initial phase-003 spec (communication & user guide). PROPOSED — awaiting human authorization."
---

# Nizam Framework — Phase 003 Spec (Communication & User Guide)

**Status: PROPOSED — awaiting human authorization.** This spec plans phase
`003-communication`. It does **not** change `run_state.json`, and the manifest carries
phase 003 as non-active (`status: pending`, `activation_state: proposed`) until a human
authorizes activation — the identical lifecycle pattern used for phase 002. It extends
`.agent/product_spec.md` (spec v1.1.0) and `.agent/product_spec_002.md`; it supersedes
neither.

## 1. Motivation — The Communication Gap

Phases 001–002 shipped a correct, self-enforcing framework whose *machine legibility* is
strong (a cold-read agent rated it 7.5/10) but whose *human legibility at first contact* is
weak (rated 6/10). A capable adopter — human or agent — landing on the repository today hits
stale pointers, a command-free README, a functional discovery bug in the adoption contract,
and no worked walkthrough. The framework tells consumers to keep their documentation honest
and current (`standard/NDS.md`) while its own entry surfaces have drifted. Phase 003 closes
that gap: it makes the framework *explain itself* — truthfully, current, and with a
single shipped presentation surface (an HTML user guide) as the human centerpiece — without
adding a line of new runtime behavior.

Every remediation below is a **documentation-truth** change sourced *from* the shipped tree
(the External Anchor Rule, `methodology/02_adversarial_tdd.md`): no claim in any new surface
may describe behavior the code does not actually have.

## 2. Findings Ledger (remediation targets)

Every claim was verified against the working tree by the orchestrator and an independent
cold-read agent.

| ID | Finding | Evidence (verified) | Remediated by |
|----|---------|---------------------|---------------|
| H1 | `CONTEXT.md` (the agent entry point) is STALE: says `NIZAM.json` "ships in feature 006… until then consult module READMEs" and `bootstrap.sh` "(ships in feature 007)" — both shipped; omits all phase-002 surfaces (`tools/validate.sh`, CI, `docs/architecture/`); describes bootstrap as injecting 3 dirs (actual: 4 + `NIZAM.json`); frontmatter `status: draft` (NDS Sec 3 → formally non-binding), `version: 0.1.0`. | `CONTEXT.md` lines 33–41, 5–7 | F-020 |
| H2 | `README.md` has zero commands: no copy-pasteable pinned-tag quickstart, no human-vs-agent entry split, no pointer to `tools/SKILL.md`, no mention of validator/CI/ADRs; "Design Decisions" written in framework-author voice, not adopter voice. | `README.md` (whole file, 39 lines) | F-020 |
| H3 | NO `LICENSE` file — a hard adoption blocker. The license CHOICE is a human gate. | `find . -name LICENSE` → absent | F-021 (human gate) |
| H4 | FUNCTIONAL adoption-contract bug: `tools/interface.md` Sec 2.1 tells runtimes to discover `tools/skill.json` at the **consumer repo root**, but `bootstrap.sh` installs the payload under `.nizam/`. Discovery as written misses every bootstrapped consumer. | `tools/interface.md` Sec 2 item 1 vs `bootstrap.sh` `DEFAULT_TARGET_DIR=".nizam"` | F-019 |
| H5 | Payload-set doc/code drift: `standard/GIP.md` (Sec 2 item 2 and Sec 2.1 item 2) says inject `standard/`,`templates/`,`schema/` (3 dirs); `bootstrap.sh` + `CHANGELOG.md` say 4 dirs (incl. `tools/`) + `NIZAM.json`. | `GIP.md` lines 33–35, 52–54 vs `bootstrap.sh` `REQUIRED_MODULE_DIRS` + `NIZAM.json` | F-019 |
| H6 | Shipped docs leak pipeline-internal state: `templates/README.md` and `methodology/README.md` reference `.agent/product_spec.md` / `product_spec` sections a fresh consumer will not have; `docs/` (ADRs, planning) is unindexed by `NIZAM.json` and its shipped-vs-internal status is undeclared. | `templates/README.md` line 14; `methodology/README.md` lines 30, 37 | F-019 (de-leak), F-017 (declare status), F-018 (index) |
| H7 | Jargon at first contact: NDS/AGF/GIP used before expansion outside `standard/`; "AGIP" (in `CHANGELOG.md` + `bootstrap.sh` header) never expanded anywhere. | `bootstrap.sh` lines 6, `CHANGELOG.md` line 61 | F-020 (README/CONTEXT/bootstrap), F-022 (CHANGELOG) |
| H8 | No adoption guidance for EXISTING repos: no conflict handling with pre-existing `CONTEXT`/`AGENTS`/CI, no incremental tiers (docs-standard-only → +templates → full loop). | `GIP.md` (no such section) | F-019 |
| H9 | No quickstart, no worked example of a governed consumer repo, no FAQ, no post-bootstrap "first governed task" walkthrough. | repo-wide absence | F-018 (guide), F-020 (README quickstart) |

Cold-read ratings at audit time: humans 6/10, agents 7.5/10. The phase target is to raise
the human rating without regressing the agent rating (the guide and truth fixes add human
legibility; the truth fixes *also* de-risk the agent path H1/H4).

## 3. Layout Amendment (specified here, recorded by F-017)

Phase 003 introduces one new shipped presentation surface and formalizes the status of the
`docs/` tree. F-017 amends `product_spec.md` Sec 2.1 (MINOR / additive → `product_spec.md`
`spec_version` 1.1.0 → 1.2.0, with a `change_log` entry per NDS Sec 4) to record it:

```text
nizam-framework/
├── docs/
│   ├── architecture/   # ADRs — shipped documentation (ADR-001, ADR-002, …)
│   ├── guide/
│   │   └── index.html  # Self-contained HTML user guide (NEW — the phase centerpiece)
│   └── planning/       # manifest.json, DEBT.md — framework-internal (NOT shipped to consumers)
```

`docs/` **shipped-vs-internal status** (declared by F-017, resolving H6):

- `docs/architecture/` and `docs/guide/` are **shipped documentation**: they are part of the
  framework's public distribution (renderable on GitHub Pages or locally) and are indexed by
  `NIZAM.json`. They are **not** part of the consumer-*injected* payload — `bootstrap.sh`
  injects only `standard/`, `templates/`, `schema/`, `tools/`, and `NIZAM.json` into a
  consumer's `.nizam/` (see H5). "Shipped" means "distributed with the framework repo," not
  "copied into every consumer."
- `docs/planning/` (`manifest.json`, `DEBT.md`) is **framework-internal** governance state,
  not shipped documentation, and is not indexed.

The layout amendment is F-017's deliverable; this section only specifies its shape so F-017
can be verified against it.

## 4. The HTML User Guide (`docs/guide/index.html`) — Design Contract (F-018)

The guide is the phase centerpiece and its largest feature. It is a **single, fully
self-contained HTML file**: inline CSS and JS, **zero external network requests**, system
font stack, `prefers-color-scheme` light/dark, semantic HTML, WCAG-AA contrast,
print-friendly, with a sticky in-page table of contents. Every factual claim in the guide is
**sourced from the shipped docs** (External Anchor Rule) — the guide invents no behavior.

### 4.1 The Version Consistency Anchor

HTML is exempt from the NDS Markdown-frontmatter contract, so the compliance validator's
`.md` sweeps (C1/C3) do not cover the guide. To keep the guide from silently drifting, it
carries the framework version in a **machine-findable** form that MUST equal
`NIZAM.json` `framework.version`:

- A `<meta name="framework-version" content="VERSION">` element in `<head>`, AND
- the same `VERSION` rendered in the footer.

This equality is an enforceable acceptance test (parse `NIZAM.json` `framework.version`;
assert the exact string appears in the guide). Because the check is **relative** to
`NIZAM.json`, it holds regardless of the absolute version at implementation time (the phase
does not bump `NIZAM.json` `framework.version` — the release version bump is the human gate
in F-022, mirroring phase 002, which left `NIZAM.json` at its pre-release version).

### 4.2 Required Content Sections (source every claim from the shipped tree)

1. **Hero** — one-sentence "what it is" + two persona CTAs ("Humans start here" /
   "Agents load `tools/SKILL.md` via `NIZAM.json`").
2. **Problem → Solution** — the four remediated flaws rendered as four cards mapping to
   `DD-1`…`DD-4` (source: `.agent/product_spec.md` Sec 4 and `README.md` Design Decisions).
3. **Quickstart** — the pinned-tag `bootstrap.sh` one-liner (a real tag), the resulting
   `.nizam/` tree, and the `--verify-only` drift check (source: `bootstrap.sh` usage +
   `standard/GIP.md`).
4. **Adoption paths** — a new-repo walkthrough AND the existing-repo incremental tiers
   (source: `standard/GIP.md`, including the new section F-019 adds).
5. **The execution loop** — a visual diagram planner → contract → Mode A → evaluator review
   → implement → Mode B → QA, with the 3-strike circuit breaker annotated (source:
   `standard/AGF.md`, `methodology/01_execution.md`, `methodology/03_circuit_breaker.md`,
   `tools/SKILL.md` Sec 3).
6. **Anatomy of a governed repo** — an annotated file tree including the `.agent/` artifact
   families and their lifecycle (source: `methodology/04_tool_driven_state.md`,
   `tools/skill.json` `state_interface`).
7. **Module reference cards** — one card per module (`standard/`, `methodology/`,
   `registry/`, `templates/`, `schema/`, `tools/`), each linking to real repo paths (source:
   `NIZAM.json` `modules`).
8. **Agent integration** — `skill.json` discovery (post-H4 order), the three abstract
   operations (read-state / write-evidence / run-verification), and a conformance-checklist
   digest (source: `tools/interface.md`).
9. **FAQ** — including what Nizam is NOT, versioning/pinning, drift detection, and license
   (source: `.agent/product_spec.md` Sec 1, `standard/GIP.md` Sec 4, F-021's LICENSE).
10. **Footer** — the framework version (MUST equal `NIZAM.json` `framework.version`) and
    canonical links (`github.com/niq-cnr/...`).

Acronyms (NDS, AGF, GIP, AGIP) are expanded on first use in the guide.

### 4.3 Guide Acceptance (objective, command-verifiable)

- Valid HTML: `python3` `html.parser` feeds the file without raising.
- Self-contained: no `<link rel="stylesheet">` and no `<script src=...>`.
- Zero external URLs in `src`/`href` other than `github.com` / `niq-cnr` links.
- Dark/light: a `prefers-color-scheme` media query is present.
- Sticky in-page TOC present (`<nav>` + `position: sticky`).
- Embedded `framework-version` (meta + footer) equals `NIZAM.json` `framework.version`
  (parsed check).
- Every repository-relative path the guide names resolves on disk.
- No `nizamiq` string anywhere in the file (the guide is out of `validate.sh` C5's sweep, so
  this is an explicit per-feature acceptance test).

## 5. Remediation Design (per feature)

### F-017 — ADR-002 (HTML user guide) + `product_spec.md` Sec 2.1 amendment + `docs/` status
Dogfood `templates/ADR_TEMPLATE.md` → `docs/architecture/ADR-002-html-user-guide.md`.
Decision recorded: adopt a shipped, dependency-free single-file HTML user guide at
`docs/guide/index.html` as a presentation surface (rationale: single-file, zero-dependency,
GitHub-Pages- or locally-renderable; HTML is exempt from NDS md-frontmatter, so the
embedded-version-equals-`NIZAM.json`-`framework.version` anchor of Sec 4.1 is its enforceable
consistency contract). Amend `product_spec.md` Sec 2.1 to admit `docs/guide/` and declare the
`docs/` shipped-vs-internal status of Sec 3 (bump `product_spec.md` `spec_version`
1.1.0 → 1.2.0, MINOR/additive, with a `change_log` entry per NDS Sec 4). **Decision + layout
of record only** — no guide HTML and no `NIZAM.json` index change here (mirrors F-011).
`NIZAM.json` indexing is deferred to F-018 because validator C4 requires every indexed path
to resolve on disk, and `docs/guide/index.html` does not exist until F-018.

### F-018 — The HTML user guide + `NIZAM.json` indexing
Author `docs/guide/index.html` to the full design contract of Sec 4. Then index the now-real
`docs/` documentation in `NIZAM.json`: add a `docs` module (or capability entries) pointing
at `docs/architecture/ADR-001-*.md`, `docs/architecture/ADR-002-*.md`, and
`docs/guide/index.html`, keeping `NIZAM.json` schema-valid against
`registry/nizam-index.schema.json` with every indexed path resolving (validator C4). This is
the phase's largest feature.

### F-019 — Adoption-contract correctness (interface discovery, payload set, de-leak, existing-repo tier)
- **H4:** Fix `tools/interface.md` Sec 2 discovery order to `.nizam/tools/skill.json` first
  (the actual bootstrap layout), then a repository-root `tools/skill.json` fallback (for a
  framework checkout itself), then pinned-checkout resolution — reconciled with
  `bootstrap.sh`'s `.nizam/` default.
- **H5:** Correct `standard/GIP.md` Sec 2 item 2 and Sec 2.1 item 2 injection lists to name
  `standard/`, `templates/`, `schema/`, `tools/`, **and** `NIZAM.json` (4 dirs + index),
  matching `bootstrap.sh` `REQUIRED_MODULE_DIRS`.
- **H6 (de-leak):** Rephrase `templates/README.md` and `methodology/README.md` to remove
  every `.agent/product_spec.md` / `product_spec` reference a fresh consumer would not have,
  pointing instead to framework-relative concepts (`standard/NDS.md`, the README/guide DD
  cards).
- **H8:** Add an "Adopting in an Existing Repository" section to `standard/GIP.md`: conflict
  rules for pre-existing `CONTEXT`/`AGENTS`/CI, and the incremental tiers (docs-standard-only
  → +templates → full loop).
Every edited `.md` here is in the validator's shipped-doc set, so each `version` bump carries
a `change_log` entry or a root `CHANGELOG.md` line (NDS Sec 4 / validator C8), and
`tools/validate.sh` stays green.

### F-020 — First-contact truth fixes (`CONTEXT.md` + `README.md` + acronyms)
- **H1:** Rewrite `CONTEXT.md` current: remove the stale "ships in feature 006/007" claims;
  add the phase-002 surfaces (`tools/validate.sh`, `.github/workflows/compliance.yml`,
  `docs/architecture/`); correct the payload description to 4 dirs + `NIZAM.json`; set the
  agent path to `NIZAM.json` → `tools/SKILL.md`; flip frontmatter `status: draft` → `active`
  and bump `version`.
- **H2/H9:** Give `README.md` a Quickstart (obtain `bootstrap.sh` via the pinned raw URL or a
  framework clone; one copy-pasteable command with a real tag; a "what you get" `.nizam/`
  tree), a two-audience entry split ("Humans start here" / "Agents load `tools/SKILL.md` via
  `NIZAM.json`"), a link to the HTML guide + the GitHub Release, and a mention of the
  validator/CI/ADRs.
- **H7:** Expand NDS/AGF/GIP at first use in `README.md`/`CONTEXT.md`, and expand "AGIP" at
  its first mention in `bootstrap.sh`'s header comment.
`CONTEXT.md` is in the validator's shipped-doc set (C1/C2/C3/C8); its `version` bump carries a
`CHANGELOG.md` line so `tools/validate.sh` stays green. `README.md` is outside the frontmatter
set but inside C5's branding sweep — its rewrite introduces no `nizamiq`/endpoint strings.
Depends on F-018 because README/CONTEXT link to `docs/guide/index.html` and the ADRs, and
"every named repo-relative path resolves" requires those files to exist.

### F-021 — LICENSE (human gate)
Add a top-level `LICENSE` file and a one-line license notice in `README.md`. The license
**choice** is a human gate: the recommendation is **MIT**, matching the source repositories'
lineage. **Structured so the phase can complete with this feature explicitly
`blocked` (blocked-on-human) if the choice is undecided** — F-021 is deliberately NOT a
dependency of the phase-close feature (F-022), so phase close is not held hostage to the
license decision. Depends on F-020 so its README license line lands after the README rewrite.

### F-022 — Phase close (CHANGELOG, green validator, publishing + release human gates)
Add `CHANGELOG.md [Unreleased]` entries for the phase-003 deliverables (HTML user guide,
`CONTEXT`/`README` rewrites, interface/GIP adoption-contract corrections, `docs/` indexing,
and LICENSE if landed); expand "AGIP" at its `CHANGELOG.md` mention (H7). Confirm
`tools/validate.sh` exits 0 on the final tree (C5's branding sweep covers `README.md`; the
guide is HTML and therefore outside C1/C3, so the guide's `nizamiq`-absence check lives in
F-018's acceptance, not the validator). Record two human gates, executing neither: (1) the
**publishing decision** — enabling GitHub Pages for `docs/guide/` — and (2) the **release
decision** — `v0.3.0`, **MINOR** per `methodology/05_release_train.md` (new user guide +
additive documentation; the interface.md discovery correction is a documentation fix — the
actual `.nizam/` bootstrap layout is unchanged — so it is not a breaking runtime change). The
pipeline does NOT cut the tag or enable Pages. Depends on F-018, F-019, F-020.

## 6. Acceptance Criteria (phase-level)

1. `docs/architecture/ADR-002-*.md` exists, is instantiated from `templates/ADR_TEMPLATE.md`
   with no unreplaced `{{` tokens and a valid ADR `Status:` line; `product_spec.md`
   `spec_version` is `1.2.0` with a matching `change_log` entry and Sec 2.1 naming
   `docs/guide/`.
2. `docs/guide/index.html` satisfies every objective check in Sec 4.3 (valid HTML,
   self-contained, no external URLs beyond github.com/niq-cnr, dark/light, sticky TOC,
   embedded version == `NIZAM.json` `framework.version`, all named paths resolve, no
   `nizamiq`).
3. `NIZAM.json` indexes `docs/architecture/` (both ADRs) and `docs/guide/index.html`, still
   validates against `registry/nizam-index.schema.json`, and every indexed path resolves
   (validator C4 green).
4. `tools/interface.md` discovery names `.nizam/tools/skill.json` first with a repo-root
   fallback; `standard/GIP.md` injection lists name `tools/` and `NIZAM.json`; neither
   `templates/README.md` nor `methodology/README.md` contains a `product_spec` reference;
   `standard/GIP.md` carries an existing-repo adoption section with the three incremental
   tiers.
5. `CONTEXT.md` is current (no "ships in feature 006/007"; names `tools/validate.sh`, CI, and
   `docs/architecture/`; describes the 4-dir + `NIZAM.json` payload; `status: active`) and
   `README.md` carries a copy-pasteable pinned-tag quickstart, a two-audience split, and a
   link to the guide.
6. A `LICENSE` file exists (or F-021 is explicitly `blocked` on the human license choice,
   which does NOT block phase close).
7. `CHANGELOG.md [Unreleased]` names the phase-003 deliverables; `tools/validate.sh` exits 0
   on the final tree; no `v0.3.0` tag is auto-cut and GitHub Pages is not auto-enabled (both
   recorded as human gates).
8. No edit touches any immutable artifact (completed `.agent/contracts/*.json`,
   `.agent/evidence/*`, `.agent/qa/*.json`, or any phase-001/002 feature list).

## 7. Constraints

- Immutable artifacts are off-limits: completed contracts, evidence, and QA verdicts from
  prior phases are audit records and MUST NOT be edited.
- Every new/edited JSON artifact validates against its schema under `schema/` (and `NIZAM.json`
  against `registry/nizam-index.schema.json`).
- 6 features, atomic command-verifiable acceptance tests, a clean acyclic dependency DAG,
  per-feature and total line estimates, evidence per `methodology/04_tool_driven_state.md`
  Sec 5.
- The guide invents no behavior: every factual claim is sourced from the shipped tree
  (External Anchor Rule).

## 8. Execution Order (topological)

```text
Parallel Group 1: F-017 (ADR-002 + spec §2.1 + docs/ status — no dependencies)
                  F-019 (adoption-contract correctness — no dependencies)
Parallel Group 2: F-018 (HTML user guide + NIZAM.json indexing — depends on F-017)
Parallel Group 3: F-020 (CONTEXT/README truth fixes + acronyms — depends on F-018)
Parallel Group 4: F-021 (LICENSE, human-gated, may end 'blocked' — depends on F-020)
                  F-022 (phase close + publishing/release human gates — depends on F-018, F-019, F-020)
```

Dependency graph validated: all dependency targets exist, no cycles, a topological ordering
exists. F-021 and F-022 are mutually independent (both depend only on F-020 / earlier), so
phase close (F-022) may complete while the LICENSE feature (F-021) waits `blocked` on the
human license choice — the intended "phase completes with LICENSE blocked-on-human" behavior.

## 9. Feature ↔ Finding Traceability

| Feature | Remediates |
|---------|-----------|
| F-017 | H6 (declare `docs/` status), layout of record for the guide |
| F-018 | H9 (worked guide/quickstart/FAQ), H6 (index `docs/`) |
| F-019 | H4 (discovery bug), H5 (payload-set drift), H6 (de-leak), H8 (existing-repo tiers) |
| F-020 | H1 (stale CONTEXT), H2 (command-free README), H7 (acronyms), H9 (README quickstart) |
| F-021 | H3 (no LICENSE — human gate) |
| F-022 | phase close: green validator, H7 (CHANGELOG AGIP), publishing + release human gates |
