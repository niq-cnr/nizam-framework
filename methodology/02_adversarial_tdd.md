---
id: nizam-adversarial-tdd
title: "Adversarial Test Design"
description: "The evaluator independence model, false-pass and false-fail hunting patterns, and the negative-testing requirement that keeps acceptance test suites load-bearing rather than tautological."
version: 0.3.0
status: active
authoritative_source: methodology/02_adversarial_tdd.md
change_log:
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Add the External Anchor Rule (Section 7) and the Mandatory Adversarial Evidence requirement (Section 8)."
  - version: "0.3.0"
    date: "2026-07-08"
    summary: "Add the Verification-Authoring Standard (Section 10), naming the four forbidden verification anti-patterns (whole-file/vacuous greps, git-diff-HEAD scope guards blind to untracked/new files, bare-adjacency/parenthetical checks, literal-substring checks) and their tools/verify_lib.sh primitive replacements."
---

# Adversarial Test Design

## 1. Overview

An acceptance test suite is only as trustworthy as the adversarial rigor applied
to it. A verification command that "usually passes" is not the same thing as a
verification command that cannot silently pass for the wrong reason. This
protocol governs the **Evaluator** role defined in `standard/AGF.md` Section 2:
the agent that runs a feature's acceptance tests and independently confirms
pass/fail with evidence, at both the contract-review stage and the QA-verdict
stage of `01_execution.md`.

## 2. Evaluator Independence

The Evaluator that authors, hardens, and executes acceptance tests MUST be a
role distinct from the Generator that writes the implementation code being
tested. This separation exists to prevent the single most common source of
false confidence in a pipeline: an agent grading its own work.

1. **Never trust generator-supplied evidence as a substitute for re-execution.**
   If a Generator's implementation report claims "tests pass" or pastes terminal
   output into its own summary, the Evaluator MUST NOT accept that claim as the
   verdict. The Evaluator re-runs every verification command itself, in its own
   execution context, and derives the verdict from what it observes — not from
   what it was told.
2. **Every verdict is re-derived, not inherited.** A prior stage's PASS is not
   evidence for a later stage's verdict. Validator Mode B's approval that files
   match the contract does not substitute for the Evaluator's own QA run; each
   gate in `01_execution.md` produces its own independent JSON verdict.
3. **Prose is not proof.** Consistent with `standard/anti_hallucination.md`
   AH-3, an Evaluator's verdict MUST cite command output or a file diff it
   personally captured. A verdict that says "confirmed working" with no
   externalised evidence path attached is treated as a rejection, not an
   equivocal pass.

## 3. False-Pass Hunting

Before trusting a verification command's PASS output, the Evaluator actively
searches for ways that command could report success without the underlying
acceptance criterion actually holding. Two generic failure patterns recur across
verification commands and MUST be checked for on every acceptance test the
Evaluator inherits from a contract:

### 3.1 The Vacuous Negated Grep

A command shaped like `! grep -q "forbidden-string" some/path` (or the inverse,
`grep -L`) is intended to prove *absence* of a forbidden pattern. But if
`some/path` does not exist, or resolves to an empty file, or an empty glob
expansion, the grep call fails to find a match for a reason that has nothing to
do with the pattern actually being absent from real content — and the command
still reports success. **A negated grep is only trustworthy once the Evaluator
has independently confirmed the target it searches is non-empty and actually
present** (for example, asserting a non-zero file count over the same glob
before trusting the negated match against it). An absence-of-match result that
cannot be distinguished from "there was nothing there to match against" is not
evidence of anything.

### 3.2 Locale-Dependent Sort Ordering

A command that pipes through `sort` (or relies on lexical ordering to build an
expected-vs-actual comparison string) can produce a different, valid-looking
ordering depending on the executing environment's locale (`LC_ALL`, `LC_COLLATE`,
or equivalent). A comparison built on an unpinned `sort` can pass in the
Evaluator's environment and fail in another agent's or a CI runner's, for
reasons that have nothing to do with the feature under test. **Any verification
command that depends on sort order MUST pin its collation explicitly** (e.g.
`LC_ALL=C sort`) rather than relying on whatever locale happens to be active,
and the Evaluator MUST flag and hardened-reject any inherited command that
sorts without an explicit, pinned collation before trusting its comparison.

