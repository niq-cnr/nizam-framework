# Pull Request Checklist

This checklist is the merge-layer projection of this framework's canonical
Definition of Done. The canonical Definition of Done is
`standard/definition_of_done.md`; every box below names a check, rule, or
gate that document (or a mechanism it cites) already enforces elsewhere, and
points back to it rather than re-explaining how it works. If a box's
underlying check does not apply to your change (for example, this change
touches no release surface), check it anyway once you have confirmed it
does not apply, and say so in Reviewer Notes below.

## Summary

Describe what this change does and why, in a sentence or two. Name the
phase and feature this change implements if it is tracked in
`.agent/feature_list*.json`.

## Related feature / phase

- Phase:
- Feature ID:
- Contract: `.agent/contracts/<id>.json` (if this change originated from a
  contracted feature)

## Definition of Done

- [ ] `tools/validate.sh` reports `SUMMARY: 16 passed, 0 failed` across checks C1 through C16 on the branch tip.
  - This is the framework's own mechanical sweep: schema validity,
    frontmatter, cross-reference resolution, and the feature-lifecycle
    invariant, among others. A red run here means the branch is not
    mergeable regardless of anything else on this list.

- [ ] `tools/fixtures_self_test.sh` exits 0.
  - Confirms the positive and negative fixtures the validator's own checks
    are proved against still behave as expected; a change that quietly
    weakens a check without anyone noticing usually shows up here first.

- [ ] `tools/e2e_bootstrap_test.sh` exits 0, if this change touches an injected payload surface.
  - "Injected payload surface" means anything a consuming repository
    receives at bootstrap time, as opposed to this framework's own
    envelope. If this change is envelope-only (for example, something
    under `.github/`, `docs/planning/`, or `.agent/`), this box is
    trivially satisfied and does not need a fresh run.

- [ ] Every governed doc this change touches pairs a `version` bump with a matching `change_log` entry (check C8's pairing rule).
  - Applies to any file carrying NDS.md frontmatter: bumping one without
    the other is exactly the drift C8 exists to catch.

- [ ] Every feature claimed `complete` in this change carries the full check C16 chain: an approved `contract`, a passing QA `verdict`, and `evidence` resolving on disk.
  - `complete` is a claim, not a status you set and move on from. C16
    mechanizes that the claim is backed by the artifacts the contract
    lifecycle actually produced.

- [ ] Every `evidence` file this change adds follows the `methodology/04_tool_driven_state.md` Section 5 shape: the exact invocation, the captured output, and a final `EXIT:<code>` line.
  - An evidence file that only asserts a result, without the command and
    output that produced it, is not evidence.

- [ ] `CHANGELOG.md`'s `[Unreleased]` section carries an entry for this change, in the file's existing house bullet style.
  - Write it for the person reading the changelog later, not for the
    reviewer reading the diff now: what changed, and why it matters.

- [ ] If this change touches a release surface, the release close-out gate defined by phase 013, feature 097 (`.github/workflows/release_closeout.yml`) reports green.
  - Release surfaces include version anchors (`NIZAM.json`, `CONTEXT.md`,
    `README.md`, `docs/guide/index.html`, `CHANGELOG.md`'s top released
    section) and `docs/planning/ROADMAP.md`'s disposition line. If this
    change touches none of those, this box does not apply; check it and
    say so in Reviewer Notes.

- [ ] This pull request is not self-merged; the release tag remains operator-only, created only via `H-FRAMEWORK-RELEASE`.
  - No agent or automation merges its own pull request, and no agent
    creates or pushes a release tag. Both are human-gated by design, and
    this box exists so that stays true even under time pressure.

## Testing

What did you run, and what did it show? Paste the relevant command output,
or reference the evidence file(s) under `.agent/evidence/` if this change
came through the contract lifecycle.

## Reviewer notes

Anything a reviewer should focus on, any box above you checked as "not
applicable" and why, or context a fresh pair of eyes will need that is not
obvious from the diff.
