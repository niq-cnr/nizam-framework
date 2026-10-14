---
id: nizam-phase018-product-spec
title: "Phase 018 — Workflow Assurance — Controls"
description: "Bounded WA control plan, recorded authorization and future independent acceptance gates."
version: 0.1.2
status: active
authoritative_source: .agent/product_spec_018.md
change_log:
  - version: "0.1.2"
    date: "2026-10-14"
    summary: "Clarify activated018 and captured119 position; preserve requirements, DAG, estimates and independent gates for120–123."
  - version: "0.1.1"
    date: "2026-10-14"
    summary: "Bind Root-applied standing authority and actual118/127 capture receipts; preserve pending lifecycle, scope, budgets and future acceptance."
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Plan pending features only; activation, implementation and budget approval remain future."
---

# Phase 018 plan

NIP-0004 accepted scope and six operator selections are inputs. [Root’s authority receipt](evidence/phase018-preflight/activation-authority.json) applies standing operator logical-next-steps authorization to existing features 119–123 and the unchanged 7,200/9,360 estimate/ceiling under H-PHASE-018; it does not assert a new numeric user quote or rely on earlier 017/016 approvals.
[Independent activation and Root promotion](evidence/phase018-preflight/activation-result.json) made phase018 active. [Feature119 is captured complete](evidence/119/evidence-capture.json); 120–123 remain pending. This planning document grants no implementation approval: each later contract still requires both pre-code gates and reviewed independent acceptance.
[Foundation 118](evidence/118/evidence-capture.json) and [controller semantics 127](evidence/127/evidence-capture.json) are captured prerequisites; 128, full phase-016 closure and later 131 are not added prerequisites. [Postmerge main CI](evidence/128/pr99-main-ci.json) passed all five jobs on PR 99 merge `fcd0584`; this integration proof does not execute future 119–123 acceptance.
Records for phases 015 and 014, installed v1.5.0, release versions and Open debts NDEBT-040/NDEBT-034 remain unchanged. Local adoption covers niq-cnr/nizam-framework only; planning is not activation.

## Architecture and external prerequisites

Feature 119 maps convergent blockers into AGF issues/required fixes and keeps advisory
minor explicit; no advisory can clear carried blockers or any nonempty array.
Feature 120 mechanizes prerequisites/actual exits and idempotent receipt recovery using
existing validate.sh/verify_lib/schemas and one coordination authority. Pending,
running, failed, invalidated, unrun and setup-error outcomes cannot pass. Feature 121 binds
dependency/conflict lanes, isolated attempts and owned rollback. Feature 122 routes by
evidenced cause inside the existing three-attempt limit; no extra cause budget.
Feature 123 verifies the same candidate on capable CI within the existing five-job
workflow, observing actual emitted job names/checkout identity, then dogfoods and
closes. It introduces no separate scheduler or new WA job. Case 8's real runtime
endpoint mechanism and full 13-case live proof remain phase 020 obligations.

Historical planning recommendation (2026-10-12; retained rather than replacing A09):
Recommended order: phase 017 foundation → phase 016 core → phase 018 controls →
phase 020 fresh acceptance → phase 019 profiles. This is a proposed order requiring future activation, not an operator
selection. Preserve historical A09-after-NIP3-120 edge; propose its supersession
explicitly for early identity/sealed ownership. Phase 018 depends specifically on core feature 127,
not completion of split NIP3-116's later CI feature 131. A15 remains after controller feature 132.
Same-list dependencies alone appear in features; cross-phase prerequisites and
shared-file serialization are separate metadata. Existing completed phases 015/014 are
inputs, not new-list dependencies. Local adoption asserts no external ecosystem.

## Acceptance position and independent ownership

Feature119’s six selectors and default26 have captured QA/hosted evidence; 120–123 commands remain future acceptance obligations.
The runner retains captured foundation118 proof at its immutable revision; current119 correctly rejects stale118 receipts. Later control selectors remain obligations of later contracts.
Its --case NAME tests exactly the named invariant; --check foundation-ready,
controls-ready or profiles-ready verifies that stage's candidate-bound receipts.
Unknown cases/checks, setup failures and missing proof exit nonzero. Existing
validate.sh calls are reused checks, not evidence that future controls exist.
Evaluator test author, Generator developer and independent acceptance
reviewer have distinct recorded session/agent identities. Freeze source obligations
and test bytes before implementation; require actual intended red-before-repair,
not transport/setup failure. Bundle changes require renewed independent review.
Mode A plus independent contract review precedes implementation; Mode B precedes
fresh independent QA and actual command/exit/revision evidence capture. Only the
Orchestrator owns run position, counters and history; all others preserve them.

## Full counted proposed budget

| ID | Product | Independent tests | Process | Total |
| --- | --- | --- | --- | --- |
| 119 | 200 | 300 | 500 | 1,000 |
| 120 | 800 | 700 | 1,250 | 2,750 |
| 121 | 300 | 450 | 550 | 1,300 |
| 122 | 200 | 250 | 500 | 950 |
| 123 | 300 | 350 | 550 | 1,200 |
| Total | 1,800 | 2,050 | 3,350 | 7,200 |

The unchanged 130% ceiling is 9,360 under Root’s authority receipt; phase018 is active, with no budget rebaseline. Process
includes registrations, contracts, independent verdicts and planning/close-out, including all incoming reconciliation/preparation once from PR 99 merge `fcd0584`. Phase 016’s archived 5,179 and prior rows remain unchanged.
Bucket sum already includes overhead; do not multiply it again. Full WA estimate: 16,100
compares historical 4,360–13,190 weighted forecasts; distinct entry/conflict controls,
independent sealed tests and split closure were omitted there. Split phase estimates of 5,400, 7,200 and 3,500 fit the 7,200/8,600 precedents.
Use existing product + tests + contract + verdict + planning classification; raw evidence
and run_state excluded, unclassified paths fail closed. Orchestrator compares only
this phase's prior completed features before appending a measurement; first feature
has no rolling baseline. Cumulative overrun requires actual human decision.
