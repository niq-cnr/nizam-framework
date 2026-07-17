---
id: nizam-schema-readme
title: "Schema Module — Index"
description: "JSON Schemas that validate every machine-readable artifact the Nizam framework and its consumers produce."
version: 0.6.0
status: draft
authoritative_source: schema/README.md
change_log:
  - version: "0.6.0"
    date: "2026-07-17"
    summary: "Added schema/ecosystem_baseline.schema.json (feature 037, handover F-007): validates the ecosystem immutable-baseline artifact -- the six baseline reference categories (framework/repository/dependency/CI/planning/evidence) and the per-item revision/timestamp anchoring rule a baseline MUST NOT mix unspecified revisions under."
  - version: "0.5.0"
    date: "2026-07-17"
    summary: "Added schema/preflight_verdict.schema.json (feature 038, handover F-008): validates the ecosystem clean-state preflight run's machine-readable verdict artifact -- the exact three-verdict enum (PASS / PASS_WITH_EXCEPTIONS / FAIL) and the structured operator-approval state PASS_WITH_EXCEPTIONS requires."
  - version: "0.4.0"
    date: "2026-07-12"
    summary: "Enumeration-completeness cleanup: added the missing work-packet.schema.json row to the Schemas table (the schema shipped in v0.5.0 but was never indexed here), including the parse-validity-only caveat for its template documented in templates/README.md."
  - version: 0.3.0
    date: "2026-07-08"
    summary: "R4a schema reconciliation (resolves NDEBT-002 part a): added schema/contract_review.schema.json (validates the pre-code contract-testability review verdict) and reconciled qa_verdict.schema.json to an anyOf union of the legacy and evolved feature-QA-verdict shapes actually produced across .agent/qa/*.json."
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
| `contract_review.schema.json` | Validates the pre-code contract-testability review verdict. | `.agent/qa/NNN-contract-review.json` |
| `run_state.schema.json` | Validates the durable run state an execution engine reads and writes across a session. | `.agent/run_state.json` |
| `work-packet.schema.json` | Validates a work-packet artifact: the minimal packet core (`id`, `objective`, `scope`, `acceptance`, `evidence`, `non_goals`) plus the optional cross-repo dispatch and linking fields (`tier`, `blast_radius`, `concurrency_lane`, `dependency_edges`, `merge_order`, and the `contract_id`/`phase_id`/`feature_id`/`train_id` foreign keys). | Work packets authored from `templates/work-packet.template.json` (the template itself is checked for JSON parse-validity only; its `{{...}}` placeholders occupy enum- and integer-typed fields). |
| `debt.schema.json` | Validates the circuit-breaker debt log: timestamp, feature, failed step, attempt count, failure mode, and human resolution. | `.agent/debt.json` |
| `capability_profile.schema.json` | Validates capability-profile bindings that map agent roles to primary/fallback models, allowed tools, and safety classes. | Capability-profile blocks in `AGENTS.md` or standalone `.agent/capability_profile.json` |
| `preflight_verdict.schema.json` | Validates the ecosystem clean-state preflight run's machine-readable verdict artifact: the exact three-verdict enum (`PASS` / `PASS_WITH_EXCEPTIONS` / `FAIL`) and the structured operator-approval state `PASS_WITH_EXCEPTIONS` requires. | `.agent/reconciliation/<execution-id>/preflight.json` |
| `ecosystem_baseline.schema.json` | Validates the ecosystem immutable-baseline artifact: the six baseline reference categories (framework/repository/dependency/CI/planning/evidence) and the per-item revision/timestamp anchoring rule (a baseline MUST NOT mix evidence from unspecified revisions). | `.agent/reconciliation/<execution-id>/baseline.json` |

## DD-3 — Evidence Externalisation

`phase.schema.json` implements Design Decision 3: phase and step evidence MUST be written
to a file (for example `.agent/evidence/step-01.txt`) and referenced *by path* from the
phase definition. Raw terminal output MUST NEVER be pasted directly into a YAML or JSON
string field.

The schema enforces this structurally, not just by convention:

1. A step whose `status` is `COMPLETED` declares an `evidence` property whose value
   MUST match the pattern `^\.agent/evidence/` — a path, not a payload. Steps with
   any other status omit this property.
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
