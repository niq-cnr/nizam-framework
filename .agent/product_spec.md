---
id: nizam-product-spec
title: "Nizam Framework — Product Specification"
description: "Architecture and scope specification for Nizam, a generalised AI-legible versioned governance framework distilled from the NizamIQ ecosystem."
tags: [spec, governance, framework, ai-legible, mono-repo]
status: draft
last_audited: "2026-07-07"
authoritative_source: NA
version: 1.2.0
spec_version: "1.2.0"
created_at: "2026-07-07T00:00:00Z"
updated_at: "2026-07-08T00:00:00Z"
change_log:
  - version: "1.0.0"
    date: "2026-07-07T00:00:00Z"
    summary: "Initial spec for Nizam framework genesis (phase 001)."
  - version: "1.1.0"
    date: "2026-07-08T00:00:00Z"
    summary: "ADR-001 layout amendment - .github/workflows/ CI enforcement and tools/validate.sh compliance validator added to the architecture (F-011)."
  - version: "1.2.0"
    date: "2026-07-08T00:00:00Z"
    summary: "ADR-002 layout amendment - docs/architecture/ and docs/guide/ admitted as shipped documentation surfaces, and the docs/ shipped-vs-internal status (docs/planning/ is framework-internal, not shipped) declared (F-017)."
---

# Nizam Framework — Product Specification

## 1. Vision

**Nizam** is a generalised, AI-legible, versioned governance framework. It distils the
load-bearing ideas of the NizamIQ ecosystem — documentation standards, planning and
execution protocols, adversarial TDD, contract-first harness loops, durable agent state,
and governance inheritance — into a single portable payload that any AI agent or engineering
team can consume, in any runtime, for any project.

Nizam is a **pure governance / methodology payload**. It ships standards, protocols, schemas,
and templates. It does not ship application code, infrastructure, or runtime services. It
learns from existing NizamIQ deployments but MUST NEVER modify them, and MUST contain no
references to NizamIQ-specific infrastructure endpoints. The "IQ" branding is dropped.

### Design Tenets

1. **Machine-first legibility** — Every document is parsable before it is readable. YAML
   frontmatter on every `.md`; a JSON index (`NIZAM.json`) as the single root entry point.
2. **One versioned truth** — A Hybrid Mono-Repo. All governance modules live in ONE repo,
   versioned together via semantic git tags, with strict internal module boundaries.
3. **Query, do not bulk-read** — Agents route through the index and read only what a task
   requires. Context is engineered, not exhausted.
4. **Runtime-agnostic** — A single unified skill payload consumable by any agent runtime.
   No per-runtime duplication (`.claude/` vs `.codex/` vs ...).

## 2. Architecture

### 2.1 Hybrid Mono-Repo Layout

```
nizam-framework/
├── NIZAM.json          # Machine-readable capability index + context router (root entry point)
├── CONTEXT.md          # Token-efficient architecture + execution-command summary
├── README.md           # Human entry point
├── CHANGELOG.md        # Semantic version history
├── bootstrap.sh        # Unified clone → inject → verify (evolution of AGIP)
├── standard/           # Documentation standard + frontmatter rules
├── methodology/        # Planning, execution, adversarial TDD, circuit breaker, release train
├── registry/           # NIZAM.json schema + scope-definition patterns
├── templates/          # CONTEXT / AGENTS / DEBT / ADR / work-packet / phase / manifest templates
├── schema/             # JSON Schemas: frontmatter, manifest, phase, feature_list, contract, qa, run_state
├── tools/              # Runtime-agnostic unified skill payload (ONE payload, no per-runtime forks)
│   └── validate.sh     # Runtime-agnostic repo-local compliance validator (ADR-001)
├── .github/workflows/  # CI enforcement of NDS §7 (compliance.yml) (ADR-001)
└── docs/
    ├── architecture/   # ADRs — shipped documentation (ADR-001, ADR-002, …)
    ├── guide/
    │   └── index.html  # Self-contained HTML user guide — shipped documentation (NEW)
    └── planning/       # manifest.json, DEBT.md — framework-internal (NOT shipped to consumers)
```

