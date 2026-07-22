---
id: nizam-schema-readme
title: "Schema Module — Index"
description: "JSON Schemas that validate every machine-readable artifact the Nizam framework and its consumers produce."
version: 0.10.0
status: draft
authoritative_source: schema/README.md
change_log:
  - version: "0.10.0"
    date: "2026-07-22"
    summary: "Added schema/ecosystem_membership_result.schema.json (phase-010 feature 077, NDEBT-031; NIP-0002 Stage 3): validates the aggregate ecosystem-level result tools/ecosystem_membership_run.py emits after iterating a membership registry -- the single ecosystem_verdict, the per-member roll-up, and the cross-repository consistency record (framework_pin_consistent + consistency_findings: every in_scope member must run under the same framework pin). A relational invariant is expressed in-schema (if framework_pin_consistent is false, ecosystem_verdict MUST be FAIL). Wired into validate.sh C12 as the sixth ecosystem family at both entry points (full-sweep + --target router, discriminated by ecosystem_verdict/framework_pin_consistent) with one positive and two negative fixtures (a schema-invalid missing-verdict and an if/then-violating inconsistent-but-PASS). Also hardened schema/ecosystem_membership.schema.json (feature 075): schema_version + last_updated are now required and pattern-constrained (semver / ISO-8601 date-prefix), enforced without a jsonschema FormatChecker. Both registered in NIZAM.json."
  - version: "0.9.0"
    date: "2026-07-22"
    summary: "Added schema/ecosystem_membership.schema.json (phase-010 feature 075, NDEBT-031; NIP-0002 Stage 3): validates a consumer's ecosystem-membership registry -- the required artifact that sets n for the 0-to-n spectrum (registry/scope_definition_patterns.md, promoted to a schema-backed active artifact in the same feature). The schema enforces the shape (the four scope lists in_scope/incubating/reference_archive/out_of_scope exist as arrays of entries, every entry has an identifying name, out_of_scope entries record a reason); the exactly-one-list invariant (no name in two lists) is a relational cross-array constraint enforced in code by tools/validate.sh C12, mirroring the ecosystem_baseline same-repo-revision split (NDEBT-023). Wired into C12 as the fifth ecosystem family at both entry points (full-sweep + --target router, discriminated by >=2 of the four scope-list keys) with one positive and two negative fixtures (a schema-invalid missing-list and a schema-valid multilist caught by the code check), and registered in NIZAM.json."
  - version: "0.8.0"
    date: "2026-07-20"
    summary: "Added schema/audit_delta.schema.json: validates the ecosystem progress-comparison delta artifact (ecosystem/07_progress_comparison.md Sec 7) -- the two revision/timestamp-anchored reference points (earlier/later) and the closed five-class transition taxonomy (new/resolved/reopened/persisting/stale, all five buckets present, no sixth class), enforcing the closure-only-with-evidence rule (Sec 4) at the schema layer by requiring a non-empty closure_evidence on every resolved and pre-window-resolved finding. Wired into tools/validate.sh C12 as the fourth ecosystem family at both entry points (full-sweep + --target router, discriminated by a top-level `transitions` object) with one positive and two negative fixtures, and registered in NIZAM.json. Completes the four core ecosystem-cycle schemas and retires the last deferred 'schema not yet present' note in 07_progress_comparison.md."
  - version: "0.7.1"
    date: "2026-07-19"
    summary: "Documentation-truth reconciliation (F-054/NDEBT-011): the work-packet.schema.json row's parse-validity-only caveat for its template is retired -- templates/work-packet.template.json now validates end-to-end against the schema. Its three optional enum/integer dispatch fields (tier/blast_radius/merge_order) cannot hold a {{...}} placeholder, so they are omitted from the starter template rather than shipped as literal defaults a copied packet could silently carry; consumers add them from this schema when a packet needs cross-repo dispatch. Mechanically asserted by a tools/fixtures_self_test.sh guard."
  - version: "0.7.0"
    date: "2026-07-17"
    summary: "Added schema/engineering_finding.schema.json (feature 039, handover F-009): validates a single engineering finding -- severity, confidence (the protocol's fixed Confirmed/Probable/Suspected vocabulary), path-referenced revision-pinned evidence, impact, owner, and closure_criteria, plus a structured, non-empty closure_evidence requirement whenever a finding's status is resolved."
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
| `work-packet.schema.json` | Validates a work-packet artifact: the minimal packet core (`id`, `objective`, `scope`, `acceptance`, `evidence`, `non_goals`) plus the optional cross-repo dispatch and linking fields (`tier`, `blast_radius`, `concurrency_lane`, `dependency_edges`, `merge_order`, and the `contract_id`/`phase_id`/`feature_id`/`train_id` foreign keys). | Work packets authored from `templates/work-packet.template.json` (the shipped template now validates end-to-end against this schema — F-054/NDEBT-011 — with the optional enum/integer dispatch fields `tier`/`blast_radius`/`merge_order` omitted from the template rather than shipped as literal defaults a copied packet could silently carry; consumers add them from this schema when a packet needs cross-repo dispatch). |
| `debt.schema.json` | Validates the circuit-breaker debt log: timestamp, feature, failed step, attempt count, failure mode, and human resolution. | `.agent/debt.json` |
| `capability_profile.schema.json` | Validates capability-profile bindings that map agent roles to primary/fallback models, allowed tools, and safety classes. | Capability-profile blocks in `AGENTS.md` or standalone `.agent/capability_profile.json` |
| `preflight_verdict.schema.json` | Validates the ecosystem clean-state preflight run's machine-readable verdict artifact: the exact three-verdict enum (`PASS` / `PASS_WITH_EXCEPTIONS` / `FAIL`) and the structured operator-approval state `PASS_WITH_EXCEPTIONS` requires. | `.agent/reconciliation/<execution-id>/preflight.json` |
| `ecosystem_baseline.schema.json` | Validates the ecosystem immutable-baseline artifact: the six baseline reference categories (framework/repository/dependency/CI/planning/evidence) and the per-item revision/timestamp anchoring rule (a baseline MUST NOT mix evidence from unspecified revisions). | `.agent/reconciliation/<execution-id>/baseline.json` |
| `engineering_finding.schema.json` | Validates a single engineering finding: severity, confidence (`Confirmed`/`Probable`/`Suspected`), path-referenced revision-pinned evidence, impact, owner, closure_criteria, and a structured, non-empty closure_evidence requirement whenever a finding's status is `resolved`. | `.agent/audits/<audit-id>/findings.json` |
| `audit_delta.schema.json` | Validates the ecosystem progress-comparison delta artifact: the two revision/timestamp-anchored reference points (`earlier`/`later`) and the closed five-class transition taxonomy (`new`/`resolved`/`reopened`/`persisting`/`stale` — all five buckets present, no sixth class admitted), with a non-empty `closure_evidence` required on every `resolved` and pre-window-resolved finding (the closure-only-with-evidence rule of `ecosystem/07_progress_comparison.md` Sec 4). | `.agent/audits/<audit-id>/delta.json` |
| `ecosystem_membership.schema.json` | Validates a consumer's ecosystem-membership registry — the required artifact that sets `n` for the 0-to-n spectrum (`registry/scope_definition_patterns.md`): the four scope lists (`in_scope`/`incubating`/`reference_archive`/`out_of_scope`) exist as arrays of entries, every entry has an identifying `name`, and `out_of_scope` entries record a `reason`. The **exactly-one-list invariant** (no `name` in two lists) is a relational cross-array constraint enforced in code by `tools/validate.sh` C12, not by the schema — the same split as the `ecosystem_baseline` same-repo-revision rule. | A consumer's own membership registry (conventionally an `ecosystem_membership.json` in the consumer repository) |
| `ecosystem_membership_result.schema.json` | Validates the aggregate, ecosystem-level result `tools/ecosystem_membership_run.py` emits after iterating a membership registry's `in_scope` set: the single `ecosystem_verdict` (`PASS`/`FAIL`), the per-member roll-up, and the cross-repository consistency record (`framework_pin_consistent` + `consistency_findings` — every member must run under the same framework pin). A relational invariant is expressed in-schema (if `framework_pin_consistent` is false, `ecosystem_verdict` MUST be `FAIL`). | `<output-dir>/membership_run.json` produced by the membership runner |

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
