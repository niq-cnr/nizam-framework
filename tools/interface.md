---
id: nizam-tools-interface
title: "Runtime-Adapter Interface"
description: "The adapter contract any agent runtime implements to discover, load, and act on the single unified Nizam skill payload (DD-4): discovery, loading, the three abstract operations, and the conformance checklist an integrator ticks through."
version: 0.2.0
status: active
authoritative_source: tools/interface.md
change_log:
  - version: "0.2.0"
    date: "2026-07-08"
    summary: "H4: reordered Section 2 Discovery so bootstrapped-consumer .nizam/tools/skill.json discovery runs first, matching bootstrap.sh's .nizam default install layout, with the repository-root tools/skill.json path retained as an explicitly labeled framework-checkout fallback."
---

# Runtime-Adapter Interface

## 1. Overview

This document specifies how an agent runtime — any host environment capable of
reading files, executing commands, and holding instructions in its working
context — discovers and loads the framework's one unified skill payload, and
how that runtime's own native tool primitives satisfy the three abstract
operations the payload's protocols assume. It describes the adapter contract
only. It ships no runtime-specific adapter implementation and no per-runtime
fork directory (DD-4): there is exactly one skill payload, `tools/SKILL.md`,
and every runtime loads that same file.

## 2. Discovery

An agent runtime locates the skill payload as follows:

1. **Bootstrapped-consumer discovery.** In a repository that has bootstrapped
   the Nizam framework via `bootstrap.sh` (`standard/GIP.md` Section 2.1), the
   runtime FIRST looks for `tools/skill.json` under the injected governance
   target directory — by default `.nizam/tools/skill.json` (`bootstrap.sh`'s
   `NIZAM_TARGET_DIR`, which defaults to `.nizam`). If present, this is the
   authoritative manifest for that repository's governed work.
2. **Framework-checkout fallback.** If no `.nizam/tools/skill.json` is found,
   the runtime falls back to a repository-root `tools/skill.json` path — the
   layout this framework repository itself ships at its own root. This
   fallback exists for a framework checkout evaluating itself (rather than a
   bootstrapped consumer repository), and is retained explicitly so it is
   unambiguously distinguishable from the bootstrapped-consumer path above.
3. **Pinned-checkout discovery.** Where a consumer repository instead
   references a pinned Nizam release tag without vendoring the framework's
   files locally, the runtime resolves `tools/skill.json` inside a checkout of
   that pinned tag (see `methodology/05_release_train.md` for the tag/version
   model).
4. **Manifest resolution.** Once `tools/skill.json` is located, the runtime
   reads its `entry_point` field to resolve the path to the instructions
   payload (`tools/SKILL.md`) and its `capabilities` array to resolve any
   individual protocol module path a task needs, without loading the whole
   framework.
5. **Failure behavior.** If no `tools/skill.json` can be found by any of the
   methods above, the runtime MUST treat the repository as ungoverned by this
   framework for the current task and MUST NOT fabricate governance behavior
   in its absence.

## 3. Loading

Once discovered, the runtime loads the payload as follows:

1. **Inject `SKILL.md` as instructions context.** The full contents of
   `tools/SKILL.md` are made available to the acting agent as system-level or
   skill-level instructions context — the same tier of context the runtime
   uses for its own standing operating instructions — rather than as
   conversational content the agent might discard or deprioritize.
2. **Load on demand, not unconditionally.** Consistent with `SKILL.md`
   Section 1, the runtime injects this payload when the current or upcoming
   task matches one of the triggers that section names, not on every
   invocation regardless of task.
3. **One payload, no forked copies.** The runtime MUST NOT maintain its own
   runtime-specific rewritten copy of `SKILL.md`. If a runtime's native
   instructions-loading mechanism requires a wrapper file (for example, a
   short pointer file in a runtime-specific configuration location), that
   wrapper MUST reference or include `tools/SKILL.md` verbatim rather than
   restate or fork its content.

## 4. The Three Abstract Operations

Every protocol document this skill summarizes assumes an agent runtime can
perform exactly three abstract operations. Each runtime's adapter maps these
onto its own native tool-calling primitives; the mapping is the adapter's
entire job.

### 4.1 `read-state`

