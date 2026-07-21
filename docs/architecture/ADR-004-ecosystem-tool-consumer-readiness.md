---
id: adr-004-ecosystem-tool-consumer-readiness
title: "ADR-004: Ecosystem-Tool Consumer-Readiness"
description: "Architecture decision that the ecosystem-cycle tools must locate the injected governance payload under a consumer's .nizam/ (a governance-root), and anchor a baseline's framework_references to the injected provenance pin rather than the consumer's HEAD — the two self-fixture assumptions the phase-007 scratch-consumer pilot proved break against a real bootstrapped consumer."
version: 0.1.0
status: active
authoritative_source: docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md
---

# ADR-004: Ecosystem-Tool Consumer-Readiness

**Status:** ACCEPTED
**Date:** 2026-07-21
**Decision Makers:** Nizam Framework maintainers (human-authorized, phase 007-consumer-adoption)
**Supersedes:** None

## Context

Phase 007 ran the ecosystem cycle's first pilot against a real, non-self consumer — a
scratch/throwaway repository bootstrapped from the released `v0.8.0` tag (feature 063).
The adoption path itself held: `bootstrap.sh` clone → inject → `--verify-only` passed,
and `tools/validate.sh --payload` was green (11/11) inside the consumer. But the loop
surfaced two concrete defects, both traceable to the same root cause: every prior run of
the ecosystem tools had been in `--self-fixture` mode, where **the framework IS the
repository under inspection**, so the tools silently assume the framework's own on-disk
layout.

1. **Governance-root assumption.** `tools/ecosystem_preflight.py`'s
   `REQUIRED_REFERENCE_PATHS` (`schema/preflight_verdict.schema.json`,
   `schema/ecosystem_baseline.schema.json`) are resolved relative to `--repo-root`. In a
   real bootstrapped consumer the governance payload lives under `.nizam/` (e.g.
   `.nizam/schema/…`), not at the repo root, so the required references do not resolve;
   and the injected, still-untracked `.nizam/` is itself flagged. A clean Preflight
   against a real consumer is therefore a hard **FAIL** (three blocking findings), even
   though the consumer is correctly bootstrapped.
2. **Framework-pin mis-anchoring.** `build_baseline_document` anchors
   `framework_references[0].revision` to `resolve_head_revision(repo_root)` — the
   consumer's own HEAD — because in self-fixture mode that HEAD *is* the framework's. In
   a real consumer the framework version is the injected pin, recorded in
   `.nizam/provenance.json` (`framework_version` / `tag`, e.g. `v0.8.0`). The baseline
   thus mislabels which framework it ran under, conflating the consumer's revision with
   the framework's.

Both were predicted in the code itself — the multi-repo consistency guard is annotated a
"defensive invariant for a future multi-repository extension" — and both block *any*
real single-repo adoption, which is the prerequisite for the broader 0–n project
spectrum (see NIP-0002).

## Decision

1. **Resolve a governance-root, distinct from the repository root.** The ecosystem tools
   that read the injected payload MUST be able to locate it under the consumer's
   governance directory (conventionally `.nizam/`) — via an explicit option (e.g.
   `--governance-root`) and/or discovery of the bootstrap target — and resolve their
   required references against that governance-root, while continuing to inspect the
   consumer's working tree via `--repo-root`. The injected payload directory is treated
   as expected, not as an untracked blocking finding. `--self-fixture` mode (governance-
   root == repo-root) remains the degenerate case and MUST keep working unchanged.
2. **Anchor `framework_references` to the injected provenance pin.**
   `build_baseline_document` MUST anchor `framework_references` to the framework pin
   recorded in the governance-root's `provenance.json` (`framework_version` / `tag`), not
   to the consumer's HEAD. `repository_references` continues to anchor to the consumer's
   HEAD. The two reference categories then record two distinct, correct facts: which
   framework, and which consumer revision.

Implementation is sequenced into **phase 008** (the realization of NIP-0002); this ADR
records the decision and the evidence, and the corresponding `docs/planning/DEBT.md`
rows (NDEBT for finding A and finding B) track the remediation.

## Consequences

### Positive

- The ecosystem tools become runnable against a real bootstrapped consumer, not only the
  framework self-fixture — the precondition for every point on the 0–n spectrum.
- A baseline records honest provenance: the framework pin and the consumer revision are
  no longer conflated, so later Audit and Compare steps can trust "which framework" and
  "which repo" independently.

### Negative / risks

- Adds a governance-root resolution surface (flag and/or discovery) that must not break
  the existing `--self-fixture`/single-repo path or the hermetic `e2e_bootstrap_test.sh`.
- Reading `provenance.json` couples the baseline builder to the bootstrap artifact's
  shape; that shape must stay stable or be versioned.

## References

- `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` — the capability proposal whose
  phase this decision is realized in.
- `ecosystem/00_ecosystem_bootstrap.md` — the Bootstrap protocol that produces the
  `.nizam/` payload and `provenance.json` these tools must read.
- `tools/ecosystem_preflight.py` — the tool the decision amends (`REQUIRED_REFERENCE_PATHS`,
  `build_baseline_document`).
- `docs/planning/DEBT.md` — the NDEBT rows tracking remediation of findings A and B.
