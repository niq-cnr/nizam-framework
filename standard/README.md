---
id: nizam-standard-readme
title: "Standard Module — Index"
description: "Index for the standard/ module: the documentation, governance, security, and architectural standards every consumer repository inherits."
version: 0.2.0
status: active
authoritative_source: standard/README.md
---

# standard/

The `standard/` module owns the Nizam Documentation Standard, the Governance Inheritance
Protocol, the Agent Governance Framework, and the universal anti-hallucination
constraints. Every document in this module is runtime-agnostic and adoptable by any
consumer repository without modification.

| File | Purpose |
|---|---|
| [`NDS.md`](NDS.md) | Nizam Documentation Standard — the six required frontmatter keys, the status lifecycle, versioning and change-log rules, and file/heading/machine-readability conventions every governed document must satisfy. |
| [`GIP.md`](GIP.md) | Governance Inheritance Protocol — how a consumer repository inherits the framework via pinned-tag cloning and `bootstrap.sh`, verifies the inheritance succeeded, and detects drift against the pinned tag over time. |
| [`AGF.md`](AGF.md) | Agent Governance Framework — the four agent roles, the dual validator gate (Mode A pre-code / Mode B post-code), the JSON verdict parse rule, and the durable-state ("no oral tradition") rule. |
| [`anti_hallucination.md`](anti_hallucination.md) | Universal anti-hallucination constraints (AH-1 through AH-4) that bind every agent role's actions, independent of protocol or task. |
| [`capability_profiles.md`](capability_profiles.md) | Binds agent roles to abstract capability profiles rather than hard-coded models. |
| [`ci_gates.md`](ci_gates.md) | The mandatory 10-gate `MERGE_READY` formula that ensures no unverified code bypasses the contract-first execution loop. |
| [`mcp_policy.md`](mcp_policy.md) | Rules for integrating Model Context Protocol (MCP) servers: namespace rules and standard surface allocations. |
| [`failure_modes.md`](failure_modes.md) | The seven canonical failure modes and their detection/response protocols. |
| [`provenance_policy.md`](provenance_policy.md) | Supply-chain provenance rules: artifact attestations, audit envelopes, and SHA-pinned workflows. |
| [`permission_classes.md`](permission_classes.md) | Deny-by-default role permission classes and Kubernetes RBAC allocations. |
| [`cross_repo_governance.md`](cross_repo_governance.md) | The executable truth layer, the cross-repo query protocol, and the seven-tier architecture model. |

## Machine Validation

The frontmatter rules `NDS.md` Section 2 defines in prose are machine-validated against
`schema/frontmatter.schema.json`. Any document under this module — and any document
injected into a consumer repository under `GIP.md`'s inheritance model — MUST validate
against that schema.
