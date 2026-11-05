---
id: nizam-definition-of-done
title: "Definition of Done"
description: "Defines the three enforced done-layers -- tests and CI green, a review verdict on the exact head, and live evidence for user-visible change -- plus Appendix A's supporting done-layers, each cited to its single-source authority rather than restated."
version: 0.5.0
status: active
enforcement: partially-enforced
authoritative_source: standard/definition_of_done.md
change_log:
  - version: "0.5.0"
    date: "2026-11-05"
    summary: "Operator directive 'governance simplification 2026-11-05 items 8, 9 and 10': compressed to three enforced layers (tests/CI green, review verdict on the exact head, live evidence) with the other layers moved to Appendix A; replaced the never-self-merge rule with recorded accountable-approver semantics (accountable approver plus an Authority-Ref trailer); made comparator acceptance conditional on a declared quality_bar; deleted the restated-not-redefined duplication."
  - version: "0.4.1"
    date: "2026-10-18"
    summary: "Clarify that check C16 (`vlib_feature_list_lifecycle`) is a deterministic structural check over `.agent/feature_list*.json`, `.agent/contracts/`, `.agent/qa/`, and referenced evidence files on disk (requiring contracts, passing QA verdicts, and non-empty evidence files for contemporary `passes: true` features while preserving legacy pre-contract-era exemptions)."
  - version: "0.4.0"
    date: "2026-10-13"
    summary: "Gate-Done (Section 5) and Feature-Done (Section 6) add comparator acceptance per `standard/acceptance_bars.md` (cost tier declared at dispatch; deterministic work exempt per its Section 1); the standard joins the References list (Section 13)."
  - version: "0.3.0"
    date: "2026-10-11"
    summary: "Extend Handoff-Done with reconstructible runtime-session continuity."
  - version: "0.2.0"
    date: "2026-10-09"
    summary: "Merge-Done (Section 8) and Enforcement (Section 11) now name four compliance.yml jobs: `convergent_review`, the convergent review suite in required-conformance mode, joins `validate`, `e2e_bootstrap` and `fixtures_self_test` (NDEBT-041)."
  - version: "0.1.0"
    date: "2026-08-18"
    summary: "Phase 013, feature 093: initial authoring of the layered Definition of Done, aggregating the framework's eight done-layers by citation and defining `complete` over the existing five-value feature-status enum."
---

# Definition of Done

> **Partially enforced.** The three enforced layers are Sections 2-4. The C16
> structural check (`tools/validate.sh` check C16, `vlib_feature_list_lifecycle`)
> verifies Feature-Done (Appendix A) file-and-status invariants over
> `.agent/feature_list*.json`, `.agent/contracts/`, `.agent/qa/`, and referenced
> evidence files on disk; it does not re-execute verification commands. Merge-Done
> (Section 2) is verified by the jobs `.github/workflows/compliance.yml` declares;
> Release-Done (Appendix A) by the release close-out gate defined by phase 013,
> feature 097. Appendix A's remaining layers are consumer-aspirational: a consuming
> repository enforces them in its own runtime.

## 1. Role

The framework recognises no single, monolithic completion state. This document
names the three enforced done-layers and the appendix's supporting layers, and
points to the authority that actually governs each. The mechanics live in the
cited sources.

## 2. Layer 1 — Tests and CI Green

A change is Tests-and-CI-Green only when every merge gate passes on the latest
relevant commit: the jobs `.github/workflows/compliance.yml` declares --
`validate` (checks C1 through C16), `e2e_bootstrap`, `fixtures_self_test`, and
`convergent_review` (the convergent review suite in required-conformance mode) --
covering the core merge gates of `standard/ci_gates.md` (capability-gated gates
apply only where that capability is declared). No single green job is
sufficient on its own; all MUST hold simultaneously.

## 3. Layer 2 — Review Verdict on the Exact Head

