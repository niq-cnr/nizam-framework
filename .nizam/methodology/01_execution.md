---
id: nizam-contract-first-execution
title: "Contract-First Harness Loop"
description: "The authoritative execution protocol: the two-loop state machine driving pre-code contract alignment and post-code implementation repair, the JSON Verdict Parse Rule, and the evidence-capture gate required before completion."
version: 0.2.0
status: active
authoritative_source: methodology/01_execution.md
change_log:
  - version: "0.2.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 correction: a passing QA verdict no longer advances directly to complete. A distinct evidence-capture gate verifies referenced .agent/evidence files exist and record each required command/result before the Orchestrator may update lifecycle state."
---

# Contract-First Harness Loop

## 1. Overview

Once `00_planning.md` has produced an eligible, dependency-cleared feature, that
feature is driven through a two-loop state machine before it is considered
complete. Loop 1 aligns on *what* will be built, before any code exists. Loop 2
verifies *what was built* matches what was aligned on. Neither loop may be
skipped, collapsed, or reordered.

This protocol is coordinated by the **Orchestrator** and governs the interaction
between the **Generator**, **Validator**, and **Evaluator** roles defined in
`standard/AGF.md` Section 2. It is bound by the Dual Validator Gate defined in
that document's Section 3; the Planner's eligible feature is its input.

## 2. Loop 1 — Pre-Code Alignment

```text
Generator proposes contract (status: "proposed")
        |
        v
Validator Mode A  (pre-code contract gate, standard/AGF.md Sec 3)
        |
        v
Evaluator contract review (independent second read of the same contract)
        |
        v
   Both approve?  --No--> Generator revises contract --> back to Validator Mode A
        |                  (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Contract status -> "approved". Loop 1 ends. Loop 2 begins.
```

A contract entering Loop 1 MUST declare, at minimum: the files it will create or
modify, its non-goals (explicit statements of what it does NOT authorize), its
verification commands (one per acceptance test it satisfies), an estimated line
count, and an evidence directory/convention (`schema/contract.schema.json`). A
proposal missing any of these is incomplete and cannot reach `approved` status.

**No implementation before approval.** A Generator MUST NOT write source code
against a contract whose `status` is anything other than `"approved"`. This is
the single most important rule in this protocol — every other gate exists to
protect it.

## 3. Loop 2 — Post-Code Repair

```text
Generator implements the approved contract's scope ONLY
        |
        v
Validator Mode B  (post-code implementation gate, standard/AGF.md Sec 3)
   - runs a diff against the pre-implementation state
   - confirms every contracted deliverable is present
   - confirms ONLY contracted files were touched
   - confirms no scope crept in beyond the contract
        |
        v
   Approved?  --No--> Generator reworks with the rejection's failure report
        |               (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Evaluator executes the contract's verification commands independently
   -> QA verdict (.agent/qa/NNN.json, pass/fail + evidence)
        |
        v
   Verdict == pass?  --No--> Generator reworks with the QA failure report
        |                     (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Evidence capture gate
   - every required verification has an externalised evidence file
   - the QA verdict references those paths and every path exists
   - command/result and actual exit status are recorded
        |
        v
   Complete?  --No--> Generator/Orchestrator repairs the evidence record
        |              (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Durable state advances: feature marked complete, next eligible feature selected
per the Dependency Enforcement Rule (00_planning.md Sec 5).
```

A Generator implementing Loop 2 MUST implement only the contracted scope. If,
during implementation, the Generator discovers the contract itself needs to
change (a missed file, an incorrect deliverable), it MUST stop and propose a
contract revision — re-entering Loop 1 — rather than silently expanding scope
under cover of "finishing the job."

**Evidence is a completion gate, not post-processing.** A passing QA JSON block
proves the Evaluator's decision, but the feature remains `in_progress` until the
Orchestrator verifies that every contracted verification has a corresponding
externalised file under `.agent/evidence/`, that the QA verdict references those
paths, and that each referenced path exists and records the command/result plus
the actual exit status. Missing or unreferenced evidence is a Loop 2 failure and
uses the same bounded repair loop; it is never filled in after the feature is
marked complete.

## 4. The JSON Verdict Parse Rule

Every gate in both loops above — Validator Mode A, Validator Mode B, the
Evaluator's contract review, and the Evaluator's QA verdict — culminates in a
machine-parseable JSON verdict block. Advancement past that gate is permitted
**only** when all four conditions hold simultaneously:

```text
final_verdict.approved === true
AND issues.length === 0
AND missing_acceptance_coverage.length === 0
AND unsupported_claims.length === 0
```

This is restated here, not redefined — `standard/AGF.md` Section 4 is
authoritative for the rule itself. The load-bearing consequence for this
protocol is: **prose framing never substitutes for the JSON block.** A report
that reads "mostly approved, one minor note" is a rejection if its JSON verdict
carries a non-empty `issues` array. An orchestrator or Generator reading a gate
result MUST parse only the JSON block to decide whether to advance.

## 5. Circuit Breaker Cross-Reference

Both loops above contain a step that can fail and be retried: Loop 1's "Generator
revises contract" step, and Loop 2's "Generator reworks" step (twice — once for a
Mode B rejection, once for a QA failure). Every one of these repeatable steps is
bound by the **same** mandatory 3-strike circuit breaker.

This protocol does not restate the breaker's internal mechanics (the per-attempt
strategy, the halt procedure, or where its counters live) — those are
authoritatively defined in `03_circuit_breaker.md`. What this protocol commits
to is narrower and non-negotiable: **no revision loop or rework loop in either
Loop 1 or Loop 2 above may exceed the attempt limit `03_circuit_breaker.md`
defines, under any circumstance.** A fourth attempt at any single named step in
this document is forbidden by that document and by extension forbidden here.

## 6. Handoff Out

When Loop 2 has both a passing QA verdict **and** a passing evidence-capture
gate, the Orchestrator updates durable state (`04_tool_driven_state.md`) to
reflect completion. Control then returns to `00_planning.md` Section 5 (the
Dependency Enforcement Rule) to select the next eligible feature.

## 7. References

- `standard/AGF.md` — the agent roles (the coordinating Orchestrator and the
  four execution roles), the Dual Validator Gate, and the authoritative
  definition of the JSON Verdict Parse Rule.
- `00_planning.md` — produces the eligible feature this loop consumes, and
  receives control back on completion via the Dependency Enforcement Rule.
- `02_adversarial_tdd.md` — the independence and rigor requirements binding the
  Evaluator's contract review and QA verdict steps above.
- `03_circuit_breaker.md` — the 3-strike limit bounding every revision and
  rework step named in Sections 2, 3, and 5 of this document.
- `04_tool_driven_state.md` — the durable-state artifacts (contracts, QA
  verdicts, run state) this loop reads from and writes to at every stage.
