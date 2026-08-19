---
id: nizam-product-spec-013
title: "Nizam Framework — Phase 013 Spec: Definition of Done (Tiers 0+1+2)"
description: "Phase-013 spec: name and consolidate the framework's scattered Definition of Done into one canonical standard, mechanize the feature-lifecycle invariant as validator check C16, ship a consumer-fillable DoD template and a merge-layer pull-request checklist, add optional advisory dod_ref keys to five schemas, add a release close-out gate that mechanizes internal version consistency, and prepare the v1.1.0 MINOR release. Activated 2026-08-18 via gate H-PHASE-013 — the 005 lesson holds: status tracked the decision lifecycle and flipped draft to active only on the recorded operator authorization."
tags: [spec, definition-of-done, enforcement, release-train, phase-013]
status: active
last_audited: "2026-08-18"
authoritative_source: NA
version: 1.1.2
spec_version: "1.1.2"
created_at: "2026-08-18T09:42:57Z"
updated_at: "2026-08-18T11:28:00Z"
change_log:
  - version: "1.1.2"
    date: "2026-08-18T11:28:00Z"
    summary: "PLAN AMENDMENT per methodology/00_planning.md Section 9 (factual correction of defective acceptance-test commands; design intent unchanged). Mode A validation of contract 093 refuted feature 093's acceptance_tests[2], which read NIZAM.json as `d['modules']['standard']['key_documents']`. NIZAM.json `modules` is a LIST of objects keyed by a `path` field, so that accessor raises `TypeError: list indices must be integers or slices, not str` and the test could never pass. Confirmed live before amending (AH-2). Corrected to `next(m for m in d['modules'] if m['path']=='standard')['key_documents']`, asserting BOTH the key_documents membership and the `nizam-definition-of-done` capability-id membership per the Mode A prescription. A sweep of every acceptance test of all seven features (092-098) found exactly one more instance of the same defect class: feature 095's acceptance_tests[1], corrected identically for the `templates` module and additionally asserting the flat top-level `d['templates']` array, which is a real array and carries the same eight entries as modules.templates.key_documents, so registration in NIZAM.json means both sites. No other accessor mismatches the real artifact shapes: 092's and 098's commands are shell/CLI or use the correct `feature_list['features']` list-of-dicts shape; 094's schema regex and 096's grep counts execute cleanly today; 097's `uses:` SHA-pin pattern and its `release.yml` step-name ordering assertion were both verified against the real .github/workflows/release.yml, where `Create or update the GitHub Release` exists at offset 6021 and the sole `uses:` line is 40-hex pinned. Working tests were not rewritten. `.agent/product_spec_013.md`'s Acceptance section repeats no NIZAM.json accessor and needed no change. `.agent/feature_list_013.json` spec_version moves to 1.1.2 in lockstep."
  - version: "1.1.1"
    date: "2026-08-18T10:05:00Z"
    summary: "PLAN AMENDMENT per methodology/00_planning.md Section 9 (factual correction, no scope change). Corrects the --payload summary baseline figure inherited from exploration: the baseline is 11 counted checks, not 12, so the one counted payload check added by C16 raises the summary to 12, not 13. Refuted during Mode A validation of contract 092 against tools/validate.sh:2383-2394, where exactly 11 `passed=$((passed + 1))` increments run in payload mode (C6 is an uncounted echo SKIP), and against captured evidence .agent/evidence/091/final-migration.txt:6 and .agent/evidence/090/migration-rehearsal.txt:6, both reading `SUMMARY (payload mode): 11 passed, 0 failed`, corroborated by the NDEBT-012 resolution note at docs/planning/DEBT.md:50. Two assertions corrected (Public contract changes; Acceptance). Design intent is unchanged: C16 still adds exactly one counted payload check. .agent/feature_list_013.json spec_version moves to 1.1.1 in lockstep with its 092 acceptance test."
  - version: "1.1.0"
    date: "2026-08-18T09:52:55Z"
    summary: "Phase 013 ACTIVATED on operator authorization (verbatim: 'approved. please proceed.', gate H-PHASE-013, 2026-08-18). Status draft -> active; spec_version 1.0.0 -> 1.1.0 (the activation-bump convention of phases 008-012); the activation is recorded in .agent/run_state.json (phase_activated) before any feature execution per NDEBT-018, current_phase advances 012-v1-consumer-safety -> 013-definition-of-done, and the scope budget resets to 2150. Execution begins with the ungated DAG root feature 092 (validator check C16)."
  - version: "1.0.0"
    date: "2026-08-18T09:42:57Z"
    summary: "Initial phase-013 proposal, authored at v1.0.0 (main 114fc8d) after the accepted 2026-08-18 analysis found the framework's done-criteria rigorous but unnamed and scattered across eight layers, the feature-lifecycle invariant mechanized by nothing, and the release/close-out surface empirically weakest. Scope is the operator's 2026-08-18 selection: Tiers 0+1+2 in one phase ending release-ready for v1.1.0 (MINOR), with the tag itself behind H-FRAMEWORK-RELEASE. Tier 3 (an ecosystem Verify protocol) is out of scope as NIP-class work. Features 092-098, DAG roots {092, 097}, original_estimate_lines 2150. No feature may enter contract negotiation before activation; current_phase remains 012-v1-consumer-safety (complete) and .agent/run_state.json is untouched until then."
