---
id: nizam-ecosystem-engineering-audit
title: "Engineering Audit Protocol"
description: "The reusable, evidence-first engineering audit protocol: consumes the current execution's Preflight verdict and Baseline, ranks evidence into four tiers, assesses claims against the ten-state maturity model under the no-promotion-beyond-evidence rule, records finding confidence, and explicitly excludes commercial/market readiness from generic engineering scoring."
version: 0.1.2
status: active
authoritative_source: ecosystem/03_engineering_audit.md
change_log:
  - version: "0.1.2"
    date: "2026-07-20"
    summary: "Tier-0 doc-truth: both stale parentheticals for schema/engineering_finding.schema.json -- in Section 7 and in the References entry, each reading 'added by a later feature in this phase; not yet present at the time this protocol was authored' -- are retired. The schema shipped in feature 039 and has been present under schema/ since. No semantic change; the commercial-readiness deferral to 08_ga_gate.md (Section 6) is unaffected."
  - version: "0.1.1"
    date: "2026-07-18"
    summary: "Feature 048 (operator PR #21 review, finding 4): the deferred GA-gate reference now uses the module's bare-filename convention (08_ga_gate.md) instead of a directory-qualified path that dangles until the document ships."
---

# Engineering Audit Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's Audit
step -- the evidence-first engineering assessment an agent or engineering
team performs once a clean-state preflight
(`ecosystem/01_clean_state_preflight.md`) has produced a verdict, and a
baseline (`ecosystem/02_evidence_baseline.md`) has been captured, for the
current execution. An audit never operates in a vacuum: every finding it
records is measured against the fixed reference point the baseline provides,
and every claim a finding makes is capped by the evidence actually available,
never by what the auditor would prefer to be true.

Consumers extend this protocol with their own repository- and
ecosystem-specific finding categories and severities; they do not redefine
its evidence hierarchy, its maturity model, its finding confidence
vocabulary, or its commercial-readiness exclusion. Those four mechanics are
defined once, here, exactly as `ecosystem/01_clean_state_preflight.md` is the
single source of truth for the preflight verdict vocabulary and
`ecosystem/02_evidence_baseline.md` is the single source of truth for the six
baseline field categories.

## 2. When to Run

An audit MUST NOT begin until:

- A clean-state preflight run has returned a `PASS` verdict, or a
  `PASS_WITH_EXCEPTIONS` verdict an operator has explicitly approved, per
  `ecosystem/01_clean_state_preflight.md` Sections 3 and 5. An audit is never
  run against a `FAIL` verdict or an unresolved `PASS_WITH_EXCEPTIONS`.
- A baseline has been captured for the current execution, per
  `ecosystem/02_evidence_baseline.md` Section 2. An audit with no baseline has
  no fixed reference point to measure evidence against and is not a valid
  audit.

The audit consumes both the Preflight verdict and the Baseline as its
required inputs: the Preflight verdict establishes that the state being
audited is clean and safe to reason about, and the Baseline supplies the
anchored, point-in-time facts (framework, repository, dependency, CI,
planning, and evidence references) every finding cites evidence from. This is
the audit's evidence-first entry condition -- an audit that begins without
both inputs is not evidence-first, it is speculative.

An audit run is deterministic and repeatable in the sense that re-running it
against the same, unchanged baseline produces the same findings; it is not
repeatable across different baselines, which is precisely why every finding
cites the baseline it was measured against.

## 3. Evidence Hierarchy

This section defines the evidence hierarchy every finding in this audit must
cite. Evidence is ranked into four tiers, strongest first:

- **Tier 1 -- Verified**: deterministic, machine-checked evidence produced by
  an existing framework mechanism -- a green `tools/validate.sh` check, a
  passing test suite, a schema-valid artifact. This is the strongest evidence
  a finding can cite.
- **Tier 2 -- Reproduced**: deterministic tool output the auditor
  independently re-ran and confirmed, but not yet wired into a standing
  automated check.
- **Tier 3 -- Observed**: a human-authored, structured observation -- a
  manual code read, a documented reproduction -- not yet independently
  re-run by anyone else.
- **Tier 4 -- Asserted**: an unverified, narrative claim with no attached
  artifact. This is the weakest evidence a finding can cite.

A finding's evidence tier determines the maximum finding confidence level
(Section 5) and the maximum maturity level (Section 4) it may claim. No
finding is recorded against evidence that does not fit one of these four
tiers; an auditor who cannot place a piece of evidence in Tier 1-4 does not
yet have evidence, only a claim.

## 4. Maturity Model

