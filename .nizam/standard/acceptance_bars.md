---
id: nizam-acceptance-bars
title: "Comparator Acceptance Bars"
description: "Defines comparator-based acceptance for quality-bearing deliverables: bar requirements (named, fetchable, comparable), the fresh-context blind critic loop, cost tiering, the bar library's pin-and-reverify discipline, and the circuit-breaker interface."
version: "0.3.0"
status: active
enforcement: consumer-aspirational
authoritative_source: standard/acceptance_bars.md
change_log:
  - version: "0.3.0"
    date: "2026-10-18"
    summary: "Align comparator circuit-breaker interface and failure-mode table with methodology/03_circuit_breaker.md work-specific diagnostic stopping and hard-stop rules (V5)."
  - version: "0.2.0"
    date: "2026-10-18"
    summary: "Align Section 3 comparator verdict format with the single authoritative AGF verdict schema (final_verdict, issues, missing_acceptance_coverage, unsupported_claims, optional advisory_minor and comparator metadata)."
  - version: "0.1.2"
    date: "2026-10-18"
    summary: "Subordinate the comparator critic loop to methodology/03_circuit_breaker.md's 3-attempt hard operational cap: a round count never grants a pass, and a loop that has not achieved a blind win by attempt 3 halts and escalates rather than making a forbidden fourth autonomous attempt."
  - version: "0.1.1"
    date: "2026-10-13"
    summary: "Adopted into the payload (PR #92, merge commit 365ae2f): status draft -> active, proposal banner replaced with the adoption note, and the Definition of Done now cites this standard from its Gate-Done and Feature-Done layers."
  - version: "0.1.0"
    date: "2026-10-13"
    summary: "Initial proposal: comparator acceptance bars distilled from operational practice — stage and destroy blind critic loops, cost tiering, measurable halves, the bar library, and the breaker interface. Staged for framework review; frontmatter/status finalized per NDS at merge."
---

# Comparator Acceptance Bars

> **ADOPTED.** Merged into the payload by PR #92 (merge commit `365ae2f`) and activated
> at adoption — status `draft` -> `active`, recorded in the change log below. The
> Definition of Done (`standard/definition_of_done.md`) cites this standard at its
> Gate-Done and Feature-Done layers. Enforcement posture: **consumer-aspirational**
> (mirroring `standard/failure_modes.md` and `methodology/05_eval_and_trace.md`);
> no validator check is claimed in this version.

## 1. Purpose and Scope

Acceptance criteria state what must be true. They do not define how **good** is judged
when a deliverable has a quality dimension — fidelity, legibility, traceability, taste.
This standard defines **comparator-based acceptance**: a named, fetchable, comparable
bar; a separate fresh-context critic judging a blind comparison; and a loop whose only
exit is winning that comparison.

Applies to **quality-bearing deliverables**: user interfaces, code and tooling,
documentation, evidence/verification packs, design artifacts, and similar.

Explicitly out of scope: **correctness-only work** — deterministic refactors,
dependency bumps, pins, conflict settlement, infrastructure reconciliation. For those,
the specification itself is the bar; bolting a taste loop onto deterministic work is a
misapplication, not extra rigor.

Complements, never replaces: `standard/AGF.md` (roles, dual gate, JSON verdicts),
`standard/convergent_code_review.md` (merge-level review), `methodology/05_eval_and_trace.md`
and `methodology/07_eval_gated_promotion.md` (model/prompt baselines),
`standard/definition_of_done.md` (completion layers). Adds the deliverable-level
comparator layer between feature acceptance criteria and the merge gate.

## 2. The Bar

A bar MUST pass three tests:

- **Named** — a specific artifact or exemplar, never a category. "Stripe's pricing page"
  passes; "award-winning SaaS sites" fails.
- **Fetchable** — the critic can actually obtain it: screenshot the live page, run the
  binary, open the repository, read the published piece. An unfetchable bar makes the
  critic hallucinate the comparison.
- **Comparable** — both artifacts can sit side by side and a judge can pick one. If the
  A/B cannot be imagined, it is not a bar.

Additional requirements:

- **Measurable half.** Where a number exists (latency, counts, coverage, pass rate,
  steps-to-observation), name it alongside the reference. Taste plus a number beats
  taste alone.
- **Hardest-reachable rule.** Prefer the hardest bar the worker can genuinely reach; a
  bar that is too easy exits the loop at round one.
- **Pin discipline.** Bars are pinned (repository + commit SHA; live URL + capture date;
  publication + edition) and **re-verified at use**. A moved or broken comparator is a
  provenance-class event: record the defect and substitute with evidence — never tolerate
  a silently softening floor.

## 3. The Critic Loop

- **Role mapping (no new roles).** Builder = Generator; critic = Validator/Evaluator
  (`standard/AGF.md` §2). The Orchestrator sequences the loop and parses verdicts.
- **Fresh context.** The critic sees only the goal, the bar, and the output — labels
  stripped where meaningful. Never the builder's reasoning, effort, or history.
- **Binary job.** "Which is better, A or B" — then name the single biggest remaining
  gap. No numeric scores (they drift upward); praise is not useful.
- **Passing exit = blind win within the circuit-breaker policy, never a round count.**
  Completing N rounds never converts a losing comparison into a pass. The loop exits with
  a pass when the critic picks ours blind within the circuit-breaker policy, or halts when
  the circuit breaker trips or a human stops the run.
