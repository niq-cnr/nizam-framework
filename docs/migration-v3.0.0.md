---
id: nizam-migration-v3
title: "v3.0.0 corrective migration candidate"
description: "Migration for complete C13 governance manifest enforcement."
version: 1.0.0
status: draft
authoritative_source: docs/migration-v3.0.0.md
---

# Unreleased major corrective candidate

This migration describes prepared NF-03/NF-04 changes; v3.0.0 has not been released.
C13 now validates `tools/skill.json` against
`schema/governance_skill.schema.json` before relational checks. This is a
breaking restriction under `methodology/06_release_train.md`, even though the
shipped manifest already conforms. Existing valid shipped manifests need no edit.

Consumer extensions must retain non-empty name, description, semantic version,
entrypoint and capabilities; every capability needs name, description and module.
Capability names are unique. Runtime requirements retain the three required
file, shell and structured-data descriptors with boolean required flags and
non-empty descriptions. The state interface retains a root index and artifact
family paths. Unknown producer fields remain allowed; known fields stay typed.
The manifest is distinct from planning manifests and portable SKILL metadata.
No manifest format-version field is added or silently reinterpreted.

Every manifest name obeys entrypoint version parity, including fixture names.
Custom negative fixtures must copy current valid runtime/state/version fields and
change only their tested invariant. Existing path and symlink containment,
intentional-subset indexing and payload carve-outs remain unchanged.

Upgrade only through the pinned bootstrap process once a reviewed immutable
release exists. Preserve consumer-owned extensions and pre-migration fixtures.
Rollback uses the prior verified immutable release, never hand-edits `.nizam/`.
No documentation-skills package or recommendation participates in this migration.
