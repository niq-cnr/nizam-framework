---
id: nizam-phase015-product-spec
title: "Phase 015 — Live Runtime Sessions: Normative Surface"
description: "Authorized plan for accepted NIP3 normative scope, five allocated features and approved bounded budget."
version: 1.0.0
status: active
authoritative_source: .agent/product_spec_015.md
change_log:
  - version: "1.0.0"
    date: "2026-10-11"
    summary: "Record authorized phase015 activation, approved7200/9360 budget and six WA design selections; implementation remains independently gated."
  - version: "0.1.0"
    date: "2026-10-11"
    summary: "Allocate110-114 and propose normative-stage plan for separate activation/budget approval; all implementation pending."
---

# Phase015 — normative live-runtime sessions

## Selection and activation boundary

NIP3 revision0.2.0 and NIP4 revision0.1.0 were accepted under H-NIP on2026-10-11,
operator verbatim "Approved and accepted, please proceed.", recorded before these
writes at87ba2ae9ae9b92565bf8bd6d5582dccb7622f881. Acceptance selects NIP3 stages015
and016 and accepts WA scope. H-PHASE-015 was exercised on 2026-10-11 with operator text "approved." at
`2026-10-11T06:30:20.388684+00:00`, recorded before product edits at authorization commit
`06c0ae0a273facce80c57506260648c41f566ebb` against source `57862f69ba30a36004ea9a17a295fc9c835afc13`
and the three accepted plan hashes in `.agent/run_state.json`. The approved
counted allowance is 7200 lines with a 9360 ceiling, including phase-level costs.
Canonical lifecycle and current feature position are read from
`.agent/feature_list_015.json` and `docs/planning/phase_015.yaml`; each feature
requires its approved contract, both independent pre-code gates, Mode B, QA and
the evidence-capture gate. Features 111–114 remain pending. Historical phase014
records and budgets remain frozen. This source work does not upgrade installed v1.5.0.

Operator design decisions were recorded at `2026-10-11T06:30:20.388684+00:00` in `.agent/run_state.json`
before product writes, authorization commit `06c0ae0a273facce80c57506260648c41f566ebb`, assessed
source `57862f69ba30a36004ea9a17a295fc9c835afc13`. Exact operator text: "approved. plese proceed as reocommeded with all items."

| choice-id | selected_recommendation |
| --- | --- |
| candidate-invalidation | Explicit assessed-input graph covering source/contracts/tests/tools/environment; unknown dependencies invalidate; record-only continuity requires all assessed inputs unchanged. |
| acceptance-ownership | Sealed immutable test bundle and independent author/reviewer sessions with recorded identities; bundle changes require renewed independent review. |
| routing-profiles | Reuse existing role/profile identifiers initially; versioned extensions only for demonstrated permission/ownership gaps with explicit migration. |
| shadow-profiles | Preregister Routine/Standard/High-assurance comparisons after trusted A10/A11; same candidates/full baseline; missed baseline blocker prevents promotion; gate reduction separate operator decision. |
| cause-routing | Evidence-based cause routing within existing three-attempt limit/counter continuity; infrastructure failures remain failures; any additional cause-specific budget requires explicit approval. |
| conflict-retry | Explicit file/state conflict lanes in single existing coordination model; serialize shared ownership, isolate retries, invalidate affected evidence, rollback only owned changes. |

Actual allocator scan of .agent/feature_list*.json confirms highest109 before
this plan, including cancelled100/101. Allocate only110-114. Single chain110->111
->112->113->114; current lifecycle follows the canonical feature list. Stable backlog packet IDs NIP3-110..114
map to these canonical IDs. Phase016115-120 remain provisional. PLAN-WA follows114;
PLAN-016 also depends114 and serializes after PLAN-WA. Relative WA implementation
versus016 stays open. Source implementation is limited to approved feature
contracts; no WA policy/gate reduction or runtime controller is delivered here.

## Architecture and feature boundaries

110: neutral document10 plus generic02/03/permissions/review/DoD definitions and
same-feature source-module registrations. Distinguish source/image/durable
records; exactly one owner and generation; serialized operations; condition
capture before unwind; failed load honesty; timeout stops waiting only. Handoff
binds committed source and replayable commands. Fresh process/build/hermetic
resolution is Evaluator acceptance; session provenance cannot prove source/heap
identity or become acceptance evidence. Orchestrator alone owns coordination
fields/counters. Lifecycle permission cannot evaluate; trial roles get no session
endpoint. DoD current0.2.0 ->planned0.3.0.

