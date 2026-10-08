---
id: nip-0003-live-runtime-sessions
title: "NIP-0003: Live Runtime Sessions"
description: "Proposal to add a language-neutral live-runtime-session protocol (ownership, process generation, serialised operations, attempt continuity, fresh-environment acceptance) with an SBCL reference binding, an optional adapter capability, schema-governed session records, and a reference controller — realized as phases 015 and 016, after phase 014."
version: 0.1.0
status: draft
authoritative_source: docs/nips/NIP-0003-live-runtime-sessions.md
last_audited: "2026-10-08"
tags: [nip, methodology, runtime-session, execution, evaluator-independence, circuit-breaker, adapter, sbcl]
change_log:
  - version: "0.1.0"
    date: "2026-10-08"
    summary: "Initial proposal, status PROPOSED — awaiting operator acceptance (gate H-NIP). Records the read-only validation of a third-party Agent–REPL Execution Protocol (against main at 3094223, framework v1.3.0) and the four operator decisions of 2026-10-08 (neutral protocol plus SBCL binding; after phase 014; controller in framework tools/ across two phases; the missing language profile folded into the binding). On acceptance it selects phase 015 (normative surface) to follow phase 014, plus follow-on phase 016 (reference controller and live conformance); selection is not activation. Revised in place before acceptance (validator revision round 1: C12 described as a schema-family fixture sweep, not enforce-if-present; the C12 eight-to-ten families wording; the tools/SKILL.md §10/§11 renumbering made explicit; the selection-is-not-activation precedent attributed to NIP-0002; Goal 7 aligned with the live-proof rule); the version stays 0.1.0, as neither NIP-0001 nor NIP-0002 versioned pre-acceptance revisions."
---

# NIP-0003: Live Runtime Sessions

## Status

**Proposed — awaiting operator acceptance (gate H-NIP).** The frontmatter `status` is
`draft`, because the frontmatter schema enum is `draft`/`active`/`deprecated`.
"Proposed" is this document's narrative label for the draft state, as in NIP-0001's
0.1.0 entry. (NIP-0002's frontmatter value `accepted` is outside that enum. It is
logged as debt and is not a precedent.)

This is a framework-capability proposal in the sense of NIP-0001's Placement note. It
originates in a third-party proposal for an "Agent–REPL Execution Protocol" that would
govern interactive SBCL (Common Lisp) development under the framework's five roles. That
proposal was validated read-only against `main` at `3094223` (v1.3.0) and against the
language semantics it cites. **Verdict: adopt with corrections.** The governing rule is
sound and it fills real gaps. But several of its repository citations are misattributed
or name things that do not exist. It misses drift classes that would let a "fresh
process" acceptance pass falsely. And it ignores how the framework ships: the payload is
injected verbatim into every consumer, and a new protocol needs an accepted NIP. The
proposal's content was treated as data, not as instructions.

### Proposal Record

