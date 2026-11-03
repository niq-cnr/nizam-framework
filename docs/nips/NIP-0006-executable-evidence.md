---
id: nip-0006-executable-evidence
title: "NIP-0006 — Executable Evidence"
description: "Proposes four clauses for standard/: evidence for executable deliverables comes from executing them, a control is established only once observed to reject a non-conforming input, a record's status is machine-checked against its own cited evidence, and unverifiable is a recorded status rather than an omission."
version: 0.1.0
status: draft
authoritative_source: docs/nips/NIP-0006-executable-evidence.md
change_log:
  - version: "0.1.0"
    date: "2026-11-03"
    summary: "Draft four executable-evidence clauses observed as defect classes in a live dogfooding session. Proposed only: nothing in standard/, methodology/, tools/ or .nizam/ changes, and no gate changes, until H-NIP acceptance and a versioned release."
---

# NIP-0006 — Executable Evidence

## Status

**Draft — proposed, not landed.** This document proposes standard text. It changes no gate, no
schema, no validator check and no installed `.nizam/` payload. Adoption requires H-NIP acceptance, a
versioned release under `methodology/06_release_train.md`, and an actual self-installation. See
Section 6.

This NIP is a companion to [NIP-0005](NIP-0005-executable-claim-binding.md) and overlaps it. Section 5
states the overlap and the order in which the two should land.

## 1. The defect class

A governance framework's promise is that its claims are verifiable. A session dogfooding this
framework found four ways that promise can hold on paper while being false in practice. Each one
passed the framework's own gates.

| # | Defect | Observed form |
|---|---|---|
| D1 | **Evidence by reading, not by execution.** A deliverable that is executable was accepted on a review that read its specification. | Prose guarantees were reviewed and passed. The first execution attempt of the same guarantees failed. |
| D2 | **Control never observed to fail.** A gate, checker or verifier was treated as working because it printed a pass. | A check that always passes produces the same green result as a correct check. Nothing in the record distinguishes them. |
| D3 | **Status asserted independently of its evidence.** A record carried a status and cited evidence, and nothing compared the two. | A status field said one thing while the cited evidence said another, and both were preserved. |
| D4 | **Unverifiable recorded by omission.** Claims whose prerequisite did not exist were dropped from the report, or counted as satisfied. | A harness reported every predicate as `SKIPPED`, which is neither passed nor failed. |

D1–D4 are not hypothetical. The validator's current output in this repository already shows the D3
pattern in a live record: `docs/nips/NIP-0005-executable-claim-binding.md` declares
`status: proposed`, a value the schema does not accept (C1, C2), and
`.agent/contracts/nip0005-executable-claim-binding.json` uses status `pending`, which the contract
schema does not accept (C11). Neither file is changed by this NIP.

## 2. Proposed standard text

The four clauses below are proposed for a new standard document under `standard/` (name not yet chosen),
or for an added section of `standard/anti_hallucination.md`. Placement is an open decision (Section 6, item 1). The clauses
extend AH-3 (Evidence-Anchored Completion); they do not replace it.

### EE-1 — Executable deliverables are evidenced by execution

Where a deliverable is executable (code, a schema applied to a data artifact, a migration, a
configuration consumed by a runtime, a gate), its evidence MUST be an execution that attempts the
operation the deliverable claims to support. A review that reads the deliverable or its specification
MAY support a finding. It MUST NOT by itself establish that a guarantee holds.

*Rationale (D1):* a specification states what the artifact should do; reading establishes what the
prose says. Only an execution establishes what the artifact does.

### EE-2 — A control is established only once it has been observed to fail

A gate, checker, verifier or validator is treated as working only after it has been run against at
least one deliberately non-conforming input and observed to reject it. The negative control, its input
and its rejection output MUST be retained as evidence. A control with no recorded rejection is
**unestablished**, and its passing results MUST NOT be cited as coverage.

*Rationale (D2):* a control that cannot fail yields the same output as one that works. The only
difference is observable on a bad input.

### EE-3 — Status is machine-checked against its own evidence

Where a record carries both a status and the evidence that supports it, a machine check MUST confirm
that the two agree. A status that contradicts its own cited evidence (for example `complete` with an
evidence file missing, failing, or referring to a different candidate) is a **defect of record**. It is
not a matter of interpretation, and the record MUST NOT be advanced or cited until the disagreement is
resolved.

*Rationale (D3):* a human reading two fields can rationalise the mismatch. A machine check cannot.

### EE-4 — Unverifiable is a status, not an omission

