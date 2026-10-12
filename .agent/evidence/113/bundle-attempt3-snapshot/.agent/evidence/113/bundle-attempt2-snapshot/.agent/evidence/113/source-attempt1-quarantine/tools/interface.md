---
id: nizam-tools-interface
title: "Runtime-Adapter Interface"
description: "The adapter contract any agent runtime implements to discover, load, and act on the single unified Nizam skill payload (DD-4): discovery, loading, the three abstract operations, and the conformance checklist an integrator ticks through."
version: 0.4.0
status: active
authoritative_source: tools/interface.md
change_log:
  - version: "0.4.0"
    date: "2026-10-12"
    summary: "Add the optional runtime-session adapter surface and conditional checks; preserve the ten mandatory conformance items."
  - version: "0.3.1"
    date: "2026-10-10"
    summary: "PATCH correction (phase-014 feature 108, NDEBT-044 d): Section 5 item 10's no-fabrication rule cites Section 2, Item 5 (Failure behavior), not Item 4 (Manifest resolution). A one-token citation fix; the checklist stays at 10 items."
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "H4: reordered Section 2 Discovery so bootstrapped-consumer .nizam/tools/skill.json discovery runs first, matching bootstrap.sh's .nizam default install layout, with the repository-root tools/skill.json path retained as an explicitly labeled framework-checkout fallback."
  - version: "0.3.0"
    date: "2026-07-10"
    summary: "Fixed a stale Section 2 Item 3 reference to the release-train protocol doc's pre-renumbering filename (a slot-05 path that no longer exists) -> methodology/06_release_train.md, the file's real current name after main's v0.5.x methodology renumbering inserted a new slot-05 doc (methodology/05_eval_and_trace.md) and shifted the release-train protocol doc from slot 05 to slot 06."
---

# Runtime-Adapter Interface

## 1. Overview

This document specifies how an agent runtime — any host environment capable of
reading files, executing commands, and holding instructions in its working
context — discovers and loads the framework's one unified skill payload, and
how that runtime's own native tool primitives satisfy the three abstract
operations the payload's protocols assume. It describes the adapter contract
only. It ships no runtime-specific adapter implementation and no per-runtime
fork directory (DD-4): there is exactly one skill payload, `tools/SKILL.md`,
and every runtime loads that same file.

## 2. Discovery

An agent runtime locates the skill payload as follows:

1. **Bootstrapped-consumer discovery.** In a repository that has bootstrapped
   the Nizam framework via `bootstrap.sh` (`standard/GIP.md` Section 2.1), the
   runtime FIRST looks for `tools/skill.json` under the injected governance
   target directory — by default `.nizam/tools/skill.json` (`bootstrap.sh`'s
   `NIZAM_TARGET_DIR`, which defaults to `.nizam`). If present, this is the
   authoritative manifest for that repository's governed work.
2. **Framework-checkout fallback.** If no `.nizam/tools/skill.json` is found,
   the runtime falls back to a repository-root `tools/skill.json` path — the
   layout this framework repository itself ships at its own root. This
   fallback exists for a framework checkout evaluating itself (rather than a
   bootstrapped consumer repository), and is retained explicitly so it is
   unambiguously distinguishable from the bootstrapped-consumer path above.
3. **Pinned-checkout discovery.** Where a consumer repository instead
   references a pinned Nizam release tag without vendoring the framework's
   files locally, the runtime resolves `tools/skill.json` inside a checkout of
   that pinned tag (see `methodology/06_release_train.md` for the tag/version
   model).
4. **Manifest resolution.** Once `tools/skill.json` is located, the runtime
   reads its `entry_point` field to resolve the path to the instructions
   payload (`tools/SKILL.md`) and its `capabilities` array to resolve any
   individual protocol module path a task needs, without loading the whole
   framework.
5. **Failure behavior.** If no `tools/skill.json` can be found by any of the
   methods above, the runtime MUST treat the repository as ungoverned by this
   framework for the current task and MUST NOT fabricate governance behavior
   in its absence.

## 3. Loading

Once discovered, the runtime loads the payload as follows:

1. **Inject `SKILL.md` as instructions context.** The full contents of
   `tools/SKILL.md` are made available to the acting agent as system-level or
   skill-level instructions context — the same tier of context the runtime
   uses for its own standing operating instructions — rather than as
   conversational content the agent might discard or deprioritize.
2. **Load on demand, not unconditionally.** Consistent with `SKILL.md`
   Section 1, the runtime injects this payload when the current or upcoming
   task matches one of the triggers that section names, not on every
   invocation regardless of task.
3. **One payload, no forked copies.** The runtime MUST NOT maintain its own
   runtime-specific rewritten copy of `SKILL.md`. If a runtime's native
   instructions-loading mechanism requires a wrapper file (for example, a
   short pointer file in a runtime-specific configuration location), that
   wrapper MUST reference or include `tools/SKILL.md` verbatim rather than
   restate or fork its content.