---

# Phase 013 — Definition of Done

## Status and authority

**ACTIVE — operator authorized activation on 2026-08-18 (verbatim: `approved. please
proceed.`, gate `H-PHASE-013`).** This spec and the DAG-validated feature list
(`.agent/feature_list_013.json`) are Planner artifacts; the activation was recorded in
`.agent/run_state.json` (`phase_activated`) before any feature execution, per the
NDEBT-018 rule, and `docs/planning/manifest.json` now carries
`current_phase: 013-definition-of-done`. The v1.1.0 tag remains behind the separate
`H-FRAMEWORK-RELEASE` gate — the pipeline never self-tags.

The authority for this scope is the operator scope decision of **2026-08-18**, which
selected the Definition of Done Tiers 0, 1, and 2 in a single phase, ending
release-ready for **v1.1.0**. It rests on an accepted analysis taken against `main` at
`114fc8d` (tag `v1.0.0`): done-criteria exist at eight layers across `standard/`,
`methodology/`, `schema/`, and CI, but no canonical artifact names them; the lifecycle
invariant that a `complete` feature implies an approved contract, a passing QA verdict,
and evidence on disk is mechanized by nothing, while `schema/README.md` Section 4 claims
otherwise; and the release/close-out surface is the empirically weakest, having produced
four release-discipline failures and three close-out slips.

The remedy is consolidation, honest enforcement classification, and selective
mechanization — aggregate rather than restate, per `methodology/03_circuit_breaker.md`
Section 1. On activation, execution begins with the ungated DAG roots, feature `092`
(check C16) and feature `097` (the close-out gate).

## Scope

Phase 013 delivers seven features across three tiers:

1. **Tier 0 — mechanize the lifecycle invariant.** Validator check C16 asserts that
   every `.agent/feature_list*.json` validates against `schema/feature_list.schema.json`
   and that each `complete` feature which declares a contract also carries a QA verdict
   and on-disk evidence. The false enforcement claim in `schema/README.md` is corrected
   in the same feature.
2. **Tier 1 — name the standard.** A new canonical document, `standard/definition_of_done.md`,
   aggregates the layered model (Step, Handoff, Gate, Feature, Plan, Merge, Release,
   Ecosystem) by citing the existing authorities rather than restating their rules, and
   classifies each layer honestly as enforced or consumer-aspirational.
3. **Tier 2 — project the standard onto working surfaces.** Optional advisory `dod_ref`
   keys on five schemas, a copy-and-fill `templates/DoD.md` for consumers, a
   `.github/PULL_REQUEST_TEMPLATE.md` merge-layer checklist, and a release close-out gate
   that mechanizes internal version consistency in both pull-request and tag modes.
4. **Release preparation.** Feature `098` prepares the v1.1.0 MINOR package last, so a
   scope halt cannot strand release surfaces mid-bump.

The phase defines `complete` over the existing five-value enum in
`schema/feature_list.schema.json`. **No `done` state exists and none may be added**; the
negative fixture introduced by feature `092` mechanizes that rule.

## Public contract changes

- **New governed document** `standard/definition_of_done.md` (a deliverable of feature
  `093`; it does not exist on the current tree). It is additive and registered in
  `NIZAM.json` and `standard/README.md`.
- **New consumer template** `templates/DoD.md` (a deliverable of feature `095`),
  additive, registered in `NIZAM.json` and `templates/README.md`.
- **Optional-only schema keys.** `dod_ref` is added to the contract, QA-verdict (both
  `anyOf` branches), feature-list, work-packet, and engineering-finding schemas as an
  optional advisory string. No `required` array changes. Under
  `methodology/06_release_train.md` Section 3.1 a new *required* key would be BREAKING;
  a purely optional key is a loosening and therefore MINOR under Section 3.2. The
  phase/debt/capability-profile schemas are deliberately untouched.
- **New validator check C16**, skip-if-absent: a repository with no
  `.agent/feature_list*.json` passes trivially, so the check cannot break a consumer who
  does not use the artifact. The default summary moves from 15 to 16 checks and the
  payload summary from 11 to 12.