**`docs/` shipped-vs-internal status (ADR-002):** `docs/architecture/` and `docs/guide/`
are shipped documentation — distributed with the framework repository and indexed by
`NIZAM.json` — but they are NOT part of `bootstrap.sh`'s consumer-injected payload
(`bootstrap.sh` injects only `standard/`, `templates/`, `schema/`, `tools/`, and
`NIZAM.json` into a consumer's `.nizam/`). `docs/planning/` (`manifest.json`, `DEBT.md`)
is framework-internal governance and pipeline state — not shipped documentation, and not
indexed by `NIZAM.json`.

### 2.2 Module Boundaries (internal contracts)

| Module | Owns | May depend on | MUST NOT contain |
|--------|------|---------------|------------------|
| `standard/` | Documentation standard, frontmatter rules, governance inheritance, anti-hallucination | `schema/` (validation targets) | Protocol execution logic, runtime code |
| `methodology/` | Planning, execution, adversarial TDD, circuit breaker, tool-driven state, release train | `standard/` | Frontmatter schema definitions, runtime code |
| `registry/` | `NIZAM.json` schema, scope-definition patterns | `schema/` | Project-specific registry data |
| `templates/` | Consumer-repo document templates | `standard/` | Filled-in project content |
| `schema/` | JSON Schemas for all machine artifacts | (none — leaf) | Prose narrative |
| `tools/` | Unified runtime-agnostic skill interface | `methodology/`, `standard/` | Per-runtime forks or duplicated skill copies |

### 2.3 Context Routing — `NIZAM.json`

`NIZAM.json` is the compact root entry point. It indexes framework capabilities, module
paths, protocol identifiers, schema locations, and the current framework version. Agents
query this index to locate the minimal set of governance files a task needs, instead of
bulk-reading the whole repository. It validates against `registry/nizam-index.schema.json`.

## 3. Module-by-Module Content Inventory

Every file the framework ships, with a one-line purpose.

### Root
| File | Purpose |
|------|---------|
| `NIZAM.json` | Machine-readable capability index and context router; root entry point. |
| `CONTEXT.md` | Token-efficient architecture + execution-command summary for agents. |
| `README.md` | Human-readable overview and quick-start. |
| `CHANGELOG.md` | Semantic version history of the framework. |
| `bootstrap.sh` | Atomic clone-pinned-tag → inject-standards → verify-compliance script. |
| `.gitignore` | Standard ignores. |

### `schema/`
| File | Purpose |
|------|---------|
| `frontmatter.schema.json` | JSON Schema for the required `.md` frontmatter keys. |
| `manifest.schema.json` | JSON Schema for planning `manifest.json`. |
| `phase.schema.json` | JSON Schema for phase definitions; evidence externalised by path. |
| `feature_list.schema.json` | JSON Schema for `.agent/feature_list.json`. |
| `contract.schema.json` | JSON Schema for per-feature contracts. |
| `qa_verdict.schema.json` | JSON Schema for QA verdicts. |
| `run_state.schema.json` | JSON Schema for durable run state. |
| `README.md` | Schema module index. |

### `standard/`
| File | Purpose |
|------|---------|
| `NDS.md` | Nizam Documentation Standard — generalised UDS: file structure, frontmatter, lifecycle. |
| `GIP.md` | Governance Inheritance Protocol — generalised AGIP; agents inherit standards at birth. |
| `AGF.md` | Agent Governance Framework — AGENTS.md structure, scope checks, delegation model. |
| `anti_hallucination.md` | Universal anti-hallucination constraints (AH-1..AH-4). |
| `README.md` | Standard module index. |

### `methodology/`
| File | Purpose |
|------|---------|
| `00_planning.md` | Planning enforcer and DAG method — verifiable-truth plans, atomic steps. |
| `01_execution.md` | Contract-first harness loop — planner→generator→validator→evaluator. |
| `02_adversarial_tdd.md` | Adversarial TDD — failing tests authored before implementation. |
| `03_circuit_breaker.md` | Universal 3-strike circuit-breaker protocol for every execution loop. |
| `04_tool_driven_state.md` | Tool-driven state management — index-query over bulk-read; evidence externalisation. |
| `05_release_train.md` | Release train protocol — semantic-version cut, gates, sign-off. |
| `README.md` | Methodology module index. |

### `registry/`
| File | Purpose |
|------|---------|
| `nizam-index.schema.json` | JSON Schema that `NIZAM.json` must validate against. |
| `scope_definition_patterns.md` | Generalised scope/registry patterns (in-scope/out-of-scope, dependency map). |
| `README.md` | Registry module index. |

### `templates/`
| File | Purpose |
|------|---------|
| `CONTEXT.md` | Consumer-repo CONTEXT.md template. |
| `AGENTS.md` | Consumer-repo agent-instructions template. |
| `DEBT.md` | Technical-debt register template. |
| `ADR_TEMPLATE.md` | Architecture Decision Record template. |
| `work-packet.template.json` | Scoped work-packet (allowed/forbidden paths, evidence) template. |
| `phase_template.yaml` | Phase definition template (evidence-by-path). |
| `manifest.template.json` | Planning manifest template. |
| `README.md` | Templates module index. |

### `tools/`
| File | Purpose |
|------|---------|
| `skill.json` | Unified runtime-agnostic skill manifest describing framework capabilities. |
| `SKILL.md` | The single skill-instructions payload consumable by any runtime. |
| `interface.md` | Runtime-adapter interface spec (how any runtime loads the one payload). |
| `README.md` | Tools module index. |

## 4. Flaw Remediations (Named Design Decisions)

These four NizamIQ flaws are remediated by explicit, named design decisions. Each is
binding on the implementation.

### DD-1 — Tool-Driven State Management (remediates Flaw 1: Context Exhaustion)
Agents MUST route through `NIZAM.json` (validated by `registry/nizam-index.schema.json`)
to locate the minimal governance files a task requires. Bulk-reading governance directories
is prohibited. `methodology/04_tool_driven_state.md` is the authoritative protocol.
*Acceptance anchor:* `NIZAM.json` parses and every indexed capability path resolves on disk.

### DD-2 — Universal Circuit Breaker (remediates Flaw 2: Infinite Loops)
Every execution loop MUST embed a mandatory 3-strike circuit breaker: after three failed
attempts on any single step, HALT, mark BLOCKED, log to DEBT, escalate; attempt 4+ is
forbidden. `methodology/03_circuit_breaker.md` is authoritative and referenced by
`01_execution.md`.
*Acceptance anchor:* the circuit-breaker doc defines the 3-strike limit and is cross-referenced by the execution protocol.

### DD-3 — Evidence Externalisation (remediates Flaw 3: YAML Brittleness)
Phase and step evidence MUST be written to files (e.g. `.agent/evidence/step-01.txt`) and
referenced by path from the phase definition. Raw terminal output MUST NEVER be pasted into
YAML string fields. `schema/phase.schema.json` encodes an evidence-path field, not an
inline-output field.
*Acceptance anchor:* `phase.schema.json` contains an evidence-path property and forbids inline proof strings.

### DD-4 — Unified Skill Payload (remediates Flaw 4: Skill Duplication)
The framework ships exactly ONE skill payload under `tools/`. No per-runtime directories
(`.claude/`, `.codex/`, etc.) are permitted. Any runtime loads the single payload through
the adapter interface in `tools/interface.md`.
*Acceptance anchor:* exactly one `SKILL.md` exists in the repo and no per-runtime skill fork directories exist.

## 5. Versioning & Bootstrap Design

- **Semantic versioning via git tags.** The framework is released as `vMAJOR.MINOR.PATCH`
  tags. `CHANGELOG.md` records every version. `NIZAM.json` carries the current version.
- **Unified `bootstrap.sh`** (evolution of AGIP). One atomic operation:
  1. Clone a **pinned tag** (never floating `main`) of `nizam-framework`.
  2. Inject `standard/`, `templates/`, `schema/` (and register `tools/`) into a consumer repo.
  3. Verify compliance — confirm the required governance files landed and `NIZAM.json` parses.
  Any failed step aborts with a non-zero exit and a clear diagnostic.
- **No NizamIQ endpoints.** The bootstrap references the generic `nizam-framework` repo and
  a `GOVERNANCE_TAG` variable only; it contains no NizamIQ-specific infrastructure URLs.

## 6. Acceptance Criteria (framework-level)

1. Every `.md` under `standard/`, `methodology/`, `registry/`, `templates/`, `tools/` begins
   with YAML frontmatter containing the 6 required keys (`id`, `title`, `description`,
   `version`, `status`, `authoritative_source`).
2. `NIZAM.json` is valid JSON, validates against `registry/nizam-index.schema.json`, and
   every capability/module path it indexes resolves on disk.
3. All seven JSON Schemas under `schema/` are valid JSON Schema documents.
4. `bootstrap.sh` passes `bash -n` and its dry-run verify step succeeds against the repo.
5. No file in the framework references a NizamIQ-specific infrastructure endpoint, and no
   "IQ" branding appears in shipped content.
6. Exactly one skill payload exists (`tools/SKILL.md`); no per-runtime skill directories.

## 7. Execution Order

```
Parallel Group 1: 000 (scaffold — no dependencies)
Parallel Group 2: 001 (schema — depends on 000)
Parallel Group 3: 002 (standard — depends on 000, 001)
Parallel Group 4: 003 (methodology — depends on 000, 002), 004 (templates — depends on 000, 002)
Parallel Group 5: 005 (tools — depends on 000, 003)
Parallel Group 6: 006 (registry + NIZAM.json index — depends on 000, 001, 002, 003, 004, 005)
Sequential:       007 (versioning + bootstrap — depends on 006)
```

Dependency graph validated: no circular dependencies, all dependency targets exist,
topological ordering is possible. Scaffold and root docs sequence first; the registry index
is authored after all content modules exist so it can index them accurately; bootstrap and
versioning close the phase.
