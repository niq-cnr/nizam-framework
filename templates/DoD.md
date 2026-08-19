---
id: nizam-template-dod
title: "DoD.md Template"
description: "Consumer-repo DoD.md template: the copy-and-fill per-project checklist that projects standard/definition_of_done.md's eight done-layers onto a fillable, Section-N-cited list. Ships seven full checklist blocks (Step through Release) plus a non-checklist eighth-layer pointer paragraph, a project-specific extension block, and a dod_ref linking note."
version: 0.1.0
status: active
authoritative_source: templates/DoD.md
---

<!--
Copy this file to your project's own definition-of-done checklist (for example, a copy
placed under docs/planning/ and named DoD.md) after bootstrap, and replace every
{{PLACEHOLDER}} token in the body below with real, project-specific content. The
frontmatter block above describes this template artifact itself; only the body that
follows is fill-in-the-blanks. This checklist is a projection, not a replacement: each
block below cites the Section of standard/definition_of_done.md that actually governs
that layer's mechanics, and this file never re-explains what that Section already says.
-->

# {{PROJECT}} — Definition of Done

**Repository:** {{REPO_NAME}}
**Checklist Owner:** {{OWNER}}
**Last Reviewed:** {{DATE}}

This is {{PROJECT}}'s copy-and-fill projection of `standard/definition_of_done.md`'s
layered model onto a per-project checklist. Completion is layered, not monolithic: a
unit of work can satisfy one layer below while a higher layer remains unsatisfied.
Check an item only when it is actually true for {{PROJECT}} today, not aspirationally.

## Step-Done

_"A single agent action is complete only with captured, externalised evidence."_
(`standard/definition_of_done.md` Section 3)

- [ ] Every completed step in this project has a captured evidence file (command
      output or a file diff), not a claim carried only in chat or memory.
- [ ] Each evidence file records the exact invocation run, the captured output, and a
      literal `EXIT:<code>` marker.
- [ ] No step in this project is marked done from inference alone.

## Handoff-Done

_"A role's output is durable only once written to its canonical file family, never
carried in chat."_ (`standard/definition_of_done.md` Section 4)

- [ ] Every role's output in this project's pipeline is written to its canonical
      durable-state file (run state, feature list, contract, QA verdict, or evidence)
      before the next role begins acting on it.
- [ ] No downstream role in this project acts on a result it can only find in
      conversation history.

## Gate-Done

_"A validator or evaluator gate advances only on a fully-satisfied JSON verdict."_
(`standard/definition_of_done.md` Section 5)

- [ ] Every gate in this project's pipeline emits a JSON verdict, parsed
      programmatically, never inferred from prose tone.
- [ ] `final_verdict.approved` is `true` before advancement.
- [ ] `issues`, `missing_acceptance_coverage`, and `unsupported_claims` are each empty
      arrays before advancement; a single non-empty entry in any of the three blocks
      advancement regardless of `approved`'s value.

## Feature-Done

_"A feature reaches `complete` only with an approved contract, a passing QA verdict,
and evidence on disk."_ (`standard/definition_of_done.md` Section 6)

- [ ] This feature has an approved contract on file.
- [ ] This feature has a passing, independently re-derived QA verdict.
- [ ] Every evidence path that QA verdict references actually resolves on disk.
- [ ] This feature's status is set to `complete` only after all three of the above
      hold together, never before.

## Plan-Done

_"A phase's features are planned only with atomic acceptance tests inside an enforced
scope budget."_ (`standard/definition_of_done.md` Section 7)

- [ ] Every acceptance test for this phase is a concrete, independently runnable
      command verifying exactly one fact, never a vague prose goal.
- [ ] Lines changed for this feature stay within this project's rolling-average
      check, or are explicitly flagged and human-acknowledged.
- [ ] Cumulative lines changed this phase remain within this project's authorized
      ceiling, or the plan has been explicitly re-authorized by a human.

## Merge-Done

_"A change is mergeable only when every CI job and the human-review gate pass
together."_ (`standard/definition_of_done.md` Section 8)

- [ ] Every CI job this project requires passes on the latest relevant commit
      (this project's required jobs: {{CI_JOB_LIST}}).
- [ ] A human reviewer has approved the change.
- [ ] No self-merge has occurred.

## Release-Done

_"A version is released only after changelog roll-up, human sign-off, and a tag cut at
the signed-off commit."_ (`standard/definition_of_done.md` Section 9)

- [ ] Every intended change for this release is merged to the mainline branch.
- [ ] This project's changelog carries an entry for the new version.
- [ ] A human sign-off gate has been satisfied.
- [ ] The release tag is created only after sign-off, at the signed-off commit, never
      before.

## Ecosystem-Done (Pointer, Not a Checklist)

If {{PROJECT}} is a participant in a multi-repository ecosystem (registered in a
shared scope document across repositories), it additionally carries an Ecosystem-Done
obligation: a multi-repository engineering claim closes only with path-referenced
closure evidence, never the mere absence of a later finding, per
`standard/definition_of_done.md` Section 10. This template ships no separate
Ecosystem-Done checklist block above, since a project with no ecosystem-membership
topology has nothing to check here. If {{PROJECT}} does participate in one, track its
own Ecosystem-Done obligations directly against that shared scope document rather than
in this file.

## Project-Specific Done Criteria

{{PROJECT_SPECIFIC_DONE_CRITERIA}}

<!-- List this project's own additional acceptance criteria beyond the eight
     framework layers above -- for example a security review, an accessibility audit,
     or a localization sign-off. Leave this section present even if empty at first
     copy; do not delete it. -->

## A Floor, Not a Guarantee

Every layer above is a process floor, not a correctness guarantee, per
`standard/definition_of_done.md` Section 12: a fully satisfied checklist proves the
process was followed, it does not prove the resulting work is correct, safe, or fit
for purpose. Human judgment and adversarial review remain required for {{PROJECT}}
regardless of how many boxes above are checked.

## Linking This Checklist: `dod_ref`

Phase 013, feature 094 added an optional, advisory `dod_ref` string property to
several Nizam schemas (see `schema/README.md` for which artifact schemas define
it), naming the path to the Definition of Done document that governs a given
artifact's completion claims. Nizam schema files live under `schema/`, such as
`schema/contract.schema.json`. If an artifact's own
governing schema carries this optional `dod_ref` property, set it to the path of
this project's own copy of this file (for example, a copy placed under
docs/planning/ and named DoD.md) to bind that artifact's completion claim to this
checklist. The property is never required, and no check fails on its absence.
