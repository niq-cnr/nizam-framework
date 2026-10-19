---
id: nizam-self-governance-agents
title: "Nizam Framework — Local Agent Instructions"
description: "Route work on this repository through its installed immutable Nizam governance."
version: 0.4.0
status: active
authoritative_source: AGENTS.md
change_log:
  - version: "0.4.0"
    date: "2026-10-19"
    summary: "Exit temporary corrective override mode upon re-bootstrapping .nizam/ to the corrective immutable release v1.10.0 (6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7) and route local agent sessions through the installed v1.10.0 governance."
  - version: "0.3.1"
    date: "2026-10-19"
    summary: "Record explicit transitional entry precedence during the v1.9.0 audit and follow-up execution mandate (C0-C5, closing F1-F3) until .nizam/ is re-bootstrapped to the corrective release in C5, and reflect default noncommitting publish mode (prepare)."
  - version: "0.3.0"
    date: "2026-10-18"
    summary: "Exit temporary corrective override mode upon re-bootstrapping .nizam/ to the corrective immutable release v1.9.0 (0c9b1c5979a922c75499e0bfe4d9dbf9524f717d) and route local agent sessions through the installed v1.9.0 governance."
  - version: "0.2.1"
    date: "2026-10-18"
    summary: "Record explicit transitional entry precedence during the v1.8.0 rollout corrective execution mandate (B0-B6, closing V1-V7) until .nizam/ is re-bootstrapped to the corrective release in B6."
  - version: "0.2.0"
    date: "2026-10-18"
    summary: "Exit temporary remediation override mode upon re-bootstrapping .nizam/ to the post-follow-up immutable release v1.8.0 (606d11ee84deff0d3b7934cbfd715223d64ac79d) and route local agent sessions through the installed v1.8.0 governance."
  - version: "0.1.2"
    date: "2026-10-18"
    summary: "Restore explicit transitional entry precedence during the 2026-10-18 post-remediation follow-up mandate (A0-A8) until .nizam/ is re-bootstrapped to the post-follow-up immutable release."
  - version: "0.1.1"
    date: "2026-10-18"
    summary: "Route local agent sessions through tools/start_path.py task classification, lightweight amendments, exclusive evidence capture, and concise status views under the 2026-10-18 remediation mandate."
  - version: "0.1.0"
    date: "2026-10-10"
    summary: "Route local agent sessions through the public v1.5.0 installation and the authorized repository-local scope."
---

# Local agent instructions

Before planning, editing or reviewing work in this repository, query
`.nizam/NIZAM.json`, then load `.nizam/tools/SKILL.md`. Resolve the installed
index's paths relative to `.nizam/` and read only the protocols the task needs.
The root modules and root `NIZAM.json` are the framework's authored product;
consult them when a task requires source work.

The operator authorized self-adoption for **niq-cnr/nizam-framework only** under
`H-CONSUMER-UPGRADE`, recorded before installation in `.agent/run_state.json`
(migrated to exact origin `https://github.com/niq-cnr/nizam-framework.git` per
[authority-interpretation.json](.agent/evidence/120/authority-interpretation.json)).
[SELF_GOVERNANCE.md](docs/planning/SELF_GOVERNANCE.md) records that local scope and
the installation's current commissioning stage, and
[REMEDIATION_2026_10_18.md](docs/planning/REMEDIATION_2026_10_18.md) records the
2026-10-18 quality and velocity remediation, follow-up (`A0`–`A8`), `v1.8.0`
rollout corrective execution (`B0`–`B6`), and `v1.9.0` audit follow-up execution
(`C0`–`C5`). No external organization scope or ecosystem membership is asserted
by this adoption.

Before starting a change, classify the task with `tools/start_path.py classify`
into `trivial`, `bugfix`, `small-change`, `standard-feature`, or `high-risk`
using canonical relative paths and semantic change properties. Non-feature routes
(`trivial`, `bugfix`, `small-change`) are gated by `tools/start_path.py
begin|done`; feature work uses the current approved contract under
`.agent/contracts/` (with bounded mechanical scope or verification updates
supported via `tools/start_path.py amend-contract` when goals, invariants, and
risk boundaries are unchanged). Use `tools/start_path.py preflight` before
governed attempts, `tools/start_path.py capture` to write exclusive
per-execution evidence files without silent overwrites, `tools/start_path.py
publish` (default `--mode prepare`; `--mode prepare|publish|finalize`) and
`tools/start_path.py build-receipt` to prepare, externally mediate, finalize, and
bind receipt-qualified stage evidence without hidden Git mutations,
`tools/start_path.py status` for a concise read-only status view, and
`tools/start_path.py resume` for receipt-verified transitions. The Orchestrator
owns lifecycle state and circuit counters in `.agent/run_state.json`;
implementation agents preserve those fields.

Do not edit installed `.nizam/` files. A future upgrade requires operator
authorization, a reviewed immutable pin update and re-bootstrap. Use
`PYTHONDONTWRITEBYTECODE=1` when invoking installed Python tools so transient
bytecode does not contaminate the exact payload inventory. Source changes in the
root framework do not update the installed release automatically.
