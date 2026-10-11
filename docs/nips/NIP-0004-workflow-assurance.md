---
id: nip-0004-workflow-assurance
title: "NIP-0004 — Workflow Assurance"
description: "Proposed staged assurance for candidate identity, evidence invalidation, gate transitions, independent test ownership and isolated coordination."
version: 1.0.0
status: active
authoritative_source: docs/nips/NIP-0004-workflow-assurance.md
change_log:
  - version: "1.0.0"
    date: "2026-10-11"
    summary: "Record accepted reviewed0.1.0 scope under H-NIP; six operator design choices remain unresolved, WA phase unallocated and enforcement/activation pending."
  - version: "0.1.0"
    date: "2026-10-11"
    summary: "Draft the authorized Workflow Assurance scope using current evidence; H-NIP acceptance and future H-PHASE activation remain pending."
---

# NIP-0004 — Workflow Assurance

## Status

**Accepted scope — H-NIP exercised on2026-10-11.** The operator accepted reviewed
0.1.0 at source `650770d9b48c31748f24b5ac6967b80a6a46c5f7` with
"Approved and accepted, please proceed." The exact decision was recorded in
`.agent/run_state.json` before edits at authorization commit
`87ba2ae9ae9b92565bf8bd6d5582dccb7622f881`. Version1.0.0/active records scope
acceptance, not implemented policy. Six unresolved design choices remain pending
operator decision; acceptance does not choose an option or reduce an active gate.
No WA phase or numeric feature IDs are allocated. Later realization requires
separate phase planning, H-PHASE activation and independent contract gates.

## Current evidence and problem

The dated Section7 outline in the backlog reconciliation identifies candidate
identity, stale evidence, verdict mapping, routing and concurrency as related
assurance concerns. Current inputs are the historical102 GA-readiness dossier,
DEBT.md (only NDEBT-040 and NDEBT-034 remain Open), commissioned local v1.5.0
identity/preflight/baseline/QA, and the verified maintenance source/CI receipts.
Feature101 was cancelled; no simplification review or101 findings are asserted.

The completed local commissioning and maintenance used a fixed assessed source
candidate, actual executing-checkout digests, independent QA, explicit evidence
gates and separate final-record stages. These are observed task practices. This
NIP proposes a reusable policy; it does not claim that the proposed schemas,
controllers or acceptance bundle already exist.

## Proposed candidate identity and invalidation

A candidate record would bind repository identity, full source commit and tree,
assessed path set and byte digests, contract/spec revision and test-bundle identity.
An actual CI checkout may be a synthetic merge commit: record its full SHA and
executed-source digests, and prove assessed bytes match the source candidate.
An ambient later HEAD is never substituted for the captured assessed candidate.

Changing assessed source, contract/spec obligations, acceptance tests, tool inputs
or required environment invalidates the affected verdict/evidence. A later record
edit may preserve the candidate only when the explicit assessed path set and all
relevant inputs are unchanged. The invalidation dependency policy is unresolved;
a proposed implementation must prove both stale rejection and legitimate record
continuity, rather than trusting a successful historical command.

## Proposed gates and verdict transitions

Operator acceptance and activation are distinct from automated document/contract
review. A proposed design check may allow design-review only. It cannot satisfy
H-NIP or H-PHASE; the scope H-NIP decision is now recorded separately. A recorded
operator decision is necessary for either gate, with
its scope, target revision and exceptions bound explicitly.

A proposed transition record would identify the stage, candidate, accountable
owner, prerequisite gate decisions, exact commands, actual exits and immutable
artifact references. Pending, running, passed, failed and invalidated are distinct
states. A command that did not run, an unsupported environment or a setup failure
cannot be promoted to passed. A machine verdict advances a stage only when its
approval is true and every blocking array is empty. Missing evidence blocks
completion even after QA passes; a new candidate requires fresh affected proof.

## Proposed test ownership

The Evaluator authors independent acceptance regressions and adversarial controls;
the Generator implements against reviewed obligations. Actual failing baseline
proof precedes repair. Tests distinguish the intended invariant from setup,
timeout and transport errors. A04b owns this behavior proposal; completed A04a repaired the existing role text
and does not deliver a frozen acceptance bundle. The independent Validator reviews scope/source and
an independent acceptance reviewer verifies actual execution. A test-authoring
session cannot approve its own acceptance bundle or source implementation.

