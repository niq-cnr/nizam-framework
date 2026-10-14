---
id: nizam-permission-classes
title: "Permission and Sandbox Policy"
description: "Deny-by-default role permission classes and Kubernetes RBAC allocations for agentic systems."
version: 0.2.0
status: active
enforcement: consumer-aspirational
authoritative_source: standard/permission_classes.md
change_log:
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
