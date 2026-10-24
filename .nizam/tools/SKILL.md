---
id: nizam-tools-skill
title: "Nizam Governance Skill"
description: "The single, runtime-agnostic instructions payload (DD-4) an agent runtime loads to plan, execute, gate, and durably record contract-first work under the Nizam framework."
version: 0.8.2
status: active
authoritative_source: tools/SKILL.md
change_log:
  - version: "0.8.2"
    date: "2026-10-19"
    summary: "Include schema/ and ecosystem/ in Section 2's directory enumeration, reference Section 4.4 external mutation mediation in Section 11's tools/interface.md entry, and maintain C13 version parity with tools/skill.json (v0.8.2)."
  - version: "0.8.1"
    date: "2026-10-19"
    summary: "Default tools/start_path.py publish to --mode prepare (noncommitting), require explicit NIZAM_MUTATION_ADAPTER completion responses for --mode publish / build-receipt --commit without local commit fallback, and record executable continuation_lineage checks in capture/classify."
  - version: "0.8.0"
    date: "2026-10-18"
    summary: "Document publish --mode prepare|publish|finalize and build-receipt runtime mutation-authority mediation (V1), align skill.json version parity (C13), and replace static installed-version/phase claims in Section 10 with provenance and capability discovery (V5)."
  - version: "0.7.0"
    date: "2026-10-18"
    summary: "Align Routine/Standard/High-assurance role allocation (independent Evaluator across all tiers), work-specific diagnostic stopping policy, publish/build-receipt producer-to-receipt workflow, and the single authoritative AGF verdict schema across all gates and comparator loops."
  - version: "0.6.2"
    date: "2026-10-18"
    summary: "Route semantic 5-class task classification, trivial/bugfix/small-change paths, lightweight contract amendments, capability preflight, exclusive evidence capture, concise status views, and receipt transitions through tools/start_path.py; clarify blocking vs. advisory_minor verdict rules."
  - version: "0.6.1"
    date: "2026-10-16"
    summary: "Route bug-fix and small-change starts through tools/start_path.py. Feature loops stay mandatory."
  - version: "0.6.0"
    date: "2026-10-12"
    summary: "Route optional runtime sessions through the adapter interface, neutral protocol and SBCL binding without a new skill."
  - version: "0.5.0"
    date: "2026-09-17"
    summary: "Route automated code review through the convergent prior-ledger-first standard and deterministic review CLI."
  - version: "0.4.0"
    date: "2026-07-17"
    summary: "Add Section 8, Ecosystem Engineering Cycle Routing (handover F-010, feature 040): routes the four shipped ecosystem lifecycle protocol documents (01/02/03/07) by path, as a closed set with an exact-text-pinned preamble and exactly four one-line bullets, nothing else; ecosystem/README.md remains authoritative for the full ten-stage lifecycle. References tools/skill.json and NIZAM.json, both extended with matching ecosystem capability entries in this same feature."
  - version: "0.3.0"
    date: "2026-07-09"
    summary: "Bump version for v0.5.1 release (payload validation mode)."
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "Add Cross-Repo Intelligence mandate (read strategy SCOPE.md, ECOSYSTEM.json, and ADRs before acting); add Eval-Gated Promotion rule (model/prompt changes treated as code changes, blocked until evals pass); add Cross-Repo Dependency Gate rule (downstream blocked until upstream contract delta approved). References methodology/07_eval_gated_promotion.md and methodology/08_cross_repo_dependency_gate.md."
  - version: "0.1.0"
    date: "2026-07-08"
    summary: "Initial skill payload: execution loop summary, circuit breaker obligations, anti-hallucination obligations, durable state and evidence-by-path obligations, verdict JSON formats."
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
   directory (`standard/`, `methodology/`, `templates/`, `schema/`, `tools/`,
   `ecosystem/`) "just in case" is prohibited. Resolve the specific capability
   path `NIZAM.json` names for the current task, read that one file, and stop.
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