Attempt definition binds contract_id, step_key and attempt across process,
subagent, worktree, context, generation and stage changes. An explicitly declared
negative probe is distinct from a governed attempt; declare expected negative
outcome and budget classification before execution. Never relabel after outcome,
reset counters at handoff or turn infrastructure failure into success. Cross-stage
continuity is defined here; WA cause-based diagnostic routing remains separate
unimplemented scope. Guard reads parent-owned counters; implementation agents
cannot write coordination state.

111: two closed Draft2020-12 schemas, with minimal required fields and all016
fields present from outset (isolation, toolchain_identity, lock_ref,
core_provenance, wait_outcome, lease_epoch, lane_authorization_ref). Eighteen
explicit _valid_/_neg_ fixtures extend C12 families, router before contract_id,
and relational generation validation. Source schema/README/index/validator and
top-level fixture-completeness rows land in the same feature. Actual F105's nested
claim map is reused later by116 for the runtime-suite subdirectory;111 creates no
nested claim-map entry. C17 stays
free; consumer .agent/sessions is not silently swept by payload validation.

112: SBCL binding/profile covers toolchain/lock/core provenance, project-code
execution by observation, non-atomic load/compile, deleted definitions, defvar,
defstruct/defconstant, CLOS/thread/special-variable hazards, condition capture,
bounded printing and cancellation confirmation. Acceptance ignores user/sys init,
uses private empty ASDF output translations and source registries with ignored
inherited configuration and private HOME/XDG. ASDF examples illustrative until
phase016 live proof. Local SBCL2.2.9.debian availability is not conformance;
required capable isolated CI remains mandatory and workstation sysctls never change.

113: optional adapter live_runtime_session required:false, interface Section5
exactly10 existing items. Seven operations and conditional S1-S9 remain optional
for nonclaiming adapters. Source index/skill/router/crosslinks registered in same
feature. Existing consumers without sessions remain conformant. Installed v1.5.0
is frozen; authored source changes never upgrade it implicitly.

114: candidate-bound next MINOR readiness and normative-stage close. Human
H-FRAMEWORK-RELEASE sign-off/tag and consumer H-CONSUMER-UPGRADE are distinct later
acts. There is no fixed release version forecast or self-tag. Existing validators/payload/fixture/
e2e checks required. Controller/stub/SBCL/live-session CI remain016 scope and
cannot be claimed delivered by015 fixtures.

## Atomic future acceptance and evidence

Normative110/112 document checks use existing section-scoped verify_lib primitives
and whole-word patterns at explicit proposed section anchors; source comments or
markers outside those sections cannot pass. Parsed JSON/AST checks bind capability,
schema and route structure. Future independent semantic review plus misplaced-
marker negative controls is required; textual markers never prove semantics alone.
Future document headings are declared by the feature acceptance anchors and can
be revised only through its reviewed contract, not silently guessed at execution.

feature_list_015.json contains runnable atomic acceptance_tests using existing
validate.sh, fixture self-test, e2e, release closeout, jsonschema or self-contained
Python structural checks. availability and future_output_targets explicitly distinguish
new absent files from future amendments to existing files. The planning check validates these
obligations; it does not execute them against absent files or claim implementation
PASS. Future contracts refine discriminatory checks/red controls independently;
no nonexistent verifier is assumed installed. Evaluator authors independent
acceptance controls; Validator ModeB precedes independent fixed-candidate QA and
externalized command/output/actual EXIT/revision receipts plus evidence gate.
Feature completion waits for all gates, and phase close never authorizes a tag.

## Approved scope budget and measurement

| Feature | NIP naive product lines | Approved counted allowance |
| --- | --- | --- |
| 110 | 600 | 1600 |
| 111 | 850 | 2200 |
| 112 | 420 | 1200 |
| 113 | 220 | 1050 |
| 114 | 240 | 1150 |
| Total | 2330 | 7200 |

Approved 130% ceiling9360. This includes counted phase-level planning/close costs
inside the per-feature allowances; no additional uncapped budget. The allowance
beyond2330 covers contracts, independent verdicts, audit/planning/registrations,
with111 largest for18 fixtures and relational controls. It is an operator-approved bounded estimate, not an empirical universal multiplier.

