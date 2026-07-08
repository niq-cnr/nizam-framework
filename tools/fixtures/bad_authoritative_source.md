<!-- INTENTIONAL NEGATIVE FIXTURE - authoritative_source deliberately wrong, used only via tools/validate.sh --target -->
---
id: bad-authoritative-source-fixture
title: "Bad Authoritative Source Fixture"
description: "Intentional negative fixture for tools/validate.sh --target: valid 6-key frontmatter except authoritative_source deliberately points at the wrong path."
version: 0.1.0
status: draft
authoritative_source: standard/NDS.md
---

# Bad Authoritative Source Fixture

This file intentionally fails the C2 format check: its `authoritative_source` value
(`standard/NDS.md`) does not equal this file's own repository-relative path
(`tools/fixtures/bad_authoritative_source.md`), and is not the literal string `NA`.

This fixture is reachable only via `bash tools/validate.sh --target
tools/fixtures/bad_authoritative_source.md`; it is never part of the default
(no-args) repo-wide sweep, which structurally excludes `tools/fixtures/`.
