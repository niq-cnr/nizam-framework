# Authority and external gates

The mandate authorizes ordinary reversible engineering inside the owning
agent's permitted role. It does **not** confer the following. Each gate names
the concrete decision that unlocks it.

## A1 — Feature contract approval (semantic source work)

- Affected: JR-12 … JR-34, JR-38, JR-40 where the change is a feature rather
  than a bounded small-change.
- Missing authority: an approved per-feature contract through the repository's
  Planner → independent contract-review mechanism.
- Prepared without it: design, typed contracts, pure functions, fixtures and
  offline tests against a pinned contract.

## A2 — Provider account, permitted data and budget

- Affected: JR-14 live transport qualification, JR-23 shadow, JR-24 advisory.
- Required decision: exact provider, exact model version, permitted repository
  data classes, spend ceiling, deadline, account owner and retention terms.
- Prepared without it: mock transport, replay, accounting fixtures and
  pre-registration.

## A3 — Release, merge and consumer upgrade

- Affected: JR-42, JR-43.
- Required decision: approval to publish a preview release, name the pilot
  consumer cohort, and authorize the supported upgrade/rollback window.
- Prepared without it: release candidate, manifests, migration rehearsal
  against local disposable consumers.

## A4 — Production influence

- Affected: JR-43 governed operation.
- Required decision: independently qualified exact family/consumer/model/
  question/projection/policy configuration and a bounded action set.

## A5 — Independent assurance and final acceptance

- Affected: JR-22, JR-44.
- Required decision: independent reviewer assignment and the Operator's final
  acceptance or explicit residual disposition.
- Implementers may prepare the dossier and recommend; they may not certify it.

## Non-inheritance

- No prior temporary override authority applies.
- No historical smoke-spending ceiling applies.
- No prior feature contract applies to this program.
- A source merge, test fixture or version string is not an installed upgrade.
