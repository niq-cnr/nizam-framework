---
id: nizam-failure-modes
title: "Failure Mode Taxonomy"
description: "The seven canonical failure modes in agentic software engineering, with explicit detection and response protocols."
version: 0.1.0
status: active
authoritative_source: standard/failure_modes.md
---

# Failure Mode Taxonomy

## 1. Overview

Agentic systems fail differently than traditional software. An agentic governance framework must explicitly name, detect, and respond to these novel failure classes. 

A compliant repository MUST design its observability and incident response playbooks around the following seven failure modes.

## 2. The Seven Canonical Failure Modes

| Failure Mode | Description | Detection | Response |
|---|---|---|---|
| **Context drift** | Role is working from stale, oversized, or partially summarized state | Trace analysis, artifact version mismatch | Re-inject fresh task packet, revalidate against strategy repo |
| **Contract drift** | Code, docs, consumer expectations, and provider behavior diverge | Pact verification, OpenAPI diff, integration test failure | Block merge, require contract delta review |
| **Privilege creep** | Role obtains tools, roots, or credentials beyond approved surface | Audit envelope analysis, RBAC log review | Revoke elevated access, investigate, update policy |
| **Tool ambiguity** | Overlapping MCP tools or vague descriptions cause wrong-tool selection | Trace analysis, tool-call pattern deviation | Namespace tools, sharpen descriptions, re-scope role allow-lists |
| **Eval blindness** | Tests pass but quality regresses because traces or evals were absent | Regression detection in production, support burden increase | Add eval coverage, recalibrate evaluator prompts |
| **Provenance break** | Artifact cannot prove where, how, and by whom it was produced | Attestation verification failure | Block deployment, rebuild with attestation |
| **Deployment mismatch** | Checks passed on wrong SHA, wrong environment, or wrong version set | SHA verification, environment audit | Rollback to last attested build, investigate |

*Attribution: This taxonomy is ported directly from the Vibe Coding Manifesto (v2.0), Section X.*
