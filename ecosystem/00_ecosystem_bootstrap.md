---
id: nizam-ecosystem-bootstrap
title: "Ecosystem Bootstrap Protocol"
description: "The reusable protocol for the ecosystem cycle's entry stage: how a consumer repository adopts the framework from a pinned, immutable released tag via the Governance Inheritance Protocol, verifies the injected payload, records its provenance pin, and reaches the clean, known state a Preflight run requires before any later stage may begin -- explicit about the 0-to-n project spectrum the stage must serve."
version: 0.5.0
status: active
authoritative_source: ecosystem/00_ecosystem_bootstrap.md
change_log:
  - version: "0.5.0"
    date: "2026-07-22"
    summary: "Phase-009 feature 070 (NDEBT-030; NIP-0002 Stage 2): the 0-case (greenfield genesis) becomes a first-class protocol. New Section 8 (Greenfield Genesis: Standing Up a New Project From Nothing) defines the create-and-scaffold entry path — create the repository, scaffold a minimal deterministic skeleton + the consumer-supplied inputs (Section 6), perform the normal inject + verify (Section 5) recording provenance (Section 7), and register the project as incubating (the count-0->1 state) for promotion incubating -> in_scope. Establishes 'genesis'/'scaffold' vocabulary for standing up a NEW consumer project, distinct from the framework's own phase-001 genesis. The Section 3 spectrum table's 0-case row and the 'two honest limits' prose are corrected from 'no protocol or tooling yet' to 'protocol defined (Section 8); create-and-scaffold capability + incubating->in_scope transition mechanized in NIP-0002 Stage 2'. References (former Section 8) renumbered to Section 9; Sections 4-7 (and every cross-reference to the Section 7 provenance shape) are unchanged."
  - version: "0.4.0"
    date: "2026-07-21"
    summary: "Phase-008 feature 068 (NDEBT-032, resolved-by-design / operator Option A): the 1-brownfield case (Section 3 table + Section 5.1) is corrected from 'documented but not yet mechanized in bootstrap.sh' to 'covered by construction' — bootstrap.sh injects only the .nizam/ payload and never writes to a consumer's root CONTEXT.md/AGENTS.md/CI (GIP Section 5.1 point 3), so it cannot silently overwrite them; reconciling a consumer's own root files against .nizam/templates/ is inherently a consumer-side manual rename-and-diff, not a bootstrap.sh operation. No bootstrap.sh change (the atomic .nizam/-only inject already satisfies GIP Section 5.1's safety). NDEBT-032 moved to Resolved in docs/planning/DEBT.md."
  - version: "0.3.0"
    date: "2026-07-21"
    summary: "Phase-008 feature 067 (NDEBT-033): Section 7 (Bootstrap Artifact) now documents the provenance.json resolved_sha field — the exact commit the pinned tag resolved to at install — as part of the recorded pin. Describes that the resolved commit makes the pin immutable (a tag name alone can be moved to replay a different payload) and that bootstrap.sh --verify-only requires the recorded commit present and, with a caller-supplied --expected-sha, rejects a differing commit. Kept in lockstep with bootstrap.sh and standard/GIP.md Section 4."
  - version: "0.2.0"
    date: "2026-07-21"
    summary: "Made the 0-to-n project spectrum first-class (new Section 3), on the operator's 2026-07-21 design requirement that the system span an ecosystem of 0 to n projects: names and scopes the 0 (greenfield genesis), 1-greenfield, 1-brownfield, and n (multi-repository) cases, states honestly which are mechanized today versus delegated to the GIP tiers, the scope-membership registry, or the deferred 04/05 coordination protocols, and cross-references docs/nips/NIP-0002-zero-to-n-project-spectrum.md as the capability framing and docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md as the pilot-proven single-project fixes. Renumbered the subsequent sections (former 3-7 become 4-8). PR #42 review correction: the Section 2 determinism statement is scoped to the injected payload and framework pin only — the provenance install timestamp (Section 7) may differ between runs and is explicitly excluded, rather than claiming reruns reproduce identical recorded provenance."
  - version: "0.1.0"
    date: "2026-07-20"
    summary: "Initial Bootstrap-stage protocol (phase-007 feature 060). The canonical lifecycle (ecosystem/README.md) begins at Bootstrap, but the stage had no protocol document until now -- it is authored here by wrapping, not restating, the Governance Inheritance Protocol (standard/GIP.md) and bootstrap.sh: the pinned-immutable-tag precondition, the injected six-module payload + NIZAM.json, verification and provenance/drift, the consumer-supplied inputs each ecosystem must provide, and the entry condition into Preflight (ecosystem/01_clean_state_preflight.md). Flips the ecosystem/README.md Module Navigation status for 00 from Planned to Shipped."