**Cross-Repo Intelligence (NMF Hybrid)**: When operating across repositories in an ecosystem deployment, the runtime reads the strategy repository's `SCOPE.md`, the local `ECOSYSTEM.json`, and relevant ADRs per `standard/cross_repo_governance.md` — a consumer-aspirational protocol this framework ships as reference and does not itself enforce (the framework is deliberately outside any ecosystem scope; Track 3 decision, feature 058).

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

Before starting a change, classify the task with `tools/start_path.py classify`
into `trivial`, `bugfix`, `small-change`, `standard-feature`, or `high-risk`
based on canonical relative paths and semantic change properties (never line
count alone). The five canonical roles map onto three assurance tiers
(`standard/AGF.md` Section 2.1): **Routine** (`trivial`, `small-change`:
`Generator` + independent `Evaluator`), **Standard** (`bugfix`,
`standard-feature`: `Planner`, `Generator`, `Validator` + independent
`Evaluator`), and **High-assurance** (`high-risk`: full five-role separation
with independent `Evaluator`). A trivial change, bug fix, or small unambiguous
change is not a feature; `tools/start_path.py begin|done
trivial|bugfix|small-change` enforces scope eligibility and verifies that the
actual changed tree and recorded QA result satisfy the route, as
`methodology/01_execution.md` Section 2.1 specifies. For an already `approved`
feature contract that needs only a bounded mechanical file-list or verification
command update without changing goals, `non_goals`, or security invariants, use
`tools/start_path.py amend-contract` (which classifies mechanical vs. semantic
changes and flags `re_approval_required: true` on semantic changes). Use
`tools/start_path.py preflight` before a governed attempt,
`tools/start_path.py capture` for exclusive per-execution evidence capture with
executable work-specific continuation and lineage checks,
`tools/start_path.py publish` (`--mode prepare|publish|finalize`, defaulting to
`--mode prepare`, separating noncommitting plan preparation from `--mode publish`
externally mediated via `NIZAM_MUTATION_ADAPTER` without local commit fallback
and `--mode finalize`)
and `tools/start_path.py build-receipt` (requiring an already-published capture
envelope unless `--commit` is explicitly passed under runtime mutation adapter
authority) to bind receipt-qualified stage evidence,
`tools/start_path.py status` for a concise read-only status view, and
`tools/start_path.py resume` for receipt-verified stage transitions. No feature
implementation may begin against a contract that is not `approved`.

**Eval-Gated Promotion**: Model and prompt changes are treated as code changes and MUST pass through this exact execution loop, blocking promotion until role-specific evals pass per `methodology/07_eval_gated_promotion.md`.

**Cross-Repo Dependency Gate**: If a feature requires upstream API changes, the downstream Generator is blocked until the upstream contract delta is approved per `methodology/08_cross_repo_dependency_gate.md`.

## 4. Circuit Breaker Obligations

Every repeatable step in either loop above — a contract revision, an
implementation rework — is governed by `methodology/03_circuit_breaker.md`:

1. Read the step's current attempt count from the project's durable
   circuit-breaker state before attempting the step.
2. Follow the escalating per-attempt diagnostic posture (a direct fix on
   attempt one, a structural/interface analysis on attempt two, an
   architectural reconsideration or bounded decomposition on attempt three)
   rather than repeating the same approach.
3. Enforce finite task-wide failure budgets: three failures with one signature
   or six failed captures across changing steps/signatures require a stop and
   explicit finite task-scoped operator recovery. Narratives, old amendments
   and decomposition labels do not reset history; decomposition needs a real
   distinct failed parent. Invariant and authority breaches stop immediately.
4. Freeze source before final QA. Reuse valid same-candidate proof and reopen
   implementation only for a concrete failing acceptance requirement or actual
   source change; record new design as a separate bounded task.

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

Every gate this skill's execution loop passes through (Section 3), including
QA checks and comparator critic loops (`standard/acceptance_bars.md`),
culminates in the single authoritative AGF JSON verdict shape:

```json
{
  "final_verdict": {
    "approved": false
  },
  "issues": [],
  "missing_acceptance_coverage": [],
  "unsupported_claims": []
}
```

