---
id: nizam-ecosystem-clean-state-preflight
title: "Clean-State Preflight Protocol"
description: "The reusable preflight protocol that gates entry into the ecosystem engineering cycle: a machine-readable verdict of exactly one of PASS, PASS_WITH_EXCEPTIONS, or FAIL, explicit blocking rules, and the operator-exception rule PASS_WITH_EXCEPTIONS carries before execution continues."
version: 0.1.3
status: active
authoritative_source: ecosystem/01_clean_state_preflight.md
change_log:
  - version: "0.1.3"
    date: "2026-07-20"
    summary: "Tier-0 doc-truth: Section 7's References entry for schema/preflight_verdict.schema.json retires the stale parenthetical 'added by a later feature in this phase; not yet present at the time this protocol was authored' -- the schema shipped in feature 038 and has been present under schema/ since. No semantic change; the reference now reads as the other sibling protocols' schema references do."
  - version: "0.1.2"
    date: "2026-07-20"
    summary: "Feature 056 (NDEBT-018.2): Section 4.1 codifies durably the operational corollary of the tracked-file blocking rule — an orchestrator-owned tracked-state write relevant to a gate decision (e.g. run_state.json's operator_gate_decision event) MUST be committed before the corresponding gated CLI invocation runs, since no --tolerate-untracked flag can rescue a tracked-file modification. Names the feature-043 self-dogfood incident it remediates, so the rule binds by document rather than by per-dispatch instruction."
  - version: "0.1.1"
    date: "2026-07-18"
    summary: "Feature 048 (operator PR #21 review, finding 2): Section 6 now defines when schema-validity binds — the finalized artifact only; a run halted pending the Section-5 operator decision records its exceptions in an informational pending artifact (the shipped CLI's preflight.pending.json) and withholds preflight.json, resolving the Sec 5/Sec 6 pre-approval contradiction empirically confirmed in review."
---

# Clean-State Preflight Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's
clean-state preflight step — the first gate an agent or engineering team runs
before reconciling, auditing, planning, executing against, or verifying a
multi-repository ecosystem. A preflight run inspects the ecosystem's current,
observable state (repository cleanliness, dependency reachability, prior
evidence freshness, and any other repository- or ecosystem-specific
preconditions the consumer registers) and emits exactly one machine-readable
verdict. Nothing downstream in the lifecycle — Baseline, Audit, Plan, Execute,
Verify, Promote, Compare — may begin until a preflight run for the current
execution has produced a verdict artifact, per Section 6.

Consumers extend this protocol with their own repository- and
ecosystem-specific blocking conditions; they do not redefine its verdict
vocabulary, its blocking discipline, or its operator-exception rule. Those
three mechanics are defined once, here, exactly as the framework's Universal
Circuit Breaker (`methodology/03_circuit_breaker.md`) is the single source of
truth for the 3-strike attempt limit.

## 2. When to Run

A preflight run MUST occur:

- At the start of every ecosystem-cycle execution, before any Baseline is
  captured (`ecosystem/02_evidence_baseline.md`) — a baseline built on an
  unclean or unverified state is not trustworthy.
- Before re-entering the cycle after a prior execution ended in `FAIL` or an
  unresolved `PASS_WITH_EXCEPTIONS` — the prior execution's blocking
  conditions MUST be re-checked, not assumed resolved.
- Before any consumer adopts a newly released framework capability
  (successor-phase consumer adoption; see the framework's
  `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` Adoption Requirement).

A preflight run is deterministic and repeatable: running it twice against the
same unchanged state MUST produce the same verdict.

## 3. Verdict

A preflight run MUST return exactly one of the following three verdicts:

- `PASS`
- `PASS_WITH_EXCEPTIONS`
- `FAIL`

No other value is a valid preflight verdict, and a run MUST NOT return more
than one of these three, or none at all. `PASS` means every check the
preflight registers succeeded outright. `PASS_WITH_EXCEPTIONS` means one or
more non-blocking findings were surfaced but nothing blocking (Section 4)
was found; this verdict is provisional until the operator-exception rule
(Section 5) is satisfied. `FAIL` means at least one blocking condition
(Section 4) was found; execution MUST NOT proceed past a `FAIL` verdict under
any circumstance.

## 4. Blocking Rules

Any of the following conditions, if present, renders the verdict `FAIL`, and
execution MUST NOT proceed:

- An in-scope repository has uncommitted or untracked changes the consumer
  has not explicitly declared tolerated (see the framework's scope-guard
  discipline, `tools/verify_lib.sh`'s `vlib_scope_guard`, for the mechanism
  this rule builds on).
- A required baseline, evidence, or planning reference the preflight depends
  on is missing, unreadable, or does not resolve to an existing path.