## 4. The Three Abstract Operations

Every protocol document this skill summarizes assumes an agent runtime can
perform exactly three abstract operations. Each runtime's adapter maps these
onto its own native tool-calling primitives; the mapping is the adapter's
entire job.

### 4.1 `read-state`

- **Purpose:** Read the current durable-state content a task needs —
  `NIZAM.json`, a governance module file, or an artifact under a project's
  `.agent/` directory (run state, feature list, a contract, a QA verdict).
- **Inputs:** A repository-relative file path.
- **Outputs:** The file's full content, or a clearly distinguishable
  not-found signal if the path does not resolve on disk.
- **Error behavior:** A runtime whose native read primitive raises an error
  (permission denied, path outside an allowed boundary) MUST surface that
  error to the acting agent rather than silently returning empty content that
  could be mistaken for a legitimately empty file.
- **Native satisfaction:** Any generic file-read capability of the host
  environment satisfies this operation.

### 4.2 `write-evidence`

- **Purpose:** Persist a material result — a proposed or revised document, a
  durable-state update, or an evidence file capturing verification output —
  to its canonical durable location, per the evidence-externalisation rule
  (`methodology/04_tool_driven_state.md` Section 3).
- **Inputs:** A repository-relative destination path and the content to
  write.
- **Outputs:** Confirmation the write completed, sufficient for the acting
  agent to treat the result as durably recorded rather than merely stated in
  conversation.
- **Error behavior:** A failed write (permission denied, disk full, path
  outside an allowed boundary) MUST be surfaced as an error, never silently
  swallowed; a role that cannot confirm its write succeeded MUST NOT report
  the corresponding step as complete (`standard/anti_hallucination.md`, AH-3).
- **Native satisfaction:** Any generic file-write or file-edit capability of
  the host environment satisfies this operation.

### 4.3 `run-verification`

- **Purpose:** Execute a contract's verification commands (or any other
  check the framework's protocols require, such as a schema validation
  command) and capture the command's output and exit code as evidence.
- **Inputs:** A command string, and the working directory it should run in.
- **Outputs:** The command's captured standard output and standard error
  (written to an evidence file per DD-3, not returned inline only) and its
  exit code.
- **Error behavior:** A non-zero exit code is a verification failure, not an
  error the runtime silently retries or reinterprets as success; the acting
  agent decides how to respond (rework, escalate) per the governing protocol.
- **Native satisfaction:** Any generic shell or command-execution capability
  of the host environment satisfies this operation.

## 5. Adapter Conformance Checklist

An integrator adapting a new agent runtime to this framework can verify
conformance against this numbered, objectively checkable list. Every item
MUST be satisfied.

1. The adapter locates `tools/skill.json` via consumer-repo discovery,
   pinned-checkout discovery, or both (Section 2).
2. The adapter resolves `entry_point` from `tools/skill.json` and loads that
   exact file's content — it does not load a paraphrased, summarized, or
   runtime-authored substitute.
3. The adapter injects the loaded payload as instructions/skill-tier context,
   not as ordinary conversational content (Section 3, Item 1).
4. The adapter loads the payload conditionally, based on the triggers
   `tools/SKILL.md Section 1` defines, not unconditionally on every
   invocation.
5. The adapter maintains no forked or rewritten copy of `tools/SKILL.md`
   anywhere in the runtime's own configuration surface (Section 3, Item 3).
6. The adapter provides a `read-state` mapping backed by a real file-read
   primitive, capable of reading any repository-relative path, including
   paths under `.agent/`.
7. The adapter provides a `write-evidence` mapping backed by a real
   file-write primitive, and surfaces write failures as errors rather than
   silent no-ops.
8. The adapter provides a `run-verification` mapping backed by a real
   command-execution primitive, capturing both output and exit code for every
   invocation.
9. The adapter surfaces every operation's error conditions to the acting
   agent rather than suppressing them (Sections 4.1-4.3).
10. The adapter does not fabricate governance behavior when no
    `tools/skill.json` can be discovered (Section 2, Item 5).

## 6. Optional Capability: Live Runtime Sessions

`live_runtime_session` is optional (`required: false`). Adapters that do not claim
it remain conformant under the ten items in Section 5. Only adapters claiming
this capability MUST satisfy the seven calls and conditional S1–S9 checks below.
This is a normative interface, not executable adapter/controller delivery.

