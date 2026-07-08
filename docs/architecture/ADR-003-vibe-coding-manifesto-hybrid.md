---
id: nizam-adr-003
title: "ADR 003: The Nizam Manifesto Framework (NMF) Hybrid"
description: "Architecture Decision Record detailing the integration of the Vibe Coding Manifesto into the Nizam Framework."
version: 0.1.0
status: active
authoritative_source: docs/architecture/ADR-003-vibe-coding-manifesto-hybrid.md
---

# ADR 003: The Nizam Manifesto Framework (NMF) Hybrid

## 1. Context

The Nizam Framework (v0.3.0) provided a highly operational, installable governance payload (the Execution Kernel) with strict schemas, tool-driven state, and a contract-first execution loop. However, it lacked constitutional breadth: it did not govern cross-repository dependencies, supply-chain provenance, CI gating, or model lifecycle management.

Conversely, the Vibe Coding Manifesto (VCM) provided exceptional constitutional breadth across the entire agentic software engineering lifecycle, but lacked an installable distribution mechanism or schema-enforced operational primitives.

## 2. Decision

We will integrate the constitutional modules of the Vibe Coding Manifesto into the installable, schema-driven format of the Nizam Framework, creating a hybrid governance stack: the **Nizam Manifesto Framework (NMF)**.

This integration treats the two frameworks as complementary layers rather than competitors.

## 3. Implementation Details

The integration ports the following VCM concepts into discrete Nizam modules:

1. **Capability Profile Model:** (`standard/capability_profiles.md` and `schema/capability_profile.schema.json`) Binds roles to abstract capability profiles rather than hard-coded models.
2. **CI Gating Formula:** (`standard/ci_gates.md`) Enforces the 10-gate `MERGE_READY` formula.
3. **MCP Security Policy:** (`standard/mcp_policy.md`) Defines namespace rules and standard surface allocations.
4. **Failure Mode Taxonomy:** (`standard/failure_modes.md`) Names the seven canonical failure modes and their detection/response protocols.
5. **Supply-Chain Provenance:** (`standard/provenance_policy.md`) Mandates artifact attestations and audit envelopes.
6. **Permission Classes:** (`standard/permission_classes.md`) Establishes deny-by-default RBAC and Kubernetes sandbox allocations.
7. **Cross-Repo Intelligence:** (`standard/cross_repo_governance.md`) Defines the executable truth layer and seven-tier architecture model.
8. **Eval and Trace Infrastructure:** (`methodology/05_eval_and_trace.md`) Defines the verification hierarchy and role-specific eval suites.

Additionally, three new hybrid innovations were introduced to bridge the gap between VCM theory and Nizam operation:

1. **Eval-Gated Model Promotion Protocol:** (`methodology/07_eval_gated_promotion.md`) Treats model changes as code changes requiring contract-first execution.
2. **Cross-Repo Dependency Gate:** (`methodology/08_cross_repo_dependency_gate.md`) Requires upstream contract delta approval before downstream execution.
3. **Circuit Breaker Debt Log:** (`templates/DEBT.md` and `schema/debt.schema.json`) Provides a schema-validated register for recording circuit breaker trips and failure modes.

## 4. Attribution

All integrated concepts, including the CI Gating Formula, the seven canonical failure modes, the capability profile model, and the cross-repo architecture tiers, are derived directly from the **Vibe Coding Manifesto**. This framework enhancement exists to operationalize those principles into a verifiable, machine-readable format.

## 5. Consequences

- **Positive:** The Nizam Framework is now constitutionally complete, governing the entire agentic lifecycle from model selection to supply-chain provenance.
- **Positive:** VCM principles are now machine-verifiable and installable via `bootstrap.sh`.
- **Negative:** The framework surface area has expanded significantly, requiring more extensive reading for human operators (though agents will continue to use DD-1 query-driven consumption).
