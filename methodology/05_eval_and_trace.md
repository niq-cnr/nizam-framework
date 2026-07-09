---
id: nizam-eval-and-trace
title: "Eval and Trace Infrastructure"
description: "The verification hierarchy, trace capture requirements, and role-specific eval suites that guarantee quality as models and prompts change."
version: 0.1.0
status: active
authoritative_source: methodology/05_eval_and_trace.md
---

# Eval and Trace Infrastructure

## 1. Overview

TDD remains necessary, but no longer sufficient. The governing quality stack in the Nizam Framework is **tests + traces + evals + CI**. 

This document defines the infrastructure required to prove that the agentic system still meets quality targets as inputs, prompts, tools, and models change.

## 2. The Verification Hierarchy

| Level | Method | Authority |
|-------|--------|-----------|
| **L1** | Unit test execution | Evaluator |
| **L2** | Type checking / schema validation | Evaluator |
| **L3** | Build verification | Evaluator |
| **L4** | Consumer/provider contract verification (Pact) | Evaluator |
| **L5** | API conformance | Evaluator |
| **L6** | E2E via Playwright | Evaluator + Orchestrator |
| **L7** | Agent eval regression (traces, graders, datasets) | Evaluator |
| **L8** | Automated code-review gate (tool declared by consumer) | Automated |
| **L9** | Supply-chain provenance check | Automated |
| **L10** | Human review | Human |

## 3. Trace Capture

Every agentic task MUST emit an audit envelope containing:

- Model identity and routing decision
- Prompt template version
- Tool-call summary with arguments and results
- Source artifact hashes
- Contract versions consumed
- Test and eval results
- Attestation references
- Human approvals

Traces are the operational tool for detecting context drift, contract drift, privilege creep, tool ambiguity, and eval blindness.

## 4. Role-Specific Eval Suites

Eval suites measure whether the agentic system still meets quality targets. Each role MUST have a regression set:

| Role | Eval Focus |
|------|-----------|
| Planner | Spec completeness, acceptance criteria testability, contract delta accuracy |
| Generator | Implementation correctness, test passage, contract conformance |
| Validator | Defect detection rate, false-positive rate |
| Evaluator | Bug catch rate, scope creep detection, false-fail rate (calibrated via seed cases) |

Model or prompt changes are **blocked** until they pass the role-specific eval thresholds.

*Attribution: The verification hierarchy, trace capture rules, and eval suite definitions are ported from the Vibe Coding Manifesto (v2.0), Section V.*
