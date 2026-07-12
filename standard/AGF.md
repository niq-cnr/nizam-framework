---
id: agent-governance-framework
title: "Agent Governance Framework (AGF)"
description: "The generalised multi-agent execution model: agent roles, the dual validator gate, the JSON verdict parse rule, and the durable-state rule for agent coordination."
version: 0.1.1
status: active
authoritative_source: standard/AGF.md
change_log:
  - version: "0.1.1"
    date: "2026-07-12"
    summary: "Documentation-truth cleanup: Section 6's circuit-breaker cross-reference now names methodology/03_circuit_breaker.md (shipped at genesis; the 'forthcoming' wording was stale), and the Section 4 verdict rule's dropped word is restored ('entry in any of the three arrays blocks advancement')."
---

# Agent Governance Framework (AGF)

## 1. Overview

The AGF defines a runtime-agnostic execution model for coordinating multiple AI agents
against a shared, contract-first delivery pipeline. It is deliberately silent on any
specific agent runtime, tool-calling API, or orchestration harness — any runtime that can
route work between four role types and honour the gates below is compliant.

## 2. The Four Agent Roles

Every execution pipeline governed by this framework is composed of four roles. A single
agent implementation MAY embody more than one role across different sessions, but a
single session MUST NOT blend roles in a way that lets one role bypass another's gate.

| Role | Responsibility | Typical Output |
|---|---|---|
| **Planner** | Expands a brief or request into product-level artifacts: an architecture/spec document and a feature list with acceptance criteria. Stays at high-level architecture; does not lock in low-level implementation detail. | A specification document, a feature list. |
| **Generator** | Proposes an implementation contract for a feature, then — once the contract is approved — implements only that contract's scope. Never expands scope silently. | A proposed contract; source code changes matching an approved contract. |
| **Validator** | Gatekeeps the pipeline at two points (Section 3): before code is written (Mode A) and after (Mode B). Does not write source code or repair contracts; it approves or rejects. | A JSON verdict (Section 4). |
| **Evaluator** | Executes the verification plan (tests, checks) against the implementation and independently confirms pass/fail with evidence. | A pass/fail verdict with required fixes on failure. |

## 3. The Dual Validator Gate

The validator operates in exactly two modes, and both are mandatory — a pipeline that
skips either mode is non-compliant.

### Mode A — Pre-Code Contract Gate

- **Trigger:** A Generator has proposed a contract (`status: "proposed"`). No
  implementation exists yet.
- **Purpose:** Confirm the contract is a complete, bounded, testable, and traceable
  translation of the specification — every deliverable maps to an explicit requirement,
  every acceptance criterion is covered by a verification step, no scope is invented, and
  no ambiguity is left for the Generator to guess at.
- **Output required before proceeding:** An approved contract. Implementation MUST NOT
  begin before a contract's status is `approved`.

### Mode B — Post-Code Implementation Gate

- **Trigger:** A Generator has completed implementation against an approved contract
  (`status: "approved"`), and the validator is instructed to inspect the resulting
  change set (e.g. via a diff against the pre-implementation state).
- **Purpose:** Confirm the implementation matches the approved contract exactly — every
  contracted deliverable is present, only contracted files were touched, every promised
  verification step exists, no unapproved dependencies or scope crept in, and nothing is
  a stub or placeholder.
- **Output required before proceeding:** An approved implementation. The pipeline MUST
  NOT hand off to the Evaluator's final verdict, nor may the orchestrator advance to the
  next feature, before Mode B approval.

Both modes are gatekeeping functions, not collaborative ones: a validator does not repair
a contract or an implementation, invent missing requirements, soften a discrepancy, or
approve on the basis of "mostly correct." Ambiguity is treated as a rejection reason, not
a warning.

## 4. The JSON Verdict Parse Rule

Every validator and evaluator decision that gates pipeline progression MUST culminate in
a single, machine-parseable JSON verdict block, in addition to any prose report. The
orchestrator (or any automated caller) advances to the next pipeline stage **only when
all four of the following hold simultaneously**:

```text
final_verdict.approved === true
AND issues.length === 0
AND missing_acceptance_coverage.length === 0
AND unsupported_claims.length === 0
```

A verdict block satisfying all four conditions above looks like this:

```json
{"final_verdict": {"approved": true}, "issues": [], "missing_acceptance_coverage": [], "unsupported_claims": []}
```

Rules for applying this gate:

1. **Parse only the JSON verdict block.** Prose framing — including language like
   "mostly approved," "approved with minor notes," or "should be fine" — MUST NOT be used
   to infer approval. If the JSON block does not independently satisfy all four
   conditions above, the result is a rejection, regardless of surrounding prose tone.
2. **Empty arrays are load-bearing.** `issues`, `missing_acceptance_coverage`, and
   `unsupported_claims` are not advisory fields; each is a hard gate. A single non-empty
   entry in any of the three arrays blocks advancement even if `approved` is `true`.
3. **No inferred approval.** An orchestrator or calling agent MUST NOT synthesize an
   `approved: true` verdict on a validator's behalf from an incomplete or malformed
   response. A missing or malformed verdict block is treated as a rejection and triggers
   the failure-handling procedure the pipeline defines for malformed subagent output.

## 5. The Durable State Rule (No Oral Tradition)

Agents operating under this framework MUST communicate results exclusively through
durable, file-based state — never through chat history, conversational memory, or any
other channel that is not independently readable by the next agent in the pipeline.

1. **Every material result is written to a file.** Specifications, feature lists,
   contracts, verdicts, and run-position state each have a canonical durable location
   (conventionally under a project's `.agent/` directory, or an equivalent
   framework-declared location) that any subsequent agent can read without depending on
   the conversation that produced it.
2. **Chat is not state.** A result that exists only as prose in an agent's response, and
   is never written to its durable location, MUST be treated as not having happened. A
   later agent or orchestrator MUST NOT act on a claimed result it cannot independently
   read from durable state.
3. **State is the handoff mechanism.** When one role hands off to the next (Planner to
   Generator, Generator to Validator, Validator to Evaluator), the receiving role's first
   action is to read the current durable state, not to trust a summary passed along in
   conversation.
4. **Preserve, don't overwrite blindly.** Updates to durable state MUST preserve fields
   the current step did not own or change; a role updates only the fields its contract or
   protocol assigns to it.

## 6. Circuit Breaker Cross-Reference

Every execution loop governed by this framework embeds a mandatory circuit breaker
limiting self-correction attempts on any single step, so that repeated failures halt for
human review rather than looping indefinitely. The full 3-strike protocol — attempt
strategy per strike, the halt procedure, and required state updates on trigger — is
defined in the framework's execution methodology (`methodology/03_circuit_breaker.md`).
This document establishes only the cross-cutting requirement: no
role defined in Section 2 may bypass or override the circuit breaker's halt decision.

## 7. References

- `standard/NDS.md` — frontmatter and document lifecycle rules referenced by contracts
  and specs this framework's agents produce.
- `standard/GIP.md` — how a consumer repository inherits this framework's governance
  content in the first place.
- `standard/anti_hallucination.md` — the constraints every role in Section 2 operates
  under while producing its output.