The sealing mechanism and handoff between test author and acceptance reviewer
remain an explicit operator choice. Scope acceptance installs no enforcement by this
text; later planning must allocate independent sessions and immutable identities.

## Proposed routing, profiles and coordination

Entry routing and A14 failure routing are separate proposed controls. Entry
routing would bind the installed index/skill, active approved contract and
selected role/profile. A role's capability is limited to its declared permissions
and owned fields; documentation labels cannot grant extra write authority.
The Orchestrator alone owns run position, counters, gate recording and coordination
history. Implementers preserve those fields and report evidence by path. A09 would
compare parsed JSON values for every unowned field, require the original history
as an exact prefix, and admit changes only to contract-declared owned fields. A
schema-valid record with an altered phase, budget or operator decision must fail
this semantic comparison; a permitted coordination append must pass.

Cross-repository scope requires actual authorized membership and inputs. This
repository's self-adoption is local; no external ecosystem is invented. Proposed
routing/profile checks would reject an unauthorized role, stale installed pin or
undeclared target. Exact routing/profile identifiers remain a design decision.

## Proposed dependencies, concurrency and retry

Parallel work would require a dependency-eligible packet and nonconflicting owned
paths/state. Shared files or dependent contracts serialize. Each retry uses an
isolated attempt root, immutable approved inputs and a bounded counter; it retains
failed evidence and cannot silently become a fourth attempt. Rollback restores
owned changes without deleting another task's files, parent state or prior proof.

The conflict representation and retry-to-invalidation mapping require separate
acceptance. This NIP neither starts concurrent runtime work nor alters the current
execution protocol. Proposed acceptance must test both allowed independent work
and forbidden shared-state races, including terminal-status/authority spoofing.

## Core first; proposed policy profiles later

A10/A11 establish trusted candidate/evidence identity and convergent-finding to
AGF verdict mapping before policy shortcuts. Blocking convergent findings populate
AGF blocking issues/required fixes; advisory findings remain explicitly advisory and
cannot clear blockers. Approval requires true approval plus empty issues,
missing_acceptance_coverage and unsupported_claims arrays. The empty-array rule is a
mechanical gate, not an inference from favorable prose.

NDEBT-040 proposes parsed owned-field comparisons instead of brittle SHA-anchored
run_state byte guards: compare frozen field values and append-only prior history,
allow only declared Orchestrator-owned coordination fields. Schema validation and
actual before/after fixtures remain necessary; a semantic guard is not blanket
permission to edit phase position, budgets or operator decisions.

A14 cause-based failure routing proposes replacing the forced strategy ladder in
methodology03 Section2 only after acceptance and activation. It depends on
NIP3-110 defining attempts, declared-negative probes and cross-stage continuity;
this NIP must not assume that dependency allocates a new cause budget. Failed CI infrastructure (for example runner provisioning) is distinct
from a semantic defect in the candidate; both are failures with evidence, never
success. Any routing rule must identify its cause, affected stage and actual
counter/identity continuity. Existing three-attempt behavior remains unchanged
until an accepted policy is activated; a process reset or new agent cannot erase
attempts. No cause budget or exception is silently adopted by this draft.

A15 Routine, Standard and High-assurance profiles are deferred until A10/A11 are
trusted. Preregistered shadow comparison must compare the proposed profile against
full baseline gates on the same candidate before any reduction is proposed. Define
comparison inputs, candidate/test identities, applicability criteria, cost and
latency budgets, mismatch/blocker thresholds and accountable operator decision
before a shadow run. Capture every comparison, including failures. A profile
that misses a baseline blocker must fail its promotion recommendation; shadow
outcomes alone cannot accept a profile or remove an active gate.

A10 would reuse existing validate.sh, verify_lib.sh and schema validation: define
stage prerequisites and idempotent recovery against existing state, then reject
double advancement, missing receipts and replay against a different candidate.
Replaying the same complete receipt must leave lifecycle state unchanged. No
second scheduler or parallel authority/state store is proposed. Dependency and
conflict semantics extend the single accountable coordination model. This NIP's
prospective version-impact assessment is MINOR for additive optional records and
checks, but MAJOR if acceptance later requires new mandatory fields or changes a
consumer contract. That assessment is a proposed release decision, not a new release.

