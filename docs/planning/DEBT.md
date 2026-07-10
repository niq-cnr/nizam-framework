---
id: nizam-debt
title: Technical Debt Register — nizam-framework
description: Known debt, deferred decisions, and cross-repo impacts for the nizam-framework repository.
version: 0.4.0
status: active
authoritative_source: nizam-framework/docs/planning/DEBT.md
---

# Technical Debt Register

## Open

| ID | Date | Severity | Description | Remediation |
|----|------|----------|-------------|-------------|
| NDEBT-002 | 2026-07-08 | Medium | `schema/qa_verdict.schema.json` (shipped in the `schema/` payload) requires keys `verdict` (enum pass/fail), `executed_at`, and `checks[]` (`{command, exit_code, evidence}`) that the reference implementation's own `.agent/qa/NNN.json` verdicts do not carry — the produced verdicts use a richer, parse-rule-oriented shape (`qa_pass`, `final_verdict`, `issues`, `unsupported_claims`, `missing_acceptance_coverage`, `adversarial`, `evidence_files`) and would fail validation against the shipped schema. Nothing enforces it: `tools/validate.sh` C4 validates only `NIZAM.json`; `.agent/qa/*.json` is never checked. Surfaced by the F-017 QA evaluator. | Part (a) RESOLVED by F-025 (schema reconciled to an anyOf union covering both shapes). Part (b) — the enforcement check — is F-028 (C11 dogfood schema validation of `.agent/`). Note for F-028: `.agent/qa/` holds a MIX of qa_verdict and contract_review documents, so C11 must route by content (a `review` field → `contract_review.schema.json`; else `qa_verdict.schema.json`), NOT by directory/filename. |
| NDEBT-003 | 2026-07-10 | Low | Two single-source-of-truth consistency gaps surfaced during F-026 that C9's `/`-qualification (an evidence-backed precision tradeoff — requiring a `/` avoids false-fails on cross-repo terms, same-dir relative links, and ASCII-tree labels) structurally cannot catch: (a) `docs/guide/index.html`'s methodology key-documents list omits `methodology/05_eval_and_trace.md`, the doc main's v0.5.x renumbering inserted; (b) `methodology/06_release_train.md` line 72 carries a bare (non-`/`-qualified) stale `05_release_train.md` reference left by that same renumbering. Both are cross-reference/enumeration consistency concerns, not path-resolution ones. Independently disclosed in `.agent/contracts/026.json` design_notes and reproduced by the F-026 QA. | Address in F-027 (C10 single-source-of-truth consistency): C10's domain covers bare-filename cross-refs and enumeration completeness — fix the guide key-docs list and the line-72 bare ref, and have C10 guard against recurrence. |
| NDEBT-004 | 2026-07-10 | Low | C9 in `--payload` mode is proven non-breaking on the framework's OWN tree only. A real bootstrapped consumer whose `.nizam/` payload lacks injected `methodology/` and `docs/architecture/` could false-fail on directory-qualified cross-references, because C9 — unlike C4 — has no payload `skipped_dirs` carve-out. Spec mandates consumer-safety only for C11 (Sec 4.1), so this was out of F-026's asserted scope. Surfaced by the F-026 Mode-A validator. | Address in F-029 (hermetic e2e consumer-bootstrap test): run `validate.sh --payload` against a real bootstrapped tree; if the e2e surfaces C9 false-fails, add a payload `skipped_dirs`/relative-resolution carve-out to C9 mirroring C4's. |

## Resolved

| ID | Date | Severity | Description | Resolution |
|----|------|----------|-------------|------------|
| NDEBT-001 | 2026-07-07 | Medium | `nizam-framework` is not registered in `nizamiq-strategy/ECOSYSTEM.json` `in_scope`. Creation authorized directly by human architectural mandate (genesis prompt, 2026-07-07). | RESOLVED 2026-07-07 by human decision: the repository is deliberately kept OUTSIDE the NizamIQ ecosystem scope as a generalised framework. It will not be registered in `ECOSYSTEM.json`. Canonical origin: `https://github.com/niq-cnr/nizam-framework.git`. |
