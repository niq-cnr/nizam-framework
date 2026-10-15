---
id: nizam-phase021-product-spec
title: "Phase 021 — Receipt Input Read Maintenance"
description: "Selected measured maintenance of per-call immutable receipt input reads; independent implementation and delivery gates remain."
version: 0.1.1
status: active
authoritative_source: .agent/product_spec_021.md
change_log:
  - version: "0.1.1"
    date: "2026-10-15"
    summary: "Record delegated activation and selected2000/2600 after clean PR104 merge; no implementation or main-CI pass claimed."
  - version: "0.1.0"
    date: "2026-10-15"
    summary: "Propose pending 133 from actual candidate profiling, preserving receipt semantics and existing runtime plans."
---

# Phase 021

Balanced real-task correctness, recovery, delivery time/cost and ease of use guide this maintenance.

Feature **133** is active in this separate maintenance phase under the recorded
[delegated selection](evidence/133/activation-decision.json), applied after PR 104
merged normally at `c8ef3cd44dd795ae249769b79a99ef4ebf3f0ad7`. Root selected
2000/2600 under operator delegation; these are not verbatim operator figures.
Independent frozen tests, bundle review and intended red remain before product work.
Features 129–132 remain phase 020; profiles 124–125 remain phase 019. Preserve the
existing 017 → 016 → 018 → 020 → 019 plan and all original allowances. Root may select
serialized maintenance ahead of 020; 133 is not a required dependency of 020.

## Measured basis and smallest target

The [immutable observation](evidence/performance-maintenance/attribution1/report.json)
at `0193deb10f82281220f352f5e6c006a6a5967c65`, SHA-256
`7b7314e0477fff5affd6d92e00d4d23f4db6f34ac7d8f0a74f9d24c4311a066d`,
records one candidate-only cProfile run: actual 0, 3077.414944s, full physical and
installed preservation. It observed 744,019 subprocess.run calls; select.poll had
1704.955111s exclusive time. `_receipt_candidate` ran 1480 times (767.648501s
cumulative), calling `_entry_blob` 119,880 times (738.420420s on that caller edge).
These cumulative values overlap; they do not establish child CPU, individual Git
command cost, profiling overhead, optimization speedup or comparative superiority.
Fixture construction and preservation are separate targets outside this tranche.

Limit product work to `_receipt_candidate` in tools/workflow_assurance.py:
resolve its immutable input reads in batches per invocation using the existing
`blobs` helper. Preserve exact commit/tree/path/blob/mode/digest/ancestry/origin,
current file reads, environment, canonical owned-record masking and all rejection
predicates. Keep `_entry_blob` behavior unchanged for every other consumer.
No facts or decisions survive the call; no global, cross-call or cross-root cache.
Keep physical observations fresh, including existing higher-level hardlink checks.
Do not optimize fixture lifecycle, snapshots, other verifiers, trust rules or CI.

## Eligibility and execution order

Planning and both independent pre-code reviews may overlap PR 104 CI. Source work
requires recorded phase activation and budget disposition, an approved contract,
Mode A and independent contract-review approval, and PR 104's normal merge after
all six required PR checks pass. Work proceeds on a separate branch; required old
main CI may run concurrently. Its five successful jobs are required before new
maintenance integration/merge. Never cancel an older required run to expedite 133.

A change to protected Source stales the historical 123 current-ready proof. Keep
that proof and its immutable policy as assessment-time evidence; do not rebind it,
rerun the old experiment merely to relabel it, or claim new current controls-ready.
New 133 fixtures and capable CI must assess the new candidate independently.
Both post-code Mode B and fresh independent QA precede Root evidence capture and
canonical completion. Evaluator authors/freezes independent regression tests;
Generator implements only the approved scope. Root alone owns lifecycle/counters.

## Acceptance

The feature list names atomic future commands; the new test runner does not yet
exist and its commands cannot pass by planning. Its differential oracle uses the
shipped unchanged `_entry_blob` on equivalent independently built synthetic Git
inputs, delegating counted operations to real Git. No test depends on unshipped
historical objects, a deep clone, a paid model or elapsed-time thresholds.

Require at least 50% fewer real immutable-input Git child processes on the same
valid multi-path readset, with identical observed bytes/modes and successful
receipt semantics. Preserve rejection semantics for each isolated defect and
fresh reads after intervening mutations/restoration; never substitute setup error
for the intended rejection. Cover exact commits/tree/ancestry/origin, missing or
nonblob entries, executable modes, literal unusual paths, current symlink/type/
bytes/mode changes, canonical owned/unowned fields and environment drift.

Retain every original 48 ordered Workflow Assurance case and all 166 fixture checks;
new independent coverage may strengthen the bank, with its actual count recorded.
Run both compliance modes and all currently required capable-CI jobs on the exact
new PR head, then observe its merge and main CI. Future phase 020's sixth runtime
job remains future. Capture actual commands/exits/revisions, raw streams and full
preservation, plus exactly one independently selected additional adversarial check.
No wall-time speedup or balanced competitor result is a completion requirement.

## Selected cost and accounting

Root selected **2000 lines**, ceiling **2600**: product 150, independent tests 450,
process 1400. Process includes carried attribution preparation/report/release/index
budget 300, this planning pair 220, contract 170, independent reviews 300,
QA/capture/CI integration 300 and closeout 110. Buckets already include overhead.
Charge actual maintained preparation and failed attempts once, including the
original attribution proposal/executor glue; unchanged capture code is reused by
immutable reference. Raw observed frames/profile remain distinct from authored
analysis and decisions; mixed maintained reports are not a free evidence bucket.

Historical 123 remains frozen 2685 plus authored-source overlay 5002, source-only
phase lower bound 11990 versus 9360 and conservative phase 26657. Its exception does
not authorize a new allowance or reset any baseline. Root records this tranche's
actual base, carried preparation and final endpoint separately; do not remeasure
or transfer 123 costs. Reuse existing capture tooling; defer its generic promotion.
No release/tag/install, runtime canary, other phase activation or superiority follows.
