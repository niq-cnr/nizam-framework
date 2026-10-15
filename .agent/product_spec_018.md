---
id: nizam-phase018-product-spec
title: "Phase 018 — Workflow Assurance — Controls"
description: "Bounded WA control plan, recorded authorization and future independent acceptance gates."
version: 0.1.6
status: active
authoritative_source: .agent/product_spec_018.md
change_log:
  - version: "0.1.6"
    date: "2026-10-15"
    summary: "Record captured 123 and canonical 018 closure, independent actual acceptance and remaining PR 104 integration; preserve requirements and original budget."
  - version: "0.1.5"
    date: "2026-10-15"
    summary: "Record captured 122 cause routing and pending 123/PR 103 integration; preserve requirements, live-adoption boundary and original budget."
  - version: "0.1.4"
    date: "2026-10-15"
    summary: "Record captured121 and pending122–123; preserve requirements, independent gates, live-adoption boundary and original budget."
  - version: "0.1.3"
    date: "2026-10-14"
    summary: "Record captured120 aligned-record receipt APIs; preserve pending121–123 and unapplied live-binding migration, requirements and budgets."
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
[Independent activation and Root promotion](evidence/phase018-preflight/activation-result.json) made phase 018 active; [canonical phase 018](../docs/planning/phase_018.yaml) now records all 119–123 complete after independent QA and [Root capture 123](evidence/123/evidence-capture.json). [PR 103 main CI](evidence/122/pr103-main-ci.json) passed all five jobs at merge `79811ef7` before 123. PR 104 final exact-head CI, merge and main CI remain pending at this closeout snapshot.
[Foundation 118](evidence/118/evidence-capture.json) and [controller semantics 127](evidence/127/evidence-capture.json) are captured prerequisites; 128, full phase-016 closure and later 131 are not added prerequisites. [Postmerge main CI](evidence/128/pr99-main-ci.json) passed all five jobs on PR 99 merge `fcd0584`; this earlier integration proof is separate from the later 119–123 acceptance.
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

Features 119–121 retain captured acceptance. [Feature 122 QA](qa/122.json) passed four selectors/default46, immutable 118 exit 0/current stale exit 1, both compliance modes and exactly one additional duplicate-key authority check. The [independent executable seal](evidence/122/executable1-current-seal.json) records four positive/intended-negative/restored trios with exits 0/1/0; [hosted default46](evidence/122/ci2-receipt.json) is separate proof.
Feature 122’s [canonical closure](evidence/122/closure.json) follows independent pre-code, renewed bundle, Mode B, fresh QA and Root capture gates. Read-only cause routing preserves failed outcomes and the three-attempt limit; integrity/producer labels do not authenticate classification or authority.

Feature 123’s actual two-pass hosted capture/verify proof passed [independent HostedReview](evidence/123/hosted-review1.json), the [final executable seal](qa/123-final-executable-seal1.json), [Mode B](validator/123-mode-b.json) and [fresh QA](qa/123.json) before Root capture. Fresh QA verified all nine mandatory expected outcomes, exact default48 and 166/166 fixtures, plus exactly one same-instance warmed-cache hardlink rejection/restoration check. The seal retains actual positive/intended-negative/restored readiness exits 0/1/0; original operational setup/static failures remain recorded. [Root’s closure decision](evidence/123/root-closeout-contract-preservation-decision.json) preserves the approved 123 contract byte-identical as one of 537 protected candidate inputs; feature completion is recorded separately in canonical lifecycle artifacts.
Root owns final feature 123 accounting in [run_state.scope_budget](run_state.json), including this refresh once; original 7,200/9,360 and prior 119–122 total 4,303 remain unchanged. Full runtime/SBCL and final CI 131 remain later phase 020 obligations; comparative performance remains unmeasured. Aligned API fixtures do not establish live Root adoption: [repository-binding migration](evidence/120/repository-binding-decision-proposal.json) remains unapplied.
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

The unchanged 130% ceiling is 9,360 under Root’s authority receipt; phase 018 is canonically complete, with no budget rebaseline. Process
includes registrations, contracts, independent verdicts and planning/close-out, including all incoming reconciliation/preparation once from PR 99 merge `fcd0584`. Phase 016’s archived 5,179 and prior rows remain unchanged.
Bucket sum already includes overhead; do not multiply it again. Full WA estimate: 16,100
compares historical 4,360–13,190 weighted forecasts; distinct entry/conflict controls,
independent sealed tests and split closure were omitted there. Split phase estimates of 5,400, 7,200 and 3,500 fit the 7,200/8,600 precedents.
Use existing product + tests + contract + verdict + planning classification; raw evidence
and run_state excluded, unclassified paths fail closed. Orchestrator compares only
this phase's prior completed features before appending a measurement; first feature
has no rolling baseline. Cumulative overrun requires actual human decision.
