# Measurement and evidence policy

This file fixes the vocabulary used by the program so that evidence classes are
not silently promoted. It does not itself approve any experiment or spending.

## 1. Evidence classes

| Class | Meaning | May support |
| --- | --- | --- |
| inspected-source | A source read at a named commit | defect existence, design review |
| PR-reported | Test/result text in a PR | lead only |
| synthetic-fixture | A constructed input | contract/parser conformance |
| local-conformance | A local test run at a named candidate | deterministic behavior |
| actual-host-isolation | A real isolated host trial | isolation claims for that host |
| actual-provider-observation | A real provider call with request identity | live compatibility for that exact config |
| exact-stored-replay | Replay of a stored observation, no model call | reproducibility |
| independently-adjudicated-semantic-quality | Blinded, frozen-label evaluation | semantic quality claim |
| operational-comparison | Real admitted workflow comparison | enable/hold/reject |
| release-install-identity | Bytes/inventory of a real release and install | release/install claim |
| real-consumer-migration | An actual consumer upgrade | adoption claim |
| staged-operation | Monitored rollout cohort | production-support claim |

Promotion between classes requires the corresponding execution. A green test
run does not become a live qualification because it is repeated.

## 2. Corrections to historical claims

- The 61.1% and 45.1% figures were supplied-unit / local-study results, not
  measured end-to-end LLM savings.
- Seeded blockers were not independent defect discoveries.
- Local shell timing was not provider latency.
- The 12 paired / 24 captured records remain valid historical evidence under
  those labels. They are not re-minted as current operational results.
- Shadow counterfactuals are not realized workflow savings.

## 3. Economics

For a frozen cohort/window:

```
cost_per_accepted_change =
    sum(all attributable provider attempts, fallbacks, retries, rework)
    / count(distinct independently accepted changes)
```

Rules:

- Include failed and abandoned work in the numerator.
- Deduplicate accepted identity; handle superseding changes explicitly.
- Report monetary values with currency and a dated price basis.
- Report provider/billing measurements separately from price-derived estimates.
- Report unresolved/unknown charges and coverage separately.
- A zero accepted-change denominator is **undefined**, not zero cost and not a
  fabricated saving.
- Missing usage is **unknown**, not zero.
- A batched request is charged once; per-question allocation is an estimate.
- Reviewer time, setup, evaluation and maintenance are reported separately
  unless a declared common monetary valuation is used.

## 4. Comparison arms

- **A** — repaired, instrumented Nizam with semantic provider off.
- **B** — existing model answers the same atomic questions with the same
  deterministic composition.
- **C** — exact pinned Jev configuration with matched projection and policy.
- **D** — exact deterministic rules where the question genuinely permits them;
  abstain elsewhere.

`C - B` estimates additional provider effect under matched conditions. `B - A`
measures the architecture/decomposition package unless projection, prompt,
runner and other factors are controlled. `D` identifies unnecessary model work.
No single aggregate metric may conceal a critical family regression.

## 5. Pre-registration requirements

Before a live cohort: task assignment/randomization or matching, clustering,
carryover controls, blinded outcome adjudication where practicable,
follow-up/rework window, sample-size rationale, quality/non-inferiority and
critical-miss tolerances, coverage/abstention criteria, latency/cost limits,
uncertainty method and stopping rule. Thresholds are not chosen after seeing
held-out results.

If thresholds or budget lack authority, prepare a concrete risk-based proposal
and obtain a decision. Do not fabricate approval or mark evaluation complete.