## Acceptance matrix

Every row describes a future obligation and a reviewed-design assertion. A design
assertion passing permits design-review only after scope acceptance; executable
policy checks and their artifacts remain future deliverables until unresolved
operator decisions, phase activation and gated implementation. Existing inputs are evidence of the problem/practice, not proof
that a future controller is implemented.

| topic | obligation | accountable-owner | actual-input-or-proposed-precondition | executable-check-or-reviewed-design-assertion | evidence-artifact | blocking-outcome | allowed-transition | required-gate-dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| identity | Bind repository, source commit/tree, assessed paths and executed checkout identity | Orchestrator | Existing commissioning/maintenance candidate and checkout receipts; proposed candidate schema | Review candidate/contract/test/policy/environment identity and trusted-runner assumptions; later compare executed source hashes to captured commit/tree and reject ambient HEAD substitution | Existing maintenance source-candidate/CI receipts; proposed identity-positive and wrong-source captures | Missing identity or differing assessed bytes blocks verification | design-review only; later verification requires accepted policy | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| invalidation | Reject evidence after relevant source, contract, test or environment changes | Validator | Proposed dependency/invalidation rule and immutable original captures | Review A09/NDEBT-040 dependency triggers and parsed owned-field comparison; later mutate source/contract/tests/environment or an unowned JSON field, reject stale proof, and accept an allowed append with frozen history prefix | Proposed stale-input negatives, changed-phase/budget/decision rejects, allowed-owned-field append and unchanged-record continuity positives | Stale or unbound proof blocks advancement | design-review only; no old QA promotion across changed inputs | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| gates | Separate human acceptance/activation from automated design and implementation gates | Orchestrator | Existing gate registry and actual decisions; proposed stage map | Review A10 stage actor/target/prerequisites using validate.sh/verify_lib.sh/schemas; later reject missing or wrong-revision decisions, double advancement and recovery with missing receipts | Existing operator-gate records; proposed missing-gate/double-advance negatives and same-receipt idempotent replay positive | Missing operator decision or prerequisite blocks its dependent stage | design-review only; no automatic H-NIP/H-PHASE satisfaction | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| verdict | Map approval plus empty blockers and genuine command exits to stage transitions | Evaluator | Existing QA/verdict shapes; proposed transition record | Review A11 convergent-to-AGF mapping: blocking findings to issues/required fixes and advisory minor to advisory only; later reject each nonempty verdict array and absent execution while advisory-only proof cannot clear carried blockers | Proposed verdict-state positives and blocker/setup-error negatives | Nonempty blockers, unsupported/setup or absent evidence blocks completion | design-review only; future QA pass still requires evidence gate | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| test-ownership | Separate developer, regression author and acceptance reviewer with red-before-repair | Evaluator | Actual maintenance red/green practice; proposed sealed independent bundle | Review A04b sealed bundle and distinct developer/regression-author/acceptance-reviewer identities; later reject self-approved, changed-seal or post-repair-only red and prove legitimate independent handoff | Existing maintenance red receipt; proposed owner/seal and ordering captures | Shared approving author or missing actual baseline failure blocks acceptance | design-review only; test ownership policy awaits decision | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| routing | Bind entry routing to authorized repository, installed pin, index and active contract | Planner | Current local AGENTS and commissioning record; proposed routing contract | Review entry authorization separately from A14 proposed strategy-ladder replacement dependent on NIP3-110; later route infrastructure versus semantic failure by recorded cause and reject stale pin, cause relabeling or counter reset | Existing local adoption record; proposed entry negatives, infrastructure/semantic routing captures and counter-continuity/relabeling rejects | Unauthorized target, stale routing input, missing cause or reset attempt identity blocks execution | design-review only; no expanded ecosystem scope | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |
| profiles | Match selected role/profile permissions and field ownership to proposed operation | Validator | Current role/capability profiles; proposed operation-to-profile mapping | Review role permissions and deferred A15 Routine/Standard/High-assurance applicability and preregistered shadow comparison after A10/A11; later attempt forbidden writes and prove a missed baseline blocker prevents recommendation | Proposed profile coverage positive, permission/state-owner negatives and preregistered same-candidate baseline/shadow mismatch/cost/latency captures | Mismatched profile, nonowner write, untrusted A10/A11 or missed baseline blocker blocks operation/promotion recommendation | design-review only; no permission change installed | H-NIP scope accepted; unresolved design decisions, trusted A10/A11 before A15, future H-PHASE activation, independent contract gates |
| concurrency | Bind dependency/conflict lanes, isolated retries and owned rollback | Generator | Existing dependency DAG/retry protocol; proposed conflict/invalidation map | Review eligible and serialized paths; later test independent positive, shared-state race and fourth-attempt rejection | Proposed conflict/race/retry/rollback captures preserving unrelated sentinel | Unsatisfied dependency, shared ownership or exceeded retry limit blocks work | design-review only; runtime scheduling remains future implementation | H-NIP scope accepted; unresolved design decisions, future H-PHASE activation, independent contract gates |

