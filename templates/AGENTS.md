---
id: nizam-template-agents
title: "AGENTS.md Template"
description: "Consumer-repo AGENTS.md template: the session-objective skeleton a bootstrapped repository copies and completes with its active phase, current objective, and delegation-matrix reference."
version: 0.1.0
status: active
authoritative_source: templates/AGENTS.md
---

<!--
Copy this file to AGENTS.md at the root of {{REPO_NAME}} after bootstrap and replace
every {{PLACEHOLDER}} token in the body below with the live session state. The
frontmatter block above describes this template artifact itself; only the body is
fill-in-the-blanks.
-->

# {{REPO_NAME}} — Agent Session Objective

## Current Session

**Current Objective:** {{CURRENT_OBJECTIVE}}

**Active Phase:** {{ACTIVE_PHASE_ID}} ({{ACTIVE_PHASE_NAME}})

**Session Started:** {{YYYY-MM-DDTHH:MMZ}}

## Mandatory Scope Check

Before performing any work in any session, confirm that {{REPO_NAME}} is listed as
in-scope in the ecosystem's canonical scope document before starting or continuing any
phase work. Treat an unlisted repository as out of scope by default and halt.

## Delegation Matrix

This repository follows the multi-agent delegation matrix defined in
`methodology/01_execution.md` and `standard/AGF.md`: `@planner` for architecture and
spec, `@generator` for contracts and implementation, `@validator` for pre-code (Mode A)
and post-code (Mode B) contract gates, `@evaluator` for QA verdicts. Never skip either
validator step.

## Constraints

- Only implement the current `active_contract_id` from `.agent/run_state.json`.
- Never mark a step COMPLETED without evidence captured under `.agent/evidence/`.
- Halt and log to `docs/planning/DEBT.md` on the third consecutive failed attempt on any
  step (the universal circuit breaker, `methodology/03_circuit_breaker.md`).

## Handoff Notes

{{HANDOFF_NOTES}}

<!-- Any context the next agent session needs: work completed, work remaining, and
     blockers still open. -->