---

# Ecosystem Bootstrap Protocol

## 1. Overview

This document is the single source of truth for the ecosystem module's Bootstrap
step -- the first stage of the canonical lifecycle (`ecosystem/README.md`), the one
by which a consumer repository adopts the framework so it can participate in the
cycle at all. Nothing downstream in the lifecycle -- Preflight, Baseline, Audit,
Plan, Execute, Verify, Promote, Compare -- can run in a consumer that has not
bootstrapped: the later stages read the injected governance payload (`standard/`,
`schema/`, `tools/`, `methodology/`, `ecosystem/`, `NIZAM.json`), and a repository
that has not inherited that payload from a pinned framework release has nothing for
them to read.

This protocol does not re-define the mechanics of inheritance; those are owned once,
authoritatively, by the Governance Inheritance Protocol (`standard/GIP.md`) and its
canonical implementation `bootstrap.sh`. What this protocol defines is the Bootstrap
*stage* of the ecosystem cycle: its precondition, the required outcome, the
consumer-supplied inputs the rest of the cycle depends on, and the exact state a
successful Bootstrap must leave behind so that the Preflight stage
(`ecosystem/01_clean_state_preflight.md`) has a clean, known reference point to gate
from.

Consumers extend this protocol with their own repository- and ecosystem-specific
adoption details (which directory holds the injected payload, which pre-existing
files they must reconcile); they do not redefine its pinned-tag precondition, its
verification requirement, or its provenance rule. Those three mechanics are defined
once, here, exactly as `standard/GIP.md` is the single source of truth for the
inheritance operation this stage performs.

## 2. When to Run

A Bootstrap run MUST occur:

- When a repository adopts the framework for the first time, before any other
  ecosystem-cycle stage is attempted against it.
- When a consumer upgrades to a newer framework release -- a new pinned tag is a new
  Bootstrap, re-run in full against the new tag, never a hand-patch of the installed
  payload (`standard/GIP.md` Section 4: remediation for drift is re-bootstrap, never
  in-place mutation).
- Whenever a compliance check (`standard/GIP.md` Section 3) finds the installed
  payload missing, unreadable, or drifted from its recorded pin.

Adopting or upgrading a consumer to a newly released framework tag is an
operator-gated decision -- the human gate `H-CONSUMER-UPGRADE`
(`docs/planning/operator_gates.md`) -- exactly as the Promote stage is human-gated.
The pipeline records the adoption decision; it never adopts on a human's behalf.

A Bootstrap run is deterministic and repeatable with respect to the injected payload
and the framework pin: re-running it against the same pinned tag and the same target
reproduces the same injected payload and the same recorded pin. Installation metadata
in the provenance artifact — notably the recorded install timestamp (Section 7) — may
differ between runs and is not part of that determinism.

## 3. Ecosystem Scale: The 0-to-n Project Spectrum

An "ecosystem" is not a fixed shape. The Bootstrap stage must serve a consumer at any
point on a spectrum of `0` to `n` projects, and this protocol is explicit about which
point a given run is entering the cycle at. The capability framing for the whole
spectrum is `docs/nips/NIP-0002-zero-to-n-project-spectrum.md`; this section states
what the Bootstrap stage covers today and what it delegates.

