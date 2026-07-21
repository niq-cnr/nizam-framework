---
id: nip-0002-zero-to-n-project-spectrum
title: "NIP-0002: The 0–n Project Spectrum"
description: "Proposal that the Ecosystem Engineering Cycle explicitly span an ecosystem of 0 to n projects — 0 (bootstrapping a new project from nothing / greenfield genesis), 1 (a single project, greenfield or brownfield), and n (many associated projects forming a complex ecosystem) — with a scope/membership registry that sets n and a staged, evidence-led realization."
version: 0.2.0
status: accepted
authoritative_source: docs/nips/NIP-0002-zero-to-n-project-spectrum.md
last_audited: "2026-07-21"
tags: [nip, ecosystem, governance, bootstrap, multi-repo, greenfield, brownfield]
change_log:
  - version: "0.2.0"
    date: "2026-07-21"
    summary: "ACCEPTED by the ecosystem operator via gate H-NIP on 2026-07-21 (operator verbatim: 'NIP-0002 is accepted'). Status proposed -> accepted (the UDS frontmatter status field moves draft -> accepted; 'Proposed' is this document's narrative label for the draft state, per the 0.1.0 entry and the Proposal Record). Acceptance SELECTS phase 008 as this NIP's realization — the same way NIP-0001's acceptance selected phase 005 — but does not itself author or activate it: phase-008 planning (a product_spec_008 + feature_list_008 + operator activation gate H-PHASE-008) remains the next planning cycle. Recorded in .agent/run_state.json (event operator_gate_decision) and docs/planning/operator_gates.md (H-NIP second exercise); docs/planning/ROADMAP.md's phase-008 section rolled from candidate to authorized."
  - version: "0.1.0"
    date: "2026-07-21"
    summary: "Initial proposal, status PROPOSED — awaiting operator acceptance (gate H-NIP). Motivated by the operator's design requirement (2026-07-21) that the system must handle ecosystems of 0-n projects, and by the phase-007 scratch-consumer pilot evidence (ADR-004; DEBT NDEBT rows) proving that even the single-project case is not yet consumer-ready. Refines NIP-0001's 'multi-repository' framing to be explicit about project count; on acceptance it becomes the plan of record for phase 008."
---

# NIP-0002: The 0–n Project Spectrum

## Status

**Accepted** (2026-07-21, gate **H-NIP**, operator verbatim: *"NIP-0002 is accepted"*).
This document is a framework-capability proposal in the sense NIP-0001's Placement note
defines (NIPs are broader than a single architecture decision; a NIP may spawn ADRs —
this one spawns `docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`).
Acceptance **selects phase `008` as this NIP's realization**, the same way NIP-0001's
acceptance selected phase `005`; consistent with that precedent, selection is not
activation — phase 008 still needs its own Planner artifacts (`product_spec_008` +
`feature_list_008`) and an operator activation gate (`H-PHASE-008`) before feature work
begins. The staged plan below is the authorized scope that planning cycle will realize.

### Proposal Record

| Field | Value |
|-------|-------|
| Decision | ACCEPTED 2026-07-21 (operator verbatim: "NIP-0002 is accepted") |
| Gate | H-NIP ("Approve a NIP before implementation becomes plan of record") |
| Motivation | Operator design requirement (2026-07-21): "the system must handle ecosystems of 0-n projects … 0 is bootstrapping a new project, through an ecosystem of one project (greenfield or brownfield) through to n associated projects that form a complex ecosystem." |
| Evidence | Phase-007 scratch-consumer pilot (feature 063); `ADR-004`; DEBT rows for pilot findings A–F |
| Consequence of acceptance | Phase `008` **selected** to realize the staged plan below (the deferred `04`/`05` ecosystem protocols and a greenfield-genesis capability are pulled into its scope, evidence-prioritized); phase-008 authoring + activation is the next planning cycle. |

## Problem

The Ecosystem Engineering Cycle (NIP-0001) is described throughout as governing
**multi-repository** ecosystems, but everything shipped and dogfooded to date operates
on exactly **one** repository:

- The tools take a single `--repo-root`; `tools/ecosystem_preflight.py` derives one
  `repository_name`, and its own multi-repo consistency guard is annotated a "defensive
  invariant for a future multi-repository extension." No shipped tool iterates a *set* of
  repositories.
- The genuine n-repo coordination lives in *deferred* protocols
  (`04_dependency_reconciliation`, `05_release_train_coordination`, both Planned) and in
  `standard/cross_repo_governance.md`, which is `enforcement: consumer-aspirational`.
- The **0-case — standing up a *new* project from nothing (greenfield genesis)** — has no
  protocol, tooling, or even vocabulary. "Genesis" and "scaffold" in this repository refer
  only to the framework building *itself* (phase 001). The Bootstrap protocol presupposes
  a consumer repository that already exists.
- Greenfield (new/empty) versus brownfield (existing content) is never named; the empty
  case is treated as the trivial "rarely empty" subcase of brownfield.

The phase-007 pilot made this concrete: the ecosystem tools carry self-fixture
assumptions that break against even a *single* real bootstrapped consumer (see ADR-004).
So the framework cannot honestly claim to serve an ecosystem of any size until it is
explicit about the whole 0-to-n spectrum and the single-project case is actually
consumer-ready.