Actual comparable014 features104/105/106/107/109/108/102 total5933 counted versus
5110 estimates (range686-991, mean847.6). Exclude mixed-basis099/103 for calibration.
Prior-three completed actuals109836/108851/102906 average864.3. Historical aggregate
8705 equals7414 per-feature plus1291 phase-level items (292+822+177); all are frozen.
Use the disclosed same counting basis: product+contract+verdict+audit+planning;
raw evidence and run_state excluded; unclassified fails closed. Raw proof is
captured separately by path. The planning-task changes are outside015 implementation
measurement. After each future feature, Orchestrator compares only preceding up-to
three completed actuals to the3x threshold before appending current count; first
feature has no rolling baseline. Cumulative>9360 halts pending explicit human
re-baseline; the Orchestrator derives the active budget from the approved canonical plan.

## Current inputs and unchanged boundaries

Historical102 retains pilot not_met and adoption insufficient_evidence despite
operator GA declaration; cancelled100/101 generated no F101 findings. Only Open
NDEBT040/034. Actual commissioning identity/baseline/QA and maintenance QA/CI are
available. Public/installed v1.5.0 remains pinned
f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852. Protect014 spec/features/YAML/manifest
entries/budgets, DEBT, installed payload and all old evidence/checkers/QA.
Activated-phase source edits are limited to each approved feature contract;
source work never changes installed governance automatically. Any later consolidation is separately
H-CONSOLIDATION-gated.

## Fixture inventory and proof-stage ownership

Each fixture below is a future111 output directly under tools/fixtures/.
Expected diagnostics refer to proposed C12 routing; negative runs must exit1 with
[C12] FAIL, never count setup failures. The shared positive for1/3 deliberately
checks only a permissible rejection record, not independent runtime enforcement.
Every negative invariant has its own discriminating record; validators must ensure
only its target condition causes failure. Full live proof belongs to016 on capable
required CI; phase015 never claims a case working.

| Fixture | Cases | Family | Kind | Expected exit/diagnostic | Purpose |
| --- | --- | --- | --- | --- | --- |
| runtime_operation_valid_rejected_foreign_stale.json | 1,3 | operation | positive | 0 / [C12] PASS | Rejected foreign requester with stale expected generation; record-shape coverage shared explicitly, neither proves live rejection |
| runtime_operation_neg_foreign_executed.json | 1 | operation | negative | 1 / [C12] FAIL | Foreign requester recorded as executed |
| runtime_operation_neg_stale_generation_executed.json | 3 | operation | negative | 1 / [C12] FAIL | Executed generation differs from expected_generation; relational check |
| runtime_operation_valid_partial_load_condition.json | 4 | operation | positive | 0 / [C12] PASS | load_source condition_signalled with image consistency false |
| runtime_operation_neg_failed_load_consistent.json | 4 | operation | negative | 1 / [C12] FAIL | Failed load claims image consistency |
| runtime_operation_valid_running_stopped_waiting.json | 5 | operation | positive | 0 / [C12] PASS | running with stopped_waiting preserves nonterminal operation |
| runtime_operation_valid_rejected_busy.json | 5 | operation | positive | 0 / [C12] PASS | Concurrent submit rejected session_busy |
| runtime_operation_neg_timeout_cancelled.json | 5 | operation | negative | 1 / [C12] FAIL | Stopped waiting falsely recorded as confirmed cancellation |
| runtime_session_valid_reattach_pending.json | 6 | session | positive | 0 / [C12] PASS | Reattach preserves generation, owner and outstanding operation reference |
| runtime_operation_neg_session_result_acceptance.json | 7,12 | operation | negative | 1 / [C12] FAIL | Session result offered as acceptance evidence; case12 has no extra schema proof |
| runtime_operation_valid_trial_rejected.json | 8 | operation | positive | 0 / [C12] PASS | Review-trial requester recorded rejected |
| runtime_operation_neg_trial_executed.json | 8 | operation | negative | 1 / [C12] FAIL | Review-trial requester recorded executed |
| runtime_operation_valid_new_generation_same_attempt.json | 9 | operation | positive | 0 / [C12] PASS | Same contract_id/step_key/attempt across generation; live counter guard deferred |
| runtime_session_valid_replayable_handoff.json | 10 | session | positive | 0 / [C12] PASS | Committed source manifest and replayable command references in handoff |
| runtime_session_valid_accept_hermetic.json | 11 | session | positive | 0 / [C12] PASS | Accept isolation declares empty private cache and ignored inherited config |
| runtime_session_neg_accept_inherited_cache.json | 11 | session | negative | 1 / [C12] FAIL | Accept record selects inherited cache |
| runtime_session_valid_transfer_lease.json | 13 | session | positive | 0 / [C12] PASS | Transfer changes principal_kind and increments lease_epoch |
| runtime_operation_neg_stale_lease_executed.json | 13 | operation | negative | 1 / [C12] FAIL | Old lease holder recorded executed after transfer |

