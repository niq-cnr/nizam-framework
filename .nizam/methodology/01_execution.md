---
id: nizam-contract-first-execution
title: "Contract-First Harness Loop"
description: "The authoritative execution protocol: the two-loop state machine driving pre-code contract alignment and post-code implementation repair, the JSON Verdict Parse Rule, and the evidence-capture gate required before completion."
version: 0.4.1
status: active
authoritative_source: methodology/01_execution.md
change_log:
  - version: "0.4.1"
    date: "2026-10-19"
    summary: "Align Section 7 reference to 03_circuit_breaker.md with the work-specific diagnostic stopping policy (removing the residual universal '3-strike limit' summary)."
  - version: "0.4.0"
    date: "2026-10-18"
    summary: "Align Section 2.1 with Routine/Standard/High-assurance role allocation (independent Evaluator across all tiers), unify scope eligibility and actual-diff verification across classify/begin/done, document publish and build-receipt producer-to-receipt integration, distinguish mechanical vs. semantic contract amendments, and align Section 5 with work-specific diagnostic stopping."
  - version: "0.3.0"
    date: "2026-10-18"
    summary: "Extend Section 2.1 with semantic 5-route task classification (trivial, bugfix, small-change, standard-feature, high-risk), lightweight contract amendments via tools/start_path.py amend-contract when goals and invariants are unchanged, exclusive per-execution evidence capture via tools/start_path.py capture, capability preflight, and blocking vs. advisory_minor verdict separation."
  - version: "0.2.1"
    date: "2026-10-16"
    summary: "Name the bug-fix and small-change routes. tools/start_path.py consumes their cause, scope, and intent records. The two feature loops stay mandatory and are not skipped."
  - version: "0.2.0"
    date: "2026-08-15"
    summary: "Phase-012 issue-52 correction: a passing QA verdict no longer advances directly to complete. A distinct evidence-capture gate verifies referenced .agent/evidence files exist and record each required command/result before the Orchestrator may update lifecycle state."
---

# Contract-First Harness Loop

## 1. Overview

Once `00_planning.md` has produced an eligible, dependency-cleared feature, that
feature is driven through a two-loop state machine before it is considered
complete. Loop 1 aligns on *what* will be built, before any code exists. Loop 2
verifies *what was built* matches what was aligned on. Neither loop may be
skipped, collapsed, or reordered for a feature. Section 2.1 is the only
non-feature route, and it does not authorize skipping either loop for a feature.

This protocol is coordinated by the **Orchestrator** and governs the interaction
between the **Generator**, **Validator**, and **Evaluator** roles defined in
`standard/AGF.md` Section 2. It is bound by the Dual Validator Gate defined in
that document's Section 3; the Planner's eligible feature is its input.

## 2. Loop 1 — Pre-Code Alignment

```text
Generator proposes contract (status: "proposed")
        |
        v
Validator Mode A  (pre-code contract gate, standard/AGF.md Sec 3)
        |
        v
Evaluator contract review (independent second read of the same contract)
        |
        v
   Both approve?  --No--> Generator revises contract --> back to Validator Mode A
        |                  (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Contract status -> "approved". Loop 1 ends. Loop 2 begins.
```

A contract entering Loop 1 MUST declare, at minimum: the files it will create or
modify, its non-goals (explicit statements of what it does NOT authorize), its
verification commands (one per acceptance test it satisfies), an estimated line
count, and an evidence directory/convention (`schema/contract.schema.json`). A
proposal missing any of these is incomplete and cannot reach `approved` status.

**No implementation before approval.** A Generator MUST NOT write source code
against a contract whose `status` is anything other than `"approved"`. This is
the single most important rule in this protocol — every other gate exists to
protect it.

### 2.1 Semantic task routing and non-feature routes

Before starting a change, classify the task using `tools/start_path.py classify`
based on canonical relative paths and semantic change properties (files touched,
defect repair vs. new contract obligations, schema/interface impact, and
security/isolation/runtime boundaries), never line count alone. Classification
returns the selected route (`trivial`, `bugfix`, `small-change`,
`standard-feature`, or `high-risk`), its assurance tier (`Routine`, `Standard`,
or `High-assurance` per `standard/AGF.md` Section 2.1), required gates, review
remit, and work-specific stopping conditions (`03_circuit_breaker.md`). Across
every tier, the **Evaluator** remains independent of the authoring Generator.

