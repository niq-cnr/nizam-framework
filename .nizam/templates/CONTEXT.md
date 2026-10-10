---
id: nizam-template-context
title: "CONTEXT.md Template"
description: "Consumer-repo CONTEXT.md template: the fill-in skeleton a bootstrapped repository copies and completes with its own architecture summary, module map, execution commands, and mandatory scope boundaries."
version: 0.1.0
status: active
authoritative_source: templates/CONTEXT.md
---

<!--
Copy this file to CONTEXT.md at the root of {{REPO_NAME}} after bootstrap and replace
every {{PLACEHOLDER}} token in the body below with real, repo-specific content. The
frontmatter block above describes this template artifact itself (per
standard/NDS.md Sec 2) and MUST NOT be edited with placeholder tokens; only the body
that follows is fill-in-the-blanks.
-->

# {{REPO_NAME}} — CONTEXT.md

**Last Updated:** {{YYYY-MM-DD}}

## 1. Architecture Summary

{{ARCHITECTURE_SUMMARY}}

<!-- One paragraph: what this repository is, its core components, and how it fits into
     the wider ecosystem it belongs to. -->

## 2. Module Map

| Module | Path | Owns | Depends On |
| --- | --- | --- | --- |
| {{MODULE_NAME}} | `{{MODULE_PATH}}` | {{MODULE_OWNS}} | {{MODULE_DEPENDS_ON}} |

<!-- Add one row per top-level module/directory this repository owns. -->

## 3. Execution Commands

| Action | Command |
| --- | --- |
| Install Dependencies | `{{INSTALL_COMMAND}}` |
| Run Tests | `{{TEST_COMMAND}}` |
| Run Linter | `{{LINT_COMMAND}}` |
| Build | `{{BUILD_COMMAND}}` |
| Run Locally | `{{RUN_COMMAND}}` |

<!-- Exact, copy-pasteable CLI commands. Do not leave a command cell empty; use "N/A"
     if a given action genuinely does not apply to this repository. -->

## Out of Scope

The following are explicit boundaries for {{REPO_NAME}}. Agents MUST NOT implement,
refactor, or propose work in these areas without explicit human authorization:

- {{OUT_OF_SCOPE_ITEMS}}

<!-- List 3-5 concrete, repo-specific hard boundaries. Generic placeholders left
     unfilled in a committed CONTEXT.md are a documentation-standard violation. -->
