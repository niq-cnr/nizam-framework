---
id: nizam-tools-readme
title: "Tools Module — Index"
description: "Index for the tools/ module: the one unified, runtime-agnostic skill payload (manifest, instructions, and adapter interface) agents load to act on the Nizam framework."
version: 0.2.0
status: active
authoritative_source: nizam-framework/tools/README.md
---

# tools/

The `tools/` module owns the one unified, runtime-agnostic skill payload agents
load to act on the Nizam framework. There is exactly one skill, loadable by any
agent runtime through the same adapter contract — no per-runtime forks.

| File | Purpose |
|---|---|
| [`skill.json`](skill.json) | Machine-readable capability manifest: the skill's name and version, its `entry_point` (`SKILL.md`), a `capabilities` array mapping named capabilities to the framework module path each one is backed by, the abstract `runtime_requirements` any host environment must provide, and the `state_interface` describing the root index and the `.agent/` artifact families. |
| [`SKILL.md`](SKILL.md) | The single instructions payload any agent runtime loads to act on the framework: when to load it, how to consume the framework by querying the root index rather than bulk-reading, a summary of the contract-first execution loop, the circuit-breaker and anti-hallucination obligations every role carries, the durable-state and evidence-by-path obligations, and the verdict JSON formats every gate produces. |
| [`interface.md`](interface.md) | The runtime-adapter specification: how any agent runtime discovers `skill.json`, loads `SKILL.md` as instructions context, maps the framework's three abstract operations (`read-state`, `write-evidence`, `run-verification`) onto its own native tool primitives, and the numbered Adapter Conformance Checklist an integrator ticks through. |

## Design Decision — DD-4: Unified Skill Payload

This module exists to remediate one specific failure mode observed in prior
governance deployments: a skill's instructions being duplicated and forked
per agent runtime (a `.claude/`-style directory alongside a `.codex/`-style
directory, each drifting independently from the other over time). DD-4's
rule is unconditional:

- **Exactly one payload.** `SKILL.md` is the only skill-instructions document
  the framework ships. It is written in a runtime-agnostic voice with no
  vendor-specific tool names, so that no runtime's adapter ever needs its own
  rewritten copy.
- **No per-runtime fork directories.** No `tools/.claude/`, no `tools/.codex/`,
  no equivalent runtime-specific subdirectory under `tools/` — or anywhere
  else in the repository — is permitted. A runtime that needs a thin,
  runtime-native pointer to `SKILL.md` is expected to reference or include it
  verbatim (`interface.md` Section 3.3), never to restate its content.
- **One adapter contract, many adapters.** `interface.md` defines the single
  contract (discovery, loading, the three abstract operations) that any
  number of runtime-specific adapters can each independently implement,
  without the framework itself ever needing to know how many runtimes exist
  or what any one of them is called.

*Acceptance anchor:* exactly one `SKILL.md` exists in the whole repository,
and no per-runtime skill fork directory exists under `tools/`
(`product_spec.md` Section 4, DD-4).

## Machine Validation

Every `.md` in this module carries the same six-key frontmatter
(`standard/NDS.md` Section 2) and validates against
`schema/frontmatter.schema.json`, identically to every other module's governed
documents. `skill.json` is validated as plain JSON (`python3 -c
"import json; json.load(open('tools/skill.json'))"`); it carries no schema of
its own within this module — it is pure data consumed by `SKILL.md` and
`interface.md`, not a document requiring frontmatter.
