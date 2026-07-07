---
id: nizam-tools-skill
title: "Nizam Governance Skill"
description: "The single, runtime-agnostic instructions payload (DD-4) an agent runtime loads to plan, execute, gate, and durably record contract-first work under the Nizam framework."
version: 0.1.0
status: active
authoritative_source: nizam-framework/tools/SKILL.md
---

# Nizam Governance Skill

## 1. When To Load This Skill

Load this skill whenever the agent runtime is about to act inside a repository
governed by the Nizam framework — that is, a repository that has been
bootstrapped against a pinned Nizam release tag and carries a root `NIZAM.json`
capability index. Concretely, load this skill before any of the following:

- Planning or expanding a request into a specification and feature list.
- Proposing or revising an implementation contract for a feature.
- Writing, modifying, or reviewing source code against an approved contract.
- Running verification commands and recording a pass/fail verdict.
- Updating any file under a project's durable-state directory (conventionally
  `.agent/`).

This skill is the entry point. It does not restate the full content of the
framework's protocol documents; it tells the agent runtime which document to
read for a given task and the non-negotiable obligations that apply regardless
of which document it reads next.

## 2. How To Consume The Framework

The framework is deliberately structured so that no single task requires
reading it in full.

1. **Query the root index first (DD-1).** Before reading any governance file,
   consult the project's root `NIZAM.json` capability index. It enumerates
   every shipped module, protocol document, schema, and template path, with
   enough metadata to resolve the minimal file set the current task needs.
   `NIZAM.json` validates against `registry/nizam-index.schema.json`.
2. **Read only the module the task needs.** Bulk-reading an entire governance
   directory (`standard/`, `methodology/`, `templates/`, `tools/`) "just in
   case" is prohibited. Resolve the specific capability path `NIZAM.json`
   names for the current task, read that one file, and stop.
3. **Follow cross-references only on demand.** Every protocol document
   cross-references related documents by path. Follow such a reference only
   when the current task genuinely requires the referenced content, not
   automatically at every mention.
4. **This skill's own manifest is a map, not a mirror.** `tools/skill.json`
   lists the capabilities this skill exposes and the module path backing each
   one; it does not duplicate their content. Treat it as a table of contents.

The full statement of this discipline lives in
`methodology/04_tool_driven_state.md` (DD-1 and DD-3); this section only
summarizes it for the runtime's first action.

## 3. The Execution Loop Summary

Every feature moves through a two-loop, contract-first state machine before it
is considered complete. This skill does not restate the loop's mechanics —
`methodology/01_execution.md` is authoritative — but every agent runtime
loading this skill must recognize its shape:

- **Loop 1 — Pre-code alignment.** A proposed contract (`status: "proposed"`)
  is checked by a pre-code gate and an independent contract review before it
  is allowed to reach `status: "approved"`. No implementation may begin
  against a contract that is not `approved`.
- **Loop 2 — Post-code repair.** Implementation against an approved contract
  is checked by a post-code gate (comparing the resulting change set against
  the contract) and then independently verified against the contract's
  verification commands before the feature is marked complete.
- **The JSON Verdict Parse Rule gates every stage in both loops.** A gate's
  decision is read exclusively from its machine-parseable JSON verdict block —
  never inferred from prose framing. Advancement is permitted only when the
  verdict's `approved` field is `true` and its `issues`,
  `missing_acceptance_coverage`, and `unsupported_claims` arrays are all
  empty. A report that reads as broadly favorable but carries a non-empty
  array in its JSON block is a rejection.

Read `methodology/01_execution.md` before proposing, implementing, or
reviewing any contract.

## 4. Circuit Breaker Obligations

Every repeatable step in either loop above — a contract revision, an
implementation rework — is bound by the framework's mandatory 3-strike attempt
limit. This skill imposes the following obligations on any agent runtime
attempting such a step, regardless of runtime:

1. Read the step's current attempt count from the project's durable
   circuit-breaker state before attempting the step.
2. Follow the escalating per-attempt strategy (a direct fix on attempt one, a
   structural/interface analysis on attempt two, an architectural
   reconsideration on attempt three) rather than repeating the same approach.
