---
id: nizam-standard-readme
title: "Standard Module — Index"
description: "Index for the standard/ module: the four documentation and governance standards every consumer repository inherits — documentation standard, governance inheritance, agent governance, and anti-hallucination constraints."
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

## Machine Validation

The frontmatter rules `NDS.md` Section 2 defines in prose are machine-validated against
`schema/frontmatter.schema.json`. Any document under this module — and any document
injected into a consumer repository under `GIP.md`'s inheritance model — MUST validate
against that schema.
