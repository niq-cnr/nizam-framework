---
id: nizam-ci-gates
title: "CI Gating Formula"
description: "The tiered MERGE_READY bar: a mandatory core gate set plus capability-gated gates a consumer requires only where it declares the capability."
version: 0.3.0
status: active
enforcement: consumer-aspirational
authoritative_source: standard/ci_gates.md
change_log:
  - version: "0.3.0"
    date: "2026-11-05"
    summary: "Operator directive 'governance simplification 2026-11-05 item 2': replaced the always-required 10-gate formula with a tiered bar -- a mandatory core (test suite, supply-chain scanning, review verdict on the exact head) plus capability-gated gates required only where the consumer declares the capability in its NIZAM.json 'declared_capabilities' key; documents that a gate implemented in zero repositories was a rule defect."
  - version: "0.2.1"
    date: "2026-09-19"
    summary: "Scrubbed the vendor-named example from the AUTOMATED_REVIEW_CLEAN gate description: the conformant-tool example now names the capability (an automated code-review tool declared by the consumer) without naming any specific vendor tool, preserving the normative meaning -- the gate remains mandatory, tool-agnostic, and consumer-declared."
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3 mechanize-or-descope decision, gate H-CONSTITUTIONAL): marked consumer-aspirational -- this framework ships the standard as a reference a consumer enforces in its own runtime and CI and does not verify its semantics, so first-contact surfaces stop implying enforcement that does not exist."
---

# CI Gating Formula

> **Consumer-aspirational.** A reference standard a consuming repository enforces in its own runtime and CI; this framework's validator does not verify these semantics. Recorded per the Track 3 mechanize-or-descope decision (feature 058).

## 1. Overview

Agentic software engineering requires a quality stack that extends beyond traditional unit tests. The Nizam Framework adopts the **tests + traces + evals + CI** model from the Vibe Coding Manifesto.

This document defines the CI gating bar.

No cross-repo change may be merged unless it satisfies this bar:

- **Core (always required):** (a) the repository's test suite for the changed surface -- the `unit-and-component` and `integration` gates -- (b) secret scanning plus dependency/SAST scanning (the `supply-chain-security` gate), and (c) a review verdict on the exact head (the automated-review gate plus human review per `standard/definition_of_done.md` Merge-Done).
- **Capability-gated:** the remaining gates -- `plan-pack-valid`, `consumer-provider-contract`, `agent-eval-regression`, `artifact-attestation`, and `playwright-e2e` -- are required only where the repository declares the corresponding capability. The consumer declares the key `declared_capabilities` in its `NIZAM.json` (not `capabilities`, which the framework index uses for its catalogue). The recognised declaration values are exactly: `plan-pack`, `consumer-provider-contract`, `agent-eval`, `artifact-attestation`, `playwright-e2e`.

An undeclared capability is not required. A capability the repository has implemented stays required once declared.

Plainly: a gate that is implemented in zero repositories was a rule defect, and the capability gating above corrects that defect.

## 2. The MERGE_READY Formula

```text
MERGE_READY = CI_GREEN
            ∧ CONTRACT_PLANES_ALIGNED
            ∧ AUTOMATED_REVIEW_CLEAN
            ∧ EVAL_REGRESSION_PASS
            ∧ PROVENANCE_EMIT
            ∧ HUMAN_APPROVED
```

No single factor is sufficient. All MUST be true simultaneously on the latest relevant SHA.

The umbrella terms in the formula map to the required CI gates as follows; the non-core factors apply only when their capability is declared:

| Formula Factor | Required CI Gate(s) |
|---|---|
| `CI_GREEN` | `unit-and-component` ∧ `integration` |
| `CONTRACT_PLANES_ALIGNED` | `plan-pack-valid` ∧ `contract-delta-reviewed` ∧ `consumer-provider-contract` (gated parts only when declared) |
| `AUTOMATED_REVIEW_CLEAN` | The tool-agnostic automated-review gate (declared by the consumer, not one of the 10 mandatory pipeline gates) |
| `EVAL_REGRESSION_PASS` | `agent-eval-regression` (capability-gated) |
| `PROVENANCE_EMIT` | `supply-chain-security` ∧ `artifact-attestation` (gated part only when declared) |
| `HUMAN_APPROVED` | `human-review` |

The `AUTOMATED_REVIEW_CLEAN` factor requires that **a conformant automated code-review tool has run on the latest relevant SHA and reports no unresolved blocking findings**. The framework MANDATES this gate but deliberately does NOT fix the tool: the specific automated code-review tool (an AI-assisted review service, a purpose-built review agent, or any conformant equivalent) is declared by the consumer — for example in its `NIZAM.json` / governance config — not by this framework. The gate is BLOCKING and deny-by-default: an absent, stale, or failed automated review means the change is NOT `MERGE_READY`.

## 3. Required CI Gates

A compliant repository MUST enforce the core gates and each gate whose capability it declares in `declared_capabilities`:

| Gate | Capability | Evidence Required | Blocking Condition |
|------|-----------|------------------|-------------------|
| `plan-pack-valid` | `plan-pack` | Planner output validates against `schema/feature_list.schema.json` and references current strategy repo artifacts | Invalid or stale plan pack |
| `contract-delta-reviewed` | core | Any schema/OpenAPI/Pact change acknowledged by owning teams | Unreviewed contract delta |
| `unit-and-component` | core | Deterministic tests green | Any failure |
| `consumer-provider-contract` | `consumer-provider-contract` | Pact or equivalent verification passes | Contract incompatibility |
| `integration` | core | Cross-service test suite green | Any failure |
| `playwright-e2e` | `playwright-e2e` | User-visible workflows pass | Flaky or failing critical journey |
| `agent-eval-regression` | `agent-eval` | Trace and eval thresholds meet baseline | Quality regression |
| `supply-chain-security` | core | Pinned actions, scans, SBOM, no policy violations | Provenance or policy breach |
| `artifact-attestation` | `artifact-attestation` | Build provenance emitted and verified | Missing or invalid attestation |
| `human-review` | core | CODEOWNERS and human reviewer approvals complete | Missing approval |

*Attribution: The MERGE_READY formula and the 10 required CI gates are derived directly from the Vibe Coding Manifesto (v2.0), Section VI.*

*Generalization: Where the manifesto names a specific automated code-review tool, the Nizam Framework generalizes that tool-specific reference into the tool-agnostic `AUTOMATED_REVIEW_CLEAN` gate — the conformant review tool is declared by the consumer, not fixed by this framework.*