| Point | What it is | Bootstrap-stage coverage today |
|-------|-----------|--------------------------------|
| **0** -- greenfield genesis | Standing up a *new* project from nothing and bootstrapping the framework into it, distinct from adopting into a repository that already exists | **Protocol defined (Section 8).** Section 8 (Greenfield Genesis) makes the create-and-scaffold entry path first-class: create the repository, scaffold the minimal deterministic skeleton + consumer-supplied inputs (Section 6), then perform the normal inject + verify (Section 5) recording provenance (Section 7). A genesis'd project is tracked in the scope registry's `incubating` partition (`registry/scope_definition_patterns.md`) -- the count-0->1 state -- and promoted `incubating -> in_scope`. The create-and-scaffold *capability* and that registry transition are mechanized in NIP-0002 Stage 2 (phase 009). |
| **1 -- greenfield** | A single repository that is new/empty | Covered as the degenerate, collision-free case of Section 5.1: with nothing pre-existing to reconcile, an inject + verify is the whole Bootstrap. |
| **1 -- brownfield** | A single repository with existing content | **Covered.** `bootstrap.sh` injects only the `.nizam/` payload directory and never writes to a consumer's root-level `CONTEXT.md`/`AGENTS.md`/CI (`standard/GIP.md` Section 5.1 point 3), so it *cannot* silently overwrite pre-existing content -- the coexistence safety is guaranteed by construction. Reconciling a consumer's own root files against the shipped `.nizam/templates/` is, by that same protocol, an inherently consumer-side manual (rename-and-diff) step, not a bootstrap.sh operation; adoption tiers (`standard/GIP.md` Section 5.2) govern how much is adopted. Section 5.1 below is the stage-level rule. |
| **n -- multi-repository** | Many associated repositories forming one ecosystem | **Partially covered.** Each repository bootstraps individually by this protocol; the *set* is declared by the consumer's ecosystem-membership registry (`registry/scope_definition_patterns.md`, the `in_scope` partition), which sets `n`. The shipped ecosystem tools take a single `--repo-root` and do not yet iterate that set; genuine cross-repository coordination lives in the deferred `04_dependency_reconciliation.md` and `05_release_train_coordination.md` protocols. |

Two honest limits follow from the table and are recorded as debt rather than papered
over. First, **the 0-case now has a protocol (Section 8) but its create-and-scaffold
tooling and `incubating -> in_scope` transition are being mechanized in NIP-0002 Stage 2**
(phase 009): the vocabulary is now unambiguous -- "genesis" and "scaffold" here mean
standing up a *new consumer project*, kept distinct from the framework building *itself*
(phase 001) -- but the single-command capability that performs the create-and-scaffold is
Stage-2 tool work, not yet a released capability. Second, **the shipped tools are
single-repo**: `tools/ecosystem_preflight.py` derives one `repository_name`, and its
multi-repository consistency guard is annotated a defensive invariant for a future
extension. A consumer running the cycle over more than one repository today runs it once
per repository and aggregates by hand. The n-case is deferred to phase 010 (NIP-0002
Stages 3-4); the single-project fixes that even a count-of-1 pilot proved necessary are
recorded in `docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`.

Whatever the count, a Bootstrap is always performed *per repository*: `n` repositories
means `n` Bootstrap runs, each satisfying this protocol's precondition, verification,
and provenance rules, against the same pinned framework tag. The membership registry
records which repositories are in scope; the Bootstrap stage brings each one into the
cycle.

## 4. Pinned-Immutable-Tag Precondition

A Bootstrap MUST inherit from a specific, immutable, released framework tag (for
example `v0.8.0`), never a floating branch reference. `main`, `master`, `HEAD`, and
any `refs/heads/*` branch are refused: pinning is what prevents a consumer from
silently inheriting mid-development governance changes it never reviewed
(`standard/GIP.md` Section 2, point 1; `bootstrap.sh` enforces this by refusing an
unpinned ref). A consumer that "adopts the framework" from a floating ref has not
performed a valid Bootstrap and MUST NOT be treated as having entered the cycle.

The pinned tag is the anchor every later stage's evidence is measured against: the
Baseline's `framework_references` (`ecosystem/02_evidence_baseline.md` Section 3)
records exactly this tag, and a Compare across two executions is only meaningful when
each side names the framework pin it ran under.

## 5. Injected Payload and Verification

A Bootstrap injects the framework's six governance module directories -- `standard/`,
`templates/`, `schema/`, `tools/`, `methodology/`, `ecosystem/` -- together with the
root `NIZAM.json` capability index, into the consumer's declared target location
(conventionally `.nizam/`). `registry/` and `docs/` are framework-envelope and are
never injected. This payload is defined authoritatively by `standard/GIP.md` Section
2, point 2; this protocol does not restate its contents, it requires that a Bootstrap
land exactly that set.

Inheritance is not complete until it is verified. `bootstrap.sh` performs
clone -> inject -> verify as one atomic operation and MUST exit non-zero, with a
diagnostic naming the specific missing or invalid artifact, if any required file is
absent, the `NIZAM.json` index fails to parse or resolve, or any injected governed
document fails frontmatter validation (`standard/GIP.md` Section 2.1). A silent
partial injection is a protocol violation: the consumer MUST treat a non-zero exit as
"inheritance did not happen," never as "inheritance mostly happened." A Bootstrap
that has not verified has not produced a state any later stage may run against.

