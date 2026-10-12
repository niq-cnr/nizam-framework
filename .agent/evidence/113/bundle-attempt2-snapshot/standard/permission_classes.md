---
id: nizam-permission-classes
title: "Permission and Sandbox Policy"
description: "Deny-by-default role permission classes and Kubernetes RBAC allocations for agentic systems."
version: 0.3.0
status: active
enforcement: consumer-aspirational
authoritative_source: standard/permission_classes.md
change_log:
  - version: "0.3.0"
    date: "2026-10-11"
    summary: "Add optional scoped runtime-session grants without general Orchestrator execution authority."
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3 mechanize-or-descope decision, gate H-CONSTITUTIONAL): marked consumer-aspirational -- this framework ships the standard as a reference a consumer enforces in its own runtime and CI and does not verify its semantics, so first-contact surfaces stop implying enforcement that does not exist."
---

# Permission and Sandbox Policy

> **Consumer-aspirational.** A reference standard a consuming repository enforces in its own runtime and CI; this framework's validator does not verify these semantics. Recorded per the Track 3 mechanize-or-descope decision (feature 058).

## 1. Overview

The security baseline for any agentic system is **deny-by-default**. Tool access is bounded by role, sandbox, roots, environment, and time. `bash` and `kubectl` are privilege-bearing capabilities requiring strict sandboxing and RBAC.

## 2. Role Permission Classes

| Role | Default Permissions | Prohibited by Default |
|------|-------------------|----------------------|
| Orchestrator | Read repos, read strategy, read task packs | Direct code editing, bash, `kubectl`, merge, deploy |
| Planner | Read repos, read strategy, structured reasoning tools | Direct code editing, merge, deploy |
| Generator | Scoped writes in task branch, sandboxed local bash | Broad repo writes, cluster access, privileged network egress, direct deploy |
| Validator | Read-only repos, schema validators, diff tools | Editing application code, merge, deploy |
| Evaluator | Sandboxed bash, Playwright, non-prod verification tools, approved `kubectl` scopes | Unapproved production mutation, code edits, merge without human sign-off |

## 3. `kubectl` Permission Classes

`kubectl` is not a generic tool; it is a privileged deploy-plane capability.

| Permission Class | Access | Approval Required |
|-----------------|--------|:---:|
| `kubectl.read.nonprod` | Read-only cluster state in non-production | No |
| `kubectl.deploy.nonprod` | Deploy operations in non-production | Evaluator + Human |
| `kubectl.read.prod` | Read-only cluster state in production | Human |
| `kubectl.deploy.prod` | Deploy operations in production | Human + Protected environment |

## 4. Credential Policy

Cloud and cluster access MUST use **ephemeral credentials** (OIDC or equivalent federation), not long-lived repository secrets.

*Attribution: These permission classes and policies are ported from the Vibe Coding Manifesto (v2.0), Section VII.*

## 5. Runtime Session Permission Classes

These optional grants are consumer-aspirational and deny-by-default. A consumer
that offers live sessions must enforce `methodology/10_live_runtime_sessions.md`
with explicit capability grants bounded to the named role and session. They do
not grant general shell access; the default Orchestrator bash prohibition in
Section 2 remains in force.

| Permission Class | Role | Allowed Scope | Denied Scope |
| --- | --- | --- | --- |
| `runtime.session.lifecycle` | Orchestrator | Open, transfer and close a session only | Evaluate, load, compile, run tests, observe project code or general bash |
| `runtime.session.operate` | Generator | Operate only its own development session with current owner, generation and lease | Foreign sessions or acceptance evidence |
| `runtime.session.accept` | Evaluator | Independent acceptance only in a fresh hermetic environment reconstructed from committed source | Warm Generator sessions, saved development images or inherited build caches |

Observation-only review trials are denied all three classes and every session
endpoint. Lifecycle calls MUST NOT evaluate project code, including observation
callbacks. Ownership, generation and lease checks precede any operation that
executes code. Permission names describe required policy, not delivered runtime
enforcement; future mechanisms require their own approved feature contracts.
