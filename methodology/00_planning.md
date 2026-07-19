---
id: nizam-planning-enforcer
title: "Planning Enforcer"
description: "The mandatory pre-code planning protocol: the spec + feature-DAG artifact pair every phase must produce before implementation begins, the dependency enforcement rule, atomic-step decomposition, and the scope budget protocol."
version: 0.2.1
status: active
authoritative_source: methodology/00_planning.md
change_log:
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Add the Plan Amendment Rule (Section 9), covering orchestrator-registrable amendments, Planner-routed re-planning, and scope-budget re-baselines."
  - version: "0.2.1"
    date: "2026-07-19"
    summary: "Documentation-truth sync (F-053/NDEBT-010): the Section 7 reference to standard/AGF.md no longer describes it as 'the four agent roles' — AGF Section 2 now defines a coordinating Orchestrator plus the four execution roles. Section 6's scope-budget protocol now names the Orchestrator as the sole writer of the scope_budget coordination field (AGF Section 5 rule 4), with an evaluator supplying only the raw measurement — resolving a PR #32 review conflict where 'the orchestrator or evaluator' both appeared to write durable state."
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

```text
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

After each Generator implementation, the **Orchestrator** compares the actual
lines changed for that feature against two thresholds, both tracked in
`.agent/run_state.json`'s `scope_budget` object (an evaluator may supply the raw
line-count measurement, but `scope_budget` is an Orchestrator-owned coordination
field — `standard/AGF.md` Section 5 rule 4 — so the Orchestrator is its sole
writer):

1. **Per-feature check.** If the lines changed for the just-completed feature
   exceed **3× the rolling average** of the actual lines changed for the last
   three completed features, the feature is flagged. A flag does not halt the
   pipeline by itself — it requires an explicit human acknowledgment recorded
   before the next feature begins, so that scope creep is visible rather than
   silently absorbed. When fewer than three features have completed, the
   rolling average is computed over however many completed features actually
   exist rather than assumed to be three. The very first completed feature has
   no rolling baseline at all and cannot be flagged by this check — it is only
   subject to its own `estimated_lines` figure and to the cumulative check
   below.
2. **Cumulative check.** If the running total of lines changed across the whole
   phase exceeds **130% of the phase's `original_estimate_lines`**, the pipeline
   MUST HALT, log the overrun to the technical-debt register, and require
   explicit human authorization before any further feature is started. This is
   a hard gate, not a flag — a phase that has grown 30% beyond its planned size
   has outgrown its original plan and needs a human decision, not an assumption
   that the plan still holds.

Both checks operate on the same `scope_budget.per_feature` array and
`scope_budget.total_lines_changed` field that `schema/run_state.schema.json`
declares — read by the check, written back only by the Orchestrator (Section 5
rule 4) — with no parallel or duplicate tracking structure introduced.

## 7. Handoff

Once a feature list has passed DAG validation (Section 3) and the Dependency
Enforcement Rule (Section 5) has selected an eligible feature, planning's
responsibility for that feature ends. Control passes to the contract-first
harness loop defined in `01_execution.md`, beginning with the Generator's
contract proposal.

## 9. The Plan Amendment Rule

A phase's plan, once established via Sections 2-3, is not immutable, but
changing it after the fact follows a strict division of authority between
the orchestrator's own registration power and the Planner role.

**Orchestrator-registrable amendments.** A post-phase or in-phase amendment
that has been **explicitly authorized by a human** may be registered
directly by the orchestrator as a new or modified feature in
`feature_list.json`, PROVIDED the authorization cites a recorded
authorization event already present in `run_state.json`'s `history` log — an
actual entry the orchestrator can point to, not a paraphrase or a
recollection of a conversation. This is the orchestrator's own registration
power and does not require routing the amendment through the Planner.

**Substantive re-planning routes to the Planner.** By contrast, any
amendment that introduces scope the human's authorization did not directly
specify — a new architecture, a new acceptance-test shape, or anything the
orchestrator would otherwise have to invent to fill in the amendment's
details — MUST route through the Planner role. The orchestrator's
registration power covers recording what a human has already decided; it
does not extend to deciding new plan content on the human's behalf.

**Scope-budget re-baselines follow the identical pattern.** When a human
authorizes raising `original_estimate_lines` or the cumulative ceiling
(Section 6's cumulative check), that re-baseline is human-authorized and
orchestrator-recorded exactly like any other amendment — and it MUST be
recorded structurally in the `scope_budget` object itself (a `rebaseline`
record naming `from`, `to`, `authorized_by`, and `at`, plus a `reason`), not
left as free-text history prose alone. Free-text history is a useful
narrative trail, but the structural record is what a downstream role or a
future audit actually reads.

## 10. References

- `standard/AGF.md` — the agent roles (the coordinating Orchestrator and the
  four execution roles, including Planner) and the dual validator gate this
  protocol's output feeds into.
- `01_execution.md` — the harness loop that consumes an eligible, planned feature.
- `03_circuit_breaker.md` — the 3-strike limit that bounds contract-revision and
  implementation-rework loops downstream of planning.
