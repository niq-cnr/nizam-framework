---
id: nizam-eval-gated-promotion
title: "Eval-Gated Model Promotion Protocol"
description: "Treats model and prompt changes as code changes, routing them through the contract-first execution loop and blocking promotion until role-specific evals pass."
version: 0.3.0
status: active
enforcement: consumer-aspirational
authoritative_source: methodology/07_eval_gated_promotion.md
change_log:
  - version: "0.3.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 correction: a degraded eval is one failed promotion attempt governed by the shared three-attempt breaker, not an immediate breaker trip. Durable fallback repinning becomes a gated contract proposal; an already-approved runtime fallback may mitigate traffic without silently mutating configuration."
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3 mechanize-or-descope decision, gate H-CONSTITUTIONAL): marked consumer-aspirational -- this framework ships the standard as a reference a consumer enforces in its own runtime and CI and does not verify its semantics, so first-contact surfaces stop implying enforcement that does not exist."
---

# Eval-Gated Model Promotion Protocol

> **Consumer-aspirational.** A reference standard a consuming repository enforces in its own runtime and CI; this framework's validator does not verify these semantics. Recorded per the Track 3 mechanize-or-descope decision (feature 058).

## 1. Overview

In an agentic ecosystem, changing a model or a prompt template is an architectural change with blast radius equal to changing a core library dependency.

The Nizam Framework treats model and prompt changes identically to code changes. They MUST pass through the contract-first execution loop defined in `methodology/01_execution.md` and MUST pass role-specific evals before promotion.

## 2. The Promotion Loop

When an engineer or agent proposes updating `schema/capability_profile.schema.json` (e.g., to promote `claude-3-5-sonnet-v2` as the new `primary_model` for the `generator-deterministic` profile):

1. **Loop 1 (Pre-Code):** The Generator proposes a contract declaring the intended model change, the expected impact, and the exact regression dataset that will be used for verification. The Validator and Evaluator approve the contract.
2. **Loop 2 (Post-Code):** The Generator updates the capability profile configuration.
3. **Eval Execution:** The Evaluator executes the role-specific eval suite (defined in `methodology/05_eval_and_trace.md`) using the new model against the regression dataset.
4. **The Gate:** The Orchestrator parses the QA verdict. If the eval score
   degrades below the baseline established by the previous model, the verdict
   is one failed attempt for this named promotion step. The attempt is discarded
   in its isolated workspace and the counter advances under
   `methodology/03_circuit_breaker.md`; attempts 1 and 2 may return through the
   normal contract/rework loop with a materially different strategy. Only a
   third failed attempt trips the breaker, blocks the step, and escalates.

## 3. Fallback Repinning Is Gated

If a promoted model passes evals but later exhibits unacceptable production
failure rates (for example context drift or tool ambiguity), the Orchestrator
MUST log the incident and route a fallback-repin **proposal** through the same
Loop 1/Loop 2 contract and evaluation gates as any other model configuration
change. It MUST NOT silently edit the durable capability profile.

A consumer runtime MAY temporarily route traffic to an already-approved
`fallback_model` when a pre-authorized operational policy permits that runtime
mitigation. Such routing does not change the durable primary/fallback pins. A
permanent repin occurs only after the gated proposal is approved and evidenced.

*Attribution: This protocol operationalizes the capability profile routing rules defined in the Vibe Coding Manifesto (v2.0), Section 3.3.*