- A prior execution's recorded findings include an unresolved P0 defect that
  the consumer has not registered as accepted risk (human gate `H-RISK`; the
  framework never accepts risk on a human's behalf).
- Any consumer-registered, repository-specific blocking condition the
  consumer has declared in its own preflight configuration.

A blocking condition is never silently downgraded to a non-blocking finding
by the preflight tool itself; only an explicit, recorded operator decision
(Section 5, or a superseding human risk-acceptance under `H-RISK`) changes
how a finding is treated in a later run.

### 4.1 Committing Gate-Decision State Before the Preflight

The first blocking rule above has a direct operational corollary for the
Orchestrator. Because any uncommitted change to a *tracked* file is
unconditionally blocking, and no `--tolerate-untracked` declaration can rescue
a tracked-file modification (that mechanism governs untracked files only), an
orchestrator-owned tracked-state write that is relevant to a gate decision --
for example an `operator_gate_decision` (or equivalent) event appended to
`run_state.json` before an approved, gated step -- MUST be committed before the
corresponding gated CLI invocation runs. Left uncommitted, that write is
itself a blocking finding, so the preflight will correctly and unavoidably
`FAIL` on the very state change that was meant to authorize the step.

This rule binds durably, by this document rather than by any per-dispatch
instruction. It was learned from feature 043's real self-dogfood run, where the
orchestrator's `H-DOGFOOD-EXCEPTION` gate-decision write to `run_state.json`
first landed as an uncommitted tracked modification: the approved invocation
genuinely `FAIL`ed (exit 1, `uncommitted tracked change (M):
.agent/run_state.json`) and only succeeded once that write was committed. The
sequence is therefore fixed -- record the gate decision in durable state,
commit it, and only then run the gated preflight invocation.

## 5. Operator-Exception Rule

`PASS_WITH_EXCEPTIONS` requires explicit operator approval before execution continues.
A preflight run that would otherwise return `PASS_WITH_EXCEPTIONS` MUST halt
and record the pending exceptions in the verdict artifact (Section 6); it
MUST NOT proceed to Baseline, Audit, Plan, or Execute until an operator has
reviewed the recorded exceptions and recorded a structured approval decision
alongside them.

No execution train starts from a `FAIL` verdict, and no execution train
continues past a recorded, unapproved `PASS_WITH_EXCEPTIONS` verdict. Once
approved, the operator's decision (identity, timestamp, and the specific
exceptions accepted) is recorded in the same verdict artifact the preflight
tool produced -- never as a separate, unlinked record -- so a later Audit or
Compare step can trace exactly which exceptions were accepted, by whom, and
against which findings.

## 6. Verdict Artifact

Every preflight run MUST emit a schema-valid, machine-readable verdict
artifact at:

```text
.agent/reconciliation/<execution-id>/preflight.json
```

where `<execution-id>` is the unique identifier of the ecosystem-cycle
execution the preflight run belongs to, per the framework's Artifact
Locations convention (`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`).
The artifact's shape (the exact three-verdict enum and the structured
operator-approval fields `PASS_WITH_EXCEPTIONS` requires) is defined by
`schema/preflight_verdict.schema.json`. This protocol governs the artifact's
required semantics; it does not itself define the JSON Schema.

Schema-validity binds the artifact once it is final. A verdict artifact is
final when it records `PASS`, `FAIL`, or `PASS_WITH_EXCEPTIONS` together with
the structured operator-approval decision Section 5 requires. A run that halts
pending operator approval (Section 5) does not yet emit `preflight.json`: it
records the pending exceptions in an informational pending artifact alongside
the eventual artifact location — the shipped preflight CLI
(`tools/ecosystem_preflight.py`) writes `preflight.pending.json`, deliberately
non-schema-conformant, and withholds `preflight.json` entirely — and the
schema-valid `preflight.json` is emitted only once the operator's decision is
folded in. That a pre-approval `PASS_WITH_EXCEPTIONS` state is unrepresentable
as a schema-valid `preflight.json` is by design, not accident: the schema's
required `operator_approval` block is the mechanism that makes an unapproved
exception set impossible to mistake for an approved one.

Evidence backing the verdict (raw tool output, logs, or intermediate checks)
is externalised by path under `.agent/evidence/<execution-id>/`, per the
framework's Evidence Capture Convention
(`methodology/04_tool_driven_state.md` Section 5) — never pasted inline into
the verdict artifact or into a chat transcript.

## 7. References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` — the accepted NIP
  defining the Preflight Verdict, Artifact Locations, and Dogfood
  Requirement this protocol implements.
- `ecosystem/README.md` — the module index and canonical lifecycle this
  protocol is one step of.
- `methodology/04_tool_driven_state.md` — the Evidence Capture Convention
  this protocol's evidence externalisation follows.
- `methodology/03_circuit_breaker.md` — the house pattern this document's
  structure and tone follow.
- `schema/preflight_verdict.schema.json` — the machine-readable schema for
  the verdict artifact this protocol requires.
