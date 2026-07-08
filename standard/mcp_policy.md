---
id: nizam-mcp-policy
title: "MCP Security Policy"
description: "Rules for integrating Model Context Protocol (MCP) servers: treating MCP as a capability plane, not a trust plane, and preventing tool ambiguity."
version: 0.1.0
status: active
authoritative_source: standard/mcp_policy.md
---

# MCP Security Policy

## 1. Overview

The Model Context Protocol (MCP) provides capability negotiation, server features, and an authorization framework for HTTP transports — but its roots are informational. MCP is a **capability plane**, not a trust plane. Operating-system sandboxing and runtime RBAC remain mandatory regardless of MCP capability negotiation.

## 2. Integration Rules

1. **Namespaced allow-lists:** MCP servers MUST be namespaced and catalogued with a per-role allow-list. Not every agent role gets every tool.
2. **No overlapping tools:** Overlapping or vaguely named tools are forbidden. Tool confusion causes wrong-tool selection, leading to context drift or privilege escalation.
3. **Roots are not isolation:** An agent running a `bash` tool via MCP cannot be contained solely by MCP roots. The process executing the bash command MUST be physically or logically sandboxed (e.g., via Docker, gVisor, or restricted VM).

## 3. Standard MCP Surface Allocations

| MCP / Tool Surface | Primary Purpose | Allowed Roles |
|---|---|---|
| **Playwright** | User-visible acceptance, regression, accessibility | Evaluator; Generator (local smoke only) |
| **web-search-prime** | Freshness checks, official-source confirmation | Planner, Validator, Evaluator |
| **sequential-thinking** | Decomposition, replanning, deadlock recovery | Orchestrator, Planner, Validator |
| **context7** | Version-pinned docs and API grounding | Planner, Generator, Validator |
| **bash** | Build, lint, unit and integration execution | Generator, Evaluator (under sandbox policy) |
| **kubectl** | Non-prod verification; approved deploy operations | Evaluator and human release roles only |

*Attribution: This MCP security policy and surface allocation table are ported from the Vibe Coding Manifesto (v2.0), Section VIII.*
