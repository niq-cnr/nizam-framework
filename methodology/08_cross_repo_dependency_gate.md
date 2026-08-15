---
id: nizam-cross-repo-dependency-gate
title: "Cross-Repo Dependency Gate"
description: "How cross-repository dependencies are declared, routed by the Orchestrator to the upstream author, and kept blocked until the owning authority approves the contract delta."
version: 0.2.0
status: active
authoritative_source: methodology/08_cross_repo_dependency_gate.md
change_log:
  - version: "0.2.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 correction: the Orchestrator routes and gates a cross-repository API-contract delta but never authors it; the owning upstream team produces the delta through its own planning/contract loop."
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

The Orchestrator MUST:

1. Route a request to the owning upstream repository/team to author the proposed
   API contract delta (for example an OpenAPI diff or Pact file) through that
   repository's own Planner/Generator contract loop. The Orchestrator records
   the dependency and request reference; it does not author the delta.
2. Submit or route the upstream-authored contract delta to the owning approval
   authority.
3. Wait for explicit approval and record the decision before unblocking the
   downstream Generator.

Execution in the downstream repository remains blocked until the upstream contract delta is approved. This prevents "blind" downstream implementation against an unagreed upstream API.

## 4. Ecosystem DAG Updates

When the orchestrator detects new cross-repository dependencies during a session, it MUST stage updates to the central `DEPENDENCY_MAP.md` (or equivalent graph representation in the strategy repository). These updates are included in the next Release Train commit.

*Attribution: This protocol operationalizes the CI Gating Formula (`contract-delta-reviewed`) and Cross-Repository Intelligence rules defined in the Vibe Coding Manifesto (v2.0).*
