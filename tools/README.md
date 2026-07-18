---
id: nizam-tools-readme
title: "Tools Module — Index"
description: "Index for the tools/ module: the one unified, runtime-agnostic skill payload (manifest, instructions, and adapter interface) agents load to act on the Nizam framework."
version: 0.3.1
status: active
authoritative_source: tools/README.md
change_log:
  - version: "0.3.0"
    date: "2026-07-10"
    summary: "Sync to the phase-004 compliance validator: document the full C1-C11 check set (C9 repo-wide path-resolution, C10 single-source-of-truth consistency, C11 dogfood schema validation, all added by phase 004) and the new SUMMARY: 11 passed, 0 failed total."
  - version: "0.3.1"
    date: "2026-07-17"
    summary: "Sync to the phase-005 compliance validator: document the new C12 ecosystem schema-family fixture check (feature 042) and the new SUMMARY: 12 passed, 0 failed total."
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

## Compliance Coverage — C1–C12

`tools/validate.sh`, the repo-local NDS compliance validator, runs twelve
checks on every PR and push to `main` (`.github/workflows/compliance.yml`).
As of phase 005 (extended validator + CI fixtures), the full default sweep
reports `SUMMARY: 12 passed, 0 failed`:

| Check | Name | What it enforces |
|---|---|---|
| C1 | Frontmatter schema | Every shipped `.md`'s frontmatter validates against `schema/frontmatter.schema.json`. |
| C2 | Format | Frontmatter fields (`version`, `status`, etc.) match their required format. |
| C3 | Untagged-fence sweep | No fenced code block in a shipped `.md` is missing a language tag. |
| C4 | `NIZAM.json` index integrity | Every path `NIZAM.json` indexes resolves on disk. |
| C5 | Branding/endpoint leakage | No vendor-specific branding or internal endpoint strings ship in the framework payload. |
| C6 | `bootstrap.sh` sanity | The inject/verify script passes its own internal sanity checks. |
| C7 | Module README presence | Every module directory carries a governed `README.md`. |
| C8 | Version-bump-vs-changelog | Any file whose frontmatter `version` increased vs `HEAD` is matched by a `change_log` entry for the new version, or a `CHANGELOG.md` line naming the file. |
| C9 | Repo-wide path-resolution | Every concrete repo-relative file path named in a shipped doc resolves on disk (placeholder/illustrative paths documented-exempt). |
| C10 | Single-source-of-truth consistency | Payload-set enumeration, bootstrapped-consumer discovery order, and the framework-version anchor stay consistent across every shipped doc. |
| C11 | Dogfood schema validation | Every `.agent/qa/*.json`, `.agent/contracts/*.json`, and `.agent/run_state.json` (when present) validates against the shipped schemas — enforce-if-present, skip-if-absent for a fresh consumer. |
| C12 | Ecosystem schema-family fixture validation | Every `tools/fixtures/{ecosystem_baseline,preflight_verdict,engineering_finding}_*.json` fixture validates (positive) or is rejected (negative) against its shipped schema, proving the fixtures are load-bearing rather than dormant. |

C9, C10, and C11 were added by phase 004 (`tools/verify_lib.sh` supplies
their shared, fixture-tested primitives); C12 was added by phase 005
(feature 042); C1–C8 shipped in earlier phases. Run `bash tools/validate.sh
--help` for the full per-check description.