3. Treat a fourth attempt at the same step as forbidden. If the third attempt
   also fails: discard the failed attempt's working changes, mark the step
   `BLOCKED` in durable state, log the failure to the project's technical-debt
   register, and halt for human review.

The full mechanics — the strategy table, the halt procedure, and where the
attempt counters live — are authoritative in `methodology/03_circuit_breaker.md`.
Read it before attempting any retryable step, and in particular before a
second or third attempt at the same step.

## 5. Anti-Hallucination Obligations

Every action taken under this skill — by any agent runtime, in any role — is
bound by the framework's universal anti-hallucination constraints:

- **Read before every write.** Re-read the exact lines to be modified
  immediately before editing; halt and report a mismatch rather than editing
  over unexpected content.
- **Detect before fix.** Re-confirm a problem still exists (re-run the failing
  check, re-read the affected content) before applying a fix; skip a fix whose
  problem is already resolved.
- **Evidence-anchored completion.** Mark a step complete only after capturing
  command output or a file diff as externalised proof — never on reasoning
  alone, and never as proof pasted inline into conversational output only.
- **Verify external system behavior.** Never assume how an external system
  (a verification tool, a build process) formats its output or names its
  artifacts; observe an actual completed run before configuring anything that
  depends on it.

These constraints are authoritative in `standard/anti_hallucination.md`
(AH-1 through AH-4). This skill does not restate their rationale; it commits
every agent runtime that loads this skill to honoring them without exception.

## 6. Durable State And Evidence-By-Path Obligations

This skill's most important structural rule: **agents communicate results by
writing files, never by chat alone.**

1. **Every material result is written to durable state.** A specification, a
   feature list, a contract, a verdict, or a run-position update each has a
   canonical durable location (conventionally under a project's `.agent/`
   directory) that the next agent in the pipeline reads directly, rather than
   trusting a conversational summary.
2. **Evidence is externalised by path (DD-3).** Captured command output or a
   diff proving a step succeeded is written to its own evidence file
   (conventionally under `.agent/evidence/`) and referenced by path from the
   contract, verdict, or state document it supports. Raw terminal output must
   never be pasted inline into a YAML or JSON string field.
3. **Preserve what you do not own.** Any update to a durable-state file
   preserves every field the current step did not change; a role updates only
   the fields its contract or protocol assigns to it.

The full statement of the artifact-family table (run state, feature list,
contracts, QA verdicts, evidence) and the evidence-externalisation rule is
authoritative in `methodology/04_tool_driven_state.md`.

## 7. Verdict JSON Formats

Every gate this skill's execution loop passes through (Section 3) culminates
in a JSON verdict block. An agent runtime forming or consuming a verdict uses
this shape:

```json
{
  "final_verdict": {
    "approved": false,
    "issues": [],
    "missing_acceptance_coverage": [],
    "unsupported_claims": []
  }
}
```

- `approved` — `true` only when every other field below is satisfied and the
  reviewing role has no remaining objection.
- `issues` — non-empty means rejection, regardless of `approved`'s value.
- `missing_acceptance_coverage` — any acceptance test not traceable to a
  verification step is listed here; non-empty means rejection.
- `unsupported_claims` — any assertion in the accompanying report not backed
  by evidence the reviewing role independently confirmed; non-empty means
  rejection.

A QA verdict extends this shape with a per-check result list and, on failure,
a required-fixes list — see `schema/qa_verdict.schema.json` for the full
structural definition. An agent runtime parses only the JSON block to decide
whether to advance; prose framing around it is informational only.

## 8. References

- `tools/skill.json` — the capability manifest this document is the payload
  for.
- `tools/interface.md` — how any agent runtime discovers and loads this
  payload, and the adapter contract for the three abstract operations
  (read-state, write-evidence, run-verification).
- `methodology/01_execution.md`, `methodology/03_circuit_breaker.md`,
  `methodology/04_tool_driven_state.md`, `standard/anti_hallucination.md` —
  the authoritative protocol documents this skill summarizes and defers to.