These two patterns are illustrative, not exhaustive. The underlying discipline
generalizes: for every verification command, ask "what condition, unrelated to
the acceptance criterion, could make this command exit 0 (or exit non-zero)
anyway?" — and harden or reject the command until no such condition remains
before trusting its output.

## 4. False-Fail Hunting

The inverse failure mode is equally dangerous: a verification command that can
report failure even when the acceptance criterion genuinely holds, because of an
environmental assumption the command silently depends on (a working directory
assumption, a tool version difference, a network dependency for what should be
a purely local check). Before accepting a FAIL result as proof of a real defect,
the Evaluator re-examines the command for such assumptions and confirms the
failure reproduces for the reason the acceptance test actually cares about, not
for an unrelated environmental reason. A verdict of FAIL still requires the same
evidentiary rigor as a verdict of PASS.

## 5. Negative Testing

Acceptance coverage that only ever exercises the "everything is correct" path is
tautological — it proves the test can pass, not that the test can meaningfully
fail. Every feature's acceptance coverage MUST include **at least one
deliberately-adversarial or negative-space check**, in addition to the contract's
listed positive verification commands. Acceptable forms include (not an
exhaustive list):

- **A stray-file guard** — asserting the exact expected set of files in a
  directory, so that an accidental leftover draft or out-of-scope artifact is
  caught even when it would not affect a simple count-based check.
- **A forbidden-string absence check with a directory-emptiness guard** — per
  Section 3.1, paired with an independent confirmation that the search target
  is non-empty.
- **An out-of-scope-edit detector** — confirming that files outside a
  contract's declared scope were not touched, so that silent scope creep is
  itself a failing condition the suite can detect.
- **Schema rejection of invalid documents** — for any feature that ships or
  relies on a JSON Schema, acceptance coverage MUST include at least one
  document deliberately constructed to violate the schema (a missing required
  key, a wrong-typed value, or a forbidden extra key on a schema with
  `additionalProperties: false`) and confirm the schema **rejects** it, not
  only that valid documents are accepted. A schema whose test suite only ever
  feeds it valid input has never actually been shown to constrain anything.

A test suite containing only ever-passing, always-affirmative checks is
insufficient acceptance coverage on its own, independent of how many such checks
exist.

## 6. The Mandatory Adversarial Spot-Check

Beyond the listed acceptance criteria a contract enumerates, every QA round
(the Loop 2 evaluator step defined in `01_execution.md` Section 3) MUST include
exactly one additional, evaluator-originated adversarial spot-check that is not
among the contract's listed verification commands. This spot-check is recorded
alongside the standard checks in the QA verdict (`schema/qa_verdict.schema.json`'s
`adversarial_check` object: a description, a result, and an evidence path) and
is subject to the same evidentiary rigor as every other check in this protocol.

The spot-check exists to catch exactly the class of defect a contract's author
did not think to enumerate — a plausible-but-wrong edge case, a boundary the
listed tests happen not to cross. A QA round that only re-runs the contract's
own list, verbatim, has not independently verified anything beyond what the
contract's author already anticipated.

## 7. The External Anchor Rule

Every consistency or QA check that asserts a document matches actual practice,
a schema, or another artifact's shape MUST anchor its expected value on a
**source external to the artifact under test** — for example the schema file
itself, a sibling protocol document, `run_state.json`'s recorded history, or
the actual behavior of the pipeline the document describes. A check MUST
NEVER derive its expected value by grepping, quoting, or otherwise
re-deriving it from the artifact-under-test's own content or phrasing.

This rule remediates a generic and recurring failure mode: a check that
verifies a document "matches practice" by searching the document itself for
its own claimed phrasing can report PASS even when the document's claim is
substantively wrong, because the thing being graded and the thing supplying
the expected answer are one and the same artifact — the check has nothing
external to disagree with it. A verification command's source of truth MUST
always live outside the file it is grading; a check whose only citation is
the artifact under test quoting itself has established nothing and MUST be
rejected as vacuous, per the false-pass discipline in Section 3.

## 8. Mandatory Adversarial Evidence

Every QA round's Section 6 adversarial spot-check MUST be captured to its own
evidence file, in addition to being recorded in the QA verdict's
`adversarial_check` object. The file naming convention is
`<contract-id>-qa-adversarial.txt` (for example
`.agent/evidence/014-qa-adversarial.txt`), following the same evidence-file
family defined in `04_tool_driven_state.md` Section 4, and the QA verdict's
`adversarial_check` object MUST reference that evidence file by path.