A bug fix, a small unambiguous change, and a trivial editorial adjustment are
not features. They do not open a product specification or a new contract, and
they do not pass through Loop 1. `tools/start_path.py` enforces a single unified
scope eligibility and actual-diff verification predicate across `classify`,
`begin`, and `done`. The feature-path gate count is unchanged.

- **Trivial change (`Routine` tier).** Editorial, comment, or documentation-only
  adjustments (`*.md`, `*.txt`, `*.rst`, `*.html`) that do not touch governance
  core (`AGENTS.md`, `NIZAM.json`, `standard/`, `methodology/`, `ecosystem/`,
  `registry/`, `templates/`), schemas, tools, contracts, or security boundaries
  may begin when `tools/start_path.py begin trivial --id <id>` exits 0 (reading
  `.agent/evidence/<id>-intent.json` with a non-empty `files` list against
  `schema/small_change_intent.schema.json` and `needs_new_contract: false`) and
  complete when `tools/start_path.py done trivial --id <id>` exits 0 (verifying
  that the actual changed tree is within the declared intent files and that a
  passing `.agent/qa/<id>.json` with non-empty executed checks and evidence
  exists).
- **Bug fix (`Standard` tier).** Implementation may begin only when
  `tools/start_path.py begin bugfix --id <id>` exits 0. That command reads
  `.agent/evidence/<id>-cause.json` against `schema/bugfix_cause.schema.json`
  and `.agent/evidence/<id>-scope.json` against
  `schema/bugfix_scope.schema.json`, rejecting high-risk or schema paths. When
  the scope names `contract_id`, `.agent/contracts/<contract_id>.json` must
  validate against `schema/contract.schema.json` with a status of `approved`,
  `implemented`, or `complete`, and every scoped file must be inside that
  contract. The repair then does not repeat Loop 1. The bug fix is not done
  until `tools/start_path.py done bugfix --id <id>` exits 0, which verifies the
  actual changed files against the declared scope and requires a passing
  `.agent/qa/<id>.json` with at least one executed check and non-empty evidence.
- **Small unambiguous change (`Routine` tier).** Implementation may begin only
  when `tools/start_path.py begin small-change --id <id>` exits 0. That command
  reads `.agent/evidence/<id>-intent.json` against
  `schema/small_change_intent.schema.json`, requires a non-empty `files` list
  eligible for `small-change`, and refuses the path when `needs_new_contract` is
  true. The change is not done until `tools/start_path.py done small-change --id
  <id>` exits 0, which verifies the actual changed scope and requires the same
  passing QA record. Use the feature path when the change needs a new contract.
- **Standard feature (`Standard` tier) and high-risk (`High-assurance` tier)
  routes.** Changes that introduce new contract obligations or modify schemas
  (`standard-feature`), or touch security/isolation, authority verification, or
  persistent-runtime boundaries (`high-risk`), MUST use the full Loop 1 and
  Loop 2 state machine (`high-risk` additionally requires capability preflight
  and convergent review or the isolation boundary suite).

## 3. Loop 2 — Post-Code Repair

```text
Generator implements the approved contract's scope ONLY
        |
        v
Validator Mode B  (post-code implementation gate, standard/AGF.md Sec 3)
   - runs a diff against the pre-implementation state
   - confirms every contracted deliverable is present
   - confirms ONLY contracted files were touched
   - confirms no scope crept in beyond the contract
        |
        v
   Approved?  --No--> Generator reworks with the rejection's failure report
        |               (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Evaluator executes the contract's verification commands independently
   -> QA verdict (.agent/qa/NNN.json, pass/fail + evidence)
        |
        v
   Verdict == pass?  --No--> Generator reworks with the QA failure report
        |                     (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Evidence capture gate
   - every required verification has an externalised evidence file
   - the QA verdict references those paths and every path exists
   - command/result and actual exit status are recorded
        |
        v
   Complete?  --No--> Generator/Orchestrator repairs the evidence record
        |              (bounded by the circuit breaker, Section 5 below)
       Yes
        v
Durable state advances: feature marked complete, next eligible feature selected
per the Dependency Enforcement Rule (00_planning.md Sec 5).
```

A Generator implementing Loop 2 MUST implement only the contracted scope. If,
during implementation, the Generator discovers the contract needs a substantive
change to its goals, `non_goals`, acceptance intent, or security/isolation
boundaries, it MUST stop and propose a contract revision — re-entering Loop 1 —
rather than silently expanding scope under cover of "finishing the job." For a
bounded mechanical update (adding a low-risk supporting file or correcting a
non-vacuous verification command while `feature_id`, `non_goals`, and security
invariants remain unchanged), the Orchestrator may validate and record a
structured amendment via `tools/start_path.py amend-contract`. If an amendment
adds high-risk/schema/governance paths or alters acceptance criteria,
`amend-contract` classifies it as `semantic`, sets `status: "proposed"` with
`re_approval_required: true`, and requires Loop 1 re-approval.

