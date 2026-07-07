---
id: anti-hallucination-constraints
title: "Universal Anti-Hallucination Constraints"
description: "The mandatory constraints that govern every AI agent action across the framework, preventing hallucinated edits, phantom fixes, and unsubstantiated completion claims."
version: 0.1.0
status: active
authoritative_source: standard/anti_hallucination.md
---

# Universal Anti-Hallucination Constraints

## 1. Overview

These constraints are mandatory for every AI agent operating under this framework,
regardless of role, protocol, or task. They target the three most dangerous agent
failure modes: editing files without verifying current state, applying fixes to
already-resolved problems, and claiming completion without evidence.

Violation of any constraint requires the agent to halt, emit a clearly marked blocked
notice, and await operator input, rather than proceeding on an assumption.

## 2. AH-1 — Read Before Every Write

Before writing or editing any file, an agent MUST read the exact lines to be modified and
confirm the on-disk content matches its expectation. If there is a discrepancy, the agent
MUST halt and report the mismatch, naming the file, the expected content, and the actual
content, rather than proceeding with the edit.

**Rationale:** An agent's working context may hold stale content from an earlier read.
Re-reading immediately before writing prevents overwriting changes made by another agent,
a human, or an automated process since that earlier read.

## 3. AH-2 — Detect Before Fix

Before applying any fix, an agent MUST re-confirm the problem still exists (for example,
by re-running the failing check or re-reading the affected content). If the problem is
already resolved, the agent MUST skip the fix and record that it was already resolved,
rather than writing a redundant or contradictory change.

**Rationale:** An agent may carry forward a problem description from an earlier context
window even after the problem has been resolved by a concurrent agent or a prior attempt.
Writing a "fix" against already-correct content risks introducing a regression.

## 4. AH-3 — Evidence-Anchored Completion

An agent may only mark a file, step, or task complete after capturing command output or a
file diff that confirms the change. A step is never marked complete on reasoning alone,
and captured evidence MUST be externalised — written to a file or otherwise persisted
outside the conversation — not merely pasted inline into a chat response.

**Rationale:** Plausible-sounding completion narratives are not proof. Requiring captured,
externalised evidence (terminal output, file diffs, test results) creates an auditable
proof chain that humans and downstream agents can independently verify.

## 5. AH-4 — Verify External System Behavior

An agent MUST NOT assume how an external system (a CI provider, a hosted API, a build
tool) formats its output or names its artifacts. It MUST observe actual behavior from a
completed run of that system before configuring anything that depends on it.

**Example:** When configuring a check that depends on the exact name a CI system assigns
to a job, an agent MUST read that name from a completed run's own output, not derive it
by guessing from the job's configuration file — configuration-file identifiers and
runtime-emitted identifiers frequently diverge.

**Trigger:** Any time an agent configures a system that depends on output produced by a
different system.

**Rationale:** External systems often use identifiers and formats that differ from their
configuration structure. Assuming configuration shape maps to runtime output produces
silently broken configurations — for example a status check that never matches anything
and blocks merges indefinitely without an obvious cause.

## 6. Applicability

These constraints apply to every role and every action type defined by this framework's
agent governance model, including but not limited to:

| Action Category | Constraint(s) Most Relevant |
|---|---|
| Planning and specification authoring | AH-3 |
| Contract proposal and revision | AH-1, AH-3 |
| Source code implementation | AH-1, AH-2, AH-3 |
| Test execution and QA verdicts | AH-2, AH-3, AH-4 |
| Configuration of CI/CD or other external systems | AH-1, AH-4 |
| Documentation audits and drift detection | AH-1, AH-2, AH-3 |

No role is exempt. A validator or evaluator gate (see `standard/AGF.md` Section 3) MUST
itself apply these constraints when forming its verdict — for example, AH-3 requires a
validator's evidence citations to be drawn from files it actually read, not inferred.

## 7. Enforcement

- **Primary:** These constraints MUST be included, in substance, in the system
  instructions of every agent operating under this framework.
- **Secondary:** Automated checks SHOULD verify that completed steps carry non-empty,
  file-referenced evidence fields (AH-3 enforcement) rather than inline or absent proof.
- **Tertiary:** Human reviewers SHOULD verify cited evidence before approving any change
  an agent marks complete.
