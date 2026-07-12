---
id: nizam-registry-readme
title: "Registry Module — Index"
description: "Index for the registry/ module: the JSON Schema the root NIZAM.json context router validates against, plus generalised ecosystem scope-definition and registry patterns for consumer repositories."
version: 0.2.1
status: active
authoritative_source: registry/README.md
change_log:
  - version: "0.2.1"
    date: "2026-07-12"
    summary: "Stale-count cleanup: the 'Relationship to NIZAM.json' section no longer hard-codes '13 capability entries' (the index had grown to 24); the sentence now refers to the capability entries without a count, so it cannot silently drift as the index grows."
---

# registry/

The `registry/` module owns the JSON Schema that the root `NIZAM.json` capability index
validates against, plus generalised scope-definition and registry patterns a consumer
repository can reuse to build its own ecosystem-level registry on top of Nizam. It
depends on `schema/` for JSON Schema conventions (see `product_spec.md` Sec 2.2) and
ships no project-specific registry data of its own.

## Files

| File | Purpose |
|---|---|
| [`nizam-index.schema.json`](nizam-index.schema.json) | JSON Schema (draft 2020-12) that the root `NIZAM.json` context router must validate against: the `framework` identity block, the `modules[]`/`capabilities[]` index shapes, the `schemas[]`/`templates[]` path indexes, the `consumption_guidance` field, and the `index_schema`/`self_reference` self-referencing entries. |
| [`scope_definition_patterns.md`](scope_definition_patterns.md) | Generalised, de-branded ecosystem registry patterns: the in-scope/incubating/reference-archive/out-of-scope list-partition shape, `depends_on` dependency-map conventions, `phase_progress` tracking, and the drift rules governing registry authority. Prose-only pattern guide; carries no filled-in project scope data. |
| `README.md` | This file — registry module index. |

## Relationship to `NIZAM.json`

The root `NIZAM.json` is **not** a file under this directory — it lives at the
repository root, per `product_spec.md` Sec 2.3, so it is the very first thing an agent
or `bootstrap.sh` run finds. This module supplies the schema `NIZAM.json` must satisfy
(`nizam-index.schema.json`) and nothing else about `NIZAM.json` itself; the index's
actual content — the module map, the capability entries, the schema and template
path indexes, and the consumption guidance — is authored and maintained at the
repository root, not restated here.

## Machine Validation

`nizam-index.schema.json` is itself validated as plain JSON Schema (parses as JSON and
declares `"$schema": "https://json-schema.org/draft/2020-12/schema"`).
`scope_definition_patterns.md` and this `README.md` carry the same six-key frontmatter
(`standard/NDS.md` Sec 2) and validate against `schema/frontmatter.schema.json`,
identically to every other module's governed documents. The root `NIZAM.json` must
validate against `nizam-index.schema.json`, and every path it indexes (every `path`,
`authoritative_source`, `key_documents` entry, and `schemas[]`/`templates[]` item) must
resolve on disk.
