# Nizam

Nizam is order, system, and governance distilled into a single, portable payload. It is a
generalised, AI-legible, versioned governance framework: a Hybrid Mono-Repo of standards,
protocols, schemas, and templates that any AI agent or engineering team can consume, in
any runtime, for any project.

Nizam does not ship application code or infrastructure. It ships the rules by which
software gets built responsibly — and the machine-readable index that lets an AI agent
find exactly the rule it needs, without reading everything.

## Design Decisions

- **DD-1 — Tool-Driven State Management.** Agents query the root `NIZAM.json` index to
  find the minimal governance files a task needs, instead of bulk-reading directories.
- **DD-2 — Universal Circuit Breaker.** Every execution loop embeds a mandatory 3-strike
  breaker: three failed attempts halts the loop, marks it blocked, and escalates.
- **DD-3 — Evidence Externalisation.** Proof of work lives in files referenced by path,
  never pasted inline into YAML or JSON state.
- **DD-4 — Unified Skill Payload.** Exactly one skill payload under `tools/`, loaded by
  any runtime through a single adapter interface — no per-runtime forks.

## Modules

| Module | Purpose |
|--------|---------|
| `schema/` | JSON Schemas for every machine-readable framework artifact. |
| `standard/` | Documentation standard, frontmatter rules, governance inheritance. |
| `methodology/` | Planning, execution, adversarial TDD, circuit breaker, release train. |
| `templates/` | Consumer-repo document and manifest templates. |
| `tools/` | The single runtime-agnostic skill payload. |
| `registry/` | The `NIZAM.json` index schema and scope-definition patterns. |

## Versioning

Nizam is released as semantically versioned git tags (`vMAJOR.MINOR.PATCH`). See
`CHANGELOG.md` for the version history. Consumer repos pin to a specific tag when
bootstrapping — never to a floating branch.
