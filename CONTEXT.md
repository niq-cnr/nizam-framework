---
id: nizam-context
title: "Nizam Framework — Context"
description: "Token-efficient architecture and execution-command summary for agents consuming the Nizam framework."
version: 0.5.0
status: active
authoritative_source: CONTEXT.md
change_log:
  - version: "0.5.0"
    date: "2026-07-13"
    summary: "Bump version for v0.6.0 release (durable enforcement C9-C11, verify_lib, hermetic e2e bootstrap test, schema reconciliation, and the documentation-truth cleanup)."
  - version: "0.4.1"
    date: "2026-07-12"
    summary: "Stale-enumeration cleanup: the Module Map's standard/ entry now names the constitutional policy documents (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance) shipped since v0.4.0, instead of only the four genesis-era core documents."
  - version: "0.4.0"
    date: "2026-07-09"
    summary: "Bump version for v0.5.1 release (payload validation mode)."
  - version: "0.3.0"
    date: "2026-07-09"
    summary: "Add docs/ to Module Map (ADRs and HTML user guide); bump version to reflect v0.5.0 release state."
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Rewrite to reflect the shipped state: NIZAM.json and bootstrap.sh have both shipped (removed stale 'ships in feature 00X' claims); named the phase-002 compliance surfaces (tools/validate.sh, .github/workflows/compliance.yml, docs/architecture/); corrected the bootstrap payload sentence to the 4 injected directories (standard/, templates/, schema/, tools/) plus NIZAM.json; stated the agent entry path (NIZAM.json -> tools/SKILL.md); expanded NDS/AGF/GIP at first use with their verbatim canonical titles."
---

# Nizam Framework — CONTEXT

## Identity

Nizam is a generalised, AI-legible, versioned governance framework. It ships standards,
protocols, schemas, and templates as a single portable payload any AI agent or engineering
team can consume, in any runtime, for any project. Nizam is not application code, not
infrastructure, and not a runtime service.

## Module Map (Hybrid Mono-Repo)

- `schema/` — JSON Schemas for every machine-readable artifact (frontmatter, manifest, phase, feature list, contract, QA verdict, run state).
- `standard/` — The Nizam Documentation Standard (NDS), the Agent Governance Framework (AGF), the Governance Inheritance Protocol (GIP), the anti-hallucination constraints, and the constitutional policy set (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance).
- `methodology/` — Planning, execution, adversarial TDD, circuit breaker, tool-driven state, release train protocols.
- `templates/` — Consumer-repo templates (CONTEXT, AGENTS, DEBT, ADR, work-packet, phase, manifest).
- `tools/` — The single runtime-agnostic skill payload (no per-runtime forks), entered via `tools/SKILL.md`.
- `registry/` — The `NIZAM.json` index schema and scope-definition patterns.
- `docs/` — Architecture Decision Records (`docs/architecture/`) and the self-contained HTML user guide (`docs/guide/index.html`).

Compliance surfaces, added in phase 002-self-compliance, keep the shipped payload honest:
`tools/validate.sh` (the repo-local compliance validator), `.github/workflows/compliance.yml`
(the CI workflow that runs it on every push and pull request), and `docs/architecture/`
(where Architecture Decision Records such as ADR-001 and ADR-002 are recorded).

## How Agents Consume the Framework

Agents route through the root `NIZAM.json` capability index rather than bulk-reading
governance directories. The index resolves the minimal set of files a task requires
(protocol, schema, or template path) so context stays engineered, not exhausted.
`NIZAM.json` is the shipped root capability index; it indexes `tools/skill.json`, whose
`entry_point` field names `tools/SKILL.md` as the agent entry path. An agent resolves
`NIZAM.json` first, then `tools/skill.json`, then loads `tools/SKILL.md` to learn how to
plan, execute, gate, and durably record work.

## Execution Commands

- Bootstrap a consumer repo: `bootstrap.sh` clones a pinned framework tag, injects the
  four governance directories `standard/`, `templates/`, `schema/`, and `tools/` plus the
  root `NIZAM.json` capability index, and verifies compliance before declaring success.
- Validate framework artifacts against their schemas using any standard JSON Schema
  validator against the files under `schema/`, or run `tools/validate.sh` for the
  repo-local compliance check that `.github/workflows/compliance.yml` runs in CI.

## Out of Scope

Nizam never modifies consumer deployments — it only ships governance payload that a
consumer repo ingests. Nizam is not a runtime: it contains no application code and no
infrastructure or hosted services. Nizam ships exactly one skill payload; no per-runtime
skill forks (e.g. `.claude/`, `.codex/`) are permitted anywhere in the repo.
