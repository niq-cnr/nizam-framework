---
id: nizam-tool-driven-state
title: "Tool-Driven State Management (DD-1 + DD-3)"
description: "The query-not-bulk-read discipline for locating governance files via the root capability index, evidence externalisation to .agent/evidence/, and the durable-state artifact families every run maintains."
version: 0.1.0
status: active
authoritative_source: methodology/04_tool_driven_state.md
---

# Tool-Driven State Management (DD-1 + DD-3)

## 1. Overview

This document defines two related design decisions that govern how agents
locate information and how they prove they did something: **DD-1 (query, don't
bulk-read)** and **DD-3 (evidence externalisation)**. Both exist to keep an
agent's working context small, precise, and independently auditable, rather
than bloated with speculative bulk reads or brittle inline proof text.

## 2. DD-1 — Query the Index, Never Bulk-Read

The framework ships a single root capability index, `NIZAM.json`, validated
against `registry/nizam-index.schema.json`. It enumerates every shipped module,
protocol document, schema, and template path the framework contains, along with
enough metadata for an agent to determine which specific file a given task
actually needs.

1. **Route through the index first.** Before reading any governance file, an
   agent MUST consult `NIZAM.json` to identify the minimal set of files its
   current task requires. `NIZAM.json` is deliberately compact so that
   consulting it costs little context relative to reading an entire module
   directory.
2. **Bulk-reading governance directories is prohibited.** An agent MUST NOT
   read every file under `standard/`, `methodology/`, `templates/`, or `tools/`
   "just in case" it becomes relevant. If a task needs the circuit-breaker
   protocol, the agent reads `NIZAM.json`, resolves the path it names for that
   capability, and reads that one file — not the whole `methodology/`
   directory alongside it.
3. **Read only what the task needs, nothing more.** This extends to
   cross-references within a document: when a protocol document (like this
   one) references another by path, an agent follows that reference only if
   its current task actually requires the referenced content, not
   automatically at every mention.

**Rationale:** Context is a scarce, exhaustible resource for any agent, in any
runtime. Every unnecessary file read is a session's worth of context spent on
content the current task will never use. DD-1 makes locating the minimal
necessary file set a first-class, indexed operation rather than something an
agent must rediscover by exploration every session.

*Acceptance anchor:* `NIZAM.json` parses as valid JSON and every capability
path it indexes resolves on disk (registry module, feature 006).

## 3. DD-3 — Evidence Externalisation

Every piece of proof that a step succeeded — captured terminal output, a file
diff, a test run's result — MUST be written to its own file under
`.agent/evidence/`, and referenced **by path** from the corresponding contract,
QA verdict, or phase document. Raw terminal output MUST NEVER be pasted inline
into a YAML or JSON string field.

1. **One evidence file per verification unit.** A contract's evidence
   convention (`schema/contract.schema.json`'s `evidence_convention` field)
   names a deterministic file-naming pattern — for example
   `.agent/evidence/<contract-id>-verify-<NN>.txt` — so that every verification
   command's output lands in its own, individually inspectable file.
2. **Reference by path, not by value.** A phase step, a contract, or a QA
   verdict records the evidence file's path (a string matching
   `^\.agent/evidence/`, per `schema/phase.schema.json`'s `evidence` property),
   never the captured text itself. `schema/phase.schema.json` enforces this
   structurally: its step object declares `additionalProperties: false` over a
   closed property set that has no inline free-text output field (no `proof`,
   `raw_output`, `terminal_output`, `console_output`, `stdout`, or `output`
   key) — a step definition that tries to smuggle raw terminal text into an
   unrecognised key is rejected by the schema, not silently tolerated as an
   unknown extension property.
3. **Why this matters.** Pasting terminal output directly into a YAML or JSON
   string is brittle: multi-line output, embedded quotes, ANSI control codes,
   and inconsistent escaping make such a string both hard to author correctly
   and hard to diff meaningfully across revisions. Externalising evidence to a
   plain text file sidesteps all of that, and gives a human reviewer a file
   they can open directly rather than un-escaping a JSON string by eye.

*Acceptance anchor:* `schema/phase.schema.json` declares an `evidence` path
property (pattern-anchored to `.agent/evidence/`) and forbids any inline
proof-output string field via its closed, `additionalProperties: false`
step schema.

## 4. The Durable-State Artifact Families

Every run maintains its position and history exclusively through the following
file families under `.agent/` (or the phase-document equivalent under
`docs/planning/`). This is the sole channel of inter-agent communication —
subagents MUST NEVER report a material result via chat prose alone
(`standard/AGF.md` Section 5, "the durable state rule").

| Artifact Family | Path Convention | Owns |
|---|---|---|
| **Run state** | `.agent/run_state.json` | Current phase/feature position, overall status, scope-budget counters, circuit-breaker attempt counters, and an append-only history log. `schema/run_state.schema.json`. |
| **Feature list** | `.agent/feature_list.json` | The planned feature DAG, each entry's dependencies and atomic acceptance tests. `schema/feature_list.schema.json`. |
| **Contracts** | `.agent/contracts/NNN.json` | Per-feature scoping: deliverables, non-goals, verification commands, evidence convention, and approval record. `schema/contract.schema.json`. |
| **QA verdicts** | `.agent/qa/NNN.json` | The Evaluator's independently re-derived pass/fail verdict, per-check results, the mandatory adversarial spot-check, and required fixes on failure. `schema/qa_verdict.schema.json`. |
| **Evidence** | `.agent/evidence/*.txt` | Captured terminal output and diff proof, one file per verification unit, referenced by path from the families above (Section 3). |

A role handing off to the next role in the pipeline (Planner to Generator,
Generator to Validator, Validator to Evaluator) MUST have its output present in
the correct family above before considering its turn complete. A result that
exists only as a chat message and was never written to its canonical location
is treated as not having happened by every downstream role.

## 5. References

- `registry/` — `NIZAM.json`'s schema and the index this document's DD-1
  section requires agents to route through (feature 006).
- `schema/phase.schema.json` — the structural enforcement of DD-3's evidence
  externalisation requirement.
- `schema/run_state.schema.json`, `schema/feature_list.schema.json`,
  `schema/contract.schema.json`, `schema/qa_verdict.schema.json` — the
  structural definitions of the artifact families in Section 4.
- `standard/AGF.md` Section 5 — the durable-state ("no oral tradition") rule
  this document's Section 4 elaborates.
