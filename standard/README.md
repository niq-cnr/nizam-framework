---
id: nizam-standard-readme
title: "Standard Module — Index"
description: "Index for the standard/ module: the documentation, governance, security, and architectural standards every consumer repository inherits."
version: 0.5.0
status: active
authoritative_source: standard/README.md
change_log:
  - version: "0.5.0"
    date: "2026-09-17"
    summary: "Update the convergent-review index for authenticated Git tree scope, old-byte diffs, sandboxed trials, no-follow replay, and atomic no-replace publication."
  - version: "0.4.0"
    date: "2026-09-17"
    summary: "Index the Convergent Automated Code Review standard and its deterministic prior-ledger-first, three-trial, replay-verifiable protocol."
  - version: "0.3.0"
    date: "2026-08-18"
    summary: "Phase 013, feature 093: add the standard/definition_of_done.md index row -- the canonical, layered Definition of Done."
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
| [`AGF.md`](AGF.md) | Agent Governance Framework — the agent roles (a coordinating Orchestrator plus four execution roles), the dual validator gate (Mode A pre-code / Mode B post-code), the JSON verdict parse rule, and the durable-state ("no oral tradition") rule. |
| [`anti_hallucination.md`](anti_hallucination.md) | Universal anti-hallucination constraints (AH-1 through AH-4) that bind every agent role's actions, independent of protocol or task. |
| [`capability_profiles.md`](capability_profiles.md) | Binds agent roles to abstract capability profiles rather than hard-coded models. |
| [`ci_gates.md`](ci_gates.md) | The mandatory 10-gate `MERGE_READY` formula that ensures no unverified code bypasses the contract-first execution loop. |
| [`mcp_policy.md`](mcp_policy.md) | Rules for integrating Model Context Protocol (MCP) servers: namespace rules and standard surface allocations. |
| [`failure_modes.md`](failure_modes.md) | The seven canonical failure modes and their detection/response protocols. |
| [`provenance_policy.md`](provenance_policy.md) | Supply-chain provenance rules: artifact attestations, audit envelopes, and SHA-pinned workflows. |
| [`permission_classes.md`](permission_classes.md) | Deny-by-default role permission classes and Kubernetes RBAC allocations. |
| [`cross_repo_governance.md`](cross_repo_governance.md) | The executable truth layer, the cross-repo query protocol, and the seven-tier architecture model. |
| [`definition_of_done.md`](definition_of_done.md) | The canonical, layered Definition of Done -- aggregates the framework's eight done-layers by citing each layer's existing authority, never restating its mechanics. |
| [`convergent_code_review.md`](convergent_code_review.md) | Runtime-neutral, prior-ledger-first automated review with trusted Git-object packet construction, authenticated old/current bytes and full-tree scope, three sandbox-isolated trials, deterministic lifecycle/verdict, human suppression, no-follow replay, and race-free publication. |

## Machine Validation

The frontmatter rules `NDS.md` Section 2 defines in prose are machine-validated against
`schema/frontmatter.schema.json`. Any document under this module — and any document
injected into a consumer repository under `GIP.md`'s inheritance model — MUST validate
against that schema.