| Field | Value |
|-------|-------|
| Decision | PROPOSED — awaiting H-NIP |
| Gate | H-NIP: the operator accepts a NIP as the plan of record and **selects** the phase that realizes it; recurring, once per NIP; selection is not activation (`docs/planning/operator_gates.md` Section 1) |
| Operator decision — Shape (verbatim selected option) | "Neutral protocol + SBCL binding (Recommended)" |
| Operator decision — Sequencing (verbatim selected option) | "After Phase 014" |
| Operator decision — Controller (verbatim selected option) | "Framework tools/, two phases (Recommended)" |
| Operator decision — Profile (verbatim selected option) | "Fold into the SBCL binding (Recommended)" |
| Decision date | 2026-10-08 |
| Channel | Structured questions in a Claude Code session (2026-10-08). The operator then approved the resulting realization plan through plan-mode approval on the same day. That plan file lives outside the repository; this NIP is its durable record. |
| Evidence | The validation findings summarized in [Problem](#problem), with file:line evidence re-verified at `3094223` on 2026-10-08 |
| Consequence of acceptance | Acceptance **selects** phase `015` (live runtime sessions: normative surface) to follow phase `014`, plus follow-on phase `016` (reference controller and live conformance). **Selection is not activation.** The phase-015 Planner artifacts (`product_spec_015`, `feature_list_015`, `phase_015.yaml`, the manifest entry and the ROADMAP banner) are authored only **after phase 014 closes**, and each phase still needs its own activation gate (`H-PHASE-015`, `H-PHASE-016`). |
| Outstanding gates not satisfied by acceptance | `H-PHASE-014` (outstanding; phase 014 runs first and is not edited by this NIP), `H-PHASE-015`, `H-PHASE-016`, `H-FRAMEWORK-RELEASE` (once per release), and `H-CONSUMER-UPGRADE` (per consumer) |

## Problem

The framework governs roles, contracts, gates, evidence and attempts. It says nothing
about a **long-lived runtime process whose state outlives a single command**: an image
that an agent loads code into, evaluates against, redefines in, and hands over. For
image-based languages this is the normal development loop. Without semantics for it, the
framework's existing guarantees have gaps that a live image can quietly fall through.

The validation established these gaps (file:line at `3094223`):

1. **"Own execution context" is never defined.** The Evaluator "re-runs every
   verification command itself, in its own execution context"
   (`methodology/02_adversarial_tdd.md:42-43`). That phrase appears nowhere else in the
   framework and is never defined. (The third-party proposal attributed it to
   `standard/AGF.md`, which is a misattribution.) It says nothing about process, build
   cache or fixtures, so an Evaluator that reuses the Generator's warm image or compiled
   artifacts can claim compliance.
2. **"Attempt" is undefined, and its continuity is unstated.** The circuit breaker sets a
   three-attempt limit (`methodology/03_circuit_breaker.md:54`) and isolates each attempt
   in its own workspace (`:61-73`). It never says what counts as one attempt, and nothing
   says that a new process, a new subagent, a context reset, a new worktree or a renamed
   operation does **not** reset the counter. This gap is language-neutral.
3. **There are no runtime-session semantics.** The framework has no concept of image
   ownership, process generation, an in-flight operation, a timeout that only stops
   waiting, a partial load, or a handover between principals. There are zero
   occurrences of `REPL`, `SBCL` or "runtime session" anywhere in the repository. The
   "SBCL language profile" the proposal assumed does not exist, and `methodology/` is
   flat (`00_` to `09_`) with no `languages/` directory. The framework is deliberately
   language-neutral (`standard/NDS.md:14-15`).
4. **A fresh process is not a fresh build.** A freshly started evaluator process that
   reuses a shared compiled-artifact cache can load code compiled against a definition
   that exists only in a developer's unsaved image. It then passes falsely. A runtime
   that resolves components through user-level or system-level registries can also load
   a same-named component from **another worktree**. Separately, a definition deleted
   from source stays live in an image that never restarted. Fresh-environment acceptance
   has to rule out all three. The proposal's "fresh process" rule rules out none of them.
5. **There is no channel for runtime evidence into review packets.** The proposal said
   review packets accept extra evidence "only through its defined, authenticated
   mechanism". That phrase exists nowhere. The packet schema is closed
   (`schema/review_packet.schema.json:339`, `"additionalProperties": false`). The
   convergent-review standard's evidence rules admit only excerpts of authenticated
   `review_files` (`standard/convergent_code_review.md` §6), and trials are
   observation-only, with no execution and no subagents
   (`templates/convergent-review-prompt.md:22,26`). Runtime evidence therefore has to
   reach review through the Evaluator's QA verdict, never through the packet.
6. **Concurrency lanes are unread.** `schema/work-packet.schema.json` declares
   `concurrency_lane` (`:63-66`) alongside dependencies and a path boundary. But no code
   reads lanes, there is no dispatcher, and no methodology document mentions work
   packets. `run_state` carries a scalar `current_feature` and `active_contract_id`
   (`schema/run_state.schema.json:16-19,84-87`) under a single-writer model
   (`standard/AGF.md:129-136`). Lanes cannot be "reused" for parallel image work until
   they have normative semantics.

Other proposal claims were confirmed and are relied on below:

- the five roles, and the Orchestrator's ownership of coordination fields
  (`standard/AGF.md:28-40,129-136`);
- Mode B before the Evaluator (`standard/AGF.md:67-69`; `methodology/01_execution.md`);
- the evidence shape: invocation, output, `EXIT:<code>`, replayable from the repo root
  (`methodology/04_tool_driven_state.md:121-138`);
- exactly three abstract adapter operations (`tools/interface.md` §4), all marked
  `required: true` in `tools/skill.json` `runtime_requirements` (`:98-111`).

The proposal understated one constraint. `standard/permission_classes.md:25-31` does not
merely omit shell access for the Orchestrator; it **prohibits** bash by default. A
session-lifecycle grant would therefore be the Orchestrator's first execution-adjacent
capability, and it has to be carved out explicitly and narrowly.

## Decision

Add a first-class, **language-neutral live-runtime-session protocol** to the framework.
Pair it with one **named reference binding for SBCL**, following the convergent-review
precedent of a neutral standard plus a named reference implementation
(`standard/convergent_code_review.md:24,62`).

The governing rule is:

```text
A live runtime session is a development aid owned by exactly one principal at a time.
Every operation against it is identified, serialised, and recorded; nothing it produces
is acceptance evidence. Acceptance is re-derived by the Evaluator in a fresh, hermetic
environment built only from committed source, and every attempt is counted across
processes, subagents, context resets, worktrees, and renames.
```

The framework defines the protocol, the generic amendments, the schemas, the optional
adapter capability, validator coverage, a reference controller, and the SBCL binding.
Each consumer defines its own language mix, its own components and its own integration
boundaries. Consumer-specific examples (for example, a workflow service in one language
that calls a retained kernel in another) stay in the consumer's repository.

## Goals

1. Define "runtime session" as distinct from an agent session (`standard/AGF.md` §2), and
   define "own execution context" and "attempt" in the generic methodology.
2. Make image ownership, process generation and one-in-flight serialisation explicit and
   machine-checkable, so a stale or foreign request is rejected **before** it executes.
3. Make failure honest. Condition capture happens before unwinding. A failed or partial
   load never claims the image is consistent. A wait timeout never claims the operation
   stopped.
4. Make acceptance hermetic: a fresh process **and** a fresh build **and** hermetic
   component resolution, built from committed source only.
5. Keep review trials free of execution, and route runtime evidence through the QA
   verdict only.
6. Ship the capability as **optional**, so existing adapters and consumers stay compliant
   and the release is MINOR.
7. Prove every acceptance case (1–13) by its phase-016 live proof in CI before it is
   claimed working. Phase-015 fixtures are additional, schema-level proof where one is
   possible; they never substitute for the live proof.

## Non-Goals

- **Execution and dispatch:**
  - multi-lane `run_state` dispatch (parallel implementation lanes need a future NIP; only
    a `lane_authorization_ref` schema hook ships);
  - resumable debugger restarts, or emitting `debugger_paused`;
  - a hosted or distributed REPL service (the framework is not a runtime);
  - remote sessions, or several principals changing one image at once.
- **Lisp tooling:**
  - SLY/SLIME/Swank integration (editor bridges appear only as examples of capabilities
    that the binding must classify);
  - Quicklisp/qlot tooling and core building.
- **Sandboxing:**
  - sandboxed SBCL acceptance;
  - changes to the review trial adapter or prompt;
  - non-Linux sandboxes.
- **Scope and policy:**
  - consumer-specific examples in any language;
  - a general language-profile mechanism (the one missing profile is folded into the SBCL
    binding);
  - mandatory adoption;
  - any edit to phase 014 or its artifacts.
- **Deferred elsewhere:** putting `tools/test_convergent_review.py` into CI is tracked as
  `NDEBT-041` and is not this NIP's scope.

## Proposed Framework Surface

Feature ids below are the provisional phase-015/016 ids from
[Staged Realization](#staged-realization). Files named below do not exist yet; they are
forward references, and shipped documents will refer to them by feature id until they
land.

### Methodology documents 10 and 11

- **`methodology/10_live_runtime_sessions.md`** (feature 103). The language-neutral
  protocol. It names no language. Its sections cover:
  - the three state classes: source, image and durable records;
  - ownership and leases, including human/agent shared-image handover;
  - process generation, and the serialised operation stream;
  - the status vocabulary, and condition-capture honesty;
  - the development loop, and fresh-environment acceptance;
  - handoff reconstructibility, and context-reset re-entry (read the durable records,
    confirm role, ownership and generation, check for an outstanding operation, compare
    the workspace to the recorded source manifest, and reconstruct if continuity cannot
    be established);
  - external resources;
  - review trials (no session capability);
  - lanes (one implementation lane by default);
  - attempt accounting (pointing to `03` §3.2);
  - durable records.

  It defines "runtime session" explicitly as distinct from an agent session. It states
  that the session record is provenance, not proof that a live heap matches source.
- **`methodology/11_sbcl_runtime_binding.md`** (feature 105). The SBCL reference binding,
  with the missing language profile folded in:
  - **The profile:** toolchain identity, a dependency-lock reference, hermetic build and
    load configuration, and core provenance (acceptance never boots a core saved from a
    development image).
  - **Image hazards:**
    - Observational operations execute project code (`macroexpand`, the printer and
      `print-object`, and inspector actions in editor bridges such as SLIME/SLY).
    - `load` and `compile-file` are non-atomic. Compile-time side effects (`defmacro`,
      `defpackage`, `eval-when`) persist when compilation fails.
    - **Drift classes:** deleted or renamed functions and removed `defmethod`s stay live;
      `defvar` is not re-initialized on reload; redefining a `defstruct` or `defconstant`
      forces a reconstruction; CLOS class redefinition updates instances lazily.
    - Threads and special variables: global values are shared, bindings are thread-local,
      and new threads do not inherit them.
    - Conditions and restarts: restarts have dynamic extent; `handler-case` unwinds before
      its clause runs, so capture uses `handler-bind` or `sb-ext:*invoke-debugger-hook*`.
    - Timeouts and cancellation: `join-thread :timeout` only stops waiting;
      `interrupt-thread`/`terminate-thread` carry unwind-protect hazards.
    - Editor REPLs are not isolation: multiple SLY REPLs share one image.
    - Bounded printing.
    - **A fresh process is not a fresh build:** a private, empty ASDF output-translation
      directory; `CL_SOURCE_REGISTRY` with `:ignore-inherited-configuration`; private
      `HOME`/`XDG`; `--no-sysinit --no-userinit`.
  - **A status mapping** from SBCL outcomes to the neutral vocabulary.

  ASDF forms are marked illustrative until feature 111 verifies them live.

### Generic amendments

These are language-neutral and land with feature 103. They land together with document
10 because they reference each other: C9 and the bare-reference guard would fail on
either half alone.

- **`methodology/03_circuit_breaker.md`** (0.2.0 → 0.3.0): a new §3.2, "What counts as an
  attempt". It covers:
  - continuity across new processes, subagents, context resets, worktrees and renamed
    operations;
  - negative outcomes declared before execution;
  - no relabelling after the fact.
- **`methodology/02_adversarial_tdd.md`** (0.4.0 → 0.5.0): a new §2 item 4 defining "own
  execution context" as a fresh process plus a fresh build cache plus fixtures built from
  committed source.
- **`standard/permission_classes.md`** (0.2.0 → 0.3.0): a new §5 with three classes:
  - `runtime.session.lifecycle`, for the Orchestrator: open, transfer and close, with no
    evaluation;
  - `runtime.session.operate`, for the Generator, on its own sessions only;
  - `runtime.session.accept`, for the Evaluator, in fresh environments only.

  Review trials are denied all three.
- **`standard/convergent_code_review.md`** (1.3.0 → 1.3.1): one §5 sentence saying trials
  never receive a session endpoint.
- **`standard/definition_of_done.md`** (0.1.0 → 0.2.0): one §4 Handoff-Done paragraph. The
  quoted one-liner stays unchanged.
- **Registration in the same change:** `methodology/README.md`; `NIZAM.json` (key documents
  and a capability), because an on-disk `methodology/*.md` must be indexed in the same
  change (`tools/fixtures_self_test.sh:337-345`); and the guide card.

### Schemas

Feature 104 adds two schemas:

- **`schema/runtime_session.schema.json`** and **`schema/runtime_operation.schema.json`.**
  - Draft 2020-12, with `urn:nizam-framework:schema:<file>` ids, and every object closed.
  - They carry **every field phase 016 needs from the start**: `isolation`,
    `toolchain_identity`, `lock_ref`, `core_provenance`, `wait_outcome`, `lease_epoch` and
    `lane_authorization_ref`. `required` is kept minimal. A later change can only loosen
    them; adding a required field later would be MAJOR.
- **Eighteen top-level fixtures** (`_valid_` and `_neg_`), one or more per acceptance case
  where a schema-level proof is possible (see [Acceptance Cases](#acceptance-cases)).
- `schema/README.md`, `tools/README.md` and `NIZAM.json` registration, and the
  `tools/fixtures_self_test.sh` rows.

### Adapter optional capability

Feature 106 changes **`tools/interface.md`** (0.3.0 → 0.4.0): a new §6, "Optional
Capability: Live Runtime Sessions". The current §6 (References) becomes §7.
**§5 (the Adapter Conformance Checklist) stays at exactly 10 items.** That is what keeps
this MINOR: an adapter that does not offer the capability remains fully conformant.

**Operations.** There are seven:

- `open-session`
- `submit-operation`
- `poll-operation`
- `cancel-operation`
- `transfer-session`
- `reattach-session`
- `close-session`

Only `submit-operation` executes anything. Its `kind` is one of `load_source`,
`compile_source`, `evaluate`, `run_tests` or `observe`. (`observe` executes too: the
binding classifies observational operations as code execution.) Session status is read
from the durable records through the existing `read-state` operation; there is no
separate status call.

**Operation statuses:**

- Terminal: `completed`, `condition_signalled`, `cancelled`, `terminated`, `rejected`.
- Non-terminal: `running`, `cancel_requested`, `debugger_paused` (optional, and not
  emitted in v1), `unknown`.
- A wait timeout is recorded as `wait_outcome: stopped_waiting`. It never ends the
  operation.

**Request identity.** Every request carries:

- `operation_id` and `session_id`;
- `expected_generation{counter, nonce}` and `expected_lease_epoch`;
- `requester{principal_kind, role, agent_id}`;
- `contract_id`, `step_key` and `attempt`;
- `kind` and `payload`;
- `context{working_dir, namespace, reader/test config refs}`;
- `limits`.

**Conditional checklist S1–S9.** These items apply only to adapters that claim the
capability:

- **S1:** records validate against the schemas.
- **S2:** a stale generation or lease is rejected before execution.
- **S3:** at most one operation is in flight.
- **S4:** a timeout never reports the operation as stopped.
- **S5:** capture happens before unwinding, and a failed load never claims the image is
  consistent.
- **S6:** review trials are rejected.
- **S7:** lifecycle operations never evaluate code.
- **S8:** session results are never acceptance evidence.
- **S9:** attempt counters survive a new generation.

`tools/skill.json` gains `runtime_requirements.live_runtime_session` with
`"required": false`, plus a capability entry. `tools/SKILL.md` gains a new §10 (Live
Runtime Sessions routing); its current §10 (References) becomes §11, paralleling the
`tools/interface.md` §6 → §7 renumbering. Once the capability exists, document 10's
`enforcement` flips to `partially-enforced`.

### Validator

**Extend C12; do not add a check number.**

- C12 gains the two families (in `FAMILIES` and the schema paths).
- Its router branches for them go **before** the `contract_id` → C11 route, because
  operation records carry a `contract_id`.
- It gains a relational check for generation mismatch, which JSON Schema cannot express.
- The existing C12 "eight families" prose (the `tools/validate.sh --help` C12 paragraph
  and the `tools/README.md` C12 row) is updated to ten.

The validator keeps reporting 16 checks. **C17 stays free**; it is earmarked for evidence
shape. Feature 104's acceptance includes running `--target` on a stale-generation
negative fixture, which must exit 1 with `[C12] FAIL`.

### Reference tooling (phase 016)

- **`tools/runtime_session.py`** (feature 108). One detached supervisor per session,
  Python standard library only, in the style of `tools/validate_evidence_freshness.py`
  (an exit-code table, custom error classes and an argparse override). It provides:
  - JSON Lines on the child's stdin and fd 3;
  - a generation made of a counter plus a `secrets.token_hex` nonce, echoed by the child;
  - an exclusive `supervisor.lock` and lease epochs. Document 10 states that this is
    workflow coordination, **not** an authentication boundary;
  - one operation in flight. A submit while busy is `rejected` (`session_busy`); there is
    no queue;
  - atomic record writes with `os.replace`;
  - a read-only attempt guard over `run_state.circuit_breaker`.

  It comes with a language-neutral stub runtime
  (`tools/fixtures/runtime_session/stub_runtime.py`) and `tools/test_runtime_session.py`.
- **Operation semantics and CI** (feature 109):
  - a new `compliance.yml` job, `live_session_conformance`, reusing the already-pinned
    action SHAs (so C14 stays satisfied), installing `sbcl` with apt, setting the userns
    sysctl in a guarded step, and running with `--require-sbcl --require-isolation`;
  - a fixture-subdirectory claim map in `tools/fixtures_self_test.sh`, which also remedies
    `NDEBT-042`;
  - `standard/definition_of_done.md` §8 and §11 saying "four jobs";
  - a pull-request template checkbox.
- **`tools/sbcl_session_loop.lisp`** (feature 110). Built-ins only, no Quicklisp:
  - `handler-bind` captures the backtrace and `compute-restarts` before aborting;
  - printing is bounded;
  - cancel uses `interrupt-thread` and waits for confirmation that the unwind happened.
    Otherwise it kills the process group and records `terminated`, and the generation
    ends.
- **The fresh-environment `accept` runner** (feature 111):
  - `git archive` into a private root;
  - `sbcl --non-interactive --no-sysinit --no-userinit`;
  - private `CL_SOURCE_REGISTRY` and `ASDF_OUTPUT_TRANSLATIONS`, both with
    `:ignore-inherited-configuration`, and private `HOME`/`XDG`;
  - the toolchain, lock and core provenance recorded;
  - evidence written in the `04` §5 shape.
- **Case 8's isolation layer** reuses `tools/isolated_trial_adapter.py` unchanged. Skips
  are always explicit, never a silent pass.
- **Docs synced to the implementation** (feature 112), plus a resolver for `.py`/`.lisp`
  path tokens. C9's path regex currently extracts only `md|json|sh|html|yml`
  (`tools/validate.sh` C9 help text), so references to the new `.py`/`.lisp` files would
  go unchecked.

### Capability routing

Add capability entries to `NIZAM.json` and `tools/skill.json`, and a routing pointer in
`tools/SKILL.md`. The single runtime-agnostic skill remains the router. No
language-specific or runtime-specific skill is introduced.

## Artifact Locations

Consumer convention, mirroring NIP-0001's `.agent/<kind>/<id>/` layout:

```text
.agent/sessions/<session-id>/session.json            # runtime_session record (committed)
.agent/sessions/<session-id>/operations/<op-id>.json # runtime_operation records
.agent/sessions/<session-id>/handoff.md              # handoff summary (committed)
.agent/evidence/<execution-id>/                      # fresh-environment acceptance evidence (04 §5 shape)
.agent/qa/<NNN>.json                                 # the only route for runtime evidence into review
```

The session record and the handoff summary are committed. Retention for raw operation
logs is settled in the feature-104 contract, to avoid committing noisy logs. Session
records are **diagnostic provenance**. A session experiment becomes acceptance evidence
only when its setup and behaviour are captured in files and independently re-run by the
Evaluator in a fresh environment.

## Status Vocabulary

**Operation status.** An operation has exactly one status at a time.

| Status | Class | Meaning |
|--------|-------|---------|
| `running` | non-terminal | Accepted and executing in the current generation. |
| `cancel_requested` | non-terminal | Cancellation asked for; the unwind is not yet confirmed. |
| `debugger_paused` | non-terminal | Reserved and optional; **not emitted in v1** (resumable restarts are a non-goal). |
| `unknown` | non-terminal | The supervisor cannot establish the outcome (for example after a disconnect). No conflicting operation may start until it resolves. |
| `completed` | terminal | Finished without a signalled condition. |
| `condition_signalled` | terminal | A condition was captured before unwinding. A failed `load_source`/`compile_source` never claims the image is consistent. |
| `cancelled` | terminal | Cancellation **confirmed** by the runtime. Never recorded without confirmation. |
| `terminated` | terminal | The process was killed. **The generation ends**; later requests carrying it are rejected. |
| `rejected` | terminal | Refused and recorded, and **never executed**: for example a stale generation, a stale lease, a foreign owner, a busy session, or a review-trial requester. |

**Wait outcome.** `wait_outcome: stopped_waiting` records that the requester stopped
waiting. It is never a status, and it never implies that the operation stopped.

Session lifecycle states and the exact rejection-reason codes are settled in the
feature-104 contract, within the closed schemas.

## Acceptance Cases

Cases 1–10 come from the third-party proposal. Cases 11–13 were added by the
validation. "015 fixture" is the schema-level proof (a C12 positive or negative
fixture) where one is possible. "016 live proof" names which runtime proves the case in
`python3 tools/test_runtime_session.py --require-sbcl --require-isolation`, which runs in
the new CI job.

| # | Case | Required outcome | 015 schema-level fixture | 016 live proof |
|---|------|------------------|--------------------------|----------------|
| 1 | A second agent attempts to mutate another agent's image | Rejected by ownership enforcement | Valid: an operation recorded `rejected` (foreign requester). Negative: a foreign-requester operation recorded as executed. | Stub |
| 2 | Two agents redefine the same symbol in their separate images | Results remain isolated | None. Isolation is a runtime property; the schema only distinguishes sessions and generations. | Stub |
| 3 | An operation uses a stale process generation | Rejected before execution | Valid: `rejected` with a mismatched `expected_generation`. Negative: `runtime_operation_neg_stale_generation_executed.json` (C12 relational check, `[C12] FAIL`). | Stub |
| 4 | A load fails after earlier forms have executed | Reported as incomplete; the image is not claimed consistent | Valid: a `load_source` operation in `condition_signalled` with the image marked not consistent. Negative: a failed load that claims consistency. | SBCL |
| 5 | A request times out while execution continues | No conflicting operation starts until the outcome is resolved | Valid: `running` with `wait_outcome: stopped_waiting`, and a concurrent submit `rejected` as busy. Negative: a timeout recorded as `cancelled`. | Stub and SBCL |
| 6 | The agent disconnects and reconnects | Pending-operation and ownership state are recovered accurately | Valid: a session record after `reattach-session` that keeps its generation and outstanding operation reference. | Stub and SBCL |
| 7 | A change works only because of an unsaved REPL definition | Fresh-process acceptance rejects the candidate | Negative: a session operation result offered as acceptance evidence (S8). | SBCL |
| 8 | A convergent-review trial requests REPL access | The execution capability is unavailable | Valid: a trial-requester operation recorded `rejected`. Negative: the same operation recorded as executed. | Stub (policy); CI (the mechanism layer, through `tools/isolated_trial_adapter.py`) |
| 9 | A new process is started during a failing governed step | The existing attempt count is preserved | Valid: a new-generation operation carrying the same `contract_id`/`step_key`/`attempt`. The counter guard itself is live-only, because it reads `run_state`. | Stub |
| 10 | A handoff is replayed in a fresh environment | Source, fixtures and commands are sufficient to reproduce the result | Valid: a session record whose handoff references a source manifest and replayable commands in the `04` §5 shape. | Stub and SBCL |
| 11 | A stale fasl in the shared cache, compiled against an unsaved macro, would make a fresh process pass | Fresh-build acceptance rejects the candidate | Valid: an accept record whose `isolation` declares a private, empty output-translation directory and ignored inherited configuration. Negative: an accept record that uses the inherited cache. | SBCL |
| 12 | A definition deleted from source is still live in the development image, and the image's tests pass | Fresh acceptance rejects the candidate | None beyond case 7. Image drift is a live property. | SBCL |
| 13 | A human and an agent hand over one shared image | Ownership transfers explicitly; the old holder's requests are rejected | Valid: a `transfer-session` record that increments `lease_epoch` and changes `principal_kind`. Negative: an operation with the pre-transfer lease epoch recorded as executed. | Stub |

In summary:

- The stub runtime proves cases 1, 2, 3, 5, 6, 8 (policy), 9, 10 and 13.
- SBCL proves cases 4, 5, 6, 7, 10, 11 and 12.
- CI proves case 8's mechanism layer.

No case is claimed working until its live proof passes in CI.

## Staged Realization

The NIP is realized in two phases, both **after phase 014 closes**. Feature ids are
provisional: they are confirmed when phase 015 is planned, in case phase 014 consumes
more ids. Each feature follows the standard two-loop lifecycle.

**Phase 015 — "live runtime sessions: normative surface."** One lane, 103 → 104 → 105 →
106 → 107. The design-time `original_estimate_lines` is 5,400 (ceiling 7,020, applying
the measured ×2.3 process weight). Planning takes place after 014 closes, and activation
is at `H-PHASE-015`.

| ID | Feature | Naive lines |
|----|---------|-------------|
| 103 | Document 10 plus the generic amendments to `02`, `03`, `permission_classes`, `convergent_code_review` and `definition_of_done`, with registration | 600 |
| 104 | Session and operation schemas, 18 fixtures, and the C12 extension | 850 |
| 105 | Document 11, the SBCL reference binding with the language profile folded in | 420 |
| 106 | The optional adapter capability (`interface.md` §6, `skill.json`, `SKILL.md`), capability routing and cross-links | 220 |
| 107 | Release preparation for the **next MINOR (expected v1.4.0)**, and phase close | 240 |

The phase-015 release **also rolls up phase 014's unreleased changes**, because phase 014
prepares no release of its own.

**Phase 016 — "reference controller and live conformance."** Preconditions for
`H-PHASE-016`:

- SBCL is available wherever the Evaluator runs (apt `sbcl` on the workstation, or
  Docker). It is not currently installed on the operator's workstation.
- A decision on whether case 8's sandbox layer is proven locally (which needs the userns
  sysctl) or in CI only.
- A re-estimate at planning time. The design-time weighted figure is about 10,500 lines;
  the phase is split if that stays above precedent.

| ID | Feature | Naive lines |
|----|---------|-------------|
| 108 | Controller core and the language-neutral stub runtime | 1,440 |
| 109 | Operation semantics, the `live_session_conformance` CI job, the fixture-subdirectory guard, and the Merge-Done "four jobs" change | 890 |
| 110 | The SBCL request loop (built-ins only) | 820 |
| 111 | The fresh-environment `accept` runner | 1,025 |
| 112 | Docs synced to the implementation, plus the `.py`/`.lisp` path-token resolver for C9 | 170 |
| 113 | Release preparation for the **next MINOR (expected v1.5.0)**, and phase close | 240 |

Release numbers are "next MINOR". The expected values hold only if no other release is
cut between phases.

## Compatibility

The change is **MINOR** in each phase. Surface by surface
(`methodology/06_release_train.md` §3.2, with §3.4 "when in doubt, round up"):

| Surface | Change | Classification and reason |
|---------|--------|---------------------------|
| `methodology/10_`, `methodology/11_` | New protocol documents | MINOR. A new protocol document is the named §3.2 example. |
| `03` §3.2, `02` §2 item 4 | New definitions of "attempt" and "own execution context" | They clarify existing rules, but they change how agents count and where they re-run, so they are rounded up to MINOR (§3.4). |
| `standard/permission_classes.md` §5 | New, narrowly scoped permission classes | MINOR. Additive; nothing previously permitted is revoked. |
| `standard/convergent_code_review.md` §5 | One sentence: trials never get a session endpoint | PATCH-level (1.3.1). It restates the existing no-execution rule; it ships within the MINOR. |
| `standard/definition_of_done.md` §4, §8, §11 | A Handoff-Done paragraph; "four jobs" | MINOR. Additive. The fourth job runs in the framework's own CI; `.github/` is not injected into consumers. |
| New schemas | `runtime_session`, `runtime_operation` | MINOR. New files; nothing that validated before is invalidated. They carry every phase-016 field from the start, so 016 never needs a MAJOR tightening. |
| C12 | Two new families and a relational check | MINOR. Consumers see no new failures: C12 is a schema-family fixture sweep that validates only the framework's own `tools/fixtures/` (each family needs at least one positive and one negative fixture), and it never runs in `--payload` mode. A consumer's `.agent/sessions/` records are swept by no check; only an explicit `--target` routes one to C12. The router branches go before the `contract_id` route, so existing contracts still route to C11. |
| `tools/interface.md` | New §6 optional capability; References becomes §7 | MINOR. **§5 stays at 10 items**, so every existing adapter remains conformant. Adding a required §5 item would be MAJOR. |
| `tools/skill.json` | `live_runtime_session` with `"required": false`, and a capability entry | MINOR. An optional requirement and an additive entry. |
| `NIZAM.json` | Key documents and capability entries | MINOR. Additive. |
| Phase-016 `tools/` files | `.py`, `.lisp`, the stub runtime and fixtures | MINOR. New files ship to consumers because `tools/` is injected (`bootstrap.sh:71-78`). This is noted in the CHANGELOG, following the convergent-review fixtures precedent. |

## Dogfood Requirement

Before each release:

1. Run every existing validator. The default mode must report `SUMMARY: 16 passed, 0
   failed`, with payload mode green as well. `tools/fixtures_self_test.sh` must account
   for every fixture, including the new ones, and `tools/e2e_bootstrap_test.sh` must exit 0.
2. Phase 015: every C12 positive fixture passes and every negative fixture fails with
   the specific `[C12] FAIL`. A Python check confirms that `tools/interface.md` §5 still
   has exactly 10 items.
3. Phase 016: the framework's own CI runs the reference controller against the stub
   runtime **and** real SBCL, proving acceptance cases 1–13. Skips are explicit and fail
   the job unless allowed.
4. The phase-015/016 features are themselves delivered under the new attempt accounting
   once feature 103 lands.
5. Record all friction as debt, and update the ROADMAP from the dogfood evidence.
6. Obtain human release approval (`H-FRAMEWORK-RELEASE`). The pipeline never self-tags.

## Adoption Requirement

- Consumers adopt only a **released, immutable tag**, under a recorded
  `H-CONSUMER-UPGRADE` decision.
- The capability is **optional**. A consumer with no live-runtime work, or an adapter
  that does not offer sessions, remains fully compliant.
- A consumer that adopts it supplies its own language mix, components, integration
  boundaries and consumer-specific examples in its own repository. The framework ships
  only the neutral protocol, the SBCL reference binding, the schemas and the reference
  tooling.
- Parallel implementation lanes are **not** enabled by adoption. They need a future NIP.

## Risks

- Release numbering shifts if a release is cut between phases.
- Rebase churn on `NIZAM.json`, `tools/skill.json`, the ROADMAP and the guide, from phase
  014's changes.
- The bare-reference guard trips on forward references to files not yet landed.
- A later schema change adds a required field, which would be MAJOR.
- No SBCL is available locally.
- A cancellation hazard leads to a stop being reported that did not happen.
- Distribution SBCL configuration leaks into acceptance.
- Consumers receive the new `.lisp` and stub files, because `tools/` ships.
- The Orchestrator's first execution-adjacent grant widens into evaluation.

## Mitigations

- The NIP names releases as "next MINOR", not as fixed numbers.
- Version numbers are set when phase 015 is planned, after phase 014 closes.
- Shipped documents refer to features by id until they land; feature 106 adds the
  cross-links.
- The phase-015 schemas carry every field phase 016 needs; later changes only loosen them.
- SBCL is installed before `H-PHASE-016` (apt `sbcl`, matching the CI runner), or Docker
  is used.
- `cancelled` is never recorded without confirmation; otherwise the controller escalates
  to `terminated` and the generation ends.
- Acceptance uses `--no-sysinit --no-userinit` and ignores inherited configuration;
  cases 11 and 12 prove it.
- The CHANGELOG notes the new shipped files (the convergent-review fixtures precedent).
- `runtime.session.lifecycle` excludes evaluation, and S7 makes that checkable.

## Acceptance Criteria

For accepting **this NIP**:

- **Pending.** The operator accepts this NIP at gate **H-NIP**, selecting phase 015 (to
  follow phase 014) and follow-on phase 016. On acceptance:
  - this document moves to `1.0.0`, frontmatter `active`, with the Status section updated
    to Accepted;
  - the `H-NIP` row in `docs/planning/operator_gates.md` records "EXERCISED AGAIN";
  - the ROADMAP's queued-candidate section rolls to "selected".
- **Pending.** Phase 014 closes. The phase-015 Planner artifacts are authored only then,
  and phase 015 is activated at `H-PHASE-015`.

For **realizing** it (phases 015/016):

- Documents 10 and 11 are indexed and path-valid, and the generic amendments have
  landed.
- The two schemas validate their positive and negative fixtures under C12, and C17 stays
  free.
- `tools/interface.md` §5 still has exactly 10 items.
- The reference controller proves acceptance cases 1–13 in CI against the stub runtime
  and SBCL.
- All existing compliance and bootstrap tests remain green.
- Both releases are tagged and documented, and consumers adopt only released tags.

## Relationship to NIP-0001, NIP-0002 and Phase 014 Feature 101

- **NIP-0001 (Ecosystem Engineering Cycle).** NIP-0003 is not an ecosystem stage. It is
  repository-level execution methodology and belongs in `methodology/`, not
  `ecosystem/`. It follows NIP-0001's shape: artifact locations under
  `.agent/<kind>/<id>/`; new schemas proven by positive and negative fixtures under C12's
  schema-family fixture validation (NIP-0001's initial schemas were C12's first families,
  features 037–039); operator gates; and dogfood before release.
- **NIP-0002 (the 0–n Project Spectrum).** Runtime sessions are scoped to one worktree of
  one repository, so they apply unchanged at every project count. They never span
  repositories, and they make no change to the membership registry. NIP-0002's Staged
  Realization is the model for the two-phase plan above.
- **Phase 014, feature 101 (the first real simplification review).** Phase 014 is not
  edited by this NIP; its contract excludes schema and workflow changes
  (`.agent/product_spec_014.md:82-83`). Feature 101 reviews the *accumulated* framework
  surface and records candidate scope for the next planning cycle. NIP-0003's surface has
  not landed by then, so 101 cannot review it. But 101's findings are a mandatory input to
  phase-015 planning: any consolidation candidate touching a surface this NIP amends
  (`02`, `03`, `permission_classes`, `interface.md`, C12) is reconciled when phase 015 is
  planned. Any decision taken under `H-CONSOLIDATION` takes precedence over this NIP's
  provisional design. The newly logged `NDEBT-041`..`NDEBT-044` are candidate inputs to
  101, like the other open rows.

## References

- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`: the NIP model.
- `docs/nips/NIP-0002-zero-to-n-project-spectrum.md`: the Staged Realization model, and
  the selection-is-not-activation precedent (its Status section), as also recorded in the
  `H-NIP` row of `docs/planning/operator_gates.md`.
- `methodology/02_adversarial_tdd.md` §2: Evaluator independence, including the
  undefined "own execution context".
- `methodology/03_circuit_breaker.md` §3, §3.1: the attempt limit and attempt isolation.
- `methodology/04_tool_driven_state.md` §5: the evidence shape.
- `methodology/06_release_train.md` §3.2, §3.4: MINOR classification and rounding up.
- `standard/AGF.md` §2, §5: the roles and single-writer coordination fields.
- `standard/permission_classes.md` §2: the role permission defaults.
- `standard/convergent_code_review.md` §1, §5, §6: the neutral-standard-plus-reference
  precedent, the three trials and authenticated evidence.
- `templates/convergent-review-prompt.md`: observation-only trials.
- `schema/review_packet.schema.json`, `schema/work-packet.schema.json` and
  `schema/run_state.schema.json`.
- `tools/interface.md` §4, §5 and `tools/skill.json` `runtime_requirements`.
- `tools/linux_trial_sandbox.sh` and `tools/isolated_trial_adapter.py`: the Linux trial
  sandbox reference, reused unchanged for case 8.
- `docs/planning/operator_gates.md`: H-NIP, H-PHASE-NNN, H-FRAMEWORK-RELEASE and
  H-CONSUMER-UPGRADE.
- `docs/planning/DEBT.md`: `NDEBT-041`..`NDEBT-044`, logged with this proposal.
- External semantics relied on by the SBCL binding: the CLHS (`macroexpand`,
  `print-object`, `load`, `compile-file`, `restart-case`/`restart-bind`, `handler-bind`,
  and §4.3.6 on class redefinition), the SBCL manual (threads, special variables,
  `join-thread`, `interrupt-thread`, `*invoke-debugger-hook*`, and the `--no-sysinit`/
  `--no-userinit` options), and the ASDF manual (source-registry and output-translations
  configuration).
