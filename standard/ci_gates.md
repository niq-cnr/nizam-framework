---
id: nizam-ci-gates
title: "CI Gating Formula"
description: "The mandatory 10-gate MERGE_READY formula that ensures no unverified code bypasses the contract-first execution loop."
version: 0.1.0
status: active
authoritative_source: standard/ci_gates.md
---

# CI Gating Formula

## 1. Overview

Agentic software engineering requires a quality stack that extends beyond traditional unit tests. The Nizam Framework adopts the **tests + traces + evals + CI** model from the Vibe Coding Manifesto.

This document defines the CI gating formula. No cross-repo change may be merged unless it satisfies this formula.

## 2. The MERGE_READY Formula

```text
MERGE_READY = CI_GREEN
            ∧ CONTRACT_PLANES_ALIGNED
            ∧ CODERABBIT_CLEAN
            ∧ EVAL_REGRESSION_PASS
            ∧ PROVENANCE_EMIT
            ∧ HUMAN_APPROVED
```

No single factor is sufficient. All MUST be true simultaneously on the latest relevant SHA.

## 3. Required CI Gates

A compliant repository MUST enforce the following gates in its CI pipeline before merge:

| Gate | Evidence Required | Blocking Condition |
|------|------------------|-------------------|
| `plan-pack-valid` | Planner output validates against `schema/feature_list.schema.json` and references current strategy repo artifacts | Invalid or stale plan pack |
| `contract-delta-reviewed` | Any schema/OpenAPI/Pact change acknowledged by owning teams | Unreviewed contract delta |
| `unit-and-component` | Deterministic tests green | Any failure |
| `consumer-provider-contract` | Pact or equivalent verification passes | Contract incompatibility |
| `integration` | Cross-service test suite green | Any failure |
| `playwright-e2e` | User-visible workflows pass | Flaky or failing critical journey |
| `agent-eval-regression` | Trace and eval thresholds meet baseline | Quality regression |
| `supply-chain-security` | Pinned actions, scans, SBOM, no policy violations | Provenance or policy breach |
| `artifact-attestation` | Build provenance emitted and verified | Missing or invalid attestation |
| `human-review` | CODEOWNERS and human reviewer approvals complete | Missing approval |

*Attribution: The MERGE_READY formula and the 10 required CI gates are derived directly from the Vibe Coding Manifesto (v2.0), Section VI.*
