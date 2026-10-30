---
id: receipt-state-publication
title: "Receipt state publication and recovery"
description: "Durability and concurrency boundaries for the existing verified receipt resume operation."
version: 1.0.0
status: active
authoritative_source: docs/architecture/receipt-state-publication.md
---

# Receipt state publication and recovery

The existing `resume_from_receipt` implementation calls
`workflow_assurance.plan_receipt_transition` to verify a receipt and derive one
owned state transition. Publication does not reinterpret its proof, create a
new receipt authority, or replenish an attempt budget.

Read-only planning checks the current state and proof without creating a lock
or changing files. Apply requires a regular state file inside the target
repository and rejects symlink identity before canonical resolution. It uses
a stable per-state OS lock under the worktree's Git administrative directory,
resolved with the hardened read-only `git rev-parse --absolute-git-dir` query
and keyed by the canonical target path. Coordination metadata therefore stays
outside the assessed candidate inventory, including linked worktrees; missing
Git administrative metadata refuses without a worktree fallback. The lock covers reading current state, real
receipt verification, planning and publication. Each contender therefore
plans against the preceding completed publication rather than a stale copy.

For an advance, publication writes complete JSON to an exclusive temporary
file in the state's directory, preserves the original file permissions,
flushes and fsyncs the file, atomically replaces the state, and fsyncs its
directory before reporting `applied: true`. The existing noop and republish
decisions do not rewrite state. Identical receipts produce one advance and
then a noop; conflicting receipt advancement still refuses through the
existing proof interpretation.

An interruption before replacement leaves the complete old state. An
interruption after replacement leaves complete new state; exact receipt
replay observes the recorded transition and does not append another event.
Before creating the same-directory temporary, apply durably writes a small
publication intent in Git administrative metadata under the same state lock.
The intent binds the target and random temporary path, old and complete new
content hashes, byte length, original mode, and exact policy and receipt
digests. It supplies no state publication authority. Exact replay can remove
only the complete matching temporary while the original state is unchanged,
then reruns real receipt verification and planning. Missing temporary files
are reconciled only against the exact old or new state. Directory fsync
confirms cleanup. Read-only planning never performs recovery.

Unknown, partial, corrupt or changed-mode temporary files and mismatched
policy, receipt or state identities remain preserved and cause a recovery
hold. Recovery does not delete arbitrary prefixed files or exempt any path
from task eligibility. Unfinished temporary files are not authoritative
state. If publication or
directory durability cannot be confirmed, the operation reports failure
rather than applied success. The host inspects current state and replays the
same verified receipt; it must not infer a new execution or reset attempts.

The supported profile requires POSIX advisory locking, atomic replacement and
file/directory fsync. It serializes cooperating users of this entrypoint;
unrestricted host code can still modify files outside the protocol. A lock
file, source hash or successful local test does not establish OS isolation,
human approval, installed commissioning or an external producer's trust.

The independent `tools/test_resume_durability.py` suite uses the existing
real verified receipt fixture and actual subprocesses. It exercises readonly
invariance, before/after publication interruption, identical and conflicting
concurrency, directory-sync failure, permissions and symlink refusal. All
fixture authorities remain explicitly synthetic.
