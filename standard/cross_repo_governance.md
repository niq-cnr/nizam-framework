---
id: nizam-cross-repo-governance
title: "Cross-Repository Intelligence"
description: "The executable truth layer, the cross-repo query protocol, and the seven-tier architecture model for ecosystem-scale governance."
version: 0.1.0
status: active
authoritative_source: standard/cross_repo_governance.md
---

# Cross-Repository Intelligence

## 1. Overview

Maintaining architectural coherence across a multi-repository ecosystem requires a centralized intelligence layer. A single repository acting as the **executable source of truth** (a designated strategy or governance repository) prevents drift and misaligned dependencies.

## 2. The Cross-Repo Query Protocol

Before any agent performs work in a repository, it MUST:

1. Query the strategy repository's `SCOPE.md` to verify the target repository is in-scope.
2. Read `ECOSYSTEM.json` for machine-readable dependency state.
3. Check relevant Architecture Decision Records (ADRs) for constraints.
4. Read the local `CONTEXT.md` for repository-specific architecture.
5. Review `docs/planning/manifest.json` for current phase state.

Failure to query the centralized truth layer before acting is a governance violation.

## 3. The Seven-Tier Architecture Model

All repositories in the ecosystem SHOULD be classified within a canonical tier model to enforce dependency ordering (lower tiers are upstream, higher tiers depend on them):

| Tier | Name | Function |
|------|------|----------|
| **0** | Identity & Access | Authentication, token issuance |
| **1** | Edge & Web Presence | Ingress, routing, edge delivery |
| **2** | Gated Portals | Human-facing interfaces, BFF entry points |
| **3** | Governance & Strategy | Policy, standards, ecosystem truth layer |
| **4** | Runtime Services | Orchestration, pipelines, data services |
| **5** | Infrastructure & Persistence | Operators, control planes, workload substrate |
| **6** | Reference Archive & Legacy | Historical systems for lineage context |

*Attribution: The cross-repo query protocol and seven-tier architecture model are ported from the Vibe Coding Manifesto (v2.0), Section IX.*
