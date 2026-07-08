---
id: nizam-release-train
title: "Release Train Protocol"
description: "The framework's own release discipline: semantic-version git-tag cuts, what constitutes a breaking vs minor vs patch change, changelog discipline, and the consumer upgrade path via bootstrap re-run against a new pinned tag."
version: 0.2.0
status: active
authoritative_source: methodology/06_release_train.md
change_log:
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Add Release Mechanics Ownership (Section 6), assigning changelog roll-up, date-stamping, and tag creation to the release-manager/orchestrator role."
---

# Release Train Protocol

## 1. Overview

The framework is a versioned governance payload, and its own release discipline
must be at least as rigorous as the discipline it asks consumer repositories to
follow. This protocol defines how a new framework version is cut, what
distinguishes a breaking change from a safe addition, the changelog obligations
that accompany every cut, and how a consumer repository moves onto a new
release once it exists.

## 2. Releases Are Semantic-Version Git Tags

The framework is released exclusively as annotated git tags of the form
`vMAJOR.MINOR.PATCH`, following standard semantic versioning. A release is never
a floating branch reference — `standard/GIP.md` Section 2 already binds every
consumer to cloning a pinned tag, never `main`, and this protocol is what makes
that pin meaningful: `main` may contain in-progress, unreleased governance
changes at any time, while a tag is immutable once cut.

Cutting a release means, at minimum:

1. All intended changes for the release are merged to the mainline branch.
2. `CHANGELOG.md` (Section 4) carries an entry for the new version.
3. A human sign-off gate is satisfied — a release is a deliberate, reviewed
   act, never an automatic consequence of a merge.
4. The tag is created and pushed only after 1-3 are satisfied.

## 3. Classifying a Change: Breaking vs Minor vs Patch

Every change to the framework's shipped content is classified into exactly one
of the three semantic-versioning tiers before its release is cut. This
classification determines which version component increments.

### 3.1 Breaking (MAJOR)

A change is breaking if a consumer repository that has already inherited a
prior version could fail, misbehave, or lose data by simply upgrading to it
without additional consumer-side changes. This includes, at minimum:

- **Any JSON Schema change that narrows what previously validated.** Adding a
  new required key to `schema/frontmatter.schema.json`, `schema/contract.schema.json`,
  or any other shipped schema is breaking — documents that validated against
  the prior schema version may no longer validate.
- **Any required-key change** to a governed document type (for example,
  changing the NDS's six required frontmatter keys) is breaking for the same
  reason: previously-compliant consumer content may become non-compliant
  without any change on the consumer's part.
- **Removal or renaming of a shipped file, module, or protocol id** a consumer
  might reference by path or id.

### 3.2 Minor (MINOR)

A change is minor if it adds new, optional capability without invalidating
anything that previously validated or worked. This includes, at minimum:

- **A new template** added under `templates/`.
- **A new protocol document** added under `methodology/` (as this phase's
  `00_planning.md` through `05_release_train.md` were, at initial framework
  genesis).
- **A schema change that only loosens constraints** — for example adding a new
  *optional* property, or widening an enum — such that every document that
  validated under the prior schema version still validates under the new one.

### 3.3 Patch (PATCH)

A change is a patch if it corrects an error without changing the shape of any
contract a consumer depends on — a typo fix, a clarifying rewording, a broken
cross-reference link repaired, or a documentation correction that does not
alter any required key, schema shape, or file path.

### 3.4 When in Doubt, Round Up

If a change plausibly straddles two tiers, it is classified at the higher
(more conservative) tier. A consumer that receives an upgrade classified more
conservatively than strictly necessary loses nothing; a consumer that receives
a breaking change mislabeled as minor or patch can silently start failing.

## 4. Changelog Discipline

Every released version, of any tier, MUST have a corresponding `CHANGELOG.md`
entry at the framework's root. An entry MUST name:

1. The version being released (matching the git tag exactly).
2. The tier (breaking / minor / patch) per Section 3.
3. A concise, human-readable description of what changed and, for a breaking
   change specifically, what a consumer must do to remain compliant after
   upgrading.

This mirrors, at the framework level, the same discipline `standard/NDS.md`
Section 4 requires of every individual governed document: a version bump with
no corresponding change record is a standard violation, whether the version
being bumped is a single document or the framework as a whole.

## 5. Consumer Upgrade Path

A consumer repository does not upgrade by hand-patching its injected governance
files to match a newer release's content. Per `standard/GIP.md` Section 4,
point 5, the only sanctioned upgrade mechanism is a **re-bootstrap against the
new pinned tag**:

1. The consumer updates its recorded `GOVERNANCE_TAG` (or equivalent pinned-tag
   reference) to the new release's tag.
2. The consumer re-runs `bootstrap.sh` (or its own equivalent of
   `standard/GIP.md` Section 2's clone -> inject -> verify sequence) against
   that new tag.
3. The consumer verifies post-upgrade compliance using the same checks defined
   in `standard/GIP.md` Section 3: required governance files present and
   non-empty, any root capability index (`NIZAM.json` or the consumer's
   equivalent) parses, and every injected document's frontmatter remains
   schema-valid.
4. If the new release is classified breaking (Section 3.1) for a schema or
   required-key change the consumer's own content depends on, the consumer
   MUST additionally remediate its own non-governance content against the new
   requirement before it is compliant — the re-bootstrap step alone only
   updates the inherited governance copy, not the consumer's independent
   content that may reference it.

Re-bootstrapping, not hand-patching, is the only path — this is unchanged from
`standard/GIP.md`'s drift-remediation model and this protocol does not
introduce a second, competing upgrade mechanism.

## 6. Release Mechanics Ownership

Once the Section 2 human sign-off gate is satisfied, three specific
release-time mechanics belong to the **release-manager role** — in practice
the **orchestrator**, since `standard/AGF.md`'s role set defines no separate
release-manager role:

1. **The changelog roll-up** — folding `CHANGELOG.md`'s `[Unreleased]`
   entries into the new version's dated section heading.
2. **Stamping the release date** on that section heading.
3. **Creating and pushing the annotated git tag** (Section 2) once 1 and 2
   are complete.

These three actions are release **mechanics**, not feature implementation:
they do not require a Generator contract, and they do not pass through the
Loop 1 / Loop 2 contract-first harness defined in `01_execution.md`. They
are nonetheless still subject to the same branch discipline as every other
change in the repository — they MUST be performed on a dedicated branch
(for example `chore/release-vX.Y.Z`) and merged via a reviewed pull request,
never committed directly to the mainline branch.

## 7. References

- `standard/GIP.md` — pinned-tag inheritance, bootstrap verification, and the
  re-bootstrap-not-hand-patch remediation model this protocol's Section 5
  builds on.
- `standard/NDS.md` Section 4 — the per-document versioning and change-log
  rules this protocol's Section 4 mirrors at the framework level.
- `CHANGELOG.md` — the framework's own running semantic version history.
