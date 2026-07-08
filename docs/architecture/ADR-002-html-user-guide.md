---
id: adr-002-html-user-guide
title: "ADR-002: HTML User Guide"
description: "Architecture decision to ship a single, self-contained, version-anchored HTML user guide at docs/guide/index.html as the framework's human-facing narrative adoption surface, and to declare the shipped-vs-internal status of the docs/ tree."
version: 0.1.0
status: active
authoritative_source: docs/architecture/ADR-002-html-user-guide.md
change_log:
  - version: "0.1.0"
    date: "2026-07-08"
    summary: "Initial ADR: adopt docs/guide/index.html as the shipped HTML user guide, version-anchored to NIZAM.json framework.version; declare docs/architecture/ and docs/guide/ as shipped documentation and docs/planning/ as framework-internal."
---

# ADR-002: HTML User Guide

**Status:** ACCEPTED
**Date:** 2026-07-08
**Decision Makers:** Nizam Framework maintainers (human-authorized, phase 003-communication)
**Supersedes:** None

## Context

A documentation-clarity audit of the shipped framework — conducted jointly by the
orchestrator and an independent cold-read agent, and recorded in
`.agent/product_spec_003.md` Sec 2 — produced cold-read ratings of humans 6/10 and
agents 7.5/10, and logged nine findings (H1-H9):

- **H1** — `CONTEXT.md`, the agent entry point, is stale: it describes `NIZAM.json` and
  `bootstrap.sh` as not-yet-shipped when both are shipped, omits phase-002 surfaces
  (`tools/validate.sh`, CI, `docs/architecture/`), and understates the files `bootstrap.sh`
  injects.
- **H2** — `README.md` has zero copy-pasteable commands: no pinned-tag quickstart, no
  human-vs-agent entry split, no pointer to `tools/SKILL.md`, no mention of the validator,
  CI, or ADRs.
- **H3** — no `LICENSE` file, a hard adoption blocker (human-gated, out of scope here).
- **H4** — a functional adoption-contract bug: `tools/interface.md` tells runtimes to
  discover `tools/skill.json` at the consumer repo root, but `bootstrap.sh` installs the
  payload under `.nizam/`, so discovery-as-written misses every bootstrapped consumer.
- **H5** — payload-set drift between `standard/GIP.md` (3 directories) and
  `bootstrap.sh`/`CHANGELOG.md` (4 directories plus `NIZAM.json`).
- **H6** — shipped docs leak pipeline-internal state, and the `docs/` tree's
  shipped-vs-internal status is undeclared and unindexed by `NIZAM.json`.
- **H7** — jargon (NDS/AGF/GIP, and the unexpanded "AGIP") appears at first contact,
  before expansion.
- **H8** — no adoption guidance for existing repos (conflict handling, incremental
  tiers).
- **H9** — no quickstart, no worked example, no FAQ, no post-bootstrap walkthrough: the
  markdown corpus is reference-shaped (standards, protocols, schemas, templates) and
  excellent for targeted agent lookup, but has no narrative adoption surface for a
  human first-time reader.

This ADR addresses the structural remediation shared by H6 and H9: the framework has no
single, self-contained, human-narrative presentation surface, and the `docs/` tree's
shipped-vs-internal boundary is undeclared.

## Decision

Ship exactly ONE self-contained HTML user guide at `docs/guide/index.html` as the
framework's human-facing narrative adoption surface (full content design deferred to
feature F-018; this ADR is the decision and layout record). The guide MUST be:

- a single file with inline CSS and inline JS — zero external network requests;
- built on a system font stack (no webfonts);
- responsive to `prefers-color-scheme` for both dark and light rendering;
- WCAG-AA contrast compliant and print-friendly;
- sourced exclusively from claims already present in the shipped docs (the External
  Anchor Rule) — the guide invents no behavior.

