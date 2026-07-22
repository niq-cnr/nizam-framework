# 0-case pilot evidence — feature 074 (phase 009 close)

Pilots the **0-case (greenfield genesis)** end-to-end with the phase-009 capability: a *new*
project stood up **from nothing** by `bootstrap.sh --genesis`, then run through the ecosystem
loop with **no hand-applied workaround**. The project (`greenfield-demo`) was created by genesis
itself — `git init` + the deterministic scaffold (README + CONTEXT + `src/PLACEHOLDER.md`) + the
injected `.nizam/` payload — from an ephemeral tag on the phase-009 branch HEAD, so its injected
payload carries the fixed tools (065–073). The consumer is ephemeral (discarded); only these
framework-side snapshots are committed.

## Outcome — the 0-case runs from nothing

| Step | Result | Evidence |
|---|---|---|
| **Genesis** — create a new project from nothing (`bootstrap.sh --genesis --project-root … --tag …`) | Project stood up: `git init` + scaffold (`README.md`, `CONTEXT.md`, `src/PLACEHOLDER.md`) + injected `.nizam/` | `genesis_scaffold_listing.txt` |
| **Provenance** — the injected payload is pinned | `provenance.json` records `tag` + `resolved_sha` (an immutable commit pin, feature 067) | `provenance_with_resolved_sha.json` |
| **Preflight** — the genesis'd project enters the cycle | **PASS_WITH_EXCEPTIONS** — the injected `.nizam/` is the *single* expected `injected_governance_payload` exception; no hard FAIL, no workaround | `preflight_PASS_WITH_EXCEPTIONS.json` |
| **Membership** — the count-0→1 state | the project is tracked `incubating` (awaiting its first clean cycle before promotion `in_scope`), per `scope_definition_patterns.md` §2.3 | `incubating_registry_sample.json` |

The 0-case that phase 008 recorded as **absent** (`NDEBT-030`) now runs end-to-end: from an empty
directory to a bootstrapped, Preflight-clean cycle participant, entirely via
`bootstrap.sh --genesis`, with the injected `.nizam/` the only Preflight exception — the same
clean outcome ADR-004 gave the count-1 case. Standing hermetic coverage is
`tools/e2e_bootstrap_test.sh` `assert_genesis` (feature 073).

## Gate

The `H-CONSUMER-UPGRADE` gate was recorded before the genesis bootstrap ran (NDEBT-018). As in
the phase-008 re-pilot, this is a **pre-release / branch-HEAD pilot** (the fixed 070–073 tools are
unreleased), exercising the gate's decision mechanics — **not** a released-immutable-tag adoption.
A released-tag genesis of a real project stays outstanding until the next `H-FRAMEWORK-RELEASE`
cuts a tag carrying the genesis capability (`NDEBT-029`).

## Residual

- The genesis capability is proven on the branch but is **not yet in a released tag** — a consumer
  on the released pin gets `--genesis` only once the next release cuts a tag carrying it
  (`NDEBT-029`, the same released-tag gap as the audit/compare tools).
- A **real, non-scratch greenfield project** remains the open production-maturity criterion across
  the whole 0–n programme (a scratch genesis exercises mechanics, not real project maturity).
  Carried into the phase-010 candidate scope alongside NIP-0002 Stages 3–4.
