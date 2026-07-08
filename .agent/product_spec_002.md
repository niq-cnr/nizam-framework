---
id: nizam-product-spec-002
title: "Nizam Framework — Phase 002 Spec Addendum (Self-Compliance Hardening)"
description: "Phase-002 specification addendum: remediates the six self-compliance gaps found after the v0.1.0 genesis by adding CI enforcement, a repo-local compliance validator, an evidence-capture convention, and adversarial/plan/release rule hardening. Extends product_spec.md, does not replace it."
tags: [spec, governance, self-compliance, ci, validator, phase-002]
status: draft
last_audited: "2026-07-08"
authoritative_source: NA
version: 1.0.0
spec_version: "1.0.0"
created_at: "2026-07-08T00:00:00Z"
updated_at: "2026-07-08T00:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-08T00:00:00Z"
    summary: "Initial phase-002 spec addendum (self-compliance hardening). PROPOSED — awaiting human authorization."
---

# Nizam Framework — Phase 002 Spec Addendum (Self-Compliance Hardening)

**Status: PROPOSED — awaiting human authorization.** This addendum plans phase
`002-self-compliance`. It does not change `run_state.json`, and the manifest carries
phase 002 as non-active (`status: pending`, `activation_state: proposed`) until a human
authorizes activation. It extends `.agent/product_spec.md` (spec v1.0.0); it does not
supersede it.

## 1. Motivation — The Self-Compliance Gap

Phase 001 shipped a governance framework that prescribes CI enforcement (`standard/NDS.md`
§7) and evidence discipline (`methodology/04_tool_driven_state.md`) but did not itself run
any of it. The framework passed 22 internal gate reviews and still shipped NDS violations
that only an external PR reviewer caught. The framework did not yet dogfood its own
standard. Phase 002 closes that gap: the framework must enforce, on itself, in CI, the
rules it asks its consumers to obey.

## 2. Findings Ledger (remediation targets)