## Thirteen-case staged evidence matrix

All case definitions/outcomes are the immutable NIP3 table. This matrix maps proof
ownership and does not modify those definitions.111 owns schema-level artifacts;
016 proposed116-118 owns live execution, with8 mechanism also CI isolation.

| Case | 015 schema artifacts | Schema limit | 016 mandatory live runtime | Working claim |
| --- | --- | --- | --- | --- |
| 1 | runtime_operation_valid_rejected_foreign_stale.json, runtime_operation_neg_foreign_executed.json | Record shape/invariant only; never proves live behavior | Stub | pending; never claimed by015 |
| 2 | None | No schema isolation proof; runtime-only | Stub | pending; never claimed by015 |
| 3 | runtime_operation_valid_rejected_foreign_stale.json, runtime_operation_neg_stale_generation_executed.json | Record shape/invariant only; never proves live behavior | Stub | pending; never claimed by015 |
| 4 | runtime_operation_valid_partial_load_condition.json, runtime_operation_neg_failed_load_consistent.json | Record shape/invariant only; never proves live behavior | SBCL | pending; never claimed by015 |
| 5 | runtime_operation_valid_running_stopped_waiting.json, runtime_operation_valid_rejected_busy.json, runtime_operation_neg_timeout_cancelled.json | Record shape/invariant only; never proves live behavior | Stub and SBCL | pending; never claimed by015 |
| 6 | runtime_session_valid_reattach_pending.json | Record shape/invariant only; never proves live behavior | Stub and SBCL | pending; never claimed by015 |
| 7 | runtime_operation_neg_session_result_acceptance.json | Record shape/invariant only; never proves live behavior | SBCL | pending; never claimed by015 |
| 8 | runtime_operation_valid_trial_rejected.json, runtime_operation_neg_trial_executed.json | Record shape/invariant only; never proves live behavior | Stub policy and CI isolation mechanism | pending; never claimed by015 |
| 9 | runtime_operation_valid_new_generation_same_attempt.json | Record shape/invariant only; never proves live behavior | Stub | pending; never claimed by015 |
| 10 | runtime_session_valid_replayable_handoff.json | Record shape/invariant only; never proves live behavior | Stub and SBCL | pending; never claimed by015 |
| 11 | runtime_session_valid_accept_hermetic.json, runtime_session_neg_accept_inherited_cache.json | Record shape/invariant only; never proves live behavior | SBCL | pending; never claimed by015 |
| 12 | runtime_operation_neg_session_result_acceptance.json | No additional schema proof beyond case7; deleted-definition drift is runtime-only | SBCL | pending; never claimed by015 |
| 13 | runtime_session_valid_transfer_lease.json, runtime_operation_neg_stale_lease_executed.json | Record shape/invariant only; never proves live behavior | Stub | pending; never claimed by015 |

## Human gates

H-NIP: satisfied for accepted NIP3/NIP4 scopes only, recorded exact operator text.
H-PHASE-015: EXERCISED; concrete plan and7200/9360 budget approved at the recorded authorization.
H-PHASE-016: OUTSTANDING after separately scoped/allocated controller plan.
WA six selected design choices: recorded above; WAphase remains unallocated after114.
H-FRAMEWORK-RELEASE/H-CONSUMER-UPGRADE: recurring future decisions, never self-execute.

## References

- docs/nips/NIP-0003-live-runtime-sessions.md and NIP-0004-workflow-assurance.md.
- .agent/feature_list_015.json and docs/planning/phase_015.yaml.
- .agent/evidence/102/ga-readiness.json and docs/planning/DEBT.md.
- .agent/qa/self-commission-v1.5.0.json and .agent/reconciliation/self-commission-v1.5.0/baseline.json.
- .agent/qa/post-ga-maintenance.json and .agent/evidence/post-ga-maintenance/capable-ci-receipt.json.
- .nizam/methodology/00_planning.md and .nizam/methodology/01_execution.md.
