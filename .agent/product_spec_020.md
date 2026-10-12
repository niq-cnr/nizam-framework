---
id: nizam-phase020-product-spec
title: "Phase 020 — Live Runtime Sessions — SBCL and Fresh Acceptance"
description: "Proposed runtime scope, bounded full cost and independently owned future live acceptance."
version: 0.1.0
status: draft
authoritative_source: .agent/product_spec_020.md
change_log:
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Plan pending controller features after reviewed WA planning; no activation or live-pass claim."
---

# Proposed phase 020

Accepted NIP-0003 scope and completed normative phase 015 are inputs. Allocate
129–132 after actual WA maximum 125. H-PHASE-020, implementation
contracts and budget approval remain future. Preserve phases 014/015, reviewed WA
plans, installed payload, released versions and Open debts NDEBT-040/NDEBT-034.
Stable NIP3-115…120 aliases map to actual IDs 126…132; NIP3-116 spans core feature 127
and final CI feature 131. Numeric evidence paths use allocated IDs, not alias suffixes.

## Architecture, prerequisites and isolation

Feature 129 binds SBCL using built-ins only, no Quicklisp. handler-bind captures conditions,
backtrace and compute-restarts before unwind; printing is bounded. Cancel must
confirm runtime unwind; otherwise kill the process group, record terminated and
end generation. Feature 130 accepts only committed source through git archive, fresh
sbcl --no-sysinit --no-userinit --non-interactive, private HOME/XDG and empty
ASDF output cache. Source registry/output translations use private roots and
:ignore-inherited-configuration; toolchain, lock and core provenance are captured.
Unsaved definitions, inherited macro/fasl cache and deleted definitions must fail.
ASDF no-op and genuine failure controls distinguish rebuild proof from setup.
Feature 131 introduces the full required sixth CI job only after features 129/130. It runs
--require-sbcl --require-isolation and binds actual checkout/source/test identity.
Case 8 combines stub policy with actual endpoint/network/filesystem denial through
unchanged isolated_trial_adapter.py, using a reachable outside positive control;
missing endpoint/setup failure cannot pass as confinement. Feature 131 also synchronizes
docs, six-job Merge-Done, PR checkbox and py/lisp path resolution. Feature 132 closes only
after the whole 17-row/13-case live matrix and independent capture. No fixed next
release, tag, GA decision or installed upgrade is implied.

Recommended order: phase 017 foundation → phase 016 core → phase 018 controls →
phase 020 fresh acceptance → phase 019 profiles, subject to future activation.
Core requires captured phase 017 foundation; phase 020 requires core feature 128 and trusted phase 018
features 119/120/123. Phase 018 requires feature 127 only, not split alias NIP3-116's later feature 131.
Feature dependencies stay within each list; external receipts and shared-file
serialization are explicit metadata in the existing single coordination model.
Full case 8 mechanism and all required stub/SBCL cases must pass on capable CI
before any case is claimed working. Existing phase 015 schema fixtures are shape proof;
current session results, skipped/unsupported runs and local version are never
acceptance substitutes. Record actual CI job names/checkout identity from completed
runs; trial access stays unavailable. No workstation sysctl changes.

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
| 129 | 650 | 450 | 1,000 | 2,100 |
| 130 | 750 | 650 | 1,200 | 2,600 |
| 131 | 300 | 500 | 800 | 1,600 |
| 132 | 150 | 150 | 750 | 1,050 |
| Total | 1,850 | 1,750 | 3,750 | 7,350 |

Proposed 130% ceiling: 9,555. Product/tests/process buckets already
price registrations, contracts, independent verdicts and planning/close costs;
do not multiply overhead again. Full controller estimate: 13,000 compares retained
4,585 naive × 2.3…2.89 = 10,545…13,251 forecasts. Full-cost splits of 5,650 and 7,350
fit the 7,200/8,600 predecessors; the larger fresh stage prices actual full live CI,
hermetic controls and captured readiness, without trimming scope to match 7,200.
Future budget activation remains separate. Use existing counted classification;
raw evidence/run_state excluded; unclassified fails closed. Rolling comparison
uses only this phase's prior completed features before appending; first feature
has no prior baseline. Cumulative overrun needs actual human authorization.
