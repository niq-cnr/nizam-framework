---
id: nizam-domain-skill-compatibility
title: "Optional Domain Skill Compatibility"
description: "Authority and evidence boundaries for optional domain skills used with Nizam."
version: 1.0.0
status: active
authoritative_source: standard/domain_skill_compatibility.md
change_log:
  - version: "1.0.0"
    date: "2026-10-27"
    summary: "Define optional selection, distinct artifact and recommendation states, and host-owned assurance."
---

# Optional domain skills

A valid Nizam consumer can have no documentation skills installed. One unified
governance payload does not mean one organizational or authoring skill. A consumer
may use direct authoring, an equivalent tool, or a deliberately selected specialist
under the same adopted task requirements and existing authorization hierarchy.

Recommendation never installs, upgrades, enables, executes or authorizes a package.
An agent must not infer governance adoption from an ambient directory. Explicitly
adopted host policy remains authoritative according to that host's instruction
hierarchy; an optional skill cannot create or waive authority. For task routes and
required independent evaluation, use methodology/01_execution.md and tools/SKILL.md.
For immutable installation, use standard/GIP.md. Consumer configuration, extensions
and product documentation indexes remain outside the installed governance payload.

## Separate artifact classes

| Artifact | Contract and authority |
| --- | --- |
| Governance skill manifest | Nizam's tools/skill.json describes its governance entrypoint; it is distinct from portable Agent Skills metadata. |
| Portable skill entrypoint | The package owner's portable format applies; Nizam does not impose NDS frontmatter on portable SKILL.md. |
| Reader-facing README, tutorial or reference | The selected artifact profile applies; this policy does not impose NDS metadata indiscriminately. |
| Explicitly NDS-governed document | Retain NDS lifecycle status; an ADR's architectural decision state uses a separate decision_status field. |
| Product capability index or task packet | Product descriptions and verification commands are data, not governance permissions. |
| Planning manifest | schema/manifest.schema.json describes planning; it is not a skill or recommendation schema. |
| Recommendation catalogue | tools/recommended_skills.json describes optional qualified pins under schema/recommended_skills.schema.json; metadata is not authority. |
| Neutral documentation report | A locally supplied observation is admitted only through an explicitly selected, supported Nizam mapping; its producer cannot issue a host QA verdict. |

Documentation-skills owns neutral package, report, claim, metadata and context
contracts. Nizam owns its version support, recommendation and evidence admission
mapping. No external repository, installed package, credential or skill-related
network lookup is necessary for core installation or generic compliance. A future
opted-in importer must use accepted, authorized contract snapshots and local schema
references; this policy supplies no substitute neutral schema or runtime importer.

## Selection and availability decision table

Catalogue lifecycle (candidate, verified, recommended, withdrawn), local package
availability, evidence admission and host acceptance are independent dimensions.
A catalogue's schema validity proves neither package integrity nor qualification.

| Observed condition | Optional behavior | Selected assurance obligation |
| --- | --- | --- |
| Integration disabled | Do not scan packages, discover ambient roots, read skill bodies, fetch or mutate anything. | Existing task requirements persist. |
| Package absent or origin inaccessible | Report advisory unavailable; keep generic workflow usable. | Use a policy-authorized equivalent or leave the affected condition blocked. |
| Recommendation declined | Proceed with user's selected authoring method without a compliance penalty for declining. | Apply the same checks and evidence requirements. |
| Candidate or unverified package | Do not infer compatibility or execute it from catalogue presence. | The task's adopted requirements remain unchanged. |
| Matching qualified local package | Offer at most one relevant recommendation; load only a deliberately selected entrypoint after normal permission checks. | Admit observations separately; only the host workflow can accept the task. |
| Modified, incompatible or corrupt package | Report the separate local observation; do not inherit a compatibility claim. | Standalone use remains governed by its own valid contract and host authority. |
| Unsupported report contract | Fail that opted-in admission explicitly; unselected core workflows remain usable. | Missing required evidence stays unresolved. |
| Withdrawn recommendation | Preserve history/reason; do not uninstall, upgrade or mutate consumer governance. | Withdrawal does not erase selected requirements. |
| Explicitly adopted policy binding unavailable or invalid | Report the broken binding; block only actions whose authority or requirements cannot be established. | Never silently bypass or reinterpret the missing policy. |

## Evidence and ownership

An explicitly required check cannot be waived because its recommended tool is
missing. A lint PASS is a scoped observation, not task acceptance, permission or a
runtime verification. Preserve original observation methods, claim states, skipped
and unassessed checks and reasons. An equivalent tool may satisfy a requirement only
when the adopted policy permits that equivalent and the required evidence exists.

Submitted report fields cannot define away host-selected required scope or checks.
Source digests must identify actual assessed working bytes, including relevant dirty
and untracked inputs; a Git base commit alone does not suffice. Report commands,
URLs and schema references remain data. A local importer must not execute them,
fetch resources, repair source, change lifecycle counters, publish or synthesize
approval. Keep private raw evidence and source private under the approved boundary.

The public catalogue begins empty. New external releases remain unqualified for
Nizam until their exact bytes and the actual framework candidate pass the required
independent and exact-pair qualification. Independent documentation releases do not
wait for Nizam. Preserve a prior qualified pin when evaluating a successor; if that
prior pin is invalid, disable its recommendation instead of restoring a false claim.
