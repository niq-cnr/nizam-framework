---
id: nizam-workflow-016-planning-spec
title: "Workflow Assurance and controller planning delivery"
description: "Deliver bounded, unactivated WA plans before controller016 planning, with explicit allocation, split budgets and independent verification."
version: 0.1.0
status: draft
authoritative_source: .agent/product_spec_workflow_016_planning.md
change_log:
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Specify authorized planning delivery only; future implementation and activation remain separately gated."
---

# Planning delivery

## Authority, baseline and gates

The operator authorized "Workflow Assurance planning, followed by phase 016
planning" and management/triage/merge of clean task PRs. The exact authorization,
scope and isolated attempt root are recorded in
`.agent/evidence/workflow-016-planning/authorization-isolation.json`.
Approved base is `3d9b24931ecad49221b8e8faffc12a7fc0fc1bf0`.
Installed `.nizam/` governance governs this delivery. NIP3/NIP4 accepted scopes
and NIP4's six selected choices are inputs, not implemented enforcement.

This spec precedes a new planning-delivery contract. Both independent pre-code
gates must approve that contract before phase plans or public overlays are
written. Delivery then requires independent ModeB, fixed-candidate QA and the
evidence-capture gate before planning packets can be marked delivered. Each
verdict must satisfy approval plus all three empty blocking arrays. The
Orchestrator alone owns lifecycle, counters and append-only coordination history.

## Deliverables and boundaries

First deliver PLAN-WA, then PLAN-016. Each proposed implementation phase receives
one draft `.agent/product_spec_NNN.md`, one `.agent/feature_list_NNN.json` and one
pending `docs/planning/phase_NNN.yaml`; every feature/step remains pending.
Append proposed entries to `docs/planning/manifest.json`, preserving existing
entries and current_phase `015-live-runtime-normative` exactly. Synchronize only
current allocation, ordering and planning-delivery overlays in ROADMAP, HANDOVER,
backlog_reconciliation, backlog_dag and NIP3/NIP4; any CHANGELOG edit is a bounded
Unreleased planning note. Preserve dated history and accepted case/choice text.
The Generator contract must enumerate the concrete file set before writing it.

Create one task validation JSON at
`.agent/evidence/workflow-016-planning/plan-validation.json`: the authoritative
planning verification result, identifying exercised revision/digests, allocation,
phase budgets, schema/DAG outcomes, projections and negative-control receipts.
Public summaries reference it rather than introducing duplicate proof records.
An independent Evaluator owns the small task checker and its controls; target
at most about 200 lines if feasible, reusing installed schemas and existing tools.
This is planning verification, not a reusable validation framework or future
runtime acceptance implementation.

Protect all phase014/015 spec/list/YAML records, statuses, budgets and historical
proofs. Phase015 remains complete at 7319 counted lines against 7200/9360.
Do not change authored runtime/modules, root NIZAM/index, schemas, installed
payload, tool implementations, workflows, release/version anchors or DEBT.
Current Open debt040/034 remains an existing input; neither is silently resolved.
No future phase activation, runtime execution, release/tag, gate reduction or
installed upgrade is authorized by this delivery. Prior114 helpers and proofs
are frozen; capture new task evidence only. Do not commit until instructed.

## Allocation, proposed execution DAG and splits

Determine the canonical maximum from actual feature lists; baseline maximum 114.
Allocate globally unique IDs above it, WA first. Retain phase016 as the accepted
controller stage label. Keep stable conceptual backlog packet aliases
NIP3-115 through NIP3-120, explicitly mapping each to allocated IDs/phases using
an actual_assigned field and collision-free future numeric evidence paths;
provisional aliases are not reserved numeric IDs. Every feature dependency names
only a feature in its own list. Cross-phase evidence/authority prerequisites and
shared-file serialization are separate metadata, not dangling dependencies.

