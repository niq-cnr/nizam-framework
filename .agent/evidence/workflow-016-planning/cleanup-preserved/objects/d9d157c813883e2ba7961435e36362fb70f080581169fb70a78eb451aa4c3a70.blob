---
id: nizam-phase016-product-spec
title: "Phase 016 — Live Runtime Sessions — Controller Core"
description: "Proposed runtime scope, bounded full cost and independently owned future live acceptance."
version: 0.1.0
status: draft
authoritative_source: .agent/product_spec_016.md
change_log:
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Plan pending controller features after reviewed WA planning; no activation or live-pass claim."
---

# Proposed phase 016

Accepted NIP-0003 scope and completed normative phase 015 are inputs. Allocate
126–128 after actual WA maximum 125. H-PHASE-016, implementation
contracts and budget approval remain future. Preserve phases 014/015, reviewed WA
plans, installed payload, released versions and Open debts NDEBT-040/NDEBT-034.
Stable NIP3-115…120 aliases map to actual IDs 126…132; NIP3-116 spans core feature 127
and final CI feature 131. Numeric evidence paths use allocated IDs, not alias suffixes.

## Architecture, prerequisites and isolation

Feature 126 delivers one detached supervisor per session, child JSON-lines protocol,
nonce/counter generation, exclusive lock and lease epoch, atomic records and
read-only attempt guard. Coordination is not authentication. Ownership, trial
rejection and stale generation/lease checks precede execution; at most one
operation runs. Creating the nested stub fixture directory and its F105 claim
registration must be the same change. Feature 127 proves timeout/busy, reattach and source-
bound replay semantics; feature 128 closes only this partial core. Lifecycle never executes
code; fresh acceptance alone can convert reproducible setup into acceptance proof.
A failed generation/process restart cannot reset a governed attempt.

Recommended order: phase 017 foundation → phase 016 core → phase 018 controls →
phase 020 fresh acceptance → phase 019 profiles, subject to future activation.
Core requires captured phase 017 foundation; phase 020 requires core feature 128 and trusted phase 018
features 119/120/123. Phase 018 requires feature 127 only, not split alias NIP3-116's later feature 131.
Feature dependencies stay within each list; external receipts and shared-file
serialization are explicit metadata in the existing single coordination model.
Before phase 016 activation, obtain standalone capability-only receipts on the
same capable Linux acceptance/CI host using existing tools:

- `PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py`
- `sbcl --version`
- `sbcl --no-sysinit --no-userinit --non-interactive --eval '(assert (= (+ 1 1) 2))'`

Required isolation mode must exit 0; never use --allow-unsupported-isolation.
Bind actual host/revision/environment and each command/exit. This preflight
requires no new controller or future feature 131 job, avoiding an activation cycle.
Observed local SBCL 2.2.9.debian is environment input only, not host conformance;
unsupported local isolation is non-passing. No workstation sysctl changes.

## Future acceptance and independent ownership

All feature commands are future acceptance obligations, not runs performed by
planning. Feature 126 introduces the future test runner; later owners expand it under
reviewed contracts. CLI --case N --runtime stub|sbcl|ci selects one live case;
case 8 additionally requires --layer policy|mechanism. --require-sbcl and
--require-isolation fail closed. --check NAME selects the named additional
invariant; unknown switches/checks, missing cases, setup errors and absent proof
exit nonzero. Evaluator authors and seals acceptance tests; Generator implements;
an independent acceptance reviewer uses a distinct recorded session identity.
Actual intended red-before-repair and immutable bundle/source identities precede
repair; changed bundles need renewed independent review. Both pre-code gates,
Mode B, independent fresh QA and actual command/exit/revision evidence capture
remain mandatory. Orchestrator alone owns coordination/counters/history.

## Full counted proposed budget

| ID | Product | Independent tests | Process | Total |
| --- | --- | --- | --- | --- |
| 126 | 1,100 | 550 | 1,250 | 2,900 |
| 127 | 450 | 600 | 900 | 1,950 |
| 128 | 200 | 100 | 500 | 800 |
| Total | 1,750 | 1,250 | 2,650 | 5,650 |

Proposed 130% ceiling: 7,345. Product/tests/process buckets already
price registrations, contracts, independent verdicts and planning/close costs;
do not multiply overhead again. Full controller estimate: 13,000 compares retained
4,585 naive × 2.3…2.89 = 10,545…13,251 forecasts. Full-cost splits of 5,650 and 7,350
fit the 7,200/8,600 predecessors; the larger fresh stage prices actual full live CI,
hermetic controls and captured readiness, without trimming scope to match 7,200.
Future budget activation remains separate. Use existing counted classification;
raw evidence/run_state excluded; unclassified fails closed. Rolling comparison
uses only this phase's prior completed features before appending; first feature
has no prior baseline. Cumulative overrun needs actual human authorization.
