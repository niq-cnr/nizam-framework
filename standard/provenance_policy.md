---
id: nizam-provenance-policy
title: "Supply-Chain Provenance Policy"
description: "Rules for ensuring every artifact, prompt, model, tool call, and release is attestable and auditable."
version: 0.2.0
status: active
enforcement: partially-enforced
authoritative_source: standard/provenance_policy.md
change_log:
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3, gate H-CONSTITUTIONAL): marked partially-enforced -- the SHA-pinned-Actions requirement is now mechanized as validate.sh check C14 (vlib_workflows_sha_pinned over the workflows directory), while the attestation, agent-audit-envelope, and SLSA-pipeline requirements are consumer-aspirational."
---

# Supply-Chain Provenance Policy

> **Partially enforced.** The SHA-pinned-Actions requirement IS verified on this repository's own workflows by `tools/validate.sh` (check C14). The artifact-attestation, agent-audit-envelope, and SLSA-pipeline requirements are consumer-aspirational — a consuming repository enforces them in its own build and release pipeline. Recorded per the Track 3 decision (feature 058).

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

*Attribution: This provenance policy is derived from the Vibe Coding Manifesto (v2.0), Sections I (Principle 7) and V.4.*
