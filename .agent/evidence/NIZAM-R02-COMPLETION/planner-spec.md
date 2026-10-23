---
id: nizam-r02-completion-planner-spec
title: "NIZAM-R02-COMPLETION: bounded F1/F2 repair specification"
description: "Preserve approved bugfix contract context and bind inherited dirty exceptions to observed content."
version: 0.1.0
status: draft
authoritative_source: .agent/evidence/NIZAM-R02-COMPLETION/planner-spec.md
---

# Purpose and verified baseline

Repair two deterministic completion defects in upstream `niq-cnr/nizam-framework`
at `00e0bcb1bd16ba2ddaf5774153bbf2c1e05244a6`:

1. **F1:** A bugfix of a protected/schema path can begin under a valid approved
   contract, but `done` drops that contract context and rejects the same repair.
2. **F2:** An unrelated file already dirty at `begin` is exempted at `done` by its
   status code and pathname alone. Further changes to its bytes, staged content,
   executable mode, symlink target, or renamed destination can pass unnoticed.

The external diagnostic `planner-reproduce-f1f2.py` ran against unchanged product
source using nine disposable real Git repositories. Its aggregate exit was 1:
seven requirements failed, while the proposed-contract rejection and unchanged
inherited-edit controls passed. Full actual command/output records are under
`planner-baseline-01/`; `planner-baseline-01.execution.json` records the top-level
invocation. This is diagnostic evidence, not independent implementation acceptance.

## Authorized product boundary

Modify only `tools/start_path.py` and `tools/test_start_path.py`. Keep the public
CLI stable. Task-owned planning, contract, review, QA and evidence records belong
to this task's separate governance work; they do not widen the product boundary.

## Required behavior

### R1 — Preserve and revalidate contract context

The supported `begin bugfix` and `done bugfix` paths must use the same contract
identity and scope eligibility semantics. An approved, implemented or complete
contract that currently covers every scoped path remains usable at completion.
The completion path must still reject a missing, proposed, identity-mismatched,
revoked or out-of-scope contract. Do not skip eligibility or contract validation
to obtain the positive result. Do not permit any `.nizam/` write.

### R2 — Bound inherited dirty exceptions to observed state

A fresh Git-backed task base must record a versioned, content-bound observation
of every pre-existing dirty path that could otherwise be exempted. The snapshot
must distinguish the index and working tree; a status string is insufficient.

For each affected path, record the relevant index stage/mode/object identity and
the worktree object's kind, relevant permission bits and byte identity. Observe
symlink link text without following the link. Represent a genuinely absent
endpoint explicitly, including deleted files and original rename endpoints.
Renames/copies require both endpoints. Do not copy source bytes into the marker.

At `done`, an unrelated inherited path is exempt only when its original observed
state remains equal. Compare every original inherited path even when it is no
longer reported by current `git status`; restoring somebody else's dirty file,
deleting an inherited untracked file, or changing a rename endpoint is still a
new out-of-scope action. Additional declared edits are allowed. New undeclared
committed, staged, unstaged and untracked paths remain rejected.

### R3 — Safe task-base compatibility

Use a new marker format/version for content-bound snapshots. Existing markers
are immutable: `begin` must never refresh their base revision, recorded dirty
state or fingerprints. Repeated `begin` is idempotent only for a valid compatible
marker. Validate its task identity, version, base commit and snapshot structure.

A version-1 marker may continue only when every pre-existing entry belongs to
the declared scope or the existing task-owned metadata exclusions, so no
unrelated dirty exemption is needed. If it contains an unrelated pre-existing
entry, the old record has insufficient evidence to prove preservation. Fail
closed with a clear recovery diagnostic that preserves that record and the
working files. Require reviewed restart under a new task identity or a separate
explicit recovery process; do not infer old fingerprints from today's state,
delete the old marker, silently re-pin, or invent a migration proof. Unknown or
malformed marker versions fail closed.

### R4 — Fail closed on observation errors

For a Git-backed task, failed Git queries, malformed/partial index or status
records, unreadable required objects, unsafe path traversal, and unsupported
object kinds must be errors, never empty observations or preservation proof.
Distinguish a deliberately represented missing endpoint from a failed read.
Do not follow ancestor symlinks outside the repository or block reading a FIFO.
Unsupported submodule/conflicted-index states may be rejected explicitly rather
than implementing a new recursive snapshot model in this repair.

Retain the existing genuinely non-Git local behavior, without treating a failed
Git observation in an already Git-backed task as permission to fall back to it.
All queries remain read-only. The repair must not change files, permissions,
the Git index, inherited evidence or task baselines as part of verification.

### R5 — Preserve metadata and surrounding behavior

Retain the exact existing task-owned evidence/QA exclusions; do not turn them
into a blanket `.agent/` exemption. Shared authority/state such as
`.agent/run_state.json` remains outside an unrelated task's scope. Do not remove
or compact evidence. Do not modify installed `.nizam/`, existing phase020 work,
CI workflows, schemas, release pins, publication adapters, sandbox policies,
QA/capture freshness, receipt-candidate binding or continuation-authority rules.
The latter known findings require separate bounded work.

## Verification and handoff

The Generator must add durable executable regressions to the existing
`tools/test_start_path.py` suite. Use real temporary Git repositories for state
semantics. Narrowly inject observation failures only where real portable
fixtures cannot deterministically trigger them. Test zero-byte files as valid
content identities. Include positive controls for preserved dirty state and
negative controls for invalid contract authority; a suite that only rejects
everything is insufficient.

The exact acceptance matrix is in `planner-contract-requirements.json`. Proposed
verification commands are the unchanged external F1/F2 probe, the existing
start-path regression suite, and the repository's existing compliance gate.
Independent Validator Mode A and Evaluator contract review precede product
implementation. Independent Mode B and QA follow it. Root owns official
classification, preflight, lifecycle/counters and the qualification decision;
this plan does not waive any unsuccessful preflight or isolation gate.