Because HTML sits entirely outside the NDS markdown-frontmatter contract (`standard/NDS.md`
frontmatter and fence rules apply only to `.md` files), the guide is given its own
machine-checkable consistency mechanism instead: the guide is **version-anchored** — its
embedded framework version (rendered in both a `<meta name="framework-version">` element
and the page footer) MUST equal `NIZAM.json`'s `framework.version` field. This makes
narrative drift between the guide and the shipped framework version machine-detectable,
independent of any markdown-specific check.

This decision also formalizes the shipped-vs-internal status of the `docs/` tree,
resolving H6:

- `docs/architecture/` (Architecture Decision Records, e.g. this file and ADR-001) and
  `docs/guide/` (the HTML user guide) are **shipped documentation** — distributed with
  the framework repository and indexed by `NIZAM.json` (deferred to F-018).
- `docs/planning/` (`manifest.json`, `DEBT.md`) is **framework-internal** governance
  and pipeline state — not shipped documentation, and not indexed by `NIZAM.json`.

No guide HTML content and no `NIZAM.json` index change are part of this decision; both
are deferred to feature F-018, because the validator's index-integrity check (C4)
requires every indexed path to resolve on disk, and `docs/guide/index.html` does not yet
exist.

## Consequences

### Positive

- The framework gains a dependency-free, GitHub-Pages- or locally-renderable narrative
  surface for human first-contact readers, raising human legibility without adding any
  runtime dependency or external service.
- The version anchor gives HTML — a format the compliance validator's markdown sweeps
  (frontmatter/fence checks) do not cover — its own machine-checkable drift contract,
  so the guide cannot silently fall out of sync with the shipped framework version.
- Declaring `docs/`'s shipped-vs-internal status closes finding H6 and gives `NIZAM.json`
  indexing (F-018) an unambiguous rule for what to index.

### Negative

- `docs/guide/index.html` sits outside `tools/validate.sh`'s C1 (frontmatter schema) and
  C3 (untagged-fence sweep) checks, because those checks are markdown-specific. The
  guide's correctness is therefore enforced by feature acceptance tests (F-018) and
  phase-close checks (F-022) instead of a new C-numbered `validate.sh` check.
- `NIZAM.json` is not updated by this decision, so the guide and the second ADR are not
  yet indexed or discoverable through the standard context-routing path until F-018
  lands.

### Follow-Up Actions

- F-018 authors `docs/guide/index.html` to the full design contract of
  `.agent/product_spec_003.md` Sec 4, then indexes `docs/architecture/ADR-001-*.md`,
  `docs/architecture/ADR-002-*.md`, and `docs/guide/index.html` in `NIZAM.json`, keeping
  it schema-valid against `registry/nizam-index.schema.json` with every indexed path
  resolving on disk (validator C4).
- F-019 corrects the adoption-contract findings (H4, H5, H8) that the guide will
  narrate.
- F-020 links the guide from `README.md` and fixes `CONTEXT.md`/`README.md` first-contact
  truth issues (H1, H2, H7).

## Alternatives Considered

| Alternative | Description | Why Rejected |
| --- | --- | --- |
| Extend the markdown corpus with a narrative onboarding `.md` file | Add a long-form "getting started" markdown document under an existing module. | Markdown still renders as a plain reference document without styling, dark/light adaptation, or a sticky table of contents; does not meaningfully raise the human cold-read rating the audit measured, and would still leave the corpus reference-shaped rather than narrative-shaped. |
| Adopt a static-site generator (e.g. a docs-site framework) | Generate a multi-page HTML site from the markdown corpus using a third-party static-site generator. | Introduces a build-time dependency and toolchain the framework's runtime-agnostic, dependency-free design tenets explicitly avoid; a single self-contained file requires no build step and no external tooling to view or ship. |
| Multiple linked HTML pages instead of one file | Split the guide into several linked HTML documents (one per section). | Breaks the zero-external-request, fully self-contained design goal (inter-page links still work, but the "one file, no dependencies, trivially copyable" property is lost); a single page with a sticky in-page table of contents satisfies the same navigability need without multiple files to keep in sync. |
