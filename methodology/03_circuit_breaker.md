---
id: nizam-circuit-breaker
title: "Universal Circuit Breaker (DD-2)"
description: "The single authoritative 3-strike attempt limit embedded by every repeatable execution loop: isolated attempt workspaces, escalating strategies, the forbidden fourth attempt, and canonical-state halt/escalation."
version: 0.4.0
status: active
authoritative_source: methodology/03_circuit_breaker.md
change_log:
  - version: "0.4.0"
    date: "2026-10-15"
    summary: "Clarify evidenced cause routing with failed outcomes and unchanged max3 continuity."
  - version: "0.3.0"
    date: "2026-10-11"
    summary: "Define governed attempts and predeclared probes with non-resetting cross-stage identity."
  - version: "0.2.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 safety repair: every attempt runs in an isolated worktree/snapshot from the last approved base; failure cleanup removes only that validated attempt root after evidence capture. The phase document is canonical and run_state is repaired idempotently as derived state, replacing the impossible cross-file atomic-write claim; the escalation cross-reference now points to Section 4 step 4."
---

# Universal Circuit Breaker (DD-2)

## 1. Overview

This document is the single source of truth for the framework's mandatory
3-strike / three-attempt limit — Design Decision DD-2, remediating the
"infinite loop" failure mode where an agent retries a failing step indefinitely
without ever escalating. Every execution loop that can repeat a step on failure
— contract revision, implementation rework, or any other repair cycle defined
elsewhere in this framework — embeds this exact limit. No document elsewhere in
the framework restates or redefines these mechanics; they cross-reference this
one by path.

## 2. Scope: Every Repeatable Loop, No Exceptions

This breaker applies uniformly to every step in the framework capable of being
retried after a failure, including but not limited to:

- Loop 1 contract revisions (`01_execution.md` Section 2) — a Generator revising
  a proposed contract after Validator Mode A or Evaluator rejection.
- Loop 2 implementation reworks (`01_execution.md` Section 3) — a Generator
  reworking code after a Validator Mode B rejection, or after a failing QA
  verdict.
- Any subagent retry a pipeline performs after a malformed or empty subagent
  response.

A step not explicitly named above is not exempt by omission — "any single,
repeatable step" is the governing scope, not an enumerated allowlist.

## 3. The Per-Attempt Strategy Table

Each attempt at a failing step MUST follow an escalating strategy. An agent
MUST NOT repeat the same diagnostic approach across attempts — each attempt
number below prescribes a materially different investigative posture:

| Attempt | Strategy |
|---|---|
| **1** | **Direct fix.** Read the exact error output. Fix the specific line or command it identifies. Assume the defect is local and mechanical. |
| **2** | **Type/interface analysis.** If the direct fix did not resolve the failure, step back and check for a structural mismatch — a type signature, an interface contract, a schema shape, or an assumption about another component's output that does not actually hold. |
| **3** | **Architectural review.** If the failure persists after a structural fix attempt, question the approach itself. Consider whether the chosen implementation strategy, not merely its details, is what needs to change. |
| **4+** | **FORBIDDEN.** No fourth attempt at the same step is permitted, regardless of how promising a new idea seems. See Section 4. |

Skipping a strategy tier (for example, attempting an architectural rewrite on
attempt 1 without first trying the direct fix) is itself a protocol violation —
the escalating order exists so that cheap, likely fixes are exhausted before
expensive, uncertain ones are attempted.

### 3.1 Attempt isolation

Every attempt MUST start from the last approved immutable base in its own
attempt-scoped workspace. In Git, use a detached worktree at a newly-created,
validated temporary path (conceptually `git worktree add --detach
<attempt-worktree> <approved-commit>`); a non-Git system uses an equivalent
copy-on-write snapshot. Never run a retry in the shared developer worktree.

The attempt root and approved base are recorded before edits begin. A failed
attempt's evidence is captured from that root and then only that exact root is
removed through the worktree/snapshot manager. A successful attempt's reviewed
diff or commit is the only material promoted back to the feature branch. The
shared tree is never recovered with repository-wide reset or clean commands.

### 3.2 What counts as an attempt

A governed attempt is one execution of a repeatable contracted step, identified
by the stable tuple `contract_id`, `step_key` and `attempt`. Its classification,
expected outcome and budget treatment MUST be declared before execution. A
negative acceptance test within that execution can succeed by producing its
predeclared expected rejection; an infrastructure failure remains a failure.

An explicitly declared diagnostic probe is distinct from a governed attempt:
its purpose, expected negative outcome and budget classification are recorded
before it runs. A probe investigates a condition without delivering a repair.
A failed repair MUST NOT be relabeled as a probe after its outcome is known,
and a probe cannot deliver an uncounted repair or supply a new attempt budget.

A new process, subagent, agent session, context reset, worktree, process
generation, operation rename or stage handoff MUST NOT reset an existing
counter. The same repair keeps its contract_id, step_key and attempt through
those boundaries. Independently defined governed steps retain their own
canonical counters; changing the stage name does not create a distinct step.

