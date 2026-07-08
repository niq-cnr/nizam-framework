---
id: nizam-cross-repo-dependency-gate
title: "Cross-Repo Dependency Gate"
description: "How the Planner updates the ecosystem dependency graph and blocks execution until upstream contract deltas are reviewed."
version: 0.1.0
status: active
authoritative_source: methodology/08_cross_repo_dependency_gate.md
---

# Cross-Repo Dependency Gate

## 1. Overview

The Planning Enforcer (`methodology/00_planning.md`) requires feature lists to be valid Directed Acyclic Graphs (DAGs) locally. However, in a multi-repository ecosystem, a feature often depends on upstream API changes in a different repository.

This document extends the Dependency Enforcement Rule to the ecosystem scale.

## 2. The Cross-Repo Discovery Rule

During the planning phase, the Planner MUST read the target repository's `ECOSYSTEM.json` and any relevant Architecture Decision Records (ADRs).

If the requested feature requires an upstream change (e.g., adding a new endpoint to a Tier 4 Runtime Service), the Planner MUST explicitly declare this dependency in the feature list.

## 3. The Contract Delta Gate

If a cross-repo dependency is declared, the pipeline MUST halt before Generator execution. 

The orchestrator (e.g., the Hermes agent) MUST:
1. Generate the proposed API contract delta (e.g., OpenAPI diff, Pact file).
2. Submit the contract delta to the owning team (human or agent) of the upstream repository.
3. Wait for explicit approval.

Execution in the downstream repository remains blocked until the upstream contract delta is approved. This prevents "blind" downstream implementation against an unagreed upstream API.

## 4. Ecosystem DAG Updates

When the orchestrator detects new cross-repository dependencies during a session, it MUST stage updates to the central `DEPENDENCY_MAP.md` (or equivalent graph representation in the strategy repository). These updates are included in the next Release Train commit.

*Attribution: This protocol operationalizes the CI Gating Formula (`contract-delta-reviewed`) and Cross-Repository Intelligence rules defined in the Vibe Coding Manifesto (v2.0).*