### 5.1 Coexisting With a Non-Empty Repository

A consumer is rarely empty when it first adopts the framework (the 1-brownfield case
of Section 3). Bootstrapping MUST coexist with what the repository already has, never
silently overwriting it. This coexistence is guaranteed **by construction**:
`bootstrap.sh` injects only the `.nizam/` payload directory (an atomic replace of that
one target) and never writes to a consumer's root-level `CONTEXT.md`, `AGENTS.md`, or CI
configuration (`standard/GIP.md` Section 5.1 point 3), so it cannot overwrite them at
all. Reconciling a consumer's own pre-existing root files against the framework's shipped
`.nizam/templates/` versions -- the rename-and-diff of `standard/GIP.md` Section 5.1 -- is
therefore an inherently consumer-side manual step, not something `bootstrap.sh` performs;
a consumer's own CI configuration is likewise added to, never replaced. A consumer MAY also adopt
incrementally through the tiers `standard/GIP.md` Section 5.2 defines
(`docs-standard-only` -> `templates` -> full loop) rather than the full contract-first
loop on day one; the Bootstrap stage is complete for whichever tier the consumer
declares, provided that tier's payload is injected and verified. The 1-greenfield case
of Section 3 is the degenerate subcase of this rule: an empty repository has nothing to
reconcile, so inject + verify is the whole stage.

## 6. Consumer-Supplied Inputs

The framework deliberately encodes no consumer's specifics. A bootstrapped consumer
that intends to run the full cycle MUST supply, in its own repository, the
ecosystem-specific inputs the later stages consume: its own registry of in-scope
repositories (the ecosystem-membership artifact that sets `n`, Section 3), its scope
boundaries, its scoring thresholds, its finding owners, and its own operator gates
(`docs/nips/NIP-0001-ecosystem-engineering-cycle.md`). These are the consumer's to
define; this protocol requires only that they exist before a stage that depends on
them runs -- for example, Preflight's consumer-registered blocking conditions
(`ecosystem/01_clean_state_preflight.md` Section 4) have no meaning until the consumer
has declared them. A Bootstrap that injects the payload but leaves these inputs
unspecified has adopted the framework's governance documents without yet being able to
run the cycle end to end, which is a valid `docs-standard-only`/`templates` tier
(Section 5.1), not a failure.

## 7. Bootstrap Artifact

Every Bootstrap MUST record its provenance in a machine-readable artifact at the root
of the injected payload:

```text
<target>/provenance.json
```

where `<target>` is the consumer's declared payload location (conventionally
`.nizam/`). The artifact records at least the inherited framework version, the pinned
`tag`, the **`resolved_sha`** (the exact commit that tag resolved to at install time),
the source the payload was cloned from, and when it was installed, so that later drift
detection (`standard/GIP.md` Section 4) and every stage's `framework_references` have a
baseline to compare against. The `resolved_sha` makes the pin an **immutable commit**,
not merely a tag *name*: a tag can be moved on the remote to replay a different payload,
so `bootstrap.sh --verify-only` requires the recorded commit to be present and, given a
caller-supplied expected SHA (`--expected-sha`, resolved out-of-band from the authentic
tag), rejects a recorded commit that differs (`NDEBT-033`). `bootstrap.sh` writes this
artifact as part of its verified install; a consumer MUST NOT synthesize it by hand,
since a hand-authored pin that does not match the injected payload is precisely the
drift the artifact exists to detect. The framework pin recorded here -- not the
consumer's own HEAD -- is what a Baseline's `framework_references` must anchor to
(`docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`).

Evidence backing a Bootstrap run (the clone/inject/verify tool output) is externalised
by path under the consumer's `.agent/evidence/<execution-id>/`, per the framework's
Evidence Capture Convention (`methodology/04_tool_driven_state.md` Section 5) -- never
pasted inline into the provenance artifact or into a chat transcript.

## 8. Greenfield Genesis: Standing Up a New Project From Nothing

The `0` point of the spectrum (Section 3) is *greenfield genesis*: there is no repository
yet. Every other Bootstrap path presupposes a repository that already exists -- brownfield
(Section 5.1) reconciles with existing content; 1-greenfield injects into an empty-but-existing
repo. Genesis is the entry path that *creates* the project the rest of the cycle will run
against, then brings it into the cycle by the same inject + verify this protocol already
defines. It does not introduce a second inheritance mechanism; it composes the ones above.

