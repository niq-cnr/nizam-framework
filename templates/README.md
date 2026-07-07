---
id: nizam-templates-readme
title: "Templates Module — Index"
description: "Index for the templates/ module: the seven consumer-repo document and manifest templates a bootstrapped repository copies and fills in — CONTEXT, AGENTS, DEBT, ADR, work-packet, phase, and manifest templates."
version: 0.2.0
status: active
authoritative_source: nizam-framework/templates/README.md
---

# templates/

The `templates/` module owns the templates a consumer repository copies after
bootstrap and fills in with its own content. It depends on `standard/` (see
`product_spec.md` Sec 2.2) for the frontmatter and documentation conventions its `.md`
templates carry, and contains no filled-in project content of its own.

| File | Purpose |
|---|---|
| [`CONTEXT.md`](CONTEXT.md) | Consumer-repo `CONTEXT.md` template: architecture summary, module map, execution commands, and the mandatory `## Out of Scope` boundary section. |
| [`AGENTS.md`](AGENTS.md) | Consumer-repo `AGENTS.md` template: current session objective, active phase, delegation-matrix reference, and scope-check reminder. |
| [`DEBT.md`](DEBT.md) | Technical-debt register template: the empty ID/Date/Severity/Description/Remediation table skeleton. |
| [`ADR_TEMPLATE.md`](ADR_TEMPLATE.md) | Architecture Decision Record template: Status/Context/Decision/Consequences skeleton, copied once per decision. |
| [`work-packet.template.json`](work-packet.template.json) | Scoped work-packet JSON template: id, objective, allowed/forbidden scope paths, acceptance criteria, and evidence file paths. |
| [`phase_template.yaml`](phase_template.yaml) | Phase definition YAML template; validates against `schema/phase.schema.json` and follows DD-3 Evidence Externalisation. |
| [`manifest.template.json`](manifest.template.json) | Planning manifest JSON template; validates against `schema/manifest.schema.json`. |

## Frontmatter Convention

Every `.md` template in this module (`CONTEXT.md`, `AGENTS.md`, `DEBT.md`,
`ADR_TEMPLATE.md`) carries **real** frontmatter describing the template artifact
itself — its own `id`, `title`, `description`, `version`, `status`, and
`authoritative_source` per `standard/NDS.md` Sec 2 — not placeholder tokens. `{{...}}`
placeholder tokens exist only in the document body that follows the closing `---`,
where a consumer repository fills them in with real, repo-specific content after
copying the file.

## Usage

1. Copy the desired template to its target path in the consumer repository (see each
   template's purpose above for its conventional destination).
2. Replace every `{{PLACEHOLDER}}` token in the body with real content. Leave the
   frontmatter block of the `.md` templates as-is, or update `version`/`status` only if
   the consumer repository intends to version its own copy independently.
3. Validate: `.md` templates against `schema/frontmatter.schema.json`; `phase_template.yaml`
   against `schema/phase.schema.json`; `manifest.template.json` against
   `schema/manifest.schema.json`; `work-packet.template.json` for JSON parse-validity.