A verdict whose `adversarial_check` has no corresponding evidence file
present on disk is **incomplete**, per `standard/anti_hallucination.md` AH-3
(evidence-anchored completion) — such a verdict MUST be treated as a
rejection, not a pass, regardless of what the verdict's prose claims about
the spot-check having been performed.

## 9. References

- `standard/AGF.md` — the Evaluator role definition and the JSON Verdict Parse
  Rule this protocol's verdicts must satisfy.
- `standard/anti_hallucination.md` — AH-2 (detect before fix) and AH-3
  (evidence-anchored completion), both directly binding on Evaluator conduct.
- `01_execution.md` — the two loops in which the Evaluator's contract review and
  QA verdict steps occur.
- `03_circuit_breaker.md` — bounds the rework loop triggered by a QA failure
  this protocol's checks produce.

## 10. Verification-Authoring Standard

A verification command is only as trustworthy as its resistance to the
false-pass and false-fail patterns catalogued in Sections 3 and 4. This
section codifies four specific anti-patterns that MUST NOT appear in any
contract's verification suite, each paired with the compliant primitive from
`tools/verify_lib.sh` (the vetted verification-helper library, F-023) that
replaces it.

**(a) Whole-file / vacuous greps** — A check that greps an entire file for a
token proves only that the token appears somewhere in the file, not that it
appears within the section, block, or context the acceptance criterion
actually cares about; per Section 3's false-pass discipline, such a
whole-file match is vacuous whenever the same token can legitimately appear
elsewhere (a prior version's change_log entry, an unrelated section, a
sibling document quoted verbatim). Use `verify_lib.sh`'s section-scoped
primitive `vlib_section_grep <file> <heading-regex> <token-regex>` instead,
which confines the match to the span running from the named heading up to
the next markdown heading at any depth (or EOF), so a token present only
outside the relevant section correctly fails the check.

**(b) `git diff HEAD` scope guards blind to new / untracked files** — A
scope guard built on `git diff --name-only HEAD` (or any other `git diff
HEAD` variant) reports changes only against paths git already knows about at
`HEAD`; it is structurally blind to a brand-new file that was never
committed, so a contract that introduces a wholly new out-of-scope file
would pass such a guard entirely undetected. Use `verify_lib.sh`'s
untracked-aware primitive `vlib_scope_guard <allowed-path-or-prefix> ...`,
built on `git status --porcelain --untracked-files=all -- .
':(exclude).agent'`, which sees new/untracked paths as well as modified
ones.

**(c) Bare-adjacency / parenthetical "appears near" checks** — A check that
only confirms two tokens occur near one another in the same paragraph or
parenthetical aside — without asserting any real structural or semantic
relationship between them (the same heading's span, the same table row, the
same schema field, the same parsed record) — can be satisfied by unrelated
prose that merely happens to mention both words close together. A bare
adjacency or parenthetical "appears near" test is not evidence of the
relationship an acceptance criterion is meant to assert, and MUST be
replaced with a check that ties the two values to the same concrete
structural anchor (for example, both tokens verified within the same
`vlib_section_grep` span, or both fields read from the same parsed record).

**(d) Literal-substring checks that false-pass on unrelated text** — A check
that merely searches for a literal substring (a version number, a path
fragment, a keyword) can false-pass when that same substring occurs in
unrelated text that has nothing to do with the acceptance criterion — a
version string embedded in an unrelated sentence, or a path fragment that is
itself a substring of a longer, different path. Require a check that asserts
real content instead: `vlib_version_increased <file>` (a YAML-parsed strict
semver tuple comparison against the file's own HEAD copy, not a substring or
`!=` comparison), `vlib_path_resolves <path-token>` (an actual `test -e`
resolution against the working tree, not a string match against the path
text), and `vlib_no_stale_payload <file>` (a real per-line structural scan
for a stale multi-directory enumeration, not a substring hit).

Every contract's verification suite MUST be reviewed against all four of
these anti-patterns, in addition to the false-pass and false-fail hunting
practice of Sections 3 and 4, before it is approved; a verification command
that relies on any of (a)-(d) is not acceptance coverage and MUST be
rejected and rewritten using the corresponding `tools/verify_lib.sh`
primitive named above.
