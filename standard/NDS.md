---
id: nizam-documentation-standard
title: "Nizam Documentation Standard (NDS)"
description: "The canonical, runtime-agnostic documentation standard for any repository that inherits the Nizam framework: required frontmatter, lifecycle, versioning, and machine-readability rules."
version: 0.1.0
status: active
authoritative_source: nizam-framework/standard/NDS.md
---

# Nizam Documentation Standard (NDS)

## 1. Overview

The NDS defines a single, machine-first documentation contract that any repository can
adopt regardless of language, runtime, or agent framework. All governance documentation
MUST be structured, parsable, and predictable before it is read by a human or an agent.

Core principles:

1. **Machine readability first.** All document metadata MUST live in structured YAML
   frontmatter, not in prose.
2. **One frontmatter block per document.** Exactly one frontmatter block, at the very
   top of the file, before any other content.
3. **Parse before read.** An agent MUST be able to validate a document's frontmatter and
   any embedded JSON/YAML artifacts without reading the narrative body.
4. **Supersede, don't delete.** Superseded documents are marked `deprecated`, not removed,
   so lineage remains auditable.

## 2. Required Frontmatter Keys

Every `.md` document governed by this standard MUST begin with a YAML frontmatter block
containing exactly these six required keys. The block MUST validate against
`schema/frontmatter.schema.json`.

| Key | Type | Format | Description |
|---|---|---|---|
| `id` | `string` | kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`) | A unique, stable identifier for the document. |
| `title` | `string` | non-empty | The human-readable title of the document. |
| `description` | `string` | non-empty | A concise, one- to two-sentence summary of the document's purpose. |
| `version` | `string` | semantic version (`MAJOR.MINOR.PATCH`) | The version of this document, independent of any code release version. |
| `status` | `string` | one of `draft`, `active`, `deprecated` | The current lifecycle state of the document. |
| `authoritative_source` | `string` | repository-relative path, or the literal `NA` | The path to the artifact this document describes, or `NA` for documents with no single source artifact. |

### 2.1 Optional Keys

| Key | Type | Description |
|---|---|---|
| `change_log` | `array` of `{version, date, summary}` objects | Optional per-document revision history. When present, each entry MUST carry all three fields. |

Modules MAY add further keys beyond the six required ones for module-specific metadata.
`schema/frontmatter.schema.json` permits additional properties; it never forbids extension,
only under-provision of the six required keys.

### 2.2 Example

```yaml
---
id: my-example-document
title: "My Example Document"
description: "Describes what this document is for, in one sentence."
version: 0.1.0
status: draft
authoritative_source: src/services/example/index.ts
---
```

## 3. Status Lifecycle

The `status` key follows a linear, one-directional lifecycle:

```
draft -> active -> deprecated
```

Rules:

1. **`draft`** — under active authorship or revision. Not yet binding on agents or humans.
2. **`active`** — the current, binding version of the document. Agents MUST treat `active`
   documents as authoritative for their domain.
3. **`deprecated`** — superseded or retired. The document is retained for lineage; it is
   never deleted. A `deprecated` document SHOULD name its replacement in its body or in a
   `change_log` entry.
4. **No skipping backward.** A document MUST NOT move from `active` back to `draft`, and
   MUST NOT move from `deprecated` back to `active`. A reintroduced need is served by a new
   document (or a new major version) that starts again at `draft`.

## 4. Versioning and Change Log Rules

1. **Semantic versioning.** Every document version follows `MAJOR.MINOR.PATCH`:
   - **MAJOR** — a breaking change to the document's meaning, structure, or a full rewrite.
   - **MINOR** — a substantial new section or non-breaking addition.
   - **PATCH** — a correction, clarification, or typo fix.
2. **Mandatory change-log entry on every version bump.** Any change to `version` MUST be
   accompanied by either a `change_log` frontmatter entry (per Sec 2.1) or an entry in the
   repository's root `CHANGELOG.md` that names the document. A version bump with no
   corresponding change record is a standard violation.
3. **Deprecation is a version bump.** Moving `status` to `deprecated` MUST be recorded as a
   change-log entry explaining why and, where applicable, what supersedes the document.

## 5. File and Heading Conventions

1. **One frontmatter block, top of file.** No document may contain more than one YAML
   frontmatter block, and it MUST be the first content in the file (no blank lines,
   comments, or other content precede it).
2. **Heading hierarchy starts at H1.** The first heading after frontmatter MUST be a
   single H1 matching (or closely paraphrasing) the frontmatter `title`. Subsequent
   sections use H2 and deeper, strictly nested (no skipping levels, e.g. H2 directly to H4).
3. **Module README requirement.** Every module directory (a directory that groups related
   governance documents, e.g. `standard/`, `methodology/`) MUST contain a `README.md` that
   indexes the module's documents with a one-line purpose for each, and carries the same
   six-key frontmatter as any other governed document.

## 6. Machine-Readability Rules

1. **Parse before read.** An automated check MUST be able to extract and validate a
   document's frontmatter without parsing the Markdown body.
2. **Tagged code fences.** Every fenced code block MUST declare a language tag (for
   example ` ```json `, ` ```bash `, ` ```yaml `). Untagged or ambiguous fences that could
   be mistaken for structural content (frontmatter-like blocks, schema-like blocks) are
   prohibited, because they break automated structural parsing.
3. **Independently valid embedded artifacts.** Any JSON or YAML artifact referenced by a
   document (a schema, a template, an example payload) MUST be independently parse-valid
   on its own — a document must never be the only thing holding an embedded artifact
   together syntactically.
4. **No branding or endpoint leakage.** Governance documents MUST NOT reference
   organization-specific infrastructure endpoints, private URLs, or internal branding.
   Documentation shipped as part of a portable governance framework must remain adoptable
   by any consumer without modification.

## 7. Enforcement

A conforming CI job SHOULD, at minimum:

1. Verify every `.md` governed by this standard begins with frontmatter containing all
   six required keys, validated against `schema/frontmatter.schema.json`.
2. Verify `status` is one of `draft`, `active`, `deprecated`.
3. Verify `version` matches `MAJOR.MINOR.PATCH`.
4. Verify every module directory contains a `README.md`.
5. Fail any change that bumps `version` without a corresponding change-log entry.