**Evidence is a completion gate, not post-processing.** A passing QA JSON block
proves the Evaluator's decision, but the feature remains `in_progress` until the
Orchestrator verifies that every contracted verification has a corresponding
externalised file under `.agent/evidence/`, that the QA verdict references those
paths, and that each referenced path exists and records the command/result plus
the actual exit status. Use `tools/start_path.py preflight` before a governed
attempt, `tools/start_path.py capture` to write exclusive per-execution evidence
files (recording command `argv`, `cwd`, `revision`, `duration_ms`,
`completion_state`, and `exit_code` without silently overwriting prior
attempts), and `tools/start_path.py publish` + `tools/start_path.py
build-receipt` to publish post-execution outputs and construct closed 12-field
capture records compatible with `verify_stage_receipt` / `tools/start_path.py
resume`. Missing or unreferenced evidence is a Loop 2 failure and uses the same
bounded repair loop; it is never filled in after the feature is marked complete.

## 4. The JSON Verdict Parse Rule

Every gate in both loops above — Validator Mode A, Validator Mode B, the
Evaluator's contract review, and the Evaluator's QA verdict — culminates in a
machine-parseable JSON verdict block. Advancement past that gate is permitted
**only** when all four conditions hold simultaneously:

```text
final_verdict.approved === true
AND issues.length === 0
AND missing_acceptance_coverage.length === 0
AND unsupported_claims.length === 0
```

This is restated here, not redefined — `standard/AGF.md` Section 4 is
authoritative for the rule itself. The load-bearing consequence for this
protocol is: **prose framing never substitutes for the JSON block.** A report
that reads "mostly approved, one minor note" is a rejection if its JSON verdict
carries a non-empty `issues` array. Conversely, blocking findings (`issues`,
`missing_acceptance_coverage`, `unsupported_claims`, `required_fixes`) MUST
cite concrete evidence or specification defects; optional suggestions and minor
observations belong in `advisory_minor` (`convergent_agf_verdict` /
`tools/start_path.py check-verdict`) and do not block advancement when the
blocking arrays are empty. An orchestrator or Generator reading a gate result
MUST parse only the JSON block to decide whether to advance.

## 5. Circuit Breaker Cross-Reference

Both loops above contain steps that can fail and be retried: Loop 1's contract
revision step and Loop 2's implementation or evidence rework steps. Every
repeatable step is governed by `03_circuit_breaker.md`: task-wide evidence
retains failures across step names and output directories. Three failures with
one signature or six failed executions across changing signatures stop the
task. Only explicit finite task-scoped operator recovery reopens its budget;
narratives, amendments and decomposition labels do not. Safety, isolation and
authority breaches remain immediate hard stops.

Freeze source and verification policy before final QA. Reuse valid captures for
the same candidate and required checks. A passing run does not trigger another
review or QA loop without a concrete source change, failure or unresolved
acceptance issue. New design work belongs in a separate bounded change.

## 6. Handoff Out

When Loop 2 has both a passing QA verdict **and** a passing evidence-capture
gate, the Orchestrator updates durable state (`04_tool_driven_state.md`) to
reflect completion. Control then returns to `00_planning.md` Section 5 (the
Dependency Enforcement Rule) to select the next eligible feature.

## 7. References

- `standard/AGF.md` — the agent roles (the coordinating Orchestrator and the
  four execution roles), the Dual Validator Gate, and the authoritative
  definition of the JSON Verdict Parse Rule.
- `00_planning.md` — produces the eligible feature this loop consumes, and
  receives control back on completion via the Dependency Enforcement Rule.
- `02_adversarial_tdd.md` — the independence and rigor requirements binding the
  Evaluator's contract review and QA verdict steps above.
- `03_circuit_breaker.md` — the work-specific diagnostic stopping policy
  (initial 3-step strategy ladder, bounded continuation or decomposition when
  invariants hold, and hard stops on repeated unresolved defect signatures or
  invariant/authority breaches) governing every revision and rework step named
  in Sections 2, 3, and 5 of this document.
- `04_tool_driven_state.md` — the durable-state artifacts (contracts, QA
  verdicts, run state) this loop reads from and writes to at every stage.