- **Purpose:** Read the current durable-state content a task needs —
  `NIZAM.json`, a governance module file, or an artifact under a project's
  `.agent/` directory (run state, feature list, a contract, a QA verdict).
- **Inputs:** A repository-relative file path.
- **Outputs:** The file's full content, or a clearly distinguishable
  not-found signal if the path does not resolve on disk.
- **Error behavior:** A runtime whose native read primitive raises an error
  (permission denied, path outside an allowed boundary) MUST surface that
  error to the acting agent rather than silently returning empty content that
  could be mistaken for a legitimately empty file.
- **Native satisfaction:** Any generic file-read capability of the host
  environment satisfies this operation.

### 4.2 `write-evidence`

- **Purpose:** Persist a material result — a proposed or revised document, a
  durable-state update, or an evidence file capturing verification output —
  to its canonical durable location, per the evidence-externalisation rule
  (`methodology/04_tool_driven_state.md` Section 3).
- **Inputs:** A repository-relative destination path and the content to
  write.
- **Outputs:** Confirmation the write completed, sufficient for the acting
  agent to treat the result as durably recorded rather than merely stated in
  conversation.
- **Error behavior:** A failed write (permission denied, disk full, path
  outside an allowed boundary) MUST be surfaced as an error, never silently
  swallowed; a role that cannot confirm its write succeeded MUST NOT report
  the corresponding step as complete (`standard/anti_hallucination.md`, AH-3).
- **Native satisfaction:** Any generic file-write or file-edit capability of
  the host environment satisfies this operation.

### 4.3 `run-verification`

- **Purpose:** Execute a contract's verification commands (or any other
  check the framework's protocols require, such as a schema validation
  command) and capture the command's output and exit code as evidence.
- **Inputs:** A command string, and the working directory it should run in.
- **Outputs:** The command's captured standard output and standard error
  (written to an evidence file per DD-3, not returned inline only) and its
  exit code.
- **Error behavior:** A non-zero exit code is a verification failure, not an
  error the runtime silently retries or reinterprets as success; the acting
  agent decides how to respond (rework, escalate) per the governing protocol.
- **Native satisfaction:** Any generic shell or command-execution capability
  of the host environment satisfies this operation.

## 5. Adapter Conformance Checklist

An integrator adapting a new agent runtime to this framework can verify
conformance against this numbered, objectively checkable list. Every item
MUST be satisfied.

1. The adapter locates `tools/skill.json` via consumer-repo discovery,
   pinned-checkout discovery, or both (Section 2).
2. The adapter resolves `entry_point` from `tools/skill.json` and loads that
   exact file's content — it does not load a paraphrased, summarized, or
   runtime-authored substitute.
3. The adapter injects the loaded payload as instructions/skill-tier context,
   not as ordinary conversational content (Section 3, Item 1).
4. The adapter loads the payload conditionally, based on the triggers
   `tools/SKILL.md Section 1` defines, not unconditionally on every
   invocation.
5. The adapter maintains no forked or rewritten copy of `tools/SKILL.md`
   anywhere in the runtime's own configuration surface (Section 3, Item 3).
6. The adapter provides a `read-state` mapping backed by a real file-read
   primitive, capable of reading any repository-relative path, including
   paths under `.agent/`.
7. The adapter provides a `write-evidence` mapping backed by a real
   file-write primitive, and surfaces write failures as errors rather than
   silent no-ops.
8. The adapter provides a `run-verification` mapping backed by a real
   command-execution primitive, capturing both output and exit code for every
   invocation.
9. The adapter surfaces every operation's error conditions to the acting
   agent rather than suppressing them (Sections 4.1-4.3).
10. The adapter does not fabricate governance behavior when no
    `tools/skill.json` can be discovered (Section 2, Item 4).

## 6. References

- `tools/skill.json` — the capability manifest an adapter discovers and
  resolves per Section 2.
- `tools/SKILL.md` — the single instructions payload an adapter loads per
  Section 3.
- `methodology/04_tool_driven_state.md` — the evidence-externalisation and
  durable-state rules the `write-evidence` operation exists to satisfy.
- `standard/anti_hallucination.md` — the constraints (in particular AH-3)
  that bind how a runtime's adapter must handle write and verification
  failures.
