---
id: nizam-capability-profiles
title: "Capability Profile Model"
description: "Binds agent roles to task types, latency budgets, cost budgets, and safety classes rather than to specific models, enabling eval-gated promotion and fallback."
version: 0.2.0
status: active
enforcement: partially-enforced
authoritative_source: standard/capability_profiles.md
change_log:
  - version: "0.2.0"
    date: "2026-07-20"
    summary: "Feature 058 (Track 3, gate H-CONSTITUTIONAL): marked partially-enforced -- the five-profile to five-AGF-role correspondence is now mechanized as validate.sh check C15 (vlib_profiles_cover_roles), while the no-hard-coded-models, eval-gated-promotion, and cross-provider-fallback requirements are consumer-aspirational."
---

# Capability Profile Model

> **Partially enforced.** The five-profile ↔ five-AGF-role correspondence IS verified by `tools/validate.sh` (check C15). The no-hard-coded-model-names, eval-gated-promotion, and cross-provider-fallback requirements are consumer-aspirational — a consuming repository binds and gates models in its own runtime. Recorded per the Track 3 decision (feature 058).

## 1. Overview

Models age, deprecate, and degrade. Hard-coding specific model names (e.g., `gpt-4o` or `claude-3-5-sonnet`) into orchestration logic or governance documents creates brittleness and prevents rapid response to outages.

The Nizam Framework solves this by introducing the **Capability Profile Model**, ported from the Vibe Coding Manifesto. Roles are bound to abstract profiles, not models. Models are bound to profiles via a configuration file, and changed only through benchmarked eval promotion.

## 2. The Five Standard Profiles

Every role defined in `standard/AGF.md` maps to one of the following capability profiles:

| Capability Profile | Task Type | Latency Budget | Cost Budget | Safety Class |
|---|---|---|---|---|
| `orchestrator-primary` | Topology selection, delegation, evidence collection | Interactive | Medium | High |
| `planner-creative` | Spec authorship, architecture analysis | Batch-tolerant | Medium | Medium |
| `generator-deterministic` | Code implementation, test authorship | Interactive | Low | High |
| `validator-structural` | Schema/contract verification | Interactive | Low | Medium |
| `evaluator-adversarial` | QA execution, regression detection | Batch-tolerant | Medium | High |

## 3. Model-Routing Rules

1. **No hard-coded bindings:** An orchestrator or calling script MUST NOT hard-code model names. It MUST resolve the model name from the active capability profile configuration at runtime.
2. **Eval-gated promotion:** A model cannot be promoted to a capability profile without passing role-specific eval thresholds on a representative regression set.
3. **Fallback requirement:** Every capability profile MUST define at least one pre-approved fallback model from a different provider, to be used automatically during primary provider outages.

## 4. Configuration Schema

A repository adopting this standard maintains its model bindings in a configuration file that validates against `schema/capability_profile.schema.json`.

*Attribution: The capability profile model and its five standard profiles are derived from the Vibe Coding Manifesto (v2.0), Section 3.3.*