"Genesis" and "scaffold" here mean standing up a **new consumer project** -- deliberately
distinct from the framework's own genesis (phase 001 built *the framework itself*). A consumer
never re-runs the framework's genesis; it runs *its own*, once, to come into existence as a
cycle participant.

A conforming greenfield genesis MUST, in order:

1. **Create the project.** Initialize a new version-controlled repository at the target
   location (`git init`), carrying no inherited history from the framework.
2. **Scaffold a minimal, deterministic skeleton.** Write the smallest project that is a valid
   cycle participant: a project `README`, at least one source placeholder that gives the Audit
   stage something real to measure, and -- critically -- the **consumer-supplied inputs Section
   6 requires** (the consumer's own registry of in-scope repositories, scope boundaries, scoring
   thresholds, finding owners, and operator gates). The skeleton is deterministic: the same
   genesis inputs produce the same scaffold, so a genesis is repeatable.
3. **Inject and verify the framework payload.** Perform the normal Bootstrap of Section 5
   against the just-created project -- clone the pinned immutable tag (Section 4), inject the
   `.nizam/` payload, verify it, and record the provenance artifact (Section 7). Genesis reuses
   this mechanism exactly; it does not redefine it.
4. **Register the project as `incubating`.** A newly genesis'd project is tracked in the
   ecosystem-membership registry's `incubating` partition
   (`registry/scope_definition_patterns.md`) -- the count-0->1 state: real enough to track, not
   yet a full member. Promotion `incubating -> in_scope` is the transition that makes the
   project count toward `n` (Section 3), performed once it has cleared its first clean
   Preflight/Baseline.

After these four steps the project is an ordinary bootstrapped consumer at a known pin, and it
**enters the cycle at Preflight** (`ecosystem/01_clean_state_preflight.md`) exactly as any other
bootstrapped repository -- genesis leaves behind precisely the clean, known state Section 5
requires, plus a scaffold for the later stages to measure and an `incubating` registry entry
recording the crossing from count 0 to count 1.

Genesis is bounded by refusal on a non-empty target: a target that already contains a project is
a brownfield adoption (Section 5.1), not a genesis, and a genesis capability MUST refuse to
scaffold over existing content rather than overwrite it -- the same coexistence safety Section
5.1 guarantees, enforced at creation time.

The create-and-scaffold capability that mechanizes steps 1-2, and the `incubating -> in_scope`
registry transition of step 4, are framework tooling delivered alongside this protocol in
NIP-0002 Stage 2; the inject + verify of step 3 and the provenance artifact of step 4 are the
existing `bootstrap.sh` mechanics this protocol already owns. Until that capability is released,
the protocol above is the authoritative definition of what a conforming genesis must produce.

## 9. References

- `standard/GIP.md` -- the Governance Inheritance Protocol whose inheritance
  operation this stage performs; the single source of truth for the pinned-tag clone,
  the injected payload, verification, drift detection, and existing-repository
  adoption this protocol wraps.
- `bootstrap.sh` -- the canonical, reusable clone -> inject -> verify implementation a
  consumer invokes rather than reimplementing the steps.
- `ecosystem/README.md` -- the module index and canonical lifecycle this protocol is
  the first stage of.
- `ecosystem/01_clean_state_preflight.md` -- the immediately following lifecycle
  stage: a bootstrapped, verified consumer at a known pin is the precondition a
  Preflight run gates from.
- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md` -- the accepted NIP defining the
  lifecycle this stage opens and the consumer-supplied inputs each ecosystem provides.
- `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` -- the capability proposal that
  makes the 0-to-n project spectrum (Section 3) first-class and sets phase 008's scope.
- `docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md` -- the pilot-proven
  decisions that a Baseline anchor to the injected framework pin and that the tools
  resolve the injected payload under a governance-root.
- `registry/scope_definition_patterns.md` -- the list-partition registry shape whose
  `in_scope`/`incubating` partitions serve as the ecosystem-membership artifact that
  sets `n` (Section 3).
- `docs/planning/operator_gates.md` -- the operator-gate registry defining
  `H-CONSUMER-UPGRADE`, the human gate that approves a consumer's adoption of or
  upgrade to a newly released framework tag.
- `methodology/04_tool_driven_state.md` -- the Evidence Capture Convention this
  protocol's evidence externalisation follows.