A change carries a review verdict on the exact head only when the convergent
review defined in `standard/convergent_code_review.md` has produced a verdict
bound to the exact current `head_sha` (stale-head input fails closed; a
superseded head is never published, per that standard's Section 2.3), and the
merge authority of Section 6 is satisfied.

## 4. Layer 3 — Live Evidence for User-Visible Change

A user-visible change is done only with evidence: evidence files in the fixed,
three-part shape per `methodology/04_tool_driven_state.md` Section 5 (exact
invocation, captured output, a literal `EXIT:<code>` marker) and, for deployed
behaviour, live evidence per `methodology/10_live_runtime_sessions.md`.

## 5. Appendix A: Supporting Layers

| Layer | One-Liner | Authority |
|---|---|---|
| Step-Done | A single agent action is complete only with captured, externalised evidence. | `standard/anti_hallucination.md` Section 4 (AH-3); evidence shape per `methodology/04_tool_driven_state.md` Section 3 |
| Handoff-Done | A role's output is durable only once written to its canonical file family, never carried in chat. | `standard/AGF.md` Section 5; artifact families per `methodology/04_tool_driven_state.md` Section 4; runtime-session continuity per `methodology/10_live_runtime_sessions.md` Section 8 |
| Gate-Done | A validator or evaluator gate advances only on a fully-satisfied JSON verdict. | `standard/AGF.md` Section 4 (JSON Verdict Parse Rule) |
| Feature-Done | A feature reaches `complete` only with an approved contract, a passing QA verdict, and evidence on disk. | Loop 2 of `methodology/01_execution.md` Section 3; the five-value enum of `schema/feature_list.schema.json`; adversarial spot-check per `methodology/02_adversarial_tdd.md` Sections 6-8; structurally verified by check C16 (`vlib_feature_list_lifecycle`) over `.agent/feature_list*.json`, `.agent/contracts/<id>.json`, `.agent/qa/<id>.json`, and non-empty `evidence_files` on disk (era-safe exemption only for legacy pre-contract-first entries lacking `passes`) |
| Plan-Done | A phase's features are planned only with atomic acceptance tests inside an enforced scope budget. | `methodology/00_planning.md` Section 4 (atomic acceptance tests) and Section 6 (Scope Budget Protocol) |
| Ecosystem-Done | A multi-repository engineering claim is closed only with path-referenced closure evidence, never absence alone. | `schema/engineering_finding.schema.json` conditional; `ecosystem/07_progress_comparison.md` Section 4 (Closure-Only-With-Evidence Rule); Verify stage per `ecosystem/README.md` |

Feature-Done note: `docs/planning/manifest.json` phase entries use a four-value
lifecycle, phase-YAML steps an uppercase five-value vocabulary, and
`.agent/run_state.json`'s `status` is a free string; these are observed shape
differences, not requirements.

## 6. Merge Authority

A merge requires (a) a recorded accountable approver and (b) an authority
reference recorded in the merge commit message: an `Authority-Ref:` trailer
naming the delegation record. Self-merge is permitted where delegated merge
authority exists and is referenced by the trailer. Activation gates and
other actors' pull requests remain human-only. `standard/ci_gates.md`
Section 2's `MERGE_READY` bar is the consumer-aspirational superset this
requirement instantiates.

## 7. Comparator Acceptance (quality_bar)

Where a task declares `quality_bar`, comparator acceptance per
`standard/acceptance_bars.md` applies; otherwise acceptance is the
specification plus tests.

## 8. Release-Done

A version is released only after `methodology/06_release_train.md` Section
2's four conditions hold in order: every intended change is merged to the
mainline branch, `CHANGELOG.md` carries an entry for the new version, a human
sign-off gate is satisfied, and only then is the tag created and pushed
through the human-gated release mechanic H-FRAMEWORK-RELEASE. Release-Done
for this framework's own repository additionally requires the release
close-out gate defined by phase 013, feature 097.

## 9. A Floor, Not a Guarantee

Every layer above is a process floor: a structural, mechanically-checkable
claim about approvals, evidence, and gates having actually run in the
correct order. None of them is a claim that the resulting system is
correct, safe, or fit for purpose. The 2026-07-18 stack collapse and the
issue #52 consumer-safety findings that followed it both passed every
mechanical gate this document names that existed at the time -- contracts
were approved, QA verdicts passed, evidence was captured -- and the
underlying defects were still real. A checklist that is fully satisfied
proves the checklist was followed; it does not prove the work is correct.

This document's layered model therefore bounds process completeness. It
never substitutes for, and must never be read as substituting for, human
judgment, adversarial review, or the semantic correctness of what was
actually built. A feature can be `complete` by every layer above and still
be wrong.

## 10. References

- `standard/anti_hallucination.md`
- `methodology/04_tool_driven_state.md`
- `standard/AGF.md`
- `standard/acceptance_bars.md`
- `methodology/01_execution.md`
- `methodology/02_adversarial_tdd.md`
- `schema/feature_list.schema.json`
- `methodology/00_planning.md`
- `.github/workflows/compliance.yml`
- `standard/ci_gates.md`
- `methodology/06_release_train.md`
- `ecosystem/README.md`
- `schema/engineering_finding.schema.json`
- `ecosystem/07_progress_comparison.md`
- `standard/capability_profiles.md`
- `methodology/10_live_runtime_sessions.md`
- `standard/convergent_code_review.md`
- `tools/validate.sh`