The Orchestrator alone owns coordination and circuit counters; implementation
agents read the current identity and preserve those fields. This definition
changes neither Section 3's strategy ladder nor the three-attempt limit,
isolation, cleanup or halt duties. Runtime continuity is specified in
`10_live_runtime_sessions.md`; it creates no extra cause-specific retry budget.

### 3.3 Evidence-based cause routing

A selected infrastructure or semantic failure MUST retain its failed outcome and
stable contract, step and allocated attempt identity. The Orchestrator selects
immutable classification and actual wrapper-capture evidence; labels and hashes
bind that evidence but do not authenticate its truth. Missing or inconsistent
proof fails closed. A successful nested expected-negative control cannot make a
failed outer wrapper successful or retroactively turn a repair into a probe.

The optional `route_failed_attempt` library proposes infrastructure diagnosis or
semantic repair for allocated attempts one and two, and halt for attempt three.
It neither executes nor authorizes a retry. The strategy ladder, three-attempt
limit, isolation and Section 4 escalation duties remain binding for either cause.
A handoff preserves counters, budgets and prior history; process, agent, session,
generation or stage changes create no additional cause-specific allowance.

## 4. Attempt 4 Is Forbidden — The Breach Procedure

If a step's third attempt (per Section 3's table) also fails, the circuit
breaker has tripped. The acting agent MUST, in order:

1. **Capture and quarantine the third attempt.** Write its diagnostics, diff,
   and exact attempt-root/base identifiers under `.agent/evidence/`. Then ask
   the worktree or snapshot manager to remove **only that validated attempt
   root**. No shared-worktree reset, repository clean, glob, or broad path is
   permitted. If the root cannot be proved attempt-owned, leave it in place,
   record it, and escalate rather than guessing at cleanup.
2. **Set the canonical step status to `BLOCKED`, then repair derived state.**
   The phase document's step-level `status` field, per
   `schema/phase.schema.json`, is the lifecycle source of truth and is written
   first. `.agent/run_state.json` is coordination state derived from that
   canonical value and is updated in a separate, idempotent operation. If the
   files disagree, execution halts; rebuild the derived entry from the phase
   document and validate both artifacts before continuing. The protocol never
   claims two files share one atomic filesystem write.
3. **Log the failure** to the technical-debt register (conventionally
   `docs/planning/DEBT.md`), naming at minimum: the phase, the feature, the
   failure type, and a reference to the last attempt's response or evidence
   file.
4. **Escalate to a human and terminate.** The agent stops. Autonomous
   continuation past a third failed attempt on any single step is never
   permitted, under any framing ("just one more try," "I think I see it now")
   — that framing is precisely what this document exists to override.

Attempt 4 is not a slower, more cautious version of attempts 1-3. It is not
permitted to occur at all.

## 5. Where Breaker State Lives

Every in-flight attempt counter is tracked in `.agent/run_state.json`'s
`circuit_breaker` object (`schema/run_state.schema.json`), keyed by a
step-identifying string (for example `"001-implementation"` or
`"002-contract"`), each holding:

```json
{
  "circuit_breaker": {
    "<step-key>": {
      "attempts": 2,
      "limit": 3
    }
  }
}
```

An agent beginning any retryable step MUST first reconcile this derived object
with the canonical phase step, then read the counter to determine which attempt
it is about to make. It MUST increment the relevant counter idempotently after
each attempt concludes (success or failure). If reconciliation cannot prove the
derived entry corresponds to the canonical step, the pipeline halts and rebuilds
it before another attempt. An agent that begins a fourth attempt without having
respected this counter has violated Section 4 regardless of its outcome.

## 6. Escalation Protocol

Escalation (Section 4, step 4) means the pipeline halts and a human reviewer is
notified — it does not mean the pipeline silently proceeds to the next feature
while marking the blocked one aside for "later." A `BLOCKED` feature remains
blocked until a human either:

- Provides a corrected approach or additional context that resolves the
  underlying defect, after which the step may be attempted fresh (resetting the
  attempt counter to 0), or
- Explicitly authorizes cancelling or descoping the feature, after which its
  status moves to `cancelled` (which, per the Dependency Enforcement Rule in
  `00_planning.md` Section 5, satisfies any downstream feature that depended on
  it, exactly as `complete` would).

No agent may unilaterally decide a `BLOCKED` feature should be silently skipped
or reattempted without one of the two human actions above.

## 7. References

- `01_execution.md` — names every contract-revision and implementation-rework
  loop this breaker bounds.
- `00_planning.md` Section 5 — the Dependency Enforcement Rule that governs how
  a `BLOCKED` or `cancelled` feature affects downstream feature eligibility.
- `schema/run_state.schema.json` — the structural definition of the
  `circuit_breaker` object referenced in Section 5.
- `schema/phase.schema.json` — the step-level `status` enum (including
  `BLOCKED`) a phase document's steps carry.
