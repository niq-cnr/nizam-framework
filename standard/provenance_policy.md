---
id: nizam-provenance-policy
title: "Supply-Chain Provenance Policy"
description: "Rules for ensuring every artifact, prompt, model, tool call, and release is attestable and auditable; consumer pins are governed by a declared version range plus a committed provenance lock."
version: 0.4.0
status: active
enforcement: partially-enforced
authoritative_source: standard/provenance_policy.md
change_log:
  - version: "0.4.0"
    date: "2026-11-05"
    summary: "Operator directive 'governance simplification 2026-11-05 item 6': replaced exact tag+SHA pinning per consumer with a declared version range plus a committed .nizam/provenance.lock.json holding the resolved tag and resolved_sha, with CI asserting lock-to-payload consistency; exact-SHA evidence remains required for release and acceptance claims. Lock schema documented in Section 2."
  - version: "0.3.0"
    date: "2026-08-15"
    summary: "Phase-012 feature 089 (issue #52): state C14 as a supplied validator capability when executed, rather than evidence that an arbitrary consumer executed the check."
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3, gate H-CONSTITUTIONAL): marked partially-enforced -- the SHA-pinned-Actions requirement is now mechanized as validate.sh check C14 (vlib_workflows_sha_pinned over the workflows directory), while the attestation, agent-audit-envelope, and SLSA-pipeline requirements are consumer-aspirational."
---

# Supply-Chain Provenance Policy

> **Partially enforced.** When a checkout runs `tools/validate.sh`, check C14 verifies
> SHA-pinned Actions in that checkout's workflows. This supplied validator capability
> is not evidence that a consumer executed it; consumers record their own execution
> evidence. The artifact-attestation, agent-audit-envelope, and SLSA-pipeline
> requirements are consumer-aspirational — a consuming repository enforces them in
> its own build and release pipeline. Recorded per the Track 3 decision (feature 058).

## 1. Overview

In an agentic engineering environment, knowing *who* wrote the code is no longer sufficient; the system must prove *which agent, using which model, under which prompt, against which contract* produced the artifact.

Every build MUST be attributable. Artifacts, prompts, models, tool calls, and releases MUST be attestable and auditable.

## 2. Provenance Requirements

1. **Artifact Attestations:** All release artifacts (container images, binaries, packages) MUST emit an artifact attestation (e.g., via GitHub Artifact Attestations or Sigstore) establishing their origin.
2. **SHA-Pinned Workflows:** Third-party GitHub Actions and reusable workflows MUST be pinned to full-length commit SHAs, not mutable tags like `@v2` or `@main`.
3. **Audit Envelopes:** Every agentic task MUST emit an audit envelope containing:
   - Model identity and routing decision
   - Prompt template version
   - Tool-call summary with arguments and results
   - Source artifact hashes
   - Contract versions consumed
4. **SLSA Alignment:** Higher-assurance deployment paths MUST utilize SLSA-oriented build pipelines.
5. **Consumer Pin Version Range and Lock:** A consumer MUST declare a version range (`declared_range`) accepted for its inherited framework, not one exact tag alone, and MUST commit a lock file `.nizam/provenance.lock.json` holding the resolved pin. The lock records exactly these keys:

| Key | Value |
|---|---|
| `framework_version` | MAJOR.MINOR.PATCH (e.g. `3.1.3`) |
| `tag` | `v` + framework_version (e.g. `v3.1.3`) |
| `resolved_sha` | the exact resolved commit, 40 lowercase hex |
| `declared_range` | comma-separated comparators such as `">=3.1.0,<4.0.0"` or an exact `"==3.1.3"`, each of `==`, `>=`, `<=`, `>`, `<` followed by MAJOR.MINOR.PATCH |
| `source_url` | the framework repository URL |

CI MUST assert lock-to-payload consistency against `.nizam/provenance.json` and reject drift (the supplied checker `tools/check_provenance_lock.py --repo DIR` performs this). Exact-SHA evidence remains REQUIRED for release and acceptance claims exactly as before: `bootstrap.sh --expected-sha` behaviour is unchanged because bootstrap still installs an exact tag; the range governs the consumer's declared acceptance envelope, not the install resolution.

*Attribution: This provenance policy is derived from the Vibe Coding Manifesto (v2.0), Sections I (Principle 7) and V.4.*