## Proposed Capability

The Ecosystem Engineering Cycle MUST explicitly model an ecosystem of a variable number
of projects, `0 ≤ count ≤ n`, and every lifecycle stage MUST be defined over that set,
degenerating cleanly to the smaller cases:

- **0 — greenfield genesis.** A first-class capability to stand up a *new* project from
  nothing and bootstrap the framework into it, distinct from adopting into an existing
  repo. The `incubating` partition of the scope registry (below) already models a tracked
  entity that "has not yet met the bar for full in-scope status … pre-implementation" —
  the natural representation of a project at count 0 transitioning to 1.
- **1 — a single project, greenfield or brownfield.** Named explicitly. Greenfield (new/
  empty) and brownfield (existing content, reconciled per `standard/GIP.md` §5.1
  rename-and-diff) are distinct entry paths of the Bootstrap stage, not footnotes.
- **n — a complex multi-repository ecosystem.** The lifecycle operates over the
  membership set: Preflight/Baseline/Audit/Compare run per in-scope repository and
  aggregate; Plan/Promote coordinate across repositories via the deferred `04`/`05`
  protocols and the cross-repo dependency gate.

**Ecosystem membership is set by a scope/registry artifact.** The number `n` is not a
tool flag; it is whatever the consumer's ecosystem-membership registry declares in-scope.
This proposal adopts `registry/scope_definition_patterns.md`'s list-partition shape
(`in_scope` / `incubating` / `reference_archive` / `out_of_scope` + `depends_on`) as the
required, named membership artifact the tools read — replacing the current single
`--repo-root` with iteration over the in-scope set. The Bootstrap protocol's
"Consumer-Supplied Inputs" already names "its own registry of in-scope repositories" as
the hook.

## Goals

- Make the 0/1-greenfield/1-brownfield/n cases explicit, named, and individually
  addressable across the Bootstrap protocol, the tools, and the membership registry.
- Make the single-project case genuinely consumer-ready first (ADR-004), since it is the
  prerequisite for every larger count.
- Reuse existing shapes (GIP adoption tiers; `scope_definition_patterns` partitions;
  provenance pin) rather than inventing parallel mechanisms.

## Non-Goals

- Auto-declaring GA or auto-consolidating across repositories (those remain human-gated:
  `H-GA`, `H-CONSOLIDATION`).
- Shipping any consumer's actual registry data; the framework ships the shape and the
  tooling, the consumer authors its membership.
- Building the whole spectrum speculatively in one step — realization is staged and
  evidence-led (below), honoring "no claim beyond its evidence."

## Staged Realization (phase 008 authorized scope)

1. **Consumer-readiness (prerequisite).** Realize `ADR-004`: governance-root resolution
   and provenance-pin anchoring, so Preflight/Baseline run against a real single consumer.
2. **The 0-case.** A greenfield-genesis capability: create + scaffold a new project and
   bootstrap the framework into it, with `incubating → in_scope` as the tracked transition.
3. **The n-case.** Extend the tools to iterate the ecosystem-membership registry (a set of
   repo-roots) instead of one `--repo-root`; promote `registry/scope_definition_patterns.md`
   from draft patterns to a required, validated membership artifact.
4. **n-coordination protocols.** Author the deferred `04_dependency_reconciliation` and
   `05_release_train_coordination` (with their companion schemas) — where cross-repo
   ordering and release-train entry genuinely live.

Each stage lands under the normal phase discipline (contract-first, dogfooded, CI-green),
and no stage is claimed working until it is proven against real evidence.

## Relationship to NIP-0001

NIP-0001 introduced the Ecosystem Engineering Cycle and described it as multi-repository
but realized only the single-repository core loop. NIP-0002 does not supersede it; it
**refines** its scope model to be explicit about project count (0…n) and makes the
membership registry the artifact that sets `n`, so the "multi-repository" language
NIP-0001 already uses is backed by a defined mechanism rather than deferred prose.

## Acceptance Criteria

- **Met (2026-07-21).** Operator accepts this NIP (gate H-NIP), selecting phase 008 as
  its realization. Phase-008 authoring + activation (`product_spec_008`,
  `feature_list_008`, `H-PHASE-008`) is the next planning cycle.
- **Met.** The Bootstrap protocol (`ecosystem/00_ecosystem_bootstrap.md`) names and
  scopes the 0/1-greenfield/1-brownfield/n cases (v0.2.0, referencing this NIP).
- **Pending phase 008.** Phase 008 delivers the staged plan above in evidence-prioritized
  order, beginning with the ADR-004 consumer-readiness fixes.

## References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` — the cycle this proposal refines.
- `docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md` — the ADR this NIP
  spawns, capturing the pilot-proven single-project fixes.
- `ecosystem/00_ecosystem_bootstrap.md` — the Bootstrap protocol amended to name the 0–n
  spectrum.
- `registry/scope_definition_patterns.md` — the list-partition registry shape adopted as
  the ecosystem-membership artifact that sets `n`.
- `standard/GIP.md` §5 — the incremental adoption tiers and brownfield reconciliation.
- `docs/planning/DEBT.md` — the NDEBT rows recording the pilot's 0–n gaps.
