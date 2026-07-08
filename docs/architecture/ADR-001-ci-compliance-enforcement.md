---
id: adr-001-ci-compliance-enforcement
title: "ADR-001: CI Compliance Enforcement"
description: "Architecture decision to adopt a repo-local, runtime-agnostic compliance validator executed by CI on every pull request and push to main, closing the gap between NDS §7's prescribed enforcement and the framework's shipped (unenforced) state."
version: 0.1.0
status: active
authoritative_source: docs/architecture/ADR-001-ci-compliance-enforcement.md
---

# ADR-001: CI Compliance Enforcement

**Status:** ACCEPTED
**Date:** 2026-07-08
**Decision Makers:** Nizam Framework maintainers (human-authorized, phase 002-self-compliance)
**Supersedes:** None

## Context

The phase-001 compliance audit found that genesis shipped `standard/NDS.md` violations —
24 `authoritative_source` values that were not repo-relative, 8 untagged code fences, and
verdict-shape drift across multiple documents — that 22 internal gate reviews failed to
catch. Those violations were only caught by an external pull-request reviewer after the
fact. Root cause: verification logic checked for frontmatter key *presence*, not value
*format* (Finding G2 in `.agent/product_spec_002.md` §2), so a syntactically-present but
semantically-wrong `authoritative_source` or an untagged fence passed every internal check.
Separately, `standard/NDS.md` §7 already prescribes CI enforcement of the documentation
standard, but the repository, as shipped, contained no CI workflow and no automated
validator of any kind (Finding G1). The framework was asking its consumers to enforce a
standard it did not enforce on itself.

## Decision

Adopt CI enforcement of `standard/NDS.md` §7 via a repo-local, runtime-agnostic compliance
validator (`tools/validate.sh`, delivered by feature F-012) invoked by a GitHub Actions
workflow (`.github/workflows/compliance.yml`, delivered by feature F-013) on every
`pull_request` and on every `push` to `main`. The validator becomes an indexed capability
in `NIZAM.json` so agents can locate and invoke it through the standard context-routing
path rather than through repository-specific tribal knowledge.

## Consequences

### Positive

- Documentation-standard violations (format-level, not merely presence-level) are caught
  by machine enforcement before merge, closing the gap that let 24 non-repo-relative
  `authoritative_source` values, 8 untagged fences, and verdict-shape drift ship
  undetected through 22 internal gate reviews.

### Negative

- The repository layout gains a GitHub-specific CI wrapper (`.github/workflows/`) around
  the otherwise portable `tools/validate.sh` validator, introducing a platform-specific
  surface that a non-GitHub consumer of the framework would need to replace with an
  equivalent CI trigger for their own platform.

### Follow-Up Actions

- F-012 implements `tools/validate.sh` and indexes it as a capability in `NIZAM.json`.
- F-013 implements `.github/workflows/compliance.yml`, wiring `tools/validate.sh` into CI.
- Consumer repositories can reuse `tools/validate.sh` directly per the Governance
  Inheritance Protocol (`standard/GIP.md`), independent of the GitHub-specific CI wrapper.

## Alternatives Considered

| Alternative | Description | Why Rejected |
| --- | --- | --- |
| Rely on external human review only | Continue depending on PR reviewers to catch NDS violations, as happened in phase 001. | Already demonstrated to fail: 22 internal gate reviews passed violations that only an external reviewer caught; not machine-enforced, not repeatable, not scalable. |
| Third-party/hosted linting service | Adopt an external SaaS documentation-linting product instead of an in-repo script. | Violates the framework's runtime-agnostic, portable-payload design tenet; would introduce an external infrastructure dependency the framework explicitly avoids. |
