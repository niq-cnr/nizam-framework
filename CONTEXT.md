---
id: nizam-context
title: "Nizam Framework — Context"
description: "Token-efficient architecture and execution-command summary for agents consuming the Nizam framework."
version: 0.1.0
status: draft
authoritative_source: CONTEXT.md
---

# Nizam Framework — CONTEXT

## Identity

Nizam is a generalised, AI-legible, versioned governance framework. It ships standards,
protocols, schemas, and templates as a single portable payload any AI agent or engineering
team can consume, in any runtime, for any project. Nizam is not application code, not
infrastructure, and not a runtime service.

## Module Map (Hybrid Mono-Repo)

- `schema/` — JSON Schemas for every machine-readable artifact (frontmatter, manifest, phase, feature list, contract, QA verdict, run state).
- `standard/` — Documentation standard, frontmatter rules, governance inheritance, anti-hallucination constraints.
- `methodology/` — Planning, execution, adversarial TDD, circuit breaker, tool-driven state, release train protocols.
- `templates/` — Consumer-repo templates (CONTEXT, AGENTS, DEBT, ADR, work-packet, phase, manifest).
- `tools/` — The single runtime-agnostic skill payload (no per-runtime forks).
- `registry/` — The `NIZAM.json` index schema and scope-definition patterns.

## How Agents Consume the Framework

Agents route through the root `NIZAM.json` capability index rather than bulk-reading
governance directories. The index resolves the minimal set of files a task requires
(protocol, schema, or template path) so context stays engineered, not exhausted.
`NIZAM.json` itself ships in feature 006 of phase 001-framework-genesis; until then,
consult the module READMEs and this file directly.

## Execution Commands

- Bootstrap a consumer repo: `bootstrap.sh` (ships in feature 007) clones a pinned
  framework tag, injects `standard/`, `templates/`, and `schema/`, and verifies compliance.
- Validate framework artifacts against their schemas using any standard JSON Schema
  validator against the files under `schema/`.

## Out of Scope

Nizam never modifies consumer deployments — it only ships governance payload that a
consumer repo ingests. Nizam is not a runtime: it contains no application code and no
infrastructure or hosted services. Nizam ships exactly one skill payload; no per-runtime
skill forks (e.g. `.claude/`, `.codex/`) are permitted anywhere in the repo.
