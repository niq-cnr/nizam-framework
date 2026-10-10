---
id: nizam-template-adr
title: "ADR Template"
description: "Architecture Decision Record template: the standard Status/Context/Decision/Consequences skeleton a repository copies once per significant architectural decision."
version: 0.1.0
status: active
authoritative_source: templates/ADR_TEMPLATE.md
---

<!--
Copy this file to docs/architecture/ADR-{{ADR_NUMBER}}-{{short-title}}.md and replace
every {{PLACEHOLDER}} token in the body below with decision-specific values. The
frontmatter block above describes this template artifact itself; only the body is
fill-in-the-blanks.

Status values: PROPOSED | ACCEPTED | SUPERSEDED | DEPRECATED (PROPOSED is the intended pre-filled default status for a newly copied ADR)
-->

# ADR-{{ADR_NUMBER}}: {{ADR_TITLE}}

**Status:** PROPOSED
**Date:** {{DECISION_DATE}}
**Decision Makers:** {{DECISION_MAKERS}}
**Supersedes:** {{SUPERSEDED_ADR_OR_NONE}}

## Context

{{DECISION_CONTEXT}}

<!-- Why is this decision needed? The forces at play, the problem being solved, and any
     constraints that influenced the decision. -->

## Decision

{{DECISION_STATEMENT}}

<!-- What was decided? State it clearly and unambiguously, in imperative language. -->

## Consequences

### Positive

- {{POSITIVE_CONSEQUENCE}}

### Negative

- {{NEGATIVE_CONSEQUENCE}}

### Follow-Up Actions

- {{FOLLOW_UP_ACTION}}

## Alternatives Considered

| Alternative | Description | Why Rejected |
| --- | --- | --- |
| {{ALTERNATIVE}} | {{ALTERNATIVE_DESCRIPTION}} | {{REJECTION_REASON}} |
