---
id: nizam-debt
title: Technical Debt Register — nizam-framework
description: Known debt, deferred decisions, and cross-repo impacts for the nizam-framework repository.
version: 0.3.0
status: active
authoritative_source: nizam-framework/docs/planning/DEBT.md
---

# Technical Debt Register

## Open

| ID | Date | Severity | Description | Remediation |
|----|------|----------|-------------|-------------|
| NDEBT-002 | 2026-07-08 | Medium | `schema/qa_verdict.schema.json` (shipped in the `schema/` payload) requires keys `verdict` (enum pass/fail), `executed_at`, and `checks[]` (`{command, exit_code, evidence}`) that the reference implementation's own `.agent/qa/NNN.json` verdicts do not carry — the produced verdicts use a richer, parse-rule-oriented shape (`qa_pass`, `final_verdict`, `issues`, `unsupported_claims`, `missing_acceptance_coverage`, `adversarial`, `evidence_files`) and would fail validation against the shipped schema. Nothing enforces it: `tools/validate.sh` C4 validates only `NIZAM.json`; `.agent/qa/*.json` is never checked. Surfaced by the F-017 QA evaluator. | Reconcile in a future self-compliance phase: update `schema/qa_verdict.schema.json` to describe the evolved verdict shape (and/or make `.agent/qa/*.json` emit the schema-required keys), and add a validator check that validates `.agent/qa/*.json` against it. Out of scope for phase 003 (communication); requires a human-authorized plan amendment. |

## Resolved

| ID | Date | Severity | Description | Resolution |
|----|------|----------|-------------|------------|
| NDEBT-001 | 2026-07-07 | Medium | `nizam-framework` is not registered in `nizamiq-strategy/ECOSYSTEM.json` `in_scope`. Creation authorized directly by human architectural mandate (genesis prompt, 2026-07-07). | RESOLVED 2026-07-07 by human decision: the repository is deliberately kept OUTSIDE the NizamIQ ecosystem scope as a generalised framework. It will not be registered in `ECOSYSTEM.json`. Canonical origin: `https://github.com/niq-cnr/nizam-framework.git`. |