- `approved` — `true` only when every sibling blocking array below is empty and
  the reviewing role has no remaining objection.
- `issues` — non-empty means rejection, regardless of `approved`'s value.
- `missing_acceptance_coverage` — any acceptance test not traceable to a
  verification step is listed here; non-empty means rejection.
- `unsupported_claims` — any assertion in the accompanying report not backed
  by evidence the reviewing role independently confirmed; non-empty means
  rejection.

Optional non-blocking observations belong in `advisory_minor` (which never
blocks advancement when `issues`, `missing_acceptance_coverage`, and
`unsupported_claims` are empty), required remediation items on failure belong
in `required_fixes`, a QA verdict includes its per-check `verdict` list
(`schema/qa_verdict.schema.json`), and comparator loops attach their metadata
under `comparator`. An agent runtime parses only the JSON block to decide
whether to advance; prose framing around it is informational only.

## 8. Ecosystem Engineering Cycle Routing

This skill remains the sole router for the Ecosystem Engineering Cycle
module (`ecosystem/README.md`); it routes to, never reproduces, the protocols below:

- `ecosystem/01_clean_state_preflight.md` -- Preflight.
- `ecosystem/02_evidence_baseline.md` -- Baseline.
- `ecosystem/03_engineering_audit.md` -- Audit.
- `ecosystem/07_progress_comparison.md` -- Compare.

## 9. Convergent Automated Code Review

Before running or consuming automated code review, read
`standard/convergent_code_review.md` and use `tools/convergent_review.py` for
fingerprints, convergence, lifecycle, counts, verdict, rendering, ledger extraction,
and replay verification. Models remain observation-only. Ordinary review discovers new
findings only on the packet delta; whole-tree discovery requires explicit human
`full_audit` mode and a Git commit/tree commitment produced by the trusted `build-packet`
command. Packet validity requires both JSON Schema and relational validation. Exactly
three independent trials are required through an enforceable sandbox adapter (workspace
or `HOME` changes alone do not qualify), prior active findings fail closed, and
suppression requires a separate human-authorized record.

## 10. Live Runtime Sessions

For adapters claiming the optional `live_runtime_session` capability, read
`tools/interface.md` Section 6, then `methodology/10_live_runtime_sessions.md`.
For the SBCL reference profile, read `methodology/11_sbcl_runtime_binding.md`.
This single runtime-agnostic skill routes to those sources rather than restating
or forking their rules. Adapters without sessions remain conformant under the
original ten mandatory adapter items; the seven calls and S1–S9 are conditional.

Existing schemas and C12 validate declared records only. Session provenance and
warm-image results never substitute for fresh independent acceptance. To
determine the installed payload version, pinned release tag/commit, and active
runtime capabilities in any repository, query `.nizam/provenance.json` and
`.nizam/NIZAM.json` (or run `tools/start_path.py preflight`) rather than
assuming a static release literal or development-phase status; source edits in a
framework checkout never silently mutate an installed `.nizam/` payload without
an authorized re-bootstrap.

## 11. References

- `tools/skill.json` — the capability manifest this document is the payload
  for.
- `tools/interface.md` — how any agent runtime discovers and loads this
  payload, and the adapter contract for the three core abstract operations
  (read-state, write-evidence, run-verification) plus Section 4.4 external
  mutation-authority mediation (`NIZAM_MUTATION_ADAPTER`).
- `methodology/01_execution.md`, `methodology/03_circuit_breaker.md`,
  `methodology/04_tool_driven_state.md`, `standard/anti_hallucination.md`,
  `standard/convergent_code_review.md`, `methodology/07_eval_gated_promotion.md`,
  `methodology/08_cross_repo_dependency_gate.md` —
  the authoritative protocol documents this skill summarizes and defers to.
- `methodology/10_live_runtime_sessions.md`, `methodology/11_sbcl_runtime_binding.md`
  and `tools/interface.md` Section 6 — the optional runtime-session sources.
