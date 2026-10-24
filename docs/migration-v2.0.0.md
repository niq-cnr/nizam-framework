---
id: nizam-migration-v2-0-0
title: "Migrating from Nizam v1.x to v2.0.0"
description: "Consumer migration for typed verification, assessed structured QA, immutable task context, exact receipt replay and finite retry authority."
version: 1.0.0
status: active
authoritative_source: docs/migration-v2.0.0.md
last_audited: "2026-10-24"
tags: [migration, v2, breaking-change, consumer]
change_log:
  - version: "1.0.0"
    date: "2026-10-24"
    summary: "Initial migration guide for mandatory completion proof and finite retry controls in v2.0.0."
---

# Migrating from v1.x to v2.0.0

Version 2.0.0 changes mandatory completion and retry behavior. Records that were
accepted by a v1.x completion gate may be insufficient for a new transition.
Historical records remain readable; that does not upgrade their proof.

This document accompanies release preparation. Adopt the published immutable
`v2.0.0` tag only after recording the consumer's upgrade authorization. Obtain
its exact commit from the annotated tag and verify the payload against that
commit. Never reuse the v1.11.0 SHA beside a v2.0.0 tag, hand-edit installed
`.nizam/` files, or treat a successful bootstrap as commissioning or production
readiness. Rehearse in a disposable consumer first and preserve existing work.
The framework's local self-installation is a separate consumer record.

## Start a task with a pinned verification inventory

Before `begin`, put a nonempty `verification` array in the scope/intent. A feature
uses the approved contract's verification array. Each check needs a unique ID,
an exact unique argument array, integer expected exit, proof kind and diagnostic:

```json
{
  "id": "unit-tests",
  "argv": ["python3", "-m", "unittest"],
  "expected_exit": 0,
  "proof_kind": "success",
  "diagnostic": null
}
```

Contract verification entries also retain `acceptance_test` and `command` for
readers. A historical prose `expected_exit` can remain in an old contract, but
new typed proof requires an integer and all typed fields. A submitted QA record
cannot choose or shorten the required inventory.

Use the installed entry point with a fresh task ID:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py begin bugfix --id repair-v2
```

`begin` preserves the task's authorization and separate index/worktree identities
in its version-2 base. Completion rechecks contract identity, current approval
and scope. It compares every inherited endpoint, including disappeared paths
and rename endpoints, across committed, staged, unstaged and untracked changes.
Unchanged unrelated work can remain inherited; a changed path needs task scope.

If an existing base lacks the required inventory, authorization or inherited
observations, preserve it and begin a fresh task. Do not overwrite it, regenerate
its initial observations from current bytes, or silently reset its history.

## Produce assessed, structured execution proof

Follow the full producer workflow in
[tools/interface.md Section 4.5](../tools/interface.md#45-structured-qa-proof-for-completion-and-receipt-prerequisites).
Use the actual installed `.nizam/tools` modules and `.nizam/schema` files.

1. Commit the assessed source and complete immutable authorization records.
   Include actual verifier/schema inputs and every material command dependency.
   For routes this includes the scope/intent, task base, bugfix cause when used,
   and applicable contract. No ownership mask may hide changes to these records.
2. Normalize the trusted inventory with `qa_required_checks` and compute
   `qa_context_sha256` from the task identity, sorted whole-record authorization
   digests and inventory. Set and assess `NIZAM_QA_CONTEXT_SHA256` and
   `NIZAM_QA_EXECUTION_ROOT`, the canonical absolute producer repository path.
3. Save an assessed identity manifest. Feature assessment keeps the strict
   `assess_repository` rules. A bounded nonfeature route may use
   `assess_route_candidate` to preserve unchanged unrelated inherited work;
   selected dependencies must still match the anchor, index and worktree.
4. Execute each pinned argument array with installed `start_path.py capture`,
   supplying the manifest path, matching task ID and requested proof kind.
   Retain the structured capture and exact stdout/stderr bytes.
5. Produce a schema-valid QA verdict with `proof_version: 2`, a digest-checked
   `candidate_ref`, and one `{id, capture}` reference for every required check.
   Keep exact aggregate counts, favorable verdict and empty blocking arrays.

A Git commit identity, a manifest file digest and the canonical candidate digest
are different bindings. A bare commit or arbitrary 64-character string does not
establish assessed proof. A passing summary cannot override contradictory
capture contents, wrong arguments, missing streams or changed inputs.

The capture producer verifies its execution root before running. A replaying
consumer in an equivalent checkout may have a different filesystem path, but
must explicitly supply the original reserved environment values and verify the
same repository, source, inputs, index and authorization context. The original
capture is preserved; it is not relabeled as a new execution.

Changing a consumed authorization record, even a contract lifecycle status,
requires a fresh assessment and execution. Keep completion lifecycle bookkeeping
in separate owned records when retaining replayable approved-contract proof.

## Preserve negative tests, empty streams and receipt checks

An ordinary success needs observed exit zero and a consistent successful
capture. An expected semantic negative needs its pinned exit and exact complete
UTF-8 diagnostic line. A successful wrapper must actually assert its child's
expected refusal and explicitly request semantic-negative proof. An ordinary
failed command cannot be renamed as success.

A zero-byte stdout or stderr is valid when the referenced digest matches those
exact bytes. A missing file, failed read or altered stream is refused.

Direct completion, route receipts and feature receipt QA prerequisites use the
same structured proof rule. Receipts retain their own command checks too.
Canonical receipt replay accepts only that receipt's exact status/time change
and one deterministic appended history event, with the baseline, worktree,
index, modes and HEAD checked. Forged or extra state edits remain refusals;
ordinary `done` does not gain a general runtime-state exception.

## Respect finite task-wide failure budgets

The default ceiling is six failed executions per task across steps, output
directories and sessions, with a ceiling of three failures of one signature.
Configured positive integer step limits remain finite. Successful checks do not
erase failures. Hypotheses, changed output paths, amendments and decomposition
labels do not create retry budget. Stop on invariant or authority breaches.

Only an explicit task-scoped operator recovery can reopen a budget. The
Orchestrator records `circuit_breaker[task_id].operator_recovery` with exactly
`task_id`, `approved: true`, finite positive `max_task_attempts`, `after_capture`
and `authority_ref`. The referenced operator record must contain the same
fields plus `role: "operator"`; `after_capture` must name a retained failed
capture for that task. The finite ceiling is checked against existing failure
history; history is not erased, and step limits are not silently raised.

Keep all failed evidence, diagnose the concrete failure and obtain any required
bounded recovery authority before another attempt. Do not invent continuation
flags or repeatedly re-run passing suites without a new change or failure.