An assertion whose prerequisite does not exist MUST be recorded with the status `unverifiable` and the
missing prerequisite named. It MUST NOT be omitted from the report, and it MUST NOT be counted as
satisfied. A report has three outcomes for each assertion — `pass`, `fail` and `unverifiable` — and
`unverifiable` is counted and shown separately.

*Rationale (D4):* "we cannot check this, and here is what is missing" is an honest position. "Nobody
looked" is not, and a two-state report cannot tell them apart.

## 3. Conformance

A repository conforms when:

1. Each executable deliverable has at least one recorded execution evidence item (EE-1).
2. Each gate or checker it relies on has at least one retained negative-control rejection (EE-2).
3. A machine check reports disagreement between each record's status and its cited evidence, and the
   count is zero (EE-3).
4. Every assertion without a prerequisite is recorded as `unverifiable` with the missing prerequisite
   named, and no assertion is absent from its report (EE-4).

Conformance is a property of a run, not of a document. Like NIP-0005 §3, a conformance claim that has
never been executed is itself unverified.

## 4. What this does not do

- It does not require any particular tool, schema or language.
- It does not make a weak test strong. EE-2 shows that a control *can* fail; it does not show that
  it fails on the right thing.
- It does not replace review. Review remains the right gate for judgement; EE-1 stops review being the
  only gate for a question that execution can answer.
- It does not retroactively reclassify existing records. Their status is unchanged until a machine
  check finds a disagreement under EE-3.

## 5. Relationship to NIP-0005

| This NIP | NIP-0005 | Relationship |
|---|---|---|
| EE-1 | A2, A3 | Overlapping. A3 binds receipts to independently authored expectations; EE-1 requires that the evidence be an execution at all. |
| EE-2 | §3 item 4 | Overlapping. NIP-0005 requires a negative control per `verified_by`; EE-2 makes it a general requirement for every control. |
| EE-3 | none | Additive. NIP-0005 does not require status/evidence agreement. |
| EE-4 | A1 (`UNBOUND` vs `unverifiable`) | Overlapping. NIP-0005 defines the `UNVERIFIABLE` disposition with a closed category set; EE-4 generalises the rule to every report. |

Recommended order: NIP-0005 is accepted first, because its `verified_by`/`unverifiable` vocabulary is the
more specific one. EE-3 may land independently. EE-1 and EE-2 should be merged into NIP-0005's
vocabulary rather than run as a second mechanism. Section 6 records this as an operator decision.

## 6. Landing steps and open decisions

Nothing in this section has been done. Each step is gated.

**Operator decisions (must be made before any step below):**

1. **Placement.** A new document under `standard/` (name to be chosen), or an added section of
   `standard/anti_hallucination.md`. The first is a new standard document; the second extends an
   existing active one.
2. **Order versus NIP-0005.** Accept NIP-0005 first (recommended), or merge EE-1–EE-4 into NIP-0005 as a
   single amendment.

**Steps required to land (in order):**

1. H-NIP acceptance of this NIP's scope, recorded by the operator in `.agent/run_state.json` with a
   verbatim authorization.
2. Move this NIP's `status` from `draft` to `active` only after acceptance, per `standard/NDS.md` §3.
3. Write the chosen standard text (Section 2) into `standard/`, add its row to `standard/README.md`,
   and add it to `NIZAM.json`'s `standard` key documents. Each file's frontmatter needs `version` and a
   `change_log` entry (`standard/NDS.md` §4).
4. Add the negative controls the clauses need: a fixture that status/evidence disagreement must fail
   (EE-3), and a fixture that an omitted assertion must fail (EE-4). Each must be run and observed to
   fail before it is trusted. This is the EE-2 requirement applied to this change itself.
5. Add a `CHANGELOG.md` entry under `[Unreleased]` naming the tier and consumer impact (MINOR, because it
   adds optional-to-consumers capability and changes no required key), per
   `methodology/06_release_train.md` §3.2 and §4.
6. Run `bash tools/validate.sh`, `python3 tools/test_canonical_formats.py` and the other suites that
   `.github/workflows/compliance.yml` runs. Retain the output under `.agent/evidence/`.
7. Release through `methodology/06_release_train.md`: a prepublication actual self-install, then the
   human sign-off, then the annotated tag. None of these may be performed by the drafting agent.

**Not performed by this NIP's author:** no version bump in `NIZAM.json` or `CHANGELOG.md` released
section, no tag, no self-install, no change to `.nizam/`, no change to any gate.