| ID | Gap | Evidence | Remediated by |
|----|-----|----------|---------------|
| G1 | NDS §7 prescribes CI enforcement; repo ships none. Genesis shipped NDS violations (non-repo-relative `authoritative_source` ×24, untagged fences ×8, verdict-shape drift). | PR #1 external review; features 009/010 remediation history | F-011, F-012, F-013 |
| G2 | Verification checked key PRESENCE not value FORMAT — why G1 passed 22 gates. | qa/* history; feature 009 findings | F-012 (format checks) |
| G3 | Evidence-capture convention gaps, now immutable: QA commands as prose (`qa/002.json`), evidence lacking exact invocation (`006-verify-05.txt`), session-absolute `/tmp` paths (`006-qa-05.txt`), missing adversarial-evidence file (`qa/000.json`). Convention existed only ad hoc in contracts. | Listed evidence/qa artifacts | F-014 (Evidence Capture Convention) |
| G4 | Durable-state timestamps estimated; one wrong (planner 08:00 vs actual 07:27, later corrected with annotation). | run_state.json history correction note | F-014 (clock-read-timestamps rule) |
| G5 | Orchestrator did plan amendments (features 008-010) and release mechanics (changelog roll-up, tagging) without a documented protocol assigning it those powers. | run_state amendment_* events; release commits | F-014 (Plan Amendment Rule + release-manager role) |
| G6 | A QA consistency check false-passed by anchoring on the artifact under test (QA-002 verified AGF's parse rule against AGF's own wrong fragments). | qa/002.json | F-014 (External Anchor Rule) |

## 3. Layout Amendment (specified here, implemented by F-011)

Phase 002 introduces two new top-level locations. F-011 amends `product_spec.md` §2.1
(MINOR / additive → product_spec.md `spec_version` 1.0.0 → 1.1.0, with a `change_log`
entry per NDS §4) to record them:

```text
nizam-framework/
├── .github/workflows/     # CI enforcement of NDS §7 (compliance.yml)
└── tools/validate.sh      # Runtime-agnostic repo-local compliance validator
```

The layout amendment is F-011's deliverable, not the planner's; this section only
specifies its shape so F-011 can be verified against it.

## 4. Remediation Design (per feature)

### F-011 — ADR-001 + product_spec §2.1 layout amendment
Instantiate `docs/architecture/ADR-001-ci-compliance-enforcement.md` from
`templates/ADR_TEMPLATE.md` (dogfooding the template): decision = adopt CI enforcement of
NDS §7 plus a repo-local compliance validator; record `.github/workflows/` and
`tools/validate.sh` as the layout addendum. Bump `product_spec.md` `spec_version` to
1.1.0 and add its `change_log` entry (NDS §4). No CI or validator code yet — this feature
authorizes and records the decision only.

### F-012 — tools/validate.sh (repo-local compliance validator)
One runtime-agnostic command, exit 0 on a clean tree, non-zero on any violation. Checks:
frontmatter schema validation of every shipped `.md` (`schema/frontmatter.schema.json`)
PLUS **format** checks (`authoritative_source` equals the file's own repo-relative path or
`NA`; `status` enum; semver `version`); untagged-fence sweep (NDS §6.2); `NIZAM.json`
schema validation + full indexed-path walker; branding/endpoint grep; `bootstrap.sh`
`bash -n` + timeout-guarded `--help`; module-README presence (NDS §5.3); and the NDS §4
version-bump-requires-changelog check against `git` history. Index `tools/validate.sh` in
`NIZAM.json` (capability count grows; index stays schema-valid, all paths resolve).
Ship NEGATIVE fixtures under `tools/fixtures/` (bad `authoritative_source` value, untagged
fence, broken indexed path) that each make the validator exit non-zero. G2 remediation:
the validator asserts value FORMAT, not merely key presence.

### F-013 — .github/workflows/compliance.yml (CI)
A GitHub Actions workflow that runs `tools/validate.sh` on `pull_request` and on push to
`main`. Acceptance: the YAML parses, and the exact command CI invokes also passes when run
locally against the repo tree.

### F-014 — Methodology / standard hardening (dogfood NDS §4 on every edit)
Each edited doc gets a `version` bump + a `change_log` entry (or a root `CHANGELOG.md`
entry) per NDS §4:
- `methodology/02_adversarial_tdd.md` — **External Anchor Rule** (a consistency check MUST
  anchor on the source of truth, never on the artifact under test — remediates G6) and a
  mandate to capture one adversarial-evidence file per QA round (remediates G3's missing
  `qa/000.json` adversarial file).
- `methodology/04_tool_driven_state.md` — **Evidence Capture Convention** (exact invocation
  as the first line of every evidence file, `EXIT:<code>` as the last line, no
  session-absolute paths, replayable from repo root — remediates G3) and a
  **clock-read-timestamps rule** for durable state (remediates G4).
- `methodology/00_planning.md` — **Plan Amendment Rule** (human-authorized post-phase
  amendments: the orchestrator may register them citing a recorded authorization event;
  substantive re-planning routes to the planner — remediates G5).
- `methodology/05_release_train.md` — assign changelog roll-up + tag mechanics explicitly
  to the release-manager/orchestrator role (remediates G5).

### F-015 — Phase close
Add root `CHANGELOG.md [Unreleased]` entries for the phase-002 deliverables; run
`tools/validate.sh` green against the final tree; record the release decision
(**v0.2.0, MINOR** — new tooling + additive protocol content per
`methodology/05_release_train.md` §3.2) as an explicit **human gate** — the planner does
NOT cut the release.

## 5. Acceptance Criteria (phase-level)

1. `docs/architecture/ADR-001-*.md` exists, is instantiated from the template, and its
   `Status:` line is a valid ADR status; `product_spec.md` `spec_version` is `1.1.0` with a
   matching `change_log` entry.
2. `tools/validate.sh` exits 0 on the clean final tree and non-zero on each shipped negative
   fixture.
3. `tools/validate.sh` is indexed in `NIZAM.json`, which still validates against
   `registry/nizam-index.schema.json` with every indexed path resolving.
4. `.github/workflows/compliance.yml` parses as YAML and its CI command passes locally.
5. Every doc edited in F-014 carries a `version` bump with a corresponding change record
   (`change_log` entry or root `CHANGELOG.md` line), verified by `validate.sh`'s NDS §4
   check.
6. No edit touches any immutable phase-001 artifact (completed contracts, evidence, or QA
   verdicts).

## 6. Constraints

- Immutable artifacts are off-limits: completed `.agent/contracts/*.json`,
  `.agent/evidence/*`, and `.agent/qa/*.json` from phases past are audit records and MUST
  NOT be edited.
- Every new JSON artifact validates against its schema under `schema/`.
- 5 features, atomic command-verifiable acceptance tests, clean acyclic dependency DAG.

## 7. Execution Order

```text
Parallel Group 1: F-011 (ADR-001 + spec §2.1 amendment — no dependencies)
Parallel Group 2: F-012 (validate.sh + NIZAM.json indexing + negative fixtures — depends on F-011)
Parallel Group 3: F-013 (compliance.yml CI — depends on F-012),
                  F-014 (methodology/standard hardening — depends on F-012)
Sequential:       F-015 (phase close + release-decision human gate — depends on F-013, F-014)
```

Dependency graph validated: no dangling references, no cycles, topological ordering exists.
F-011 records the layout so downstream files have a sanctioned home; F-012 builds the
validator that F-013 wires into CI and against which F-014's dogfooded version bumps are
checked; F-015 closes the phase and hands the release decision to a human.

## 8. Feature ↔ Finding Traceability

| Feature | Remediates |
|---------|-----------|
| F-011 | G1 (decision of record + layout) |
| F-012 | G1, G2 (format-not-presence validator) |
| F-013 | G1 (CI enforcement of NDS §7) |
| F-014 | G3, G4, G5, G6 (evidence, timestamps, amendment/release roles, external anchor) |
| F-015 | G1 (green enforcement on final tree + release gate) |
