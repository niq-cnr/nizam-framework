---
id: nizam-template-agents
title: "AGENTS.md Template"
description: "Consumer-repo AGENTS.md template: the session-objective skeleton a bootstrapped repository copies and completes with its active phase, current objective, and delegation-matrix reference."
version: 0.3.0
status: active
authoritative_source: templates/AGENTS.md
change_log:
  - version: "0.3.0"
    date: "2026-10-27"
    summary: "NF-05: route consumers through the installed index, canonical task classifier and stopping policy, with conditional ecosystem membership."
  - version: "0.2.0"
    date: "2026-10-11"
    summary: "Route Evaluator delegation to both independent contract review and implementation QA (A04a)."
---

<!--
Copy this file to AGENTS.md at the root of {{REPO_NAME}} after bootstrap and replace
every {{PLACEHOLDER}} token in the body below with the live session state. The
frontmatter block above describes this template artifact itself; only the body is
fill-in-the-blanks.
-->

# {{REPO_NAME}} — Agent Session Objective

## Current Session

**Current Objective:** {{CURRENT_OBJECTIVE}}

**Active Phase:** {{ACTIVE_PHASE_ID}} ({{ACTIVE_PHASE_NAME}})

**Session Started:** {{YYYY-MM-DDTHH:MMZ}}

## Installed Governance

Before planning, editing or reviewing, query `.nizam/NIZAM.json`, then load
`.nizam/tools/SKILL.md`. Resolve indexed paths relative to `.nizam/` and read
only the protocols the task needs. The consumer's own documents and extensions
remain outside that immutable installation.

If this repository has configured ecosystem membership, verify the applicable
scope using that membership's canonical scope document and adopted policy.
Standalone adoption does not require ecosystem membership.

## Task Routing

Use `.nizam/tools/start_path.py classify` before starting a change. Follow the
selected canonical route: `trivial`, `bugfix`, `small-change`,
`standard-feature`, or `high-risk`. The installed skill routes to the applicable
begin/done gates or approved feature contract and required independent review.
Record scoped evidence through the installed tools before claiming completion.

Role allocation and contract gates are defined in
`.nizam/standard/AGF.md` and `.nizam/methodology/01_execution.md`.
The stopping policy is defined only in
`.nizam/methodology/03_circuit_breaker.md`; follow that installed policy rather
than a copied attempt threshold. Do not edit installed governance files.

## Handoff Notes

{{HANDOFF_NOTES}}

<!-- Any context the next agent session needs: work completed, work remaining, and
     blockers still open. -->
