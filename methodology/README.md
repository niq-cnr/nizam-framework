---
id: nizam-methodology-readme
title: "Methodology Module — Index"
description: "Index for the methodology/ module: the six protocol documents governing planning, contract-first execution, adversarial TDD, the universal circuit breaker, tool-driven durable state, and the release train."
version: 0.2.1
status: active
authoritative_source: methodology/README.md
change_log:
  - version: "0.2.1"
    date: "2026-07-08"
    summary: "H6 de-leak: rephrased both internal .agent-directory spec-file references (the 00_planning.md table row and the Design Decision Cross-Reference citation) to point to framework-relative sources a fresh consumer repository actually has."
---

# methodology/

The `methodology/` module owns the execution methodology: planning enforcement,
the contract-first harness loop, adversarial TDD, the universal circuit
breaker, tool-driven durable state, and the release train protocol. Every
document in this module is runtime-agnostic and builds on the agent roles and
gates defined in `standard/AGF.md`.

| File | Purpose |
|---|---|
| [`00_planning.md`](00_planning.md) | Planning Enforcer — the mandatory pre-code specification and feature-list artifact pair, the feature list as a validated DAG, the Dependency Enforcement Rule, atomic-step acceptance-test decomposition, and the Scope Budget Protocol (per-feature 3x rolling-average flag, cumulative 130% halt). |
| [`01_execution.md`](01_execution.md) | Contract-First Harness Loop — the two-loop state machine (Loop 1 pre-code alignment, Loop 2 post-code repair) driving Generator/Validator/Evaluator interaction, and the JSON Verdict Parse Rule that gates every stage. |
| [`02_adversarial_tdd.md`](02_adversarial_tdd.md) | Adversarial Test Design — Evaluator independence (never trust generator-supplied evidence), false-pass and false-fail hunting patterns, the negative-testing requirement, and the mandatory per-QA-round adversarial spot-check. |
| [`03_circuit_breaker.md`](03_circuit_breaker.md) | Universal Circuit Breaker (DD-2) — the single authoritative 3-strike attempt limit embedded by every repeatable loop in the framework, its per-attempt strategy table, and the forbidden-fourth-attempt halt/escalation procedure. |
| [`04_tool_driven_state.md`](04_tool_driven_state.md) | Tool-Driven State Management (DD-1 + DD-3) — querying the `NIZAM.json` capability index instead of bulk-reading governance directories, evidence externalisation to `.agent/evidence/`, and the durable-state artifact family table. |
| [`05_release_train.md`](05_release_train.md) | Release Train Protocol — semantic-version git-tag releases, the breaking/minor/patch classification rules, changelog discipline, and the consumer upgrade path via re-bootstrap against a new pinned tag. |

## Design Decision Cross-Reference

Two documents in this module are each the authoritative home for one of the
framework's named Design Decisions (this repository's root `README.md`, "Design
Decisions" section):

- **`03_circuit_breaker.md`** remediates **DD-2 (Universal Circuit Breaker)** —
  the mandatory 3-strike limit that prevents any execution loop from retrying a
  failing step indefinitely.
- **`04_tool_driven_state.md`** remediates both **DD-1 (Tool-Driven State
  Management)** — routing through `NIZAM.json` instead of bulk-reading — and
  **DD-3 (Evidence Externalisation)** — proof lives in `.agent/evidence/`
  files, never pasted inline into YAML or JSON.

## Machine Validation

Every `.md` in this module carries the same six-key frontmatter
(`standard/NDS.md` Section 2) and validates against
`schema/frontmatter.schema.json`, identically to every other module's governed
documents.
