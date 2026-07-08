---
id: nizam-template-debt
title: "DEBT.md Template"
description: "Technical-debt register template: the empty debt-register table skeleton a bootstrapped repository copies and populates as debt is logged."
version: 0.1.0
status: active
authoritative_source: templates/DEBT.md
---

<!--
Copy this file to docs/planning/DEBT.md at {{REPO_NAME}}'s root after bootstrap. Append
one row per logged debt item; never delete a row, only move it to "Resolved Items" with
a remediation date. The frontmatter block above describes this template artifact
itself; only the table rows below are fill-in-the-blanks.
-->

# {{REPO_NAME}}: Technical Debt Register

This document tracks known technical debt, architectural gaps, and deferred work for
{{REPO_NAME}}, reviewed as part of every planning cycle per
`methodology/00_planning.md`.

## Active Debt Items

| ID | Date | Severity | Description | Remediation |
| --- | --- | --- | --- | --- |
| {{DEBT_ID_PREFIX}}-001 | {{YYYY-MM-DD}} | {{SEVERITY}} | {{DEBT_DESCRIPTION}} | {{REMEDIATION_PLAN}} |

<!-- Severity SHOULD be one of: BLOCKER, HIGH, MEDIUM, LOW. -->

## Resolved Items

| ID | Date Resolved | Description | Resolution |
| --- | --- | --- | --- |
| _None yet._ | | | |
