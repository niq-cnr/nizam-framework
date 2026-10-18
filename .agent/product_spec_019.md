---
id: nizam-phase019-product-spec
title: "Phase 019 — Workflow Assurance — Deferred Profiles"
description: "Proposed bounded WA scope, future atomic acceptance and independent evidence gates."
version: 0.2.0
status: active
authoritative_source: .agent/product_spec_019.md
change_log:
  - version: "0.2.0"
    date: "2026-10-18"
    summary: "Reconcile 124/125 under the 2026-10-18 operator quality and velocity remediation mandate: generic repository/worktree profile comparison and shadow recommendation proceed after completed 018/123, while persistent-runtime SBCL profile claims remain gated on 020/130-132."
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Plan pending features only; activation, implementation and budget approval remain future."
---

# Phase 019 — Workflow Assurance Profiles

NIP-0004 accepted scope, six operator selections, and the 2026-10-18 operator
quality and velocity remediation mandate (`docs/planning/REMEDIATION_2026_10_18.md`)
are inputs. This phase allocates 124–125. Generic repository and worktree assurance
profiles proceed directly after completed Phase 018 (`123`); persistent-runtime /
SBCL profile qualification remains gated on Phase 020 features `130–132`.

## Architecture and external prerequisites

Feature 124 preregisters proposed Routine/Standard/High-assurance applicability and
same-candidate full-baseline comparison, immutable candidate/test identities,
mismatch/blocker thresholds, cost/latency bounds and accountable operator decision
before any shadow run. Feature 125 records every comparison including failed outcomes;
a missed baseline blocker rejects promotion recommendation. No recommendation or
shadow result activates a profile, reduces a gate or grants additional permission.
Existing role/profile identifiers remain unchanged. Under the 2026-10-18 remediation
mandate, generic repository/worktree profile comparison and recommendation depend on
completed Phase 018 (`119`, `120`, `123`) and remediated CI/fixture baselines (`R1–R8`),
whereas persistent-runtime / SBCL profile claims continue to require Phase 020 (`130–132`).

## Future acceptance and independent ownership

All commands in the list are future acceptance obligations; none is run here.
The future runner is introduced by feature 115 and expanded under later feature contracts.
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
| 124 | 400 | 400 | 800 | 1,600 |
| 125 | 400 | 550 | 950 | 1,900 |
| Total | 800 | 950 | 1,750 | 3,500 |

Proposed 130% ceiling: 4,550; no active ceiling or budget rebaseline. Process
includes registrations, contracts, independent verdicts and planning/close-out.
Bucket sum already includes overhead; do not multiply it again. Full WA estimate: 16,100
compares historical 4,360–13,190 weighted forecasts; distinct entry/conflict controls,
independent sealed tests and split closure were omitted there. Split phase estimates of 5,400, 7,200 and 3,500 fit the 7,200/8,600 precedents.
Use existing product + tests + contract + verdict + planning classification; raw evidence
and run_state excluded, unclassified paths fail closed. Orchestrator compares only
this phase's prior completed features before appending a measurement; first feature
has no rolling baseline. Cumulative overrun requires actual human decision.