## Unresolved choices

| choice-id | proposed-options | accountable-decision-owner | required-gate-dependencies | blocked-transition | decision-status |
| --- | --- | --- | --- | --- | --- |
| candidate-invalidation | Complete dependency closure versus explicit assessed-input graph; define record-only continuity exceptions | Operator | H-NIP scope accepted; explicit operator design decision, future H-PHASE planning/activation | Accepted scope to adopted invalidation policy and executable enforcement | pending operator decision |
| acceptance-ownership | Sealed test bundle with separate author/reviewer sessions versus equivalent independently audited handoff | Operator | H-NIP scope accepted; explicit operator design decision, future H-PHASE planning/activation | Accepted scope to adopted acceptance ownership/sealing | pending operator decision |
| routing-profiles | Reuse existing role/profile identifiers versus versioned extensions with explicit scope migration | Operator | H-NIP scope accepted; explicit operator design decision, future H-PHASE planning/activation | Accepted scope to changed routing or permission policy | pending operator decision |
| shadow-profiles | Preregister Routine/Standard/High-assurance comparison after trusted A10/A11; decide any gate reduction separately | Operator | H-NIP scope accepted; explicit operator design decision, A10/A11 trusted, future H-PHASE planning/activation | Accepted scope to adopted assurance profiles or reduced gates | pending operator decision |
| cause-routing | Define cause budgets from NIP3-110 and infrastructure-versus-semantic routing without resetting counters | Operator | H-NIP scope accepted; explicit operator design decision, NIP3-110, future H-PHASE planning/activation | Accepted scope to cause-based retry/routing policy | pending operator decision |
| conflict-retry | Explicit file/state conflict lanes and retry invalidation graph versus an equivalent reviewed conflict representation within existing coordination | Operator | H-NIP scope accepted; explicit operator design decision, future H-PHASE planning/activation | Accepted scope to runtime concurrency/retry/rollback enforcement | pending operator decision |

## Staged adoption and non-goals

Current ordering serializes PLAN-WA planning after canonical NIP3-114
(normative-stage/phase015 close), which remains pending. Relative WA implementation
versus controller stage/phase016 stays open; no WA phase is allocated.
H-NIP scope acceptance is recorded. The six design choices still require explicit
operator decisions; no option is selected by scope acceptance. A later concrete
phase plan must pass H-PHASE activation and independent contracts before any
schemas/checkers/controllers or policy are implemented. Design review alone cannot
execute policy, close an unresolved choice or reduce an active gate. Release and
consumer upgrade remain distinct decisions. No runtime implementation, new release
or installed v1.5.0 change occurs in this planning task.

## References

- docs/planning/backlog_reconciliation.md (dated Section7 outline and current overlay).
- docs/planning/operator_gates.md and docs/planning/DEBT.md.
- docs/planning/SELF_GOVERNANCE.md and .agent/qa/self-commission-v1.5.0.json.
- .agent/evidence/102/ga-readiness.json and .agent/qa/post-ga-maintenance.json.
- .agent/evidence/post-ga-maintenance/source-candidate.json and capable-ci-receipt.json.
