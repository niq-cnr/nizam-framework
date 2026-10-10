---
id: nizam-review-gate-flake-management
title: "Review-Gate Flake Management"
description: "Operational doctrine for infrastructure failures of a convergent review gate: fail-closed principles, an open flake-class taxonomy, a bounded retry ladder, protected-repository rules, telemetry, evidence duties, and flake-rate targets."
version: 0.1.0
status: active
authoritative_source: methodology/09_review_gate_flake_management.md
change_log:
  - version: "0.1.0"
    date: "2026-09-30"
    summary: "Initial doctrine: scope and fail-closed principles; the open F1-F6 flake-class taxonomy; the bounded retry ladder with class-exception duties; protected-repository rules; telemetry duties; evidence duties including post-merge evidence races and canonical-vs-vendored resync waves; and the KPI targets."
---

# Review-Gate Flake Management

## 1. Overview

A convergent review gate (`standard/convergent_code_review.md`) can end red for
reasons that have nothing to do with the change under review: the provider
returned an empty completion, the orchestration hung past its kill deadline, the
packet was too large for the reviewer to act on, or the gate finished but could
not publish its result. This document is the operational doctrine for that
failure family.

It is the sibling of the Universal Circuit Breaker
(`methodology/03_circuit_breaker.md`): the breaker bounds loops whose step fails
on the merits of the work — a rejected contract, a failing rework, a review that
returns a genuine `request_changes` verdict. This document governs what happens
when the gate machinery itself fails while the change under review may be
perfectly sound. The boundary is absolute: a red run carrying a genuine review
verdict is a verdict and follows the review standard; a red run caused by
infrastructure is a flake and follows this document.

Throughout, placeholder vocabulary keeps the doctrine instance-agnostic:
`<review gate>` (the consumer's automated review gate), `<packet>` (the
authenticated change packet the gate reviews), `<ledger>` (the run-outcome
ledger defined in Section 6), and `<protected repos>` (the repositories that
admit no class exceptions, Section 5).

## 2. Scope and Principles

In scope: any run of `<review gate>` whose failure to complete is attributable
to the gate stack — model provider, orchestration harness, packet shape, or
publication transport — rather than to findings about the change. Out of scope:
red runs carrying genuine blocking findings; those are verdicts and follow
`standard/convergent_code_review.md`, with attempt accounting under
`methodology/03_circuit_breaker.md` as usual.

Five principles govern every flake response:

1. **Fail-closed is correct.** A gate that cannot complete MUST report red or
   absent, never green. An absent, stale, or failed automated review means the
   change is NOT merge-ready (`standard/ci_gates.md`, `AUTOMATED_REVIEW_CLEAN`).
2. **Red is non-terminal.** An infrastructure red carries no judgment about the
   change. It authorizes exactly the retry ladder of Section 4 — nothing more.
3. **Never fake green.** No actor may mark the gate satisfied without the
   gate's own output. Synthesizing, predicting, or copying a prior run's green
   over a current red is prohibited in every circumstance.
4. **Flake is not a verdict.** A flake MUST NOT be recorded as review approval,
   and a genuine finding MUST NOT be reframed as a flake to dodge it.
   Classification under Section 3 is evidence-bound, not convenience-bound.
5. **A green claim requires the gate's own output.** The only acceptable green
   is a completed run of `<review gate>` on the exact merge head, published by
   the gate itself.

## 3. Flake-Class Taxonomy

Every failed gate run is classified into exactly one class before any retry or
exception is considered. The taxonomy is open: a new class MAY be added only
with production evidence — the telemetry artifact plus the diagnosing narrative
— and a versioned revision of this document (`standard/NDS.md` Section 4).

| Class | Name | Signature |
|---|---|---|
| F1 | no-output | Provider or model returns an empty or unparseable completion; a trial produces no observation document at all. |
| F2 | hang / timeout | Orchestration-level: a trial exceeds its timeout budget and is killed (trial timeouts plus kill-after); the run dies on the clock, not on a verdict. |
| F3 | behavior / mis-tie | The gate completes but mis-ties output to input: output-schema ambiguity (an expected artifact is mis-shaped or mis-keyed, resolved in operations by adding the expected file) or index hallucination (findings keyed to paths or line numbers that do not exist in `<packet>`). |
| F4 | large-packet zero-write | On an oversized `<packet>` the reviewer deterministically makes zero write attempts — completion arrives, no observations are produced. Size-dependent and reproducible on the same packet. |
| F5 | posting / API failure | The gate completes internally but cannot publish its result — transport rejection, permissions, rate limit; the verdict exists but is unreachable. |
| F6 | provider-degradation window | Time-clustered failures across otherwise-unrelated runs (same model, same time-of-day); a base-rate spike rather than a packet-specific defect. |

Class citation is mandatory downstream: the exception records, ledger entries,
and KPI rollups of Sections 4, 6, and 8 all name the class. A run that cannot be
classified from its evidence is not a flake; it is an unknown failure and waits
for diagnosis.

## 4. The Bounded Retry Ladder

Failed gate attempts climb exactly this ladder, and it is deliberately tighter
than the breaker's universal three:

```text
attempt 1: initial gate run on the merge head
           |- bounded trial-local retry (inside the run, bounded by gate config)
attempt 2: ONE re-dispatch (a single fresh gate run)
           |- exhaustion: class-exception (policy-gated, never protected)
           |              or honest re-run (the protected default)
attempt 3: reserved — breaker territory; new attempts here require a human ruling
```

