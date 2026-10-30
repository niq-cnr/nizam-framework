---
id: task-budget-reservations
title: "Task failure capacity and pending reservations"
description: "Atomic derived capacity preserves bounded parallelism and truthful unknown execution outcomes."
version: 1.0.0
status: active
authoritative_source: docs/architecture/task-budget-reservations.md
---

# Task failure capacity and pending reservations

The existing task failure ceiling applies across steps and output directories.
Checking only completed failures before reserving allows concurrent callers to
authorize more failures than the ceiling. Current native capture therefore
checks its continuation policy while holding the existing common task lock and
creates the existing reservation before releasing that lock. Command execution
runs after release. External allocation uses the same task lock and its existing
serialized permit ledger transition.

Unresolved native reservation markers occupy capacity until a matching validated
terminal capture exists. Unconsumed external permits occupy capacity according to
their existing allocated/admitted step counters, cross-checked against permit
records. These are derived values, not a second budget or owner ledger. Actual
failed counts remain actual observed failures. A process interruption without
terminal evidence retains its reservation after restart; changing the step or
output directory does not erase it. A retry of the same step requires its prior
outcome.

Independent steps can overlap while both remaining task and signature capacities
permit another reservation. Without existing finite operator recovery, the
potential capacity is the minimum of `6 - observed failures` and
`3 - maximum observed same-signature failures`; each unresolved reservation
occupies one slot. The conservative signature reservation does not guess a
future defect or trust changing labels to create allowance. Three initially
available slots can execute concurrently. A successful terminal result frees
its slot without adding a failure; a failure converts its pending slot to one
observed failure. Fresh locked evaluation prevents an authorization checked
before a sixth failure from dispatching after that failure is published.

The existing channel-specific finite operator recovery remains the only recovery
authority. It preserves all prior failure and reservation history and does not
clear same-step pending execution or corrupt evidence. Explicit recovery changes
only the existing finite allowance and signature policy. Current source refuses
invalid, contradictory or partial matching history rather than normalizing it or
inventing a terminal capture. Existing orphan-publication reconciliation remains
separate from permission to execute again.

Capacity holds identify observed failures and unresolved reservations separately.
External callers distinguish `pending_task_capacity` and
`pending_signature_capacity` from actual `task_ceiling_exhausted` or
`signature_ceiling_exhausted`. A pending hold means await or reconcile actual
outcomes; it does not grant another execution, a standalone fallback or automatic
operator authority. Native CLI holds use the same distinction in diagnostics.

The supported shared lock profile remains cooperating same-effective-user POSIX
controllers, with fixed private coordination outside the assessed worktree.
Pending markers and permits still live in the existing evidence histories. Mixed
native/external history cannot be converted automatically into a new allowance.
Selecting a new source requires quiescing superseded controllers and preserving
unknown outcomes; mixed old/new controller concurrency is not qualified.

The independent `tools/test_task_budget_reservations.py` corpus exercises real
public captures, actual subprocess overlap, the seven-dispatch overrun, a stale
pre-reservation check, non-Git interruption/restart, success release, corrupt
markers, external cross-step capacity and existing finite recovery. Authority
documents used in temporary fixtures are synthetic, not real operator consent.