Proposed decomposition: phase017 WA foundation; phase018 WA controls;
phase019 deferred profiles; phase016 controller core; phase020 SBCL/fresh
acceptance. Final plans determine the necessary phase count from coherent
boundaries and full estimates. The WA foundation establishes assessed candidate,
contract/test/tool/environment identity, conservative invalidation, parsed owned
fields/frozen history and sealed independent acceptance ownership. Controls cover
A10 recovery/receipt gates, A11 blocking/advisory mapping and capable CI,
authorized entry routing, conflict lanes/owned rollback and A14 cause routing.
Reuse existing role/profile identifiers and the single coordination model.
Infrastructure failures remain failures; attempt identity and the existing
three-attempt limit survive process, agent, generation and stage changes.

Recommend implementing the critical minimum foundation before controller work,
then additional controls; A15 profile shadow comparison requires trusted A10/A11,
same-candidate full baseline gates and preregistered mismatch/cost/latency bounds.
A missed baseline blocker prevents promotion recommendation. This execution order
is a Planner recommendation, not a recorded operator phase selection/activation.
Existing candidate A09/A15 serialize_after NIP3-120 edges remain historical inputs:
the plans must explicitly propose any superseding edge, mapped owner and rationale
for foundation-first work rather than silently dropping those edges. Preserve
dated history; adoption of the proposed order requires future activation scope.
Serialize shared product/state paths even where technical dependencies allow
independent work. Each split closes with bounded readiness/evidence obligations;
no split claims full runtime conformance prematurely.

## Future acceptance and budgets

Preserve and map all 13 NIP3 live cases. Explicitly require stub policy and capable
CI isolation-mechanism proof for case8 using the existing isolated trial adapter;
local unsupported capability is non-passing. SBCL cases require committed-source
archive, fresh process, no user/system init, private HOME/XDG, empty build cache,
private ASDF source/output configuration ignoring inherited resolution, and actual
toolchain/lock/core provenance. Observe local SBCL version only as an environment
record; it cannot prove supported execution. No workstation sysctls change.

Feature acceptance_tests must be concrete, atomic commands. Proposed runner paths
and CLI switches are explicit future implementation outputs with an assigned
owner and case/negative-control obligation. A small future WA case runner may
serve those obligations; no future tool is asserted present or run during planning.
Schema fixture success and session experiment results cannot substitute for
independent fresh acceptance or any required live/CI case.

Controller's retained 4585 naive estimate implies 10545 at 2.3 and 13251 at 2.89,
before any omitted obligations. Historical WA packet forecasts total4360–13190
weighted and do not separately price all entry/conflict controls. These are
planning inputs, not adopted budgets. Full future estimates must separately
include normative/product code, independent tests, registrations, contracts,
verdicts, planning/close-out and counted process costs. Compare each proposed
phase with concrete 7200 and 8600 predecessor estimates; split coherent deliverables
when the full weighted design exceeds precedent rather than raising a nominal
baseline to conceal scope. Publish per-feature estimates, their sum and 130% ceiling
consistently, with the existing evidence/coordination classification disclosed.
Future budgets require their own activation decision.

Propose 1200 counted lines for this planning-delivery task, covering new planning
documents and contract/verdict process only. It is outside the closed phase015
budget, not a phase rebaseline or active ceiling. Actual measurement and any
required budget decision remain Orchestrator responsibilities; preserve existing
scope_budget and count raw evidence separately under the current rules.

## Delivery verification

Validate each list/YAML and manifest against actual installed schemas; check
global uniqueness, same-list references, topological ordering, pending states,
budget sums/ceilings, alias mapping, 13-case proof ownership and public projections.
Use discriminating controls for duplicate/dangling/cyclic IDs, activation/current
phase spoofing, wrong budget sums, omitted cases and schema/live proof confusion.
Scope verification proves protected paths unchanged. Capture every executed
command, output, actual exit and exercised revision/digests by task evidence path.
Complete existing compliance/payload and immutable-install checks appropriate to
the final planning diff. Successful delivery means verified proposed plans only;
the Orchestrator advances PLAN-WA/PLAN-016 after evidence capture and retains all
future implementation/activation gates.