Every claim in an audit finding is assessed against the following ten-level
maturity model, in ascending order:

1. Designed
2. Authored
3. Implemented
4. Unit Tested
5. Integrated
6. Rendered
7. Deployed
8. Exercised
9. Observable
10. Production Proven

No claim may be promoted beyond its evidence: a finding MUST NOT assert a
maturity level higher than its cited evidence tier (Section 3) supports, and
MUST NOT assert a maturity level the evidence itself does not demonstrate --
citing a passing unit test alone (Tier 1 evidence of level 4, Unit Tested)
does not support a claim of level 7, Deployed, without separate deployment
evidence. This is the no-promotion-beyond-evidence rule, and it applies to
every finding this protocol governs, without exception: an auditor who wants
to claim a higher maturity level must gather the evidence for that level, not
infer it from a lower one.

## 5. Finding Confidence Levels

Every finding in this audit records a confidence level, independent of its
severity or the maturity level it asserts:

- **Confirmed** -- backed by Tier 1 evidence (Section 3); independently
  reproducible by anyone with access to the same tooling.
- **Probable** -- backed by Tier 2 evidence; reproducible by the auditor, not
  yet wired into an automated check.
- **Suspected** -- backed by Tier 3 evidence; a single documented
  observation, not yet independently re-run by anyone else.

A finding backed only by Tier 4 (Asserted) evidence MUST NOT be recorded at a
confidence level higher than Suspected, and SHOULD be excluded from an
audit's findings entirely until at least Tier 3 evidence is gathered. An
audit that records Confirmed or Probable findings on Tier 4 evidence has
violated the no-promotion-beyond-evidence rule (Section 4) at the confidence
layer, exactly as it would at the maturity layer.

## 6. Commercial Readiness Exclusion

Commercial and market readiness -- pricing, go-to-market timing, customer
commitments, sales pipeline, and competitive positioning --
MUST NOT be embedded in generic engineering scoring. This protocol's
evidence hierarchy (Section 3), maturity model (Section 4), and finding
confidence levels (Section 5) measure engineering state only: whether
something was designed, built, tested, integrated, deployed, exercised,
observed running, and proven in production, backed by evidence an auditor
can point to.

Commercial and GA readiness are assessed separately, by the deferred GA gate
(`08_ga_gate.md`, this module's planned protocol document, per
`docs/nips/NIP-0001-ecosystem-engineering-cycle.md` Section 2.3), and MUST
NOT be conflated with, or substituted for, an engineering audit finding. An
engineering finding that scores a capability's commercial fit, pricing
model, or market timing is out of scope for this protocol and belongs, if
anywhere, in the GA gate's own evidence package -- never in this audit's
findings.

## 7. Audit Artifact

Every audit run MUST emit a schema-valid, machine-readable findings artifact
at:

```text
.agent/audits/<audit-id>/findings.json
```

and a corresponding human-readable report at:

```text
.agent/audits/<audit-id>/report.md
```

where `<audit-id>` is the unique identifier of the ecosystem-cycle audit,
per the framework's Artifact Locations convention
(`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`). The findings
artifact's shape (severity, confidence per Section 5, evidence per Section 3,
impact, owner, and closure criteria) is defined by
`schema/engineering_finding.schema.json`. This protocol governs the
artifact's required semantics; it does not itself define the JSON Schema.

Evidence backing every finding (raw tool output, logs, or intermediate
collection results) is externalised by path under
`.agent/evidence/<execution-id>/`, per the framework's Evidence Capture
Convention (`methodology/04_tool_driven_state.md` Section 5) -- never pasted
inline into the findings artifact, the report, or a chat transcript.

## 8. References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` -- the accepted NIP
  defining the Maturity Model, the Artifact Locations, and the Dogfood
  Requirement this protocol implements.
- `ecosystem/README.md` -- the module index and canonical lifecycle this
  protocol is one step of.
- `ecosystem/01_clean_state_preflight.md` -- the preceding lifecycle step: no
  audit is run except from a `PASS` or approved `PASS_WITH_EXCEPTIONS`
  preflight verdict.
- `ecosystem/02_evidence_baseline.md` -- the immediately preceding lifecycle
  step: no audit is run without a captured baseline to measure evidence
  against.
- `methodology/04_tool_driven_state.md` -- the Evidence Capture Convention
  this protocol's evidence externalisation follows.
- `methodology/03_circuit_breaker.md` -- the house pattern this document's
  structure, tone, and immutability discipline follow.
- `schema/engineering_finding.schema.json` -- the machine-readable schema for
  the findings artifact this protocol requires.
