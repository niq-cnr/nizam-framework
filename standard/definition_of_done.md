---
id: nizam-definition-of-done
title: "Definition of Done"
description: "Aggregates the framework's eight done-layers -- Step, Handoff, Gate, Feature, Plan, Merge, Release, and Ecosystem -- by citing each layer's existing authority rather than restating its mechanics."
version: 0.1.0
status: active
enforcement: partially-enforced
authoritative_source: standard/definition_of_done.md
change_log:
  - version: "0.1.0"
    date: "2026-08-18"
    summary: "Phase 013, feature 093: initial authoring of the layered Definition of Done, aggregating the framework's eight done-layers by citation and defining `complete` over the existing five-value feature-status enum."
---

# Definition of Done

> **Partially enforced.** This document's Feature-Done layer (Section 6) --
> the complete-implies-contract-plus-QA-plus-evidence invariant -- is
> verified by `tools/validate.sh` check C16 when a checkout runs it. This
> document's Merge-Done and Release-Done layers (Sections 8-9) are verified
> by the release close-out gate defined by phase 013, feature 097. Every
> other named layer -- Step, Handoff, Gate, Plan, and Ecosystem -- is
> consumer-aspirational: a consuming repository enforces it in its own
> runtime, mirroring the same aspirational/enforced split already recorded
> by `standard/capability_profiles.md` and `standard/ci_gates.md`'s own
> banners. This document does not claim C16 verifies anything beyond the
> Feature-Done layer.

## 1. Role and Authority

This document defines no completion mechanics of its own. Each layer named
below is restated here only as a pointer to its existing, single-source
authority -- never redefined -- mirroring `methodology/01_execution.md`
Section 4's own governing sentence: "this is restated here, not redefined."
Where this document quotes another authority's exact wording, that wording
remains that authority's, restated, not redefined, here.

The framework recognises no single, monolithic completion state. Completion
is a layered claim: a unit of work can satisfy one layer's authority while a
higher layer's authority remains unsatisfied, and this document's sole
purpose is to name each layer, point to the authority that actually governs
it, and record which layers this framework's own tooling currently
mechanizes. A reader who wants to know how any one layer's mechanics
actually work MUST follow this document's citation to that layer's
authoritative source; this document is a map of the territory, not the
territory itself.

## 2. The Layered Model

| Layer | One-Liner | Authority |
|---|---|---|
| Step-Done | A single agent action is complete only with captured, externalised evidence. | Section 3 |
| Handoff-Done | A role's output is durable only once written to its canonical file family, never carried in chat. | Section 4 |
| Gate-Done | A validator or evaluator gate advances only on a fully-satisfied JSON verdict. | Section 5 |
| Feature-Done | A feature reaches `complete` only with an approved contract, a passing QA verdict, and evidence on disk. | Section 6 |
| Plan-Done | A phase's features are planned only with atomic acceptance tests inside an enforced scope budget. | Section 7 |
| Merge-Done | A change is mergeable only when every CI job and the human-review gate pass together. | Section 8 |
| Release-Done | A version is released only after changelog roll-up, human sign-off, and a tag cut at the signed-off commit. | Section 9 |
| Ecosystem-Done | A multi-repository engineering claim is closed only with path-referenced closure evidence, never absence alone. | Section 10 |

## 3. Step-Done

A single agent action -- a file edit, a verification command, a captured
result -- is complete only when it satisfies AH-3, evidence-anchored
completion, defined in `standard/anti_hallucination.md` Section 4: an agent
may mark a step complete only after capturing command output or a file diff
that confirms the change, externalised outside the conversation. That
document's Section 7 directive that automated checks SHOULD verify
completed steps carry evidence is the framework's own mandate for exactly
what check C16 mechanizes at the feature-list level (Section 6 below).

Where that evidence lives, and its required shape, is DD-3, evidence
externalisation, defined in `methodology/04_tool_driven_state.md` Section 3:
one evidence file per verification unit, referenced by path, never pasted
inline. That document's Section 5 defines the fixed, three-part evidence
file shape -- exact invocation, captured output, a literal `EXIT:<code>`
marker -- every Step-Done claim in this framework ultimately rests on.