| Call | Meaning and execution boundary |
| --- | --- |
| `open-session` | Establish a session and record its owner, generation and lease; do not evaluate project code. |
| `submit-operation` | Admit one authorized project-code operation with correlated identity and limits. |
| `poll-operation` | Read the correlated observed outcome without executing project observation callbacks. |
| `cancel-operation` | Request cancellation of the correlated operation; requesting does not confirm stopping or rollback. |
| `transfer-session` | Explicitly change owner and increment lease_epoch; preserve or resolve outstanding work without evaluating project code. |
| `reattach-session` | Recover and check owner, generation, lease and outstanding operation; do not transfer ownership or evaluate project code. |
| `close-session` | Observe correlated closure and preserve unresolved effects/resources; do not evaluate project code or claim rollback. |

Only `submit-operation` executes project code. Its `kind` is exactly
`load_source`, `compile_source`, `evaluate`, `run_tests` or `observe`.
Observation invokes project code in the binding and needs the same authorization
and serial operation stream as evaluation. Existing `read-state` reads durable
session status; there is no separate status call or endpoint. Control calls MUST
NOT invoke project printers, arbitrary restarts or observation callbacks.

Requests correlate `operation_id` and `session_id`, `expected_generation`
(`counter`, `nonce`), `expected_lease_epoch`, and `requester` (`principal_kind`,
`role`, `agent_id`), with `contract_id`, `step_key` and `attempt`. A submitted
operation supplies `kind`, `payload`, `context` (`working_dir`, `namespace`,
`reader_config_ref`, `test_config_ref`) and `limits`. These abstract request
inputs map to the existing records; they add no required schema fields. Unknown
identity or continuity cannot authorize execution. Reattachment reads outstanding
work before any submit, preserves attempt identity and never grants new authority.

Terminal operation statuses are `completed`, `condition_signalled`, `cancelled`,
`terminated` and `rejected`. Nonterminal statuses are `running`,
`cancel_requested` and `unknown`. The optional `debugger_paused` is not emitted
in v1 and is not an additional status in the existing record schemas.
A timeout records `wait_outcome: stopped_waiting`; it stops waiting only and
leaves execution and its busy lane outstanding until an observed outcome resolves
it. `cancelled` requires observed stopping and `cancellation_confirmed: true`;
consistency and remaining effects must be assessed separately.

Use the existing [permission classes](../standard/permission_classes.md):
`runtime.session.lifecycle` gives the Orchestrator open/transfer/close authority
only, without project-code execution; `runtime.session.operate` confines the
Generator to its own development session; `runtime.session.accept` gives the
Evaluator independent fresh acceptance. Reattachment grants no additional
permission. Review trials receive no endpoint or session permission.

| Conditional check | Required behavior for a claiming adapter |
| --- | --- |
| S1 | Session and operation records validate against the existing schemas; record validity proves no live behavior. |
| S2 | Reject stale generation or lease before execution and verify the requester is the current owner. |
| S3 | At most one operation is in flight; preserve or resolve outstanding work before conflicting submit or lifecycle transfer. |
| S4 | A timeout stops waiting only and never reports execution stopped; preserve the outstanding operation and busy lane. |
| S5 | Capture conditions and applicable restarts before unwind; a failed partial load or compile never claims image consistency. |
| S6 | Reject review-trial requests before execution; trials receive no endpoint or session permission. |
| S7 | Lifecycle calls never evaluate project code, including observation callbacks. |
| S8 | Session results and provenance are never acceptance evidence; acceptance requires an independent fresh process, fresh build and hermetic inputs. |
| S9 | Attempt counters and contract/step/attempt identity survive new generation, process, subagent and stage; only the Orchestrator owns coordination counters. |

The [neutral protocol](../methodology/10_live_runtime_sessions.md) and
[SBCL reference binding](../methodology/11_sbcl_runtime_binding.md) define these
consumer duties. Existing schema/C12 checks establish declared record validity
only; they cannot prove live ownership, runtime conformance or source/heap identity.
Executable controller/adapter/SBCL enforcement and all thirteen live proofs remain
pending phase016 features115–120. The installed v1.5.0 payload is unchanged.

## 7. References

- `tools/skill.json` — the capability manifest an adapter discovers and
  resolves per Section 2.
- `tools/SKILL.md` — the single instructions payload an adapter loads per
  Section 3.
- `methodology/04_tool_driven_state.md` — the evidence-externalisation and
  durable-state rules the `write-evidence` operation exists to satisfy.
- `standard/anti_hallucination.md` — the constraints (in particular AH-3)
  that bind how a runtime's adapter must handle write and verification
  failures.
- [Live Runtime Sessions](../methodology/10_live_runtime_sessions.md) and
  [SBCL Runtime Binding](../methodology/11_sbcl_runtime_binding.md) — normative
  optional-session semantics and reference profile.
- [Session schema](../schema/runtime_session.schema.json) and
  [operation schema](../schema/runtime_operation.schema.json) — existing records,
  not live runtime proof.