1. **Initial attempt** — the gate's first run on the merge head. Trial-local
   retries (re-running a failed trial inside the same run, within the gate's
   configured bound) are part of this attempt, not new dispatches.
2. **ONE re-dispatch** — exactly one fresh gate run. A second re-dispatch is
   forbidden at this tier; it is an uncounted fourth-plus attempt in breaker
   terms.
3. **Exhaustion** — one of exactly two dispositions:
   - **Class exception** — only where consumer policy explicitly allows it, and
     NEVER on `<protected repos>`. Every exception requires ALL four duties:
     (a) class citation from Section 3; (b) zero-findings confirmation — no
     blocking finding stands against the merge head, so nothing was merged
     around; (c) an evidence artifact capturing the failure; (d) a `<ledger>`
     entry naming class, attempt count, and the authorizing policy.
   - **Honest re-run** — the protected default: the change waits for a green
     gate run. No merge occurs until the gate itself completes green.

Attempt accounting rides the universal circuit breaker's counters
(`methodology/03_circuit_breaker.md` Section 5): the gate-dispatch step is a
repeatable step like any other, the ladder above is its gate-specific shape,
and attempts beyond the ladder are a NEW human ruling (breaker Section 4's
breach procedure and Section 6's escalation) — never a self-serve extra try.
Honest re-runs continue only until the breaker's third attempt; past it, the
step is `BLOCKED` and a human either supplies a corrected approach or
authorizes descoping.

The ladder's shape is the compromise: one re-dispatch absorbs transient
provider faults (F1, F2, F5, F6) without letting an ailing gate stack become a
merge bypass, while sustained pressure flows to the upstream fix instead of to
exception volume (Sections 5 and 7).

## 5. Protected Repositories

`<protected repos>` — declared per consumer; conventionally the
governance-critical and release-authority repositories — admit NO class
exceptions. A flake on a protected repository is never merged around. The only
disposition is re-run patience (Section 4's honest re-run) plus the upstream
fix: repair the gate stack, or shrink and re-shape the packet (an F4 remedy) so
the gate can genuinely complete. The cost of waiting is the accepted price of
never faking green on the repositories every other repository trusts.

## 6. Telemetry Duties

1. **Per-run telemetry artifact.** Every gate run — green, red-with-findings,
   or flake — writes a durable artifact recording: outcome, class (when
   failed), attempt number, model and provider identity, packet size, and
   elapsed time. Convention: one artifact per run under `.agent/evidence/`.
2. **Central `<ledger>` rollup.** Per-run artifacts roll up into a central
   ledger across repositories: per-class counts, per-model counts, flake-rate
   per run, and time-of-day clustering. The ledger — not impression — is the
   measurement instrument for every KPI in Section 8.
3. **Synthetic probes (optional).** A fixed reference `<packet>`, run on a
   schedule against the models in service, measures the base flake rate per
   model and time-of-day. F6 windows are declared against this baseline, never
   ad hoc.

## 7. Evidence Duties

1. **Artifact naming.** Evidence artifacts name the run, class, and attempt —
   for example `<gate>-F4-attempt2-<head>` — so a ledger reader can join
   artifact to ledger entry without narrative.
2. **Post-merge evidence races.** Evidence must be complete and pushed BEFORE
   the lane signals PR-ready: a merge may follow green immediately, and pushes
   after it strand on the branch. An artifact genuinely produced after CI
   completes belongs at a scratch path named in the lane report, carried into
   the mainline by a follow-up micro-lane with byte-exact verification. Every
   committed artifact is text-only; binary payloads never ride a review-gated
   branch.
3. **Canonical-versus-vendored drift.** When the canonical `<review gate>` is
   fixed, ALL vendored copies are resynced in one wave: every consumer pulls
   the fix in a single coordinated re-bootstrap. A vendored copy running a
   known-fixed defect is a defect of its own — drift — tracked in `<ledger>`
   like any other failure. Drift found is an open defect, never an accepted
   state.

## 8. Key Performance Indicators (Targets)

| KPI | Target | Instrument |
|---|---|---|
| Flake-rate per run | Trend to the synthetic-probe base rate; investigate any sustained excess | per-run telemetry rolled into `<ledger>` |
| Exception-merges | Zero — every exception is policy debt to eliminate by fixing its class upstream | `<ledger>` exception entries |
| Mean-time-to-green | Bounded by the ladder (initial plus re-dispatch); sustained growth is provider or stack debt | per-run timestamps rolled into `<ledger>` |

These are targets, not thresholds. The ledger exists so they are measured
facts, never folklore.

## 9. References

- `methodology/03_circuit_breaker.md` — the attempt counters and forbidden
  fourth attempt this ladder embeds; this document's scope begins where a
  failure stops being about the work.
- `standard/convergent_code_review.md` — verdict semantics, lifecycle, and
  replay; this document never redefines them.
- `standard/ci_gates.md` — `AUTOMATED_REVIEW_CLEAN`: an absent, stale, or
  failed automated review means NOT merge-ready.
- `standard/NDS.md` — Section 4 versioning discipline for taxonomy revisions.

Provenance: this doctrine was validated in production fleet operations on
2026-09-30 — a fail-closed review gate, the bounded retry ladder, and the
class taxonomy with ledger and engine diagnoses.