- **New framework-envelope surfaces** under `.github/` (a pull-request template, a
  close-out script, and a close-out workflow). These are release-publication machinery,
  not injected consumer payload, so they change no consumer contract.

Classified as **MINOR** overall: nothing that validated under v1.0.0 is invalidated.

## Safety and state model

C16 is **era-safe by construction**. Its lifecycle assertion is an if-present predicate
per artifact: the contract file is itself the declaration that a feature ran
contract-first, so features from eras before contract-first execution are not
retroactively judged, and no arbitrary cutoff date is encoded. Because Loop 1 writes the
contract before any code, the check still bites on every future feature. Re-verified
against the current tree before proposing: 12 lists, 92 features, 91 complete, 61 with a
contract, 0 violations — era-safe and non-vacuous.

C16 deliberately does not judge verdict polarity and deliberately does not validate the
evidence file *format* of `methodology/04_tool_driven_state.md` Section 5. Historical
evidence files use variant headers and would fail such a check; that residue is recorded
as aspirational in the new standard and named as a candidate C17.

State writes follow the canonical-first rule. `docs/planning/phase_013.yaml` is the
canonical structured lifecycle document, registered from `docs/planning/manifest.json`;
`.agent/run_state.json` is derived coordination state written idempotently afterwards.
No protocol claims a multi-file atomic write. Every timestamp is clock-read per
`methodology/04_tool_driven_state.md` Section 5.1.

The close-out gate is read-only with respect to git refs: it performs string comparison
against version anchors and never creates or pushes a tag. The pipeline never self-tags.

## Feature DAG

- **092** — validator check C16 plus the `schema/README.md` doc-truth fix. Root.
- **093** — `standard/definition_of_done.md` and its registration. Depends on 092.
- **094** — optional `dod_ref` keys on five schemas. Depends on 093.
- **095** — `templates/DoD.md` consumer template. Depends on 093.
- **096** — `.github/PULL_REQUEST_TEMPLATE.md` merge checklist. Depends on 093.
- **097** — release close-out gate (script, workflow, and the blocking release step). Root.
- **098** — v1.1.0 release preparation. Depends on 092–097.

The DAG is acyclic with two roots (`092` and `097`), which may proceed in parallel. The
topological execution order is: parallel group 1 `092` and `097`; then `093`; then
parallel group 3 `094`, `095`, and `096`; then sequentially `098`.
Feature `098` is deliberately last so that a scope-budget halt cannot leave version
anchors half-bumped. `original_estimate_lines` is 2150; the 130 percent cumulative
ceiling is 2795.

## Acceptance

Phase-level acceptance is the union of every feature's acceptance tests in
`.agent/feature_list_013.json` plus the following:

- `bash tools/validate.sh` reports `SUMMARY: 16 passed, 0 failed` with `[C16] PASS`.
- `bash tools/validate.sh --payload` reports 12 passed with an explicit C16 payload-skip PASS.
- `bash tools/fixtures_self_test.sh` exits 0, including the enumeration guards that prove
  the new document and template are registered.
- `bash tools/e2e_bootstrap_test.sh` exits 0 and the injected payload carries the new
  standard and template.
- `python3 .github/scripts/release_closeout.py --mode pr` exits 0 on the prepared tree.
- `git rev-parse -q --verify refs/tags/v1.1.0` returns non-zero: no v1.1.0 tag exists,
  because the tag is the operator's act alone.

## Out of scope

- **Tier 3 — an ecosystem Verify protocol.** This is NIP-class work requiring an
  accepted proposal; its future lifecycle number is 09, since 06 and 08 are reserved for
  planned documents asserted absent by contracts 035–037.
- **Schema changes to phase, debt, and capability-profile schemas.** These declare
  `additionalProperties: false` by DD-3 design and are left untouched.
- **An evidence-shape check.** Validating the Section 5 evidence format is recorded as a
  candidate C17, not built here.
- **The rolled-forward phase-012 candidate scope** — a real non-scratch multi-repo pilot
  and lifecycle stages 06 and 08 with `H-CONSOLIDATION` and `H-GA`. It is not cancelled;
  it rolls to phase 014, and the operator chooses the ordering at `H-PHASE-013`.

## Human gates

- `H-PHASE-013`: **OUTSTANDING** — the operator must authorize activation before any
  feature enters contract negotiation. The activation record is written to
  `.agent/run_state.json` before feature execution, per the NDEBT-018 rule.
- `H-FRAMEWORK-RELEASE`: **OUTSTANDING** — after feature `098`, the operator must
  approve the v1.1.0 version, changelog, and annotated tag, and push that tag. The
  pipeline records the readiness but never self-tags.