- **Circuit-breaker interface (subordinate to `methodology/03_circuit_breaker.md`).**
  Every autonomous comparator loop is subordinate to `methodology/03_circuit_breaker.md`:
  attempt counters drive escalating diagnostic posture or bounded decomposition when
  invariants hold, and if a blind win is not achieved by attempt 3 on the same unresolved
  gap without a viable bounded decomposition, the agent MUST halt and escalate per
  `methodology/03_circuit_breaker.md` Section 4.
- **Verdict format.** Recorded as machine-parseable JSON verdict blocks using the single
  authoritative AGF verdict schema (`standard/AGF.md` §4); prose may accompany, the block
  is the verdict. When the blind comparison fails, the gap is recorded in `issues` and
  `final_verdict.approved` is `false`; comparator metadata is carried under `comparator`:

  ```json
  {
    "final_verdict": {"approved": true},
    "issues": [],
    "missing_acceptance_coverage": [],
    "unsupported_claims": [],
    "advisory_minor": [],
    "comparator": {
      "bar": "<bar id>",
      "blind_win": true,
      "halves": {"<name>": "..."},
      "biggest_gap": "<one line>"
    }
  }
  ```

## 4. Cost Tiering

Critics consume builder-grade resources; tier before dispatch and record the tier.

| Tier | Applies to | Rigor |
|---|---|---|
| **A — full bar loop** | Quality-critical deliverables (user-facing interfaces, flagship code, public documentation, evidence packs) | Named bar + builder/critic loops + measurable halves + external cross-check where one exists. Run few at a time. |
| **B — critic-lite** | Standard code and evidence work | Bar = named in-repo exemplar or the specification; critic role = the standing gates plus ONE fresh-context falsification pass at acceptance. |
| **C — spec-only** | Deterministic work (§1 out-of-scope list) | No taste loop; acceptance = gates and digests against the specification. |

## 5. The Bar Library

- Bars are shared infrastructure: one **bar-of-record** per deliverable family —
  comparator(s), measurable halves, review date — reused across all work in that family.
- Stored per the evidence-by-path convention of `methodology/04_tool_driven_state.md`;
  drift and re-verification reuse `standard/GIP.md`'s pin semantics (a moved comparator
  is treated like a moved tag: detect, record, re-establish — never trust).
- **Regression leg is mandatory**: the exemplar set doubles as a regression control —
  new work MUST NOT weaken the comparators it must beat.

## 6. Measurable-Halves Families (reference — extend per family)

| Family | Halves |
|---|---|
| Code / tooling | All gates green · zero new failures · named counts (suite size, coverage floor, p95, benchmark score) |
| Evidence / verification | Every claim pinned to a raw transcript line · zero unfalsifiable claims |
| UI / journeys | Dead-end controls = 0 · real data (no silent mock fallback) · honest empty/error/denied states · bounded steps-to-observation · keyboard accessibility |
| Documentation | Format/length constraints · a named comparable piece |
| Ops / artifacts | Pre/post state proofs · digests · smoke probes |

## 7. Failure-Mode Guards

Extends the `standard/failure_modes.md` taxonomy with deliverable-quality blindness
(the comparator analogue of **Eval blindness**):

| Failure | Detection | Response |
|---|---|---|
| Soft/vague bar | The naming test fails | Reject the bar; offer 2–3 candidates, let the accountable human pick |
| Builder self-judging | Critic shares builder context | Enforce freshness; re-run the verdict |
| Score drift | Numeric scoring appears | Binary A/B only |
| Round-count pass | Exhausting rounds is treated as a passing exit | Require a blind win under `methodology/03_circuit_breaker.md`, or halt and escalate when attempt 3 on the same unresolved gap fails without a viable bounded decomposition |
| Over-specification | The brief exceeds bar + loop in length | Minimal wins — cut to bar, loop, halves |
| Broken/stale comparator | Pin re-verification fails at use | Record as defect; substitute with evidence |

## 8. Roles, Authority, and Disclosure

No new roles: this standard binds the existing Orchestrator/Generator/Validator/Evaluator
model. Bar SELECTION for flagship deliverables MAY be a recorded human decision (offer
2–3 candidate bars; wait for the pick). Where a deployment collapses roles, the collapse
MUST be disclosed in durable state, per `AGF.md` §2.

## 9. Adoption Checklist (consumer runtime)

1. Classify the work: quality-bearing vs deterministic.
2. Declare the tier at dispatch.
3. Name the bar (or offer candidates and record the pick).
4. Record the bar-of-record: comparator pin, halves, review date.
5. Run the builder/critic loop with a fresh-context critic.
6. Record JSON verdicts + the regression leg in the evidence bundle.
7. Re-verify comparators at use; substitute with evidence when broken.

## 10. Non-Goals

- No pixel/parity demands where a floor suffices; the external leg is a sanity floor,
  not a summit.
- No replacement of convergent code review (merge level) or eval-gated promotion
  (model level).
- No mandatory external comparator: a pinned internal exemplar set is a valid bar; its
  self-referential ceiling is the known limitation, mitigated by an external floor where
  one is fetchable.

## 11. Enforcement

Consumer-aspirational: the framework ships the standard; each consuming repository
enforces it in its own runtime and CI. No `tools/validate.sh` check is claimed by this
version. A future optional check (bar-of-record presence for tier-A tasks) is a
candidate, explicitly out of scope here.

## 12. Cross-References (cite, not restate)

`standard/AGF.md` §2–§4 · `methodology/03_circuit_breaker.md` ·
`methodology/04_tool_driven_state.md` · `methodology/05_eval_and_trace.md` ·
`methodology/07_eval_gated_promotion.md` · `standard/failure_modes.md` ·
`standard/definition_of_done.md` · `standard/GIP.md` ·
`standard/convergent_code_review.md` · `schema/frontmatter.schema.json`.
