---
id: nizam-schema-readme
title: "Schema Module — Index"
description: "JSON Schemas that validate every machine-readable artifact the Nizam framework and its consumers produce."
version: 0.2.0
status: draft
authoritative_source: schema/README.md
---

# schema/

The `schema/` module is a **leaf module** (see `product_spec.md` Sec 2.2): it owns the
machine-verifiable contracts every other artifact in the framework — and every consumer
repository that adopts the framework — validates against. It depends on nothing and
contains no prose narrative, only JSON Schema documents.

Every schema in this module:

- Is valid JSON.
- Declares `"$schema": "https://json-schema.org/draft/2020-12/schema"` (JSON Schema draft
  2020-12).
- Declares a `$id`, `title`, and `description`.
- Permits `additionalProperties` on extension points so consumer repositories can extend
  a shape without breaking validation, while still enforcing the required keys and enums
  that make an artifact machine-legible.

## Schemas

| Schema | Purpose | Validates |
|--------|---------|-----------|
| `frontmatter.schema.json` | Validates the YAML frontmatter block required at the top of every governance Markdown file (`standard/`, `methodology/`, `templates/`, `tools/`, and module `README.md` files). Enforces the 6 required keys: `id`, `title`, `description`, `version`, `status` (`draft`\|`active`\|`deprecated`), `authoritative_source`. | Frontmatter on any governed `.md` file. |
| `manifest.schema.json` | Validates the planning manifest that names the current phase and lists every phase a repository tracks. | `docs/planning/manifest.json` |
| `phase.schema.json` | Validates a phase definition. Implements **DD-3, Evidence Externalisation** (see below). | Phase definition documents produced from `templates/phase_template.yaml`. |
| `feature_list.schema.json` | Validates the DAG-validated, acceptance-test-bearing feature breakdown of a phase. | `.agent/feature_list.json` |
| `contract.schema.json` | Validates a per-feature contract: scope, non-goals, and verification commands agreed before implementation. | `.agent/contracts/NNN.json` |
| `qa_verdict.schema.json` | Validates an evaluator's pass/fail verdict for a feature, including per-check exit codes and evidence paths. | `.agent/qa/NNN.json` |
| `run_state.schema.json` | Validates the durable run state an execution engine reads and writes across a session. | `.agent/run_state.json` |
| `debt.schema.json` | Validates the circuit-breaker debt log: timestamp, feature, failed step, attempt count, failure mode, and human resolution. | `.agent/debt.json` |
| `capability_profile.schema.json` | Validates capability-profile bindings that map agent roles to primary/fallback models, allowed tools, and safety classes. | Capability-profile blocks in `AGENTS.md` or standalone `.agent/capability_profile.json` |

## DD-3 — Evidence Externalisation

`phase.schema.json` implements Design Decision 3: phase and step evidence MUST be written
to a file (for example `.agent/evidence/step-01.txt`) and referenced *by path* from the
phase definition. Raw terminal output MUST NEVER be pasted directly into a YAML or JSON
string field.

The schema enforces this structurally, not just by convention:

1. Every step declares an `evidence` property whose value MUST match the pattern
   `^\.agent/evidence/` — a path, not a payload.
2. Both the phase object and the step object declare `"additionalProperties": false`
   over an explicit, closed property set. That set intentionally omits any inline
   free-text output field (`proof`, `raw_output`, `terminal_output`, `console_output`,
   `stdout`, `output`). Because unknown properties are rejected outright, a phase document
   cannot smuggle pasted-in terminal output into an unrecognised key and have it silently
   tolerated as a harmless extension property.

This closes the gap that caused the YAML brittleness this framework's predecessors suffered: a schema that only
checked for the *presence* of an evidence field, without also forbidding inline-output
fields, would still validate a document that carried both a legitimate evidence path and
a giant pasted console dump sitting right next to it.
