---
id: nizam-methodology-readme
title: "Methodology Module — Index"
description: "Index for the methodology/ module: the protocol documents governing planning, contract-first execution, adversarial TDD, the universal circuit breaker, tool-driven durable state, eval and trace infrastructure, the release train, and cross-repo dependency gates."
version: 0.3.0
status: active
authoritative_source: methodology/README.md
change_log:
  - version: "0.3.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 sync: index summaries now expose isolated-attempt recovery, evidence-before-completion, the five-role eval suite, validator-gated release preparation, three-attempt eval promotion, and the Orchestrator routing/non-authorship boundary."
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
| [`00_planning.md`](00_planning.md) | Planning Enforcer — the mandatory pre-code specification and feature-list artifact pair, validated DAG and dependency rule, atomic acceptance tests, and Scope Budget Protocol (the current feature is excluded from its prior-three rolling baseline; cumulative 130% halt). |
| [`01_execution.md`](01_execution.md) | Contract-First Harness Loop — Orchestrator-coordinated pre-code alignment and post-code repair, the JSON Verdict Parse Rule, and the externalised-evidence gate required before completion. |
| [`02_adversarial_tdd.md`](02_adversarial_tdd.md) | Adversarial Test Design — Evaluator independence (never trust generator-supplied evidence), false-pass and false-fail hunting patterns, the negative-testing requirement, and the mandatory per-QA-round adversarial spot-check. |
| [`03_circuit_breaker.md`](03_circuit_breaker.md) | Universal Circuit Breaker (DD-2) — three isolated attempts from an approved base, exact attempt-root cleanup after evidence capture, canonical phase state with idempotently repaired run state, and no fourth attempt. |
| [`04_tool_driven_state.md`](04_tool_driven_state.md) | Tool-Driven State Management (DD-1 + DD-3) — index-first discovery, externalised evidence, durable artifact families, and every handoff in the five-role chain. |
| [`05_eval_and_trace.md`](05_eval_and_trace.md) | Eval and Trace Infrastructure — verification hierarchy, trace capture, and eval suites for Orchestrator plus all four execution roles. |
| [`06_release_train.md`](06_release_train.md) | Release Train Protocol — SemVer classification, validator-gated changelog/version preparation, human sign-off, the final tag act, and consumer re-bootstrap. |
| [`07_eval_gated_promotion.md`](07_eval_gated_promotion.md) | Eval-Gated Model Promotion Protocol — model/prompt changes use contract-first evals; degraded evals consume the shared three-attempt breaker and durable fallback repins remain gated. |
| [`08_cross_repo_dependency_gate.md`](08_cross_repo_dependency_gate.md) | Cross-Repo Dependency Gate — the Planner declares dependencies; the Orchestrator routes but does not author upstream deltas, and blocks until owner approval. |

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