## 4. Handoff-Done

A role's output is durable, and therefore ready to hand off to the next
role in the pipeline, only once it exists in its canonical file family --
never as a claim carried in chat history. `standard/AGF.md` Section 5, the
Durable State Rule, is the single source of truth for this requirement:
chat is not state, and a later role MUST NOT act on a result it cannot
independently read from durable state.

`methodology/04_tool_driven_state.md` Section 4 names the concrete artifact
families -- run state, feature list, contracts, QA verdicts, evidence -- a
handoff between the Orchestrator, Planner, Generator, Validator, and
Evaluator roles must have populated before that role's turn is considered
complete.

## 5. Gate-Done

A validator or evaluator gate advances the pipeline only when its JSON
verdict satisfies all four conditions of the JSON Verdict Parse Rule,
defined in `standard/AGF.md` Section 4: `final_verdict.approved` is `true`,
and `issues`, `missing_acceptance_coverage`, and `unsupported_claims` are
each empty. Prose framing -- "mostly approved," "should be fine" -- never
substitutes for a satisfied JSON block; a single non-empty entry in any of
the three arrays blocks advancement regardless of `approved`'s value.

## 6. Feature-Done

A feature is `complete` over the five-value lifecycle enum
`schema/feature_list.schema.json` declares: `pending`, `in_progress`,
`complete`, `blocked`, and `cancelled`. A feature reaches `complete` only
when Loop 2 of `methodology/01_execution.md` Section 3 has been satisfied in
full -- an approved implementation, a passing independently-re-derived QA
verdict, and a passing evidence-capture gate confirming every referenced
`.agent/evidence/` path actually exists -- and that same document's Section
6 hands control back to the Dependency Enforcement Rule only once all three
hold together. No sixth terminal state exists in this enum, and this
document proposes none: no `done` state exists and none may be added.

The Evaluator role's independent re-derivation of that verdict is bound by
`methodology/02_adversarial_tdd.md` Section 6 (the mandatory adversarial
spot-check), Section 7 (the External Anchor Rule -- an expected value MUST
be drawn from a source outside the artifact under test), and Section 8 (the
mandatory adversarial evidence file every such spot-check requires).

Other framework surfaces track related but distinct lifecycle vocabularies,
observed here as a mapping, not re-legislated: `docs/planning/manifest.json`
phase entries use a four-value lifecycle (`pending`, `in_progress`,
`complete`, `blocked`, with no `cancelled` counterpart at the phase level);
individual phase-YAML steps use an uppercase five-value vocabulary
(`PENDING`, `IN_PROGRESS`, `AWAITING_IMPLEMENTATION`, `COMPLETED`,
`BLOCKED`); and `.agent/run_state.json`'s own `status` field is an
unconstrained free string. This document describes that observed shape
difference; it does not require any of the three to converge on the
feature-list enum's five values or wording.

## 7. Plan-Done

Every planned feature's acceptance coverage must be atomic before the
feature is Plan-Done: `methodology/00_planning.md` Section 4 requires each
`acceptance_tests` entry to be a concrete, independently runnable command
verifying exactly one fact, never a vague prose goal a later Validator or
Evaluator gate would have to interpret rather than execute.

That document's Section 6, the Scope Budget Protocol, is the layer's second
governing mechanic: a per-feature rolling-average check and a phase-level
130%-of-`original_estimate_lines` cumulative ceiling that every subsequent
implementation is measured against once work begins, so Plan-Done also
bounds how far actual implementation may drift from what was planned
before a human must re-authorize the plan.

## 8. Merge-Done

A change is mergeable only when every job `.github/workflows/compliance.yml`
declares -- `validate` (checks C1 through C16), `e2e_bootstrap`, and
`fixtures_self_test` -- passes on the latest relevant commit, together with
human review and this framework's own never-self-merge rule. No single
green job is sufficient on its own; all three, plus a human reviewer's
approval, MUST hold simultaneously before a pull request lands.

