---
id: nizam-self-governance-agents
title: "Nizam Framework — Local Agent Instructions"
description: "Route work on this repository through its installed immutable Nizam governance."
version: 0.1.0
status: active
authoritative_source: AGENTS.md
change_log:
  - version: "0.1.0"
    date: "2026-10-10"
    summary: "Route local agent sessions through the public v1.5.0 installation and the authorized repository-local scope."
---

# Local agent instructions

Before planning, editing or reviewing work in this repository, query
`.nizam/NIZAM.json`, then load `.nizam/tools/SKILL.md`. Resolve the installed
index's paths relative to `.nizam/` and read only the protocols the task needs.
The installed payload is the governance used here. The root modules and root
`NIZAM.json` are the framework's authored product; consult them when a contracted
task requires source work.

The operator authorized self-adoption for **niq-cnr/nizam-framework only** under
`H-CONSUMER-UPGRADE`, recorded before installation in `.agent/run_state.json`.
[SELF_GOVERNANCE.md](docs/planning/SELF_GOVERNANCE.md) records that local scope and
the installation's current commissioning stage. No external organization scope
or ecosystem membership is asserted by this adoption.

Use the current approved contract under `.agent/contracts/`. Follow both
independent pre-code gates and the implementation, QA and evidence-capture gates
in the installed execution protocol. Preserve historical phase records and
capture command output, actual exit status and the exercised revision by path.
The Orchestrator owns lifecycle state and circuit counters in
`.agent/run_state.json`; implementation agents preserve those fields.

Do not edit installed `.nizam/` files. A future upgrade requires operator
authorization, a reviewed immutable pin update and re-bootstrap. Use
`PYTHONDONTWRITEBYTECODE=1` when invoking installed Python tools so transient
bytecode does not contaminate the exact payload inventory. Source changes in the
root framework do not update the installed release automatically.
