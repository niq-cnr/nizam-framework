---
id: nizam-planning-enforcer
title: "Planning Enforcer"
description: "The mandatory pre-code planning protocol: the spec + feature-DAG artifact pair every phase must produce before implementation begins, the dependency enforcement rule, atomic-step decomposition, and the scope budget protocol."
version: 0.1.0
status: active
authoritative_source: nizam-framework/methodology/00_planning.md
---

# Planning Enforcer

## 1. Overview

No implementation work may begin against a phase that has not first produced a
verifiable plan. The Planning Enforcer is the runtime-agnostic protocol that makes
this mandatory: it defines the artifact pair every phase must produce, the shape
those artifacts must take, and the rules that gate a feature from `pending` to
implementable.

This protocol governs the **Planner** role defined in `standard/AGF.md` Section 2.
It hands off to the harness loop defined in `01_execution.md`.

## 2. The Mandatory Pre-Code Artifact Pair

Before any Generator begins work on any feature in a phase, the Planner MUST have
produced, and committed to durable state, both of the following:

1. **A specification document** (conventionally `.agent/product_spec.md`) — the
   architecture, module boundaries, and phase-level acceptance criteria a human or
   agent can read to understand *why* the phase exists and what "done" means at the
   phase level.
2. **A feature list** (conventionally `.agent/feature_list.json`) — the phase
   decomposed into individually implementable features, each carrying an explicit
   `dependencies` array and a set of atomic `acceptance_tests` (Section 4).

A phase with only one of the two artifacts is not planned. A Generator or
orchestrator that begins implementation work against a phase lacking either
artifact is in violation of this protocol, independent of how confident it is
about the missing artifact's likely content.

## 3. The Feature List as a Directed Acyclic Graph

Every feature in a feature list carries an explicit `dependencies` array naming
zero or more other feature ids in the same list. Treated together, the feature
list forms a directed graph, and that graph MUST be acyclic.

### 3.1 Validation at Planning Time

Before a feature list is accepted as planned, it MUST be validated against both of
the following, and REJECTED if either fails:

1. **No dangling references.** Every id named in any feature's `dependencies`
   array MUST correspond to another feature actually present in the same list. A
   dependency referencing a non-existent feature id is a planning defect, not a
   runtime concern to be discovered later.
2. **No cycles.** The dependency graph, taken as a whole, MUST admit at least one
   valid topological ordering. A feature list containing a cycle (directly, e.g.
   A depends on B and B depends on A, or transitively through a longer chain)
   MUST be rejected and returned to the Planner for revision before any feature in
   it is handed to a Generator.

A feature list that fails either check is not planned; it is a draft with a
defect, and the pipeline treats it accordingly (reject, revise, re-validate) —
it is never patched around at execution time.

## 4. Atomic-Step Decomposition

Each feature's `acceptance_tests` array MUST consist of concrete, independently
runnable commands or checks — a shell invocation, a script, a grep, a schema
validation call — never a vague prose goal such as "the module works correctly"
or "documentation is updated as appropriate."

**Rationale:** A later Validator or Evaluator gate (`standard/AGF.md` Section 3)
needs a verifiable-truth anchor, not a subjective judgement call. An acceptance
test phrased as a runnable command produces a deterministic exit code that any
agent — or any human — can re-execute and get the same answer from. A prose goal
produces only an opinion, and opinions are exactly what the dual validator gate
and the JSON Verdict Parse Rule (`standard/AGF.md` Section 4) exist to route
around.

An acceptance test is atomic when it tests exactly one verifiable fact. A
feature's acceptance test list SHOULD be decomposed until every entry meets this
bar, rather than left as a small number of compound checks that can pass or fail
for entangled reasons.

## 5. The Dependency Enforcement Rule

Before any feature is handed from planning to implementation (i.e. before a
Generator is asked to propose a contract for it), the following gate algorithm
MUST be applied:

```
For the next feature with status "pending":
  1. Read its "dependencies" array.
  2. For each dependency id in that array, resolve its current status:
     - status is "complete" or "cancelled"  -> this dependency is satisfied
     - status is anything else (pending, in_progress, blocked) -> NOT satisfied
  3. If ALL dependencies are satisfied -> this feature is eligible; proceed.
  4. If ANY dependency is NOT satisfied -> skip this feature; check the next
     "pending" feature in the list.
  5. If no "pending" feature in the entire list has all dependencies satisfied
     -> DEADLOCK. Log the deadlock (naming the blocking feature(s) and their
        unsatisfied dependencies) to the technical-debt register, halt the
        pipeline, and escalate to a human. Do not guess at a resolution and do
        not silently skip the phase.
```

This rule is a hard gate, not a heuristic. A feature whose dependencies are not
yet complete or cancelled MUST NOT be started, even if a Generator or
orchestrator believes the work is safe to begin early. "Believes it is safe" is
exactly the judgement call this rule exists to remove.

### 5.1 Deadlock Is Not a Retry Condition

A deadlock detected by step 5 above is not resolved by waiting and re-checking —
if no dependency's status is expected to change without human or upstream-agent
action, re-polling the same graph produces the same deadlock. Deadlock is a
planning-time or execution-time defect (a genuine cycle that slipped past Section
3's validation, or a dependency that is itself permanently blocked) and is
escalated, not retried in a loop.

## 6. Scope Budget Protocol

Planning also produces a per-feature `estimated_lines` figure (recorded in the
feature list and echoed into each feature's contract, `01_execution.md` Section
2) and a phase-level `original_estimate_lines` total. These estimates are the
baseline the Scope Budget Protocol checks actual implementation against, once
work begins.

After each Generator implementation, the orchestrator or evaluator compares the
actual lines changed for that feature against two thresholds, both tracked in
`.agent/run_state.json`'s `scope_budget` object:

1. **Per-feature check.** If the lines changed for the just-completed feature
   exceed **3× the rolling average** of the actual lines changed for the last
   three completed features, the feature is flagged. A flag does not halt the
   pipeline by itself — it requires an explicit human acknowledgment recorded
   before the next feature begins, so that scope creep is visible rather than
   silently absorbed.
2. **Cumulative check.** If the running total of lines changed across the whole
   phase exceeds **130% of the phase's `original_estimate_lines`**, the pipeline
   MUST HALT, log the overrun to the technical-debt register, and require
   explicit human authorization before any further feature is started. This is
   a hard gate, not a flag — a phase that has grown 30% beyond its planned size
   has outgrown its original plan and needs a human decision, not an assumption
   that the plan still holds.

Both checks read and write the same `scope_budget.per_feature` array and
`scope_budget.total_lines_changed` field that `schema/run_state.schema.json`
declares; no parallel or duplicate tracking structure is introduced.

## 7. Handoff

Once a feature list has passed DAG validation (Section 3) and the Dependency
Enforcement Rule (Section 5) has selected an eligible feature, planning's
responsibility for that feature ends. Control passes to the contract-first
harness loop defined in `01_execution.md`, beginning with the Generator's
contract proposal.

## 8. References

- `standard/AGF.md` — the four agent roles (including Planner) and the dual
  validator gate this protocol's output feeds into.
- `01_execution.md` — the harness loop that consumes an eligible, planned feature.
- `03_circuit_breaker.md` — the 3-strike limit that bounds contract-revision and
  implementation-rework loops downstream of planning.