`standard/ci_gates.md` Section 2's `MERGE_READY` formula is the
consumer-aspirational superset this layer generalises to: this framework's
own three-job workflow mechanizes one concrete instantiation of that
formula's `CI_GREEN` and `HUMAN_APPROVED` factors; a consuming repository's
own CI enforces the formula's remaining factors in its own runtime.

## 9. Release-Done

A version is released only after `methodology/06_release_train.md` Section
2's four conditions hold in order: every intended change is merged to the
mainline branch, `CHANGELOG.md` carries an entry for the new version, a
human sign-off gate is satisfied, and only then is the tag created and
pushed. That document's Section 6 divides the layer further: changelog
roll-up, the release date, and version anchors are durable preparation that
MUST pass the ordinary contract/validator/evaluator loops like any other
feature; only the final tag act belongs to the human-gated release
mechanic H-FRAMEWORK-RELEASE, and creates no tracked file diff of its own.

Release-Done for this framework's own repository additionally requires the
release close-out gate defined by phase 013, feature 097, once that
feature lands -- Merge-Done and Release-Done together are the two layers
this document's own banner names as verified by that gate.

## 10. Ecosystem-Done

A multi-repository engineering claim reaches its own Verify stage --
`ecosystem/README.md`'s canonical lifecycle names it the step that confirms
the executed work actually satisfies its contracts and closes the findings
it claimed to close -- only with path-referenced closure evidence, never
the mere absence of a finding from a later scan.
`schema/engineering_finding.schema.json` mechanizes this precisely: every
finding requires non-empty `closure_criteria` regardless of status, while
`closure_evidence` is required and non-empty only when a finding's `status`
is `resolved`, enforced by the schema's own conditional -- never for a
finding recorded `open`.

`ecosystem/07_progress_comparison.md` Section 4, the Closure-Only-With-
Evidence Rule, is the comparison-time restatement of the same discipline: a
finding is classified `resolved` only with closure evidence, never on the
basis of its mere absence from a later execution's scan.

A future Verify-stage protocol addition to this ecosystem lifecycle remains
out of scope for this phase and is not named here by any not-yet-existing
filename, consistent with this document's own no-forward-path discipline
(Section 11).

## 11. Enforcement

Exactly two layers are mechanically enforced by this framework's own
tooling today. Feature-Done (Section 6) is verified by `tools/validate.sh`
check C16, mechanizing the era-safe referential rule that every `complete`
feature has a corresponding approved contract, a passing QA verdict, and
evidence resolving on disk. Merge-Done (Section 8) is verified by the
three jobs `.github/workflows/compliance.yml` declares, which already run
on this repository today. Release-Done (Section 9) additionally requires
the release close-out gate defined by phase 013, feature 097, once that
feature lands.

Two further deliverables extend this enforcement without altering it: the
consumer template defined by phase 013, feature 095, and the pull-request
template defined by phase 013, feature 096 -- both currently pending in
this phase's own feature list, and both referenced here by feature id and
phase only, never by path, because this framework's own DAG does not
guarantee their landing order relative to this document.

Every other named layer -- Step-Done, Handoff-Done, Gate-Done, Plan-Done,
and Ecosystem-Done -- is consumer-aspirational: a consuming repository
enforces it in its own runtime, per the same split `standard/capability_profiles.md`
and `standard/ci_gates.md` already record for their own domains. A
per-step evidence check mirroring `methodology/04_tool_driven_state.md`
Section 5's evidence-capture-convention shape, distinct from C16's
feature-level check, remains aspirational residue: no such per-step check
is mechanized by this framework's own tooling today.

## 12. A Floor, Not a Guarantee

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

## 13. References

- `standard/anti_hallucination.md`
- `methodology/04_tool_driven_state.md`
- `standard/AGF.md`
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
- `tools/validate.sh`
- `docs/planning/manifest.json`
- `.agent/run_state.json`
